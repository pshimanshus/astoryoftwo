"""Incremental SQLite FTS5 index over the shared retrieval manifest."""
from __future__ import annotations

import json
import os
import re
import shutil
import sqlite3
import tempfile
from datetime import datetime, timezone
from pathlib import Path

from pipeline.agentic.contracts import RecallHit
from pipeline.agentic.retrieval_manifest import (
    ManifestRecord,
    collect_source_files,
    load_manifest,
)
from pipeline.agentic.retrieval_filters import (
    parse_retrieval_filters,
    record_is_eligible,
    scope_priority,
)

DEFAULT_INDEX_PATH = Path("memory/agentic/index/memory.sqlite3")
INDEX_SCHEMA = "fts5-manifest-index/v2"

def collect_indexable_files(root: Path) -> list[tuple[Path, str]]:
    """Compatibility inventory; the manifest remains the only indexed corpus."""
    return [(path, kind) for path, kind, _authority, _lifecycle in collect_source_files(root.resolve())]

def _state_path(index: Path) -> Path:
    return index.with_suffix(index.suffix + ".state.json")

def _schema_current(path: Path) -> bool:
    if not path.is_file():
        return False
    try:
        with sqlite3.connect(path) as conn:
            value = conn.execute("SELECT value FROM metadata WHERE key='schema_version'").fetchone()
        return bool(value and value[0] == INDEX_SCHEMA)
    except sqlite3.Error:
        return False

def _create_schema(conn: sqlite3.Connection) -> None:
    conn.execute("CREATE TABLE metadata(key TEXT PRIMARY KEY, value TEXT NOT NULL)")
    conn.execute("INSERT INTO metadata(key,value) VALUES('schema_version',?)", (INDEX_SCHEMA,))
    conn.execute(
        "CREATE VIRTUAL TABLE memory USING fts5("
        "record_id UNINDEXED, path UNINDEXED, title, kind UNINDEXED, text, "
        "confidence UNINDEXED, scope UNINDEXED, captured_at UNINDEXED, "
        "feedback_ids UNINDEXED, package_path UNINDEXED, source_pointer UNINDEXED, "
        "content_sha256 UNINDEXED, authority UNINDEXED, lifecycle UNINDEXED, "
        "eligible_roles UNINDEXED, tokenize='unicode61 remove_diacritics 2')"
    )

def _insert(conn: sqlite3.Connection, record: ManifestRecord) -> None:
    conn.execute(
        "INSERT INTO memory(record_id,path,title,kind,text,confidence,scope,captured_at,feedback_ids,"
        "package_path,source_pointer,content_sha256,authority,lifecycle,eligible_roles) "
        "VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
        (record.record_id, record.legacy_path, record.title, record.kind, record.text,
         record.confidence, record.scope, record.captured_at, json.dumps(record.feedback_ids),
         record.package, record.source_pointer, record.content_sha256, record.authority,
         record.lifecycle, json.dumps(record.eligible_roles)),
    )

