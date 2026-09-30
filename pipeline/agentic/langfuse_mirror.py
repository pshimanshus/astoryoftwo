"""Disabled-by-default, redacted Langfuse observability mirror."""

from __future__ import annotations

import hashlib
import importlib.metadata
import importlib.util
import inspect
import json
import math
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import Any, Callable, Iterable, Mapping
from urllib.parse import urlparse


LANGFUSE_TESTED_VERSION = "4.15.1"
LANGFUSE_WORKER_TIMEOUT_SECONDS = 10.0
ALLOWED_FIELDS = frozenset(
    {
        "feedback_id",
        "learning_event_id",
        "eval_task_ids",
        "user_instruction_sha256",
        "asset_sha256",
        "primary_diagnosis",
        "secondary_diagnoses",
        "scope",
        "status",
        "generation_effect",
    }
)
_SCOPES = frozenset({"workflow", "package", "slide", "asset", "copy", "global"})
_STATUSES = frozenset(
    {
        "captured",
        "diagnosed",
        "applied",
        "evaluated",
        "learning_proposed",
        "learning_declined",
        "approved",
        "promoted",
        "rejected",
    }
)
_EFFECTS = frozenset({"none", "slide_local", "shared"})
_DIAGNOSES = frozenset(
    {
        "concept_recognition",
        "voice_copy",
        "scene_action",
        "identity_reference",
        "exact_text_layout",
        "dimensions_brandmark",
        "instruction_drift",
        "runtime_tool_failure",
        "provenance_qa",
    }
)
_SAFE_ID = re.compile(r"[A-Za-z0-9][A-Za-z0-9._:-]{0,127}")


def _installed_version(distribution: str) -> str | None:
    try:
        return importlib.metadata.version(distribution)
    except (importlib.metadata.PackageNotFoundError, ValueError):
        return None


def _base_url_is_safe(value: str | None) -> bool:
    if not value:
        return True
    try:
        parsed = urlparse(value)
        hostname = parsed.hostname
    except ValueError:
        return False
    if parsed.username or parsed.password or not parsed.hostname:
        return False
    return parsed.scheme == "https" or (
        parsed.scheme == "http" and hostname in {"localhost", "127.0.0.1", "::1"}
    )


def langfuse_environment_status() -> dict[str, Any]:
    """Report capability and credential presence without returning secret values."""

    installed = _installed_version("langfuse")
    worker_python = _worker_python()
    isolated_python = _workspace_root() / ".venv-evals" / "bin" / "python"
    base_url = os.environ.get("LANGFUSE_BASE_URL") or os.environ.get("LANGFUSE_HOST")
    try:
        sdk_installed = importlib.util.find_spec("langfuse") is not None
    except (ImportError, ValueError):
        sdk_installed = "langfuse" in __import__("sys").modules
    return {
        "enabled": os.environ.get("ASOT_LANGFUSE_ENABLED") == "1",
        "sdk_installed": sdk_installed,
        "sdk_version": installed,
        "tested_sdk_version": LANGFUSE_TESTED_VERSION,
        "worker_python_present": worker_python is not None,
        "worker_uses_isolated_venv": bool(
            worker_python is not None
            and worker_python == isolated_python.resolve(strict=False)
        ),
        "delivery_mode": "bounded_subprocess" if worker_python is not None else "unavailable",
        "delivery_timeout_seconds": LANGFUSE_WORKER_TIMEOUT_SECONDS,
        "credentials_present": bool(
            os.environ.get("LANGFUSE_PUBLIC_KEY") and os.environ.get("LANGFUSE_SECRET_KEY")
        ),
        "base_url_valid": _base_url_is_safe(base_url),
        "install_command": f"python -m pip install 'langfuse=={LANGFUSE_TESTED_VERSION}'",
        "isolated_setup_command": "make feedback-integrations-setup",
    }


