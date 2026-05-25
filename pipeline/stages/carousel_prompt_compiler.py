from __future__ import annotations

import re


MAX_PROMPT_CHARS = 1800

FORMAT_COPY = {
    "instagram_post": (
        "Create an exact 4:5 canvas for an Instagram carousel slide, 1080x1350 if size is "
        "available, not a 9:16 story canvas."
    ),
    "reels_stories": (
        "Create an exact 9:16 canvas for Reels/Stories, 1080x1920 if size is available, "
        "not a 4:5 carousel canvas."
    ),
}

ABSOLUTE_PATH_PATTERN = re.compile(r"/(?:[^,\]\n'\"`]+/)+[^,\]\n'\"`]+")
RELATIVE_REFERENCE_PATH_PATTERN = re.compile(r"\b(?:output|config|identity_images)/[^,\]\n'\"`]+")
REFERENCE_LIST_PATTERN = re.compile(r"\bReferences:\s*\[[^\]]*\]\.?\s*", flags=re.IGNORECASE)
CONTRACT_NOISE_PATTERN = re.compile(
    r"\b(?:"
    r"Required final file|"
    r"Source provenance|"
    r"Save packaged final to|"
    r"Native output contract|"
    r"Identity dossier path|"
    r"Identity preflight path"
    r"):\s*[^.]+\.?\s*",
    flags=re.IGNORECASE,
)


def clean_text(value: str) -> str:
    cleaned = str(value)
    cleaned = REFERENCE_LIST_PATTERN.sub("Use the attached reference images. ", cleaned)
    cleaned = ABSOLUTE_PATH_PATTERN.sub("attached reference image", cleaned)
    cleaned = RELATIVE_REFERENCE_PATH_PATTERN.sub("attached reference image", cleaned)
    cleaned = CONTRACT_NOISE_PATTERN.sub("", cleaned)
    cleaned = re.sub(r"\b(?:png|jpg|jpeg|webp|json|md)\.\s*", "", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"\s+", " ", cleaned)
    return cleaned.strip()


def extract_scene_summary(prompt: str) -> str:
    cleaned = clean_text(prompt)
    match = re.search(
        r"\bScene:\s*(.*?)(?=\s+\b(?:Mood|Composition|Style):|$)",
        cleaned,
        flags=re.IGNORECASE,
    )
    if match:
        scene = match.group(1).strip()
        if scene:
            return scene[:700].strip()
    return cleaned[:700].strip()


def compile_image_prompt(
    slide_number: int,
    slide_count: int,
    slide_copy: str,
    visual: str,
    format_key: str,
    style: str,
    negative: str,
) -> str:
    if format_key not in FORMAT_COPY:
        raise ValueError(f"Unsupported format_key: {format_key}")

    lines = [
        f"Slide {slide_number:02d} of {slide_count:02d}.",
        FORMAT_COPY[format_key],
        "Use the attached identity and style references as visual inputs.",
        "Do not resize from another format. Generate this canvas natively.",
        "Draw one soft @a.storyof.two scene where Aachu and Zuv behavior carries the joke.",
        f"Scene: {clean_text(visual)}",
        f"Style: {clean_text(style)}",
        (
            "Keep warm off-white paper, imperfect black linework, matte muted colors, "
            "expressive recurring faces, and generous negative space."
        ),
        f"Render this exact handwritten text inside the artwork: {slide_copy!r}.",
        "Add the tiny low-contrast handwritten brandmark '@a.storyof.two' at bottom-right.",
        f"Negative: {clean_text(negative)}",
    ]
    prompt = "\n".join(lines).strip() + "\n"
    if len(prompt) > MAX_PROMPT_CHARS:
        raise ValueError(f"Compiled image prompt is too long: {len(prompt)} characters.")
    return prompt
