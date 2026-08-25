"""Small, read-only health check for the carousel hot path.

The doctor validates claims against the files and pixels that currently exist.
It deliberately does not require creative-room transcripts, Event A reviews,
agent provenance, task/run graphs, or fingerprint ledgers.  Those can still be
kept as optional working notes, but they cannot certify an image.
"""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable

from PIL import Image, UnidentifiedImageError

from pipeline.agentic.checks.final_assets import validate_publishable_final_assets
from pipeline.agentic.checks.prompt_constraints import check_prompt_constraints
from pipeline.stages.carousel_format_contract import (
    DEFAULT_NATIVE_FORMATS,
    FORMAT_CONTRACT_FILENAME,
    SUPPORTED_NATIVE_FORMATS,
    expected_output_path,
    format_spec,
    locked_formats,
)
from pipeline.stages.carousel_visual_storytelling import first_failed_pixel_gate
from pipeline.stages.carousel_generation_inputs import build_generation_inputs
from pipeline.stages.carousel_generation_state import STATE_SCHEMA_VERSION
from pipeline.stages.carousel_pixel_qa import validate_final_qa, validate_proof_qa


SEVERITY_RANK = {"ok": 0, "info": 1, "warning": 2, "blocker": 3}
SLIDE_NUMBER_RE = re.compile(r"slide[-_](\d+)", re.IGNORECASE)
CORRECTION_ARTIFACTS = ("creator-correction.json", "correction.json")
ACTIVE_GENERATION_ARTIFACTS = (
    "slides.json",
    "copy.json",
    "prompt-pack.json",
    "generation-state.json",
    "image-generation.json",  # legacy read compatibility
    "final-images.json",
)
HANDOFF_STATES = {
    "handoff_ready",
    "ready_for_codex_builtin_generation",
    "handoff_ready_for_codex_builtin_image_generation",
}
PROOF_CANDIDATE_STATES = {
    "generated_quarantined",
    "proof_ready_for_review",
    "qa_pass_candidate",
    "creator_approved_proof",
}
PROOF_FAILURE_STATES = {
    "proof_failed",
    "rejected_spatial_integrity",
    "blocked_visual_qa",
}
BATCH_STATES = {
    "batch_allowed",
    "batch_generation_ready",
    "continue_batch",
    "proof_accepted_continue_batch",
    "proof_passed",
    "remaining_slides_ready",
}
FINAL_STATES = {"generated", "packaged", "publish_ready", "publishable"}


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
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {}
    return payload if isinstance(payload, dict) else {}


def _read_text(path: Path) -> str:
    if not path.exists():
        return ""
    try:
        return path.read_text(encoding="utf-8")
    except OSError:
        return ""


def _issue(
    code: str,
    severity: str,
    message: str,
    *,
    evidence: Iterable[Path | str] = (),
    next_action: str = "",
) -> WorkflowIssue:
    return WorkflowIssue(
        code=code,
        severity=severity,
        message=message,
        evidence=[str(item) for item in evidence],
        next_action=next_action,
    )


def _status(payload: dict[str, Any] | Any) -> str:
    if isinstance(payload, dict):
        value = payload.get("proof_state") or payload.get("state") or payload.get("status")
    else:
        value = payload
    return str(value or "").strip().lower()


def _boolish(value: Any) -> bool | None:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        normalized = value.strip().lower()
        if normalized in {"pass", "passed", "true", "yes", "ok"}:
            return True
        if normalized in {"fail", "failed", "false", "no", "blocked"}:
            return False
    if isinstance(value, dict):
        if isinstance(value.get("pass"), bool):
            return value["pass"]
        return _boolish(value.get("status") or value.get("verdict"))
    return None


def _qa_passed(payload: dict[str, Any]) -> bool:
    return payload.get("pass") is True or _status(payload.get("status") or payload.get("verdict")) == "pass"


def _publishable_claim(payload: dict[str, Any]) -> bool:
    if payload.get("publishable") is False and payload.get("done") is not True:
        return False
    return bool(
        payload.get("publishable") is True
        or payload.get("done") is True
        or _status(payload.get("status")) in FINAL_STATES
    )


def _is_handoff(payload: dict[str, Any]) -> bool:
    return _status(payload.get("status")) in HANDOFF_STATES


