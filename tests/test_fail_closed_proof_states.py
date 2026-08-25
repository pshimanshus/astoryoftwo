from __future__ import annotations

import json
from datetime import date
from pathlib import Path

from PIL import Image
import pytest

from pipeline.stages.codex_builtin_image_generation import (
    approve_proof,
    ingest_generated_outputs,
    prepare_codex_builtin_image_generation,
    review_quarantined_outputs,
)
from pipeline.stages.codex_native_carousel import create_codex_native_carousel


def _png(path: Path, size: tuple[int, int] = (1080, 1440)) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    Image.new("RGB", size, "ivory").save(path)
    return path


def _package(tmp_path: Path) -> Path:
    brief = tmp_path / "brief.json"
    brief.write_text(
        json.dumps(
            {
                "slides": [
                    {
                        "copy": f"Locked copy {number}",
                        "physical_action": f"Aachu and Zuv perform visible action {number} together.",
                    }
                    for number in range(1, 5)
                ]
            }
        ),
        encoding="utf-8",
    )
    identity_paths = [
        _png(tmp_path / "identity/aachu/a.png", (40, 40)),
        _png(tmp_path / "identity/zuv/z.png", (41, 40)),
        _png(tmp_path / "identity/together/face.png", (42, 40)),
        _png(tmp_path / "identity/together/body.png", (43, 40)),
    ]
    return create_codex_native_carousel(
        story="A difficult shared decision",
        image_paths=[],
        identity_image_paths=identity_paths,
        style_reference_paths=[_png(tmp_path / "style.png", (44, 40))],
        creative_baseline_path=brief,
        output_root=tmp_path / "output/carousels",
        today=date(2026, 8, 24),
    )


def _failed_authored_qa(slide: int) -> dict[str, object]:
    return {
        "status": "FAIL",
        "inspection": {"method": "codex_view_image", "decoded_pixels_observed": True},
        "selected_slides": [slide],
        "slides": [
            {
                "slide": slide,
                "reviews": {
                    "instagram_post": {
                        "checks": {
                            "physical_action": {
                                "status": "FAIL",
                                "evidence": "Both people pull unrelated objects, so the locked action is not visible.",
                            }
                        }
                    }
                },
            }
        ],
    }


def _failed_attempt(package: Path, tmp_path: Path, slide: int, attempt: int) -> dict[str, object]:
    ingest_generated_outputs(
        package,
        {"instagram_post": [_png(tmp_path / f"attempt-{attempt}.png")]},
        proof_slide=slide if attempt == 1 else None,
    )
    (package / "proof-qa.json").write_text(
        json.dumps(_failed_authored_qa(slide)), encoding="utf-8"
    )
    return review_quarantined_outputs(package)


def test_failed_semantic_proof_retries_only_the_proof_slide(tmp_path: Path) -> None:
    package = _package(tmp_path)
    prepare_codex_builtin_image_generation(package, proof_slide=2)
    failed = _failed_attempt(package, tmp_path, 2, 1)
    assert failed["status"] == "proof_failed"
    assert failed["selected_slides"] == [2]
    assert failed["slides"]["2"]["attempts"] == 1
    assert not (package / "final-images.json").exists()

    repair = prepare_codex_builtin_image_generation(package)
    assert repair["status"] == "handoff_ready"
    assert repair["selected_slides"] == [2]
    assert len(list((package / ".internal/compiled-prompts").rglob("*.prompt.txt"))) == 1


def test_two_semantic_attempts_exhaust_only_current_premise(tmp_path: Path) -> None:
    package = _package(tmp_path)
    prepare_codex_builtin_image_generation(package, proof_slide=2)
    first = _failed_attempt(package, tmp_path, 2, 1)
    assert first["next_action"] == "retry_selected_slides"
    prepare_codex_builtin_image_generation(package)
    second = _failed_attempt(package, tmp_path, 2, 2)
    assert second["status"] == "proof_failed"
    assert second["slides"]["2"]["attempts"] == 2
    assert second["next_action"] == "repair_visual_premise"
    blocked = prepare_codex_builtin_image_generation(package)
    assert blocked["status"] == "proof_failed"
    assert blocked["next_action"] == "repair_visual_premise"


def test_creator_cannot_override_failed_pixels(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="approval|proof|candidate"):
        approve_proof(_package(tmp_path), proof_sha256="sha256:" + "0" * 64)
