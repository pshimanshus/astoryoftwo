from __future__ import annotations

import hashlib
import re

import pytest

from pipeline.stages.carousel_master_prompt import (
    MASTER_PROMPT_VERSION,
    load_canonical_master_prompt,
    master_prompt_contract,
)
from pipeline.stages.carousel_contract import load_active_illustration_style_profile
from pipeline.stages.carousel_generation_inputs import effective_slide_prompt_fields
from pipeline.stages.carousel_prompt_compiler import (
    MAX_NEGATIVE_WORDS,
    MAX_PROMPT_CHARS,
    MAX_PROMPT_WORDS,
    MAX_SCENE_WORDS,
    compile_image_prompt,
    extract_scene_summary,
)
from pipeline.stages.codex_builtin_image_generation import generator_prompt_text


def _section(prompt: str, heading: str, next_heading: str) -> str:
    match = re.search(
        rf"{re.escape(heading)}\n(.*?)(?=\n\n{re.escape(next_heading)}\n)",
        prompt,
        flags=re.DOTALL,
    )
    assert match is not None
    return match.group(1).strip()


def _compile(**overrides: object) -> str:
    values: dict[str, object] = {
        "slide_number": 1,
        "slide_count": 6,
        "slide_copy": "I was never unsure of you.\nI was lost inside our life.",
        "visual": (
            "At the dining table, Aachu and Zuv pull one folded paper map in opposite "
            "directions while the same lamp stays between them. Their eyes move from the "
            "map to each other. Medium overhead angle; the hands and map are the focal point."
        ),
        "format_key": "instagram_post",
        "style": (
            "Cinematic observational watercolor-and-ink on neutral warm ivory/off-white paper; "
            "tactile grain, transparent blooms, natural asymmetry, and no yellow, mustard, sepia finish."
        ),
        "negative": "No photorealism, no 3D, no stock couple.",
        "relationship_state": "Both recognize the disagreement softening into shared attention.",
        "camera": {
            "shot_size": "medium overhead action frame",
            "position": "table-height three-quarter view beside their active hands",
            "negative_space": "quiet upper-left paper field above the lamp",
        },
        "focal_hierarchy": (
            "Their opposing hands read first, the folded map second, and upper-left copy stays clear."
        ),
        "setting": {
            "place": "their scratched apartment dining table beside the window",
            "time": "late rainy afternoon",
            "motivated_light": (
                "cool window light travels from frame-left across their hands and the folded map"
            ),
            "depth_layers": {
                "foreground": "blurred chair edge implies the viewer arrived mid-conversation",
                "midground": "their hands pull the map around the fixed lamp",
                "background": "rain-streaked glass holds the unresolved travel horizon",
            },
        },
        "visual_richness": {
            "point_of_view": "Their shared hesitation organizes the frame around the contested map.",
            "before_frame": "Each partner had quietly chosen a different route across the page.",
            "after_frame": "Their eyes meet before either hand finally releases the paper.",
            "continuation_pull": "Which route will become theirs once the pulling stops?",
            "story_evidence": [
                {
                    "carrier": "the creased paper map",
                    "observable_state": "two penciled routes diverge beneath their opposing grips",
                    "narrative_job": "proves that both futures are physically present",
                },
                {
                    "carrier": "the fixed table lamp",
                    "observable_state": "it stays centered while their bodies pull apart",
                    "narrative_job": "proves one shared home underneath the disagreement",
                },
            ],
            "posed_portrait_allowed": False,
            "decorative_clutter_allowed": False,
        },
    }
    values.update(overrides)
    return compile_image_prompt(**values)  # type: ignore[arg-type]


def _edit_operation(format_key: str = "instagram_post") -> dict[str, object]:
    return {
        "intent": "edit",
        "targets": {
            format_key: {
                "path": ".internal/references/edit-targets/target.png",
                "sha256": "sha256:" + "a" * 64,
                "width": 1080,
                "height": 1440,
            }
        },
    }


def test_legacy_generation_prompt_bytes_are_unchanged() -> None:
    # Captured before adding image_operation, from the frozen implementation
    # baseline. Equality to the new default alone would miss shared drift.
    assert hashlib.sha256(_compile().encode()).hexdigest() == (
        "fdbd7508b040d2b8b8f7cbcca242e2c7d856ae17dbf56099a8c25a0f33af6992"
    )