def _allows_batch(payload: dict[str, Any]) -> bool:
    return bool(
        _status(payload) in BATCH_STATES
        or payload.get("can_continue_batch") is True
        or payload.get("continue_batch") is True
        or payload.get("batch_generation_allowed") is True
    )


def _proof_failed(state: dict[str, Any], qa: dict[str, Any]) -> bool:
    status = _status(state)
    if status in PROOF_FAILURE_STATES:
        return True
    # A newly generated quarantined proof is reviewable; it becomes failed only
    # when the pixel review or recorded issue list says so.
    if status == "generated_quarantined":
        return bool(first_failed_pixel_gate(qa) or (_status(qa.get("status")) == "fail"))
    return False


def _slide_records(package_dir: Path) -> list[dict[str, Any]]:
    for filename in ("slides.json", "prompt-pack.json", "final-images.json"):
        payload = _read_json(package_dir / filename)
        records = payload.get("slides")
        if isinstance(records, list) and records:
            return [record for record in records if isinstance(record, dict)]
        if filename == "slides.json" and isinstance(payload, list):
            return [record for record in payload if isinstance(record, dict)]
    return []


def _slide_number(record: dict[str, Any], fallback: int) -> int:
    try:
        return int(record.get("slide") or record.get("slide_number") or fallback)
    except (TypeError, ValueError):
        return fallback


def _slide_text(record: dict[str, Any]) -> str:
    for key in ("text", "copy", "on_image_text", "slide_text"):
        value = record.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return ""


def _expected_copy(package_dir: Path) -> dict[int, str]:
    return {
        _slide_number(record, index): _slide_text(record)
        for index, record in enumerate(_slide_records(package_dir), start=1)
        if _slide_text(record)
    }


def _active_paths(package_dir: Path, correction: dict[str, Any]) -> list[Path]:
    declared = correction.get("active_artifact_paths")
    if isinstance(declared, list) and declared:
        candidates = [package_dir / str(item) for item in declared]
    else:
        candidates = [package_dir / name for name in ACTIVE_GENERATION_ARTIFACTS]
        prompt_root = package_dir / "codex-image-prompts"
        if prompt_root.exists():
            candidates.extend(prompt_root.rglob("*.txt"))
    return [path for path in candidates if path.exists() and path.is_file()]


def _stale_generation_matches(package_dir: Path) -> list[str]:
    correction: dict[str, Any] = {}
    for filename in CORRECTION_ARTIFACTS:
        correction = _read_json(package_dir / filename)
        if correction:
            break
    if not correction:
        return []
    phrases: list[str] = []
    for key in ("rejected_route_phrases", "stale_phrases", "old_route_phrases", "old_phrases"):
        raw = correction.get(key)
        if isinstance(raw, str):
            phrases.append(raw)
        elif isinstance(raw, list):
            phrases.extend(str(item) for item in raw)
    phrases = [phrase.strip().lower() for phrase in phrases if phrase.strip()]
    matches: list[str] = []
    for path in _active_paths(package_dir, correction):
        text = _read_text(path).lower()
        matches.extend(f"{path.name}: {phrase}" for phrase in phrases if phrase in text)
    return list(dict.fromkeys(matches))


def _identity_reference_issues(
    package_dir: Path,
    prompt_pack: dict[str, Any],
    *,
    strict_v3: bool = False,
) -> list[str]:
    if strict_v3:
        from pipeline.stages.codex_builtin_image_generation import (
            identity_consistency_gate_reason,
        )

        reason = identity_consistency_gate_reason(package_dir)
        return [reason] if reason else []
    refs = [
        *(prompt_pack.get("identity_reference_images") or []),
        *(prompt_pack.get("identity_dossier_reference_images") or []),
    ]
    if not refs:
        return ["prompt-pack.json must attach selected Aachu/Zuv identity reference images."]
    issues: list[str] = []
    for raw in refs:
        path = Path(str(raw)).expanduser()
        if not path.is_absolute():
            path = package_dir / path
        if not path.is_file():
            issues.append(f"Identity reference does not exist: {path}")
    return issues


