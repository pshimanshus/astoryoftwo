from __future__ import annotations

from pathlib import Path

import pytest

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
    assert "4:5" in prompt
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

    assert "exact 4:5 canvas" in post
    assert "not a 9:16 story canvas" in post
    assert "exact 9:16 canvas" in story
    assert "not a 4:5 carousel canvas" in story
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


def test_compile_image_prompt_preserves_canonical_master_prompt_fragments():
    canonical = Path("config/references/a-story-illustration-master-prompt.md").read_text(encoding="utf-8")
    required_fragments = [
        "If actual identity reference images and style reference images cannot be used by the image-generation call",
        "This means neutral premium ivory/off-white paper, not yellow, not mustard",
        "If the paper/background reads yellow, mustard, sepia, beige/tan, parchment, coffee-stained, or heavy cream",
        "BRANDMARK RULE:",
        "BRAND LABEL WORKFLOW:",
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
    assert "exact 4:5 canvas" in prompt


def test_compile_image_prompt_rejects_unsupported_format():
    with pytest.raises(ValueError, match="Unsupported format_key"):
        compile_image_prompt(
            slide_number=1,
            slide_count=5,
            slide_copy="Copy",
            visual="Visual",
            format_key="square",
            style="Style",
            negative="Negative",
        )


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
