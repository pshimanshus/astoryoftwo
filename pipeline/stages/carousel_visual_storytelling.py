"""Compact physical-scene preflight and rendered-pixel story validation.

Only files and pixels certify output. The default workflow does not require
agent provenance, task IDs, raw-response ledgers, or chained fingerprints.
"""

from __future__ import annotations

from contextlib import ExitStack, contextmanager
from dataclasses import dataclass
from datetime import datetime, timezone
import fcntl
import hashlib
import json
import os
from pathlib import Path, PurePosixPath, PureWindowsPath
import re
import tempfile
import unicodedata
from typing import Any, Iterable, Mapping

from PIL import Image, UnidentifiedImageError

from pipeline.stages.carousel_format_contract import (
    DEFAULT_NATIVE_FORMATS,
    SUPPORTED_NATIVE_FORMATS,
    locked_formats,
)
from pipeline.stages.carousel_visual_integrity import (
    validate_visual_richness_contract,
)


DIRECTOR_STORYBOARD_KEY = "director_storyboard"
VISUAL_STORY_READABILITY_KEY = "visual_story_readability"
CREATOR_CORRECTION_ARTIFACTS = ("creator-correction.json", "correction.json")
CREATOR_CORRECTION_SCHEMA_VERSION = "creator-correction/v3"
LEGACY_CREATOR_CORRECTION_SCHEMA_VERSION = "creator-correction/v2"
LEGACY_SUCCESSOR_RETIREMENT_SCHEMA_VERSION = "successor-retirement/v1"
SUCCESSOR_RETIREMENT_SCHEMA_VERSION = "successor-retirement/v2"
SUCCESSOR_RETIREMENT_DOCUMENT_NAMESPACE = "successor-retirement-document/v1"
CREATOR_FEEDBACK_KINDS = frozenset(
    {"correction", "rejection", "approval", "preference", "lock", "observation"}
)
CREATOR_FEEDBACK_SCOPES = frozenset(
    {"workflow", "package", "slide", "asset", "copy", "global"}
)
CREATOR_FEEDBACK_EFFECTS = frozenset({"none", "slide_local", "shared"})
CREATOR_FEEDBACK_DIAGNOSES = frozenset(
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
        "carousel_intelligence_calibration",
    }
)
CREATOR_FEEDBACK_STATUSES = (
    "captured",
    "diagnosed",
    "applied",
    "evaluated",
    "learning_proposed",
    "learning_declined",
    "approved",
    "promoted",
    "rejected",
)
CREATOR_FEEDBACK_TERMINAL_STATUSES = frozenset({"promoted", "rejected"})
CREATOR_FEEDBACK_TRANSITIONS = {
    "captured": frozenset({"diagnosed", "rejected"}),
    "diagnosed": frozenset({"applied", "rejected"}),
    "applied": frozenset({"evaluated", "rejected"}),
    "evaluated": frozenset({"learning_proposed", "approved", "promoted", "rejected"}),
    "learning_proposed": frozenset({"evaluated", "learning_declined", "approved", "rejected"}),
    "learning_declined": frozenset({"evaluated", "applied"}),
    "approved": frozenset({"evaluated", "learning_declined", "promoted", "rejected"}),
    "promoted": frozenset(),
    "rejected": frozenset(),
}
BRANDMARK_PLACEMENT = "top-right"


@dataclass(frozen=True)
class ExpectedFrameAsset:
    relative_path: str
    dimensions: tuple[int, int]


