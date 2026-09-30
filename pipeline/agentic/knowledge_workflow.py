"""Dynamic, receipt-backed evidence-to-wiki workflow.

The controller chooses only the stages an event needs. Reviewer functions are
pure: they return findings and never receive a write capability. The A4
compiler is the single wiki writer. The controller persists the resulting
route, reviews, delta, and workflow receipt, then emits a retrieval
invalidation only after it verifies a successful compiler receipt.
"""

from __future__ import annotations

import fcntl
import hashlib
import json
import os
import re
import tempfile
import tomllib
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Iterator, Mapping

from pipeline.agentic.contracts import utc_now_iso


RUNS_DIR = Path("memory/agentic/knowledge-workflows")
INVALIDATIONS_DIR = Path("memory/agentic/retrieval-invalidations")
SAFE_ID = re.compile(r"[^A-Za-z0-9._-]+")
ROLE_RECORDS = {
    "evidence_reviewer": Path(".codex/agents/asot_evidence_reviewer.toml"),
    "contradiction_reviewer": Path(".codex/agents/asot_contradiction_reviewer.toml"),
    "wiki_compiler_verifier": Path(".codex/agents/asot_wiki_compiler_verifier.toml"),
}


def _sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _canonical_hash(value: object) -> str:
    return _sha256_bytes(
        json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode(
            "utf-8"
        )
    )


def _read_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"invalid workflow JSON at {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise ValueError(f"workflow JSON must be an object: {path}")
    return value


def _safe_path(root: Path, supplied: str, *, must_exist: bool = True) -> Path:
    raw = Path(supplied)
    if not supplied.strip() or raw.is_absolute() or ".." in raw.parts:
        raise ValueError(f"workflow path must be workspace relative: {supplied!r}")
    candidate = (root / raw).resolve()
    try:
        candidate.relative_to(root)
    except ValueError as exc:
        raise ValueError(f"workflow path escapes workspace: {supplied}") from exc
    if must_exist and not candidate.is_file():
        raise ValueError(f"workflow artifact is missing: {supplied}")
    return candidate


