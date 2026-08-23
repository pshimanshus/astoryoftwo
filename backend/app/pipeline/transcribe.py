from __future__ import annotations

from app.providers.base import LLMProvider


def story_from_audio(audio_bytes: bytes, mime_type: str, llm: LLMProvider) -> str:
    text = (llm.transcribe(audio_bytes, mime_type) or "").strip()
    if not text:
        raise ValueError("empty transcript")
    return text
