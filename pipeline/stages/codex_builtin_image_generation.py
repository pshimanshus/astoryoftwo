from __future__ import annotations

import json
import hashlib
import re
import shutil
from collections.abc import Callable
from datetime import date
from pathlib import Path
from typing import Any

from pipeline.agentic.checks.prompt_constraints import check_prompt_constraints
from pipeline.layer_e.artifacts import layer_e_gate_reason
from pipeline.agentic.generation_capability import write_generation_capability
from pipeline.stages.carousel_generation_state import GenerationStatus, write_generation_state
from pipeline.stages.carousel_format_contract import (
    FORMAT_CONTRACT_FILENAME,
    INSTAGRAM_POST_FORMAT,
    REELS_STORIES_FORMAT,
    SQUARE_FORMAT,
    expected_frame_bindings,
    expected_output_relative_path,
    expected_output_path,
    expected_source_path,
    format_spec,
    load_format_contract,
    locked_format_contract_fingerprint,
    locked_formats,
    native_output_contract,
    normalize_requested_formats,
    write_format_contract,
)
from pipeline.stages.carousel_prompt_compiler import compile_image_prompt, extract_scene_summary
from pipeline.stages.carousel_quality import validate_spatial_topology_check
from pipeline.stages.carousel_style_consistency import house_style_consistency_gate_reason
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
from pipeline.stages.model_native_image_generation import (
    NATIVE_OUTPUT_FORMATS,
    decode_png,
    existing_reference_paths,
)


BACKEND = "codex_builtin"
GENERATION_MODE = "model_native_publishable"
MAX_VISUAL_QA_RETRIES = 2
QUARANTINE_FOLDER = ".internal/visual-quarantine"
ATTEMPT_LEDGER = ".internal/visual-qa-attempts.json"
PROMOTION_STAGING_FOLDER = ".internal/promotion-staging"
PROMPT_HANDOFF_ACTIVE_FOLDER = "codex-image-prompts"
PROMPT_HANDOFF_STAGING_FOLDER = ".internal/codex-image-prompts-staging"
PROMPT_HANDOFF_SCHEMA_VERSION = "compiled-prompt-handoff/v1"
VISUAL_QA_REVIEW_KEYS = (
    "anatomy_entity_spatial_identity",
    "storytelling_richness_text_style",
)


def write_json(path: Path, data: Any) -> None:
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def sha256_binding(payload: bytes) -> str:
    return "sha256:" + sha256_bytes(payload)


def remove_path_without_following(path: Path) -> None:
    """Remove one package artifact without ever following a symlink target."""

    if path.is_symlink() or path.is_file():
        path.unlink()
    elif path.exists():
        shutil.rmtree(path)


def prompt_handoff_relative_path(
    output_format: str,
    slide_number: int,
    kind: str,
) -> str:
    stem = f"slide-{int(slide_number):02d}"
    if kind == "generator_prompt":
        filename = f"{stem}.prompt.txt"
    elif kind == "handoff_markdown":
        filename = f"{stem}.md"
    else:
        raise ValueError(f"Unsupported compiled-prompt handoff file kind: {kind}")
    return f"{PROMPT_HANDOFF_ACTIVE_FOLDER}/{format_prompt_dir_name(output_format)}/{filename}"


