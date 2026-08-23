from __future__ import annotations

from copy import deepcopy
import re
from typing import Any

from pipeline.stages.carousel_master_prompt import build_generation_master_prompt
from pipeline.stages.carousel_visual_integrity import (
    action_topology_prompt,
    build_action_topology_contract,
    build_hand_ownership_map,
    build_spatial_topology_contract,
    build_visual_richness_contract,
    hand_ownership_prompt,
    spatial_topology_prompt,
    visual_richness_prompt,
)

# Upper bound on a single compiled image prompt. The canonical master prompt body
# alone is ~17k chars; this leaves comfortable headroom for the per-slide contract
# (size, pose, wardrobe, props, background, emotion, style lock, negative prompt)
# while still catching runaway inputs. The Codex built-in image path accepts long
# prompts, and the built-in provider enforces this as a hard request limit.
# Whole-person topology and hand-ownership contracts are deliberately explicit;
# keep enough room for both instead of trimming safety-critical clauses.
MAX_PROMPT_CHARS = 32000

# These generic closing sections repeat rules already present earlier in the
# master prompt. For a dense, topology-sensitive scene, remove them only as a
# last-mile size repair so door/hand/spatial instructions remain intact.
DENSE_PROMPT_REDUNDANT_SECTIONS = {
    "ASSET TYPE:",
    "BRAND INTEGRATION VISIBILITY RULE:",
    "BRAND LABEL WORKFLOW:",
    "REFERENCE ESSENCE RULE:",
    "FINAL IDENTITY REINFORCEMENT:",
    "FINAL STYLE REINFORCEMENT:",
    "PROJECT STYLE LOCK:",
}

# Targeted image edits already carry a locked scene, exact copy, identity lock,
# and slide-specific hand/topology contracts.  Repeating broad ideation advice
# after that point dilutes the local repair instruction without adding a gate.
TARGETED_EDIT_REDUNDANT_SECTIONS = DENSE_PROMPT_REDUNDANT_SECTIONS | {
    "USE CASE:",
    "REFERENCE IMAGE ROLES:",
    "IDENTITY IMAGE INPUT CONTRACT:",
    "FACE PRESERVATION RULES:",
    "ILLUSTRATION STYLE:",
    "COMPOSITION AND FORMAT:",
    "EMOTIONAL DIRECTION:",
    "WARDROBE CONTINUITY:",
    "RECURRING PROPS AND MOTIFS:",
    "BACKGROUND STYLE:",
    "LINE AND TEXTURE DETAILS:",
    "ANATOMY AND QUALITY RULES:",
    "SCENE LOGIC AND POSE RULES:",
}

TARGETED_EDIT_CONCISE_SECTIONS = {
    "STAGE-SCENE / VISUAL RECEIPT:": (
        "Keep the locked visible behavior and object contact readable with the copy hidden."
    ),
    "SHOT LADDER / VISUAL VARIETY:": (
        "Preserve this slide's locked shot role and do not invent another panel or scene. "
        "No split-screen divider may appear."
    ),
    "RELATIONSHIP MOTION:": (
        "Preserve the locked shared action and emotional turn; do not replace it with a generic pose."
    ),
}

