"""Shared carousel image-generation manifest state."""

from __future__ import annotations

import json
from enum import StrEnum
from pathlib import Path
from typing import Any


class GenerationStatus(StrEnum):
    DRAFT = "draft"
    HANDOFF_READY = "handoff_ready"
    BLOCKED = "blocked"
    LEGACY_PREVIEW_GENERATED = "legacy_preview_generated"
    DRY_RUN_GENERATED = "dry_run_generated"
    PROOF_READY_FOR_REVIEW = "proof_ready_for_review"
    GENERATED = "generated"
    GENERATED_AUDIT_FAILED = "generated_audit_failed"
    QA_PASSED = "qa_passed"
    PUBLISH_READY = "publish_ready"
    GENERATED_QUARANTINED = "GENERATED_QUARANTINED"
    QA_PASS_CANDIDATE = "QA_PASS_CANDIDATE"
    CREATOR_APPROVED_PROOF = "CREATOR_APPROVED_PROOF"
    BATCH_ALLOWED = "BATCH_ALLOWED"
    REJECTED_SPATIAL_INTEGRITY = "REJECTED_SPATIAL_INTEGRITY"
    BLOCKED_VISUAL_QA = "BLOCKED_VISUAL_QA"


DONE_STATUSES = {
    GenerationStatus.GENERATED,
    GenerationStatus.PUBLISH_READY,
}
PUBLISHABLE_STATUSES = {
    GenerationStatus.PUBLISH_READY,
}
HUMAN_GENERATION_STATUSES = {
    GenerationStatus.HANDOFF_READY,
    GenerationStatus.PROOF_READY_FOR_REVIEW,
}

PROOF_PIPELINE_STATUSES = {
    GenerationStatus.GENERATED_QUARANTINED,
    GenerationStatus.QA_PASS_CANDIDATE,
    GenerationStatus.CREATOR_APPROVED_PROOF,
    GenerationStatus.BATCH_ALLOWED,
    GenerationStatus.REJECTED_SPATIAL_INTEGRITY,
    GenerationStatus.BLOCKED_VISUAL_QA,
}

ALLOWED_PROOF_TRANSITIONS = {
    GenerationStatus.GENERATED_QUARANTINED: {
        GenerationStatus.QA_PASS_CANDIDATE,
        GenerationStatus.REJECTED_SPATIAL_INTEGRITY,
        GenerationStatus.BLOCKED_VISUAL_QA,
    },
    GenerationStatus.QA_PASS_CANDIDATE: {
        GenerationStatus.CREATOR_APPROVED_PROOF,
        GenerationStatus.BLOCKED_VISUAL_QA,
    },
    GenerationStatus.CREATOR_APPROVED_PROOF: {
        GenerationStatus.BATCH_ALLOWED,
        GenerationStatus.BLOCKED_VISUAL_QA,
    },
    GenerationStatus.BATCH_ALLOWED: set(),
    GenerationStatus.REJECTED_SPATIAL_INTEGRITY: {
        GenerationStatus.GENERATED_QUARANTINED,
        GenerationStatus.BLOCKED_VISUAL_QA,
    },
    GenerationStatus.BLOCKED_VISUAL_QA: set(),
}


def _existing_generation_status(carousel_dir: Path) -> GenerationStatus | None:
    path = carousel_dir / "image-generation.json"
    if not path.exists():
        return None
    try:
        value = json.loads(path.read_text(encoding="utf-8")).get("status")
        return GenerationStatus(value)
    except (OSError, json.JSONDecodeError, ValueError, AttributeError):
        return None


def validate_proof_transition(
    current: GenerationStatus | None,
    requested: GenerationStatus,
) -> None:
    """Block lifecycle skips once a proof has entered the fail-closed state machine."""

    if requested in PROOF_PIPELINE_STATUSES and current not in PROOF_PIPELINE_STATUSES:
        if requested != GenerationStatus.GENERATED_QUARANTINED:
            current_label = current.value if current is not None else "none"
            raise ValueError(
                "Invalid proof-state entry: "
                f"{current_label} -> {requested.value}; first state must be "
                f"{GenerationStatus.GENERATED_QUARANTINED.value}."
            )
        return
    if current in PROOF_PIPELINE_STATUSES and requested not in PROOF_PIPELINE_STATUSES:
        if current == GenerationStatus.BATCH_ALLOWED and requested in {
            GenerationStatus.PUBLISH_READY,
            GenerationStatus.GENERATED_AUDIT_FAILED,
        }:
            return
        raise ValueError(
            f"Invalid exit from fail-closed proof state: {current.value} -> {requested.value}."
        )
    if requested not in PROOF_PIPELINE_STATUSES:
        return
    if requested == current:
        return
    allowed = ALLOWED_PROOF_TRANSITIONS.get(current, set())
    if requested not in allowed:
        raise ValueError(
            f"Invalid proof-state transition: {current.value} -> {requested.value}."
        )


def write_generation_state(
    carousel_dir: Path,
    *,
    status: GenerationStatus,
    backend: str,
    generation_mode: str,
    slide_count: int,
    reason: str | None = None,
    slides: list[dict[str, Any]] | None = None,
    extra: dict[str, Any] | None = None,
) -> dict[str, Any]:
    validate_proof_transition(_existing_generation_status(carousel_dir), status)
    if status in DONE_STATUSES.union(PROOF_PIPELINE_STATUSES) and not slides:
        raise ValueError(f"status {status.value!r} requires slides records")

    state: dict[str, Any] = {
        "status": status.value,
        "backend": backend,
        "generation_mode": generation_mode,
        "slide_count": slide_count,
        "done": status in DONE_STATUSES,
        "publishable": status in PUBLISHABLE_STATUSES,
        "requires_human_generation": status in HUMAN_GENERATION_STATUSES,
        "slides": slides or [],
    }
    if reason is not None:
        state["reason"] = reason
    if extra:
        reserved_keys = set(state)
        conflicts = sorted(reserved_keys.intersection(extra))
        if conflicts:
            raise ValueError(f"extra contains reserved generation state keys: {', '.join(conflicts)}")
        state.update(extra)

    carousel_dir.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(state, indent=2, ensure_ascii=False)
    for filename in ("image-generation.json", "final-images.json"):
        (carousel_dir / filename).write_text(payload, encoding="utf-8")
    return state
