from __future__ import annotations

from pathlib import Path

import pytest

from pipeline.stages.carousel_master_prompt import master_prompt_contract
from pipeline.stages.carousel_prompt_compiler import MAX_PROMPT_CHARS, compile_image_prompt, extract_scene_summary
from pipeline.stages.codex_builtin_image_generation import generator_prompt_text


def test_compile_image_prompt_removes_file_paths_and_contract_noise():
    prompt = compile_image_prompt(
        slide_number=4,
        slide_count=6,
        slide_copy="He saw. He pretended to sleep.",
        visual=(
            "Zuv notices the wallet audit, smiles, and points toward the backup pocket. "
            "Required final file: output/carousels/2026-05-24/wallet/final/slide-04.png. "
            "Source provenance: /Users/himanshusharma/astoryoftwo-analysis/output/carousels/final-images.json. "
            "Identity dossier path: config/identity-dossier.json. "
            "References: [identity_images/aachu.png, output/carousels/storyboard.md]."
        ),
        format_key="instagram_post",
        style=(
            "premium romantic watercolor-and-ink illustration using "
            "/Users/himanshusharma/astoryoftwo-analysis/config/carousel_style_contract.json"
        ),
        negative="No photorealism, no 3D, no stock couple.",
    )

    assert "final-images.json" not in prompt
    assert "identity-dossier.json" not in prompt
    assert "/Users/" not in prompt
    assert "output/carousels" not in prompt
    assert "identity_images/" not in prompt
    assert "Required final file" not in prompt
    assert "Source provenance" not in prompt
    assert "Identity dossier path" not in prompt
    assert "png." not in prompt
    assert "json." not in prompt
    assert "md." not in prompt
    assert "He saw. He pretended to sleep." in prompt
    assert "MASTER PROMPT VERSION" in prompt
    assert "CHARACTER IDENTITY LOCK" in prompt
    assert "TEXT RULE" in prompt
    assert "3:4" in prompt
    assert len(prompt) <= MAX_PROMPT_CHARS


def test_compile_image_prompt_uses_native_format_lock():
    post = compile_image_prompt(
        slide_number=1,
        slide_count=5,
        slide_copy="Some wives don't ask. They audit wallets.",
        visual="Aachu mock-officially opens the wallet while Zuv watches amused.",
        format_key="instagram_post",
        style="premium romantic watercolor-and-ink illustration",
        negative="No photorealism.",
    )
    story = compile_image_prompt(
        slide_number=1,
        slide_count=5,
        slide_copy="Some wives don't ask. They audit wallets.",
        visual="Aachu mock-officially opens the wallet while Zuv watches amused.",
        format_key="reels_stories",
        style="premium romantic watercolor-and-ink illustration",
        negative="No photorealism.",
    )

    assert "exact 3:4 canvas" in post
    assert "not a 9:16 story canvas" in post
    assert "exact 9:16 canvas" in story
    assert "not a 3:4 carousel canvas" in story
    assert "do not resize from another format" in post.lower()
    assert "do not resize from another format" in story.lower()


def test_compile_image_prompt_uses_creator_text_rule_without_no_text_conflict():
    prompt = compile_image_prompt(
        slide_number=3,
        slide_count=5,
        slide_copy="Cup ready tha.",
        visual="Aachu stands near the kitchen doorway while Zuv notices the cup already waiting.",
        format_key="instagram_post",
        style="premium romantic watercolor-and-ink illustration",
        negative="No photorealism.",
    )

    assert "romantic narrative slide" in prompt
    assert "with exact readable text baked naturally into the image" in prompt
    assert "ON-IMAGE TEXT:\nCup ready tha." in prompt
    assert "Include the exact written text provided in the ON-IMAGE TEXT section" in prompt
    assert "Preserve spelling, line breaks, punctuation, and wording exactly" in prompt
    assert "Do not add extra words" in prompt
    assert "BRAND INTEGRATION VISIBILITY RULE" in prompt
    assert "no text baked into image" not in prompt.lower()


