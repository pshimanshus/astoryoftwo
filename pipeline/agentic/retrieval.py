"""Backend router for derived, cited long-term recall."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Protocol

from pipeline.agentic.contracts import RecallHit


class RetrievalBackend(Protocol):
    name: str

    def build(self, root: Path) -> Path: ...
    def search(self, root: Path, query: str, limit: int) -> list[RecallHit]: ...


def backend_name(requested: str | None = None) -> str:
    return (requested or os.getenv("ASOT_RETRIEVAL_BACKEND", "fts5")).strip().lower()


def search(root: Path, query: str, *, limit: int = 8, backend: str | None = None) -> list[RecallHit]:
    selected = backend_name(backend)
    if selected in {"qmd", "qmd_hybrid"}:
        from pipeline.agentic.retrieval_qmd import search_qmd
        hits = search_qmd(root, query, limit=limit)
        if hits:
            return hits
    elif selected in {"sentence_transformers", "local_dense"}:
        from pipeline.agentic.retrieval_sentence_transformers import search_local_dense
        hits = search_local_dense(root, query, limit=limit)
        if hits:
            return hits
    from pipeline.agentic.memory_index import build_memory_index, search_memory
    return search_memory(build_memory_index(root), query, limit=limit)
