"""Deterministic, hash-bound corpus shared by every retrieval backend."""
from __future__ import annotations

import hashlib
import json
import os
import re
import tempfile
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable

MANIFEST_VERSION = "retrieval-manifest/v2"
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
    chunk_start_line: int = 0
    chunk_end_line: int = 0
    confidence: float = 0.5
    scope: str = ""
    package: str = ""
    feedback_ids: tuple[str, ...] = ()
    supersedes_feedback_ids: tuple[str, ...] = ()
    captured_at: str = ""
    eligible_roles: tuple[str, ...] = ("*",)
    legacy_fragment: str = ""

    @property
    def legacy_path(self) -> str:
        if self.legacy_fragment:
            return f"{self.source_path}#{self.legacy_fragment}"
        if self.kind == "creator_correction" and self.feedback_ids:
            return f"{self.source_path}#{self.feedback_ids[0]}"
        return self.source_path

def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()

def canonical_manifest_digest(records: Iterable[ManifestRecord]) -> str:
    payload = [asdict(record) for record in records]
    return sha256_bytes(json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode())

def _record_id(relative: str, pointer: str, source_hash: str) -> str:
    return sha256_bytes(f"{relative}:{pointer}:{source_hash}".encode())[:24]

def _title(text: str, fallback: str) -> str:
    match = re.search(r"(?m)^#\s+(.+?)\s*$", text)
    return match.group(1).strip() if match else fallback

def _confidence(text: str) -> float:
    match = re.search(r"(?m)^confidence:\s*(0(?:\.\d+)?|1(?:\.0+)?)\s*$", text)
    return float(match.group(1)) if match else 0.5

def _chunks(text: str) -> list[tuple[int, int, str]]:
    """Heading/paragraph chunks; a heading is retained with its following text."""
    lines = text.splitlines()
    if not lines:
        return []
    result: list[tuple[int, int, str]] = []
    start = 1
    for line_no, line in enumerate(lines, 1):
        current = "\n".join(lines[start - 1:line_no])
        boundary = line_no > start and (line.startswith("#") or (not line.strip() and len(current) >= 900))
        if boundary:
            previous_end = line_no - 1 if line.startswith("#") else line_no
            body = "\n".join(lines[start - 1:previous_end]).strip()
            if body:
                result.append((start, previous_end, body))
            start = line_no if line.startswith("#") else line_no + 1
    if start <= len(lines):
        body = "\n".join(lines[start - 1:]).strip()
        if body:
            result.append((start, len(lines), body))
    return result

def collect_source_files(root: Path, *, include_history: bool = False) -> list[tuple[Path, str, str, str]]:
    files: dict[Path, tuple[str, str, str]] = {}
    for pattern, kind, authority, lifecycle in SOURCE_GLOBS:
        if lifecycle == "history" and not include_history:
            continue
        for path in sorted(root.glob(pattern)):
            if path.is_file() and path not in files and not SMOKE_RE.search(path.relative_to(root).as_posix()):
                files[path] = (kind, authority, lifecycle)
    return [(path, *metadata) for path, metadata in sorted(files.items())]

def _strings(value: object) -> list[str]:
    return [str(item) for item in value if item] if isinstance(value, list) else ([str(value)] if value else [])

def _creator_text(event: dict[str, object]) -> str:
    values: list[str] = []
    for key in ("user_instruction_exact", "primary_diagnosis", "root_cause", "desired_behavior",
                "must_change", "must_preserve", "corrections", "rejected_route_phrases"):
        values.extend(_strings(event.get(key)))
    return "\n".join(values)

def _retirement_sets(root: Path) -> tuple[dict[str, set[str]], dict[str, set[str]]]:
    from pipeline.stages.carousel_visual_storytelling import successor_feedback_retirement_status
    feedback: dict[str, set[str]] = {}
    learning: dict[str, set[str]] = {}
    for path in root.glob("output/carousels/**/creator-correction.json"):
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        if not isinstance(payload, dict) or "successor_retirement" not in payload:
            continue
        status = successor_feedback_retirement_status(path.parent, workspace_root=root)
        if status.get("retired"):
            package = str(status.get("package_path") or "").strip("/")
            feedback[package] = {str(value) for value in status.get("retired_feedback_ids") or []}
            learning[package] = {str(value) for value in status.get("retired_learning_event_ids") or []}
    return feedback, learning