@pytest.mark.parametrize("format_key", ["instagram_post", "reels_stories", "square"])
def test_targetless_generation_is_byte_identical(format_key: str) -> None:
    prompt = _compile(format_key=format_key)
    assert _compile(format_key=format_key, image_operation=None) == prompt
    assert _compile(format_key=format_key, image_operation={"intent": "generate"}) == prompt
    assert _compile(
        format_key=format_key, image_operation={"intent": "generate", "targets": {}}
    ) == prompt


@pytest.mark.parametrize("format_key", ["instagram_post", "reels_stories", "square"])
def test_edit_uses_target_first_and_canonical_scene_copy_and_feedback(format_key: str) -> None:
    exact = "We saved /home/us/photo.jpg.  Exactly twice.\nReferences: [us]."
    profile = load_active_illustration_style_profile()
    prompt = _compile(
        format_key=format_key,
        slide_copy=exact,
        style=profile["generation_prompt"],
        negative=profile["negative_prompt"],
        image_operation=_edit_operation(format_key),
        feedback_constraints=[{
            "must_change": ["Move only the lamp to the far table edge."],
            "must_preserve": ["Keep the folded map between their hands."],
        }],
    )

    assert prompt.startswith("EDIT INPUTS:\nEdit image 1, the existing canvas.")
    assert "Images 2-5 are the four canonical Aachu/Zuv identity references" in prompt
    assert "image 6 is the canonical style board" in prompt
    assert "not identity or style authority" in prompt
    assert "PRIMARY REQUEST:\nEdit image 1 into one image-led" in prompt
    assert "Create one image-led" not in prompt
    assert _section(prompt, "ON-IMAGE TEXT:", "SCENE:") == exact
    assert prompt.count("ON-IMAGE TEXT:\n") == 1
    assert prompt.count("SCENE:\n") == 1
    assert prompt.count("Move only the lamp to the far table edge.") == 1
    assert prompt.count("Keep the folded map between their hands.") == 1
    assert "target.png" not in prompt
    assert "sha256:" not in prompt
    assert len(prompt) <= MAX_PROMPT_CHARS
    assert len(prompt.split()) <= MAX_PROMPT_WORDS


@pytest.mark.parametrize("operation", [
    [], {}, {"intent": "replace"}, {"intent": "generate", "targets": {"square": {"path": "x"}}},
    {"intent": "edit", "targets": []}, {"intent": "edit", "targets": {}},
    {"intent": "edit", "targets": {"instagram_post": {}}}, _edit_operation("square"),
])
def test_edit_operation_requires_a_target_for_the_selected_format(operation: object) -> None:
    with pytest.raises(ValueError, match="image_operation"):
        _compile(image_operation=operation)


def test_edit_stays_fail_closed_when_its_instructions_exceed_prompt_budget() -> None:
    # A generation prompt can fit while edit role instructions would overflow.
    words = MAX_PROMPT_WORDS - len(_compile(slide_copy="One.").split())
    exact = "One. " + "copy " * words
    baseline = _compile(slide_copy=exact)
    assert len(baseline.split()) == MAX_PROMPT_WORDS
    with pytest.raises(ValueError, match="too long"):
        _compile(slide_copy=exact, image_operation=_edit_operation())


def test_compile_image_prompt_is_compact_and_removes_pipeline_noise():
    prompt = _compile(
        visual=(
            "Zuv notices the wallet audit and points toward the backup pocket. "
            "Required final file: output/carousels/demo/final/slide-04.png. "
            "Source provenance: /Users/example/output/final-images.json. "
            "Identity dossier path: config/identity-dossier.json. "
            "References: [identity_images/aachu.png, output/storyboard.md]."
        ),
        style="premium watercolor using /Users/example/config/style.json",
    )

    for noise in (
        "/Users/",
        "output/carousels",
        "identity_images/",
        "Required final file",
        "Source provenance",
        "Identity dossier path",
        "final-images.json",
    ):
        assert noise not in prompt
    assert len(prompt) <= MAX_PROMPT_CHARS
    assert len(prompt.split()) <= MAX_PROMPT_WORDS


