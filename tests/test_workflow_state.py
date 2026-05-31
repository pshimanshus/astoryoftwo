"""Tests for the workflow-runner typed contracts."""

from __future__ import annotations

import pytest

from pipeline.agentic.contracts import (
    PauseRequest,
    RepairBudget,
    RunArtifact,
    WorkflowGate,
    WorkflowRun,
    WorkflowStateRecord,
)


def test_repair_budget_increments_immutably() -> None:
    budget = RepairBudget(max_retries=2)
    assert budget.retries_used == 0
    next_budget = budget.increment()
    assert budget.retries_used == 0  # original unchanged
    assert next_budget.retries_used == 1


def test_repair_budget_exhausts_at_max_retries() -> None:
    budget = RepairBudget(max_retries=2)
    assert budget.exhausted is False
    after_one = budget.increment()
    assert after_one.exhausted is False
    after_two = after_one.increment()
    assert after_two.exhausted is True


def test_repair_budget_rejects_negative_max_retries() -> None:
    with pytest.raises(ValueError):
        RepairBudget(max_retries=-1)


def test_run_artifact_records_path_and_kind() -> None:
    artifact = RunArtifact(name="slides.md", path="/tmp/pkg/slides.md", kind="output")
    assert artifact.kind == "output"
    assert artifact.name == "slides.md"
    assert artifact.written_at  # auto-populated timestamp


def test_run_artifact_rejects_unknown_kind() -> None:
    with pytest.raises(ValueError):
        RunArtifact(name="x", path="/tmp/x", kind="not_a_real_kind")


def test_pause_request_rejects_unknown_awaiting_value() -> None:
    with pytest.raises(ValueError):
        PauseRequest(
            state="awaiting_concept_lock",
            reason="test",
            awaiting="not_a_real_pause",
            summary_path="/tmp/x",
            resume_hint="x",
        )


def test_workflow_state_record_collects_gates() -> None:
    record = WorkflowStateRecord(state="proof_generation")
    record.gates.append(WorkflowGate(name="palette", status="PASS"))
    record.gates.append(
        WorkflowGate(name="ocr_text", status="FAIL", reason="text drift")
    )
    assert [g.status for g in record.gates] == ["PASS", "FAIL"]
    assert record.repair_budget.exhausted is False  # default budget
    assert record.pause is None
    assert record.entered_at  # auto-populated
    assert record.exited_at is None


def test_workflow_run_detects_paused_state() -> None:
    run = WorkflowRun(
        run_id="r1",
        system="carousel_jam",
        package_dir="/tmp/pkg",
        current_state="awaiting_concept_lock",
        history=[
            WorkflowStateRecord(
                state="awaiting_concept_lock",
                pause=PauseRequest(
                    state="awaiting_concept_lock",
                    reason="three concept routes ready",
                    awaiting="concept_lock",
                    summary_path="/tmp/pkg/concept.md",
                    resume_hint="reply 'lock route N'",
                ),
            )
        ],
    )

    assert run.is_paused() is True
    pause = run.latest_pause()
    assert pause is not None
    assert pause.awaiting == "concept_lock"
    assert pause.summary_path == "/tmp/pkg/concept.md"


def test_workflow_run_not_paused_when_history_empty() -> None:
    run = WorkflowRun(
        run_id="r2",
        system="carousel_jam",
        package_dir="/tmp/pkg",
        current_state="session_start",
    )
    assert run.is_paused() is False
    assert run.latest_pause() is None


def test_workflow_run_not_paused_when_last_record_has_no_pause() -> None:
    run = WorkflowRun(
        run_id="r3",
        system="carousel_jam",
        package_dir="/tmp/pkg",
        current_state="copy_generation",
        history=[WorkflowStateRecord(state="raw_scene_lock", exited_at="2026-05-31T10:00:00+00:00")],
    )
    assert run.is_paused() is False
    assert run.latest_pause() is None


def test_workflow_run_round_trips_through_json() -> None:
    run = WorkflowRun(
        run_id="r4",
        system="carousel_jam",
        package_dir="/tmp/pkg",
        current_state="proof_generation",
        history=[
            WorkflowStateRecord(
                state="prompt_compile",
                gates=[WorkflowGate(name="prompt_constraints", status="PASS")],
            ),
        ],
        artifacts=[
            RunArtifact(name="prompts/slide-01.txt", path="/tmp/pkg/prompts/slide-01.txt", kind="output"),
        ],
    )

    raw = run.model_dump_json()
    reconstructed = WorkflowRun.model_validate_json(raw)

    assert reconstructed.run_id == run.run_id
    assert reconstructed.current_state == run.current_state
    assert len(reconstructed.history) == 1
    assert reconstructed.history[0].gates[0].status == "PASS"
    assert reconstructed.artifacts[0].kind == "output"
