"""SQLite FTS memory index for meaning-oriented repo recall."""

from __future__ import annotations

import hashlib
import json
import os
import re
import sqlite3
import tempfile
from datetime import datetime, timezone
from pathlib import Path

from pipeline.agentic.contracts import RecallHit


DEFAULT_INDEX_PATH = Path("memory/agentic/index/memory.sqlite3")
SCOPE_FILTER_RE = re.compile(r"\bscope:(workflow|package|slide|asset|copy|global)\b")
PACKAGE_FILTER_RE = re.compile(
    r"(?<![A-Za-z0-9_])package:(?:\"([^\"]+)\"|'([^']+)'|([A-Za-z0-9_./-]+))"
)
INDEXED_GLOBS = (
    ("memory/working.md", "working"),
    ("memory/semantic/*.md", "semantic"),
    ("wiki/**/*.md", "wiki"),
    ("config/rules/*.md", "rule"),
    ("config/skills/*.md", "skill"),
    (".agents/skills/**/SKILL.md", "repo_skill"),
    (".codex/agents/*.toml", "agent"),
    ("agents/*.md", "agent"),
    ("docs/**/*.md", "doc"),
    ("output/reports/*.md", "report"),
    ("output/reports/carousel-results/*.json", "carousel_result"),
    ("memory/agentic/learning-events/*.json", "learning_event"),
    ("output/carousels/**/creator-correction.json", "creator_correction"),
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


def _index_fingerprint(root: Path) -> str:
    """Hash the eligible source set so unchanged builds keep the last index."""
    digest = hashlib.sha256()
    for path, kind in collect_indexable_files(root):
        relative = path.relative_to(root).as_posix()
        digest.update(kind.encode("utf-8"))
        digest.update(b"\0")
        digest.update(relative.encode("utf-8"))
        digest.update(b"\0")
        digest.update(path.read_bytes())
        digest.update(b"\0")
    return digest.hexdigest()


def _index_state_path(index: Path) -> Path:
    return index.with_suffix(index.suffix + ".state.json")


def _string_list(value: object) -> str:
    if isinstance(value, list):
        return " ".join(str(item) for item in value if item)
    return str(value or "")


def _package_path_from_correction(relative: str, payload: dict[str, object]) -> str:
    package_id = payload.get("package_id")
    if isinstance(package_id, str) and package_id.strip():
        return package_id.strip().strip("/")
    suffix = "/creator-correction.json"
    return relative[: -len(suffix)] if relative.endswith(suffix) else ""


def _feedback_id_from_event_id(value: object) -> str:
    event_id = str(value or "")
    prefix = "event-feedback-"
    return event_id[len(prefix) :] if event_id.startswith(prefix) else ""


def build_memory_index(root: Path, index_path: Path | None = None) -> Path:
    root = root.resolve()
    index = root / (index_path or DEFAULT_INDEX_PATH)
    index.parent.mkdir(parents=True, exist_ok=True)
    fingerprint = _index_fingerprint(root)
    state_path = _index_state_path(index)
    if index.is_file() and state_path.is_file():
        try:
            state = json.loads(state_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            state = {}
        if state.get("fingerprint") == fingerprint:
            return index

    from pipeline.stages.carousel_visual_storytelling import (
        successor_feedback_retirement_status,
    )

    from pipeline.stages.carousel_patterns import load_patterns, pattern_recall_text

    # Validate before replacing the previous good index. Invalid evidence is an
    # explicit rebuild error, not verified recall or an empty successful import.
    pattern_registry = load_patterns(root)
    retired_feedback_by_package: dict[str, set[str]] = {}
    retired_learning_by_package: dict[str, set[str]] = {}
    for correction in root.glob("output/carousels/**/creator-correction.json"):
        try:
            payload = json.loads(correction.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        if not isinstance(payload, dict) or "successor_retirement" not in payload:
            continue
        retirement = successor_feedback_retirement_status(
            correction.parent, workspace_root=root
        )
        if retirement.get("retired"):
            package_path = str(retirement["package_path"]).strip().strip("/")
            retired_feedback_by_package[package_path] = {
                str(value)
                for value in retirement.get("retired_feedback_ids") or []
                if str(value)
            }
            retired_learning_by_package[package_path] = {
                str(value)
                for value in retirement.get("retired_learning_event_ids") or []
                if str(value)
            }
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{index.name}.",
        suffix=".tmp",
        dir=index.parent,
    )
    os.close(descriptor)
    temporary_index = Path(temporary_name)
    conn: sqlite3.Connection | None = None
    try:
        conn = sqlite3.connect(temporary_index)
        conn.execute(
            "CREATE VIRTUAL TABLE memory USING fts5("
            "path, title, kind, text, tags, confidence UNINDEXED, scope UNINDEXED, "
            "captured_at UNINDEXED, feedback_id UNINDEXED, supersedes_feedback_id UNINDEXED, "
            "package_path UNINDEXED)"
        )
        for path, kind in collect_indexable_files(root):
            text = path.read_text(encoding="utf-8", errors="ignore")
            relative = path.relative_to(root).as_posix()
            if kind == "carousel_result":
                try:
                    result = json.loads(text)
                except json.JSONDecodeError as exc:
                    raise ValueError(f"Invalid carousel result research: {relative}") from exc
                if not isinstance(result, dict):
                    raise ValueError(f"Invalid carousel result research: {relative}")
                text = "Research observation; not production policy.\n" + json.dumps(result, ensure_ascii=False)
                conn.execute(
                    "INSERT INTO memory(path,title,kind,text,tags,confidence,scope,captured_at,feedback_id,supersedes_feedback_id,package_path) VALUES (?,?,?,?,?,?,?,?,?,?,?)",
                    (relative, f"Carousel result {result.get('shortcode') or result.get('result_id') or path.stem}", kind,
                     text, "carousel_result research observation uncertainty", 0.5, "research",
                     str((result.get('latest_observation') or {}).get('observed_at') or result.get('reviewed_at') or ""),
                     "", "", str(result.get('package_id') or "")),
                )
                continue
            if kind == "creator_correction":
                try:
                    payload = json.loads(text)
                except json.JSONDecodeError:
                    payload = {}
                events = payload.get("events") if isinstance(payload, dict) else None
                if isinstance(events, list):
                    package_path = _package_path_from_correction(relative, payload).strip("/")
                    retired_feedback_ids = retired_feedback_by_package.get(
                        package_path, set()
                    )
                    for event in events:
                        if not isinstance(event, dict) or event.get("status") == "rejected":
                            continue
                        feedback_id = str(event.get("feedback_id") or "")
                        if feedback_id in retired_feedback_ids:
                            continue
                        searchable = "\n".join(
                            str(value)
                            for value in (
                                event.get("user_instruction_exact"),
                                event.get("primary_diagnosis"),
                                event.get("root_cause"),
                                event.get("desired_behavior"),
                                _string_list(event.get("must_change")),
                                _string_list(event.get("must_preserve")),
                            )
                            if value
                        )
                        conn.execute(
                            "INSERT INTO memory(path,title,kind,text,tags,confidence,scope,captured_at,feedback_id,supersedes_feedback_id,package_path) "
                            "VALUES (?,?,?,?,?,?,?,?,?,?,?)",
                            (
                                f"{relative}#{feedback_id}",
                                f"Creator correction {feedback_id}",
                                kind,
                                searchable,
                                " ".join(
                                    [kind, str(event.get("scope") or ""), str(event.get("primary_diagnosis") or "")]
                                ),
                                1.0,
                                str(event.get("scope") or ""),
                                str(event.get("captured_at") or ""),
                                feedback_id,
                                str(event.get("supersedes_feedback_id") or ""),
                                package_path,
                            ),
                        )
                    continue
            event_payload = {}
            if kind == "learning_event":
                try:
                    event_payload = json.loads(text)
                except json.JSONDecodeError:
                    pass
                if not isinstance(event_payload, dict):
                    event_payload = {}
                if (
                    event_payload.get("feedback_status") == "rejected"
                    or event_payload.get("source") == "langfuse_annotation_candidate"
                    or event_payload.get("eval_disposition") == "candidate_only"
                ):
                    continue
            metadata = event_payload.get("feedback_metadata") or {}
            if not isinstance(metadata, dict):
                metadata = {}
            package_path = str(event_payload.get("package_path") or "").strip().strip("/")
            if kind == "learning_event":
                event_id = str(event_payload.get("event_id") or "")
                feedback_id = str(metadata.get("feedback_id") or "")
                if (
                    event_id in retired_learning_by_package.get(package_path, set())
                    or feedback_id
                    in retired_feedback_by_package.get(package_path, set())
                ):
                    continue
            if kind == "creator_correction":
                package_path = _package_path_from_correction(relative, event_payload)
            supersedes_feedback_id = str(
                event_payload.get("supersedes_feedback_id")
                or metadata.get("supersedes_feedback_id")
                or _feedback_id_from_event_id(event_payload.get("supersedes_event_id"))
                or ""
            )
            conn.execute(
                "INSERT INTO memory(path,title,kind,text,tags,confidence,scope,captured_at,feedback_id,supersedes_feedback_id,package_path) "
                "VALUES (?,?,?,?,?,?,?,?,?,?,?)",
                (
                    relative,
                    title_for(text, path.stem),
                    kind,
                    text,
                    " ".join([kind, path.stem]),
                    confidence_for(text),
                    str(event_payload.get("scope") or ""),
                    str(event_payload.get("created_at") or ""),
                    str(metadata.get("feedback_id") or ""),
                    supersedes_feedback_id,
                    package_path,
                ),
            )
        for pattern in pattern_registry["patterns"]:
            conn.execute(
                "INSERT INTO memory(path,title,kind,text,tags,confidence,scope,captured_at,feedback_id,supersedes_feedback_id,package_path) VALUES (?,?,?,?,?,?,?,?,?,?,?)",
                (f"config/references/carousel-patterns.json#{pattern['id']}", pattern["title"],
                 "carousel_pattern", pattern_recall_text(pattern),
                 "carousel_pattern research " + " ".join(pattern.get("tags", [])),
                 0.5, "research", str(pattern_registry.get("saved_on") or ""), "", "", ""),
            )
        conn.commit()
        conn.close()
        conn = None
        os.replace(temporary_index, index)
        temporary_state = state_path.with_suffix(state_path.suffix + ".tmp")
        temporary_state.write_text(
            json.dumps({"schema_version": "fts5-index-state/v1", "fingerprint": fingerprint}) + "\n",
            encoding="utf-8",
        )
        os.replace(temporary_state, state_path)
        from pipeline.agentic.retrieval_manifest import write_manifest

        write_manifest(root)
    finally:
        if conn is not None:
            conn.close()
        temporary_index.unlink(missing_ok=True)
    return index


def snippet(text: str, query: str) -> str:
    lowered = text.lower()
    terms = [term.lower() for term in re.findall(r"[A-Za-z0-9]+", query)]
    positions = [lowered.find(term) for term in terms if lowered.find(term) >= 0]
    start = max(0, min(positions) - 80) if positions else 0
    return text[start : start + 220].replace("\n", " ").strip()


def _research_snippet(text: str, kind: str, query: str) -> str:
    if kind == "carousel_pattern":
        from pipeline.stages.carousel_patterns import pattern_recall_snippet
        return pattern_recall_snippet(text)
    if kind == "carousel_result":
        payload = json.loads(text.split("\n", 1)[1])
        review = payload.get("review") or {}
        assessment = payload.get("mechanism_assessment") or review.get("mechanism_assessment") or "unavailable"
        if isinstance(assessment, dict):
            assessment = f"{assessment.get('status', 'unavailable')}: {assessment.get('reason', '')}"
        limits = payload.get("limits") or review.get("limits") or ["Result limitations unavailable."]
        observed_at = (payload.get("latest_observation") or {}).get("observed_at") or payload.get("reviewed_at") or "unavailable"
        return f"Research observation ({observed_at}); not production policy. {assessment} Limit: {_string_list(limits)}"
    return snippet(text, query)


def _query_filters(query: str) -> tuple[str, str, str]:
    scope_match = SCOPE_FILTER_RE.search(query)
    package_match = PACKAGE_FILTER_RE.search(query)
    requested_scope = scope_match.group(1) if scope_match else ""
    requested_package = ""
    if package_match:
        requested_package = next(
            (group for group in package_match.groups() if group is not None),
            "",
        ).strip().strip("/")
        carousel_marker = "output/carousels/"
        if carousel_marker in requested_package:
            requested_package = carousel_marker + requested_package.split(carousel_marker, 1)[1]
    lexical_query = SCOPE_FILTER_RE.sub(" ", query)
    lexical_query = PACKAGE_FILTER_RE.sub(" ", lexical_query).strip()
    return lexical_query, requested_scope, requested_package


def _escape_like(value: str) -> str:
    return value.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")


def _package_matches(candidate: object, requested: str) -> bool:
    package_path = str(candidate or "").strip().strip("/")
    if not requested:
        return True
    return package_path == requested or package_path.endswith(f"/{requested}")


def search_memory(index_path: Path, query: str, limit: int = 8) -> list[RecallHit]:
    if limit <= 0:
        return []
    lexical_query, requested_scope, requested_package = _query_filters(query)
    conn = sqlite3.connect(index_path)
    terms = [term for term in re.findall(r"\w+", lexical_query, flags=re.UNICODE) if len(term) > 1]
    match_query = " OR ".join(f"{term}*" for term in terms)
    columns = (
        "path, title, kind, text, confidence, bm25(memory) AS score, "
        "scope, captured_at, feedback_id, supersedes_feedback_id, package_path"
    )
    conditions = [
        "(feedback_id = '' OR feedback_id NOT IN ("
        "SELECT supersedes_feedback_id FROM memory WHERE supersedes_feedback_id != ''))"
    ]
    params: list[object] = []
    if requested_package:
        escaped_package = _escape_like(requested_package)
        package_condition = "(package_path = ? OR package_path LIKE ? ESCAPE '\\'"
        params.extend((requested_package, f"%/{escaped_package}"))
        conditions.append(package_condition + ")")
    fetch_limit = max(limit * 12, 64)
    try:
        if terms:
            rows = conn.execute(
                f"SELECT {columns} FROM memory WHERE memory MATCH ? AND "
                + " AND ".join(conditions)
                + " ORDER BY score LIMIT ?",
                (match_query, *params, fetch_limit),
            ).fetchall()
        elif requested_package:
            rows = conn.execute(
                "SELECT path, title, kind, text, confidence, 0.0 AS score, "
                "scope, captured_at, feedback_id, supersedes_feedback_id, package_path "
                "FROM memory WHERE "
                + " AND ".join(conditions)
                + " LIMIT ?",
                (*params, fetch_limit),
            ).fetchall()
        else:
            return []
    except sqlite3.OperationalError:
        if not terms:
            return []
        rows = conn.execute(
            f"""
            SELECT path, title, kind, text, confidence, 0.0 AS score,
                   scope, captured_at, feedback_id, supersedes_feedback_id, package_path
            FROM memory
            WHERE ({' OR '.join('text LIKE ?' for _ in terms)})
              AND {' AND '.join(conditions)}
            LIMIT ?
            """,
            (*[f"%{term}%" for term in terms], *params, fetch_limit),
        ).fetchall()
    finally:
        conn.close()

    def rank(row: tuple[object, ...]) -> tuple[float, str]:
        score = float(row[5] or 0.0)
        if requested_package and _package_matches(row[10], requested_package):
            score -= 3.0
        if requested_scope and row[6] == requested_scope:
            score -= 2.0
        if row[2] in {"creator_correction", "learning_event"} and row[7]:
            try:
                captured = datetime.fromisoformat(str(row[7]).replace("Z", "+00:00"))
                if captured.tzinfo is None:
                    captured = captured.replace(tzinfo=timezone.utc)
                age_days = max(0.0, (datetime.now(timezone.utc) - captured).total_seconds() / 86400)
                score -= max(0.0, 1.0 - min(age_days, 365.0) / 365.0)
            except ValueError:
                pass
        return score, str(row[0])

    ranked_rows = sorted(rows, key=rank)
    # A linked learning event and its canonical package correction describe one
    # feedback memory. Prefer the package correction without consuming two slots.
    canonical_by_feedback: dict[str, tuple[object, ...]] = {}
    unlinked_rows: list[tuple[object, ...]] = []
    for row in ranked_rows:
        feedback_id = str(row[8] or "")
        if not feedback_id:
            unlinked_rows.append(row)
            continue
        current = canonical_by_feedback.get(feedback_id)
        if current is None or (row[2] == "creator_correction" and current[2] != "creator_correction"):
            canonical_by_feedback[feedback_id] = row
    active_rows = sorted([*unlinked_rows, *canonical_by_feedback.values()], key=rank)[:limit]
    root = index_path.resolve().parents[3]

    def cited_hit(row: tuple[object, ...]) -> RecallHit:
        stored_path = str(row[0])
        source_path, _, fragment = stored_path.partition("#")
        source = root / source_path
        try:
            source_hash = hashlib.sha256(source.read_bytes()).hexdigest()
            line_count = len(source.read_text(encoding="utf-8", errors="ignore").splitlines())
        except OSError:
            source_hash, line_count = "", 0
        pointer = f"record:{fragment}" if fragment else f"lines:1-{max(1, line_count)}"
        authority = {
            "semantic": "approved_preference",
            "creator_correction": "approved_preference",
            "rule": "canonical",
            "skill": "workflow",
            "agent": "workflow",
        }.get(str(row[2]), "reviewed_observation")
        record_id = hashlib.sha256(
            f"{source_path}:{pointer}:{source_hash}".encode("utf-8")
        ).hexdigest()[:24]
        return RecallHit(
            path=stored_path,
            title=row[1],
            kind=row[2],
            snippet=_research_snippet(row[3], row[2], query),
            confidence=float(row[4] or 0.5),
            score=rank(row)[0],
            backend="fts5",
            record_id=record_id,
            source_path=source_path,
            source_pointer=pointer,
            content_sha256=source_hash,
            authority=authority,
            lifecycle="active",
        )

    return [cited_hit(row) for row in active_rows]