@pytest.mark.parametrize(
    ("format_key", "label", "size", "ratio", "excluded"),
    [
        ("instagram_post", "Instagram Post Output", "1080x1440", "3:4", "9:16 Story/Reel"),
        ("reels_stories", "Reels/Stories Output", "1080x1920", "9:16", "3:4 carousel"),
        ("square", "Square Output", "1080x1080", "1:1", "3:4 carousel"),
    ],
)
def test_compile_image_prompt_locks_one_native_format(
    format_key: str, label: str, size: str, ratio: str, excluded: str
):
    prompt = _compile(format_key=format_key)

    assert f"Canvas: {label}; exact {size} px; native {ratio}" in prompt
    assert excluded in prompt
    assert "Do not crop, pad, stretch, resize, or derive it from another format" in prompt
    assert "downsample" not in prompt.lower()
    assert "accepted source" not in prompt.lower()
    if format_key == "instagram_post":
        assert "exact 1080x1440 px; native 3:4" in prompt
        assert "1440x1920" not in prompt


def test_compile_image_prompt_preserves_exact_text_line_breaks_and_brandmark():
    exact = "Commitment answered who.\nWe are still learning how."
    prompt = _compile(slide_copy=exact)

    assert f"ON-IMAGE TEXT:\n{exact}" in prompt
    assert "including spelling, capitalization, punctuation, and line breaks" in prompt
    assert "Add no other words except" in prompt
    assert "`@a.storyof.two` at the top-right" in prompt
    assert "textless" not in prompt.casefold()


def test_exact_copy_is_never_sanitized_as_scene_or_reference_prose() -> None:
    exact = (
        "We saved /home/us/photo.jpg.  Exactly twice.\n"
        "References: [us]. The file was vows.png."
    )

    prompt = _compile(slide_copy=exact)

    assert f"ON-IMAGE TEXT:\n{exact}" in prompt
    assert "attached reference image" not in _section(
        prompt, "ON-IMAGE TEXT:", "SCENE:"
    )


def test_prompt_keeps_reference_identity_wardrobe_and_style_requirements():
    prompt = _compile()

    assert "attached actual Aachu and Zuv identity images" in prompt
    assert "If actual identity and style references are not attached, stop" in prompt
    assert "Preserve their whole-person likeness" in prompt
    assert "Wardrobe from attached identity references" in prompt
    assert "neutral warm ivory/off-white paper" in prompt
    assert "yellow, mustard, sepia" in prompt


def test_prompt_uses_attached_identity_contract_without_inlining_full_dossier():
    prompt = _compile()

    assert "Non-negotiable Identity:" not in prompt
    assert "attached actual Aachu and Zuv identity images" in prompt
    assert "Preserve their whole-person likeness" in prompt
    assert len(prompt) <= MAX_PROMPT_CHARS
    assert len(prompt.split()) <= MAX_PROMPT_WORDS


def test_relationship_state_is_not_duplicated_as_microexpression():
    relationship = "They remain connected while disagreeing."
    prompt = _compile(relationship_state=relationship, emotion=None)

    assert prompt.count(relationship) == 1
    assert "Microexpression and body language:" not in prompt

    distinct_emotion = "Aachu's jaw softens while Zuv keeps a patient gaze."
    with_emotion = _compile(
        relationship_state=relationship,
        emotion=distinct_emotion,
    )
    assert relationship in with_emotion
    assert f"Microexpression and body language: {distinct_emotion}" in with_emotion


def test_prompt_keeps_action_camera_focal_and_compact_entity_integrity():
    prompt = _compile()

    assert "pull one folded paper map in opposite directions" in prompt
    assert "Medium overhead angle" in prompt
    assert "the hands and map are the focal point" in prompt
    assert "No extra person, duplicate couple, unexplained reflection" in prompt
    assert "Every visible hand belongs to a visible body" in prompt
    assert "spatially separate and physically coherent" in prompt
    assert "LIMB AND HAND PLAN:" in prompt
    assert "owner -> arm -> wrist -> hand -> contacted object" in prompt
    assert "WHOLE-PERSON AND OBJECT TOPOLOGY:" in prompt
    assert "table=separate_from" in prompt


def test_slide_specific_limb_plan_is_serialized_without_validator_essay_noise():
    prompt = _compile()

    assert "LIMB AND HAND PLAN:" in prompt
    assert "WHOLE-PERSON AND OBJECT TOPOLOGY:" in prompt
    for removed in (
        "HAND OWNERSHIP MAP (HARD GATE)",
        "ACTION CHRONOLOGY AND DOOR-SIDE CONTRACT (HARD GATE)",
        "WHOLE-PERSON SPATIAL TOPOLOGY (HARD GATE)",
        "VISUAL RICHNESS CONTRACT (HARD GATE)",
        "director_event_fingerprint",
        "review_provenance",
        "expected_frame_bindings",
    ):
        assert removed not in prompt


