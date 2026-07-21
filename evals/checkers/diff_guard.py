from __future__ import annotations

import fnmatch
import subprocess
from pathlib import Path
from typing import Iterable

from evals.schemas import CheckResult, EvalTask


PROTECTED_EVAL_HARNESS_PATHS = ("evals/**",)


def normalize_path(path: str) -> str:
    return path.strip().strip('"').replace("\\", "/")


def parse_git_status(status_text: str) -> list[str]:
    paths: list[str] = []
    for line in status_text.splitlines():
        if not line:
            continue
        payload = line[3:] if len(line) > 3 else ""
        if " -> " in payload:
            payload = payload.split(" -> ", 1)[1]
        path = normalize_path(payload)
        if path:
            paths.append(path)
    return paths


def changed_paths(root: Path) -> list[str]:
    result = subprocess.run(
        ["git", "status", "--porcelain"],
        cwd=root,
        text=True,
        capture_output=True,
        check=False,
    )
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or "git status failed")
    return parse_git_status(result.stdout)


def _matches(path: str, patterns: Iterable[str]) -> bool:
    normalized = normalize_path(path)
    return any(fnmatch.fnmatch(normalized, pattern) for pattern in patterns)


def check_changed_paths(task: EvalTask, paths: list[str]) -> list[CheckResult]:
    results: list[CheckResult] = []
    harness_hits = [
        path for path in paths if _matches(path, PROTECTED_EVAL_HARNESS_PATHS)
    ]
    if harness_hits:
        results.append(
            CheckResult(
                code="eval_harness_protected",
                status="FAIL",
                severity="critical",
                message="Solver changes may not modify the eval harness, task metadata, or fixtures.",
                evidence=harness_hits,
            )
        )
    else:
        results.append(
            CheckResult(
                code="eval_harness_protected",
                status="PASS",
                severity="info",
                message="No protected eval harness paths were changed.",
            )
        )

    forbidden_hits = [
        path for path in paths if _matches(path, task.forbidden_paths)
    ]
    if forbidden_hits:
        results.append(
            CheckResult(
                code="forbidden_path",
                status="FAIL",
                severity="critical",
                message="Changed paths include files forbidden by the eval task.",
                evidence=forbidden_hits,
            )
        )
    else:
        results.append(
            CheckResult(
                code="forbidden_path",
                status="PASS",
                severity="info",
                message="No forbidden changed paths found.",
            )
        )

    if task.allowed_paths:
        outside = [
            path
            for path in paths
            if not _matches(path, task.allowed_paths)
            and not _matches(path, task.forbidden_paths)
            and not _matches(path, PROTECTED_EVAL_HARNESS_PATHS)
        ]
    else:
        outside = []

    if outside:
        results.append(
            CheckResult(
                code="path_outside_allowed_scope",
                status="FAIL",
                severity="major",
                message="Changed paths fall outside the task allowlist.",
                evidence=outside,
            )
        )
    else:
        results.append(
            CheckResult(
                code="path_outside_allowed_scope",
                status="PASS",
                severity="info",
                message="All changed paths are within the task allowlist.",
            )
        )
    return results
