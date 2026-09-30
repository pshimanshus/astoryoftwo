from __future__ import annotations

import re
from typing import Any


from pipeline.stages.carousel_master_prompt import build_generation_master_prompt
from pipeline.stages.carousel_sequence import slide_sequence_issues
from pipeline.stages.carousel_visual_storytelling import validate_cinematic_slide_direction
from pipeline.stages.carousel_visual_integrity import (
    build_action_topology_contract,
    build_hand_ownership_map,
    build_spatial_topology_contract,
    compact_hand_ownership_prompt,
    compact_spatial_topology_prompt,
    validate_hand_ownership_contract,
    validate_spatial_topology_contract,
    visual_richness_prompt,
    scene_contract_prompt,
    validate_pre_generation_scene_contract,
)


# Image prompts are creative handoffs, not serialized workflow state. These caps
# keep the physical scene and exact copy salient instead of burying them under
# validator prose.
MAX_PROMPT_CHARS = 8000
# A fully explicit four-hand plus person/object topology plan needs slightly
# more room than the previous validator-only prompt. Keep the cap tight enough
# to preserve scene salience while never truncating anatomy/contact locks.
MAX_PROMPT_WORDS = 1050
MAX_SCENE_WORDS = 180
MAX_NEGATIVE_WORDS = 80
MAX_SCENE_CONTRACT_WORDS = 300

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


def _prompt_phrase(value: Any) -> str:
    return str(value or "").strip().rstrip(". ;")


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
    copy_mode: str,
    scene: str,
    format_key: str,
    style: str,
    negative: str,
    cinematic_direction: str,
    wardrobe: str,
    props: str,
    hand_plan: str,
    spatial_plan: str,
    must_change: list[str],
    must_preserve: list[str],
) -> str:
    return build_generation_master_prompt(
        slide_number=slide_number,
        slide_count=slide_count,
        slide_copy=slide_copy,
        copy_mode=copy_mode,
        scene_description=scene,
        cinematic_description=cinematic_direction,
        hand_description=hand_plan,
        spatial_description=spatial_plan,
        wardrobe_description=wardrobe,
        prop_description=props,
        format_key=format_key,
        style_prompt=style,
        negative_prompt=negative,
        must_change=must_change,
        must_preserve=must_preserve,
    )


def _feedback_prompt_constraints(
    feedback_constraints: list[dict[str, Any]] | None,
) -> tuple[list[str], list[str]]:
    """Project active feedback into concise creator-owned prompt constraints."""

    def generation_phrase(text: str) -> str:
        lowered = text.casefold()
        if lowered.startswith("qa must "):
            return ""
        if "hook and story premise" in lowered:
            return ""
        if "slide 4 proof beat" in lowered or "slide 4 exact copy" in lowered:
            return ""
        if "parcel must sit on the floor" in lowered:
            return "Parcel on flat floor mat; no step-down."
        if "parcel remains on the floor mat" in lowered:
            return "Parcel on flat floor mat; no step-down."
        if "remove aachu's bag" in lowered:
            return "No bag on Aachu."
        if "avoid same clothes" in lowered:
            return "Casual Saturday noon clothes."
        if "evil-eye locket" in lowered:
            return "Zuv evil-eye locket visible."
        if "normal-height adults" in lowered:
            return "Normal-height adults; no compressed/chibi bodies."
        if "avoid deep crouch" in lowered:
            return "No deep crouch; Aachu mostly upright, slight bend/point."
        if "doorframe" in lowered and "adult scale" in lowered:
            return "Use doorframe, hallway, and body proportions for adult scale."
        if "aachu has no bag" in lowered and "locket" in lowered:
            return "No bag; casual noon clothes; Zuv locket visible."
        return text

    projected: dict[str, list[str]] = {"must_change": [], "must_preserve": []}
    seen: dict[str, set[str]] = {"must_change": set(), "must_preserve": set()}
    for record in feedback_constraints or []:
        if not isinstance(record, dict):
            raise ValueError("feedback constraints must contain JSON objects")
        for key in projected:
            values = record.get(key) or []
            if not isinstance(values, list):
                raise ValueError(f"feedback constraint {key} must be a list")
            for value in values:
                phrase = generation_phrase(str(value))
                if not phrase:
                    continue
                text = _compact_words(
                    phrase,
                    80,
                    field_name=f"feedback {key}",
                )
                identity = text.casefold()
                if text and identity not in seen[key]:
                    projected[key].append(text)
                    seen[key].add(identity)
    return projected["must_change"], projected["must_preserve"]


