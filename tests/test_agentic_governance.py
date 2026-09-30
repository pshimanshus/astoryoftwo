from __future__ import annotations

import json
from pathlib import Path

import pytest

from pipeline.agentic.learning_loop import (
    apply_learning_proposal,
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
