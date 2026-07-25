from __future__ import annotations

import fnmatch
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
from typing import Any, Iterable

from evals.schemas import CheckResult, EvalTask


BASELINE_SCHEMA_VERSION = "1.0"
MUTATION_SCHEMA_VERSION = "1.0"
EXCLUDED_DIRECTORY_NAMES = {
    ".git",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    ".worktrees",
    "__pycache__",
    "node_modules",
    "venv",
}
EXCLUDED_FILE_SUFFIXES = {".pyc", ".pyo"}


class AttemptContractError(ValueError):
    """Raised when evaluator-owned attempt evidence is missing or invalid."""


def _canonical_json(payload: dict[str, Any]) -> bytes:
    return json.dumps(
        payload,
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")


def _sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _record_integrity(payload: dict[str, Any]) -> str:
    unsigned = dict(payload)
    unsigned.pop("record_sha256", None)
    return _sha256_bytes(_canonical_json(unsigned))


def _safe_relative_path(raw_path: str) -> str:
    normalized = raw_path.replace("\\", "/")
    pure = PurePosixPath(normalized)
    if normalized in {"", "."} or pure.is_absolute() or ".." in pure.parts:
        raise AttemptContractError(f"Unsafe attempt path: {raw_path}")
    return pure.as_posix()


def _is_within(path: Path, root: Path) -> bool:
    try:
        path.resolve().relative_to(root.resolve())
    except ValueError:
        return False
    return True


def require_evaluator_owned_path(path: Path, workspace_root: Path, *, label: str) -> None:
    if _is_within(path, workspace_root):
        raise AttemptContractError(
            f"{label} must live outside the solver workspace: {path}"
        )


def capture_workspace(root: Path) -> dict[str, str]:
    """Hash the solver-visible workspace without depending on Git state.

    The baseline may already contain fixture overlays, hidden mutations, and
    unrelated dirty files. Comparing hashes after the agent run therefore
    measures only changes made after the evaluator froze the baseline.
    """

    root = root.resolve()
    snapshot: dict[str, str] = {}
    for current, directory_names, file_names in os.walk(root):
        directory_names[:] = sorted(
            name
            for name in directory_names
            if name not in EXCLUDED_DIRECTORY_NAMES
        )
        current_path = Path(current)
        for name in sorted(file_names):
            path = current_path / name
            if path.suffix in EXCLUDED_FILE_SUFFIXES:
                continue
            relative = path.relative_to(root).as_posix()
            if path.is_symlink():
                target = os.readlink(path)
                snapshot[relative] = _sha256_bytes(
                    f"symlink\0{target}".encode("utf-8")
                )
            elif path.is_file():
                snapshot[relative] = _sha256_file(path)
    return snapshot


def changed_since_baseline(
    baseline_files: dict[str, str],
    current_files: dict[str, str],
) -> list[str]:
    all_paths = set(baseline_files) | set(current_files)
    return sorted(
        path
        for path in all_paths
        if baseline_files.get(path) != current_files.get(path)
    )


def eval_contract_fingerprint(task: EvalTask) -> str:
    """Fingerprint the trusted harness and every file in this task definition."""

    eval_root = Path(__file__).resolve().parent
    digest = hashlib.sha256()
    roots = (
        ("harness", eval_root),
        ("task", task.task_dir.resolve()),
    )
    seen: set[Path] = set()
    for label, root in roots:
        if not root.exists():
            continue
        for current, directory_names, file_names in os.walk(root):
            directory_names[:] = sorted(
                name
                for name in directory_names
                if name not in EXCLUDED_DIRECTORY_NAMES
            )
            current_path = Path(current)
            for name in sorted(file_names):
                path = (current_path / name).resolve()
                if path in seen or path.suffix in EXCLUDED_FILE_SUFFIXES:
                    continue
                seen.add(path)
                relative = path.relative_to(root).as_posix()
                digest.update(f"{label}/{relative}\0".encode("utf-8"))
                digest.update(_sha256_file(path).encode("ascii"))
                digest.update(b"\0")
    return digest.hexdigest()


def _matches_any(path: str, patterns: Iterable[str]) -> bool:
    return any(fnmatch.fnmatch(path, pattern) for pattern in patterns)


def load_mutation_manifest(
    path: Path,
    *,
    task: EvalTask,
    workspace_root: Path,
) -> dict[str, Any]:
    require_evaluator_owned_path(
        path,
        workspace_root,
        label="Hidden mutation manifest",
    )
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise AttemptContractError("Hidden mutation manifest must be a JSON object")
    if payload.get("schema_version") != MUTATION_SCHEMA_VERSION:
        raise AttemptContractError("Unsupported hidden mutation manifest schema")
    if payload.get("task_id") != task.id:
        raise AttemptContractError("Hidden mutation manifest task_id does not match")
    mutation_id = payload.get("mutation_id")
    if not isinstance(mutation_id, str) or not mutation_id.strip():
        raise AttemptContractError("Hidden mutation manifest needs mutation_id")
    mutated_files = payload.get("mutated_files")
    if not isinstance(mutated_files, list) or not mutated_files:
        raise AttemptContractError("Hidden mutation manifest needs mutated_files")

    verified_files: list[dict[str, str]] = []
    for item in mutated_files:
        if not isinstance(item, dict):
            raise AttemptContractError("Each mutated_files entry must be an object")
        relative = _safe_relative_path(str(item.get("path", "")))
        expected_sha = str(item.get("sha256", ""))
        if len(expected_sha) != 64:
            raise AttemptContractError(
                f"Mutation entry needs a SHA-256 digest: {relative}"
            )
        target = workspace_root / relative
        if not target.is_file():
            raise AttemptContractError(f"Mutated file is missing: {relative}")
        if target.is_symlink():
            raise AttemptContractError(
                f"Mutated file may not be a symlink: {relative}"
            )
        actual_sha = _sha256_file(target)
        if actual_sha != expected_sha:
            raise AttemptContractError(
                f"Mutation digest does not match workspace file: {relative}"
            )
        verified_files.append({"path": relative, "sha256": actual_sha})

    changed_paths = [item["path"] for item in verified_files]
    production_targets = [
        path
        for path in task.expected_files_changed
        if not path.startswith(("tests/", "output/", "docs/"))
    ]
    if not _matches_any_path(changed_paths, production_targets):
        raise AttemptContractError(
            "Hidden mutation must touch at least one expected production solution file"
        )
    return {
        "schema_version": MUTATION_SCHEMA_VERSION,
        "task_id": task.id,
        "mutation_id": mutation_id,
        "mutated_files": verified_files,
        "manifest_sha256": _sha256_file(path),
    }


def _matches_any_path(paths: Iterable[str], patterns: Iterable[str]) -> bool:
    return any(_matches_any(path, patterns) for path in paths)


def create_baseline_record(
    task: EvalTask,
    workspace_root: Path,
    baseline_checks: list[CheckResult],
    *,
    mutation_manifest_path: Path | None = None,
) -> dict[str, Any]:
    failures = sorted(
        {check.code for check in baseline_checks if check.status == "FAIL"}
    )
    issues: list[str] = []
    mutation: dict[str, Any] | None = None

    if not failures:
        issues.append(
            "The starting state is already resolved; a no-op agent could pass"
        )

    if task.fixture_contract.mode == "regression":
        if mutation_manifest_path is None:
            issues.append(
                "Regression task requires an evaluator-owned hidden mutation manifest"
            )
        else:
            try:
                mutation = load_mutation_manifest(
                    mutation_manifest_path,
                    task=task,
                    workspace_root=workspace_root,
                )
            except (FileNotFoundError, OSError, json.JSONDecodeError, AttemptContractError) as exc:
                issues.append(str(exc))
    elif mutation_manifest_path is not None:
        issues.append("Solution fixtures must not use a hidden mutation manifest")

    ready = not issues
    record: dict[str, Any] = {
        "schema_version": BASELINE_SCHEMA_VERSION,
        "status": "READY" if ready else "NOT_READY",
        "task_id": task.id,
        "fixture_mode": task.fixture_contract.mode,
        "benchmark_setup": task.fixture_contract.benchmark_setup,
        "eval_contract_sha256": eval_contract_fingerprint(task),
        "baseline": {
            "resolved": not failures,
            "failing_check_codes": failures,
            "checks": [check.to_dict() for check in baseline_checks],
        },
        "mutation": mutation,
        "issues": issues,
    }
    if ready:
        record["workspace"] = {"files": capture_workspace(workspace_root)}
    record["record_sha256"] = _record_integrity(record)
    return record


def write_baseline_record(
    record: dict[str, Any],
    path: Path,
    *,
    workspace_root: Path,
) -> None:
    require_evaluator_owned_path(path, workspace_root, label="Baseline record")
    if record.get("status") != "READY":
        raise AttemptContractError("Refusing to write a baseline that is not READY")
    if path.exists():
        raise AttemptContractError(f"Refusing to overwrite baseline record: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")


def load_baseline_record(
    path: Path,
    *,
    workspace_root: Path,
) -> dict[str, Any]:
    require_evaluator_owned_path(path, workspace_root, label="Baseline record")
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise AttemptContractError("Baseline record must be a JSON object")
    if payload.get("schema_version") != BASELINE_SCHEMA_VERSION:
        raise AttemptContractError("Unsupported baseline record schema")
    if payload.get("status") != "READY":
        raise AttemptContractError("Baseline record is not READY")
    expected_integrity = payload.get("record_sha256")
    if expected_integrity != _record_integrity(payload):
        raise AttemptContractError("Baseline record integrity check failed")
    workspace = payload.get("workspace")
    if not isinstance(workspace, dict) or not isinstance(workspace.get("files"), dict):
        raise AttemptContractError("Baseline record has no workspace snapshot")
    return payload


def attempt_transition_checks(
    task: EvalTask,
    workspace_root: Path,
    baseline_record: dict[str, Any],
    final_checks: list[CheckResult],
    *,
    current_files: dict[str, str] | None = None,
) -> tuple[list[str], list[CheckResult]]:
    baseline_files = baseline_record["workspace"]["files"]
    current_files = current_files or capture_workspace(workspace_root)
    changed_paths = changed_since_baseline(baseline_files, current_files)
    results: list[CheckResult] = []

    task_matches = baseline_record.get("task_id") == task.id
    results.append(
        _result(
            "baseline_task_match",
            task_matches,
            "Baseline record belongs to this task.",
            "Baseline record belongs to a different task.",
        )
    )

    contract_matches = (
        baseline_record.get("eval_contract_sha256")
        == eval_contract_fingerprint(task)
    )
    results.append(
        _result(
            "eval_contract_unchanged",
            contract_matches,
            "Eval task and trusted checker contract are unchanged.",
            "Eval task or checker contract changed after the baseline was frozen.",
        )
    )

    results.append(
        _result(
            "patch_required",
            bool(changed_paths),
            "The agent changed the baseline workspace.",
            "No files changed after baseline; no-op solutions cannot pass.",
            evidence=changed_paths,
        )
    )

    expected_hits = [
        path
        for path in changed_paths
        if path in current_files and _matches_any(path, task.expected_files_changed)
    ]
    results.append(
        _result(
            "expected_solution_file_changed",
            bool(expected_hits),
            "At least one declared solution file was updated and remains present.",
            "The patch did not leave an updated declared solution file.",
            evidence=expected_hits or changed_paths,
        )
    )

    baseline_failures = baseline_record["baseline"].get(
        "failing_check_codes",
        [],
    )
    statuses: dict[str, list[str]] = {}
    for check in final_checks:
        statuses.setdefault(check.code, []).append(check.status)
    not_fixed = [
        code
        for code in baseline_failures
        if code not in statuses or any(status != "PASS" for status in statuses[code])
    ]
    results.append(
        _result(
            "fail_to_pass_transition",
            bool(baseline_failures) and not not_fixed,
            "Every checker that failed at baseline now passes.",
            "One or more baseline failures did not flip to PASS.",
            evidence=[
                f"baseline_failures={','.join(baseline_failures)}",
                f"not_fixed={','.join(not_fixed)}",
            ],
        )
    )

    regression_setup_valid = (
        task.fixture_contract.mode != "regression"
        or isinstance(baseline_record.get("mutation"), dict)
    )
    results.append(
        _result(
            "regression_setup_proven",
            regression_setup_valid,
            "Required hidden regression setup is bound to the baseline.",
            "Regression baseline has no verified hidden mutation.",
        )
    )
    return changed_paths, results


def _result(
    code: str,
    passed: bool,
    pass_message: str,
    fail_message: str,
    *,
    evidence: list[str] | None = None,
) -> CheckResult:
    return CheckResult(
        code=code,
        status="PASS" if passed else "FAIL",
        severity="info" if passed else "critical",
        message=pass_message if passed else fail_message,
        evidence=evidence or [],
    )
