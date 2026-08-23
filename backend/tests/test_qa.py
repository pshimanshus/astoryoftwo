import unittest
from app.models import SlidePrompt
from app.providers.base import QAResult
from app.pipeline.qa import qa_slide, render_with_qa
from tests.fakes import FakeLLM, FakeRenderer


SP = SlidePrompt(index=0, image_prompt="draw", on_image_text="hi", use_setting_ref=False)


class QATests(unittest.TestCase):
    def test_qa_slide_parses_pass(self):
        llm = FakeLLM(responses=[{"passed": True, "reason": "on style"}])
        res = qa_slide(b"img", SP, llm)
        self.assertIsInstance(res, QAResult)
        self.assertTrue(res.passed)

    def test_render_with_qa_returns_on_first_pass(self):
        llm = FakeLLM(responses=[{"passed": True, "reason": "ok"}])
        r = FakeRenderer(image=b"GOOD")
        out = render_with_qa(SP, r, llm, "1024x1536", [], None, max_retries=2)
        self.assertEqual(out, b"GOOD")
        self.assertEqual(len(r.prompts), 1)            # no retry

    def test_render_with_qa_retries_then_succeeds(self):
        llm = FakeLLM(responses=[{"passed": False, "reason": "yellow cast"},
                                 {"passed": True, "reason": "fixed"}])
        r = FakeRenderer(image=b"IMG")
        out = render_with_qa(SP, r, llm, "1024x1536", [], None, max_retries=2)
        self.assertEqual(out, b"IMG")
        self.assertEqual(len(r.prompts), 2)            # one retry

    def test_render_with_qa_raises_after_cap(self):
        llm = FakeLLM(responses=[{"passed": False, "reason": "bad"}] * 5)
        with self.assertRaises(RuntimeError):
            render_with_qa(SP, FakeRenderer(), llm, "1024x1536", [], None, max_retries=2)
