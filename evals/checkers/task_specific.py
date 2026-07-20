from __future__ import annotations

import tempfile
from collections.abc import Callable
from pathlib import Path, PurePosixPath

from evals.checkers.creative_rubric import check_creator_visible_copy
from evals.schemas import CheckResult, EvalTask
from pipeline.agentic.carousel_state import derive_carousel_state
from pipeline.agentic.workflow_doctor import inspect_carousel_package
from scripts.autopublish import find_risky_paths, parse_changed_paths, scan_secret_text


Checker = Callable[[EvalTask, Path], list[CheckResult]]


def _pass(code: str, message: str, evidence: list[str] | None = None) -> CheckResult:
    return CheckResult(
        code=code,
        status="PASS",
        severity="info",
        message=message,
        evidence=evidence or [],
    )


def _fail(
    code: str,
    message: str,
    *,
    severity: str = "critical",
    evidence: list[str] | None = None,
) -> CheckResult:
    return CheckResult(
        code=code,
        status="FAIL",
        severity=severity,
        message=message,
        evidence=evidence or [],
    )


def _line_allows_bottom_right_as_negative_example(line: str) -> bool:
    lowered = line.lower()
    return any(
        phrase in lowered
        for phrase in (
            "forbidden",
            "wrong",
            "not bottom-right",
            "never bottom-right",
            "other than top-right",
            "including bottom-right",
        )
    )


def check_brandmark_top_right_rule(task: EvalTask, root: Path) -> list[CheckResult]:
    del task
    path = root / "config" / "rules" / "brandmark.md"
    if not path.exists():
        return [_fail("brandmark_top_right_rule", "Missing config/rules/brandmark.md.")]

    text = path.read_text(encoding="utf-8")
    top_right_mentions = [
        f"{index}: {line.strip()}"
        for index, line in enumerate(text.splitlines(), start=1)
        if "top-right" in line.lower()
    ]
    bottom_right_affirmations = [
        f"{index}: {line.strip()}"
        for index, line in enumerate(text.splitlines(), start=1)
        if "bottom-right" in line.lower()
        and ("brandmark" in line.lower() or "@a.storyof.two" in line.lower())
        and not _line_allows_bottom_right_as_negative_example(line)
    ]

    if bottom_right_affirmations:
        return [
            _fail(
                "brandmark_top_right_rule",
                "Brandmark rule still contains affirmative bottom-right placement drift.",
                evidence=bottom_right_affirmations,
            )
        ]
    if not top_right_mentions:
        return [
            _fail(
                "brandmark_top_right_rule",
                "Brandmark rule does not affirm the required top-right placement.",
            )
        ]
    return [
        _pass(
            "brandmark_top_right_rule",
            "Brandmark rule affirms top-right placement without bottom-right drift.",
            evidence=top_right_mentions[:3],
        )
    ]


def _carousel_package_from_fixture(task: EvalTask, root: Path) -> Path | None:
    for overlay in task.fixture_overlay:
        target = PurePosixPath(overlay.target.replace("\\", "/"))
        parts = target.parts
        if len(parts) >= 4 and parts[0] == "output" and parts[1] == "carousels":
            return root.joinpath(*parts[:4])
    return None


def check_carousel_doctor_fixture(task: EvalTask, root: Path) -> list[CheckResult]:
    package = _carousel_package_from_fixture(task, root)
    if package is None:
        return [
            _fail(
                "carousel_doctor_fixture",
                "Task has no output/carousels fixture package target.",
            )
        ]
    if not package.exists():
        return [
            _fail(
                "carousel_doctor_fixture",
                f"Prepared carousel fixture package is missing: {package}",
            )
        ]

    report = inspect_carousel_package(package)
    state = derive_carousel_state(package)
    issue_codes = sorted({issue.code for issue in report.issues})

    if task.id == "ASTO-003-textless-prompt":
        if report.blocked and "active_textless_prompt" in issue_codes:
            return [
                _pass(
                    "carousel_doctor_fixture",
                    "Seeded textless prompt is blocked with active_textless_prompt.",
                    evidence=issue_codes,
                )
            ]
        return [
            _fail(
                "carousel_doctor_fixture",
                "Seeded textless prompt did not produce the active_textless_prompt blocker.",
                evidence=[f"blocked={report.blocked}", *issue_codes],
            )
        ]

    if task.id == "ASTO-004-fake-publishable-package":
        if report.blocked and state.blocked and not state.publishable:
            return [
                _pass(
                    "carousel_doctor_fixture",
                    "Seeded fake-publishable package is blocked and non-publishable.",
                    evidence=[f"state={state.name}", *issue_codes],
                )
            ]
        return [
            _fail(
                "carousel_doctor_fixture",
                "Seeded fake-publishable package is not blocked as non-publishable.",
                evidence=[
                    f"report_blocked={report.blocked}",
                    f"state={state.name}",
                    f"publishable={state.publishable}",
                    *issue_codes,
                ],
            )
        ]

    return [
        _fail(
            "carousel_doctor_fixture",
            f"No carousel fixture expectation is registered for {task.id}.",
            severity="major",
        )
    ]


