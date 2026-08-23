from __future__ import annotations


class FakeLLM:
    def __init__(self, transcript: str = "", responses: list[dict] | None = None):
        self._transcript = transcript
        self._responses = list(responses or [])
        self.calls: list[tuple[str, str, int]] = []

    def transcribe(self, audio_bytes: bytes, mime_type: str) -> str:
        return self._transcript

    def reason_json(self, system: str, prompt: str, image_bytes=None) -> dict:
        self.calls.append((system, prompt, len(image_bytes or [])))
        return self._responses.pop(0) if self._responses else {}


class FakeRenderer:
    def __init__(self, image: bytes = b"PNG"):
        self._image = image
        self.prompts: list[str] = []

    def render(self, prompt: str, ref_images, size: str) -> bytes:
        self.prompts.append(prompt)
        return self._image