def _stable_fingerprint(payload: Any, *, namespace: str) -> str:
    encoded = json.dumps(
        {"namespace": namespace, "payload": payload},
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return "sha256:" + hashlib.sha256(encoded).hexdigest()


def generation_payload_fingerprint(prompt_pack: Any) -> str:
    return _stable_fingerprint(prompt_pack, namespace="visual-generation-payload/v1")


def current_creator_correction_fingerprint(package_dir: Path) -> str:
    root = Path(package_dir)
    artifacts: list[dict[str, Any]] = []
    for filename in CREATOR_CORRECTION_ARTIFACTS:
        path = root / filename
        if not path.exists() and not path.is_symlink():
            continue
        entry: dict[str, Any] = {"name": filename, "symlink": path.is_symlink()}
        try:
            raw = path.read_bytes()
            entry["payload"] = json.loads(raw.decode("utf-8"))
        except (OSError, UnicodeDecodeError, json.JSONDecodeError):
            try:
                entry["raw_sha256"] = hashlib.sha256(path.read_bytes()).hexdigest()
            except OSError:
                entry["unreadable"] = True
        artifacts.append(entry)
    return _stable_fingerprint(artifacts, namespace="creator-correction-state/v1")


def _string_list(value: Any) -> list[str]:
    if isinstance(value, str):
        return [value] if value.strip() else []
    if not isinstance(value, list):
        return []
    result: list[str] = []
    for item in value:
        if isinstance(item, str):
            text = item
        elif isinstance(item, Mapping):
            text = str(item.get("instruction") or item.get("text") or "")
        else:
            text = str(item)
        if text.strip() and text not in result:
            result.append(text)
    return result


def _feedback_artifacts(package_dir: Path) -> list[tuple[Path, dict[str, Any], bytes]]:
    root = Path(package_dir).expanduser()
    result: list[tuple[Path, dict[str, Any], bytes]] = []
    for filename in CREATOR_CORRECTION_ARTIFACTS:
        path = root / filename
        if not path.exists() and not path.is_symlink():
            continue
        if path.is_symlink() or not path.is_file():
            raise ValueError(f"{filename} must be a regular package file.")
        raw = path.read_bytes()
        try:
            payload = json.loads(raw.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise ValueError(f"{filename} must contain valid UTF-8 JSON.") from exc
        if not isinstance(payload, dict):
            raise ValueError(f"{filename} must contain one JSON object.")
        result.append((path, payload, raw))
    return result


def _feedback_text_sha256(value: str) -> str:
    return "sha256:" + hashlib.sha256(value.encode("utf-8")).hexdigest()


def diagnose_creator_feedback(value: str, *, fallback: str = "provenance_qa") -> str:
    """Return the deterministic first-pass diagnosis used by capture/backfill."""

    text = value.casefold()
    categories = (
        ("dimensions_brandmark", ("1080", "dimension", "ratio", "canvas", "brandmark", "logo")),
        ("exact_text_layout", ("exact text", "word", "spelling", "copy inside", "layout", "typography")),
        ("identity_reference", ("identity", "face", "likeness", "aachu", "zuv", "reference")),
        ("scene_action", ("scene", "action", "hand", "pose", "prop", "visual", "illustration")),
        ("voice_copy", ("voice", "caption", "copy", "line", "tone", "wording")),
        ("concept_recognition", ("concept", "recognition", "relatable", "send", "story", "idea")),
        ("instruction_drift", ("instruction", "rule", "skill", "workflow", "always", "never")),
        ("runtime_tool_failure", ("tool", "runtime", "imagegen", "timeout", "failed to run")),
        ("provenance_qa", ("audit", "hash", "qa", "provenance", "receipt", "evidence")),
    )
    for diagnosis, needles in categories:
        if any(needle in text for needle in needles):
            return diagnosis
    return fallback


def _normalized_diagnosis(value: str | None, *, exact_text: str) -> str:
    diagnosis = str(value or "").strip().replace("/", "_").replace("-", "_")
    aliases = {
        "concept": "concept_recognition",
        "recognition": "concept_recognition",
        "voice": "voice_copy",
        "copy": "voice_copy",
        "scene": "scene_action",
        "action": "scene_action",
        "identity": "identity_reference",
        "reference": "identity_reference",
        "exact_text": "exact_text_layout",
        "layout": "exact_text_layout",
        "dimensions": "dimensions_brandmark",
        "brandmark": "dimensions_brandmark",
        "runtime": "runtime_tool_failure",
        "tool_failure": "runtime_tool_failure",
        "provenance": "provenance_qa",
        "qa": "provenance_qa",
    }
    diagnosis = aliases.get(diagnosis, diagnosis)
    if not diagnosis or diagnosis == "untriaged":
        return diagnose_creator_feedback(exact_text)
    if diagnosis not in CREATOR_FEEDBACK_DIAGNOSES:
        raise ValueError(
            "Unsupported creator feedback diagnosis: "
            f"{diagnosis}. Expected one of {', '.join(sorted(CREATOR_FEEDBACK_DIAGNOSES))}."
        )
    return diagnosis


def _normalize_repair_operations(value: Iterable[Mapping[str, Any]] = ()) -> list[dict[str, Any]]:
    operations: list[dict[str, Any]] = []
    for item in value:
        if not isinstance(item, Mapping):
            raise ValueError("repair operations must be JSON objects")
        artifact = str(item.get("artifact") or "").strip()
        pointer = str(item.get("json_pointer") or "").strip()
        if not artifact or not pointer.startswith("/") or "value" not in item:
            raise ValueError(
                "each repair operation requires artifact, /json_pointer, and value"
            )
        operations.append(
            {
                "artifact": artifact,
                "json_pointer": pointer,
                "value": item["value"],
            }
        )
    return operations


def _normalize_verification_assertions(
    value: Iterable[Mapping[str, Any]] = (),
) -> list[dict[str, Any]]:
    """Validate non-mutating JSON assertions used to prove a creator correction."""

    assertions: list[dict[str, Any]] = []
    for item in value:
        if not isinstance(item, Mapping):
            raise ValueError("verification assertions must be JSON objects")
        artifact = str(item.get("artifact") or "").strip()
        pointer = str(item.get("json_pointer") or "").strip()
        operator = str(item.get("operator") or "").strip()
        if not artifact or not pointer.startswith("/") or "value" not in item:
            raise ValueError(
                "each verification assertion requires artifact, /json_pointer, operator, and value"
            )
        if operator not in {"equals", "contains"}:
            raise ValueError("verification assertion operator must be equals or contains")
        assertions.append(
            {
                "artifact": artifact,
                "json_pointer": pointer,
                "operator": operator,
                "value": item["value"],
            }
        )
    return assertions


def _event_defaults(record: Mapping[str, Any]) -> dict[str, Any]:
    exact = str(record.get("user_instruction_exact") or record.get("legacy_summary") or "")
    captured_at = str(record.get("captured_at") or record.get("recorded_at") or "")
    diagnosis = str(
        record.get("primary_diagnosis")
        or record.get("diagnosis")
        or diagnose_creator_feedback(exact)
    )
    if diagnosis == "untriaged" or diagnosis not in CREATOR_FEEDBACK_DIAGNOSES:
        diagnosis = diagnose_creator_feedback(exact)
    result = {
        "feedback_id": str(record.get("feedback_id") or ""),
        "captured_at": captured_at,
        "user_instruction_exact": exact,
        "user_instruction_sha256": str(
            record.get("user_instruction_sha256") or _feedback_text_sha256(exact)
        ),
        "kind": str(record.get("kind") or "correction"),
        "scope": str(record.get("scope") or "package"),
        "slide_number": (
            int(record["slide_number"])
            if record.get("slide_number") is not None
            else None
        ),
        "slides": sorted({int(value) for value in record.get("slides") or []}),
        "asset_sha256": record.get("asset_sha256"),
        "primary_diagnosis": diagnosis,
        "secondary_diagnoses": _string_list(record.get("secondary_diagnoses")),
        "root_cause": record.get("root_cause") or record.get("diagnosis"),
        "desired_behavior": record.get("desired_behavior"),
        "must_change": _string_list(record.get("must_change")),
        "must_preserve": _string_list(record.get("must_preserve")),
        "affected_artifacts": _string_list(record.get("affected_artifacts")),
        "repair_operations": _normalize_repair_operations(record.get("repair_operations") or []),
        "verification_assertions": _normalize_verification_assertions(
            record.get("verification_assertions") or []
        ),
        "action_taken": record.get("action_taken"),
        "action_history": list(record.get("action_history") or []),
        "adoption_provenance": record.get("adoption_provenance"),
        "resolution_evidence": _string_list(record.get("resolution_evidence")),
        "learning_event_id": record.get("learning_event_id"),
        "learning_proposal_id": record.get("learning_proposal_id"),
        "eval_task_ids": _string_list(record.get("eval_task_ids")),
        "eval_waiver_reason": record.get("eval_waiver_reason"),
        "status": str(record.get("status") or "captured"),
        "generation_effect": str(record.get("generation_effect") or "none"),
        "supersedes_feedback_id": record.get("supersedes_feedback_id"),
        "historical_only": bool(record.get("historical_only", False)),
        "learning_disposition": record.get("learning_disposition") or (
            "declined" if record.get("status") == "learning_declined" else None
        ),
        "legacy_artifact": record.get("legacy_artifact"),
        "legacy_payload_sha256": record.get("legacy_payload_sha256"),
    }
    if result["slide_number"] is None and len(result["slides"]) == 1:
        result["slide_number"] = result["slides"][0]
    if result["slide_number"] is not None and result["slide_number"] not in result["slides"]:
        result["slides"].append(result["slide_number"])
        result["slides"].sort()
    return result


def _legacy_feedback_record(
    path: Path,
    payload: Mapping[str, Any],
    raw: bytes,
) -> dict[str, Any]:
    exact = next(
        (
            str(payload[key])
            for key in ("user_instruction_exact", "creator_feedback", "correction")
            if isinstance(payload.get(key), str) and str(payload[key]).strip()
        ),
        None,
    )
    legacy_corrections = _string_list(payload.get("corrections"))
    diagnosis_value = payload.get("diagnosis")
    diagnosis = "; ".join(_string_list(diagnosis_value))
    visual = payload.get("visual_story_correction")
    if not diagnosis and isinstance(visual, Mapping):
        diagnosis = str(visual.get("creator_diagnosis") or "")
    status = str(payload.get("status") or "").upper()
    if "REJECT" in status:
        kind = "rejection"
    elif exact and exact.strip().casefold() in {"go ahead", "approved", "approve", "yes"}:
        kind = "approval"
    elif "LOCK" in status and not legacy_corrections:
        kind = "lock"
    else:
        kind = "correction"
    recorded = next(
        (
            str(payload[key])
            for key in ("recorded_on", "recorded_date", "date", "latest_revision_date")
            if payload.get(key)
        ),
        "",
    )
    digest = hashlib.sha256(raw).hexdigest()
    instruction = exact or "\n".join(legacy_corrections) or json.dumps(
        payload, ensure_ascii=False, sort_keys=True
    )
    rejected_phrases = _string_list(payload.get("rejected_route_phrases"))
    preserved = _string_list(payload.get("constraints"))
    return _event_defaults({
        "feedback_id": f"fb-legacy-{digest[:16]}",
        "captured_at": recorded,
        "user_instruction_exact": instruction,
        "kind": kind,
        "scope": "package",
        "slides": [],
        "primary_diagnosis": diagnose_creator_feedback(
            " ".join([instruction, diagnosis, *rejected_phrases])
        ),
        "root_cause": diagnosis or None,
        "desired_behavior": preserved[0] if preserved else None,
        "must_change": rejected_phrases,
        "must_preserve": preserved,
        "affected_artifacts": [path.name],
        "action_taken": {
            "type": "metadata_backfill",
            "legacy_status": str(payload.get("status") or "unknown"),
        },
        "resolution_evidence": [path.name],
        "eval_task_ids": [f"FEEDBACK-{digest[:16]}"],
        "eval_waiver_reason": (
            "Historical correction predates deterministic feedback-case capture; "
            "metadata was normalized without changing carousel media."
        ),
        "status": "evaluated",
        "generation_effect": "none" if kind in {"approval", "lock"} else "shared",
        "supersedes_feedback_id": None,
        "learning_event_id": None,
        "historical_only": True,
        "legacy_artifact": path.name,
        "legacy_payload_sha256": f"sha256:{digest}",
    })


def creator_feedback_records(package_dir: Path) -> list[dict[str, Any]]:
    """Return one normalized read-only view across legacy and v2 corrections."""

    records: list[dict[str, Any]] = []
    artifacts = _feedback_artifacts(package_dir)
    normalized = [
        item
        for item in artifacts
        if item[1].get("schema_version") == CREATOR_CORRECTION_SCHEMA_VERSION
    ]
    # Once a normalized writer exists it contains the preserved legacy sources;
    # do not surface a still-present correction.json as a duplicate event.
    for path, payload, raw in normalized or artifacts:
        if payload.get("schema_version") == CREATOR_CORRECTION_SCHEMA_VERSION:
            events = payload.get("events")
            if not isinstance(events, list):
                raise ValueError("creator-correction/v3 requires an events array.")
            for item in events:
                if not isinstance(item, dict):
                    raise ValueError("creator-correction/v3 events must be objects.")
                records.append(_event_defaults(item))
        elif payload.get("schema_version") == LEGACY_CREATOR_CORRECTION_SCHEMA_VERSION:
            feedback = payload.get("feedback")
            if not isinstance(feedback, list):
                raise ValueError("creator-correction/v2 requires a feedback array.")
            for item in feedback:
                if not isinstance(item, dict):
                    raise ValueError("creator-correction/v2 feedback records must be objects.")
                records.append(_event_defaults(item))
        else:
            records.append(_legacy_feedback_record(path, payload, raw))
    return records


def _creator_correction_document(
    package_dir: Path,
    *,
    package_id: str,
) -> dict[str, Any]:
    artifacts = _feedback_artifacts(package_dir)
    for path, payload, _ in artifacts:
        if (
            path.name == "creator-correction.json"
            and payload.get("schema_version") == CREATOR_CORRECTION_SCHEMA_VERSION
        ):
            events = payload.get("events")
            if not isinstance(events, list):
                raise ValueError("creator-correction/v3 requires an events array.")
            return {
                **payload,
                "package_id": str(payload.get("package_id") or package_id),
                "events": events,
            }

    events = creator_feedback_records(package_dir)
    legacy_sources = [
        {
            "artifact": path.name,
            "sha256": "sha256:" + hashlib.sha256(raw).hexdigest(),
            "schema_version": payload.get("schema_version"),
            "payload": payload,
            "raw_utf8": raw.decode("utf-8"),
        }
        for path, payload, raw in artifacts
    ]
    document: dict[str, Any] = {
        "schema_version": CREATOR_CORRECTION_SCHEMA_VERSION,
        "package_id": package_id,
        "events": events,
    }
    if legacy_sources:
        document["legacy_sources"] = legacy_sources
    return document


def _workspace_package(
    workspace: Path,
    supplied: str | Path,
    *,
    label: str,
) -> tuple[Path, str]:
    candidate = Path(supplied).expanduser()
    if not candidate.is_absolute():
        candidate = workspace / candidate
    if candidate.is_symlink():
        raise ValueError(f"{label} cannot be a symlink")
    resolved = candidate.resolve(strict=True)
    try:
        relative = resolved.relative_to(workspace).as_posix()
    except ValueError as exc:
        raise ValueError(f"{label} must stay inside the workspace") from exc
    if not resolved.is_dir():
        raise ValueError(f"{label} must be a package directory")
    return resolved, relative


def _successor_feedback_lineage(
    document: Mapping[str, Any],
    *,
    package_path: str,
    workspace_root: Path,
) -> list[dict[str, str]]:
    """Return proven origins for live events while validating the full history."""

    if document.get("schema_version") != CREATOR_CORRECTION_SCHEMA_VERSION:
        raise ValueError("successor retirement requires creator-correction/v3")
    adoption = document.get("successor_adoption")
    if not isinstance(adoption, Mapping) or not str(
        adoption.get("source_package_path") or ""
    ).strip():
        raise ValueError("successor retirement requires successor_adoption metadata")
    events = document.get("events")
    if not isinstance(events, list):
        raise ValueError("successor retirement requires an events array")

    workspace = Path(workspace_root).resolve(strict=True)
    by_feedback_id: dict[str, Mapping[str, Any]] = {}
    rows: list[dict[str, str]] = []
    for event in events:
        if not isinstance(event, Mapping):
            raise ValueError("successor retirement events must be objects")
        feedback_id = str(event.get("feedback_id") or "")
        if not feedback_id or feedback_id in by_feedback_id:
            raise ValueError("successor retirement requires unique feedback identities")
        by_feedback_id[feedback_id] = event
        # Historical and rejected events remain recallable evidence. Their exact
        # bytes are still part of the immutable retired document and must never
        # become a way to bypass exact-feedback validation.
        exact_hash = _feedback_text_sha256(str(event.get("user_instruction_exact") or ""))
        if event.get("user_instruction_sha256") != exact_hash:
            raise ValueError("successor retirement found stale exact-feedback hash")
        if event.get("historical_only") is True or event.get("status") == "rejected":
            continue
        provenance = event.get("adoption_provenance")
        if isinstance(provenance, Mapping) and provenance.get("source_feedback_id"):
            origin_package = str(provenance.get("source_package_path") or "")
            origin_feedback_id = str(provenance.get("source_feedback_id") or "")
            origin_hash = str(provenance.get("source_user_instruction_sha256") or "")
            if not origin_package or origin_hash != exact_hash:
                raise ValueError("successor retirement found incomplete adoption provenance")
            source_learning_event_id = str(
                provenance.get("source_learning_event_id") or ""
            )
        else:
            origin_package = package_path
            origin_feedback_id = feedback_id
            origin_hash = exact_hash
            source_learning_event_id = str(event.get("learning_event_id") or "")
        _validate_feedback_origin(
            workspace,
            package_path=origin_package,
            feedback_id=origin_feedback_id,
            instruction_hash=origin_hash,
            expected_learning_event_id=source_learning_event_id,
        )
        rows.append(
            {
                "retired_feedback_id": feedback_id,
                "origin_package_path": origin_package,
                "origin_feedback_id": origin_feedback_id,
                "user_instruction_sha256": origin_hash,
            }
        )

    carried = [str(value) for value in adoption.get("carried_feedback_ids") or []]
    source_ids = [str(value) for value in adoption.get("source_feedback_ids") or []]
    if len(carried) != len(source_ids):
        raise ValueError("successor adoption source and carried identities must align")
    if len(carried) != len(set(carried)) or len(source_ids) != len(set(source_ids)):
        raise ValueError("successor adoption identities must be unique")
    if any(value not in by_feedback_id for value in carried):
        raise ValueError("successor adoption references a missing carried event")
    carried_origins = [
        str((by_feedback_id[value].get("adoption_provenance") or {}).get("source_feedback_id") or "")
        for value in carried
    ]
    if carried_origins != source_ids:
        raise ValueError("successor adoption source identities do not match carried events")
    adoption_source = str(adoption.get("source_package_path") or "")
    _, canonical_adoption_source = _workspace_package(
        workspace, adoption_source, label="successor adoption source"
    )
    if adoption_source != canonical_adoption_source:
        raise ValueError("successor adoption source path must be canonical")
    provenance_event_ids = []
    for feedback_id, event in by_feedback_id.items():
        provenance = event.get("adoption_provenance")
        if not isinstance(provenance, Mapping) or not provenance:
            continue
        provenance_event_ids.append(feedback_id)
        if (
            str(provenance.get("source_package_path") or "") != adoption_source
            or not str(provenance.get("source_feedback_id") or "")
        ):
            raise ValueError("carried event provenance disagrees with successor_adoption")
    if provenance_event_ids != carried:
        raise ValueError("successor_adoption must enumerate every carried event")
    return sorted(
        rows,
        key=lambda item: (
            item["origin_package_path"],
            item["origin_feedback_id"],
            item["retired_feedback_id"],
        ),
    )


def _retirement_document_fingerprint(document: Mapping[str, Any]) -> str:
    immutable_document = {
        key: value for key, value in document.items() if key != "successor_retirement"
    }
    return _stable_fingerprint(
        immutable_document, namespace=SUCCESSOR_RETIREMENT_DOCUMENT_NAMESPACE
    )


def _validate_feedback_origin(
    workspace: Path,
    *,
    package_path: str,
    feedback_id: str,
    instruction_hash: str,
    expected_learning_event_id: str = "",
) -> None:
    """Prove a lineage origin against canonical package or LearningEvent bytes."""

    origin, canonical_path = _workspace_package(
        workspace, package_path, label="feedback origin package"
    )
    if package_path != canonical_path:
        raise ValueError("feedback origin package path must be canonical")
    evidence_ids: set[str] = set()
    found = False
    archived_event_only = False
    matching_learning_events = 0
    correction = origin / "creator-correction.json"
    if correction.exists():
        if correction.is_symlink() or not correction.is_file():
            raise ValueError("feedback origin creator-correction.json must be regular")
        payload = json.loads(correction.read_text(encoding="utf-8"))
        if (
            isinstance(payload, Mapping)
            and payload.get("schema_version") == CREATOR_CORRECTION_SCHEMA_VERSION
        ):
            events = payload.get("events")
            if not isinstance(events, list):
                raise ValueError("feedback origin creator-correction.json is invalid")
            matches = [
                event
                for event in events
                if isinstance(event, Mapping) and event.get("feedback_id") == feedback_id
            ]
            if len(matches) > 1:
                raise ValueError("feedback origin identity is duplicated")
            if not matches:
                from pipeline.stages.carousel_generation_state import archived_package_read_only_reason

                # Read-only packages can retain an earlier v3 correction file;
                # later feedback is deliberately captured only as LearningEvents.
                if not archived_package_read_only_reason(origin) or not expected_learning_event_id:
                    raise ValueError("feedback lineage origin is absent from its v3 package")
                archived_event_only = True
            else:
                found = True
                event = matches[0]
                actual_hash = _feedback_text_sha256(
                    str(event.get("user_instruction_exact") or "")
                )
                if (
                    event.get("user_instruction_sha256") != actual_hash
                    or actual_hash != instruction_hash
                ):
                    raise ValueError("feedback origin exact text does not match lineage")
                if event.get("learning_event_id"):
                    evidence_ids.add(str(event["learning_event_id"]))

    for event_path in sorted(
        workspace.glob("memory/agentic/learning-events/*.json")
    ):
        try:
            payload = json.loads(event_path.read_text(encoding="utf-8"))
        except (OSError, UnicodeDecodeError, json.JSONDecodeError):
            continue
        if not isinstance(payload, Mapping):
            continue
        metadata = payload.get("feedback_metadata")
        if (
            payload.get("source") != "creator_feedback"
            or payload.get("package_path") != package_path
            or not isinstance(metadata, Mapping)
            or metadata.get("feedback_id") != feedback_id
        ):
            continue
        matching_learning_events += 1
        if archived_event_only and (
            metadata.get("historical_package_read_only") is not True
            or payload.get("event_id") != expected_learning_event_id
            or matching_learning_events > 1
            or event_path.is_symlink()
        ):
            raise ValueError("archived feedback origin requires one matching read-only LearningEvent")
        found = True
        actual_hash = _feedback_text_sha256(
            str(payload.get("user_instruction_exact") or "")
        )
        stored_hash = payload.get("user_instruction_sha256")
        if (
            actual_hash != instruction_hash
            or (stored_hash is not None and stored_hash != actual_hash)
        ):
            raise ValueError("feedback origin LearningEvent conflicts with package evidence")
        if payload.get("event_id"):
            evidence_ids.add(str(payload["event_id"]))
    if not found:
        raise ValueError("feedback lineage origin does not exist")
    if expected_learning_event_id and expected_learning_event_id not in evidence_ids:
        raise ValueError("feedback lineage source LearningEvent identity does not match")


def _retirement_identity_payload(
    *,
    package_path: str,
    target_path: str,
    source_rows: list[dict[str, str]],
    retired_document_sha256: str,
    retired_at: str,
    retired_by: str,
    reason_exact: str,
    migration_provenance: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "retired_package_path": package_path,
        "superseded_by_package_path": target_path,
        "carried_feedback_lineage": source_rows,
        "retired_document_sha256": retired_document_sha256,
        "retired_at": retired_at,
        "retired_by": retired_by,
        "reason_exact": reason_exact,
        "production_state_effect": "none",
    }
    if migration_provenance is not None:
        payload["migration_provenance"] = dict(migration_provenance)
    return payload


def _lineage_origins(rows: Iterable[Mapping[str, str]]) -> set[tuple[str, str, str]]:
    return {
        (
            str(row["origin_package_path"]),
            str(row["origin_feedback_id"]),
            str(row["user_instruction_sha256"]),
        )
        for row in rows
    }


def _read_successor_document(package: Path, *, label: str) -> dict[str, Any]:
    correction = package / "creator-correction.json"
    if correction.is_symlink() or not correction.is_file():
        raise ValueError(f"{label} requires a regular creator-correction.json")
    document = json.loads(correction.read_text(encoding="utf-8"))
    if not isinstance(document, dict):
        raise ValueError(f"{label} correction must be an object")
    return document


def _validate_retirement_chain(
    workspace: Path,
    package: Path,
    package_path: str,
    *,
    visited: set[str],
) -> dict[str, Any]:
    if package_path in visited:
        raise ValueError("successor retirement chain contains a cycle")
    visited = {*visited, package_path}
    document = _read_successor_document(package, label="retired successor")
    retirement = document.get("successor_retirement")
    if not isinstance(retirement, Mapping):
        raise ValueError("successor retirement chain ended without retirement metadata")
    if retirement.get("schema_version") != SUCCESSOR_RETIREMENT_SCHEMA_VERSION:
        if retirement.get("schema_version") == LEGACY_SUCCESSOR_RETIREMENT_SCHEMA_VERSION:
            raise ValueError("legacy successor retirement requires explicit v2 migration")
        raise ValueError("unsupported successor retirement schema")
    target, target_path = _workspace_package(
        workspace,
        str(retirement.get("superseded_by_package_path") or ""),
        label="superseding successor",
    )
    if target == package:
        raise ValueError("a successor cannot retire into itself")
    source_rows = _successor_feedback_lineage(
        document, package_path=package_path, workspace_root=workspace
    )
    stored_rows = retirement.get("carried_feedback_lineage")
    if stored_rows != source_rows:
        raise ValueError("retirement lineage no longer matches retired feedback bytes")
    document_sha256 = _retirement_document_fingerprint(document)
    if retirement.get("retired_document_sha256") != document_sha256:
        raise ValueError("retired successor document changed after retirement")
    target_document = _read_successor_document(target, label="superseding successor")
    target_rows = _successor_feedback_lineage(
        target_document, package_path=target_path, workspace_root=workspace
    )
    required_origins = _lineage_origins(source_rows)
    if not required_origins.issubset(_lineage_origins(target_rows)):
        raise ValueError("superseding successor does not carry every live feedback origin")
    reason = str(retirement.get("reason_exact") or "")
    retired_by = str(retirement.get("retired_by") or "")
    retired_at = str(retirement.get("retired_at") or "")
    if not reason.strip() or not retired_by.strip() or not retired_at.strip():
        raise ValueError("retirement requires exact reason, actor, and timestamp")
    try:
        parsed_retired_at = datetime.fromisoformat(retired_at)
    except ValueError as exc:
        raise ValueError("retirement timestamp must be ISO-8601") from exc
    if parsed_retired_at.tzinfo is None:
        raise ValueError("retirement timestamp must include a timezone")
    if retirement.get("production_state_effect") != "none":
        raise ValueError("feedback retirement must not change production state")
    migration = retirement.get("migration_provenance")
    if migration is not None and not isinstance(migration, Mapping):
        raise ValueError("retirement migration provenance must be an object")
    identity_payload = _retirement_identity_payload(
        package_path=package_path,
        target_path=target_path,
        source_rows=source_rows,
        retired_document_sha256=document_sha256,
        retired_at=retired_at,
        retired_by=retired_by,
        reason_exact=reason,
        migration_provenance=migration,
    )
    expected_id = _stable_fingerprint(
        identity_payload, namespace=SUCCESSOR_RETIREMENT_SCHEMA_VERSION
    )
    if retirement.get("retirement_id") != expected_id:
        raise ValueError("retirement identity is stale")

    active_leaf_path = target_path
    if "successor_retirement" in target_document:
        target_status = _validate_retirement_chain(
            workspace, target, target_path, visited=visited
        )
        active_leaf_path = str(target_status["active_leaf_package_path"])
        leaf, _ = _workspace_package(
            workspace, active_leaf_path, label="active successor leaf"
        )
        leaf_rows = _successor_feedback_lineage(
            _read_successor_document(leaf, label="active successor leaf"),
            package_path=active_leaf_path,
            workspace_root=workspace,
        )
        if not required_origins.issubset(_lineage_origins(leaf_rows)):
            raise ValueError("active successor leaf does not carry retired feedback origins")

    row_ids = {row["retired_feedback_id"] for row in source_rows}
    learning_ids = sorted(
        str(event.get("learning_event_id"))
        for event in document.get("events") or []
        if isinstance(event, Mapping)
        and event.get("feedback_id") in row_ids
        and event.get("learning_event_id")
    )
    return {
        "retired": True,
        "issues": [],
        "package_path": package_path,
        "superseded_by_package_path": target_path,
        "active_leaf_package_path": active_leaf_path,
        "retirement_id": expected_id,
        "retired_at": retired_at,
        "retired_by": retired_by,
        "reason_exact": reason,
        "carried_feedback_count": len(source_rows),
        "retired_feedback_ids": sorted(row_ids),
        "retired_learning_event_ids": learning_ids,
    }


def successor_feedback_retirement_status(
    package_dir: Path,
    *,
    workspace_root: Path,
) -> dict[str, Any]:
    """Validate explicit feedback-lineage retirement without changing any state."""

    try:
        workspace = Path(workspace_root).expanduser().resolve(strict=True)
        package, package_path = _workspace_package(
            workspace, package_dir, label="retired successor"
        )
        document = _read_successor_document(package, label="retired successor")
        retirement = document.get("successor_retirement")
        if retirement is None:
            return {"retired": False, "issues": [], "package_path": package_path}
        return _validate_retirement_chain(
            workspace, package, package_path, visited=set()
        )
    except (OSError, UnicodeDecodeError, json.JSONDecodeError, ValueError) as exc:
        return {
            "retired": False,
            "issues": [str(exc)],
            "package_path": str(package_dir),
        }


def _validate_legacy_retirement_for_migration(
    workspace: Path,
    package: Path,
    package_path: str,
    target: Path,
    target_path: str,
    document: Mapping[str, Any],
    target_document: Mapping[str, Any],
) -> dict[str, Any]:
    """Validate an honest v1 record before an explicit, auditable v2 upgrade."""

    retirement = document.get("successor_retirement")
    if not isinstance(retirement, Mapping) or retirement.get(
        "schema_version"
    ) != LEGACY_SUCCESSOR_RETIREMENT_SCHEMA_VERSION:
        raise ValueError("existing retirement is not migratable successor-retirement/v1")
    if str(retirement.get("superseded_by_package_path") or "") != target_path:
        raise ValueError("legacy retirement names a different superseding successor")
    if "successor_retirement" in target_document:
        raise ValueError("legacy retirement target is no longer an active leaf")
    source_rows = _successor_feedback_lineage(
        document, package_path=package_path, workspace_root=workspace
    )
    target_rows = _successor_feedback_lineage(
        target_document, package_path=target_path, workspace_root=workspace
    )
    if retirement.get("carried_feedback_lineage") != source_rows:
        raise ValueError("legacy retirement lineage no longer matches source bytes")
    if not _lineage_origins(source_rows).issubset(_lineage_origins(target_rows)):
        raise ValueError("legacy retirement target does not carry every live origin")
    retired_at = str(retirement.get("retired_at") or "")
    retired_by = str(retirement.get("retired_by") or "")
    reason = str(retirement.get("reason_exact") or "")
    if not retired_at or not retired_by.strip() or not reason.strip():
        raise ValueError("legacy retirement lacks actor, reason, or timestamp")
    legacy_identity = {
        "retired_package_path": package_path,
        "superseded_by_package_path": target_path,
        "carried_feedback_lineage": source_rows,
        "retired_at": retired_at,
        "retired_by": retired_by,
        "reason_exact": reason,
        "production_state_effect": "none",
    }
    expected_legacy_id = _stable_fingerprint(
        legacy_identity, namespace=LEGACY_SUCCESSOR_RETIREMENT_SCHEMA_VERSION
    )
    if retirement.get("retirement_id") != expected_legacy_id:
        raise ValueError("legacy retirement identity is stale")
    if retirement.get("production_state_effect") != "none":
        raise ValueError("legacy retirement changed production state")
    return {
        "source_rows": source_rows,
        "retired_at": retired_at,
        "retired_by": retired_by,
        "reason_exact": reason,
        "legacy_retirement_id": expected_legacy_id,
    }


def retire_successor_feedback(
    package_dir: Path,
    *,
    workspace_root: Path,
    superseded_by: Path,
    retired_by: str,
    reason_exact: str,
) -> dict[str, Any]:
    """Explicitly retire duplicate feedback debt while preserving package history."""

    if not retired_by.strip() or not reason_exact.strip():
        raise ValueError("retirement requires --retired-by and a non-empty --reason")
    workspace = Path(workspace_root).expanduser().resolve(strict=True)
    package, package_path = _workspace_package(
        workspace, package_dir, label="retired successor"
    )
    target, target_path = _workspace_package(
        workspace, superseded_by, label="superseding successor"
    )
    if package == target:
        raise ValueError("a successor cannot retire into itself")
    metadata_upgraded = False
    with _feedback_locks(package, target):
        # Re-read both endpoints only after the canonical dual lock is held.
        # This serializes A->B against B->A and closes the check/write race.
        document = _creator_correction_document(package, package_id=package_path)
        target_document = _creator_correction_document(target, package_id=target_path)
        if "successor_retirement" in target_document:
            target_status = successor_feedback_retirement_status(
                target, workspace_root=workspace
            )
            if target_status.get("retired"):
                raise ValueError("superseding successor is already retired")
            raise ValueError("superseding successor has invalid retirement metadata")
        existing = document.get("successor_retirement")
        if existing is not None:
            if not isinstance(existing, Mapping):
                raise ValueError("existing successor retirement metadata is invalid")
            if existing.get("schema_version") == SUCCESSOR_RETIREMENT_SCHEMA_VERSION:
                status = successor_feedback_retirement_status(
                    package, workspace_root=workspace
                )
                if (
                    status.get("retired")
                    and status.get("superseded_by_package_path") == target_path
                    and status.get("retired_by") == retired_by
                    and status.get("reason_exact") == reason_exact
                ):
                    return {**status, "idempotent": True, "metadata_upgraded": False}
                raise ValueError("successor already has different or invalid retirement metadata")
            legacy = _validate_legacy_retirement_for_migration(
                workspace,
                package,
                package_path,
                target,
                target_path,
                document,
                target_document,
            )
            if (
                legacy["retired_by"] != retired_by
                or legacy["reason_exact"] != reason_exact
            ):
                raise ValueError("legacy retirement migration requires the original actor and exact reason")
            source_rows = legacy["source_rows"]
            retired_at = legacy["retired_at"]
            migration_provenance: dict[str, Any] | None = {
                "from_schema_version": LEGACY_SUCCESSOR_RETIREMENT_SCHEMA_VERSION,
                "from_retirement_id": legacy["legacy_retirement_id"],
                "migrated_at": datetime.now(timezone.utc).isoformat(),
                "migrated_by": retired_by,
                "authorization_reason_exact": reason_exact,
            }
            metadata_upgraded = True
        else:
            source_rows = _successor_feedback_lineage(
                document, package_path=package_path, workspace_root=workspace
            )
            target_rows = _successor_feedback_lineage(
                target_document, package_path=target_path, workspace_root=workspace
            )
            if not _lineage_origins(source_rows).issubset(
                _lineage_origins(target_rows)
            ):
                raise ValueError("superseding successor does not carry every live feedback origin")
            retired_at = datetime.now(timezone.utc).isoformat()
            migration_provenance = None
        retired_document_sha256 = _retirement_document_fingerprint(document)
        identity_payload = _retirement_identity_payload(
            package_path=package_path,
            target_path=target_path,
            source_rows=source_rows,
            retired_document_sha256=retired_document_sha256,
            retired_at=retired_at,
            retired_by=retired_by,
            reason_exact=reason_exact,
            migration_provenance=migration_provenance,
        )
        retirement_id = _stable_fingerprint(
            identity_payload, namespace=SUCCESSOR_RETIREMENT_SCHEMA_VERSION
        )
        document["successor_retirement"] = {
            "schema_version": SUCCESSOR_RETIREMENT_SCHEMA_VERSION,
            "retirement_id": retirement_id,
            "retired_at": retired_at,
            "retired_by": retired_by,
            "reason_exact": reason_exact,
            "superseded_by_package_path": target_path,
            "carried_feedback_lineage": source_rows,
            "retired_document_sha256": retired_document_sha256,
            "production_state_effect": "none",
        }
        if migration_provenance is not None:
            document["successor_retirement"]["migration_provenance"] = migration_provenance
        _atomic_write_json(package / "creator-correction.json", document)
    status = successor_feedback_retirement_status(package, workspace_root=workspace)
    if not status.get("retired"):
        raise ValueError("written successor retirement did not validate")
    return {
        **status,
        "idempotent": False,
        "metadata_upgraded": metadata_upgraded,
    }


def _find_feedback_event(document: Mapping[str, Any], feedback_id: str) -> dict[str, Any]:
    events = document.get("events")
    if not isinstance(events, list):
        raise ValueError("creator-correction/v3 requires an events array.")
    for event in events:
        if isinstance(event, dict) and event.get("feedback_id") == feedback_id:
            return event
    raise ValueError(f"Unknown creator feedback event: {feedback_id}")


def backfill_creator_correction(package_dir: Path, *, workspace_root: Path) -> dict[str, Any]:
    """Normalize historical metadata with complete source payload preservation."""

    root = Path(package_dir).resolve(strict=True)
    workspace = Path(workspace_root).resolve(strict=True)
    package_id = root.relative_to(workspace).as_posix()
    from evals.feedback_cases import ensure_feedback_case, evaluate_feedback_case, feedback_eval_task_id
    from pipeline.agentic.learning_loop import capture_learning_event

    with _feedback_lock(root):
        document = _creator_correction_document(root, package_id=package_id)
        # Never waive a live correction or reset an existing v3 lifecycle.
        source_path = root / "creator-correction.json"
        if source_path.is_file():
            source = json.loads(source_path.read_text(encoding="utf-8"))
            if source.get("schema_version") == CREATOR_CORRECTION_SCHEMA_VERSION:
                return document
        for event in document["events"]:
            event_id = f"event-feedback-{event['feedback_id']}"
            event["learning_event_id"] = event_id
            event["eval_task_ids"] = [feedback_eval_task_id(event["feedback_id"])]
            event["historical_only"] = True
            event["captured_at"] = event.get("captured_at") or root.parent.name
            event["root_cause"] = event.get("root_cause") or "Historical correction; original cause was not separately recorded."
            event["action_taken"] = event.get("action_taken") or {"type": "metadata_backfill"}
            event["resolution_evidence"] = event.get("resolution_evidence") or ["creator-correction.json"]
            event["eval_waiver_reason"] = event.get("eval_waiver_reason") or (
                "Historical correction predates feedback regression capture; only metadata is normalized, without claiming a new pixel review or changing media."
            )
            event["status"] = "evaluated"
        _atomic_write_json(root / "creator-correction.json", document)
    for event in document["events"]:
        ensure_feedback_case(workspace, root, event)
        evaluate_feedback_case(workspace, root, event)
        capture_learning_event(
            workspace, source="creator_feedback", summary=str(event.get("root_cause") or event["primary_diagnosis"]),
            evidence_paths=[f"{package_id}/creator-correction.json"], event_id=event["learning_event_id"],
            user_instruction_exact=event["user_instruction_exact"], diagnosis=event["primary_diagnosis"],
            scope=event["scope"], package_path=package_id, feedback_status="evaluated",
            resolution_evidence=event["resolution_evidence"], eval_disposition="waived",
            feedback_metadata={"feedback_id": event["feedback_id"], "eval_task_ids": event["eval_task_ids"], "historical_only": True},
        )
    return document


def update_creator_feedback_event(
    package_dir: Path,
    feedback_id: str,
    *,
    updates: Mapping[str, Any],
    expected_status: str | None = None,
) -> dict[str, Any]:
    """Atomically update lifecycle metadata without replacing event identity."""

    root = Path(package_dir).expanduser().resolve(strict=True)
    target = root / "creator-correction.json"
    if target.is_symlink():
        raise ValueError("creator-correction.json cannot be a symlink.")
    with _feedback_lock(root):
        document = _creator_correction_document(root, package_id=str(root))
        event = _find_feedback_event(document, feedback_id)
        current = str(event.get("status") or "captured")
        if expected_status is not None and current != expected_status:
            raise ValueError(
                f"Feedback {feedback_id} expected status {expected_status}, got {current}."
            )
        requested = str(updates.get("status") or current)
        if requested != current and requested not in CREATOR_FEEDBACK_TRANSITIONS.get(
            current, frozenset()
        ):
            raise ValueError(f"Invalid feedback transition: {current} -> {requested}")
        immutable = {"feedback_id", "captured_at", "user_instruction_exact", "user_instruction_sha256"}
        if immutable.intersection(updates):
            raise ValueError("Feedback identity and exact creator wording are immutable.")
        event.update(dict(updates))
        normalized = _event_defaults(event)
        event.clear()
        event.update(normalized)
        _atomic_write_json(target, document)
        return dict(event)


def _json_pointer_tokens(pointer: str) -> list[str]:
    if not pointer.startswith("/"):
        raise ValueError("repair json_pointer must start with /")
    return [part.replace("~1", "/").replace("~0", "~") for part in pointer[1:].split("/")]


def _replace_json_pointer(document: Any, pointer: str, value: Any) -> None:
    tokens = _json_pointer_tokens(pointer)
    if not tokens:
        raise ValueError("repair cannot replace an entire artifact")
    cursor = document
    for token in tokens[:-1]:
        if isinstance(cursor, list):
            try:
                index = int(token)
                if index < 0:
                    raise ValueError("negative list index")
                cursor = cursor[index]
            except (IndexError, TypeError, ValueError) as exc:
                raise ValueError(f"invalid list segment in repair pointer: {pointer}") from exc
        elif isinstance(cursor, dict) and token in cursor:
            cursor = cursor[token]
        else:
            raise ValueError(f"repair pointer does not exist: {pointer}")
    leaf = tokens[-1]
    if isinstance(cursor, list):
        try:
            index = int(leaf)
        except ValueError as exc:
            raise ValueError(f"invalid list index in repair pointer: {pointer}") from exc
        if index < 0 or index >= len(cursor):
            raise ValueError(f"repair list index is out of range: {pointer}")
        cursor[index] = value
    elif isinstance(cursor, dict) and leaf in cursor:
        cursor[leaf] = value
    else:
        raise ValueError(f"repair pointer does not exist: {pointer}")


def _safe_feedback_artifact(package_dir: Path, relative: str) -> Path:
    if not relative.strip() or Path(relative).is_absolute() or ".." in Path(relative).parts:
        raise ValueError(f"feedback artifact must be package-relative: {relative}")
    root = package_dir.resolve(strict=True)
    path = root / relative
    cursor = root
    for part in Path(relative).parts:
        cursor /= part
        if cursor.is_symlink():
            raise ValueError(f"feedback artifact cannot traverse a symlink: {relative}")
    try:
        path.resolve(strict=False).relative_to(root)
    except ValueError as exc:
        raise ValueError(f"feedback artifact leaves package: {relative}") from exc
    return path


def revise_creator_feedback_assertions(
    package_dir: Path, *, workspace_root: Path, feedback_id: str,
    verification_assertions: Iterable[Mapping[str, Any]] | None = None,
    diagnosis: str | None = None, must_change: list[str] | None = None,
    must_preserve: list[str] | None = None,
    repair_operations: Iterable[Mapping[str, Any]] | None = None,
    affected_artifacts: list[str] | None = None, eval_waiver_reason: str | None = None,
    revised_by: str, reason: str,
) -> dict[str, Any]:
    """Revise executable expectations with an audit trail, retaining original feedback."""
    from evals.feedback_cases import revise_feedback_case_assertions
    from pipeline.stages.carousel_generation_state import require_writable_package

    root = Path(package_dir).resolve(strict=True)
    require_writable_package(root)
    if not _feedback_package_is_writable_v3(root):
        raise ValueError("Archived packages are read-only; revise their successor.")
    assertions = (_normalize_verification_assertions(verification_assertions)
                  if verification_assertions is not None else None)
    operations = (_normalize_repair_operations(repair_operations)
                  if repair_operations is not None else None)
    with _feedback_lock(root):
        document = _creator_correction_document(root, package_id=str(root))
        event = _find_feedback_event(document, feedback_id)
        case = revise_feedback_case_assertions(
            workspace_root, root, event, assertions, revised_by=revised_by, reason=reason,
            diagnosis=diagnosis, must_change=must_change, must_preserve=must_preserve,
            repair_operations=operations, affected_artifacts=affected_artifacts,
            **({"eval_waiver_reason": eval_waiver_reason} if eval_waiver_reason is not None else {}),
        )
        event["verification_assertions"] = case["verification_assertions"]
        event["primary_diagnosis"] = case["diagnosis"]
        event["must_change"] = case["must_change"]
        event["must_preserve"] = case["must_preserve"]
        event["repair_operations"] = case["repair_operations"]
        event["eval_waiver_reason"] = case.get("eval_waiver_reason")
        event["affected_artifacts"] = list(case["affected_artifacts"])
        event["eval_task_ids"] = [case["task_id"]]
        _atomic_write_json(root / "creator-correction.json", document)
    return case


def apply_creator_feedback_revision(
    package_dir: Path,
    *,
    workspace_root: Path,
    feedback_id: str,
) -> dict[str, Any]:
    """Repair the same package, bind evidence, and run its deterministic eval."""

    root = Path(package_dir).expanduser().resolve(strict=True)
    workspace = Path(workspace_root).expanduser().resolve(strict=True)
    from pipeline.stages.carousel_generation_state import require_writable_package

    require_writable_package(root)
    if not _feedback_package_is_writable_v3(root):
        raise ValueError("Archived or incomplete carousel packages are read-only; create a new v3 package.")
    target = root / "creator-correction.json"
    with _feedback_lock(root):
        document = _creator_correction_document(root, package_id=str(root))
        event = _find_feedback_event(document, feedback_id)
        current = str(event.get("status") or "captured")
        if current == "learning_declined":
            event["learning_disposition"] = "declined"
        from evals.feedback_cases import ensure_feedback_case

        case = ensure_feedback_case(workspace, root, event)
        event["eval_task_ids"] = [case["task_id"]]
        if current in {"evaluated", "learning_proposed", "learning_declined", "approved", "promoted"}:
            from evals.feedback_cases import load_feedback_case, feedback_case_is_current
            from pipeline.stages.carousel_generation_state import read_generation_state

            saved = load_feedback_case(workspace, str(event["eval_task_ids"][0]))
            if saved.get("status") in {"passed", "waived"} and feedback_case_is_current(root, saved, event):
                return {"feedback": dict(event), "evaluation": saved, "generation_state": read_generation_state(root)}
        if current not in {"diagnosed", "applied", "evaluated", "learning_declined", "learning_proposed", "approved"}:
            raise ValueError(
                f"Feedback {feedback_id} cannot be revised from status {current}."
            )
        before: dict[str, str | None] = {}
        after: dict[str, str | None] = {}
        grouped: dict[str, list[Mapping[str, Any]]] = {}
        pending_writes: dict[Path, Any] = {}
        for operation in event.get("repair_operations") or []:
            grouped.setdefault(str(operation["artifact"]), []).append(operation)
        for relative, operations in grouped.items():
            path = _safe_feedback_artifact(root, relative)
            if not path.is_file():
                raise ValueError(f"repair artifact does not exist: {relative}")
            raw = path.read_bytes()
            before[relative] = "sha256:" + hashlib.sha256(raw).hexdigest()
            try:
                payload = json.loads(raw.decode("utf-8"))
            except (UnicodeDecodeError, json.JSONDecodeError) as exc:
                raise ValueError(f"repair operations require a JSON artifact: {relative}") from exc
            for operation in operations:
                _replace_json_pointer(payload, str(operation["json_pointer"]), operation["value"])
            pending_writes[path] = payload
            encoded = (json.dumps(payload, indent=2, ensure_ascii=False) + "\n").encode("utf-8")
            after[relative] = "sha256:" + hashlib.sha256(encoded).hexdigest()

        affected = _string_list(event.get("affected_artifacts"))
        for relative in affected:
            path = _safe_feedback_artifact(root, relative)
            if relative not in before:
                from evals.feedback_cases import artifact_hashes

                before[relative] = (
                    (artifact_hashes(root, [relative]).get(relative))
                )
                after[relative] = before[relative]
        waiver = str(event.get("eval_waiver_reason") or "").strip()
        changed = [name for name in grouped if before.get(name) != after.get(name)]
        if grouped and not changed and not event.get("action_taken"):
            raise ValueError("declared repair did not change any targeted artifact")
        if not grouped and not waiver:
            from evals.feedback_cases import load_feedback_case

            task_id = str((event.get("eval_task_ids") or [""])[0])
            baseline = load_feedback_case(workspace, task_id).get("baseline_artifact_hashes") or {}
            from evals.feedback_cases import artifact_hashes

            now = artifact_hashes(root, affected)
            changed = [name for name in affected if now.get(name) != baseline.get(name)]
            after.update(now)
            if not changed and not event.get("verification_assertions"):
                raise ValueError(
                    "No repair was detected. Apply the correction to the existing package "
                    "or supply explicit --repair-json operations before revise."
                )

        for path, payload in pending_writes.items():
            _atomic_write_json(path, payload)
        previous_action = event.get("action_taken")
        event["action_taken"] = {
            "type": "existing_package_repair" if changed and grouped else (
                "verification_of_current_state" if not waiver else "documented_eval_waiver"
            ),
            "artifacts_changed": changed if grouped else [],
            "artifact_changes_since_capture": changed if not grouped else [],
            "before_sha256": before,
            "after_sha256": after,
        }
        if previous_action:
            event.setdefault("action_history", []).append(previous_action)
        event["resolution_evidence"] = sorted(
            set(_string_list(event.get("resolution_evidence")) + changed + [
                item["artifact"] for item in event.get("verification_assertions") or []
            ])
        )
        if waiver and not event["resolution_evidence"]:
            event["resolution_evidence"] = ["creator-correction.json"]
        event["status"] = "applied"
        normalized = _event_defaults(event)
        event.clear()
        event.update(normalized)
        _atomic_write_json(target, document)

    try:
        from pipeline.stages.codex_builtin_image_generation import reconcile_package_state

        from pipeline.stages.carousel_generation_state import read_generation_state
        state = read_generation_state(root)
        if state.get("schema_version") == "carousel-generation-state/v3":
            state = reconcile_package_state(root)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        state = {"status": "blocked", "next_action": "repair_inputs", "reason": str(exc)}

    from evals.feedback_cases import evaluate_feedback_case

    result = evaluate_feedback_case(workspace, root, event)
    updated = update_creator_feedback_event(
        root,
        feedback_id,
        updates={"status": "evaluated"},
        expected_status="applied",
    )
    from pipeline.agentic.learning_loop import update_learning_event

    learning_event_id = str(updated.get("learning_event_id") or "")
    if learning_event_id:
        update_learning_event(
            workspace,
            learning_event_id,
            feedback_status="evaluated",
            resolution_evidence=list(updated.get("resolution_evidence") or []),
            eval_disposition=str(result["status"]),
        )
    from pipeline.agentic.langfuse_mirror import mirror_feedback_event

    mirror_feedback_event(
        updated,
        eval_scores={"deterministic": str(result.get("status") or "")},
    )
    if result.get("status") == "passed":
        proposal = propose_feedback_learning_if_eligible(
            root,
            workspace_root=workspace,
            feedback_id=feedback_id,
        )
        if proposal is not None:
            updated = next(
                item
                for item in creator_feedback_records(root)
                if item.get("feedback_id") == feedback_id
            )
    return {"feedback": updated, "evaluation": result, "generation_state": state}


def creator_feedback_status(
    package_dir: Path,
    *,
    workspace_root: Path,
    feedback_id: str | None = None,
) -> dict[str, Any]:
    """Return lifecycle and eval evidence without changing the package."""

    from evals.feedback_cases import load_feedback_case, feedback_case_is_current

    records = creator_feedback_records(package_dir)
    if feedback_id:
        records = [record for record in records if record.get("feedback_id") == feedback_id]
        if not records:
            raise ValueError(f"Unknown creator feedback event: {feedback_id}")
    evaluations: dict[str, Any] = {}
    for record in records:
        for task_id in record.get("eval_task_ids") or []:
            try:
                evaluations[str(task_id)] = load_feedback_case(workspace_root, str(task_id))
                if evaluations[str(task_id)].get("status") in {"passed", "waived"} and not feedback_case_is_current(package_dir, evaluations[str(task_id)], record):
                    evaluations[str(task_id)] = {**evaluations[str(task_id)], "status": "stale"}
            except (FileNotFoundError, OSError, ValueError):
                evaluations[str(task_id)] = {"status": "missing"}
    unresolved = [
        str(record["feedback_id"])
        for record in records
        if (record.get("kind") in {"correction", "rejection"} or record.get("must_change"))
        and (
            record.get("status") not in {"evaluated", "learning_proposed", "learning_declined", "approved", "promoted", "rejected"}
            or (any(
                evaluations.get(str(task_id), {}).get("status") not in {"passed", "waived"}
                for task_id in record.get("eval_task_ids") or ([] if record.get("eval_waiver_reason") else [""])
            ))
        )
    ]
    return {
        "schema_version": CREATOR_CORRECTION_SCHEMA_VERSION,
        "events": records,
        "evaluations": evaluations,
        "unresolved_feedback_ids": unresolved,
        "status": "blocked" if unresolved else "ready",
    }


def _learning_target_for_diagnosis(diagnosis: str) -> str:
    return {
        "concept_recognition": "config/rules/golden-theme.md",
        "voice_copy": "config/rules/voice.md",
        "scene_action": "config/rules/visual-variety.md",
        "identity_reference": "config/rules/identity.md",
        "exact_text_layout": "config/rules/on-image-text.md",
        "dimensions_brandmark": "config/rules/image-dimensions.md",
        "instruction_drift": "config/skills/carousel-jam-runtime-context.md",
        "runtime_tool_failure": "config/skills/carousel-jam-autopilot.md",
        "provenance_qa": "config/skills/illustration-carousel-framework.md",
        "carousel_intelligence_calibration": "config/skills/instagram-carousel-intelligence.md",
    }[diagnosis]


_LEARNING_BEHAVIOR_STOPWORDS = frozenset(
    {
        "a",
        "an",
        "and",
        "are",
        "as",
        "at",
        "be",
        "both",
        "by",
        "do",
        "for",
        "from",
        "have",
        "in",
        "is",
        "it",
        "keep",
        "make",
        "must",
        "need",
        "of",
        "on",
        "or",
        "partner",
        "partners",
        "please",
        "should",
        "show",
        "that",
        "the",
        "their",
        "them",
        "they",
        "to",
        "use",
        "visible",
        "with",
    }
)
_LEARNING_BEHAVIOR_ALIASES = {
    "act": "action",
    "actions": "action",
    "acting": "action",
    "acts": "action",
    "couple": "relationship",
    "couples": "relationship",
    "dimensions": "dimension",
    "formats": "format",
    "movements": "movement",
    "poses": "pose",
    "portraits": "portrait",
    "scenes": "scene",
    "shots": "shot",
    "together": "shared",
}
_TRANSFERABLE_BEHAVIOR_TERMS = frozenset(
    {
        "action",
        "body",
        "brandmark",
        "camera",
        "caption",
        "clothing",
        "copy",
        "dimension",
        "exact",
        "expression",
        "face",
        "format",
        "generation",
        "hair",
        "hash",
        "hook",
        "identity",
        "instruction",
        "layout",
        "movement",
        "palette",
        "pose",
        "portrait",
        "prompt",
        "proportion",
        "provenance",
        "qa",
        "receipt",
        "recognition",
        "reference",
        "relationship",
        "runtime",
        "scene",
        "setting",
        "shared",
        "shot",
        "size",
        "text",
        "tool",
        "typography",
        "variety",
        "voice",
        "wardrobe",
    }
)
_STRONG_TRANSFERABLE_BEHAVIOR_TERMS = frozenset(
    {"brandmark", "identity", "provenance", "typography"}
)
_PACKAGE_LOCAL_LANGUAGE = re.compile(
    r"(?:\bthis (?:carousel|package|post|slide|story)\b|"
    r"\b(?:slide|frame|asset)\s*#?\d+\b|"
    r"(?:^|\s)(?:slides|frames|assets)\s+\d+(?:\s*(?:,|and|to|-)\s*\d+)+\b|"
    r"(?:^|[\\/])(?:slides|final|proof|candidates?)(?:[\\/]|$)|"
    r"\.(?:json|png|jpe?g|webp|mp4)\b)",
    flags=re.IGNORECASE,
)


def _learning_behavior_text(event: Mapping[str, Any]) -> str:
    """Return the diagnosed behavior, never package copy or root-cause prose."""

    parts = _string_list(event.get("must_change"))
    desired = str(event.get("desired_behavior") or "").strip()
    if desired:
        parts.append(desired)
    if not parts:
        parts.append(str(event.get("user_instruction_exact") or ""))
    return " ; ".join(part for part in parts if part.strip())


def _normalized_learning_behavior(event: Mapping[str, Any]) -> tuple[str, frozenset[str]]:
    """Build a deterministic semantic key from the requested behavior.

    This intentionally ignores the diagnosis label.  Diagnosis alone is too
    broad to establish that two creator corrections describe the same durable
    rule.
    """

    text = unicodedata.normalize("NFKC", _learning_behavior_text(event)).casefold()
    raw_tokens = re.findall(r"[a-z0-9]+", text)
    tokens: list[str] = []
    for raw in raw_tokens:
        token = _LEARNING_BEHAVIOR_ALIASES.get(raw, raw)
        if token in _LEARNING_BEHAVIOR_STOPWORDS:
            continue
        if token in _TRANSFERABLE_BEHAVIOR_TERMS:
            tokens.append(token)
            continue
        if len(token) > 4 and token.endswith("ing"):
            token = token[:-3]
        elif len(token) > 4 and token.endswith("ed"):
            token = token[:-2]
        token = _LEARNING_BEHAVIOR_ALIASES.get(token, token)
        if token:
            tokens.append(token)
    unique = frozenset(tokens)
    return " ".join(sorted(unique)), unique


def _learning_behaviors_match(
    event: Mapping[str, Any],
    other: Mapping[str, Any],
) -> bool:
    left_key, left = _normalized_learning_behavior(event)
    right_key, right = _normalized_learning_behavior(other)
    if not left or not right:
        return False
    if left_key == right_key:
        return True
    # Negated and affirmative instructions are never semantic matches.
    negators = {"no", "not", "never", "without"}
    if bool(left & negators) != bool(right & negators):
        return False
    overlap = len(left & right)
    union = len(left | right)
    return overlap >= 2 and overlap / union >= 0.72


def _feedback_is_transferable_learning(event: Mapping[str, Any]) -> bool:
    """Reject package facts while retaining portable creative constraints."""

    behavior = _learning_behavior_text(event)
    if not behavior.strip() or _PACKAGE_LOCAL_LANGUAGE.search(behavior):
        return False
    _, tokens = _normalized_learning_behavior(event)
    portable = tokens & _TRANSFERABLE_BEHAVIOR_TERMS
    return len(portable) >= 2 or bool(portable & _STRONG_TRANSFERABLE_BEHAVIOR_TERMS)


def _learning_pattern_key(event: Mapping[str, Any], target_path: str) -> str:
    behavior_key, _ = _normalized_learning_behavior(event)
    payload = {
        "diagnosis": str(event.get("primary_diagnosis") or ""),
        "normalized_behavior": behavior_key,
        "target_path": target_path,
    }
    return "sha256:" + hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()


def propose_feedback_learning_if_eligible(
    package_dir: Path,
    *,
    workspace_root: Path,
    feedback_id: str,
) -> dict[str, Any] | None:
    """Create a real, inactive proposal only for explicit or repeated patterns."""

    root = Path(package_dir).resolve(strict=True)
    workspace = Path(workspace_root).resolve(strict=True)
    event = next(
        item for item in creator_feedback_records(root) if item["feedback_id"] == feedback_id
    )
    if (event.get("status") != "evaluated" or event.get("historical_only")
            or event.get("learning_disposition") == "declined"):
        return None
    from evals.feedback_cases import load_feedback_case, feedback_case_is_current

    def passed_current(candidate: Mapping[str, Any], package: Path) -> bool:
        ids = candidate.get("eval_task_ids") or []
        if not ids:
            return False
        try:
            return all(
                (case := load_feedback_case(workspace, str(task_id))).get("status") == "passed"
                and feedback_case_is_current(package, case, candidate)
                for task_id in ids
            )
        except (OSError, ValueError):
            return False

    if not passed_current(event, root):
        return None
    exact = str(event.get("user_instruction_exact") or "")
    explicit = bool(re.search(r"\b(always|never)\b", exact, flags=re.IGNORECASE))
    diagnosis = str(event["primary_diagnosis"])
    if not _feedback_is_transferable_learning(event):
        return None
    matching_packages: set[str] = set()
    matching_events: list[Mapping[str, Any]] = []
    for path in workspace.glob("output/carousels/**/creator-correction.json"):
        try:
            for other in creator_feedback_records(path.parent):
                if (
                    other.get("primary_diagnosis") == diagnosis
                    and other.get("status") in {"evaluated", "learning_proposed", "approved", "promoted"}
                    and not other.get("historical_only")
                    and other.get("learning_disposition") != "declined"
                    and other.get("feedback_id") != feedback_id
                    and path.parent.resolve() != root
                    and _feedback_is_transferable_learning(other)
                    and _learning_behaviors_match(event, other)
                    and passed_current(other, path.parent)
                ):
                    matching_packages.add(path.parent.resolve().as_posix())
                    matching_events.append(other)
        except (OSError, ValueError, json.JSONDecodeError):
            continue
    if not explicit and not matching_packages:
        return None

    event_id = str(event.get("learning_event_id") or "")
    proposal_dir = workspace / "memory" / "agentic" / "learning-proposals"
    for proposal_path in proposal_dir.glob("*.json"):
        try:
            proposal = json.loads(proposal_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        if proposal.get("source_event_id") == event_id:
            return proposal

    target_relative = _learning_target_for_diagnosis(diagnosis)
    pattern_key = _learning_pattern_key(event, target_relative)
    supporting_event_ids = sorted(
        {
            event_id,
            *(
                str(other.get("learning_event_id") or "")
                for other in matching_events
                if other.get("learning_event_id")
            ),
        }
        - {""}
    )
    supporting_packages = sorted(
        {
            root.relative_to(workspace).as_posix(),
            *(Path(value).relative_to(workspace).as_posix() for value in matching_packages),
        }
    )
    for proposal_path in proposal_dir.glob("*.json"):
        try:
            proposal = json.loads(proposal_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        if (
            proposal.get("target_path") == target_relative
            and (
                proposal.get("learning_pattern_key") == pattern_key
                or (
                    isinstance(proposal.get("normalized_behavior"), str)
                    and _learning_behaviors_match(
                        event,
                        {"desired_behavior": proposal["normalized_behavior"]},
                    )
                )
            )
        ):
            if proposal.get("status") in {"draft", "approved"}:
                proposal["supporting_event_ids"] = sorted(
                    set(_string_list(proposal.get("supporting_event_ids")))
                    | set(supporting_event_ids)
                )
                proposal["supporting_package_paths"] = sorted(
                    set(_string_list(proposal.get("supporting_package_paths")))
                    | set(supporting_packages)
                )
                from pipeline.agentic.learning_loop import atomic_write_text

                atomic_write_text(
                    proposal_path,
                    json.dumps(proposal, indent=2, ensure_ascii=False) + "\n",
                )
            return {
                **proposal,
                "deduplicated": True,
                "existing_proposal_path": proposal_path.relative_to(workspace).as_posix(),
            }
    target = workspace / target_relative
    current = target.read_text(encoding="utf-8")
    change = _learning_behavior_text(event)
    preserve = "; ".join(
        item for item in _string_list(event.get("must_preserve"))
        if _feedback_is_transferable_learning({"desired_behavior": item})
    ) or "Existing canonical constraints."
    addition = "\n".join(
        [
            "",
            f"## Creator correction {feedback_id}",
            "",
            f"- Required behavior: {change}",
            f"- Preserve: {preserve}",
            f"- Diagnosis: `{diagnosis}`.",
            f"- Evidence: `{root.relative_to(workspace).as_posix()}/creator-correction.json`.",
            "",
        ]
    )
    from pipeline.agentic.learning_loop import create_learning_proposal

    proposal_path = create_learning_proposal(
        workspace,
        source_event_id=event_id,
        target_path=target_relative,
        proposed_action="modify",
        rationale=(
            "Explicit always/never creator instruction."
            if explicit
            else "Same diagnosed failure occurred across two independent packages."
        ),
        proposed_content=current.rstrip() + "\n" + addition,
        required_validators=["skill_eval", "creator_workflow_contract", "agentic_docs_contract"],
        dedupe_key=pattern_key,
        normalized_behavior=_normalized_learning_behavior(event)[0],
        supporting_event_ids=supporting_event_ids,
        supporting_package_paths=supporting_packages,
    )
    proposal = json.loads(proposal_path.read_text(encoding="utf-8"))
    if proposal.get("source_event_id") != event_id:
        return {
            **proposal,
            "deduplicated": True,
            "existing_proposal_path": proposal_path.relative_to(workspace).as_posix(),
        }
    update_creator_feedback_event(
        root,
        feedback_id,
        updates={"status": "learning_proposed", "learning_proposal_id": proposal["proposal_id"]},
        expected_status="evaluated",
    )
    from pipeline.agentic.learning_loop import update_learning_event

    update_learning_event(
        workspace,
        event_id,
        feedback_status="learning_proposed",
        resolution_evidence=list(event.get("resolution_evidence") or []),
        eval_disposition="passed",
    )
    return proposal


def _constraint_slide_targets(clause: str) -> set[int]:
    """Read explicit slide labels from derived constraints, never raw feedback."""
    targets: set[int] = set()
    for match in re.finditer(r"\bslides?\s+(\d+(?:\s*(?:,|and|&)\s*\d+)*)", clause, re.I):
        targets.update(int(value) for value in re.findall(r"\d+", match.group(1)))
    return targets


def active_feedback_constraints(
    package_dir: Path,
    slide_number: int,
) -> list[dict[str, Any]]:
    """Return only stable, generation-facing constraints for one slide."""

    records = creator_feedback_records(package_dir)
    superseded = {
        str(record.get("supersedes_feedback_id"))
        for record in records
        if record.get("supersedes_feedback_id") and record.get("status") != "rejected"
    }
    constraints: list[dict[str, Any]] = []
    for record in records:
        feedback_id = str(record.get("feedback_id") or "")
        effect = str(record.get("generation_effect") or "none")
        slides = {int(value) for value in record.get("slides") or []}
        must_change = _string_list(record.get("must_change"))
        must_preserve = _string_list(record.get("must_preserve"))
        if effect == "none" and record.get("kind") == "approval" and must_change:
            effect = "slide_local" if slides else "shared"
        # A package-scoped event may contain only explicitly targeted clauses.
        # Project those clauses before compiling, while retaining exact source text.
        must_change = [clause for clause in must_change if not _constraint_slide_targets(clause)
                       or int(slide_number) in _constraint_slide_targets(clause)]
        must_preserve = [clause for clause in must_preserve if not _constraint_slide_targets(clause)
                         or int(slide_number) in _constraint_slide_targets(clause)]
        if (
            not feedback_id
            or feedback_id in superseded
            or record.get("historical_only") is True
            or record.get("status") == "rejected"
            or effect not in {"slide_local", "shared"}
            or (effect == "slide_local" and int(slide_number) not in slides)
            # Exact feedback remains durable evidence, but it must not churn
            # prompt bytes or invalidate generated work until Codex has derived
            # an explicit generation-facing change/preserve projection.
            or not (must_change or must_preserve)
        ):
            continue
        constraints.append(
            {
                "feedback_id": feedback_id,
                "must_change": must_change,
                "must_preserve": must_preserve,
            }
        )
    return sorted(constraints, key=lambda item: item["feedback_id"])


@contextmanager
def _feedback_lock(package_dir: Path) -> Iterable[None]:
    root = Path(package_dir).resolve(strict=True)
    internal = root / ".internal"
    if internal.is_symlink():
        raise ValueError(".internal cannot be a symlink.")
    internal.mkdir(exist_ok=True)
    lock_path = internal / "creator-feedback.lock"
    flags = os.O_CREAT | os.O_RDWR
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW
    descriptor = os.open(lock_path, flags, 0o600)
    try:
        fcntl.flock(descriptor, fcntl.LOCK_EX)
        yield
    finally:
        fcntl.flock(descriptor, fcntl.LOCK_UN)
        os.close(descriptor)


@contextmanager
def _feedback_locks(*package_dirs: Path) -> Iterable[None]:
    """Lock retirement endpoints in canonical order to prevent inverse races."""

    ordered = sorted({Path(path).resolve(strict=True) for path in package_dirs}, key=str)
    with ExitStack() as stack:
        for package in ordered:
            stack.enter_context(_feedback_lock(package))
        yield


def _atomic_write_json(path: Path, payload: Mapping[str, Any]) -> None:
    text = json.dumps(payload, indent=2, ensure_ascii=False) + "\n"
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{path.name}.",
        suffix=".tmp",
        dir=path.parent,
    )
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            handle.write(text)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    finally:
        if temporary.exists():
            temporary.unlink()


def _feedback_package_is_writable_v3(package_dir: Path) -> bool:
    """Return whether normalized feedback may be written inside this package.

    Historical and incomplete packages are immutable provenance.  Feedback for
    them may still become a workspace LearningEvent, but it must not create a
    correction artifact, lock directory, eval case, or implicit state upgrade.
    """

    from pipeline.stages.carousel_generation_state import archived_package_read_only_reason

    if archived_package_read_only_reason(package_dir):
        return False
    state_path = package_dir / "generation-state.json"
    if state_path.is_symlink() or not state_path.is_file():
        return False
    try:
        payload = json.loads(state_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError):
        return False
    return (
        isinstance(payload, Mapping)
        and payload.get("schema_version") == "carousel-generation-state/v3"
    )


def record_creator_feedback(
    package_dir: Path,
    *,
    workspace_root: Path,
    user_instruction_exact: str,
    kind: str,
    scope: str,
    slide_numbers: Iterable[int] = (),
    diagnosis: str | None = None,
    primary_diagnosis: str | None = None,
    secondary_diagnoses: Iterable[str] = (),
    root_cause: str | None = None,
    desired_behavior: str | None = None,
    must_change: Iterable[str] = (),
    must_preserve: Iterable[str] = (),
    affected_artifacts: Iterable[str] = (),
    repair_operations: Iterable[Mapping[str, Any]] = (),
    verification_assertions: Iterable[Mapping[str, Any]] = (),
    asset_sha256: str | None = None,
    eval_waiver_reason: str | None = None,
    generation_effect: str | None = None,
    supersedes_feedback_id: str | None = None,
) -> dict[str, Any]:
    """Append one normalized correction, eval case, and linked LearningEvent."""

    supplied = Path(package_dir).expanduser()
    if supplied.is_symlink():
        raise ValueError("Carousel package cannot be a symlink.")
    root = supplied.resolve(strict=True)
    if not root.is_dir():
        raise ValueError("Carousel package must be a directory.")
    if not user_instruction_exact.strip():
        raise ValueError("Creator feedback text cannot be empty.")
    if kind not in CREATOR_FEEDBACK_KINDS:
        raise ValueError(f"Unsupported creator feedback kind: {kind}")
    if scope not in CREATOR_FEEDBACK_SCOPES:
        raise ValueError(f"Unsupported creator feedback scope: {scope}")
    slides = sorted({int(value) for value in slide_numbers})
    if any(value < 1 for value in slides):
        raise ValueError("Feedback slide numbers must be positive integers.")
    if scope in {"slide", "copy"} and not slides:
        raise ValueError(f"{scope}-scoped feedback requires at least one --slide.")
    if asset_sha256 is not None and not str(asset_sha256).startswith("sha256:"):
        asset_sha256 = "sha256:" + str(asset_sha256)
    if scope == "asset" and not asset_sha256:
        raise ValueError("Asset-scoped feedback requires --asset-sha.")
    if asset_sha256 and not re.fullmatch(r"sha256:[0-9a-f]{64}", asset_sha256):
        raise ValueError("asset_sha256 must be sha256:<64 lowercase hex>.")
    if scope == "asset" and not slides:
        from pipeline.stages.carousel_generation_state import read_generation_state

        state = read_generation_state(root)
        for number, slide in (state.get("slides") or {}).items():
            for attempt in slide.get("attempt_history") or []:
                if any(source.get("sha256") == asset_sha256 for source in attempt.get("returned_sources") or []):
                    slides.append(int(number))
                    break
        slides = sorted(set(slides))
        if not slides:
            raise ValueError("Asset hash has no recorded slide binding; provide --slide for this asset.")
    change_list = _string_list(list(must_change))
    preserve_list = _string_list(list(must_preserve))
    operations = _normalize_repair_operations(repair_operations)
    assertions = _normalize_verification_assertions(verification_assertions)
    affected = _string_list(list(affected_artifacts))
    for operation in operations + assertions:
        if operation["artifact"] not in affected:
            affected.append(operation["artifact"])
    if not affected:
        if scope in {"slide", "copy"}:
            affected = ["slides.json"]
        elif scope == "asset":
            affected = ["generation-state.json"]
    effect = generation_effect or (
        "slide_local"
        if scope in {"slide", "copy", "asset"} and (kind in {"correction", "rejection"} or change_list)
        else (
            "shared"
            if scope in {"package", "workflow", "global"}
            and (kind in {"correction", "rejection"} or change_list)
            else "none"
        )
    )
    if effect not in CREATOR_FEEDBACK_EFFECTS:
        raise ValueError(f"Unsupported generation effect: {effect}")
    if effect == "slide_local" and not slides:
        raise ValueError("slide_local feedback requires at least one slide.")

    target = root / "creator-correction.json"
    workspace = Path(workspace_root).expanduser().resolve(strict=True)
    try:
        package_path = root.relative_to(workspace).as_posix()
    except ValueError:
        package_path = str(root)
    writable_v3 = _feedback_package_is_writable_v3(root)
    identity = {
        "package_path": package_path,
        "user_instruction_exact": user_instruction_exact,
        "kind": kind,
        "scope": scope,
        "slides": slides,
        "asset_sha256": asset_sha256,
    }
    feedback_id = "fb-" + hashlib.sha256(
        json.dumps(identity, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode(
            "utf-8"
        )
    ).hexdigest()[:16]
    learning_event_id = f"event-feedback-{feedback_id}"
    diagnosis_text = _normalized_diagnosis(
        primary_diagnosis or diagnosis,
        exact_text=user_instruction_exact,
    )
    eval_task_id: str | None = None
    if writable_v3:
        from evals.feedback_cases import feedback_eval_task_id

        eval_task_id = feedback_eval_task_id(feedback_id)
    record = _event_defaults({
        "feedback_id": feedback_id,
        "captured_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "user_instruction_exact": user_instruction_exact,
        "user_instruction_sha256": _feedback_text_sha256(user_instruction_exact),
        "kind": kind,
        "scope": scope,
        "slide_number": slides[0] if len(slides) == 1 else None,
        "slides": slides,
        "asset_sha256": asset_sha256,
        "primary_diagnosis": diagnosis_text,
        "secondary_diagnoses": [_normalized_diagnosis(value, exact_text=user_instruction_exact) for value in secondary_diagnoses],
        "root_cause": str(root_cause or "").strip() or (
            f"Creator-reported {diagnosis_text} issue; specific cause awaits review."
        ),
        "desired_behavior": str(desired_behavior or "").strip() or "; ".join(change_list or preserve_list) or user_instruction_exact,
        "must_change": change_list,
        "must_preserve": preserve_list,
        "affected_artifacts": affected,
        "repair_operations": operations,
        "verification_assertions": assertions,
        "action_taken": None,
        "resolution_evidence": [],
        "generation_effect": effect if writable_v3 else "none",
        "supersedes_feedback_id": supersedes_feedback_id,
        "learning_event_id": learning_event_id,
        "eval_task_ids": [eval_task_id] if eval_task_id else [],
        "eval_waiver_reason": str(eval_waiver_reason or "").strip() or None,
        "status": "diagnosed" if writable_v3 else "captured",
        "historical_only": not writable_v3,
    })

    if not writable_v3:
        from pipeline.agentic.learning_loop import capture_learning_event

        capture_learning_event(
            workspace,
            source="creator_feedback",
            summary=str(root_cause or diagnosis or user_instruction_exact),
            evidence_paths=[package_path],
            event_id=learning_event_id,
            user_instruction_exact=user_instruction_exact,
            diagnosis=diagnosis_text,
            scope=scope,
            package_path=package_path,
            feedback_status="captured",
            resolution_evidence=[],
            eval_disposition="background",
            feedback_metadata={
                "feedback_id": feedback_id,
                "kind": kind,
                "slides": slides,
                "asset_sha256": asset_sha256,
                "primary_diagnosis": diagnosis_text,
                "root_cause": record.get("root_cause"),
                "desired_behavior": record.get("desired_behavior"),
                "must_change": record["must_change"],
                "must_preserve": record["must_preserve"],
                "verification_assertions": record["verification_assertions"],
                "generation_effect": "none",
                "eval_task_ids": [],
                "historical_package_read_only": True,
            },
        )
        return record

    if target.is_symlink():
        raise ValueError("creator-correction.json cannot be a symlink.")
    with _feedback_lock(root):
        document = _creator_correction_document(root, package_id=package_path)
        events = document.get("events")
        if not isinstance(events, list):
            raise ValueError("creator-correction/v3 requires an events array.")
        if supersedes_feedback_id and not any(
            item.get("feedback_id") == supersedes_feedback_id for item in events if isinstance(item, dict)
        ):
            raise ValueError("supersedes_feedback_id must identify an existing correction in this package")
        existing = next(
            (
                item
                for item in events
                if isinstance(item, dict) and item.get("feedback_id") == feedback_id
            ),
            None,
        )
        if existing is None:
            events.append(record)
            document["events"] = events
            _atomic_write_json(target, document)
        else:
            record = _event_defaults(existing)

    from evals.feedback_cases import ensure_feedback_case

    ensure_feedback_case(workspace, root, record)

    from pipeline.agentic.learning_loop import capture_learning_event

    capture_learning_event(
        workspace,
        source="creator_feedback",
        summary=str(root_cause or diagnosis or user_instruction_exact),
        evidence_paths=[
            f"{package_path}/creator-correction.json"
        ],
        event_id=learning_event_id,
        user_instruction_exact=user_instruction_exact,
        diagnosis=diagnosis_text,
        scope=scope,
        package_path=package_path,
        feedback_status=str(record["status"]),
        resolution_evidence=list(record.get("resolution_evidence") or []),
        eval_disposition="background",
        feedback_metadata={
            "feedback_id": feedback_id,
            "kind": kind,
            "slides": slides,
            "asset_sha256": asset_sha256,
            "primary_diagnosis": diagnosis_text,
            "root_cause": record.get("root_cause"),
            "desired_behavior": record.get("desired_behavior"),
            "must_change": record["must_change"],
            "must_preserve": record["must_preserve"],
            "verification_assertions": record["verification_assertions"],
            "generation_effect": effect,
            "eval_task_ids": record["eval_task_ids"],
        },
    )
    from pipeline.agentic.langfuse_mirror import mirror_feedback_event

    mirror_feedback_event(record)
    return record


def _director_payload(plan_or_director: Any) -> dict[str, Any] | None:
    if not isinstance(plan_or_director, dict):
        return None
    nested = plan_or_director.get(DIRECTOR_STORYBOARD_KEY)
    return nested if isinstance(nested, dict) else plan_or_director


def _slide_number(record: Mapping[str, Any], fallback: int = 0) -> int:
    try:
        return int(record.get("slide") or record.get("slide_number") or fallback)
    except (TypeError, ValueError):
        return fallback


def _records(payload: Any) -> list[dict[str, Any]]:
    if isinstance(payload, list):
        return [item for item in payload if isinstance(item, dict)]
    if isinstance(payload, dict) and isinstance(payload.get("slides"), list):
        return [item for item in payload["slides"] if isinstance(item, dict)]
    return []


def _canonical_storyboard_source(slides: Any) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    for index, record in enumerate(_records(slides), start=1):
        result.append(
            {
                "slide": _slide_number(record, index),
                "copy": str(record.get("copy") or record.get("text") or ""),
                "physical_action": str(
                    record.get("physical_action")
                    or record.get("visual_sentence")
                    or record.get("visual")
                    or record.get("scene")
                    or ""
                ),
                "relationship_state": record.get("relationship_state"),
                "camera": record.get("camera"),
                "focal_hierarchy": record.get("focal_hierarchy"),
                "setting": record.get("setting"),
                "visual_richness": record.get("visual_richness"),
            }
        )
    return result


def storyboard_source_fingerprint(slides: Any) -> str:
    return _stable_fingerprint(_canonical_storyboard_source(slides), namespace="storyboard-source/v2")


def _frame_file_value(frame: Mapping[str, Any]) -> Any:
    return frame.get("file") if frame.get("file") not in (None, "") else frame.get("path")


def requested_story_formats(package_dir: Path | None) -> tuple[str, ...]:
    return tuple(locked_formats(package_dir)) if package_dir is not None else tuple(DEFAULT_NATIVE_FORMATS)


def story_formats_from_records(records: Any) -> tuple[str, ...]:
    values: list[str] = []
    if isinstance(records, list):
        for record in records:
            if isinstance(record, Mapping):
                value = str(record.get("format") or "")
                if value and value not in values:
                    values.append(value)
    return tuple(values)


def image_file_fingerprint(path: Path) -> str:
    return "sha256:" + hashlib.sha256(Path(path).read_bytes()).hexdigest()


PIXEL_QA_ORDER = (
    "semantic_action",
    "relationship_state",
    "cinematic_story_frame",
    "entity_anatomy_spatial",
    "identity",
    "text_style_dimensions",
)
_PIXEL_GATE_ALIASES = {
    "semantic_action": ("semantic_action", "semantic_action_legible", "core_action_legible", "action_legible"),
    "relationship_state": ("relationship_state", "relationship_state_legible", "relationship_turn_legible"),
    "cinematic_story_frame": (
        "cinematic_story_frame",
        "cinematic_story_frame_legible",
        "cinematic_depth",
    ),
    "entity_anatomy_spatial": ("entity_anatomy_spatial", "entity_anatomy_spatial_integrity", "anatomy_spatial", "scene_entity_integrity", "anatomy_inventory", "spatial_topology"),
    "identity": ("identity", "identity_consistency", "identity_match"),
    "text_style_dimensions": ("text_style_dimensions", "exact_text_style_dimensions_brandmark", "integrated_text_style_dimensions", "exact_text", "brandmark", "style", "dimensions"),
}


def _explicit_pass_value(value: Any) -> bool | None:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        normalized = value.strip().lower()
        if normalized in {"pass", "passed", "true", "yes", "ok"}:
            return True
        if normalized in {"fail", "failed", "false", "no", "blocked"}:
            return False
    if isinstance(value, Mapping):
        if isinstance(value.get("pass"), bool):
            return bool(value["pass"])
        return _explicit_pass_value(value.get("status") or value.get("verdict"))
    return None


def _numbered_pixel_records(payload: Mapping[str, Any]) -> list[Mapping[str, Any]]:
    result: list[Mapping[str, Any]] = []
    for key in ("slides", "frames"):
        value = payload.get(key)
        if isinstance(value, list):
            result.extend(item for item in value if isinstance(item, Mapping))
    return result


def first_failed_pixel_gate(qa: Any) -> tuple[str, str] | None:
    """Return the earliest explicit pixel failure in the fixed QA order."""

    if not isinstance(qa, Mapping):
        return None
    checks = qa.get("checks")
    checks = checks if isinstance(checks, Mapping) else {}
    readability = checks.get(VISUAL_STORY_READABILITY_KEY)
    readability = readability if isinstance(readability, Mapping) else {}
    containers = (qa, checks, readability)
    records = [*_numbered_pixel_records(qa), *_numbered_pixel_records(readability)]
    reviews = qa.get("reviews") or qa.get("reviewers")
    reviews = reviews if isinstance(reviews, Mapping) else {}
    legacy_reviews = {
        "entity_anatomy_spatial": ("anatomy_entity_spatial_identity",),
        "identity": ("anatomy_entity_spatial_identity",),
        "text_style_dimensions": ("storytelling_richness_text_style",),
    }

    for gate in PIXEL_QA_ORDER:
        aliases = _PIXEL_GATE_ALIASES[gate]
        for container in containers:
            for alias in aliases:
                if alias in container and _explicit_pass_value(container[alias]) is False:
                    return gate, f"{gate} failed on the rendered pixels ({alias})."
        for record in records:
            slide = record.get("slide") or record.get("slide_number") or "?"
            record_checks = record.get("checks")
            record_checks = record_checks if isinstance(record_checks, Mapping) else {}
            for record_container in (record, record_checks):
                for alias in aliases:
                    if alias in record_container and _explicit_pass_value(record_container[alias]) is False:
                        return gate, f"{gate} failed on rendered slide {slide} ({alias})."
        for alias in legacy_reviews.get(gate, ()):
            if alias in reviews and _explicit_pass_value(reviews[alias]) is False:
                return gate, f"{gate} failed in the rendered-pixel review ({alias})."
    return None


def _physical_action(record: Mapping[str, Any]) -> str:
    staged = record.get("staged_action")
    if isinstance(staged, Mapping):
        values = [str(staged.get(key) or "").strip() for key in ("subject", "action", "target_or_object", "reaction_or_consequence")]
        if all(values):
            return " ".join(values)
    for key in ("physical_action", "visual_sentence", "observable_action", "visual", "scene", "silent_read"):
        value = record.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return ""


_ACTION_PLACEHOLDER_PREFIXES = (
    "draft needed",
    "placeholder",
    "same as copy",
    "scene needed",
    "tbd",
    "todo",
)


def physical_action_issue(action: Any, *, copy: Any = "") -> str | None:
    """Return why a proposed scene is not yet a concrete physical event."""

    text = " ".join(str(action or "").strip().split())
    normalized = text.lower().strip(" .:;!?-")
    normalized_copy = " ".join(str(copy or "").strip().lower().split()).strip(" .:;!?-")
    if not text or len(text.split()) < 6:
        return "needs a concrete physical action with subject, action, target, and visible consequence"
    if normalized.startswith(_ACTION_PLACEHOLDER_PREFIXES):
        return "contains a placeholder instead of a physical action"
    if normalized_copy and normalized == normalized_copy:
        return "repeats the slide copy instead of describing visible action"
    return None


_GENERIC_VISUAL_PHRASES = {
    "appropriate composition",
    "cozy home",
    "couple moment",
    "nice lighting",
    "some props",
    "warm scene",
}


def _generic_visual_text(value: Any, *, minimum_words: int = 3) -> bool:
    text = " ".join(str(value or "").strip().lower().split())
    return not text or text in _GENERIC_VISUAL_PHRASES or len(text.split()) < minimum_words


def validate_cinematic_slide_direction(
    record: Any,
    *,
    slide_number: int,
    is_final: bool = False,
) -> list[str]:
    """Validate one canonical, observable story-frame direction.

    This is the shared production validator used by package preflight and the
    deterministic cinematic evals.  It deliberately validates typed evidence,
    not subjective adjectives or an aggregate taste score.
    """

    if not isinstance(record, Mapping):
        return [f"slide {slide_number} cinematic direction must be an object."]

    prefix = f"slide {slide_number}"
    issues: list[str] = []
    relationship_state = record.get("relationship_state") or record.get("emotion")
    if _generic_visual_text(relationship_state):
        issues.append(f"{prefix}.relationship_state must name the visible emotional turn.")

    camera = record.get("camera")
    if not isinstance(camera, Mapping):
        issues.append(f"{prefix}.camera must be an object with shot_size, position, and negative_space.")
        camera = {}
    for key, minimum_words in (
        ("shot_size", 1),
        ("position", 3),
        ("negative_space", 3),
    ):
        if _generic_visual_text(camera.get(key), minimum_words=minimum_words):
            issues.append(f"{prefix}.camera.{key} is missing or generic rather than physically specific.")

    if _generic_visual_text(record.get("focal_hierarchy")):
        issues.append(f"{prefix}.focal_hierarchy must name the first read, second read, and protected copy space.")

    setting = record.get("setting")
    if not isinstance(setting, Mapping):
        issues.append(
            f"{prefix}.setting must be an object with place, time, motivated_light, and depth_layers."
        )
        setting = {}
    for key, minimum_words in (
        ("place", 2),
        ("time", 1),
        ("motivated_light", 4),
    ):
        if _generic_visual_text(setting.get(key), minimum_words=minimum_words):
            issues.append(f"{prefix}.setting.{key} is missing or generic rather than scene-motivated.")
    depth_layers = setting.get("depth_layers")
    if not isinstance(depth_layers, Mapping):
        issues.append(f"{prefix}.setting.depth_layers must name foreground, midground, and background jobs.")
    else:
        for key in ("foreground", "midground", "background"):
            if _generic_visual_text(depth_layers.get(key)):
                issues.append(
                    f"{prefix}.setting.depth_layers.{key} is missing or generic rather than story-supporting."
                )

    richness_issues = validate_visual_richness_contract(
        record.get("visual_richness"),
        require_continuation=not is_final,
    )
    issues.extend(f"{prefix}.{issue}." for issue in richness_issues)
    return issues


def validate_director_storyboard(
    plan: Any,
    *,
    slide_count: int,
    expected_slides: Any | None = None,
    expected_formats: Iterable[str] | None = None,
) -> list[str]:
    """Fail-closed physical-action and cinematic-story preflight."""
    if not isinstance(plan, dict):
        return ["visual direction must be a structured object."]
    payload = _director_payload(plan) or {}
    records = _records(payload)
    if not records:
        records = _records(plan)
    issues: list[str] = []
    if len(records) != slide_count:
        issues.append(f"visual direction has {len(records)} slide records, expected {slide_count}.")
    seen: set[int] = set()
    narrative_jobs: list[str] = []
    shot_sizes: list[str] = []
    for index, record in enumerate(records, start=1):
        slide = _slide_number(record, index)
        if slide in seen or not 1 <= slide <= slide_count:
            issues.append(f"visual direction has invalid or repeated slide {slide}.")
        seen.add(slide)
        action_issue = physical_action_issue(
            _physical_action(record),
            copy=record.get("copy") or record.get("text"),
        )
        if action_issue:
            issues.append(f"slide {slide} {action_issue}.")
        issues.extend(
            validate_cinematic_slide_direction(
                record,
                slide_number=slide,
                is_final=index == slide_count,
            )
        )
        narrative_job = str(record.get("role") or record.get("narrative_job") or "").strip().lower()
        if narrative_job:
            narrative_jobs.append(narrative_job)
        camera = record.get("camera")
        if isinstance(camera, Mapping):
            shot_size = str(camera.get("shot_size") or "").strip().lower()
            if shot_size:
                shot_sizes.append(shot_size)
    if slide_count > 1 and len(narrative_jobs) == len(records) and len(set(narrative_jobs)) < 2:
        issues.append("visual direction repeats one narrative job across the whole sequence.")
    if slide_count > 2 and len(shot_sizes) == len(records) and len(set(shot_sizes)) < 2:
        if not str(payload.get("deliberate_shot_repetition_reason") or "").strip():
            issues.append("visual direction repeats one shot size without a deliberate story reason.")
    if expected_slides is not None:
        expected_numbers = {
            _slide_number(record, index)
            for index, record in enumerate(_records(expected_slides), start=1)
        }
        if seen != expected_numbers:
            issues.append("visual direction slide numbers do not match slides.json.")
    if expected_formats is not None:
        requested = payload.get("requested_formats")
        if requested is not None and list(requested) != [str(item) for item in expected_formats]:
            issues.append("visual direction requested_formats does not match the current format lock.")
    return issues


def _safe_relative_path(raw: Any) -> tuple[str | None, str | None]:
    value = str(raw or "").strip()
    if not value:
        return None, "is missing"
    if PurePosixPath(value).is_absolute() or PureWindowsPath(value).is_absolute():
        return None, "must be package-relative"
    path = PurePosixPath(value.replace("\\", "/"))
    if ".." in path.parts:
        return None, "must not escape the package"
    return path.as_posix(), None


def _coerce_expected_asset(value: Any) -> ExpectedFrameAsset | None:
    if isinstance(value, ExpectedFrameAsset):
        return value
    if not isinstance(value, Mapping):
        return None
    path = value.get("relative_path") or value.get("path")
    dimensions = value.get("dimensions") or value.get("size")
    if not path or not isinstance(dimensions, (list, tuple)) or len(dimensions) != 2:
        return None
    try:
        return ExpectedFrameAsset(str(path), (int(dimensions[0]), int(dimensions[1])))
    except (TypeError, ValueError):
        return None


def validate_frame_readability(
    check: Any,
    *,
    slide_count: int,
    required_formats: Iterable[str] = DEFAULT_NATIVE_FORMATS,
    expected_frame_bindings: Mapping[tuple[int, str], Any] | None = None,
    package_dir: Path | None = None,
    require_files: bool = False,
) -> list[str]:
    """Validate image-first story evidence against the current frame files."""
    if not isinstance(check, dict):
        return ["visual_story_readability must be a structured object."]
    failed = first_failed_pixel_gate(check)
    if failed is not None:
        return [failed[1]]

    issues: list[str] = []
    if check.get("pass") is not True or str(check.get("status") or "").upper() != "PASS":
        issues.append("visual_story_readability must be PASS with pass true.")
    if check.get("image_first") is False:
        issues.append("visual_story_readability.image_first cannot be false.")

    formats = tuple(str(item) for item in required_formats)
    unsupported = sorted(set(formats) - set(SUPPORTED_NATIVE_FORMATS))
    if unsupported:
        issues.append("unsupported requested formats: " + ", ".join(unsupported))
    frames = check.get("frames")
    if not isinstance(frames, list):
        return issues + ["visual_story_readability.frames must be a per-slide, per-format list."]

    expected_keys = {(slide, output_format) for slide in range(1, slide_count + 1) for output_format in formats}
    normalized_bindings = {
        key: asset
        for key, raw in (expected_frame_bindings or {}).items()
        if (asset := _coerce_expected_asset(raw)) is not None
    }
    seen: set[tuple[int, str]] = set()
    used_hashes: set[str] = set()
    for index, frame in enumerate(frames, start=1):
        if not isinstance(frame, Mapping):
            issues.append(f"frame record {index} must be an object.")
            continue
        slide = _slide_number(frame, index)
        output_format = str(frame.get("format") or "")
        key = (slide, output_format)
        prefix = f"frame[{slide}:{output_format or '?'}]"
        if key not in expected_keys:
            issues.append(f"{prefix} is not a locked slide/format pair.")
        elif key in seen:
            issues.append(f"{prefix} is repeated.")
        seen.add(key)
        if frame.get("core_action_legible") is not True:
            issues.append(f"{prefix}.core_action_legible must be true.")
        if frame.get("relationship_turn_legible") is not True:
            issues.append(f"{prefix}.relationship_turn_legible must be true.")
        if frame.get("frame_reads_as_caught_event") is not True:
            issues.append(f"{prefix}.frame_reads_as_caught_event must be true.")
        if frame.get("before_after_implied") is not True:
            issues.append(f"{prefix}.before_after_implied must be true.")
        if frame.get("focal_action_clear") is not True:
            issues.append(f"{prefix}.focal_action_clear must be true.")
        light = frame.get("motivated_light_observed")
        if isinstance(light, Mapping):
            if _generic_visual_text(light.get("source")) or _generic_visual_text(
                light.get("direction")
            ):
                issues.append(
                    f"{prefix}.motivated_light_observed must name a visible source and direction."
                )
        elif _generic_visual_text(light, minimum_words=5):
            issues.append(
                f"{prefix}.motivated_light_observed must name a visible source and direction."
            )
        observed_depth = frame.get("depth_layers_observed")
        if not isinstance(observed_depth, Mapping) or any(
            _generic_visual_text(observed_depth.get(layer))
            for layer in ("foreground", "midground", "background")
        ):
            issues.append(
                f"{prefix}.depth_layers_observed must contain concrete foreground, midground, and background evidence."
            )
        observed_evidence = frame.get("story_evidence_observed")
        if not isinstance(observed_evidence, list) or not 2 <= len(observed_evidence) <= 4:
            issues.append(f"{prefix}.story_evidence_observed must contain two to four visible items.")
        elif any(_generic_visual_text(value) for value in observed_evidence):
            issues.append(f"{prefix}.story_evidence_observed contains generic evidence.")
        if frame.get("posed_portrait") is not False:
            issues.append(f"{prefix}.posed_portrait must be false.")
        if frame.get("decorative_clutter") is not False:
            issues.append(f"{prefix}.decorative_clutter must be false.")
        generic_ai_tells = frame.get("generic_ai_tells")
        if not isinstance(generic_ai_tells, list) or generic_ai_tells:
            issues.append(f"{prefix}.generic_ai_tells must be an empty list.")
        if slide == slide_count:
            if _generic_visual_text(frame.get("final_payoff_observed")):
                issues.append(f"{prefix}.final_payoff_observed must name the visible resolved after-state.")
        elif _generic_visual_text(frame.get("continuation_pull_observed")):
            issues.append(f"{prefix}.continuation_pull_observed must name the visible next-beat question.")
        if not str(frame.get("observed_image_first_read") or "").strip():
            issues.append(f"{prefix}.observed_image_first_read is missing.")
        if not str(frame.get("evidence") or "").strip():
            issues.append(f"{prefix}.evidence is missing.")
        contradictions = frame.get("copy_visual_contradictions")
        if isinstance(contradictions, list) and contradictions:
            issues.append(
                f"{prefix}.copy_visual_contradictions: "
                + "; ".join(str(item) for item in contradictions if str(item).strip())
            )
        unexpected_story = frame.get("unexpected_story")
        if isinstance(unexpected_story, list) and unexpected_story:
            issues.append(
                f"{prefix}.unexpected_story: "
                + "; ".join(str(item) for item in unexpected_story if str(item).strip())
            )

        relative_path, path_issue = _safe_relative_path(_frame_file_value(frame))
        if path_issue:
            issues.append(f"{prefix}.file {path_issue}.")
            continue
        expected_asset = normalized_bindings.get(key)
        if expected_asset and relative_path != expected_asset.relative_path:
            issues.append(f"{prefix}.file must equal {expected_asset.relative_path}.")
        if package_dir is None:
            if require_files:
                issues.append("file-backed readability validation requires package_dir.")
            continue
        path = Path(package_dir) / str(relative_path)
        try:
            resolved = path.resolve(strict=True)
            resolved.relative_to(Path(package_dir).resolve(strict=True))
        except (FileNotFoundError, OSError, ValueError):
            issues.append(f"{prefix}.file is missing or outside the package.")
            continue
        if path.is_symlink() or not path.is_file():
            issues.append(f"{prefix}.file must be a regular package image.")
            continue
        digest = image_file_fingerprint(path)
        if digest in used_hashes:
            issues.append(f"{prefix}.file duplicates another reviewed frame's exact bytes.")
        used_hashes.add(digest)
        if str(frame.get("image_fingerprint") or "") != digest:
            issues.append(f"{prefix}.image_fingerprint is missing or stale.")
        try:
            with Image.open(path) as image:
                dimensions = tuple(image.size)
                image.verify()
        except (UnidentifiedImageError, OSError, SyntaxError, ValueError):
            issues.append(f"{prefix}.file is not a decodable image.")
            continue
        if expected_asset and dimensions != expected_asset.dimensions:
            issues.append(
                f"{prefix}.file dimensions are {dimensions[0]}x{dimensions[1]}, expected {expected_asset.dimensions[0]}x{expected_asset.dimensions[1]}."
            )

    missing = sorted(expected_keys - seen)
    if missing:
        issues.append("frames missing required records: " + ", ".join(f"{slide}:{fmt}" for slide, fmt in missing))
    if len(frames) != len(expected_keys):
        issues.append(f"frames has {len(frames)} records, expected {len(expected_keys)}.")
    if isinstance(check.get("issues"), list) and check["issues"]:
        issues.append("visual_story_readability declares unresolved issues while claiming PASS.")
    return issues
