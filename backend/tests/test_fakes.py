import unittest
from tests.fakes import FakeLLM, FakeRenderer


class FakeTests(unittest.TestCase):
    def test_fake_llm_transcribe_and_reason(self):
        llm = FakeLLM(transcript="hello", responses=[{"a": 1}, {"b": 2}])
        self.assertEqual(llm.transcribe(b"x", "audio/webm"), "hello")
        self.assertEqual(llm.reason_json("sys", "p1"), {"a": 1})
        self.assertEqual(llm.reason_json("sys", "p2"), {"b": 2})
        self.assertEqual(len(llm.calls), 2)

    def test_fake_renderer_records_prompts(self):
        r = FakeRenderer(image=b"IMG")
        self.assertEqual(r.render("draw", [], "1024x1536"), b"IMG")
        self.assertEqual(r.prompts, ["draw"])
