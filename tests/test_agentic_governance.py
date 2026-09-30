from __future__ import annotations

import json
from pathlib import Path

import pytest

from pipeline.agentic.learning_loop import (
    apply_learning_proposal,
    approve_learning_proposal,
    capture_learning_event,
    create_learning_proposal,
)
from pipeline.agentic.validator_registry import (
    receipt_path,
    run_required_validators,
)


def _proposal(root: Path) -> tuple[Path, Path]:
    target = root / "config" / "skills" / "alpha.md"
    target.parent.mkdir(parents=True)
    target.write_text("before\n", encoding="utf-8")
    event = capture_learning_event(root, source="test", summary="A bounded learning.")
    proposal_path = create_learning_proposal(
        root,
        source_event_id=event.event_id,
        target_path="config/skills/alpha.md",
        proposed_action="modify",
        rationale="Update an approved skill surface.",
        proposed_content="after\n",
        required_validators=["skill_eval"],
    )
    return target, proposal_path


def test_apply_requires_a_persisted_hash_bound_validator_receipt(tmp_path: Path):
    target, proposal_path = _proposal(tmp_path)

    with pytest.raises(ValueError, match="missing passing validator receipt"):
        apply_learning_proposal(tmp_path, proposal_path, approved_by="creator")

    receipts = run_required_validators(tmp_path, proposal_path)
    assert receipts[0]["status"] == "PASS"
    receipt = json.loads(
        receipt_path(tmp_path, receipts[0]["binding"]["proposal_id"], "skill_eval").read_text(
            encoding="utf-8"
        )
    )
    assert receipt["binding"]["after_hash"] == receipts[0]["binding"]["after_hash"]

    applied = apply_learning_proposal(tmp_path, proposal_path, approved_by="creator")
    assert target.read_text(encoding="utf-8") == "after\n"
    assert applied["validator_receipts"] == [receipts[0]["receipt_path"]]


def test_receipt_is_rejected_after_target_changes(tmp_path: Path):
    target, proposal_path = _proposal(tmp_path)
    run_required_validators(tmp_path, proposal_path)
    target.write_text("changed by another editor\n", encoding="utf-8")

    with pytest.raises(ValueError, match="target changed since proposal creation"):
        apply_learning_proposal(tmp_path, proposal_path, approved_by="creator")


def test_apply_enforces_target_scoped_approval_authority(tmp_path: Path):
    target = tmp_path / "pipeline" / "agentic" / "target.py"
    target.parent.mkdir(parents=True)
    target.write_text("before\n", encoding="utf-8")
    event = capture_learning_event(tmp_path, source="test", summary="Code-surface learning.")
    proposal_path = create_learning_proposal(
        tmp_path,
        source_event_id=event.event_id,
        target_path="pipeline/agentic/target.py",
        proposed_action="modify",
        rationale="Repair runtime behavior.",
        proposed_content="after\n",
        required_validators=["skill_eval"],
    )
    run_required_validators(tmp_path, proposal_path)

    with pytest.raises(ValueError, match="cannot apply changes"):
        apply_learning_proposal(tmp_path, proposal_path, approved_by="creator")

    applied = apply_learning_proposal(tmp_path, proposal_path, approved_by="maintainer")
    assert applied["approval_authority"] == "maintainer"


def test_unknown_validator_is_rejected_at_proposal_creation(tmp_path: Path):
    target = tmp_path / "config" / "skills" / "alpha.md"
    target.parent.mkdir(parents=True)
    target.write_text("before\n", encoding="utf-8")
    event = capture_learning_event(tmp_path, source="test", summary="Bad validator request.")

    with pytest.raises(ValueError, match="non-allow-listed"):
        create_learning_proposal(
            tmp_path,
            source_event_id=event.event_id,
            target_path="config/skills/alpha.md",
            proposed_action="modify",
            rationale="Try an untrusted command.",
            proposed_content="after\n",
            required_validators=["shell_command"],
        )


def test_protected_target_authority_wins_over_broad_maintainer_glob(tmp_path: Path):
    target, proposal_path = _proposal(tmp_path)
    run_required_validators(tmp_path, proposal_path)

    with pytest.raises(ValueError, match="cannot apply changes"):
        apply_learning_proposal(tmp_path, proposal_path, approved_by="maintainer")

    assert target.read_text(encoding="utf-8") == "before\n"


def test_hash_bound_creator_approval_rejects_revalidated_new_artifact(tmp_path: Path):
    target, proposal_path = _proposal(tmp_path)
    run_required_validators(tmp_path, proposal_path)
    approve_learning_proposal(tmp_path, proposal_path, approved_by="creator")
    proposal = json.loads(proposal_path.read_text(encoding="utf-8"))
    content_path = tmp_path / proposal["proposed_content_path"]
    content_path.write_text("different after approval\n", encoding="utf-8")
    import hashlib

    proposal["after_hash"] = hashlib.sha256(content_path.read_bytes()).hexdigest()
    proposal_path.write_text(json.dumps(proposal), encoding="utf-8")
    run_required_validators(tmp_path, proposal_path)

    with pytest.raises(ValueError, match="approval evidence is .*stale"):
        apply_learning_proposal(tmp_path, proposal_path, approved_by="creator")

    assert target.read_text(encoding="utf-8") == "before\n"


