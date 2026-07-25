"""Fail-closed review -> repair -> verify loop for carousel packages.

The loop is intentionally orchestration-only. The workflow doctor and optional
deterministic commands grade the current package; a repair runner receives only
their concrete feedback; the next iteration grades the package again. Human
approval, identity evidence, reviewer provenance, and generated pixels are
never fabricated to make the loop converge.
"""

from __future__ import annotations

import hashlib
import json
import shlex
import shutil
import subprocess
from collections.abc import Callable, Sequence
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from pipeline.agentic.carousel_state import CarouselState, derive_carousel_state
from pipeline.agentic.workflow_doctor import WorkflowDoctorReport, inspect_carousel_package


TRACE_SCHEMA_VERSION = "1.0"
TRACE_DIR = ".internal/review-loop"
HUMAN_REQUIRED_CODES = {
    "creator_approval_asset_hash_mismatch",
    "qa_pass_without_creator_approval",
    "blocked_visual_qa_terminal",
}
HUMAN_REQUIRED_MESSAGE_FRAGMENTS = (
    "explicit creator approval",
    "identity review is blocked or unverified",
    "requires human generation",
    "generation is unavailable",
    "missing identity reference",
)


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def _append_jsonl(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(payload, ensure_ascii=False) + "\n")


@dataclass(frozen=True)
class VerificationResult:
    command: list[str]
    returncode: int
    stdout: str = ""
    stderr: str = ""

    @property
    def passed(self) -> bool:
        return self.returncode == 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "command": self.command,
            "returncode": self.returncode,
            "passed": self.passed,
            "stdout": self.stdout[-12000:],
            "stderr": self.stderr[-12000:],
        }


@dataclass(frozen=True)
class RepairResult:
    command: list[str]
    returncode: int
    stdout: str = ""
    stderr: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "command": self.command,
            "returncode": self.returncode,
            "stdout": self.stdout[-20000:],
            "stderr": self.stderr[-20000:],
        }


@dataclass(frozen=True)
class ReviewLoopConfig:
    max_iterations: int = 12
    stagnation_limit: int = 3
    repair_command: tuple[str, ...] | None = None
    verify_commands: tuple[tuple[str, ...], ...] = ()
    review_only: bool = False
    command_timeout_seconds: int = 1800

    def __post_init__(self) -> None:
        if self.max_iterations < 1:
            raise ValueError("max_iterations must be at least 1")
        if self.stagnation_limit < 1:
            raise ValueError("stagnation_limit must be at least 1")
        if self.command_timeout_seconds < 1:
            raise ValueError("command_timeout_seconds must be at least 1")


@dataclass(frozen=True)
class ReviewLoopResult:
    status: str
    iterations: int
    package_dir: str
    state: dict[str, Any]
    issue_codes: list[str] = field(default_factory=list)
    reason: str = ""
    trace_dir: str = ""

    @property
    def complete(self) -> bool:
        return self.status == "COMPLETE"

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": TRACE_SCHEMA_VERSION,
            "status": self.status,
            "complete": self.complete,
            "iterations": self.iterations,
            "package_dir": self.package_dir,
            "state": self.state,
            "issue_codes": self.issue_codes,
            "reason": self.reason,
            "trace_dir": self.trace_dir,
        }


InspectFn = Callable[[Path], WorkflowDoctorReport]
StateFn = Callable[[Path], CarouselState]
RepairFn = Callable[[Path, Path, int], RepairResult]
VerifyFn = Callable[[Path, Sequence[Sequence[str]], int], list[VerificationResult]]


def parse_command(value: str) -> tuple[str, ...]:
    command = tuple(shlex.split(value))
    if not command:
        raise ValueError("command must not be empty")
    return command


def _expand_command(command: Sequence[str], package_dir: Path, feedback_path: Path) -> list[str]:
    values = {"package": str(package_dir), "feedback": str(feedback_path)}
    return [str(part).format(**values) for part in command]


def _command_cwd(package_dir: Path) -> Path:
    for candidate in (package_dir, *package_dir.parents):
        if (candidate / ".git").exists() or (candidate / "AGENTS.md").exists():
            return candidate
    return Path.cwd()


def run_verifiers(
    package_dir: Path,
    commands: Sequence[Sequence[str]],
    timeout_seconds: int,
) -> list[VerificationResult]:
    results: list[VerificationResult] = []
    for raw_command in commands:
        command = _expand_command(raw_command, package_dir, package_dir / TRACE_DIR / "feedback.json")
        try:
            completed = subprocess.run(
                command,
                cwd=_command_cwd(package_dir),
                capture_output=True,
                text=True,
                timeout=timeout_seconds,
                check=False,
            )
            results.append(
                VerificationResult(
                    command=command,
                    returncode=completed.returncode,
                    stdout=completed.stdout,
                    stderr=completed.stderr,
                )
            )
        except (OSError, subprocess.TimeoutExpired) as exc:
            results.append(VerificationResult(command=command, returncode=124, stderr=str(exc)))
    return results


