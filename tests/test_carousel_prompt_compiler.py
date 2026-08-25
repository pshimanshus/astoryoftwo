from __future__ import annotations

import re

import pytest

from pipeline.stages.carousel_master_prompt import (
    MASTER_PROMPT_VERSION,
    load_canonical_master_prompt,
    master_prompt_contract,
)
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
        "style": "premium romantic watercolor-and-ink illustration",
        "negative": "No photorealism, no 3D, no stock couple.",
    }
    values.update(overrides)
    return compile_image_prompt(**values)  # type: ignore[arg-type]


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


def test_prompt_keeps_action_camera_focal_and_compact_entity_integrity():
    prompt = _compile()

    assert "pull one folded paper map in opposite directions" in prompt
    assert "Medium overhead angle" in prompt
    assert "the hands and map are the focal point" in prompt
    assert "No extra person, duplicate couple, unexplained reflection" in prompt
    assert "Every visible hand belongs to a visible body" in prompt
    assert "spatially separate and physically coherent" in prompt


def test_validator_essays_are_not_serialized_into_generation_prompt():
    prompt = _compile()

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
        pose="Keep the shared action readable from an overhead camera. " * 80,
        negative="No extra person or broken hand. " * 80,
    )

    scene = _section(prompt, "SCENE:", "IDENTITY AND WARDROBE:")
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


def test_canonical_generation_body_has_no_workflow_state_or_duplicate_prompt_sections():
    canonical = load_canonical_master_prompt()

    assert MASTER_PROMPT_VERSION.endswith("v5-compact")
    assert canonical.count("ON-IMAGE TEXT:") == 1
    assert canonical.count("SCENE:") == 1
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


def test_extract_scene_summary_and_legacy_generator_drop_old_checklist_noise():
    legacy_prompt = (
        "Style reference images: [config/carousel_style_contract.json]. "
        "Scene: Aachu opens Zuv's wallet while he holds out the backup card. "
        "Mood: warm and playful. Composition: "
        + ("legacy package checklist and provenance noise " * 120)
    )

    assert extract_scene_summary(legacy_prompt) == (
        "Aachu opens Zuv's wallet while he holds out the backup card."
    )
    prompt = generator_prompt_text(
        {"slide": 2, "text": "He prepared for it.", "prompt": legacy_prompt},
        "instagram_post",
    )
    assert "Aachu opens Zuv's wallet" in prompt
    assert "legacy package checklist" not in prompt
    assert len(prompt) <= MAX_PROMPT_CHARS


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
