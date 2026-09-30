"""Guarded learning loop: capture, propose, evaluate; never auto-apply."""

from __future__ import annotations

import hashlib
import json
import os
import re
import tempfile
import uuid
from contextlib import contextmanager
from datetime import date
from pathlib import Path
from typing import Any, Iterator

import fcntl

from pipeline.agentic.audit_log import append_audit_event, snapshot_file
from pipeline.agentic.approval_policy import require_approval_authority
from pipeline.agentic.contracts import LearningEvent, LearningProposal, utc_now_iso
from pipeline.agentic.skill_eval import evaluate_learning_proposal
from pipeline.agentic.validator_registry import (
    allowed_validator_ids,
    require_current_validator_receipts,
    run_required_validators,
)


CREATOR_FEEDBACK_PENDING_LINKAGE = "package_local_pending_linkage"


def hash_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _string_values(value: object) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(item) for item in value if str(item).strip()]


def atomic_create_text(path: Path, text: str) -> bool:
    """Create a complete file without overwriting an existing path."""

    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{path.name}.",
        suffix=".tmp",
        dir=path.parent,
    )
    temporary_path = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            handle.write(text)
            handle.flush()
            os.fsync(handle.fileno())
        try:
            os.link(temporary_path, path)
        except FileExistsError:
            return False
        return True
    finally:
        temporary_path.unlink(missing_ok=True)


def atomic_write_text(path: Path, text: str) -> None:
    """Replace a text file only after its complete contents are durable."""

    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{path.name}.",
        suffix=".tmp",
        dir=path.parent,
    )
    temporary_path = Path(temporary_name)
    try:
        mode = path.stat().st_mode & 0o777 if path.exists() else 0o644
        os.fchmod(descriptor, mode)
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            handle.write(text)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary_path, path)
    finally:
        temporary_path.unlink(missing_ok=True)


def validate_event_id(event_id: str) -> str:
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]{0,127}", event_id):
        raise ValueError("event_id must be a filename-safe stable identifier")
    return event_id


def same_learning_event(left: LearningEvent, right: LearningEvent) -> bool:
    return left.model_dump(exclude={"created_at"}) == right.model_dump(exclude={"created_at"})


def read_learning_event(path: Path) -> LearningEvent:
    payload = read_json(path)
    if not payload:
        raise ValueError(f"existing learning event is not valid JSON: {path}")
    return LearningEvent.model_validate(payload)


def safe_repo_path(
    root: Path,
    supplied_path: str | Path,
    *,
    label: str,
    allow_absolute: bool = False,
) -> Path:
    """Resolve a non-symlink path and prove that it remains under the workspace."""

    raw = Path(supplied_path)
    if not str(supplied_path).strip():
        raise ValueError(f"{label} must not be empty")
    if raw.is_absolute() and not allow_absolute:
        raise ValueError(f"{label} must be workspace-relative")
    if ".." in raw.parts:
        raise ValueError(f"{label} must not contain parent traversal")

    candidate = raw if raw.is_absolute() else root / raw
    lexical_path = Path(os.path.abspath(candidate))
    try:
        relative_parts = lexical_path.relative_to(root).parts
    except ValueError as error:
        raise ValueError(f"{label} must stay inside the workspace") from error

    cursor = root
    for part in relative_parts:
        cursor /= part
        if cursor.is_symlink():
            raise ValueError(f"{label} must not traverse a symlink: {cursor}")

    resolved_path = lexical_path.resolve(strict=False)
    try:
        resolved_path.relative_to(root)
    except ValueError as error:
        raise ValueError(f"{label} must stay inside the workspace") from error
    return resolved_path


@contextmanager
def learning_apply_lock(root: Path, proposal_path: Path) -> Iterator[None]:
    """Serialize validation and application for one stable proposal path."""

    proposal_key = proposal_path.relative_to(root).as_posix()
    lock_id = hashlib.sha256(proposal_key.encode("utf-8")).hexdigest()[:24]
    lock_dir = root / "memory" / "agentic" / "locks"
    lock_dir.mkdir(parents=True, exist_ok=True)
    lock_path = lock_dir / f"apply-{lock_id}.lock"
    with lock_path.open("a+", encoding="utf-8") as lock_handle:
        fcntl.flock(lock_handle.fileno(), fcntl.LOCK_EX)
        try:
            yield
        finally:
            fcntl.flock(lock_handle.fileno(), fcntl.LOCK_UN)


