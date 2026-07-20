"""Guarded learning loop: capture, propose, evaluate; never auto-apply."""

from __future__ import annotations

import hashlib
import json
from datetime import date
from pathlib import Path
from typing import Any

from pipeline.agentic.audit_log import append_audit_event, snapshot_file
from pipeline.agentic.contracts import LearningEvent, LearningProposal, utc_now_iso
from pipeline.agentic.skill_eval import evaluate_learning_proposal


def hash_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def capture_learning_event(
    root: Path,
    *,
    source: str,
    summary: str,
    evidence_paths: list[str] | None = None,
) -> LearningEvent:
    root = root.resolve()
    directory = root / "memory" / "agentic" / "learning-events"
    directory.mkdir(parents=True, exist_ok=True)
    event_id = f"event-{date.today().isoformat()}-{len(list(directory.glob('*.json'))) + 1}"
    event = LearningEvent(
        event_id=event_id,
        source=source,
        summary=summary,
        evidence_paths=evidence_paths or [],
    )
    (directory / f"{event_id}.json").write_text(
        event.model_dump_json(indent=2) + "\n",
        encoding="utf-8",
    )
    return event


def create_learning_proposal(
    root: Path,
    *,
    source_event_id: str,
    target_path: str,
    proposed_action: str,
    rationale: str,
    proposed_content: str,
    required_validators: list[str],
) -> Path:
    root = root.resolve()
    target = root / target_path
    before_text = target.read_text(encoding="utf-8") if target.exists() else ""
    if target.exists():
        snapshot_file(root, target_path)

    directory = root / "memory" / "agentic" / "learning-proposals"
    content_dir = directory / "content"
    content_dir.mkdir(parents=True, exist_ok=True)
    proposal_id = f"proposal-{date.today().isoformat()}-{len(list(directory.glob('*.json'))) + 1}"
    content_path = content_dir / f"{proposal_id}.md"
    content_path.write_text(proposed_content, encoding="utf-8")
    proposal = LearningProposal(
        proposal_id=proposal_id,
        source_event_id=source_event_id,
        target_path=target_path,
        proposed_action=proposed_action,  # type: ignore[arg-type]
        rationale=rationale,
        before_hash=hash_text(before_text),
        after_hash=hash_text(proposed_content),
        required_validators=required_validators,
        proposed_content_path=content_path.relative_to(root).as_posix(),
    )
    path = directory / f"{proposal_id}.json"
    path.write_text(json.dumps(proposal.model_dump(), indent=2) + "\n", encoding="utf-8")
    return path


def apply_learning_proposal(root: Path, proposal_path: Path, *, approved_by: str) -> dict[str, Any]:
    root = root.resolve()
    if not proposal_path.is_absolute():
        proposal_path = root / proposal_path
    payload = read_json(proposal_path)
    proposal_status = str(payload.get("status", ""))
    if proposal_status not in {"draft", "approved"}:
        raise ValueError(f"proposal status must be draft or approved before apply, got {proposal_status}")
    result = evaluate_learning_proposal(root, proposal_path)
    if result.status != "PASS":
        raise ValueError(f"skill_eval failed: {'; '.join(result.issues)}")

    content_path = payload.get("proposed_content_path")
    if not content_path:
        raise ValueError("proposal missing proposed_content_path")
    target_path = str(payload.get("target_path", ""))
    target = root / target_path
    proposed_content = (root / str(content_path)).read_text(encoding="utf-8")

    snapshot = snapshot_file(root, target_path) if target.exists() else None
    if payload.get("proposed_action") in {"create", "modify"}:
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(proposed_content, encoding="utf-8")
    elif payload.get("proposed_action") == "deprecate":
        target.write_text(proposed_content, encoding="utf-8")
    else:
        raise ValueError(f"unsupported proposed_action: {payload.get('proposed_action')}")

    payload["status"] = "applied"
    payload["approved_by"] = approved_by
    payload["applied_at"] = utc_now_iso()
    proposal_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    evidence = [relative_to(root, proposal_path)]
    if snapshot:
        evidence.append(relative_to(root, snapshot))
    audit_path = append_audit_event(
        root,
        actor=approved_by,
        action="apply_learning_proposal",
        target_path=target_path,
        rationale=str(payload.get("rationale", "")),
        evidence_paths=evidence,
    )

    return {
        "proposal_id": payload.get("proposal_id", proposal_path.stem),
        "status": "applied",
        "target_path": target_path,
        "proposal_path": relative_to(root, proposal_path),
        "snapshot_path": relative_to(root, snapshot),
        "audit_path": relative_to(root, audit_path),
    }