def build_memory_index(root: Path, index_path: Path | None = None) -> Path:
    root = root.resolve()
    index = root / (index_path or DEFAULT_INDEX_PATH)
    index.parent.mkdir(parents=True, exist_ok=True)
    # Keep the historical failure seam while collecting no second corpus.
    collect_indexable_files(root)
    _manifest_path, records, digest = load_manifest(root)
    state_path = _state_path(index)
    if index.is_file() and state_path.is_file() and _schema_current(index):
        try:
            state = json.loads(state_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            state = {}
        if state.get("manifest_sha256") == digest:
            return index

    descriptor, temporary_name = tempfile.mkstemp(prefix=f".{index.name}.", suffix=".tmp", dir=index.parent)
    os.close(descriptor)
    temporary = Path(temporary_name)
    conn: sqlite3.Connection | None = None
    try:
        if _schema_current(index):
            shutil.copy2(index, temporary)
            conn = sqlite3.connect(temporary)
        else:
            temporary.unlink(missing_ok=True)
            conn = sqlite3.connect(temporary)
            _create_schema(conn)
        existing = {str(row[0]) for row in conn.execute("SELECT record_id FROM memory")}
        desired = {record.record_id for record in records}
        for record_id in sorted(existing - desired):
            conn.execute("DELETE FROM memory WHERE record_id=?", (record_id,))
        by_id = {record.record_id: record for record in records}
        for record_id in sorted(desired - existing):
            _insert(conn, by_id[record_id])
        conn.execute("INSERT OR REPLACE INTO metadata(key,value) VALUES('manifest_sha256',?)", (digest,))
        conn.commit()
        conn.execute("PRAGMA optimize")
        conn.close()
        conn = None
        os.replace(temporary, index)
        state_payload = {"schema_version": INDEX_SCHEMA, "manifest_sha256": digest,
                         "record_count": len(records)}
        state_tmp = state_path.with_suffix(state_path.suffix + ".tmp")
        state_tmp.write_text(json.dumps(state_payload, sort_keys=True) + "\n", encoding="utf-8")
        os.replace(state_tmp, state_path)
    finally:
        if conn is not None:
            conn.close()
        temporary.unlink(missing_ok=True)
    return index

def _snippet(text: str, query: str, kind: str) -> str:
    if kind == "carousel_pattern":
        from pipeline.stages.carousel_patterns import pattern_recall_snippet
        return pattern_recall_snippet(text)
    if kind == "carousel_result":
        return text[:1200].replace("\n", " ").strip()
    lowered = text.casefold()
    positions = [lowered.find(term.casefold()) for term in re.findall(r"\w+", query, re.UNICODE)
                 if len(term) > 1 and lowered.find(term.casefold()) >= 0]
    start = max(0, min(positions) - 80) if positions else 0
    return text[start:start + 300].replace("\n", " ").strip()

def search_memory(index_path: Path, query: str, limit: int = 8) -> list[RecallHit]:
    if limit <= 0:
        return []
    filters = parse_retrieval_filters(query)
    lexical = filters.lexical_query
    terms = [term for term in re.findall(r"\w+", lexical, re.UNICODE) if len(term) > 1]
    match_query = " OR ".join('"' + term.replace('"', '""') + '"*' for term in terms)
    columns = ("record_id,path,title,kind,text,confidence,scope,captured_at,feedback_ids,package_path,"
               "source_pointer,content_sha256,authority,lifecycle,eligible_roles,bm25(memory) AS score")
    with sqlite3.connect(index_path) as conn:
        if terms:
            try:
                rows = conn.execute(f"SELECT {columns} FROM memory WHERE memory MATCH ? ORDER BY score LIMIT ?",
                                    (match_query, max(64, limit * 12))).fetchall()
            except sqlite3.OperationalError:
                rows = conn.execute(f"SELECT {columns} FROM memory WHERE " + " OR ".join("text LIKE ?" for _ in terms),
                                    (*[f"%{term}%" for term in terms],)).fetchall()
        elif filters.package:
            rows = conn.execute(f"SELECT {columns} FROM memory LIMIT ?", (max(64, limit * 12),)).fetchall()
        else:
            return []

    def eligible(row: tuple[object, ...]) -> bool:
        return record_is_eligible(
            package=str(row[9] or ""),
            eligible_roles=json.loads(str(row[14] or "[]")),
            filters=filters,
        )

    def rank(row: tuple[object, ...]) -> tuple[float, str]:
        score = float(row[15] or 0.0)
        if filters.package:
            score -= 3.0
        score -= 2.0 * scope_priority(str(row[6] or ""), filters.scope)
        if row[3] in {"creator_correction", "learning_event"} and row[7]:
            try:
                captured = datetime.fromisoformat(str(row[7]).replace("Z", "+00:00"))
                if captured.tzinfo is None:
                    captured = captured.replace(tzinfo=timezone.utc)
                age = max(0.0, (datetime.now(timezone.utc) - captured).total_seconds() / 86400)
                score -= max(0.0, 1.0 - min(age, 365.0) / 365.0)
            except ValueError:
                pass
        return score, str(row[0])

    candidates = sorted((row for row in rows if eligible(row)), key=rank)
    # Linked learning-event and correction records remain independently eligible;
    # collapse them only when both matched this query, preferring the correction.
    unlinked: list[tuple[object, ...]] = []
    by_feedback: dict[str, tuple[object, ...]] = {}
    for row in candidates:
        feedback = next(iter(json.loads(str(row[8] or "[]"))), "")
        if not feedback:
            unlinked.append(row)
            continue
        current = by_feedback.get(feedback)
        if current is None or (row[3] == "creator_correction" and current[3] != "creator_correction"):
            by_feedback[feedback] = row
    ranked = sorted([*unlinked, *by_feedback.values()], key=rank)[:limit]
    hits = []
    for row in ranked:
        path = str(row[1])
        source_path = path.partition("#")[0]
        hits.append(RecallHit(
            path=path, title=str(row[2]), kind=str(row[3]),
            snippet=_snippet(str(row[4]), lexical, str(row[3])), confidence=float(row[5] or 0.5),
            score=rank(row)[0], backend="fts5", requested_backend="fts5",
            record_id=str(row[0]), source_path=source_path, source_pointer=str(row[10]),
            content_sha256=str(row[11]), authority=str(row[12]), lifecycle=str(row[13]),
            scope=str(row[6] or ""), package=str(row[9] or ""),
            feedback_ids=list(json.loads(str(row[8] or "[]"))),
        ))
    return hits
