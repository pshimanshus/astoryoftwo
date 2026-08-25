from __future__ import annotations

import json
from datetime import date
from pathlib import Path

from PIL import Image
import pytest

from pipeline.agentic.workflow_doctor import inspect_carousel_package
from pipeline.stages.carousel_generation_state import (
    PUBLIC_STATUSES,
    STATE_SCHEMA_VERSION,
    initialize_generation_state,
    read_generation_state,
    write_v3_state,
)
from pipeline.stages.codex_builtin_image_generation import reconcile_package_state
from pipeline.stages.codex_native_carousel import create_codex_native_carousel


EXPECTED_STATES = {
    "draft",
    "blocked",
    "handoff_ready",
    "proof_qa_required",
    "proof_failed",
    "awaiting_creator_proof_approval",
    "batch_ready",
    "final_qa_required",
    "final_qa_failed",
    "publish_ready",
}


def _png(path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    Image.new("RGB", (40, 40), "tan").save(path)
    return path


def _package(tmp_path: Path) -> Path:
    brief = tmp_path / "brief.json"
    brief.write_text(
        json.dumps(
            {
                "slides": [
                    {
                        "copy": f"Exact copy {number}",
                        "physical_action": f"Aachu and Zuv move object {number} together.",
                    }
                    for number in range(1, 5)
                ]
            }
        ),
        encoding="utf-8",
    )
    return create_codex_native_carousel(
        story="They choose one direction together.",
        image_paths=[],
        identity_image_paths=[_png(tmp_path / "identity.png")],
        creative_baseline_path=brief,
        output_root=tmp_path / "output/carousels",
        today=date(2026, 8, 24),
    )


def test_public_state_vocabulary_is_exact() -> None:
    assert set(PUBLIC_STATUSES) == EXPECTED_STATES


def test_new_package_starts_with_compact_v3_state_only(tmp_path: Path) -> None:
    package = _package(tmp_path)
    state = read_generation_state(package)

    assert set(state) == {
        "schema_version",
        "status",
        "next_action",
        "proof_slide",
        "selected_slides",
        "selected_formats",
        "format_sha256",
        "slides",
    }
    assert state["schema_version"] == STATE_SCHEMA_VERSION
    assert state["status"] == "draft"
    assert state["selected_formats"] == ["instagram_post"]
    assert not (package / "image-generation.json").exists()
    assert not (package / "final-images.json").exists()
    for record in state["slides"].values():
        assert set(record) == {
            "status",
            "attempts",
            "source_sha256",
            "prompt_sha256",
            "references_sha256",
            "input_sha256",
        }


def test_write_v3_state_rejects_duplicate_transient_ledgers(tmp_path: Path) -> None:
    package = _package(tmp_path)
    state = read_generation_state(package)
    state["approved_final_candidates"] = {"1": {"path": "not-allowed"}}

    from pipeline.stages.carousel_generation_state import compact_v3_state

    with pytest.raises(ValueError, match="non-canonical"):
        compact_v3_state(state)
    assert not (package / "image-generation.json").exists()


def test_archived_v2_is_read_only_and_not_rewritten(tmp_path: Path) -> None:
    legacy = {
        "schema_version": "carousel-generation-state/v2",
        "status": "BATCH_ALLOWED",
        "slides": [{"slide": 1}],
    }
    (tmp_path / "image-generation.json").write_text(json.dumps(legacy), encoding="utf-8")

    assert read_generation_state(tmp_path) == legacy
    assert not (tmp_path / "generation-state.json").exists()


def test_initializer_is_deterministic_for_existing_inputs(tmp_path: Path) -> None:
    package = _package(tmp_path)
    first = read_generation_state(package)
    second = initialize_generation_state(package)
    assert second == first


@pytest.mark.parametrize(
    "field",
    (
        "format_sha256",
        "source_sha256",
        "prompt_sha256",
        "references_sha256",
        "input_sha256",
    ),
)
def test_v3_writer_rejects_empty_or_noncanonical_fingerprints(
    tmp_path: Path,
    field: str,
) -> None:
    package = _package(tmp_path)
    state = read_generation_state(package)
    if field == "format_sha256":
        state[field] = ""
    else:
        state["slides"]["1"][field] = "SHA256:" + "A" * 64

    with pytest.raises(ValueError, match="canonical sha256"):
        write_v3_state(package, state)


def test_cleared_component_hashes_are_doctor_blocked_and_reconciled(
    tmp_path: Path,
) -> None:
    package = _package(tmp_path)
    state_path = package / "generation-state.json"
    state = read_generation_state(package)
    expected_input = state["slides"]["1"]["input_sha256"]
    for field in ("source_sha256", "prompt_sha256", "references_sha256"):
        state["slides"]["1"][field] = ""
    # Simulate post-write tampering; production writes reject this shape.
    state_path.write_text(json.dumps(state), encoding="utf-8")

    report = inspect_carousel_package(package)
    stale = [
        issue for issue in report.issues if issue.code == "stale_slide_input_fingerprint"
    ]
    assert stale
    assert all(field in stale[0].message for field in (
        "source_sha256",
        "prompt_sha256",
        "references_sha256",
    ))

    repaired = reconcile_package_state(package)
    assert repaired["slides"]["1"]["input_sha256"] == expected_input
    assert all(
        repaired["slides"]["1"][field].startswith("sha256:")
        and len(repaired["slides"]["1"][field]) == 71
        for field in ("source_sha256", "prompt_sha256", "references_sha256")
    )
