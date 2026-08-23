import unittest
from app.models import SlidePrompt
from app.pipeline.render import render_slide
from tests.fakes import FakeRenderer


class RenderTests(unittest.TestCase):
    def test_render_returns_bytes_and_passes_prompt(self):
        r = FakeRenderer(image=b"IMG")
        sp = SlidePrompt(index=0, image_prompt="draw", on_image_text=None, use_setting_ref=False)
        out = render_slide(sp, r, "1024x1536", style_refs=[], setting_ref=None)
        self.assertEqual(out, b"IMG")
        self.assertEqual(r.prompts, ["draw"])

    def test_setting_ref_included_only_when_requested(self):
        captured = {}

        class RefSpy(FakeRenderer):
            def render(self, prompt, ref_images, size):
                captured["refs"] = list(ref_images)
                return super().render(prompt, ref_images, size)

        sp_keep = SlidePrompt(index=0, image_prompt="x", on_image_text=None, use_setting_ref=True)
        render_slide(sp_keep, RefSpy(), "1024x1536", style_refs=[b"style"], setting_ref=b"photo")
        self.assertEqual(captured["refs"], [b"style", b"photo"])

        sp_fresh = SlidePrompt(index=0, image_prompt="x", on_image_text=None, use_setting_ref=False)
        render_slide(sp_fresh, RefSpy(), "1024x1536", style_refs=[b"style"], setting_ref=b"photo")
        self.assertEqual(captured["refs"], [b"style"])