FORMAT_COPY = {
    "instagram_post": (
        "Create an exact 3:4 canvas for an Instagram carousel source at exactly 1440x1920 px, "
        "to be exported proportionally to a 1080x1440 final; not a 9:16 story canvas."
    ),
    "reels_stories": (
        "Create an exact 9:16 canvas for Reels/Stories at exactly 1080x1920 px, "
        "not a 3:4 carousel canvas."
    ),
    "square": (
        "Create an exact 1:1 square canvas at exactly 1080x1080 px, composed natively "
        "for square rather than cropped, padded, or stretched from another canvas."
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


def prompt_contract_without_repeated_scene(contract: dict[str, Any]) -> dict[str, Any]:
    """Keep the safety contract while avoiding four verbatim scene copies.

    The locked scene is already rendered once in the master prompt. Hand,
    action, spatial-topology, and richness sections need to bind to that scene,
    but repeating a long scene verbatim inside each section can overflow the
    prompt cap on the exact door/chronology beats that need those guards most.
    """

    compact = deepcopy(contract)
    if compact.get("scene_action_binding"):
        compact["scene_action_binding"] = "Use the locked Scene description above."
    return compact


def compact_dense_prompt(prompt: str) -> str:
    """Drop only redundant master sections while preserving scene hard gates."""

    parts = prompt.strip().split("\n\n")
    kept = [
        part
        for part in parts
        if not any(part.startswith(heading) for heading in DENSE_PROMPT_REDUNDANT_SECTIONS)
    ]
    return "\n\n".join(kept).strip() + "\n"


def compact_targeted_edit_prompt(prompt: str) -> str:
    """Keep edit-critical gates prominent and remove broad first-pass advice."""

    kept: list[str] = []
    for part in prompt.strip().split("\n\n"):
        if any(
            part.startswith(heading)
            for heading in TARGETED_EDIT_REDUNDANT_SECTIONS
        ):
            continue
        concise_heading = next(
            (
                heading
                for heading in TARGETED_EDIT_CONCISE_SECTIONS
                if part.startswith(heading)
            ),
            None,
        )
        if concise_heading is not None:
            kept.append(
                concise_heading
                + "\n"
                + TARGETED_EDIT_CONCISE_SECTIONS[concise_heading]
            )
        else:
            kept.append(part)
    return "\n\n".join(kept).strip() + "\n"


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
    if format_key not in FORMAT_COPY:
        raise ValueError(f"Unsupported format_key: {format_key}")

    scene = clean_text(visual)
    hand_contract = hand_map or build_hand_ownership_map(scene)
    action_contract = action_topology or build_action_topology_contract(
        scene, clean_slide_copy(slide_copy)
    )
    action_issues = action_contract.get("issues") if isinstance(action_contract, dict) else []
    if action_issues:
        raise ValueError(
            "Action chronology/topology is unresolved: "
            + "; ".join(str(item) for item in action_issues)
        )
    topology_contract = spatial_topology or build_spatial_topology_contract(scene)
    richness_contract = visual_richness or build_visual_richness_contract(scene)
    pose_text = clean_text(
        pose
        or (
            "Use scene-specific lived-in couple body language: soft eye contact, a small "
            "care gesture, warm teasing posture, or leaning toward each other without "
            "feeling staged."
        )
    )
    pose_text += "\n\n" + hand_ownership_prompt(
        prompt_contract_without_repeated_scene(hand_contract)
    )
    action_prompt = action_topology_prompt(
        prompt_contract_without_repeated_scene(action_contract)
    )
    if action_prompt:
        pose_text += "\n\n" + action_prompt
    pose_text += "\n\n" + spatial_topology_prompt(
        prompt_contract_without_repeated_scene(topology_contract)
    )
    background_text = clean_text(
        background
        or (
            "Soft minimal environment implied by the scene, with faded watercolor edges and "
            "lower detail than the characters."
        )
    )
    background_text += "\n\n" + visual_richness_prompt(
        prompt_contract_without_repeated_scene(richness_contract)
    )
    prompt = build_generation_master_prompt(
        slide_number=slide_number,
        slide_count=slide_count,
        slide_copy=clean_slide_copy(slide_copy),
        scene_description=scene,
        pose_description=pose_text,
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
        background_description=background_text,
        emotion_description=clean_text(
            emotion
            or "Quietly in love, comfortable, playful, emotionally safe, and specific to the slide beat."
        ),
        format_key=format_key,
        style_prompt=clean_text(style),
        negative_prompt=clean_text(negative),
    ).strip() + "\n"
    if "TARGETED EDIT INSTRUCTION" in scene:
        prompt = compact_targeted_edit_prompt(prompt)
    if len(prompt) > MAX_PROMPT_CHARS and len(scene) <= 5000:
        prompt = compact_dense_prompt(prompt)
    if len(prompt) > MAX_PROMPT_CHARS:
        raise ValueError(f"Compiled image prompt is too long: {len(prompt)} characters.")
    return prompt
