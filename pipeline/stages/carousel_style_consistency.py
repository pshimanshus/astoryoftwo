from __future__ import annotations

import re
from typing import Any


HOUSE_STYLE_SCENE_RULE = (
    "house-style illustrated scene consistency: @a.storyof.two final image prompts "
    "must stay premium romantic watercolor-and-ink full scenes where Aachu/Zuv "
    "behavior carries the slide; paper artifacts, posters, receipts, labels, or "
    "stationery can only be tiny scene details, never the visual system."
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


def _slide_prompt_text(prompt_pack: dict[str, Any]) -> list[tuple[int, str]]:
    prompts: list[tuple[int, str]] = []
    for index, slide in enumerate(prompt_pack.get("slides", []), start=1):
        number = int(slide.get("slide") or index)
        prompts.append((number, str(slide.get("prompt") or "")))
    return prompts


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


def prompt_style_drift_issues(prompt_pack: dict[str, Any]) -> list[str]:
    issues: list[str] = []
    for number, prompt in _slide_prompt_text(prompt_pack):
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
    return issues


def house_style_consistency_gate_reason(prompt_pack: dict[str, Any]) -> str | None:
    issues = prompt_style_drift_issues(prompt_pack)
    if not issues:
        return None
    return HOUSE_STYLE_SCENE_RULE + " Blocked issue(s): " + "; ".join(issues)
