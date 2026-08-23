from __future__ import annotations

from functools import lru_cache

from app.config import settings
from app.data_refs import load_winner_bank
from app.providers.gemini import GeminiProvider
from app.providers.openai_renderer import OpenAIRenderer
from app.store import JobStore


@lru_cache
def get_store() -> JobStore:
    return JobStore(db_path=settings.data_dir / "jobs.db", blob_root=settings.data_dir / "blobs")


def get_llm():
    return GeminiProvider(api_key=settings.gemini_api_key, model=settings.gemini_model)


def get_renderer():
    return OpenAIRenderer(api_key=settings.openai_api_key, model=settings.image_model)


@lru_cache
def get_bank() -> list[dict]:
    return load_winner_bank()