def test_validator_receipt_rejects_changed_validator_contract(tmp_path: Path):
    _, proposal_path = _proposal(tmp_path)
    run_required_validators(tmp_path, proposal_path)
    registry_path = tmp_path / "config" / "agentic_validator_registry.json"
    registry_path.parent.mkdir(parents=True, exist_ok=True)
    registry_path.write_text(
        json.dumps(
            {
                "schema_version": "1.0",
                "validators": {
                    "skill_eval": {
                        "executor": "skill_eval",
                        "contract_version": "skill-eval/v2",
                        "description": "changed contract",
                    }
                },
            }
        ),
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="stale validator contract receipt"):
        apply_learning_proposal(tmp_path, proposal_path, approved_by="creator")


def test_creator_workflow_validator_checks_real_source_event(tmp_path: Path):
    target = tmp_path / "config" / "skills" / "alpha.md"
    target.parent.mkdir(parents=True)
    target.write_text("before\n", encoding="utf-8")
    proposal_path = create_learning_proposal(
        tmp_path,
        source_event_id="missing-event",
        target_path="config/skills/alpha.md",
        proposed_action="modify",
        rationale="A claimed creator workflow update.",
        proposed_content="after\n",
        required_validators=["skill_eval", "creator_workflow_contract"],
    )

    receipts = run_required_validators(tmp_path, proposal_path)

    assert receipts[0]["status"] == "FAIL"
    assert "existing source learning event" in " ".join(receipts[0]["issues"])


def test_docs_validator_rejects_retired_prepost_orchestration(tmp_path: Path):
    target = tmp_path / "config" / "skill-systems.json"
    target.parent.mkdir(parents=True)
    target.write_text('{"systems": {}}\n', encoding="utf-8")
    event = capture_learning_event(tmp_path, source="test", summary="Workflow update")
    proposal_path = create_learning_proposal(
        tmp_path,
        source_event_id=event.event_id,
        target_path="config/skill-systems.json",
        proposed_action="modify",
        rationale="Try to restore an obsolete runtime.",
        proposed_content=json.dumps(
            {"systems": {"prepost_reel": {"specialist_agent_count": 5}}}
        ),
        required_validators=["agentic_docs_contract"],
    )

    receipts = run_required_validators(tmp_path, proposal_path)

    assert receipts[0]["status"] == "FAIL"
    assert "retired specialist-agent contract" in " ".join(receipts[0]["issues"])


def _source_bound_proposal(root: Path) -> tuple[Path, Path, Path, Path]:
    target = root / "config" / "skills" / "alpha.md"
    target.parent.mkdir(parents=True)
    target.write_text("before\n", encoding="utf-8")
    evidence = root / "evidence" / "review.md"
    evidence.parent.mkdir(parents=True)
    evidence.write_text("source fact\n", encoding="utf-8")
    event = capture_learning_event(
        root,
        source="reviewed_observation",
        summary="A source-bound learning.",
        evidence_paths=["evidence/review.md"],
    )
    event_path = (
        root / "memory" / "agentic" / "learning-events" / f"{event.event_id}.json"
    )
    proposal_path = create_learning_proposal(
        root,
        source_event_id=event.event_id,
        target_path="config/skills/alpha.md",
        proposed_action="modify",
        rationale="Persist the reviewed observation.",
        proposed_content="after\n",
        required_validators=["skill_eval", "creator_workflow_contract"],
    )
    return target, proposal_path, event_path, evidence


def test_receipt_binds_source_event_and_evidence_hashes(tmp_path: Path):
    _, proposal_path, event_path, evidence = _source_bound_proposal(tmp_path)

    receipts = run_required_validators(tmp_path, proposal_path)

    creator_receipt = next(
        item for item in receipts if item["validator_id"] == "creator_workflow_contract"
    )
    assert creator_receipt["status"] == "PASS"
    artifacts = creator_receipt["dependencies"]["artifacts"]
    assert [item["path"] for item in artifacts] == [
        event_path.relative_to(tmp_path).as_posix(),
        evidence.relative_to(tmp_path).as_posix(),
    ]
    assert all(item["state"] == "file" and item["sha256"] for item in artifacts)


@pytest.mark.parametrize("mutation", ["delete_event", "change_event", "change_evidence"])
def test_apply_rejects_stale_validator_source_dependencies(
    tmp_path: Path,
    mutation: str,
):
    target, proposal_path, event_path, evidence = _source_bound_proposal(tmp_path)
    run_required_validators(tmp_path, proposal_path)
    if mutation == "delete_event":
        event_path.unlink()
    elif mutation == "change_event":
        event = json.loads(event_path.read_text(encoding="utf-8"))
        event["summary"] = "Changed after validation."
        event_path.write_text(json.dumps(event), encoding="utf-8")
    else:
        evidence.write_text("changed source fact\n", encoding="utf-8")

    with pytest.raises(ValueError, match="stale validator dependency receipt"):
        apply_learning_proposal(tmp_path, proposal_path, approved_by="creator")

    assert target.read_text(encoding="utf-8") == "before\n"


def test_creator_workflow_validator_rejects_symlink_evidence(tmp_path: Path):
    _, proposal_path, _, evidence = _source_bound_proposal(tmp_path)
    outside = tmp_path.parent / f"{tmp_path.name}-outside-evidence.md"
    outside.write_text("outside\n", encoding="utf-8")
    evidence.unlink()
    evidence.symlink_to(outside)

    receipts = run_required_validators(tmp_path, proposal_path)

    creator_receipt = next(
        item for item in receipts if item["validator_id"] == "creator_workflow_contract"
    )
    assert creator_receipt["status"] == "FAIL"
    assert "must not traverse a symlink" in " ".join(creator_receipt["issues"])