def _apply_image_operation(
    prompt: str, image_operation: dict[str, Any] | None, *, format_key: str
) -> str:
    """Describe edit roles without making target pixels a second story authority.

    Target paths, hashes, and dimensions are validated by the generation-input
    boundary. They stay out of the creative prompt, as do any alternate scene
    or copy instructions: canonical slide fields and feedback own those.
    """
    if image_operation is None:
        return prompt
    if not isinstance(image_operation, dict):
        raise ValueError("image_operation must be a JSON object")
    intent = image_operation.get("intent")
    targets = image_operation.get("targets", {})
    if not isinstance(targets, dict):
        raise ValueError("image_operation targets must be a JSON object")
    if intent == "generate" and not targets:
        return prompt
    if intent != "edit":
        raise ValueError("image_operation must be edit or targetless generate")
    if not isinstance(targets.get(format_key), dict) or not targets[format_key]:
        raise ValueError(f"image_operation edit requires a target for {format_key}")
    edit_inputs = (
        "EDIT INPUTS:\n"
        "Edit image 1, the existing canvas. Images 2-5 are the four canonical "
        "Aachu/Zuv identity references; image 6 is the canonical style board. Image 1 supplies "
        "the editable pixels, not identity or style authority. Apply the locked "
        "scene, exact copy, and any ACTIVE CREATOR FEEDBACK below. Preserve all "
        "unaffected content; change only what those canonical directions require.\n\n"
    )
    # Keep the historical generation body byte-stable. Only edit requests use
    # this variation of the primary verb; no second scene/copy payload is added.
    return edit_inputs + prompt.replace(
        "PRIMARY REQUEST:\nCreate one image-led ",
        "PRIMARY REQUEST:\nEdit image 1 into one image-led ",
        1,
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
    camera: dict[str, Any] | None = None,
    focal_hierarchy: str | None = None,
    setting: dict[str, Any] | None = None,
    relationship_state: str | None = None,
    continuity_lock: str | None = None,
    # Legacy read-only aliases. New package writers never emit them.
    pose: str | None = None,
    wardrobe: str | None = None,
    props: str | None = None,
    background: str | None = None,
    emotion: str | None = None,
    hand_map: dict[str, Any] | None = None,
    action_topology: dict[str, Any] | None = None,
    spatial_topology: dict[str, Any] | None = None,
    visual_richness: dict[str, Any] | None = None,
    feedback_constraints: list[dict[str, Any]] | None = None,
    copy_mode: str = "text",
    beat_delta: str | None = None,
    copy_image_relation: dict[str, Any] | None = None,
    image_operation: dict[str, Any] | None = None,
    scene_contract: dict[str, Any] | None = None,
) -> str:
    """Compile one compact, generation-facing prompt.

    Limb ownership, contact geometry, and whole-person/object topology are
    generation inputs as well as validator inputs. A generic anatomy negative
    cannot substitute for a slide-specific map.
    """

    sequence_fields = {"copy": slide_copy, "copy_mode": copy_mode}
    if beat_delta is not None:
        sequence_fields["beat_delta"] = beat_delta
    if copy_image_relation is not None:
        sequence_fields["copy_image_relation"] = copy_image_relation
    sequence_issues = slide_sequence_issues(sequence_fields)
    if sequence_issues:
        raise ValueError("Slide copy/sequence is unresolved: " + "; ".join(sequence_issues))
    copy = clean_slide_copy(slide_copy)
    full_scene = clean_text(visual)
    contract_text = ""
    if scene_contract is not None:
        contract_issues = validate_pre_generation_scene_contract(scene_contract)
        if isinstance(scene_contract, dict) and clean_text(
            str(scene_contract.get("scene_action_binding") or "")
        ) != full_scene:
            contract_issues.append(
                "pre-generation scene contract scene_action_binding does not match the compiled scene"
            )
        if isinstance(scene_contract, dict) and " ".join(
            str(scene_contract.get("copy_action_binding") or "").split()
        ) != " ".join(copy.split()):
            contract_issues.append(
                "pre-generation scene contract copy_action_binding does not match the compiled copy"
            )
        for name, supplied in (("hand_map", hand_map), ("spatial_topology", spatial_topology)):
            if isinstance(scene_contract, dict) and supplied is not None and supplied != scene_contract.get(name):
                contract_issues.append(
                    f"pre-generation scene contract {name} does not match the compiled slide plan"
                )
        if contract_issues:
            raise ValueError(
                "Pre-generation scene contract is unresolved: "
                + "; ".join(str(item) for item in contract_issues)
            )
        contract_text = _compact_words(
            scene_contract_prompt(
                scene_contract,
                include_hand_map=False,
                include_spatial_topology=False,
                include_visual_richness=False,
            ),
            MAX_SCENE_CONTRACT_WORDS,
            field_name="scene contract",
        )

    normalized_camera = dict(camera or {})
    if pose and not normalized_camera.get("position"):
        normalized_camera["position"] = pose
    normalized_setting = dict(setting or {})
    if background and not normalized_setting.get("place"):
        normalized_setting["place"] = background
    cinematic_record = {
        "physical_action": full_scene,
        "relationship_state": relationship_state or emotion or "",
        "camera": normalized_camera,
        "focal_hierarchy": focal_hierarchy or "",
        "setting": normalized_setting,
        "visual_richness": visual_richness,
    }
    cinematic_issues = validate_cinematic_slide_direction(
        cinematic_record,
        slide_number=slide_number,
        is_final=slide_number == slide_count,
    )
    if cinematic_issues:
        raise ValueError("Cinematic story direction is unresolved: " + "; ".join(cinematic_issues))
    action_contract = action_topology or build_action_topology_contract(full_scene, copy)
    action_issues = action_contract.get("issues") if isinstance(action_contract, dict) else []
    if action_issues:
        raise ValueError(
            "Action chronology/topology is unresolved: "
            + "; ".join(str(item) for item in action_issues)
        )

    hand_contract = (
        scene_contract.get("hand_map") if scene_contract is not None
        else hand_map or build_hand_ownership_map(full_scene)
    )
    hand_issues = validate_hand_ownership_contract(hand_contract)
    if hand_issues:
        raise ValueError("Hand ownership/contact plan is unresolved: " + "; ".join(hand_issues))
    spatial_contract = (
        scene_contract.get("spatial_topology") if scene_contract is not None
        else spatial_topology or build_spatial_topology_contract(full_scene)
    )
    spatial_issues = validate_spatial_topology_contract(spatial_contract)
    if spatial_issues:
        raise ValueError("Whole-person/object topology is unresolved: " + "; ".join(spatial_issues))
    must_change, must_preserve = _feedback_prompt_constraints(feedback_constraints)

    relationship_phrase = _prompt_phrase(relationship_state or emotion)
    emotion_phrase = _prompt_phrase(emotion)
    cinematic_lines = [
        "Camera: {shot_size}; {position}; copy space: {negative_space}.".format(
            shot_size=normalized_camera.get("shot_size", ""),
            position=normalized_camera.get("position", ""),
            negative_space=normalized_camera.get("negative_space", ""),
        ),
        "Setting: {place}; time/weather: {time}; motivated light: {light}.".format(
            place=normalized_setting.get("place", ""),
            time=normalized_setting.get("time", ""),
            light=normalized_setting.get("motivated_light", ""),
        ),
        "Depth: foreground={foreground}; midground={midground}; background={background}.".format(
            **dict(normalized_setting.get("depth_layers") or {})
        ),
        f"Focal hierarchy: {_prompt_phrase(focal_hierarchy)}.",
        f"Relationship state: {relationship_phrase}.",
    ]
    # Do not repeat relationship_state verbatim as an expression direction.
    # Keep a distinct creator-authored emotion when one is actually supplied.
    if emotion_phrase and emotion_phrase.casefold() != relationship_phrase.casefold():
        cinematic_lines.append(f"Microexpression and body language: {emotion_phrase}.")
    cinematic_lines.extend(
        (
            "Continuity: "
            + _prompt_phrase(
                continuity_lock or "No invented continuity beyond this frame."
            )
            + ".",
            visual_richness_prompt(visual_richness or {}),
        )
    )
    # Only this beat's actionable consequence belongs in the image prompt.
    # Story-plan explanations and research annotations stay in the package.
    if beat_delta is not None:
        cinematic_lines.append("This beat adds: " + _compact_words(
            beat_delta, 40, field_name="beat delta"
        ))
    if copy_image_relation is not None:
        cinematic_lines.append(
            f"Image/copy {copy_image_relation['kind']}: " + _compact_words(
                copy_image_relation["proof"], 50, field_name="copy-image physical proof"
            )
        )

    fields = {
        "scene": _compact_words(full_scene, MAX_SCENE_WORDS, field_name="scene"),
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
        "style": _compact_words(style, 110, field_name="style"),
        "negative": _compact_words(
            negative,
            MAX_NEGATIVE_WORDS,
            field_name="essential negatives",
        ),
        "hand_plan": compact_hand_ownership_prompt(hand_contract),
        "spatial_plan": compact_spatial_topology_prompt(spatial_contract),
        "cinematic_direction": _compact_words(
            "\n".join(cinematic_lines),
            260,
            field_name="cinematic direction",
        ),
        "must_change": must_change,
        "must_preserve": must_preserve,
    }

    if contract_text:
        fields["scene"] = f"{fields['scene']}\n\n{contract_text}"
    prompt = _build_prompt(
        slide_number=slide_number,
        slide_count=slide_count,
        slide_copy=copy,
        copy_mode=copy_mode,
        format_key=format_key,
        **fields,
    )
    prompt = _apply_image_operation(prompt, image_operation, format_key=format_key)

    if len(prompt) > MAX_PROMPT_CHARS or _word_count(prompt) > MAX_PROMPT_WORDS:
        raise ValueError(
            "Compiled image prompt is too long: "
            f"{len(prompt)} characters / {_word_count(prompt)} words."
        )
    return prompt