@contextmanager
def learning_proposal_create_lock(root: Path) -> Iterator[None]:
    """Serialize proposal deduplication and identifier allocation."""

    lock_dir = root / "memory" / "agentic" / "locks"
    lock_dir.mkdir(parents=True, exist_ok=True)
    lock_path = lock_dir / "create-learning-proposal.lock"
    with lock_path.open("a+", encoding="utf-8") as lock_handle:
        fcntl.flock(lock_handle.fileno(), fcntl.LOCK_EX)
        try:
            yield
        finally:
            fcntl.flock(lock_handle.fileno(), fcntl.LOCK_UN)


def capture_learning_event(
    root: Path,
    *,
    source: str,
    summary: str,
    evidence_paths: list[str] | None = None,
    event_id: str | None = None,
    user_instruction_exact: str | None = None,
    diagnosis: str | None = None,
    scope: str | None = None,
    package_path: str | None = None,
    feedback_status: str | None = None,
    resolution_evidence: list[str] | None = None,
    eval_disposition: str | None = None,
    supersedes_event_id: str | None = None,
    feedback_metadata: dict[str, object] | None = None,
) -> LearningEvent:
    root = root.resolve()
    directory = root / "memory" / "agentic" / "learning-events"
    directory.mkdir(parents=True, exist_ok=True)
    feedback_metadata = (
        dict(feedback_metadata) if isinstance(feedback_metadata, dict) else feedback_metadata
    )
    if source == "creator_feedback":
        feedback_status = feedback_status or "captured"
        metadata = feedback_metadata or {}
        has_feedback_link = bool(
            package_path and str(metadata.get("feedback_id") or "").strip()
        )
        if eval_disposition is None:
            eval_disposition = (
                "background" if has_feedback_link else CREATOR_FEEDBACK_PENDING_LINKAGE
            )
    supplied_event_id = event_id is not None
    if event_id is None:
        event_id = f"event-{date.today().isoformat()}-{uuid.uuid4().hex[:12]}"
    event_id = validate_event_id(event_id)
    path = directory / f"{event_id}.json"

    event_values: dict[str, Any] = {
        "event_id": event_id,
        "source": source,
        "summary": summary,
        "evidence_paths": evidence_paths or [],
        "user_instruction_exact": user_instruction_exact,
        "diagnosis": diagnosis,
        "scope": scope,
        "package_path": package_path,
        "feedback_status": feedback_status,
        "resolution_evidence": resolution_evidence or [],
        "eval_disposition": eval_disposition,
        "supersedes_event_id": supersedes_event_id,
        "feedback_metadata": feedback_metadata,
    }
    if path.exists():
        existing = read_learning_event(path)
        candidate = LearningEvent(**event_values, created_at=existing.created_at)
        if source == "creator_feedback":
            candidate = candidate.model_copy(update={
                "feedback_status": existing.feedback_status,
                "resolution_evidence": existing.resolution_evidence,
                "eval_disposition": existing.eval_disposition,
            })
        if supplied_event_id and same_learning_event(existing, candidate):
            return existing
        raise ValueError(f"learning event_id already exists with different content: {event_id}")

    event = LearningEvent(**event_values)
    serialized = json.dumps(event.model_dump(mode="json"), indent=2, ensure_ascii=False) + "\n"
    created = atomic_create_text(path, serialized)
    if created:
        return event

    existing = read_learning_event(path)
    candidate = event.model_copy(update={"created_at": existing.created_at})
    if supplied_event_id and same_learning_event(existing, candidate):
        return existing
    raise ValueError(f"learning event_id already exists with different content: {event_id}")


def update_learning_event(
    root: Path,
    event_id: str,
    *,
    feedback_status: str,
    resolution_evidence: list[str],
    eval_disposition: str,
) -> LearningEvent:
    """Update lifecycle evidence while preserving the captured event identity."""

    root = root.resolve()
    event_id = validate_event_id(event_id)
    path = root / "memory" / "agentic" / "learning-events" / f"{event_id}.json"
    existing = read_learning_event(path)
    updated = existing.model_copy(
        update={
            "feedback_status": feedback_status,
            "resolution_evidence": list(resolution_evidence),
            "eval_disposition": eval_disposition,
        }
    )
    atomic_write_text(
        path,
        json.dumps(updated.model_dump(mode="json"), indent=2, ensure_ascii=False) + "\n",
    )
    return updated


