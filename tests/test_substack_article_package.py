import json
import tempfile
import unittest
from datetime import date
from pathlib import Path

from scripts.create_substack_article_package import (
    ARTICLE_ARTIFACTS,
    create_article_package,
    discover_carousel_images,
    slugify_title,
)


class SubstackArticlePackageTests(unittest.TestCase):
    def test_slugify_title_keeps_article_paths_stable(self):
        self.assertEqual(slugify_title("Calm Enough For My Chaos"), "calm-enough-for-my-chaos")
        self.assertEqual(slugify_title("  "), "couple-love-article")

    def test_discovers_root_carousel_slides_first(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            carousel = Path(tmpdir) / "carousel"
            final = carousel / "final"
            final.mkdir(parents=True)
            (carousel / "slide-01.png").write_bytes(b"root")
            (final / "slide-01.png").write_bytes(b"final")

            images = discover_carousel_images(carousel)

        self.assertEqual(images, [carousel / "slide-01.png"])

    def test_create_article_package_writes_gated_contract(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = Path(tmpdir)
            carousel = workspace / "output" / "carousels" / "2026-05-17" / "he-didnt-marry-peace"
            carousel.mkdir(parents=True)
            (carousel / "concept.json").write_text(
                json.dumps(
                    {
                        "title": "He Didn't Marry Peace",
                        "human_truth": "Love gives chaos a safe place.",
                    }
                ),
                encoding="utf-8",
            )
            (carousel / "storyboard.md").write_text("# Storyboard", encoding="utf-8")
            (carousel / "slides.json").write_text("[]", encoding="utf-8")
            (carousel / "copy.json").write_text("{}", encoding="utf-8")
            (carousel / "slide-01.png").write_bytes(b"image")

            out_dir = create_article_package(
                carousel_dir=carousel,
                title="Calm Enough For My Chaos",
                output_root=workspace / "output" / "articles",
                today=date(2026, 5, 17),
            )

            manifest = json.loads((out_dir / "source-manifest.json").read_text(encoding="utf-8"))
            gates = (out_dir / "editorial-gates.md").read_text(encoding="utf-8")
            brief = (out_dir / "article-brief.md").read_text(encoding="utf-8")
            outline = (out_dir / "outline.md").read_text(encoding="utf-8")
            layer_e = json.loads((out_dir / "layer-e-story-selling.json").read_text(encoding="utf-8"))
            artifact_exists = {artifact: (out_dir / artifact).exists() for artifact in ARTICLE_ARTIFACTS}

            self.assertEqual(out_dir.name, "calm-enough-for-my-chaos")
            self.assertEqual(manifest["source_carousel"], str(carousel))
            self.assertEqual(manifest["theme"], "couple-love-substack")
            self.assertEqual(manifest["artifacts"], ARTICLE_ARTIFACTS)
            self.assertEqual(manifest["carousel_images"], [str(carousel / "slide-01.png")])
            self.assertEqual(
                manifest["story_selling_contract"]["skill"],
                "config/skills/romance-story-selling-engine.md",
            )
            self.assertIn(
                "config/references/story-selling-canon/rubric.md",
                manifest["story_selling_contract"]["references"],
            )
            for artifact, exists in artifact_exists.items():
                self.assertTrue(exists, artifact)
            self.assertIn("Gate 1 - Source Integrity", gates)
            self.assertIn("Gate 7 - Final Publish Approval", gates)
            self.assertIn("Gate 8 - Story Selling Fit", gates)
            self.assertIn("Do not publish until every gate is PASS or PASS_WITH_NOTES.", gates)
            self.assertEqual(manifest["layer_e_story_selling"]["artifact"], "layer-e-story-selling.json")
            self.assertTrue(layer_e["selected_story_lens"])
            self.assertIn("Layer E Story-Selling Angle", brief)
            self.assertIn(layer_e["selected_story_lens"], brief)
            self.assertIn("Opening Hook", outline)
            self.assertNotIn("TBD", outline)
            self.assertIn("romance-story-selling-engine", brief)
            self.assertIn("Story-Selling", brief)

    def test_article_framework_documents_story_selling_gate(self):
        framework = Path("config/skills/couple-substack-article-framework.md").read_text(
            encoding="utf-8"
        )

        self.assertIn("config/skills/romance-story-selling-engine.md", framework)
        self.assertIn("config/references/story-selling-canon/rubric.md", framework)
        self.assertIn("Gate 8 - Story Selling Fit", framework)
        self.assertIn("28/30", framework)
