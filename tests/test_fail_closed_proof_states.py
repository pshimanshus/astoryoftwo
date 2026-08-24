from __future__ import annotations

import json
from datetime import date
from pathlib import Path

from PIL import Image
import pytest

from pipeline.stages.codex_builtin_image_generation import (
    accept_failed_proof_by_creator,
    package_codex_builtin_outputs,
    prepare_codex_builtin_image_generation,
    promote_quarantined_codex_builtin_outputs,
    recompile_failed_proof_handoff,
)
from pipeline.stages.codex_native_carousel import create_codex_native_carousel


def _png(path: Path, size: tuple[int, int] = (1080, 1440)) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    Image.new("RGB", size, "ivory").save(path)
    return path


def _package(tmp_path: Path) -> Path:
    identity = _png(tmp_path / "identity.png", (300, 300))
    brief = tmp_path / "brief.json"
    brief.write_text(
        json.dumps(
            {
                "slides": [
                    {"copy": f"Locked copy {number}", "physical_action": f"Aachu and Zuv perform visible action {number}."}
                    for number in range(1, 5)
                ]
            }
        ),
        encoding="utf-8",
    )
    return create_codex_native_carousel(
        story="A difficult shared decision",
        image_paths=[],
        identity_image_paths=[identity],
        creative_baseline_path=brief,
        output_root=tmp_path / "output/carousels",
        today=date(2026, 8, 24),
    )


def _failed_qa(state: dict[str, object]) -> dict[str, object]:
    candidate = state["quarantine_candidates"][0]  # type: ignore[index]
    return {
        "schema_version": "carousel-pixel-qa/v1",
        "scope": "proof",
        "status": "FAIL",
        "image_set_sha256": state["image_set_sha256"],
        "slides": [
            {
                "slide": candidate["slide"],
                "native_outputs": candidate["native_outputs"],
                "checks": {
                    "semantic_action": {
                        "status": "FAIL",
                        "evidence": "Both people pull unrelated objects, so the intended shared decision is not visible.",
                    }
                },
            }
        ],
    }


def test_failed_semantic_proof_is_not_handoff_ready_and_retry_is_slide_local(tmp_path: Path) -> None:
    package = _package(tmp_path)
    prepare_codex_builtin_image_generation(package, proof_slide=2)
    first = package_codex_builtin_outputs(
        package,
        {"instagram_post": [_png(tmp_path / "attempt-1.png")]},
        proof_slide=2,
    )
    (package / "proof-qa.json").write_text(json.dumps(_failed_qa(first)), encoding="utf-8")
    failed = promote_quarantined_codex_builtin_outputs(package)
    assert failed["status"] == "proof_failed"
    assert failed["next_action"] == "repair_visual_premise"
    assert failed["repair_slides"] == [2]
    assert not (package / "final-images.json").exists()

    repair = recompile_failed_proof_handoff(package)
    assert repair["status"] == "handoff_ready"
    assert repair["stage"] == "repair"
    assert repair["selected_slides"] == [2]
    prompt_files = list((package / ".internal/compiled-prompts").rglob("*.prompt.txt"))
    assert len(prompt_files) == 1
    assert prompt_files[0].name == "slide-02.prompt.txt"


def test_two_failed_semantic_attempts_block_more_generation(tmp_path: Path) -> None:
    package = _package(tmp_path)
    prepare_codex_builtin_image_generation(package, proof_slide=2)
    for attempt in (1, 2):
        state = package_codex_builtin_outputs(
            package,
            {"instagram_post": [_png(tmp_path / f"attempt-{attempt}.png")]},
            proof_slide=2 if attempt == 1 else None,
        )
        (package / "proof-qa.json").write_text(json.dumps(_failed_qa(state)), encoding="utf-8")
        state = promote_quarantined_codex_builtin_outputs(package)
        if attempt == 1:
            assert state["status"] == "proof_failed"
            recompile_failed_proof_handoff(package)
    assert state["status"] == "blocked_visual_qa"
    assert state["attempts_by_slide"]["2"] == 2
    assert state["next_action"] == "revise_copy_or_visual_premise"
    blocked = prepare_codex_builtin_image_generation(package)
    assert blocked["status"] == "blocked_visual_qa"


def test_creator_cannot_override_a_failed_proof(tmp_path: Path) -> None:
    package = _package(tmp_path)
    with pytest.raises(ValueError, match="cannot be accepted"):
        accept_failed_proof_by_creator(package, package / "approval.json")


def test_wrong_size_candidate_is_rejected_instead_of_resized(tmp_path: Path) -> None:
    package = _package(tmp_path)
    prepare_codex_builtin_image_generation(package, proof_slide=1)
    with pytest.raises(ValueError, match="must be native 1080x1440"):
        package_codex_builtin_outputs(
            package,
            {"instagram_post": [_png(tmp_path / "wrong.png", (1440, 1920))]},
            proof_slide=1,
        )
    assert not (package / "final").exists()
