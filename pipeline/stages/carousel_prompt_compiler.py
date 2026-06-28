from __future__ import annotations

import re

from pipeline.stages.carousel_master_prompt import build_generation_master_prompt

# Upper bound on a single compiled image prompt. The canonical master prompt body
# alone is ~17k chars; this leaves comfortable headroom for the per-slide contract
# (size, pose, wardrobe, props, background, emotion, style lock, negative prompt)
# while still catching runaway inputs. The Codex built-in image path accepts long
# prompts, so the cap is a guardrail against accidental bloat, not a model limit.
MAX_PROMPT_CHARS = 24000

FORMAT_COPY = {
    "instagram_post": (
        "Create an exact 4:5 canvas for an Instagram carousel slide at exactly 1080x1350 px, "
        "not a 9:16 story canvas."
    ),
    "reels_stories": (
        "Create an exact 9:16 canvas for Reels/Stories at exactly 1080x1920 px, "
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


def clean_slide_copy(value: str) -> str:
    text = str(value).replace("\r\n", "\n").replace("\r", "\n")
    return "\n".join(clean_text(line) for line in text.split("\n")).strip()


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
    *,
    pose: str | None = None,
    wardrobe: str | None = None,
    props: str | None = None,
    background: str | None = None,
    emotion: str | None = None,
) -> str:
    if format_key not in FORMAT_COPY:
        raise ValueError(f"Unsupported format_key: {format_key}")

    scene = clean_text(visual)
    prompt = build_generation_master_prompt(
        slide_number=slide_number,
        slide_count=slide_count,
        slide_copy=clean_slide_copy(slide_copy),
        scene_description=scene,
        pose_description=clean_text(
            pose
            or (
                "Use scene-specific lived-in couple body language: soft eye contact, a small "
                "care gesture, warm teasing posture, or leaning toward each other without "
                "feeling staged."
            )
        ),
        wardrobe_description=clean_text(
            wardrobe
            or (
                "Use the selected identity images or current identity photos as wardrobe anchors; "
                "vary scene-appropriate outfits and repeat items only when continuity requires."
            )
        ),
        prop_description=clean_text(
            props
            or (
                "Use only props implied by the scene or recurring @a.storyof.two motifs; keep "
                "them secondary to the couple's emotional behavior."
            )
        ),
        background_description=clean_text(
            background
            or (
                "Soft minimal environment implied by the scene, with faded watercolor edges and "
                "lower detail than the characters."
            )
        ),
        emotion_description=clean_text(
            emotion
            or "Quietly in love, comfortable, playful, emotionally safe, and specific to the slide beat."
        ),
        format_key=format_key,
        style_prompt=clean_text(style),
        negative_prompt=clean_text(negative),
    ).strip() + "\n"
    if len(prompt) > MAX_PROMPT_CHARS:
        raise ValueError(f"Compiled image prompt is too long: {len(prompt)} characters.")
    return prompt
