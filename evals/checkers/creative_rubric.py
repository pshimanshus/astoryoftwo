from __future__ import annotations

from pathlib import Path

from evals.schemas import CheckResult


FRAMEWORK_TERMS = (
    "Story-Selling",
    "Golden Theme",
    "Stage-Scene Gate",
    "28/30",
    "rubric",
    "selector verdict",
)


def check_creator_visible_copy(path: Path) -> list[CheckResult]:
    if not path.exists():
        return [
            CheckResult(
                code="creator_visible_copy",
                status="FAIL",
                severity="critical",
                message=f"Missing creator-visible copy artifact: {path}",
            )
        ]
    text = path.read_text(encoding="utf-8")
    leaked = [term for term in FRAMEWORK_TERMS if term in text]
    if leaked:
        return [
            CheckResult(
                code="creator_visible_framework_language",
                status="FAIL",
                severity="major",
                message="Creator-visible copy leaks internal framework language.",
                evidence=leaked,
            )
        ]
    return [
        CheckResult(
            code="creator_visible_framework_language",
            status="PASS",
            severity="info",
            message="No internal framework terms found in creator-visible copy.",
        )
    ]
