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


def _required_sha256(value: Any, *, field: str) -> str:
    binding = str(value or "")
    if not SHA256_BINDING_RE.fullmatch(binding):
        raise ValueError(f"{field} must be canonical sha256:<64 lowercase hex>.")
    return binding


def _compact_slide(value: dict[str, Any]) -> dict[str, Any]:
    return {
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
                    **fingerprints,
                }
                for number, fingerprints in inputs["slides"].items()
            },
        },
    )
__all__ = [
    "GenerationStatus",
    "PUBLIC_STATUSES",
    "STATE_FILE",
    "STATE_SCHEMA_VERSION",
    "compact_v3_state",
    "initialize_generation_state",
    "read_generation_state",
    "write_v3_state",
]
