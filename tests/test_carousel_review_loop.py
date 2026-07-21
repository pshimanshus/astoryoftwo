from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from pipeline.agentic.carousel_review_loop import (
    RepairResult,
    ReviewLoopConfig,
    run_review_loop,
)
from pipeline.agentic.carousel_state import CarouselState
from pipeline.agentic.workflow_doctor import WorkflowDoctorReport, WorkflowIssue


def _state(package: Path, *, publishable: bool, blocked: bool = False) -> CarouselState:
    return CarouselState(
        name="publishable" if publishable else "blocked" if blocked else "copy_locked",
        publishable=publishable,
        blocked=blocked,
        next_action="ready_for_closeout" if publishable else "repair_blockers",
        issue_codes=[],
        package_dir=str(package),
    )


def _issue(code: str, message: str = "Repair this package.") -> WorkflowIssue:
    return WorkflowIssue(
        code=code,
        severity="blocker",
        message=message,
        evidence=["artifact.json"],
        next_action="repair_blockers",
    )


def test_clean_publishable_package_exits_without_repair(tmp_path: Path) -> None:
    package = tmp_path / "clean"
    package.mkdir()
    repair_calls: list[int] = []

    result = run_review_loop(
        package,
        repo_root=tmp_path,
        config=ReviewLoopConfig(max_iterations=4),
        inspect_fn=lambda _: WorkflowDoctorReport(str(package), []),
        state_fn=lambda _: _state(package, publishable=True),
        repair_fn=lambda _package, _feedback, iteration: (
            repair_calls.append(iteration) or RepairResult(["repair"], 0)
        ),
    )

    assert result.status == "COMPLETE"
    assert result.iterations == 1
    assert repair_calls == []
    assert json.loads((package / ".internal/review-loop/summary.json").read_text())["complete"] is True


def test_review_feedback_repairs_then_rechecks_until_publishable(tmp_path: Path) -> None:
    package = tmp_path / "repairable"
    package.mkdir()
    phase = {"fixed": False}

    def inspect(_: Path) -> WorkflowDoctorReport:
        issues = [] if phase["fixed"] else [_issue("active_prompt_constraints_failed")]
        return WorkflowDoctorReport(str(package), issues)

    def state(_: Path) -> CarouselState:
        return _state(package, publishable=phase["fixed"], blocked=not phase["fixed"])

    def repair(_package: Path, feedback: Path, iteration: int) -> RepairResult:
        payload = json.loads(feedback.read_text(encoding="utf-8"))
        assert payload["effective_issues"][0]["code"] == "active_prompt_constraints_failed"
        assert iteration == 1
        phase["fixed"] = True
        return RepairResult(["repair"], 0, stdout="fixed")

    result = run_review_loop(
        package,
        repo_root=tmp_path,
        config=ReviewLoopConfig(max_iterations=4),
        inspect_fn=inspect,
        state_fn=state,
        repair_fn=repair,
    )

    assert result.status == "COMPLETE"
    assert result.iterations == 2
    events = [json.loads(line) for line in (package / ".internal/review-loop/trace.jsonl").read_text().splitlines()]
    assert [event["event"] for event in events] == ["verification", "repair", "verification"]


def test_human_approval_blocker_never_invokes_repair_agent(tmp_path: Path) -> None:
    package = tmp_path / "human"
    package.mkdir()
    repair_calls: list[int] = []
    report = WorkflowDoctorReport(
        str(package),
        [_issue("qa_pass_without_creator_approval", "QA-passed proof requires explicit creator approval.")],
    )

    result = run_review_loop(
        package,
        repo_root=tmp_path,
        config=ReviewLoopConfig(max_iterations=4),
        inspect_fn=lambda _: report,
        state_fn=lambda _: _state(package, publishable=False, blocked=True),
        repair_fn=lambda _package, _feedback, iteration: (
            repair_calls.append(iteration) or RepairResult(["repair"], 0)
        ),
    )

    assert result.status == "HUMAN_REQUIRED"
    assert repair_calls == []
    assert "qa_pass_without_creator_approval" in result.issue_codes


def test_repeated_identical_review_stops_as_stagnated_and_writes_proposal(tmp_path: Path) -> None:
    package = tmp_path / "stagnant"
    package.mkdir()
    repair_calls: list[int] = []
    report = WorkflowDoctorReport(str(package), [_issue("director_storyboard_failed")])

    def repair(_package: Path, _feedback: Path, iteration: int) -> RepairResult:
        repair_calls.append(iteration)
        return RepairResult(["repair"], 0, stdout="no effective change")

    result = run_review_loop(
        package,
        repo_root=tmp_path,
        config=ReviewLoopConfig(max_iterations=8, stagnation_limit=2),
        inspect_fn=lambda _: report,
        state_fn=lambda _: _state(package, publishable=False, blocked=True),
        repair_fn=repair,
    )

    assert result.status == "STAGNATED"
    assert result.iterations == 3
    assert repair_calls == [1, 2]
    proposal = json.loads((package / ".internal/review-loop/improvement-proposal.json").read_text())
    assert proposal["status"] == "DRAFT_FOR_HUMAN_REVIEW"
    assert "director_storyboard_failed" in proposal["recurring_issue_codes"]


def test_review_only_reports_failure_without_repairs(tmp_path: Path) -> None:
    package = tmp_path / "review-only"
    package.mkdir()
    result = run_review_loop(
        package,
        repo_root=tmp_path,
        config=ReviewLoopConfig(review_only=True),
        inspect_fn=lambda _: WorkflowDoctorReport(str(package), [_issue("missing_final_audit")]),
        state_fn=lambda _: _state(package, publishable=False, blocked=True),
        repair_fn=lambda *_: (_ for _ in ()).throw(AssertionError("repair should not run")),
    )

    assert result.status == "REVIEW_FAILED"


def test_cli_review_only_writes_machine_readable_trace(tmp_path: Path) -> None:
    package = tmp_path / "cli-review"
    package.mkdir()

    completed = subprocess.run(
        [sys.executable, "scripts/carousel_review_loop.py", str(package), "--review-only"],
        capture_output=True,
        text=True,
        check=False,
        timeout=30,
    )

    payload = json.loads(completed.stdout)
    assert completed.returncode == 2
    assert payload["status"] == "REVIEW_FAILED"
    assert payload["state"]["name"] == "draft"
    assert (package / ".internal/review-loop/feedback.json").exists()


def test_loop_is_routed_through_make_and_carousel_skill_system() -> None:
    makefile = Path("Makefile").read_text(encoding="utf-8")
    systems = json.loads(Path("config/skill-systems.json").read_text(encoding="utf-8"))
    components = systems["systems"]["carousel_jam"]["components"]
    gates = systems["systems"]["carousel_jam"]["gates"]

    assert "review-loop:" in makefile
    assert "scripts/carousel_review_loop.py" in makefile
    assert "config/skills/carousel-review-loop.md" in components
    assert "review_loop_converged" in gates