def test_compile_image_prompt_still_blocks_contradictory_action_topology():
    with pytest.raises(ValueError, match="Action chronology/topology is unresolved"):
        _compile(
            slide_copy=(
                "He still checked the lock twice.\nShe still rolled her eyes.\n\n"
                "Then she went back\nand checked it with him."
            ),
            visual=(
                "Back home after the date, viewed entirely from inside the entryway. "
                "Aachu tugs the interior handle herself while Zuv watches and smiles."
            ),
        )


def test_verbose_inputs_are_deduplicated_and_compacted_to_field_budgets():
    repeated = "The clothes, hair, shoes, and corridor remain dry before departure. " * 80
    prompt = _compile(
        visual=(
            "Aachu turns back and joins Zuv at the closed exterior door so both test the "
            "same handle together. " + repeated
        ),
        camera={
            "shot_size": "medium overhead action frame",
            "position": "Keep the shared action readable from an overhead camera. " * 80,
            "negative_space": "quiet upper-left paper field above the lamp",
        },
        negative="No extra person or broken hand. " * 80,
    )

    scene = _section(prompt, "SCENE:", "CINEMATIC STORY FRAME:")
    negative = re.search(
        r"ESSENTIAL NEGATIVES:\n(.*?)(?=\n\nSLIDE DIRECTION)",
        prompt,
        flags=re.DOTALL,
    )
    assert negative is not None
    assert len(scene.split()) <= MAX_SCENE_WORDS
    assert len(negative.group(1).split()) <= MAX_NEGATIVE_WORDS
    assert scene.count("corridor remain dry before departure") == 1
    assert len(prompt) <= MAX_PROMPT_CHARS
    assert len(prompt.split()) <= MAX_PROMPT_WORDS


def test_locked_field_over_budget_blocks_instead_of_dropping_tail() -> None:
    wardrobe = " ".join(f"wardrobe-token-{index}" for index in range(55)) + " LOCKED_TAIL"

    with pytest.raises(ValueError, match="Locked wardrobe exceeds its 55-word"):
        _compile(wardrobe=wardrobe)


@pytest.mark.parametrize("format_key", ["instagram_post", "reels_stories", "square"])
def test_active_profile_leaves_budget_for_specific_slide_negatives(format_key: str) -> None:
    profile = load_active_illustration_style_profile()
    slide_negative = (
        "No spare keys, printed route labels, additional cups, open doors, anonymous hands, "
        "floating objects, mirrored furniture, invented jewelry, replaced clothing, duplicated "
        "maps, reversed gaze, or a second simultaneous action."
    )
    effective = effective_slide_prompt_fields(
        {"negative_prompt": slide_negative},
        shared_negative=profile["negative_prompt"],
    )

    prompt = _compile(
        format_key=format_key,
        style=profile["generation_prompt"],
        negative=effective["negative_prompt"],
    )

    assert profile["generation_prompt"] in prompt
    assert profile["negative_prompt"] in prompt
    assert slide_negative in prompt
    assert len(effective["negative_prompt"].split()) <= MAX_NEGATIVE_WORDS
    assert len(prompt) <= MAX_PROMPT_CHARS
    assert len(prompt.split()) <= MAX_PROMPT_WORDS


def test_canonical_generation_body_has_no_workflow_state_or_duplicate_prompt_sections():
    canonical = load_canonical_master_prompt()

    assert MASTER_PROMPT_VERSION.endswith("v7-cinematic-style-profile")
    assert canonical.count("ON-IMAGE TEXT:") == 1
    assert canonical.count("SCENE:") == 1
    assert canonical.count("CINEMATIC STORY FRAME:") == 1
    assert canonical.count("[INSERT CANONICAL HOUSE STYLE HERE]") == 1
    for noise in (
        "hash",
        "provenance",
        "manifest",
        "approval ledger",
        "lifecycle",
        "prompt-pack.json",
        "visual-qa.json",
    ):
        assert noise not in canonical.casefold()