def test_compile_image_prompt_always_includes_hand_ownership_and_visual_richness_contracts():
    prompt = compile_image_prompt(
        slide_number=8,
        slide_count=10,
        slide_copy='Kyunki gussa apni jagah.\n“Tum theek ho?” apni jagah.',
        visual="Aachu offers Zuv a tissue at the apartment doorway.",
        format_key="instagram_post",
        style="premium romantic watercolor-and-ink illustration",
        negative="No photorealism.",
    )

    assert "HAND OWNERSHIP MAP (HARD GATE):" in prompt
    assert "Aachu left hand" in prompt
    assert "Aachu right hand" in prompt
    assert "Zuv left hand" in prompt
    assert "Zuv right hand" in prompt
    assert "anonymous hand entering from the door" in prompt
    assert "WHOLE-PERSON SPATIAL TOPOLOGY (HARD GATE):" in prompt
    assert "person absorbed by or morphed into a door" in prompt
    assert "solid-object boundary crossing the head, neck, shoulder, back, torso, or visible limb" in prompt
    assert "Aachu: visible regions=head, neck, shoulders, torso" in prompt
    assert "Zuv: visible regions=head, neck, shoulders, torso" in prompt
    assert "VISUAL RICHNESS CONTRACT (HARD GATE):" in prompt
    assert "foreground, midground, and background" in prompt
    assert "2-4 story-relevant environmental details" in prompt
    assert "sparse two-person pose beside text" in prompt


def test_compile_image_prompt_blocks_wrong_side_or_solo_lock_callback():
    with pytest.raises(ValueError, match="Action chronology/topology is unresolved"):
        compile_image_prompt(
            slide_number=7,
            slide_count=7,
            slide_copy=(
                "He still checked the lock twice.\n"
                "She still rolled her eyes.\n\n"
                "Then she went back\n"
                "and checked it with him."
            ),
            visual=(
                "Back home after the date, viewed entirely from inside the entryway. "
                "Aachu tugs the interior handle herself while Zuv watches and smiles."
            ),
            format_key="instagram_post",
            style="premium romantic watercolor-and-ink illustration",
            negative="No photorealism.",
        )


def test_compile_image_prompt_embeds_explicit_lock_action_chronology():
    prompt = compile_image_prompt(
        slide_number=7,
        slide_count=7,
        slide_copy=(
            "He still checked the lock twice.\n"
            "She still rolled her eyes.\n\n"
            "Then she went back\n"
            "and checked it with him."
        ),
        visual=(
            "Callback to the moment they left for the date, viewed entirely from outside "
            "the apartment in the corridor after the fully closed door has closed. "
            "Zuv tests the exterior handle. Aachu had taken two steps toward the lift, "
            "turns back, joins him, and tests the same closed handle so both participate."
        ),
        format_key="instagram_post",
        style="premium romantic watercolor-and-ink illustration",
        negative="No photorealism.",
    )

    assert "ACTION CHRONOLOGY AND DOOR-SIDE CONTRACT (HARD GATE):" in prompt
    assert "Camera side: outside." in prompt
    assert "Temporal phase: before_departure." in prompt
    assert "Door state: fully_closed." in prompt
    assert "Return path visibly staged: True." in prompt
    assert "Shared checking action visibly staged: True." in prompt
    assert "one partner checks alone while the other merely watches" in prompt


