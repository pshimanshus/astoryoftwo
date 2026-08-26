"""Read-only public state derivation for illustrated carousel packages."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from pipeline.agentic.checks.final_assets import validate_publishable_final_assets
from pipeline.agentic.workflow_doctor import inspect_carousel_package
from pipeline.stages.carousel_generation_state import (
    STATE_SCHEMA_VERSION,
    canonical_state_and_next_action,
)


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


def derive_carousel_state(package_dir: Path, *, report: Any | None = None) -> CarouselState:
    package_dir = Path(package_dir).expanduser()
    state = _read_json(package_dir / "generation-state.json") or _read_json(
        package_dir / "image-generation.json"
    )
    is_v3 = state.get("schema_version") == STATE_SCHEMA_VERSION
    name, next_action = canonical_state_and_next_action(state)

    report = report or inspect_carousel_package(package_dir)
    issue_codes = list(dict.fromkeys(issue.code for issue in report.issues))
    blocked = name in {"blocked", "proof_failed", "final_qa_failed"} or report.blocked
    publishable = name == "publish_ready" and not report.blocked
    if publishable and not is_v3:
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