def create_learning_proposal(
    root: Path,
    *,
    source_event_id: str,
    target_path: str,
    proposed_action: str,
    rationale: str,
    proposed_content: str,
    required_validators: list[str],
    dedupe_key: str | None = None,
    normalized_behavior: str | None = None,
    supporting_event_ids: list[str] | None = None,
    supporting_package_paths: list[str] | None = None,
) -> Path:
    root = root.resolve()
    unknown_validators = sorted(set(required_validators) - allowed_validator_ids(root))
    if unknown_validators:
        raise ValueError(
            "proposal requires non-allow-listed validators: "
            + ", ".join(unknown_validators)
        )
    directory = root / "memory" / "agentic" / "learning-proposals"
    content_dir = directory / "content"
    content_dir.mkdir(parents=True, exist_ok=True)
    with learning_proposal_create_lock(root):
        if dedupe_key:
            for existing_path in sorted(directory.glob("*.json")):
                existing = read_json(existing_path)
                if (
                    existing.get("target_path") == target_path
                    and existing.get("learning_pattern_key") == dedupe_key
                ):
                    if existing.get("status") in {"draft", "approved"}:
                        existing["supporting_event_ids"] = sorted(
                            set(_string_values(existing.get("supporting_event_ids")))
                            | set(supporting_event_ids or [])
                        )
                        existing["supporting_package_paths"] = sorted(
                            set(_string_values(existing.get("supporting_package_paths")))
                            | set(supporting_package_paths or [])
                        )
                        atomic_write_text(
                            existing_path,
                            json.dumps(existing, indent=2, ensure_ascii=False) + "\n",
                        )
                    return existing_path

        target = safe_repo_path(root, target_path, label="target_path")
        before_text = target.read_text(encoding="utf-8") if target.exists() else ""
        if target.exists():
            snapshot_file(root, target_path)
        prefix = f"proposal-{date.today().isoformat()}"
        for index in range(1, 10000):
            proposal_id = f"{prefix}-{index}"
            path = directory / f"{proposal_id}.json"
            if not path.exists():
                break
        else:
            raise RuntimeError("Could not allocate learning proposal id")
        content_path = content_dir / f"{proposal_id}.md"
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
        ).model_dump()
        if dedupe_key:
            proposal["learning_pattern_key"] = dedupe_key
            proposal["normalized_behavior"] = normalized_behavior or ""
            proposal["supporting_event_ids"] = sorted(set(supporting_event_ids or []))
            proposal["supporting_package_paths"] = sorted(
                set(supporting_package_paths or [])
            )
        if not atomic_create_text(content_path, proposed_content):
            raise RuntimeError(f"Learning proposal content path already exists: {content_path}")
        if not atomic_create_text(
            path,
            json.dumps(proposal, indent=2, ensure_ascii=False) + "\n",
        ):
            content_path.unlink(missing_ok=True)
            raise RuntimeError(f"Learning proposal path appeared concurrently: {path}")
        return path


