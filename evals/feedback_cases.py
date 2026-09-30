"""Executable regression cases derived from explicit creator feedback."""

from __future__ import annotations

import hashlib
import json
import os
import tempfile
import copy
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping


SCHEMA_VERSION = "creator-feedback-eval/v1"
CASE_DIRECTORY = Path("evals/feedback-cases")
EVALUATOR_CONTRACT_VERSION = "creator-feedback-evaluator/v2"
EVALUATOR_CONTRACT = {
    "version": EVALUATOR_CONTRACT_VERSION,
    "required_checks": (
        "exact_feedback_preserved",
        "repair_evidence_linked",
        "declared_artifacts_repaired",
    ),
    "hash_only_fallback_check": "machine_verifiable_repair_contract",
    "repair_operation_checks": (
        "declared_repair_values",
        "unaffected_json_preserved",
        "failure_reproduced",
    ),
    "verification_assertion_checks": ("verification_assertions",),
    "supported_assertion_operators": ("equals", "contains"),
    "artifact_freshness": "sha256",
}
_UNSET = object()


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def sha256_bytes(value: bytes) -> str:
    return "sha256:" + hashlib.sha256(value).hexdigest()


def _atomic_write_json(path: Path, payload: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{path.name}.", suffix=".tmp", dir=path.parent
    )
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            json.dump(payload, handle, indent=2, ensure_ascii=False)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


def feedback_eval_task_id(feedback_id: str) -> str:
    return "FEEDBACK-" + feedback_id.removeprefix("fb-").upper()


