"""Independent black-box checks of the approved ImageGen maintenance contract.

Fixtures create small offline packages; invocation records are authored here from
the public handoff, never manufactured by the ingestion implementation.
"""

from __future__ import annotations

from copy import deepcopy
import argparse
import base64
import hashlib
import importlib.util
import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from pipeline.stages import codex_builtin_image_generation as runtime
from pipeline.stages.carousel_generation_inputs import build_generation_inputs
from pipeline.stages.carousel_generation_state import write_v3_state
from tests.test_carousel_source_normalization import (
    _authored_qa,
    _candidate,
    _package,
    _png,
)


def _sha(path: Path) -> str:
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


def _snapshot(package: Path) -> dict[str, bytes]:
    return {
        str(path.relative_to(package)): path.read_bytes()
        for path in package.rglob("*")
        if path.is_file()
    }


def _operation(package: Path, intent: str, *, color: str = "tan", slide: int = 2) -> None:
    slides_path = package / "slides.json"
    slides = json.loads(slides_path.read_text())
    target = _png(package / f".internal/references/edit-targets/{color}.png", (1080, 1440), color)
    operation = {"intent": intent, "targets": {}}
    if intent == "edit":
        operation["targets"] = {
            "instagram_post": {
                "path": str(target.relative_to(package)),
                "sha256": _sha(target),
                "width": 1080,
                "height": 1440,
            }
        }
    slides[slide - 1]["image_operation"] = operation
    slides_path.write_text(json.dumps(slides))


def _prepared(tmp_path: Path, intent: str = "generate") -> tuple[Path, Path, dict]:
    package = _package(tmp_path)
    if intent == "edit":
        _operation(package, intent)
    state = runtime.prepare_codex_builtin_image_generation(package, proof_slide=2)
    assert state["status"] == "handoff_ready"
    source = _png(tmp_path / "returned.png", (1086, 1448), "skyblue")
    return package, source, _handoff(package)


def _handoff(package: Path) -> dict:
    state = runtime.read_generation_state(package)
    return runtime.build_compiled_prompt_handoff(
        package,
        slide_numbers=state["selected_slides"],
        output_formats=state["selected_formats"],
    )


def _records(package: Path, source: Path, handoff: dict) -> list[dict]:
    assert len(handoff["files"]) == 1
    file = handoff["files"][0]
    return [{
        "slide": file["slide"],
        "format": file["format"],
        "intent": file["intent"],
        "tool": "image_gen.imagegen",
        "sent_prompt_sha256": _sha(package / file["path"]),
        "input_images": deepcopy(file["input_images"]),
        "returned_source_sha256": _sha(source),
    }]


def _ingest(package: Path, source: Path, records: list[dict]):
    return runtime.ingest_generated_outputs(
        package,
        {"instagram_post": [source]},
        proof_slide=2,
        invocation_records=records,
    )


@pytest.mark.parametrize("intent", ["generate", "edit"])
def test_fresh_return_requires_invocation_without_any_mutation(tmp_path: Path, intent: str):
    package, source, _ = _prepared(tmp_path, intent)
    before = _snapshot(package)
    with pytest.raises(ValueError, match="[Ii]nvocation"):
        runtime.ingest_generated_outputs(package, {"instagram_post": [source]}, proof_slide=2)
    assert _snapshot(package) == before


@pytest.mark.parametrize("intent", ["generate", "edit"])
@pytest.mark.parametrize("attack", [
    "aggregate_prompt", "wrong_tool", "wrong_intent", "missing_input",
    "reordered_inputs", "substituted_reference", "wrong_input_dimensions",
    "wrong_raw_hash", "empty_coverage", "duplicate_coverage", "extra_coverage",
    "server_attestation", "synthetic_bypass", "legacy_bypass",
    "float_input_width", "float_slide",
])
def test_invocation_tampering_fails_before_package_mutation(tmp_path: Path, intent: str, attack: str):
    package, source, handoff = _prepared(tmp_path, intent)
    records = _records(package, source, handoff)
    record = records[0]
    if attack == "aggregate_prompt":
        record["sent_prompt_sha256"] = runtime.read_generation_state(package)["slides"]["2"]["prompt_sha256"]
        assert record["sent_prompt_sha256"] != _sha(package / handoff["files"][0]["path"])
    elif attack == "wrong_tool":
        record["tool"] = "imagegen"
    elif attack == "wrong_intent":
        record["intent"] = "edit" if intent == "generate" else "generate"
    elif attack == "missing_input":
        record["input_images"].pop()
    elif attack == "reordered_inputs":
        record["input_images"].reverse()
    elif attack == "substituted_reference":
        record["input_images"][-1] = deepcopy(record["input_images"][-2])
    elif attack == "wrong_input_dimensions":
        record["input_images"][0]["width"] = 99999
    elif attack == "wrong_raw_hash":
        record["returned_source_sha256"] = "sha256:" + "0" * 64
    elif attack == "empty_coverage":
        records = []
    elif attack == "duplicate_coverage":
        records.append(deepcopy(record))
    elif attack == "extra_coverage":
        records.append({**deepcopy(record), "slide": 3})
    elif attack == "server_attestation":
        record["evidence"] = "server_attested"
    elif attack == "synthetic_bypass":
        record["synthetic"] = True
    elif attack == "legacy_bypass":
        record["legacy"] = True
    elif attack == "float_input_width":
        record["input_images"][0]["width"] = float(record["input_images"][0]["width"])
    elif attack == "float_slide":
        record["slide"] = float(record["slide"])
    before = _snapshot(package)
    with pytest.raises(ValueError):
        _ingest(package, source, records)
    assert _snapshot(package) == before


