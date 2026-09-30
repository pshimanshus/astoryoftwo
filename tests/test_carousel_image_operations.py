"""Offline edit operations and invocation lifecycle, using synthetic PNG returns."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from pipeline.stages.carousel_generation_inputs import build_generation_inputs
from pipeline.stages.carousel_generation_state import compact_v3_state, read_generation_state
from pipeline.stages.codex_builtin_image_generation import (
    _assert_current_receipt,
    build_compiled_prompt_handoff,
    prepare_codex_builtin_image_generation,
)
from tests.helpers.imagegen_invocations import ingest_synthetic_outputs
from tests.test_carousel_source_normalization import _candidate, _package, _png
from tests.test_illustration_carousel import _approve_proof


def _operation(number: int, source: Path) -> list[dict]:
    return [{"slide": number, "intent": "edit", "targets": {"instagram_post": str(source)}}]


def _snapshot(package: Path) -> dict[str, bytes]:
    return {path.relative_to(package).as_posix(): path.read_bytes()
            for path in package.rglob("*") if path.is_file()}


def test_generate_is_canonical_and_hash_stable(tmp_path):
    package = _package(tmp_path)
    before = build_generation_inputs(package)
    path = package / "slides.json"
    slides = json.loads(path.read_text())
    slides[0]["image_operation"] = {"intent": "generate", "targets": {}}
    path.write_text(json.dumps(slides))
    assert build_generation_inputs(package) == before


def test_edit_snapshots_existing_candidate_before_invalidation_and_keeps_retry_count(tmp_path):
    package = _package(tmp_path)
    prepare_codex_builtin_image_generation(package, proof_slide=2)
    source = _png(tmp_path / "source.png", (1080, 1440))
    first = ingest_synthetic_outputs(package, {"instagram_post": [source]}, proof_slide=2)
    candidate = _candidate(package, 2, 1)
    target = package / candidate["native_outputs"]["instagram_post"]["path"]
    original = target.read_bytes()
    state = prepare_codex_builtin_image_generation(package, proof_slide=2, image_operations=_operation(2, target))
    assert state["status"] == "handoff_ready"
    assert state["slides"]["2"]["attempts"] == 1
    assert state["slides"]["2"]["premise_sha256"] == first["slides"]["2"]["premise_sha256"]
    assert not target.exists()
    handoff = build_compiled_prompt_handoff(package, slide_numbers=[2], output_formats=["instagram_post"])
    item = handoff["files"][0]
    assert item["intent"] == "edit"
    assert len(handoff["reference_bindings"]) == 5
    assert len(item["input_images"]) == 6
    assert item["input_images"][0] == item["edit_target_binding"]
    assert (package / item["edit_target_binding"]["path"]).read_bytes() == original
    second = ingest_synthetic_outputs(package, {"instagram_post": [_png(tmp_path / "edited.png", (1080, 1440), "red")]})
    assert second["slides"]["2"]["attempts"] == 2
    receipt = second["slides"]["2"]["attempt_history"][-1]
    assert receipt["invocations"][0]["evidence"] == "operator_recorded"
    assert "model" not in receipt["invocations"][0]
    assert "tool_call_id" not in receipt["invocations"][0]
    assert compact_v3_state(second) == second
    _assert_current_receipt(package, second, _candidate(package, 2, 2))
    next_target = package / _candidate(package, 2, 2)["native_outputs"]["instagram_post"]["path"]
    exhausted = prepare_codex_builtin_image_generation(package, proof_slide=2, image_operations=_operation(2, next_target))
    assert exhausted["next_action"] == "repair_visual_premise"
    assert exhausted["slides"]["2"]["attempts"] == 2


@pytest.mark.parametrize("bad_operation", [
    {"slide": 2, "intent": "edit", "targets": {}},
    {"slide": 2, "intent": "edit", "targets": {"square": "missing.png"}},
    {"slide": 3, "intent": "generate", "targets": {}},
    {"slide": 2, "intent": "generate", "targets": {"instagram_post": "missing.png"}},
])
def test_invalid_operation_is_byte_stable(tmp_path, bad_operation):
    package = _package(tmp_path)
    prepare_codex_builtin_image_generation(package, proof_slide=2)
    before = _snapshot(package)
    with pytest.raises(ValueError):
        prepare_codex_builtin_image_generation(package, proof_slide=2, image_operations=[bad_operation])
    assert _snapshot(package) == before


def test_all_operations_validated_before_first_snapshot(tmp_path):
    package = _package(tmp_path)
    target = _png(tmp_path / "target.png", (1080, 1440))
    before = _snapshot(package)
    with pytest.raises(ValueError):
        prepare_codex_builtin_image_generation(package, proof_slide=2, image_operations=[
            *_operation(2, target), {"slide": 99, "intent": "generate", "targets": {}}
        ])
    assert _snapshot(package) == before


def test_proof_edit_revokes_approval_and_other_edit_keeps_hidden_candidates(tmp_path):
    package = _package(tmp_path)
    _approve_proof(package, tmp_path, proof_slide=3)
    prepare_codex_builtin_image_generation(package)
    outputs = {"instagram_post": [_png(tmp_path / f"batch-{n}.png", (1080, 1440), "red") for n in (1, 2, 4)]}
    ingest_synthetic_outputs(package, outputs)
    # Use the candidate API to avoid depending on the quarantine's nesting.
    second = _candidate(package, 2, 1)
    unrelated = package / second["native_outputs"]["instagram_post"]["path"]
    unrelated_bytes = unrelated.read_bytes()
    first = _candidate(package, 1, 1)
    target = package / first["native_outputs"]["instagram_post"]["path"]
    edited = prepare_codex_builtin_image_generation(package, image_operations=_operation(1, target))
    assert edited["selected_slides"] == [1]
    assert unrelated.read_bytes() == unrelated_bytes
    assert (package / "proof-qa.json").is_file()
    proof = _candidate(package, 3, 1)
    proof_target = package / proof["native_outputs"]["instagram_post"]["path"]
    edited = prepare_codex_builtin_image_generation(package, proof_slide=3, image_operations=_operation(3, proof_target))
    assert edited["selected_slides"] == [3]
    assert not (package / "proof-qa.json").exists()
    assert unrelated.read_bytes() == unrelated_bytes


def test_stale_proof_inputs_cannot_authorize_nonproof_edit(tmp_path):
    package = _package(tmp_path)
    _approve_proof(package, tmp_path, proof_slide=3)
    slides_path = package / "slides.json"
    slides = json.loads(slides_path.read_text())
    slides[2]["copy"] += " Changed before edit."
    slides_path.write_text(json.dumps(slides))
    before = _snapshot(package)
    target = _png(tmp_path / "edit-target.png", (1080, 1440))
    with pytest.raises(ValueError, match="proof selection"):
        prepare_codex_builtin_image_generation(package, image_operations=_operation(1, target))
    assert _snapshot(package) == before


def test_legacy_persisted_receipts_are_not_rewritten_with_invented_evidence(tmp_path):
    from pipeline.stages.codex_builtin_image_generation import reconcile_package_state

    package = _package(tmp_path)
    prepare_codex_builtin_image_generation(package, proof_slide=2)
    ingest_synthetic_outputs(package, {"instagram_post": [_png(tmp_path / "source.png", (1080, 1440))]})
    # Model an already-persisted receipt from the preceding schema version.
    state_path = package / "generation-state.json"
    state = json.loads(state_path.read_text())
    state["slides"]["2"]["attempt_history"][0].pop("invocations")
    state_path.write_text(json.dumps(state))
    candidate = _candidate(package, 2, 1)
    candidate["generation_receipt"].pop("invocations")
    candidate_path = next(package.glob(".internal/visual-quarantine/**/candidate.json"))
    candidate_path.write_text(json.dumps(candidate))
    before = _snapshot(package)
    _assert_current_receipt(package, read_generation_state(package), candidate)
    reconcile_package_state(package)
    assert _snapshot(package) == before