def evaluate_learning_proposal_review(root: Path, proposal_path: Path) -> dict[str, Any]:
    root = root.resolve()
    if not proposal_path.is_absolute():
        proposal_path = root / proposal_path
    payload = read_json(proposal_path)
    result = evaluate_learning_proposal(root, proposal_path)
    proposal_status = str(payload.get("status", "unknown"))
    next_action = "fix_proposal"
    if result.status == "PASS" and proposal_status == "draft":
        next_action = "review_then_apply_learning"
    elif result.status == "PASS" and proposal_status == "approved":
        next_action = "apply_learning"
    elif result.status == "PASS" and proposal_status == "applied":
        next_action = "none"

    return {
        "proposal_id": result.proposal_id,
        "status": result.status,
        "issues": result.issues,
        "warnings": result.warnings,
        "proposal_status": proposal_status,
        "target_path": payload.get("target_path", ""),
        "proposed_action": payload.get("proposed_action", ""),
        "rationale": payload.get("rationale", ""),
        "proposed_content_path": payload.get("proposed_content_path", ""),
        "auto_apply": payload.get("auto_apply"),
        "next_action": next_action,
        "apply_command": (
            f"venv/bin/python scripts/agentic_os.py apply-learning "
            f"{relative_to(root, proposal_path)} --approved-by <reviewer>"
        ),
    }


def compact(text: object, limit: int = 180) -> str:
    normalized = " ".join(str(text).split())
    if len(normalized) <= limit:
        return normalized
    return normalized[: limit - 1].rstrip() + "…"