def test_invalid_invocation_is_rejected_before_require_v3(tmp_path: Path, monkeypatch):
    package, source, handoff = _prepared(tmp_path)
    records = _records(package, source, handoff)
    records[0]["returned_source_sha256"] = "sha256:" + "0" * 64
    def reconciliation_must_not_run(*args, **kwargs):
        pytest.fail("Invalid invocation entered mutating _require_v3 reconciliation")
    monkeypatch.setattr(runtime, "_require_v3", reconciliation_must_not_run)
    with pytest.raises(ValueError):
        _ingest(package, source, records)


@pytest.mark.parametrize("asset", ["target", "reference", "prompt", "returned"])
def test_changed_bytes_after_prepare_cannot_be_laundered_by_reconciliation(tmp_path: Path, asset: str):
    package, source, handoff = _prepared(tmp_path, "edit")
    records = _records(package, source, handoff)
    file = handoff["files"][0]
    if asset == "returned":
        _png(source, (1086, 1448), "plum")
    elif asset == "prompt":
        path = package / file["path"]
        path.write_text(path.read_text() + "\nUNRECORDED EDIT")
    else:
        index = 0 if asset == "target" else 1
        path = package / file["input_images"][index]["path"]
        _png(path, (1080, 1440) if asset == "target" else (40, 40), "plum")
    before = _snapshot(package)
    with pytest.raises(ValueError):
        _ingest(package, source, records)
    assert _snapshot(package) == before


def test_reauthored_target_and_invocation_still_require_prepare(tmp_path: Path):
    package, source, _ = _prepared(tmp_path, "edit")
    _operation(package, "edit", color="plum")
    # The prompt text does not change when only the editable canvas changes.
    # A newly authored invocation must not launder that change into old state.
    records = _records(package, source, _handoff(package))
    before = _snapshot(package)
    with pytest.raises(ValueError, match="[Pp]repare|inputs.*changed"):
        _ingest(package, source, records)
    assert _snapshot(package) == before


def test_edit_handoff_target_is_first_but_reference_manifest_stays_five(tmp_path: Path):
    package, source, handoff = _prepared(tmp_path, "edit")
    file = handoff["files"][0]
    assert file["intent"] == "edit"
    assert len(handoff["reference_bindings"]) == 5
    assert len(file["input_images"]) == 6
    target = file["edit_target_binding"]
    assert file["input_images"][0]["path"] == target["path"]
    assert file["input_images"][0]["sha256"] == _sha(package / target["path"])
    assert [(i["path"], i["sha256"]) for i in file["input_images"][1:]] == [
        (i["path"], i["sha256"]) for i in handoff["reference_bindings"]
    ]
    state = _ingest(package, source, _records(package, source, handoff))
    assert state["status"] == "proof_qa_required"
    assert state["slides"]["2"]["attempts"] == 1


@pytest.mark.parametrize("intent", ["generate", "edit"])
def test_target_or_intent_change_preserves_exhausted_semantic_budget(tmp_path: Path, intent: str):
    package, source, handoff = _prepared(tmp_path)
    initial = runtime.read_generation_state(package)["slides"]["2"]
    for attempt in (1, 2):
        state = _ingest(package, source, _records(package, source, handoff))
        assert state["slides"]["2"]["attempts"] == attempt
        if attempt == 1:
            runtime.prepare_codex_builtin_image_generation(package, proof_slide=2)
            handoff = _handoff(package)
    _operation(package, "edit", color="plum")
    runtime.prepare_codex_builtin_image_generation(package, proof_slide=2)
    _operation(package, intent, color="salmon")
    state = runtime.prepare_codex_builtin_image_generation(package, proof_slide=2)
    assert state["slides"]["2"]["attempts"] == 2
    assert state["slides"]["2"]["premise_sha256"] == initial["premise_sha256"]
    assert state["status"] == "proof_failed"
    assert state["next_action"] == "repair_visual_premise"


