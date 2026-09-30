"""Compact, disk-backed generation prompt for @a.storyof.two carousels."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
import re
from typing import Any

from pipeline.stages.carousel_sequence import copy_issue

MASTER_PROMPT_VERSION = "a-story-of-two-v7-cinematic-style-profile"
CANONICAL_MASTER_PROMPT_PATH = Path("config/references/a-story-illustration-master-prompt.md")

MASTER_PROMPT_REQUIRED_SECTIONS = [
    "PRIMARY REQUEST",
    "ON-IMAGE TEXT",
    "SCENE",
    "CINEMATIC STORY FRAME",
    "LIMB AND HAND PLAN",
    "WHOLE-PERSON AND OBJECT TOPOLOGY",
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
    "@a.storyof.two",
    "No extra person, duplicate couple",
    "LIMB AND HAND PLAN:",
    "WHOLE-PERSON AND OBJECT TOPOLOGY:",
    "[INSERT SLIDE-SPECIFIC CINEMATIC DIRECTION HERE]",
    "[INSERT CANONICAL HOUSE STYLE HERE]",
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
                "source_size": "1080x1440",
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
    cinematic_description: str,
    hand_description: str,
    spatial_description: str,
    style_prompt: str,
    negative_prompt: str,
) -> str:
    rendered = (
        master_prompt.replace(
            "[INSERT EXACT TEXT TO INCLUDE IN THE ILLUSTRATION HERE]",
            slide_copy,
        )
        .replace("[INSERT SLIDE SCENE HERE]", scene_description)
        .replace(
            "[INSERT SLIDE-SPECIFIC CINEMATIC DIRECTION HERE]",
            cinematic_description,
        )
        .replace("[INSERT SLIDE-SPECIFIC LIMB AND HAND PLAN HERE]", hand_description)
        .replace("[INSERT SLIDE-SPECIFIC PERSON AND OBJECT TOPOLOGY HERE]", spatial_description)
        .replace("[INSERT CANONICAL HOUSE STYLE HERE]", style_prompt)
        .replace("[INSERT ESSENTIAL NEGATIVES HERE]", negative_prompt)
        .strip()
    )
    if "[INSERT " in rendered:
        raise ValueError("Canonical master prompt contains an unresolved placeholder.")
    if rendered.count(style_prompt) != 1:
        raise ValueError("Canonical house style must be inserted exactly once.")
    return rendered


def build_generation_master_prompt(
    *,
    slide_number: int,
    slide_count: int,
    slide_copy: str,
    scene_description: str,
    cinematic_description: str,
    hand_description: str,
    spatial_description: str,
    wardrobe_description: str,
    prop_description: str,
    format_key: str,
    style_prompt: str,
    negative_prompt: str,
    must_change: list[str] | None = None,
    must_preserve: list[str] | None = None,
    copy_mode: str = "text",
) -> str:
    if format_key not in NATIVE_FORMAT_SPECS:
        raise ValueError(f"Unsupported format_key: {format_key}")
    issue = copy_issue({"copy": slide_copy, "copy_mode": copy_mode})
    if issue:
        raise ValueError(issue)

    spec = NATIVE_FORMAT_SPECS[format_key]
    master = _fill_slide_placeholders(
        load_canonical_master_prompt(),
        slide_copy=slide_copy,
        scene_description=scene_description,
        cinematic_description=cinematic_description,
        hand_description=hand_description,
        spatial_description=spatial_description,
        style_prompt=style_prompt,
        negative_prompt=negative_prompt,
    )
    if copy_mode == "wordless":
        # Rewrite only the canonical instruction section, leaving locked scene
        # and style content untouched. The empty ON-IMAGE TEXT section carries
        # no candidate words for the model to accidentally render.
        master, count = re.subn(
            r"(?<=\nTEXT AND BRAND:\n).*?(?=\n\nSCENE INTEGRITY:)",
            "No story text. This is an intentionally wordless slide. "
            "Do not invent dialogue, captions, labels, or lettering. "
            "Render only the tiny, low-contrast handwritten brandmark "
            "`@a.storyof.two` at the top-right.",
            master,
            flags=re.DOTALL,
        )
        if count != 1:
            raise ValueError("Canonical wordless text-and-brand section is unresolved.")
    slide_contract = f"""

SLIDE DIRECTION — {slide_number:02d}/{slide_count:02d}:
Canvas: {spec['label']}; exact {spec['size']} px; native {spec['ratio']}; {spec['avoid']}. Compose natively. Do not crop, pad, stretch, resize, or derive it from another format.
Wardrobe from attached identity references: {wardrobe_description}
Story props: {prop_description}
"""
    feedback_contract = ""
    if must_change or must_preserve:
        change_lines = "\n".join(f"- {value}" for value in must_change or []) or "- None."
        preserve_lines = "\n".join(f"- {value}" for value in must_preserve or []) or "- None."
        feedback_contract = f"""

ACTIVE CREATOR FEEDBACK — THIS SLIDE:
MUST CHANGE:
{change_lines}
MUST PRESERVE:
{preserve_lines}
"""
    return (master + slide_contract + feedback_contract).strip() + "\n"
