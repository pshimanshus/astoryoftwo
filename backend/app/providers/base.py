from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol, runtime_checkable


@dataclass
class QAResult:
    passed: bool
    reason: str


@runtime_checkable
class LLMProvider(Protocol):
    def transcribe(self, audio_bytes: bytes, mime_type: str) -> str: ...
    def reason_json(self, system: str, prompt: str,
                    image_bytes: list[bytes] | None = None) -> dict: ...


@runtime_checkable
class Renderer(Protocol):
    def render(self, prompt: str, ref_images: list[bytes], size: str) -> bytes: ...
