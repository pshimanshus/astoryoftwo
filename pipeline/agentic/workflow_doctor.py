"""Read-only carousel package inspector.

The doctor catches contradictions between package artifacts before a session
trusts a PASS/GO/handoff label.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from pipeline.agentic.checks.prompt_constraints import check_prompt_constraints


SEVERITY_RANK = {"ok": 0, "info": 1, "warning": 2, "blocker": 3}
SLIDE_NUMBER_RE = re.compile(r"slide[-_](\d+)", re.IGNORECASE)


@dataclass(frozen=True)
class WorkflowIssue:
    code: str
    severity: str
    message: str
    evidence: list[str] = field(default_factory=list)
    next_action: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "code": self.code,
            "severity": self.severity,
            "message": self.message,
            "evidence": self.evidence,
            "next_action": self.next_action,
        }


@dataclass(frozen=True)
class WorkflowDoctorReport:
    package_dir: str
    issues: list[WorkflowIssue] = field(default_factory=list)

    @property
    def highest_severity(self) -> str:
        if not self.issues:
            return "ok"
        return max(self.issues, key=lambda issue: SEVERITY_RANK[issue.severity]).severity

    @property
    def blocked(self) -> bool:
        return self.highest_severity == "blocker"

    def to_dict(self) -> dict[str, Any]:
        return {
            "package_dir": self.package_dir,
            "highest_severity": self.highest_severity,
            "blocked": self.blocked,
            "issues": [issue.to_dict() for issue in self.issues],
        }


def _read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {}
    return data if isinstance(data, dict) else {}


def _read_text(path: Path) -> str:
    if not path.exists():
        return ""
    try:
        return path.read_text(encoding="utf-8")
    except OSError:
        return ""


def _artifact(package_dir: Path, name: str) -> str:
    return str(package_dir / name)


def _issue(
    code: str,
    severity: str,
    message: str,
    *,
    evidence: list[Path | str] | None = None,
    next_action: str = "",
) -> WorkflowIssue:
    return WorkflowIssue(
        code=code,
        severity=severity,
        message=message,
        evidence=[str(item) for item in evidence or []],
        next_action=next_action,
    )


def _status(value: Any) -> str:
    return str(value or "").strip().lower()


def _text_from_slide_record(record: dict[str, Any]) -> str:
    for key in ("text", "copy", "on_image_text", "slide_text"):
        value = record.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return ""


def _expected_copy_by_slide(package_dir: Path) -> dict[int, str]:
    expected: dict[int, str] = {}
    for filename in ("prompt-pack.json", "slides.json"):
        data = _read_json(package_dir / filename)
        records = data.get("slides")
        if not isinstance(records, list):
            continue
        for index, record in enumerate(records):
            if not isinstance(record, dict):
                continue
            try:
                number = int(record.get("slide") or record.get("slide_number") or index + 1)
            except (TypeError, ValueError):
                continue
            copy = _text_from_slide_record(record)
            if number > 0 and copy:
                expected[number] = copy
    return expected


def _prompt_slide_number(prompt_path: Path) -> int | None:
    match = SLIDE_NUMBER_RE.search(prompt_path.name)
    if not match:
        return None
    try:
        return int(match.group(1))
    except ValueError:
        return None


def _slide_numbers(package_dir: Path, final_images: dict[str, Any]) -> list[int]:
    records = final_images.get("slides")
    if isinstance(records, list) and records:
        numbers = [int(record.get("slide", 0) or 0) for record in records if isinstance(record, dict)]
        return sorted(number for number in numbers if number > 0)

    slide_count = int(final_images.get("slide_count") or 0)
    if slide_count > 0:
        return list(range(1, slide_count + 1))

    prompt_pack = _read_json(package_dir / "prompt-pack.json")
    prompts = prompt_pack.get("slides")
    if isinstance(prompts, list) and prompts:
        return sorted(int(item.get("slide", index + 1) or index + 1) for index, item in enumerate(prompts))

    final_files = sorted((package_dir / "final").glob("slide-*.png"))
    if final_files:
        numbers: list[int] = []
        for path in final_files:
            try:
                numbers.append(int(path.stem.split("-")[-1]))
            except ValueError:
                continue
        if numbers:
            return sorted(numbers)

    return []


def _has_publishable_final_claim(final_images: dict[str, Any]) -> bool:
    return (
        final_images.get("publishable") is True
        or final_images.get("done") is True
        or _status(final_images.get("status")) in {"packaged", "publish_ready", "publishable"}
    )


def _is_handoff_state(payload: dict[str, Any]) -> bool:
    return _status(payload.get("status")) in {
        "handoff_ready",
        "ready_for_codex_builtin_generation",
        "handoff_ready_for_codex_builtin_image_generation",
    }


def inspect_carousel_package(package_dir: Path) -> WorkflowDoctorReport:
    package_dir = package_dir.expanduser()
    issues: list[WorkflowIssue] = []

    if not package_dir.exists():
        return WorkflowDoctorReport(
            package_dir=str(package_dir),
            issues=[
                _issue(
                    "package_missing",
                    "blocker",
                    "Carousel package directory does not exist.",
                    evidence=[package_dir],
                )
            ],
        )

    manifest = _read_json(package_dir / "manifest.json")
    visual_plan_quality = _read_json(package_dir / "visual-plan-quality.json")
    image_generation = _read_json(package_dir / "image-generation.json")
    final_images = _read_json(package_dir / "final-images.json")
    final_audit = _read_json(package_dir / "final-audit.json")
    text_generated_candidates = _read_json(package_dir / "text-generated-candidates.json")
    raw_scene = _read_text(package_dir / "raw-scene-row.md").lower()
    blocker_text = _read_text(package_dir / "image-generation-blocker.md").lower()

    if _status(image_generation.get("status")) == "blocked" or _status(final_images.get("status")) == "blocked":
        issues.append(
            _issue(
                "image_generation_blocked",
                "blocker",
                image_generation.get("reason")
                or final_images.get("reason")
                or "Image generation manifest is blocked.",
                evidence=[package_dir / "image-generation.json", package_dir / "final-images.json"],
                next_action="repair_blockers",
            )
        )

    final_images_status = _status(final_images.get("status"))
    final_status = _status(final_images.get("final_status"))
    if final_images_status == "not_final" or "not_final" in final_images_status or "blocked" in final_status:
        issues.append(
            _issue(
                "semantic_generation_blocked",
                "blocker",
                "Final image metadata says the package is not final or remains blocked.",
                evidence=[package_dir / "final-images.json"],
                next_action="retry_text_bearing_generation_or_keep_blocked",
            )
        )

    publish_gate = text_generated_candidates.get("publish_gate")
    if isinstance(publish_gate, dict) and _status(publish_gate.get("status")) == "blocked":
        issues.append(
            _issue(
                "publish_gate_blocked",
                "blocker",
                "Text-generated candidates publish gate is BLOCKED.",
                evidence=[package_dir / "text-generated-candidates.json"],
                next_action="repair_candidate_blockers_before_generation",
            )
        )

    textless_sources = text_generated_candidates.get("textless_sources")
    if isinstance(textless_sources, dict) and _status(textless_sources.get("status")) == "rejected_hard_fail":
        issues.append(
            _issue(
                "textless_sources_rejected",
                "blocker",
                "Textless source images were rejected as a hard fail.",
                evidence=[package_dir / "text-generated-candidates.json"],
                next_action="discard_textless_sources_and_retry_text_bearing_generation",
            )
        )

    expected_copy = _expected_copy_by_slide(package_dir)
    prompt_root = package_dir / "codex-image-prompts"
    for prompt_path in sorted(prompt_root.rglob("*.prompt.txt")) if prompt_root.exists() else []:
        slide_number = _prompt_slide_number(prompt_path)
        expected_text = expected_copy.get(slide_number or 0)
        gate = check_prompt_constraints(prompt_path, expected_text=expected_text)
        if gate.status == "PASS":
            continue
        is_textless = "forbidden textless/source-art directive" in gate.reason
        issues.append(
            _issue(
                "active_textless_prompt" if is_textless else "active_prompt_constraints_failed",
                "blocker",
                f"Active prompt file fails prompt constraints: {gate.reason}",
                evidence=[prompt_path],
                next_action="repair_or_quarantine_active_prompt_before_generation",
            )
        )

    if "status: rejected" in raw_scene and visual_plan_quality.get("can_generate") is True:
        issues.append(
            _issue(
                "raw_scene_rejected_but_generation_allowed",
                "blocker",
                "raw-scene-row.md rejects generation, but visual-plan-quality.json still allows it.",
                evidence=[package_dir / "raw-scene-row.md", package_dir / "visual-plan-quality.json"],
                next_action="repair_storyboard_before_generation",
            )
        )

    if "no final pngs" in blocker_text and _has_publishable_final_claim(final_images):
        issues.append(
            _issue(
                "stale_blocker_with_generated_finals",
                "blocker",
                "image-generation-blocker.md says no final PNGs exist while final-images.json claims generated/publishable output.",
                evidence=[package_dir / "image-generation-blocker.md", package_dir / "final-images.json"],
                next_action="remove_or_supersede_stale_blocker_after_verifying_native_finals",
            )
        )

    manifest_status = _status(manifest.get("status"))
    if manifest_status == "fresh_generation_in_progress":
        required = {
            "missing_prompt_pack": "prompt-pack.json",
            "missing_visual_debate": "visual-debate.json",
            "missing_post_copy_visual_room": "post-copy-visual-room.json",
            "missing_final_audit": "final-audit.json",
        }
        for code, filename in required.items():
            path = package_dir / filename
            if not path.exists():
                issues.append(
                    _issue(
                        code,
                        "blocker",
                        f"{filename} is required before a fresh-generation package can be trusted.",
                        evidence=[path],
                        next_action="complete_required_c_layer_artifacts",
                    )
                )

    if (package_dir / "final").exists() and not (package_dir / "final-reels-stories").exists():
        issues.append(
            _issue(
                "missing_reels_stories_final_folder",
                "blocker",
                "3:4 final images exist without the required separate native 9:16 final-reels-stories folder.",
                evidence=[package_dir / "final", package_dir / "final-reels-stories"],
                next_action="generate_separate_native_reels_stories_outputs",
            )
        )

    if _has_publishable_final_claim(final_images):
        if not (package_dir / "visual-qa.md").exists() and not (package_dir / "visual-qa.json").exists():
            issues.append(
                _issue(
                    "publishable_without_visual_qa",
                    "blocker",
                    "final-images.json claims publishable/generated output without visual QA evidence.",
                    evidence=[package_dir / "final-images.json", package_dir / "visual-qa.md", package_dir / "visual-qa.json"],
                    next_action="run_visual_qa_before_marking_publishable",
                )
            )
        if final_audit.get("pass") is not True and _status(final_audit.get("status")) not in {"pass", "pass_with_notes"}:
            issues.append(
                _issue(
                    "publishable_without_final_audit",
                    "blocker",
                    "final-images.json claims publishable/generated output without a passing final audit.",
                    evidence=[package_dir / "final-images.json", package_dir / "final-audit.json"],
                    next_action="run_final_audit_before_marking_publishable",
                )
            )

        slide_numbers = _slide_numbers(package_dir, final_images)
        for number in slide_numbers:
            final_path = package_dir / "final" / f"slide-{number:02d}.png"
            reels_path = package_dir / "final-reels-stories" / f"slide-{number:02d}.png"
            if not final_path.exists():
                issues.append(
                    _issue(
                        "missing_instagram_post_final",
                        "blocker",
                        f"Missing native 3:4 final image for slide {number:02d}.",
                        evidence=[final_path],
                        next_action="package_all_native_final_outputs",
                    )
                )
            if not reels_path.exists():
                issues.append(
                    _issue(
                        "missing_reels_stories_final",
                        "blocker",
                        f"Missing native 9:16 Reels/Stories final image for slide {number:02d}.",
                        evidence=[reels_path],
                        next_action="package_all_native_final_outputs",
                    )
                )

    if not any(issue.severity == "blocker" for issue in issues):
        handoff = _is_handoff_state(image_generation) or _is_handoff_state(final_images)
        if handoff and final_images.get("publishable") is not True:
            issues.append(
                _issue(
                    "handoff_ready_not_publishable",
                    "warning",
                    "Prompt handoff exists, but final native images are not publishable yet.",
                    evidence=[package_dir / "image-generation.json", package_dir / "final-images.json"],
                    next_action="generate_with_identity_refs",
                )
            )

    return WorkflowDoctorReport(package_dir=str(package_dir), issues=issues)
