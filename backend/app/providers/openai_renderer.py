from __future__ import annotations

import base64
import io


class OpenAIRenderer:
    def __init__(self, api_key: str, model: str, client=None):
        self.model = model
        if client is not None:
            self._client = client
        else:
            from openai import OpenAI
            self._client = OpenAI(api_key=api_key)

    def render(self, prompt: str, ref_images: list[bytes], size: str) -> bytes:
        if ref_images:
            resp = self._client.images.edit(
                model=self.model, prompt=prompt, size=size,
                image=[io.BytesIO(b) for b in ref_images],
            )
        else:
            resp = self._client.images.generate(
                model=self.model, prompt=prompt, size=size, n=1,
            )
        return base64.b64decode(resp.data[0].b64_json)