def run_langfuse_sdk_smoke() -> dict[str, Any]:
    """Verify installed SDK methods without constructing a client or doing I/O."""

    environment = langfuse_environment_status()
    if not environment["sdk_installed"]:
        return {
            "status": "not_run",
            "reason": "langfuse is not installed",
            "coverage": "none",
            "external_calls": "none",
        }
    try:
        from langfuse import Langfuse, get_client  # type: ignore

        required = {
            "get_client": inspect.signature(get_client),
            "create_trace_id": inspect.signature(Langfuse.create_trace_id),
            "start_as_current_observation": inspect.signature(
                Langfuse.start_as_current_observation
            ),
            "create_score": inspect.signature(Langfuse.create_score),
            "flush": inspect.signature(Langfuse.flush),
        }
        if "seed" not in required["create_trace_id"].parameters:
            raise ValueError("create_trace_id lacks seed")
        if "trace_context" not in required["start_as_current_observation"].parameters:
            raise ValueError("observation API lacks trace_context")
        if "score_id" not in required["create_score"].parameters:
            raise ValueError("score API lacks idempotency key")
    except Exception as exc:
        return {
            "status": "failed",
            "reason": type(exc).__name__,
            "coverage": "installed_sdk_import_and_signature_contract",
            "external_calls": "none",
            "sdk_version": environment["sdk_version"],
        }
    return {
        "status": "passed",
        "coverage": "installed_sdk_import_and_signature_contract",
        "external_calls": "none",
        "sdk_version": environment["sdk_version"],
    }


