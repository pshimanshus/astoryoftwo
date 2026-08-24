"""Compact, disk-backed generation prompt for @a.storyof.two carousels."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Any


MASTER_PROMPT_VERSION = "a-story-of-two-watercolor-ink-v5-compact"
CANONICAL_MASTER_PROMPT_PATH = Path("config/references/a-story-illustration-master-prompt.md")

MASTER_PROMPT_REQUIRED_SECTIONS = [
    "PRIMARY REQUEST",
    "ON-IMAGE TEXT",
    "SCENE",
    "IDENTITY AND WARDROBE",
    "HOUSE STYLE",
    "TEXT AND BRAND",
    "SCENE INTEGRITY",
    "ESSENTIAL NEGATIVES",
]

CANONICAL_REQUIRED_FRAGMENTS = [
    "ON-IMAGE TEXT:",
    "attached actual Aachu and Zuv identity images",
    "wardrobe anchors",
    "physical event must remain understandable with the copy hidden",
    "neutral warm ivory/off-white paper",
    "@a.storyof.two",
    "No extra person, duplicate couple",
]

NATIVE_FORMAT_SPECS: dict[str, dict[str, str]] = {
    "instagram_post": {
        "label": "Instagram Post Output",
        "ratio": "3:4",
        "size": "1080x1440",
        "avoid": "not a 9:16 Story/Reel or square canvas",
    },
    "reels_stories": {
        "label": "Reels/Stories Output",
        "ratio": "9:16",
        "size": "1080x1920",
        "avoid": "not a 3:4 carousel or square canvas",
    },
    "square": {
        "label": "Square Output",
        "ratio": "1:1",
        "size": "1080x1080",
        "avoid": "not a 3:4 carousel or 9:16 Story/Reel canvas",
    },
}


def _extract_text_fence(markdown: str) -> str:
    start_marker = "```text"
    start = markdown.find(start_marker)
    if start == -1:
        return markdown.strip()
    body_start = markdown.find("\n", start)
    if body_start == -1:
        return markdown.strip()
    end = markdown.find("\n```", body_start)
    if end == -1:
        return markdown[body_start:].strip()
    return markdown[body_start:end].strip()


@lru_cache(maxsize=1)
def load_canonical_master_prompt() -> str:
    prompt = _extract_text_fence(CANONICAL_MASTER_PROMPT_PATH.read_text(encoding="utf-8"))
    missing = [fragment for fragment in CANONICAL_REQUIRED_FRAGMENTS if fragment not in prompt]
    if missing:
        raise ValueError(
            "Canonical master prompt is missing required fragments: " + ", ".join(missing)
        )
    return prompt


def master_prompt_contract() -> dict[str, Any]:
    return {
        "version": MASTER_PROMPT_VERSION,
        "source_path": str(CANONICAL_MASTER_PROMPT_PATH),
        "required": True,
        "rule": (
            "Compile one compact generation prompt from exact copy, the physical scene, "
            "attached identity/style references, wardrobe, camera/focal direction, house "
            "style, native dimensions, brandmark, and essential negatives. Keep workflow "
            "state, hashes, provenance, and QA schemas outside the model prompt."
        ),
        "required_sections": MASTER_PROMPT_REQUIRED_SECTIONS,
        "native_outputs": {
            "instagram_post": {
                "aspect_ratio": "3:4",
                "size": "1080x1440",
                "source_size": "1440x1920",
                "directory": "final/",
            },
            "reels_stories": {
                "aspect_ratio": "9:16",
                "size": "1080x1920",
                "directory": "final-reels-stories/",
            },
            "square": {
                "aspect_ratio": "1:1",
                "size": "1080x1080",
                "source_size": "1080x1080",
                "directory": "final-square/",
            },
        },
        "text_rule": (
            "Bake the supplied ON-IMAGE TEXT into the illustration exactly, preserving "
            "spelling, punctuation, capitalization, and line breaks. Add no other text "
            "except the tiny top-right @a.storyof.two brandmark."
        ),
    }


def _fill_slide_placeholders(
    master_prompt: str,
    *,
    slide_copy: str,
    scene_description: str,
    negative_prompt: str,
) -> str:
    return (
        master_prompt.replace(
            "[INSERT EXACT TEXT TO INCLUDE IN THE ILLUSTRATION HERE]",
            slide_copy,
        )
        .replace("[INSERT SLIDE SCENE HERE]", scene_description)
        .replace("[INSERT ESSENTIAL NEGATIVES HERE]", negative_prompt)
        .strip()
    )


def build_generation_master_prompt(
    *,
    slide_number: int,
    slide_count: int,
    slide_copy: str,
    scene_description: str,
    pose_description: str,
    wardrobe_description: str,
    prop_description: str,
    background_description: str,
    emotion_description: str,
    format_key: str,
    style_prompt: str,
    negative_prompt: str,
) -> str:
    if format_key not in NATIVE_FORMAT_SPECS:
        raise ValueError(f"Unsupported format_key: {format_key}")

    spec = NATIVE_FORMAT_SPECS[format_key]
    master = _fill_slide_placeholders(
        load_canonical_master_prompt(),
        slide_copy=slide_copy,
        scene_description=scene_description,
        negative_prompt=negative_prompt,
    )
    slide_contract = f"""

SLIDE DIRECTION — {slide_number:02d}/{slide_count:02d}:
Canvas: {spec['label']}; exact {spec['size']} px; native {spec['ratio']}; {spec['avoid']}. Compose natively. Do not crop, pad, stretch, resize, or derive it from another format.
Camera and body language: {pose_description}
Wardrobe from attached identity references: {wardrobe_description}
Story props: {prop_description}
Setting and focal hierarchy: {background_description}
Emotional beat: {emotion_description}
Additional style note: {style_prompt}
"""
    return (master + slide_contract).strip() + "\n"
