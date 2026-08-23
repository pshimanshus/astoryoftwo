import unittest
from app.pipeline.match import match_winner
from tests.fakes import FakeLLM


BANK = [{"caption": "love in small moments", "childCount": 4, "commentsCount": 10, "commentSendProxy": 3}]


class MatchTests(unittest.TestCase):
    def test_returns_matchresult_with_clamped_slides(self):
        llm = FakeLLM(responses=[{"pattern_id": "p1", "slide_count": 9, "beats": ["a", "b"]}])
        mr = match_winner("we argue then laugh", "A", "B", "together", BANK, llm,
                          min_slides=3, max_slides=5)
        self.assertEqual(mr.pattern_id, "p1")
        self.assertEqual(mr.slide_count, 5)          # 9 clamped to max 5
        self.assertEqual(len(mr.beats), 5)           # padded to slide_count

    def test_truncates_extra_beats(self):
        llm = FakeLLM(responses=[{"pattern_id": "p2", "slide_count": 3,
                                  "beats": ["a", "b", "c", "d", "e"]}])
        mr = match_winner("s", "A", "B", "sending", BANK, llm)
        self.assertEqual(len(mr.beats), 3)

    def test_passes_story_and_bank_to_llm(self):
        llm = FakeLLM(responses=[{"pattern_id": "p", "slide_count": 3, "beats": ["a", "b", "c"]}])
        match_winner("the rooftop night", "A", "B", "together", BANK, llm)
        _system, prompt, _imgs = llm.calls[0]
        self.assertIn("rooftop night", prompt)
