"""Typed retrieval backends with explicit, observable fallback."""
from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

from pipeline.agentic.contracts import RecallHit
from pipeline.agentic.retrieval_errors import BackendStale, BackendUnavailable

class RetrievalBackend(Protocol):
    name: str
    def availability(self) -> tuple[bool, str]: ...
    def build(self, root: Path) -> Path: ...
    def search(self, root: Path, query: str, limit: int) -> list[RecallHit]: ...

class Fts5Backend:
    name = "fts5"
    def availability(self) -> tuple[bool, str]:
        return True, ""
    def build(self, root: Path) -> Path:
        from pipeline.agentic.memory_index import build_memory_index
        return build_memory_index(root)
    def search(self, root: Path, query: str, limit: int) -> list[RecallHit]:
        from pipeline.agentic.memory_index import search_memory
        return search_memory(self.build(root), query, limit=limit)

@dataclass(frozen=True)
class RetrievalResult:
    requested_backend: str
    actual_backend: str
    evaluated: bool
    hits: list[RecallHit]
    fallback_reason: str = ""

def backend_name(requested: str | None = None) -> str:
    selected = (requested or os.getenv("ASOT_RETRIEVAL_BACKEND", "fts5")).strip().lower()
    aliases = {"qmd_hybrid": "qmd", "local_dense": "sentence_transformers",
               "sentence_transformers_hybrid": "sentence_transformers", "auto": "fts5"}
    return aliases.get(selected, selected)

def get_backend(requested: str | None = None) -> RetrievalBackend:
    selected = backend_name(requested)
    if selected == "fts5":
        return Fts5Backend()
    if selected == "qmd":
        from pipeline.agentic.retrieval_qmd import QmdHybridBackend
        return QmdHybridBackend()
    if selected == "sentence_transformers":
        from pipeline.agentic.retrieval_sentence_transformers import SentenceTransformersHybridBackend
        return SentenceTransformersHybridBackend()
    raise ValueError(f"unknown retrieval backend: {selected}")

def search_with_status(root: Path, query: str, *, limit: int = 8,
                       backend: str | None = None, allow_fallback: bool = True) -> RetrievalResult:
    requested = backend_name(backend)
    candidate = get_backend(requested)
    try:
        available, reason = candidate.availability()
        if not available:
            raise BackendUnavailable(reason)
        hits = candidate.search(root.resolve(), query, limit)
        for hit in hits:
            hit.requested_backend = requested
        return RetrievalResult(requested, candidate.name, True, hits)
    except (BackendUnavailable, BackendStale, OSError, ValueError) as exc:
        if requested == "fts5" or not allow_fallback:
            return RetrievalResult(requested, candidate.name, False, [], str(exc))
        fallback = Fts5Backend().search(root.resolve(), query, limit)
        reason = f"{type(exc).__name__}: {exc}"
        for hit in fallback:
            hit.requested_backend = requested
            hit.fallback_reason = reason
        return RetrievalResult(requested, "fts5", False, fallback, reason)

def search(root: Path, query: str, *, limit: int = 8,
           backend: str | None = None) -> list[RecallHit]:
    return search_with_status(root, query, limit=limit, backend=backend, allow_fallback=True).hits
