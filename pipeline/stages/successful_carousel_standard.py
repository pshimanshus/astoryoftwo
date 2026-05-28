"""Gate carousel packages against the living success standard.

This module deliberately avoids judging creative success by a narrow list of
hook words. The standard should travel through the agents as a north star:
they must record the goals they are serving, while deterministic code only
blocks missing alignment, weak scores, undersized arcs, and obvious object-first
drift.
"""

from __future__ import annotations

import re
from typing import Any


SUCCESSFUL_CAROUSEL_STANDARD_PATH = "wiki/insights/successful-carousel-standard.md"
SUCCESSFUL_CAROUSEL_STANDARD_CONTRACT: dict[str, Any] = {
    "source": SUCCESSFUL_CAROUSEL_STANDARD_PATH,
    "mode": "creative_north_star",
    "rule": (
        "Build a public identity mirror with concrete couple receipts, active Zuv care, "
        "an emotional reversal, and a send/save thesis; stage the story in visible "
        "actions before choosing poster text; do not optimize for keywords."
    ),
    "open_reasoning_policy": (
        "Expose the real goal and selection logic; do not optimize for keywords or "
        "let slide copy substitute for staged story action."
    ),
    "prompt_rule": (
        "Prompts must prove relationship behavior through stage-scene Aachu/Zuv action; "
        "text completes the scene instead of carrying it."
    ),
    "success_goals": [
        "public identity mirror",
        "concrete couple receipts",
        "active Zuv care",
        "emotional reversal",
        "send/save thesis",
        "stage-scene storytelling",
    ],
}

TEXT_DRIVEN_VISUAL_TERMS = (
    "quote-card",
    "quote card",
    "poster text",
    "poster copy",
    "text carries",
    "text explains",
    "text-driven",
    "characters added",
    "added later",
    "stand beside a quote",
    "stand beside the text",
    "written large above",
    "generic couple art",
    "thesis as the main image",
)


def _text(value: Any) -> str:
    if isinstance(value, dict):
        return " ".join(_text(item) for item in value.values())
    if isinstance(value, list):
        return " ".join(_text(item) for item in value)
    return str(value or "")


def _score(package: dict[str, Any]) -> float:
    for value in (
        package.get("review", {}).get("story_selling_score", {}).get("total"),
        package.get("concept", {}).get("story_selling_decision", {}).get("score", {}).get("total"),
    ):
        try:
            return float(value)
        except (TypeError, ValueError):
            continue
    return 0.0


def _path(package: dict[str, Any], *keys: str) -> Any:
    value: Any = package
    for key in keys:
        if not isinstance(value, dict):
            return None
        value = value.get(key)
    return value


def _slides(package: dict[str, Any]) -> list[dict[str, Any]]:
    slides = package.get("slides", [])
    return [slide for slide in slides if isinstance(slide, dict)] if isinstance(slides, list) else []


def stage_scene_storytelling_issues(slides: list[dict[str, Any]]) -> list[str]:
    """Return deterministic misses for text-driven or unstaged visual plans.

    This check intentionally catches only observable structural misses. It does
    not try to judge taste; it blocks the old failure mode where strong slide
    copy and high scores hid the absence of staged action.
    """

    issues: list[str] = []
    for slide in slides:
        number = slide.get("slide", "?")
        visual = str(slide.get("visual", "")).lower()
        if not visual.strip():
            issues.append(f"Slide {number} has no staged visual scene.")
            continue

        leaked_terms = [term for term in TEXT_DRIVEN_VISUAL_TERMS if term in visual]
        if leaked_terms:
            issues.append(
                f"Slide {number} is text-driven instead of stage-scene storytelling: "
                f"{', '.join(leaked_terms)}."
            )
            continue

    return issues


def _alignment_record(package: dict[str, Any]) -> dict[str, Any]:
    value = _path(package, "concept", "successful_carousel_standard_alignment")
    return value if isinstance(value, dict) else {}


def _standard_contract_present(package: dict[str, Any], section: str) -> bool:
    value = _path(package, section, "successful_carousel_standard")
    return isinstance(value, dict) and value.get("source") == SUCCESSFUL_CAROUSEL_STANDARD_PATH


