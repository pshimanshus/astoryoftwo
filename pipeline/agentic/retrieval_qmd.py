"""Opt-in QMD adapter.  QMD data is derived and never authoritative."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
from pathlib import Path

from pipeline.agentic.contracts import RecallHit
from pipeline.agentic.retrieval_manifest import build_manifest


def search_qmd(root: Path, query: str, *, limit: int) -> list[RecallHit]:
    if os.getenv("ASOT_RETRIEVAL_QMD_ENABLED") != "1" or not shutil.which("qmd"):
        return []
    try:
        result = subprocess.run(["qmd", "query", query, "--json", "-n", str(limit)], cwd=root,
                                capture_output=True, text=True, timeout=10, check=True)
        payload = json.loads(result.stdout)
    except (OSError, ValueError, subprocess.SubprocessError):
        return []
    by_path = {record.source_path: record for record in build_manifest(root)}
    entries = payload if isinstance(payload, list) else payload.get("results", [])
    hits: list[RecallHit] = []
    for item in entries if isinstance(entries, list) else []:
        path = str(item.get("path") or item.get("file") or "")
        record = by_path.get(path)
        if not record:
            continue
        hits.append(RecallHit(path=record.source_path, title=record.title, kind=record.kind,
                               snippet=record.text[:220], score=float(item.get("score") or 0),
                               confidence=record.confidence, backend="qmd_hybrid", record_id=record.record_id,
                               source_path=record.source_path, source_pointer=record.source_pointer,
                               content_sha256=record.content_sha256, authority=record.authority,
                               lifecycle=record.lifecycle))
    return hits[:limit]
