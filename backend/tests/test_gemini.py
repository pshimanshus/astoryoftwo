import json
import unittest
from unittest.mock import MagicMock

from app.providers.gemini import GeminiProvider


class GeminiTests(unittest.TestCase):
    def _provider(self, text):
        client = MagicMock()
        resp = MagicMock()
        resp.text = text
        client.models.generate_content.return_value = resp
        return GeminiProvider(api_key="k", model="gemini-2.5-flash", client=client), client

    def test_reason_json_parses_object(self):
        p, client = self._provider('{"pattern_id": "p1", "slide_count": 3}')
        out = p.reason_json("sys", "match this")
        self.assertEqual(out["slide_count"], 3)
        client.models.generate_content.assert_called_once()
        kwargs = client.models.generate_content.call_args.kwargs
        self.assertEqual(kwargs["model"], "gemini-2.5-flash")

    def test_reason_json_strips_code_fence(self):
        p, _ = self._provider('```json\n{"ok": true}\n```')
        self.assertEqual(p.reason_json("s", "p"), {"ok": True})

    def test_transcribe_returns_text(self):
        p, client = self._provider("we met in the rain")
        self.assertEqual(p.transcribe(b"audiobytes", "audio/webm"), "we met in the rain")