def _agent_alignment_pass(package: dict[str, Any]) -> bool:
    alignment = _alignment_record(package)
    goals = alignment.get("success_goals_addressed")
    if isinstance(goals, list) and len([goal for goal in goals if str(goal).strip()]) >= 5:
        return True
    return _standard_contract_present(package, "concept") and _standard_contract_present(package, "prompt_pack")


def _prompt_alignment_pass(package: dict[str, Any]) -> bool:
    if _standard_contract_present(package, "prompt_pack"):
        return True
    prompt_text = _text(package.get("prompt_pack", {})).lower()
    return (
        SUCCESSFUL_CAROUSEL_STANDARD_PATH.lower() in prompt_text
        and "do not optimize for keywords" in prompt_text
    )


def _object_first_issue(package: dict[str, Any]) -> str | None:
    """Return a failure only when the premise clearly belongs to a prop/aesthetic.

    This is intentionally conservative. An object can be a brilliant receipt of
    love; it fails only when it becomes the subject and no relationship behavior
    is doing the work.
    """

    first_slide = _slides(package)[:1]
    first_slide_text = _text(first_slide).lower()
    concept_text = _text(package.get("concept", {})).lower()
    premise_text = f"{first_slide_text} {concept_text}"
    object_terms = (
        "bag",
        "dress",
        "outfit",
        "photo",
        "place",
        "view",
        "trip",
        "food",
        "cafe",
        "light",
        "aesthetic",
        "vibe",
    )
    relationship_terms = (
        "relationship",
        "love",
        "care",
        "partner",
        "couple",
        "marry",
        "married",
        "he",
        "she",
        "they",
        "aachu",
        "zuv",
    )
    has_object = any(re.search(rf"\b{re.escape(term)}\b", premise_text) for term in object_terms)
    has_relationship = any(
        re.search(rf"\b{re.escape(term)}\b", premise_text) for term in relationship_terms
    )
    if has_object and not has_relationship:
        return "Object-first premise: the prop, place, outfit, or aesthetic is the subject instead of relationship proof."
    return None


def _dimension(passed: bool, issue: str) -> tuple[dict[str, bool], list[str]]:
    return {"pass": passed}, ([] if passed else [issue])


def evaluate_successful_carousel_standard(package: dict[str, Any], *, slide_count: int) -> dict[str, Any]:
    object_first_issue = _object_first_issue(package)
    agent_alignment = _alignment_record(package)

    dimensions: dict[str, dict[str, bool]] = {}
    issues: list[str] = []
    checks = {
        "agent_goal_alignment": _dimension(
            _agent_alignment_pass(package),
            "Missing recorded agent alignment to the successful-carousel goals.",
        ),
        "relationship_first_premise": _dimension(
            object_first_issue is None,
            object_first_issue or "Object-first premise: relationship proof is not doing the work.",
        ),
        "story_selling_threshold": _dimension(
            _score(package) >= 28,
            "Story-Selling score is below 28/30.",
        ),
        "prompt_goal_alignment": _dimension(
            _prompt_alignment_pass(package),
            "Prompts do not carry the successful-carousel standard into generation handoff.",
        ),
        "stage_scene_storytelling": _dimension(
            not stage_scene_storytelling_issues(_slides(package)),
            "Carousel is text-driven; stage visible action first and use text only to complete the scene.",
        ),
    }
    for name, (dimension, failed) in checks.items():
        dimensions[name] = dimension
        issues.extend(failed)
    issues.extend(stage_scene_storytelling_issues(_slides(package)))
    if slide_count < 4:
        issues.append("Carousel needs at least four slides to prove hook, receipt, response, and payoff.")

    passed = not issues
    return {
        "source": SUCCESSFUL_CAROUSEL_STANDARD_PATH,
        "status": "PASS" if passed else "REPAIR",
        "pass": passed,
        "agent_alignment": agent_alignment
        or {
            "status": "MISSING",
            "instruction": "Record how concept, copy, visual, prompt, and QA choices serve the success goals.",
        },
        "dimensions": dimensions,
        "issues": issues,
    }