def _canonical_fingerprint(payload: dict[str, Any]) -> str:
    encoded = json.dumps(
        payload,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return sha256_binding(encoded)


def build_compiled_prompt_handoff(
    carousel_dir: Path,
    *,
    slide_numbers: list[int],
    output_formats: list[str] | tuple[str, ...],
    prompt_source_root: Path | None = None,
) -> dict[str, Any]:
    """Bind the exact prompt pair exposed for every requested slide/format."""

    carousel_dir = Path(carousel_dir).expanduser()
    canonical_formats = list(normalize_requested_formats(output_formats))
    canonical_slides = sorted(int(number) for number in slide_numbers)
    if not canonical_slides or len(canonical_slides) != len(set(canonical_slides)):
        raise ValueError("Compiled-prompt handoff requires unique current slide numbers.")
    source_root = prompt_source_root or carousel_dir / PROMPT_HANDOFF_ACTIVE_FOLDER
    files: list[dict[str, Any]] = []
    for number in canonical_slides:
        for output_format in canonical_formats:
            for kind in ("generator_prompt", "handoff_markdown"):
                relative_path = prompt_handoff_relative_path(output_format, number, kind)
                source_path = source_root / Path(relative_path).relative_to(
                    PROMPT_HANDOFF_ACTIVE_FOLDER
                )
                if source_path.is_symlink() or not source_path.is_file():
                    raise ValueError(
                        f"Compiled-prompt handoff file is missing or unsafe: {relative_path}"
                    )
                files.append(
                    {
                        "slide": number,
                        "format": output_format,
                        "kind": kind,
                        "relative_path": relative_path,
                        "sha256": sha256_binding(source_path.read_bytes()),
                    }
                )

    prompt_pack_path = carousel_dir / "prompt-pack.json"
    slides_path = carousel_dir / "slides.json"
    input_bindings = {
        "prompt_pack": {
            "relative_path": "prompt-pack.json",
            "sha256": sha256_binding(prompt_pack_path.read_bytes()),
        },
        "slides": {
            "relative_path": "slides.json",
            "sha256": sha256_binding(slides_path.read_bytes()),
        },
    }
    fingerprint_payload = {
        "schema_version": PROMPT_HANDOFF_SCHEMA_VERSION,
        "requested_formats": canonical_formats,
        "slide_numbers": canonical_slides,
        "format_contract_fingerprint": locked_format_contract_fingerprint(carousel_dir),
        "input_bindings": input_bindings,
        "files": files,
    }
    return {
        **fingerprint_payload,
        "handoff_set_fingerprint": _canonical_fingerprint(fingerprint_payload),
    }


def _bound_package_file_issues(
    carousel_dir: Path,
    binding: Any,
    *,
    expected_relative_path: str,
) -> list[str]:
    issues: list[str] = []
    if not isinstance(binding, dict):
        return [f"missing binding for {expected_relative_path}"]
    raw_path = binding.get("relative_path")
    if raw_path != expected_relative_path:
        issues.append(f"binding path must be {expected_relative_path}")
        return issues
    relative_path = Path(str(raw_path))
    if relative_path.is_absolute() or ".." in relative_path.parts:
        return [f"binding path is external or traverses the package: {raw_path}"]

    package_root = carousel_dir.expanduser().resolve()
    candidate = carousel_dir / relative_path
    cursor = carousel_dir
    for part in relative_path.parts:
        cursor = cursor / part
        if cursor.is_symlink():
            issues.append(f"bound handoff path contains a symlink: {raw_path}")
            return issues
    try:
        candidate.resolve().relative_to(package_root)
    except (OSError, ValueError):
        issues.append(f"bound handoff path escapes the package: {raw_path}")
        return issues
    if not candidate.is_file():
        issues.append(f"bound handoff file is missing: {raw_path}")
        return issues
    expected_sha = binding.get("sha256")
    actual_sha = sha256_binding(candidate.read_bytes())
    if expected_sha != actual_sha:
        issues.append(f"bound handoff file changed after compilation: {raw_path}")
    return issues


def compiled_prompt_handoff_integrity_issues(
    carousel_dir: Path,
    *,
    state: Any,
    slides: list[dict[str, Any]],
    output_formats: list[str] | tuple[str, ...],
) -> list[str]:
    """Verify a ready prompt set against the current package before quarantine."""

    if not isinstance(state, dict):
        return ["image-generation.json is missing or malformed"]
    handoff = state.get("compiled_prompt_handoff")
    if not isinstance(handoff, dict):
        return ["HANDOFF_READY state is missing compiled_prompt_handoff bindings"]
    issues: list[str] = []
    allowed_states = {
        GenerationStatus.HANDOFF_READY.value,
        GenerationStatus.GENERATED_QUARANTINED.value,
        GenerationStatus.QA_PASS_CANDIDATE.value,
        GenerationStatus.CREATOR_APPROVED_PROOF.value,
        GenerationStatus.REJECTED_SPATIAL_INTEGRITY.value,
    }
    if state.get("status") not in allowed_states:
        issues.append("generation state is not eligible for compiled-prompt packaging")
    canonical_formats = list(normalize_requested_formats(output_formats))
    try:
        slide_numbers = [int(slide["slide"]) for slide in slides]
    except (KeyError, TypeError, ValueError):
        return ["prompt-pack.json has invalid current slide numbers"]
    if not slide_numbers or len(slide_numbers) != len(set(slide_numbers)):
        return ["prompt-pack.json must have unique current slide numbers"]
    canonical_slides = sorted(slide_numbers)

    if handoff.get("schema_version") != PROMPT_HANDOFF_SCHEMA_VERSION:
        issues.append("compiled-prompt handoff schema is missing or unsupported")
    if handoff.get("requested_formats") != canonical_formats:
        issues.append("compiled-prompt handoff formats are stale for the current lock")
    if state.get("requested_formats") != canonical_formats:
        issues.append("generation-state formats are stale for the current lock")
    if handoff.get("slide_numbers") != canonical_slides:
        issues.append("compiled-prompt handoff slides are stale for prompt-pack.json")
    if state.get("slide_count") != len(canonical_slides):
        issues.append("generation-state slide count is stale for prompt-pack.json")
    try:
        state_slide_numbers = sorted(
            int(record.get("slide", 0) or 0)
            for record in state.get("slides", [])
            if isinstance(record, dict)
        )
    except (TypeError, ValueError):
        state_slide_numbers = []
    if state_slide_numbers != canonical_slides:
        issues.append("generation-state slide records do not cover the current slides")
    format_fingerprint = locked_format_contract_fingerprint(carousel_dir)
    if handoff.get("format_contract_fingerprint") != format_fingerprint:
        issues.append("compiled-prompt handoff format fingerprint is stale")

    input_bindings = handoff.get("input_bindings")
    if not isinstance(input_bindings, dict):
        issues.append("compiled-prompt handoff input bindings are missing")
    else:
        issues.extend(
            _bound_package_file_issues(
                carousel_dir,
                input_bindings.get("prompt_pack"),
                expected_relative_path="prompt-pack.json",
            )
        )
        issues.extend(
            _bound_package_file_issues(
                carousel_dir,
                input_bindings.get("slides"),
                expected_relative_path="slides.json",
            )
        )

    raw_files = handoff.get("files")
    if not isinstance(raw_files, list):
        issues.append("compiled-prompt handoff file bindings are missing")
        raw_files = []
    expected: dict[str, tuple[int, str, str]] = {}
    for number in canonical_slides:
        for output_format in canonical_formats:
            for kind in ("generator_prompt", "handoff_markdown"):
                path = prompt_handoff_relative_path(output_format, number, kind)
                expected[path] = (number, output_format, kind)
    seen: set[str] = set()
    for binding in raw_files:
        if not isinstance(binding, dict):
            issues.append("compiled-prompt handoff contains a malformed file binding")
            continue
        raw_path = binding.get("relative_path")
        if not isinstance(raw_path, str):
            issues.append("compiled-prompt handoff contains a binding without a relative path")
            continue
        if raw_path in seen:
            issues.append(f"compiled-prompt handoff repeats a file binding: {raw_path}")
            continue
        seen.add(raw_path)
        metadata = expected.get(raw_path)
        if metadata is None:
            issues.append(f"compiled-prompt handoff binds an unexpected path: {raw_path}")
            continue
        number, output_format, kind = metadata
        if (
            binding.get("slide") != number
            or binding.get("format") != output_format
            or binding.get("kind") != kind
        ):
            issues.append(f"compiled-prompt handoff metadata is stale for {raw_path}")
        issues.extend(
            _bound_package_file_issues(
                carousel_dir,
                binding,
                expected_relative_path=raw_path,
            )
        )
    for missing in sorted(set(expected) - seen):
        issues.append(f"compiled-prompt handoff is missing a file binding: {missing}")
    active_root = carousel_dir / PROMPT_HANDOFF_ACTIVE_FOLDER
    if active_root.is_symlink() or not active_root.is_dir():
        issues.append("active compiled-prompt root is missing or symlinked")
    else:
        for candidate in active_root.rglob("*"):
            if not (candidate.is_file() or candidate.is_symlink()):
                continue
            relative = candidate.relative_to(carousel_dir).as_posix()
            if relative not in expected:
                issues.append(f"active compiled-prompt set contains an unbound file: {relative}")

    fingerprint_payload = {
        "schema_version": handoff.get("schema_version"),
        "requested_formats": handoff.get("requested_formats"),
        "slide_numbers": handoff.get("slide_numbers"),
        "format_contract_fingerprint": handoff.get("format_contract_fingerprint"),
        "input_bindings": handoff.get("input_bindings"),
        "files": handoff.get("files"),
    }
    if handoff.get("handoff_set_fingerprint") != _canonical_fingerprint(fingerprint_payload):
        issues.append("compiled-prompt handoff set fingerprint is stale")
    return issues


def image_set_sha256(slides: list[dict[str, Any]]) -> str:
    bindings: list[str] = []
    for slide in slides:
        number = int(slide["slide"])
        for output_format in normalize_requested_formats(slide["native_outputs"].keys()):
            item = slide["native_outputs"][output_format]
            bindings.append(
                f"{number}:{output_format}:{item['sha256']}:{item['width']}x{item['height']}"
            )
    return sha256_bytes("\n".join(bindings).encode("utf-8"))


def quarantine_dir(carousel_dir: Path, retry_count: int) -> Path:
    return carousel_dir / QUARANTINE_FOLDER / f"attempt-{retry_count + 1:02d}"


def attempt_ledger_path(carousel_dir: Path) -> Path:
    return carousel_dir / ATTEMPT_LEDGER


def load_attempt_ledger(carousel_dir: Path) -> dict[str, Any]:
    path = attempt_ledger_path(carousel_dir)
    if not path.exists():
        return {"schema_version": "1.0", "max_retries": MAX_VISUAL_QA_RETRIES, "attempts": []}
    ledger = load_json(path)
    attempts = ledger.get("attempts")
    if not isinstance(attempts, list):
        raise ValueError("Visual-QA attempt ledger is malformed.")
    return ledger


def write_attempt_ledger(carousel_dir: Path, ledger: dict[str, Any]) -> None:
    path = attempt_ledger_path(carousel_dir)
    path.parent.mkdir(parents=True, exist_ok=True)
    write_json(path, ledger)


def next_retry_count(carousel_dir: Path) -> int:
    """Derive the next immutable attempt number from persisted state."""

    ledger = load_attempt_ledger(carousel_dir)
    attempts = ledger["attempts"]
    if not attempts:
        return 0
    last = attempts[-1]
    if not isinstance(last, dict) or last.get("status") != "QA_FAILED":
        raise ValueError(
            "A new candidate is allowed only after the current quarantined attempt has "
            "completed QA with a recorded failure."
        )
    retry_count = len(attempts)
    if retry_count > MAX_VISUAL_QA_RETRIES:
        raise ValueError("Visual-QA retry limit is exhausted; the run is BLOCKED_VISUAL_QA.")
    return retry_count


def append_attempt(
    carousel_dir: Path,
    *,
    retry_count: int,
    image_set_hash: str,
) -> None:
    ledger = load_attempt_ledger(carousel_dir)
    attempts = ledger["attempts"]
    if retry_count != len(attempts):
        raise ValueError(
            f"Attempt ledger expected retry_count {len(attempts)}, got {retry_count}."
        )
    attempts.append(
        {
            "attempt": retry_count + 1,
            "retry_count": retry_count,
            "image_set_sha256": image_set_hash,
            "status": "QUARANTINED",
            "qa_issues": [],
            "targeted_repair_instructions": [],
        }
    )
    write_attempt_ledger(carousel_dir, ledger)


def update_current_attempt(
    carousel_dir: Path,
    *,
    status: str,
    qa_issues: list[str] | None = None,
) -> None:
    ledger = load_attempt_ledger(carousel_dir)
    attempts = ledger["attempts"]
    if not attempts:
        raise ValueError("Cannot update visual-QA attempt ledger before generation.")
    current = attempts[-1]
    current["status"] = status
    if qa_issues is not None:
        current["qa_issues"] = list(qa_issues)
        current["targeted_repair_instructions"] = [
            f"Repair this exact QA failure without weakening any other locked constraint: {issue}"
            for issue in qa_issues
        ]
    write_attempt_ledger(carousel_dir, ledger)


def resolve_package_artifact_path(carousel_dir: Path, raw_path: str | Path | None, default: str) -> Path:
    path = Path(raw_path) if raw_path is not None else Path(default)
    return path if path.is_absolute() else carousel_dir / path


def _qa_slide_records(visual_qa: dict[str, Any]) -> list[dict[str, Any]]:
    records = visual_qa.get("slides")
    return records if isinstance(records, list) else []


def _qa_check_slide_record(
    visual_qa: dict[str, Any], check_name: str, slide_number: int
) -> dict[str, Any] | None:
    for record in _qa_slide_records(visual_qa):
        if isinstance(record, dict) and record.get("slide") == slide_number:
            value = record.get(check_name)
            if isinstance(value, dict):
                return value
    checks = visual_qa.get("checks")
    check = checks.get(check_name) if isinstance(checks, dict) else None
    records = check.get("slides") if isinstance(check, dict) else None
    if isinstance(records, list):
        for record in records:
            if isinstance(record, dict) and record.get("slide") == slide_number:
                return record
    return None


def _qa_native_output_binding(
    visual_qa: dict[str, Any], slide_number: int, output_format: str
) -> dict[str, Any] | None:
    for record in _qa_slide_records(visual_qa):
        if not isinstance(record, dict) or record.get("slide") != slide_number:
            continue
        outputs = record.get("native_outputs") or record.get("source_images")
        binding = outputs.get(output_format) if isinstance(outputs, dict) else None
        return binding if isinstance(binding, dict) else None
    return None


def _quarantine_review_root(
    carousel_dir: Path,
    slides: list[dict[str, Any]],
) -> Path | None:
    """Return one verified package-contained attempt root for Event B."""

    package_root = Path(carousel_dir).expanduser().resolve()
    quarantine_root = (package_root / QUARANTINE_FOLDER).resolve()
    attempt_roots: set[Path] = set()
    found = False
    for slide in slides:
        outputs = slide.get("native_outputs")
        if not isinstance(outputs, dict):
            continue
        for output in outputs.values():
            if not isinstance(output, dict) or not output.get("path"):
                continue
            found = True
            raw_path = Path(str(output["path"])).expanduser()
            candidate = raw_path if raw_path.is_absolute() else package_root / raw_path
            if ".." in raw_path.parts:
                return None
            try:
                relative = candidate.resolve().relative_to(quarantine_root)
            except (OSError, ValueError):
                return None
            if len(relative.parts) != 3 or not re.fullmatch(
                r"attempt-\d{2,}", relative.parts[0]
            ):
                return None
            cursor = quarantine_root
            for part in relative.parts:
                cursor = cursor / part
                if cursor.is_symlink():
                    return None
            attempt_roots.add(quarantine_root / relative.parts[0])
    if not found or len(attempt_roots) != 1:
        return None
    return next(iter(attempt_roots))


def _qa_format_evidence(
    record: dict[str, Any] | None,
    output_format: str,
) -> dict[str, Any] | None:
    """Return evidence for one independently generated native image."""

    if not isinstance(record, dict):
        return None
    formats = record.get("formats")
    evidence = formats.get(output_format) if isinstance(formats, dict) else None
    return evidence if isinstance(evidence, dict) else None


def _validate_format_source_asset(
    evidence: dict[str, Any],
    expected_asset: dict[str, Any],
    *,
    label: str,
    check_name: str,
    issues: list[str],
) -> None:
    source_asset = evidence.get("source_asset")
    if not isinstance(source_asset, dict):
        issues.append(f"{label} {check_name} requires source_asset hash and dimensions")
        return
    if source_asset.get("sha256") != expected_asset["sha256"]:
        issues.append(f"{label} {check_name} source_asset hash is stale")
    if (
        source_asset.get("width") != expected_asset["width"]
        or source_asset.get("height") != expected_asset["height"]
    ):
        issues.append(f"{label} {check_name} source_asset dimensions are stale")


def validate_exact_image_visual_qa(
    visual_qa: dict[str, Any],
    quarantine_slides: list[dict[str, Any]],
    *,
    visual_plan: dict[str, Any] | None = None,
    carousel_dir: Path | None = None,
    include_story_checks: bool = True,
) -> list[str]:
    """Return fail-closed issues for post-generation QA bound to exact pixels."""

    issues: list[str] = []
    if carousel_dir is None:
        issues.append(
            "visual-qa.json requires carousel_dir to verify package-contained quarantine assets"
        )
    else:
        quarantine_formats: tuple[str, ...] = ()
        for quarantine_slide in quarantine_slides:
            outputs = quarantine_slide.get("native_outputs")
            if isinstance(outputs, dict) and outputs:
                quarantine_formats = tuple(str(value) for value in outputs)
                break
        issues.extend(
            validate_quarantine_integrity(
                quarantine_slides,
                quarantine_formats,
                carousel_dir=carousel_dir,
            )
        )
    try:
        schema_parts = str(visual_qa.get("schema_version") or "0.0").split(".")
        schema_version = (int(schema_parts[0]), int(schema_parts[1]))
    except (ValueError, IndexError):
        schema_version = (0, 0)
    if schema_version < (2, 1):
        issues.append("visual-qa.json schema_version must be at least 2.1")
    if visual_qa.get("status") != "PASS":
        issues.append("visual-qa.json status must be PASS")
    if visual_qa.get("proof_state") not in {
        GenerationStatus.QA_PASS_CANDIDATE.value,
        GenerationStatus.CREATOR_APPROVED_PROOF.value,
        GenerationStatus.BATCH_ALLOWED.value,
    }:
        issues.append("visual-qa.json proof_state must be QA_PASS_CANDIDATE or a later approved state")
    expected_set_hash = image_set_sha256(quarantine_slides)
    if visual_qa.get("image_set_sha256") != expected_set_hash:
        issues.append("visual-qa.json image_set_sha256 is missing or stale")

    reviews = visual_qa.get("reviews")
    if not isinstance(reviews, dict):
        issues.append("visual-qa.json must include two independent structured reviews")
        reviews = {}
    reviewers: set[str] = set()
    for key in VISUAL_QA_REVIEW_KEYS:
        review = reviews.get(key)
        review_passed = isinstance(review, dict) and (
            review.get("pass") is True or review.get("status") == "PASS"
        )
        if not review_passed:
            issues.append(f"visual-qa.json review {key} must be a structured PASS")
            continue
        reviewer = str(review.get("reviewer_id") or review.get("reviewer") or "").strip()
        evidence = str(review.get("evidence") or "").strip()
        if not reviewer:
            issues.append(f"visual-qa.json review {key} must name its reviewer")
        elif reviewer in reviewers:
            issues.append("visual-qa.json post-generation reviews must use independent reviewers")
        reviewers.add(reviewer)
        if len(evidence) < 20:
            issues.append(f"visual-qa.json review {key} needs concrete evidence")

    for source_slide in quarantine_slides:
        number = int(source_slide["slide"])
        for output_format, expected in source_slide["native_outputs"].items():
            binding = _qa_native_output_binding(visual_qa, number, output_format)
            if not binding:
                issues.append(f"slide {number} {output_format} is missing exact-image QA binding")
                continue
            if binding.get("sha256") != expected["sha256"]:
                issues.append(f"slide {number} {output_format} QA hash is stale")
            if binding.get("width") != expected["width"] or binding.get("height") != expected["height"]:
                issues.append(f"slide {number} {output_format} QA dimensions are stale")

        anatomy_root = _qa_check_slide_record(visual_qa, "anatomy_inventory", number)
        entity_root = _qa_check_slide_record(visual_qa, "scene_entity_integrity", number)
        richness_root = _qa_check_slide_record(visual_qa, "visual_richness", number)
        for output_format, expected_asset in source_slide["native_outputs"].items():
            label = f"slide {number} {output_format}"
            anatomy = _qa_format_evidence(anatomy_root, output_format)
            if not anatomy:
                issues.append(f"{label} requires format-specific anatomy_inventory evidence")
            else:
                for count_key in ("expected_arms", "observed_arms", "expected_hands", "observed_hands"):
                    if not isinstance(anatomy.get(count_key), int):
                        issues.append(f"{label} anatomy_inventory requires integer {count_key}")
                if anatomy.get("expected_arms") != anatomy.get("observed_arms"):
                    issues.append(f"{label} observed arms do not match expected arms")
                if anatomy.get("expected_hands") != anatomy.get("observed_hands"):
                    issues.append(f"{label} observed hands do not match expected hands")
                source_asset = anatomy.get("source_asset")
                if not isinstance(source_asset, dict):
                    issues.append(f"{label} anatomy_inventory requires source_asset hash and dimensions")
                else:
                    if source_asset.get("sha256") != expected_asset["sha256"]:
                        issues.append(f"{label} anatomy_inventory source_asset hash is stale")
                    if (
                        source_asset.get("width") != expected_asset["width"]
                        or source_asset.get("height") != expected_asset["height"]
                    ):
                        issues.append(f"{label} anatomy_inventory source_asset dimensions are stale")
                hands = anatomy.get("visible_hands")
                if not isinstance(hands, list) or len(hands) != anatomy.get("observed_hands"):
                    issues.append(f"{label} anatomy_inventory must inventory every observed hand")
                else:
                    for index, hand in enumerate(hands, start=1):
                        if not isinstance(hand, dict):
                            issues.append(f"{label} hand {index} must be structured")
                            continue
                        for key in ("owner", "side", "action"):
                            if not str(hand.get(key) or "").strip():
                                issues.append(f"{label} hand {index} must name {key}")
                        if hand.get("side") not in {"left", "right"}:
                            issues.append(f"{label} hand {index} must identify left or right side")
                        if hand.get("story_required") is not True:
                            issues.append(f"{label} hand {index} is not required by the locked scene")
                        if hand.get("attachment_visible") is not True:
                            issues.append(f"{label} hand {index} is not visibly attached")
                        if len(str(hand.get("attachment_evidence") or "").strip()) < 12:
                            issues.append(f"{label} hand {index} needs wrist/forearm attachment evidence")
                        if "contact_object" not in hand:
                            issues.append(f"{label} hand {index} must record contact_object, including null")
                        if hand.get("contact_geometry_pass") is not True:
                            issues.append(f"{label} hand {index} fails hand-object contact geometry")
                        if len(str(hand.get("occlusion_evidence") or "").strip()) < 12:
                            issues.append(f"{label} hand {index} needs concrete contact/occlusion evidence")
                        if hand.get("solid_object_intersection") is not False:
                            issues.append(f"{label} hand {index} intersects a solid object")
                        if hand.get("edge_entry_unexplained") is not False:
                            issues.append(f"{label} hand {index} has an unexplained edge entry")
                for defect_key in ("unexpected_limbs", "duplicated_limbs"):
                    defects = anatomy.get(defect_key)
                    if not isinstance(defects, list):
                        issues.append(f"{label} anatomy_inventory requires {defect_key} list")
                    elif defects:
                        issues.append(f"{label} anatomy_inventory reports {defect_key}")
                if anatomy.get("malformed_fingers") not in (False, []):
                    issues.append(f"{label} anatomy_inventory reports malformed_fingers")

            entity = _qa_format_evidence(entity_root, output_format)
            if not entity:
                issues.append(f"{label} requires format-specific scene_entity_integrity evidence")
            else:
                _validate_format_source_asset(
                    entity,
                    expected_asset,
                    label=label,
                    check_name="scene_entity_integrity",
                    issues=issues,
                )
                if entity.get("expected_people") != entity.get("observed_people"):
                    issues.append(f"{label} people/entity inventory does not match")
                for limb in ("arms", "hands"):
                    expected = entity.get(f"expected_{limb}")
                    observed = entity.get(f"observed_{limb}")
                    if not isinstance(expected, int) or not isinstance(observed, int):
                        issues.append(f"{label} scene_entity_integrity requires expected/observed {limb}")
                    elif expected != observed:
                        issues.append(f"{label} scene_entity_integrity {limb} inventory does not match")
                for key in ("unexpected_entities", "unexpected_limbs", "duplicated_limbs"):
                    unexpected = entity.get(key)
                    if not isinstance(unexpected, list):
                        issues.append(f"{label} scene_entity_integrity requires {key} list")
                    elif unexpected:
                        issues.append(f"{label} scene_entity_integrity reports {key}")
                if len(str(entity.get("evidence") or "").strip()) < 20:
                    issues.append(f"{label} scene_entity_integrity needs concrete evidence")

            richness = _qa_format_evidence(richness_root, output_format)
            if not richness:
                issues.append(f"{label} requires format-specific visual_richness evidence")
            else:
                _validate_format_source_asset(
                    richness,
                    expected_asset,
                    label=label,
                    check_name="visual_richness",
                    issues=issues,
                )
                for key in ("foreground", "midground", "background", "focal_action", "cause_effect"):
                    if not str(richness.get(key) or "").strip():
                        issues.append(f"{label} visual_richness requires {key}")
                details = richness.get("story_details")
                if not isinstance(details, list) or not 2 <= len(details) <= 4:
                    issues.append(f"{label} visual_richness requires 2-4 story_details")
                if richness.get("posed_portrait") is not False:
                    issues.append(f"{label} must explicitly reject posed portrait composition")
                if richness.get("decorative_clutter") is not False:
                    issues.append(f"{label} must explicitly reject decorative clutter")

    if include_story_checks:
        checks = visual_qa.get("checks")
        topology = checks.get("spatial_topology") if isinstance(checks, dict) else None
        issues.extend(
            f"visual-qa.json {issue}"
            for issue in validate_spatial_topology_check(
                topology,
                slide_count=len(quarantine_slides),
            )
        )
        readability = (
            checks.get(VISUAL_STORY_READABILITY_KEY)
            if isinstance(checks, dict)
            else None
        )
        if carousel_dir is None:
            issues.append(
                "visual-qa.json story checks require carousel_dir so the persisted format "
                "contract can be verified"
            )
        else:
            review_formats = locked_formats(carousel_dir)
            issues.extend(
                validate_frame_readability(
                    readability,
                    slide_count=len(quarantine_slides),
                    required_formats=review_formats,
                    expected_director_event_fingerprint=director_event_fingerprint(visual_plan),
                    event_a_review_provenance=director_review_provenance(visual_plan),
                    event_a_creator_correction_fingerprint=(
                        director_creator_correction_fingerprint(visual_plan)
                    ),
                    expected_creator_correction_fingerprint=(
                        current_creator_correction_fingerprint(carousel_dir)
                    ),
                    event_a_generation_payload_fingerprint=(
                        director_generation_payload_fingerprint(visual_plan)
                    ),
                    expected_generation_payload_fingerprint=(
                        current_generation_payload_fingerprint(carousel_dir)
                    ),
                    director_author_id=director_author_id(visual_plan),
                    director_reviewer_id=director_reviewer_id(visual_plan),
                    expected_frame_bindings=expected_frame_bindings(
                        carousel_dir,
                        len(quarantine_slides),
                        review_formats,
                    ),
                    package_dir=_quarantine_review_root(
                        carousel_dir,
                        quarantine_slides,
                    ),
                    provenance_package_dir=carousel_dir,
                    require_files=True,
                )
            )
    return issues


def validate_creator_approval(
    approval: dict[str, Any], *, expected_image_set_sha256: str
) -> list[str]:
    issues: list[str] = []
    if approval.get("status") != "APPROVED" or approval.get("approved") is not True:
        issues.append("creator proof approval must be explicitly APPROVED")
    if approval.get("image_set_sha256") != expected_image_set_sha256:
        issues.append("creator proof approval is missing or belongs to a different image set")
    if not str(approval.get("approved_by") or "").strip():
        issues.append("creator proof approval must record approved_by")
    if len(str(approval.get("evidence") or "").strip()) < 8:
        issues.append("creator proof approval must record concrete evidence")
    return issues


def validate_quarantine_integrity(
    slides: list[dict[str, Any]],
    output_formats: tuple[str, ...] | list[str],
    *,
    carousel_dir: Path | None = None,
) -> list[str]:
    issues: list[str] = []
    if carousel_dir is None:
        return [
            "quarantine integrity requires carousel_dir to verify package-contained canonical assets"
        ]
    package_root = Path(carousel_dir).expanduser().resolve()
    quarantine_root = (package_root / QUARANTINE_FOLDER).resolve()
    for slide in slides:
        number = slide.get("slide")
        try:
            slide_number = int(number)
        except (TypeError, ValueError):
            issues.append(f"quarantined slide {number} has an invalid slide number")
            continue
        outputs = slide.get("native_outputs")
        if not isinstance(outputs, dict):
            issues.append(f"quarantined slide {number} has no native_outputs")
            continue
        for output_format in output_formats:
            item = outputs.get(output_format)
            if not isinstance(item, dict):
                issues.append(f"quarantined slide {number} is missing {output_format}")
                continue
            try:
                output_folder = str(format_spec(output_format)["folder"])
            except ValueError:
                issues.append(
                    f"quarantined slide {number} has unsupported format {output_format}"
                )
                continue
            raw_path = Path(str(item.get("path") or "")).expanduser()
            path = raw_path if raw_path.is_absolute() else package_root / raw_path
            canonical = True
            if not str(item.get("path") or "").strip() or ".." in raw_path.parts:
                canonical = False
            try:
                relative = path.resolve().relative_to(quarantine_root)
            except (OSError, ValueError):
                canonical = False
                relative = None
            if relative is not None:
                expected_relative = Path(
                    relative.parts[0] if relative.parts else "",
                    output_folder,
                    f"slide-{slide_number:02d}.png",
                )
                if (
                    len(relative.parts) != 3
                    or not re.fullmatch(r"attempt-\d{2,}", relative.parts[0])
                    or relative != expected_relative
                ):
                    canonical = False
            try:
                lexical_relative = path.absolute().relative_to(package_root)
            except ValueError:
                lexical_relative = None
            if lexical_relative is not None:
                cursor = package_root
                for part in lexical_relative.parts:
                    cursor = cursor / part
                    if cursor.is_symlink():
                        canonical = False
                        break
            if not canonical:
                issues.append(
                    f"quarantined slide {number} {output_format} path must be the canonical package-contained quarantine asset"
                )
                continue
            if not path.is_file():
                issues.append(f"quarantined slide {number} {output_format} file is missing")
                continue
            image_bytes = path.read_bytes()
            if sha256_bytes(image_bytes) != item.get("sha256"):
                issues.append(f"quarantined slide {number} {output_format} hash is stale")
            try:
                dimensions = image_dimensions(image_bytes)
            except (RuntimeError, ValueError):
                issues.append(f"quarantined slide {number} {output_format} is not a readable image")
                continue
            if dimensions["width"] != item.get("width") or dimensions["height"] != item.get("height"):
                issues.append(f"quarantined slide {number} {output_format} dimensions are stale")
    return issues


def identity_consistency_gate_reason(carousel_dir: Path) -> str | None:
    review_path = carousel_dir / "identity-consistency-review.json"
    if not review_path.exists():
        return "identity-consistency-review.json is required before Codex built-in image generation."
    review = load_json(review_path)
    if review.get("status") != "PASS":
        issues = review.get("issues") or ["identity consistency review did not pass"]
        return "identity-consistency-review.json did not pass: " + "; ".join(str(issue) for issue in issues)
    return None


def visual_plan_quality_gate_reason(carousel_dir: Path) -> str | None:
    review_path = carousel_dir / "visual-plan-quality.json"
    if not review_path.exists():
        return "visual-plan-quality.json is required as the per-slide pre-generation visual screen before Codex built-in image generation."
    review = load_json(review_path)
    if review.get("status") != "PASS" or not review.get("can_generate"):
        issues = review.get("issues") or ["pre-generation visual screen did not pass"]
        return "visual-plan-quality.json did not pass: " + "; ".join(str(issue) for issue in issues)
    slides_path = carousel_dir / "slides.json"
    expected_slides: Any = []
    if slides_path.exists():
        try:
            expected_slides = json.loads(slides_path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            expected_slides = []
    slide_records = (
        expected_slides
        if isinstance(expected_slides, list)
        else expected_slides.get("slides", [])
        if isinstance(expected_slides, dict)
        else []
    )
    try:
        generation_fingerprint = current_generation_payload_fingerprint(carousel_dir)
    except ValueError as exc:
        return str(exc)
    director_issues = validate_director_storyboard(
        review,
        slide_count=len(slide_records),
        expected_slides=expected_slides,
        expected_formats=locked_formats(carousel_dir),
        expected_format_contract_fingerprint=locked_format_contract_fingerprint(
            carousel_dir
        ),
        expected_creator_correction_fingerprint=(
            current_creator_correction_fingerprint(carousel_dir)
        ),
        expected_generation_payload_fingerprint=generation_fingerprint,
        provenance_package_dir=carousel_dir,
    )
    if director_issues:
        return "visual-plan-quality.json director story check did not pass: " + "; ".join(
            director_issues
        )
    return None


def existing_paths(raw_paths: list[Any]) -> list[Path]:
    paths: list[Path] = []
    seen: set[str] = set()
    for raw in raw_paths:
        path = Path(str(raw)).expanduser()
        marker = str(path)
        if marker not in seen and path.exists():
            paths.append(path)
            seen.add(marker)
    return paths


def slide_source_paths(slide: dict[str, Any]) -> list[Path]:
    return existing_paths(slide.get("source_images", []))


def generator_prompt_text(slide_prompt: dict[str, Any], output_format: str) -> str:
    visual = slide_prompt.get("visual") or slide_prompt.get("scene")
    if not visual:
        visual = extract_scene_summary(str(slide_prompt["prompt"]))
    return compile_image_prompt(
        int(slide_prompt["slide"]),
        int(slide_prompt.get("slide_count") or 0) or 1,
        str(slide_prompt["text"]),
        str(visual),
        output_format,
        str(slide_prompt.get("style") or "premium hand-drawn romantic watercolor-and-ink illustration on warm ivory paper with visible paper grain"),
        str(slide_prompt.get("negative_prompt") or "No photorealism, no 3D, no stock couple, no quote card."),
        pose=str(slide_prompt.get("pose") or slide_prompt.get("body_language") or ""),
        wardrobe=str(slide_prompt.get("wardrobe") or ""),
        props=str(slide_prompt.get("props") or ""),
        background=str(slide_prompt.get("background") or ""),
        emotion=str(slide_prompt.get("emotion") or ""),
        hand_map=slide_prompt.get("hand_map"),
        spatial_topology=slide_prompt.get("spatial_topology_contract"),
        visual_richness=slide_prompt.get("visual_richness_contract"),
    )


def reject_non_codex_builtin_sources(carousel_dir: Path, generated_paths_by_format: dict[str, list[str | Path]]) -> None:
    carousel_root = carousel_dir.expanduser().resolve()
    forbidden_markers = {
        "tmp-generated/local-native",
        "tmp-generated\\local-native",
        "source-generated-local",
    }
    rejected: list[str] = []
    for paths in generated_paths_by_format.values():
        for raw_path in paths:
            path = Path(raw_path).expanduser()
            marker = str(path)
            resolved_marker = str(path.resolve()) if path.exists() else marker
            normalized = marker.replace("\\", "/")
            normalized_resolved = resolved_marker.replace("\\", "/")
            inside_carousel = False
            try:
                path.resolve().relative_to(carousel_root)
                inside_carousel = True
            except (FileNotFoundError, ValueError):
                inside_carousel = False
            if any(token in normalized or token in normalized_resolved for token in forbidden_markers):
                rejected.append(marker)
            elif inside_carousel and "model-native-source" not in normalized_resolved:
                rejected.append(marker)
    if rejected:
        raise ValueError(
            "Codex built-in packaging requires real external/generated model sources, not local placeholder "
            "or renderer outputs. Rejected source path(s): "
            + ", ".join(rejected)
        )


def write_blocked_status(carousel_dir: Path, reason: str) -> dict[str, Any]:
    return write_generation_state(
        carousel_dir,
        status=GenerationStatus.BLOCKED,
        backend=BACKEND,
        generation_mode=GENERATION_MODE,
        slide_count=infer_slide_count(carousel_dir),
        reason=reason,
    )


def infer_slide_count(carousel_dir: Path) -> int:
    for filename in ("slides.json", "prompt-pack.json"):
        path = carousel_dir / filename
        if not path.exists():
            continue
        try:
            payload = load_json(path)
        except (json.JSONDecodeError, OSError):
            continue
        if isinstance(payload, list):
            return len(payload)
        slides = payload.get("slides")
        if isinstance(slides, list):
            return len(slides)
    return 0


def proof_slide_from_gate(proof_gate: str | None, slides: list[dict[str, Any]]) -> int:
    if proof_gate:
        match = re.search(r"\bslide\s+0*(\d+)\b", proof_gate, flags=re.IGNORECASE)
        if match:
            requested = int(match.group(1))
            if any(int(slide.get("slide", 0) or 0) == requested for slide in slides):
                return requested
    if slides:
        return int(slides[min(3, len(slides) - 1)].get("slide", 1))
    return 1


def write_handoff_blocker(carousel_dir: Path, result: dict[str, Any], proof_gate: str | None = None) -> None:
    slides = result.get("slides", [])
    requested_formats = result.get("requested_formats") or list(locked_formats(carousel_dir))
    proof_slide = result.get("requested_proof_slide") or proof_slide_from_gate(proof_gate, slides)
    slide_count = int(result.get("slide_count") or len(slides))
    proof_copy = ""
    proof_generator_prompt = ""
    for slide in slides:
        if int(slide.get("slide", 0) or 0) == proof_slide:
            proof_copy = str(slide.get("copy", ""))
            generator_prompt_files = slide.get("generator_prompt_files") or {}
            for output_format in requested_formats:
                if generator_prompt_files.get(output_format):
                    proof_generator_prompt = str(generator_prompt_files[output_format])
                    break
            if not proof_generator_prompt and generator_prompt_files:
                proof_generator_prompt = str(next(iter(generator_prompt_files.values())))
            break
    prompt_handoff_lines = []
    for output_format in requested_formats:
        output_spec = NATIVE_OUTPUT_FORMATS[output_format]
        prompt_path = carousel_dir / "codex-image-prompts" / format_prompt_dir_name(output_format)
        prompt_handoff_lines.append(f"- {output_spec['label']} prompts: `{prompt_path}`")
    final_image_lines = [
        (
            f"- `{format_spec(output_format)['folder']}/slide-01.png` through "
            f"`slide-{slide_count:02d}.png` ({NATIVE_OUTPUT_FORMATS[output_format]['label']})"
        )
        for output_format in requested_formats
    ]
    blocker = [
        "# Image Generation Blocker",
        "",
        "status: HANDOFF_READY_IMAGES_PENDING",
        "",
        "No final PNGs were generated by this step.",
        "",
        "This package is ready for Codex built-in image generation, but the CLI can only",
        "prepare prompt files and provenance expectations. It cannot call the interactive",
        "built-in image generator or produce identity-referenced final artwork by itself.",
        "",
        "Prompt handoff:",
        "",
        *prompt_handoff_lines,
        f"- Paste-ready generator prompts: `.prompt.txt` files beside each `.md` handoff file.",
        "",
        "Final images still required:",
        "",
        *final_image_lines,
        "",
        "Rules:",
        "",
        "- generate only the current-request formats listed above;",
        "- generate every requested aspect ratio natively; do not derive one from another;",
        "- use the watercolor-and-ink master prompt in each paste-ready `.prompt.txt`;",
        "- use identity references as actual image inputs;",
        "- preserve exact slide copy and `@a.storyof.two` inside the generated image;",
        "- package generated sources with `scripts/package_generated_carousel.py`.",
    ]
    if proof_copy:
        blocker.extend(
            [
                "",
                "Proof-first recommendation:",
                "",
                f"- slide {proof_slide:02d}: `{proof_copy}`",
            ]
        )
        if proof_generator_prompt:
            blocker.append(f"- paste only this proof prompt after attaching references: `{proof_generator_prompt}`")
    (carousel_dir / "image-generation-blocker.md").write_text("\n".join(blocker) + "\n", encoding="utf-8")


def requested_native_output_formats(formats: list[str] | None) -> list[str]:
    return list(normalize_requested_formats(formats))


def expected_file_for_format(carousel_dir: Path, output_format: str, number: int) -> Path:
    return expected_output_path(carousel_dir, output_format, number)


def clean_packaged_output_files(carousel_dir: Path, slide_numbers: list[int]) -> None:
    for folder_name in [format_spec(value)["folder"] for value in normalize_requested_formats([INSTAGRAM_POST_FORMAT, REELS_STORIES_FORMAT, SQUARE_FORMAT])]:
        folder = carousel_dir / folder_name
        folder.mkdir(parents=True, exist_ok=True)
        for path in folder.glob("slide-*.png"):
            path.unlink()

    source_dir = carousel_dir / "final" / "model-native-source"
    if not source_dir.exists():
        return
    for number in slide_numbers:
        for prefix in [format_spec(value)["source_prefix"] for value in normalize_requested_formats([INSTAGRAM_POST_FORMAT, REELS_STORIES_FORMAT, SQUARE_FORMAT])]:
            source_path = source_dir / f"{prefix}-slide-{number:02d}.png"
            if source_path.exists():
                source_path.unlink()


def quarantine_generated_sources(
    carousel_dir: Path,
    *,
    slides: list[dict[str, Any]],
    generated_paths_by_format: dict[str, list[str | Path]],
    retry_count: int,
    output_formats: tuple[str, ...],
) -> list[dict[str, Any]]:
    """Copy model results into an internal, non-publishable exact-image quarantine."""

    attempt_dir = quarantine_dir(carousel_dir, retry_count)
    if attempt_dir.exists():
        shutil.rmtree(attempt_dir)
    attempt_dir.mkdir(parents=True, exist_ok=True)
    records: list[dict[str, Any]] = []
    for index, slide_prompt in enumerate(slides):
        number = int(slide_prompt["slide"])
        native_outputs: dict[str, Any] = {}
        for output_format in output_formats:
            source_path = Path(generated_paths_by_format[output_format][index]).expanduser()
            if not source_path.exists():
                raise FileNotFoundError(f"Missing Codex generated image: {source_path}")
            image_bytes = source_path.read_bytes()
            dimensions = require_native_source_dimensions(
                image_bytes=image_bytes,
                output_format=output_format,
                slide_number=number,
                path=source_path,
            )
            format_dir = attempt_dir / str(format_spec(output_format)["folder"])
            format_dir.mkdir(parents=True, exist_ok=True)
            target = format_dir / f"slide-{number:02d}.png"
            target.write_bytes(image_bytes)
            native_outputs[output_format] = {
                "path": str(target),
                "sha256": sha256_bytes(image_bytes),
                "width": dimensions["width"],
                "height": dimensions["height"],
            }
        records.append(
            {
                "slide": number,
                "copy": slide_prompt["text"],
                "status": GenerationStatus.GENERATED_QUARANTINED.value,
                "native_outputs": native_outputs,
            }
        )
    return records


def format_prompt_dir_name(output_format: str) -> str:
    return str(format_spec(output_format)["prompt_folder"])


def image_dimensions(image_bytes: bytes) -> dict[str, Any]:
    source = decode_png(image_bytes)
    source_height, source_width = source.shape[:2]
    return {
        "width": source_width,
        "height": source_height,
        "aspect": round(source_width / source_height, 4),
    }


def target_size_for_format(output_format: str) -> tuple[int, int]:
    width, height = format_spec(output_format)["target_size"]
    return int(width), int(height)


def source_size_for_format(output_format: str) -> tuple[int, int]:
    raw_size = format_spec(output_format)["source_size"]
    return int(raw_size[0]), int(raw_size[1])


def allowed_source_sizes_for_format(output_format: str) -> list[tuple[int, int]]:
    return [
        (int(width), int(height))
        for width, height in format_spec(output_format)["allowed_source_sizes"]
    ]


def require_native_source_dimensions(
    *,
    image_bytes: bytes,
    output_format: str,
    slide_number: int,
    path: Path,
) -> dict[str, Any]:
    dimensions = image_dimensions(image_bytes)
    actual_size = (dimensions["width"], dimensions["height"])
    expected_sizes = allowed_source_sizes_for_format(output_format)
    if actual_size not in expected_sizes:
        label = NATIVE_OUTPUT_FORMATS[output_format]["label"]
        expected = " or ".join(f"{width}x{height}" for width, height in expected_sizes)
        raise ValueError(
            f"Slide {slide_number} {label} native source dimensions are "
            f"{dimensions['width']}x{dimensions['height']}; expected {expected}. "
            f"Regenerate {path} at an approved source size instead of cropping, padding, "
            "stretching, or containing a wrong-size source."
        )
    return dimensions


def normalize_for_upload(image_bytes: bytes, width: int, height: int) -> tuple[bytes, dict[str, Any], str, str | None]:
    import cv2

    dimensions = image_dimensions(image_bytes)
    source = decode_png(image_bytes)
    source_height, source_width = source.shape[:2]
    if (source_width, source_height) == (width, height):
        return (
            image_bytes,
            dimensions,
            "source already matches exact native upload size",
            None,
        )

    if source_width * height != source_height * width:
        raise RuntimeError(
            "Generated source aspect ratio does not match the upload target: "
            f"source={source_width}x{source_height}, target={width}x{height}."
        )

    interpolation = cv2.INTER_AREA if source_width >= width and source_height >= height else cv2.INTER_LANCZOS4
    resized = cv2.resize(source, (width, height), interpolation=interpolation)
    ok, encoded = cv2.imencode(".png", resized)
    if not ok:
        raise RuntimeError("Could not encode normalized native upload PNG.")
    return (
        encoded.tobytes(),
        dimensions,
        f"proportional export from {source_width}x{source_height} to exact {width}x{height}",
        None,
    )


def infer_workspace_root_from_carousel_dir(carousel_dir: Path) -> Path:
    resolved = carousel_dir.expanduser().resolve()
    for candidate in [resolved, *resolved.parents]:
        if (candidate / "AGENTS.md").exists() or (candidate / "config" / "carousel_style_contract.json").exists():
            return candidate

    for parent in resolved.parents:
        if parent.name == "out":
            return parent.parent
        if parent.name == "carousels" and parent.parent.name == "output":
            return parent.parent.parent

    if resolved.parent != resolved:
        return resolved.parent
    return resolved


def build_handoff_markdown(
    *,
    slide_number: int,
    output_label: str,
    prompt_filename: str | Path,
    reference_paths: list[str | Path],
    exact_slide_copy: str,
    expected_file: str | Path,
    generated_source: str | Path,
    aspect_ratio: str | None = None,
    source_pixel_size: str | None = None,
    upload_pixel_size: str | None = None,
    native_output_rule: str | None = None,
    identity_dossier_path: str | None = None,
    identity_preflight_path: str | None = None,
) -> str:
    prompt_path = Path(str(prompt_filename))
    prompt_display = prompt_path.name
    lines = [
        f"# Codex Built-In Image Prompt - Slide {slide_number:02d} - {output_label}",
        "",
        "Use the Codex built-in image generator. Do not use external API keys or external image API clients.",
        "",
        "## How To Use This File",
        "",
        "- This markdown file is the Codex handoff/checklist, not the exact text to paste into the image model.",
        f"- Paste the full prompt from `{prompt_display}` into the image generator.",
        f"- Prompt file path: `{prompt_filename}`.",
        "- After generation, package the returned image with `scripts/package_generated_carousel.py` or the proof-specific workflow.",
        "",
        "## Prompt Source",
        "",
        f"Paste the full prompt from `{prompt_display}`. This markdown file intentionally does not duplicate the prompt body, so `.prompt.txt` remains the only generation prompt source.",
        "",
        "## Native Output Contract",
        "",
        f"- Native output format: {output_label}",
    ]
    if source_pixel_size:
        lines.append(
            f"- Required generated source size: {source_pixel_size} px "
            "(mandatory; generate this source size, not just this ratio)"
        )
    if upload_pixel_size:
        lines.append(f"- Required final upload/export size: {upload_pixel_size} px")
    if aspect_ratio:
        lines.append(f"- Required aspect ratio: {aspect_ratio}")
    lines.extend(
        [
            f"- Required final file: `{expected_file}`",
        ]
    )
    if native_output_rule:
        lines.append(f"- {native_output_rule}")
    lines.extend(
        [
            "- Generate this format as its own artwork. Do not create it by resizing another social format.",
            "",
            "## Hard Gate",
            "",
            "- The paste-ready `.prompt.txt` must include the @a.storyof.two watercolor-and-ink master prompt structure.",
            "- Before any slide generation, read `identity-generation-preflight.md` and load/view `identity-face-contact-sheet.jpg`.",
            "- Preserve the carousel story-director spine embedded in `prompt-pack.json`: hook, setup, proof, bridge, active Zuv role, earned ending, and send/save reason.",
            "- Before calling image generation, load/view every identity reference listed below so they are actual image inputs in the Codex context.",
            "- Use the selected identity images as face, hair, expression, body proportion, posture, and relationship-energy references.",
            "- Do not accept generic Aachu/Zuv faces.",
            "- Keep the exact slide copy and tiny `@a.storyof.two` brandmark inside the generated image.",
            "",
            "## Identity Dossier",
            "",
            f"- Dossier: {identity_dossier_path or 'missing'}",
            f"- Preflight: {identity_preflight_path or 'missing'}",
            "",
            "## Actual Image Inputs",
            "",
        ]
    )
    if reference_paths:
        lines.extend(f"- {path}" for path in reference_paths)
    else:
        lines.append("- none recorded")
    lines.extend(
        [
            "",
            "## Exact Slide Copy",
            "",
            exact_slide_copy,
            "",
            "## Expected Output",
            "",
            f"- Save packaged final to `{expected_file}`.",
            f"- Source provenance should point to the Codex generated image copied into `{generated_source}`.",
        ]
    )
    return "\n".join(lines) + "\n"


def prompt_file_text(
    *,
    carousel_dir: Path,
    slide_prompt: dict[str, Any],
    output_format: str,
    generator_prompt_path: Path,
    dossier_paths: list[Path],
    identity_dossier_path: str | None,
    identity_preflight_path: str | None,
    identity_paths: list[Path],
    source_paths: list[Path],
    style_paths: list[Path],
) -> str:
    number = int(slide_prompt["slide"])
    text = slide_prompt["text"]
    output_spec = NATIVE_OUTPUT_FORMATS[output_format]
    expected_file = expected_output_path(carousel_dir, output_format, number)
    generated_source = expected_source_path(carousel_dir, output_format, number)
    reference_paths: list[Path] = []
    reference_paths.extend(dossier_paths)
    reference_paths.extend(identity_paths)
    reference_paths.extend(source_paths)
    reference_paths.extend(style_paths)
    return build_handoff_markdown(
        slide_number=number,
        output_label=output_spec["label"],
        prompt_filename=generator_prompt_path,
        reference_paths=reference_paths,
        exact_slide_copy=str(text),
        expected_file=expected_file,
        generated_source=generated_source,
        aspect_ratio=output_spec["aspect_ratio"],
        source_pixel_size=output_spec.get("source_size_label") or output_spec["upload_size"],
        upload_pixel_size=output_spec["upload_size"],
        native_output_rule=native_output_contract(locked_formats(carousel_dir))["rule"],
        identity_dossier_path=identity_dossier_path,
        identity_preflight_path=identity_preflight_path,
    )


def prepare_codex_builtin_image_generation(
    carousel_dir: Path,
    *,
    proof_slide: int | None = None,
    formats: list[str] | None = None,
) -> dict[str, Any]:
    carousel_dir = carousel_dir.expanduser()
    prompt_dir = carousel_dir / PROMPT_HANDOFF_ACTIVE_FOLDER
    prompt_staging_dir = carousel_dir / PROMPT_HANDOFF_STAGING_FOLDER
    # A previous active set is executable by a human or agent. Invalidate it
    # before reading any mutable prerequisite so a blocked recompilation can
    # never leave stale prompts available for use.
    remove_path_without_following(prompt_dir)
    remove_path_without_following(prompt_staging_dir)
    if formats is not None:
        format_contract = write_format_contract(
            carousel_dir,
            formats,
            source="codex_builtin_current_request",
            replace=True,
        )
    elif (carousel_dir / FORMAT_CONTRACT_FILENAME).exists():
        format_contract = load_format_contract(carousel_dir)
    else:
        format_contract = write_format_contract(
            carousel_dir,
            None,
            source="codex_builtin_post_default",
        )
    output_formats = list(normalize_requested_formats(format_contract["requested_formats"]))
    generation_capability = write_generation_capability(carousel_dir)
    prompt_pack = load_json(carousel_dir / "prompt-pack.json")
    slides = prompt_pack.get("slides", [])
    if not slides:
        raise ValueError("prompt-pack.json does not include slide prompts.")
    total_prompt_pack_slide_count = len(slides)
    if proof_slide is not None:
        slides = [slide for slide in slides if int(slide.get("slide", 0) or 0) == proof_slide]
        if not slides:
            raise ValueError(f"proof_slide {proof_slide} is not present in prompt-pack.json.")

    visual_quality_reason = visual_plan_quality_gate_reason(carousel_dir)
    if visual_quality_reason:
        return write_blocked_status(carousel_dir, visual_quality_reason)

    identity_reason = identity_consistency_gate_reason(carousel_dir)
    if identity_reason:
        return write_blocked_status(carousel_dir, identity_reason)

    style_consistency_reason = house_style_consistency_gate_reason(prompt_pack)
    if style_consistency_reason:
        return write_blocked_status(carousel_dir, style_consistency_reason)

    layer_e_reason = layer_e_gate_reason(carousel_dir)
    if layer_e_reason:
        return write_blocked_status(carousel_dir, layer_e_reason)

    dossier_paths = existing_paths(prompt_pack.get("identity_dossier_reference_images", []))
    identity_paths = existing_paths(prompt_pack.get("identity_reference_images", []))
    if not dossier_paths:
        return write_blocked_status(
            carousel_dir,
            "Codex built-in image generation requires identity-face-contact-sheet.jpg as an actual image input.",
        )
    if not identity_paths:
        return write_blocked_status(
            carousel_dir,
            "Codex built-in image generation requires selected identity images as actual image inputs.",
        )

    style_paths = [
        path
        for path in existing_reference_paths({"style_reference_images": prompt_pack.get("style_reference_images", [])})
        if path not in identity_paths
    ]
    prompt_staging_dir.parent.mkdir(parents=True, exist_ok=True)
    prompt_staging_dir.mkdir()
    handoff_complete = False
    try:
        records = []
        slide_plans = load_json(carousel_dir / "slides.json")
        for slide_prompt in slides:
            number = int(slide_prompt["slide"])
            slide_plan = next(
                (
                    item
                    for item in slide_plans
                    if int(item.get("slide", 0) or 0) == number
                ),
                {},
            )
            source_paths = slide_source_paths(slide_plan)
            active_prompt_files: dict[str, Path] = {}
            staging_prompt_files: dict[str, Path] = {}
            for output_format in output_formats:
                format_dir = format_prompt_dir_name(output_format)
                active_prompt_files[output_format] = (
                    prompt_dir / format_dir / f"slide-{number:02d}.md"
                )
                staging_prompt_files[output_format] = (
                    prompt_staging_dir / format_dir / f"slide-{number:02d}.md"
                )
            for output_format, staging_prompt_path in staging_prompt_files.items():
                staging_prompt_path.parent.mkdir(parents=True, exist_ok=True)
                staging_generator_path = staging_prompt_path.with_suffix(".prompt.txt")
                staging_generator_path.write_text(
                    generator_prompt_text(slide_prompt, output_format),
                    encoding="utf-8",
                )
                gate = check_prompt_constraints(
                    staging_generator_path,
                    expected_text=str(slide_prompt["text"]),
                )
                if gate.status != "PASS":
                    return write_blocked_status(
                        carousel_dir,
                        (
                            f"Compiled prompt constraints failed for slide {number:02d} "
                            f"{format_prompt_dir_name(output_format)}: {gate.reason}"
                        ),
                    )
                active_generator_path = active_prompt_files[output_format].with_suffix(
                    ".prompt.txt"
                )
                staging_prompt_path.write_text(
                    prompt_file_text(
                        carousel_dir=carousel_dir,
                        slide_prompt=slide_prompt,
                        output_format=output_format,
                        generator_prompt_path=active_generator_path,
                        dossier_paths=dossier_paths,
                        identity_dossier_path=prompt_pack.get("identity_dossier_path"),
                        identity_preflight_path=prompt_pack.get("identity_generation_preflight_path"),
                        identity_paths=identity_paths,
                        source_paths=source_paths,
                        style_paths=style_paths,
                    ),
                    encoding="utf-8",
                )
            first_output_format = output_formats[0]
            first_prompt_path = active_prompt_files[first_output_format]
            records.append(
                {
                    "slide": number,
                    "copy": slide_prompt["text"],
                    "status": "awaiting_codex_builtin_image",
                    "generation_mode": GENERATION_MODE,
                    "backend": BACKEND,
                    "prompt_file": first_prompt_path.relative_to(carousel_dir).as_posix(),
                    "prompt_files": {
                        key: path.relative_to(carousel_dir).as_posix()
                        for key, path in active_prompt_files.items()
                    },
                    "generator_prompt_files": {
                        key: path.with_suffix(".prompt.txt").relative_to(carousel_dir).as_posix()
                        for key, path in active_prompt_files.items()
                    },
                    "expected_file": expected_output_relative_path(first_output_format, number),
                    "expected_files": {
                        output_format: expected_output_relative_path(output_format, number)
                        for output_format in output_formats
                    },
                    "identity_dossier_reference_images": [str(path) for path in dossier_paths],
                    "identity_reference_images": [str(path) for path in identity_paths],
                    "story_reference_images": [str(path) for path in source_paths],
                    "style_reference_images": [str(path) for path in style_paths],
                }
            )

        compiled_handoff = build_compiled_prompt_handoff(
            carousel_dir,
            slide_numbers=[int(slide["slide"]) for slide in slides],
            output_formats=output_formats,
            prompt_source_root=prompt_staging_dir,
        )
        # Same-filesystem rename is the exposure point: no active prompt path
        # exists until every prompt and markdown file has passed compilation.
        prompt_staging_dir.replace(prompt_dir)
        result = write_generation_state(
            carousel_dir,
            status=GenerationStatus.HANDOFF_READY,
            backend=BACKEND,
            generation_mode=GENERATION_MODE,
            slide_count=total_prompt_pack_slide_count,
            reason="Prompt files are ready; final PNGs still require Codex built-in image generation.",
            slides=records,
            extra={
                "proof_gate": prompt_pack.get("proof_gate"),
                "requested_proof_slide": proof_slide,
                "requested_formats": output_formats,
                "native_output_contract": native_output_contract(output_formats),
                "generation_capability": generation_capability,
                "prompt_dir": PROMPT_HANDOFF_ACTIVE_FOLDER,
                "compiled_prompt_handoff": compiled_handoff,
                "identity_reference_requirement": (
                    "Load/view identity-face-contact-sheet.jpg and selected identity images before every "
                    "Codex image generation call; the final art must preserve Aachu/Zuv face structure."
                ),
            },
        )
        write_handoff_blocker(carousel_dir, result, prompt_pack.get("proof_gate"))
        handoff_complete = True
        return result
    finally:
        remove_path_without_following(prompt_staging_dir)
        if not handoff_complete:
            remove_path_without_following(prompt_dir)


def package_codex_builtin_outputs(
    carousel_dir: Path,
    *,
    generated_paths: list[str | Path] | None = None,
    generated_paths_by_format: dict[str, list[str | Path]] | None = None,
    refresh_quality: bool = False,
    visual_qa_path: str | Path | None = None,
    creator_approval_path: str | Path | None = None,
    promote_existing_quarantine: bool = False,
) -> dict[str, Any]:
    carousel_dir = carousel_dir.expanduser()
    output_formats = locked_formats(carousel_dir)
    output_contract = native_output_contract(output_formats)
    prompt_pack = load_json(carousel_dir / "prompt-pack.json")
    slides = prompt_pack.get("slides", [])
    if generated_paths is not None:
        raise ValueError(
            "Codex built-in packaging requires generated_paths_by_format keyed by the "
            "current-request format contract."
        )
    if not generated_paths_by_format and not promote_existing_quarantine:
        raise ValueError("generated_paths_by_format is required.")
    expected_formats = set(output_formats)
    compiled_handoff: dict[str, Any] | None = None
    if not promote_existing_quarantine:
        supplied_formats = set(generated_paths_by_format or {})
        if supplied_formats != expected_formats:
            raise ValueError(
                "generated_paths_by_format must contain exactly: "
                + ", ".join(output_formats)
            )
        for format_key, paths in (generated_paths_by_format or {}).items():
            if len(paths) != len(slides):
                raise ValueError(f"Expected {len(slides)} {format_key} image paths, got {len(paths)}.")
        reject_non_codex_builtin_sources(carousel_dir, generated_paths_by_format or {})
        state_path = carousel_dir / "image-generation.json"
        try:
            handoff_state = load_json(state_path)
        except (OSError, json.JSONDecodeError):
            handoff_state = None
        handoff_issues = compiled_prompt_handoff_integrity_issues(
            carousel_dir,
            state=handoff_state,
            slides=slides,
            output_formats=list(output_formats),
        )
        if handoff_issues:
            remove_path_without_following(carousel_dir / PROMPT_HANDOFF_ACTIVE_FOLDER)
            reason = "Compiled prompt handoff integrity failed: " + "; ".join(handoff_issues)
            if isinstance(handoff_state, dict) and handoff_state.get("status") in {
                GenerationStatus.GENERATED_QUARANTINED.value,
                GenerationStatus.QA_PASS_CANDIDATE.value,
                GenerationStatus.CREATOR_APPROVED_PROOF.value,
                GenerationStatus.REJECTED_SPATIAL_INTEGRITY.value,
            }:
                raise ValueError(reason)
            return write_blocked_status(carousel_dir, reason)
        compiled_handoff = handoff_state["compiled_prompt_handoff"]

    visual_quality_reason = visual_plan_quality_gate_reason(carousel_dir)
    if visual_quality_reason:
        return write_blocked_status(carousel_dir, visual_quality_reason)

    identity_reason = identity_consistency_gate_reason(carousel_dir)
    if identity_reason:
        return write_blocked_status(carousel_dir, identity_reason)

    slide_numbers = [int(slide.get("slide", 0) or 0) for slide in slides]
    current_proof_status: GenerationStatus | None = None
    if promote_existing_quarantine:
        state_path = carousel_dir / "image-generation.json"
        if not state_path.exists():
            raise ValueError("No quarantined generation state exists to promote.")
        current_state = load_json(state_path)
        existing_compiled_handoff = current_state.get("compiled_prompt_handoff")
        if isinstance(existing_compiled_handoff, dict):
            compiled_handoff = existing_compiled_handoff
        current_proof_status = GenerationStatus(current_state.get("status"))
        if current_state.get("status") not in {
            GenerationStatus.GENERATED_QUARANTINED.value,
            GenerationStatus.QA_PASS_CANDIDATE.value,
            GenerationStatus.CREATOR_APPROVED_PROOF.value,
        }:
            raise ValueError("Current generation state is not eligible for quarantined promotion.")
        quarantine_records = current_state.get("slides") or []
        retry_count = int(current_state.get("retry_count", 0))
        quarantine_issues = validate_quarantine_integrity(
            quarantine_records,
            output_formats,
            carousel_dir=carousel_dir,
        )
        if quarantine_issues:
            return write_generation_state(
                carousel_dir,
                status=GenerationStatus.BLOCKED_VISUAL_QA,
                backend=BACKEND,
                generation_mode=GENERATION_MODE,
                slide_count=len(slides),
                reason="Quarantined pixels changed or disappeared; prior QA and approval are invalid.",
                slides=quarantine_records,
                extra={
                    "proof_state": GenerationStatus.BLOCKED_VISUAL_QA.value,
                    "retry_count": retry_count,
                    "max_visual_qa_retries": MAX_VISUAL_QA_RETRIES,
                    "quarantine_integrity_issues": quarantine_issues,
                },
            )
    else:
        retry_count = next_retry_count(carousel_dir)
        quarantine_records = quarantine_generated_sources(
            carousel_dir,
            slides=slides,
            generated_paths_by_format=generated_paths_by_format or {},
            retry_count=retry_count,
            output_formats=output_formats,
        )
    quarantine_extra = {
        "proof_state": GenerationStatus.GENERATED_QUARANTINED.value,
        "retry_count": retry_count,
        "max_visual_qa_retries": MAX_VISUAL_QA_RETRIES,
        "retries_remaining": MAX_VISUAL_QA_RETRIES - retry_count,
        "quarantine_dir": str(quarantine_dir(carousel_dir, retry_count)),
        "image_set_sha256": image_set_sha256(quarantine_records),
        "requested_formats": list(output_formats),
        "native_output_contract": output_contract,
    }
    if compiled_handoff is not None:
        quarantine_extra["compiled_prompt_handoff"] = compiled_handoff
    if not promote_existing_quarantine:
        append_attempt(
            carousel_dir,
            retry_count=retry_count,
            image_set_hash=quarantine_extra["image_set_sha256"],
        )
        write_generation_state(
            carousel_dir,
            status=GenerationStatus.GENERATED_QUARANTINED,
            backend=BACKEND,
            generation_mode=GENERATION_MODE,
            slide_count=len(slides),
            reason="Generated images are quarantined pending exact-image post-generation visual QA.",
            slides=quarantine_records,
            extra=quarantine_extra,
        )

    resolved_visual_qa_path = resolve_package_artifact_path(
        carousel_dir, visual_qa_path, "visual-qa.json"
    )
    if not resolved_visual_qa_path.exists():
        clean_packaged_output_files(carousel_dir, slide_numbers)
        return write_generation_state(
            carousel_dir,
            status=GenerationStatus.GENERATED_QUARANTINED,
            backend=BACKEND,
            generation_mode=GENERATION_MODE,
            slide_count=len(slides),
            reason="Exact-image visual-qa.json is required before any proof can be promoted.",
            slides=quarantine_records,
            extra=quarantine_extra,
        )

    visual_qa = load_json(resolved_visual_qa_path)
    visual_plan = load_json(carousel_dir / "visual-plan-quality.json")
    visual_qa_issues = validate_exact_image_visual_qa(
        visual_qa,
        quarantine_records,
        visual_plan=visual_plan,
        carousel_dir=carousel_dir,
    )
    if visual_qa_issues:
        update_current_attempt(
            carousel_dir,
            status="QA_FAILED",
            qa_issues=visual_qa_issues,
        )
        clean_packaged_output_files(carousel_dir, slide_numbers)
        failed_extra = {
            **quarantine_extra,
            "visual_qa_path": str(resolved_visual_qa_path),
            "visual_qa_issues": visual_qa_issues,
        }
        spatial_failure = any("spatial_topology" in issue for issue in visual_qa_issues)
        if retry_count >= MAX_VISUAL_QA_RETRIES:
            failed_extra["proof_state"] = GenerationStatus.BLOCKED_VISUAL_QA.value
            return write_generation_state(
                carousel_dir,
                status=GenerationStatus.BLOCKED_VISUAL_QA,
                backend=BACKEND,
                generation_mode=GENERATION_MODE,
                slide_count=len(slides),
                reason="Visual QA failed after the initial generation and two repair retries; batching is blocked.",
                slides=quarantine_records,
                extra=failed_extra,
            )
        if spatial_failure:
            failed_extra["proof_state"] = GenerationStatus.REJECTED_SPATIAL_INTEGRITY.value
        return write_generation_state(
            carousel_dir,
            status=(
                GenerationStatus.REJECTED_SPATIAL_INTEGRITY
                if spatial_failure
                else GenerationStatus.GENERATED_QUARANTINED
            ),
            backend=BACKEND,
            generation_mode=GENERATION_MODE,
            slide_count=len(slides),
            reason=(
                "Whole-person spatial integrity failed; regenerate the rejected body/environment relationship before packaging."
                if spatial_failure
                else "Visual QA failed; regenerate with targeted repairs before packaging."
            ),
            slides=quarantine_records,
            extra=failed_extra,
        )

    candidate_extra = {
        **quarantine_extra,
        "proof_state": GenerationStatus.QA_PASS_CANDIDATE.value,
        "visual_qa_path": str(resolved_visual_qa_path),
    }
    update_current_attempt(carousel_dir, status="QA_PASSED")
    if current_proof_status != GenerationStatus.CREATOR_APPROVED_PROOF:
        write_generation_state(
            carousel_dir,
            status=GenerationStatus.QA_PASS_CANDIDATE,
            backend=BACKEND,
            generation_mode=GENERATION_MODE,
            slide_count=len(slides),
            reason="Exact-image visual QA passed; explicit creator approval is still required.",
            slides=quarantine_records,
            extra=candidate_extra,
        )

    resolved_approval_path = resolve_package_artifact_path(
        carousel_dir, creator_approval_path, "creator-proof-approval.json"
    )
    if not resolved_approval_path.exists():
        clean_packaged_output_files(carousel_dir, slide_numbers)
        return write_generation_state(
            carousel_dir,
            status=GenerationStatus.QA_PASS_CANDIDATE,
            backend=BACKEND,
            generation_mode=GENERATION_MODE,
            slide_count=len(slides),
            reason="QA-passed proof is awaiting explicit creator approval; batching remains blocked.",
            slides=quarantine_records,
            extra=candidate_extra,
        )
    approval = load_json(resolved_approval_path)
    approval_issues = validate_creator_approval(
        approval, expected_image_set_sha256=quarantine_extra["image_set_sha256"]
    )
    if approval_issues:
        clean_packaged_output_files(carousel_dir, slide_numbers)
        return write_generation_state(
            carousel_dir,
            status=GenerationStatus.QA_PASS_CANDIDATE,
            backend=BACKEND,
            generation_mode=GENERATION_MODE,
            slide_count=len(slides),
            reason="Creator approval record is missing, stale, or invalid; batching remains blocked.",
            slides=quarantine_records,
            extra={**candidate_extra, "creator_approval_issues": approval_issues},
        )

    approved_extra = {
        **candidate_extra,
        "proof_state": GenerationStatus.CREATOR_APPROVED_PROOF.value,
        "creator_approval_path": str(resolved_approval_path),
    }
    update_current_attempt(carousel_dir, status="CREATOR_APPROVED")
    if current_proof_status != GenerationStatus.CREATOR_APPROVED_PROOF:
        write_generation_state(
            carousel_dir,
            status=GenerationStatus.CREATOR_APPROVED_PROOF,
            backend=BACKEND,
            generation_mode=GENERATION_MODE,
            slide_count=len(slides),
            reason="The exact QA-passed image set has explicit creator approval.",
            slides=quarantine_records,
            extra=approved_extra,
        )

    if not refresh_quality:
        clean_packaged_output_files(carousel_dir, slide_numbers)
        return write_generation_state(
            carousel_dir,
            status=GenerationStatus.CREATOR_APPROVED_PROOF,
            backend=BACKEND,
            generation_mode=GENERATION_MODE,
            slide_count=len(slides),
            reason="Creator approval is recorded, but promotion is blocked until final audit runs.",
            slides=quarantine_records,
            extra={**approved_extra, "promotion_blocker": "final_audit_required"},
        )

    generated_paths_by_format = {
        output_format: [
            record["native_outputs"][output_format]["path"] for record in quarantine_records
        ]
        for output_format in output_formats
    }
    clean_packaged_output_files(carousel_dir, slide_numbers)

    staging_root = (
        carousel_dir
        / PROMOTION_STAGING_FOLDER
        / quarantine_extra["image_set_sha256"]
    )
    if staging_root.exists():
        shutil.rmtree(staging_root)
    staging_final_dir = staging_root / "final"
    source_dir = staging_final_dir / "model-native-source"
    staging_output_dirs = {
        output_format: staging_root / str(format_spec(output_format)["folder"])
        for output_format in output_formats
    }
    for folder in {staging_final_dir, source_dir, *staging_output_dirs.values()}:
        folder.mkdir(parents=True, exist_ok=True)

    prompt_refs = [str(path) for path in existing_reference_paths(prompt_pack)]
    slide_plans = load_json(carousel_dir / "slides.json")
    records = []
    normalization_notes: list[str] = []
    for index, slide_prompt in enumerate(slides):
        number = int(slide_prompt["slide"])
        native_outputs: dict[str, Any] = {}
        compatibility_fields: dict[str, Any] = {}
        for output_format in output_formats:
            source_path = Path(generated_paths_by_format[output_format][index]).expanduser()
            if not source_path.exists():
                raise FileNotFoundError(f"Missing Codex generated image: {source_path}")
            image_bytes = source_path.read_bytes()
            require_native_source_dimensions(
                image_bytes=image_bytes,
                output_format=output_format,
                slide_number=number,
                path=source_path,
            )
            spec = format_spec(output_format)
            staged_source = source_dir / f"{spec['source_prefix']}-slide-{number:02d}.png"
            shutil.copyfile(source_path, staged_source)
            source_target = expected_source_path(carousel_dir, output_format, number)
            target = expected_output_path(carousel_dir, output_format, number)
            staged_target = staging_output_dirs[output_format] / target.name
            target_width, target_height = target_size_for_format(output_format)
            output_bytes, source_dimensions, normalization, warning = normalize_for_upload(
                image_bytes, target_width, target_height
            )
            staged_target.write_bytes(output_bytes)
            if warning:
                normalization_notes.append(
                    f"Slide {number} {spec['label']}: {warning}"
                )
            native_outputs[output_format] = {
                "label": spec["label"],
                "aspect_ratio": spec["aspect_ratio"],
                "source": str(source_target),
                "codex_generated_source": str(source_path),
                "source_dimensions": source_dimensions,
                "file": str(target),
                "upload_size": f"{target_width}x{target_height}",
                "normalization": normalization,
            }
            if output_format == INSTAGRAM_POST_FORMAT:
                compatibility_fields.update(
                    source=str(source_target),
                    codex_generated_source=str(source_path),
                    file=str(target),
                )
            elif output_format == REELS_STORIES_FORMAT:
                compatibility_fields.update(
                    reels_stories_source=str(source_target),
                    reels_stories_file=str(target),
                )
            elif output_format == SQUARE_FORMAT:
                compatibility_fields.update(
                    square_source=str(source_target),
                    square_file=str(target),
                )
        slide_plan = next(
            (
                item
                for item in slide_plans
                if int(item.get("slide", 0) or 0) == number
            ),
            {},
        )
        reference_images = [
            *prompt_refs,
            *[str(path) for path in slide_source_paths(slide_plan)],
        ]
        records.append(
            {
                "slide": number,
                "copy": slide_prompt["text"],
                "generation_mode": GENERATION_MODE,
                "backend": BACKEND,
                "prompt": slide_prompt["prompt"],
                "reference_images": reference_images,
                **compatibility_fields,
                "native_outputs": native_outputs,
            }
        )

    normalization_text = (
        "Each surface is generated from its own exact native pixel source. Wrong-size sources "
        "are rejected before packaging instead of being resized, cropped, or padded."
    )
    generation_extra = {
        "requested_formats": list(output_formats),
        "native_output_contract": output_contract,
        "normalization": normalization_text,
        "notes": normalization_notes,
        **approved_extra,
        "proof_state": GenerationStatus.BATCH_ALLOWED.value,
    }
    result = write_generation_state(
        carousel_dir,
        status=GenerationStatus.BATCH_ALLOWED,
        backend=BACKEND,
        generation_mode=GENERATION_MODE,
        slide_count=len(slides),
        slides=records,
        extra=generation_extra,
    )
    from pipeline.stages.carousel_quality import QualityContext, write_quality_artifacts

    manifest = load_json(carousel_dir / "manifest.json")
    package = {
        "concept": load_json(carousel_dir / "concept.json"),
        "slides": load_json(carousel_dir / "slides.json"),
        "visual_plan_quality": load_json(carousel_dir / "visual-plan-quality.json"),
        "prompt_pack": prompt_pack,
        "copy": load_json(carousel_dir / "copy.json"),
    }
    final_audit = write_quality_artifacts(
        QualityContext(
            story=manifest["source_story"],
            title=manifest["title"],
            slug=manifest["slug"],
            today=date.fromisoformat(manifest["date"]),
            out_dir=carousel_dir,
            image_paths=[
                Path(item["path"])
                for item in manifest.get("reference_images", [])
                if isinstance(item, dict) and item.get("path")
            ],
            slide_count=len(slides),
            package=package,
            manifest=manifest,
            render_result=result,
            workspace_root=infer_workspace_root_from_carousel_dir(carousel_dir),
            asset_root=staging_root,
        )
    )
    audit_extra = {
        **generation_extra,
        "final_audit_status": final_audit["status"],
        "final_audit_pass": bool(final_audit["pass"]),
        "final_audit_path": str(carousel_dir / "final-audit.json"),
        "promotion_staging_dir": str(staging_root),
    }
    if not final_audit["pass"]:
        update_current_attempt(carousel_dir, status="FINAL_AUDIT_FAILED")
        result = write_generation_state(
            carousel_dir,
            status=GenerationStatus.GENERATED_AUDIT_FAILED,
            backend=BACKEND,
            generation_mode=GENERATION_MODE,
            slide_count=len(slides),
            reason="Final audit failed; publishable folders were not created and staged files remain internal.",
            slides=records,
            extra=audit_extra,
        )
    else:
        public_dirs = {
            carousel_dir / str(format_spec(value)["folder"])
            for value in normalize_requested_formats(
                [INSTAGRAM_POST_FORMAT, REELS_STORIES_FORMAT, SQUARE_FORMAT]
            )
        }
        for public_dir in public_dirs:
            if public_dir.exists():
                shutil.rmtree(public_dir)
        for staging_dir in {staging_final_dir, *staging_output_dirs.values()}:
            target_dir = carousel_dir / staging_dir.relative_to(staging_root)
            staging_dir.replace(target_dir)
        update_current_attempt(carousel_dir, status="PROMOTED")
        result = write_generation_state(
            carousel_dir,
            status=GenerationStatus.PUBLISH_READY,
            backend=BACKEND,
            generation_mode=GENERATION_MODE,
            slide_count=len(slides),
            slides=records,
            extra=audit_extra,
        )
    return result


def promote_quarantined_codex_builtin_outputs(
    carousel_dir: Path,
    *,
    refresh_quality: bool = False,
    visual_qa_path: str | Path | None = None,
    creator_approval_path: str | Path | None = None,
) -> dict[str, Any]:
    """Revalidate and promote an existing quarantine without original temp sources."""

    return package_codex_builtin_outputs(
        carousel_dir,
        refresh_quality=refresh_quality,
        visual_qa_path=visual_qa_path,
        creator_approval_path=creator_approval_path,
        promote_existing_quarantine=True,
    )


def run_fail_closed_visual_worker(
    carousel_dir: Path,
    *,
    generate_attempt: Callable[[int, list[str]], dict[str, list[str | Path]]],
    review_attempt: Callable[[dict[str, Any]], dict[str, Any]],
    creator_approval_path: str | Path | None = None,
    refresh_quality: bool = True,
) -> dict[str, Any]:
    """Generate, inspect, and repair internally with at most two retries.

    The generator receives the persisted retry count and the exact issues from
    the preceding attempt. Candidates stay quarantined until review and any
    creator-approved promotion completes.
    """

    carousel_dir = carousel_dir.expanduser()
    repair_issues: list[str] = []
    while True:
        retry_count = next_retry_count(carousel_dir)
        generated = generate_attempt(retry_count, list(repair_issues))
        pending_qa = carousel_dir / ".internal" / f"pending-qa-attempt-{retry_count + 1:02d}.json"
        state = package_codex_builtin_outputs(
            carousel_dir,
            generated_paths_by_format=generated,
            visual_qa_path=pending_qa,
        )
        if state.get("status") != GenerationStatus.GENERATED_QUARANTINED.value:
            return state

        visual_qa = review_attempt(state)
        qa_path = carousel_dir / "visual-qa.json"
        write_json(qa_path, visual_qa)
        state = promote_quarantined_codex_builtin_outputs(
            carousel_dir,
            refresh_quality=refresh_quality,
            visual_qa_path=qa_path,
            creator_approval_path=creator_approval_path,
        )
        if state.get("status") == GenerationStatus.BLOCKED_VISUAL_QA.value:
            return state
        repair_issues = list(state.get("visual_qa_issues") or [])
        if not repair_issues:
            return state
