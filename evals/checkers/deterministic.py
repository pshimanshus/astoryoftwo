from __future__ import annotations

import subprocess
from pathlib import Path

from evals.schemas import CheckResult, EvalTask


def run_required_commands(task: EvalTask, root: Path, timeout: int = 120) -> list[CheckResult]:
    results: list[CheckResult] = []
    for index, command in enumerate(task.required_commands, start=1):
        result = subprocess.run(
            command,
            cwd=root,
            text=True,
            capture_output=True,
            check=False,
            timeout=timeout,
        )
        evidence = []
        if result.stdout.strip():
            evidence.append(result.stdout.strip()[-2000:])
        if result.stderr.strip():
            evidence.append(result.stderr.strip()[-2000:])
        results.append(
            CheckResult(
                code=f"required_command_{index}",
                status="PASS" if result.returncode == 0 else "FAIL",
                severity="info" if result.returncode == 0 else "critical",
                message=" ".join(command),
                evidence=evidence,
            )
        )
    return results


def check_prompt_exists(task: EvalTask) -> CheckResult:
    prompt_path = task.task_dir / task.prompt
    return CheckResult(
        code="prompt_exists",
        status="PASS" if prompt_path.exists() else "FAIL",
        severity="info" if prompt_path.exists() else "critical",
        message=f"Task prompt exists: {prompt_path}",
        evidence=[str(prompt_path)] if prompt_path.exists() else [],
    )