def _qa_native_outputs(qa: dict[str, Any]) -> list[tuple[int, str, dict[str, Any]]]:
    outputs: list[tuple[int, str, dict[str, Any]]] = []
    records = qa.get("slides")
    if not isinstance(records, list):
        return outputs
    for index, record in enumerate(records, start=1):
        if not isinstance(record, dict):
            continue
        slide = _slide_number(record, index)
        native = record.get("native_outputs")
        if isinstance(native, dict):
            outputs.extend(
                (slide, str(output_format), binding)
                for output_format, binding in native.items()
                if isinstance(binding, dict)
            )
            continue
        binding = record.get("source_asset") or record.get("asset")
        if isinstance(binding, dict):
            outputs.append((slide, str(record.get("format") or "instagram_post"), binding))
    return outputs


def _qa_asset_hash_issues(package_dir: Path, qa: dict[str, Any]) -> list[str]:
    """Bind every QA claim to the exact current image bytes."""

    issues: list[str] = []
    for slide, output_format, binding in _qa_native_outputs(qa):
        raw_path = str(binding.get("path") or binding.get("relative_path") or "").strip()
        expected_hash = str(binding.get("sha256") or binding.get("hash") or "").lower()
        if expected_hash.startswith("sha256:"):
            expected_hash = expected_hash.removeprefix("sha256:")
        if not raw_path or not expected_hash:
            issues.append(f"slide {slide} {output_format}: QA path or SHA-256 is missing")
            continue
        path = Path(raw_path).expanduser()
        if not path.is_absolute():
            path = package_dir / path
        try:
            resolved = path.resolve(strict=True)
            root = package_dir.resolve(strict=True)
            resolved.relative_to(root)
        except (FileNotFoundError, OSError, ValueError):
            issues.append(f"slide {slide} {output_format}: reviewed asset is missing or outside package: {path}")
            continue
        if path.is_symlink() or not path.is_file():
            issues.append(f"slide {slide} {output_format}: reviewed asset is not a regular package file: {path}")
            continue
        actual_hash = hashlib.sha256(path.read_bytes()).hexdigest()
        if actual_hash != expected_hash:
            issues.append(
                f"slide {slide} {output_format}: {path} records sha256:{expected_hash} but is sha256:{actual_hash}"
            )
        try:
            with Image.open(path) as image:
                actual_dimensions = tuple(image.size)
                image.verify()
        except (UnidentifiedImageError, OSError, SyntaxError, ValueError):
            issues.append(f"slide {slide} {output_format}: reviewed asset is not a decodable image")
            continue
        if output_format in {"instagram_post", "reels_stories", "square"}:
            expected_dimensions = tuple(format_spec(output_format)["target_size"])
            if actual_dimensions != expected_dimensions:
                issues.append(
                    f"slide {slide} {output_format}: dimensions are {actual_dimensions[0]}x{actual_dimensions[1]}, expected {expected_dimensions[0]}x{expected_dimensions[1]}"
                )
            recorded_dimensions = (binding.get("width"), binding.get("height"))
            if all(value is not None for value in recorded_dimensions) and recorded_dimensions != actual_dimensions:
                issues.append(
                    f"slide {slide} {output_format}: recorded dimensions are stale"
                )
    return issues


