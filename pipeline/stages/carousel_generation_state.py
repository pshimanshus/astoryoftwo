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


DONE_STATUSES = {
    GenerationStatus.GENERATED,
}
HUMAN_GENERATION_STATUSES = {
    GenerationStatus.HANDOFF_READY,
    GenerationStatus.PROOF_READY_FOR_REVIEW,
}


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
    if status in DONE_STATUSES and not slides:
        raise ValueError(f"status {status.value!r} requires slides records")

    state: dict[str, Any] = {
        "status": status.value,
        "backend": backend,
        "generation_mode": generation_mode,
        "slide_count": slide_count,
        "done": status in DONE_STATUSES,
        "publishable": status in DONE_STATUSES,
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
