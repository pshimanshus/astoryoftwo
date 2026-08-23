import unittest
from app.models import SlidePrompt
from app.pipeline.assemble import assemble_slides


class AssembleTests(unittest.TestCase):
    def test_assembles_ordered_captioned_slides(self):
        saved = {}

        def save_blob(name, data):
            saved[name] = data
            return f"/blobs/{name}"

        prompts = [
            SlidePrompt(index=0, image_prompt="a", on_image_text="one", use_setting_ref=False),
            SlidePrompt(index=1, image_prompt="b", on_image_text=None, use_setting_ref=False),
        ]
        images = [b"IMG0", b"IMG1"]
        slides = assemble_slides(prompts, images, save_blob)
        self.assertEqual([s.index for s in slides], [0, 1])
        self.assertEqual(slides[0].caption, "one")
        self.assertIsNone(slides[1].caption)
        self.assertEqual(slides[0].image_path, "/blobs/slide_0.png")
        self.assertEqual(saved["slide_1.png"], b"IMG1")