def _default_codex_repair(
    repo_root: Path,
    package_dir: Path,
    feedback_path: Path,
    iteration: int,
    timeout_seconds: int,
) -> RepairResult:
    codex = shutil.which("codex")
    if not codex:
        return RepairResult(command=["codex"], returncode=127, stderr="Codex CLI is unavailable.")

    command = [
        codex,
        "exec",
        "--ephemeral",
        "-C",
        str(repo_root),
        "-s",
        "workspace-write",
        "-a",
        "never",
        "-",
    ]
    prompt = f"""Repair iteration {iteration} for this A Story of Two carousel package:
{package_dir}

Read the exact grader feedback at:
{feedback_path}

Fix every safely fixable issue in scope, then run the smallest relevant checks.
Preserve unrelated dirty-worktree changes. Do not stage, commit, push, publish,
delete broad paths, or rewrite AGENTS.md. Never fabricate creator approval,
identity/likeness evidence, reviewer independence or provenance, visual
inspection, generated pixels, or passing audit records. If an issue genuinely
needs a human, unavailable image generation, or new external evidence, leave it
blocked and explain that in the package rather than faking convergence.
"""
    try:
        completed = subprocess.run(
            command,
            cwd=repo_root,
            input=prompt,
            capture_output=True,
            text=True,
            timeout=timeout_seconds,
            check=False,
        )
        return RepairResult(
            command=command,
            returncode=completed.returncode,
            stdout=completed.stdout,
            stderr=completed.stderr,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        return RepairResult(command=command, returncode=124, stderr=str(exc))


def make_repair_runner(
    *,
    repo_root: Path,
    config: ReviewLoopConfig,
) -> RepairFn:
    def repair(package_dir: Path, feedback_path: Path, iteration: int) -> RepairResult:
        if config.repair_command:
            command = _expand_command(config.repair_command, package_dir, feedback_path)
            try:
                completed = subprocess.run(
                    command,
                    cwd=repo_root,
                    capture_output=True,
                    text=True,
                    timeout=config.command_timeout_seconds,
                    check=False,
                )
                return RepairResult(
                    command=command,
                    returncode=completed.returncode,
                    stdout=completed.stdout,
                    stderr=completed.stderr,
                )
            except (OSError, subprocess.TimeoutExpired) as exc:
                return RepairResult(command=command, returncode=124, stderr=str(exc))
        return _default_codex_repair(
            repo_root,
            package_dir,
            feedback_path,
            iteration,
            config.command_timeout_seconds,
        )

    return repair


def _effective_issues(
    report: WorkflowDoctorReport,
    state: CarouselState,
    verifications: Sequence[VerificationResult],
) -> list[dict[str, Any]]:
    issues = [issue.to_dict() for issue in report.issues if issue.severity in {"warning", "blocker"}]
    if not state.publishable:
        issues.append(
            {
                "code": "state_not_publishable",
                "severity": "blocker" if state.blocked else "warning",
                "message": f"Derived package state is {state.name}, not publishable.",
                "evidence": [],
                "next_action": state.next_action,
            }
        )
    for index, result in enumerate(verifications, start=1):
        if result.passed:
            continue
        issues.append(
            {
                "code": f"verification_command_{index}_failed",
                "severity": "blocker",
                "message": "A configured deterministic verifier failed.",
                "evidence": [" ".join(result.command), result.stderr[-4000:], result.stdout[-4000:]],
                "next_action": "repair_the_verifier_failure_and_rerun",
            }
        )
    return issues


def _issue_signature(issues: Sequence[dict[str, Any]], state: CarouselState) -> str:
    normalized = {
        "state": state.name,
        "publishable": state.publishable,
        "issues": [
            {
                "code": issue.get("code"),
                "severity": issue.get("severity"),
                "next_action": issue.get("next_action"),
                "message": issue.get("message"),
            }
            for issue in issues
        ],
    }
    raw = json.dumps(normalized, sort_keys=True, ensure_ascii=False).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def _human_required(issues: Sequence[dict[str, Any]]) -> list[str]:
    blockers: list[str] = []
    for issue in issues:
        code = str(issue.get("code") or "")
        message = str(issue.get("message") or "").lower()
        if (
            code in HUMAN_REQUIRED_CODES
            or code.startswith("creator_") and code.endswith("_approval_required")
            or any(fragment in message for fragment in HUMAN_REQUIRED_MESSAGE_FRAGMENTS)
        ):
            blockers.append(code)
    return blockers


def _finalize(
    *,
    package_dir: Path,
    trace_dir: Path,
    status: str,
    iterations: int,
    state: CarouselState,
    issues: Sequence[dict[str, Any]],
    reason: str,
) -> ReviewLoopResult:
    result = ReviewLoopResult(
        status=status,
        iterations=iterations,
        package_dir=str(package_dir),
        state=state.to_dict(),
        issue_codes=[str(issue.get("code") or "") for issue in issues],
        reason=reason,
        trace_dir=str(trace_dir),
    )
    _write_json(trace_dir / "summary.json", result.to_dict())
    return result


def run_review_loop(
    package_dir: Path,
    *,
    repo_root: Path,
    config: ReviewLoopConfig,
    inspect_fn: InspectFn = inspect_carousel_package,
    state_fn: StateFn = derive_carousel_state,
    repair_fn: RepairFn | None = None,
    verify_fn: VerifyFn = run_verifiers,
) -> ReviewLoopResult:
    package_dir = package_dir.expanduser().resolve()
    repo_root = repo_root.expanduser().resolve()
    if not package_dir.is_dir():
        raise ValueError(f"Carousel package directory does not exist: {package_dir}")
    trace_dir = package_dir / TRACE_DIR
    trace_path = trace_dir / "trace.jsonl"
    feedback_path = trace_dir / "feedback.json"
    repair_fn = repair_fn or make_repair_runner(repo_root=repo_root, config=config)

    previous_signature = ""
    stagnant_cycles = 0
    last_state = state_fn(package_dir)
    last_issues: list[dict[str, Any]] = []

    for iteration in range(1, config.max_iterations + 1):
        report = inspect_fn(package_dir)
        state = state_fn(package_dir)
        verifications = verify_fn(
            package_dir,
            config.verify_commands,
            config.command_timeout_seconds,
        )
        issues = _effective_issues(report, state, verifications)
        signature = _issue_signature(issues, state)
        last_state = state
        last_issues = issues

        review_event = {
            "schema_version": TRACE_SCHEMA_VERSION,
            "event": "verification",
            "iteration": iteration,
            "recorded_at": _now(),
            "signature": signature,
            "state": state.to_dict(),
            "doctor": report.to_dict(),
            "verifications": [result.to_dict() for result in verifications],
            "effective_issues": issues,
        }
        _append_jsonl(trace_path, review_event)
        _write_json(feedback_path, review_event)

        if not issues and state.publishable:
            return _finalize(
                package_dir=package_dir,
                trace_dir=trace_dir,
                status="COMPLETE",
                iterations=iteration,
                state=state,
                issues=[],
                reason="Package is publishable and every configured review passed.",
            )

        human_codes = _human_required(issues)
        if human_codes:
            return _finalize(
                package_dir=package_dir,
                trace_dir=trace_dir,
                status="HUMAN_REQUIRED",
                iterations=iteration,
                state=state,
                issues=issues,
                reason="Loop stopped instead of fabricating required human or external evidence: "
                + ", ".join(human_codes),
            )

        if config.review_only:
            return _finalize(
                package_dir=package_dir,
                trace_dir=trace_dir,
                status="REVIEW_FAILED",
                iterations=iteration,
                state=state,
                issues=issues,
                reason="Review-only mode found unresolved issues.",
            )

        if signature == previous_signature:
            stagnant_cycles += 1
        else:
            stagnant_cycles = 0
        previous_signature = signature
        if stagnant_cycles >= config.stagnation_limit:
            _write_json(
                trace_dir / "improvement-proposal.json",
                {
                    "schema_version": TRACE_SCHEMA_VERSION,
                    "status": "DRAFT_FOR_HUMAN_REVIEW",
                    "reason": "The same grader result repeated without convergence.",
                    "recurring_issue_codes": [issue.get("code") for issue in issues],
                    "suggested_action": "Improve the repair harness or obtain missing evidence; do not weaken graders.",
                },
            )
            return _finalize(
                package_dir=package_dir,
                trace_dir=trace_dir,
                status="STAGNATED",
                iterations=iteration,
                state=state,
                issues=issues,
                reason="The verification signature repeated without progress.",
            )

        if iteration == config.max_iterations:
            break

        repair_result = repair_fn(package_dir, feedback_path, iteration)
        _append_jsonl(
            trace_path,
            {
                "schema_version": TRACE_SCHEMA_VERSION,
                "event": "repair",
                "iteration": iteration,
                "recorded_at": _now(),
                "feedback_signature": signature,
                "result": repair_result.to_dict(),
            },
        )

    _write_json(
        trace_dir / "improvement-proposal.json",
        {
            "schema_version": TRACE_SCHEMA_VERSION,
            "status": "DRAFT_FOR_HUMAN_REVIEW",
            "reason": "The bounded repair budget was exhausted.",
            "recurring_issue_codes": [issue.get("code") for issue in last_issues],
            "suggested_action": "Review traces, improve the repair harness, or obtain missing evidence; do not weaken graders.",
        },
    )
    return _finalize(
        package_dir=package_dir,
        trace_dir=trace_dir,
        status="MAX_ITERATIONS",
        iterations=config.max_iterations,
        state=last_state,
        issues=last_issues,
        reason="The bounded review/repair budget was exhausted before convergence.",
    )