def test_compile_image_prompt_deduplicates_long_locked_scene_across_safety_contracts():
    scene = (
        "Callback to the moment they left for the date, viewed entirely from outside "
        "the apartment in the dry corridor after the fully closed door has closed. "
        "Zuv's right hand pulls the exterior handle while his left hand holds the car key. "
        "Aachu had taken two steps toward the lift, visibly turns back, and presses her right "
        "palm beside the latch so both participate. Her tote remains on her left shoulder and "
        "a tightly rolled bone-dry umbrella stays under her left arm. "
        + ("The clothes, hair, shoes, and corridor remain unmistakably dry before departure. " * 45)
    )
    slide_copy = (
        "He still checked the lock twice.\n"
        "She still rolled her eyes.\n\n"
        "Then she went back\n"
        "and checked it with him."
    )

    prompt = compile_image_prompt(
        slide_number=7,
        slide_count=7,
        slide_copy=slide_copy,
        visual=scene,
        format_key="instagram_post",
        style="premium romantic watercolor-and-ink illustration",
        negative="No photorealism.",
    )

    normalized_scene = " ".join(scene.split())
    assert prompt.count(normalized_scene) == 1
    assert prompt.count("Scene action binding: Use the locked Scene description above.") == 4
    assert "HAND OWNERSHIP MAP (HARD GATE):" in prompt
    assert "ACTION CHRONOLOGY AND DOOR-SIDE CONTRACT (HARD GATE):" in prompt
    assert "WHOLE-PERSON SPATIAL TOPOLOGY (HARD GATE):" in prompt
    assert "VISUAL RICHNESS CONTRACT (HARD GATE):" in prompt
    assert len(prompt) <= MAX_PROMPT_CHARS


def test_dense_prompt_compaction_preserves_required_house_style_lock():
    prompt = compile_image_prompt(
        slide_number=7,
        slide_count=7,
        slide_copy="Still us.",
        visual="Aachu and Zuv verify one fully closed apartment door from the exterior corridor.",
        format_key="instagram_post",
        style="premium romantic watercolor-and-ink illustration",
        negative="No photorealism.",
        pose="Keep the exterior closed-door hand ownership and body separation explicit. " * 90,
    )

    assert len(prompt) <= MAX_PROMPT_CHARS
    assert "Observational Intimacy Premium" in prompt
    assert "STYLE ACCEPTANCE RULE:" in prompt
    assert "ASSET TYPE:" not in prompt


def test_targeted_edit_prompt_keeps_hard_gates_without_broad_prompt_noise():
    prompt = compile_image_prompt(
        slide_number=7,
        slide_count=7,
        slide_copy="Still us.",
        visual=(
            "TARGETED EDIT INSTRUCTION: Preserve the left vignette. Rebuild the right "
            "door with one lever beside the true latch edge and a visible jamb. "
            "LOCKED SCENE TO PRESERVE: Aachu and Zuv verify one fully closed apartment "
            "door from the exterior corridor."
        ),
        format_key="instagram_post",
        style="premium romantic watercolor-and-ink illustration",
        negative="No photorealism.",
    )

    assert "TARGETED EDIT INSTRUCTION" in prompt
    assert "ON-IMAGE TEXT:" in prompt
    assert "HAND OWNERSHIP MAP (HARD GATE):" in prompt
    assert "WHOLE-PERSON SPATIAL TOPOLOGY (HARD GATE):" in prompt
    assert "STYLE ACCEPTANCE RULE:" in prompt
    assert "STAGE-SCENE / VISUAL RECEIPT:" in prompt
    assert "SHOT LADDER / VISUAL VARIETY:" in prompt
    assert "RELATIONSHIP MOTION:" in prompt
    assert "RECURRING PROPS AND MOTIFS:" not in prompt
    assert "BACKGROUND STYLE:" not in prompt


def test_compile_image_prompt_preserves_canonical_master_prompt_fragments():
    canonical = Path("config/references/a-story-illustration-master-prompt.md").read_text(encoding="utf-8")
    required_fragments = [
        "prompt assembly is autopilot by default",
        "treat those photos as current-request identity references",
        "If actual identity reference images and style reference images cannot be used by the image-generation call",
        "The final image-generation call must attach selected actual identity images",
        "Wardrobe must be selected from the attached identity images",
        "PAPER TONE LOCK:",
        "STAGE-SCENE / VISUAL RECEIPT:",
        "SHOT LADDER / VISUAL VARIETY:",
        "RELATIONSHIP MOTION:",
        "Aachu is 5'6\"",
        "Zuv is 5'8\"",
        "This means neutral premium ivory/off-white paper, not yellow, not mustard",
        "If the paper/background reads yellow, mustard, sepia, beige/tan, parchment, coffee-stained, or heavy cream",
        "BRANDMARK RULE:",
        "BRAND LABEL WORKFLOW:",
        "Run Format Inference Preflight first",
        "Do not silently snap back to `3:4`, `9:16`, feed, Story",
    ]
    prompt = compile_image_prompt(
        slide_number=1,
        slide_count=5,
        slide_copy="dumber",
        visual="Aachu at a kitchen doorway, Zuv smiling from inside.",
        format_key="instagram_post",
        style="premium romantic watercolor-and-ink illustration",
        negative="No photorealism.",
    )

    for fragment in required_fragments:
        assert fragment in canonical
        assert fragment in prompt


