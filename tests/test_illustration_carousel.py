import json
import os
import subprocess
import sys
import tempfile
import unittest
from datetime import date
from pathlib import Path
from unittest.mock import Mock, patch

from pipeline.stages.c1_illustration_carousel import (
    ARTIFACT_CONTRACT,
    DEFAULT_SLIDE_COUNT,
    MAX_STORY_SLIDES,
    MIN_STORY_SLIDES,
    ORCHESTRATOR_SKILLS,
    SPECIALIST_AGENTS,
    build_manifest,
    extract_json_object,
    load_skill,
    parse_story_command,
    slugify_title,
    validate_package,
    validate_slide_count,
)
from pipeline.stages.codex_native_carousel import create_codex_native_carousel, try_render_assets


class IllustrationCarouselTests(unittest.TestCase):
    def png_bytes(self, width: int, height: int, value: int = 255) -> bytes:
        import cv2
        import numpy as np

        ok, encoded = cv2.imencode(".png", np.full((height, width, 3), value, dtype=np.uint8))
        self.assertTrue(ok)
        return encoded.tobytes()

    def png_size(self, path: Path) -> tuple[int, int]:
        import cv2

        image = cv2.imread(str(path))
        self.assertIsNotNone(image)
        height, width = image.shape[:2]
        return width, height

    def write_passing_visual_qa(self, out_dir: Path, slide_count: int = 5) -> None:
        (out_dir / "visual-qa.json").write_text(
            json.dumps(
                {
                    "schema_version": "1.0",
                    "status": "PASS",
                    "checks": {
                        "storyboard": {"pass": True, "evidence": "Human QA checked each slide against storyboard."},
                        "aachu_face": {
                            "pass": True,
                            "reference_option_ids": ["ID01"],
                            "likeness_notes": "Long dark hair, expressive brows, soft oval face, and smile energy match ID01.",
                        },
                        "zuv_face": {
                            "pass": True,
                            "reference_option_ids": ["ID01"],
                            "likeness_notes": "Dark wavy hair, thick brows, beard, face structure, and grounded expression match ID01.",
                        },
                        "dress_continuity": {"pass": True, "evidence": "Outfits and continuity cues were checked."},
                        "style": {"pass": True, "evidence": "Warm hand-drawn storybook style was checked."},
                        "model_native_text": {"pass": True, "evidence": "Copy and brandmark were checked."},
                        "final_files": {"pass": True, "evidence": "All final files were checked."},
                    },
                }
            ),
            encoding="utf-8",
        )
        lines = ["# Visual QA", ""]
        for number in range(1, slide_count + 1):
            lines.append(f"- [x] Slide {number} final image matches slide {number} storyboard.")
        lines.extend(
            [
                "- [x] Aachu face is recognizably based on the identity reference.",
                "- [x] Zuv face is recognizably based on the identity reference.",
                "- [x] Clothing and dress details follow the identity/style references.",
                "- [x] Illustration style matches the selected carousel style direction.",
                "- [x] Rendered text and brandmark are visible, accurate, and part of the artwork.",
            ]
        )
        (out_dir / "visual-qa.md").write_text("\n".join(lines) + "\n", encoding="utf-8")

    def test_slugify_title_keeps_carousel_paths_stable(self):
        self.assertEqual(slugify_title("Anchal Under the Stars!!"), "anchal-under-the-stars")
        self.assertEqual(slugify_title("  "), "illustration-carousel")

    def test_extract_json_object_handles_fenced_agent_output(self):
        payload = {"title": "He Didn't Marry Peace", "slides": [{"slide": 1}]}
        text = f"Here is the package:\n```json\n{json.dumps(payload)}\n```\nDone."

        self.assertEqual(extract_json_object(text), payload)

    def test_build_manifest_uses_artifact_contract_and_reference_images(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            image = Path(tmpdir) / "moment.jpg"
            image.write_bytes(b"not-real-image-data")

            manifest = build_manifest(
                title="Proposal Under Stars",
                slug="proposal-under-stars",
                story="A private proposal under the night sky.",
                image_paths=[image],
                today=date(2026, 5, 9),
            )

        self.assertEqual(manifest["date"], "2026-05-09")
        self.assertEqual(manifest["slug"], "proposal-under-stars")
        self.assertEqual(manifest["channel"], "@a.storyof.two")
        self.assertEqual(manifest["status"], "draft_for_human_review")
        self.assertEqual(
            manifest["reference_images"],
            [{"path": str(image), "role": "user supplied story reference"}],
        )
        self.assertEqual(manifest["artifacts"], ARTIFACT_CONTRACT)

    def test_anthropic_manifest_can_record_identity_references(self):
        from pipeline.stages.c1_illustration_carousel import build_manifest

        with tempfile.TemporaryDirectory() as tmpdir:
            story_image = Path(tmpdir) / "story.jpg"
            identity_image = Path(tmpdir) / "identity.jpg"
            story_image.write_bytes(b"story")
            identity_image.write_bytes(b"identity")

            manifest = build_manifest(
                title="Legacy Identity",
                slug="legacy-identity",
                story="A tiny ritual story.",
                image_paths=[story_image],
                identity_image_paths=[identity_image],
                today=date(2026, 5, 16),
            )

        self.assertEqual(
            manifest["identity_references"],
            [{"path": str(identity_image), "role": "Aachu/Zuv face consistency reference"}],
        )

    def test_story_command_defaults_to_five_slides(self):
        command = "/story title: Anchal Under the Stars\nI proposed under the sky."

        parsed = parse_story_command(command)

        self.assertEqual(parsed["title"], "Anchal Under the Stars")
        self.assertEqual(parsed["story"], "I proposed under the sky.")
        self.assertEqual(parsed["slide_count"], DEFAULT_SLIDE_COUNT)
        self.assertEqual((MIN_STORY_SLIDES, MAX_STORY_SLIDES), (4, 10))

    def test_slide_count_allows_longer_story_arcs_for_story_command(self):
        self.assertEqual(validate_slide_count(4), 4)
        self.assertEqual(validate_slide_count(5), 5)
        self.assertEqual(validate_slide_count(6), 6)
        self.assertEqual(validate_slide_count(10), 10)

        with self.assertRaises(ValueError):
            validate_slide_count(11)

    def test_codex_native_builder_creates_package_without_anthropic_key(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            image = Path(tmpdir) / "first-date.jpg"
            image.write_bytes(b"not-real-image-data")

            out_dir = create_codex_native_carousel(
                story="First date cups, second date jokes, then Ladakh.",
                image_paths=[image],
                title="First Date To Ladakh",
                output_root=Path(tmpdir) / "out",
                render_assets=False,
                today=date(2026, 5, 10),
            )

            manifest = json.loads((out_dir / "manifest.json").read_text(encoding="utf-8"))
            concept = json.loads((out_dir / "concept.json").read_text(encoding="utf-8"))
            prompt_pack = json.loads((out_dir / "prompt-pack.json").read_text(encoding="utf-8"))
            review = json.loads((out_dir / "review.json").read_text(encoding="utf-8"))
            storyboard = (out_dir / "storyboard.md").read_text(encoding="utf-8")
            approval = (out_dir / "final-approval.md").read_text(encoding="utf-8")

        self.assertEqual(out_dir.name, "first-date-to-ladakh")
        self.assertEqual(manifest["runtime"], "codex_native_local")
        self.assertEqual(manifest["status"], "draft_for_human_review")
        self.assertEqual(len(prompt_pack["slides"]), DEFAULT_SLIDE_COUNT)
        self.assertTrue(review["pass"])
        self.assertEqual(concept["story_selling_contract"]["skill"], "config/skills/romance-story-selling-engine.md")
        self.assertGreaterEqual(review["story_selling_score"]["total"], 28)
        self.assertEqual(review["story_selling_gate"]["status"], "PASS")
        self.assertTrue(review["story_selling_gate"]["selected_concept_process_card"])
        self.assertIn("Story-Selling process card", prompt_pack["slides"][0]["prompt"])
        self.assertIn("Story-Selling Spine", storyboard)
        self.assertIn("Story-Selling Gate: PASS", approval)

    def test_codex_native_prompt_pack_has_compact_generation_fields(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            identity_image = Path(tmpdir) / "aachu-zuv.png"
            identity_image.write_bytes(b"identity-image")

            out_dir = create_codex_native_carousel(
                story=(
                    "Selected concept from the Golden Theme tournament: She Was Not High-Maintenance. "
                    "Aachu is in a green dress, barefoot, and Zuv notices before she asks."
                ),
                image_paths=[],
                identity_image_paths=[identity_image],
                title="Wallet Audit Tiny Test",
                output_root=Path(tmpdir) / "out",
                render_assets=False,
                today=date(2026, 5, 24),
            )

            prompt_pack = json.loads((out_dir / "prompt-pack.json").read_text(encoding="utf-8"))

        self.assertLessEqual(len(prompt_pack["style_reference_images"]), 3)
        for slide in prompt_pack["slides"]:
            self.assertEqual(slide["slide_count"], 5)
            self.assertTrue(slide["visual"])
            self.assertTrue(slide["style"])
            self.assertLessEqual(len(slide["style"]), 260)
            self.assertTrue(slide["negative_prompt"])
            self.assertLessEqual(len(slide["prompt"]), 9500)

    def test_local_dry_run_backend_creates_both_native_formats(self):
        from pipeline.stages.local_dry_run_image_backend import generate_local_dry_run_images

        with tempfile.TemporaryDirectory() as tmpdir:
            identity_image = Path(tmpdir) / "aachu-zuv.png"
            identity_image.write_bytes(b"identity-image")

            out_dir = create_codex_native_carousel(
                story=(
                    "Selected concept from the Golden Theme tournament: She Was Not High-Maintenance. "
                    "Aachu is in a green dress, barefoot, and Zuv notices before she asks."
                ),
                image_paths=[],
                identity_image_paths=[identity_image],
                title="Wallet Audit Dry Run",
                output_root=Path(tmpdir) / "out",
                render_assets=False,
                today=date(2026, 5, 24),
            )

            result = generate_local_dry_run_images(out_dir)
            manifest = json.loads((out_dir / "final-images.json").read_text(encoding="utf-8"))
            instagram_path = out_dir / "final" / "slide-01.png"
            reels_path = out_dir / "final-reels-stories" / "slide-01.png"
            first_instagram_bytes = instagram_path.read_bytes()
            first_reels_bytes = reels_path.read_bytes()
            second_result = generate_local_dry_run_images(out_dir)

            self.assertEqual(result["status"], "dry_run_generated")
            self.assertEqual(result["backend"], "local_dry_run")
            self.assertFalse(result["publishable"])
            self.assertFalse(result["done"])
            self.assertEqual(manifest["status"], "dry_run_generated")
            self.assertFalse(manifest["publishable"])
            self.assertTrue(instagram_path.exists())
            self.assertTrue(reels_path.exists())
            self.assertEqual(self.png_size(instagram_path), (1080, 1350))
            self.assertEqual(self.png_size(reels_path), (1080, 1920))
            self.assertEqual(instagram_path.read_bytes(), first_instagram_bytes)
            self.assertEqual(reels_path.read_bytes(), first_reels_bytes)
            self.assertEqual(second_result["status"], "dry_run_generated")

            slide_record = result["slides"][0]
            self.assertEqual(slide_record["file"], str(instagram_path))
            self.assertEqual(slide_record["reels_stories_file"], str(reels_path))
            self.assertIn("instagram_post", slide_record["native_outputs"])
            self.assertIn("reels_stories", slide_record["native_outputs"])
            self.assertTrue(slide_record["prompt"])
            self.assertTrue(slide_record["copy"])
            self.assertEqual(slide_record["backend"], "local_dry_run")
            self.assertEqual(slide_record["generation_mode"], "local_dry_run_not_publishable")
            self.assertFalse(slide_record["publishable"])
            self.assertEqual(slide_record["source_backend"], "prompt-pack.json")
            self.assertIn("source_prompt_pack", slide_record)
            self.assertIn("provenance", slide_record)

    def test_local_dry_run_legacy_renderer_writes_preview_only_manifest(self):
        from scripts.legacy.render_illustrated_carousel_draft import render_carousel

        with tempfile.TemporaryDirectory() as tmpdir:
            out_dir = Path(tmpdir)
            slides = [
                {
                    "slide": number,
                    "copy": f"Slide {number}",
                    "visual": "Aachu and Zuv share a quiet food-table moment.",
                }
                for number in range(1, 6)
            ]
            (out_dir / "slides.json").write_text(json.dumps(slides), encoding="utf-8")
            (out_dir / "prompt-pack.json").write_text(
                json.dumps(
                    {
                        "slides": [
                            {"slide": number, "copy": f"Slide {number}", "prompt": f"Prompt {number}"}
                            for number in range(1, 6)
                        ]
                    }
                ),
                encoding="utf-8",
            )

            with patch("scripts.legacy.render_illustrated_carousel_draft.make_contact_sheet"):
                render_carousel(out_dir)
            manifest = json.loads((out_dir / "final-images.json").read_text(encoding="utf-8"))
            image_generation = json.loads((out_dir / "image-generation.json").read_text(encoding="utf-8"))
            visual_qa = json.loads((out_dir / "visual-qa.json").read_text(encoding="utf-8"))
            visual_qa_markdown = (out_dir / "visual-qa.md").read_text(encoding="utf-8")

        self.assertIn(manifest["status"], {"legacy_preview_generated", "dry_run_generated"})
        self.assertEqual(manifest["backend"], "legacy_local_renderer")
        self.assertEqual(manifest["generation_mode"], "legacy_local_preview_not_publishable")
        self.assertFalse(manifest["publishable"])
        self.assertEqual(image_generation["backend"], "legacy_local_renderer")
        self.assertFalse(image_generation["publishable"])
        self.assertFalse(all(slide["publishable"] for slide in manifest["slides"]))
        self.assertNotEqual(visual_qa["status"], "PASS")
        self.assertFalse(visual_qa["can_satisfy_final_gate"])
        self.assertIn("preview-only", visual_qa_markdown)

    def test_legacy_local_carousel_renderer_writes_preview_only_state(self):
        from pipeline.stages.local_carousel_renderer import render_local_carousel

        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = Path(tmpdir)
            identity_image = workspace / "aachu-zuv.png"
            identity_image.write_bytes(b"identity-image")
            out_dir = create_codex_native_carousel(
                story=(
                    "Selected concept from the Golden Theme tournament: She Was Not High-Maintenance. "
                    "Aachu is in a green dress, barefoot, and Zuv notices before she asks."
                ),
                image_paths=[],
                identity_image_paths=[identity_image],
                title="Legacy Local Renderer State",
                output_root=workspace / "out",
                render_assets=False,
                today=date(2026, 5, 24),
            )

            result = render_local_carousel(out_dir, refresh_quality=False, workspace_root=workspace)
            manifest = json.loads((out_dir / "final-images.json").read_text(encoding="utf-8"))
            image_generation = json.loads((out_dir / "image-generation.json").read_text(encoding="utf-8"))
            visual_qa = json.loads((out_dir / "visual-qa.json").read_text(encoding="utf-8"))

        self.assertEqual(result["status"], "legacy_preview_generated")
        self.assertEqual(manifest, image_generation)
        self.assertEqual(manifest["backend"], "legacy_local_renderer")
        self.assertEqual(manifest["generation_mode"], "legacy_local_preview_not_publishable")
        self.assertFalse(manifest["done"])
        self.assertFalse(manifest["publishable"])
        self.assertFalse(manifest["can_satisfy_final_gate"])
        self.assertFalse(all(slide["publishable"] for slide in manifest["slides"]))
        self.assertNotEqual(visual_qa["status"], "PASS")
        self.assertFalse(visual_qa["can_satisfy_final_gate"])

    def test_local_renderer_skips_text_only_slides_without_reference_images(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            result = try_render_assets(
                Path(tmpdir),
                [{"slide": 1, "copy": "He married I'm not hungry.", "source_images": []}],
            )

        self.assertEqual(result["status"], "skipped")
        self.assertIn("No source images", result["reason"])

    def test_food_denial_story_uses_shareable_not_hungry_arc(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            out_dir = create_codex_native_carousel(
                story=(
                    "Aachu says she is not hungry. Then she takes one bite from Zuv's plate, "
                    "then the best bite. Zuv orders extra now because love knows your order anyway."
                ),
                image_paths=[],
                title="He Married I'm Not Hungry",
                output_root=Path(tmpdir) / "out",
                render_assets=False,
                today=date(2026, 5, 19),
            )

            slides = json.loads((out_dir / "slides.json").read_text(encoding="utf-8"))
            concept = json.loads((out_dir / "concept.json").read_text(encoding="utf-8"))
            copy = json.loads((out_dir / "copy.json").read_text(encoding="utf-8"))
            visual_debate = json.loads((out_dir / "visual-debate.json").read_text(encoding="utf-8"))

        self.assertEqual(slides[0]["copy"], "He married \"I'm not hungry.\"")
        self.assertEqual(slides[2]["copy"], "Then the best bite.")
        self.assertEqual(concept["content_lane"], "Golden Food Denial")
        self.assertEqual(concept["concept_selection"]["winner"], "He Married I'm Not Hungry")
        self.assertEqual(visual_debate["winner"], "Plate Becomes A Love Receipt")
        self.assertIn("orders extra", copy["caption_recommended"])

    def test_private_captions_story_uses_selected_agent_room_copy_and_visual_system(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            identity = Path(tmpdir) / "aachu-zuv.jpg"
            identity.write_bytes(b"identity-image")

            out_dir = create_codex_native_carousel(
                story=(
                    "Selected concept from the four-agent repair: Some Couples Come With Private Captions. "
                    "The public format is paired labels over shared scenes: her being dramatic, him taking it seriously; "
                    "her stressed, him listening first; her excited about a tiny thing, him happy because she is; "
                    "her doesn't like it, him already on her side; him acting tough, her knows he's soft; "
                    "him bad joke, her favorite sound. Final thesis: the right person captions you kindly."
                ),
                image_paths=[],
                identity_image_paths=[identity],
                title="Some Couples Come With Private Captions",
                slide_count=8,
                output_root=Path(tmpdir) / "out",
                render_assets=False,
                today=date(2026, 5, 23),
            )

            concept = json.loads((out_dir / "concept.json").read_text(encoding="utf-8"))
            slides = json.loads((out_dir / "slides.json").read_text(encoding="utf-8"))
            copy = json.loads((out_dir / "copy.json").read_text(encoding="utf-8"))
            prompt_pack = json.loads((out_dir / "prompt-pack.json").read_text(encoding="utf-8"))
            concept_selection = json.loads((out_dir / "concept-selection.json").read_text(encoding="utf-8"))
            visual_debate = json.loads((out_dir / "visual-debate.json").read_text(encoding="utf-8"))
            post_copy_room = json.loads((out_dir / "post-copy-visual-room.json").read_text(encoding="utf-8"))

        expected_copy = [
            "some couples come with private captions",
            "her: being dramatic\nhim: taking it seriously",
            "her: stressed\nhim: listening first",
            "her: excited about a tiny thing\nhim: happy because she is",
            "her: doesn't like it\nhim: already on her side",
            "him: acting tough\nher: knows he's soft",
            "him: bad joke\nher: favorite sound",
            "the right person captions you kindly",
        ]
        joined = " ".join(
            expected_copy
            + [slide["visual"] for slide in slides]
            + [prompt["prompt"] for prompt in prompt_pack["slides"]]
        ).lower()
        self.assertEqual(concept["content_lane"], "Golden Private Captions")
        self.assertEqual([slide["copy"] for slide in slides], expected_copy)
        self.assertEqual(prompt_pack["text_overlay_plan"]["slide_copy"], expected_copy)
        self.assertEqual(concept_selection["winner"], "Some Couples Come With Private Captions")
        self.assertGreaterEqual(concept_selection["winner_score"], 28)
        self.assertEqual(visual_debate["winner"], "Private Caption Shared Frames")
        self.assertEqual(post_copy_room["status"], "GO")
        self.assertIn("paired private labels", joined)
        self.assertIn("labels near each person", joined)
        self.assertIn("aachu", joined)
        self.assertIn("zuv", joined)
        self.assertIn("captions you kindly", copy["caption_recommended"])
        self.assertNotIn("friends", joined)
        self.assertNotIn("monica", joined)
        self.assertNotIn("chandler", joined)

    def test_tasty_life_story_uses_repaired_payoff_arc_and_persona_gate(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            out_dir = create_codex_native_carousel(
                story="55 se 70 nahi. Bas life zyada tasty ho gayi.",
                image_paths=[],
                title="Life Zyada Tasty Ho Gayi",
                slide_count=6,
                output_root=Path(tmpdir) / "out",
                render_assets=False,
                today=date(2026, 5, 22),
            )

            concept = json.loads((out_dir / "concept.json").read_text(encoding="utf-8"))
            slides = json.loads((out_dir / "slides.json").read_text(encoding="utf-8"))
            copy = json.loads((out_dir / "copy.json").read_text(encoding="utf-8"))
            prompt_pack = json.loads((out_dir / "prompt-pack.json").read_text(encoding="utf-8"))
            review = json.loads((out_dir / "review.json").read_text(encoding="utf-8"))
            concept_selection = json.loads((out_dir / "concept-selection.json").read_text(encoding="utf-8"))
            visual_debate = json.loads((out_dir / "visual-debate.json").read_text(encoding="utf-8"))

        expected_copy = [
            "Woh bas \"khaya?\" nahi poochta.",
            "Woh \"aur logi?\" bolta hai.",
            "The second serving wasn't just food.",
            "No comments. Just comfort.",
            "Wanting started feeling safe.",
            "55 se 70 nahi.\nBas life zyada tasty ho gayi.",
        ]
        joined_copy = " ".join(slide["copy"] for slide in slides)
        joined_visuals = " ".join(slide["visual"] for slide in slides).lower()
        self.assertEqual(concept["content_lane"], "Golden Tasty Life")
        self.assertEqual([slide["copy"] for slide in slides], expected_copy)
        self.assertEqual(prompt_pack["text_overlay_plan"]["slide_copy"], expected_copy)
        self.assertEqual(concept["concept_selection"]["winner"], "The Second Serving Was Never Just Food")
        self.assertEqual(concept_selection["winner_score"], 29.7)
        self.assertEqual(
            concept["story_selling_decision"]["selected_concept_process_card"],
            "Card 05 - Banter To Belonging",
        )
        self.assertGreaterEqual(len(concept_selection["candidates"]), 5)
        self.assertEqual(visual_debate["winner"], "Lived-In Home Becomes A Love Receipt")
        self.assertEqual(concept["carousel_story_director_persona"]["status"], "PASS")
        self.assertEqual(concept["carousel_story_director_persona"]["selected_hook"], expected_copy[0])
        self.assertEqual(review["story_director_gate"]["status"], "PASS")
        self.assertIn("comfort and appetite-for-life", concept["human_truth"])
        self.assertIn("aur logi", copy["caption_recommended"])
        self.assertIn("second serving", copy["caption_recommended"])
        self.assertIn("comfort without comments", copy["caption_recommended"])
        self.assertIn("bas life zyada tasty", copy["caption_recommended"])
        self.assertIn("Carousel Story Director persona", prompt_pack["slides"][0]["prompt"])
        self.assertIn("home", joined_visuals)
        self.assertIn("kitchen counter", joined_visuals)
        self.assertIn("couch", joined_visuals)
        self.assertIn("second serving", joined_visuals)
        self.assertIn("no counting", joined_visuals)
        self.assertNotIn("cafe", joined_visuals)
        self.assertNotIn("restaurant", joined_visuals)
        self.assertNotIn("It started with one ordinary moment.", joined_copy)

    def test_codex_native_builder_writes_quality_spine_and_wiki_memory(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = Path(tmpdir)
            image = workspace / "first-date.jpg"
            image.write_bytes(b"not-real-image-data")

            out_dir = create_codex_native_carousel(
                story="First date cups, second date jokes, then Ladakh.",
                image_paths=[image],
                title="First Date To Ladakh",
                output_root=workspace / "output" / "carousels",
                render_assets=False,
                today=date(2026, 5, 10),
            )

            ledger = json.loads((out_dir / "run-ledger.json").read_text(encoding="utf-8"))
            manifest = json.loads((out_dir / "manifest.json").read_text(encoding="utf-8"))
            prompt_pack = json.loads((out_dir / "prompt-pack.json").read_text(encoding="utf-8"))
            stage_reviews = json.loads((out_dir / "stage-reviews.json").read_text(encoding="utf-8"))
            final_audit = json.loads((out_dir / "final-audit.json").read_text(encoding="utf-8"))
            wiki_update = (out_dir / "wiki-update.md").read_text(encoding="utf-8")
            wiki_page = workspace / "wiki" / "carousels" / "first-date-to-ladakh.md"
            wiki_page_exists = wiki_page.exists()
            wiki_index = (workspace / "wiki" / "index.md").read_text(encoding="utf-8")
            working_memory = (workspace / "memory" / "working.md").read_text(encoding="utf-8")
            graph = json.loads((workspace / "memory" / "graph.json").read_text(encoding="utf-8"))

        requirement_ids = {requirement["id"] for requirement in ledger["requirements"]}
        self.assertTrue({"REQ-STYLE-001", "REQ-PHOTO-001", "REQ-SLIDES-001"}.issubset(requirement_ids))
        self.assertTrue({"REQ-BRAND-001", "REQ-NEGATIVE-001", "REQ-WIKI-001"}.issubset(requirement_ids))
        self.assertTrue({"REQ-MODEL-NATIVE-TEXT-001", "REQ-VISUAL-QA-001"}.issubset(requirement_ids))
        self.assertIn("REQ-IDENTITY-CONSISTENCY-001", requirement_ids)
        self.assertIn("REQ-VISUAL-PLAN-QUALITY-001", requirement_ids)
        self.assertEqual(prompt_pack["text_overlay_plan"]["brandmark"], "@a.storyof.two")
        self.assertIn("bottom-right", prompt_pack["text_overlay_plan"]["brandmark_placement"])
        self.assertIn("identity_consistency_review", manifest["quality_spine"]["artifacts"])
        self.assertIn("visual_plan_quality", manifest["quality_spine"]["artifacts"])
        self.assertEqual(manifest["quality_spine"]["observer"], "C0.5-Jarvis")
        self.assertEqual(manifest["quality_spine"]["artifacts"]["final_audit"], "final-audit.json")
        self.assertEqual(ledger["observer"]["agent"], "C0.5-Jarvis")
        self.assertEqual(ledger["final_gate"]["status"], "NEEDS_FIXES")
        self.assertIn("render_assets=False", ledger["final_gate"]["notes"])
        self.assertIn("prompt_reviewer", stage_reviews["reviews"])
        self.assertEqual(final_audit["status"], "NEEDS_FIXES")
        self.assertFalse(final_audit["pass"])
        self.assertFalse(final_audit["requirements"]["REQ-FINAL-IMAGES-001"]["pass"])
        self.assertFalse(final_audit["requirements"]["REQ-IDENTITY-001"]["pass"])
        self.assertFalse(final_audit["requirements"]["REQ-IDENTITY-CONSISTENCY-001"]["pass"])
        self.assertTrue(final_audit["requirements"]["REQ-VISUAL-PLAN-QUALITY-001"]["pass"])
        self.assertFalse(final_audit["requirements"]["REQ-MODEL-NATIVE-TEXT-001"]["pass"])
        self.assertFalse(final_audit["requirements"]["REQ-VISUAL-QA-001"]["pass"])
        self.assertTrue(all(final_audit["requirements"]["REQ-WIKI-001"]["evidence"].values()))
        self.assertIn("First Date To Ladakh", wiki_update)
        self.assertTrue(wiki_page_exists)
        self.assertIn("[First Date To Ladakh](carousels/first-date-to-ladakh.md)", wiki_index)
        self.assertIn("C-layer carousel run: First Date To Ladakh", working_memory)
        self.assertIn("carousel:first-date-to-ladakh", graph["entities"])

    def test_cli_defaults_to_codex_native_without_anthropic_key(self):
        repo_root = Path(__file__).resolve().parent.parent
        with tempfile.TemporaryDirectory() as tmpdir:
            image = Path(tmpdir) / "first-date.jpg"
            image.write_bytes(b"not-real-image-data")
            output_root = Path(tmpdir) / "out"
            env = os.environ.copy()
            env.pop("ANTHROPIC_API_KEY", None)

            result = subprocess.run(
                [
                    sys.executable,
                    str(repo_root / "scripts" / "create_illustration_carousel.py"),
                    "--story",
                    "First date cups, second date jokes, then Ladakh.",
                    "--title",
                    "CLI Native",
                    "--image",
                    str(image),
                    "--output-root",
                    str(output_root),
                    "--no-render",
                ],
                cwd=repo_root,
                env=env,
                text=True,
                capture_output=True,
                check=False,
            )

            manifest_path = output_root / str(date.today()) / "cli-native" / "manifest.json"
            manifest_exists = manifest_path.exists()

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("Codex-native carousel package saved", result.stdout)
        self.assertTrue(manifest_exists)

    def test_cli_accepts_identity_image_for_codex_native_runs(self):
        repo_root = Path(__file__).resolve().parent.parent
        with tempfile.TemporaryDirectory() as tmpdir:
            story_image = Path(tmpdir) / "anklet.jpg"
            identity_image = Path(tmpdir) / "identity.jpg"
            story_image.write_bytes(b"story-image")
            identity_image.write_bytes(b"identity-image")
            output_root = Path(tmpdir) / "out"
            env = os.environ.copy()
            env.pop("ANTHROPIC_API_KEY", None)

            result = subprocess.run(
                [
                    sys.executable,
                    str(repo_root / "scripts" / "create_illustration_carousel.py"),
                    "--story",
                    "Before proposing I tied her anklet. After marriage I still tie her sandals.",
                    "--title",
                    "CLI Identity",
                    "--image",
                    str(story_image),
                    "--identity-image",
                    str(identity_image),
                    "--output-root",
                    str(output_root),
                    "--no-render",
                ],
                cwd=repo_root,
                env=env,
                text=True,
                capture_output=True,
                check=False,
            )

            manifest_path = output_root / str(date.today()) / "cli-identity" / "manifest.json"
            manifest = json.loads(manifest_path.read_text(encoding="utf-8")) if manifest_path.exists() else {}

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(
            manifest["identity_references"],
            [{"path": str(identity_image), "role": "Aachu/Zuv face consistency reference"}],
        )

    def test_carousel_style_contract_contains_aachu_zuv_north_star(self):
        from pipeline.stages.carousel_contract import load_style_contract

        contract = load_style_contract()

        self.assertIn("Aachu and Zuv", contract["north_star"])
        self.assertIn("Product Unshipped", contract["shared_style_prompt"])
        self.assertIn("soft hand-drawn flat vector", contract["shared_style_prompt"])
        self.assertIn("warm hand-drawn desi storybook illustration", contract["compact_style_prompt"])
        self.assertIn("Aachu/Zuv faces", contract["compact_style_prompt"])
        self.assertIn("No photorealism", contract["shared_negative_prompt"])
        self.assertEqual(contract["brandmark"], "@a.storyof.two")
        self.assertEqual(contract["typography"]["strategy"], "model_native")
        self.assertEqual(
            contract["style_references"],
            [
                "output/carousels/2026-05-19/main-kar-lungi/final/slide-01.png",
                "output/carousels/2026-05-19/love-carries-the-heavier-half/final/slide-03.png",
                "output/carousels/2026-05-16/he-learned-her-subtitles/final/slide-02.png",
            ],
        )
        self.assertEqual(contract["legacy_typography"]["strategy"], "legacy_local_overlay")
        self.assertIn("spark", contract["characters"]["aachu"]["relationship_role"])
        self.assertIn("steady flame", contract["characters"]["zuv"]["relationship_role"])

    def test_golden_viral_theme_skill_is_required_for_carousels(self):
        from pipeline.stages.carousel_contract import load_style_contract

        skill_name = "golden-viral-carousel-theme"
        skill_path = Path("config/skills/golden-viral-carousel-theme.md")
        reference_path = Path("config/references/golden-viral-carousel-theme-reference.md")

        self.assertTrue(skill_path.exists())
        self.assertTrue(reference_path.exists())

        skill_text = skill_path.read_text(encoding="utf-8")
        reference_text = reference_path.read_text(encoding="utf-8")
        framework_text = Path("config/skills/illustration-carousel-framework.md").read_text(encoding="utf-8")
        contract = load_style_contract()

        self.assertIn("universal relationship truth", skill_text)
        self.assertIn("golden theme", skill_text.lower())
        self.assertIn("object-specific", reference_text)
        self.assertIn(str(reference_path), framework_text)
        self.assertTrue(contract["golden_theme_contract"]["required"])
        self.assertEqual(contract["golden_theme_contract"]["skill"], str(skill_path))
        self.assertEqual(contract["golden_theme_contract"]["reference"], str(reference_path))
        self.assertIn(skill_name, ORCHESTRATOR_SKILLS)
        for _, skill_names in SPECIALIST_AGENTS:
            self.assertIn(skill_name, skill_names)

    def test_romance_story_selling_skill_is_registered_for_carousel_concepting(self):
        skill_name = "romance-story-selling-engine"
        skill_path = Path("config/skills/romance-story-selling-engine.md")
        reference_dir = Path("config/references/story-selling-canon")

        self.assertTrue(skill_path.exists())
        self.assertTrue((reference_dir / "concept-process-cards.md").exists())
        self.assertTrue((reference_dir / "rubric.md").exists())

        skill_text = skill_path.read_text(encoding="utf-8")
        framework_text = Path("config/skills/illustration-carousel-framework.md").read_text(encoding="utf-8")

        self.assertIn("Story-Selling", skill_text)
        self.assertIn("golden-theme variant tournament", skill_text)
        self.assertIn(str(reference_dir / "concept-process-cards.md"), framework_text)
        self.assertIn("source-policy.md", skill_text)
        loaded_skill = load_skill(skill_name)
        self.assertIn("Story Selling Canon Source Policy", loaded_skill)
        self.assertIn("Concept Process Cards", loaded_skill)
        self.assertIn("30-point rubric", loaded_skill)
        self.assertIn(skill_name, ORCHESTRATOR_SKILLS)
        for _, skill_names in SPECIALIST_AGENTS:
            self.assertIn(skill_name, skill_names)

    def test_anthropic_package_validation_requires_story_selling_gate(self):
        package = {
            "concept": {"title": "Tiny Care", "slide_count": 5},
            "post_copy_visual_room": {"status": "GO", "selected_visual_system": "Tiny Ritual Evidence"},
            "visual_debate": {"status": "PASS", "winner": "Tiny Ritual Evidence"},
            "slides": [{"slide": 1, "copy": "x", "visual": "y"}],
            "prompt_pack": {"slides": [{"slide": 1, "prompt": "p"}]},
            "copy": {},
            "review": {"status": "draft_review", "total": 35, "max": 40, "pass": True},
        }

        with self.assertRaisesRegex(Exception, "story_selling_score"):
            validate_package(package)

        package["review"].update(
            {
                "story_selling_score": {"total": 29},
                "story_selling_gate": {
                    "status": "PASS",
                    "selected_concept_process_card": "Card 07 - Anti-Ideal To Real Love",
                },
                "story_selling_hard_fails": [],
            }
        )

        validate_package(package)

    def test_style_contract_blocks_photo_filter_placeholders_as_final_art(self):
        from pipeline.stages.carousel_contract import load_style_contract

        contract = load_style_contract()
        production_gate = contract.get("production_gate", {})

        self.assertEqual(production_gate.get("final_art_requirement"), "generated_scene_illustrations")
        self.assertIn("photo-filter", production_gate.get("forbidden_final_art", []))
        self.assertIn("opencv-cartoon-filter", production_gate.get("forbidden_final_art", []))
        self.assertIn("prompt-pack.json", production_gate.get("required_package_artifacts", []))
        self.assertIn("final-audit.json", production_gate.get("required_package_artifacts", []))

    def test_no_uncontracted_one_off_carousel_generator_scripts(self):
        repo_root = Path(__file__).resolve().parent.parent
        allowed = {
            "create_illustration_carousel.py",
            "create_star_proposal_carousel.py",
            "package_generated_carousel.py",
            "package_star_proposal_generated_carousel.py",
            "render_carousel_text_overlays.py",
        }

        carousel_scripts = {
            path.name
            for path in (repo_root / "scripts").glob("*carousel*.py")
        }

        self.assertEqual(
            carousel_scripts - allowed,
            set(),
            "Create new carousels through scripts/create_illustration_carousel.py "
            "or the C-layer package flow; do not add one-off renderers that bypass "
            "prompt-pack/review/final-audit artifacts.",
        )

    def test_codex_native_manifest_records_identity_reference(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = Path(tmpdir)
            story_image = workspace / "anklet.jpg"
            identity_image = workspace / "aachu-zuv-7.43.23\u202fPM.png"
            story_image.write_bytes(b"story-image")
            identity_image.write_bytes(b"identity-image")

            out_dir = create_codex_native_carousel(
                story="He tied the anklet before proposing; after marriage he still ties her sandals.",
                image_paths=[story_image],
                identity_image_paths=[identity_image],
                title="Same Posture",
                output_root=workspace / "output" / "carousels",
                render_assets=False,
                today=date(2026, 5, 16),
            )

            manifest = json.loads((out_dir / "manifest.json").read_text(encoding="utf-8"))
            prompt_pack = json.loads((out_dir / "prompt-pack.json").read_text(encoding="utf-8"))
            identity_review = json.loads((out_dir / "identity-consistency-review.json").read_text(encoding="utf-8"))

        self.assertEqual(
            manifest["identity_references"],
            [{"path": str(identity_image), "role": "Aachu/Zuv face consistency reference"}],
        )
        self.assertIn(str(identity_image), prompt_pack["identity_reference_images"])
        self.assertIn("Aachu", prompt_pack["character_bible"])
        self.assertIn("Zuv", prompt_pack["character_bible"])
        self.assertIn("clothing", prompt_pack["identity_reference_usage"])
        self.assertEqual(identity_review["agent"], "C3.5-IdentityConsistency")
        self.assertEqual(identity_review["status"], "PASS")
        self.assertEqual(len(identity_review["slides"]), DEFAULT_SLIDE_COUNT)
        self.assertTrue(
            all(
                {"face_structure", "facial_expression", "clothing", "cross_slide_consistency"}.issubset(
                    slide["checks"]
                )
                for slide in identity_review["slides"]
            )
        )
        self.assertTrue(all(slide["checks"]["identity_references_attached"] for slide in identity_review["slides"]))
        self.assertIn(str(identity_image), prompt_pack["slides"][0]["prompt"])
        self.assertIn("Identity continuity lock", prompt_pack["slides"][0]["prompt"])

    def test_codex_native_discovers_workspace_identity_images_folder(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = Path(tmpdir)
            story_image = workspace / "anklet.jpg"
            identity_dir = workspace / "identity_images"
            identity_dir.mkdir()
            identity_image = identity_dir / "aachu_zuv.png"
            story_image.write_bytes(b"story-image")
            identity_image.write_bytes(b"identity-image")

            out_dir = create_codex_native_carousel(
                story="He tied the anklet before proposing; after marriage he still ties her sandals.",
                image_paths=[story_image],
                title="Auto Identity",
                output_root=workspace / "output" / "carousels",
                render_assets=False,
                today=date(2026, 5, 16),
            )

            manifest = json.loads((out_dir / "manifest.json").read_text(encoding="utf-8"))
            prompt_pack = json.loads((out_dir / "prompt-pack.json").read_text(encoding="utf-8"))

        selfEqual = self.assertEqual
        selfEqual(
            manifest["identity_references"],
            [{"path": str(identity_image.resolve()), "role": "Aachu/Zuv face consistency reference"}],
        )
        self.assertEqual(prompt_pack["identity_reference_images"], [str(identity_image.resolve())])

    def test_codex_native_auto_identity_discovery_uses_curated_bundle(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = Path(tmpdir)
            story_image = workspace / "story.jpg"
            identity_dir = workspace / "identity_images"
            identity_dir.mkdir()
            story_image.write_bytes(b"story-image")
            discovered = []
            for index in range(7):
                image = identity_dir / f"identity-{index:02d}.jpg"
                image.write_bytes(b"identity-image")
                discovered.append(image.resolve())

            out_dir = create_codex_native_carousel(
                story="A soft archive about Aachu and Zuv becoming home in tiny moments.",
                image_paths=[story_image],
                title="Small Evidence",
                output_root=workspace / "output" / "carousels",
                render_assets=False,
                today=date(2026, 5, 16),
            )

            manifest = json.loads((out_dir / "manifest.json").read_text(encoding="utf-8"))
            prompt_pack = json.loads((out_dir / "prompt-pack.json").read_text(encoding="utf-8"))

        selected = [str(path) for path in discovered[:4]]
        self.assertEqual(prompt_pack["identity_reference_images"], selected)
        self.assertEqual(
            [reference["path"] for reference in manifest["identity_references"]],
            selected,
        )
        self.assertEqual(manifest["identity_reference_selection"]["candidate_count"], 7)
        self.assertEqual(manifest["identity_reference_selection"]["selected_count"], 4)
        self.assertIn("small curated", prompt_pack["identity_reference_usage"])
        self.assertIn("Do not dump", prompt_pack["identity_reference_strategy"]["rule"])

    def test_codex_native_rejects_overlarge_explicit_identity_bundle(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = Path(tmpdir)
            story_image = workspace / "story.jpg"
            story_image.write_bytes(b"story-image")
            identity_paths = []
            for index in range(5):
                image = workspace / f"identity-{index:02d}.jpg"
                image.write_bytes(b"identity-image")
                identity_paths.append(image)

            with self.assertRaisesRegex(ValueError, "at most 4 curated identity references"):
                create_codex_native_carousel(
                    story="A soft archive about Aachu and Zuv.",
                    image_paths=[story_image],
                    identity_image_paths=identity_paths,
                    title="Small Evidence",
                    output_root=workspace / "output" / "carousels",
                    render_assets=False,
                    today=date(2026, 5, 16),
                )

    def test_interactive_mode_blank_identity_keeps_auto_discovery_enabled(self):
        from pipeline.stages.c1_illustration_carousel import interactive_mode

        responses = [
            "Auto Identity",
            "A small story about Aachu and Zuv.",
            "/tmp/story.jpg",
            "",
            "",
            "",
        ]

        with patch("builtins.input", side_effect=responses), patch("builtins.print"):
            options = interactive_mode()

        self.assertIsNone(options["identity_image_paths"])

    def test_tiny_ritual_story_uses_aachu_zuv_theme_not_travel_template(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            image = Path(tmpdir) / "anklet.jpg"
            image.write_bytes(b"story-image")

            out_dir = create_codex_native_carousel(
                story="Before proposing I tied her anklet. After marriage I still tie her shoes and sandals.",
                image_paths=[image],
                title="Same Posture",
                output_root=Path(tmpdir) / "out",
                render_assets=False,
                today=date(2026, 5, 16),
            )

            concept = json.loads((out_dir / "concept.json").read_text(encoding="utf-8"))
            slides = json.loads((out_dir / "slides.json").read_text(encoding="utf-8"))

        joined = " ".join(slide["copy"] + " " + slide["visual"] for slide in slides).lower()
        self.assertEqual(concept["content_lane"], "Tiny Rituals")
        self.assertIn("anklet", joined)
        self.assertIn("sandals", joined)
        self.assertNotIn("date became a trip", joined)
        self.assertNotIn("story feel huge", joined)

    def test_chaotic_wife_story_uses_viral_reference_pattern(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            image = Path(tmpdir) / "identity.jpg"
            image.write_bytes(b"story-image")

            out_dir = create_codex_native_carousel(
                story=(
                    "He did not marry peace. He married Aachu chaos: tears while saying "
                    "I am fine, suitcase drama, mood swings, and Zuv choosing her every day."
                ),
                image_paths=[image],
                title="He Did Not Marry Peace",
                output_root=Path(tmpdir) / "out",
                render_assets=False,
                today=date(2026, 5, 16),
            )

            concept = json.loads((out_dir / "concept.json").read_text(encoding="utf-8"))
            slides = json.loads((out_dir / "slides.json").read_text(encoding="utf-8"))

        slide_copy = [slide["copy"] for slide in slides]
        joined = " ".join(slide_copy + [slide["visual"] for slide in slides]).lower()
        self.assertEqual(concept["content_lane"], "Chaotic Wife, Calm Husband")
        self.assertEqual(slide_copy[0], "He didn't marry peace.")
        self.assertIn("mujhe kuch nahi hua", joined)
        self.assertIn("14 outfits", joined)
        self.assertIn("10 moods", joined)
        self.assertIn("chaos", slide_copy[-1].lower())
        self.assertNotIn("date became a trip", joined)
        self.assertNotIn("story feel huge", joined)

    def test_mood_changed_story_preserves_selected_golden_theme_copy(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            identity = Path(tmpdir) / "aachu-zuv.jpg"
            identity.write_bytes(b"identity-image")

            out_dir = create_codex_native_carousel(
                story=(
                    "Selected concept from the Golden Theme tournament: Her mood changed. "
                    "His hand did not. Universal relationship truth: some moods change "
                    "mid-walk, and love is the person who notices both the feeling and "
                    "the hand still reaching. Public slide copy must be exactly: "
                    "Slide 1: Some moods change mid-walk. Slide 2: She feels everything "
                    "fully. Slide 3: Her hand still reaches. Slide 4: He slows the world "
                    "down. Slide 5: Love keeps pace."
                ),
                image_paths=[],
                identity_image_paths=[identity],
                title="Her Mood Changed His Hand Didnt",
                output_root=Path(tmpdir) / "out",
                render_assets=False,
                today=date(2026, 5, 17),
            )

            concept = json.loads((out_dir / "concept.json").read_text(encoding="utf-8"))
            slides = json.loads((out_dir / "slides.json").read_text(encoding="utf-8"))
            prompt_pack = json.loads((out_dir / "prompt-pack.json").read_text(encoding="utf-8"))
            copy = json.loads((out_dir / "copy.json").read_text(encoding="utf-8"))

        expected_copy = [
            "Some moods change mid-walk.",
            "She feels everything fully.",
            "Her hand still reaches.",
            "He slows the world down.",
            "Love keeps pace.",
        ]
        self.assertEqual(concept["content_lane"], "Golden Mood Steadiness")
        self.assertEqual([slide["copy"] for slide in slides], expected_copy)
        self.assertEqual(prompt_pack["text_overlay_plan"]["slide_copy"], expected_copy)
        joined = " ".join(expected_copy + [slide["visual"] for slide in slides]).lower()
        self.assertIn("hand", joined)
        self.assertIn("pace", joined)
        self.assertIn("slow", joined)
        self.assertNotIn("mujhe kuch nahi hua", joined)
        self.assertNotIn("14 outfits", joined)
        self.assertIn("love keeps pace", copy["caption_recommended"])

    def test_morning_person_story_uses_chai_silence_arc(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            image = Path(tmpdir) / "identity.jpg"
            image.write_bytes(b"story-image")

            out_dir = create_codex_native_carousel(
                story=(
                    "Zuv did not marry a morning person. He married Aachu's five more minutes, "
                    "sleepy chaos, angry hungry cute moods, and learned chai first questions later."
                ),
                image_paths=[image],
                title="He Did Not Marry A Morning Person",
                output_root=Path(tmpdir) / "out",
                render_assets=False,
                today=date(2026, 5, 16),
            )

            concept = json.loads((out_dir / "concept.json").read_text(encoding="utf-8"))
            slides = json.loads((out_dir / "slides.json").read_text(encoding="utf-8"))
            copy = json.loads((out_dir / "copy.json").read_text(encoding="utf-8"))

        slide_copy = [slide["copy"] for slide in slides]
        joined = " ".join(slide_copy + [slide["visual"] for slide in slides]).lower()
        self.assertEqual(concept["content_lane"], "Chaotic Wife, Calm Husband")
        self.assertEqual(slide_copy[0], "He didn't marry a morning person.")
        self.assertIn("5 more minutes", joined)
        self.assertIn("chai first", joined)
        self.assertIn("questions later", joined)
        self.assertIn("not to talk", slide_copy[-1].lower())
        self.assertIn("chai and silence", copy["caption_recommended"])
        self.assertNotIn("mujhe kuch nahi hua", copy["caption_recommended"])
        self.assertNotIn("date became a trip", joined)
        self.assertNotIn("story feel huge", joined)

    def test_photo_ritual_story_uses_hinglish_bubble_arc(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            waterfall = Path(tmpdir) / "waterfall.jpg"
            lantern = Path(tmpdir) / "lantern.jpg"
            waterfall.write_bytes(b"waterfall")
            lantern.write_bytes(b"lantern")

            out_dir = create_codex_native_carousel(
                story=(
                    "Every trip has one bas ek photo aur person. In our story, Aachu is "
                    "the memory maker and Zuv is the haan baba patience person. Waterfall "
                    "by day, lantern light by night, same photo ritual."
                ),
                image_paths=[waterfall, lantern],
                title="Bas Ek Photo Aur",
                output_root=Path(tmpdir) / "out",
                render_assets=False,
                today=date(2026, 5, 16),
            )

            concept = json.loads((out_dir / "concept.json").read_text(encoding="utf-8"))
            slides = json.loads((out_dir / "slides.json").read_text(encoding="utf-8"))
            copy = json.loads((out_dir / "copy.json").read_text(encoding="utf-8"))

        slide_copy = [slide["copy"] for slide in slides]
        joined = " ".join(slide_copy + [slide["visual"] for slide in slides]).lower()
        speech_bubbles = " ".join(
            slide.get("text_layout", {}).get("speech_bubble", "") for slide in slides
        ).lower()
        self.assertEqual(concept["content_lane"], "Tiny Rituals")
        self.assertEqual(slide_copy[0], 'Har trip mein ek "bas ek photo aur" person hota hai.')
        self.assertEqual(slides[0]["role"], "universal hook")
        self.assertEqual(slides[1]["role"], "specific revelation")
        self.assertEqual(slides[2]["role"], "proof beat")
        self.assertEqual(slides[3]["role"], "emotional turn")
        self.assertEqual(slides[4]["role"], "save/share thesis")
        self.assertIn("humare mein, obviously aachu", joined)
        self.assertIn("haan baba", joined)
        self.assertIn("waterfall", joined)
        self.assertIn("lantern", joined)
        self.assertIn("memories ko ours bana dena", joined)
        self.assertIn("last one, promise", speech_bubbles)
        self.assertIn("haan baba", speech_bubbles)
        self.assertIn("bas ek photo aur", copy["caption_recommended"])
        self.assertNotIn("date became a trip", joined)
        self.assertNotIn("story feel huge", joined)

    def test_kashmiri_language_story_uses_family_belonging_arc(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            identity = Path(tmpdir) / "aachu-zuv.jpg"
            identity.write_bytes(b"identity-image")

            out_dir = create_codex_native_carousel(
                story=(
                    "He did not learn the meaning, he learned the vibe. Aachu says Kashmiri "
                    "words with full tone and family energy. Zuv repeats kurta, patpahan, "
                    "ursu ursu, and namaskar mahara in a funny voice, even to her parents."
                ),
                image_paths=[],
                identity_image_paths=[identity],
                title="He Didn't Learn The Meaning. He Learned The Vibe.",
                output_root=Path(tmpdir) / "out",
                render_assets=False,
                today=date(2026, 5, 16),
            )

            concept = json.loads((out_dir / "concept.json").read_text(encoding="utf-8"))
            slides = json.loads((out_dir / "slides.json").read_text(encoding="utf-8"))
            copy = json.loads((out_dir / "copy.json").read_text(encoding="utf-8"))

        slide_copy = [slide["copy"] for slide in slides]
        joined = " ".join(slide_copy + [slide["visual"] for slide in slides]).lower()
        self.assertEqual(concept["content_lane"], "Kashmiri Wife x Non-Kashmiri Husband")
        self.assertEqual(slide_copy[0], "Some people become the inside joke.")
        self.assertEqual(slide_copy[-1], "Love is trying to belong.")
        self.assertTrue(all(len(copy.split()) <= 8 for copy in slide_copy))
        self.assertIn("family passwords", joined)
        self.assertIn("same funny tone", joined)
        self.assertIn("trying to join the room", joined)
        self.assertIn("her people laugh", joined)
        self.assertIn("Golden Theme score: 29.5/30", copy["posting_notes"])
        self.assertNotIn("date became a trip", joined)
        self.assertNotIn("story feel huge", joined)

    def test_subtitles_story_uses_mood_translation_arc(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            identity = Path(tmpdir) / "aachu-zuv.jpg"
            identity.write_bytes(b"identity-image")

            out_dir = create_codex_native_carousel(
                story=(
                    "Some people come with subtitles. Aachu says kuch nahi but her "
                    "face says the full paragraph: hungry, sleepy, offended, missing "
                    "you, wants chai. Zuv learned her translation."
                ),
                image_paths=[],
                identity_image_paths=[identity],
                title="He Learned Her Subtitles",
                output_root=Path(tmpdir) / "out",
                render_assets=False,
                today=date(2026, 5, 16),
            )

            concept = json.loads((out_dir / "concept.json").read_text(encoding="utf-8"))
            slides = json.loads((out_dir / "slides.json").read_text(encoding="utf-8"))
            copy = json.loads((out_dir / "copy.json").read_text(encoding="utf-8"))

        slide_copy = [slide["copy"] for slide in slides]
        joined = " ".join(slide_copy + [slide["visual"] for slide in slides]).lower()
        speech_bubbles = " ".join(
            slide.get("text_layout", {}).get("speech_bubble", "") for slide in slides
        ).lower()
        self.assertEqual(concept["content_lane"], "Chaotic Wife, Calm Husband")
        self.assertEqual(slide_copy[0], "Some people come with subtitles.")
        self.assertEqual(slide_copy[-1], "Maybe love is learning the subtitles.")
        self.assertTrue(all(len(copy.split()) <= 8 for copy in slide_copy))
        self.assertIn("full paragraph", joined)
        self.assertIn("hungry", joined)
        self.assertIn("wants chai", joined)
        self.assertIn("kuch nahi", joined)
        self.assertIn("translation", joined)
        self.assertIn("kuch nahi", speech_bubbles)
        self.assertIn("learning the subtitles", copy["caption_recommended"])
        self.assertNotIn("date became a trip", joined)
        self.assertNotIn("story feel huge", joined)

    def test_workday_homecoming_story_uses_himanshu_pov_arc_and_tournament(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            identity = Path(tmpdir) / "aachu-zuv.jpg"
            identity.write_bytes(b"identity-image")

            out_dir = create_codex_native_carousel(
                story=(
                    "Selected concept from the Golden Theme tournament: guy has a bad work day, "
                    "sits in his car, remembers Aachu waiting at home with chai, drama, and one long story, "
                    "then smiles before driving home."
                ),
                image_paths=[],
                identity_image_paths=[identity],
                title="Maybe Chaos Is Also Home",
                output_root=Path(tmpdir) / "out",
                render_assets=False,
                today=date(2026, 5, 18),
            )

            concept = json.loads((out_dir / "concept.json").read_text(encoding="utf-8"))
            slides = json.loads((out_dir / "slides.json").read_text(encoding="utf-8"))
            copy = json.loads((out_dir / "copy.json").read_text(encoding="utf-8"))
            prompt_pack = json.loads((out_dir / "prompt-pack.json").read_text(encoding="utf-8"))
            concept_selection = json.loads((out_dir / "concept-selection.json").read_text(encoding="utf-8"))

        expected_copy = [
            "Some days make him want silence.",
            "Then he remembers her waiting.",
            "Chai. Drama. One long story.",
            "And he smiles before home.",
            "Maybe chaos is also home.",
        ]
        joined = " ".join(expected_copy + [slide["visual"] for slide in slides]).lower()
        self.assertEqual(concept["content_lane"], "Himanshu POV")
        self.assertEqual([slide["copy"] for slide in slides], expected_copy)
        self.assertEqual(prompt_pack["text_overlay_plan"]["slide_copy"], expected_copy)
        self.assertEqual(concept["concept_selection"]["decision"], "GO")
        self.assertGreaterEqual(concept["concept_selection"]["winner_score"], 28)
        self.assertEqual(concept_selection["winner"], "Maybe Chaos Is Also Home")
        self.assertGreaterEqual(len(concept_selection["candidates"]), 5)
        self.assertIn("bad work", joined)
        self.assertIn("parked car", joined)
        self.assertIn("ghar aa jao", joined)
        self.assertIn("chai", joined)
        self.assertIn("long story", joined)
        self.assertIn("chaos is also home", copy["caption_recommended"])
        self.assertNotIn("date became a trip", joined)
        self.assertNotIn("story feel huge", joined)

    def test_high_maintenance_story_uses_care_without_shrinking_arc_and_tournament(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            image = Path(tmpdir) / "ayatana-balcony.jpg"
            identity = Path(tmpdir) / "aachu-zuv.jpg"
            image.write_bytes(b"story-image")
            identity.write_bytes(b"identity-image")

            out_dir = create_codex_native_carousel(
                story=(
                    "Selected concept from the Golden Theme tournament: She Was Not High-Maintenance. "
                    "Aachu is in a green dress on the Ayatana balcony, barefoot and fully alive. "
                    "Zuv notices the tiny discomfort before she asks and kneels to help with her shoes. "
                    "Golden Theme score: 29.5/30. Public slide copy must be exactly: "
                    "Slide 1: She was not high-maintenance. Slide 2: She was just fully alive. "
                    "Slide 3: Bare feet. Green dress. Tiny crisis. Slide 4: He noticed before she asked. "
                    "Slide 5: Maybe love is care without shrinking."
                ),
                image_paths=[image],
                identity_image_paths=[identity],
                title="She Was Not High Maintenance",
                output_root=Path(tmpdir) / "out",
                render_assets=False,
                today=date(2026, 5, 18),
            )

            concept = json.loads((out_dir / "concept.json").read_text(encoding="utf-8"))
            slides = json.loads((out_dir / "slides.json").read_text(encoding="utf-8"))
            copy = json.loads((out_dir / "copy.json").read_text(encoding="utf-8"))
            prompt_pack = json.loads((out_dir / "prompt-pack.json").read_text(encoding="utf-8"))
            concept_selection = json.loads((out_dir / "concept-selection.json").read_text(encoding="utf-8"))

        expected_copy = [
            "She was not high-maintenance.",
            "She was just fully alive.",
            "Bare feet. Green dress. Tiny crisis.",
            "He noticed before she asked.",
            "Maybe love is care without shrinking.",
        ]
        joined = " ".join(expected_copy + [slide["visual"] for slide in slides]).lower()
        self.assertEqual(concept["content_lane"], "Golden Care Without Shrinking")
        self.assertEqual([slide["copy"] for slide in slides], expected_copy)
        self.assertEqual(prompt_pack["text_overlay_plan"]["slide_copy"], expected_copy)
        self.assertEqual(concept["concept_selection"]["decision"], "GO")
        self.assertEqual(concept["concept_selection"]["winner"], "She Was Not High-Maintenance")
        self.assertEqual(concept_selection["winner_score"], 29.5)
        self.assertGreaterEqual(len(concept_selection["candidates"]), 5)
        self.assertIn("green dress", joined)
        self.assertIn("bare feet", joined)
        self.assertIn("tiny discomfort", joined)
        self.assertIn("notices", joined)
        self.assertIn("care without shrinking", copy["caption_recommended"])
        self.assertIn("Golden Theme score: 29.5/30", copy["posting_notes"])
        self.assertNotIn("before the ring", joined)
        self.assertNotIn("anklet", joined)
        self.assertNotIn("date became a trip", joined)

    def test_softness_under_fire_story_uses_be_safe_arc_and_tournament(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            restaurant = Path(tmpdir) / "restaurant-wall.jpg"
            aquarium = Path(tmpdir) / "aquarium.jpg"
            identity = Path(tmpdir) / "aachu-zuv.jpg"
            restaurant.write_bytes(b"story-image")
            aquarium.write_bytes(b"story-image")
            identity.write_bytes(b"identity-image")

            out_dir = create_codex_native_carousel(
                story=(
                    "Selected concept from the Golden Theme tournament: He didn't marry someone "
                    "who says everything gently. Aachu loves physical affection, says be safe from "
                    "the bottom of her heart, and sometimes her spicy attitude is hurt asking to be "
                    "understood. Zuv learns to hear the hurt underneath and comes closer gently. "
                    "Final thesis: Maybe love is softness under fire."
                ),
                image_paths=[restaurant, aquarium],
                identity_image_paths=[identity],
                title="Softness Under Fire",
                output_root=Path(tmpdir) / "out",
                render_assets=False,
                today=date(2026, 5, 19),
            )

            concept = json.loads((out_dir / "concept.json").read_text(encoding="utf-8"))
            slides = json.loads((out_dir / "slides.json").read_text(encoding="utf-8"))
            copy = json.loads((out_dir / "copy.json").read_text(encoding="utf-8"))
            prompt_pack = json.loads((out_dir / "prompt-pack.json").read_text(encoding="utf-8"))
            concept_selection = json.loads((out_dir / "concept-selection.json").read_text(encoding="utf-8"))
            visual_debate = json.loads((out_dir / "visual-debate.json").read_text(encoding="utf-8"))
            visual_plan_quality = json.loads((out_dir / "visual-plan-quality.json").read_text(encoding="utf-8"))

        expected_copy = [
            "He didn't marry someone who says everything gently.",
            '"Don\'t touch me" still held his sleeve.',
            '"Be safe" came out like a warning.',
            "So he heard the hurt underneath.",
            "Maybe love is softness under fire.",
        ]
        joined = " ".join(expected_copy + [slide["visual"] for slide in slides]).lower()
        self.assertEqual(concept["content_lane"], "Golden Softness Under Fire")
        self.assertEqual([slide["copy"] for slide in slides], expected_copy)
        self.assertEqual(prompt_pack["text_overlay_plan"]["slide_copy"], expected_copy)
        self.assertEqual(concept["concept_selection"]["decision"], "GO")
        self.assertEqual(concept_selection["winner"], "Softness Under Fire")
        self.assertGreaterEqual(concept_selection["winner_score"], 28)
        self.assertGreaterEqual(len(concept_selection["candidates"]), 5)
        self.assertEqual(visual_debate["winner"], "Sharp Words, Soft Hands")
        self.assertEqual(visual_plan_quality["status"], "PASS")
        self.assertEqual(visual_plan_quality["decision"], "GO")
        self.assertIn("be safe", joined)
        self.assertIn("hurt underneath", joined)
        self.assertIn("sleeve", joined)
        self.assertIn("aachu", slides[3]["visual"].lower())
        self.assertIn("zuv", slides[3]["visual"].lower())
        self.assertIn("same", slides[3]["visual"].lower())
        self.assertIn("warning", slides[2]["visual"].lower())
        self.assertIn("brows", slides[2]["visual"].lower())
        self.assertIn("Aquarium Underwater Quiet", visual_debate["rejected_visual_patterns"])
        self.assertIn("softness under fire", copy["caption_recommended"])
        self.assertNotIn("date became a trip", joined)
        self.assertNotIn("aquarium", joined)
        self.assertNotIn("underwater", joined)
        self.assertNotIn("blue light", joined)
        self.assertNotIn("blue quiet", joined)
        self.assertNotIn("soft outline", joined)

    def test_softness_under_fire_visual_quality_rejects_losing_visual_option_leak(self):
        from pipeline.stages.codex_native_carousel import build_visual_debate, build_visual_plan_quality

        story = (
            "Aachu says be safe from the bottom of her heart, but it can sound sharp. "
            "Zuv learns to hear the hurt underneath. Maybe love is softness under fire."
        )
        slides = [
            {
                "slide": 1,
                "copy": "He didn't marry someone who says everything gently.",
                "visual": "Aachu turns away at the warm cafe table while Zuv stays close and patient.",
                "role": "universal hook",
                "emotion": "recognition",
            },
            {
                "slide": 2,
                "copy": '"Don\'t touch me" still held his sleeve.',
                "visual": "Aachu looks annoyed while holding Zuv's sleeve; he keeps his hand open nearby.",
                "role": "aachu-specific proof",
                "emotion": "contradictory softness",
            },
            {
                "slide": 3,
                "copy": '"Be safe" came out like a warning.',
                "visual": "Phone-message proof beat with a handwritten be safe note.",
                "role": "concrete proof",
                "emotion": "protective worry",
            },
            {
                "slide": 4,
                "copy": "So he heard the hurt underneath.",
                "visual": "Aquarium-blue contrast scene: Zuv alone in calm profile under blue light, hearing the hurt underneath while a soft outline of Aachu floats nearby.",
                "role": "zuv role",
                "emotion": "active understanding",
            },
            {
                "slide": 5,
                "copy": "Maybe love is softness under fire.",
                "visual": "Aachu and Zuv stand close together in warm light.",
                "role": "save/share thesis",
                "emotion": "tender acceptance",
            },
        ]

        visual_debate = build_visual_debate(story, slides, "Golden Softness Under Fire")
        quality = build_visual_plan_quality(
            story=story,
            slides=slides,
            visual_debate=visual_debate,
            lane="Golden Softness Under Fire",
        )

        joined_issues = " ".join(quality["issues"]).lower()
        self.assertEqual(quality["status"], "REPAIR")
        self.assertEqual(quality["decision"], "BLOCK_GENERATION")
        self.assertIn("aquarium", joined_issues)
        self.assertIn("losing", joined_issues)
        self.assertFalse(quality["can_generate"])

    def test_imperfect_repair_story_uses_spacious_apology_arc(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            identity = Path(tmpdir) / "aachu-zuv.jpg"
            identity.write_bytes(b"identity-image")

            out_dir = create_codex_native_carousel(
                story=(
                    "Selected concept: She Was Sorry. Bas Style Alag Tha. "
                    "Aachu does not always say sorry in perfect words. She comes back "
                    "with attitude, still angry, fixing Zuv's collar. Zuv knows not to "
                    "laugh because this is her apology language. Love learns the apology's accent. "
                    "Keep the visual system airy with one gesture, wide silence, and no crowded props."
                ),
                image_paths=[],
                identity_image_paths=[identity],
                title="She Was Sorry Bas Style Alag Tha",
                output_root=Path(tmpdir) / "out",
                render_assets=False,
                today=date(2026, 5, 19),
            )

            concept = json.loads((out_dir / "concept.json").read_text(encoding="utf-8"))
            slides = json.loads((out_dir / "slides.json").read_text(encoding="utf-8"))
            copy = json.loads((out_dir / "copy.json").read_text(encoding="utf-8"))
            prompt_pack = json.loads((out_dir / "prompt-pack.json").read_text(encoding="utf-8"))
            visual_debate = json.loads((out_dir / "visual-debate.json").read_text(encoding="utf-8"))
            concept_selection = json.loads((out_dir / "concept-selection.json").read_text(encoding="utf-8"))

        expected_copy = [
            "Some people don't say sorry.",
            "They come back with attitude.",
            "Still angry, fixing your collar.",
            "And he knows not to laugh.",
            "Love learns the apology's accent.",
        ]
        joined = " ".join(
            expected_copy
            + [slide["visual"] for slide in slides]
            + [prompt["prompt"] for prompt in prompt_pack["slides"]]
        ).lower()
        self.assertEqual(concept["content_lane"], "Golden Imperfect Repair")
        self.assertEqual([slide["copy"] for slide in slides], expected_copy)
        self.assertEqual(prompt_pack["text_overlay_plan"]["slide_copy"], expected_copy)
        self.assertEqual(visual_debate["winner"], "One Gesture, Wide Silence")
        self.assertEqual(concept_selection["winner"], "She Was Sorry. Bas Style Alag Tha.")
        self.assertEqual(concept["story_selling_decision"]["selected_concept_process_card"], "Card 06 - Delay The Confession")
        self.assertGreaterEqual(concept_selection["winner_score"], 28)
        self.assertGreaterEqual(len(concept_selection["candidates"]), 5)
        self.assertIn("collar", joined)
        self.assertIn("negative space", joined)
        self.assertIn("small hearts", joined)
        self.assertIn("reaction ticks", joined)
        self.assertIn("blush marks", joined)
        self.assertIn("no crowded props", joined)
        self.assertIn("apology's accent", copy["caption_recommended"])
        self.assertNotIn("date became a trip", joined)
        self.assertNotIn("softness under fire", joined)

    def test_main_kar_lungi_story_uses_visual_debate_gate_and_outdoor_care_arc(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            identity = Path(tmpdir) / "aachu-zuv.jpg"
            identity.write_bytes(b"identity-image")

            out_dir = create_codex_native_carousel(
                story=(
                    "Selected B concept: Main kar lungi. Translation: don't go far. "
                    "She wanted to do it herself. He helped like it was nothing. "
                    "Maybe love is care without making a scene. Use outdoor visuals, "
                    "no home interiors, no repeated rocks or red shoes."
                ),
                image_paths=[],
                identity_image_paths=[identity],
                title="Main Kar Lungi",
                output_root=Path(tmpdir) / "out",
                render_assets=False,
                today=date(2026, 5, 18),
            )

            concept = json.loads((out_dir / "concept.json").read_text(encoding="utf-8"))
            slides = json.loads((out_dir / "slides.json").read_text(encoding="utf-8"))
            prompt_pack = json.loads((out_dir / "prompt-pack.json").read_text(encoding="utf-8"))
            visual_debate = json.loads((out_dir / "visual-debate.json").read_text(encoding="utf-8"))
            manifest = json.loads((out_dir / "manifest.json").read_text(encoding="utf-8"))

        expected_copy = [
            "Main kar lungi.",
            "Translation: don't go far.",
            "She wanted to do it herself.",
            "He helped like it was nothing.",
            "Maybe love is care without making a scene.",
        ]
        joined = " ".join(expected_copy + [slide["visual"] for slide in slides]).lower()
        self.assertEqual(concept["content_lane"], "Golden Independent Care")
        self.assertEqual([slide["copy"] for slide in slides], expected_copy)
        self.assertEqual(prompt_pack["text_overlay_plan"]["slide_copy"], expected_copy)
        self.assertEqual(visual_debate["status"], "PASS")
        self.assertEqual(len(visual_debate["agents"]), 3)
        self.assertEqual(visual_debate["winner"], "Outdoor Threshold")
        self.assertIn("visual_debate", manifest["artifacts"])
        self.assertIn("visual_debate", manifest["quality_spine"]["artifacts"])
        self.assertIn("outdoor", joined)
        self.assertIn("public", joined)
        self.assertIn("traffic side", joined)
        self.assertIn("crowd", joined)
        self.assertIn("without making a scene", joined)
        self.assertNotIn("cafe", joined)
        self.assertNotIn("gate", joined)
        self.assertNotIn("bag", joined)
        self.assertNotIn("home interior", joined)
        self.assertNotIn("red shoes", joined)
        self.assertNotIn("rocks", joined)

    def test_cli_accepts_identity_only_codex_native_runs(self):
        repo_root = Path(__file__).resolve().parent.parent
        with tempfile.TemporaryDirectory() as tmpdir:
            identity_image = Path(tmpdir) / "identity.jpg"
            identity_image.write_bytes(b"identity-image")
            output_root = Path(tmpdir) / "out"
            env = os.environ.copy()
            env.pop("ANTHROPIC_API_KEY", None)

            result = subprocess.run(
                [
                    sys.executable,
                    str(repo_root / "scripts" / "create_illustration_carousel.py"),
                    "--story",
                    "Bad work day in the car, then he remembers Aachu waiting at home.",
                    "--title",
                    "CLI Identity Only",
                    "--identity-image",
                    str(identity_image),
                    "--output-root",
                    str(output_root),
                    "--no-render",
                ],
                cwd=repo_root,
                env=env,
                text=True,
                capture_output=True,
                check=False,
            )

            manifest_path = output_root / str(date.today()) / "cli-identity-only" / "manifest.json"
            manifest = json.loads(manifest_path.read_text(encoding="utf-8")) if manifest_path.exists() else {}

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(
            manifest["identity_references"],
            [{"path": str(identity_image), "role": "Aachu/Zuv face consistency reference"}],
        )
        self.assertEqual(manifest["reference_images"], [])

    def test_storyboard_prompt_pack_and_text_plan_match_slides(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            image = Path(tmpdir) / "anklet.jpg"
            image.write_bytes(b"story-image")

            out_dir = create_codex_native_carousel(
                story="Before proposing I tied her anklet. After marriage I still tie her sandals.",
                image_paths=[image],
                title="Same Posture",
                output_root=Path(tmpdir) / "out",
                render_assets=False,
                today=date(2026, 5, 16),
            )

            slides = json.loads((out_dir / "slides.json").read_text(encoding="utf-8"))
            prompts = json.loads((out_dir / "prompt-pack.json").read_text(encoding="utf-8"))
            storyboard = (out_dir / "storyboard.md").read_text(encoding="utf-8")

        slide_copy = [slide["copy"] for slide in slides]
        self.assertEqual(prompts["text_overlay_plan"]["slide_copy"], slide_copy)
        self.assertEqual([prompt["text"] for prompt in prompts["slides"]], slide_copy)
        for copy in slide_copy:
            self.assertIn(copy, storyboard)

    def test_prompts_require_model_native_publishable_art(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            image = Path(tmpdir) / "anklet.jpg"
            identity = Path(tmpdir) / "identity.jpg"
            image.write_bytes(b"story")
            identity.write_bytes(b"identity")

            out_dir = create_codex_native_carousel(
                story="Before proposing I tied her anklet. After marriage I still tie her sandals.",
                image_paths=[image],
                identity_image_paths=[identity],
                title="Integrated Typography",
                output_root=Path(tmpdir) / "out",
                render_assets=False,
                today=date(2026, 5, 16),
            )

            prompt_pack = json.loads((out_dir / "prompt-pack.json").read_text(encoding="utf-8"))

        joined = "\n".join(slide["prompt"] for slide in prompt_pack["slides"])
        self.assertEqual(
            prompt_pack["text_overlay_plan"]["composition_role"],
            "publishable_final_illustration_with_text",
        )
        self.assertTrue(
            all(slide["generation_mode"] == "model_native_publishable" for slide in prompt_pack["slides"])
        )
        self.assertIn("Generate the complete publishable social slide artwork", joined)
        self.assertIn("Render this exact handwritten-style text inside the artwork", joined)
        self.assertIn("house-style illustrated scene consistency", joined)
        self.assertIn("illustrated scene", joined)
        self.assertIn("@a.storyof.two", joined)
        self.assertIn(str(identity), joined)
        self.assertIn("output/carousels/2026-05-19/main-kar-lungi/final/slide-01.png", joined)
        self.assertIn("output/carousels/2026-05-19/love-carries-the-heavier-half/final/slide-03.png", joined)
        self.assertIn("output/carousels/2026-05-16/he-learned-her-subtitles/final/slide-02.png", joined)
        self.assertNotIn("/Users/himanshusharma/Downloads", joined)
        self.assertNotIn("caricature faces", joined.lower())
        self.assertNotIn("illustrated poster", joined.lower())
        self.assertNotIn("Reserve intentional whitespace", joined)
        self.assertNotIn("clean art", joined.lower())
        self.assertNotIn("text applied locally", joined.lower())
        self.assertNotIn("No text inside the artwork", joined)

    def test_codex_handoff_blocks_artifact_prompt_style_drift(self):
        from pipeline.stages.codex_builtin_image_generation import prepare_codex_builtin_image_generation

        with tempfile.TemporaryDirectory() as tmpdir:
            carousel_dir = Path(tmpdir) / "jo-tu-kahegi"
            carousel_dir.mkdir()
            identity = carousel_dir / "identity.jpg"
            contact_sheet = carousel_dir / "identity-face-contact-sheet.jpg"
            identity.write_bytes(b"identity")
            contact_sheet.write_bytes(b"contact-sheet")

            (carousel_dir / "visual-plan-quality.json").write_text(
                json.dumps({"status": "PASS", "can_generate": True, "issues": []}),
                encoding="utf-8",
            )
            (carousel_dir / "identity-consistency-review.json").write_text(
                json.dumps({"status": "PASS"}),
                encoding="utf-8",
            )
            (carousel_dir / "slides.json").write_text(
                json.dumps(
                    [
                        {
                            "slide": 1,
                            "copy": 'Me with my "jo tu kahegi wahi hoga"',
                            "visual": "A drawn low-fi night-photo poster artifact on warm paper.",
                        }
                    ]
                ),
                encoding="utf-8",
            )
            (carousel_dir / "prompt-pack.json").write_text(
                json.dumps(
                    {
                        "shared_style_prompt": "soft hand-drawn desi storybook illustration",
                        "shared_negative_prompt": "No photorealism, no 3D, no stock, no quote-card.",
                        "identity_dossier_reference_images": [str(contact_sheet)],
                        "identity_reference_images": [str(identity)],
                        "slides": [
                            {
                                "slide": 1,
                                "text": 'Me with my "jo tu kahegi wahi hoga"',
                                "prompt": (
                                    "Use case: illustrated relationship artifact. "
                                    "Create a drawn low-fi night-photo poster artifact on warm paper, "
                                    "not a full @a.storyof.two illustrated couple scene."
                                ),
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )

            result = prepare_codex_builtin_image_generation(carousel_dir)

        self.assertEqual(result["status"], "blocked")
        self.assertIn("house-style illustrated scene", result["reason"])
        self.assertIn("low-fi night-photo poster", result["reason"])

    def test_style_consistency_allows_negated_artifact_terms(self):
        from pipeline.stages.carousel_style_consistency import prompt_style_drift_issues

        issues = prompt_style_drift_issues(
            {
                "slides": [
                    {
                        "slide": 1,
                        "prompt": (
                            "Create a lived Aachu/Zuv scene. The main image must be the couple's "
                            "body language, not a paper object, receipt, tiny museum label, "
                            "phrase exhibit on warm paper, or stationery surface."
                        ),
                    }
                ]
            }
        )

        self.assertEqual(issues, [])

    def test_package_generated_carousel_packages_two_native_formats(self):
        from scripts.package_generated_carousel import package_generated_images

        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = Path(tmpdir)
            out_dir = workspace / "output" / "carousels" / "2026-05-16" / "same-posture"
            source_dir = workspace / "generated"
            out_dir.mkdir(parents=True)
            source_dir.mkdir()
            slides = [{"slide": number, "copy": f"Slide {number}"} for number in range(1, 6)]
            (out_dir / "slides.json").write_text(json.dumps(slides), encoding="utf-8")
            prompt_pack = {
                "slides": [
                    {
                        "slide": number,
                        "text": f"Slide {number}",
                        "prompt": f"Prompt for slide {number}",
                    }
                    for number in range(1, 6)
                ]
            }
            (out_dir / "prompt-pack.json").write_text(json.dumps(prompt_pack), encoding="utf-8")
            (out_dir / "identity-consistency-review.json").write_text(
                json.dumps({"status": "PASS"}),
                encoding="utf-8",
            )
            (out_dir / "visual-plan-quality.json").write_text(
                json.dumps({"status": "PASS", "can_generate": True, "issues": []}),
                encoding="utf-8",
            )
            for number in range(1, 6):
                (source_dir / f"instagram-{number}.png").write_bytes(self.png_bytes(1080, 1350, value=240))
                (source_dir / f"reels-stories-{number}.png").write_bytes(self.png_bytes(1080, 1920, value=230))

            manifest = package_generated_images(
                carousel_dir=out_dir,
                instagram_post_paths=[source_dir / f"instagram-{number}.png" for number in range(1, 6)],
                reels_stories_paths=[source_dir / f"reels-stories-{number}.png" for number in range(1, 6)],
            )
            slide_01_exists = (out_dir / "final" / "slide-01.png").exists()
            slide_05_exists = (out_dir / "final" / "slide-05.png").exists()
            reels_slide_01_exists = (out_dir / "final-reels-stories" / "slide-01.png").exists()
            reels_slide_05_exists = (out_dir / "final-reels-stories" / "slide-05.png").exists()

        self.assertEqual(manifest["status"], "generated")
        self.assertEqual(len(manifest["slides"]), 5)
        self.assertIn("native_output_contract", manifest)
        self.assertTrue(slide_01_exists)
        self.assertTrue(slide_05_exists)
        self.assertTrue(reels_slide_01_exists)
        self.assertTrue(reels_slide_05_exists)
        self.assertIn("native_outputs", manifest["slides"][0])

    def test_package_generated_carousel_rejects_local_native_renderer_sources(self):
        from scripts.package_generated_carousel import package_generated_images

        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = Path(tmpdir)
            out_dir = workspace / "output" / "carousels" / "2026-05-19" / "not-hungry"
            source_dir = out_dir / "tmp-generated" / "local-native"
            out_dir.mkdir(parents=True)
            source_dir.mkdir(parents=True)
            (out_dir / "slides.json").write_text(
                json.dumps([{"slide": number, "copy": f"Slide {number}"} for number in range(1, 6)]),
                encoding="utf-8",
            )
            (out_dir / "prompt-pack.json").write_text(
                json.dumps(
                    {
                        "slides": [
                            {"slide": number, "text": f"Slide {number}", "prompt": f"Prompt {number}"}
                            for number in range(1, 6)
                        ]
                    }
                ),
                encoding="utf-8",
            )
            (out_dir / "identity-consistency-review.json").write_text(
                json.dumps({"status": "PASS"}),
                encoding="utf-8",
            )
            for number in range(1, 6):
                (source_dir / f"instagram-{number}.png").write_bytes(self.png_bytes(1080, 1350, value=240))
                (source_dir / f"reels-{number}.png").write_bytes(self.png_bytes(1080, 1920, value=230))

            with self.assertRaises(ValueError) as error:
                package_generated_images(
                    carousel_dir=out_dir,
                    instagram_post_paths=[source_dir / f"instagram-{number}.png" for number in range(1, 6)],
                    reels_stories_paths=[source_dir / f"reels-{number}.png" for number in range(1, 6)],
                )

        self.assertIn("local-native", str(error.exception))

    def test_overlay_manifest_preserves_slide_copy(self):
        from scripts.render_carousel_text_overlays import build_overlay_manifest

        slides = [
            {"slide": 1, "copy": "Before the ring, there was an anklet."},
            {"slide": 2, "copy": "He thought he was tying jewellery."},
        ]

        manifest = build_overlay_manifest(slides)

        self.assertEqual(manifest["typography"]["strategy"], "legacy_local_overlay")
        self.assertEqual(manifest["composition_role"], "publishable_final_illustration_with_text")
        self.assertEqual(manifest["slides"][0]["text"], "Before the ring, there was an anklet.")
        self.assertEqual(
            manifest["slides"][0]["composition_role"],
            "final_illustration_with_integrated_typography",
        )
        self.assertEqual(manifest["slides"][1]["brandmark"], "@a.storyof.two")

    def test_overlay_manifest_records_storybook_typography_rules(self):
        from scripts.render_carousel_text_overlays import build_overlay_manifest

        manifest = build_overlay_manifest(
            [
                {
                    "slide": 1,
                    "copy": "He didn't marry peace.",
                    "text_layout": {
                        "primary_position": "bottom_center",
                        "speech_bubble": "mujhe kuch\nnahi hua",
                    },
                }
            ]
        )

        renderer = manifest["renderer"]
        self.assertEqual(renderer["font_role"], "hand_drawn_storybook")
        self.assertEqual(renderer["panel_style"], "no_quote_card_panel")
        self.assertEqual(renderer["brandmark_style"], "subtle_but_readable")
        self.assertIn("reference-style", renderer["placement"])
        self.assertEqual(manifest["slides"][0]["text_layout"]["primary_position"], "bottom_center")
        self.assertIn("mujhe kuch", manifest["slides"][0]["text_layout"]["speech_bubble"])

    def test_render_overlays_fails_when_final_images_are_missing(self):
        from scripts.render_carousel_text_overlays import render_overlays

        with tempfile.TemporaryDirectory() as tmpdir:
            out_dir = Path(tmpdir)
            slides = [
                {"slide": 1, "copy": "Before the ring, there was an anklet."},
                {"slide": 2, "copy": "He thought he was tying jewellery."},
            ]
            (out_dir / "slides.json").write_text(json.dumps(slides), encoding="utf-8")

            with self.assertRaises(FileNotFoundError) as raised:
                render_overlays(out_dir)

        self.assertIn("Missing final images for overlay", str(raised.exception))

    def test_final_audit_fails_when_final_images_are_missing(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            image = Path(tmpdir) / "anklet.jpg"
            image.write_bytes(b"story-image")

            out_dir = create_codex_native_carousel(
                story="Before proposing I tied her anklet. After marriage I still tie her sandals.",
                image_paths=[image],
                title="Same Posture",
                output_root=Path(tmpdir) / "out",
                render_assets=False,
                today=date(2026, 5, 16),
            )

            final_audit = json.loads((out_dir / "final-audit.json").read_text(encoding="utf-8"))

        self.assertEqual(final_audit["status"], "NEEDS_FIXES")
        self.assertIn("REQ-FINAL-IMAGES-001", final_audit["requirements"])
        self.assertFalse(final_audit["requirements"]["REQ-FINAL-IMAGES-001"]["pass"])

    def test_asset_reviewer_accepts_model_native_generated_status(self):
        from pipeline.stages.carousel_quality import QualityContext, build_run_ledger, build_stage_reviews

        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = Path(tmpdir)
            image = workspace / "identity.jpg"
            image.write_bytes(b"story-image")
            out_dir = create_codex_native_carousel(
                story="Every trip has one bas ek photo aur person. Zuv says haan baba.",
                image_paths=[image],
                title="Generated Assets",
                output_root=workspace / "out",
                render_assets=False,
                today=date(2026, 5, 16),
            )
            final_dir = out_dir / "final"
            final_dir.mkdir()
            for number in range(1, 6):
                (final_dir / f"slide-{number:02d}.png").write_bytes(b"fake-png")

            manifest = json.loads((out_dir / "manifest.json").read_text(encoding="utf-8"))
            package = {
                "concept": json.loads((out_dir / "concept.json").read_text(encoding="utf-8")),
                "slides": json.loads((out_dir / "slides.json").read_text(encoding="utf-8")),
                "prompt_pack": json.loads((out_dir / "prompt-pack.json").read_text(encoding="utf-8")),
                "copy": json.loads((out_dir / "copy.json").read_text(encoding="utf-8")),
            }
            context = QualityContext(
                story=manifest["source_story"],
                title=manifest["title"],
                slug=manifest["slug"],
                today=date(2026, 5, 16),
                out_dir=out_dir,
                image_paths=[image],
                slide_count=5,
                package=package,
                manifest=manifest,
                render_result={"status": "generated", "generation_mode": "model_native_publishable"},
                workspace_root=workspace,
            )
            ledger = build_run_ledger(context)
            stage_reviews = build_stage_reviews(context, ledger)

        asset_review = stage_reviews["reviews"]["asset_reviewer"]
        self.assertNotEqual(asset_review["status"], "NEEDS_FIXES")
        self.assertNotIn("Unexpected render status", " ".join(asset_review["issues"]))

    def test_final_audit_fails_without_local_overlays_and_checked_visual_qa(self):
        from pipeline.stages.carousel_quality import (
            QualityContext,
            build_final_audit,
            build_run_ledger,
            build_stage_reviews,
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = Path(tmpdir)
            image = workspace / "anklet.jpg"
            identity = workspace / "identity.jpg"
            image.write_bytes(b"story-image")
            identity.write_bytes(b"identity-image")
            out_dir = create_codex_native_carousel(
                story="Before proposing I tied her anklet. After marriage I still tie her sandals.",
                image_paths=[image],
                identity_image_paths=[identity],
                title="Needs Overlay QA",
                output_root=workspace / "out",
                render_assets=False,
                today=date(2026, 5, 16),
            )
            final_dir = out_dir / "final"
            final_dir.mkdir()
            for number in range(1, 6):
                (final_dir / f"slide-{number:02d}.png").write_bytes(b"fake-png")

            manifest = json.loads((out_dir / "manifest.json").read_text(encoding="utf-8"))
            package = {
                "concept": json.loads((out_dir / "concept.json").read_text(encoding="utf-8")),
                "slides": json.loads((out_dir / "slides.json").read_text(encoding="utf-8")),
                "prompt_pack": json.loads((out_dir / "prompt-pack.json").read_text(encoding="utf-8")),
                "copy": json.loads((out_dir / "copy.json").read_text(encoding="utf-8")),
            }
            context = QualityContext(
                story=manifest["source_story"],
                title=manifest["title"],
                slug=manifest["slug"],
                today=date(2026, 5, 16),
                out_dir=out_dir,
                image_paths=[image],
                slide_count=5,
                package=package,
                manifest=manifest,
                render_result={"status": "skipped", "reason": "test"},
                workspace_root=workspace,
            )
            ledger = build_run_ledger(context)
            stage_reviews = build_stage_reviews(context, ledger)
            audit = build_final_audit(context, ledger, stage_reviews)

        self.assertFalse(audit["requirements"]["REQ-FINAL-IMAGES-001"]["pass"])
        self.assertFalse(audit["requirements"]["REQ-MODEL-NATIVE-TEXT-001"]["pass"])
        self.assertFalse(audit["requirements"]["REQ-VISUAL-QA-001"]["pass"])
        self.assertEqual(audit["status"], "NEEDS_FIXES")

    def test_final_audit_rejects_local_overlay_for_model_native_default(self):
        from pipeline.stages.carousel_quality import (
            QualityContext,
            build_final_audit,
            build_run_ledger,
            build_stage_reviews,
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = Path(tmpdir)
            image = workspace / "identity.jpg"
            image.write_bytes(b"story-image")
            out_dir = create_codex_native_carousel(
                story="He did not marry peace. He married Aachu chaos.",
                image_paths=[image],
                title="Typography Gate",
                output_root=workspace / "out",
                render_assets=False,
                today=date(2026, 5, 16),
            )
            for folder in ["final", "final-with-text"]:
                (out_dir / folder).mkdir(exist_ok=True)
                for number in range(1, 6):
                    (out_dir / folder / f"slide-{number:02d}.png").write_bytes(b"fake-png")
            (out_dir / "text-overlay.json").write_text(
                json.dumps({"status": "rendered", "slides": []}),
                encoding="utf-8",
            )

            manifest = json.loads((out_dir / "manifest.json").read_text(encoding="utf-8"))
            package = {
                "concept": json.loads((out_dir / "concept.json").read_text(encoding="utf-8")),
                "slides": json.loads((out_dir / "slides.json").read_text(encoding="utf-8")),
                "prompt_pack": json.loads((out_dir / "prompt-pack.json").read_text(encoding="utf-8")),
                "copy": json.loads((out_dir / "copy.json").read_text(encoding="utf-8")),
            }
            context = QualityContext(
                story=manifest["source_story"],
                title=manifest["title"],
                slug=manifest["slug"],
                today=date(2026, 5, 16),
                out_dir=out_dir,
                image_paths=[image],
                slide_count=5,
                package=package,
                manifest=manifest,
                render_result={"status": "skipped", "reason": "test"},
                workspace_root=workspace,
            )
            ledger = build_run_ledger(context)
            stage_reviews = build_stage_reviews(context, ledger)
            audit = build_final_audit(context, ledger, stage_reviews)

        self.assertFalse(audit["requirements"]["REQ-MODEL-NATIVE-TEXT-001"]["pass"])
        self.assertIn(
            "final-with-text",
            " ".join(audit["requirements"]["REQ-MODEL-NATIVE-TEXT-001"]["evidence"]["issues"]),
        )

    def test_model_native_generation_prepares_codex_image_tool_handoff_without_api_key(self):
        from pipeline.stages.model_native_image_generation import generate_model_native_images

        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = Path(tmpdir)
            image = workspace / "identity.jpg"
            image.write_bytes(b"story-image")
            out_dir = create_codex_native_carousel(
                story="He did not marry peace. He married Aachu chaos.",
                image_paths=[image],
                identity_image_paths=[image],
                title="Missing Key",
                output_root=workspace / "out",
                render_assets=False,
                today=date(2026, 5, 16),
            )

            result = generate_model_native_images(out_dir)
            manifest = json.loads((out_dir / "final-images.json").read_text(encoding="utf-8"))
            blocker_text = (out_dir / "image-generation-blocker.md").read_text(encoding="utf-8")
            slide_01_exists = (out_dir / "final" / "slide-01.png").exists()
            reels_slide_01_exists = (out_dir / "final-reels-stories" / "slide-01.png").exists()

        self.assertEqual(result["status"], "handoff_ready")
        self.assertEqual(manifest["status"], "handoff_ready")
        self.assertFalse(result["done"])
        self.assertFalse(result["publishable"])
        self.assertTrue(result["requires_human_generation"])
        self.assertFalse(slide_01_exists)
        self.assertFalse(reels_slide_01_exists)
        self.assertIn("Codex image tool", blocker_text)
        self.assertNotIn("OPENAI_API_KEY", blocker_text)
        self.assertNotIn("API key", blocker_text)

    def test_model_native_generation_has_no_api_client_parameters(self):
        import inspect

        from pipeline.stages.model_native_image_generation import generate_model_native_images

        parameters = inspect.signature(generate_model_native_images).parameters

        self.assertNotIn("api_key", parameters)
        self.assertNotIn("client", parameters)
        self.assertNotIn("model", parameters)
        self.assertNotIn("size", parameters)

    def test_model_native_generation_uses_pre_generation_gates_before_handoff(self):
        from pipeline.stages.model_native_image_generation import generate_model_native_images

        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = Path(tmpdir)
            image = workspace / "identity.jpg"
            image.write_bytes(b"story-image")
            out_dir = create_codex_native_carousel(
                story="He did not marry peace. He married Aachu chaos.",
                image_paths=[image],
                identity_image_paths=[image],
                title="Identity Gate Block",
                output_root=workspace / "out",
                render_assets=False,
                today=date(2026, 5, 16),
            )
            (out_dir / "identity-consistency-review.json").write_text(
                json.dumps(
                    {
                        "agent": "C3.5-IdentityConsistency",
                        "status": "NEEDS_FIXES",
                        "issues": ["generic faces risk"],
                        "slides": [],
                    }
                ),
                encoding="utf-8",
            )

            result = generate_model_native_images(out_dir)

        self.assertEqual(result["status"], "blocked")
        self.assertIn("identity-consistency-review.json", result["reason"])

    def test_cli_rejects_legacy_api_image_backend_even_without_generation(self):
        repo_root = Path(__file__).resolve().parent.parent
        with tempfile.TemporaryDirectory() as tmpdir:
            identity = Path(tmpdir) / "identity.jpg"
            identity.write_bytes(b"identity-image")
            legacy_backend = "open" + "ai"

            result = subprocess.run(
                [
                    sys.executable,
                    str(repo_root / "scripts" / "create_illustration_carousel.py"),
                    "--story",
                    "He did not marry peace. He married Aachu chaos.",
                    "--title",
                    "Reject Legacy Backend",
                    "--identity-image",
                    str(identity),
                    "--output-root",
                    str(Path(tmpdir) / "out"),
                    "--image-backend",
                    legacy_backend,
                    "--no-render",
                ],
                cwd=repo_root,
                text=True,
                capture_output=True,
                check=False,
            )

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("invalid choice", result.stderr)

    def test_cli_help_describes_codex_image_tool_without_api_key_path(self):
        repo_root = Path(__file__).resolve().parent.parent

        result = subprocess.run(
            [
                sys.executable,
                str(repo_root / "scripts" / "create_illustration_carousel.py"),
                "--help",
            ],
            cwd=repo_root,
            text=True,
            capture_output=True,
            check=False,
        )

        self.assertEqual(result.returncode, 0)
        self.assertIn("Codex image tool", result.stdout)
        self.assertNotIn("API key", result.stdout)
        self.assertNotIn("OpenAI", result.stdout)

    def test_cli_rejects_local_dry_run_with_handoff_flags(self):
        repo_root = Path(__file__).resolve().parent.parent
        with tempfile.TemporaryDirectory() as tmpdir:
            identity = Path(tmpdir) / "identity.jpg"
            identity.write_bytes(b"identity-image")

            result = subprocess.run(
                [
                    sys.executable,
                    str(repo_root / "scripts" / "create_illustration_carousel.py"),
                    "--story",
                    "He did not marry peace. He married Aachu chaos.",
                    "--title",
                    "Reject Dry Run Handoff Flags",
                    "--identity-image",
                    str(identity),
                    "--output-root",
                    str(Path(tmpdir) / "out"),
                    "--image-backend",
                    "local-dry-run",
                    "--prepare-image-handoff",
                    "--no-render",
                ],
                cwd=repo_root,
                text=True,
                capture_output=True,
                check=False,
            )

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("local-dry-run cannot be combined", result.stderr)

    def test_model_native_reference_selection_uses_curated_identity_bundle_and_style_refs(self):
        from pipeline.stages.model_native_image_generation import existing_reference_paths

        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = Path(tmpdir)
            identity_paths = [workspace / f"identity-{index:02d}.jpg" for index in range(18)]
            style_paths = [workspace / f"style-{index:02d}.png" for index in range(3)]
            for path in [*identity_paths, *style_paths]:
                path.write_bytes(b"image")

            selected = existing_reference_paths(
                {
                    "style_reference_images": [str(path) for path in style_paths],
                    "identity_reference_images": [str(path) for path in identity_paths],
                }
            )

        self.assertEqual(len(selected), 6)
        self.assertEqual(selected[:4], identity_paths[:4])
        self.assertEqual(selected[-2:], style_paths[:2])

    def test_codex_builtin_handoff_writes_identity_reference_prompt_files(self):
        from pipeline.stages.codex_builtin_image_generation import prepare_codex_builtin_image_generation

        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = Path(tmpdir)
            (workspace / "AGENTS.md").write_text("test workspace marker\n", encoding="utf-8")
            story_image = workspace / "balcony.jpg"
            identity = workspace / "aachu-zuv.jpg"
            story_image.write_bytes(b"story-image")
            identity.write_bytes(b"identity-image")
            out_dir = create_codex_native_carousel(
                story=(
                    "Selected concept from the Golden Theme tournament: She Was Not High-Maintenance. "
                    "Aachu is in a green dress, barefoot, and Zuv notices before she asks."
                ),
                image_paths=[story_image],
                identity_image_paths=[identity],
                title="Codex Builtin Handoff",
                output_root=workspace / "out",
                render_assets=False,
                today=date(2026, 5, 18),
            )
            prompt_pack = json.loads((out_dir / "prompt-pack.json").read_text(encoding="utf-8"))
            for slide_prompt in prompt_pack["slides"]:
                slide_prompt["prompt"] = (
                    "Use case: illustrated relationship scene. "
                    f"Identity reference images: ['{identity}']. "
                    f"Story reference images: ['{story_image}']. "
                    "Face identity contract: preserve Aachu and Zuv from the attached references. "
                    "Create a soft desi storybook full-scene illustration on warm paper. "
                    "Aachu is fully alive and Zuv notices before she asks. "
                    "Render this exact handwritten-style text inside the artwork: She was not high-maintenance. "
                    "Add tiny @a.storyof.two brandmark bottom-right."
                )
            prompt_pack["proof_gate"] = "Generate Slide 1 Instagram post proof first."
            (out_dir / "prompt-pack.json").write_text(json.dumps(prompt_pack), encoding="utf-8")

            result = prepare_codex_builtin_image_generation(out_dir)
            manifest = json.loads((out_dir / "final-images.json").read_text(encoding="utf-8"))
            instagram_prompt_path = out_dir / "codex-image-prompts" / "instagram-post" / "slide-01.md"
            reels_stories_prompt_path = out_dir / "codex-image-prompts" / "reels-stories" / "slide-01.md"
            instagram_generator_prompt_path = (
                out_dir / "codex-image-prompts" / "instagram-post" / "slide-01.prompt.txt"
            )
            reels_stories_generator_prompt_path = (
                out_dir / "codex-image-prompts" / "reels-stories" / "slide-01.prompt.txt"
            )
            instagram_prompt_text = instagram_prompt_path.read_text(encoding="utf-8")
            reels_stories_prompt_text = reels_stories_prompt_path.read_text(encoding="utf-8")
            instagram_generator_prompt_text = instagram_generator_prompt_path.read_text(encoding="utf-8")
            reels_stories_generator_prompt_text = reels_stories_generator_prompt_path.read_text(encoding="utf-8")
            blocker_path = out_dir / "image-generation-blocker.md"
            blocker_text = blocker_path.read_text(encoding="utf-8") if blocker_path.exists() else ""

        self.assertEqual(result["status"], "handoff_ready")
        self.assertEqual(manifest["backend"], "codex_builtin")
        self.assertEqual(manifest["generation_mode"], "model_native_publishable")
        self.assertEqual(manifest["slides"][0]["status"], "awaiting_codex_builtin_image")
        self.assertEqual(
            manifest["slides"][0]["prompt_files"],
            {
                "instagram_post": str(instagram_prompt_path),
                "reels_stories": str(reels_stories_prompt_path),
            },
        )
        self.assertEqual(
            manifest["slides"][0]["generator_prompt_files"],
            {
                "instagram_post": str(instagram_generator_prompt_path),
                "reels_stories": str(reels_stories_generator_prompt_path),
            },
        )
        self.assertIn("Native output format: Instagram post", instagram_prompt_text)
        self.assertIn("Native output format: Reels/Stories", reels_stories_prompt_text)
        self.assertIn(str(instagram_generator_prompt_path), instagram_prompt_text)
        self.assertIn("exact 4:5 canvas", instagram_generator_prompt_text)
        self.assertIn("not a 9:16 story canvas", instagram_generator_prompt_text)
        self.assertIn("exact 9:16 canvas", reels_stories_generator_prompt_text)
        self.assertIn("not a 4:5 carousel canvas", reels_stories_generator_prompt_text)
        self.assertNotIn("Save packaged final", instagram_generator_prompt_text)
        self.assertNotIn("Source provenance", instagram_generator_prompt_text)
        self.assertNotIn("Required final file", instagram_generator_prompt_text)
        self.assertNotIn("identity-generation-preflight.md", instagram_generator_prompt_text)
        self.assertNotIn(str(identity), instagram_generator_prompt_text)
        self.assertNotIn(str(story_image), instagram_generator_prompt_text)
        self.assertIn("final/slide-01.png", instagram_prompt_text)
        self.assertIn("final-reels-stories/slide-01.png", reels_stories_prompt_text)
        self.assertIn(str(identity), instagram_prompt_text)
        self.assertIn(str(story_image), instagram_prompt_text)
        self.assertIn("identity-face-contact-sheet.jpg", instagram_prompt_text)
        self.assertIn("identity-generation-preflight.md", instagram_prompt_text)
        self.assertIn("Face identity contract", instagram_prompt_text)
        self.assertIn("actual image inputs", instagram_prompt_text)
        self.assertIn("She was not high-maintenance.", instagram_prompt_text)
        self.assertIn("Final PNGs are pending Codex image tool generation", blocker_text)
        self.assertIn("slide 01", blocker_text)
        self.assertIn(str(instagram_generator_prompt_path), blocker_text)

    def test_codex_builtin_handoff_compiles_fresh_package_prompt_files(self):
        from pipeline.stages.carousel_prompt_compiler import MAX_PROMPT_CHARS
        from pipeline.stages.codex_builtin_image_generation import prepare_codex_builtin_image_generation

        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = Path(tmpdir)
            identity = workspace / "aachu-zuv.png"
            identity.write_bytes(b"identity-image")

            out_dir = create_codex_native_carousel(
                story=(
                    "Selected concept from the Golden Theme tournament: She Was Not High-Maintenance. "
                    "Aachu is in a green dress, barefoot, and Zuv notices before she asks."
                ),
                image_paths=[],
                identity_image_paths=[identity],
                title="Fresh Compact Handoff",
                output_root=workspace / "out",
                render_assets=False,
                today=date(2026, 5, 24),
            )

            result = prepare_codex_builtin_image_generation(out_dir)
            prompt_files = sorted((out_dir / "codex-image-prompts").glob("*/*.prompt.txt"))
            prompt_texts = [path.read_text(encoding="utf-8") for path in prompt_files]

        self.assertEqual(result["status"], "handoff_ready")
        self.assertEqual(len(prompt_files), DEFAULT_SLIDE_COUNT * 2)
        self.assertTrue(prompt_texts)
        self.assertTrue(all(len(text) <= MAX_PROMPT_CHARS for text in prompt_texts))

    def test_prepare_codex_handoff_can_write_single_proof_prompt(self):
        from pipeline.stages.codex_builtin_image_generation import prepare_codex_builtin_image_generation

        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = Path(tmpdir)
            identity = workspace / "aachu-zuv.png"
            identity.write_bytes(b"identity-image")

            out_dir = create_codex_native_carousel(
                story=(
                    "Selected concept from the Golden Theme tournament: She Was Not High-Maintenance. "
                    "Aachu is in a green dress, barefoot, and Zuv notices before she asks."
                ),
                image_paths=[],
                identity_image_paths=[identity],
                title="Single Proof Prompt",
                output_root=workspace / "out",
                render_assets=False,
                today=date(2026, 5, 24),
            )

            prepare_codex_builtin_image_generation(out_dir)
            result = prepare_codex_builtin_image_generation(
                out_dir,
                proof_slide=4,
                formats=["instagram_post"],
            )
            prompt_files = sorted(
                path.relative_to(out_dir / "codex-image-prompts").as_posix()
                for path in (out_dir / "codex-image-prompts").glob("**/*")
                if path.is_file()
            )
            blocker_text = (out_dir / "image-generation-blocker.md").read_text(encoding="utf-8")

        self.assertEqual(result["status"], "handoff_ready")
        self.assertEqual(result["requested_proof_slide"], 4)
        self.assertEqual(result["requested_formats"], ["instagram_post"])
        self.assertEqual(len(result["slides"]), 1)
        self.assertEqual(result["slides"][0]["slide"], 4)
        self.assertIn("instagram_post", result["slides"][0]["prompt_files"])
        self.assertNotIn("reels_stories", result["slides"][0]["prompt_files"])
        self.assertEqual(
            prompt_files,
            [
                "instagram-post/slide-04.md",
                "instagram-post/slide-04.prompt.txt",
            ],
        )
        self.assertIn("Instagram post prompts:", blocker_text)
        self.assertIn("codex-image-prompts/instagram-post", blocker_text)
        self.assertNotIn("Reels/Stories prompts:", blocker_text)
        self.assertNotIn("codex-image-prompts/reels-stories", blocker_text)
        self.assertIn("final/slide-01.png` through `slide-05.png", blocker_text)
        self.assertIn("final-reels-stories/slide-01.png` through `slide-05.png", blocker_text)
        self.assertIn("slide 04", blocker_text)
        self.assertIn("instagram-post/slide-04.prompt.txt", blocker_text)

    def test_prepare_codex_handoff_blocker_uses_reels_proof_prompt(self):
        from pipeline.stages.codex_builtin_image_generation import prepare_codex_builtin_image_generation

        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = Path(tmpdir)
            identity = workspace / "aachu-zuv.png"
            identity.write_bytes(b"identity-image")

            out_dir = create_codex_native_carousel(
                story=(
                    "Selected concept from the Golden Theme tournament: She Was Not High-Maintenance. "
                    "Aachu is in a green dress, barefoot, and Zuv notices before she asks."
                ),
                image_paths=[],
                identity_image_paths=[identity],
                title="Reels Proof Prompt",
                output_root=workspace / "out",
                render_assets=False,
                today=date(2026, 5, 24),
            )

            result = prepare_codex_builtin_image_generation(
                out_dir,
                proof_slide=3,
                formats=["reels_stories"],
            )
            blocker_text = (out_dir / "image-generation-blocker.md").read_text(encoding="utf-8")

        self.assertEqual(result["requested_proof_slide"], 3)
        self.assertEqual(result["requested_formats"], ["reels_stories"])
        self.assertIn("Reels/Stories prompts:", blocker_text)
        self.assertNotIn("Instagram post prompts:", blocker_text)
        self.assertIn("reels-stories/slide-03.prompt.txt", blocker_text)
        self.assertNotIn("instagram-post/slide-03.prompt.txt", blocker_text)

    def test_prepare_codex_handoff_clears_stale_prompts_when_later_run_blocks(self):
        from pipeline.stages.codex_builtin_image_generation import prepare_codex_builtin_image_generation

        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = Path(tmpdir)
            identity = workspace / "aachu-zuv.png"
            identity.write_bytes(b"identity-image")

            out_dir = create_codex_native_carousel(
                story=(
                    "Selected concept from the Golden Theme tournament: She Was Not High-Maintenance. "
                    "Aachu is in a green dress, barefoot, and Zuv notices before she asks."
                ),
                image_paths=[],
                identity_image_paths=[identity],
                title="Blocked Stale Prompt Cleanup",
                output_root=workspace / "out",
                render_assets=False,
                today=date(2026, 5, 24),
            )

            prepare_codex_builtin_image_generation(out_dir)
            initial_prompt_files = sorted((out_dir / "codex-image-prompts").glob("**/*.prompt.txt"))
            (out_dir / "visual-plan-quality.json").unlink()
            result = prepare_codex_builtin_image_generation(out_dir)
            stale_prompt_files = sorted((out_dir / "codex-image-prompts").glob("**/*"))

        self.assertTrue(initial_prompt_files)
        self.assertIn(result["status"], {"BLOCKED", "blocked"})
        self.assertFalse(result["done"])
        self.assertFalse(result["publishable"])
        self.assertEqual(stale_prompt_files, [])

    def test_codex_builtin_handoff_blocks_missing_visual_plan_quality_gate(self):
        from pipeline.stages.codex_builtin_image_generation import prepare_codex_builtin_image_generation

        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = Path(tmpdir)
            story_image = workspace / "balcony.jpg"
            identity = workspace / "aachu-zuv.jpg"
            story_image.write_bytes(b"story-image")
            identity.write_bytes(b"identity-image")
            out_dir = create_codex_native_carousel(
                story=(
                    "Selected concept from the Golden Theme tournament: She Was Not High-Maintenance. "
                    "Aachu is in a green dress, barefoot, and Zuv notices before she asks."
                ),
                image_paths=[story_image],
                identity_image_paths=[identity],
                title="Missing Visual Screen",
                output_root=workspace / "out",
                render_assets=False,
                today=date(2026, 5, 19),
            )
            (out_dir / "visual-plan-quality.json").unlink()

            result = prepare_codex_builtin_image_generation(out_dir)
            manifest = json.loads((out_dir / "final-images.json").read_text(encoding="utf-8"))

        self.assertEqual(result["status"], "blocked")
        self.assertEqual(manifest["status"], "blocked")
        self.assertFalse(result["done"])
        self.assertFalse(result["publishable"])
        self.assertFalse(result["requires_human_generation"])
        self.assertEqual(result["slide_count"], 5)
        self.assertEqual(result["slides"], [])
        self.assertIn("visual-plan-quality.json", result["reason"])
        self.assertIn("pre-generation", result["reason"])

    def test_cli_generate_images_defaults_to_codex_builtin_handoff(self):
        repo_root = Path(__file__).resolve().parent.parent
        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = Path(tmpdir)
            story_image = workspace / "balcony.jpg"
            identity = workspace / "aachu-zuv.jpg"
            story_image.write_bytes(b"story-image")
            identity.write_bytes(b"identity-image")
            story_file = workspace / "story.txt"
            story_file.write_text(
                "Selected concept from the Golden Theme tournament: She Was Not High-Maintenance. "
                "Aachu is in a green dress, barefoot, and Zuv notices before she asks.",
                encoding="utf-8",
            )
            output_root = workspace / "out"
            result = subprocess.run(
                [
                    sys.executable,
                    str(repo_root / "scripts" / "create_illustration_carousel.py"),
                    "--story-file",
                    str(story_file),
                    "--title",
                    "CLI Codex Builtin",
                    "--image",
                    str(story_image),
                    "--identity-image",
                    str(identity),
                    "--output-root",
                    str(output_root),
                    "--no-render",
                    "--generate-images",
                ],
                cwd=repo_root,
                text=True,
                capture_output=True,
                check=False,
            )
            final_images_path = output_root / str(date.today()) / "cli-codex-builtin" / "final-images.json"
            manifest = json.loads(final_images_path.read_text(encoding="utf-8")) if final_images_path.exists() else {}
            blocker_path = output_root / str(date.today()) / "cli-codex-builtin" / "image-generation-blocker.md"
            blocker_exists = blocker_path.exists()

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("Codex image tool handoff", result.stdout)
        self.assertIn("Use Codex image generation in-session", result.stdout)
        self.assertEqual(manifest["status"], "handoff_ready")
        self.assertEqual(manifest["backend"], "codex_builtin")
        self.assertTrue(blocker_exists)

    def test_cli_proof_slide_implies_codex_builtin_handoff(self):
        repo_root = Path(__file__).resolve().parent.parent
        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = Path(tmpdir)
            story_image = workspace / "balcony.jpg"
            identity = workspace / "aachu-zuv.jpg"
            story_image.write_bytes(b"story-image")
            identity.write_bytes(b"identity-image")
            story_file = workspace / "story.txt"
            story_file.write_text(
                "Selected concept from the Golden Theme tournament: She Was Not High-Maintenance. "
                "Aachu is in a green dress, barefoot, and Zuv notices before she asks.",
                encoding="utf-8",
            )
            output_root = workspace / "out"

            result = subprocess.run(
                [
                    sys.executable,
                    str(repo_root / "scripts" / "create_illustration_carousel.py"),
                    "--story-file",
                    str(story_file),
                    "--title",
                    "CLI Proof Handoff",
                    "--image",
                    str(story_image),
                    "--identity-image",
                    str(identity),
                    "--output-root",
                    str(output_root),
                    "--no-render",
                    "--proof-slide",
                    "4",
                    "--proof-format",
                    "instagram_post",
                ],
                cwd=repo_root,
                text=True,
                capture_output=True,
                check=False,
            )
            out_dir = output_root / str(date.today()) / "cli-proof-handoff"
            manifest = json.loads((out_dir / "final-images.json").read_text(encoding="utf-8"))
            prompt_files = sorted(
                path.relative_to(out_dir / "codex-image-prompts").as_posix()
                for path in (out_dir / "codex-image-prompts").glob("**/*")
                if path.is_file()
            )
            blocker_text = (out_dir / "image-generation-blocker.md").read_text(encoding="utf-8")

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("Codex image tool handoff", result.stdout)
        self.assertEqual(manifest["status"], "handoff_ready")
        self.assertEqual(manifest["requested_proof_slide"], 4)
        self.assertEqual(manifest["requested_formats"], ["instagram_post"])
        self.assertEqual(
            prompt_files,
            [
                "instagram-post/slide-04.md",
                "instagram-post/slide-04.prompt.txt",
            ],
        )
        self.assertIn("slide 04", blocker_text)

    def test_package_codex_builtin_outputs_writes_model_native_manifest(self):
        import cv2
        import numpy as np

        from pipeline.stages.codex_builtin_image_generation import package_codex_builtin_outputs

        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = Path(tmpdir)
            story_image = workspace / "balcony.jpg"
            identity = workspace / "aachu-zuv.jpg"
            story_image.write_bytes(b"story-image")
            identity.write_bytes(b"identity-image")
            out_dir = create_codex_native_carousel(
                story=(
                    "Selected concept from the Golden Theme tournament: She Was Not High-Maintenance. "
                    "Aachu is in a green dress, barefoot, and Zuv notices before she asks."
                ),
                image_paths=[story_image],
                identity_image_paths=[identity],
                title="Codex Builtin Packaged",
                output_root=workspace / "out",
                render_assets=False,
                today=date(2026, 5, 18),
            )
            generated_dir = workspace / "generated"
            generated_dir.mkdir()
            instagram_paths = []
            reels_stories_paths = []
            for number in range(1, 6):
                instagram_path = generated_dir / f"instagram-post-slide-{number:02d}.png"
                instagram_path.write_bytes(self.png_bytes(8, 10, 240))
                instagram_paths.append(instagram_path)

                reels_stories_path = generated_dir / f"reels-stories-slide-{number:02d}.png"
                reels_stories_path.write_bytes(self.png_bytes(9, 16, 230))
                reels_stories_paths.append(reels_stories_path)

            with self.assertRaises(ValueError):
                package_codex_builtin_outputs(out_dir, generated_paths=instagram_paths)

            result = package_codex_builtin_outputs(
                out_dir,
                generated_paths_by_format={
                    "instagram_post": instagram_paths,
                    "reels_stories": reels_stories_paths,
                },
            )
            manifest = json.loads((out_dir / "final-images.json").read_text(encoding="utf-8"))
            slide_01_exists = (out_dir / "final" / "slide-01.png").exists()
            reels_slide_01_exists = (out_dir / "final-reels-stories" / "slide-01.png").exists()
            slide_01_native_outputs = manifest["slides"][0]["native_outputs"]
            instagram_size = self.png_size(out_dir / "final" / "slide-01.png")
            reels_stories_size = self.png_size(out_dir / "final-reels-stories" / "slide-01.png")

        self.assertEqual(result["status"], "generated")
        self.assertTrue(result["done"])
        self.assertTrue(result["publishable"])
        self.assertTrue(manifest["done"])
        self.assertTrue(manifest["publishable"])
        self.assertEqual(manifest["backend"], "codex_builtin")
        self.assertEqual(manifest["generation_mode"], "model_native_publishable")
        self.assertEqual(manifest["native_output_contract"]["formats"], ["instagram_post", "reels_stories"])
        self.assertTrue(slide_01_exists)
        self.assertTrue(reels_slide_01_exists)
        self.assertEqual(instagram_size, (1080, 1350))
        self.assertEqual(reels_stories_size, (1080, 1920))
        self.assertIn("instagram_post", slide_01_native_outputs)
        self.assertIn("reels_stories", slide_01_native_outputs)
        self.assertNotEqual(
            slide_01_native_outputs["instagram_post"]["source"],
            slide_01_native_outputs["reels_stories"]["source"],
        )
        self.assertNotIn("hd_file", manifest["slides"][0])
        self.assertIn(str(identity), manifest["slides"][0]["reference_images"])
        self.assertIn(str(story_image), manifest["slides"][0]["reference_images"])

    def test_package_generated_outputs_removes_stale_extra_final_slide_files(self):
        from pipeline.stages.codex_builtin_image_generation import package_codex_builtin_outputs

        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = Path(tmpdir)
            story_image = workspace / "balcony.jpg"
            identity = workspace / "aachu-zuv.jpg"
            story_image.write_bytes(b"story-image")
            identity.write_bytes(b"identity-image")
            out_dir = create_codex_native_carousel(
                story=(
                    "Selected concept from the Golden Theme tournament: She Was Not High-Maintenance. "
                    "Aachu is in a green dress, barefoot, and Zuv notices before she asks."
                ),
                image_paths=[story_image],
                identity_image_paths=[identity],
                title="Codex Builtin Stale Cleanup",
                output_root=workspace / "out",
                render_assets=False,
                today=date(2026, 5, 18),
            )
            (out_dir / "final").mkdir(exist_ok=True)
            (out_dir / "final-reels-stories").mkdir(exist_ok=True)
            (out_dir / "final" / "slide-99.png").write_bytes(b"stale-post")
            (out_dir / "final-reels-stories" / "slide-99.png").write_bytes(b"stale-story")
            generated_dir = workspace / "generated"
            generated_dir.mkdir()
            instagram_paths = []
            reels_stories_paths = []
            for number in range(1, 6):
                instagram_path = generated_dir / f"instagram-post-slide-{number:02d}.png"
                instagram_path.write_bytes(self.png_bytes(8, 10, 240))
                instagram_paths.append(instagram_path)
                reels_stories_path = generated_dir / f"reels-stories-slide-{number:02d}.png"
                reels_stories_path.write_bytes(self.png_bytes(9, 16, 230))
                reels_stories_paths.append(reels_stories_path)

            package_codex_builtin_outputs(
                out_dir,
                generated_paths_by_format={
                    "instagram_post": instagram_paths,
                    "reels_stories": reels_stories_paths,
                },
            )
            final_files = sorted(path.name for path in (out_dir / "final").glob("slide-*.png"))
            reels_files = sorted(path.name for path in (out_dir / "final-reels-stories").glob("slide-*.png"))

        self.assertEqual(final_files, [f"slide-{number:02d}.png" for number in range(1, 6)])
        self.assertEqual(reels_files, [f"slide-{number:02d}.png" for number in range(1, 6)])

    def test_package_generated_outputs_refreshes_final_audit(self):
        from pipeline.stages.codex_builtin_image_generation import package_codex_builtin_outputs

        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = Path(tmpdir)
            story_image = workspace / "balcony.jpg"
            identity = workspace / "aachu-zuv.jpg"
            story_image.write_bytes(b"story-image")
            identity.write_bytes(b"identity-image")
            out_dir = create_codex_native_carousel(
                story=(
                    "Selected concept from the Golden Theme tournament: She Was Not High-Maintenance. "
                    "Aachu is in a green dress, barefoot, and Zuv notices before she asks."
                ),
                image_paths=[story_image],
                identity_image_paths=[identity],
                title="Codex Builtin Audit Refresh",
                output_root=workspace / "out",
                render_assets=False,
                today=date(2026, 5, 18),
            )
            self.write_passing_visual_qa(out_dir)
            visual_qa_markdown = (out_dir / "visual-qa.md").read_text(encoding="utf-8")
            generated_dir = workspace / "external-generated"
            generated_dir.mkdir()
            instagram_paths = []
            reels_stories_paths = []
            for number in range(1, 6):
                instagram_path = generated_dir / f"instagram-post-slide-{number:02d}.png"
                instagram_path.write_bytes(self.png_bytes(8, 10, 240))
                instagram_paths.append(instagram_path)

                reels_stories_path = generated_dir / f"reels-stories-slide-{number:02d}.png"
                reels_stories_path.write_bytes(self.png_bytes(9, 16, 230))
                reels_stories_paths.append(reels_stories_path)

            result = package_codex_builtin_outputs(
                out_dir,
                generated_paths_by_format={
                    "instagram_post": instagram_paths,
                    "reels_stories": reels_stories_paths,
                },
                refresh_quality=True,
            )
            final_audit = json.loads((out_dir / "final-audit.json").read_text(encoding="utf-8"))
            refreshed_visual_qa_markdown = (out_dir / "visual-qa.md").read_text(encoding="utf-8")
            workspace_wiki_exists = (workspace / "wiki").exists()
            workspace_memory_exists = (workspace / "memory").exists()

        self.assertEqual(result["status"], "generated")
        self.assertIn(final_audit["status"], {"PASS", "PASS_WITH_NOTES"})
        self.assertEqual(refreshed_visual_qa_markdown, visual_qa_markdown)
        self.assertTrue(workspace_wiki_exists)
        self.assertTrue(workspace_memory_exists)

    def test_package_generated_outputs_reports_audit_failed_status(self):
        from pipeline.stages.codex_builtin_image_generation import package_codex_builtin_outputs

        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = Path(tmpdir)
            story_image = workspace / "balcony.jpg"
            identity = workspace / "aachu-zuv.jpg"
            story_image.write_bytes(b"story-image")
            identity.write_bytes(b"identity-image")
            out_dir = create_codex_native_carousel(
                story=(
                    "Selected concept from the Golden Theme tournament: She Was Not High-Maintenance. "
                    "Aachu is in a green dress, barefoot, and Zuv notices before she asks."
                ),
                image_paths=[story_image],
                identity_image_paths=[identity],
                title="Codex Builtin Audit Failed",
                output_root=workspace / "out",
                render_assets=False,
                today=date(2026, 5, 18),
            )
            generated_dir = workspace / "external-generated"
            generated_dir.mkdir()
            instagram_paths = []
            reels_stories_paths = []
            for number in range(1, 6):
                instagram_path = generated_dir / f"instagram-post-slide-{number:02d}.png"
                instagram_path.write_bytes(self.png_bytes(8, 10, 240))
                instagram_paths.append(instagram_path)

                reels_stories_path = generated_dir / f"reels-stories-slide-{number:02d}.png"
                reels_stories_path.write_bytes(self.png_bytes(9, 16, 230))
                reels_stories_paths.append(reels_stories_path)

            result = package_codex_builtin_outputs(
                out_dir,
                generated_paths_by_format={
                    "instagram_post": instagram_paths,
                    "reels_stories": reels_stories_paths,
                },
                refresh_quality=True,
            )
            manifest = json.loads((out_dir / "final-images.json").read_text(encoding="utf-8"))
            final_audit = json.loads((out_dir / "final-audit.json").read_text(encoding="utf-8"))

        self.assertEqual(final_audit["status"], "NEEDS_FIXES")
        self.assertFalse(final_audit["pass"])
        self.assertEqual(result["status"], "generated_audit_failed")
        self.assertFalse(result["done"])
        self.assertFalse(result["publishable"])
        self.assertEqual(result["final_audit_status"], "NEEDS_FIXES")
        self.assertFalse(result["final_audit_pass"])
        self.assertEqual(manifest["status"], "generated_audit_failed")
        self.assertFalse(manifest["done"])
        self.assertFalse(manifest["publishable"])
        self.assertEqual(manifest["final_audit_status"], "NEEDS_FIXES")

    def test_workspace_root_fallback_uses_package_parent_for_external_dirs(self):
        from pipeline.stages.codex_builtin_image_generation import infer_workspace_root_from_carousel_dir

        with tempfile.TemporaryDirectory() as tmpdir:
            package_dir = Path(tmpdir) / "external" / "pkg"
            package_dir.mkdir(parents=True)
            inferred = infer_workspace_root_from_carousel_dir(package_dir)

        self.assertEqual(inferred, package_dir.parent.resolve())
        self.assertNotEqual(inferred, Path("/"))
        self.assertNotEqual(inferred, Path.cwd())

    def test_quality_refresh_does_not_overwrite_existing_visual_qa_markdown(self):
        from pipeline.stages.carousel_quality import QualityContext, write_quality_artifacts

        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = Path(tmpdir)
            image = workspace / "balcony.jpg"
            identity = workspace / "aachu-zuv.jpg"
            image.write_bytes(b"story-image")
            identity.write_bytes(b"identity-image")
            out_dir = create_codex_native_carousel(
                story="She said bas 500. He kept extra there.",
                image_paths=[image],
                identity_image_paths=[identity],
                title="Visual QA Preserve",
                output_root=workspace / "out",
                render_assets=False,
                today=date(2026, 5, 18),
            )
            existing_visual_qa = "# Visual QA\n\n- [x] FAIL: human reviewer rejected slide 3 face likeness.\n"
            (out_dir / "visual-qa.md").write_text(existing_visual_qa, encoding="utf-8")
            manifest = json.loads((out_dir / "manifest.json").read_text(encoding="utf-8"))
            package = {
                "concept": json.loads((out_dir / "concept.json").read_text(encoding="utf-8")),
                "slides": json.loads((out_dir / "slides.json").read_text(encoding="utf-8")),
                "visual_plan_quality": json.loads((out_dir / "visual-plan-quality.json").read_text(encoding="utf-8")),
                "prompt_pack": json.loads((out_dir / "prompt-pack.json").read_text(encoding="utf-8")),
                "copy": json.loads((out_dir / "copy.json").read_text(encoding="utf-8")),
            }

            write_quality_artifacts(
                QualityContext(
                    story=manifest["source_story"],
                    title=manifest["title"],
                    slug=manifest["slug"],
                    today=date.fromisoformat(manifest["date"]),
                    out_dir=out_dir,
                    image_paths=[image],
                    slide_count=5,
                    package=package,
                    manifest=manifest,
                    render_result={"status": "skipped", "reason": "test refresh"},
                    workspace_root=workspace,
                )
            )
            refreshed_visual_qa = (out_dir / "visual-qa.md").read_text(encoding="utf-8")

        self.assertEqual(refreshed_visual_qa, existing_visual_qa)

    def test_final_audit_rejects_local_placeholder_final_images(self):
        from pipeline.stages.carousel_quality import (
            QualityContext,
            build_final_audit,
            build_run_ledger,
            build_stage_reviews,
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = Path(tmpdir)
            image = workspace / "identity.jpg"
            image.write_bytes(b"story-image")
            out_dir = create_codex_native_carousel(
                story="He did not marry peace. He married Aachu chaos.",
                image_paths=[image],
                title="Placeholder Gate",
                output_root=workspace / "out",
                render_assets=False,
                today=date(2026, 5, 16),
            )
            source_dir = out_dir / "source-generated-local"
            final_dir = out_dir / "final"
            reels_stories_dir = out_dir / "final-reels-stories"
            overlay_dir = out_dir / "final-with-text"
            source_dir.mkdir()
            final_dir.mkdir()
            reels_stories_dir.mkdir()
            overlay_dir.mkdir()
            records = []
            for number in range(1, 6):
                source = source_dir / f"instagram-slide-{number:02d}.png"
                reels_source = source_dir / f"reels-stories-slide-{number:02d}.png"
                final = final_dir / f"slide-{number:02d}.png"
                reels_final = reels_stories_dir / f"slide-{number:02d}.png"
                source.write_bytes(b"placeholder-png")
                reels_source.write_bytes(b"placeholder-reels-png")
                final.write_bytes(b"placeholder-png")
                reels_final.write_bytes(b"placeholder-reels-png")
                (overlay_dir / f"slide-{number:02d}.png").write_bytes(b"overlay-png")
                records.append(
                    {
                        "slide": number,
                        "source": str(source),
                        "file": str(final),
                        "reels_stories_source": str(reels_source),
                        "reels_stories_file": str(reels_final),
                        "native_outputs": {
                            "instagram_post": {
                                "source": str(source),
                                "file": str(final),
                            },
                            "reels_stories": {
                                "source": str(reels_source),
                                "file": str(reels_final),
                            },
                        },
                    }
                )
            (out_dir / "final-images.json").write_text(
                json.dumps(
                    {
                        "status": "packaged",
                        "native_output_contract": {
                            "formats": ["instagram_post", "reels_stories"],
                        },
                        "slides": records,
                    }
                ),
                encoding="utf-8",
            )
            (out_dir / "text-overlay.json").write_text(
                json.dumps(
                    {
                        "status": "rendered",
                        "renderer": {
                            "font_role": "hand_drawn_storybook",
                            "panel_style": "no_quote_card_panel",
                            "brandmark_style": "subtle_but_readable",
                        },
                        "slides": [],
                    }
                ),
                encoding="utf-8",
            )
            (out_dir / "visual-qa.md").write_text(
                "\n".join(
                    [
                        "# Visual QA",
                        "- [x] Slide 1 final image matches slide 1 storyboard: He didn't marry peace.",
                        "- [x] Aachu face is recognizably based on the identity reference.",
                        "- [x] Zuv face is recognizably based on the identity reference.",
                    ]
                ),
                encoding="utf-8",
            )

            manifest = json.loads((out_dir / "manifest.json").read_text(encoding="utf-8"))
            package = {
                "concept": json.loads((out_dir / "concept.json").read_text(encoding="utf-8")),
                "slides": json.loads((out_dir / "slides.json").read_text(encoding="utf-8")),
                "prompt_pack": json.loads((out_dir / "prompt-pack.json").read_text(encoding="utf-8")),
                "copy": json.loads((out_dir / "copy.json").read_text(encoding="utf-8")),
            }
            context = QualityContext(
                story=manifest["source_story"],
                title=manifest["title"],
                slug=manifest["slug"],
                today=date(2026, 5, 16),
                out_dir=out_dir,
                image_paths=[image],
                slide_count=5,
                package=package,
                manifest=manifest,
                render_result={"status": "skipped", "reason": "test"},
                workspace_root=workspace,
            )
            ledger = build_run_ledger(context)
            stage_reviews = build_stage_reviews(context, ledger)
            audit = build_final_audit(context, ledger, stage_reviews)

        self.assertFalse(audit["requirements"]["REQ-FINAL-IMAGES-001"]["pass"])
        self.assertIn("source-generated-local", " ".join(audit["requirements"]["REQ-FINAL-IMAGES-001"]["evidence"]["issues"]))

    def test_final_audit_rejects_single_source_resized_output_manifest(self):
        from pipeline.stages.carousel_quality import (
            QualityContext,
            build_final_audit,
            build_run_ledger,
            build_stage_reviews,
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = Path(tmpdir)
            image = workspace / "identity.jpg"
            image.write_bytes(b"story-image")
            out_dir = create_codex_native_carousel(
                story="He did not marry peace. He married Aachu chaos.",
                image_paths=[image],
                identity_image_paths=[image],
                title="Single Source Gate",
                output_root=workspace / "out",
                render_assets=False,
                today=date(2026, 5, 16),
            )
            generated_dir = workspace / "generated"
            final_dir = out_dir / "final"
            reels_stories_dir = out_dir / "final-reels-stories"
            generated_dir.mkdir()
            final_dir.mkdir()
            reels_stories_dir.mkdir()
            records = []
            for number in range(1, 6):
                source = generated_dir / f"slide-{number:02d}.png"
                final = final_dir / f"slide-{number:02d}.png"
                reels = reels_stories_dir / f"slide-{number:02d}.png"
                source.write_bytes(b"generated-png")
                final.write_bytes(b"generated-png")
                reels.write_bytes(b"same-source-derived-png")
                records.append(
                    {
                        "slide": number,
                        "generation_mode": "model_native_publishable",
                        "source": str(source),
                        "file": str(final),
                        "reels_stories_file": str(reels),
                    }
                )
            (out_dir / "final-images.json").write_text(
                json.dumps(
                    {
                        "status": "generated",
                        "generation_mode": "model_native_publishable",
                        "slides": records,
                    }
                ),
                encoding="utf-8",
            )

            manifest = json.loads((out_dir / "manifest.json").read_text(encoding="utf-8"))
            package = {
                "concept": json.loads((out_dir / "concept.json").read_text(encoding="utf-8")),
                "slides": json.loads((out_dir / "slides.json").read_text(encoding="utf-8")),
                "prompt_pack": json.loads((out_dir / "prompt-pack.json").read_text(encoding="utf-8")),
                "copy": json.loads((out_dir / "copy.json").read_text(encoding="utf-8")),
            }
            context = QualityContext(
                story=manifest["source_story"],
                title=manifest["title"],
                slug=manifest["slug"],
                today=date(2026, 5, 16),
                out_dir=out_dir,
                image_paths=[image],
                slide_count=5,
                package=package,
                manifest=manifest,
                render_result={"status": "skipped", "reason": "test"},
                workspace_root=workspace,
            )
            ledger = build_run_ledger(context)
            stage_reviews = build_stage_reviews(context, ledger)
            audit = build_final_audit(context, ledger, stage_reviews)

        self.assertFalse(audit["requirements"]["REQ-FINAL-IMAGES-001"]["pass"])
        self.assertIn("native_outputs", " ".join(audit["requirements"]["REQ-FINAL-IMAGES-001"]["evidence"]["issues"]))

    def test_final_audit_accepts_identity_only_generated_carousel(self):
        from pipeline.stages.carousel_quality import (
            QualityContext,
            build_final_audit,
            build_run_ledger,
            build_stage_reviews,
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = Path(tmpdir)
            identity = workspace / "aachu-zuv.jpg"
            identity.write_bytes(b"identity-image")
            out_dir = create_codex_native_carousel(
                story=(
                    "Some people come with subtitles. Aachu says kuch nahi but her face "
                    "says the full paragraph. Zuv learned her translation."
                ),
                image_paths=[],
                identity_image_paths=[identity],
                title="Identity Only Generated",
                output_root=workspace / "out",
                render_assets=False,
                today=date(2026, 5, 16),
            )
            source_dir = out_dir / "final" / "model-native-source"
            reels_stories_dir = out_dir / "final-reels-stories"
            source_dir.mkdir(parents=True)
            reels_stories_dir.mkdir()
            for number in range(1, 6):
                (out_dir / "final" / f"slide-{number:02d}.png").parent.mkdir(exist_ok=True)
                (out_dir / "final" / f"slide-{number:02d}.png").write_bytes(b"generated-png")
                (reels_stories_dir / f"slide-{number:02d}.png").write_bytes(b"generated-reels-png")
                (source_dir / f"instagram-post-slide-{number:02d}.png").write_bytes(b"generated-source-png")
                (source_dir / f"reels-stories-slide-{number:02d}.png").write_bytes(b"generated-reels-source-png")
            prompt_pack = json.loads((out_dir / "prompt-pack.json").read_text(encoding="utf-8"))
            final_manifest = {
                "status": "generated",
                "backend": "codex_builtin",
                "generation_mode": "model_native_publishable",
                "native_output_contract": {
                    "formats": ["instagram_post", "reels_stories"],
                },
                "slides": [
                    {
                        "slide": slide["slide"],
                        "copy": slide["text"],
                        "backend": "codex_builtin",
                        "generation_mode": "model_native_publishable",
                        "source": str(source_dir / f"instagram-post-slide-{slide['slide']:02d}.png"),
                        "file": str(out_dir / "final" / f"slide-{slide['slide']:02d}.png"),
                        "reels_stories_source": str(source_dir / f"reels-stories-slide-{slide['slide']:02d}.png"),
                        "reels_stories_file": str(
                            out_dir / "final-reels-stories" / f"slide-{slide['slide']:02d}.png"
                        ),
                        "native_outputs": {
                            "instagram_post": {
                                "source": str(source_dir / f"instagram-post-slide-{slide['slide']:02d}.png"),
                                "file": str(out_dir / "final" / f"slide-{slide['slide']:02d}.png"),
                            },
                            "reels_stories": {
                                "source": str(source_dir / f"reels-stories-slide-{slide['slide']:02d}.png"),
                                "file": str(
                                    out_dir / "final-reels-stories" / f"slide-{slide['slide']:02d}.png"
                                ),
                            },
                        },
                        "prompt": slide["prompt"],
                    }
                    for slide in prompt_pack["slides"]
                ],
            }
            (out_dir / "final-images.json").write_text(json.dumps(final_manifest), encoding="utf-8")
            (out_dir / "visual-qa.json").write_text(
                json.dumps(
                    {
                        "checks": {
                            "storyboard": {"pass": True},
                            "aachu_face": {
                                "pass": True,
                                "reference_option_ids": ["ID30", "ID31"],
                                "likeness_notes": "Long dark hair, expressive brows, soft oval face, and smile energy match ID30/ID31.",
                            },
                            "zuv_face": {
                                "pass": True,
                                "reference_option_ids": ["ID34"],
                                "likeness_notes": "Dark wavy hair, thick brows, beard, face structure, and grounded expression match ID34.",
                            },
                            "dress_continuity": {"pass": True},
                            "style": {"pass": True},
                            "model_native_text": {"pass": True},
                            "final_files": {"pass": True},
                        }
                    }
                ),
                encoding="utf-8",
            )
            (out_dir / "visual-qa.md").write_text(
                "\n".join(
                    [
                        "# Visual QA",
                        "- [x] Slide 1 final image matches slide 1 storyboard: Some people come with subtitles.",
                        "- [x] Slide 2 final image matches slide 2 storyboard: Aachu's face says everything first.",
                        "- [x] Slide 3 final image matches slide 3 storyboard: Her mouth says: \"kuch nahi.\"",
                        "- [x] Slide 4 final image matches slide 4 storyboard: Zuv knows the translation.",
                        "- [x] Slide 5 final image matches slide 5 storyboard: Maybe love is learning the subtitles.",
                        "- [x] Aachu face is recognizably based on the identity reference.",
                        "- [x] Zuv face is recognizably based on the identity reference.",
                    ]
                ),
                encoding="utf-8",
            )

            manifest = json.loads((out_dir / "manifest.json").read_text(encoding="utf-8"))
            package = {
                "concept": json.loads((out_dir / "concept.json").read_text(encoding="utf-8")),
                "slides": json.loads((out_dir / "slides.json").read_text(encoding="utf-8")),
                "visual_plan_quality": json.loads(
                    (out_dir / "visual-plan-quality.json").read_text(encoding="utf-8")
                ),
                "prompt_pack": prompt_pack,
                "copy": json.loads((out_dir / "copy.json").read_text(encoding="utf-8")),
            }
            context = QualityContext(
                story=manifest["source_story"],
                title=manifest["title"],
                slug=manifest["slug"],
                today=date(2026, 5, 16),
                out_dir=out_dir,
                image_paths=[],
                slide_count=5,
                package=package,
                manifest=manifest,
                render_result={"status": "generated", "generation_mode": "model_native_publishable"},
                workspace_root=workspace,
            )
            ledger = build_run_ledger(context)
            stage_reviews = build_stage_reviews(context, ledger)
            audit = build_final_audit(context, ledger, stage_reviews)

        self.assertTrue(audit["requirements"]["REQ-PHOTO-001"]["pass"])
        self.assertNotEqual(stage_reviews["reviews"]["intake_reviewer"]["status"], "NEEDS_FIXES")
        self.assertNotEqual(stage_reviews["reviews"]["visual_reviewer"]["status"], "NEEDS_FIXES")
        self.assertEqual(audit["status"], "PASS_WITH_NOTES")

    def test_final_audit_rejects_checkbox_only_visual_qa(self):
        from pipeline.stages.carousel_quality import (
            QualityContext,
            build_final_audit,
            build_run_ledger,
            build_stage_reviews,
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = Path(tmpdir)
            image = workspace / "identity.jpg"
            image.write_bytes(b"story-image")
            out_dir = create_codex_native_carousel(
                story="He did not marry peace. He married Aachu chaos.",
                image_paths=[image],
                title="Checkbox QA Gate",
                output_root=workspace / "out",
                render_assets=False,
                today=date(2026, 5, 16),
            )
            generated_dir = workspace / "generated"
            final_dir = out_dir / "final"
            reels_stories_dir = out_dir / "final-reels-stories"
            overlay_dir = out_dir / "final-with-text"
            generated_dir.mkdir()
            final_dir.mkdir()
            reels_stories_dir.mkdir()
            overlay_dir.mkdir()
            records = []
            for number in range(1, 6):
                instagram_source = generated_dir / f"instagram-post-slide-{number:02d}.png"
                reels_source = generated_dir / f"reels-stories-slide-{number:02d}.png"
                final = final_dir / f"slide-{number:02d}.png"
                reels = reels_stories_dir / f"slide-{number:02d}.png"
                instagram_source.write_bytes(b"generated-png")
                reels_source.write_bytes(b"generated-reels-png")
                final.write_bytes(b"generated-png")
                reels.write_bytes(b"generated-reels-png")
                (overlay_dir / f"slide-{number:02d}.png").write_bytes(b"overlay-png")
                records.append(
                    {
                        "slide": number,
                        "generation_mode": "model_native_publishable",
                        "prompt": "test prompt",
                        "source": str(instagram_source),
                        "file": str(final),
                        "reels_stories_source": str(reels_source),
                        "reels_stories_file": str(reels),
                        "native_outputs": {
                            "instagram_post": {"source": str(instagram_source), "file": str(final)},
                            "reels_stories": {"source": str(reels_source), "file": str(reels)},
                        },
                    }
                )
            (out_dir / "final-images.json").write_text(
                json.dumps(
                    {
                        "status": "packaged",
                        "generation_mode": "model_native_publishable",
                        "native_output_contract": {"formats": ["instagram_post", "reels_stories"]},
                        "slides": records,
                    }
                ),
                encoding="utf-8",
            )
            (out_dir / "text-overlay.json").write_text(
                json.dumps(
                    {
                        "status": "rendered",
                        "renderer": {
                            "font_role": "hand_drawn_storybook",
                            "panel_style": "no_quote_card_panel",
                            "brandmark_style": "subtle_but_readable",
                        },
                        "slides": [],
                    }
                ),
                encoding="utf-8",
            )
            (out_dir / "visual-qa.md").write_text(
                "\n".join(
                    [
                        "# Visual QA",
                        "- [x] Slide 1 final image matches slide 1 storyboard: He didn't marry peace.",
                        "- [x] Aachu face is recognizably based on the identity reference.",
                        "- [x] Zuv face is recognizably based on the identity reference.",
                    ]
                ),
                encoding="utf-8",
            )

            manifest = json.loads((out_dir / "manifest.json").read_text(encoding="utf-8"))
            package = {
                "concept": json.loads((out_dir / "concept.json").read_text(encoding="utf-8")),
                "slides": json.loads((out_dir / "slides.json").read_text(encoding="utf-8")),
                "prompt_pack": json.loads((out_dir / "prompt-pack.json").read_text(encoding="utf-8")),
                "copy": json.loads((out_dir / "copy.json").read_text(encoding="utf-8")),
            }
            context = QualityContext(
                story=manifest["source_story"],
                title=manifest["title"],
                slug=manifest["slug"],
                today=date(2026, 5, 16),
                out_dir=out_dir,
                image_paths=[image],
                slide_count=5,
                package=package,
                manifest=manifest,
                render_result={"status": "skipped", "reason": "test"},
                workspace_root=workspace,
            )
            ledger = build_run_ledger(context)
            stage_reviews = build_stage_reviews(context, ledger)
            audit = build_final_audit(context, ledger, stage_reviews)

        self.assertTrue(audit["requirements"]["REQ-FINAL-IMAGES-001"]["pass"])
        self.assertFalse(audit["requirements"]["REQ-VISUAL-QA-001"]["pass"])
        self.assertIn("visual-qa.json", " ".join(audit["requirements"]["REQ-VISUAL-QA-001"]["evidence"]["failed"]))

    def test_structured_visual_qa_requires_face_reference_evidence(self):
        from pipeline.stages.carousel_quality import QualityContext, structured_visual_qa_gate

        with tempfile.TemporaryDirectory() as tmpdir:
            out_dir = Path(tmpdir)
            (out_dir / "visual-qa.json").write_text(
                json.dumps(
                    {
                        "checks": {
                            "storyboard": {"pass": True},
                            "aachu_face": {"pass": True},
                            "zuv_face": {
                                "pass": True,
                                "reference_option_ids": ["ID34"],
                                "likeness_notes": "Face shape, beard, brows, and hair volume match ID34.",
                            },
                            "dress_continuity": {"pass": True},
                            "style": {"pass": True},
                            "model_native_text": {"pass": True},
                            "final_files": {"pass": True},
                        }
                    }
                ),
                encoding="utf-8",
            )
            context = QualityContext(
                story="x",
                title="x",
                slug="x",
                today=date(2026, 5, 19),
                out_dir=out_dir,
                image_paths=[],
                slide_count=5,
                package={},
                manifest={},
                render_result={},
                workspace_root=out_dir,
            )

            result = structured_visual_qa_gate(context)

        self.assertFalse(result["pass"])
        self.assertIn("aachu_face", " ".join(result["failed"]))

    def test_wiki_update_records_audit_issues_and_notes(self):
        from pipeline.stages.carousel_quality import QualityContext, build_wiki_update

        context = QualityContext(
            story="He did not marry peace.",
            title="He Did Not Marry Peace",
            slug="he-did-not-marry-peace",
            today=date(2026, 5, 16),
            out_dir=Path("output/carousels/2026-05-16/he-did-not-marry-peace"),
            image_paths=[],
            slide_count=5,
            package={
                "concept": {"human_truth": "Love makes the chaos feel safe."},
                "copy": {"caption_recommended": "he didn't marry peace."},
            },
            manifest={"runtime": "codex_native_local"},
            render_result={"status": "skipped", "reason": "render_assets=False"},
            workspace_root=Path("."),
        )
        audit = {
            "status": "NEEDS_FIXES",
            "issues": ["REQ-VISUAL-QA-001: Aachu/Zuv face likeness needs regeneration."],
            "notes": ["Typography overlay regenerated with storybook renderer."],
        }

        wiki_update = build_wiki_update(context, audit)

        self.assertIn("## Issues", wiki_update)
        self.assertIn("Aachu/Zuv face likeness needs regeneration", wiki_update)
        self.assertIn("## Notes", wiki_update)
        self.assertIn("Typography overlay regenerated", wiki_update)


if __name__ == "__main__":
    unittest.main()
