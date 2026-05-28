"""SQLite FTS memory index for meaning-oriented repo recall."""

from __future__ import annotations

import re
import sqlite3
from pathlib import Path

from pipeline.agentic.contracts import RecallHit


DEFAULT_INDEX_PATH = Path("memory/agentic/index/memory.sqlite3")
INDEXED_GLOBS = (
    ("memory/working.md", "working"),
    ("memory/semantic/*.md", "semantic"),
    ("wiki/**/*.md", "wiki"),
    ("config/skills/*.md", "skill"),
    ("agents/*.md", "agent"),
    ("docs/**/*.md", "doc"),
    ("output/reports/*.md", "report"),
)


def title_for(text: str, fallback: str) -> str:
    match = re.search(r"(?m)^#\s+(.+?)\s*$", text)
    return match.group(1).strip() if match else fallback


def confidence_for(text: str) -> float:
    match = re.search(r"(?m)^confidence:\s*(0(?:\.\d+)?|1(?:\.0+)?)\s*$", text)
    return float(match.group(1)) if match else 0.5


def collect_indexable_files(root: Path) -> list[tuple[Path, str]]:
    seen: set[Path] = set()
    files: list[tuple[Path, str]] = []
    for pattern, kind in INDEXED_GLOBS:
        for path in sorted(root.glob(pattern)):
            if path.is_file() and path not in seen:
                seen.add(path)
                files.append((path, kind))
    return files


def build_memory_index(root: Path, index_path: Path | None = None) -> Path:
    root = root.resolve()
    index = root / (index_path or DEFAULT_INDEX_PATH)
    index.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(index)
    try:
        conn.execute("DROP TABLE IF EXISTS memory")
        conn.execute(
            "CREATE VIRTUAL TABLE memory USING fts5(path, title, kind, text, tags, confidence UNINDEXED)"
        )
        for path, kind in collect_indexable_files(root):
            text = path.read_text(encoding="utf-8", errors="ignore")
            relative = path.relative_to(root).as_posix()
            conn.execute(
                "INSERT INTO memory(path, title, kind, text, tags, confidence) VALUES (?, ?, ?, ?, ?, ?)",
                (
                    relative,
                    title_for(text, path.stem),
                    kind,
                    text,
                    " ".join([kind, path.stem]),
                    confidence_for(text),
                ),
            )
        conn.commit()
    finally:
        conn.close()
    return index


def snippet(text: str, query: str) -> str:
    lowered = text.lower()
    terms = [term.lower() for term in re.findall(r"[A-Za-z0-9]+", query)]
    positions = [lowered.find(term) for term in terms if lowered.find(term) >= 0]
    start = max(0, min(positions) - 80) if positions else 0
    return text[start : start + 220].replace("\n", " ").strip()


def search_memory(index_path: Path, query: str, limit: int = 8) -> list[RecallHit]:
    conn = sqlite3.connect(index_path)
    terms = [term for term in re.findall(r"[A-Za-z0-9]+", query) if len(term) > 2]
    match_query = " OR ".join(f"{term}*" for term in terms) if terms else query
    try:
        rows = conn.execute(
            """
            SELECT path, title, kind, text, confidence, bm25(memory) AS score
            FROM memory
            WHERE memory MATCH ?
            ORDER BY score
            LIMIT ?
            """,
            (match_query, limit),
        ).fetchall()
    except sqlite3.OperationalError:
        if not terms:
            return []
        rows = conn.execute(
            f"""
            SELECT path, title, kind, text, confidence, 0.0 AS score
            FROM memory
            WHERE {' OR '.join('text LIKE ?' for _ in terms)}
            LIMIT ?
            """,
            (*[f"%{term}%" for term in terms], limit),
        ).fetchall()
    finally:
        conn.close()

    return [
        RecallHit(
            path=row[0],
            title=row[1],
            kind=row[2],
            snippet=snippet(row[3], query),
            confidence=float(row[4] or 0.5),
            score=float(row[5] or 0.0),
        )
        for row in rows
    ]