def _json_record(*, relative: str, pointer: str, source_hash: str, title: str, kind: str,
                 text: str, authority: str, lifecycle: str, confidence: float = 0.5,
                 scope: str = "", package: str = "", feedback_ids: Iterable[str] = (),
                 supersedes: Iterable[str] = (), captured_at: str = "",
                 legacy_fragment: str = "", roles: tuple[str, ...] = ("*",)) -> ManifestRecord:
    return ManifestRecord(_record_id(relative, pointer, source_hash), relative, pointer, title, kind,
                          text, source_hash, authority, lifecycle, confidence=confidence,
                          scope=scope, package=package,
                          feedback_ids=tuple(x for x in feedback_ids if x),
                          supersedes_feedback_ids=tuple(x for x in supersedes if x),
                          captured_at=captured_at, eligible_roles=roles,
                          legacy_fragment=legacy_fragment)

def _records_for_json(root: Path, path: Path, kind: str, authority: str, lifecycle: str,
                      retired_feedback: dict[str, set[str]],
                      retired_learning: dict[str, set[str]]) -> list[ManifestRecord]:
    raw = path.read_bytes()
    source_hash = sha256_bytes(raw)
    relative = path.relative_to(root).as_posix()
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError:
        return []
    if not isinstance(payload, dict):
        return []
    if kind == "creator_correction":
        package = str(payload.get("package_id") or relative.removesuffix("/creator-correction.json")).strip("/")
        events = payload.get("events")
        if not isinstance(events, list):
            return [_json_record(relative=relative, pointer="$", source_hash=source_hash,
                                 title="Creator correction", kind=kind,
                                 text=json.dumps(payload, ensure_ascii=False, sort_keys=True),
                                 authority=authority, lifecycle=lifecycle, package=package, confidence=1.0)]
        records = []
        for index, item in enumerate(events):
            if not isinstance(item, dict) or item.get("status") == "rejected":
                continue
            feedback_id = str(item.get("feedback_id") or "")
            if feedback_id in retired_feedback.get(package, set()):
                continue
            text = _creator_text(item)
            if text:
                records.append(_json_record(
                    relative=relative, pointer=f"/events/{index}", source_hash=source_hash,
                    title=f"Creator correction {feedback_id or index}", kind=kind, text=text,
                    authority=authority, lifecycle=lifecycle, confidence=1.0,
                    scope=str(item.get("scope") or ""), package=package,
                    feedback_ids=(feedback_id,), supersedes=(str(item.get("supersedes_feedback_id") or ""),),
                    captured_at=str(item.get("captured_at") or "")))
        return records
    if kind == "learning_event":
        if (payload.get("source") == "langfuse_annotation_candidate"
                or payload.get("eval_disposition") == "candidate_only"
                or payload.get("feedback_status") == "rejected"):
            return []
        metadata = payload.get("feedback_metadata") if isinstance(payload.get("feedback_metadata"), dict) else {}
        package = str(payload.get("package_path") or "").strip("/")
        event_id = str(payload.get("event_id") or "")
        feedback_id = str(metadata.get("feedback_id") or "")
        if event_id in retired_learning.get(package, set()) or feedback_id in retired_feedback.get(package, set()):
            return []
        supersedes = str(payload.get("supersedes_feedback_id") or metadata.get("supersedes_feedback_id") or "")
        supersedes_event = str(payload.get("supersedes_event_id") or "")
        if not supersedes and supersedes_event.startswith("event-feedback-"):
            supersedes = supersedes_event.removeprefix("event-feedback-")
        return [_json_record(relative=relative, pointer="$", source_hash=source_hash,
                             title=str(payload.get("summary") or event_id or path.stem), kind=kind,
                             text=json.dumps(payload, ensure_ascii=False, sort_keys=True),
                             authority=authority, lifecycle=lifecycle, scope=str(payload.get("scope") or ""),
                             package=package, feedback_ids=(feedback_id,), supersedes=(supersedes,),
                             captured_at=str(payload.get("created_at") or ""),
                             roles=("evidence_reviewer", "contradiction_reviewer", "wiki_compiler_verifier"))]
    if kind == "carousel_result":
        review = payload.get("review") if isinstance(payload.get("review"), dict) else {}
        assessment = payload.get("mechanism_assessment") or review.get("mechanism_assessment") or "unavailable"
        limits = payload.get("limits") or review.get("limits") or ["Result limitations unavailable."]
        text = "Research observation; not production policy.\n" + json.dumps(
            {"assessment": assessment, "limits": limits, "record": payload}, ensure_ascii=False, sort_keys=True)
        latest = payload.get("latest_observation") if isinstance(payload.get("latest_observation"), dict) else {}
        return [_json_record(relative=relative, pointer="$", source_hash=source_hash,
                             title=f"Carousel result {payload.get('shortcode') or payload.get('result_id') or path.stem}",
                             kind=kind, text=text, authority=authority, lifecycle=lifecycle,
                             scope="research", package=str(payload.get("package_id") or ""),
                             captured_at=str(latest.get("observed_at") or payload.get("reviewed_at") or ""))]
    return [_json_record(relative=relative, pointer="$", source_hash=source_hash, title=path.stem,
                         kind=kind, text=json.dumps(payload, ensure_ascii=False, sort_keys=True),
                         authority=authority, lifecycle=lifecycle)]

