from __future__ import annotations

import json
from datetime import date
from pathlib import Path

from PIL import Image
import pytest

from pipeline.agentic.carousel_state import derive_carousel_state
from pipeline.stages.codex_builtin_image_generation import (
    ingest_generated_outputs,
    prepare_codex_builtin_image_generation,
)
from pipeline.stages.codex_native_carousel import create_codex_native_carousel


def _png(path: Path, size: tuple[int, int] = (40, 40), color: str = "tan") -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    Image.new("RGB", size, color).save(path)
    return path


def _package(tmp_path: Path) -> Path:
    brief = tmp_path / "brief.json"
    brief.write_text(
        json.dumps(
            {
                "slides": [
                    {
                        "copy": f"Locked copy {number}",
                        "physical_action": f"They complete concrete action {number} together.",
                    }
                    for number in range(1, 5)
                ]
            }
        ),
        encoding="utf-8",
    )
    identity_paths = [
        _png(tmp_path / "identity/aachu/a.png", color="salmon"),
        _png(tmp_path / "identity/zuv/z.png", color="skyblue"),
        _png(tmp_path / "identity/together/face.png", color="tan"),
        _png(tmp_path / "identity/together/body.png", color="plum"),
    ]
    return create_codex_native_carousel(
        story="One shared direction.",
        image_paths=[],
        identity_image_paths=identity_paths,
        style_reference_paths=[_png(tmp_path / "style.png", color="ivory")],
        creative_baseline_path=brief,
        output_root=tmp_path / "output/carousels",
        today=date(2026, 8, 24),
    )


def test_derived_state_uses_exact_v3_draft_vocabulary(tmp_path: Path) -> None:
    state = derive_carousel_state(_package(tmp_path))
    assert state.name == "draft"
    assert state.next_action == "prepare_riskiest_proof"
    assert state.publishable is False


def test_handoff_state_uses_generation_state_truth(tmp_path: Path) -> None:
    package = _package(tmp_path)
    prepare_codex_builtin_image_generation(package, proof_slide=2)
    state = derive_carousel_state(package)
    assert state.name == "handoff_ready"
    assert state.next_action == "generate_selected_slides"
    assert state.blocked is False


def test_ingested_proof_is_proof_qa_required_not_generic_ready(tmp_path: Path) -> None:
    package = _package(tmp_path)
    prepare_codex_builtin_image_generation(package, proof_slide=2)
    ingest_generated_outputs(
        package,
        {"instagram_post": [_png(tmp_path / "proof.png", (1080, 1440))]},
        proof_slide=2,
    )
    state = derive_carousel_state(package)
    assert state.name == "proof_qa_required"
    assert state.next_action == "review_proof_pixels"


def test_story_only_prepare_reports_blocked_with_concrete_next_action(tmp_path: Path) -> None:
    package = create_codex_native_carousel(
        story="Unresolved story only.",
        image_paths=[],
        identity_image_paths=[_png(tmp_path / "identity.png")],
        slide_count=4,
        output_root=tmp_path / "output/carousels",
        today=date(2026, 8, 24),
    )
    prepare_codex_builtin_image_generation(package)
    state = derive_carousel_state(package)
    assert state.name == "blocked"
    assert state.blocked is True
    assert state.next_action == "lock_visible_actions"


def test_archived_v2_state_is_mapped_read_only_to_v3_vocabulary(tmp_path: Path) -> None:
    package = tmp_path / "archived"
    package.mkdir()
    legacy = {"schema_version": "carousel-generation-state/v2", "status": "BATCH_ALLOWED"}
    (package / "image-generation.json").write_text(json.dumps(legacy), encoding="utf-8")
    state = derive_carousel_state(package)
    assert state.name == "batch_ready"
    assert not (package / "generation-state.json").exists()


def test_archived_v2_prepare_with_format_change_leaves_whole_tree_unchanged(
    tmp_path: Path,
) -> None:
    package = tmp_path / "archived-prepare"
    package.mkdir()
    (package / "generation-state.json").write_text(
        json.dumps(
            {
                "schema_version": "carousel-generation-state/v2",
                "status": "BATCH_ALLOWED",
            }
        ),
        encoding="utf-8",
    )
    (package / "format-contract.json").write_text("legacy-format-bytes", encoding="utf-8")
    (package / "sentinel.bin").write_bytes(b"unchanged")
    before = {
        path.relative_to(package).as_posix(): path.read_bytes()
        for path in package.rglob("*")
        if path.is_file()
    }

    with pytest.raises(ValueError, match="Archived v2 carousel packages are read-only"):
        prepare_codex_builtin_image_generation(package, formats=["square"])

    after = {
        path.relative_to(package).as_posix(): path.read_bytes()
        for path in package.rglob("*")
        if path.is_file()
    }
    assert after == before