def _required_pixel_gate_issues(qa: dict[str, Any]) -> list[str]:
    """Require the five ordered pixel-review categories on a passing claim."""

    checks = qa.get("checks")
    checks = checks if isinstance(checks, dict) else {}
    readability = checks.get("visual_story_readability")
    readability = readability if isinstance(readability, dict) else {}

    aliases = {
        "semantic_action": (("semantic_action", "semantic_action_legible", "core_action_legible"),),
        "relationship_state": (("relationship_state", "relationship_state_legible", "relationship_turn_legible"),),
        "entity_anatomy_spatial": (("entity_anatomy_spatial", "entity_anatomy_spatial_integrity", "anatomy_spatial", "scene_entity_integrity"),),
        "identity": (("identity", "identity_consistency", "identity_match"),),
        "text_style_dimensions": (
            ("text_style_dimensions", "exact_text_style_dimensions_brandmark", "integrated_text_style_dimensions"),
            ("exact_text",),
            ("brandmark",),
            ("style",),
        ),
    }

    def one_component(names: tuple[str, ...]) -> bool | None:
        for container in (qa, checks, readability):
            for name in names:
                if name in container:
                    result = _boolish(container[name])
                    if result is not None:
                        return result
        records = qa.get("slides")
        values: list[bool] = []
        if isinstance(records, list):
            for record in records:
                if not isinstance(record, dict):
                    continue
                record_checks = record.get("checks")
                record_checks = record_checks if isinstance(record_checks, dict) else {}
                for record_container in (record, record_checks):
                    for name in names:
                        if name in record_container:
                            result = _boolish(record_container[name])
                            if result is not None:
                                values.append(result)
                                break
                    else:
                        continue
                    break
        return all(values) if values else None

    # Legacy structured QA is accepted only when it contains equivalent actual
    # review evidence.  This keeps existing packages readable during migration.
    reviews = qa.get("reviews") or qa.get("reviewers")
    reviews = reviews if isinstance(reviews, dict) else {}
    anatomy_review = reviews.get("anatomy_entity_spatial_identity")
    story_review = reviews.get("storytelling_richness_text_style")
    fallback = {
        "entity_anatomy_spatial": _boolish(anatomy_review),
        "identity": _boolish(anatomy_review),
        "text_style_dimensions": _boolish(story_review),
    }

    issues: list[str] = []
    for gate, components in aliases.items():
        results = [one_component(names) for names in components]
        # A combined compact gate satisfies all finish subcomponents. If it is
        # absent, the per-slide exact-text/brandmark/style checks must each pass.
        if gate == "text_style_dimensions" and results[0] is True:
            result = True
        else:
            present = [value for value in results if value is not None]
            result = all(present) if present and len(present) == len(results) else None
        if result is None and gate in fallback:
            result = fallback[gate]
        if result is not True:
            issues.append(f"{gate} pixel gate must explicitly pass")
    return issues


def _creator_approved(package_dir: Path, state: dict[str, Any], qa: dict[str, Any]) -> bool:
    if state.get("creator_approved") is True or state.get("creator_approval") is True:
        return True
    embedded = qa.get("creator_approval")
    approval = embedded if isinstance(embedded, dict) else _read_json(
        package_dir / "creator-proof-approval.json"
    )
    if not approval:
        return False
    approved = approval.get("approved") is True or _status(approval.get("status")) == "approved"
    qa_hash = str(qa.get("image_set_sha256") or "")
    approval_hash = str(approval.get("image_set_sha256") or "")
    return bool(approved and qa_hash and qa_hash == approval_hash)


def _v3_creator_approved(
    package_dir: Path,
    state: dict[str, Any],
    qa: dict[str, Any],
) -> bool:
    proof_slide = state.get("proof_slide")
    approval = qa.get("creator_approval") if isinstance(qa, dict) else None
    if proof_slide is None or not isinstance(approval, dict):
        return False
    slide = (state.get("slides") or {}).get(str(proof_slide), {})
    candidate = (
        package_dir
        / ".internal/approved-final-candidates"
        / f"slide-{int(proof_slide):02d}"
        / "candidate.json"
    )
    return bool(
        approval.get("approved") is True
        and _status(approval.get("status")) == "approved"
        and approval.get("proof_input_sha256") == slide.get("input_sha256")
        and candidate.is_file()
        and not candidate.is_symlink()
    )


