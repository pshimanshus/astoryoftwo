"""Opt-in QMD collection built only from the shared retrieval manifest."""
from __future__ import annotations

import json
import os
import shutil
import subprocess
from pathlib import Path
from typing import Callable

from pipeline.agentic.contracts import RecallHit
from pipeline.agentic.retrieval_errors import BackendStale, BackendUnavailable
from pipeline.agentic.retrieval_manifest import ManifestRecord, load_manifest
from pipeline.agentic.retrieval_filters import (
    parse_retrieval_filters,
    record_is_eligible,
    scope_priority,
)

QMD_DIR = Path("memory/agentic/index/qmd")
COLLECTION = "asot-derived"
MAX_OUTPUT_BYTES = 1_000_000
Runner = Callable[[list[str], Path, dict[str, str]], str]

def _environment(directory: Path) -> dict[str, str]:
    env = dict(os.environ)
    env.update({
        "XDG_CONFIG_HOME": str(directory / "config"),
        "XDG_CACHE_HOME": str(directory / "cache"),
        "QMD_NO_UPDATE": "1",
        "NO_UPDATE_NOTIFIER": "1",
        "CI": "1",
    })
    return env

def _run_bounded(command: list[str], cwd: Path, env: dict[str, str]) -> str:
    process = subprocess.Popen(command, cwd=cwd, env=env, stdout=subprocess.PIPE,
                               stderr=subprocess.PIPE, text=False)
    try:
        stdout, stderr = process.communicate(timeout=20)
    except subprocess.TimeoutExpired as exc:
        process.kill()
        process.communicate()
        raise BackendUnavailable("qmd subprocess timed out") from exc
    if len(stdout) > MAX_OUTPUT_BYTES or len(stderr) > MAX_OUTPUT_BYTES:
        raise BackendUnavailable("qmd subprocess exceeded output bound")
    if process.returncode:
        detail = stderr.decode("utf-8", errors="replace")[:300]
        raise BackendUnavailable(f"qmd command failed: {detail}")
    return stdout.decode("utf-8", errors="strict")

def _record_document(record: ManifestRecord) -> str:
    return "\n".join((
        "---", f"record_id: {record.record_id}", f"source_path: {record.source_path}",
        f"source_pointer: {record.source_pointer}", f"content_sha256: {record.content_sha256}",
        "---", "", f"# {record.title}", "", record.text, "",
    ))

