import tempfile
import unittest
from pathlib import Path

from app.models import Job, JobInput, JobStatus, Slide, MatchResult
from app.store import JobStore


def make_job():
    ji = JobInput(device_id="d", delivery_contact="c", creator_name="A", partner_name="B",
                  relationship="together", setting_choice="keep", quote_mode="none",
                  quote_copy=None, photo_paths=["p.jpg"], audio_path="a.webm")
    return Job.new(ji)


class StoreTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        root = Path(self.tmp.name)
        self.store = JobStore(db_path=root / "jobs.db", blob_root=root / "blobs")

    def tearDown(self):
        self.tmp.cleanup()

    def test_create_and_get_roundtrip(self):
        job = make_job()
        self.store.create(job)
        got = self.store.get(job.id)
        self.assertEqual(got.id, job.id)
        self.assertEqual(got.status, JobStatus.QUEUED)
        self.assertEqual(got.input.creator_name, "A")

    def test_save_persists_status_match_and_slides(self):
        job = make_job()
        self.store.create(job)
        job.status = JobStatus.READY
        job.story_text = "we met in the rain"
        job.match = MatchResult(pattern_id="p1", slide_count=2, beats=["x", "y"])
        job.slides = [Slide(index=0, image_path="0.png", caption="hi")]
        self.store.save(job)
        got = self.store.get(job.id)
        self.assertEqual(got.status, JobStatus.READY)
        self.assertEqual(got.story_text, "we met in the rain")
        self.assertEqual(got.match.slide_count, 2)
        self.assertEqual(got.slides[0].caption, "hi")

    def test_get_missing_returns_none(self):
        self.assertIsNone(self.store.get("nope"))

    def test_blob_roundtrip(self):
        job = make_job()
        self.store.create(job)
        path = self.store.save_blob(job.id, "photo0.jpg", b"\x89PNGdata")
        self.assertTrue(Path(path).exists())
        self.assertEqual(self.store.read_blob(path), b"\x89PNGdata")
