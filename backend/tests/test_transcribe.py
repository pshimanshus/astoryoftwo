import unittest
from app.pipeline.transcribe import story_from_audio
from tests.fakes import FakeLLM


class TranscribeTests(unittest.TestCase):
    def test_returns_transcript(self):
        self.assertEqual(story_from_audio(b"x", "audio/webm", FakeLLM(transcript="we met")), "we met")

    def test_blank_raises(self):
        with self.assertRaises(ValueError):
            story_from_audio(b"x", "audio/webm", FakeLLM(transcript="   "))
