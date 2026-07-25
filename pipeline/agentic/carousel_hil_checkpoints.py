"""Hash-bound human checkpoints for concept, copy, images, and publish."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Literal

from pipeline.agentic.checks.final_assets import validate_publishable_final_assets
from pipeline.agentic.carousel_state import CarouselState, derive_carousel_state
from pipeline.agentic.workflow_doctor import WorkflowDoctorReport, WorkflowIssue, inspect_carousel_package


Stage = Literal["concept", "copy", "images", "publish"]
Decision = Literal["APPROVE", "REVISE", "REJECT"]
STAGES: tuple[Stage, ...] = ("concept", "copy", "images", "publish")
HIL_DIR = ".internal/hil"
APPROVALS_FILE = "approvals.json"

STAGE_ARTIFACTS: dict[Stage, tuple[str, ...]] = {
    "concept": (
        "source-memory-brief.json",
        "concept-routes.json",
        "concept-debate.json",
        "concept-repairs.json",
        "taste-gate.json",
        "verification.json",
        "concept-selection.json",
    ),
    "copy": (
        "story-director-lock.json",
        "slides.json",
        "copy.json",
        "format-contract.json",
        "copy-verification.json",
    ),
    "images": (
        "identity-consistency-review.json",
        "final-images.json",
        "visual-qa.json",
    ),
    "publish": (
        "final-images.json",
        "visual-qa.json",
        "final-audit.json",
    ),
}

COPY_CHECKS = (
    "exact_text",
    "hook_and_retention",
    "copy_scene_alignment",
    "voice_and_public_name_boundary",
    "ending_and_send_reason",
)


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {}
    return value if isinstance(value, dict) else {}


def _write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def stage_artifact_paths(package_dir: Path, stage: Stage) -> list[Path]:
    paths = [package_dir / name for name in STAGE_ARTIFACTS[stage]]
    if stage in {"images", "publish"}:
        for folder in ("final", "final-reels-stories", "final-square"):
            paths.extend(sorted((package_dir / folder).glob("slide-*.png")))
    return paths


def stage_fingerprint(package_dir: Path, stage: Stage) -> str:
    records = []
    for path in stage_artifact_paths(package_dir, stage):
        relative = str(path.relative_to(package_dir))
        records.append(
            {
                "path": relative,
                "exists": path.is_file(),
                "sha256": _sha256(path) if path.is_file() else "MISSING",
            }
        )
    raw = json.dumps(records, sort_keys=True, ensure_ascii=False).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def _approval_ledger(package_dir: Path) -> dict[str, Any]:
    path = package_dir / HIL_DIR / APPROVALS_FILE
    value = _read_json(path)
    if not value:
        return {"schema_version": "1.0", "stages": {}, "decisions": []}
    value.setdefault("schema_version", "1.0")
    value.setdefault("stages", {})
    value.setdefault("decisions", [])
    return value


def approval_valid(package_dir: Path, stage: Stage) -> bool:
    ledger = _approval_ledger(package_dir)
    record = ledger.get("stages", {}).get(stage)
    return bool(
        isinstance(record, dict)
        and record.get("decision") == "APPROVE"
        and record.get("source") == "explicit_creator_input"
        and record.get("artifact_fingerprint") == stage_fingerprint(package_dir, stage)
    )


def next_unapproved_stage(package_dir: Path) -> Stage | None:
    for stage in STAGES:
        if not approval_valid(package_dir, stage):
            return stage
    return None


def _issue(code: str, message: str, *, evidence: list[str] | None = None, next_action: str = "") -> WorkflowIssue:
    return WorkflowIssue(
        code=code,
        severity="blocker",
        message=message,
        evidence=evidence or [],
        next_action=next_action,
    )


def _status(value: Any) -> str:
    return str(value or "").strip().lower()


def _require_prior_approval(package_dir: Path, stage: Stage) -> list[WorkflowIssue]:
    index = STAGES.index(stage)
    if index == 0:
        return []
    prior = STAGES[index - 1]
    if approval_valid(package_dir, prior):
        return []
    return [
        _issue(
            f"creator_{prior}_approval_required",
            f"The {stage} loop cannot start until the creator approves the current {prior} artifacts.",
            evidence=[str(package_dir / HIL_DIR / APPROVALS_FILE)],
            next_action=f"present_clean_{prior}_candidate_to_creator",
        )
    ]


def _required_file_issues(package_dir: Path, stage: Stage) -> list[WorkflowIssue]:
    issues: list[WorkflowIssue] = []
    for name in STAGE_ARTIFACTS[stage]:
        path = package_dir / name
        if not path.is_file():
            issues.append(
                _issue(
                    f"{stage}_artifact_missing",
                    f"{name} is required before the {stage} checkpoint can be shown to the creator.",
                    evidence=[str(path)],
                    next_action=f"maker_create_or_repair_{stage}_artifacts",
                )
            )
    return issues


def _concept_issues(package_dir: Path) -> list[WorkflowIssue]:
    issues = _required_file_issues(package_dir, "concept")
    selection = _read_json(package_dir / "concept-selection.json")
    verification = _read_json(package_dir / "verification.json")
    if selection and _status(selection.get("status")) not in {"ready_for_concept_lock", "go", "pass"}:
        issues.append(_issue("concept_not_verified", "Concept selection is not ready for creator lock."))
    if selection and _status(selection.get("creator_approval")) not in {"pending", ""}:
        issues.append(
            _issue(
                "concept_embeds_creator_approval",
                "Concept artifacts may not self-assert creator approval; approval belongs in the HIL ledger.",
            )
        )
    if verification:
        reviews = verification.get("reviews")
        selector = verification.get("selector")
        if not isinstance(reviews, list) or len(reviews) < 2:
            issues.append(_issue("concept_independent_reviews_missing", "Concept requires two independent verifier reviews."))
        task_ids = {
            str(review.get("critic_task_id") or review.get("reviewer_task_id") or "")
            for review in reviews or []
            if isinstance(review, dict)
        }
        if "" in task_ids or len(task_ids) < 2:
            issues.append(_issue("concept_review_independence_failed", "Concept verifier task IDs must be present and distinct."))
        if not isinstance(selector, dict) or _status(selector.get("verdict")) != "pass":
            issues.append(_issue("concept_selector_not_passed", "Fresh concept selector must return PASS."))
    return issues


def _copy_issues(package_dir: Path) -> list[WorkflowIssue]:
    issues = _require_prior_approval(package_dir, "copy") + _required_file_issues(package_dir, "copy")
    slides_path = package_dir / "slides.json"
    if slides_path.exists():
        try:
            payload = json.loads(slides_path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            payload = []
        slides = payload if isinstance(payload, list) else payload.get("slides", []) if isinstance(payload, dict) else []
        if not slides or any(not str(item.get("copy") or item.get("text") or "").strip() for item in slides if isinstance(item, dict)):
            issues.append(_issue("copy_slides_incomplete", "Every slide must contain locked non-empty copy."))
    review = _read_json(package_dir / "copy-verification.json")
    if review:
        if _status(review.get("status")) != "pass":
            issues.append(_issue("copy_verifier_not_passed", "Copy verifier must return PASS."))
        maker_id = str(review.get("maker_run_id") or "").strip()
        verifier_id = str(review.get("verifier_run_id") or "").strip()
        if not maker_id or not verifier_id or maker_id == verifier_id:
            issues.append(_issue("copy_review_independence_failed", "Copy maker and verifier run IDs must be present and distinct."))
        checks = review.get("checks") if isinstance(review.get("checks"), dict) else {}
        for check in COPY_CHECKS:
            item = checks.get(check)
            if not isinstance(item, dict) or item.get("pass") is not True or len(str(item.get("evidence") or "")) < 20:
                issues.append(_issue(f"copy_check_{check}_failed", f"Copy verification requires concrete PASS evidence for {check}."))
    return issues


def _images_issues(package_dir: Path) -> list[WorkflowIssue]:
    issues = _require_prior_approval(package_dir, "images") + _required_file_issues(package_dir, "images")
    assets = validate_publishable_final_assets(package_dir)
    for item in assets.issues:
        issues.append(_issue(item.code, item.reason, evidence=[str(package_dir / item.path)]))
    identity = _read_json(package_dir / "identity-consistency-review.json")
    if identity and _status(identity.get("status") or identity.get("verdict")) != "pass":
        issues.append(_issue("image_identity_not_passed", "Image checkpoint requires passing structured identity review."))
    qa = _read_json(package_dir / "visual-qa.json")
    if qa:
        if _status(qa.get("status") or qa.get("verdict")) != "pass":
            issues.append(_issue("image_visual_qa_not_passed", "Every final image must pass structured visual QA."))
        try:
            schema = tuple(int(part) for part in str(qa.get("schema_version") or "0.0").split(".")[:2])
        except ValueError:
            schema = (0, 0)
        if schema < (2, 1):
            issues.append(_issue("image_visual_qa_schema_stale", "Image checkpoint requires visual-qa schema 2.1 or newer."))
    return issues


def _publish_issues(package_dir: Path) -> list[WorkflowIssue]:
    issues = _require_prior_approval(package_dir, "publish") + _required_file_issues(package_dir, "publish")
    audit = _read_json(package_dir / "final-audit.json")
    if audit and audit.get("pass") is not True and _status(audit.get("status")) not in {"pass", "pass_with_notes"}:
        issues.append(_issue("final_audit_not_passed", "Publish checkpoint requires a passing final audit."))
    report = inspect_carousel_package(package_dir)
    issues.extend(issue for issue in report.issues if issue.severity in {"warning", "blocker"})
    state = derive_carousel_state(package_dir)
    if not state.publishable:
        issues.append(_issue("publish_state_not_ready", f"Derived state is {state.name}, not publishable."))
    return issues


def inspect_stage(package_dir: Path, stage: Stage) -> WorkflowDoctorReport:
    package_dir = package_dir.expanduser().resolve()
    if stage == "concept":
        issues = _concept_issues(package_dir)
    elif stage == "copy":
        issues = _copy_issues(package_dir)
    elif stage == "images":
        issues = _images_issues(package_dir)
    else:
        issues = _publish_issues(package_dir)
    unique: dict[tuple[str, str], WorkflowIssue] = {}
    for issue in issues:
        unique[(issue.code, issue.message)] = issue
    return WorkflowDoctorReport(str(package_dir), list(unique.values()))


def derive_stage_state(package_dir: Path, stage: Stage) -> CarouselState:
    report = inspect_stage(package_dir, stage)
    ready = not report.issues
    return CarouselState(
        name=f"{stage}_ready_for_creator" if ready else f"{stage}_repair",
        publishable=ready,
        blocked=not ready,
        next_action=(f"present_{stage}_candidate_to_creator" if ready else f"repair_{stage}_issues"),
        issue_codes=[issue.code for issue in report.issues],
        package_dir=str(package_dir),
    )


@dataclass(frozen=True)
class CreatorDecisionResult:
    status: str
    stage: Stage
    decision: Decision
    artifact_fingerprint: str
    invalidated_stages: list[Stage]
    next_stage: Stage | None

    def to_dict(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "stage": self.stage,
            "decision": self.decision,
            "artifact_fingerprint": self.artifact_fingerprint,
            "invalidated_stages": self.invalidated_stages,
            "next_stage": self.next_stage,
        }


def write_stage_candidate(package_dir: Path, stage: Stage) -> Path:
    report = inspect_stage(package_dir, stage)
    if report.issues:
        raise ValueError(f"Cannot present {stage}; verifier still reports issues.")
    path = package_dir / HIL_DIR / f"{stage}-candidate.json"
    _write_json(
        path,
        {
            "schema_version": "1.0",
            "stage": stage,
            "status": "AWAITING_CREATOR_APPROVAL",
            "artifact_fingerprint": stage_fingerprint(package_dir, stage),
            "artifacts": [str(path.relative_to(package_dir)) for path in stage_artifact_paths(package_dir, stage)],
            "verified_at": _now(),
            "allowed_decisions": ["APPROVE", "REVISE", "REJECT"],
        },
    )
    return path


def record_creator_decision(
    package_dir: Path,
    stage: Stage,
    decision: Decision,
    *,
    decided_by: str,
    feedback: str = "",
) -> CreatorDecisionResult:
    package_dir = package_dir.expanduser().resolve()
    candidate = _read_json(package_dir / HIL_DIR / f"{stage}-candidate.json")
    fingerprint = stage_fingerprint(package_dir, stage)
    if not candidate or candidate.get("status") != "AWAITING_CREATOR_APPROVAL":
        raise ValueError(f"No verified {stage} candidate is awaiting creator approval.")
    if candidate.get("artifact_fingerprint") != fingerprint:
        raise ValueError(f"The {stage} candidate changed after verification; rerun its loop before deciding.")
    report = inspect_stage(package_dir, stage)
    if report.issues:
        codes = ", ".join(sorted({issue.code for issue in report.issues}))
        raise ValueError(f"The {stage} verifier is no longer clean ({codes}); rerun its loop before deciding.")
    if not decided_by.strip():
        raise ValueError("decided_by is required")

    ledger = _approval_ledger(package_dir)
    stage_map = ledger["stages"]
    index = STAGES.index(stage)
    invalidated = list(STAGES[index + 1 :])
    for downstream in invalidated:
        stage_map.pop(downstream, None)
    if decision == "APPROVE":
        stage_map[stage] = {
            "decision": decision,
            "source": "explicit_creator_input",
            "artifact_fingerprint": fingerprint,
            "decided_by": decided_by.strip(),
            "decided_at": _now(),
            "feedback": feedback,
        }
        status = "APPROVED_TO_PUBLISH" if stage == "publish" else "APPROVED"
    else:
        stage_map.pop(stage, None)
        status = "REOPENED_FOR_REPAIR" if decision == "REVISE" else "REJECTED"
    ledger["decisions"].append(
        {
            "stage": stage,
            "decision": decision,
            "source": "explicit_creator_input",
            "artifact_fingerprint": fingerprint,
            "decided_by": decided_by.strip(),
            "decided_at": _now(),
            "feedback": feedback,
            "invalidated_stages": invalidated,
        }
    )
    _write_json(package_dir / HIL_DIR / APPROVALS_FILE, ledger)
    return CreatorDecisionResult(
        status=status,
        stage=stage,
        decision=decision,
        artifact_fingerprint=fingerprint,
        invalidated_stages=invalidated,
        next_stage=next_unapproved_stage(package_dir),
    )


def run_hil_stage_loop(
    package_dir: Path,
    stage: Stage,
    *,
    repo_root: Path,
    config: Any,
    repair_fn: Any = None,
) -> dict[str, Any]:
    """Run maker/verifier cycles for exactly one stage, then stop for HIL."""

    from pipeline.agentic.carousel_review_loop import TRACE_DIR, run_review_loop

    result = run_review_loop(
        package_dir,
        repo_root=repo_root,
        config=config,
        inspect_fn=lambda path: inspect_stage(path, stage),
        state_fn=lambda path: derive_stage_state(path, stage),
        repair_fn=repair_fn,
    )
    payload = result.to_dict()
    payload["stage"] = stage
    if result.complete:
        candidate_path = write_stage_candidate(package_dir, stage)
        payload.update(
            {
                "status": "AWAITING_CREATOR_APPROVAL",
                "complete": False,
                "candidate_path": str(candidate_path),
                "artifact_fingerprint": stage_fingerprint(package_dir, stage),
                "allowed_decisions": ["APPROVE", "REVISE", "REJECT"],
                "reason": f"The {stage} maker/verifier loop is clean and awaits creator decision.",
            }
        )
        _write_json(package_dir / TRACE_DIR / "summary.json", payload)
    return payload