def _atomic_json(path: Path, payload: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            json.dump(payload, handle, indent=2, sort_keys=True, ensure_ascii=False)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


@contextmanager
def _workflow_lock(root: Path) -> Iterator[None]:
    lock_path = root / "memory" / "agentic" / "locks" / "knowledge-workflow.lock"
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    with lock_path.open("a+", encoding="utf-8") as handle:
        fcntl.flock(handle.fileno(), fcntl.LOCK_EX)
        try:
            yield
        finally:
            fcntl.flock(handle.fileno(), fcntl.LOCK_UN)


def select_roles(event: Mapping[str, Any]) -> list[str]:
    """Choose the minimum bounded role set required by an event."""

    roles = ["evidence_reviewer"]
    claims = event.get("claims")
    conflicts = event.get("conflicts", event.get("contradictions"))
    if event.get("check_contradictions") is True or (
        isinstance(claims, list) and len(claims) > 1
    ) or (isinstance(conflicts, list) and bool(conflicts)):
        roles.append("contradiction_reviewer")
    if event.get("compile") is not False:
        roles.extend(["wiki_compiler", "wiki_compiler_verifier"])
    return roles


def validate_role_records(root: Path, roles: list[str]) -> dict[str, str]:
    """Resolve selected reviewer roles to executable, read-only records."""

    resolved: dict[str, str] = {}
    for role in roles:
        record_relative = ROLE_RECORDS.get(role)
        if record_relative is None:
            continue
        record_path = root / record_relative
        try:
            record = tomllib.loads(record_path.read_text(encoding="utf-8"))
        except (OSError, tomllib.TOMLDecodeError) as exc:
            raise ValueError(f"invalid agent role record {record_relative}: {exc}") from exc
        if record.get("runtime_role") != role:
            raise ValueError(f"agent record does not bind runtime role {role}")
        if record.get("sandbox_mode") != "read-only":
            raise ValueError(f"reviewer role must be read-only: {role}")
        resolved[role] = record_relative.as_posix()
    return resolved


def review_evidence(root: Path, event: Mapping[str, Any]) -> dict[str, Any]:
    """Pure evidence review. The controller persists its returned value."""

    evidence = event.get("evidence")
    if not isinstance(evidence, list) or not evidence:
        return {
            "role": "evidence_reviewer",
            "status": "DATA_GAP",
            "issues": ["event has no bounded evidence records"],
            "sources": [],
        }
    sources: list[dict[str, Any]] = []
    issues: list[str] = []
    for index, item in enumerate(evidence):
        if not isinstance(item, dict) or not isinstance(item.get("path"), str):
            issues.append(f"evidence[{index}] must contain a workspace-relative path")
            continue
        try:
            path = _safe_path(root, str(item["path"]))
        except ValueError as exc:
            issues.append(str(exc))
            continue
        actual = _sha256_bytes(path.read_bytes())
        declared = str(item.get("sha256") or "")
        if declared and declared != actual:
            issues.append(f"evidence hash mismatch: {item['path']}")
        sources.append({"path": str(item["path"]), "sha256": actual})
    return {
        "role": "evidence_reviewer",
        "status": "PASS" if sources and not issues else "DATA_GAP",
        "issues": issues,
        "sources": sources,
    }


def review_contradictions(
    event: Mapping[str, Any], *, verified_source_paths: set[str] | None = None
) -> dict[str, Any]:
    """Pure contradiction review that preserves conflicts instead of choosing."""

    verified_source_paths = verified_source_paths or set()
    supplied = event.get("conflicts", event.get("contradictions", []))
    conflicts: list[dict[str, Any]] = []
    issues: list[str] = []
    if not isinstance(supplied, list):
        issues.append("conflicts must be an array")
    else:
        for index, conflict in enumerate(supplied):
            if not isinstance(conflict, dict):
                issues.append(f"conflict[{index}] must be an object")
                continue
            claim = str(conflict.get("claim") or "").strip()
            sources = conflict.get("source_paths")
            if not claim or not isinstance(sources, list) or len(sources) < 2:
                issues.append(
                    f"conflict[{index}] requires a claim and at least two source_paths"
                )
                continue
            unverified = sorted({str(item) for item in sources} - verified_source_paths)
            if unverified:
                issues.append(
                    f"conflict[{index}] cites unverified evidence: {', '.join(unverified)}"
                )
                continue
            conflicts.append(
                {
                    "claim": claim,
                    "source_paths": [str(item) for item in sources],
                    "resolution": str(conflict.get("resolution") or "unresolved"),
                }
            )
    claims = event.get("claims", [])
    if claims is not None and not isinstance(claims, list):
        issues.append("claims must be an array")
    elif isinstance(claims, list):
        grouped: dict[str, list[dict[str, str]]] = {}
        for index, claim_record in enumerate(claims):
            if not isinstance(claim_record, dict):
                issues.append(f"claims[{index}] must be an object")
                continue
            claim = str(claim_record.get("claim") or claim_record.get("statement") or "").strip()
            value = claim_record.get("direction", claim_record.get("value"))
            source = str(claim_record.get("source_path") or "").strip()
            if not claim or value is None or not source:
                issues.append(
                    f"claims[{index}] requires claim/statement, direction/value, and source_path"
                )
                continue
            if source not in verified_source_paths:
                issues.append(f"claims[{index}] cites unverified evidence: {source}")
                continue
            grouped.setdefault(" ".join(claim.casefold().split()), []).append(
                {"claim": claim, "value": str(value), "source_path": source}
            )
        for records in grouped.values():
            values = {record["value"] for record in records}
            sources = sorted({record["source_path"] for record in records})
            if len(values) > 1 and len(sources) > 1:
                conflicts.append(
                    {
                        "claim": records[0]["claim"],
                        "source_paths": sources,
                        "observed_values": sorted(values),
                        "resolution": "unresolved",
                    }
                )
    status = "DATA_GAP" if issues else ("PASS_WITH_CONFLICTS" if conflicts else "PASS")
    return {
        "role": "contradiction_reviewer",
        "status": status,
        "issues": issues,
        "preserved_conflicts": conflicts,
    }


def _execute_a4(root: Path, event: Mapping[str, Any]) -> Path:
    """Call the registered A4 plan/apply API; no other role receives it."""

    analysis_value = event.get("analysis_path")
    if not isinstance(analysis_value, str):
        raise ValueError("compile event requires analysis_path")
    analysis_path = _safe_path(root, analysis_value)
    from pipeline.stages import a4_wiki

    builder = getattr(a4_wiki, "build_compile_plan", None) or getattr(
        a4_wiki, "plan_compile", None
    )
    if builder is None or not hasattr(a4_wiki, "apply_compile_plan"):
        raise ValueError("A4 compiler does not expose build/apply compile plan")
    plan = builder(root, analysis_path=analysis_path)
    a4_wiki.apply_compile_plan(plan)
    receipt_path = getattr(plan, "receipt_path", None)
    if not isinstance(receipt_path, Path) or not receipt_path.is_file():
        raise ValueError("A4 compiler did not persist its commit receipt")
    return receipt_path


def verify_compile_receipt(root: Path, receipt_path: Path) -> dict[str, Any]:
    receipt = _read_json(receipt_path)
    issues: list[str] = []
    if str(receipt.get("status") or "") not in {"applied", "compiled", "success"}:
        issues.append("compiler receipt does not report successful application")
    analysis_path = receipt.get("analysis_path")
    analysis_hash = receipt.get("analysis_sha256")
    if isinstance(analysis_path, str) and isinstance(analysis_hash, str):
        try:
            actual = _sha256_bytes(_safe_path(root, analysis_path).read_bytes())
            if actual != analysis_hash:
                issues.append("compiler receipt analysis hash is stale")
        except ValueError as exc:
            issues.append(str(exc))
    else:
        issues.append("compiler receipt lacks analysis path/hash binding")
    targets = [str(item) for item in receipt.get("targets") or []]
    output_hashes = receipt.get("output_hashes", {})
    if not targets:
        issues.append("compiler receipt has no declared targets")
    if not isinstance(output_hashes, dict) or not output_hashes:
        issues.append("compiler receipt requires output_hashes")
    elif any(target not in output_hashes for target in targets):
        issues.append("compiler receipt does not hash every declared target")
    if isinstance(output_hashes, dict):
        for output, expected in output_hashes.items():
            if not isinstance(output, str) or not isinstance(expected, str):
                issues.append("compiler output hash binding is malformed")
                continue
            try:
                actual = _sha256_bytes(_safe_path(root, output).read_bytes())
                if actual != expected:
                    issues.append(f"compiled output hash mismatch: {output}")
            except ValueError as exc:
                issues.append(str(exc))
    return {
        "role": "wiki_compiler_verifier",
        "status": "PASS" if not issues else "REPAIR",
        "issues": issues,
        "receipt_path": receipt_path.relative_to(root).as_posix(),
        "receipt_sha256": _sha256_bytes(receipt_path.read_bytes()),
        "output_hashes": output_hashes if isinstance(output_hashes, dict) else {},
        "targets": targets,
    }


def run_knowledge_workflow(
    root: Path,
    event_path: Path,
    *,
    execute_compile: bool = False,
) -> dict[str, Any]:
    """Execute one dynamically routed event and persist its complete receipts."""

    root = root.resolve()
    event_path = event_path if event_path.is_absolute() else root / event_path
    event_path = event_path.resolve()
    try:
        event_path.relative_to(root)
    except ValueError as exc:
        raise ValueError("event_path must stay inside workspace") from exc
    event = _read_json(event_path)
    event_hash = _canonical_hash(event)
    raw_id = str(event.get("event_id") or event_path.stem)
    event_id = SAFE_ID.sub("-", raw_id).strip(".-") or "knowledge-event"
    run_id = f"{event_id}-{event_hash[:12]}"
    run_dir = root / RUNS_DIR / run_id
    roles = select_roles(event)
    role_records = validate_role_records(root, roles)
    route = {
        "schema_version": "knowledge-route/v1",
        "run_id": run_id,
        "event_path": event_path.relative_to(root).as_posix(),
        "event_sha256": event_hash,
        "selected_roles": roles,
        "role_records": role_records,
        "reviewer_mode": "read_only",
        "execution_mode": "deterministic_role_contracts",
        "writer_role": "wiki_compiler" if "wiki_compiler" in roles else None,
    }

    with _workflow_lock(root):
        evidence_review = review_evidence(root, event)
        contradiction_review = (
            review_contradictions(
                event,
                verified_source_paths={
                    str(source["path"])
                    for source in evidence_review.get("sources", [])
                    if isinstance(source, dict) and source.get("path")
                },
            )
            if "contradiction_reviewer" in roles
            else None
        )
        reviews: list[dict[str, Any]] = [evidence_review]
        if contradiction_review is not None:
            reviews.append(contradiction_review)
        can_compile = all(review["status"] not in {"DATA_GAP", "REPAIR"} for review in reviews)
        compile_review: dict[str, Any] | None = None
        compiler_error: str | None = None
        if "wiki_compiler" in roles and can_compile:
            try:
                if execute_compile:
                    receipt_path = _execute_a4(root, event)
                else:
                    receipt_value = event.get("compile_receipt_path")
                    if not isinstance(receipt_value, str):
                        raise ValueError(
                            "compile_receipt_path is required when execute_compile is false"
                        )
                    receipt_path = _safe_path(root, receipt_value)
                compile_review = verify_compile_receipt(root, receipt_path)
            except (OSError, ValueError) as exc:
                compiler_error = str(exc)
                compile_review = {
                    "role": "wiki_compiler_verifier",
                    "status": "REPAIR",
                    "issues": [compiler_error],
                    "output_hashes": {},
                    "targets": [],
                }
            reviews.append(compile_review)

        successful_compile = bool(
            "wiki_compiler" in roles
            and compile_review is not None
            and compile_review.get("status") == "PASS"
        )
        status = "PASS" if (
            all(review["status"] not in {"DATA_GAP", "REPAIR"} for review in reviews)
            and ("wiki_compiler" not in roles or successful_compile)
        ) else "REPAIR"
        conflicts = (
            contradiction_review.get("preserved_conflicts", [])
            if contradiction_review
            else []
        )
        delta = {
            "schema_version": "knowledge-delta/v1",
            "run_id": run_id,
            "status": "compiled" if successful_compile else "not_compiled",
            "targets": compile_review.get("targets", []) if compile_review else [],
            "output_hashes": compile_review.get("output_hashes", {}) if compile_review else {},
            "preserved_conflicts": conflicts,
        }

        _atomic_json(run_dir / "route.json", route)
        for review in reviews:
            _atomic_json(run_dir / "reviews" / f"{review['role']}.json", review)
        _atomic_json(run_dir / "knowledge-delta.json", delta)

        invalidation_path: Path | None = None
        if successful_compile:
            invalidation = {
                "schema_version": "retrieval-invalidation/v1",
                "run_id": run_id,
                "reason": "verified_wiki_compile",
                "compile_receipt_path": compile_review["receipt_path"],
                "compile_receipt_sha256": compile_review["receipt_sha256"],
                "output_hashes": compile_review.get("output_hashes", {}),
                "created_at": utc_now_iso(),
            }
            invalidation_path = root / INVALIDATIONS_DIR / f"{run_id}.json"
            _atomic_json(invalidation_path, invalidation)

        receipt = {
            "schema_version": "knowledge-workflow/v1",
            "run_id": run_id,
            "status": status,
            "event_sha256": event_hash,
            "selected_roles": roles,
            "compiler_error": compiler_error,
            "route_path": (run_dir / "route.json").relative_to(root).as_posix(),
            "review_paths": [
                (run_dir / "reviews" / f"{review['role']}.json")
                .relative_to(root)
                .as_posix()
                for review in reviews
            ],
            "knowledge_delta_path": (run_dir / "knowledge-delta.json")
            .relative_to(root)
            .as_posix(),
            "retrieval_invalidation_path": (
                invalidation_path.relative_to(root).as_posix()
                if invalidation_path
                else None
            ),
            "completed_at": utc_now_iso(),
        }
        _atomic_json(run_dir / "workflow-receipt.json", receipt)
        return receipt
