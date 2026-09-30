"""Persisted, incremental multilingual E5 index fused with FTS5 by RRF."""
from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from pipeline.agentic.contracts import RecallHit
from pipeline.agentic.memory_index import build_memory_index, search_memory
from pipeline.agentic.retrieval_errors import BackendStale, BackendUnavailable
from pipeline.agentic.retrieval_manifest import ManifestRecord, load_manifest
from pipeline.agentic.retrieval_filters import (
    parse_retrieval_filters,
    record_is_eligible,
    scope_priority,
)

LOCAL_DIR = Path("memory/agentic/index/local-dense")
MODEL_ID = "intfloat/multilingual-e5-base"
_MODEL_CACHE: dict[str, Any] = {}

def _numpy():
    try:
        import numpy as np  # type: ignore[import-not-found]
    except ImportError as exc:
        raise BackendUnavailable("numpy is unavailable for local dense retrieval") from exc
    return np

def _model():
    if MODEL_ID in _MODEL_CACHE:
        return _MODEL_CACHE[MODEL_ID]
    try:
        from sentence_transformers import SentenceTransformer  # type: ignore[import-not-found]
    except ImportError as exc:
        raise BackendUnavailable("sentence-transformers is unavailable") from exc
    _MODEL_CACHE[MODEL_ID] = SentenceTransformer(MODEL_ID)
    return _MODEL_CACHE[MODEL_ID]

def _normalize(vectors: Any) -> Any:
    np = _numpy()
    values = np.asarray(vectors, dtype="float32")
    if values.ndim == 1:
        values = values.reshape(1, -1)
    norms = np.linalg.norm(values, axis=1, keepdims=True)
    norms[norms == 0] = 1.0
    return values / norms

def _encode(encoder: Any, texts: list[str]) -> Any:
    try:
        values = encoder.encode(texts, normalize_embeddings=True)
    except TypeError:
        values = encoder.encode(texts)
    return _normalize(values)