def _inspect_v3_package(
    package_dir: Path,
    state: dict[str, Any],
    formats: tuple[str, ...],
) -> WorkflowDoctorReport:
    """Validate the compact v3 truth surface without legacy terminology."""

    issues: list[WorkflowIssue] = []
    status = _status(state)
    selected = [int(value) for value in state.get("selected_slides") or []]
    state_slides = state.get("slides") if isinstance(state.get("slides"), dict) else {}
    allowed_root = {
        "schema_version",
        "status",
        "next_action",
        "proof_slide",
        "selected_slides",
        "selected_formats",
        "format_sha256",
        "slides",
        "reason",
    }
    unexpected = sorted(set(state) - allowed_root)
    if unexpected:
        issues.append(
            _issue(
                "v3_state_not_compact",
                "blocker",
                "generation-state.json contains non-canonical transient fields.",
                evidence=unexpected,
                next_action="rewrite_compact_v3_state",
            )
        )
    if list(state.get("selected_formats") or []) != list(formats):
        issues.append(
            _issue(
                "format_contract_mismatch",
                "blocker",
                "generation-state.json selected formats do not match the current lock.",
                evidence=[package_dir / FORMAT_CONTRACT_FILENAME, package_dir / "generation-state.json"],
                next_action="reconcile_package_state",
            )
        )

    try:
        current = build_generation_inputs(package_dir)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        issues.append(
            _issue(
                "generation_inputs_invalid",
                "blocker",
                str(exc),
                evidence=[package_dir / "slides.json", package_dir / "prompt-pack.json"],
                next_action="repair_inputs",
            )
        )
        current = {"slides": {}, "format_sha256": ""}
    if state.get("format_sha256") != current.get("format_sha256"):
        issues.append(
            _issue(
                "stale_format_fingerprint",
                "blocker",
                "The generation state was compiled against a different format contract.",
                evidence=[package_dir / "generation-state.json"],
                next_action="reconcile_package_state",
            )
        )
    for number, fingerprints in current.get("slides", {}).items():
        recorded = state_slides.get(number, {})
        fingerprint_keys = (
            "source_sha256",
            "prompt_sha256",
            "references_sha256",
            "input_sha256",
        )
        mismatched = [
            key
            for key in fingerprint_keys
            if recorded.get(key) != fingerprints.get(key)
        ]
        if mismatched:
            issues.append(
                _issue(
                    "stale_slide_input_fingerprint",
                    "blocker",
                    f"Slide {number} state is stale against current semantic inputs: "
                    + ", ".join(mismatched),
                    evidence=[package_dir / "generation-state.json"],
                    next_action="reconcile_package_state",
                )
            )

    if status != "draft":
        identity = _identity_reference_issues(
            package_dir,
            _read_json(package_dir / "prompt-pack.json"),
            strict_v3=True,
        )
        if identity:
            issues.append(
                _issue(
                    "identity_references_missing",
                    "blocker",
                    "Actual Aachu/Zuv references are required before image generation.",
                    evidence=identity,
                    next_action="attach_selected_identity_references",
                )
            )

    if status == "handoff_ready":
        from pipeline.stages.codex_builtin_image_generation import (
            compiled_prompt_handoff_integrity_issues,
        )

        prompt_issues = compiled_prompt_handoff_integrity_issues(package_dir, state=state)
        if prompt_issues:
            issues.append(
                _issue(
                    "compiled_prompt_stale",
                    "blocker",
                    "; ".join(prompt_issues),
                    evidence=[package_dir / ".internal/compiled-prompts"],
                    next_action="recompile_prompt_handoff",
                )
            )

    proof_qa = _read_json(package_dir / "proof-qa.json")
    if status in {"awaiting_creator_proof_approval", "batch_ready"}:
        from pipeline.stages.codex_builtin_image_generation import (
            current_proof_qa_issues,
        )

        qa_issues = current_proof_qa_issues(
            package_dir,
            proof_qa,
            state=state,
        )
        if qa_issues:
            issues.append(
                _issue(
                    "proof_pixel_qa_incomplete",
                    "blocker",
                    "; ".join(qa_issues),
                    evidence=[package_dir / "proof-qa.json"],
                    next_action="review_proof_pixels",
                )
            )
        if status == "batch_ready" and not _v3_creator_approved(package_dir, state, proof_qa):
            issues.append(
                _issue(
                    "batch_without_approved_proof",
                    "blocker",
                    "Batch generation requires a hash-bound embedded creator approval.",
                    evidence=[package_dir / "proof-qa.json"],
                    next_action="approve_current_proof",
                )
            )

    public_manifest = _read_json(package_dir / "final-images.json")
    public_qa = _read_json(package_dir / "visual-qa.json")
    final_audit = _read_json(package_dir / "final-audit.json")
    final_png_exists = any(
        (package_dir / str(format_spec(value)["folder"])).is_dir()
        and any((package_dir / str(format_spec(value)["folder"])).glob("*.png"))
        for value in SUPPORTED_NATIVE_FORMATS
    )
    if status != "publish_ready" and (public_manifest or final_png_exists):
        issues.append(
            _issue(
                "premature_public_final",
                "blocker",
                "Public final evidence exists before complete-deck audit and promotion.",
                evidence=[package_dir / "final-images.json"],
                next_action="retract_public_finals",
            )
        )

    if status == "final_qa_required" and state.get("next_action") == "finalize_deck":
        hidden_root = package_dir / ".internal/final-audit-candidate"
        hidden_manifest = _read_json(package_dir / ".internal/final-manifest-candidate.json")
        qa_issues = validate_final_qa(hidden_root, public_qa, hidden_manifest)
        if qa_issues:
            issues.append(
                _issue(
                    "final_pixel_qa_incomplete",
                    "blocker",
                    "; ".join(qa_issues),
                    evidence=[package_dir / "visual-qa.json"],
                    next_action="review_final_pixels",
                )
            )

    if status == "publish_ready":
        from pipeline.stages.carousel_quality import build_final_audit

        audit = build_final_audit(package_dir, write=False)
        if audit.get("status") != "PASS":
            issues.append(
                _issue(
                    "publish_evidence_stale",
                    "blocker",
                    "; ".join(audit.get("issues") or ["final audit failed"]),
                    evidence=[
                        package_dir / "final-images.json",
                        package_dir / "visual-qa.json",
                        package_dir / "final-audit.json",
                    ],
                    next_action="repair_publish_evidence",
                )
            )
        if _status(final_audit) != "pass":
            issues.append(
                _issue(
                    "publishable_without_final_audit",
                    "blocker",
                    "publish_ready requires final-audit.json status PASS.",
                    evidence=[package_dir / "final-audit.json"],
                    next_action="run_final_audit",
                )
            )

    if status in {"blocked", "proof_failed", "final_qa_failed"}:
        issues.append(
            _issue(
                f"carousel_{status}",
                "blocker",
                str(state.get("reason") or f"Carousel state is {status}."),
                evidence=[package_dir / "generation-state.json"],
                next_action=str(state.get("next_action") or "repair_current_failure"),
            )
        )

    return WorkflowDoctorReport(package_dir=str(package_dir), issues=issues)


