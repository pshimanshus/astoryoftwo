"""Durable learning must remain backed by current package evidence."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from pipeline.agentic.learning_loop import (
    apply_learning_proposal,
    approve_learning_proposal,
    capture_learning_event,
    decline_learning_proposal,
    learning_debt_records,
)
from pipeline.stages.carousel_visual_storytelling import (
    apply_creator_feedback_revision,
    creator_feedback_records,
    record_creator_feedback,
)


def _write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload), encoding="utf-8")


def _package(root: Path, name: str) -> Path:
    path = root / "output" / "carousels" / "2026-09-05" / name
    _write_json(
        path / "generation-state.json",
        {
            "schema_version": "carousel-generation-state/v3",
            "status": "draft",
            "slides": {},
        },
    )
    _write_json(
        path / "slides.json",
        {
            "slides": [
                {"copy": "Locked words", "physical_action": "A posed portrait"},
                {"copy": "Preserve this slide"},
            ]
        },
    )
    return path


def _capture_and_revise(
    root: Path,
    package: Path,
    *,
    text: str,
) -> dict[str, object]:
    event = record_creator_feedback(
        package,
        workspace_root=root,
        user_instruction_exact=text,
        kind="correction",
        scope="slide",
        slide_numbers=[1],
        primary_diagnosis="scene_action",
        must_change=["Show the shared physical action."],
        must_preserve=["Keep the exact copy and unrelated slides."],
        repair_operations=[
            {
                "artifact": "slides.json",
                "json_pointer": "/slides/0/physical_action",
                "value": "Both partners pull the same table toward the window.",
            }
        ],
    )
    return apply_creator_feedback_revision(
        package,
        workspace_root=root,
        feedback_id=str(event["feedback_id"]),
    )


def _target(root: Path) -> Path:
    target = root / "config" / "rules" / "visual-variety.md"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text("# Visual variety\n\nconfidence: 0.9\n", encoding="utf-8")
    return target


def _make_stale(package: Path) -> None:
    slides = json.loads((package / "slides.json").read_text(encoding="utf-8"))
    slides["slides"][1]["copy"] = "Unrelated mutation after evaluation"
    _write_json(package / "slides.json", slides)


def test_approval_refuses_stale_source_feedback_evidence(tmp_path: Path) -> None:
    target = _target(tmp_path)
    package = _package(tmp_path, "source")
    result = _capture_and_revise(
        tmp_path,
        package,
        text="Always show a shared physical action.",
    )
    proposal = next(tmp_path.glob("memory/agentic/learning-proposals/*.json"))
    before = target.read_bytes()
    _make_stale(package)

    with pytest.raises(ValueError, match="stale or not passing"):
        approve_learning_proposal(
            tmp_path,
            proposal,
            approved_by="creator",
        )

    assert result["feedback"]["status"] == "learning_proposed"
    assert json.loads(proposal.read_text(encoding="utf-8"))["status"] == "draft"
    assert target.read_bytes() == before


def test_apply_rechecks_freshness_under_lock_after_approval(tmp_path: Path) -> None:
    target = _target(tmp_path)
    package = _package(tmp_path, "source")
    _capture_and_revise(
        tmp_path,
        package,
        text="Always show a shared physical action.",
    )
    proposal = next(tmp_path.glob("memory/agentic/learning-proposals/*.json"))
    approve_learning_proposal(tmp_path, proposal, approved_by="creator")
    before = target.read_bytes()
    _make_stale(package)

    with pytest.raises(ValueError, match="stale or not passing"):
        apply_learning_proposal(tmp_path, proposal, approved_by="creator")

    assert json.loads(proposal.read_text(encoding="utf-8"))["status"] == "approved"
    assert target.read_bytes() == before


def test_approval_validates_every_supporting_package_not_only_source(tmp_path: Path) -> None:
    _target(tmp_path)
    first = _package(tmp_path, "first")
    second = _package(tmp_path, "second")
    _capture_and_revise(
        tmp_path,
        first,
        text="Show a shared physical action in the scene.",
    )
    result = _capture_and_revise(
        tmp_path,
        second,
        text="Show a shared physical action in the scene.",
    )
    proposal = next(tmp_path.glob("memory/agentic/learning-proposals/*.json"))
    payload = json.loads(proposal.read_text(encoding="utf-8"))
    assert result["feedback"]["status"] == "learning_proposed"
    assert len(payload["supporting_event_ids"]) == 2
    assert len(payload["supporting_package_paths"]) == 2
    _make_stale(first)

    with pytest.raises(ValueError, match="stale or not passing"):
        approve_learning_proposal(tmp_path, proposal, approved_by="creator")


def test_decline_retry_converges_after_proposal_write_only_failure(tmp_path: Path) -> None:
    _target(tmp_path)
    package = _package(tmp_path, "source")
    result = _capture_and_revise(
        tmp_path,
        package,
        text="Always show a shared physical action.",
    )
    proposal = next(tmp_path.glob("memory/agentic/learning-proposals/*.json"))
    payload = json.loads(proposal.read_text(encoding="utf-8"))
    payload.update(
        {
            "status": "rejected",
            "decision": "declined",
            "declined_by": "codex-review",
            "declined_reason": "Package evidence does not justify a global rule.",
            "declined_at": "2026-09-05T00:00:00+00:00",
        }
    )
    _write_json(proposal, payload)

    first = decline_learning_proposal(
        tmp_path,
        proposal,
        declined_by="codex-review",
        reason="Package evidence does not justify a global rule.",
    )
    second = decline_learning_proposal(
        tmp_path,
        proposal,
        declined_by="codex-review",
        reason="Package evidence does not justify a global rule.",
    )
    feedback = creator_feedback_records(package)[0]

    assert result["feedback"]["status"] == "learning_proposed"
    assert first == second
    assert feedback["status"] == "evaluated"
    assert feedback["learning_disposition"] == "declined"


def test_langfuse_import_is_candidate_review_not_proposal_debt(tmp_path: Path) -> None:
    capture_learning_event(
        tmp_path,
        source="langfuse_annotation_candidate",
        event_id="event-langfuse-a1b2c3",
        summary="Reviewer noted a possible identity drift.",
        user_instruction_exact="The face may not match the reference.",
        eval_disposition="candidate_only",
        feedback_metadata={"external_annotation_id": "annotation-1"},
    )

    debt = learning_debt_records(tmp_path, limit=10)

    assert len(debt) == 1
    assert debt[0]["kind"] == "candidate_review"
    assert debt[0]["line"].startswith("review imported annotation")
    assert not list(tmp_path.glob("memory/agentic/learning-proposals/*.json"))
