from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from evals.schemas import CheckResult, EvalTask


SEVERITY_WEIGHTS = {
    "critical": 1.0,
    "major": 0.5,
    "minor": 0.1,
    "info": 0.0,
}


@dataclass(frozen=True)
class EvalReport:
    task_id: str
    resolved: bool
    score: float
    summary: dict[str, int]
    checks: list[CheckResult]

    def to_dict(self) -> dict[str, Any]:
        return {
            "task_id": self.task_id,
            "resolved": self.resolved,
            "score": self.score,
            "summary": self.summary,
            "checks": [check.to_dict() for check in self.checks],
        }


def score_checks(task: EvalTask, checks: list[CheckResult]) -> EvalReport:
    failures = [check for check in checks if check.status == "FAIL"]
    critical = sum(check.severity == "critical" for check in failures)
    major = sum(check.severity == "major" for check in failures)
    minor = sum(check.severity == "minor" for check in failures)
    pending = sum(check.status == "PENDING" for check in checks)
    penalty = sum(SEVERITY_WEIGHTS.get(check.severity, 0.0) for check in failures)
    total = max(1, len(checks))
    score = max(0.0, round(1.0 - (penalty / total), 4))
    criteria = task.pass_criteria
    resolved = (
        critical <= criteria.critical_failures_allowed
        and major <= criteria.major_failures_allowed
        and minor <= criteria.minor_failures_allowed
        and score >= criteria.minimum_score
        and pending == 0
    )
    return EvalReport(
        task_id=task.id,
        resolved=resolved,
        score=score,
        summary={
            "checks": len(checks),
            "failures": len(failures),
            "critical_failures": critical,
            "major_failures": major,
            "minor_failures": minor,
            "pending_reviews": pending,
        },
        checks=checks,
    )