class SentenceTransformersHybridBackend:
    name = "sentence_transformers_hybrid"

    def __init__(self, *, encoder: Any | None = None) -> None:
        self.encoder = encoder

    def availability(self) -> tuple[bool, str]:
        if os.getenv("ASOT_RETRIEVAL_LOCAL_DENSE_ENABLED") != "1" and self.encoder is None:
            return False, "ASOT_RETRIEVAL_LOCAL_DENSE_ENABLED is not 1"
        try:
            _numpy()
            if self.encoder is None:
                import sentence_transformers  # type: ignore[import-not-found]  # noqa: F401
        except (BackendUnavailable, ImportError) as exc:
            return False, str(exc)
        return True, ""

    def build(self, root: Path) -> Path:
        available, reason = self.availability()
        if not available:
            raise BackendUnavailable(reason)
        np = _numpy()
        encoder = self.encoder or _model()
        root = root.resolve()
        _manifest, records, digest = load_manifest(root)
        directory = root / LOCAL_DIR
        directory.mkdir(parents=True, exist_ok=True)
        vectors_path, state_path = directory / "vectors.npz", directory / "state.json"
        old: dict[str, Any] = {}
        if vectors_path.is_file() and state_path.is_file():
            try:
                state = json.loads(state_path.read_text(encoding="utf-8"))
                data = np.load(vectors_path, allow_pickle=False)
                if state.get("model_id") == MODEL_ID:
                    old = {record_id: vector for record_id, vector in zip(state.get("record_ids") or [], data["vectors"])}
            except (OSError, ValueError, KeyError, json.JSONDecodeError):
                old = {}
        missing = [record for record in records if record.record_id not in old]
        if missing:
            encoded = _encode(encoder, [f"passage: {record.text}" for record in missing])
            old.update({record.record_id: encoded[index] for index, record in enumerate(missing)})
        if records:
            vectors = np.vstack([old[record.record_id] for record in records]).astype("float32")
        else:
            vectors = np.empty((0, 0), dtype="float32")
        temporary = directory / "vectors.tmp.npz"
        np.savez_compressed(temporary, vectors=vectors)
        os.replace(temporary, vectors_path)
        state = {"schema_version": "local-dense-index/v1", "manifest_sha256": digest,
                 "model_id": MODEL_ID, "record_ids": [record.record_id for record in records],
                 "record_count": len(records), "dimensions": int(vectors.shape[1]) if vectors.ndim == 2 and len(vectors) else 0}
        state_path.write_text(json.dumps(state, sort_keys=True) + "\n", encoding="utf-8")
        return directory

    def _load(self, root: Path) -> tuple[list[ManifestRecord], Any]:
        np = _numpy()
        _manifest, records, digest = load_manifest(root)
        directory = root / LOCAL_DIR
        state_path, vectors_path = directory / "state.json", directory / "vectors.npz"
        if not state_path.is_file() or not vectors_path.is_file():
            raise BackendStale("local dense index has not been built")
        try:
            state = json.loads(state_path.read_text(encoding="utf-8"))
            vectors = np.load(vectors_path, allow_pickle=False)["vectors"]
        except (OSError, ValueError, KeyError, json.JSONDecodeError) as exc:
            raise BackendStale("local dense index is unreadable") from exc
        if (state.get("manifest_sha256") != digest or state.get("model_id") != MODEL_ID
                or state.get("record_ids") != [record.record_id for record in records]
                or len(vectors) != len(records)):
            raise BackendStale("local dense index is stale for the current manifest")
        return records, vectors

    def search(self, root: Path, query: str, limit: int) -> list[RecallHit]:
        available, reason = self.availability()
        if not available:
            raise BackendUnavailable(reason)
        np = _numpy()
        encoder = self.encoder or _model()
        root = root.resolve()
        records, vectors = self._load(root)
        filters = parse_retrieval_filters(query)
        lexical = filters.lexical_query
        if not lexical or not records:
            dense_ids: list[str] = []
        else:
            query_vector = _encode(encoder, [f"query: {lexical}"])[0]
            scores = vectors @ query_vector
            eligible = []
            for index, record in enumerate(records):
                if not record_is_eligible(
                    package=record.package,
                    eligible_roles=record.eligible_roles,
                    filters=filters,
                ):
                    continue
                eligible.append((scope_priority(record.scope, filters.scope),
                                 float(scores[index]), record.record_id))
            dense_ids = [record_id for _scope, _score, record_id
                         in sorted(eligible, reverse=True)[:max(20, limit * 4)]]
        lexical_hits = search_memory(build_memory_index(root), query, limit=max(20, limit * 4))
        ranks: dict[str, float] = {}
        for rank, record_id in enumerate(dense_ids, 1):
            ranks[record_id] = ranks.get(record_id, 0.0) + 1.0 / (60 + rank)
        lexical_by_id = {hit.record_id: hit for hit in lexical_hits}
        for rank, hit in enumerate(lexical_hits, 1):
            ranks[hit.record_id] = ranks.get(hit.record_id, 0.0) + 1.0 / (60 + rank)
        by_id = {record.record_id: record for record in records}
        hits: list[RecallHit] = []
        for record_id, score in sorted(ranks.items(), key=lambda item: (-item[1], item[0]))[:limit]:
            record = by_id.get(record_id)
            if record is None:
                continue
            lexical_hit = lexical_by_id.get(record_id)
            hits.append(RecallHit(
                path=record.legacy_path, title=record.title, kind=record.kind,
                snippet=(lexical_hit.snippet if lexical_hit else record.text[:300].replace("\n", " ")),
                score=score, confidence=record.confidence, backend=self.name,
                requested_backend="sentence_transformers", record_id=record.record_id,
                source_path=record.source_path, source_pointer=record.source_pointer,
                content_sha256=record.content_sha256, authority=record.authority,
                lifecycle=record.lifecycle, scope=record.scope, package=record.package,
                feedback_ids=list(record.feedback_ids)))
        return hits

def build_local_dense_index(root: Path, *, encoder: Any | None = None) -> Path:
    return SentenceTransformersHybridBackend(encoder=encoder).build(root)

def search_local_dense(root: Path, query: str, *, limit: int,
                       encoder: Any | None = None) -> list[RecallHit]:
    return SentenceTransformersHybridBackend(encoder=encoder).search(root, query, limit)
