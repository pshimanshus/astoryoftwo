"""Gate carousel packages against the living success standard."""

from __future__ import annotations

from typing import Any


SUCCESSFUL_CAROUSEL_STANDARD_PATH = "wiki/insights/successful-carousel-standard.md"
SUCCESSFUL_CAROUSEL_STANDARD_CONTRACT: dict[str, Any] = {
    "source": SUCCESSFUL_CAROUSEL_STANDARD_PATH,
    "mode": "creative_north_star",
    "rule": (
        "Build a public identity mirror with concrete couple receipts, active Zuv care, "
        "an emotional reversal, and a send/save thesis; do not optimize for keywords."
    ),
    "open_reasoning_policy": "Expose the real goal and selection logic; do not optimize for keywords.",
    "prompt_rule": "Prompts must prove relationship behavior through scene-first Aachu/Zuv action.",
    "success_goals": [
        "public identity mirror",
        "concrete couple receipts",
        "active Zuv care",
        "emotional reversal",
        "send/save thesis",
        "scene-first illustration",
    ],
}


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


def _dimension(passed: bool, issue: str) -> tuple[dict[str, bool], list[str]]:
    return {"pass": passed}, ([] if passed else [issue])


def evaluate_successful_carousel_standard(package: dict[str, Any], *, slide_count: int) -> dict[str, Any]:
    text = _text(package).lower()
    object_first = any(token in text for token in ("red bag", "the bag")) and not any(
        token in text for token in ("aachu", "zuv", "he ", "she ")
    )

    dimensions: dict[str, dict[str, bool]] = {}
    issues: list[str] = []
    checks = {
        "agent_goal_alignment": _dimension(
            any(token in text for token in ("public identity mirror", "this is us", "send/save", "send this")),
            "Missing agent alignment to the public identity mirror.",
        ),
        "relationship_first_premise": _dimension(
            not object_first and ("zuv" in text or ("he " in text and "she " in text) or "partner" in text),
            "Object-first premise: relationship proof is not doing the work.",
        ),
        "story_selling_threshold": _dimension(
            _score(package) >= 28,
            "Story-Selling score is below 28/30.",
        ),
        "prompt_goal_alignment": _dimension(
            "scene" in text and any(token in text for token in ("aachu", "zuv", "identity continuity")),
            "Prompts are not aligned to scene-first Aachu/Zuv proof.",
        ),
    }
    for name, (dimension, failed) in checks.items():
        dimensions[name] = dimension
        issues.extend(failed)
    if slide_count < 4:
        issues.append("Carousel needs at least four slides to prove hook, receipt, response, and payoff.")

    passed = not issues
    return {
        "source": SUCCESSFUL_CAROUSEL_STANDARD_PATH,
        "status": "PASS" if passed else "REPAIR",
        "pass": passed,
        "agent_alignment": dimensions["agent_goal_alignment"]["pass"],
        "dimensions": dimensions,
        "issues": issues,
    }
