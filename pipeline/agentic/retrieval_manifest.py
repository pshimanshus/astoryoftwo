"""Build the single, derived corpus used by every recall backend.

The manifest is deliberately not a source of truth.  It is a reproducible,
hash-bound projection of eligible repository records.
"""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import asdict, dataclass
from pathlib import Path


MANIFEST_VERSION = "retrieval-manifest/v1"
MANIFEST_PATH = Path("memory/agentic/index/retrieval-manifest.json")
SOURCE_GLOBS = (
    ("memory/working.md", "working", "reviewed_observation", "active"),
    ("memory/semantic/*.md", "semantic", "approved_preference", "active"),
    ("wiki/**/*.md", "wiki", "reviewed_observation", "active"),
    ("config/rules/*.md", "rule", "canonical", "active"),
    ("config/skills/*.md", "skill", "workflow", "active"),
    (".agents/skills/**/SKILL.md", "repo_skill", "workflow", "active"),
    (".codex/agents/*.toml", "agent", "workflow", "active"),
    ("agents/*.md", "agent_reference", "historical", "history"),
    ("output/reports/carousel-results/*.json", "carousel_result", "reviewed_observation", "active"),
    ("memory/agentic/learning-events/*.json", "learning_event", "reviewed_observation", "active"),
    ("output/carousels/**/creator-correction.json", "creator_correction", "approved_preference", "active"),
)
SMOKE_RE = re.compile(r"(?:smoke|dry-run|audit-refresh|pipeline-repair)", re.I)


@dataclass(frozen=True)
class ManifestRecord:
    record_id: str
    source_path: str
    source_pointer: str
    title: str
    kind: str
    text: str
    content_sha256: str
    authority: str
    lifecycle: str
    chunk_start_line: int
    chunk_end_line: int
    confidence: float = 0.5


def _sha(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _title(text: str, fallback: str) -> str:
    match = re.search(r"(?m)^#\s+(.+?)\s*$", text)
    return match.group(1).strip() if match else fallback


def _confidence(text: str) -> float:
    match = re.search(r"(?m)^confidence:\s*(0(?:\.\d+)?|1(?:\.0+)?)\s*$", text)
    return float(match.group(1)) if match else 0.5


def _chunks(text: str) -> list[tuple[int, int, str]]:
    lines = text.splitlines()
    groups: list[tuple[int, int, str]] = []
    start = 0
    bucket: list[str] = []
    for index, line in enumerate(lines, start=1):
        if bucket and (line.startswith("#") or (not line.strip() and len("\n".join(bucket)) > 700)):
            groups.append((start or 1, index - 1, "\n".join(bucket).strip()))
            bucket, start = [], index
        if not bucket:
            start = index
        bucket.append(line)
    if bucket:
        groups.append((start, len(lines), "\n".join(bucket).strip()))
    return [(first, last, body) for first, last, body in groups if body]


def build_manifest(root: Path, *, include_history: bool = False) -> list[ManifestRecord]:
    root = root.resolve()
    files: dict[Path, tuple[str, str, str]] = {}
    for pattern, kind, authority, lifecycle in SOURCE_GLOBS:
        if lifecycle == "history" and not include_history:
            continue
        for path in sorted(root.glob(pattern)):
            if path.is_file() and path not in files:
                files[path] = (kind, authority, lifecycle)
    records: list[ManifestRecord] = []
    for path, (kind, authority, lifecycle) in sorted(files.items()):
        relative = path.relative_to(root).as_posix()
        if SMOKE_RE.search(relative):
            continue
        text = path.read_text(encoding="utf-8", errors="ignore")
        source_hash = _sha(text)
        for first, last, body in _chunks(text):
            pointer = f"lines:{first}-{last}"
            record_id = _sha(f"{relative}:{pointer}:{source_hash}")[:24]
            records.append(ManifestRecord(record_id, relative, pointer, _title(text, path.stem), kind, body,
                                          source_hash, authority, lifecycle, first, last, _confidence(text)))
    return records


def write_manifest(root: Path, *, include_history: bool = False, path: Path | None = None) -> tuple[Path, list[ManifestRecord]]:
    root = root.resolve()
    records = build_manifest(root, include_history=include_history)
    destination = root / (path or MANIFEST_PATH)
    destination.parent.mkdir(parents=True, exist_ok=True)
    payload = {"schema_version": MANIFEST_VERSION, "records": [asdict(record) for record in records]}
    destination.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return destination, records
