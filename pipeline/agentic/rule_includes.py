"""Canonical rule include expander for the Agentic OS.

Skill files, prompts, and context sections reference shared rule fragments
via `{{rule:NAME}}` markers. This module resolves those markers against
`config/rules/<NAME>.md` so the canonical rule text lives in exactly one
place per concept (palette, identity, on-image-text, brandmark,
brand-zone, voice, golden-theme, story-selling).
"""

from __future__ import annotations

import re
from functools import lru_cache
from pathlib import Path

RULE_INCLUDE_PATTERN = re.compile(r"\{\{rule:([a-z0-9_\-]+)\}\}")
RULES_DIR_NAME = "config/rules"


@lru_cache(maxsize=64)
def _load_rule(workspace_root: Path, name: str) -> str:
    path = workspace_root / RULES_DIR_NAME / f"{name}.md"
    if not path.exists():
        raise FileNotFoundError(
            f"Unknown rule include: {name} (looked at {path})"
        )
    return path.read_text(encoding="utf-8").strip()


def expand_rule_includes(text: str, workspace_root: Path) -> str:
    """Replace every `{{rule:NAME}}` marker with the contents of
    `config/rules/<NAME>.md` from the given workspace root.
    """

    def _sub(match: re.Match[str]) -> str:
        return _load_rule(workspace_root, match.group(1))

    return RULE_INCLUDE_PATTERN.sub(_sub, text)


def rule_names_referenced(text: str) -> list[str]:
    """Return the sorted unique list of rule names referenced in text."""
    return sorted({match.group(1) for match in RULE_INCLUDE_PATTERN.finditer(text)})


def clear_rule_cache() -> None:
    """Reset the rule loader cache. Mostly used by tests."""
    _load_rule.cache_clear()
