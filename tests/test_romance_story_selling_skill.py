import json
import unittest
from datetime import date
from pathlib import Path

from scripts.build_romance_story_selling_skill import (
    build_skill_review,
    parse_concept_process_cards,
    validate_skill_package,
)


ROOT = Path(__file__).resolve().parents[1]


class RomanceStorySellingSkillTests(unittest.TestCase):
    def test_layer_e_required_files_exist_and_have_contract_markers(self):
        result = validate_skill_package(ROOT)

        self.assertEqual(result["missing_files"], [])
        self.assertEqual(result["status"], "PASS")
        self.assertGreaterEqual(result["source_count"], 40)
        self.assertIn("romance-story-selling-engine", result["skill_text"])
        self.assertIn("Story-Selling", result["skill_text"])
        self.assertIn("28/30", result["rubric_text"])
        self.assertIn("golden viral carousel theme", result["skill_text"].lower())

    def test_process_cards_parse_to_source_backed_bank(self):
        card_path = ROOT / "config" / "references" / "story-selling-canon" / "concept-process-cards.md"
        cards = parse_concept_process_cards(card_path)

        self.assertGreaterEqual(len(cards), 20)
        card_one = next(card for card in cards if card["id"] == "card-01")
        self.assertEqual(
            card_one["a_story_of_two_filter"],
            "Zuv must make the moment easier without making Aachu smaller.",
        )
        for card in cards:
            self.assertTrue(card["id"])
            self.assertTrue(card["title"])
            self.assertTrue(card["source_patterns"])
            self.assertGreater(card["confidence"], 0)
            self.assertTrue(card["process"])

    def test_build_skill_review_writes_jarvis_outputs(self):
        with self.subTest("build review artifacts"):
            import tempfile

            with tempfile.TemporaryDirectory() as tmpdir:
                out_dir = build_skill_review(
                    root=ROOT,
                    output_root=Path(tmpdir),
                    run_date=date(2026, 5, 18),
                )

                review = (out_dir / "skill-build-review.md").read_text(encoding="utf-8")
                backtest = (out_dir / "gold-carousel-backtest.md").read_text(encoding="utf-8")
                bank = json.loads((out_dir / "concept-process-bank.json").read_text(encoding="utf-8"))

        self.assertIn("Status: PASS", review)
        self.assertIn("romance-story-selling-engine", review)
        self.assertIn("calm enough for chaos", backtest.lower())
        self.assertIn("New Concept Tournament Using Only Layer E", backtest)
        self.assertIn("Winner score: Story-Selling 29/30", backtest)
        self.assertIn("Decision: GO", backtest)
        self.assertIn("Aachu", backtest)
        self.assertIn("Zuv", backtest)
        self.assertGreaterEqual(len(bank["processes"]), 20)
        self.assertEqual(bank["generated_for"], "@a.storyof.two")


if __name__ == "__main__":
    unittest.main()