def _validate_feedback_proposal_evidence(
    root: Path,
    proposal: dict[str, Any],
) -> None:
    """Fail closed when durable learning is no longer backed by current evals."""

    source_event_id = str(proposal.get("source_event_id") or "")
    supporting_ids = _string_values(proposal.get("supporting_event_ids"))
    event_ids = list(dict.fromkeys([source_event_id, *supporting_ids]))
    declared_supporting_packages = set(
        _string_values(proposal.get("supporting_package_paths"))
    )
    covered_packages: set[str] = set()
    feedback_events = 0

    for event_id in event_ids:
        if not event_id:
            continue
        event_path = (
            root
            / "memory"
            / "agentic"
            / "learning-events"
            / f"{validate_event_id(event_id)}.json"
        )
        event = read_json(event_path)
        # Legacy non-feedback proposals did not require a stored source event.
        # A declared supporting event, however, is evidence and must exist.
        if not event:
            if event_id in supporting_ids:
                raise ValueError(
                    f"supporting learning event is missing or invalid: {event_id}"
                )
            continue
        if event.get("source") != "creator_feedback":
            continue

        feedback_events += 1
        metadata = event.get("feedback_metadata") or {}
        if not isinstance(metadata, dict) or not metadata.get("feedback_id"):
            raise ValueError(
                f"creator-feedback learning event lacks feedback identity: {event_id}"
            )
        package_value = str(event.get("package_path") or "").strip()
        if not package_value:
            raise ValueError(
                f"creator-feedback learning event lacks package_path: {event_id}"
            )
        package_path = safe_repo_path(
            root,
            package_value,
            label=f"learning event {event_id} package_path",
            allow_absolute=True,
        )

        from evals.feedback_cases import feedback_case_is_current, load_feedback_case
        from pipeline.stages.carousel_visual_storytelling import creator_feedback_records

        feedback_id = str(metadata["feedback_id"])
        try:
            feedback = next(
                item
                for item in creator_feedback_records(package_path)
                if item.get("feedback_id") == feedback_id
            )
        except (OSError, ValueError, StopIteration) as error:
            raise ValueError(
                f"supporting creator feedback is missing or invalid: {feedback_id}"
            ) from error
        if feedback.get("learning_disposition") == "declined" or feedback.get(
            "status"
        ) == "rejected":
            raise ValueError(
                f"supporting creator feedback is not eligible for learning: {feedback_id}"
            )
        task_ids = _string_values(feedback.get("eval_task_ids"))
        if not task_ids:
            raise ValueError(
                f"supporting creator feedback has no deterministic eval: {feedback_id}"
            )
        for task_id in task_ids:
            try:
                case = load_feedback_case(root, task_id)
            except (OSError, ValueError) as error:
                raise ValueError(
                    f"supporting creator feedback eval is missing or invalid: {task_id}"
                ) from error
            if case.get("status") != "passed" or not feedback_case_is_current(
                package_path, case, feedback
            ):
                raise ValueError(
                    f"supporting creator feedback eval is stale or not passing: {task_id}"
                )
        try:
            covered_packages.add(package_path.relative_to(root).as_posix())
        except ValueError:
            covered_packages.add(str(package_path))

    if feedback_events and declared_supporting_packages - covered_packages:
        missing = ", ".join(
            sorted(declared_supporting_packages - covered_packages)
        )
        raise ValueError(
            f"supporting package paths lack current feedback evidence: {missing}"
        )


def approve_learning_proposal(
    root: Path,
    proposal_path: Path,
    *,
    approved_by: str,
) -> dict[str, Any]:
    """Record explicit human approval without applying the proposed content."""

    root = root.resolve()
    reviewer = approved_by.strip()
    path = safe_repo_path(root, proposal_path, label="proposal_path", allow_absolute=True)
    with learning_apply_lock(root, path):
        payload = read_json(path)
        status = str(payload.get("status") or "")
        retry = status == "approved" and payload.get("creator_approved_by") == reviewer
        if status != "draft" and not retry:
            raise ValueError("only a draft learning proposal can be approved")
        _validate_feedback_proposal_evidence(root, payload)
        target_value = str(payload.get("target_path") or "")
        authority = require_approval_authority(
            root, approver=reviewer, target_path=target_value
        )
        if authority != "creator":
            raise ValueError("feedback-derived learning requires explicit creator authority")
        source = read_json(
            root / "memory" / "agentic" / "learning-events" / f"{payload.get('source_event_id')}.json"
        )
        metadata = source.get("feedback_metadata") or {}
        package_path: Path | None = None
        feedback_id = ""
        feedback_status = ""
        if source.get("source") == "creator_feedback" and isinstance(metadata, dict) and metadata.get("feedback_id") and source.get("package_path"):
            package_path = safe_repo_path(
                root,
                str(source["package_path"]),
                label="learning event package_path",
                allow_absolute=True,
            )
            feedback_id = str(metadata["feedback_id"])
            from pipeline.stages.carousel_visual_storytelling import creator_feedback_records

            feedback_status = str(next(
                item for item in creator_feedback_records(package_path)
                if item.get("feedback_id") == feedback_id
            ).get("status") or "")
            if feedback_status not in {"learning_proposed", "approved"}:
                raise ValueError(
                    "linked creator feedback must be learning_proposed or approved before approval"
                )

        if not retry:
            payload["status"] = "approved"
            payload["creator_approved_by"] = reviewer
            payload["creator_approved_at"] = utc_now_iso()
            atomic_write_text(path, json.dumps(payload, indent=2, ensure_ascii=False) + "\n")

        if package_path is not None:
            from pipeline.stages.carousel_visual_storytelling import update_creator_feedback_event

            if feedback_status == "learning_proposed":
                update_creator_feedback_event(
                    package_path,
                    feedback_id,
                    updates={"status": "approved"},
                    expected_status="learning_proposed",
                )
            update_learning_event(
                root,
                str(payload.get("source_event_id")),
                feedback_status="approved",
                resolution_evidence=list(source.get("resolution_evidence") or []),
                eval_disposition=str(source.get("eval_disposition") or "passed"),
            )
        return payload


