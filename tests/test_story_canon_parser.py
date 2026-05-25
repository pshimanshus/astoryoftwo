import json
import tempfile
import unittest
from pathlib import Path

from scripts.ingest_story_canon import ingest_story_canon, load_source_register, plan_ingestion


def write_register(path: Path, sources: list[dict]) -> None:
    path.write_text(json.dumps({"sources": sources}, indent=2), encoding="utf-8")


class StoryCanonParserTests(unittest.TestCase):
    def test_dry_run_filters_type_and_max_sources_without_writing_files(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = Path(tmpdir)
            register_path = workspace / "source-register.json"
            output_dir = workspace / "story-canon"
            sources = [
                {
                    "id": "gutenberg-persuasion",
                    "type": "book",
                    "title": "Persuasion",
                    "creator": "Jane Austen",
                    "source_url": "https://www.gutenberg.org/ebooks/105",
                    "license_status": "public_domain_us",
                    "allowed_use": ["full_text_analysis", "short_quotes", "derived_patterns"],
                    "ingestion_mode": "robot_harvest_or_manual_seed",
                    "priority": 1,
                    "confidence": 0.95,
                },
                {
                    "id": "loc-may-irwin-kiss",
                    "type": "film",
                    "title": "The May Irwin Kiss",
                    "creator": "William Heise",
                    "source_url": "https://www.loc.gov/item/00694129/",
                    "license_status": "public_domain_us",
                    "allowed_use": ["metadata_analysis", "derived_patterns"],
                    "ingestion_mode": "metadata_only",
                    "priority": 2,
                    "confidence": 0.9,
                },
                {
                    "id": "open-library-north-and-south",
                    "type": "book",
                    "title": "North and South",
                    "creator": "Elizabeth Gaskell",
                    "source_url": "https://openlibrary.org/works/OL158842W",
                    "license_status": "public_domain_us",
                    "allowed_use": ["metadata_analysis", "derived_patterns"],
                    "ingestion_mode": "metadata_only",
                    "priority": 3,
                    "confidence": 0.85,
                },
            ]
            write_register(register_path, sources)

            result = ingest_story_canon(
                source_register=register_path,
                source_type="book",
                dry_run=True,
                max_sources=1,
                output_dir=output_dir,
            )

        self.assertEqual(result["mode"], "dry_run")
        self.assertEqual([source["id"] for source in result["sources"]], ["gutenberg-persuasion"])
        self.assertFalse((output_dir / "source-cards").exists())
        self.assertFalse((output_dir / "parsed").exists())
        self.assertFalse((output_dir / "raw").exists())

    def test_non_dry_run_writes_source_cards_and_parsed_metadata_only(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = Path(tmpdir)
            register_path = workspace / "source-register.json"
            output_dir = workspace / "story-canon"
            write_register(
                register_path,
                [
                    {
                        "id": "storygrid-love-genre",
                        "type": "article",
                        "title": "Love Genre",
                        "creator": "Story Grid",
                        "source_url": "https://storygrid.com/love-genre/",
                        "license_status": "modern_copyright",
                        "allowed_use": ["metadata_analysis", "short_summary", "derived_patterns"],
                        "ingestion_mode": "metadata_only",
                        "summary": "A craft reference about connection, hate-love value, sacrifice, and obligatory love-story movements.",
                        "process_tags": ["love_genre", "sacrifice", "connection"],
                        "extraction_notes": ["Use as a framework card, not a mirrored article body."],
                        "priority": 1,
                        "confidence": 0.8,
                    }
                ],
            )

            result = ingest_story_canon(
                source_register=register_path,
                source_type="all",
                dry_run=False,
                max_sources=None,
                output_dir=output_dir,
            )

            source_card = json.loads(
                (output_dir / "source-cards" / "storygrid-love-genre.json").read_text(encoding="utf-8")
            )
            parsed = json.loads(
                (output_dir / "parsed" / "articles" / "storygrid-love-genre.json").read_text(encoding="utf-8")
            )

        self.assertEqual(result["mode"], "ingest")
        self.assertEqual(result["written_count"], 2)
        self.assertEqual(source_card["id"], "storygrid-love-genre")
        self.assertEqual(source_card["allowed_use"], ["metadata_analysis", "short_summary", "derived_patterns"])
        self.assertEqual(parsed["content_policy"], "metadata_only_no_full_text_fetch")
        self.assertEqual(parsed["body_text"], None)
        self.assertEqual(parsed["summary"], "A craft reference about connection, hate-love value, sacrifice, and obligatory love-story movements.")

    def test_policy_blocks_full_text_analysis_for_unclear_or_copyrighted_sources(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            register_path = Path(tmpdir) / "source-register.json"
            write_register(
                register_path,
                [
                    {
                        "id": "paid-romance-craft-book",
                        "type": "book",
                        "title": "Paid Romance Craft Book",
                        "creator": "Modern Author",
                        "source_url": "https://example.com/paid-book",
                        "license_status": "paid",
                        "allowed_use": ["metadata_analysis", "full_text_analysis"],
                        "ingestion_mode": "metadata_only",
                        "priority": 1,
                        "confidence": 0.7,
                    }
                ],
            )

            with self.assertRaisesRegex(ValueError, "full_text_analysis"):
                load_source_register(register_path)

    def test_policy_blocks_full_text_analysis_for_review_gated_sources(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            register_path = Path(tmpdir) / "source-register.json"
            write_register(
                register_path,
                [
                    {
                        "id": "review-gated-public-domain",
                        "type": "book",
                        "title": "Review Gated Book",
                        "creator": "Author",
                        "source_url": "https://www.gutenberg.org/ebooks/999",
                        "license_status": "public_domain_us_review_before_bulk_use",
                        "allowed_use": ["full_text_analysis", "derived_patterns"],
                        "ingestion_mode": "robot_harvest_or_manual_seed",
                        "priority": 1,
                        "confidence": 0.7,
                    }
                ],
            )

            with self.assertRaisesRegex(ValueError, "full_text_analysis"):
                load_source_register(register_path)

    def test_missing_source_register_fails_with_clear_error(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            missing_register = Path(tmpdir) / "missing-register.json"

            with self.assertRaisesRegex(ValueError, "Source register not found"):
                load_source_register(missing_register)

    def test_plan_marks_gutenberg_sources_as_robot_or_manual_seed_without_fetching(self):
        source = {
            "id": "gutenberg-pride-and-prejudice",
            "type": "book",
            "title": "Pride and Prejudice",
            "creator": "Jane Austen",
            "source_url": "https://www.gutenberg.org/ebooks/1342",
            "license_status": "public_domain_us",
            "allowed_use": ["full_text_analysis", "short_quotes", "derived_patterns"],
            "ingestion_mode": "robot_harvest_or_manual_seed",
            "priority": 1,
            "confidence": 0.95,
        }

        planned = plan_ingestion(source)

        self.assertEqual(planned["fetch_status"], "planned_not_fetched")
        self.assertEqual(planned["network_fetch"], False)
        self.assertIn("robot", planned["notes"].lower())

    def test_dry_run_treats_craft_and_framework_sources_as_article_lane(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = Path(tmpdir)
            register_path = workspace / "source-register.json"
            output_dir = workspace / "story-canon"
            write_register(
                register_path,
                [
                    {
                        "id": "copyblogger-story-sells",
                        "type": "craft_article",
                        "title": "How to Write a Story That Sells",
                        "creator": "Copyblogger",
                        "source_url": "https://copyblogger.com/how-to-write-a-story/",
                        "license_status": "modern_copyright",
                        "allowed_use": ["metadata_analysis", "short_summary", "derived_patterns"],
                        "ingestion_mode": "metadata_only",
                        "priority": 1,
                        "confidence": 0.8,
                    },
                    {
                        "id": "storybrand-framework",
                        "type": "story_selling_framework",
                        "title": "StoryBrand Framework",
                        "creator": "StoryBrand",
                        "source_url": "https://storybrand.com/learn-the-framework/",
                        "license_status": "modern_copyright",
                        "allowed_use": ["metadata_analysis", "short_summary", "derived_patterns"],
                        "ingestion_mode": "metadata_only",
                        "priority": 2,
                        "confidence": 0.82,
                    },
                ],
            )

            result = ingest_story_canon(
                source_register=register_path,
                source_type="article",
                dry_run=True,
                output_dir=output_dir,
            )

        self.assertEqual(result["selected_count"], 2)
        self.assertEqual(
            [source["id"] for source in result["sources"]],
            ["copyblogger-story-sells", "storybrand-framework"],
        )


if __name__ == "__main__":
    unittest.main()
