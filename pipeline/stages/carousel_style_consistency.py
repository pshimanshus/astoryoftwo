"""Fail-closed checks for the one active illustration style profile.

The style contract owns the generation language. This module validates an
immutable package snapshot and, when supplied, the derived compiled prompts;
it intentionally contains no fallback style prose.
"""

from __future__ import annotations

import re
from collections.abc import Iterable, Mapping
from typing import Any

from pipeline.stages.carousel_contract import (
    load_active_illustration_style_profile,
    style_profile_contract_sha256,
)


HOUSE_STYLE_SCENE_RULE = (
    "the active cinematic-observational-watercolor profile must be bound exactly "
    "once; Aachu/Zuv behavior carries the scene and poster/stationery artifacts "
    "cannot become the visual system"
)

FORBIDDEN_PROMPT_STYLE_DRIFT_TERMS = (
    "use case: illustrated relationship artifact",
    "low-fi night-photo poster",
    "private archive poster",
    "poster artifact",
    "old attendance sheet",
    "old attendance register",
    "relationship terms-and-conditions slip",
    "tiny legal receipt",
    "drawn crossed-out scoreboard artifact",
    "scoreboard artifact",
    "tiny museum label",
    "phrase exhibit on warm paper",
)


def _is_negated_style_warning(prompt_lower: str, term: str) -> bool:
    start = 0
    while True:
        index = prompt_lower.find(term, start)
        if index == -1:
            return True
        prefix = prompt_lower[max(0, index - 140) : index]
        sentence_fragment = re.split(r"[.!?;]\s*", prefix)[-1]
        if not any(
            marker in sentence_fragment
            for marker in (
                "no ",
                "not ",
                "never ",
                "do not ",
                "must not ",
                "avoid ",
                "reject ",
                "rejected ",
            )
        ):
            return False
        start = index + len(term)


def _compiled_prompt_records(
    compiled_prompts: Mapping[int, str] | Iterable[tuple[int, str]] | None,
) -> list[tuple[int, str]]:
    if compiled_prompts is None:
        return []
    values = compiled_prompts.items() if isinstance(compiled_prompts, Mapping) else compiled_prompts
    return [(int(number), str(prompt)) for number, prompt in values]


def prompt_style_drift_issues(
    compiled_prompts: Mapping[int, str] | Iterable[tuple[int, str]] | None,
    *,
    generation_prompt: str,
) -> list[str]:
    issues: list[str] = []
    for number, prompt in _compiled_prompt_records(compiled_prompts):
        prompt_lower = prompt.lower()
        hits = [
            term
            for term in FORBIDDEN_PROMPT_STYLE_DRIFT_TERMS
            if term in prompt_lower and not _is_negated_style_warning(prompt_lower, term)
        ]
        if hits:
            issues.append(
                f"Slide {number} prompt uses non-house artifact/poster visual language: "
                + ", ".join(hits)
            )
        count = prompt.count(generation_prompt)
        if count != 1:
            issues.append(
                f"Slide {number} prompt must contain the active generation style exactly once; "
                f"found {count}."
            )
    return issues


def style_profile_snapshot_issues(prompt_pack: Mapping[str, Any]) -> list[str]:
    """Compare a package snapshot with the active validated profile."""

    active = load_active_illustration_style_profile()
    snapshot = prompt_pack.get("style_profile")
    if not isinstance(snapshot, Mapping):
        return ["prompt-pack.json must contain one style_profile snapshot"]
    issues: list[str] = []
    expected_contract_hash = style_profile_contract_sha256(active)
    for key in ("id", "version", "generation_prompt", "negative_prompt"):
        if snapshot.get(key) != active.get(key):
            issues.append(f"style_profile.{key} is stale")
    if snapshot.get("contract_sha256") != expected_contract_hash:
        issues.append("style_profile.contract_sha256 is stale")
    active_reference = active.get("reference")
    snapshot_reference = snapshot.get("reference")
    if not isinstance(active_reference, Mapping) or not isinstance(snapshot_reference, Mapping):
        issues.append("style_profile.reference is missing")
    else:
        if snapshot_reference.get("sha256") != active_reference.get("sha256"):
            issues.append("style_profile.reference.sha256 is stale")
        if snapshot_reference.get("attachment_count") != active_reference.get(
            "attachment_count"
        ):
            issues.append("style_profile.reference.attachment_count is stale")
        if active_reference.get("attachment_count") != 1:
            issues.append("active style profile must declare one attachment")
    return issues


def house_style_consistency_gate_reason(
    prompt_pack: Mapping[str, Any],
    *,
    compiled_prompts: Mapping[int, str] | Iterable[tuple[int, str]] | None = None,
) -> str | None:
    active = load_active_illustration_style_profile()
    issues = style_profile_snapshot_issues(prompt_pack)
    issues.extend(
        prompt_style_drift_issues(
            compiled_prompts,
            generation_prompt=str(active["generation_prompt"]),
        )
    )
    if not issues:
        return None
    return HOUSE_STYLE_SCENE_RULE + ". Blocked issue(s): " + "; ".join(issues)


__all__ = [
    "HOUSE_STYLE_SCENE_RULE",
    "FORBIDDEN_PROMPT_STYLE_DRIFT_TERMS",
    "house_style_consistency_gate_reason",
    "prompt_style_drift_issues",
    "style_profile_snapshot_issues",
]
