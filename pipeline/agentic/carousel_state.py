"""Read-only public state derivation for illustrated carousel packages."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from pipeline.agentic.checks.final_assets import validate_publishable_final_assets
from pipeline.agentic.workflow_doctor import inspect_carousel_package
from pipeline.stages.carousel_generation_state import PUBLIC_STATUSES, STATE_SCHEMA_VERSION


@dataclass(frozen=True)
class CarouselState:
    name: str
    publishable: bool
    blocked: bool
    next_action: str
    issue_codes: list[str] = field(default_factory=list)
    package_dir: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "publishable": self.publishable,
            "blocked": self.blocked,
            "next_action": self.next_action,
            "issue_codes": self.issue_codes,
            "package_dir": self.package_dir,
        }


def _read_json(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (FileNotFoundError, OSError, json.JSONDecodeError):
        return {}
    return payload if isinstance(payload, dict) else {}


def _status(value: Any) -> str:
    if isinstance(value, dict):
        value = value.get("status") or value.get("state") or value.get("proof_state")
    return str(value or "").strip().lower()


def _legacy_state(package_dir: Path) -> tuple[str, str]:
    legacy = _read_json(package_dir / "image-generation.json") or _read_json(
        package_dir / "generation-state.json"
    )
    status = _status(legacy)
    mapping = {
        "generated_quarantined": ("proof_qa_required", "review_proof_pixels"),
        "proof_ready_for_review": ("proof_qa_required", "review_proof_pixels"),
        "qa_pass_candidate": ("awaiting_creator_proof_approval", "approve_proof"),
        "creator_approved_proof": ("batch_ready", "prepare_remaining_slides"),
        "batch_allowed": ("batch_ready", "prepare_remaining_slides"),
        "generated_audit_failed": ("final_qa_failed", "repair_final_audit"),
        "generated": ("final_qa_required", "run_final_pixel_qa"),
        "packaged": ("final_qa_required", "run_final_pixel_qa"),
        "publishable": ("publish_ready", "publish"),
    }
    if status in PUBLIC_STATUSES:
        return status, str(legacy.get("next_action") or "inspect_archived_package")
    return mapping.get(status, ("draft", "inspect_archived_package"))


def derive_carousel_state(package_dir: Path) -> CarouselState:
    package_dir = Path(package_dir).expanduser()
    state = _read_json(package_dir / "generation-state.json")
    if state.get("schema_version") == STATE_SCHEMA_VERSION:
        name = _status(state)
        next_action = str(state.get("next_action") or "repair_state")
    else:
        name, next_action = _legacy_state(package_dir)

    report = inspect_carousel_package(package_dir)
    issue_codes = list(dict.fromkeys(issue.code for issue in report.issues))
    blocked = name in {"blocked", "proof_failed", "final_qa_failed"} or report.blocked
    publishable = name == "publish_ready" and not report.blocked
    if publishable:
        assets = validate_publishable_final_assets(package_dir)
        if not assets.ok:
            publishable = False
            blocked = True
            name = "final_qa_failed"
            next_action = "repair_final_image_assets"
            issue_codes.extend(issue.code for issue in assets.issues)
    elif name == "publish_ready" and report.blocked:
        name = "final_qa_failed"
        next_action = report.issues[0].next_action or "repair_publish_evidence"
    return CarouselState(
        name=name,
        publishable=publishable,
        blocked=blocked,
        next_action=next_action,
        issue_codes=list(dict.fromkeys(issue_codes)),
        package_dir=str(package_dir),
    )


__all__ = ["CarouselState", "derive_carousel_state"]
