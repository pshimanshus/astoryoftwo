"""Canonical compact v3 state for carousel image generation.

This file is the only public transient state surface. It never mirrors state
into ``image-generation.json`` or ``final-images.json``; those names are,
respectively, a legacy read fallback and the final file inventory.
"""

from __future__ import annotations

import json
import re
from enum import StrEnum
from pathlib import Path
from typing import Any

from pipeline.stages.carousel_generation_inputs import build_generation_inputs


STATE_SCHEMA_VERSION = "carousel-generation-state/v3"
STATE_FILE = "generation-state.json"


class GenerationStatus(StrEnum):
    DRAFT = "draft"
    BLOCKED = "blocked"
    HANDOFF_READY = "handoff_ready"
    PROOF_QA_REQUIRED = "proof_qa_required"
    PROOF_FAILED = "proof_failed"
    AWAITING_CREATOR_PROOF_APPROVAL = "awaiting_creator_proof_approval"
    BATCH_READY = "batch_ready"
    FINAL_QA_REQUIRED = "final_qa_required"
    FINAL_QA_FAILED = "final_qa_failed"
    PUBLISH_READY = "publish_ready"


PUBLIC_STATUSES = tuple(status.value for status in GenerationStatus)
SHA256_BINDING_RE = re.compile(r"^sha256:[0-9a-f]{64}$")
LEGACY_STATE_TRANSITIONS = {
    "generated_quarantined": ("proof_qa_required", "review_proof_pixels"),
    "proof_ready_for_review": ("proof_qa_required", "review_proof_pixels"),
    "qa_pass_candidate": ("awaiting_creator_proof_approval", "approve_proof"),
    "creator_approved_proof": ("batch_ready", "prepare_remaining_slides"),
    "batch_allowed": ("batch_ready", "prepare_remaining_slides"),
    "blocked_visual_qa": ("proof_failed", "repair_visual_premise"),
    "generated_audit_failed": ("final_qa_failed", "repair_final_audit"),
    "generated": ("final_qa_required", "run_final_pixel_qa"),
    "packaged": ("final_qa_required", "run_final_pixel_qa"),
    "publishable": ("publish_ready", "publish"),
}


