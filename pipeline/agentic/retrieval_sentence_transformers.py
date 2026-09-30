"""Opt-in local dense retrieval; dependencies are intentionally optional."""

from __future__ import annotations

import os
from pathlib import Path

from pipeline.agentic.contracts import RecallHit
from pipeline.agentic.retrieval_manifest import build_manifest


def search_local_dense(root: Path, query: str, *, limit: int) -> list[RecallHit]:
    if os.getenv("ASOT_RETRIEVAL_LOCAL_DENSE_ENABLED") != "1":
        return []
    try:
        from sentence_transformers import SentenceTransformer  # type: ignore[import-not-found]
        import numpy as np
    except ImportError:
        return []
    records = build_manifest(root)
    if not records:
        return []
    try:
        model = SentenceTransformer("intfloat/multilingual-e5-base")
        vectors = model.encode([f"passage: {record.text}" for record in records], normalize_embeddings=True)
        query_vector = model.encode([f"query: {query}"], normalize_embeddings=True)[0]
        order = np.argsort(np.asarray(vectors) @ np.asarray(query_vector))[::-1][:limit]
    except Exception:
        return []
    return [RecallHit(path=records[index].source_path, title=records[index].title, kind=records[index].kind,
                      snippet=records[index].text[:220], score=float(vectors[index] @ query_vector),
                      confidence=records[index].confidence, backend="sentence_transformers",
                      record_id=records[index].record_id, source_path=records[index].source_path,
                      source_pointer=records[index].source_pointer, content_sha256=records[index].content_sha256,
                      authority=records[index].authority, lifecycle=records[index].lifecycle) for index in order]
