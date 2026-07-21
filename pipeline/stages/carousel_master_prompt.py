"""Disk-backed final illustration prompt for @a.storyof.two carousels."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Any


MASTER_PROMPT_VERSION = "a-story-of-two-watercolor-ink-v4-observational-intimacy-premium-lock"
CANONICAL_MASTER_PROMPT_PATH = Path("config/references/a-story-illustration-master-prompt.md")

MASTER_PROMPT_REQUIRED_SECTIONS = [
    "USE CASE",
    "ASSET TYPE",
    "REFERENCE IMAGE ROLES",
    "IDENTITY IMAGE INPUT CONTRACT",
    "PRIMARY REQUEST",
    "SCENE",
    "CHARACTER IDENTITY LOCK",
    "FACE PRESERVATION RULES",
    "ILLUSTRATION STYLE",
    "COLOR PALETTE",
    "COMPOSITION AND FORMAT",
    "EMOTIONAL DIRECTION",
    "WARDROBE CONTINUITY",
    "RECURRING PROPS AND MOTIFS",
    "BACKGROUND STYLE",
    "LINE AND TEXTURE DETAILS",
    "ANATOMY AND QUALITY RULES",
    "SCENE LOGIC AND POSE RULES",
    "TEXT RULE",
    "STYLE ACCEPTANCE RULE",
    "BRANDMARK RULE",
    "FINAL IDENTITY REINFORCEMENT",
    "FINAL STYLE REINFORCEMENT",
    "REFERENCE ESSENCE RULE",
    "BRAND INTEGRATION VISIBILITY RULE",
    "BRAND LABEL WORKFLOW",
]

CANONICAL_REQUIRED_FRAGMENTS = [
    "ON-IMAGE TEXT:",
    "@a.storyof.two",
    "prompt assembly is autopilot by default",
    "treat those photos as current-request identity references",
    "This means neutral premium ivory/off-white paper, not yellow, not mustard",
    "If the paper/background reads yellow, mustard, sepia, beige/tan, parchment, coffee-stained, or heavy cream",
    "The final image-generation call must attach selected actual identity images",
    "Wardrobe must be selected from the attached identity images",
    "BRANDMARK RULE:",
    "BRAND LABEL WORKFLOW:",
]

NATIVE_FORMAT_SPECS: dict[str, dict[str, str]] = {
    "instagram_post": {
        "label": "Instagram Post Output",
        "ratio": "3:4",
        "size": "1080x1440",
        "canvas": "exact 3:4 canvas for an Instagram carousel source, native 1440x1920 px, exported proportionally to 1080x1440 px",
        "avoid": "not a 9:16 story canvas",
    },
    "reels_stories": {
        "label": "Reels/Stories Output",
        "ratio": "9:16",
        "size": "1080x1920",
        "canvas": "exact 9:16 canvas for Reels/Stories, native 1080x1920 px",
        "avoid": "not a 3:4 carousel canvas",
    },
    "square": {
        "label": "Square Output",
        "ratio": "1:1",
        "size": "1080x1080",
        "canvas": "exact 1:1 square canvas, native 1080x1080 px",
        "avoid": "not a 3:4 carousel or 9:16 story canvas",
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
            "Canonical master prompt is missing required fragments: "
            + ", ".join(missing)
        )
    return prompt


def master_prompt_contract() -> dict[str, Any]:
    return {
        "version": MASTER_PROMPT_VERSION,
        "source_path": str(CANONICAL_MASTER_PROMPT_PATH),
        "required": True,
        "rule": (
            "Every final Codex/image-generation prompt for @a.storyof.two carousel slides "
            "must load the creator-locked watercolor-and-ink master prompt from disk, "
            "then fill the slide-specific on-image text, scene, pose, wardrobe, "
            "props, background, emotion, native format, and negative prompt."
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
            "When ON-IMAGE TEXT is supplied, bake that exact readable text naturally "
            "into the illustration as polished hand-drawn typography in clean warm "
            "negative space. Preserve spelling, punctuation, capitalization, and line "
            "breaks exactly. Do not invent any other text."
        ),
    }


def _fill_slide_placeholders(master_prompt: str, *, slide_copy: str, scene_description: str) -> str:
    return (
        master_prompt.replace(
            "[INSERT EXACT TEXT TO INCLUDE IN THE ILLUSTRATION HERE]",
            slide_copy,
        )
        .replace("[INSERT SLIDE SCENE HERE]", scene_description)
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
    )
    slide_contract = f"""

MASTER PROMPT VERSION:
{MASTER_PROMPT_VERSION}

SLIDE-SPECIFIC CONTRACT:
This is a premium hand-drawn romantic narrative slide with exact readable text baked naturally into the image.
Current render: {spec['label']}, {spec['canvas']}, {spec['avoid']}.
Required output size: exactly {spec['size']} px, native {spec['ratio']}. The pixel size is mandatory, not optional. Generate the canvas natively at exactly {spec['size']} px; never output any other dimension and never rely on the aspect ratio alone.
Do not resize from another format. Do not resize, crop, pad, stretch, or extend one format from the other. Generate this canvas natively.
Preserve spelling, line breaks, punctuation, and wording exactly.
Slide {slide_number:02d} of {slide_count:02d}.

PROJECT STYLE LOCK:
{style_prompt}

POSE/BODY LANGUAGE:
{pose_description}

WARDROBE:
{wardrobe_description}

PROPS:
{prop_description}

BACKGROUND:
{background_description}

EMOTION:
{emotion_description}

NEGATIVE PROMPT:
{negative_prompt}
"""
    return (master + slide_contract).strip() + "\n"