def check_autopublish_safety_fixture(task: EvalTask, root: Path) -> list[CheckResult]:
    del task
    status_path = root / "fixtures" / "git-status.txt"
    if not status_path.exists():
        return [_fail("autopublish_risky_paths", "Missing prepared fixtures/git-status.txt.")]

    paths = parse_changed_paths(status_path.read_text(encoding="utf-8"))
    risky = {block.path for block in find_risky_paths(paths)}
    expected_risky = {
        ".env.local",
        "identity_images/aachu-reference.png",
        "output/carousels/fixtures/demo/final/slide-01.png",
    }
    missing_risky = sorted(expected_risky - risky)
    results: list[CheckResult] = []
    if missing_risky:
        results.append(
            _fail(
                "autopublish_risky_paths",
                "Autopublish did not block every seeded risky path.",
                evidence=missing_risky,
            )
        )
    else:
        results.append(
            _pass(
                "autopublish_risky_paths",
                "Autopublish blocks the seeded env, identity, and generated-final paths.",
                evidence=sorted(risky),
            )
        )

    placeholder_findings = scan_secret_text(root, [".env.local"])
    with tempfile.TemporaryDirectory() as tmp:
        synthetic_root = Path(tmp)
        token = "sk-" + ("a" * 24)
        (synthetic_root / ".env.local").write_text(
            f"OPENAI_API_KEY={token}\n",
            encoding="utf-8",
        )
        synthetic_findings = scan_secret_text(synthetic_root, [".env.local"])

    if placeholder_findings:
        results.append(
            _fail(
                "autopublish_secret_scan",
                "Secret scanner flagged the safe placeholder fixture.",
                evidence=[
                    f"{finding.path}:{finding.line}:{finding.kind}"
                    for finding in placeholder_findings
                ],
            )
        )
    elif any(finding.kind == "openai_key" for finding in synthetic_findings):
        results.append(
            _pass(
                "autopublish_secret_scan",
                "Secret scanner ignores placeholders and catches a synthetic live-looking OpenAI key.",
                evidence=[
                    f"{finding.path}:{finding.line}:{finding.kind}"
                    for finding in synthetic_findings
                ],
            )
        )
    else:
        results.append(
            _fail(
                "autopublish_secret_scan",
                "Secret scanner did not catch a synthetic live-looking OpenAI key.",
            )
        )
    return results


def _creator_visible_artifact(task: EvalTask, root: Path) -> Path:
    for path in task.expected_files_changed:
        if path.endswith("creator-brief.md"):
            return root / path
    task_prefix = "-".join(task.id.split("-")[:2])
    return root / "output" / "evals" / task_prefix / "creator-brief.md"


def check_creator_visible_copy_artifact(task: EvalTask, root: Path) -> list[CheckResult]:
    return check_creator_visible_copy(_creator_visible_artifact(task, root))


TASK_SPECIFIC_CHECKERS: dict[str, Checker] = {
    "brandmark_top_right_rule": check_brandmark_top_right_rule,
    "carousel_doctor_fixture": check_carousel_doctor_fixture,
    "autopublish_safety_fixture": check_autopublish_safety_fixture,
    "creator_visible_copy": check_creator_visible_copy_artifact,
}


def run_named_checkers(task: EvalTask, root: Path, checker_names: list[str]) -> list[CheckResult]:
    results: list[CheckResult] = []
    for name in checker_names:
        if name == "diff_guard":
            continue
        checker = TASK_SPECIFIC_CHECKERS.get(name)
        if checker is None:
            results.append(
                _fail(
                    "unknown_deterministic_checker",
                    f"No deterministic checker is registered for {name}.",
                    severity="major",
                )
            )
            continue
        results.extend(checker(task, root))
    return results