def inspect_carousel_package(package_dir: Path) -> WorkflowDoctorReport:
    package_dir = Path(package_dir).expanduser()
    if not package_dir.exists():
        return WorkflowDoctorReport(
            package_dir=str(package_dir),
            issues=[_issue("package_missing", "blocker", "Carousel package directory does not exist.", evidence=[package_dir])],
        )

    issues: list[WorkflowIssue] = []
    prompt_pack = _read_json(package_dir / "prompt-pack.json")
    generation_state = _read_json(package_dir / "generation-state.json")
    legacy_generation = _read_json(package_dir / "image-generation.json")
    state = generation_state or legacy_generation
    final_images = _read_json(package_dir / "final-images.json")
    proof_qa = _read_json(package_dir / "proof-qa.json")
    final_qa = _read_json(package_dir / "visual-qa.json")
    active_qa = proof_qa or final_qa
    final_audit = _read_json(package_dir / "final-audit.json")

    try:
        formats = tuple(locked_formats(package_dir))
    except (ValueError, json.JSONDecodeError, OSError) as exc:
        formats = tuple(DEFAULT_NATIVE_FORMATS)
        issues.append(
            _issue(
                "invalid_format_contract",
                "blocker",
                f"The current-request format contract is invalid: {exc}",
                evidence=[package_dir / FORMAT_CONTRACT_FILENAME],
                next_action="repair_and_relock_current_request_formats",
            )
        )

    if generation_state.get("schema_version") == STATE_SCHEMA_VERSION:
        report = _inspect_v3_package(package_dir, generation_state, formats)
        if issues:
            return WorkflowDoctorReport(
                package_dir=str(package_dir),
                issues=[*issues, *report.issues],
            )
        return report

    stale_matches = _stale_generation_matches(package_dir)
    if stale_matches:
        issues.append(
            _issue(
                "stale_artifact_carryover",
                "blocker",
                "Creator-rejected language remains in active generation artifacts.",
                evidence=stale_matches[:12],
                next_action="rebuild_generation_artifacts_from_current_copy",
            )
        )

    expected_copy = _expected_copy(package_dir)
    prompt_root = package_dir / "codex-image-prompts"
    for prompt_path in sorted(prompt_root.rglob("*.prompt.txt")) if prompt_root.exists() else []:
        match = SLIDE_NUMBER_RE.search(prompt_path.name)
        slide = int(match.group(1)) if match else 0
        result = check_prompt_constraints(prompt_path, expected_text=expected_copy.get(slide))
        if result.status != "PASS":
            issue_code = (
                "active_textless_prompt"
                if "forbidden textless/source-art directive" in result.reason
                else "active_prompt_constraints_failed"
            )
            issues.append(
                _issue(
                    issue_code,
                    "blocker",
                    f"Active prompt fails exact generation constraints: {result.reason}",
                    evidence=[prompt_path],
                    next_action="repair_active_prompt",
                )
            )

    status = _status(state)
    generated_or_handoff = bool(
        status in HANDOFF_STATES | PROOF_CANDIDATE_STATES | PROOF_FAILURE_STATES | BATCH_STATES
        or _publishable_claim(final_images)
    )
    if generated_or_handoff:
        if not (package_dir / FORMAT_CONTRACT_FILENAME).exists():
            issues.append(
                _issue(
                    "missing_format_contract",
                    "blocker",
                    "Generation requires a current-request format lock.",
                    evidence=[package_dir / FORMAT_CONTRACT_FILENAME],
                    next_action="lock_current_request_formats",
                )
            )
        for artifact_name, payload in (("generation-state.json", state), ("final-images.json", final_images)):
            requested = payload.get("requested_formats")
            if requested is not None and list(requested) != list(formats):
                issues.append(
                    _issue(
                        "format_contract_mismatch",
                        "blocker",
                        f"{artifact_name} does not match format-contract.json.",
                        evidence=[package_dir / FORMAT_CONTRACT_FILENAME, package_dir / artifact_name],
                        next_action="regenerate_from_current_format_lock",
                    )
                )

        identity_issues = _identity_reference_issues(package_dir, prompt_pack)
        if identity_issues:
            issues.append(
                _issue(
                    "identity_references_missing",
                    "blocker",
                    "Actual Aachu/Zuv reference images must be attached before generation.",
                    evidence=[package_dir / "prompt-pack.json", *identity_issues],
                    next_action="attach_selected_identity_references",
                )
            )

    if status == "blocked":
        issues.append(
            _issue(
                "image_generation_blocked",
                "blocker",
                str(state.get("reason") or "Image generation is blocked."),
                evidence=[package_dir / ("generation-state.json" if generation_state else "image-generation.json")],
                next_action="repair_blockers",
            )
        )

    failed_pixel_gate = first_failed_pixel_gate(active_qa)
    if _proof_failed(state, active_qa):
        gate = failed_pixel_gate[0] if failed_pixel_gate else "semantic_action"
        detail = failed_pixel_gate[1] if failed_pixel_gate else "Proof is recorded as failed."
        issues.append(
            _issue(
                f"proof_{gate}_failed",
                "blocker",
                detail,
                evidence=[
                    package_dir / ("proof-qa.json" if proof_qa else "visual-qa.json"),
                    package_dir / ("generation-state.json" if generation_state else "image-generation.json"),
                ],
                next_action="repair_visual_premise",
            )
        )

    if status in PROOF_CANDIDATE_STATES | BATCH_STATES or _allows_batch(state):
        if not active_qa:
            issues.append(
                _issue(
                    "proof_pixel_qa_missing",
                    "blocker" if _allows_batch(state) else "warning",
                    "The generated proof still needs an actual-pixel review.",
                    evidence=[package_dir / "proof-qa.json"],
                    next_action="review_proof_pixels",
                )
            )
        elif _qa_passed(active_qa):
            gate_issues = _required_pixel_gate_issues(active_qa)
            hash_issues = _qa_asset_hash_issues(package_dir, active_qa)
            if gate_issues or hash_issues:
                issues.append(
                    _issue(
                        "proof_pixel_qa_incomplete",
                        "blocker",
                        "Proof PASS is missing current-pixel evidence for the ordered QA gates.",
                        evidence=[package_dir / ("proof-qa.json" if proof_qa else "visual-qa.json"), *(gate_issues + hash_issues)[:12]],
                        next_action="repair_visual_premise",
                    )
                )
        elif not _proof_failed(state, active_qa):
            issues.append(
                _issue(
                    "proof_pixel_qa_not_passed",
                    "blocker" if _allows_batch(state) else "warning",
                    "Proof pixel QA has not passed.",
                    evidence=[package_dir / ("proof-qa.json" if proof_qa else "visual-qa.json")],
                    next_action="repair_visual_premise",
                )
            )

    if _allows_batch(state):
        if not _qa_passed(active_qa) or not _creator_approved(package_dir, state, active_qa):
            issues.append(
                _issue(
                    "batch_without_approved_proof",
                    "blocker",
                    "Remaining slides require an actual-pixel QA pass and creator approval of this proof.",
                    evidence=[package_dir / "proof-qa.json", package_dir / "creator-proof-approval.json"],
                    next_action="approve_current_proof_or_repair_it",
                )
            )

    if _publishable_claim(final_images):
        asset_report = validate_publishable_final_assets(package_dir)
        for asset_issue in asset_report.issues:
            issues.append(
                _issue(
                    asset_issue.code,
                    asset_issue.severity,
                    asset_issue.reason,
                    evidence=[package_dir / asset_issue.path],
                    next_action="repair_final_image_assets",
                )
            )
        final_outputs = _qa_native_outputs(final_images)
        final_binding_issues = _qa_asset_hash_issues(package_dir, final_images)
        if not final_outputs:
            final_binding_issues.append(
                "final-images.json must bind every final native output by path, SHA-256, width, and height"
            )
        if final_binding_issues:
            issues.append(
                _issue(
                    "final_image_binding_mismatch",
                    "blocker",
                    "final-images.json does not match the exact current final pixels.",
                    evidence=[package_dir / "final-images.json", *final_binding_issues[:12]],
                    next_action="repair_final_image_assets",
                )
            )
        if not final_qa or not _qa_passed(final_qa):
            issues.append(
                _issue(
                    "publishable_without_visual_qa",
                    "blocker",
                    "Publishable output requires passing actual-pixel visual-qa.json.",
                    evidence=[package_dir / "visual-qa.json"],
                    next_action="run_final_pixel_qa",
                )
            )
        else:
            gate_issues = _required_pixel_gate_issues(final_qa)
            hash_issues = _qa_asset_hash_issues(package_dir, final_qa)
            if gate_issues or hash_issues:
                issues.append(
                    _issue(
                        "final_pixel_qa_incomplete",
                        "blocker",
                        "Final QA must bind semantic, relationship, anatomy/spatial, identity, text/style/brandmark, and dimensions to current pixels.",
                        evidence=[package_dir / "visual-qa.json", *(gate_issues + hash_issues)[:12]],
                        next_action="repair_or_rerun_final_pixel_qa",
                    )
                )
        if not (final_audit.get("pass") is True and _status(final_audit.get("status")) == "pass"):
            issues.append(
                _issue(
                    "publishable_without_final_audit",
                    "blocker",
                    "Publishable output requires a passing final-audit.json.",
                    evidence=[package_dir / "final-audit.json"],
                    next_action="run_final_audit",
                )
            )

        records = _slide_records(package_dir)
        for index, record in enumerate(records, start=1):
            slide = _slide_number(record, index)
            for output_format in formats:
                path = expected_output_path(package_dir, output_format, slide)
                if not path.exists():
                    spec = format_spec(output_format)
                    width, height = spec["target_size"]
                    issues.append(
                        _issue(
                            f"missing_{output_format}_final",
                            "blocker",
                            f"Missing {width}x{height} final for slide {slide:02d}.",
                            evidence=[path],
                            next_action="package_all_locked_final_outputs",
                        )
                    )

    if not any(issue.severity == "blocker" for issue in issues) and _is_handoff(state):
        issues.append(
            _issue(
                "handoff_ready_not_publishable",
                "warning",
                "Copy and prompts are ready; generate the risky proof with attached references.",
                evidence=[package_dir / ("generation-state.json" if generation_state else "image-generation.json")],
                next_action="generate_risky_proof",
            )
        )

    return WorkflowDoctorReport(package_dir=str(package_dir), issues=issues)