def test_extract_scene_summary_but_legacy_prompt_cannot_generate_without_cinematic_data():
    legacy_prompt = (
        "Style reference images: [config/carousel_style_contract.json]. "
        "Scene: Aachu opens Zuv's wallet while he holds out the backup card. "
        "Mood: warm and playful. Composition: "
        + ("legacy package checklist and provenance noise " * 120)
    )

    assert extract_scene_summary(legacy_prompt) == (
        "Aachu opens Zuv's wallet while he holds out the backup card."
    )
    with pytest.raises(ValueError, match="active style and negative prompts"):
        generator_prompt_text(
            {"slide": 2, "text": "He prepared for it.", "prompt": legacy_prompt},
            "instagram_post",
        )


def test_master_prompt_contract_keeps_only_requested_native_outputs():
    contract = master_prompt_contract()

    assert contract["version"] == MASTER_PROMPT_VERSION
    assert contract["native_outputs"]["instagram_post"]["size"] == "1080x1440"
    assert contract["native_outputs"]["instagram_post"]["source_size"] == "1080x1440"
    assert contract["native_outputs"]["reels_stories"]["size"] == "1080x1920"
    assert contract["native_outputs"]["square"]["size"] == "1080x1080"
    assert "hashes, provenance, and QA schemas outside" in contract["rule"]


def test_compile_image_prompt_rejects_when_exact_copy_alone_breaks_budget():
    exact_copy = "exact-copy-word " * (MAX_PROMPT_WORDS + 100)

    with pytest.raises(ValueError, match="too long"):
        _compile(slide_copy=exact_copy)


def test_explicit_hand_contact_plan_reaches_generation_prompt() -> None:
    hand_map = {
        "people": ["Aachu", "Zuv"],
        "expected_anatomical_hands": 4,
        "expected_visible_hands": 4,
        "hands": [
            {
                "owner": "Aachu",
                "side": "right",
                "visibility": "visible",
                "action": "points beside the left bookcase panel",
                "attachment": "continuous arm-to-wrist-to-hand",
                "contact": "index finger stops outside the wood",
            },
            {
                "owner": "Aachu",
                "side": "left",
                "visibility": "visible",
                "action": "rests on her own hip",
                "attachment": "continuous arm-to-wrist-to-hand",
                "contact": "palm touches only her denim waistband",
            },
            {
                "owner": "Zuv",
                "side": "right",
                "visibility": "visible",
                "action": "points at the shelf alignment hole",
                "attachment": "continuous arm-to-wrist-to-hand",
                "contact": "index finger stops above the shelf",
            },
            {
                "owner": "Zuv",
                "side": "left",
                "visibility": "visible",
                "action": "supports the shelf's right end",
                "attachment": "continuous arm-to-wrist-to-hand",
                "contact": "palm supports the underside; fingers curl around the exterior edge",
            },
        ],
    }

    prompt = _compile(hand_map=hand_map)

    assert "Aachu left: visible; rests on her own hip" in prompt
    assert "palm touches only her denim waistband" in prompt
    assert "Zuv left: visible; supports the shelf's right end" in prompt


def test_incomplete_hand_contact_plan_blocks_generation() -> None:
    with pytest.raises(ValueError, match="Hand ownership/contact plan is unresolved"):
        _compile(
            hand_map={
                "people": ["Aachu"],
                "expected_visible_hands": 1,
                "hands": [
                    {
                        "owner": "Aachu",
                        "side": "right",
                        "visibility": "visible",
                        "action": "touches the shelf",
                        "attachment": "hand",
                    }
                ],
            }
        )


def test_cinematic_direction_and_style_are_compiled_exactly_once() -> None:
    prompt = _compile()
    style = (
        "Cinematic observational watercolor-and-ink on neutral warm ivory/off-white paper; "
        "tactile grain, transparent blooms, natural asymmetry, and no yellow, mustard, sepia finish."
    )

    assert prompt.count(style) == 1
    assert prompt.count("CINEMATIC STORY FRAME:") == 1
    assert prompt.count("Point of view:") == 1
    assert prompt.count("the creased paper map") == 1
    assert "Additional style note" not in prompt


def test_missing_cinematic_direction_blocks_before_prompt_compilation() -> None:
    with pytest.raises(ValueError, match="Cinematic story direction is unresolved"):
        _compile(camera=None, setting=None, visual_richness=None)