def test_explicit_targetless_generation_preserves_legacy_input_hashes(tmp_path: Path):
    package = _package(tmp_path)
    before = build_generation_inputs(package)
    _operation(package, "generate")
    assert build_generation_inputs(package) == before


def test_editing_approved_proof_revokes_creator_approval(tmp_path: Path):
    package, source, handoff = _prepared(tmp_path)
    _png(source, (1086, 1448), "linen")
    _ingest(package, source, _records(package, source, handoff))
    qa = package / "proof-qa.json"
    qa.write_text(json.dumps(_authored_qa(package, [2])))
    state = runtime.review_quarantined_outputs(package, qa_path=qa)
    assert state["status"] == "awaiting_creator_proof_approval"
    runtime.approve_proof(
        package,
        approved_by="Creator",
        proof_sha256=runtime.current_proof_binding_sha256(package),
    )
    _operation(package, "edit", color="plum")
    state = runtime.prepare_codex_builtin_image_generation(package, proof_slide=2)
    assert state["status"] == "handoff_ready"
    assert state["slides"]["2"]["attempts"] == 1
    assert not runtime._proof_approved(package, state)


@pytest.mark.parametrize("attack", ["missing_target", "missing_source", "duplicate_slide", "generate_with_target"])
def test_prepare_validates_entire_operation_batch_before_mutating(tmp_path: Path, attack: str):
    package = _package(tmp_path)
    source = _png(tmp_path / "edit-source.png", (1080, 1440), "tan")
    operations = [{"slide": 2, "intent": "edit", "targets": {"instagram_post": str(source)}}]
    if attack == "missing_target":
        operations.append({"slide": 3, "intent": "edit", "targets": {}})
    elif attack == "missing_source":
        operations.append({"slide": 3, "intent": "edit", "targets": {"instagram_post": str(tmp_path / "absent.png")}})
    elif attack == "duplicate_slide":
        operations.append(deepcopy(operations[0]))
    else:
        operations.append({"slide": 3, "intent": "generate", "targets": {"instagram_post": str(source)}})
    before = _snapshot(package)
    with pytest.raises(ValueError):
        runtime.prepare_codex_builtin_image_generation(package, proof_slide=2, image_operations=operations)
    assert _snapshot(package) == before


def test_prepare_copies_edit_target_before_source_changes(tmp_path: Path):
    package = _package(tmp_path)
    source = _png(tmp_path / "editable.png", (1080, 1440), "tan")
    original = source.read_bytes()
    runtime.prepare_codex_builtin_image_generation(
        package,
        proof_slide=2,
        image_operations=[{"slide": 2, "intent": "edit", "targets": {"instagram_post": str(source)}}],
    )
    handoff = _handoff(package)
    target = handoff["files"][0]["edit_target_binding"]
    bound_path = package / target["path"]
    assert bound_path.read_bytes() == original
    assert target["sha256"].removeprefix("sha256:") in bound_path.name
    assert str(bound_path.relative_to(package)).startswith(".internal/references/edit-targets/")
    _png(source, (1080, 1440), "plum")
    returned = _png(tmp_path / "returned.png", (1080, 1440), "salmon")
    state = _ingest(package, returned, _records(package, returned, handoff))
    assert state["status"] == "proof_qa_required"


def test_multiformat_edit_validates_every_return_before_any_ingestion(tmp_path: Path):
    package = _package(tmp_path)
    sizes = {"instagram_post": (1080, 1440), "square": (1080, 1080)}
    targets = {key: _png(tmp_path / f"target-{key}.png", size, "tan") for key, size in sizes.items()}
    runtime.prepare_codex_builtin_image_generation(
        package,
        proof_slide=2,
        formats=list(sizes),
        image_operations=[{"slide": 2, "intent": "edit", "targets": {key: str(path) for key, path in targets.items()}}],
    )
    handoff = _handoff(package)
    outputs, records = {}, []
    for file in handoff["files"]:
        key = file["format"]
        raw = _png(tmp_path / f"returned-{key}.png", sizes[key], "linen")
        outputs[key] = [raw]
        assert file["edit_target_binding"]["sha256"] == _sha(targets[key])
        records.extend(_records(package, raw, {"files": [file]}))
    records.reverse()  # Coverage is keyed by slide/format, not record-array position.
    tampered = deepcopy(records)
    tampered[-1]["returned_source_sha256"] = "sha256:" + "0" * 64
    before = _snapshot(package)
    with pytest.raises(ValueError):
        runtime.ingest_generated_outputs(package, outputs, invocation_records=tampered)
    assert _snapshot(package) == before
    state = runtime.ingest_generated_outputs(package, outputs, invocation_records=records)
    assert state["status"] == "proof_qa_required"
    invocations = state["slides"]["2"]["attempt_history"][-1]["invocations"]
    assert {item["format"] for item in invocations} == set(sizes)


