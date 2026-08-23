from __future__ import annotations

import json


class GeminiProvider:
    def __init__(self, api_key: str, model: str, client=None):
        self.model = model
        if client is not None:
            self._client = client
            self._types = None
        else:
            from google import genai
            from google.genai import types
            self._client = genai.Client(api_key=api_key)
            self._types = types

    def _part_from_bytes(self, data: bytes, mime: str):
        if self._types is not None:
            return self._types.Part.from_bytes(data=data, mime_type=mime)
        return {"inline_data": {"mime_type": mime, "data": data}}

    def transcribe(self, audio_bytes: bytes, mime_type: str) -> str:
        contents = [
            self._part_from_bytes(audio_bytes, mime_type),
            "Transcribe this voice note into plain text. Return only the words spoken.",
        ]
        resp = self._client.models.generate_content(model=self.model, contents=contents)
        return (resp.text or "").strip()

    def reason_json(self, system: str, prompt: str, image_bytes: list[bytes] | None = None) -> dict:
        contents: list = [f"{system}\n\n{prompt}"]
        for img in image_bytes or []:
            contents.append(self._part_from_bytes(img, "image/png"))
        config = None
        if self._types is not None:
            config = self._types.GenerateContentConfig(response_mime_type="application/json")
        resp = self._client.models.generate_content(model=self.model, contents=contents, config=config)
        return _parse_json(resp.text or "{}")


def _parse_json(text: str) -> dict:
    t = text.strip()
    if t.startswith("```"):
        t = t.split("```", 2)[1]
        if t.startswith("json"):
            t = t[4:]
        t = t.strip().rstrip("`").strip()
    return json.loads(t)
