import unittest
from app.models import Job, JobInput, JobStatus, Slide, SlidePrompt, MatchResult


def make_input(**kw):
    base = dict(
        device_id="dev_1", delivery_contact="a@b.com", creator_name="Aarav",
        partner_name="Mira", relationship="together", setting_choice="keep",
        quote_mode="agent", quote_copy=None, photo_paths=["p1.jpg"], audio_path="a.webm",
    )
    base.update(kw)
    return JobInput(**base)


class ModelTests(unittest.TestCase):
    def test_job_new_defaults(self):
        job = Job.new(make_input())
        self.assertEqual(job.status, JobStatus.QUEUED)
        self.assertTrue(job.id)
        self.assertEqual(job.slides, [])
        self.assertIsNone(job.story_text)
        self.assertIsNone(job.error)
        self.assertEqual(job.created_at, job.updated_at)

    def test_touch_changes_updated_at(self):
        job = Job.new(make_input())
        first = job.updated_at
        job.status = JobStatus.RUNNING
        job.touch()
        self.assertGreaterEqual(job.updated_at, first)

    def test_quote_mode_values(self):
        for mode in ("own", "agent", "none"):
            self.assertEqual(make_input(quote_mode=mode).quote_mode, mode)

    def test_slide_and_prompt_and_match(self):
        sp = SlidePrompt(index=0, image_prompt="x", on_image_text="hi", use_setting_ref=True)
        sl = Slide(index=0, image_path="out/0.png", caption="hi")
        mr = MatchResult(pattern_id="p1", slide_count=4, beats=["a", "b", "c", "d"])
        self.assertEqual((sp.index, sl.index, mr.slide_count), (0, 0, 4))