def test_handoff_markdown_points_to_prompt_txt_without_second_prompt_body():
    from pipeline.stages.codex_builtin_image_generation import build_handoff_markdown

    markdown = build_handoff_markdown(
        slide_number=1,
        output_label="Instagram Post Output",
        prompt_filename="slide-01.prompt.txt",
        reference_paths=["identity_images/aachu-zuv-reference.jpg"],
        exact_slide_copy="dumber",
        expected_file="final/slide-01.png",
        generated_source="final/model-native-source/instagram-post-slide-01.png",
    )

    assert "Paste the full prompt from `slide-01.prompt.txt`" in markdown
    assert "This markdown file intentionally does not duplicate the prompt body" in markdown
    assert "\n## Prompt Source\n" in markdown
    assert "\n## Prompt\n" not in markdown
    assert "ON-IMAGE TEXT:\ndumber" not in markdown


def test_extract_scene_summary_prefers_scene_block_from_legacy_prompt():
    legacy_prompt = (
        "References: [output/carousels/demo/final-images.json]. "
        "Scene: Aachu opens the wallet while Zuv quietly points at the emergency cash pocket. "
        "Mood: amused, safe, conspiratorial. "
        "Composition: repeated notes " + ("that should not leak into the scene summary " * 50)
    )

    summary = extract_scene_summary(legacy_prompt)

    assert summary == "Aachu opens the wallet while Zuv quietly points at the emergency cash pocket."


def test_generator_prompt_text_compacts_legacy_prompt_without_visual_or_scene():
    legacy_prompt = (
        "Style reference images: [config/carousel_style_contract.json]. "
        "Scene: Aachu opens Zuv's wallet with mock-serious focus while Zuv watches, already "
        "holding out the backup card like he knew this audit was coming. "
        "Mood: warm, playful, deeply married. "
        "Composition: " + ("legacy package checklist and provenance noise " * 120)
    )

    prompt = generator_prompt_text(
        {
            "slide": 2,
            "text": "He did not stop the audit. He prepared for it.",
            "prompt": legacy_prompt,
        },
        "instagram_post",
    )

    assert len(prompt) <= MAX_PROMPT_CHARS
    assert "Aachu opens Zuv's wallet" in prompt
    assert "holding out the backup card" in prompt
    assert "legacy package checklist" not in prompt
    assert "exact 3:4 canvas" in prompt


def test_compile_image_prompt_uses_square_native_format_lock():
    prompt = compile_image_prompt(
        slide_number=1,
        slide_count=5,
        slide_copy="Copy",
        visual="Aachu and Zuv share chai at the kitchen counter.",
        format_key="square",
        style="premium romantic watercolor-and-ink illustration",
        negative="No photorealism.",
    )

    assert "Square Output" in prompt
    assert "exact 1:1 square canvas, native 1080x1080 px" in prompt
    assert "Required output size: exactly 1080x1080 px, native 1:1" in prompt
    assert "not a 3:4 carousel or 9:16 story canvas" in prompt
    assert "do not resize from another format" in prompt.lower()
    assert master_prompt_contract()["native_outputs"]["square"] == {
        "aspect_ratio": "1:1",
        "size": "1080x1080",
        "source_size": "1080x1080",
        "directory": "final-square/",
    }


def test_compile_image_prompt_rejects_over_budget_prompt():
    with pytest.raises(ValueError, match="too long"):
        compile_image_prompt(
            slide_number=1,
            slide_count=5,
            slide_copy="Copy",
            visual="Visual " * 1200,
            format_key="instagram_post",
            style="Style",
            negative="Negative",
        )