def test_old_receipt_read_is_byte_stable_and_does_not_invent_invocation(tmp_path: Path):
    package, source, handoff = _prepared(tmp_path)
    _ingest(package, source, _records(package, source, handoff))
    # A pre-maintenance v3 receipt is the same old schema with no invocation key.
    state_path = package / "generation-state.json"
    state = json.loads(state_path.read_text())
    receipt = state["slides"]["2"]["attempt_history"][0]
    receipt.pop("invocations", None)
    state_path.write_text(json.dumps(state, indent=4) + "\n")
    before = _snapshot(package)
    read = runtime.read_generation_state(package)
    assert "invocations" not in read["slides"]["2"]["attempt_history"][0]
    assert _snapshot(package) == before
    compacted = write_v3_state(package, read)
    assert "invocations" not in compacted["slides"]["2"]["attempt_history"][0]


@pytest.mark.parametrize("intent", ["generate", "edit"])
def test_operator_record_survives_compaction_and_keeps_raw_return_hash(tmp_path: Path, intent: str):
    package, source, handoff = _prepared(tmp_path, intent)
    records = _records(package, source, handoff)
    records[0].update({"tool_call_id": "exposed-call-123", "model": "exposed-model-id"})
    state = _ingest(package, source, records)
    receipt = state["slides"]["2"]["attempt_history"][0]
    evidence = receipt["invocations"]
    assert evidence == [{"evidence": "operator_recorded", **records[0]}]
    assert receipt["pixel_review_status"] == "pending"
    assert receipt["approval_status"] == "pending"
    candidate = _candidate(package, 2, 1)
    assert candidate["generation_receipt"]["invocations"] == evidence
    assert evidence[0]["returned_source_sha256"] == candidate["source_evidence"]["instagram_post"]["sha256"]
    assert evidence[0]["returned_source_sha256"] != candidate["native_outputs"]["instagram_post"]["sha256"]
    compacted = write_v3_state(package, state)
    assert compacted["slides"]["2"]["attempt_history"][0]["invocations"] == evidence


def test_invocation_survives_proof_approval_and_final_promotion(tmp_path: Path):
    package, source, handoff = _prepared(tmp_path, "edit")
    _png(source, (1086, 1448), "linen")
    records = _records(package, source, handoff)
    _ingest(package, source, records)
    (package / "proof-qa.json").write_text(json.dumps(_authored_qa(package, [2])))
    state = runtime.review_quarantined_outputs(package)
    assert state["status"] == "awaiting_creator_proof_approval"
    runtime.approve_proof(package, approved_by="Creator", proof_sha256=runtime.current_proof_binding_sha256(package))
    runtime.prepare_codex_builtin_image_generation(package)
    batch = _handoff(package)
    paths, calls = [], []
    for item in batch["files"]:
        raw = _png(tmp_path / f"batch-{item['slide']}.png", (1080, 1440), "linen")
        paths.append(raw)
        calls.extend(_records(package, raw, {"files": [item]}))
    runtime.ingest_generated_outputs(package, {"instagram_post": paths}, invocation_records=calls)
    (package / "visual-qa.json").write_text(json.dumps(_authored_qa(package, [1, 2, 3, 4])))
    runtime.review_quarantined_outputs(package)
    final = runtime.finalize_codex_builtin_outputs(package)
    assert final["status"] == "publish_ready"
    expected = {call["slide"]: {"evidence": "operator_recorded", **call} for call in records + calls}
    for number, slide in final["slides"].items():
        assert slide["attempt_history"][-1]["invocations"] == [expected[int(number)]]
        assert slide["attempt_history"][-1]["promotion_status"] == "promoted"