def _pattern_records(root: Path) -> list[ManifestRecord]:
    from pipeline.stages.carousel_patterns import load_patterns, pattern_recall_text
    registry = load_patterns(root)
    if registry.get("status") == "unavailable":
        return []
    path = root / "config/references/carousel-patterns.json"
    if not path.is_file():
        return []
    source_hash = sha256_bytes(path.read_bytes())
    relative = path.relative_to(root).as_posix()
    return [_json_record(relative=relative, pointer=f"/patterns/{index}", source_hash=source_hash,
                         title=str(pattern.get("title") or pattern.get("id")), kind="carousel_pattern",
                         text=pattern_recall_text(pattern), authority="reviewed_observation",
                         lifecycle="active", scope="research",
                         legacy_fragment=str(pattern.get("id") or index))
            for index, pattern in enumerate(registry.get("patterns") or []) if isinstance(pattern, dict)]

def build_manifest(root: Path, *, include_history: bool = False) -> list[ManifestRecord]:
    root = root.resolve()
    retired_feedback, retired_learning = _retirement_sets(root)
    records: list[ManifestRecord] = []
    for path, kind, authority, lifecycle in collect_source_files(root, include_history=include_history):
        if path.suffix.lower() == ".json":
            records.extend(_records_for_json(root, path, kind, authority, lifecycle,
                                             retired_feedback, retired_learning))
            continue
        raw = path.read_bytes()
        text = raw.decode("utf-8", errors="ignore")
        relative = path.relative_to(root).as_posix()
        source_hash = sha256_bytes(raw)
        for first, last, body in _chunks(text):
            pointer = f"lines:{first}-{last}"
            records.append(ManifestRecord(_record_id(relative, pointer, source_hash), relative, pointer,
                                          _title(text, path.stem), kind, body, source_hash,
                                          authority, lifecycle, first, last, _confidence(text)))
    records.extend(_pattern_records(root))
    superseded = {value for record in records for value in record.supersedes_feedback_ids}
    active = [record for record in records if not superseded.intersection(record.feedback_ids)]
    return sorted(active, key=lambda record: (record.source_path, record.source_pointer, record.record_id))

def write_manifest(root: Path, *, include_history: bool = False,
                   path: Path | None = None) -> tuple[Path, list[ManifestRecord]]:
    root = root.resolve()
    records = build_manifest(root, include_history=include_history)
    destination = root / (path or MANIFEST_PATH)
    destination.parent.mkdir(parents=True, exist_ok=True)
    payload = {"schema_version": MANIFEST_VERSION,
               "manifest_sha256": canonical_manifest_digest(records),
               "record_count": len(records), "records": [asdict(record) for record in records]}
    encoded = (json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode()
    if destination.is_file() and destination.read_bytes() == encoded:
        return destination, records
    descriptor, temporary_name = tempfile.mkstemp(prefix=f".{destination.name}.", suffix=".tmp", dir=destination.parent)
    try:
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(encoded)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary_name, destination)
    finally:
        Path(temporary_name).unlink(missing_ok=True)
    return destination, records

def load_manifest(root: Path) -> tuple[Path, list[ManifestRecord], str]:
    path, records = write_manifest(root)
    payload = json.loads(path.read_text(encoding="utf-8"))
    digest = canonical_manifest_digest(records)
    if payload.get("schema_version") != MANIFEST_VERSION or payload.get("manifest_sha256") != digest:
        raise ValueError("retrieval manifest is stale or corrupt")
    return path, records, digest
