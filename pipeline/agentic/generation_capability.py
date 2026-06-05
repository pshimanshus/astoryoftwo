"""Session-level image generation capability signal."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any


TRUTHY = {"1", "true", "yes", "on"}


def detect_generation_capability(workspace_root: Path) -> dict[str, Any]:
    raw = os.environ.get("CODEX_CAN_ATTACH_IDENTITY_REFS", "")
    can_attach_identity_refs = raw.strip().lower() in TRUTHY
    return {
        "schema_version": "1.0",
        "workspace_root": str(workspace_root.expanduser()),
        "capability_source": "environment",
        "can_attach_identity_refs": can_attach_identity_refs,
        "package_terminal_state": (
            "publishable_after_visual_qa"
            if can_attach_identity_refs
            else "HANDOFF_READY_FOR_CODEX_WITH_IDENTITY"
        ),
        "reason": (
            "The current session declares that actual identity reference images can be attached to generation calls."
            if can_attach_identity_refs
            else "The current session has no declared ability to attach actual identity reference images to generation calls."
        ),
        "required_identity_inputs": [
            "identity-face-contact-sheet.jpg",
            "selected Aachu identity references",
            "selected Zuv identity references",
            "selected together reference when available",
        ],
        "next_action": (
            "generate_proof_then_batch_native_outputs"
            if can_attach_identity_refs
            else "handoff_to_identity_reference_capable_generation_environment"
        ),
    }


def write_generation_capability(workspace_root: Path) -> dict[str, Any]:
    workspace_root = workspace_root.expanduser()
    workspace_root.mkdir(parents=True, exist_ok=True)
    payload = detect_generation_capability(workspace_root)
    (workspace_root / "generation-capability.json").write_text(
        json.dumps(payload, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    return payload
