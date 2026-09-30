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
        "target_authorities": [
            {"authority": "creator", "patterns": [
                "config/rules/**",
                "config/skills/**",
                "config/skill-systems.json",
                "config/agentic_*.json",
                "config/token_budget_contract.json",
                "memory/semantic/**",
                "memory/working.md",
                "AGENTS.md",
                "CLAUDE.md",
                "agents/**",
                ".agents/skills/**",
                ".codex/agents/**",
            ]},
            {"authority": "maintainer", "patterns": [
                "config/**", "pipeline/**", "scripts/**", "agents/**",
            ]},
        ],
        "authorities": {
            "creator": {
                "identities": ["creator"],
                "targets": [
                    "config/skills/**", "config/rules/**", "config/skill-systems.json",
                    "config/agentic_*.json", "config/token_budget_contract.json",
                    "memory/semantic/**", "memory/working.md", "AGENTS.md",
                    "CLAUDE.md", "agents/**", ".agents/skills/**",
                    ".codex/agents/**",
                ],
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


def _normalized_target(target_path: str) -> str:
    target = Path(target_path)
    if ".." in target.parts:
        raise ValueError("target_path must not contain parent traversal")
    if target.is_absolute():
        raise ValueError("target_path must be a workspace-relative path")
    normalized = target.as_posix()
    if not normalized or normalized == ".":
        raise ValueError("target_path must name a workspace-relative artifact")
    return normalized


def required_authority_for_target(root: Path, target_path: str) -> str:
    """Resolve authority from the artifact, independent of the proposed actor.

    ``target_authorities`` is ordered from most protected to least protected.
    This prevents a broad maintainer glob such as ``config/**`` from weakening
    the creator boundary for rules, skills, semantic preferences, or workflow
    definitions.
    """

    normalized = _normalized_target(target_path)
    policy = load_approval_policy(root)
    rules = policy.get("target_authorities")
    if isinstance(rules, list):
        for rule in rules:
            if not isinstance(rule, dict):
                continue
            authority = rule.get("authority")
            patterns = rule.get("patterns")
            if authority not in policy["authorities"] or not isinstance(patterns, list):
                continue
            if any(
                isinstance(pattern, str) and fnmatch.fnmatchcase(normalized, pattern)
                for pattern in patterns
            ):
                return str(authority)

    # Compatibility for an older policy without ordered target rules. Creator
    # wins an overlap because its artifacts carry semantic/product authority.
    matches: list[str] = []
    for authority, definition in policy["authorities"].items():
        if not isinstance(definition, dict):
            continue
        patterns = definition.get("targets", [])
        if any(
            isinstance(pattern, str) and fnmatch.fnmatchcase(normalized, pattern)
            for pattern in patterns
        ):
            matches.append(str(authority))
    if "creator" in matches:
        return "creator"
    if len(matches) == 1:
        return matches[0]
    if not matches:
        raise ValueError(f"no approval authority is configured for target: {normalized}")
    raise ValueError(f"ambiguous approval authority for target: {normalized}")


def require_approval_authority(root: Path, *, approver: str, target_path: str) -> str:
    """Return the authority that may approve this target, or fail closed."""
    if not approver.strip():
        raise ValueError("approved_by must name an authorized human authority")
    normalized = _normalized_target(target_path)
    policy = load_approval_policy(root)
    required = required_authority_for_target(root, normalized)
    authority = authority_for(root, approver)
    if authority is None:
        raise ValueError(
            f"{required} approval requires an authorized identity; "
            f"approver has no authority in policy: {approver}"
        )
    if authority != required:
        raise ValueError(f"approval authority '{authority}' cannot apply changes to {normalized}")
    return required
