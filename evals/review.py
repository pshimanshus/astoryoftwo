from __future__ import annotations

import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

from evals.checkers.task_specific import run_named_checkers
from evals.fixtures import materialize_task_fixture
from evals.schemas import CheckResult, EvalTask


@dataclass(frozen=True)
class FixtureReview:
    task_id: str
    mode: str
    expected_outcome: str
    observed_outcome: str
    benchmark_setup: str
    certification_status: str
    aligned: bool
    checks: list[CheckResult]

    def to_dict(self) -> dict[str, Any]:
        return {
            "task_id": self.task_id,
            "mode": self.mode,
            "expected_outcome": self.expected_outcome,
            "observed_outcome": self.observed_outcome,
            "benchmark_setup": self.benchmark_setup,
            "certification_status": self.certification_status,
            "aligned": self.aligned,
            "checks": [check.to_dict() for check in self.checks],
        }


def review_task_fixture_once(task: EvalTask) -> FixtureReview:
    """Materialize and inspect one task exactly once.

    A solution fixture should be unresolved before the solver changes it. A
    regression fixture should be guarded by the current production validator.
    Regression fixtures need a separate hidden code mutation before they can
    award agent solve credit; this review only verifies their guard direction.
    """

    with tempfile.TemporaryDirectory(prefix=f"{task.id}-review-") as raw_dir:
        workspace = Path(raw_dir)
        materialize_task_fixture(task, workspace)
        checker_names = [
            name for name in task.deterministic_checkers if name != "diff_guard"
        ]
        checks = run_named_checkers(task, workspace, checker_names)

    observed = "unresolved" if any(check.status == "FAIL" for check in checks) else "guarded"
    expected = task.fixture_contract.expected_outcome
    return FixtureReview(
        task_id=task.id,
        mode=task.fixture_contract.mode,
        expected_outcome=expected,
        observed_outcome=observed,
        benchmark_setup=task.fixture_contract.benchmark_setup,
        certification_status=(
            "BASELINE_AND_GRADE_REQUIRED"
            if task.fixture_contract.mode == "solution"
            else "NOT_READY_WITHOUT_HIDDEN_MUTATION"
        ),
        aligned=observed == expected,
        checks=checks,
    )


def review_suite_once(tasks: Iterable[EvalTask]) -> dict[str, Any]:
    """Run one bounded, registry-ordered fixture-direction review."""

    frozen_tasks = list(tasks)
    reviews = [review_task_fixture_once(task) for task in frozen_tasks]
    issues = [
        f"{review.task_id}: expected {review.expected_outcome}, observed {review.observed_outcome}"
        for review in reviews
        if not review.aligned
    ]
    hidden_setup_required = sum(
        review.certification_status == "NOT_READY_WITHOUT_HIDDEN_MUTATION"
        for review in reviews
    )
    return {
        "status": "FAIL" if issues else "PASS",
        "review_protocol": "single_pass_registry_order",
        "reviewed_task_count": len(reviews),
        "visible_solution_fixture_count": len(reviews) - hidden_setup_required,
        "hidden_mutation_required_count": hidden_setup_required,
        "issues": issues,
        "tasks": [review.to_dict() for review in reviews],
    }