def redacted_feedback_payload(
    event: Mapping[str, Any],
    *,
    eval_scores: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Allowlist non-content metadata; exact creator text never leaves the repo."""

    payload: dict[str, Any] = {}
    enums = {
        "scope": _SCOPES,
        "status": _STATUSES,
        "generation_effect": _EFFECTS,
        "primary_diagnosis": _DIAGNOSES,
    }
    for key in sorted(ALLOWED_FIELDS):
        value = event.get(key)
        if key in enums and isinstance(value, str) and value in enums[key]:
            payload[key] = value
        elif key.endswith("sha256") and isinstance(value, str) and re.fullmatch(
            r"sha256:[0-9a-f]{64}", value
        ):
            payload[key] = value
        elif key in {"feedback_id", "learning_event_id"} and isinstance(value, str) and re.fullmatch(
            r"(?:fb-|event-)[A-Za-z0-9._-]{1,100}", value
        ):
            payload[key] = value
        elif key == "eval_task_ids" and isinstance(value, list):
            payload[key] = [
                item
                for item in value
                if isinstance(item, str)
                and re.fullmatch(r"(?:FEEDBACK-|ASTO-)[A-Za-z0-9._-]{1,100}", item)
            ]
        elif key == "secondary_diagnoses" and isinstance(value, list):
            payload[key] = [
                item for item in value if isinstance(item, str) and item in _DIAGNOSES
            ]
    if eval_scores:
        safe_scores: dict[str, Any] = {}
        for key, value in eval_scores.items():
            name = str(key)
            if not re.fullmatch(r"[A-Za-z0-9_]{1,60}", name):
                continue
            if isinstance(value, bool):
                safe_scores[name] = value
            elif isinstance(value, (int, float)) and math.isfinite(float(value)):
                safe_scores[name] = value
            elif isinstance(value, str) and value in {
                "passed",
                "failed",
                "waived",
                "not_run",
                "scored",
            }:
                safe_scores[name] = value
        if safe_scores:
            payload["eval_scores"] = safe_scores
    summary_source = "|".join(
        str(payload.get(key) or "")
        for key in ("primary_diagnosis", "scope", "status", "generation_effect")
    )
    payload["redacted_trace_summary_sha256"] = "sha256:" + hashlib.sha256(
        summary_source.encode("utf-8")
    ).hexdigest()
    identity_source = "|".join(
        str(payload.get(key) or "")
        for key in ("feedback_id", "learning_event_id", "status")
    )
    payload["mirror_idempotency_sha256"] = "sha256:" + hashlib.sha256(
        identity_source.encode("utf-8")
    ).hexdigest()
    return payload


def validate_redacted_feedback_payload(payload: Mapping[str, Any]) -> dict[str, Any]:
    """Reject payload expansion and recompute every derived mirror field."""

    allowed = set(ALLOWED_FIELDS) | {
        "eval_scores",
        "redacted_trace_summary_sha256",
        "mirror_idempotency_sha256",
    }
    extra = sorted(str(key) for key in payload if key not in allowed)
    if extra:
        raise ValueError("redacted Langfuse payload contains unsupported fields")
    event = {key: payload.get(key) for key in ALLOWED_FIELDS if key in payload}
    scores = payload.get("eval_scores")
    if scores is not None and not isinstance(scores, Mapping):
        raise ValueError("redacted Langfuse eval_scores must be a mapping")
    rebuilt = redacted_feedback_payload(event, eval_scores=scores)
    for key in ("redacted_trace_summary_sha256", "mirror_idempotency_sha256"):
        if payload.get(key) != rebuilt[key]:
            raise ValueError("redacted Langfuse payload integrity check failed")
    return rebuilt


def _sdk_export(payload: dict[str, Any]) -> None:
    """Use the Langfuse v3/v4 Python client with only redacted metadata."""

    payload = validate_redacted_feedback_payload(payload)

    try:
        from langfuse import get_client  # type: ignore

        client = get_client()
    except ImportError:  # Langfuse Python SDK v2 compatibility
        from langfuse import Langfuse  # type: ignore

        client = Langfuse()
    seed = str(payload["mirror_idempotency_sha256"])
    trace_id = client.create_trace_id(seed=seed)
    with client.start_as_current_observation(
        as_type="span",
        name="creator-feedback-lifecycle",
        trace_context={"trace_id": trace_id},
        metadata=dict(payload),
    ):
        pass
    # A stable score id makes retries update one lifecycle marker even if the
    # tracing backend records more than one span.
    client.create_score(
        name="creator_feedback_mirrored",
        value=1.0,
        trace_id=trace_id,
        score_id=hashlib.sha256(seed.encode("utf-8")).hexdigest(),
        data_type="NUMERIC",
        metadata={"mirror_idempotency_sha256": seed},
    )
    client.flush()


def _workspace_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _worker_python() -> Path | None:
    configured = os.environ.get("ASOT_FEEDBACK_INTEGRATIONS_PY")
    candidates = [Path(configured).expanduser()] if configured else []
    candidates.append(_workspace_root() / ".venv-evals" / "bin" / "python")
    if importlib.util.find_spec("langfuse") is not None:
        candidates.append(Path(sys.executable))
    for candidate in candidates:
        try:
            resolved = candidate.resolve(strict=True)
        except (OSError, RuntimeError):
            continue
        if resolved.is_file() and os.access(resolved, os.X_OK):
            return resolved
    return None


def _isolated_sdk_export(payload: dict[str, Any]) -> None:
    """Export through a bounded worker so the production interpreter stays clean."""

    worker_python = _worker_python()
    if worker_python is None:
        raise ModuleNotFoundError("no Langfuse worker interpreter is available")
    completed = subprocess.run(
        [str(worker_python), "-m", "pipeline.agentic.langfuse_worker"],
        input=json.dumps(validate_redacted_feedback_payload(payload)),
        text=True,
        cwd=_workspace_root(),
        env=os.environ.copy(),
        capture_output=True,
        timeout=LANGFUSE_WORKER_TIMEOUT_SECONDS,
        check=False,
    )
    if completed.returncode != 0:
        raise RuntimeError("isolated Langfuse worker failed")


def mirror_feedback_event(
    event: Mapping[str, Any],
    *,
    eval_scores: Mapping[str, Any] | None = None,
    exporter: Callable[[dict[str, Any]], None] | None = None,
) -> dict[str, Any]:
    """Run a bounded best-effort mirror; failures never change local results."""

    payload = redacted_feedback_payload(event, eval_scores=eval_scores)
    if os.environ.get("ASOT_LANGFUSE_ENABLED") != "1":
        return {"status": "disabled", "payload": payload}
    if not os.environ.get("LANGFUSE_PUBLIC_KEY") or not os.environ.get("LANGFUSE_SECRET_KEY"):
        return {"status": "not_run", "reason": "missing Langfuse credentials", "payload": payload}
    base_url = os.environ.get("LANGFUSE_BASE_URL") or os.environ.get("LANGFUSE_HOST")
    if not _base_url_is_safe(base_url):
        return {"status": "not_run", "reason": "invalid Langfuse base URL", "payload": payload}
    if exporter is None and _worker_python() is None:
        return {"status": "not_run", "reason": "Langfuse worker is not installed", "payload": payload}

    dispatch_exporter = exporter or _isolated_sdk_export
    try:
        dispatch_exporter(dict(payload))
    except subprocess.TimeoutExpired:
        return {"status": "failed_nonblocking", "reason": "TimeoutExpired", "payload": payload}
    except Exception as exc:
        return {"status": "failed_nonblocking", "reason": type(exc).__name__, "payload": payload}
    return {"status": "mirrored", "payload": payload}


def _annotation_mapping(annotation: Any) -> Mapping[str, Any]:
    if isinstance(annotation, Mapping):
        return annotation
    model_dump = getattr(annotation, "model_dump", None)
    if callable(model_dump):
        value = model_dump(mode="json")
        if isinstance(value, Mapping):
            return value
    raise ValueError("annotation must be a mapping or SDK score model")


def annotation_identity_sha256(annotation_id: str) -> str:
    candidate = str(annotation_id or "").strip()
    if not _SAFE_ID.fullmatch(candidate):
        raise ValueError("annotation id is missing or invalid")
    return "sha256:" + hashlib.sha256(candidate.encode("utf-8")).hexdigest()


def candidate_event_from_annotation(annotation: Any) -> dict[str, Any]:
    """Validate one human annotation and return a local-review candidate only."""

    payload = _annotation_mapping(annotation)
    source = str(payload.get("source") or "").upper()
    if source != "ANNOTATION":
        raise ValueError("only source=ANNOTATION scores can become feedback candidates")
    annotation_id = str(payload.get("id") or "").strip()
    identity = annotation_identity_sha256(annotation_id)
    text_values = (
        payload.get("comment"),
        payload.get("string_value"),
        payload.get("stringValue"),
        payload.get("value"),
    )
    exact = next(
        (value for value in text_values if isinstance(value, str) and value.strip()),
        "",
    )
    if not exact.strip():
        raise ValueError("annotation requires a non-empty text value or comment")
    if len(exact) > 500:
        raise ValueError("annotation text exceeds the Langfuse 500 character limit")
    metadata = payload.get("metadata")
    scope_value = metadata.get("scope") if isinstance(metadata, Mapping) else None
    scope = str(scope_value or "package")
    if scope not in _SCOPES:
        raise ValueError("annotation scope is invalid")
    return {
        "source": "langfuse_annotation_candidate",
        "candidate_status": "pending_local_review",
        "user_instruction_exact": exact,
        "user_instruction_sha256": "sha256:" + hashlib.sha256(exact.encode("utf-8")).hexdigest(),
        "scope": scope,
        "external_annotation_id_sha256": identity,
    }


def import_annotation_candidates(
    annotations: Iterable[Any],
    *,
    existing_annotation_ids: Iterable[str] = (),
) -> dict[str, Any]:
    """Normalize annotations idempotently without writing creator feedback."""

    seen: set[str] = set()
    for value in existing_annotation_ids:
        candidate = str(value)
        if re.fullmatch(r"sha256:[0-9a-f]{64}", candidate):
            seen.add(candidate)
        else:
            seen.add(annotation_identity_sha256(candidate))
    candidates: list[dict[str, Any]] = []
    batch_candidates: dict[str, dict[str, Any]] = {}
    duplicate_count = 0
    invalid: list[dict[str, str]] = []
    for index, annotation in enumerate(annotations):
        try:
            candidate = candidate_event_from_annotation(annotation)
        except ValueError as exc:
            invalid.append({"index": str(index), "reason": str(exc)})
            continue
        identity = candidate["external_annotation_id_sha256"]
        prior = batch_candidates.get(identity)
        if prior is not None:
            if prior != candidate:
                invalid.append(
                    {"index": str(index), "reason": "annotation id has conflicting content"}
                )
            else:
                duplicate_count += 1
            continue
        if identity in seen:
            duplicate_count += 1
            continue
        seen.add(identity)
        batch_candidates[identity] = candidate
        candidates.append(candidate)
    return {
        "status": "candidates_ready" if candidates else "no_new_candidates",
        "candidates": candidates,
        "candidate_count": len(candidates),
        "duplicate_count": duplicate_count,
        "invalid": invalid,
        "persistence": "none",
        "next_action": "local_diagnosis_and_creator_feedback_capture",
    }


__all__ = [
    "ALLOWED_FIELDS",
    "LANGFUSE_TESTED_VERSION",
    "LANGFUSE_WORKER_TIMEOUT_SECONDS",
    "annotation_identity_sha256",
    "candidate_event_from_annotation",
    "import_annotation_candidates",
    "langfuse_environment_status",
    "mirror_feedback_event",
    "redacted_feedback_payload",
    "run_langfuse_sdk_smoke",
    "validate_redacted_feedback_payload",
]