class QmdHybridBackend:
    name = "qmd_hybrid"

    def __init__(self, *, runner: Runner | None = None, executable: str | None = None) -> None:
        self.runner = runner or _run_bounded
        self.executable = executable or shutil.which("qmd") or ""

    def availability(self) -> tuple[bool, str]:
        if os.getenv("ASOT_RETRIEVAL_QMD_ENABLED") != "1":
            return False, "ASOT_RETRIEVAL_QMD_ENABLED is not 1"
        if not self.executable:
            return False, "qmd executable is unavailable"
        return True, ""

    def build(self, root: Path) -> Path:
        available, reason = self.availability()
        if not available:
            raise BackendUnavailable(reason)
        root = root.resolve()
        _manifest, records, digest = load_manifest(root)
        directory = root / QMD_DIR
        documents = directory / "documents"
        documents.mkdir(parents=True, exist_ok=True)
        desired = {record.record_id for record in records}
        state_path = directory / "state.json"
        if state_path.is_file():
            try:
                current = json.loads(state_path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                current = {}
            if (current.get("manifest_sha256") == digest
                    and current.get("record_ids") == sorted(desired)
                    and all((documents / f"{record_id}.md").is_file() for record_id in desired)):
                return directory
        for stale in documents.glob("*.md"):
            if stale.stem not in desired:
                stale.unlink()
        for record in records:
            target = documents / f"{record.record_id}.md"
            content = _record_document(record)
            if not target.is_file() or target.read_text(encoding="utf-8") != content:
                target.write_text(content, encoding="utf-8")
        env = _environment(directory)
        # QMD owns only this generated collection; update hooks are disabled in env.
        try:
            self.runner([self.executable, "collection", "remove", COLLECTION], root, env)
        except BackendUnavailable:
            pass
        self.runner([self.executable, "collection", "add", str(documents), "--name", COLLECTION,
                     "--mask", "*.md"], root, env)
        self.runner([self.executable, "embed", "--collection", COLLECTION], root, env)
        state = {"schema_version": "qmd-derived-collection/v1", "manifest_sha256": digest,
                 "record_count": len(records), "record_ids": sorted(desired)}
        state_path.write_text(json.dumps(state, sort_keys=True) + "\n", encoding="utf-8")
        return directory

    def _current_records(self, root: Path) -> tuple[dict[str, ManifestRecord], Path]:
        _manifest, records, digest = load_manifest(root)
        directory = root / QMD_DIR
        state_path = directory / "state.json"
        if not state_path.is_file():
            raise BackendStale("qmd collection has not been built")
        try:
            state = json.loads(state_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise BackendStale("qmd state is unreadable") from exc
        if state.get("manifest_sha256") != digest:
            raise BackendStale("qmd collection is stale for the current manifest")
        return {record.record_id: record for record in records}, directory

    def search(self, root: Path, query: str, limit: int) -> list[RecallHit]:
        available, reason = self.availability()
        if not available:
            raise BackendUnavailable(reason)
        by_id, directory = self._current_records(root.resolve())
        filters = parse_retrieval_filters(query)
        if not filters.lexical_query and not filters.package:
            return []
        fetch_limit = max(64, limit * 12)
        output = self.runner([self.executable, "query", filters.lexical_query, "--collection", COLLECTION,
                              "--json", "-n", str(fetch_limit)], root.resolve(), _environment(directory))
        try:
            payload = json.loads(output)
        except json.JSONDecodeError as exc:
            raise BackendUnavailable("qmd returned invalid JSON") from exc
        entries = payload if isinstance(payload, list) else payload.get("results", [])
        if not isinstance(entries, list):
            raise BackendUnavailable("qmd result shape is invalid")
        eligible: list[tuple[int, int, ManifestRecord, dict[str, object]]] = []
        for rank, item in enumerate(entries):
            if not isinstance(item, dict):
                continue
            raw_id = str(item.get("record_id") or item.get("id") or "")
            if not raw_id:
                raw_path = str(item.get("path") or item.get("file") or "")
                raw_id = Path(raw_path).stem
            record = by_id.get(raw_id)
            if record is None:  # Reject foreign/stale QMD documents.
                continue
            if not record_is_eligible(
                package=record.package,
                eligible_roles=record.eligible_roles,
                filters=filters,
            ):
                continue
            eligible.append((-scope_priority(record.scope, filters.scope), rank, record, item))
        hits: list[RecallHit] = []
        for _scope_rank, _original_rank, record, item in sorted(eligible):
            hits.append(RecallHit(
                path=record.legacy_path, title=record.title, kind=record.kind,
                snippet=record.text[:300].replace("\n", " "), score=float(item.get("score") or 0.0),
                confidence=record.confidence, backend=self.name, requested_backend="qmd",
                record_id=record.record_id, source_path=record.source_path,
                source_pointer=record.source_pointer, content_sha256=record.content_sha256,
                authority=record.authority, lifecycle=record.lifecycle, scope=record.scope,
                package=record.package, feedback_ids=list(record.feedback_ids)))
        return hits[:limit]

def build_qmd_collection(root: Path, *, runner: Runner | None = None,
                         executable: str | None = None) -> Path:
    return QmdHybridBackend(runner=runner, executable=executable).build(root)

def search_qmd(root: Path, query: str, *, limit: int) -> list[RecallHit]:
    return QmdHybridBackend().search(root, query, limit)