def decline_learning_proposal(
    root: Path,
    proposal_path: Path,
    *,
    declined_by: str,
    reason: str,
) -> dict[str, Any]:
    """Close a policy proposal without rejecting its package-level correction.

    A creator correction and a proposed global learning are separate decisions.
    Declining the latter records a separate learning disposition. Correction
    evidence remains eligible for revision and generation.
    """

    root = root.resolve()
    reviewer = declined_by.strip()
    rationale = reason.strip()
    if not reviewer:
        raise ValueError("declined_by must identify the reviewer")
    if not rationale:
        raise ValueError("reason is required when declining a learning proposal")
    path = safe_repo_path(root, proposal_path, label="proposal_path", allow_absolute=True)
    with learning_apply_lock(root, path):
        payload = read_json(path)
        status = str(payload.get("status") or "")
        retry = status == "rejected" and payload.get("decision") == "declined"
        if retry:
            if (
                payload.get("declined_by") == reviewer
                and payload.get("declined_reason") == rationale
            ):
                pass
            else:
                raise ValueError("learning proposal was already declined with a different decision")
        if status not in {"draft", "approved"} and not retry:
            raise ValueError(
                f"only a draft or approved learning proposal can be declined, got {status}"
            )

        source_event_id = validate_event_id(str(payload.get("source_event_id") or ""))
        source_path = (
            root / "memory" / "agentic" / "learning-events" / f"{source_event_id}.json"
        )
        source = read_json(source_path)
        metadata = source.get("feedback_metadata") or {}
        package_path: Path | None = None
        feedback_id = ""
        feedback_status = ""
        if (
            source.get("source") == "creator_feedback"
            and isinstance(metadata, dict)
            and metadata.get("feedback_id")
            and source.get("package_path")
        ):
            package_path = safe_repo_path(
                root,
                str(source["package_path"]),
                label="learning event package_path",
                allow_absolute=True,
            )
            from pipeline.stages.carousel_visual_storytelling import creator_feedback_records

            feedback_id = str(metadata["feedback_id"])
            feedback = next(
                item
                for item in creator_feedback_records(package_path)
                if item.get("feedback_id") == feedback_id
            )
            feedback_status = str(feedback.get("status") or "")
            already_converged = (
                feedback_status == "evaluated"
                and feedback.get("learning_disposition") == "declined"
            )
            if feedback_status not in {"learning_proposed", "approved"} and not (
                retry and (feedback_status == "evaluated" or already_converged)
            ):
                raise ValueError(
                    "linked creator feedback must be learning_proposed or approved before "
                    f"decline, got {feedback_status}"
                )

        if not retry:
            payload["status"] = "rejected"
            payload["decision"] = "declined"
            payload["declined_by"] = reviewer
            payload["declined_reason"] = rationale
            payload["declined_at"] = utc_now_iso()
            atomic_write_text(path, json.dumps(payload, indent=2, ensure_ascii=False) + "\n")

        if package_path is not None:
            from pipeline.stages.carousel_visual_storytelling import (
                update_creator_feedback_event,
            )

            update_creator_feedback_event(
                package_path,
                feedback_id,
                updates={"status": "evaluated", "learning_disposition": "declined"},
                expected_status=feedback_status,
            )
            update_learning_event(
                root,
                source_event_id,
                feedback_status="evaluated",
                resolution_evidence=list(source.get("resolution_evidence") or []),
                eval_disposition=str(source.get("eval_disposition") or "passed"),
            )

        if not retry:
            append_audit_event(
                root,
                actor=reviewer,
                action="decline_learning_proposal",
                target_path=relative_to(root, path),
                rationale=rationale,
                evidence_paths=[relative_to(root, path)],
            )
        return payload


