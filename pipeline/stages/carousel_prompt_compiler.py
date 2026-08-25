from __future__ import annotations

import re
from typing import Any

from pipeline.stages.carousel_master_prompt import build_generation_master_prompt
from pipeline.stages.carousel_visual_integrity import build_action_topology_contract


# Image prompts are creative handoffs, not serialized workflow state. These caps
# keep the physical scene and exact copy salient instead of burying them under
# validator prose.
MAX_PROMPT_CHARS = 8000
MAX_PROMPT_WORDS = 900
MAX_SCENE_WORDS = 180
MAX_NEGATIVE_WORDS = 80

BASE_ESSENTIAL_NEGATIVES = (
    "No generic stock couple, face drift, extra fingers or limbs, detached hands, "
    "merged bodies, impossible grip, object penetration, random text, external logo "
    "or watermark, split screen, UI, photorealism, anime, 3D render, flat vector art, "
    "glossy finish, harsh shadow, oversaturation, or yellow paper."
)

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
    # Exact on-image copy is creator-owned data, not scene prose. Only normalize
    # platform line endings; path/reference/noise sanitizers would rewrite
    # legitimate words, punctuation, extensions, or deliberate spacing.
    return str(value).replace("\r\n", "\n").replace("\r", "\n")


def _word_count(value: str) -> int:
    return len(value.split())


def _compact_words(
    value: str,
    limit: int,
    *,
    field_name: str,
    allow_truncate: bool = False,
) -> str:
    """Deduplicate repetition, then fail rather than erase locked semantics."""

    cleaned = clean_text(value)
    if _word_count(cleaned) <= limit:
        return cleaned

    unique_sentences: list[str] = []
    seen: set[str] = set()
    for sentence in re.split(r"(?<=[.!?])\s+", cleaned):
        normalized = re.sub(r"\W+", " ", sentence).strip().casefold()
        if not normalized or normalized in seen:
            continue
        seen.add(normalized)
        unique_sentences.append(sentence.strip())

    compacted = " ".join(unique_sentences)
    words = compacted.split()
    if len(words) <= limit:
        return compacted.strip()
    if allow_truncate:
        return " ".join(words[:limit]).strip()
    raise ValueError(
        f"Locked {field_name} exceeds its {limit}-word prompt limit after deduplication."
    )


def extract_scene_summary(prompt: str) -> str:
    cleaned = clean_text(prompt)
    match = re.search(
        r"\bScene:\s*(.*?)(?=\s+\b(?:Mood|Composition|Style):|$)",
        cleaned,
        flags=re.IGNORECASE,
    )
    if match and match.group(1).strip():
        return _compact_words(
            match.group(1),
            MAX_SCENE_WORDS,
            field_name="legacy scene",
            allow_truncate=True,
        )
    return _compact_words(
        cleaned,
        MAX_SCENE_WORDS,
        field_name="legacy scene",
        allow_truncate=True,
    )


def _build_prompt(
    *,
    slide_number: int,
    slide_count: int,
    slide_copy: str,
    scene: str,
    format_key: str,
    style: str,
    negative: str,
    pose: str,
    wardrobe: str,
    props: str,
    background: str,
    emotion: str,
) -> str:
    return build_generation_master_prompt(
        slide_number=slide_number,
        slide_count=slide_count,
        slide_copy=slide_copy,
        scene_description=scene,
        pose_description=pose,
        wardrobe_description=wardrobe,
        prop_description=props,
        background_description=background,
        emotion_description=emotion,
        format_key=format_key,
        style_prompt=style,
        negative_prompt=negative,
    )


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
    hand_map: dict[str, Any] | None = None,
    action_topology: dict[str, Any] | None = None,
    spatial_topology: dict[str, Any] | None = None,
    visual_richness: dict[str, Any] | None = None,
) -> str:
    """Compile one compact, generation-facing prompt.

    The rich hand, spatial, and visual-story contracts remain validator inputs;
    they are intentionally not serialized into the model prompt. Action
    chronology is checked here only because a contradictory scene should never
    reach generation.
    """

    # Retain the public call shape while moving these contracts to validators.
    del hand_map, spatial_topology, visual_richness

    copy = clean_slide_copy(slide_copy)
    full_scene = clean_text(visual)
    action_contract = action_topology or build_action_topology_contract(full_scene, copy)
    action_issues = action_contract.get("issues") if isinstance(action_contract, dict) else []
    if action_issues:
        raise ValueError(
            "Action chronology/topology is unresolved: "
            + "; ".join(str(item) for item in action_issues)
        )

    fields = {
        "scene": _compact_words(full_scene, MAX_SCENE_WORDS, field_name="scene"),
        "pose": _compact_words(
            pose
            or (
                "Choose the shot size and camera angle that make the physical action clearest. "
                "Keep the action and its reaction as the focal hierarchy; use natural, "
                "scene-specific body language rather than a posed couple portrait."
            ),
            60,
            field_name="pose/composition/camera",
        ),
        "wardrobe": _compact_words(
            wardrobe
            or (
                "Use visible clothing and accessory anchors from the attached identity or "
                "current-request photos; repeat only when the scene continues."
            ),
            55,
            field_name="wardrobe",
        ),
        "props": _compact_words(
            props or "Include only objects required by the action or its visible consequence.",
            35,
            field_name="props",
        ),
        "background": _compact_words(
            background
            or (
                "Use a lived-in setting that proves what just happened. Keep it secondary "
                "to the action, with clear foreground, subject plane, and negative space."
            ),
            45,
            field_name="background/setting",
        ),
        "emotion": _compact_words(
            emotion or "Match the exact beat: intimate, specific, human, and emotionally legible.",
            25,
            field_name="emotion",
        ),
        "style": _compact_words(style, 55, field_name="style"),
        "negative": _compact_words(
            f"{BASE_ESSENTIAL_NEGATIVES} {negative}",
            MAX_NEGATIVE_WORDS,
            field_name="essential negatives",
        ),
    }

    prompt = _build_prompt(
        slide_number=slide_number,
        slide_count=slide_count,
        slide_copy=copy,
        format_key=format_key,
        **fields,
    )

    if len(prompt) > MAX_PROMPT_CHARS or _word_count(prompt) > MAX_PROMPT_WORDS:
        raise ValueError(
            "Compiled image prompt is too long: "
            f"{len(prompt)} characters / {_word_count(prompt)} words."
        )
    return prompt
