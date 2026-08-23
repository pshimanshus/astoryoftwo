import io
import tempfile
import unittest
from pathlib import Path

from fastapi.testclient import TestClient

from app import deps
from app.main import app
from app.store import JobStore
from tests.fakes import FakeLLM, FakeRenderer


class ApiTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        root = Path(self.tmp.name)
        self.store = JobStore(db_path=root / "j.db", blob_root=root / "b")
        self.llm = FakeLLM(transcript="we met", responses=[
            {"pattern_id": "p", "slide_count": 3, "beats": ["x", "y", "z"]},
            {"slides": [{"image_prompt": "a", "on_image_text": "t0"},
                        {"image_prompt": "b", "on_image_text": "t1"},
                        {"image_prompt": "c", "on_image_text": "t2"}]},
            {"passed": True, "reason": "ok"}, {"passed": True, "reason": "ok"},
            {"passed": True, "reason": "ok"},
        ])
        app.dependency_overrides[deps.get_store] = lambda: self.store
        app.dependency_overrides[deps.get_llm] = lambda: self.llm
        app.dependency_overrides[deps.get_renderer] = lambda: FakeRenderer(image=b"IMG")
        app.dependency_overrides[deps.get_bank] = lambda: [{"caption": "x", "childCount": 3}]

    def tearDown(self):
        app.dependency_overrides.clear()
        self.tmp.cleanup()

    def _submit(self, client):
        files = [("photos", ("p.jpg", io.BytesIO(b"PHOTO"), "image/jpeg")),
                 ("audio", ("v.webm", io.BytesIO(b"AUDIO"), "audio/webm"))]
        data = dict(device_id="d", delivery_contact="c", creator_name="A", partner_name="B",
                    relationship="together", setting_choice="fresh", quote_mode="agent", quote_copy="")
        return client.post("/jobs", files=files, data=data)

    def test_submit_returns_job_id(self):
        with TestClient(app) as client:
            r = self._submit(client)
        self.assertEqual(r.status_code, 200)
        self.assertIn("job_id", r.json())

    def test_poll_reaches_ready_with_slides(self):
        with TestClient(app) as client:
            job_id = self._submit(client).json()["job_id"]
            r = client.get(f"/jobs/{job_id}")
        body = r.json()
        self.assertEqual(body["status"], "ready")
        self.assertEqual(len(body["slides"]), 3)
        self.assertTrue(body["slides"][0]["url"].endswith("/slides/0.png"))

    def test_slide_image_streams(self):
        with TestClient(app) as client:
            job_id = self._submit(client).json()["job_id"]
            r = client.get(f"/jobs/{job_id}/slides/0.png")
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.content, b"IMG")

    def test_unknown_job_404(self):
        with TestClient(app) as client:
            self.assertEqual(client.get("/jobs/nope").status_code, 404)