def apply_learning_proposal(root: Path, proposal_path: Path, *, approved_by: str) -> dict[str, Any]:
    root = root.resolve()
    approved_by = approved_by.strip()
    if not approved_by:
        raise ValueError("approved_by must identify the reviewer applying the proposal")
    proposal_path = safe_repo_path(
        root,
        proposal_path,
        label="proposal_path",
        allow_absolute=True,
    )
    with learning_apply_lock(root, proposal_path):
        return apply_learning_proposal_locked(root, proposal_path, approved_by=approved_by)


def apply_learning_proposal_locked(
    root: Path,
    proposal_path: Path,
    *,
    approved_by: str,
) -> dict[str, Any]:
    payload = read_json(proposal_path)
    proposal_status = str(payload.get("status", ""))
    if proposal_status not in {"draft", "approved"}:
        raise ValueError(f"proposal status must be draft or approved before apply, got {proposal_status}")

    source_event_id = str(payload.get("source_event_id") or "")
    source_path = root / "memory" / "agentic" / "learning-events" / f"{source_event_id}.json"
    source_event = read_json(source_path)
    if source_event.get("source") == "creator_feedback":
        _validate_feedback_proposal_evidence(root, payload)
        target_for_approval = str(payload.get("target_path") or "")
        try:
            feedback_authority = require_approval_authority(
                root, approver=approved_by, target_path=target_for_approval
            )
        except ValueError as error:
            raise ValueError(
                "feedback-derived rule, skill, or memory changes require creator approval before apply"
            ) from error
        if proposal_status == "draft" and feedback_authority == "creator":
            payload["creator_approved_by"] = approved_by
            payload["creator_approved_at"] = utc_now_iso()
        elif proposal_status != "approved" or not str(payload.get("creator_approved_by") or ""):
            raise ValueError(
                "feedback-derived rule, skill, or memory changes require creator approval before apply"
            )

    target_path_value = payload.get("target_path")
    if not isinstance(target_path_value, str) or not target_path_value.strip():
        raise ValueError("proposal missing target_path")
    # Reject a malicious target before any evaluator resolves it. For a safe
    # target, preserve the existing public contract by reporting proposal-policy
    # failures before resolving the proposed content file.
    target = safe_repo_path(root, target_path_value, label="target_path")
    result = evaluate_learning_proposal(root, proposal_path)
    if result.status != "PASS":
        raise ValueError(f"skill_eval failed: {'; '.join(result.issues)}")

    content_path_value = payload.get("proposed_content_path")
    if not isinstance(content_path_value, str) or not content_path_value.strip():
        raise ValueError("proposal missing proposed_content_path")
    content = safe_repo_path(root, content_path_value, label="proposed_content_path")
    if not content.is_file():
        raise ValueError(f"proposed_content_path must be a regular file: {content_path_value}")

    action = payload.get("proposed_action")
    if action not in {"create", "modify", "deprecate"}:
        raise ValueError(f"unsupported proposed_action: {action}")
    if action == "create" and target.exists():
        raise ValueError(f"target already exists for create proposal: {target_path_value}")
    if action in {"modify", "deprecate"} and not target.is_file():
        raise ValueError(f"target_path missing for {action} proposal: {target_path_value}")

    proposed_content = content.read_text(encoding="utf-8")
    proposed_hash = hash_text(proposed_content)
    if payload.get("after_hash") != proposed_hash:
        raise ValueError("proposed content changed after proposal creation (after_hash mismatch)")

    before_text = target.read_text(encoding="utf-8") if target.exists() else ""
    current_before_hash = hash_text(before_text)
    if payload.get("before_hash") != current_before_hash:
        raise ValueError("target changed since proposal creation (before_hash mismatch)")

    approval_authority = require_approval_authority(
        root, approver=approved_by, target_path=target_path_value
    )
    validator_receipts = require_current_validator_receipts(root, proposal_path)

    target_path = target.relative_to(root).as_posix()

    snapshot = snapshot_file(root, target_path) if target.exists() else None
    atomic_write_text(target, proposed_content)

    payload["status"] = "applied"
    payload["applied_by"] = approved_by
    payload["approved_by"] = payload.get("creator_approved_by", approved_by)
    payload["approval_authority"] = approval_authority
    payload["validator_receipts"] = validator_receipts
    payload["applied_at"] = utc_now_iso()
    atomic_write_text(
        proposal_path,
        json.dumps(payload, indent=2, ensure_ascii=False) + "\n",
    )

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

    if source_event.get("source") == "creator_feedback":
        metadata = source_event.get("feedback_metadata") or {}
        if isinstance(metadata, dict) and metadata.get("feedback_id") and source_event.get("package_path"):
            package_path = Path(str(source_event.get("package_path") or ""))
            if not package_path.is_absolute():
                package_path = root / package_path
            from pipeline.stages.carousel_visual_storytelling import creator_feedback_records, update_creator_feedback_event

            current_feedback = next(item for item in creator_feedback_records(package_path) if item.get("feedback_id") == metadata["feedback_id"])
            if current_feedback.get("status") == "learning_proposed":
                update_creator_feedback_event(package_path, metadata["feedback_id"], updates={"status": "approved"}, expected_status="learning_proposed")

            update_creator_feedback_event(
                package_path,
                str(metadata.get("feedback_id") or ""),
                updates={"status": "promoted"},
                expected_status="approved",
            )
            update_learning_event(
                root,
                source_event_id,
                feedback_status="promoted",
                resolution_evidence=list(source_event.get("resolution_evidence") or []),
                eval_disposition=str(source_event.get("eval_disposition") or "passed"),
            )

    return {
        "proposal_id": payload.get("proposal_id", proposal_path.stem),
        "status": "applied",
        "target_path": target_path,
        "proposal_path": relative_to(root, proposal_path),
        "snapshot_path": relative_to(root, snapshot),
        "audit_path": relative_to(root, audit_path),
        "approval_authority": approval_authority,
        "validator_receipts": validator_receipts,
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
        next_action = "validate_then_review_then_apply_learning"
    elif result.status == "PASS" and proposal_status == "approved":
        next_action = "apply_learning"
    elif result.status == "PASS" and proposal_status == "applied":
        next_action = "none"
    elif proposal_status == "rejected":
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


def learning_debt_records(root: Path, limit: int | None = 5) -> list[dict[str, str]]:
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
    from datetime import date
    from pipeline.stages.wiki_health import feedback_health_evidence

    for repair in feedback_health_evidence(root, date.today())["unresolved_records"]:
        candidates.append(("feedback_repair", root / repair["source"], repair, repair["created_at"]))
    for path, payload in events:
        event_id = str(payload.get("event_id", path.stem))
        metadata = payload.get("feedback_metadata") or {}
        if payload.get("source") == "creator_feedback" and metadata.get("feedback_id"):
            # Repair debt is different from policy-proposal debt. A resolved
            # correction needs no generalized rule, and historical metadata is
            # not an obligation to create one.
            continue
        if metadata.get("superseded_by_event_ids"):
            replacements = [root / "memory/agentic/learning-events" / f"{event_id}.json"
                            for event_id in metadata["superseded_by_event_ids"]
                            if isinstance(event_id, str) and re.fullmatch(r"event-[A-Za-z0-9._-]+", event_id)]
            if replacements and all(item.is_file() for item in replacements):
                continue
        unlinked_creator_feedback = payload.get("source") == "creator_feedback"
        if unlinked_creator_feedback:
            # A generic creator-feedback capture is package-local repair input
            # until it is linked to the canonical creator-correction surface.
            # It must stay visible, but it cannot silently assert that a global
            # rule/skill/memory proposal is required. An explicit proposal can
            # still cite this event through create_learning_proposal().
            if event_id not in proposed_event_ids:
                if payload.get("eval_disposition") != "background":
                    candidates.append(
                        ("feedback_linkage", path, payload, str(payload.get("created_at", "")))
                    )
            continue
        annotation_candidate = bool(
            payload.get("source") == "langfuse_annotation_candidate"
            and payload.get("eval_disposition") == "candidate_only"
        )
        if annotation_candidate:
            candidates.append(
                ("candidate_review", path, payload, str(payload.get("created_at", "")))
            )
            continue
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
        if kind == "feedback_repair":
            line = f"repair unresolved creator feedback {payload.get('event_id', path.stem)}: {compact(payload.get('summary', ''))}"
        elif kind == "feedback_linkage":
            line = (
                f"link package-local creator feedback {payload.get('event_id', path.stem)} "
                f"to a correction before durable learning: "
                f"{compact(payload.get('summary', ''))}"
            )
        elif kind == "candidate_review":
            line = (
                f"review imported annotation {payload.get('event_id', path.stem)}: "
                f"{compact(payload.get('summary', ''))}"
            )
        elif kind == "event":
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
