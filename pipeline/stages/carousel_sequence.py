"""Story/beat contracts and authored whole-sequence review validation.

This module checks evidence structure and freshness. It never inspects pixels
or supplies an editorial verdict. Research metadata is not a generation input.
"""
from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

SEQUENCE_CONTRACT = "carousel-sequence/v1"
REVIEW_SCHEMA = "carousel-sequence-review/v1"
STORY_FIELDS = (
    "theme", "recognition", "sequence_mode", "opening_promise", "mismatch",
    "turn_or_accumulation", "payoff", "send_reason",
)
SEQUENCE_MODES = {
    "unfolding_question", "recognition_rewards", "accumulating_evidence",
    "relationship_change", "hybrid", "creator_defined",
}
RELATION_KINDS = {"contradiction", "completion", "reinterpretation", "direct_depiction", "wordless"}
REVIEW_SLIDE_FIELDS = (
    "slide", "role", "copy", "copy_mode", "beat_delta", "copy_image_relation",
    "physical_action", "relationship_state", "visual_richness", "continuity_lock",
    "camera", "focal_hierarchy", "setting", "props", "wardrobe", "hand_map", "spatial_topology",
)


def _text(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def copy_issue(slide: Mapping[str, Any]) -> str | None:
    mode = slide.get("copy_mode", "text")
    text = slide.get("copy", slide.get("text"))
    if mode not in ("text", "wordless"):
        return "copy_mode must be text or wordless"
    if not isinstance(text, str):
        return "copy must be an exact string"
    if mode == "wordless":
        return None if text == "" else "wordless copy must be the empty string"
    return None if text.strip() else "text slide is missing exact copy; intentional silence requires copy_mode=wordless"


def story_plan_issues(plan: Any) -> list[str]:
    if not isinstance(plan, Mapping):
        return ["story_plan must contain the approved story intention"]
    issues = [f"story_plan.{key} is required" for key in STORY_FIELDS if not _text(plan.get(key))]
    if isinstance(plan.get("sequence_mode"), str) and plan["sequence_mode"] not in SEQUENCE_MODES:
        issues.append("story_plan.sequence_mode must name a supported mode or creator_defined")
    return issues


def slide_sequence_issues(slide: Mapping[str, Any], require_fields: bool = False) -> list[str]:
    issues = []
    error = copy_issue(slide)
    if error:
        issues.append(error)
    for key in ("role", "beat_delta"):
        if (require_fields or key in slide) and not _text(slide.get(key)):
            issues.append(f"{key} must name this slide's contribution")
    if require_fields or "copy_image_relation" in slide:
        relation = slide.get("copy_image_relation")
        if not isinstance(relation, Mapping):
            issues.append("copy_image_relation must contain kind and physical proof")
        else:
            if not isinstance(relation.get("kind"), str) or relation["kind"] not in RELATION_KINDS:
                issues.append("copy_image_relation.kind is invalid")
            if not _text(relation.get("proof")):
                issues.append("copy_image_relation.proof must describe the visible relationship between image and words")
            if (slide.get("copy_mode") == "wordless") != (relation.get("kind") == "wordless"):
                issues.append("copy_image_relation.kind must agree with copy_mode")
    return issues


def sequence_enabled(context: Mapping[str, Any], slides: Sequence[Mapping[str, Any]]) -> bool:
    return ("sequence_contract" in context or "story_plan" in context
            or any("beat_delta" in s or "copy_image_relation" in s for s in slides))


def sequence_plan_issues(context: Mapping[str, Any], slides: Sequence[Mapping[str, Any]]) -> list[str]:
    if not sequence_enabled(context, slides):
        return []  # Historical packages retain their original contract.
    issues = story_plan_issues(context.get("story_plan"))
    if context.get("sequence_contract", SEQUENCE_CONTRACT) != SEQUENCE_CONTRACT:
        issues.append("unsupported sequence_contract")
    if not slides:
        issues.append("sequence needs at least one slide")
    if any(type(s.get("slide")) is not int for s in slides) or [s.get("slide") for s in slides] != list(range(1, len(slides) + 1)):
        issues.append("sequence slide numbers must be unique and ordered from 1")
    for index, slide in enumerate(slides, 1):
        issues.extend(f"slide {index}: {issue}" for issue in slide_sequence_issues(slide, True))
        if not _text(slide.get("physical_action")):
            issues.append(f"slide {index}: physical_action is required")
        richness = slide.get("visual_richness")
        richness = richness if isinstance(richness, Mapping) else {}
        if index < len(slides) and not _text(richness.get("continuation_pull")):
            issues.append(f"slide {index}: continuation_pull must name the next question or recognition reward")
    return issues


def sequence_input_fingerprint(context: Mapping[str, Any], slides: Sequence[Mapping[str, Any]]) -> str:
    payload = {
        "contract": context.get("sequence_contract", SEQUENCE_CONTRACT),
        "story_plan": context.get("story_plan"),
        "slides": [{key: s[key] for key in REVIEW_SLIDE_FIELDS if key in s} for s in slides],
    }
    return "sha256:" + hashlib.sha256(json.dumps(payload, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode()).hexdigest()


def package_sequence_inputs(package: Path) -> tuple[dict, list[dict]]:
    context_path = package / "creative-context.json"
    context = json.loads(context_path.read_text()) if context_path.exists() else {}
    payload = json.loads((package / "slides.json").read_text())
    slides = payload.get("slides") if isinstance(payload, dict) else payload
    if not isinstance(context, dict) or not isinstance(slides, list) or any(not isinstance(s, dict) for s in slides):
        raise ValueError("sequence context and slides have invalid shapes")
    return context, slides


def sequence_review_issues(context: Mapping[str, Any], slides: Sequence[Mapping[str, Any]], review: Any, formats: Sequence[str]) -> list[str]:
    if not sequence_enabled(context, slides):
        return []
    issues = [f"sequence: {issue}" for issue in sequence_plan_issues(context, slides)]
    if not isinstance(review, Mapping):
        return issues + ["sequence_review is required for the complete ordered deck"]
    if review.get("schema_version") != REVIEW_SCHEMA:
        issues.append(f"sequence_review.schema_version must be {REVIEW_SCHEMA}")
    if review.get("source_sha256") != sequence_input_fingerprint(context, slides):
        issues.append("sequence_review.source_sha256 is missing or stale")
    reviews = review.get("formats")
    if not isinstance(reviews, Mapping) or set(reviews) != set(formats):
        return issues + ["sequence_review.formats must match locked formats exactly"]
    numbers = [s["slide"] for s in slides if isinstance(s.get("slide"), int)]
    pairs = list(zip(numbers, numbers[1:]))
    for fmt in formats:
        row = reviews[fmt]
        prefix = f"sequence_review {fmt}"
        if not isinstance(row, Mapping):
            issues.append(f"{prefix} must contain authored observations")
            continue
        if row.get("status") != "PASS":
            issues.append(f"{prefix} did not pass")
        if row.get("issues") != []:
            issues.append(f"{prefix} has missing or unresolved issues: {row.get('issues')}")
        for field in ("hook_observed", "coherence_observed", "redundancy_observed"):
            if not _text(row.get(field)):
                issues.append(f"{prefix}.{field} needs actual sequence evidence")
        transitions = row.get("transitions")
        if (not isinstance(transitions, list)
            or any(not isinstance(r, Mapping) for r in transitions)
            or [(r.get("from_slide"), r.get("to_slide")) for r in transitions] != pairs):
            issues.append(f"{prefix}.transitions must cover every adjacent pair once in order")
        elif any(not _text(r.get("development_observed")) for r in transitions):
            issues.append(f"{prefix}.transitions need observed development, timing or recognition reward")
        relations = row.get("copy_image")
        if (not isinstance(relations, list) or any(not isinstance(r, Mapping) for r in relations)
            or [r.get("slide") for r in relations] != numbers):
            issues.append(f"{prefix}.copy_image must cover every slide once in order")
        else:
            for planned, observed in zip(slides, relations):
                relation = planned.get("copy_image_relation")
                kind = relation.get("kind") if isinstance(relation, Mapping) else None
                if observed.get("kind") != kind or not _text(observed.get("observed")):
                    issues.append(f"{prefix}.copy_image slide {planned.get('slide')} lacks the planned relation and observed proof")
        closure = row.get("closure")
        if not isinstance(closure, Mapping):
            issues.append(f"{prefix}.closure is required")
        else:
            setup = closure.get("setup_slides")
            if (not isinstance(setup, list) or not setup
                or any(type(n) is not int or n not in numbers for n in setup)
                or len(set(setup)) != len(setup)):
                issues.append(f"{prefix}.closure.setup_slides must reference real setup positions")
            if not numbers or closure.get("ending_slide") != numbers[-1] or not _text(closure.get("observed")):
                issues.append(f"{prefix}.closure must explain the actual ending against its setup")
    return issues
