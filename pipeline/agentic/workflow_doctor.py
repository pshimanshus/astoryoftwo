"""Read-only carousel package inspector.

The doctor catches contradictions between package artifacts before a session
trusts a PASS/GO/handoff label.
"""

from __future__ import annotations

import json
import hashlib
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from pipeline.agentic.checks.prompt_constraints import check_prompt_constraints
from pipeline.agentic.checks.final_assets import validate_publishable_final_assets
from pipeline.stages.carousel_format_contract import (
    FORMAT_CONTRACT_FILENAME,
    DEFAULT_NATIVE_FORMATS,
    expected_frame_bindings,
    expected_output_path,
    format_spec,
    locked_format_contract_fingerprint,
    locked_formats,
)
from pipeline.stages.codex_builtin_image_generation import (
    approved_proof_batch_handoff_attestation_issues,
    compiled_prompt_handoff_integrity_issues,
    creator_override_batch_handoff_integrity_issues,
    load_attempt_ledger,
    next_retry_count,
    retry_prompt_handoff_attestation_issues,
    sha256_binding,
    validate_exact_image_visual_qa,
    validate_quarantine_integrity,
)
from pipeline.stages.carousel_visual_storytelling import (
    VISUAL_STORY_READABILITY_KEY,
    current_creator_correction_fingerprint,
    current_generation_payload_fingerprint,
    director_author_id,
    director_creator_correction_fingerprint,
    director_event_fingerprint,
    director_generation_payload_fingerprint,
    director_review_provenance,
    director_reviewer_id,
    validate_director_storyboard,
    validate_frame_readability,
)


SEVERITY_RANK = {"ok": 0, "info": 1, "warning": 2, "blocker": 3}
SLIDE_NUMBER_RE = re.compile(r"slide[-_](\d+)", re.IGNORECASE)
CORRECTION_ARTIFACTS = ("creator-correction.json", "correction.json")
DEFAULT_ACTIVE_GENERATION_ARTIFACTS = (
    "slides.json",
    "copy.json",
    "post-copy-visual-room.json",
    "visual-debate.json",
    "visual-plan-quality.json",
    "prompt-pack.json",
    "review.json",
    "manifest.json",
    "image-generation.json",
    "final-images.json",
)
BATCH_CONTINUATION_STATUSES = {
    "batch_generation_ready",
    "continue_batch",
    "proof_accepted_continue_batch",
    "proof_passed",
    "remaining_slides_ready",
}
IDENTITY_BLOCK_STATUSES = {
    "blocked",
    "blocked_for_identity_eval",
    "identity_unverified",
}
PROOF_LIFECYCLE_STATES = {
    "generated_quarantined",
    "qa_pass_candidate",
    "creator_approved_proof",
    "batch_allowed",
    "rejected_spatial_integrity",
    "blocked_visual_qa",
}
GENERATED_PROOF_STATES = PROOF_LIFECYCLE_STATES | {
    "proof_ready_for_review",
    "proof_passed",
}


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


def _boolish_true(value: Any) -> bool:
    return value is True or (isinstance(value, str) and value.strip().lower() == "true")


def _list_text(value: Any) -> list[str]:
    if isinstance(value, str):
        return [value]
    if isinstance(value, list):
        return [str(item) for item in value if str(item).strip()]
    return []


