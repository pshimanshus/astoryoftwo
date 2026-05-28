"""Append-only audit log and file snapshots for agentic decisions."""

from __future__ import annotations

import hashlib
import json
import shutil
from datetime import date
from pathlib import Path

from pipeline.agentic.contracts import AuditEvent


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def snapshot_file(root: Path, relative_path: str) -> Path:
    root = root.resolve()
    source = root / relative_path
    if not source.exists():
        raise FileNotFoundError(relative_path)
    digest = hashlib.sha256(source.read_bytes()).hexdigest()[:16]
    target = root / "memory" / "agentic" / "snapshots" / f"{relative_path.replace('/', '__')}.{digest}.snapshot"
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, target)
    return target


def append_audit_event(
    root: Path,
    *,
    actor: str,
    action: str,
    target_path: str,
    rationale: str,
    evidence_paths: list[str] | None = None,
) -> Path:
    root = root.resolve()
    path = root / "memory" / "agentic" / "audit" / f"{date.today().isoformat()}.jsonl"
    path.parent.mkdir(parents=True, exist_ok=True)
    event = AuditEvent(
        event_id=f"audit-{date.today().isoformat()}-{path.stat().st_size if path.exists() else 0}",
        actor=actor,
        action=action,
        target_path=target_path,
        rationale=rationale,
        evidence_paths=evidence_paths or [],
    )
    with path.open("a", encoding="utf-8") as handle:
        handle.write(event.model_dump_json() + "\n")
    return path
