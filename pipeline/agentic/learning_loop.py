"""Guarded learning loop: capture, propose, evaluate; never auto-apply."""

from __future__ import annotations

import hashlib
import json
from datetime import date
from pathlib import Path

from pipeline.agentic.audit_log import snapshot_file
from pipeline.agentic.contracts import LearningEvent, LearningProposal


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