def _dedupe(values: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        normalized = value.strip()
        key = normalized.lower()
        if not normalized or key in seen:
            continue
        seen.add(key)
        result.append(normalized)
    return result


def _declared_creator_correction(package_dir: Path) -> dict[str, Any]:
    for filename in CORRECTION_ARTIFACTS:
        data = _read_json(package_dir / filename)
        if data:
            return data
    return {}


def _stale_phrases(correction: dict[str, Any]) -> list[str]:
    phrases: list[str] = []
    for key in (
        "rejected_route_phrases",
        "stale_phrases",
        "old_route_phrases",
        "old_phrases",
    ):
        phrases.extend(_list_text(correction.get(key)))
    return _dedupe(phrases)


def _active_generation_paths(package_dir: Path, correction: dict[str, Any]) -> list[Path]:
    raw_paths = _list_text(correction.get("active_artifact_paths"))
    paths = [package_dir / raw_path for raw_path in raw_paths]
    if not paths:
        paths = [package_dir / filename for filename in DEFAULT_ACTIVE_GENERATION_ARTIFACTS]
        prompt_dir = package_dir / "codex-image-prompts"
        if prompt_dir.exists():
            paths.extend(sorted(path for path in prompt_dir.rglob("*.txt") if path.is_file()))
    return [path for path in paths if path.exists()]


def _stale_generation_matches(package_dir: Path, correction: dict[str, Any]) -> list[str]:
    phrases = [phrase.lower() for phrase in _stale_phrases(correction)]
    if not phrases:
        return []

    matches: list[str] = []
    for path in _active_generation_paths(package_dir, correction):
        text = _read_text(path).lower()
        if not text:
            continue
        for phrase in phrases:
            if phrase in text:
                matches.append(f"{path.name}: {phrase}")
    return _dedupe(matches)


def _allows_batch_continuation(payload: dict[str, Any]) -> bool:
    return any(
        _boolish_true(payload.get(key))
        for key in ("can_continue_batch", "continue_batch", "batch_generation_allowed")
    )


def _is_batch_continuation_state(payload: dict[str, Any]) -> bool:
    return _status(payload.get("status")) in BATCH_CONTINUATION_STATUSES or _allows_batch_continuation(payload)


def _identity_review_status(review: dict[str, Any]) -> str:
    return _status(review.get("status") or review.get("verdict"))


def _has_person_reference_ids(review: dict[str, Any]) -> bool:
    selected = review.get("selected_reference_ids")
    if isinstance(selected, dict):
        return bool(selected.get("aachu")) and bool(selected.get("zuv"))

    references = review.get("identity_references")
    if isinstance(references, list):
        joined = " ".join(str(item).lower() for item in references)
        return bool(references) and ("aachu" in joined or "zuv" in joined)
    return False


def _has_specific_likeness_notes(review: dict[str, Any]) -> bool:
    notes = review.get("likeness_notes")
    if not isinstance(notes, dict):
        return False

    def has_note(person: str) -> bool:
        note = str(notes.get(person) or "").strip()
        return len(note.split()) >= 8

    return has_note("aachu") and has_note("zuv")


def _identity_gate_requested(
    package_dir: Path,
    image_generation: dict[str, Any],
    final_images: dict[str, Any],
    review: dict[str, Any],
) -> bool:
    if _is_batch_continuation_state(image_generation) or _is_batch_continuation_state(final_images):
        return True
    if _identity_review_status(review) in IDENTITY_BLOCK_STATUSES:
        return True
    if (package_dir / "proof").exists() and _allows_batch_continuation(image_generation):
        return True
    return False


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

    try:
        fallback_formats = locked_formats(package_dir)
    except (ValueError, json.JSONDecodeError, OSError):
        fallback_formats = DEFAULT_NATIVE_FORMATS
    final_files = [
        path
        for output_format in fallback_formats
        for path in sorted(
            (package_dir / str(format_spec(output_format)["folder"])).glob("slide-*.png")
        )
    ]
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


def _proof_state(payload: dict[str, Any]) -> str:
    for key in ("proof_state", "lifecycle_state", "state", "status"):
        candidate = _status(payload.get(key))
        if candidate in GENERATED_PROOF_STATES:
            return candidate
    return ""


def _schema_version(value: Any) -> tuple[int, int] | None:
    try:
        parts = str(value).split(".")
        return int(parts[0]), int(parts[1])
    except (TypeError, ValueError, IndexError):
        return None


def _qa_slide_records(visual_qa: dict[str, Any]) -> list[dict[str, Any]]:
    records = visual_qa.get("slides")
    if isinstance(records, list):
        return [record for record in records if isinstance(record, dict)]
    checks = visual_qa.get("checks")
    anatomy = checks.get("anatomy_inventory") if isinstance(checks, dict) else None
    records = anatomy.get("slides") if isinstance(anatomy, dict) else None
    return [record for record in records or [] if isinstance(record, dict)]


def _structured_visual_qa_v2_issues(
    package_dir: Path,
    visual_qa: dict[str, Any],
    *,
    visual_plan: dict[str, Any] | None = None,
) -> list[str]:
    issues: list[str] = []
    version = _schema_version(visual_qa.get("schema_version"))
    if version is None or version < (2, 1):
        issues.append("schema_version must be at least 2.1")

    checks = visual_qa.get("checks")
    if not isinstance(checks, dict):
        issues.append("checks must be an object")
        checks = {}
    for check_name in (
        "anatomy_inventory",
        "scene_entity_integrity",
        "spatial_topology",
        "visual_richness",
    ):
        check = checks.get(check_name)
        if not isinstance(check, dict):
            issues.append(f"checks.{check_name} must be structured evidence, not a boolean")
            continue
        records = check.get("slides")
        if not isinstance(records, list) or not records:
            issues.append(f"checks.{check_name}.slides must contain per-slide evidence")

    if not _proof_state(visual_qa):
        issues.append("proof_state must name the fail-closed lifecycle state")

    reviewers = visual_qa.get("reviews") or visual_qa.get("reviewers")
    if not isinstance(reviewers, dict):
        issues.append("two independent reviewer records are required")
    else:
        reviewer_aliases = (
            ("anatomy_entity_spatial_identity", "anatomy_entity_spatial_identity_reviewer"),
            ("storytelling_richness_text_style", "storytelling_richness_text_style_reviewer"),
        )
        reviewer_ids: list[str] = []
        for aliases in reviewer_aliases:
            review = next((reviewers.get(key) for key in aliases if isinstance(reviewers.get(key), dict)), None)
            if not review:
                issues.append(f"missing reviewer evidence: {aliases[0]}")
                continue
            if not isinstance(review.get("pass"), bool):
                issues.append(f"reviewer {aliases[0]} must include an explicit boolean pass result")
            reviewer_id = str(review.get("reviewer_id") or "").strip()
            if not reviewer_id:
                issues.append(f"reviewer {aliases[0]} is missing reviewer_id")
            else:
                reviewer_ids.append(reviewer_id)
            if not review.get("evidence") and not review.get("notes"):
                issues.append(f"reviewer {aliases[0]} is missing evidence")
        if len(reviewer_ids) == 2 and reviewer_ids[0] == reviewer_ids[1]:
            issues.append("the two post-generation reviews must use distinct reviewer_id values")

    qa_slides = visual_qa.get("slides")
    exact_records: list[dict[str, Any]] = []
    if isinstance(qa_slides, list):
        for record in qa_slides:
            if not isinstance(record, dict):
                continue
            outputs = record.get("native_outputs")
            if isinstance(outputs, dict):
                resolved_outputs: dict[str, Any] = {}
                for output_format, output in outputs.items():
                    if not isinstance(output, dict):
                        resolved_outputs[output_format] = output
                        continue
                    resolved = dict(output)
                    # Keep the canonical package-relative quarantine binding intact.
                    # validate_quarantine_integrity resolves it against package_dir
                    # and deliberately rejects absolute or non-canonical aliases.
                    resolved_outputs[output_format] = resolved
                exact_records.append(
                    {"slide": record.get("slide"), "native_outputs": resolved_outputs}
                )
    if not exact_records:
        issues.append("slides must bind every native output to exact current pixels")
    else:
        output_formats = list(exact_records[0]["native_outputs"])
        issues.extend(
            validate_quarantine_integrity(
                exact_records,
                output_formats,
                carousel_dir=package_dir,
            )
        )
        issues.extend(
            validate_exact_image_visual_qa(
                visual_qa,
                exact_records,
                visual_plan=visual_plan,
                carousel_dir=package_dir,
                include_story_checks=False,
            )
        )
    return issues


def _asset_path_and_hash(record: dict[str, Any]) -> tuple[str, str]:
    asset = next(
        (
            record.get(key)
            for key in ("source_asset", "asset", "image_asset")
            if isinstance(record.get(key), dict)
        ),
        {},
    )
    raw_path = (
        asset.get("path")
        or asset.get("file")
        or record.get("source_image_path")
        or record.get("asset_path")
        or ""
    )
    raw_hash = (
        asset.get("sha256")
        or asset.get("hash")
        or record.get("source_image_sha256")
        or record.get("asset_sha256")
        or ""
    )
    return str(raw_path), str(raw_hash)


def _qa_asset_hash_issues(package_dir: Path, visual_qa: dict[str, Any]) -> list[str]:
    issues: list[str] = []
    qa_slides = visual_qa.get("slides")
    if isinstance(qa_slides, list):
        for record in qa_slides:
            if not isinstance(record, dict):
                continue
            outputs = record.get("native_outputs")
            if not isinstance(outputs, dict):
                continue
            for output_format, output in outputs.items():
                if not isinstance(output, dict):
                    issues.append(
                        f"slide {record.get('slide')}: {output_format} binding is not structured"
                    )
                    continue
                raw_path = str(output.get("path") or "").strip()
                recorded_hash = str(output.get("sha256") or "").strip()
                if not raw_path or not recorded_hash:
                    issues.append(
                        f"slide {record.get('slide')}: {output_format} path or SHA-256 is missing"
                    )
                    continue
                path = Path(raw_path).expanduser()
                if not path.is_absolute():
                    path = package_dir / path
                if not path.is_file():
                    issues.append(
                        f"slide {record.get('slide')}: reviewed {output_format} asset is missing: {path}"
                    )
                    continue
                actual_hash = hashlib.sha256(path.read_bytes()).hexdigest()
                if actual_hash != recorded_hash.lower().removeprefix("sha256:"):
                    issues.append(
                        f"slide {record.get('slide')}: {path} records {recorded_hash} but is sha256:{actual_hash}"
                    )
    for index, record in enumerate(_qa_slide_records(visual_qa), start=1):
        raw_path, recorded_hash = _asset_path_and_hash(record)
        if not raw_path or not recorded_hash:
            continue
        path = Path(raw_path).expanduser()
        if not path.is_absolute():
            path = package_dir / path
        if not path.is_file():
            issues.append(
                f"slide {record.get('slide') or index}: reviewed source asset is missing: {path}"
            )
            continue
        actual_hash = hashlib.sha256(path.read_bytes()).hexdigest()
        expected_hash = recorded_hash.lower().removeprefix("sha256:")
        if actual_hash != expected_hash:
            issues.append(
                f"slide {record.get('slide') or index}: {path} records {recorded_hash} but is sha256:{actual_hash}"
            )
    return issues


def _qa_reviews_pass(visual_qa: dict[str, Any]) -> bool:
    reviews = visual_qa.get("reviews") or visual_qa.get("reviewers")
    if not isinstance(reviews, dict):
        return False
    first = reviews.get("anatomy_entity_spatial_identity") or reviews.get(
        "anatomy_entity_spatial_identity_reviewer"
    )
    second = reviews.get("storytelling_richness_text_style") or reviews.get(
        "storytelling_richness_text_style_reviewer"
    )
    return (
        isinstance(first, dict)
        and isinstance(second, dict)
        and first.get("pass") is True
        and second.get("pass") is True
    )


def _creator_approved(
    approval: dict[str, Any] | None = None,
    *,
    expected_image_set_sha256: str = "",
) -> bool:
    return bool(
        approval
        and approval.get("status") == "APPROVED"
        and approval.get("approved") is True
        and expected_image_set_sha256
        and approval.get("image_set_sha256") == expected_image_set_sha256
        and str(approval.get("approved_by") or "").strip()
        and str(approval.get("evidence") or "").strip()
    )


def _retry_metadata(payloads: list[dict[str, Any]]) -> tuple[int | None, int | None]:
    retry_count: int | None = None
    retry_limit: int | None = None
    for payload in payloads:
        retry_policy = payload.get("retry_policy")
        sources = [payload, retry_policy] if isinstance(retry_policy, dict) else [payload]
        for source in sources:
            for key in ("retry_count", "retries", "automatic_retries"):
                if source.get(key) is not None:
                    try:
                        retry_count = int(source[key])
                    except (TypeError, ValueError):
                        pass
            for key in (
                "max_retries",
                "max_auto_retries",
                "max_visual_qa_retries",
                "automatic_retry_limit",
            ):
                if source.get(key) is not None:
                    try:
                        retry_limit = int(source[key])
                    except (TypeError, ValueError):
                        pass
    return retry_count, retry_limit


def _failed_proof_retry_is_ready(
    package_dir: Path,
    image_generation: dict[str, Any],
    final_images: dict[str, Any],
) -> bool:
    """Recognize only a current, hash-bound failed-proof retry handoff."""

    if image_generation != final_images:
        return False
    if image_generation.get("proof_only") is not True:
        return False
    if _status(image_generation.get("status")) not in {
        "generated_quarantined",
        "rejected_spatial_integrity",
    }:
        return False
    if _status(image_generation.get("proof_state")) != _status(
        image_generation.get("status")
    ):
        return False
    qa_issues = image_generation.get("visual_qa_issues")
    if not isinstance(qa_issues, list) or not qa_issues:
        return False

    try:
        proof_slide = int(image_generation["requested_proof_slide"])
        prompt_pack = _read_json(package_dir / "prompt-pack.json")
        prompt_slides = prompt_pack.get("slides")
        if not isinstance(prompt_slides, list):
            return False
        selected_slides = [
            slide
            for slide in prompt_slides
            if isinstance(slide, dict)
            and int(slide.get("slide", 0) or 0) == proof_slide
        ]
        if len(selected_slides) != 1:
            return False
        current_formats = list(locked_formats(package_dir))
        if retry_prompt_handoff_attestation_issues(
            package_dir,
            state=image_generation,
        ):
            return False
        if compiled_prompt_handoff_integrity_issues(
            package_dir,
            state=image_generation,
            slides=selected_slides,
            output_formats=current_formats,
        ):
            return False

        ledger = load_attempt_ledger(package_dir)
        attempts = ledger.get("attempts")
        if not isinstance(attempts, list) or not attempts:
            return False
        latest = attempts[-1]
        if not isinstance(latest, dict) or latest.get("status") != "QA_FAILED":
            return False
        attestation = image_generation.get("retry_prompt_handoff_attestation")
        if not isinstance(attestation, dict):
            return False
        if attestation.get("failed_attempt") != latest:
            return False
        if attestation.get("next_retry_count") != len(attempts):
            return False
        if image_generation.get("retry_count") != latest.get("retry_count"):
            return False
        if next_retry_count(package_dir) != len(attempts):
            return False
    except (KeyError, TypeError, ValueError, OSError, json.JSONDecodeError):
        return False
    return True


def _failed_full_deck_retry_is_ready(
    package_dir: Path,
    image_generation: dict[str, Any],
    final_images: dict[str, Any],
) -> bool:
    """Recognize a hash-bound handoff that replaces one QA-failed full deck."""

    if image_generation != final_images or not _is_handoff_state(image_generation):
        return False
    if image_generation.get("proof_only") is not False:
        return False
    attestation = image_generation.get(
        "qa_failed_full_deck_retry_handoff_attestation"
    )
    if not isinstance(attestation, dict):
        return False
    try:
        payload = {
            key: value
            for key, value in attestation.items()
            if key != "attestation_fingerprint"
        }
        encoded = json.dumps(
            payload,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
        expected_fingerprint = "sha256:" + hashlib.sha256(encoded).hexdigest()
        if attestation.get("attestation_fingerprint") != expected_fingerprint:
            return False
        if _status(attestation.get("source_status")) not in {
            "generated_quarantined",
            "rejected_spatial_integrity",
        }:
            return False
        if not isinstance(attestation.get("visual_qa_binding"), dict):
            return False
        qa_binding = attestation["visual_qa_binding"]
        qa_path = package_dir / str(qa_binding.get("relative_path") or "")
        if (
            not qa_path.is_file()
            or qa_path.is_symlink()
            or sha256_binding(qa_path.read_bytes()) != qa_binding.get("sha256")
        ):
            return False
        failed_qa = _read_json(qa_path)
        if (
            _status(failed_qa.get("status")) != "fail"
            or failed_qa.get("image_set_sha256")
            != attestation.get("failed_image_set_sha256")
        ):
            return False

        ledger = load_attempt_ledger(package_dir)
        attempts = ledger.get("attempts")
        if not isinstance(attempts, list) or not attempts:
            return False
        latest = attempts[-1]
        if (
            not isinstance(latest, dict)
            or latest.get("status") != "QA_FAILED"
            or attestation.get("failed_attempt") != latest
            or attestation.get("next_retry_count") != len(attempts)
            or next_retry_count(
                package_dir,
                allow_approved_proof_batch=True,
            )
            != len(attempts)
        ):
            return False
        prompt_pack = _read_json(package_dir / "prompt-pack.json")
        prompt_slides = prompt_pack.get("slides")
        if not isinstance(prompt_slides, list) or len(prompt_slides) < 2:
            return False
        current_formats = list(locked_formats(package_dir))
        if compiled_prompt_handoff_integrity_issues(
            package_dir,
            state=image_generation,
            slides=prompt_slides,
            output_formats=current_formats,
        ):
            return False
        if approved_proof_batch_handoff_attestation_issues(
            package_dir,
            state=image_generation,
        ):
            return False
    except (KeyError, TypeError, ValueError, OSError, json.JSONDecodeError):
        return False
    return True


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
    identity_review = _read_json(package_dir / "identity-consistency-review.json")
    visual_qa = _read_json(package_dir / "visual-qa.json")
    approved_proof_handoff_claimed = isinstance(
        image_generation.get("approved_proof_batch_handoff_attestation"),
        dict,
    )
    approved_proof_handoff_issues = (
        approved_proof_batch_handoff_attestation_issues(
            package_dir,
            state=image_generation,
        )
        if approved_proof_handoff_claimed
        else []
    )
    if approved_proof_handoff_claimed and not approved_proof_handoff_issues:
        approval_relative_path = image_generation[
            "approved_proof_batch_handoff_attestation"
        ]["creator_approval_binding"]["relative_path"]
        creator_approval = _read_json(package_dir / approval_relative_path)
    else:
        creator_approval = _read_json(package_dir / "creator-proof-approval.json")
    text_generated_candidates = _read_json(package_dir / "text-generated-candidates.json")
    raw_scene = _read_text(package_dir / "raw-scene-row.md").lower()
    blocker_text = _read_text(package_dir / "image-generation-blocker.md").lower()
    correction = _declared_creator_correction(package_dir)
    correction_fingerprint = current_creator_correction_fingerprint(package_dir)
    try:
        generation_fingerprint = current_generation_payload_fingerprint(package_dir)
    except ValueError:
        generation_fingerprint = None

    try:
        current_formats = locked_formats(package_dir)
    except (ValueError, json.JSONDecodeError, OSError) as exc:
        current_formats = DEFAULT_NATIVE_FORMATS
        issues.append(
            _issue(
                "invalid_format_contract",
                "blocker",
                f"The current-request format contract is invalid: {exc}",
                evidence=[package_dir / FORMAT_CONTRACT_FILENAME],
                next_action="repair_and_relock_current_request_formats",
            )
        )

    lifecycle_payloads = [image_generation, final_images, visual_qa]
    lifecycle_states = {
        state for state in (_proof_state(payload) for payload in lifecycle_payloads) if state
    }
    proof_files = [
        path
        for dirname in ("proof", "proofs", "quarantine")
        if (package_dir / dirname).exists()
        for path in (package_dir / dirname).rglob("*")
        if path.is_file()
    ]
    has_generated_proof = bool(lifecycle_states or proof_files)
    qa_v2_issues = (
        _structured_visual_qa_v2_issues(
            package_dir,
            visual_qa,
            visual_plan=visual_plan_quality,
        )
        if has_generated_proof
        else []
    )
    retry_ready_failed_proof = _failed_proof_retry_is_ready(
        package_dir,
        image_generation,
        final_images,
    )
    retry_ready_failed_full_deck = _failed_full_deck_retry_is_ready(
        package_dir,
        image_generation,
        final_images,
    )
    creator_override_handoff_claimed = (
        (_is_handoff_state(image_generation) or _is_handoff_state(final_images))
        and any(
            payload.get("creator_override") is True
            or isinstance(payload.get("creator_override_proof_binding"), dict)
            for payload in (image_generation, final_images)
        )
    )
    creator_override_handoff_issues = (
        creator_override_batch_handoff_integrity_issues(
            package_dir,
            state=image_generation,
            final_state=final_images,
        )
        if creator_override_handoff_claimed
        else []
    )
    creator_override_handoff_valid = (
        creator_override_handoff_claimed
        and not creator_override_handoff_issues
    )
    if creator_override_handoff_issues:
        issues.append(
            _issue(
                "creator_override_handoff_integrity_invalid",
                "blocker",
                "Creator-override batch handoff evidence is missing, stale, or contradictory.",
                evidence=[
                    package_dir / "image-generation.json",
                    package_dir / "final-images.json",
                    *creator_override_handoff_issues[:12],
                ],
                next_action="restore_the_bound_creator_override_evidence_or_reaccept_the_current_failed_proof",
            )
        )
    if (
        has_generated_proof
        and qa_v2_issues
        and not retry_ready_failed_proof
        and not retry_ready_failed_full_deck
        and not creator_override_handoff_valid
    ):
        issues.append(
            _issue(
                "generated_proof_without_structured_qa_v2",
                "blocker",
                "Generated proof is quarantined until schema-v2 structured visual QA is complete.",
                evidence=[package_dir / "visual-qa.json", *qa_v2_issues[:12]],
                next_action="run_both_post_generation_reviews_and_record_schema_v2_visual_qa",
            )
        )

    hash_issues = _qa_asset_hash_issues(package_dir, visual_qa)
    if hash_issues:
        issues.append(
            _issue(
                "visual_qa_asset_hash_mismatch",
                "blocker",
                "Visual QA evidence is stale because a reviewed source asset has changed.",
                evidence=[package_dir / "visual-qa.json", *hash_issues[:12]],
                next_action="invalidate_stale_qa_and_review_the_current_asset",
            )
        )

    publishable_claim = any(_has_publishable_final_claim(payload) for payload in lifecycle_payloads)
    batch_claim = any(_allows_batch_continuation(payload) for payload in lifecycle_payloads)
    expected_image_set_sha256 = str(visual_qa.get("image_set_sha256") or "").strip()
    creator_approved = _creator_approved(
        creator_approval,
        expected_image_set_sha256=expected_image_set_sha256,
    )
    if approved_proof_handoff_issues:
        issues.append(
            _issue(
                "approved_proof_handoff_integrity_invalid",
                "blocker",
                "The QA-passed proof handoff evidence is missing, stale, or contradictory.",
                evidence=[
                    package_dir / "image-generation.json",
                    *approved_proof_handoff_issues[:12],
                ],
                next_action="restore_the_exact_approved_proof_evidence_before_generation",
            )
        )
    if (
        creator_approval
        and not creator_approved
        and not retry_ready_failed_full_deck
    ):
        issues.append(
            _issue(
                "creator_approval_asset_hash_mismatch",
                "blocker",
                "Creator approval is missing required evidence or is bound to a different image set.",
                evidence=[
                    package_dir / "creator-proof-approval.json",
                    f"expected_image_set_sha256={expected_image_set_sha256 or 'missing'}",
                    f"approved_image_set_sha256={creator_approval.get('image_set_sha256') or 'missing'}",
                ],
                next_action="approve_the_current_qa_passed_image_set_and_record_its_exact_hash",
            )
        )
    if "generated_quarantined" in lifecycle_states and (publishable_claim or batch_claim):
        issues.append(
            _issue(
                "quarantined_proof_claims_continuation",
                "blocker",
                "A quarantined proof cannot be publishable or allow batch continuation.",
                evidence=[package_dir / "image-generation.json", package_dir / "final-images.json"],
                next_action="remove_publish_and_batch_claims_until_qa_and_creator_approval_pass",
            )
        )

    qa_claims_pass = (
        "qa_pass_candidate" in lifecycle_states
        or _status(visual_qa.get("status") or visual_qa.get("verdict")) == "pass"
    )
    if has_generated_proof and qa_claims_pass and not creator_approved:
        issues.append(
            _issue(
                "qa_pass_without_creator_approval",
                "blocker",
                "QA-passed proof still requires explicit creator approval before continuation.",
                evidence=[package_dir / "visual-qa.json", package_dir / "image-generation.json"],
                next_action="record_creator_approval_before_promoting_the_proof",
            )
        )

    if batch_claim and "batch_allowed" not in lifecycle_states:
        issues.append(
            _issue(
                "batch_allowed_without_correct_state",
                "blocker",
                "Batch continuation is claimed without the BATCH_ALLOWED lifecycle state.",
                evidence=[package_dir / "image-generation.json", package_dir / "final-images.json"],
                next_action="promote_creator_approved_proof_to_batch_allowed_or_disable_batching",
            )
        )
    if "batch_allowed" in lifecycle_states and not creator_override_handoff_valid and (
        not creator_approved or qa_v2_issues or not _qa_reviews_pass(visual_qa)
    ):
        issues.append(
            _issue(
                "batch_state_without_required_gates",
                "blocker",
                "BATCH_ALLOWED requires schema-v2 QA and creator-approved proof state.",
                evidence=[package_dir / "visual-qa.json", package_dir / "image-generation.json"],
                next_action="complete_qa_and_creator_approval_before_batch_promotion",
            )
        )

    if "blocked_visual_qa" in lifecycle_states and not creator_override_handoff_valid:
        retry_count, retry_limit = _retry_metadata(lifecycle_payloads)
        if retry_count != 2 or retry_limit != 2:
            issues.append(
                _issue(
                    "blocked_visual_qa_retry_metadata_invalid",
                    "blocker",
                    "BLOCKED_VISUAL_QA is valid only after exactly two automatic retries.",
                    evidence=[
                        package_dir / "visual-qa.json",
                        f"retry_count={retry_count!r}",
                        f"max_auto_retries={retry_limit!r}",
                    ],
                    next_action="record_the_two-retry_exhaustion_or_return_to_quarantine",
                )
            )
        if publishable_claim or batch_claim:
            issues.append(
                _issue(
                    "blocked_visual_qa_claims_publishable",
                    "blocker",
                    "BLOCKED_VISUAL_QA is terminal and cannot be publishable or batchable.",
                    evidence=[package_dir / "image-generation.json", package_dir / "final-images.json"],
                    next_action="remove_publish_and_batch_claims_and_keep_the_run_blocked",
                )
            )
        issues.append(
            _issue(
                "blocked_visual_qa_terminal",
                "blocker",
                "Visual QA exhausted its two retries; the run is correctly stopped and cannot publish.",
                evidence=[package_dir / "visual-qa.json"],
                next_action="start_a_new_creator-directed repair rather than continuing_this_batch",
            )
        )

    slides_value: Any = []
    slides_path = package_dir / "slides.json"
    if slides_path.exists():
        try:
            slides_value = json.loads(slides_path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            slides_value = []
    slide_records = (
        slides_value
        if isinstance(slides_value, list)
        else slides_value.get("slides", [])
        if isinstance(slides_value, dict)
        else []
    )

    handoff_or_generated = (
        _is_handoff_state(image_generation)
        or _is_handoff_state(final_images)
        or _status(final_images.get("status")) in {"generated", "packaged", "publish_ready", "publishable"}
        or _has_publishable_final_claim(final_images)
    )
    if handoff_or_generated:
        if not (package_dir / FORMAT_CONTRACT_FILENAME).exists():
            issues.append(
                _issue(
                    "missing_format_contract",
                    "blocker",
                    "Handoff and generated packages must persist the current-request format lock.",
                    evidence=[package_dir / FORMAT_CONTRACT_FILENAME],
                    next_action="lock_current_request_formats_before_generation",
                )
            )
        for artifact_name, payload in (
            ("image-generation.json", image_generation),
            ("final-images.json", final_images),
        ):
            requested = payload.get("requested_formats")
            if requested is not None and list(requested) != list(current_formats):
                issues.append(
                    _issue(
                        "format_contract_mismatch",
                        "blocker",
                        f"{artifact_name} requested_formats does not match format-contract.json.",
                        evidence=[
                            package_dir / FORMAT_CONTRACT_FILENAME,
                            package_dir / artifact_name,
                        ],
                        next_action="regenerate_artifacts_from_the_current_format_lock",
                    )
                )
        director_issues = validate_director_storyboard(
            visual_plan_quality,
            slide_count=len(slide_records),
            expected_slides=slides_value,
            expected_formats=current_formats,
            expected_format_contract_fingerprint=locked_format_contract_fingerprint(
                package_dir
            ),
            expected_creator_correction_fingerprint=correction_fingerprint,
            expected_generation_payload_fingerprint=generation_fingerprint,
            provenance_package_dir=package_dir,
        )
        if director_issues:
            issues.append(
                _issue(
                    "director_storyboard_failed",
                    "blocker",
                    "Pre-generation director/storyboard evidence is missing, incomplete, or stale.",
                    evidence=[package_dir / "visual-plan-quality.json", *director_issues[:8]],
                    next_action="run_visual_story_precheck_before_generation_or_handoff",
                )
            )

    stale_matches = _stale_generation_matches(package_dir, correction)
    if stale_matches:
        issues.append(
            _issue(
                "stale_artifact_carryover",
                "blocker",
                "Creator correction has rejected phrases that still appear in active generation-facing artifacts.",
                evidence=stale_matches[:12],
                next_action="rebuild_generation_facing_artifacts_from_corrected_source",
            )
        )

    if _identity_gate_requested(package_dir, image_generation, final_images, identity_review):
        identity_status = _identity_review_status(identity_review)
        identity_evidence = [
            package_dir / "identity-consistency-review.json",
            package_dir / "image-generation.json",
            package_dir / "final-images.json",
        ]
        if not identity_review:
            issues.append(
                _issue(
                    "identity_eval_missing_stop_gate",
                    "blocker",
                    "Batch continuation is requested without structured identity-consistency-review.json evidence.",
                    evidence=identity_evidence,
                    next_action="record_identity_unverified_or_run_structured_identity_eval",
                )
            )
        elif identity_status in IDENTITY_BLOCK_STATUSES:
            issues.append(
                _issue(
                    "identity_eval_unverified_stop_gate",
                    "blocker",
                    "Identity review is blocked or unverified, so batch generation must not continue.",
                    evidence=identity_evidence,
                    next_action="repair_identity_eval_before_generating_next_slide",
                )
            )
        elif identity_status != "pass":
            issues.append(
                _issue(
                    "identity_eval_not_passed_stop_gate",
                    "blocker",
                    "Identity review exists but does not pass.",
                    evidence=identity_evidence,
                    next_action="repair_identity_eval_before_generating_next_slide",
                )
            )
        else:
            missing_identity_fields: list[str] = []
            if not _has_person_reference_ids(identity_review):
                missing_identity_fields.append("selected reference IDs for Aachu and Zuv")
            if not _has_specific_likeness_notes(identity_review):
                missing_identity_fields.append("specific likeness notes for Aachu and Zuv")
            if missing_identity_fields and not creator_override_handoff_valid:
                issues.append(
                    _issue(
                        "identity_eval_incomplete_stop_gate",
                        "blocker",
                        "Identity review PASS is missing required structured evidence: "
                        + "; ".join(missing_identity_fields)
                        + ".",
                        evidence=identity_evidence,
                        next_action="complete_identity_review_reference_ids_and_likeness_notes",
                    )
                )

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

    if _has_publishable_final_claim(final_images):
        final_asset_report = validate_publishable_final_assets(package_dir)
        for asset_issue in final_asset_report.issues:
            issues.append(
                _issue(
                    asset_issue.code,
                    asset_issue.severity,
                    asset_issue.reason,
                    evidence=[package_dir / asset_issue.path],
                    next_action="repair_final_image_assets",
                )
            )
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
            for output_format in current_formats:
                final_path = expected_output_path(package_dir, output_format, number)
                if not final_path.exists():
                    spec = format_spec(output_format)
                    width, height = spec["target_size"]
                    issues.append(
                        _issue(
                            f"missing_{output_format}_final",
                            "blocker",
                            f"Missing requested {spec['label']} {width}x{height} final image for slide {number:02d}.",
                            evidence=[final_path],
                            next_action="package_all_locked_native_final_outputs",
                        )
                    )

    final_render_files = [
        path
        for output_format in current_formats
        for path in sorted(
            (package_dir / str(format_spec(output_format)["folder"])).glob("slide-*.png")
        )
    ]
    if final_render_files or _has_publishable_final_claim(final_images):
        visual_qa = _read_json(package_dir / "visual-qa.json")
        checks = visual_qa.get("checks") if isinstance(visual_qa, dict) else None
        readability = (
            checks.get(VISUAL_STORY_READABILITY_KEY)
            if isinstance(checks, dict)
            else None
        )
        readability_issues = validate_frame_readability(
            readability,
            slide_count=len(slide_records) or len(_slide_numbers(package_dir, final_images)),
            required_formats=current_formats,
            expected_director_event_fingerprint=director_event_fingerprint(
                visual_plan_quality
            ),
            event_a_review_provenance=director_review_provenance(visual_plan_quality),
            event_a_creator_correction_fingerprint=(
                director_creator_correction_fingerprint(visual_plan_quality)
            ),
            expected_creator_correction_fingerprint=correction_fingerprint,
            event_a_generation_payload_fingerprint=(
                director_generation_payload_fingerprint(visual_plan_quality)
            ),
            expected_generation_payload_fingerprint=generation_fingerprint,
            director_author_id=director_author_id(visual_plan_quality),
            director_reviewer_id=director_reviewer_id(visual_plan_quality),
            expected_frame_bindings=expected_frame_bindings(
                package_dir,
                len(slide_records) or len(_slide_numbers(package_dir, final_images)),
                current_formats,
            ),
            package_dir=package_dir,
            provenance_package_dir=package_dir,
            require_files=True,
        )
        if readability_issues:
            issues.append(
                _issue(
                    "visual_story_readability_failed",
                    "blocker",
                    "Rendered frames have not passed the independent visual-story readability audit.",
                    evidence=[package_dir / "visual-qa.json", *readability_issues[:8]],
                    next_action="run_visual_story_postcheck_and_repair_weak_frames",
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