def _patch_fixture(tmp_path: Path):
    module_path = Path(__file__).resolve().parents[1] / "tools/imagegen-skill-patch/manage.py"
    spec = importlib.util.spec_from_file_location("independent_imagegen_patch", module_path)
    assert spec and spec.loader
    manager = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(manager)
    _, payloads, _ = manager.load_package()
    target = tmp_path / "installed-imagegen"
    target.mkdir()
    for name, (before, _) in payloads.items():
        if before is not None:
            path = target / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(before)
    (target / "unrelated.txt").write_bytes(b"must survive")
    return manager, target, tmp_path / "outside-backups"


def test_patch_refuses_existing_drift_without_writing_target_or_backup(tmp_path: Path):
    manager, target, backup = _patch_fixture(tmp_path)
    (target / "SKILL.md").write_bytes(b"creator edited installed skill")
    before = _snapshot(target)
    with pytest.raises(manager.PatchError, match="drift"):
        manager.manage("apply", target, backup)
    assert _snapshot(target) == before
    assert not backup.exists()


def test_patch_observes_replace_then_failure_and_can_guardedly_roll_back(tmp_path: Path, monkeypatch):
    manager, target, backup = _patch_fixture(tmp_path)
    before = _snapshot(target)
    original_write = manager.atomic_write
    failed = False
    def fail_after_replacement(path, data, mode=None):
        nonlocal failed
        original_write(path, data, mode)
        if path == target / "SKILL.md" and not failed:
            failed = True
            raise OSError("injected after-replacement failure")
    monkeypatch.setattr(manager, "atomic_write", fail_after_replacement)
    with pytest.raises(manager.PatchError, match="interrupted"):
        manager.manage("apply", target, backup)
    report = manager.manage("check", target, backup)
    assert report["status"] == "partial"
    receipt = json.loads((Path(report["backup"]) / "receipt.json").read_text())
    assert receipt["status"] == "apply_failed"
    assert receipt["states"]["SKILL.md"] == "after"
    monkeypatch.setattr(manager, "atomic_write", original_write)
    assert manager.manage("rollback", target, backup)["status"] == "baseline"
    assert _snapshot(target) == before


def test_patch_rollback_refuses_new_drift_and_preserves_backup(tmp_path: Path):
    manager, target, backup = _patch_fixture(tmp_path)
    report = manager.manage("apply", target, backup)
    (target / "SKILL.md").write_bytes(b"later creator edit")
    before_target = _snapshot(target)
    before_backup = _snapshot(Path(report["backup"]))
    with pytest.raises(manager.PatchError, match="drift"):
        manager.manage("rollback", target, backup)
    assert _snapshot(target) == before_target
    assert _snapshot(Path(report["backup"])) == before_backup


@pytest.mark.parametrize("collision", ["original", "derivative"])
def test_paid_cli_output_collision_keeps_response_without_retry(tmp_path: Path, monkeypatch, collision: str):
    manager, _, _ = _patch_fixture(tmp_path)
    _, payloads, _ = manager.load_package()
    cli_path = tmp_path / "patched-image-gen.py"
    cli_path.write_bytes(payloads["scripts/image_gen.py"][1])
    spec = importlib.util.spec_from_file_location("independent_imagegen_cli", cli_path)
    assert spec and spec.loader
    cli = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(cli)
    parser = argparse.ArgumentParser()
    cli._add_shared_args(parser)
    output = tmp_path / "final.png"
    recovery_root = tmp_path / "recovery"
    args = parser.parse_args([
        "--prompt", "Offline collision fixture", "--out", str(output),
        "--recovery-dir", str(recovery_root), "--downscale-max-dim", "16",
    ])
    returned = _png(tmp_path / "server-fixture.png", (32, 32), "linen").read_bytes()
    collided = output if collision == "original" else cli._derive_downscale_path(output, args.downscale_suffix)
    calls = []
    def fake_generate(**payload):
        calls.append(payload)
        collided.write_bytes(b"concurrent creator file")
        return SimpleNamespace(data=[SimpleNamespace(b64_json=base64.b64encode(returned).decode())])
    monkeypatch.setattr(cli, "_create_client", lambda: SimpleNamespace(images=SimpleNamespace(generate=fake_generate)))
    with pytest.raises(cli.OutputWriteError, match="retained"):
        cli._generate(args)
    assert len(calls) == 1
    assert collided.read_bytes() == b"concurrent creator file"
    recovery, = recovery_root.iterdir()
    assert (recovery / "original-001.png").read_bytes() == returned
    assert json.loads((recovery / "response.json").read_text()) == [base64.b64encode(returned).decode()]
    receipt = json.loads((recovery / "recovery.json").read_text())
    assert receipt["status"] == "promotion_failed"
    assert receipt["promoted"] == ([] if collision == "original" else [str(output)])