def evaluator_contract_sha256() -> str:
    """Return the stable evaluator contract fingerprint.

    The version must be bumped whenever pass/fail semantics change. Stored
    results without this exact fingerprint are evidence, but cannot be current.
    """

    return sha256_bytes(
        json.dumps(
            EVALUATOR_CONTRACT,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
    )


def feedback_case_path(workspace_root: Path, task_id: str) -> Path:
    if not re.fullmatch(r"FEEDBACK-[A-Z0-9_-]+", task_id):
        raise ValueError("Invalid feedback eval task ID")
    return workspace_root.resolve() / CASE_DIRECTORY / f"{task_id}.json"


def artifact_hashes(package_dir: Path, artifacts: list[str]) -> dict[str, str | None]:
    root = package_dir.resolve()
    result: dict[str, str | None] = {}
    for relative in artifacts:
        path = root / relative
        try:
            path.resolve(strict=False).relative_to(root)
        except ValueError as exc:
            raise ValueError(f"feedback eval artifact leaves package: {relative}") from exc
        if path.is_symlink():
            raise ValueError(f"feedback eval artifact cannot be a symlink: {relative}")
        result[relative] = sha256_bytes(path.read_bytes()) if path.is_file() else None
    return result


def _operation_projection(package: Path, operations: list[dict[str, Any]]) -> tuple[dict[str, str], list[bool]]:
    from pipeline.stages.carousel_visual_storytelling import _replace_json_pointer

    grouped: dict[str, list[dict[str, Any]]] = {}
    for operation in operations:
        grouped.setdefault(str(operation["artifact"]), []).append(operation)
    preserved: dict[str, str] = {}
    matches: list[bool] = []
    for relative, items in grouped.items():
        artifact_hashes(package, [relative])  # reject paths outside the package
        payload = json.loads((package / relative).read_text(encoding="utf-8"))
        masked = copy.deepcopy(payload)
        for item in items:
            cursor = payload
            for token in str(item["json_pointer"])[1:].split("/"):
                token = token.replace("~1", "/").replace("~0", "~")
                cursor = cursor[int(token)] if isinstance(cursor, list) else cursor[token]
            matches.append(cursor == item["value"])
            _replace_json_pointer(masked, str(item["json_pointer"]), {"feedback_repair_slot": True})
        preserved[relative] = sha256_bytes(
            json.dumps(masked, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
        )
    return preserved, matches


def _normalize_verification_assertions(value: Any) -> list[dict[str, Any]]:
    if value is None:
        return []
    if not isinstance(value, (list, tuple)):
        raise ValueError("verification_assertions must be an array")
    normalized: list[dict[str, Any]] = []
    for index, item in enumerate(value):
        if not isinstance(item, Mapping):
            raise ValueError(f"verification assertion {index + 1} must be an object")
        artifact = str(item.get("artifact") or "").strip()
        pointer = str(item.get("json_pointer") or "")
        operator = str(item.get("operator") or "").strip()
        if not artifact:
            raise ValueError(f"verification assertion {index + 1} requires artifact")
        if not pointer.startswith("/"):
            raise ValueError(
                f"verification assertion {index + 1} requires a non-root JSON pointer"
            )
        if operator not in {"equals", "contains"}:
            raise ValueError(
                f"verification assertion {index + 1} operator must be equals or contains"
            )
        if "value" not in item:
            raise ValueError(f"verification assertion {index + 1} requires value")
        normalized.append(
            {
                "artifact": artifact,
                "json_pointer": pointer,
                "operator": operator,
                "value": copy.deepcopy(item["value"]),
            }
        )
    return normalized


def _normalize_text_contract(value: Any, *, field: str) -> list[str]:
    if not isinstance(value, (list, tuple)):
        raise ValueError(f"{field} must be an array")
    result: list[str] = []
    for item in value:
        text = str(item)
        if text.strip() and text not in result:
            result.append(text)
    return result


def _normalize_repair_operations(value: Any) -> list[dict[str, Any]]:
    if value is None:
        return []
    if not isinstance(value, (list, tuple)):
        raise ValueError("repair_operations must be an array")
    result: list[dict[str, Any]] = []
    for index, item in enumerate(value):
        if not isinstance(item, Mapping):
            raise ValueError(f"repair operation {index + 1} must be an object")
        artifact = str(item.get("artifact") or "").strip()
        pointer = str(item.get("json_pointer") or "")
        if not artifact:
            raise ValueError(f"repair operation {index + 1} requires artifact")
        if not pointer.startswith("/"):
            raise ValueError(
                f"repair operation {index + 1} requires a non-root JSON pointer"
            )
        if "value" not in item:
            raise ValueError(f"repair operation {index + 1} requires value")
        result.append(
            {
                "artifact": artifact,
                "json_pointer": pointer,
                "value": copy.deepcopy(item["value"]),
            }
        )
    return result


def _normalize_artifacts(value: Any) -> list[str]:
    if value is None:
        return []
    if not isinstance(value, (list, tuple)):
        raise ValueError("affected_artifacts must be an array")
    result: list[str] = []
    for item in value:
        text = str(item).strip()
        if text and text not in result:
            result.append(text)
    return result


def _effective_artifacts(
    affected_artifacts: list[str],
    operations: list[dict[str, Any]],
    assertions: list[dict[str, Any]],
) -> list[str]:
    result = list(affected_artifacts)
    for item in operations + assertions:
        relative = str(item["artifact"])
        if relative not in result:
            result.append(relative)
    return result


def _event_verification_contract(event: Mapping[str, Any]) -> dict[str, Any]:
    operations = _normalize_repair_operations(event.get("repair_operations"))
    assertions = _normalize_verification_assertions(
        event.get("verification_assertions")
    )
    affected = _effective_artifacts(
        _normalize_artifacts(event.get("affected_artifacts")),
        operations,
        assertions,
    )
    waiver = str(event.get("eval_waiver_reason") or "").strip() or None
    return {
        "diagnosis": str(event.get("primary_diagnosis") or ""),
        "must_change": list(event.get("must_change") or []),
        "must_preserve": list(event.get("must_preserve") or []),
        "affected_artifacts": affected,
        "repair_operations": operations,
        "verification_assertions": assertions,
        "eval_waiver_reason": waiver,
    }


def _case_verification_contract(case: Mapping[str, Any]) -> dict[str, Any]:
    operations = _normalize_repair_operations(case.get("repair_operations"))
    assertions = _normalize_verification_assertions(
        case.get("verification_assertions")
    )
    waiver = str(
        case.get("eval_waiver_reason") or case.get("waiver_reason") or ""
    ).strip() or None
    return {
        "diagnosis": str(case.get("diagnosis") or ""),
        "must_change": list(case.get("must_change") or []),
        "must_preserve": list(case.get("must_preserve") or []),
        "affected_artifacts": _effective_artifacts(
            _normalize_artifacts(case.get("affected_artifacts")),
            operations,
            assertions,
        ),
        "repair_operations": operations,
        "verification_assertions": assertions,
        "eval_waiver_reason": waiver,
    }


def _json_pointer_value(payload: Any, pointer: str) -> Any:
    cursor = payload
    for raw_token in pointer[1:].split("/"):
        token = raw_token.replace("~1", "/").replace("~0", "~")
        if isinstance(cursor, list):
            if not re.fullmatch(r"0|[1-9][0-9]*", token):
                raise ValueError(f"invalid JSON array index: {token}")
            index = int(token)
            if index >= len(cursor):
                raise IndexError(index)
            cursor = cursor[index]
        elif isinstance(cursor, Mapping):
            cursor = cursor[token]
        else:
            raise TypeError(f"JSON pointer traverses a scalar at {token}")
    return cursor


def _evaluate_verification_assertions(
    package: Path, assertions: list[dict[str, Any]]
) -> list[bool]:
    payloads: dict[str, Any] = {}
    matches: list[bool] = []
    for assertion in assertions:
        relative = assertion["artifact"]
        artifact_hashes(package, [relative])  # reject paths outside the package
        if relative not in payloads:
            payloads[relative] = json.loads(
                (package / relative).read_text(encoding="utf-8")
            )
        actual = _json_pointer_value(payloads[relative], assertion["json_pointer"])
        expected = assertion["value"]
        if assertion["operator"] == "equals":
            matches.append(actual == expected)
        elif isinstance(actual, str) and isinstance(expected, str):
            matches.append(expected in actual)
        elif isinstance(actual, list):
            matches.append(expected in actual)
        elif isinstance(actual, Mapping) and isinstance(expected, str):
            matches.append(expected in actual)
        else:
            matches.append(False)
    return matches


def _verification_contract_payload(case: Mapping[str, Any]) -> dict[str, Any]:
    """Return only fields that define what a feedback result proves."""

    return {
        "feedback_id": str(case.get("feedback_id") or ""),
        "package_path": str(case.get("package_path") or ""),
        "user_instruction_sha256": str(case.get("user_instruction_sha256") or ""),
        "diagnosis": str(case.get("diagnosis") or ""),
        "must_change": list(case.get("must_change") or []),
        "must_preserve": list(case.get("must_preserve") or []),
        "source_affected_artifacts": list(
            case.get("source_affected_artifacts")
            or case.get("affected_artifacts")
            or []
        ),
        "affected_artifacts": list(case.get("affected_artifacts") or []),
        "repair_operations": _normalize_repair_operations(
            case.get("repair_operations")
        ),
        "verification_assertions": _normalize_verification_assertions(
            case.get("verification_assertions")
        ),
        "eval_waiver_reason": str(
            case.get("eval_waiver_reason") or case.get("waiver_reason") or ""
        ).strip()
        or None,
        "baseline_artifact_hashes": dict(
            case.get("baseline_artifact_hashes") or {}
        ),
        "preserved_projection_hashes": dict(
            case.get("preserved_projection_hashes") or {}
        ),
        "revision": int(case.get("verification_contract_revision") or 1),
    }


def verification_contract_sha256(case: Mapping[str, Any]) -> str:
    return sha256_bytes(
        json.dumps(
            _verification_contract_payload(case),
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
    )


def _evaluation_snapshot(case: Mapping[str, Any]) -> dict[str, Any] | None:
    if not case.get("evaluated_at") and not case.get("checks"):
        return None
    return {
        "status": case.get("status"),
        "evaluated_at": case.get("evaluated_at"),
        "evaluator_contract_version": case.get("evaluator_contract_version"),
        "evaluator_contract_sha256": case.get("evaluator_contract_sha256"),
        "verification_contract_revision": case.get(
            "verification_contract_revision"
        ),
        "verification_contract_sha256": case.get(
            "verification_contract_sha256"
        ),
        "checks": copy.deepcopy(case.get("checks") or []),
        "issues": list(case.get("issues") or []),
        "failure_reproduced": bool(case.get("failure_reproduced")),
        "regression_promotable": bool(case.get("regression_promotable")),
        "waiver_reason": case.get("waiver_reason"),
    }


def _immutable_case_identity(
    workspace: Path,
    package: Path,
    event: Mapping[str, Any],
) -> dict[str, Any]:
    exact = str(event.get("user_instruction_exact") or "")
    exact_sha256 = str(event.get("user_instruction_sha256") or "")
    if sha256_bytes(exact.encode("utf-8")) != exact_sha256:
        raise ValueError("creator feedback exact text does not match its SHA-256")
    package_path = (
        package.relative_to(workspace).as_posix()
        if package == workspace or workspace in package.parents
        else str(package)
    )
    return {
        "feedback_id": str(event["feedback_id"]),
        "package_path": package_path,
        "user_instruction_sha256": exact_sha256,
    }


def _assert_immutable_case_identity(
    case: Mapping[str, Any],
    expected: Mapping[str, Any],
) -> None:
    actual = {key: case.get(key) for key in expected}
    if actual != dict(expected):
        raise ValueError(
            "feedback eval task already exists with different immutable identity: "
            f"{case.get('task_id')}"
        )


def ensure_feedback_case(
    workspace_root: Path,
    package_dir: Path,
    event: Mapping[str, Any],
) -> dict[str, Any]:
    """Create one stable, executable case without duplicating it on retries."""

    workspace = workspace_root.resolve()
    package = package_dir.resolve()
    feedback_id = str(event["feedback_id"])
    task_id = feedback_eval_task_id(feedback_id)
    path = feedback_case_path(workspace, task_id)
    event_contract = _event_verification_contract(event)
    operations = event_contract["repair_operations"]
    assertions = event_contract["verification_assertions"]
    source_artifacts = _normalize_artifacts(event.get("affected_artifacts"))
    artifacts = event_contract["affected_artifacts"]
    stable_identity = _immutable_case_identity(workspace, package, event)
    expected = {
        **stable_identity,
        "diagnosis": event_contract["diagnosis"],
        "must_change": event_contract["must_change"],
        "must_preserve": event_contract["must_preserve"],
        "source_affected_artifacts": source_artifacts,
        "affected_artifacts": artifacts,
        "verification_assertions": assertions,
        "eval_waiver_reason": event_contract["eval_waiver_reason"],
        "baseline_artifact_hashes": artifact_hashes(package, artifacts),
    }
    if path.is_file():
        payload = json.loads(path.read_text(encoding="utf-8"))
        _assert_immutable_case_identity(payload, stable_identity)
        if _case_verification_contract(payload) != event_contract:
            raise ValueError(
                "feedback eval task has different identity-derived contract; use "
                "revise_feedback_case_assertions()"
            )
        return payload
    preserved, matches = _operation_projection(package, operations)
    payload = {
        "schema_version": SCHEMA_VERSION,
        "task_id": task_id,
        **expected,
        "status": "pending",
        "created_at": utc_now_iso(),
        "evaluated_at": None,
        "checks": [],
        "repair_operations": operations,
        "preserved_projection_hashes": preserved,
        "failure_reproduced": bool(matches) and not all(matches),
        "evaluator_contract_version": EVALUATOR_CONTRACT_VERSION,
        "evaluator_contract_sha256": evaluator_contract_sha256(),
        "verification_contract_revision": 1,
        "verification_contract_history": [],
        "evaluation_history": [],
    }
    payload["verification_contract_sha256"] = verification_contract_sha256(
        payload
    )
    _atomic_write_json(path, payload)
    return payload


def revise_feedback_case_assertions(
    workspace_root: Path,
    package_dir: Path,
    event: Mapping[str, Any],
    verification_assertions: list[dict[str, Any]] | None = None,
    *,
    diagnosis: str | None = None,
    must_change: list[str] | None = None,
    must_preserve: list[str] | None = None,
    repair_operations: list[dict[str, Any]] | None = None,
    affected_artifacts: list[str] | None = None,
    eval_waiver_reason: str | None | object = _UNSET,
    revised_by: str,
    reason: str,
) -> dict[str, Any]:
    """Revise derived verification terms, never the exact creator evidence.

    This is the safe retrofit path for an old hash-only result. The original
    feedback identity and baselines stay immutable, while the former contract
    and evaluation are retained as append-only history.
    """

    workspace = workspace_root.resolve()
    package = package_dir.resolve()
    reviewer = revised_by.strip()
    rationale = reason.strip()
    if not reviewer:
        raise ValueError("revised_by must identify the assertion reviewer")
    if not rationale:
        raise ValueError("reason is required for an assertion revision")
    task_id = feedback_eval_task_id(str(event["feedback_id"]))
    path = feedback_case_path(workspace, task_id)
    case = load_feedback_case(workspace, task_id)
    expected_identity = _immutable_case_identity(workspace, package, event)
    _assert_immutable_case_identity(case, expected_identity)
    assertions = (
        _normalize_verification_assertions(verification_assertions)
        if verification_assertions is not None
        else _normalize_verification_assertions(
            case.get("verification_assertions")
        )
    )
    if verification_assertions is not None and not assertions:
        raise ValueError("an assertion revision requires at least one assertion")
    next_operations = (
        _normalize_repair_operations(repair_operations)
        if repair_operations is not None
        else _normalize_repair_operations(case.get("repair_operations"))
    )
    next_diagnosis = (
        str(diagnosis).strip()
        if diagnosis is not None
        else str(case.get("diagnosis") or "")
    )
    if not next_diagnosis:
        raise ValueError("diagnosis cannot be empty")
    next_must_change = (
        _normalize_text_contract(must_change, field="must_change")
        if must_change is not None
        else list(case.get("must_change") or [])
    )
    next_must_preserve = (
        _normalize_text_contract(must_preserve, field="must_preserve")
        if must_preserve is not None
        else list(case.get("must_preserve") or [])
    )
    base_artifacts = (
        _normalize_artifacts(affected_artifacts)
        if affected_artifacts is not None
        else _normalize_artifacts(case.get("affected_artifacts"))
    )
    next_artifacts = _effective_artifacts(
        base_artifacts,
        next_operations,
        assertions,
    )
    next_waiver = (
        _case_verification_contract(case)["eval_waiver_reason"]
        if eval_waiver_reason is _UNSET
        else str(eval_waiver_reason or "").strip() or None
    )
    changed_contract = bool(
        assertions
        != _normalize_verification_assertions(case.get("verification_assertions"))
        or next_diagnosis != str(case.get("diagnosis") or "")
        or next_must_change != list(case.get("must_change") or [])
        or next_must_preserve != list(case.get("must_preserve") or [])
        or next_operations
        != _normalize_repair_operations(case.get("repair_operations"))
        or next_artifacts
        != _case_verification_contract(case)["affected_artifacts"]
        or next_waiver
        != _case_verification_contract(case)["eval_waiver_reason"]
    )
    if not changed_contract:
        requested_contract = {
            "diagnosis": next_diagnosis,
            "must_change": next_must_change,
            "must_preserve": next_must_preserve,
            "affected_artifacts": next_artifacts,
            "repair_operations": next_operations,
            "verification_assertions": assertions,
            "eval_waiver_reason": next_waiver,
        }
        # The case write and creator-correction write are separate atomic
        # files. If the case committed first and the event write failed, a
        # retry must return the already-current case so the lifecycle wrapper
        # can finish synchronizing the event. A true no-op against an already
        # synchronized event remains an error.
        if (
            requested_contract == _case_verification_contract(case)
            and _event_verification_contract(event) != requested_contract
        ):
            return case
        raise ValueError("assertion revision does not change the verification contract")

    contract_history = list(case.get("verification_contract_history") or [])
    contract_history.append(
        {
            "revision": int(case.get("verification_contract_revision") or 1),
            "verification_contract_sha256": case.get(
                "verification_contract_sha256"
            ),
            "feedback_id": case.get("feedback_id"),
            "package_path": case.get("package_path"),
            "user_instruction_sha256": case.get("user_instruction_sha256"),
            "diagnosis": case.get("diagnosis"),
            "must_change": list(case.get("must_change") or []),
            "must_preserve": list(case.get("must_preserve") or []),
            "source_affected_artifacts": list(
                case.get("source_affected_artifacts")
                or case.get("affected_artifacts")
                or []
            ),
            "affected_artifacts": list(case.get("affected_artifacts") or []),
            "repair_operations": copy.deepcopy(
                case.get("repair_operations") or []
            ),
            "verification_assertions": copy.deepcopy(
                case.get("verification_assertions") or []
            ),
            "baseline_artifact_hashes": dict(
                case.get("baseline_artifact_hashes") or {}
            ),
            "preserved_projection_hashes": dict(
                case.get("preserved_projection_hashes") or {}
            ),
            "eval_waiver_reason": _case_verification_contract(case)[
                "eval_waiver_reason"
            ],
            "superseded_at": utc_now_iso(),
            "superseded_by": reviewer,
            "reason": rationale,
        }
    )
    evaluation_history = list(case.get("evaluation_history") or [])
    previous_evaluation = _evaluation_snapshot(case)
    if previous_evaluation is not None:
        evaluation_history.append(previous_evaluation)

    artifacts = next_artifacts
    baseline = dict(case.get("baseline_artifact_hashes") or {})
    missing_baselines = [relative for relative in artifacts if relative not in baseline]
    if missing_baselines:
        baseline.update(artifact_hashes(package, missing_baselines))

    operations_changed = next_operations != _normalize_repair_operations(
        case.get("repair_operations")
    )
    if operations_changed:
        preserved_projection_hashes, matches = _operation_projection(
            package, next_operations
        )
        failure_reproduced = bool(matches) and not all(matches)
    else:
        preserved_projection_hashes = dict(
            case.get("preserved_projection_hashes") or {}
        )
        failure_reproduced = bool(case.get("failure_reproduced"))

    case.update(
        {
            "source_affected_artifacts": list(
                case.get("source_affected_artifacts")
                or event.get("affected_artifacts")
                or []
            ),
            "affected_artifacts": artifacts,
            "baseline_artifact_hashes": baseline,
            "diagnosis": next_diagnosis,
            "must_change": next_must_change,
            "must_preserve": next_must_preserve,
            "repair_operations": next_operations,
            "preserved_projection_hashes": preserved_projection_hashes,
            "failure_reproduced": failure_reproduced,
            "verification_assertions": assertions,
            "eval_waiver_reason": next_waiver,
            "verification_contract_revision": int(
                case.get("verification_contract_revision") or 1
            )
            + 1,
            "verification_contract_history": contract_history,
            "evaluation_history": evaluation_history,
            "status": "pending",
            "evaluated_at": None,
            "checks": [],
            "issues": [],
            "waiver_reason": None,
            "regression_promotable": False,
            "evaluator_contract_version": EVALUATOR_CONTRACT_VERSION,
            "evaluator_contract_sha256": evaluator_contract_sha256(),
        }
    )
    case["verification_contract_sha256"] = verification_contract_sha256(case)
    _atomic_write_json(path, case)
    return case


def evaluate_feedback_case(
    workspace_root: Path,
    package_dir: Path,
    event: Mapping[str, Any],
) -> dict[str, Any]:
    """Evaluate a feedback repair deterministically and persist its result."""

    workspace = workspace_root.resolve()
    package = package_dir.resolve()
    task_id = feedback_eval_task_id(str(event["feedback_id"]))
    path = feedback_case_path(workspace, task_id)
    ensure_feedback_case(workspace, package, event)
    payload = json.loads(path.read_text(encoding="utf-8"))
    evaluation_history = list(payload.get("evaluation_history") or [])
    previous_evaluation = _evaluation_snapshot(payload)
    if previous_evaluation is not None:
        evaluation_history.append(previous_evaluation)
    payload["evaluation_history"] = evaluation_history
    payload.setdefault(
        "source_affected_artifacts",
        [str(value) for value in event.get("affected_artifacts") or []],
    )
    payload.setdefault("verification_contract_revision", 1)
    payload.setdefault("verification_contract_history", [])
    payload["eval_waiver_reason"] = _event_verification_contract(event)[
        "eval_waiver_reason"
    ]
    checks: list[dict[str, Any]] = []

    exact = str(event.get("user_instruction_exact") or "")
    exact_ok = sha256_bytes(exact.encode("utf-8")) == payload.get("user_instruction_sha256")
    checks.append(
        {
            "code": "exact_feedback_preserved",
            "status": "PASS" if exact_ok else "FAIL",
        }
    )

    operations = payload.get("repair_operations") or []
    if operations:
        try:
            preserved, matches = _operation_projection(package, operations)
            exact_repair = bool(matches) and all(matches)
            preserved_ok = preserved == payload.get("preserved_projection_hashes")
        except (OSError, ValueError, KeyError, IndexError, TypeError):
            exact_repair = preserved_ok = False
        checks.extend([
            {"code": "declared_repair_values", "status": "PASS" if exact_repair else "FAIL"},
            {"code": "unaffected_json_preserved", "status": "PASS" if preserved_ok else "FAIL"},
            {"code": "failure_reproduced", "status": "PASS" if payload.get("failure_reproduced") else "FAIL"},
        ])

    assertions = _normalize_verification_assertions(
        payload.get("verification_assertions")
    )
    if assertions:
        try:
            assertion_matches = _evaluate_verification_assertions(package, assertions)
            assertions_ok = bool(assertion_matches) and all(assertion_matches)
        except (OSError, ValueError, KeyError, IndexError, TypeError, json.JSONDecodeError):
            assertions_ok = False
        checks.append(
            {
                "code": "verification_assertions",
                "status": "PASS" if assertions_ok else "FAIL",
            }
        )

    waiver = str(event.get("eval_waiver_reason") or "").strip()
    if not operations and not assertions:
        checks.append(
            {
                "code": "machine_verifiable_repair_contract",
                "status": "WAIVED" if waiver else "UNVERIFIED",
                "reason": (
                    "Explicit eval waiver recorded."
                    if waiver
                    else (
                        "No repair_operations JSON-pointer assertions are available; "
                        "no verification_assertions were declared; artifact hashes alone "
                        "cannot prove must_change or must_preserve."
                    )
                ),
            }
        )

    resolution = [str(value) for value in event.get("resolution_evidence") or []]
    action = event.get("action_taken")
    resolved = bool(action and resolution)
    checks.append(
        {
            "code": "repair_evidence_linked",
            "status": "PASS" if resolved else "FAIL",
        }
    )

    artifacts = [str(value) for value in payload.get("affected_artifacts") or []]
    current_hashes = artifact_hashes(package, artifacts)
    baseline_hashes = payload.get("baseline_artifact_hashes") or {}
    operation_artifacts = {
        str(item.get("artifact"))
        for item in payload.get("repair_operations") or []
        if isinstance(item, Mapping) and item.get("artifact")
    }
    changed = all(
        current_hashes.get(relative) is not None
        and current_hashes.get(relative) != baseline_hashes.get(relative)
        for relative in operation_artifacts
    )
    checks.append(
        {
            "code": "declared_artifacts_repaired",
            "status": "PASS" if changed or not operation_artifacts else "FAIL",
            "current_hashes": current_hashes,
        }
    )

    failed = [check["code"] for check in checks if check["status"] == "FAIL"]
    unverified = [
        check["code"] for check in checks if check["status"] == "UNVERIFIED"
    ]
    status = (
        "waived"
        if waiver and exact_ok
        else ("failed" if failed else ("unverified" if unverified else "passed"))
    )
    payload.update(
        {
            "status": status,
            "evaluated_at": utc_now_iso(),
            "checks": checks,
            "issues": failed + unverified,
            "waiver_reason": waiver or None,
            "regression_promotable": bool(
                status == "passed" and payload.get("failure_reproduced")
            ),
            "evaluator_contract_version": EVALUATOR_CONTRACT_VERSION,
            "evaluator_contract_sha256": evaluator_contract_sha256(),
        }
    )
    payload["verification_contract_sha256"] = verification_contract_sha256(
        payload
    )
    _atomic_write_json(path, payload)
    return payload


def load_feedback_case(workspace_root: Path, task_id: str) -> dict[str, Any]:
    path = feedback_case_path(workspace_root, task_id)
    if not path.is_file() or path.is_symlink():
        raise FileNotFoundError(f"feedback eval task not found: {task_id}")
    payload = json.loads(path.read_text(encoding="utf-8"))
    if payload.get("schema_version") != SCHEMA_VERSION:
        raise ValueError(f"unsupported feedback eval schema: {payload.get('schema_version')}")
    return payload


def feedback_case_is_current(
    package_dir: Path,
    case: Mapping[str, Any],
    event: Mapping[str, Any] | None = None,
) -> bool:
    """Return whether stored evidence still proves the current evaluator contract."""

    if event is not None:
        try:
            package = package_dir.resolve()
            package_value = str(case.get("package_path") or "")
            if package_value:
                recorded_package = Path(package_value)
                if recorded_package.is_absolute():
                    if recorded_package.resolve() != package:
                        return False
                else:
                    suffix = recorded_package
                    if tuple(package.parts[-len(suffix.parts) :]) != suffix.parts:
                        return False
            if str(case.get("feedback_id") or "") != str(
                event.get("feedback_id") or ""
            ):
                return False
            if str(case.get("user_instruction_sha256") or "") != str(
                event.get("user_instruction_sha256") or ""
            ):
                return False
            if sha256_bytes(
                str(event.get("user_instruction_exact") or "").encode("utf-8")
            ) != str(event.get("user_instruction_sha256") or ""):
                return False
            if _case_verification_contract(case) != _event_verification_contract(
                event
            ):
                return False
            if not event.get("action_taken") or not list(
                event.get("resolution_evidence") or []
            ):
                return False
        except (OSError, TypeError, ValueError):
            return False
    if case.get("status") not in {"passed", "waived"}:
        return False
    if case.get("evaluator_contract_version") != EVALUATOR_CONTRACT_VERSION:
        return False
    if case.get("evaluator_contract_sha256") != evaluator_contract_sha256():
        return False
    try:
        if case.get("verification_contract_sha256") != verification_contract_sha256(
            case
        ):
            return False
        assertions = _normalize_verification_assertions(
            case.get("verification_assertions")
        )
    except (TypeError, ValueError):
        return False
    operations = list(case.get("repair_operations") or [])
    waiver = str(case.get("waiver_reason") or "").strip()
    if not operations and not assertions and not waiver:
        return False

    check_statuses = {
        str(check.get("code")): str(check.get("status"))
        for check in case.get("checks") or []
        if isinstance(check, Mapping)
    }
    required_passes = {
        "exact_feedback_preserved",
        "repair_evidence_linked",
        "declared_artifacts_repaired",
    }
    if operations:
        required_passes.update(
            {
                "declared_repair_values",
                "unaffected_json_preserved",
                "failure_reproduced",
            }
        )
    if assertions:
        required_passes.add("verification_assertions")
    if any(check_statuses.get(code) != "PASS" for code in required_passes):
        return False
    if waiver and check_statuses.get("machine_verifiable_repair_contract") != "WAIVED":
        return False
    if any(value in {"FAIL", "UNVERIFIED"} for value in check_statuses.values()):
        return False

    recorded = next((check.get("current_hashes") for check in case.get("checks") or []
                     if check.get("code") == "declared_artifacts_repaired"), None)
    if recorded is None:
        return False
    try:
        return artifact_hashes(package_dir, list(case.get("affected_artifacts") or [])) == recorded
    except (OSError, ValueError):
        return False


__all__ = [
    "CASE_DIRECTORY",
    "EVALUATOR_CONTRACT_VERSION",
    "SCHEMA_VERSION",
    "artifact_hashes",
    "ensure_feedback_case",
    "evaluate_feedback_case",
    "evaluator_contract_sha256",
    "feedback_case_path",
    "feedback_eval_task_id",
    "feedback_case_is_current",
    "load_feedback_case",
    "revise_feedback_case_assertions",
    "verification_contract_sha256",
]
