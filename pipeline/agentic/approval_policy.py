"""Target-scoped human approval policy for learning proposals."""

from __future__ import annotations

import fnmatch
import json
from pathlib import Path
from typing import Any


POLICY_PATH = Path("config/agentic_approval_policy.json")


def default_approval_policy() -> dict[str, Any]:
    """Compatibility-safe policy for isolated workspaces used by the CLI/tests."""
    return {
        "schema_version": "1.0",
        "authorities": {
            "creator": {
                "identities": ["creator"],
                "targets": ["config/skills/**", "config/rules/**", "memory/semantic/**", "memory/working.md"],
            },
            "maintainer": {
                "identities": ["maintainer"],
                "targets": ["config/**", "pipeline/**", "scripts/**", "agents/**", ".codex/agents/**"],
            },
        },
    }


def load_approval_policy(root: Path) -> dict[str, Any]:
    path = root.resolve() / POLICY_PATH
    if not path.exists():
        return default_approval_policy()
    try:
        policy = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"invalid approval policy: {exc}") from exc
    if not isinstance(policy, dict) or not isinstance(policy.get("authorities"), dict):
        raise ValueError("approval policy must contain an authorities object")
    return policy


def authority_for(root: Path, approver: str) -> str | None:
    for authority, definition in load_approval_policy(root)["authorities"].items():
        if not isinstance(definition, dict):
            continue
        identities = definition.get("identities", [])
        if approver in identities:
            return authority
    return None


def require_approval_authority(root: Path, *, approver: str, target_path: str) -> str:
    """Return the authority that may approve this target, or fail closed."""
    if not approver.strip():
        raise ValueError("approved_by must name an authorized human authority")
    target = Path(target_path)
    if target.is_absolute() or ".." in target.parts:
        raise ValueError("target_path must be a workspace-relative path")
    policy = load_approval_policy(root)
    authority = authority_for(root, approver)
    if authority is None:
        raise ValueError(f"approver has no authority in policy: {approver}")
    definitions = policy["authorities"]
    definition = definitions[authority]
    targets = definition.get("targets", []) if isinstance(definition, dict) else []
    normalized = target.as_posix()
    if not any(isinstance(pattern, str) and fnmatch.fnmatchcase(normalized, pattern) for pattern in targets):
        raise ValueError(f"approval authority '{authority}' cannot apply changes to {normalized}")
    return authority