def read_json(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return payload if isinstance(payload, dict) else {}


def relative_to(root: Path, path: Path | None) -> str:
    if not path:
        return "missing"
    try:
        return str(path.relative_to(root))
    except ValueError:
        return str(path)


def recent_learning_records(root: Path, limit: int = 5) -> list[dict[str, str]]:
    candidates: list[tuple[str, Path, dict[str, Any]]] = []
    for kind, pattern in (
        ("event", "memory/agentic/learning-events/*.json"),
        ("proposal", "memory/agentic/learning-proposals/*.json"),
    ):
        for path in root.glob(pattern):
            payload = read_json(path)
            if payload:
                candidates.append((kind, path, payload))

    def sort_key(item: tuple[str, Path, dict[str, Any]]) -> tuple[str, float, str]:
        _, path, payload = item
        return (
            str(payload.get("created_at", "")),
            path.stat().st_mtime,
            path.as_posix(),
        )

    records: list[dict[str, str]] = []
    for kind, path, payload in sorted(candidates, key=sort_key, reverse=True)[:limit]:
        if kind == "event":
            line = (
                f"event {payload.get('event_id', path.stem)} from "
                f"{payload.get('source', 'unknown source')}: "
                f"{compact(payload.get('summary', ''))}"
            )
        else:
            status = payload.get("status", "draft")
            target = payload.get("target_path", "unknown target")
            line = (
                f"proposal-only {status} {payload.get('proposal_id', path.stem)} "
                f"-> {target}: {compact(payload.get('rationale', ''))}"
            )
        records.append(
            {
                "kind": kind,
                "path": relative_to(root, path),
                "line": line,
            }
        )
    return records


def learning_debt_records(root: Path, limit: int = 5) -> list[dict[str, str]]:
    events: list[tuple[Path, dict[str, Any]]] = []
    proposals: list[tuple[Path, dict[str, Any]]] = []
    hypotheses: list[tuple[Path, dict[str, Any]]] = []
    for path in root.glob("memory/agentic/learning-events/*.json"):
        payload = read_json(path)
        if payload:
            events.append((path, payload))
    for path in root.glob("memory/agentic/learning-proposals/*.json"):
        payload = read_json(path)
        if payload:
            proposals.append((path, payload))
    for path in root.glob("memory/agentic/hypotheses/*.json"):
        payload = read_json(path)
        if payload:
            hypotheses.append((path, payload))

    proposed_event_ids = {
        str(payload.get("source_event_id", ""))
        for _, payload in proposals
        if payload.get("source_event_id")
    }
    learned_hypothesis_paths = {
        str(evidence)
        for _, payload in events
        for evidence in payload.get("evidence_paths", [])
        if str(evidence).startswith("memory/agentic/hypotheses/")
    }

    candidates: list[tuple[str, Path, dict[str, Any], str]] = []
    for path, payload in events:
        event_id = str(payload.get("event_id", path.stem))
        if event_id not in proposed_event_ids:
            candidates.append(("event", path, payload, str(payload.get("created_at", ""))))
    for path, payload in hypotheses:
        hypothesis_reference = relative_to(root, path)
        if (
            payload.get("status") == "resolved"
            and payload.get("outcome") == "supported"
            and hypothesis_reference not in learned_hypothesis_paths
        ):
            candidates.append(("supported_hypothesis", path, payload, str(payload.get("resolved_at", ""))))
    for path, payload in proposals:
        status = str(payload.get("status", "draft"))
        if status == "draft":
            candidates.append(("draft_proposal", path, payload, str(payload.get("created_at", ""))))
        elif status == "approved":
            candidates.append(("approved_proposal", path, payload, str(payload.get("created_at", ""))))

    def sort_key(item: tuple[str, Path, dict[str, Any], str]) -> tuple[str, float, str]:
        _, path, _, created_at = item
        return (created_at, path.stat().st_mtime, path.as_posix())

    records: list[dict[str, str]] = []
    for kind, path, payload, _ in sorted(candidates, key=sort_key, reverse=True)[:limit]:
        if kind == "event":
            line = (
                f"needs proposal {payload.get('event_id', path.stem)} from "
                f"{payload.get('source', 'unknown source')}: "
                f"{compact(payload.get('summary', ''))}"
            )
        elif kind == "supported_hypothesis":
            line = (
                f"capture learning from supported hypothesis {payload.get('hypothesis_id', path.stem)}: "
                f"{compact(payload.get('result_summary') or payload.get('hypothesis', ''))}"
            )
        elif kind == "draft_proposal":
            line = (
                f"review draft proposal {payload.get('proposal_id', path.stem)} "
                f"(skill_eval: {proposal_eval_status(root, path)}) "
                f"-> {payload.get('target_path', 'unknown target')}: "
                f"{compact(payload.get('rationale', ''))}"
            )
        else:
            line = (
                f"apply approved proposal {payload.get('proposal_id', path.stem)} "
                f"(skill_eval: {proposal_eval_status(root, path)}) "
                f"-> {payload.get('target_path', 'unknown target')}: "
                f"{compact(payload.get('rationale', ''))}"
            )
        records.append(
            {
                "kind": kind,
                "path": relative_to(root, path),
                "line": line,
            }
        )
    return records


def proposal_eval_status(root: Path, path: Path) -> str:
    try:
        return evaluate_learning_proposal(root, path).status
    except (OSError, json.JSONDecodeError, KeyError, TypeError, ValueError):
        return "FAIL"


def hypothesis_directory(root: Path) -> Path:
    directory = root / "memory" / "agentic" / "hypotheses"
    directory.mkdir(parents=True, exist_ok=True)
    return directory


def next_hypothesis_path(root: Path) -> tuple[str, Path]:
    directory = hypothesis_directory(root)
    prefix = f"hypothesis-{date.today().isoformat()}"
    for index in range(1, 1000):
        hypothesis_id = f"{prefix}-{index}"
        path = directory / f"{hypothesis_id}.json"
        if not path.exists():
            return hypothesis_id, path
    raise RuntimeError("Could not allocate hypothesis id.")


def capture_hypothesis(
    root: Path,
    *,
    source: str,
    hypothesis: str,
    success_signal: str,
    falsifier: str,
    evidence_paths: list[str] | None = None,
) -> dict[str, Any]:
    root = root.resolve()
    hypothesis_id, path = next_hypothesis_path(root)
    payload: dict[str, Any] = {
        "hypothesis_id": hypothesis_id,
        "source": source,
        "hypothesis": hypothesis,
        "success_signal": success_signal,
        "falsifier": falsifier,
        "status": "open",
        "evidence_paths": evidence_paths or [],
        "created_at": utc_now_iso(),
    }
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    payload["hypothesis_path"] = path.relative_to(root).as_posix()
    return payload


def hypothesis_path(root: Path, hypothesis_id: str) -> Path:
    return root / "memory" / "agentic" / "hypotheses" / f"{hypothesis_id}.json"


def resolve_hypothesis(
    root: Path,
    *,
    hypothesis_id: str,
    outcome: str,
    result_summary: str,
    evidence_paths: list[str] | None = None,
) -> dict[str, Any]:
    root = root.resolve()
    path = hypothesis_path(root, hypothesis_id)
    payload = read_json(path)
    if not payload:
        raise FileNotFoundError(f"Missing hypothesis: {hypothesis_id}")

    existing_evidence = list(payload.get("evidence_paths", []))
    for evidence in evidence_paths or []:
        if evidence not in existing_evidence:
            existing_evidence.append(evidence)

    payload.update(
        {
            "status": "resolved",
            "outcome": outcome,
            "result_summary": result_summary,
            "evidence_paths": existing_evidence,
            "resolved_at": utc_now_iso(),
        }
    )
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    payload["hypothesis_path"] = path.relative_to(root).as_posix()
    return payload


def list_hypotheses(
    root: Path,
    *,
    status: str | None = None,
    limit: int = 20,
) -> list[dict[str, Any]]:
    root = root.resolve()
    directory = root / "memory" / "agentic" / "hypotheses"
    if not directory.exists():
        return []

    records: list[dict[str, Any]] = []
    for path in directory.glob("*.json"):
        payload = read_json(path)
        if not payload:
            continue
        if status and payload.get("status") != status:
            continue
        payload["hypothesis_path"] = path.relative_to(root).as_posix()
        records.append(payload)

    return sorted(
        records,
        key=lambda item: (str(item.get("created_at", "")), str(item.get("hypothesis_id", ""))),
        reverse=True,
    )[:limit]
