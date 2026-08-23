import unittest
from app.models import JobInput, MatchResult
from app.pipeline.prompt_build import build_slide_prompts
from tests.fakes import FakeLLM


def ji(**kw):
    base = dict(device_id="d", delivery_contact="c", creator_name="A", partner_name="B",
                relationship="together", setting_choice="keep", quote_mode="agent",
                quote_copy=None, photo_paths=["p.jpg"], audio_path="a.webm")
    base.update(kw); return JobInput(**base)


MATCH = MatchResult(pattern_id="p1", slide_count=2, beats=["first glance", "still here"])


class PromptBuildTests(unittest.TestCase):
    def test_agent_mode_uses_llm_text_and_brandmark(self):
        llm = FakeLLM(responses=[{"slides": [
            {"image_prompt": "two people, rain", "on_image_text": "the first glance"},
            {"image_prompt": "two people, older", "on_image_text": "still here"},
        ]}])
        prompts = build_slide_prompts(MATCH, ji(quote_mode="agent"), llm)
        self.assertEqual(len(prompts), 2)
        self.assertEqual(prompts[0].on_image_text, "the first glance")
        self.assertIn("@a.storyof.two", prompts[0].image_prompt)
        self.assertTrue(prompts[0].use_setting_ref)

    def test_none_mode_has_no_text(self):
        llm = FakeLLM(responses=[{"slides": [
            {"image_prompt": "a", "on_image_text": "x"},
            {"image_prompt": "b", "on_image_text": "y"},
        ]}])
        prompts = build_slide_prompts(MATCH, ji(quote_mode="none"), llm)
        self.assertTrue(all(p.on_image_text is None for p in prompts))

    def test_own_mode_uses_user_copy(self):
        llm = FakeLLM(responses=[{"slides": [{"image_prompt": "a", "on_image_text": "ignored"},
                                             {"image_prompt": "b", "on_image_text": "ignored"}]}])
        prompts = build_slide_prompts(MATCH, ji(quote_mode="own", quote_copy="our forever | and a day"), llm)
        self.assertEqual(prompts[0].on_image_text, "our forever")
        self.assertEqual(prompts[1].on_image_text, "and a day")

    def test_fresh_setting_disables_ref(self):
        llm = FakeLLM(responses=[{"slides": [{"image_prompt": "a", "on_image_text": None},
                                             {"image_prompt": "b", "on_image_text": None}]}])
        prompts = build_slide_prompts(MATCH, ji(setting_choice="fresh", quote_mode="none"), llm)
        self.assertFalse(any(p.use_setting_ref for p in prompts))