def _read_json(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (FileNotFoundError, OSError, json.JSONDecodeError):
        return {}
    return payload if isinstance(payload, dict) else {}


def read_generation_state(package_dir: Path) -> dict[str, Any]:
    """Read v3 state, falling back to archived legacy state without writing."""

    package_dir = Path(package_dir).expanduser()
    return _read_json(package_dir / STATE_FILE) or _read_json(
        package_dir / "image-generation.json"
    )


def archived_package_read_only_reason(package_dir: Path) -> str | None:
    """Check both lifecycle and prompt schemas before any package mutation."""

    package_dir = Path(package_dir).expanduser()
    state = read_generation_state(package_dir)
    prompt_pack = _read_json(package_dir / "prompt-pack.json")
    if (state and state.get("schema_version") != STATE_SCHEMA_VERSION) or (
        prompt_pack.get("schema_version")
        and prompt_pack["schema_version"] != "carousel-prompt-pack/v3"
    ):
        return (
            "Archived v2 carousel packages are read-only; create a new v3 package "
            "with the active style profile."
        )
    return None


def require_writable_package(package_dir: Path) -> None:
    reason = archived_package_read_only_reason(package_dir)
    if reason:
        raise ValueError(reason)


def canonical_state_and_next_action(state: dict[str, Any]) -> tuple[str, str]:
    """Map current or archived state to the one public vocabulary.

    This is deliberately the sole compatibility map. New v3 writes are strict;
    archived packages remain read-only but every reader reports the same public
    state and next action.
    """

    raw = str(
        state.get("status") or state.get("state") or state.get("proof_state") or "draft"
    ).strip().lower()
    supplied_next = str(state.get("next_action") or "").strip()
    if state.get("schema_version") == STATE_SCHEMA_VERSION:
        if raw not in PUBLIC_STATUSES:
            return "blocked", "repair_state"
        return raw, supplied_next or "repair_state"

    if raw in PUBLIC_STATUSES:
        return raw, supplied_next or "inspect_archived_package"
    public, default_next = LEGACY_STATE_TRANSITIONS.get(
        raw,
        ("blocked", "inspect_archived_package"),
    )
    stage = str(state.get("stage") or state.get("repair_scope") or "proof").lower()
    if public == "proof_qa_required" and stage != "proof":
        public, default_next = "final_qa_required", "run_final_pixel_qa"
    elif public == "proof_failed" and stage != "proof":
        public, default_next = "final_qa_failed", "repair_final_pixel_qa"
    return public, supplied_next or default_next


def _required_sha256(value: Any, *, field: str) -> str:
    binding = str(value or "")
    if not SHA256_BINDING_RE.fullmatch(binding):
        raise ValueError(f"{field} must be canonical sha256:<64 lowercase hex>.")
    return binding


def _compact_slide(value: dict[str, Any]) -> dict[str, Any]:
    history = value.get("attempt_history") or []
    if not isinstance(history, list):
        raise ValueError("attempt_history must be an array.")
    compact = {
        "status": str(value.get("status") or "draft"),
        "attempts": int(value.get("attempts", 0) or 0),
        "source_sha256": _required_sha256(
            value.get("source_sha256"), field="source_sha256"
        ),
        "prompt_sha256": _required_sha256(
            value.get("prompt_sha256"), field="prompt_sha256"
        ),
        "references_sha256": _required_sha256(
            value.get("references_sha256"), field="references_sha256"
        ),
        "input_sha256": _required_sha256(
            value.get("input_sha256"), field="input_sha256"
        ),
        "attempt_history": [_compact_attempt(item) for item in history],
    }
    # v3 packages created before premise-scoped retry accounting remain
    # readable and writable. Reconciliation adds the current premise hash on
    # the first real input change without inventing a legacy reset.
    if value.get("premise_sha256") not in {None, ""}:
        compact["premise_sha256"] = _required_sha256(
            value.get("premise_sha256"), field="premise_sha256"
        )
    return compact


def _optional_sha256(value: Any, *, field: str) -> str | None:
    if value in {None, ""}:
        return None
    return _required_sha256(value, field=field)


def _compact_attempt(value: Any) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ValueError("attempt_history entries must be objects.")
    boundary = str(value.get("generator_boundary") or "")
    if boundary != "codex_builtin_imagegen":
        raise ValueError("attempt generator_boundary must be codex_builtin_imagegen.")
    returned = value.get("returned_sources") or []
    references = value.get("references") or []
    if not isinstance(returned, list) or not isinstance(references, list):
        raise ValueError("attempt references and returned_sources must be arrays.")
    if "feedback_ids" in value:
        ids = value["feedback_ids"]
        if (not isinstance(ids, list)
                or any(not isinstance(item, str) or not item for item in ids)
                or len(set(ids)) != len(ids)
                or (value.get("feedback_id") is not None and value["feedback_id"] not in ids)):
            raise ValueError("attempt.feedback_ids must contain unique IDs and its scalar feedback_id.")
    return {
        "generator_boundary": boundary,
        "tool_reported_model": value.get("tool_reported_model"),
        "prompt_sha256": _required_sha256(value.get("prompt_sha256"), field="attempt.prompt_sha256"),
        "reference_manifest_sha256": _required_sha256(
            value.get("reference_manifest_sha256"), field="attempt.reference_manifest_sha256"
        ),
        "references": [
            {
                "path": str(item.get("path") or ""),
                "sha256": _required_sha256(item.get("sha256"), field="attempt.reference.sha256"),
                "role": str(item.get("role") or ""),
            }
            for item in references
            if isinstance(item, dict)
        ],
        "slide": int(value.get("slide") or 0),
        "attempt": int(value.get("attempt") or 0),
        "returned_sources": [
            {
                "format": str(item.get("format") or ""),
                "path": str(item.get("path") or ""),
                "sha256": _required_sha256(item.get("sha256"), field="attempt.source.sha256"),
                "width": int(item.get("width") or 0),
                "height": int(item.get("height") or 0),
                "returned_at": str(item.get("returned_at") or ""),
            }
            for item in returned
            if isinstance(item, dict)
        ],
        "feedback_id": value.get("feedback_id"),
        **({"feedback_ids": list(value["feedback_ids"])} if "feedback_ids" in value else {}),
        "pixel_review_status": str(value.get("pixel_review_status") or "pending"),
        "qa_sha256": _optional_sha256(value.get("qa_sha256"), field="attempt.qa_sha256"),
        "reviewed_at": value.get("reviewed_at"),
        "approval_status": str(value.get("approval_status") or "pending"),
        "promotion_status": str(value.get("promotion_status") or "pending"),
    }


def compact_v3_state(state: dict[str, Any]) -> dict[str, Any]:
    allowed = {
        "schema_version",
        "status",
        "next_action",
        "proof_slide",
        "selected_slides",
        "selected_formats",
        "format_sha256",
        "slides",
        "reason",
    }
    unexpected = sorted(set(state) - allowed)
    if unexpected:
        raise ValueError(
            "v3 generation state contains non-canonical fields: "
            + ", ".join(unexpected)
        )
    status = str(state.get("status") or GenerationStatus.DRAFT.value)
    if status not in PUBLIC_STATUSES:
        raise ValueError(f"Unsupported carousel generation status: {status}")
    slides = state.get("slides")
    if not isinstance(slides, dict) or not slides:
        raise ValueError("v3 generation state requires compact per-slide records.")
    result: dict[str, Any] = {
        "schema_version": STATE_SCHEMA_VERSION,
        "status": status,
        "next_action": str(state.get("next_action") or "prepare_riskiest_proof"),
        "proof_slide": (
            int(state["proof_slide"])
            if state.get("proof_slide") is not None
            else None
        ),
        "selected_slides": [int(value) for value in state.get("selected_slides") or []],
        "selected_formats": [str(value) for value in state.get("selected_formats") or []],
        "format_sha256": _required_sha256(
            state.get("format_sha256"), field="format_sha256"
        ),
        "slides": {
            str(int(number)): _compact_slide(record)
            for number, record in sorted(
                slides.items(), key=lambda item: int(item[0])
            )
            if isinstance(record, dict)
        },
    }
    reason = str(state.get("reason") or "").strip()
    if reason:
        result["reason"] = reason
    return result


def write_v3_state(package_dir: Path, state: dict[str, Any]) -> dict[str, Any]:
    require_writable_package(package_dir)
    compact = compact_v3_state(state)
    package_dir = Path(package_dir).expanduser()
    package_dir.mkdir(parents=True, exist_ok=True)
    (package_dir / STATE_FILE).write_text(
        json.dumps(compact, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    return compact


def initialize_generation_state(package_dir: Path) -> dict[str, Any]:
    """Write the first v3 state after the minimal package inputs exist."""

    package_dir = Path(package_dir)
    require_writable_package(package_dir)
    inputs = build_generation_inputs(package_dir)
    try:
        raw_slides = json.loads((package_dir / "slides.json").read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        raw_slides = []
    needs_actions = any(
        isinstance(slide, dict) and slide.get("needs_physical_action") is True
        for slide in raw_slides if isinstance(raw_slides, list)
    )
    first_action = "lock_visible_actions" if needs_actions else "prepare_riskiest_proof"
    return write_v3_state(
        package_dir,
        {
            "status": GenerationStatus.DRAFT.value,
            "next_action": first_action,
            "proof_slide": None,
            "selected_slides": [],
            "selected_formats": inputs["selected_formats"],
            "format_sha256": inputs["format_sha256"],
            "slides": {
                number: {
                    "status": "draft",
                    "attempts": 0,
                    "attempt_history": [],
                    **fingerprints,
                }
                for number, fingerprints in inputs["slides"].items()
            },
        },
    )
__all__ = [
    "archived_package_read_only_reason",
    "canonical_state_and_next_action",
    "GenerationStatus",
    "LEGACY_STATE_TRANSITIONS",
    "PUBLIC_STATUSES",
    "STATE_FILE",
    "STATE_SCHEMA_VERSION",
    "compact_v3_state",
    "initialize_generation_state",
    "read_generation_state",
    "require_writable_package",
    "write_v3_state",
]
