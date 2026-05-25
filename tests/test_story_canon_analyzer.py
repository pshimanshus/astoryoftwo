import unittest

from scripts.analyze_story_canon import build_pattern_map, validate_patterns


class StoryCanonAnalyzerTests(unittest.TestCase):
    def test_framework_sources_route_to_sell_online_and_support_sources_are_excluded(self):
        sources = [
            {
                "id": "storybrand-framework",
                "type": "story_selling_framework",
                "title": "StoryBrand Framework",
                "creator": "StoryBrand",
                "source_url": "https://storybrand.com/learn-the-framework/",
                "license_status": "copyrighted_web_article",
                "allowed_use": ["metadata_analysis", "short_summary", "derived_patterns"],
                "ingestion_mode": "metadata_only",
                "confidence": 0.8,
            },
            {
                "id": "gutenberg-robot-access-policy",
                "type": "book",
                "title": "Project Gutenberg Robot Access Policy",
                "creator": "Project Gutenberg",
                "source_url": "https://www.gutenberg.org/policy/robot_access.html",
                "license_status": "access_policy",
                "allowed_use": ["ingestion_rules", "source_discovery"],
                "ingestion_mode": "policy_reference",
                "confidence": 0.95,
            },
            {
                "id": "open-library-developers-api",
                "type": "book",
                "title": "Open Library Developers API",
                "creator": "Open Library",
                "source_url": "https://openlibrary.org/developers/api",
                "license_status": "api_metadata_terms",
                "allowed_use": ["metadata_analysis", "source_discovery", "derived_patterns"],
                "ingestion_mode": "api_metadata_only",
                "confidence": 0.85,
            },
            {
                "id": "gutenberg-pride-and-prejudice",
                "type": "book",
                "title": "Pride and Prejudice",
                "creator": "Jane Austen",
                "source_url": "https://www.gutenberg.org/ebooks/1342",
                "license_status": "public_domain_us",
                "allowed_use": ["full_text_analysis", "derived_patterns"],
                "ingestion_mode": "robot_harvest_or_manual_seed",
                "confidence": 0.96,
            },
        ]

        pattern_map = build_pattern_map(sources, {})
        validate_patterns(pattern_map)

        sell_online_sources = {
            source_id
            for pattern in pattern_map["sell_online_engine"]
            for source_id in pattern["source_ids"]
        }
        romance_sources = {
            source_id
            for pattern in pattern_map["romance_arc"]
            for source_id in pattern["source_ids"]
        }

        self.assertIn("storybrand-framework", sell_online_sources)
        self.assertNotIn("storybrand-framework", romance_sources)
        self.assertIn("gutenberg-pride-and-prejudice", romance_sources)
        self.assertIn("gutenberg-robot-access-policy", pattern_map["excluded_source_ids"])
        self.assertIn("open-library-developers-api", pattern_map["excluded_source_ids"])
        self.assertNotIn("gutenberg-robot-access-policy", romance_sources)
        self.assertNotIn("open-library-developers-api", romance_sources)

        for schema in ["romance_arc", "scene_engine", "sell_online_engine", "carousel_adapter"]:
            for pattern in pattern_map[schema]:
                self.assertIsNotNone(pattern.get("confidence"))
                self.assertTrue(pattern.get("source_ids"))


if __name__ == "__main__":
    unittest.main()
