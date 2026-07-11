from __future__ import annotations

from pathlib import Path

from evals.schemas import CheckResult
from pipeline.agentic.carousel_state import derive_carousel_state
from pipeline.agentic.workflow_doctor import inspect_carousel_package


def check_carousel_package(package_dir: Path) -> list[CheckResult]:
    report = inspect_carousel_package(package_dir)
    state = derive_carousel_state(package_dir)
    results: list[CheckResult] = []

    if report.blocked:
        results.append(
            CheckResult(
                code="carousel_doctor",
                status="FAIL",
                severity="critical",
                message="Carousel doctor found blocker issues.",
                evidence=[issue.code for issue in report.issues],
            )
        )
    else:
        results.append(
            CheckResult(
                code="carousel_doctor",
                status="PASS",
                severity="info",
                message=f"Carousel doctor highest severity: {report.highest_severity}.",
            )
        )

    if state.publishable and state.blocked:
        results.append(
            CheckResult(
                code="carousel_state_contradiction",
                status="FAIL",
                severity="critical",
                message="Carousel state is both publishable and blocked.",
            )
        )
    else:
        results.append(
            CheckResult(
                code="carousel_state_contradiction",
                status="PASS",
                severity="info",
                message=f"Carousel state: {state.name}.",
            )
        )
    return results
