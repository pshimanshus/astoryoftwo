import tempfile
import unittest
from pathlib import Path

from app.models import Job, JobInput, JobStatus
from app.store import JobStore
from app.pipeline.run import run_job
from tests.fakes import FakeLLM, FakeRenderer


class RunTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        root = Path(self.tmp.name)
        self.store = JobStore(db_path=root / "j.db", blob_root=root / "b")

    def tearDown(self):
        self.tmp.cleanup()

    def _job(self, **kw):
        ji = JobInput(device_id="d", delivery_contact="c", creator_name="A", partner_name="B",
                      relationship="together", setting_choice="fresh", quote_mode="agent",
                      quote_copy=None, photo_paths=[], audio_path="", **kw)
        job = Job.new(ji)
        audio = self.store.save_blob(job.id, "voice.webm", b"AUDIO")
        job.input.audio_path = audio
        self.store.create(job)
        return job

    def _llm(self):
        # slide_count 3 = the min-slides floor; 3 beats, 3 prompt slides, 3 QA passes.
        return FakeLLM(transcript="we met in the rain", responses=[
            {"pattern_id": "p1", "slide_count": 3, "beats": ["glance", "stay", "still"]},  # match
            {"slides": [{"image_prompt": "a", "on_image_text": "t0"},
                        {"image_prompt": "b", "on_image_text": "t1"},
                        {"image_prompt": "c", "on_image_text": "t2"}]},                    # prompt build
            {"passed": True, "reason": "ok"},                                              # qa slide 0
            {"passed": True, "reason": "ok"},                                              # qa slide 1
            {"passed": True, "reason": "ok"},                                              # qa slide 2
        ])

    def test_happy_path_reaches_ready(self):
        job = self._job()
        run_job(job.id, self.store, self._llm(), FakeRenderer(image=b"IMG"),
                bank=[{"caption": "x", "childCount": 3, "commentsCount": 1, "commentSendProxy": 1}])
        got = self.store.get(job.id)
        self.assertEqual(got.status, JobStatus.READY)
        self.assertEqual(len(got.slides), 3)
        self.assertEqual(got.story_text, "we met in the rain")

    def test_transcription_failure_marks_failed(self):
        job = self._job()
        run_job(job.id, self.store, FakeLLM(transcript="  "), FakeRenderer(),
                bank=[{"caption": "x", "childCount": 2}])
        got = self.store.get(job.id)
        self.assertEqual(got.status, JobStatus.FAILED)
        self.assertIn("transcript", (got.error or "").lower())
