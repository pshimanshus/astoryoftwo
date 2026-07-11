"""Canonical derived state for illustrated carousel packages."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from pipeline.agentic.checks.final_assets import validate_publishable_final_assets
from pipeline.agentic.workflow_doctor import inspect_carousel_package


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
    if not path.exists():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {}
    return data if isinstance(data, dict) else {}


def _status(payload: dict[str, Any]) -> str:
    return str(payload.get("status") or "").strip().lower()


def _audit_passed(payload: dict[str, Any]) -> bool:
    return payload.get("pass") is True or _status(payload) in {"pass", "pass_with_notes"}


def _handoff_ready(payload: dict[str, Any]) -> bool:
    return _status(payload) in {
        "handoff_ready",
        "ready_for_codex_builtin_generation",
        "handoff_ready_for_codex_builtin_image_generation",
    }


def _has_final_slide_png(package_dir: Path) -> bool:
    return any(
        path.is_file()
        for name in ("final", "final-reels-stories")
        for path in (package_dir / name).glob("slide-*.png")
    )


def _has_generated_signal(final_images: dict[str, Any], package_dir: Path) -> bool:
    return (
        _status(final_images) in {"generated", "packaged", "generated_audit_failed"}
        or bool(final_images.get("done"))
        or _has_final_slide_png(package_dir)
    )


def _unique_issue_codes(codes: list[str]) -> list[str]:
    seen: set[str] = set()
    unique: list[str] = []

    for code in codes:
        if code and code not in seen:
            seen.add(code)
            unique.append(code)

    return unique


def derive_carousel_state(package_dir: Path) -> CarouselState:
    package_dir = package_dir.expanduser()

    report = inspect_carousel_package(package_dir)
    issue_codes = [issue.code for issue in report.issues]

    if report.blocked:
        return CarouselState(
            name="blocked",
            publishable=False,
            blocked=True,
            next_action=report.issues[0].next_action or "repair_blockers",
            issue_codes=_unique_issue_codes(issue_codes),
            package_dir=str(package_dir),
        )

    image_generation = _read_json(package_dir / "image-generation.json")
    final_images = _read_json(package_dir / "final-images.json")
    final_audit = _read_json(package_dir / "final-audit.json")

    if _status(image_generation) == "blocked" or _status(final_images) == "blocked":
        return CarouselState(
            name="blocked",
            publishable=False,
            blocked=True,
            next_action="repair_blockers",
            issue_codes=_unique_issue_codes(issue_codes),
            package_dir=str(package_dir),
        )

    if final_images.get("publishable") is True and _audit_passed(final_audit):
        asset_report = validate_publishable_final_assets(package_dir)

        if not asset_report.ok:
            asset_issue_codes = [issue.code for issue in asset_report.issues]

            return CarouselState(
                name="blocked",
                publishable=False,
                blocked=True,
                next_action="repair_final_image_assets",
                issue_codes=_unique_issue_codes(issue_codes + asset_issue_codes),
                package_dir=str(package_dir),
            )

        return CarouselState(
            name="publishable",
            publishable=True,
            blocked=False,
            next_action="ready_for_closeout",
            issue_codes=_unique_issue_codes(issue_codes),
            package_dir=str(package_dir),
        )

    if _has_generated_signal(final_images, package_dir):
        return CarouselState(
            name="partial_final",
            publishable=False,
            blocked=False,
            next_action="run_visual_qa_and_final_audit",
            issue_codes=_unique_issue_codes(issue_codes),
            package_dir=str(package_dir),
        )

    if (
        _handoff_ready(image_generation)
        or _handoff_ready(final_images)
        or (package_dir / "image-generation-blocker.md").exists()
    ):
        return CarouselState(
            name="handoff_ready",
            publishable=False,
            blocked=False,
            next_action="generate_with_identity_refs",
            issue_codes=_unique_issue_codes(issue_codes),
            package_dir=str(package_dir),
        )

    if _status(image_generation) == "proof_ready_for_review" or (
        package_dir / "non-final-proofs"
    ).exists():
        return CarouselState(
            name="proof_ready",
            publishable=False,
            blocked=False,
            next_action="review_or_repair_proof",
            issue_codes=_unique_issue_codes(issue_codes),
            package_dir=str(package_dir),
        )

    if (package_dir / "prompt-pack.json").exists() or (package_dir / "copy.json").exists():
        return CarouselState(
            name="copy_locked",
            publishable=False,
            blocked=False,
            next_action="prepare_image_handoff",
            issue_codes=_unique_issue_codes(issue_codes),
            package_dir=str(package_dir),
        )

    return CarouselState(
        name="draft",
        publishable=False,
        blocked=False,
        next_action="complete_c_layer_package",
        issue_codes=_unique_issue_codes(issue_codes),
        package_dir=str(package_dir),
    )
