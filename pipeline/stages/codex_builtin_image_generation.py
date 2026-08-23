from __future__ import annotations

import json
import hashlib
import re
import shutil
import uuid
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
FULL_DECK_ATTEMPT_LEDGER = ".internal/full-deck-visual-qa-attempts.json"
FULL_DECK_QUARANTINE_FOLDER = ".internal/full-deck-visual-quarantine"
FULL_DECK_VISUAL_QA = ".internal/full-deck-visual-qa.json"
CREATOR_OVERRIDE_FULL_DECK_SCOPE = "creator_override_full_deck"
PROMOTION_STAGING_FOLDER = ".internal/promotion-staging"
PROMPT_HANDOFF_ACTIVE_FOLDER = "codex-image-prompts"
PROMPT_HANDOFF_STAGING_FOLDER = ".internal/codex-image-prompts-staging"
PROMPT_HANDOFF_BACKUP_FOLDER = ".internal/codex-image-prompts-previous"
PROMPT_HANDOFF_SCHEMA_VERSION = "compiled-prompt-handoff/v1"
APPROVED_PROOF_BATCH_HANDOFF_SCHEMA_VERSION = (
    "approved-proof-batch-handoff/v1"
)
APPROVED_PROOF_BATCH_HANDOFF_ARCHIVE = (
    ".internal/approved-proof/handoff-attestation.json"
)
RETRY_HANDOFF_SCHEMA_VERSION = "retry-prompt-handoff/v1"
CREATOR_FAILED_PROOF_APPROVAL_SCHEMA_VERSION = (
    "creator-failed-proof-approval/v1"
)
CREATOR_OVERRIDE_PROOF_BINDING_SCHEMA_VERSION = (
    "creator-override-proof-binding/v1"
)
CREATOR_ACCEPTED_WITH_KNOWN_EXCEPTIONS = (
    "CREATOR_ACCEPTED_WITH_KNOWN_EXCEPTIONS"
)
RETRY_GATE_INPUT_FILES = (
    FORMAT_CONTRACT_FILENAME,
    "prompt-pack.json",
    "slides.json",
    "visual-plan-quality.json",
    "identity-consistency-review.json",
    "review.json",
    "layer-e-story-selling.json",
    "stage-reviews.json",
)
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
        GenerationStatus.BATCH_ALLOWED.value,
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
    state_slide_count = state.get("slide_count")
    legacy_proof_count = (
        len(canonical_slides) == 1
        and state.get("requested_proof_slide") == canonical_slides[0]
        and isinstance(state_slide_count, int)
        and state_slide_count > len(canonical_slides)
    )
    if state_slide_count != len(canonical_slides) and not legacy_proof_count:
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
    if state.get("status") in {
        GenerationStatus.GENERATED_QUARANTINED.value,
        GenerationStatus.REJECTED_SPATIAL_INTEGRITY.value,
    }:
        issues.extend(retry_prompt_handoff_attestation_issues(carousel_dir, state=state))
    if state.get("approved_proof_batch_handoff_attestation") is not None:
        issues.extend(
            approved_proof_batch_handoff_attestation_issues(
                carousel_dir,
                state=state,
            )
        )
    return issues


def approved_proof_batch_handoff_attestation_issues(
    carousel_dir: Path,
    *,
    state: Any,
) -> list[str]:
    """Verify the immutable proof evidence carried into a clean full-deck handoff."""

    if not isinstance(state, dict):
        return ["approved-proof batch handoff state is malformed"]
    attestation = state.get("approved_proof_batch_handoff_attestation")
    if not isinstance(attestation, dict):
        return ["approved-proof batch handoff attestation is missing"]

    issues: list[str] = []
    if (
        attestation.get("schema_version")
        != APPROVED_PROOF_BATCH_HANDOFF_SCHEMA_VERSION
    ):
        issues.append("approved-proof batch handoff schema is missing or unsupported")
    fingerprint_payload = {
        key: value
        for key, value in attestation.items()
        if key != "attestation_fingerprint"
    }
    if attestation.get("attestation_fingerprint") != _canonical_fingerprint(
        fingerprint_payload
    ):
        issues.append("approved-proof batch handoff attestation fingerprint is stale")
    if attestation.get("requested_formats") != state.get("requested_formats"):
        issues.append("approved-proof batch handoff formats are stale")

    for label, binding in (
        ("visual QA", attestation.get("visual_qa_binding")),
        ("creator approval", attestation.get("creator_approval_binding")),
    ):
        if not isinstance(binding, dict) or not isinstance(
            binding.get("relative_path"), str
        ):
            issues.append(f"approved-proof batch handoff is missing {label} binding")
            continue
        issues.extend(
            f"approved-proof {label}: {issue}"
            for issue in _bound_package_file_issues(
                carousel_dir,
                binding,
                expected_relative_path=binding["relative_path"],
            )
        )

    quarantine_bindings = attestation.get("quarantine_bindings")
    if not isinstance(quarantine_bindings, list) or not quarantine_bindings:
        issues.append("approved-proof batch handoff quarantine bindings are missing")
    else:
        seen: set[str] = set()
        for binding in quarantine_bindings:
            if not isinstance(binding, dict) or not isinstance(
                binding.get("relative_path"), str
            ):
                issues.append("approved-proof batch handoff has a malformed quarantine binding")
                continue
            relative_path = binding["relative_path"]
            if relative_path in seen:
                issues.append("approved-proof batch handoff repeats a quarantine binding")
                continue
            seen.add(relative_path)
            issues.extend(
                f"approved-proof quarantine: {issue}"
                for issue in _bound_package_file_issues(
                    carousel_dir,
                    binding,
                    expected_relative_path=relative_path,
                )
            )
    return issues


def _failed_proof_retry_scope(state: Any) -> bool:
    """Return whether a state is a failed proof that requires retry attestation."""

    if not isinstance(state, dict) or state.get("proof_only") is not True:
        return False
    status = state.get("status")
    if status == GenerationStatus.REJECTED_SPATIAL_INTEGRITY.value:
        return True
    return (
        status == GenerationStatus.GENERATED_QUARANTINED.value
        and isinstance(state.get("visual_qa_issues"), list)
        and bool(state["visual_qa_issues"])
    )


def _binding_for_package_file(carousel_dir: Path, relative_path: str) -> dict[str, str]:
    relative = Path(relative_path)
    if relative.is_absolute() or ".." in relative.parts:
        raise ValueError(f"Retry handoff input escapes the package: {relative_path}")
    package_root = carousel_dir.expanduser().resolve()
    path = carousel_dir / relative
    cursor = carousel_dir
    for part in relative.parts:
        cursor = cursor / part
        if cursor.is_symlink():
            raise ValueError(f"Retry handoff input contains a symlink: {relative_path}")
    try:
        path.resolve().relative_to(package_root)
    except (OSError, ValueError) as exc:
        raise ValueError(f"Retry handoff input escapes the package: {relative_path}") from exc
    if path.is_symlink() or not path.is_file():
        raise ValueError(f"Retry handoff input is missing or unsafe: {relative_path}")
    return {
        "relative_path": relative_path,
        "sha256": sha256_binding(path.read_bytes()),
    }


def _retry_gate_input_bindings(carousel_dir: Path) -> list[dict[str, str]]:
    return [
        _binding_for_package_file(carousel_dir, relative_path)
        for relative_path in RETRY_GATE_INPUT_FILES
    ]


def retry_prompt_handoff_attestation_issues(
    carousel_dir: Path,
    *,
    state: Any,
) -> list[str]:
    """Verify the retry handoff only for a proof with persisted failed QA.

    Fresh quarantines and full-deck generation states intentionally do not use
    this attestation. Their ordinary compiled-handoff checks remain unchanged.
    """

    if not _failed_proof_retry_scope(state):
        return []
    attestation = state.get("retry_prompt_handoff_attestation")
    if not isinstance(attestation, dict):
        return ["failed proof retry is missing retry_prompt_handoff_attestation"]

    issues: list[str] = []
    if attestation.get("schema_version") != RETRY_HANDOFF_SCHEMA_VERSION:
        issues.append("retry prompt handoff attestation schema is missing or unsupported")
    fingerprint_payload = {
        key: value
        for key, value in attestation.items()
        if key != "attestation_fingerprint"
    }
    if attestation.get("attestation_fingerprint") != _canonical_fingerprint(
        fingerprint_payload
    ):
        issues.append("retry prompt handoff attestation fingerprint is stale")
    if attestation.get("source_status") != state.get("status"):
        issues.append("retry prompt handoff attestation source status is stale")
    if attestation.get("proof_slide") != state.get("requested_proof_slide"):
        issues.append("retry prompt handoff attestation proof slide is stale")
    if attestation.get("requested_formats") != state.get("requested_formats"):
        issues.append("retry prompt handoff attestation formats are stale")
    if attestation.get("failed_image_set_sha256") != state.get("image_set_sha256"):
        issues.append("retry prompt handoff attestation image set is stale")

    handoff = state.get("compiled_prompt_handoff")
    if (
        not isinstance(handoff, dict)
        or attestation.get("replacement_handoff_set_fingerprint")
        != handoff.get("handoff_set_fingerprint")
    ):
        issues.append("retry prompt handoff attestation does not bind the active handoff")

    failed_attempt = attestation.get("failed_attempt")
    ledger = load_attempt_ledger(carousel_dir)
    attempts = ledger.get("attempts", [])
    if not isinstance(failed_attempt, dict):
        issues.append("retry prompt handoff attestation is missing failed-attempt evidence")
    else:
        attempt_number = failed_attempt.get("attempt")
        matching = [
            attempt
            for attempt in attempts
            if isinstance(attempt, dict) and attempt.get("attempt") == attempt_number
        ]
        if len(matching) != 1 or matching[0] != failed_attempt:
            issues.append("retry prompt handoff attestation failed-attempt evidence is stale")

    for label, binding in (
        ("visual QA", attestation.get("visual_qa_binding")),
        ("attempt ledger", attestation.get("attempt_ledger_binding")),
    ):
        if not isinstance(binding, dict):
            issues.append(f"retry prompt handoff attestation is missing {label} binding")
            continue
        relative_path = binding.get("relative_path")
        if not isinstance(relative_path, str):
            issues.append(f"retry prompt handoff attestation has malformed {label} binding")
            continue
        issues.extend(
            f"retry {label}: {issue}"
            for issue in _bound_package_file_issues(
                carousel_dir,
                binding,
                expected_relative_path=relative_path,
            )
        )

    gate_bindings = attestation.get("gate_input_bindings")
    expected_gate_paths = list(RETRY_GATE_INPUT_FILES)
    if not isinstance(gate_bindings, list):
        issues.append("retry prompt handoff attestation gate input bindings are missing")
    else:
        seen_gate_paths: list[str] = []
        for binding in gate_bindings:
            if not isinstance(binding, dict):
                issues.append("retry prompt handoff attestation has malformed gate input binding")
                continue
            relative_path = binding.get("relative_path")
            if not isinstance(relative_path, str):
                issues.append("retry prompt handoff attestation gate binding has no path")
                continue
            seen_gate_paths.append(relative_path)
            issues.extend(
                f"retry gate input: {issue}"
                for issue in _bound_package_file_issues(
                    carousel_dir,
                    binding,
                    expected_relative_path=relative_path,
                )
            )
        if seen_gate_paths != expected_gate_paths:
            issues.append("retry prompt handoff attestation gate input set is stale")

    backup_dir = attestation.get("previous_prompt_backup_dir")
    backup_files = attestation.get("previous_prompt_files")
    if not isinstance(backup_dir, str) or not isinstance(backup_files, list):
        issues.append("retry prompt handoff attestation previous prompt backup is missing")
    else:
        expected_prefix = backup_dir.rstrip("/") + "/"
        seen_backup_paths: set[str] = set()
        for binding in backup_files:
            if not isinstance(binding, dict):
                issues.append("retry prompt handoff attestation has malformed backup binding")
                continue
            relative_path = binding.get("relative_path")
            if not isinstance(relative_path, str) or not relative_path.startswith(
                expected_prefix
            ):
                issues.append("retry prompt handoff backup binding escapes its immutable attempt")
                continue
            if relative_path in seen_backup_paths:
                issues.append("retry prompt handoff repeats an immutable backup binding")
                continue
            seen_backup_paths.add(relative_path)
            issues.extend(
                f"retry prompt backup: {issue}"
                for issue in _bound_package_file_issues(
                    carousel_dir,
                    binding,
                    expected_relative_path=relative_path,
                )
            )
        backup_root = carousel_dir / backup_dir
        actual_backup_paths = {
            path.relative_to(carousel_dir).as_posix()
            for path in backup_root.rglob("*")
            if path.is_file() or path.is_symlink()
        }
        if actual_backup_paths != seen_backup_paths:
            issues.append("retry prompt handoff immutable backup file set changed")
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


def _selected_slide_numbers(slides: list[dict[str, Any]]) -> list[int]:
    return [int(slide["slide"]) for slide in slides]


def _canonical_quarantine_frame_bindings(
    slides: list[dict[str, Any]],
    output_formats: tuple[str, ...],
) -> dict[tuple[int, str], dict[str, Any]]:
    """Bind Event B to canonical upload frames for the selected slide set."""

    bindings: dict[tuple[int, str], dict[str, Any]] = {}
    for slide_number in _selected_slide_numbers(slides):
        for output_format in output_formats:
            width, height = target_size_for_format(output_format)
            bindings[(slide_number, output_format)] = {
                "relative_path": expected_output_relative_path(output_format, slide_number),
                "dimensions": (width, height),
                "width": width,
                "height": height,
            }
    return bindings


def _dense_slide_adapter(
    check: Any,
    *,
    selected_slide_numbers: list[int],
    records_key: str,
) -> tuple[Any, list[str], dict[int, int]]:
    """Adapt sparse proof slide IDs to validators whose legacy API is count-based."""

    dense_map = {
        number: index
        for index, number in enumerate(selected_slide_numbers, start=1)
    }
    if selected_slide_numbers == list(range(1, len(selected_slide_numbers) + 1)):
        return check, [], dense_map
    if not isinstance(check, dict):
        return check, [], dense_map
    raw_records = check.get(records_key)
    if not isinstance(raw_records, list):
        return check, [], dense_map

    issues: list[str] = []
    seen: list[int] = []
    adapted = json.loads(json.dumps(check))
    for record in adapted[records_key]:
        if not isinstance(record, dict):
            continue
        try:
            number = int(record.get("slide"))
        except (TypeError, ValueError):
            issues.append(f"{records_key} contains an invalid proof slide number")
            continue
        seen.append(number)
        if number in dense_map:
            record["slide"] = dense_map[number]
    if set(seen) != set(selected_slide_numbers):
        issues.append(
            f"{records_key} must cover exactly the selected proof slides: "
            + ", ".join(str(number) for number in selected_slide_numbers)
        )
    return adapted, issues, dense_map


def quarantine_dir(carousel_dir: Path, retry_count: int) -> Path:
    return carousel_dir / QUARANTINE_FOLDER / f"attempt-{retry_count + 1:02d}"


def package_relative_path(carousel_dir: Path, path: Path) -> str:
    """Return one canonical POSIX path relative to the carousel package root."""

    package_root = Path(carousel_dir).expanduser().resolve()
    try:
        return path.expanduser().resolve().relative_to(package_root).as_posix()
    except ValueError as exc:
        raise ValueError(f"Quarantine asset escapes the carousel package: {path}") from exc


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


def next_retry_count(
    carousel_dir: Path,
    *,
    allow_approved_proof_batch: bool = False,
) -> int:
    """Derive the next immutable attempt number from persisted state."""

    ledger = load_attempt_ledger(carousel_dir)
    attempts = ledger["attempts"]
    if not attempts:
        return 0
    last = attempts[-1]
    eligible_statuses = {"QA_FAILED"}
    if allow_approved_proof_batch:
        eligible_statuses.add("BATCH_ALLOWED")
    if not isinstance(last, dict) or last.get("status") not in eligible_statuses:
        raise ValueError(
            "A new candidate is allowed only after the current quarantined attempt has "
            "completed QA with a recorded failure."
        )
    retry_count = len(attempts)
    retry_limit = (
        MAX_VISUAL_QA_RETRIES + 1
        if allow_approved_proof_batch
        and attempts
        and isinstance(attempts[0], dict)
        and attempts[0].get("status") == GenerationStatus.BATCH_ALLOWED.value
        else MAX_VISUAL_QA_RETRIES
    )
    if retry_count > retry_limit:
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


def full_deck_quarantine_dir(carousel_dir: Path, retry_count: int) -> Path:
    return (
        carousel_dir
        / FULL_DECK_QUARANTINE_FOLDER
        / f"attempt-{retry_count + 1:02d}"
    )


def load_full_deck_attempt_ledger(carousel_dir: Path) -> dict[str, Any]:
    path = carousel_dir / FULL_DECK_ATTEMPT_LEDGER
    if not path.exists():
        return {
            "schema_version": "full-deck-visual-qa-attempts/v1",
            "scope": CREATOR_OVERRIDE_FULL_DECK_SCOPE,
            "max_retries": MAX_VISUAL_QA_RETRIES,
            "attempts": [],
        }
    ledger = load_json(path)
    if (
        ledger.get("schema_version") != "full-deck-visual-qa-attempts/v1"
        or ledger.get("scope") != CREATOR_OVERRIDE_FULL_DECK_SCOPE
        or not isinstance(ledger.get("attempts"), list)
    ):
        raise ValueError("Full-deck visual-QA attempt ledger is malformed.")
    return ledger


def write_full_deck_attempt_ledger(
    carousel_dir: Path,
    ledger: dict[str, Any],
) -> None:
    path = carousel_dir / FULL_DECK_ATTEMPT_LEDGER
    path.parent.mkdir(parents=True, exist_ok=True)
    write_json(path, ledger)


def next_full_deck_retry_count(carousel_dir: Path) -> int:
    """Derive a batch retry without mutating or counting proof attempts."""

    attempts = load_full_deck_attempt_ledger(carousel_dir)["attempts"]
    if not attempts:
        return 0
    last = attempts[-1]
    if not isinstance(last, dict) or last.get("status") != "QA_FAILED":
        raise ValueError(
            "A new full-deck candidate is allowed only after the current full-deck "
            "quarantine completed QA with a recorded failure."
        )
    retry_count = len(attempts)
    if retry_count > MAX_VISUAL_QA_RETRIES:
        raise ValueError(
            "Full-deck visual-QA retry limit is exhausted; the batch remains blocked."
        )
    return retry_count


def append_full_deck_attempt(
    carousel_dir: Path,
    *,
    retry_count: int,
    image_set_hash: str,
    quarantine_path: str,
    origin_handoff_fingerprint: str,
) -> None:
    ledger = load_full_deck_attempt_ledger(carousel_dir)
    attempts = ledger["attempts"]
    if retry_count != len(attempts):
        raise ValueError(
            f"Full-deck attempt ledger expected retry_count {len(attempts)}, "
            f"got {retry_count}."
        )
    attempts.append(
        {
            "attempt": retry_count + 1,
            "retry_count": retry_count,
            "scope": CREATOR_OVERRIDE_FULL_DECK_SCOPE,
            "image_set_sha256": image_set_hash,
            "quarantine_dir": quarantine_path,
            "origin_handoff_fingerprint": origin_handoff_fingerprint,
            "status": "QUARANTINED",
            "qa_issues": [],
            "targeted_repair_instructions": [],
        }
    )
    write_full_deck_attempt_ledger(carousel_dir, ledger)


def update_current_full_deck_attempt(
    carousel_dir: Path,
    *,
    status: str,
    qa_issues: list[str] | None = None,
) -> None:
    ledger = load_full_deck_attempt_ledger(carousel_dir)
    attempts = ledger["attempts"]
    if not attempts:
        raise ValueError("Cannot update full-deck visual-QA before batch generation.")
    current = attempts[-1]
    current["status"] = status
    if qa_issues is not None:
        current["qa_issues"] = list(qa_issues)
        current["targeted_repair_instructions"] = [
            f"Repair this exact full-deck QA failure without weakening any locked constraint: {issue}"
            for issue in qa_issues
        ]
    write_full_deck_attempt_ledger(carousel_dir, ledger)


def validate_current_full_deck_attempt(
    carousel_dir: Path,
    *,
    state: dict[str, Any],
) -> None:
    """Bind the active batch manifest to exactly one separate ledger attempt."""

    attempts = load_full_deck_attempt_ledger(carousel_dir)["attempts"]
    if not attempts or not isinstance(attempts[-1], dict):
        raise ValueError("Creator-override full-deck candidate has no ledger attempt.")
    current = attempts[-1]
    retry_count = state.get("retry_count")
    expected_statuses = {
        GenerationStatus.GENERATED_QUARANTINED.value: {
            "QUARANTINED",
            "QA_FAILED",
        },
        GenerationStatus.REJECTED_SPATIAL_INTEGRITY.value: {"QA_FAILED"},
        GenerationStatus.BLOCKED_VISUAL_QA.value: {"QA_FAILED"},
        GenerationStatus.QA_PASS_CANDIDATE.value: {"QA_PASSED"},
        GenerationStatus.CREATOR_APPROVED_PROOF.value: {"CREATOR_APPROVED"},
        GenerationStatus.BATCH_ALLOWED.value: {"CREATOR_APPROVED"},
    }
    if (
        not isinstance(retry_count, int)
        or current.get("attempt") != retry_count + 1
        or current.get("retry_count") != retry_count
        or current.get("scope") != CREATOR_OVERRIDE_FULL_DECK_SCOPE
        or current.get("image_set_sha256") != state.get("image_set_sha256")
        or current.get("quarantine_dir") != state.get("quarantine_dir")
        or current.get("origin_handoff_fingerprint")
        != state.get("creator_override_origin_handoff_fingerprint")
        or current.get("status") not in expected_statuses.get(
            state.get("status"),
            set(),
        )
    ):
        raise ValueError(
            "Creator-override full-deck candidate and its QA ledger disagree."
        )


def reconstruct_full_deck_quarantine_records(
    carousel_dir: Path,
    *,
    state: dict[str, Any],
    prompt_slides: list[dict[str, Any]],
    output_formats: tuple[str, ...],
) -> list[dict[str, Any]]:
    """Rebind a crash-interrupted pre-audit state to immutable batch pixels."""

    if (
        state.get("status") != GenerationStatus.BATCH_ALLOWED.value
        or state.get("proof_state") != GenerationStatus.BATCH_ALLOWED.value
        or state.get("generation_scope") != CREATOR_OVERRIDE_FULL_DECK_SCOPE
        or state.get("publishable") is not False
        or state.get("done") is not False
        or state.get("full_deck_qa_passed") is not True
        or state.get("visual_qa_status") != "QA_PASSED"
        or state.get("requested_formats") != list(output_formats)
    ):
        raise ValueError(
            "Creator-override pre-audit re-entry requires an exact non-publishable "
            "full-deck BATCH_ALLOWED state."
        )
    try:
        retry_count = int(state["retry_count"])
        prompt_numbers = [int(slide["slide"]) for slide in prompt_slides]
        state_numbers = [int(slide["slide"]) for slide in state["slides"]]
    except (KeyError, TypeError, ValueError) as exc:
        raise ValueError(
            "Creator-override pre-audit re-entry has malformed deck coverage."
        ) from exc
    if (
        not prompt_numbers
        or prompt_numbers != state_numbers
        or len(prompt_numbers) != len(set(prompt_numbers))
        or state.get("slide_count") != len(prompt_numbers)
        or state.get("total_slide_count") != len(prompt_numbers)
    ):
        raise ValueError(
            "Creator-override pre-audit re-entry does not cover the exact current deck."
        )

    attempt_dir = full_deck_quarantine_dir(carousel_dir, retry_count)
    if state.get("quarantine_dir") != package_relative_path(
        carousel_dir,
        attempt_dir,
    ):
        raise ValueError(
            "Creator-override pre-audit re-entry quarantine binding is stale."
        )

    records: list[dict[str, Any]] = []
    for slide in prompt_slides:
        number = int(slide["slide"])
        native_outputs: dict[str, Any] = {}
        for output_format in output_formats:
            spec = format_spec(output_format)
            frame_path = (
                attempt_dir
                / str(spec["folder"])
                / f"slide-{number:02d}.png"
            )
            source_path = (
                attempt_dir
                / "model-native-source"
                / f"{spec['source_prefix']}-slide-{number:02d}.png"
            )
            if not frame_path.is_file() or not source_path.is_file():
                raise ValueError(
                    "Creator-override pre-audit re-entry quarantine files are missing."
                )
            frame_bytes = frame_path.read_bytes()
            source_bytes = source_path.read_bytes()
            frame_dimensions = image_dimensions(frame_bytes)
            source_dimensions = require_native_source_dimensions(
                image_bytes=source_bytes,
                output_format=output_format,
                slide_number=number,
                path=source_path,
            )
            if (
                frame_dimensions["width"],
                frame_dimensions["height"],
            ) != target_size_for_format(output_format):
                raise ValueError(
                    "Creator-override pre-audit re-entry quarantine dimensions are invalid."
                )
            native_outputs[output_format] = {
                "path": package_relative_path(carousel_dir, frame_path),
                "sha256": sha256_bytes(frame_bytes),
                "width": frame_dimensions["width"],
                "height": frame_dimensions["height"],
                "model_native_source": {
                    "path": package_relative_path(carousel_dir, source_path),
                    "sha256": sha256_bytes(source_bytes),
                    "width": source_dimensions["width"],
                    "height": source_dimensions["height"],
                },
            }
        records.append(
            {
                "slide": number,
                "copy": slide["text"],
                "status": GenerationStatus.GENERATED_QUARANTINED.value,
                "native_outputs": native_outputs,
            }
        )

    integrity_issues = validate_quarantine_integrity(
        records,
        output_formats,
        carousel_dir=carousel_dir,
    )
    if integrity_issues or image_set_sha256(records) != state.get("image_set_sha256"):
        raise ValueError(
            "Creator-override pre-audit re-entry quarantine evidence is stale: "
            + "; ".join(integrity_issues or ["image-set fingerprint changed"])
        )
    return records


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


def _known_quarantine_binding(
    package_root: Path,
    raw_path: Path,
) -> tuple[Path, Path] | None:
    """Bind a path to one exact supported quarantine root without symlinks."""

    if ".." in raw_path.parts:
        return None
    candidate = raw_path if raw_path.is_absolute() else package_root / raw_path
    try:
        lexical_relative = candidate.absolute().relative_to(package_root)
    except ValueError:
        return None
    cursor = package_root
    for part in lexical_relative.parts:
        cursor = cursor / part
        if cursor.is_symlink():
            return None
    for folder in (QUARANTINE_FOLDER, FULL_DECK_QUARANTINE_FOLDER):
        quarantine_root = (package_root / folder).resolve()
        try:
            relative = candidate.resolve().relative_to(quarantine_root)
        except (OSError, ValueError):
            continue
        return quarantine_root, relative
    return None


def _quarantine_review_root(
    carousel_dir: Path,
    slides: list[dict[str, Any]],
) -> Path | None:
    """Return one verified package-contained attempt root for Event B."""

    package_root = Path(carousel_dir).expanduser().resolve()
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
            binding = _known_quarantine_binding(package_root, raw_path)
            if binding is None:
                return None
            quarantine_root, relative = binding
            if len(relative.parts) != 3 or not re.fullmatch(
                r"attempt-\d{2,}", relative.parts[0]
            ):
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
        selected_slide_numbers = _selected_slide_numbers(quarantine_slides)
        adapted_topology, topology_adapter_issues, _ = _dense_slide_adapter(
            topology,
            selected_slide_numbers=selected_slide_numbers,
            records_key="slides",
        )
        issues.extend(topology_adapter_issues)
        issues.extend(
            f"visual-qa.json {issue}"
            for issue in validate_spatial_topology_check(
                adapted_topology,
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
            adapted_readability, readability_adapter_issues, dense_map = (
                _dense_slide_adapter(
                    readability,
                    selected_slide_numbers=selected_slide_numbers,
                    records_key="frames",
                )
            )
            issues.extend(readability_adapter_issues)
            frame_bindings = _canonical_quarantine_frame_bindings(
                quarantine_slides,
                review_formats,
            )
            if selected_slide_numbers != list(
                range(1, len(selected_slide_numbers) + 1)
            ):
                frame_bindings = {
                    (dense_map[slide_number], output_format): binding
                    for (slide_number, output_format), binding in frame_bindings.items()
                }
            issues.extend(
                validate_frame_readability(
                    adapted_readability,
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
                    expected_frame_bindings=frame_bindings,
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


def visual_qa_issues_fingerprint(issues: list[str]) -> str:
    """Bind a creator acknowledgement to one exact, ordered QA issue list."""

    payload = json.dumps(
        issues,
        ensure_ascii=False,
        separators=(",", ":"),
    ).encode("utf-8")
    return sha256_binding(payload)


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
    bound_attempt_roots: set[Path] = set()
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
            binding = _known_quarantine_binding(package_root, raw_path)
            if binding is None:
                canonical = False
                relative = None
                quarantine_root = None
            else:
                quarantine_root, relative = binding
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
            if not canonical:
                issues.append(
                    f"quarantined slide {number} {output_format} path must be the canonical package-contained quarantine asset"
                )
                continue
            assert quarantine_root is not None
            bound_attempt_roots.add(quarantine_root / relative.parts[0])
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
            source = item.get("model_native_source")
            if source is None:
                continue
            if not isinstance(source, dict):
                issues.append(
                    f"quarantined slide {number} {output_format} model-native source binding is malformed"
                )
                continue
            source_raw_path = Path(str(source.get("path") or "")).expanduser()
            source_path = (
                source_raw_path
                if source_raw_path.is_absolute()
                else package_root / source_raw_path
            )
            source_canonical = True
            if not str(source.get("path") or "").strip() or ".." in source_raw_path.parts:
                source_canonical = False
            source_binding = _known_quarantine_binding(
                package_root,
                source_raw_path,
            )
            if source_binding is None:
                source_canonical = False
                source_relative = None
                source_quarantine_root = None
            else:
                source_quarantine_root, source_relative = source_binding
            if source_relative is not None:
                expected_source_relative = Path(
                    source_relative.parts[0] if source_relative.parts else "",
                    "model-native-source",
                    f"{format_spec(output_format)['source_prefix']}-slide-{slide_number:02d}.png",
                )
                if (
                    len(source_relative.parts) != 3
                    or not re.fullmatch(r"attempt-\d{2,}", source_relative.parts[0])
                    or source_relative != expected_source_relative
                    or source_quarantine_root != quarantine_root
                    or source_relative.parts[0] != relative.parts[0]
                ):
                    source_canonical = False
            if not source_canonical:
                issues.append(
                    f"quarantined slide {number} {output_format} model-native source path must be package-contained"
                )
                continue
            if not source_path.is_file():
                issues.append(
                    f"quarantined slide {number} {output_format} model-native source is missing"
                )
                continue
            source_bytes = source_path.read_bytes()
            if sha256_bytes(source_bytes) != source.get("sha256"):
                issues.append(
                    f"quarantined slide {number} {output_format} model-native source hash is stale"
                )
            try:
                source_dimensions = image_dimensions(source_bytes)
            except (RuntimeError, ValueError):
                issues.append(
                    f"quarantined slide {number} {output_format} model-native source is not readable"
                )
                continue
            if (
                source_dimensions["width"] != source.get("width")
                or source_dimensions["height"] != source.get("height")
            ):
                issues.append(
                    f"quarantined slide {number} {output_format} model-native source dimensions are stale"
                )
    if len(bound_attempt_roots) > 1:
        issues.append(
            "quarantined slides must belong to one canonical quarantine attempt scope"
        )
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


def pre_generation_review_gate_reason(carousel_dir: Path) -> str | None:
    """Block handoff when package-level creative reviews disagree or remain open.

    Layer E, the story review, the successful-carousel standard, and the
    stage-review summary are separate views of the same pre-generation
    decision.  A single manually repaired ``GO`` artifact must never overrule a
    stale ``REPAIR`` elsewhere in the package.
    """

    allowed = {"PASS", "PASS_WITH_NOTES", "GO"}
    issues: list[str] = []

    review_path = carousel_dir / "review.json"
    if not review_path.exists():
        return "review.json is required before Codex built-in image generation."
    review = load_json(review_path)

    score = review.get("story_selling_score")
    total = score.get("total") if isinstance(score, dict) else None
    try:
        review_total = float(total)
    except (TypeError, ValueError):
        review_total = -1.0
        issues.append("review.json story_selling_score.total is missing or invalid")
    else:
        if review_total < 28:
            issues.append(
                f"review.json Story-Selling score is {review_total:g}/30, below 28/30"
            )

    story_gate = review.get("story_selling_gate")
    if not isinstance(story_gate, dict) or str(story_gate.get("status") or "").upper() not in allowed:
        issues.append("review.json story_selling_gate is not PASS/GO")
    hard_fails = review.get("story_selling_hard_fails")
    if not isinstance(hard_fails, list):
        issues.append("review.json story_selling_hard_fails must be a list")
    elif hard_fails:
        issues.append(
            "review.json still declares Story-Selling hard fails: "
            + "; ".join(str(item) for item in hard_fails)
        )

    director_gate = review.get("story_director_gate")
    if not isinstance(director_gate, dict) or str(director_gate.get("status") or "").upper() not in allowed:
        issues.append("review.json story_director_gate is not PASS/GO")

    success_gate = review.get("successful_carousel_standard_gate")
    success_status = (
        str(success_gate.get("status") or "").upper()
        if isinstance(success_gate, dict)
        else ""
    )
    if (
        not isinstance(success_gate, dict)
        or success_status not in allowed
        or success_gate.get("pass") is False
    ):
        issues.append("review.json successful_carousel_standard_gate is not PASS/GO")

    layer_e_path = carousel_dir / "layer-e-story-selling.json"
    if layer_e_path.exists():
        layer_e = load_json(layer_e_path)
        layer_e_score = layer_e.get("story_selling_score")
        layer_e_total = (
            layer_e_score.get("total") if isinstance(layer_e_score, dict) else None
        )
        layer_e_total_number: float | None = None
        try:
            layer_e_total_number = float(layer_e_total)
        except (TypeError, ValueError):
            issues.append(
                "layer-e-story-selling.json story_selling_score.total is missing or invalid"
            )
        else:
            if review_total >= 0 and layer_e_total_number != review_total:
                issues.append(
                    "Layer E and review.json Story-Selling scores disagree "
                    f"({layer_e_total_number:g}/30 vs {review_total:g}/30)"
                )

        concept_path = carousel_dir / "concept.json"
        if concept_path.exists():
            concept = load_json(concept_path)
            decision = concept.get("story_selling_decision")
            if isinstance(decision, dict):
                concept_score = decision.get("score")
                concept_total = (
                    concept_score.get("total")
                    if isinstance(concept_score, dict)
                    else None
                )
                try:
                    concept_total_number = float(concept_total)
                except (TypeError, ValueError):
                    issues.append(
                        "concept.json story_selling_decision.score.total is missing or invalid"
                    )
                else:
                    if (
                        layer_e_total_number is not None
                        and concept_total_number != layer_e_total_number
                    ):
                        issues.append(
                            "Layer E and concept.json Story-Selling scores disagree "
                            f"({layer_e_total_number:g}/30 vs {concept_total_number:g}/30)"
                        )
                if str(decision.get("decision") or "").upper() != str(
                    layer_e.get("status") or ""
                ).upper():
                    issues.append(
                        "Layer E and concept.json Story-Selling decisions disagree"
                    )

        prompt_pack_path = carousel_dir / "prompt-pack.json"
        if prompt_pack_path.exists():
            prompt_pack = load_json(prompt_pack_path)
            prompt_layer_e = prompt_pack.get("layer_e_story_selling")
            if isinstance(prompt_layer_e, dict):
                if str(prompt_layer_e.get("status") or "").upper() != str(
                    layer_e.get("status") or ""
                ).upper():
                    issues.append(
                        "Layer E and prompt-pack.json Story-Selling decisions disagree"
                    )

    stage_reviews_path = carousel_dir / "stage-reviews.json"
    if stage_reviews_path.exists():
        stage_payload = load_json(stage_reviews_path)
        stage_reviews = stage_payload.get("reviews")
        required_pre_generation_stages = {
            "story_reviewer",
            "arc_reviewer",
            "visual_reviewer",
            "identity_consistency_reviewer",
            "prompt_reviewer",
            "success_standard_reviewer",
        }
        if isinstance(stage_reviews, dict):
            for name in sorted(required_pre_generation_stages):
                record = stage_reviews.get(name)
                if not isinstance(record, dict):
                    issues.append(f"stage-reviews.json is missing {name}")
                    continue
                status = str(record.get("status") or "").upper()
                if status not in allowed:
                    details = record.get("issues")
                    suffix = (
                        ": " + "; ".join(str(item) for item in details)
                        if isinstance(details, list) and details
                        else ""
                    )
                    issues.append(
                        f"stage-reviews.json {name} is {status or 'MISSING'}{suffix}"
                    )

    if issues:
        return "Pre-generation package review did not pass: " + "; ".join(issues)
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
    repair_instruction = str(slide_prompt.get("repair_instruction") or "").strip()
    if repair_instruction:
        visual = (
            "TARGETED EDIT INSTRUCTION (takes priority while preserving every other "
            "locked detail): "
            + repair_instruction
            + "\n\nLOCKED SCENE TO PRESERVE: "
            + str(visual)
        )
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
        action_topology=slide_prompt.get("action_topology_contract"),
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
    slide_count = int(
        result.get("total_slide_count") or result.get("slide_count") or len(slides)
    )
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
    quarantine_scope_dir: Path | None = None,
    refuse_existing_scope: bool = False,
) -> list[dict[str, Any]]:
    """Copy model results into an internal, non-publishable exact-image quarantine."""

    attempt_dir = quarantine_scope_dir or quarantine_dir(carousel_dir, retry_count)
    if attempt_dir.exists():
        if refuse_existing_scope:
            raise ValueError(
                "Full-deck quarantine scope already exists; refusing to overwrite "
                f"immutable candidate evidence: {attempt_dir}"
            )
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
            source_dimensions = require_native_source_dimensions(
                image_bytes=image_bytes,
                output_format=output_format,
                slide_number=number,
                path=source_path,
            )
            source_dir = attempt_dir / "model-native-source"
            source_dir.mkdir(parents=True, exist_ok=True)
            source_target = (
                source_dir
                / f"{format_spec(output_format)['source_prefix']}-slide-{number:02d}.png"
            )
            source_target.write_bytes(image_bytes)
            target_width, target_height = target_size_for_format(output_format)
            frame_bytes, _, normalization, warning = normalize_for_upload(
                image_bytes,
                target_width,
                target_height,
            )
            format_dir = attempt_dir / str(format_spec(output_format)["folder"])
            format_dir.mkdir(parents=True, exist_ok=True)
            target = format_dir / f"slide-{number:02d}.png"
            target.write_bytes(frame_bytes)
            native_outputs[output_format] = {
                "path": package_relative_path(carousel_dir, target),
                "sha256": sha256_bytes(frame_bytes),
                "width": target_width,
                "height": target_height,
                "normalization": normalization,
                "normalization_warning": warning,
                "model_native_source": {
                    "path": package_relative_path(carousel_dir, source_target),
                    "sha256": sha256_bytes(image_bytes),
                    "width": source_dimensions["width"],
                    "height": source_dimensions["height"],
                },
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
    target_width, target_height = target_size_for_format(output_format)
    exact_target_aspect = (
        dimensions["width"] * target_height
        == dimensions["height"] * target_width
    )
    meets_target_minimum = (
        dimensions["width"] >= target_width
        and dimensions["height"] >= target_height
    )
    if (
        actual_size not in expected_sizes
        and not (exact_target_aspect and meets_target_minimum)
    ):
        label = NATIVE_OUTPUT_FORMATS[output_format]["label"]
        expected = " or ".join(f"{width}x{height}" for width, height in expected_sizes)
        raise ValueError(
            f"Slide {slide_number} {label} native source dimensions are "
            f"{dimensions['width']}x{dimensions['height']}; expected {expected}, or an "
            f"exact {target_width}:{target_height} aspect source at least "
            f"{target_width}x{target_height}. "
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


def _creator_override_batch_handoff_evidence(
    carousel_dir: Path,
    *,
    requested_formats: list[str] | None,
    _accepted_state: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Validate and snapshot one creator-accepted failed proof for batch handoff."""

    if _accepted_state is None:
        state_path = carousel_dir / "image-generation.json"
        final_state_path = carousel_dir / "final-images.json"
        try:
            state_bytes = state_path.read_bytes()
            final_state_bytes = final_state_path.read_bytes()
            state = json.loads(state_bytes)
            final_state = json.loads(final_state_bytes)
        except (FileNotFoundError, OSError, json.JSONDecodeError) as exc:
            raise ValueError(
                "Creator-override full-deck handoff requires matching generation manifests."
            ) from exc
        if not isinstance(state, dict) or state != final_state:
            raise ValueError(
                "Creator-override full-deck handoff requires image-generation.json and "
                "final-images.json to contain the same current state."
            )
    else:
        state = json.loads(json.dumps(_accepted_state))
    if state.get("status") != GenerationStatus.BATCH_ALLOWED.value:
        raise ValueError(
            "Creator-override full-deck handoff requires BATCH_ALLOWED."
        )
    if state.get("proof_state") != GenerationStatus.BATCH_ALLOWED.value:
        raise ValueError(
            "Creator-override BATCH_ALLOWED status and proof_state must agree."
        )
    if (
        state.get("creator_override") is not True
        or state.get("batch_generation_allowed") is not True
    ):
        raise ValueError(
            "BATCH_ALLOWED can compile a full deck only from a recorded creator override."
        )
    if state.get("proof_only") is not True:
        raise ValueError(
            "Creator-override BATCH_ALLOWED must still describe the accepted proof-only run."
        )
    if (
        state.get("publishable") is not False
        or state.get("done") is not False
        or state.get("proof_qa_passed") is not False
        or state.get("visual_qa_status") != "QA_FAILED"
    ):
        raise ValueError(
            "Creator-override BATCH_ALLOWED must preserve its non-publishable QA_FAILED state."
        )

    try:
        proof_slide = int(state["requested_proof_slide"])
        retry_count = int(state["retry_count"])
    except (KeyError, TypeError, ValueError) as exc:
        raise ValueError(
            "Creator-override BATCH_ALLOWED is missing proof-slide or retry evidence."
        ) from exc
    proof_records = state.get("slides")
    if (
        not isinstance(proof_records, list)
        or len(proof_records) != 1
        or not isinstance(proof_records[0], dict)
        or int(proof_records[0].get("slide", 0) or 0) != proof_slide
    ):
        raise ValueError(
            "Creator-override BATCH_ALLOWED must bind exactly its accepted proof slide."
        )

    current_formats = list(locked_formats(carousel_dir))
    if state.get("requested_formats") != current_formats:
        raise ValueError(
            "Creator-override BATCH_ALLOWED formats disagree with the current format lock."
        )
    if requested_formats is not None:
        supplied_formats = list(normalize_requested_formats(requested_formats))
        if supplied_formats != current_formats:
            raise ValueError(
                "Creator-override full-deck handoff cannot change the accepted proof formats."
            )

    prompt_pack = load_json(carousel_dir / "prompt-pack.json")
    prompt_slides = prompt_pack.get("slides") if isinstance(prompt_pack, dict) else None
    if not isinstance(prompt_slides, list) or not prompt_slides:
        raise ValueError(
            "Creator-override full-deck handoff requires a non-empty prompt pack."
        )
    try:
        prompt_slide_numbers = [int(slide["slide"]) for slide in prompt_slides]
    except (KeyError, TypeError, ValueError) as exc:
        raise ValueError(
            "Creator-override full-deck handoff found invalid prompt-pack slide numbers."
        ) from exc
    if (
        len(prompt_slide_numbers) != len(set(prompt_slide_numbers))
        or proof_slide not in prompt_slide_numbers
        or state.get("total_slide_count") != len(prompt_slides)
    ):
        raise ValueError(
            "Creator-override BATCH_ALLOWED proof scope is stale for the current full deck."
        )

    quarantine_issues = validate_quarantine_integrity(
        proof_records,
        current_formats,
        carousel_dir=carousel_dir,
    )
    if quarantine_issues:
        raise ValueError(
            "Creator-override BATCH_ALLOWED quarantine integrity failed: "
            + "; ".join(quarantine_issues)
        )
    current_image_set_sha256 = image_set_sha256(proof_records)
    if state.get("image_set_sha256") != current_image_set_sha256:
        raise ValueError(
            "Creator-override BATCH_ALLOWED image-set binding is stale."
        )
    expected_quarantine_dir = package_relative_path(
        carousel_dir,
        quarantine_dir(carousel_dir, retry_count),
    )
    if state.get("quarantine_dir") != expected_quarantine_dir:
        raise ValueError(
            "Creator-override BATCH_ALLOWED quarantine directory binding is stale."
        )

    visual_qa_issues = state.get("visual_qa_issues")
    if (
        not isinstance(visual_qa_issues, list)
        or not visual_qa_issues
        or not all(isinstance(issue, str) and issue for issue in visual_qa_issues)
    ):
        raise ValueError(
            "Creator-override BATCH_ALLOWED must preserve the exact failed-QA issue list."
        )
    issues_fingerprint = visual_qa_issues_fingerprint(visual_qa_issues)

    approval_binding = state.get("creator_approval_binding")
    approval_path = state.get("creator_approval_path")
    if (
        not isinstance(approval_binding, dict)
        or not isinstance(approval_path, str)
        or approval_binding.get("relative_path") != approval_path
        or approval_binding.get("sha256") != state.get("creator_approval_sha256")
    ):
        raise ValueError(
            "Creator-override BATCH_ALLOWED is missing its bound creator approval."
        )
    try:
        current_approval_binding, approval_bytes = _read_creator_override_package_file(
            carousel_dir,
            approval_path,
            label="Creator failed-proof approval",
        )
    except ValueError as exc:
        raise ValueError(
            f"Creator-override BATCH_ALLOWED approval binding is invalid: {exc}"
        ) from exc
    if current_approval_binding != approval_binding:
        raise ValueError(
            "Creator-override BATCH_ALLOWED creator approval changed after acceptance."
        )
    try:
        approval = json.loads(approval_bytes)
    except json.JSONDecodeError as exc:
        raise ValueError(
            "Creator-override BATCH_ALLOWED creator approval is malformed."
        ) from exc
    if (
        not isinstance(approval, dict)
        or approval.get("status") != "APPROVED"
        or approval.get("approved") is not True
        or str(approval.get("approved_by") or "").strip().casefold() != "creator"
        or approval.get("image_set_sha256") != current_image_set_sha256
        or approval.get("accepts_known_qa_exceptions") is not True
        or approval.get("acknowledged_visual_qa_issues") != visual_qa_issues
        or approval.get("acknowledged_visual_qa_issues_fingerprint")
        != issues_fingerprint
    ):
        raise ValueError(
            "Creator-override BATCH_ALLOWED creator approval no longer matches the failed proof."
        )

    approval_record = state.get("creator_override_record")
    if not isinstance(approval_record, dict):
        raise ValueError(
            "Creator-override BATCH_ALLOWED is missing its immutable approval record."
        )
    record_payload = {
        key: value
        for key, value in approval_record.items()
        if key != "record_fingerprint"
    }
    if (
        approval_record.get("schema_version")
        != CREATOR_FAILED_PROOF_APPROVAL_SCHEMA_VERSION
        or approval_record.get("source_status")
        not in {
            GenerationStatus.BLOCKED_VISUAL_QA.value,
            GenerationStatus.REJECTED_SPATIAL_INTEGRITY.value,
        }
        or approval_record.get("proof_slide") != proof_slide
        or approval_record.get("retry_count") != retry_count
        or approval_record.get("image_set_sha256") != current_image_set_sha256
        or approval_record.get("approved_by") != "creator"
        or approval_record.get("accepts_known_qa_exceptions") is not True
        or approval_record.get("acknowledged_visual_qa_issues")
        != visual_qa_issues
        or approval_record.get("acknowledged_visual_qa_issues_fingerprint")
        != issues_fingerprint
        or approval_record.get("approval_binding") != approval_binding
        or approval_record.get("record_fingerprint")
        != _canonical_fingerprint(record_payload)
    ):
        raise ValueError(
            "Creator-override BATCH_ALLOWED approval record is stale or incomplete."
        )

    known_exceptions = state.get("known_qa_exceptions")
    visual_qa_binding = approval_record.get("visual_qa_binding")
    visual_qa_path = state.get("visual_qa_path")
    if (
        not isinstance(known_exceptions, dict)
        or known_exceptions.get("qa_status") != "QA_FAILED"
        or known_exceptions.get("visual_qa_issues") != visual_qa_issues
        or known_exceptions.get("visual_qa_issues_fingerprint")
        != issues_fingerprint
        or known_exceptions.get("visual_qa_binding") != visual_qa_binding
        or known_exceptions.get("creator_evidence")
        != approval_record.get("evidence")
        or not isinstance(visual_qa_binding, dict)
        or not isinstance(visual_qa_path, str)
        or visual_qa_binding.get("relative_path") != visual_qa_path
    ):
        raise ValueError(
            "Creator-override BATCH_ALLOWED known-exception evidence is stale or incomplete."
        )
    try:
        current_visual_qa_binding, visual_qa_bytes = (
            _read_creator_override_package_file(
                carousel_dir,
                visual_qa_path,
                label="Failed visual-QA artifact",
            )
        )
    except ValueError as exc:
        raise ValueError(
            f"Creator-override BATCH_ALLOWED visual-QA binding is invalid: {exc}"
        ) from exc
    if current_visual_qa_binding != visual_qa_binding:
        raise ValueError(
            "Creator-override BATCH_ALLOWED failed visual-QA artifact changed after acceptance."
        )
    try:
        visual_qa = json.loads(visual_qa_bytes)
    except json.JSONDecodeError as exc:
        raise ValueError(
            "Creator-override BATCH_ALLOWED failed visual-QA artifact is malformed."
        ) from exc
    if (
        not isinstance(visual_qa, dict)
        or visual_qa.get("image_set_sha256") != current_image_set_sha256
        or str(visual_qa.get("status") or "").upper() == "PASS"
    ):
        raise ValueError(
            "Creator-override BATCH_ALLOWED failed visual-QA artifact is stale or claims PASS."
        )

    ledger = load_attempt_ledger(carousel_dir)
    attempts = ledger.get("attempts")
    if (
        not isinstance(attempts, list)
        or not attempts
        or not isinstance(attempts[-1], dict)
    ):
        raise ValueError(
            "Creator-override BATCH_ALLOWED is missing its accepted failed attempt."
        )
    latest_attempt = attempts[-1]
    history = latest_attempt.get("status_history")
    accepted_history = (
        [
            event
            for event in history
            if isinstance(event, dict)
            and event.get("status") == CREATOR_ACCEPTED_WITH_KNOWN_EXCEPTIONS
        ]
        if isinstance(history, list)
        else []
    )
    failed_history = (
        [
            event
            for event in history
            if isinstance(event, dict) and event.get("status") == "QA_FAILED"
        ]
        if isinstance(history, list)
        else []
    )
    if (
        latest_attempt.get("status")
        != CREATOR_ACCEPTED_WITH_KNOWN_EXCEPTIONS
        or latest_attempt.get("attempt") != approval_record.get("attempt")
        or latest_attempt.get("retry_count") != retry_count
        or latest_attempt.get("image_set_sha256") != current_image_set_sha256
        or latest_attempt.get("qa_status") != "QA_FAILED"
        or latest_attempt.get("qa_issues") != visual_qa_issues
        or latest_attempt.get("visual_qa_issues_fingerprint")
        != issues_fingerprint
        or latest_attempt.get("creator_override") != approval_record
        or latest_attempt.get("batch_generation_allowed") is not True
        or latest_attempt.get("publishable") is not False
        or not any(
            event.get("image_set_sha256") == current_image_set_sha256
            and event.get("visual_qa_issues_fingerprint") == issues_fingerprint
            and event.get("visual_qa_binding") == visual_qa_binding
            for event in failed_history
        )
        or not any(
            event.get("approval_binding") == approval_binding
            and event.get("creator_override_record_fingerprint")
            == approval_record.get("record_fingerprint")
            for event in accepted_history
        )
    ):
        raise ValueError(
            "Creator-override BATCH_ALLOWED attempt ledger is stale or incomplete."
        )

    proof_binding: dict[str, Any] = {
        "schema_version": CREATOR_OVERRIDE_PROOF_BINDING_SCHEMA_VERSION,
        "source_status": GenerationStatus.BATCH_ALLOWED.value,
        "proof_state": GenerationStatus.BATCH_ALLOWED.value,
        "proof_slide": proof_slide,
        "proof_slide_record": json.loads(json.dumps(proof_records[0])),
        "retry_count": retry_count,
        "image_set_sha256": current_image_set_sha256,
        "quarantine_dir": expected_quarantine_dir,
        "requested_formats": current_formats,
        "visual_qa_path": visual_qa_path,
        "visual_qa_binding": json.loads(json.dumps(visual_qa_binding)),
        "visual_qa_issues_fingerprint": issues_fingerprint,
        "creator_approval_binding": json.loads(json.dumps(approval_binding)),
        "creator_override_record_fingerprint": approval_record[
            "record_fingerprint"
        ],
        "attempt_ledger_binding": _binding_for_package_file(
            carousel_dir,
            ATTEMPT_LEDGER,
        ),
    }
    proof_binding["binding_fingerprint"] = _canonical_fingerprint(proof_binding)

    carried_evidence: dict[str, Any] = {
        "proof_state": GenerationStatus.BATCH_ALLOWED.value,
        "accepted_proof_slide": proof_slide,
        "creator_override": True,
        "batch_generation_allowed": True,
        "creator_approval_path": approval_path,
        "creator_approval_binding": json.loads(json.dumps(approval_binding)),
        "creator_approval_sha256": approval_binding["sha256"],
        "creator_override_record": json.loads(json.dumps(approval_record)),
        "known_qa_exceptions": json.loads(json.dumps(known_exceptions)),
        "creator_override_proof_binding": proof_binding,
        "visual_qa_path": visual_qa_path,
        "visual_qa_status": "QA_FAILED",
        "visual_qa_issues": list(visual_qa_issues),
        "proof_qa_passed": False,
        "accepted_proof_image_set_sha256": current_image_set_sha256,
        "accepted_proof_quarantine_dir": expected_quarantine_dir,
        "promotion_blocker": "creator_override_allows_batch_generation_only",
    }
    return carried_evidence


def creator_override_batch_handoff_integrity_issues(
    carousel_dir: Path,
    *,
    state: Any,
    final_state: Any,
) -> list[str]:
    """Validate a prepared full-deck handoff against its accepted failed proof.

    The carried creator override is batch-only. It can suppress historical
    proof blockers only while both manifests describe the same non-publishable
    HANDOFF_READY deck and every immutable proof/approval binding still
    validates.
    """

    if not isinstance(state, dict) or not isinstance(final_state, dict):
        return ["creator-override handoff generation manifests are missing or malformed"]
    if state != final_state:
        return ["creator-override handoff generation manifests disagree"]

    issues: list[str] = []
    required_values = {
        "status": GenerationStatus.HANDOFF_READY.value,
        "proof_state": GenerationStatus.BATCH_ALLOWED.value,
        "proof_only": False,
        "requested_proof_slide": None,
        "creator_override": True,
        "batch_generation_allowed": True,
        "publishable": False,
        "done": False,
        "proof_qa_passed": False,
        "visual_qa_status": "QA_FAILED",
    }
    for key, expected in required_values.items():
        if state.get(key) != expected:
            issues.append(
                f"creator-override handoff {key} must remain {expected!r}"
            )

    try:
        current_formats = list(locked_formats(carousel_dir))
    except (ValueError, OSError, json.JSONDecodeError) as exc:
        issues.append(f"creator-override handoff format lock is invalid: {exc}")
        current_formats = []
    if state.get("requested_formats") != current_formats:
        issues.append(
            "creator-override handoff requested formats disagree with the current format lock"
        )

    try:
        prompt_pack = load_json(carousel_dir / "prompt-pack.json")
    except (FileNotFoundError, OSError, json.JSONDecodeError) as exc:
        issues.append(f"creator-override handoff prompt pack is invalid: {exc}")
        prompt_pack = {}
    prompt_slides = prompt_pack.get("slides") if isinstance(prompt_pack, dict) else None
    prompt_slide_numbers: list[int] = []
    if not isinstance(prompt_slides, list) or not prompt_slides:
        issues.append("creator-override handoff requires a non-empty full-deck prompt pack")
    else:
        try:
            prompt_slide_numbers = [int(slide["slide"]) for slide in prompt_slides]
        except (KeyError, TypeError, ValueError):
            issues.append("creator-override handoff prompt-pack slide numbers are invalid")
            prompt_slide_numbers = []
        if len(prompt_slide_numbers) != len(set(prompt_slide_numbers)):
            issues.append("creator-override handoff prompt-pack slide numbers repeat")

    handoff_slides = state.get("slides")
    handoff_slide_numbers: list[int] = []
    if not isinstance(handoff_slides, list):
        issues.append("creator-override handoff full-deck slide records are missing")
    else:
        try:
            handoff_slide_numbers = [int(slide["slide"]) for slide in handoff_slides]
        except (KeyError, TypeError, ValueError):
            issues.append("creator-override handoff full-deck slide records are malformed")
            handoff_slide_numbers = []
    if (
        not prompt_slide_numbers
        or handoff_slide_numbers != prompt_slide_numbers
        or state.get("slide_count") != len(prompt_slide_numbers)
        or state.get("total_slide_count") != len(prompt_slide_numbers)
    ):
        issues.append(
            "creator-override handoff does not cover the exact current full deck"
        )

    if (
        prompt_slide_numbers
        and len(prompt_slide_numbers) == len(set(prompt_slide_numbers))
        and current_formats
    ):
        try:
            compiled_handoff_issues = compiled_prompt_handoff_integrity_issues(
                carousel_dir,
                state=state,
                slides=prompt_slides,
                output_formats=current_formats,
            )
        except (KeyError, TypeError, ValueError, OSError, json.JSONDecodeError) as exc:
            issues.append(
                f"creator-override full-deck compiled handoff is invalid: {exc}"
            )
        else:
            issues.extend(
                "creator-override full-deck compiled handoff: " + issue
                for issue in compiled_handoff_issues
            )

    proof_binding = state.get("creator_override_proof_binding")
    if not isinstance(proof_binding, dict):
        issues.append("creator-override handoff proof binding is missing")
        return issues

    accepted_state = {
        "status": proof_binding.get("source_status"),
        "proof_state": proof_binding.get("proof_state"),
        "creator_override": state.get("creator_override"),
        "batch_generation_allowed": state.get("batch_generation_allowed"),
        "proof_only": True,
        "publishable": state.get("publishable"),
        "done": state.get("done"),
        "proof_qa_passed": state.get("proof_qa_passed"),
        "visual_qa_status": state.get("visual_qa_status"),
        "requested_proof_slide": proof_binding.get("proof_slide"),
        "retry_count": proof_binding.get("retry_count"),
        "slides": [proof_binding.get("proof_slide_record")],
        "requested_formats": proof_binding.get("requested_formats"),
        "total_slide_count": state.get("total_slide_count"),
        "image_set_sha256": proof_binding.get("image_set_sha256"),
        "quarantine_dir": proof_binding.get("quarantine_dir"),
        "visual_qa_issues": state.get("visual_qa_issues"),
        "creator_approval_binding": state.get("creator_approval_binding"),
        "creator_approval_path": state.get("creator_approval_path"),
        "creator_approval_sha256": state.get("creator_approval_sha256"),
        "creator_override_record": state.get("creator_override_record"),
        "known_qa_exceptions": state.get("known_qa_exceptions"),
        "visual_qa_path": state.get("visual_qa_path"),
    }
    try:
        expected_evidence = _creator_override_batch_handoff_evidence(
            carousel_dir,
            requested_formats=current_formats,
            _accepted_state=accepted_state,
        )
    except ValueError as exc:
        issues.append(f"creator-override accepted-proof evidence is invalid: {exc}")
        return issues

    for key, expected in expected_evidence.items():
        if state.get(key) != expected:
            issues.append(
                f"creator-override handoff carried evidence is stale: {key}"
            )
    return issues


def _validated_creator_override_origin_handoff(
    carousel_dir: Path,
    *,
    lifecycle_state: dict[str, Any],
    final_state: dict[str, Any],
) -> tuple[dict[str, Any], str] | None:
    """Return the immutable override handoff behind a full-deck lifecycle."""

    if lifecycle_state.get("generation_scope") == CREATOR_OVERRIDE_FULL_DECK_SCOPE:
        if lifecycle_state != final_state:
            raise ValueError(
                "Creator-override full-deck generation manifests disagree."
            )
        snapshot = lifecycle_state.get("creator_override_origin_handoff")
        fingerprint = lifecycle_state.get("creator_override_origin_handoff_fingerprint")
        if (
            not isinstance(snapshot, dict)
            or fingerprint != _canonical_fingerprint(snapshot)
        ):
            raise ValueError(
                "Creator-override full-deck origin handoff is missing or tampered."
            )
        if lifecycle_state.get("compiled_prompt_handoff") != snapshot.get(
            "compiled_prompt_handoff"
        ):
            raise ValueError(
                "Creator-override full-deck compiled handoff changed after source acceptance."
            )
    elif (
        lifecycle_state.get("status") == GenerationStatus.HANDOFF_READY.value
        and lifecycle_state.get("creator_override") is True
    ):
        snapshot = json.loads(json.dumps(lifecycle_state))
        fingerprint = _canonical_fingerprint(snapshot)
    else:
        return None

    integrity_issues = creator_override_batch_handoff_integrity_issues(
        carousel_dir,
        state=snapshot,
        final_state=(
            final_state
            if lifecycle_state.get("status") == GenerationStatus.HANDOFF_READY.value
            else snapshot
        ),
    )
    if integrity_issues:
        raise ValueError(
            "Creator-override full-deck handoff integrity failed: "
            + "; ".join(integrity_issues)
        )
    return snapshot, fingerprint


def _approved_proof_batch_handoff_evidence(
    carousel_dir: Path,
    *,
    requested_formats: list[str] | None,
) -> dict[str, Any]:
    """Archive and bind one QA-passed creator-approved proof before full-deck compile."""

    carousel_dir = carousel_dir.expanduser().resolve()
    state_path = carousel_dir / "image-generation.json"
    final_state_path = carousel_dir / "final-images.json"
    try:
        state = json.loads(state_path.read_bytes())
        final_state = json.loads(final_state_path.read_bytes())
    except (FileNotFoundError, OSError, json.JSONDecodeError) as exc:
        raise ValueError(
            "Approved-proof full-deck handoff requires matching generation manifests."
        ) from exc
    if not isinstance(state, dict) or state != final_state:
        raise ValueError(
            "Approved-proof full-deck handoff requires image-generation.json and "
            "final-images.json to contain the same current state."
        )
    if (
        state.get("status") != GenerationStatus.BATCH_ALLOWED.value
        or state.get("proof_state")
        != GenerationStatus.CREATOR_APPROVED_PROOF.value
        or state.get("proof_only") is not True
        or state.get("publishable") is not False
        or state.get("done") is not False
    ):
        raise ValueError(
            "Approved-proof full-deck handoff requires the exact non-publishable "
            "QA-passed proof state."
        )

    current_formats = list(locked_formats(carousel_dir))
    if state.get("requested_formats") != current_formats:
        raise ValueError(
            "Approved-proof formats disagree with the current format lock."
        )
    if requested_formats is not None:
        supplied_formats = list(normalize_requested_formats(requested_formats))
        if supplied_formats != current_formats:
            raise ValueError(
                "Requested full-deck formats disagree with the approved proof."
            )

    proof_records = state.get("slides")
    if not isinstance(proof_records, list) or len(proof_records) != 1:
        raise ValueError("Approved-proof handoff must bind exactly one proof slide.")
    try:
        proof_slide = int(state["requested_proof_slide"])
        record_slide = int(proof_records[0]["slide"])
    except (KeyError, TypeError, ValueError) as exc:
        raise ValueError("Approved-proof slide evidence is malformed.") from exc
    if proof_slide != record_slide:
        raise ValueError("Approved-proof slide record does not match its selected proof.")
    quarantine_issues = validate_quarantine_integrity(
        proof_records,
        tuple(current_formats),
        carousel_dir=carousel_dir,
    )
    if quarantine_issues:
        raise ValueError(
            "Approved-proof quarantine integrity failed: "
            + "; ".join(quarantine_issues)
        )
    if state.get("image_set_sha256") != image_set_sha256(proof_records):
        raise ValueError("Approved-proof image-set binding is stale.")

    visual_qa_path = resolve_package_artifact_path(
        carousel_dir,
        state.get("visual_qa_path"),
        "visual-qa.json",
    )
    visual_qa_binding, visual_qa_bytes = _read_creator_override_package_file(
        carousel_dir,
        visual_qa_path,
        label="Approved-proof visual QA",
    )
    try:
        visual_qa = json.loads(visual_qa_bytes)
    except json.JSONDecodeError as exc:
        raise ValueError("Approved-proof visual QA is malformed.") from exc
    qa_issues = validate_exact_image_visual_qa(
        visual_qa,
        proof_records,
        visual_plan=load_json(carousel_dir / "visual-plan-quality.json"),
        carousel_dir=carousel_dir,
    )
    if qa_issues:
        raise ValueError(
            "Approved-proof visual QA is no longer valid: " + "; ".join(qa_issues)
        )

    approval_binding, approval_bytes = _read_creator_override_package_file(
        carousel_dir,
        state.get("creator_approval_path") or "creator-proof-approval.json",
        label="Approved-proof creator approval",
    )
    if state.get("creator_approval_sha256") != approval_binding["sha256"]:
        raise ValueError("Approved-proof creator approval binding is stale.")
    try:
        approval = json.loads(approval_bytes)
    except json.JSONDecodeError as exc:
        raise ValueError("Approved-proof creator approval is malformed.") from exc
    approval_issues = validate_creator_approval(
        approval,
        expected_image_set_sha256=state["image_set_sha256"],
    )
    if approval_issues:
        raise ValueError(
            "Approved-proof creator approval is invalid: "
            + "; ".join(approval_issues)
        )

    latest_attempts = load_attempt_ledger(carousel_dir).get("attempts")
    latest_attempt = latest_attempts[-1] if isinstance(latest_attempts, list) and latest_attempts else None
    if (
        not isinstance(latest_attempt, dict)
        or latest_attempt.get("status") != GenerationStatus.BATCH_ALLOWED.value
        or latest_attempt.get("image_set_sha256") != state["image_set_sha256"]
    ):
        raise ValueError("Approved-proof attempt ledger is stale or incomplete.")

    archive_dir = carousel_dir / ".internal" / "approved-proof"
    archive_dir.mkdir(parents=True, exist_ok=True)
    archive_files = {
        archive_dir / "visual-qa.json": visual_qa_bytes,
        archive_dir / "creator-approval.json": approval_bytes,
    }
    for archive_path, payload in archive_files.items():
        if archive_path.exists() and archive_path.read_bytes() != payload:
            raise ValueError(
                f"Approved-proof archive already exists with different bytes: {archive_path.name}"
            )
        if not archive_path.exists():
            archive_path.write_bytes(payload)

    archived_visual_qa_binding = _binding_for_package_file(
        carousel_dir,
        ".internal/approved-proof/visual-qa.json",
    )
    archived_approval_binding = _binding_for_package_file(
        carousel_dir,
        ".internal/approved-proof/creator-approval.json",
    )
    quarantine_bindings: list[dict[str, str]] = []
    for proof_record in proof_records:
        outputs = proof_record.get("native_outputs")
        if not isinstance(outputs, dict):
            raise ValueError("Approved-proof native output bindings are missing.")
        for output in outputs.values():
            if not isinstance(output, dict) or not isinstance(output.get("path"), str):
                raise ValueError("Approved-proof native output binding is malformed.")
            quarantine_bindings.append(
                _binding_for_package_file(carousel_dir, output["path"])
            )

    source_handoff = state.get("compiled_prompt_handoff")
    if not isinstance(source_handoff, dict):
        raise ValueError("Approved-proof compiled prompt handoff is missing.")
    source_handoff_payload = {
        key: value
        for key, value in source_handoff.items()
        if key != "handoff_set_fingerprint"
    }
    if source_handoff.get("handoff_set_fingerprint") != _canonical_fingerprint(
        source_handoff_payload
    ):
        raise ValueError("Approved-proof compiled handoff fingerprint is stale.")
    for input_name, expected_path in (
        ("prompt_pack", "prompt-pack.json"),
        ("slides", "slides.json"),
    ):
        input_binding = source_handoff.get("input_bindings", {}).get(input_name)
        binding_issues = _bound_package_file_issues(
            carousel_dir,
            input_binding,
            expected_relative_path=expected_path,
        )
        if binding_issues:
            raise ValueError(
                "Approved-proof compiled handoff input changed: "
                + "; ".join(binding_issues)
            )
    proof_prompt_slides = [
        slide
        for slide in load_json(carousel_dir / "prompt-pack.json").get("slides", [])
        if int(slide.get("slide", 0) or 0) == proof_slide
    ]
    if (carousel_dir / PROMPT_HANDOFF_ACTIVE_FOLDER).exists():
        handoff_issues = compiled_prompt_handoff_integrity_issues(
            carousel_dir,
            state=state,
            slides=proof_prompt_slides,
            output_formats=current_formats,
        )
        if handoff_issues:
            raise ValueError(
                "Approved-proof compiled handoff is invalid: "
                + "; ".join(handoff_issues)
            )

    payload = {
        "schema_version": APPROVED_PROOF_BATCH_HANDOFF_SCHEMA_VERSION,
        "proof_slide": proof_slide,
        "requested_formats": current_formats,
        "image_set_sha256": state["image_set_sha256"],
        "source_handoff_set_fingerprint": source_handoff.get(
            "handoff_set_fingerprint"
        ),
        "visual_qa_binding": archived_visual_qa_binding,
        "creator_approval_binding": archived_approval_binding,
        "quarantine_bindings": quarantine_bindings,
    }
    return {
        **payload,
        "attestation_fingerprint": _canonical_fingerprint(payload),
    }


def _archive_approved_proof_batch_handoff_evidence(
    carousel_dir: Path,
    evidence: dict[str, Any],
) -> None:
    """Keep the immutable proof handoff across a later compile failure."""

    archive_path = carousel_dir / APPROVED_PROOF_BATCH_HANDOFF_ARCHIVE
    archive_path.parent.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(evidence, indent=2, ensure_ascii=False).encode("utf-8")
    if archive_path.exists():
        try:
            existing = json.loads(archive_path.read_bytes())
        except (OSError, json.JSONDecodeError) as exc:
            raise ValueError("Approved-proof handoff archive is malformed.") from exc
        if existing != evidence:
            raise ValueError(
                "Approved-proof handoff archive already exists with different evidence."
            )
        return
    archive_path.write_bytes(payload)


def _recover_approved_proof_batch_handoff_evidence(
    carousel_dir: Path,
    *,
    requested_formats: list[str] | None,
) -> dict[str, Any]:
    """Recover an approved-proof attestation after a failed prompt recompile.

    The proof image, original QA, creator approval, and attempt ledger are all
    immutable package evidence.  A transient compile failure must not erase
    that approval and force the creator to approve the same hash again.
    """

    carousel_dir = carousel_dir.expanduser().resolve()
    current_formats = list(locked_formats(carousel_dir))
    if requested_formats is not None:
        supplied_formats = list(normalize_requested_formats(requested_formats))
        if supplied_formats != current_formats:
            raise ValueError(
                "Requested full-deck formats disagree with the archived approved proof."
            )

    archive_path = carousel_dir / APPROVED_PROOF_BATCH_HANDOFF_ARCHIVE
    if archive_path.exists():
        try:
            evidence = json.loads(archive_path.read_bytes())
        except (OSError, json.JSONDecodeError) as exc:
            raise ValueError("Approved-proof handoff archive is malformed.") from exc
        state = {
            "requested_formats": current_formats,
            "approved_proof_batch_handoff_attestation": evidence,
        }
        issues = approved_proof_batch_handoff_attestation_issues(
            carousel_dir,
            state=state,
        )
        if issues:
            raise ValueError(
                "Archived approved-proof handoff is invalid: " + "; ".join(issues)
            )
        return evidence

    visual_qa_path = carousel_dir / ".internal" / "approved-proof" / "visual-qa.json"
    approval_path = carousel_dir / ".internal" / "approved-proof" / "creator-approval.json"
    try:
        visual_qa = json.loads(visual_qa_path.read_bytes())
        approval = json.loads(approval_path.read_bytes())
    except (FileNotFoundError, OSError, json.JSONDecodeError) as exc:
        raise ValueError(
            "Approved-proof recovery requires the immutable QA and creator-approval archive."
        ) from exc
    if not isinstance(visual_qa, dict) or not isinstance(approval, dict):
        raise ValueError("Approved-proof recovery archive is malformed.")

    approved_image_set = str(approval.get("image_set_sha256") or "")
    approval_issues = validate_creator_approval(
        approval,
        expected_image_set_sha256=approved_image_set,
    )
    if approval_issues:
        raise ValueError(
            "Archived approved-proof creator approval is invalid: "
            + "; ".join(approval_issues)
        )
    attempts = load_attempt_ledger(carousel_dir).get("attempts")
    latest_attempt = attempts[-1] if isinstance(attempts, list) and attempts else None
    if (
        not isinstance(latest_attempt, dict)
        or latest_attempt.get("status") != GenerationStatus.BATCH_ALLOWED.value
        or latest_attempt.get("image_set_sha256") != approved_image_set
    ):
        raise ValueError("Archived approved-proof attempt ledger is stale or incomplete.")

    readability = (visual_qa.get("checks") or {}).get(VISUAL_STORY_READABILITY_KEY)
    frames = readability.get("frames") if isinstance(readability, dict) else None
    if not isinstance(frames, list) or not frames:
        raise ValueError("Archived approved-proof QA is missing reviewed frame evidence.")
    proof_slides = {
        int(frame.get("slide", 0) or 0)
        for frame in frames
        if isinstance(frame, dict)
    }
    if len(proof_slides) != 1 or 0 in proof_slides:
        raise ValueError("Archived approved-proof QA must bind exactly one proof slide.")
    proof_slide = next(iter(proof_slides))

    native_outputs: dict[str, dict[str, Any]] = {}
    quarantine_bindings: list[dict[str, str]] = []
    quarantine_root = carousel_dir / ".internal" / "visual-quarantine"
    for output_format in current_formats:
        matching_frames = [
            frame
            for frame in frames
            if isinstance(frame, dict)
            and int(frame.get("slide", 0) or 0) == proof_slide
            and frame.get("format") == output_format
        ]
        if len(matching_frames) != 1:
            raise ValueError(
                f"Archived approved-proof QA must bind one {output_format} frame."
            )
        expected_hash = str(matching_frames[0].get("image_fingerprint") or "")
        if expected_hash.startswith("sha256:"):
            expected_hash = expected_hash.removeprefix("sha256:")
        candidates = []
        for candidate in quarantine_root.rglob(f"slide-{proof_slide:02d}.png"):
            if candidate.is_symlink() or not candidate.is_file():
                continue
            try:
                payload = candidate.read_bytes()
            except OSError:
                continue
            if sha256_bytes(payload) == expected_hash:
                candidates.append((candidate, payload))
        if not candidates:
            raise ValueError(
                f"Archived approved-proof image is missing for {output_format}."
            )
        candidate, payload = sorted(candidates, key=lambda item: item[0].as_posix())[0]
        dimensions = image_dimensions(payload)
        native_outputs[output_format] = {
            "path": candidate.relative_to(carousel_dir).as_posix(),
            "sha256": expected_hash,
            "width": dimensions["width"],
            "height": dimensions["height"],
        }
        quarantine_bindings.append(
            _binding_for_package_file(
                carousel_dir,
                candidate.relative_to(carousel_dir).as_posix(),
            )
        )

    recovered_image_set = image_set_sha256(
        [{"slide": proof_slide, "native_outputs": native_outputs}]
    )
    if recovered_image_set != approved_image_set:
        raise ValueError("Archived approved-proof image-set binding is stale.")

    payload = {
        "schema_version": APPROVED_PROOF_BATCH_HANDOFF_SCHEMA_VERSION,
        "proof_slide": proof_slide,
        "requested_formats": current_formats,
        "image_set_sha256": approved_image_set,
        "source_handoff_set_fingerprint": None,
        "recovered_after_state_loss": True,
        "visual_qa_binding": _binding_for_package_file(
            carousel_dir,
            visual_qa_path.relative_to(carousel_dir).as_posix(),
        ),
        "creator_approval_binding": _binding_for_package_file(
            carousel_dir,
            approval_path.relative_to(carousel_dir).as_posix(),
        ),
        "quarantine_bindings": quarantine_bindings,
    }
    evidence = {
        **payload,
        "attestation_fingerprint": _canonical_fingerprint(payload),
    }
    _archive_approved_proof_batch_handoff_evidence(carousel_dir, evidence)
    return evidence


def prepare_codex_builtin_image_generation(
    carousel_dir: Path,
    *,
    proof_slide: int | None = None,
    formats: list[str] | None = None,
) -> dict[str, Any]:
    carousel_dir = carousel_dir.expanduser()
    prompt_dir = carousel_dir / PROMPT_HANDOFF_ACTIVE_FOLDER
    prompt_staging_dir = carousel_dir / PROMPT_HANDOFF_STAGING_FOLDER
    creator_override_evidence: dict[str, Any] | None = None
    approved_proof_evidence: dict[str, Any] | None = None
    full_deck_retry_evidence: dict[str, Any] | None = None
    try:
        existing_state = load_json(carousel_dir / "image-generation.json")
    except (FileNotFoundError, OSError, json.JSONDecodeError):
        existing_state = None
    if (
        isinstance(existing_state, dict)
        and existing_state.get("status")
        in {
            GenerationStatus.GENERATED_QUARANTINED.value,
            GenerationStatus.REJECTED_SPATIAL_INTEGRITY.value,
        }
        and existing_state.get("proof_only") is False
    ):
        if proof_slide is not None:
            raise ValueError(
                "QA-failed full-deck retry must recompile the full deck; "
                "proof_slide must be omitted."
            )
        final_state = load_json(carousel_dir / "final-images.json")
        if final_state != existing_state:
            raise ValueError(
                "QA-failed full-deck retry generation manifests disagree."
            )
        slide_records = existing_state.get("slides")
        if (
            not isinstance(slide_records, list)
            or len(slide_records) < 2
            or existing_state.get("slide_count") != len(slide_records)
            or existing_state.get("total_slide_count") != len(slide_records)
            or existing_state.get("image_set_sha256")
            != image_set_sha256(slide_records)
        ):
            raise ValueError(
                "QA-failed full-deck retry image-set evidence is incomplete or stale."
            )
        output_formats = list(locked_formats(carousel_dir))
        if existing_state.get("requested_formats") != output_formats:
            raise ValueError(
                "QA-failed full-deck retry formats disagree with the current format lock."
            )
        quarantine_issues = validate_quarantine_integrity(
            slide_records,
            output_formats,
            carousel_dir=carousel_dir,
        )
        if quarantine_issues:
            raise ValueError(
                "QA-failed full-deck retry quarantine evidence is inconsistent: "
                + "; ".join(quarantine_issues)
            )
        attempts = load_attempt_ledger(carousel_dir).get("attempts")
        latest_attempt = (
            attempts[-1] if isinstance(attempts, list) and attempts else None
        )
        state_issues = existing_state.get("visual_qa_issues")
        if (
            not isinstance(latest_attempt, dict)
            or latest_attempt.get("status") != "QA_FAILED"
            or latest_attempt.get("image_set_sha256")
            != existing_state.get("image_set_sha256")
            or latest_attempt.get("retry_count")
            != existing_state.get("retry_count")
            or not isinstance(state_issues, list)
            or not state_issues
            or latest_attempt.get("qa_issues") != state_issues
        ):
            raise ValueError(
                "QA-failed full-deck retry state and attempt ledger disagree."
            )
        qa_relative_path = existing_state.get("visual_qa_path")
        if not isinstance(qa_relative_path, str):
            raise ValueError(
                "QA-failed full-deck retry is missing its visual-QA artifact."
            )
        qa_binding = _binding_for_package_file(carousel_dir, qa_relative_path)
        qa_payload = load_json(carousel_dir / qa_relative_path)
        if (
            not isinstance(qa_payload, dict)
            or qa_payload.get("status") != "FAIL"
            or qa_payload.get("image_set_sha256")
            != existing_state.get("image_set_sha256")
        ):
            raise ValueError(
                "QA-failed full-deck retry visual-QA binding is stale or not failed."
            )
        next_retry = next_retry_count(
            carousel_dir,
            allow_approved_proof_batch=(
                carousel_dir / APPROVED_PROOF_BATCH_HANDOFF_ARCHIVE
            ).is_file(),
        )
        full_deck_retry_payload = {
            "schema_version": "qa-failed-full-deck-retry-handoff/v1",
            "source_status": existing_state["status"],
            "failed_image_set_sha256": existing_state["image_set_sha256"],
            "failed_attempt": latest_attempt,
            "visual_qa_binding": qa_binding,
            "next_retry_count": next_retry,
        }
        full_deck_retry_evidence = {
            **full_deck_retry_payload,
            "attestation_fingerprint": _canonical_fingerprint(
                full_deck_retry_payload
            ),
        }
    if (
        isinstance(existing_state, dict)
        and existing_state.get("status") == GenerationStatus.HANDOFF_READY.value
        and isinstance(
            existing_state.get("approved_proof_batch_handoff_attestation"),
            dict,
        )
    ):
        attestation_issues = approved_proof_batch_handoff_attestation_issues(
            carousel_dir,
            state=existing_state,
        )
        if attestation_issues:
            raise ValueError(
                "Approved-proof full-deck handoff cannot be recompiled: "
                + "; ".join(attestation_issues)
            )
        approved_proof_evidence = existing_state[
            "approved_proof_batch_handoff_attestation"
        ]
        retry_attestation = existing_state.get(
            "qa_failed_full_deck_retry_handoff_attestation"
        )
        if isinstance(retry_attestation, dict):
            retry_payload = {
                key: value
                for key, value in retry_attestation.items()
                if key != "attestation_fingerprint"
            }
            if retry_attestation.get(
                "attestation_fingerprint"
            ) != _canonical_fingerprint(retry_payload):
                raise ValueError(
                    "QA-failed full-deck retry handoff attestation is stale."
                )
            full_deck_retry_evidence = retry_attestation
    if (
        isinstance(existing_state, dict)
        and existing_state.get("status") == GenerationStatus.BATCH_ALLOWED.value
    ):
        if proof_slide is not None:
            raise ValueError(
                "Creator-override BATCH_ALLOWED can compile only the full deck; "
                "proof_slide must be omitted."
            )
        if (
            existing_state.get("proof_state")
            == GenerationStatus.CREATOR_APPROVED_PROOF.value
            and existing_state.get("creator_override") is not True
        ):
            approved_proof_evidence = _approved_proof_batch_handoff_evidence(
                carousel_dir,
                requested_formats=formats,
            )
        else:
            creator_override_evidence = _creator_override_batch_handoff_evidence(
                carousel_dir,
                requested_formats=formats,
            )

    if approved_proof_evidence is not None:
        _archive_approved_proof_batch_handoff_evidence(
            carousel_dir,
            approved_proof_evidence,
        )
    elif (
        creator_override_evidence is None
        and proof_slide is None
        and (carousel_dir / ".internal" / "approved-proof" / "visual-qa.json").is_file()
        and (carousel_dir / ".internal" / "approved-proof" / "creator-approval.json").is_file()
    ):
        approved_proof_evidence = _recover_approved_proof_batch_handoff_evidence(
            carousel_dir,
            requested_formats=formats,
        )

    preserves_approved_proof = (
        creator_override_evidence is not None or approved_proof_evidence is not None
    )

    # A previous active set is executable by a human or agent. Invalidate it
    # before reading any mutable prerequisite so a blocked recompilation can
    # never leave stale prompts available for use. A creator-override transition
    # validates every immutable proof/approval binding first and keeps the prior
    # proof-only set intact if a prerequisite blocks the full-deck compilation.
    if not preserves_approved_proof:
        remove_path_without_following(prompt_dir)
    remove_path_without_following(prompt_staging_dir)
    if preserves_approved_proof:
        format_contract = load_format_contract(carousel_dir)
    elif formats is not None:
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

    def blocked_result(reason: str) -> dict[str, Any]:
        if creator_override_evidence is not None:
            raise ValueError(
                "Creator-override full-deck handoff remains blocked: " + reason
            )
        return write_blocked_status(carousel_dir, reason)

    visual_quality_reason = visual_plan_quality_gate_reason(carousel_dir)
    if visual_quality_reason:
        return blocked_result(visual_quality_reason)

    identity_reason = identity_consistency_gate_reason(carousel_dir)
    if identity_reason:
        return blocked_result(identity_reason)

    style_consistency_reason = house_style_consistency_gate_reason(prompt_pack)
    if style_consistency_reason:
        return blocked_result(style_consistency_reason)

    layer_e_reason = layer_e_gate_reason(carousel_dir)
    if layer_e_reason:
        return blocked_result(layer_e_reason)

    package_review_reason = pre_generation_review_gate_reason(carousel_dir)
    if package_review_reason:
        return blocked_result(package_review_reason)

    dossier_paths = existing_paths(prompt_pack.get("identity_dossier_reference_images", []))
    identity_paths = existing_paths(prompt_pack.get("identity_reference_images", []))
    if not dossier_paths:
        return blocked_result(
            "Codex built-in image generation requires identity-face-contact-sheet.jpg as an actual image input.",
        )
    if not identity_paths:
        return blocked_result(
            "Codex built-in image generation requires selected identity images as actual image inputs.",
        )

    style_paths = [
        path
        for path in existing_reference_paths({"style_reference_images": prompt_pack.get("style_reference_images", [])})
        if path not in identity_paths
    ]
    if preserves_approved_proof:
        remove_path_without_following(prompt_dir)
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
                    return blocked_result(
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
        state_extra: dict[str, Any] = {
            "proof_gate": prompt_pack.get("proof_gate"),
            "requested_proof_slide": proof_slide,
            "proof_only": proof_slide is not None,
            "total_slide_count": total_prompt_pack_slide_count,
            "requested_formats": output_formats,
            "native_output_contract": native_output_contract(output_formats),
            "generation_capability": generation_capability,
            "prompt_dir": PROMPT_HANDOFF_ACTIVE_FOLDER,
            "compiled_prompt_handoff": compiled_handoff,
            "identity_reference_requirement": (
                "Load/view identity-face-contact-sheet.jpg and selected identity images before every "
                "Codex image generation call; the final art must preserve Aachu/Zuv face structure."
            ),
        }
        if creator_override_evidence is not None:
            state_extra.update(creator_override_evidence)
        if approved_proof_evidence is not None:
            state_extra["approved_proof_batch_handoff_attestation"] = (
                approved_proof_evidence
            )
        if full_deck_retry_evidence is not None:
            state_extra["qa_failed_full_deck_retry_handoff_attestation"] = (
                full_deck_retry_evidence
            )

        result = write_generation_state(
            carousel_dir,
            status=GenerationStatus.HANDOFF_READY,
            backend=BACKEND,
            generation_mode=GENERATION_MODE,
            slide_count=len(slides),
            reason=(
                "Full-deck prompt files are ready under the creator's bound failed-proof "
                "acceptance; the known proof exceptions remain QA_FAILED and no image is "
                "publishable."
                if creator_override_evidence is not None
                else "Full-deck prompt files are ready from the exact QA-passed, creator-approved proof; final PNGs still require Codex built-in image generation."
                if approved_proof_evidence is not None
                else "Prompt files are ready; final PNGs still require Codex built-in image generation."
            ),
            slides=records,
            extra=state_extra,
            creator_override_handoff_validated=(
                creator_override_evidence is not None
                or approved_proof_evidence is not None
            ),
            qa_failed_full_deck_retry_handoff_validated=(
                full_deck_retry_evidence is not None
            ),
        )
        write_handoff_blocker(carousel_dir, result, prompt_pack.get("proof_gate"))
        handoff_complete = True
        return result
    finally:
        remove_path_without_following(prompt_staging_dir)
        if not handoff_complete:
            remove_path_without_following(prompt_dir)


def _failed_proof_retry_context(
    carousel_dir: Path,
) -> tuple[dict[str, Any], dict[str, Any], int, list[str], Path]:
    """Load and cross-check the immutable evidence for one failed proof."""

    state_path = carousel_dir / "image-generation.json"
    final_state_path = carousel_dir / "final-images.json"
    try:
        state = load_json(state_path)
        final_state = load_json(final_state_path)
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError("Failed-proof retry requires both generation state manifests.") from exc
    if state != final_state:
        raise ValueError("Failed-proof retry generation state manifests disagree.")
    if state.get("status") not in {
        GenerationStatus.GENERATED_QUARANTINED.value,
        GenerationStatus.REJECTED_SPATIAL_INTEGRITY.value,
    }:
        raise ValueError(
            "Failed-proof handoff recompile requires GENERATED_QUARANTINED or "
            "REJECTED_SPATIAL_INTEGRITY."
        )
    if not _failed_proof_retry_scope(state):
        raise ValueError(
            "Failed-proof handoff recompile requires a proof-only state with persisted QA failures."
        )
    try:
        proof_slide = int(state["requested_proof_slide"])
    except (KeyError, TypeError, ValueError) as exc:
        raise ValueError("Failed-proof retry is missing its selected proof slide.") from exc

    output_formats = list(locked_formats(carousel_dir))
    if state.get("requested_formats") != output_formats:
        raise ValueError("Failed-proof retry formats disagree with the current format lock.")
    if state.get("proof_state") != state.get("status"):
        raise ValueError("Failed-proof retry lifecycle status and proof_state disagree.")
    if state.get("slide_count") != 1:
        raise ValueError("Failed-proof retry state must contain exactly one proof slide.")
    slide_records = state.get("slides")
    if (
        not isinstance(slide_records, list)
        or len(slide_records) != 1
        or int(slide_records[0].get("slide", 0) or 0) != proof_slide
    ):
        raise ValueError("Failed-proof retry state does not contain its selected proof slide.")
    if image_set_sha256(slide_records) != state.get("image_set_sha256"):
        raise ValueError("Failed-proof retry image-set binding is stale.")
    quarantine_issues = validate_quarantine_integrity(
        slide_records,
        output_formats,
        carousel_dir=carousel_dir,
    )
    if quarantine_issues:
        raise ValueError(
            "Failed-proof retry quarantine evidence is inconsistent: "
            + "; ".join(quarantine_issues)
        )

    ledger = load_attempt_ledger(carousel_dir)
    attempts = ledger["attempts"]
    if not attempts or not isinstance(attempts[-1], dict):
        raise ValueError("Failed-proof retry requires an attempt ledger entry.")
    failed_attempt = attempts[-1]
    if failed_attempt.get("status") != "QA_FAILED":
        raise ValueError("Failed-proof retry requires the latest ledger attempt to be QA_FAILED.")
    if failed_attempt.get("image_set_sha256") != state.get("image_set_sha256"):
        raise ValueError("Failed-proof retry state and ledger image-set bindings disagree.")
    if failed_attempt.get("retry_count") != state.get("retry_count"):
        raise ValueError("Failed-proof retry state and ledger retry counts disagree.")
    state_issues = state.get("visual_qa_issues")
    if (
        not isinstance(state_issues, list)
        or not state_issues
        or failed_attempt.get("qa_issues") != state_issues
    ):
        raise ValueError("Failed-proof retry state and ledger QA failure evidence disagree.")
    retry_count = next_retry_count(carousel_dir)
    if retry_count > MAX_VISUAL_QA_RETRIES:
        raise ValueError("Visual-QA retry limit is exhausted; handoff cannot be recompiled.")

    qa_relative_path = state.get("visual_qa_path")
    if not isinstance(qa_relative_path, str):
        raise ValueError("Failed-proof retry is missing its visual QA path.")
    _binding_for_package_file(carousel_dir, qa_relative_path)
    qa = load_json(carousel_dir / qa_relative_path)
    if not isinstance(qa, dict):
        raise ValueError("Failed-proof retry visual QA is malformed.")
    if qa.get("image_set_sha256") != state.get("image_set_sha256"):
        raise ValueError("Failed-proof retry visual QA belongs to a different image set.")
    visual_plan = load_json(carousel_dir / "visual-plan-quality.json")
    recomputed_qa_issues = validate_exact_image_visual_qa(
        qa,
        slide_records,
        visual_plan=visual_plan,
        carousel_dir=carousel_dir,
    )
    if not recomputed_qa_issues:
        raise ValueError(
            "Failed-proof retry visual QA no longer reproduces any validator failure."
        )

    expected_quarantine_dir = package_relative_path(
        carousel_dir,
        quarantine_dir(carousel_dir, int(state["retry_count"])),
    )
    if state.get("quarantine_dir") != expected_quarantine_dir:
        raise ValueError("Failed-proof retry quarantine directory binding is stale.")
    return state, failed_attempt, proof_slide, output_formats, carousel_dir / qa_relative_path


def _retry_source_handoff_issues(
    carousel_dir: Path,
    *,
    state: dict[str, Any],
    proof_slide: int,
    output_formats: list[str],
) -> list[str]:
    """Check the exposed source prompt set without requiring stale inputs to match."""

    handoff = state.get("compiled_prompt_handoff")
    if not isinstance(handoff, dict):
        return ["failed proof state is missing its prior compiled handoff"]
    issues: list[str] = []
    if handoff.get("schema_version") != PROMPT_HANDOFF_SCHEMA_VERSION:
        issues.append("prior compiled handoff schema is missing or unsupported")
    if handoff.get("requested_formats") != output_formats:
        issues.append("prior compiled handoff formats disagree with the failed proof")
    if handoff.get("slide_numbers") != [proof_slide]:
        issues.append("prior compiled handoff does not expose exactly the failed proof slide")
    fingerprint_payload = {
        "schema_version": handoff.get("schema_version"),
        "requested_formats": handoff.get("requested_formats"),
        "slide_numbers": handoff.get("slide_numbers"),
        "format_contract_fingerprint": handoff.get("format_contract_fingerprint"),
        "input_bindings": handoff.get("input_bindings"),
        "files": handoff.get("files"),
    }
    if handoff.get("handoff_set_fingerprint") != _canonical_fingerprint(
        fingerprint_payload
    ):
        issues.append("prior compiled handoff fingerprint is stale")

    expected = {
        prompt_handoff_relative_path(output_format, proof_slide, kind): (
            output_format,
            kind,
        )
        for output_format in output_formats
        for kind in ("generator_prompt", "handoff_markdown")
    }
    if (
        handoff.get("format_contract_fingerprint")
        != locked_format_contract_fingerprint(carousel_dir)
    ):
        issues.append("prior compiled handoff format fingerprint is stale")
    raw_files = handoff.get("files")
    if not isinstance(raw_files, list):
        return [*issues, "prior compiled handoff file bindings are missing"]
    seen: set[str] = set()
    for binding in raw_files:
        if not isinstance(binding, dict):
            issues.append("prior compiled handoff has a malformed file binding")
            continue
        relative_path = binding.get("relative_path")
        if not isinstance(relative_path, str) or relative_path not in expected:
            issues.append("prior compiled handoff has an unexpected file binding")
            continue
        if relative_path in seen:
            issues.append(f"prior compiled handoff repeats {relative_path}")
            continue
        seen.add(relative_path)
        expected_format, expected_kind = expected[relative_path]
        if (
            binding.get("slide") != proof_slide
            or binding.get("format") != expected_format
            or binding.get("kind") != expected_kind
        ):
            issues.append(f"prior compiled handoff metadata is stale for {relative_path}")
        issues.extend(
            _bound_package_file_issues(
                carousel_dir,
                binding,
                expected_relative_path=relative_path,
            )
        )
    if seen != set(expected):
        issues.append("prior compiled handoff does not bind the complete proof prompt set")
    active_root = carousel_dir / PROMPT_HANDOFF_ACTIVE_FOLDER
    actual = {
        path.relative_to(carousel_dir).as_posix()
        for path in active_root.rglob("*")
        if path.is_file() or path.is_symlink()
    }
    if actual != set(expected):
        issues.append("active prior prompt set contains missing or unbound files")
    return issues


def _raise_retry_gate_failure(label: str, reason: str | None) -> None:
    if reason:
        raise ValueError(f"Failed-proof handoff recompile {label} failed: {reason}")


def _retry_prompt_records(
    carousel_dir: Path,
    *,
    prompt_staging_dir: Path,
    slides: list[dict[str, Any]],
    output_formats: list[str],
    prompt_pack: dict[str, Any],
) -> list[dict[str, Any]]:
    """Compile a complete replacement prompt set without exposing it."""

    dossier_paths = existing_paths(prompt_pack.get("identity_dossier_reference_images", []))
    identity_paths = existing_paths(prompt_pack.get("identity_reference_images", []))
    if not dossier_paths:
        raise ValueError(
            "Failed-proof handoff recompile requires identity-face-contact-sheet.jpg "
            "as an actual image input."
        )
    if not identity_paths:
        raise ValueError(
            "Failed-proof handoff recompile requires selected identity images "
            "as actual image inputs."
        )
    style_paths = [
        path
        for path in existing_reference_paths(
            {"style_reference_images": prompt_pack.get("style_reference_images", [])}
        )
        if path not in identity_paths
    ]
    slide_plans = load_json(carousel_dir / "slides.json")
    records: list[dict[str, Any]] = []
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
        for output_format in output_formats:
            format_dir = format_prompt_dir_name(output_format)
            active_prompt_path = (
                carousel_dir
                / PROMPT_HANDOFF_ACTIVE_FOLDER
                / format_dir
                / f"slide-{number:02d}.md"
            )
            staging_prompt_path = (
                prompt_staging_dir / format_dir / f"slide-{number:02d}.md"
            )
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
                raise ValueError(
                    f"Compiled prompt constraints failed for slide {number:02d} "
                    f"{format_dir}: {gate.reason}"
                )
            active_generator_path = active_prompt_path.with_suffix(".prompt.txt")
            staging_prompt_path.write_text(
                prompt_file_text(
                    carousel_dir=carousel_dir,
                    slide_prompt=slide_prompt,
                    output_format=output_format,
                    generator_prompt_path=active_generator_path,
                    dossier_paths=dossier_paths,
                    identity_dossier_path=prompt_pack.get("identity_dossier_path"),
                    identity_preflight_path=prompt_pack.get(
                        "identity_generation_preflight_path"
                    ),
                    identity_paths=identity_paths,
                    source_paths=source_paths,
                    style_paths=style_paths,
                ),
                encoding="utf-8",
            )
            active_prompt_files[output_format] = active_prompt_path
        first_output_format = output_formats[0]
        records.append(
            {
                "slide": number,
                "copy": slide_prompt["text"],
                "status": "awaiting_codex_builtin_image",
                "generation_mode": GENERATION_MODE,
                "backend": BACKEND,
                "prompt_file": active_prompt_files[first_output_format]
                .relative_to(carousel_dir)
                .as_posix(),
                "prompt_files": {
                    key: path.relative_to(carousel_dir).as_posix()
                    for key, path in active_prompt_files.items()
                },
                "generator_prompt_files": {
                    key: path.with_suffix(".prompt.txt")
                    .relative_to(carousel_dir)
                    .as_posix()
                    for key, path in active_prompt_files.items()
                },
                "expected_file": expected_output_relative_path(
                    first_output_format, number
                ),
                "expected_files": {
                    output_format: expected_output_relative_path(output_format, number)
                    for output_format in output_formats
                },
                "identity_dossier_reference_images": [
                    str(path) for path in dossier_paths
                ],
                "identity_reference_images": [str(path) for path in identity_paths],
                "story_reference_images": [str(path) for path in source_paths],
                "style_reference_images": [str(path) for path in style_paths],
            }
        )
    return records


def recompile_failed_proof_handoff(carousel_dir: Path) -> dict[str, Any]:
    """Atomically replace only the compiled handoff for a QA-failed proof."""

    carousel_dir = Path(carousel_dir).expanduser()
    state, failed_attempt, proof_slide, output_formats, qa_path = (
        _failed_proof_retry_context(carousel_dir)
    )
    prompt_pack = load_json(carousel_dir / "prompt-pack.json")
    all_slides = prompt_pack.get("slides", [])
    slides = [
        slide
        for slide in all_slides
        if int(slide.get("slide", 0) or 0) == proof_slide
    ]
    if len(slides) != 1:
        raise ValueError(
            "Failed-proof retry slide is not present exactly once in prompt-pack.json."
        )
    if state.get("total_slide_count") != len(all_slides):
        raise ValueError("Failed-proof retry total slide count is stale.")
    if str(slides[0].get("text")) != str(state["slides"][0].get("copy")):
        raise ValueError("Failed-proof retry cannot change the exact proof copy.")
    source_handoff_issues = _retry_source_handoff_issues(
        carousel_dir,
        state=state,
        proof_slide=proof_slide,
        output_formats=output_formats,
    )
    if source_handoff_issues:
        raise ValueError(
            "Failed-proof retry prior handoff is inconsistent: "
            + "; ".join(source_handoff_issues)
        )

    _raise_retry_gate_failure(
        "visual-plan gate", visual_plan_quality_gate_reason(carousel_dir)
    )
    _raise_retry_gate_failure(
        "identity gate", identity_consistency_gate_reason(carousel_dir)
    )
    _raise_retry_gate_failure(
        "house-style gate", house_style_consistency_gate_reason(prompt_pack)
    )
    _raise_retry_gate_failure("Layer E gate", layer_e_gate_reason(carousel_dir))
    _raise_retry_gate_failure(
        "pre-generation review gate", pre_generation_review_gate_reason(carousel_dir)
    )
    gate_input_bindings = _retry_gate_input_bindings(carousel_dir)

    prompt_dir = carousel_dir / PROMPT_HANDOFF_ACTIVE_FOLDER
    prompt_staging_dir = carousel_dir / PROMPT_HANDOFF_STAGING_FOLDER
    if prompt_dir.is_symlink() or not prompt_dir.is_dir():
        raise ValueError("Failed-proof retry active prompt set is missing or unsafe.")
    for path in prompt_dir.rglob("*"):
        if path.is_symlink():
            raise ValueError("Failed-proof retry active prompt set contains a symlink.")
    remove_path_without_following(prompt_staging_dir)
    prompt_staging_dir.parent.mkdir(parents=True, exist_ok=True)
    prompt_staging_dir.mkdir()
    backup_dir = (
        carousel_dir
        / PROMPT_HANDOFF_BACKUP_FOLDER
        / f"attempt-{int(failed_attempt['attempt']):02d}"
    )
    if backup_dir.exists() or backup_dir.is_symlink():
        raise ValueError(
            "Immutable failed-attempt prompt backup already exists; refusing to overwrite it."
        )

    state_path = carousel_dir / "image-generation.json"
    final_state_path = carousel_dir / "final-images.json"
    transaction_id = uuid.uuid4().hex
    state_temp = carousel_dir / ".internal" / f".retry-state-{transaction_id}.json"
    final_state_temp = carousel_dir / ".internal" / f".retry-final-{transaction_id}.json"
    old_state_bytes = state_path.read_bytes()
    old_final_state_bytes = final_state_path.read_bytes()
    swapped = False
    try:
        _retry_prompt_records(
            carousel_dir,
            prompt_staging_dir=prompt_staging_dir,
            slides=slides,
            output_formats=output_formats,
            prompt_pack=prompt_pack,
        )
        replacement_handoff = build_compiled_prompt_handoff(
            carousel_dir,
            slide_numbers=[proof_slide],
            output_formats=output_formats,
            prompt_source_root=prompt_staging_dir,
        )

        backup_dir.parent.mkdir(parents=True, exist_ok=True)
        prompt_dir.replace(backup_dir)
        try:
            prompt_staging_dir.replace(prompt_dir)
        except Exception:
            backup_dir.replace(prompt_dir)
            raise
        swapped = True

        previous_prompt_files = [
            _binding_for_package_file(
                carousel_dir, path.relative_to(carousel_dir).as_posix()
            )
            for path in sorted(backup_dir.rglob("*"))
            if path.is_file()
        ]
        attestation: dict[str, Any] = {
            "schema_version": RETRY_HANDOFF_SCHEMA_VERSION,
            "source_status": state["status"],
            "proof_slide": proof_slide,
            "requested_formats": output_formats,
            "failed_image_set_sha256": state["image_set_sha256"],
            "failed_attempt": failed_attempt,
            "visual_qa_binding": _binding_for_package_file(
                carousel_dir, qa_path.relative_to(carousel_dir).as_posix()
            ),
            "attempt_ledger_binding": _binding_for_package_file(
                carousel_dir, ATTEMPT_LEDGER
            ),
            "gate_input_bindings": gate_input_bindings,
            "previous_handoff_set_fingerprint": (
                state.get("compiled_prompt_handoff", {}).get(
                    "handoff_set_fingerprint"
                )
            ),
            "replacement_handoff_set_fingerprint": replacement_handoff[
                "handoff_set_fingerprint"
            ],
            "previous_prompt_backup_dir": backup_dir.relative_to(
                carousel_dir
            ).as_posix(),
            "previous_prompt_files": previous_prompt_files,
            "next_retry_count": len(load_attempt_ledger(carousel_dir)["attempts"]),
        }
        attestation["attestation_fingerprint"] = _canonical_fingerprint(attestation)
        updated_state = json.loads(json.dumps(state))
        updated_state["compiled_prompt_handoff"] = replacement_handoff
        updated_state["retry_prompt_handoff_attestation"] = attestation
        write_json(state_temp, updated_state)
        write_json(final_state_temp, updated_state)
        state_temp.replace(state_path)
        final_state_temp.replace(final_state_path)
        return updated_state
    except Exception:
        if swapped:
            remove_path_without_following(prompt_dir)
            if backup_dir.exists():
                backup_dir.replace(prompt_dir)
        state_path.write_bytes(old_state_bytes)
        final_state_path.write_bytes(old_final_state_bytes)
        raise
    finally:
        remove_path_without_following(prompt_staging_dir)
        remove_path_without_following(state_temp)
        remove_path_without_following(final_state_temp)


def _read_creator_override_package_file(
    carousel_dir: Path,
    raw_path: str | Path,
    *,
    label: str,
) -> tuple[dict[str, str], bytes]:
    """Read one immutable, package-contained approval artifact."""

    package_root = carousel_dir.expanduser().resolve()
    supplied = Path(raw_path).expanduser()
    if ".." in supplied.parts:
        raise ValueError(f"{label} path cannot traverse outside the carousel package.")
    candidate = supplied if supplied.is_absolute() else package_root / supplied
    try:
        lexical_relative = candidate.absolute().relative_to(package_root)
    except ValueError as exc:
        raise ValueError(f"{label} must be stored inside the carousel package.") from exc

    cursor = package_root
    for part in lexical_relative.parts:
        cursor = cursor / part
        if cursor.is_symlink():
            raise ValueError(f"{label} path cannot contain a symlink.")
    try:
        resolved = candidate.resolve(strict=True)
        relative_path = resolved.relative_to(package_root).as_posix()
    except (FileNotFoundError, OSError, ValueError) as exc:
        raise ValueError(
            f"{label} is missing or escapes the carousel package."
        ) from exc
    if not resolved.is_file():
        raise ValueError(f"{label} must be a regular file.")
    payload = resolved.read_bytes()
    return {
        "relative_path": relative_path,
        "sha256": sha256_binding(payload),
    }, payload


def _read_full_deck_approval_file(
    carousel_dir: Path,
    raw_path: str | Path,
    *,
    allow_legacy_package_prefix: bool,
) -> tuple[Path, dict[str, str], bytes]:
    """Read a canonical approval, decoding one historical relative path shape."""

    try:
        binding, payload = _read_creator_override_package_file(
            carousel_dir,
            raw_path,
            label="Full-deck creator approval",
        )
    except ValueError:
        supplied = Path(raw_path).expanduser()
        package_arg = Path(carousel_dir).expanduser()
        legacy_suffix = (".internal", "full-deck-creator-approval.json")
        legacy_prefix = supplied.parts[: -len(legacy_suffix)]
        package_root_parts = carousel_dir.expanduser().resolve().parts
        prefix_matches_package = bool(legacy_prefix) and (
            (
                not package_arg.is_absolute()
                and legacy_prefix == package_arg.parts
            )
            or (
                package_arg.is_absolute()
                and len(legacy_prefix) <= len(package_root_parts)
                and tuple(package_root_parts[-len(legacy_prefix) :])
                == legacy_prefix
            )
        )
        if (
            not allow_legacy_package_prefix
            or supplied.is_absolute()
            or ".." in supplied.parts
            or tuple(supplied.parts[-len(legacy_suffix) :]) != legacy_suffix
            or not prefix_matches_package
        ):
            raise
        legacy_relative = Path(*legacy_suffix)
        binding, payload = _read_creator_override_package_file(
            carousel_dir,
            legacy_relative,
            label="Legacy full-deck creator approval",
        )
    resolved = carousel_dir.expanduser().resolve() / binding["relative_path"]
    return resolved, binding, payload


def accept_failed_proof_by_creator(
    carousel_dir: Path,
    approval_path: str | Path,
) -> dict[str, Any]:
    """Allow batch generation after explicit acceptance of one exact failed proof.

    This is intentionally not a QA promotion. The failed QA artifact, issue
    list, and QA_FAILED ledger evidence remain intact and publishability stays
    false. The creator approval only permits generation of the rest of the
    batch with the acknowledged proof exceptions.
    """

    carousel_dir = Path(carousel_dir).expanduser()
    state_path = carousel_dir / "image-generation.json"
    final_state_path = carousel_dir / "final-images.json"
    ledger_path = attempt_ledger_path(carousel_dir)
    try:
        old_state_bytes = state_path.read_bytes()
        old_final_state_bytes = final_state_path.read_bytes()
        old_ledger_bytes = ledger_path.read_bytes()
        state = json.loads(old_state_bytes)
        final_state = json.loads(old_final_state_bytes)
        ledger = json.loads(old_ledger_bytes)
    except (FileNotFoundError, OSError, json.JSONDecodeError) as exc:
        raise ValueError(
            "Creator failed-proof acceptance requires matching generation manifests "
            "and an existing attempt ledger."
        ) from exc
    if not isinstance(state, dict) or state != final_state:
        raise ValueError(
            "Creator failed-proof acceptance requires image-generation.json and "
            "final-images.json to contain the same current state."
        )

    source_status = state.get("status")
    allowed_source_statuses = {
        GenerationStatus.BLOCKED_VISUAL_QA.value,
        GenerationStatus.REJECTED_SPATIAL_INTEGRITY.value,
    }
    if source_status not in allowed_source_statuses:
        raise ValueError(
            "Creator failed-proof acceptance requires BLOCKED_VISUAL_QA or "
            "REJECTED_SPATIAL_INTEGRITY."
        )
    if state.get("proof_state") != source_status:
        raise ValueError(
            "Creator failed-proof acceptance requires status and proof_state to agree."
        )
    if state.get("proof_only") is not True:
        raise ValueError(
            "Creator failed-proof acceptance is available only for a proof-only run."
        )

    try:
        proof_slide = int(state["requested_proof_slide"])
        retry_count = int(state["retry_count"])
    except (KeyError, TypeError, ValueError) as exc:
        raise ValueError(
            "Creator failed-proof acceptance is missing proof-slide or retry evidence."
        ) from exc
    slides = state.get("slides")
    if (
        not isinstance(slides, list)
        or len(slides) != 1
        or not isinstance(slides[0], dict)
        or int(slides[0].get("slide", 0) or 0) != proof_slide
    ):
        raise ValueError(
            "Creator failed-proof acceptance requires exactly the selected proof slide."
        )

    output_formats = list(locked_formats(carousel_dir))
    if state.get("requested_formats") != output_formats:
        raise ValueError(
            "Creator failed-proof acceptance formats disagree with the current format lock."
        )
    quarantine_issues = validate_quarantine_integrity(
        slides,
        output_formats,
        carousel_dir=carousel_dir,
    )
    if quarantine_issues:
        raise ValueError(
            "Creator failed-proof acceptance quarantine integrity failed: "
            + "; ".join(quarantine_issues)
        )
    current_image_set_sha256 = image_set_sha256(slides)
    if state.get("image_set_sha256") != current_image_set_sha256:
        raise ValueError(
            "Creator failed-proof acceptance image-set binding is stale."
        )
    expected_quarantine_dir = package_relative_path(
        carousel_dir,
        quarantine_dir(carousel_dir, retry_count),
    )
    if state.get("quarantine_dir") != expected_quarantine_dir:
        raise ValueError(
            "Creator failed-proof acceptance quarantine directory binding is stale."
        )

    attempts = ledger.get("attempts") if isinstance(ledger, dict) else None
    if not isinstance(attempts, list) or not attempts or not isinstance(
        attempts[-1], dict
    ):
        raise ValueError(
            "Creator failed-proof acceptance requires a current ledger attempt."
        )
    failed_attempt = attempts[-1]
    if failed_attempt.get("status") != "QA_FAILED":
        raise ValueError(
            "Creator failed-proof acceptance requires the latest attempt to remain QA_FAILED."
        )
    if failed_attempt.get("image_set_sha256") != current_image_set_sha256:
        raise ValueError(
            "Creator failed-proof acceptance state and ledger image-set bindings disagree."
        )
    if failed_attempt.get("retry_count") != retry_count:
        raise ValueError(
            "Creator failed-proof acceptance state and ledger retry counts disagree."
        )

    visual_qa_issues = state.get("visual_qa_issues")
    if (
        not isinstance(visual_qa_issues, list)
        or not visual_qa_issues
        or not all(isinstance(issue, str) and issue for issue in visual_qa_issues)
        or failed_attempt.get("qa_issues") != visual_qa_issues
    ):
        raise ValueError(
            "Creator failed-proof acceptance requires the exact persisted QA failure list."
        )
    issues_fingerprint = visual_qa_issues_fingerprint(visual_qa_issues)

    visual_qa_path = state.get("visual_qa_path")
    if not isinstance(visual_qa_path, str):
        raise ValueError(
            "Creator failed-proof acceptance is missing its failed visual-QA artifact."
        )
    visual_qa_binding, visual_qa_bytes = _read_creator_override_package_file(
        carousel_dir,
        visual_qa_path,
        label="Failed visual-QA artifact",
    )
    try:
        visual_qa = json.loads(visual_qa_bytes)
    except json.JSONDecodeError as exc:
        raise ValueError(
            "Creator failed-proof acceptance visual-QA artifact is malformed."
        ) from exc
    if (
        not isinstance(visual_qa, dict)
        or visual_qa.get("image_set_sha256") != current_image_set_sha256
    ):
        raise ValueError(
            "Creator failed-proof acceptance visual-QA artifact belongs to a "
            "different image set."
        )

    approval_binding, approval_bytes = _read_creator_override_package_file(
        carousel_dir,
        approval_path,
        label="Creator failed-proof approval",
    )
    try:
        approval = json.loads(approval_bytes)
    except json.JSONDecodeError as exc:
        raise ValueError("Creator failed-proof approval is malformed.") from exc
    if not isinstance(approval, dict):
        raise ValueError("Creator failed-proof approval must be a JSON object.")

    approval_issues: list[str] = []
    if approval.get("status") != "APPROVED" or approval.get("approved") is not True:
        approval_issues.append("status must be APPROVED with approved=true")
    if approval.get("image_set_sha256") != current_image_set_sha256:
        approval_issues.append("image_set_sha256 is stale or missing")
    if str(approval.get("approved_by") or "").strip().casefold() != "creator":
        approval_issues.append("approved_by must be creator")
    evidence = str(approval.get("evidence") or "").strip()
    if len(evidence) < 8:
        approval_issues.append("evidence must concretely record the creator decision")
    if approval.get("accepts_known_qa_exceptions") is not True:
        approval_issues.append("accepts_known_qa_exceptions must be true")
    if approval.get("acknowledged_visual_qa_issues") != visual_qa_issues:
        approval_issues.append(
            "acknowledged_visual_qa_issues must exactly match the current failures"
        )
    if (
        approval.get("acknowledged_visual_qa_issues_fingerprint")
        != issues_fingerprint
    ):
        approval_issues.append(
            "acknowledged_visual_qa_issues_fingerprint is stale or missing"
        )
    if approval_issues:
        raise ValueError(
            "Creator failed-proof approval is invalid: "
            + "; ".join(approval_issues)
        )

    approval_record: dict[str, Any] = {
        "schema_version": CREATOR_FAILED_PROOF_APPROVAL_SCHEMA_VERSION,
        "source_status": source_status,
        "proof_slide": proof_slide,
        "attempt": failed_attempt.get("attempt"),
        "retry_count": retry_count,
        "image_set_sha256": current_image_set_sha256,
        "approved_by": "creator",
        "evidence": evidence,
        "accepts_known_qa_exceptions": True,
        "acknowledged_visual_qa_issues": list(visual_qa_issues),
        "acknowledged_visual_qa_issues_fingerprint": issues_fingerprint,
        "approval_binding": approval_binding,
        "visual_qa_binding": visual_qa_binding,
    }
    approval_record["record_fingerprint"] = _canonical_fingerprint(
        approval_record
    )
    known_exceptions = {
        "qa_status": "QA_FAILED",
        "visual_qa_issues": list(visual_qa_issues),
        "visual_qa_issues_fingerprint": issues_fingerprint,
        "visual_qa_binding": visual_qa_binding,
        "creator_evidence": evidence,
    }

    updated_state = json.loads(json.dumps(state))
    updated_state.update(
        {
            "status": GenerationStatus.BATCH_ALLOWED.value,
            "proof_state": GenerationStatus.BATCH_ALLOWED.value,
            "reason": (
                "The creator accepted this exact QA-failed proof with the recorded "
                "known exceptions. Batch generation is allowed; the proof remains "
                "non-publishable and did not pass QA."
            ),
            "done": False,
            "publishable": False,
            "requires_human_generation": False,
            "batch_generation_allowed": True,
            "creator_override": True,
            "creator_approval_path": approval_binding["relative_path"],
            "creator_approval_binding": approval_binding,
            "creator_approval_sha256": approval_binding["sha256"],
            "creator_override_record": approval_record,
            "known_qa_exceptions": known_exceptions,
            "visual_qa_status": "QA_FAILED",
            "proof_qa_passed": False,
            "promotion_blocker": "creator_override_allows_batch_generation_only",
        }
    )

    updated_ledger = json.loads(json.dumps(ledger))
    updated_attempt = updated_ledger["attempts"][-1]
    prior_history = updated_attempt.get("status_history")
    status_history = (
        list(prior_history) if isinstance(prior_history, list) else []
    )
    status_history.extend(
        [
            {
                "status": "QA_FAILED",
                "image_set_sha256": current_image_set_sha256,
                "visual_qa_issues_fingerprint": issues_fingerprint,
                "visual_qa_binding": visual_qa_binding,
            },
            {
                "status": CREATOR_ACCEPTED_WITH_KNOWN_EXCEPTIONS,
                "approval_binding": approval_binding,
                "creator_override_record_fingerprint": approval_record[
                    "record_fingerprint"
                ],
            },
        ]
    )
    updated_attempt.update(
        {
            "status": CREATOR_ACCEPTED_WITH_KNOWN_EXCEPTIONS,
            "qa_status": "QA_FAILED",
            "qa_issues": list(visual_qa_issues),
            "visual_qa_issues_fingerprint": issues_fingerprint,
            "creator_override": approval_record,
            "batch_generation_allowed": True,
            "publishable": False,
            "status_history": status_history,
        }
    )

    transaction_id = uuid.uuid4().hex
    internal_dir = carousel_dir / ".internal"
    internal_dir.mkdir(parents=True, exist_ok=True)
    state_temp = internal_dir / f".creator-override-state-{transaction_id}.json"
    final_state_temp = internal_dir / f".creator-override-final-{transaction_id}.json"
    ledger_temp = internal_dir / f".creator-override-ledger-{transaction_id}.json"
    state_payload = json.dumps(
        updated_state, indent=2, ensure_ascii=False
    ).encode("utf-8")
    ledger_payload = json.dumps(
        updated_ledger, indent=2, ensure_ascii=False
    ).encode("utf-8")
    state_replaced = False
    final_state_replaced = False
    ledger_replaced = False
    try:
        state_temp.write_bytes(state_payload)
        final_state_temp.write_bytes(state_payload)
        ledger_temp.write_bytes(ledger_payload)

        if (
            state_path.read_bytes() != old_state_bytes
            or final_state_path.read_bytes() != old_final_state_bytes
            or ledger_path.read_bytes() != old_ledger_bytes
        ):
            raise ValueError(
                "Creator failed-proof evidence changed during acceptance; retry "
                "against the current state."
            )
        if (
            _read_creator_override_package_file(
                carousel_dir,
                approval_binding["relative_path"],
                label="Creator failed-proof approval",
            )[1]
            != approval_bytes
            or _read_creator_override_package_file(
                carousel_dir,
                visual_qa_binding["relative_path"],
                label="Failed visual-QA artifact",
            )[1]
            != visual_qa_bytes
        ):
            raise ValueError(
                "Creator failed-proof approval or QA evidence changed during acceptance."
            )
        final_quarantine_issues = validate_quarantine_integrity(
            slides,
            output_formats,
            carousel_dir=carousel_dir,
        )
        if final_quarantine_issues:
            raise ValueError(
                "Creator failed-proof quarantine changed during acceptance: "
                + "; ".join(final_quarantine_issues)
            )

        state_temp.replace(state_path)
        state_replaced = True
        final_state_temp.replace(final_state_path)
        final_state_replaced = True
        ledger_temp.replace(ledger_path)
        ledger_replaced = True
        return updated_state
    except Exception:
        if state_replaced:
            state_path.write_bytes(old_state_bytes)
        if final_state_replaced:
            final_state_path.write_bytes(old_final_state_bytes)
        if ledger_replaced:
            ledger_path.write_bytes(old_ledger_bytes)
        raise
    finally:
        remove_path_without_following(state_temp)
        remove_path_without_following(final_state_temp)
        remove_path_without_following(ledger_temp)


def package_codex_builtin_outputs(
    carousel_dir: Path,
    *,
    generated_paths: list[str | Path] | None = None,
    generated_paths_by_format: dict[str, list[str | Path]] | None = None,
    refresh_quality: bool = False,
    visual_qa_path: str | Path | None = None,
    creator_approval_path: str | Path | None = None,
    promote_existing_quarantine: bool = False,
    proof_slide: int | None = None,
) -> dict[str, Any]:
    carousel_dir = carousel_dir.expanduser()
    output_formats = locked_formats(carousel_dir)
    output_contract = native_output_contract(output_formats)
    prompt_pack = load_json(carousel_dir / "prompt-pack.json")
    all_slides = prompt_pack.get("slides", [])
    slides = all_slides
    if generated_paths is not None:
        raise ValueError(
            "Codex built-in packaging requires generated_paths_by_format keyed by the "
            "current-request format contract."
        )
    if not generated_paths_by_format and not promote_existing_quarantine:
        raise ValueError("generated_paths_by_format is required.")
    state_path = carousel_dir / "image-generation.json"
    final_state_path = carousel_dir / "final-images.json"
    try:
        lifecycle_state = load_json(state_path)
        final_lifecycle_state = load_json(final_state_path)
    except (OSError, json.JSONDecodeError):
        lifecycle_state = None
        final_lifecycle_state = None
    if promote_existing_quarantine:
        if not isinstance(lifecycle_state, dict):
            raise ValueError("No quarantined generation state exists to promote.")
        recorded_proof_slide = lifecycle_state.get("requested_proof_slide")
        if lifecycle_state.get("proof_only") is True:
            try:
                proof_slide = int(recorded_proof_slide)
            except (TypeError, ValueError) as exc:
                raise ValueError("Proof-only quarantine is missing its selected proof slide.") from exc
    elif proof_slide is not None:
        recorded_proof_slide = (
            lifecycle_state.get("requested_proof_slide")
            if isinstance(lifecycle_state, dict)
            else None
        )
        if recorded_proof_slide != proof_slide:
            raise ValueError(
                f"proof_slide {proof_slide} does not match the compiled proof handoff "
                f"({recorded_proof_slide!r})."
            )
    elif isinstance(lifecycle_state, dict) and lifecycle_state.get(
        "requested_proof_slide"
    ) is not None:
        raise ValueError(
            "The active handoff is proof-only; pass proof_slide (CLI: --proof-slide) "
            "with the selected generated proof."
        )
    if proof_slide is not None:
        slides = [
            slide
            for slide in all_slides
            if int(slide.get("slide", 0) or 0) == proof_slide
        ]
        if len(slides) != 1:
            raise ValueError(f"proof_slide {proof_slide} is not present exactly once.")
    proof_only = proof_slide is not None
    creator_override_origin: tuple[dict[str, Any], str] | None = None
    creator_override_scope_claimed = (
        not proof_only
        and isinstance(lifecycle_state, dict)
        and (
            lifecycle_state.get("creator_override") is True
            or lifecycle_state.get("generation_scope")
            == CREATOR_OVERRIDE_FULL_DECK_SCOPE
        )
    )
    if creator_override_scope_claimed and not isinstance(final_lifecycle_state, dict):
        raise ValueError(
            "Creator-override full-deck packaging requires matching generation manifests."
        )
    if (
        creator_override_scope_claimed
        and isinstance(final_lifecycle_state, dict)
    ):
        creator_override_origin = _validated_creator_override_origin_handoff(
            carousel_dir,
            lifecycle_state=lifecycle_state,
            final_state=final_lifecycle_state,
        )
    creator_override_full_deck = creator_override_origin is not None
    approved_proof_batch_attestation = (
        lifecycle_state.get("approved_proof_batch_handoff_attestation")
        if isinstance(lifecycle_state, dict)
        else None
    )
    if (
        not proof_only
        and not isinstance(approved_proof_batch_attestation, dict)
        and (carousel_dir / APPROVED_PROOF_BATCH_HANDOFF_ARCHIVE).is_file()
    ):
        archived_attestation = load_json(
            carousel_dir / APPROVED_PROOF_BATCH_HANDOFF_ARCHIVE
        )
        attestation_state = {
            "requested_formats": list(output_formats),
            "approved_proof_batch_handoff_attestation": archived_attestation,
        }
        if not approved_proof_batch_handoff_attestation_issues(
            carousel_dir,
            state=attestation_state,
        ):
            approved_proof_batch_attestation = archived_attestation
    approved_proof_batch_full_deck = (
        not proof_only
        and isinstance(
            approved_proof_batch_attestation,
            dict,
        )
    )
    effective_retry_limit = (
        MAX_VISUAL_QA_RETRIES + 1
        if approved_proof_batch_full_deck
        else MAX_VISUAL_QA_RETRIES
    )
    if (
        creator_override_full_deck
        and isinstance(lifecycle_state, dict)
        and lifecycle_state.get("generation_scope")
        == CREATOR_OVERRIDE_FULL_DECK_SCOPE
    ):
        validate_current_full_deck_attempt(
            carousel_dir,
            state=lifecycle_state,
        )

    def update_active_attempt(
        *,
        status: str,
        qa_issues: list[str] | None = None,
    ) -> None:
        if creator_override_full_deck:
            update_current_full_deck_attempt(
                carousel_dir,
                status=status,
                qa_issues=qa_issues,
            )
        else:
            update_current_attempt(
                carousel_dir,
                status=status,
                qa_issues=qa_issues,
            )

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
        handoff_state = lifecycle_state
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
    scope_extra = {
        "proof_only": proof_only,
        "requested_proof_slide": proof_slide,
        "total_slide_count": len(all_slides),
    }
    current_proof_status: GenerationStatus | None = None
    preaudit_reentry = False
    if promote_existing_quarantine:
        current_state = lifecycle_state
        if not isinstance(current_state, dict):
            raise ValueError("No quarantined generation state exists to promote.")
        existing_compiled_handoff = current_state.get("compiled_prompt_handoff")
        if isinstance(existing_compiled_handoff, dict):
            compiled_handoff = existing_compiled_handoff
        current_proof_status = GenerationStatus(current_state.get("status"))
        eligible_statuses = {
            GenerationStatus.GENERATED_QUARANTINED.value,
            GenerationStatus.QA_PASS_CANDIDATE.value,
            GenerationStatus.CREATOR_APPROVED_PROOF.value,
        }
        if (
            creator_override_full_deck
            and current_state.get("status")
            == GenerationStatus.BATCH_ALLOWED.value
        ):
            preaudit_reentry = True
            eligible_statuses.add(GenerationStatus.BATCH_ALLOWED.value)
        if current_state.get("status") not in eligible_statuses:
            raise ValueError("Current generation state is not eligible for quarantined promotion.")
        retry_count = int(current_state.get("retry_count", 0))
        quarantine_records = (
            reconstruct_full_deck_quarantine_records(
                carousel_dir,
                state=current_state,
                prompt_slides=slides,
                output_formats=output_formats,
            )
            if preaudit_reentry
            else current_state.get("slides") or []
        )
        active_quarantine_dir = (
            full_deck_quarantine_dir(carousel_dir, retry_count)
            if creator_override_full_deck
            else quarantine_dir(carousel_dir, retry_count)
        )
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
                    "max_visual_qa_retries": effective_retry_limit,
                    "quarantine_integrity_issues": quarantine_issues,
                },
            )
    else:
        retry_count = (
            next_full_deck_retry_count(carousel_dir)
            if creator_override_full_deck
            else next_retry_count(
                carousel_dir,
                allow_approved_proof_batch=approved_proof_batch_full_deck,
            )
        )
        active_quarantine_dir = (
            full_deck_quarantine_dir(carousel_dir, retry_count)
            if creator_override_full_deck
            else quarantine_dir(carousel_dir, retry_count)
        )
        quarantine_records = quarantine_generated_sources(
            carousel_dir,
            slides=slides,
            generated_paths_by_format=generated_paths_by_format or {},
            retry_count=retry_count,
            output_formats=output_formats,
            quarantine_scope_dir=active_quarantine_dir,
            refuse_existing_scope=creator_override_full_deck,
        )
    quarantine_extra = {
        "proof_state": GenerationStatus.GENERATED_QUARANTINED.value,
        "retry_count": retry_count,
        "max_visual_qa_retries": effective_retry_limit,
        "retries_remaining": effective_retry_limit - retry_count,
        "quarantine_dir": package_relative_path(
            carousel_dir,
            active_quarantine_dir,
        ),
        "image_set_sha256": image_set_sha256(quarantine_records),
        "requested_formats": list(output_formats),
        "native_output_contract": output_contract,
        **scope_extra,
    }
    if creator_override_origin is not None:
        origin_handoff, origin_handoff_fingerprint = creator_override_origin
        quarantine_extra.update(
            {
                "generation_scope": CREATOR_OVERRIDE_FULL_DECK_SCOPE,
                "full_deck_qa_state": "FULL_DECK_GENERATED_QUARANTINED",
                "full_deck_qa_passed": False,
                "proof_qa_passed": False,
                "visual_qa_status": "PENDING_FULL_DECK_QA",
                "promotion_blocker": "fresh_full_deck_visual_qa_required",
                "creator_override_origin_handoff": origin_handoff,
                "creator_override_origin_handoff_fingerprint": (
                    origin_handoff_fingerprint
                ),
                "full_deck_visual_qa_path": FULL_DECK_VISUAL_QA,
            }
        )
    if compiled_handoff is not None:
        quarantine_extra["compiled_prompt_handoff"] = compiled_handoff
    if approved_proof_batch_full_deck:
        quarantine_extra["approved_proof_batch_handoff_attestation"] = (
            approved_proof_batch_attestation
        )
    retry_attestation = (
        lifecycle_state.get("retry_prompt_handoff_attestation")
        if isinstance(lifecycle_state, dict)
        else None
    )
    if isinstance(retry_attestation, dict):
        quarantine_extra["retry_prompt_handoff_attestation"] = retry_attestation
    if not promote_existing_quarantine:
        if creator_override_full_deck:
            append_full_deck_attempt(
                carousel_dir,
                retry_count=retry_count,
                image_set_hash=quarantine_extra["image_set_sha256"],
                quarantine_path=quarantine_extra["quarantine_dir"],
                origin_handoff_fingerprint=quarantine_extra[
                    "creator_override_origin_handoff_fingerprint"
                ],
            )
        else:
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
        carousel_dir,
        visual_qa_path,
        FULL_DECK_VISUAL_QA if creator_override_full_deck else "visual-qa.json",
    )
    if preaudit_reentry and (
        current_state.get("visual_qa_path")
        != package_relative_path(carousel_dir, resolved_visual_qa_path)
    ):
        raise ValueError(
            "Creator-override pre-audit re-entry visual-QA binding changed."
        )
    if not resolved_visual_qa_path.exists():
        if not proof_only:
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
        update_active_attempt(
            status="QA_FAILED",
            qa_issues=visual_qa_issues,
        )
        if not proof_only:
            clean_packaged_output_files(carousel_dir, slide_numbers)
        failed_extra = {
            **quarantine_extra,
            "visual_qa_path": package_relative_path(
                carousel_dir,
                resolved_visual_qa_path,
            ),
            "visual_qa_issues": visual_qa_issues,
        }
        if creator_override_full_deck:
            failed_extra["full_deck_qa_state"] = "FULL_DECK_QA_FAILED"
            failed_extra["visual_qa_status"] = "QA_FAILED"
        spatial_failure = any("spatial_topology" in issue for issue in visual_qa_issues)
        if retry_count >= effective_retry_limit:
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
        "visual_qa_path": package_relative_path(
            carousel_dir,
            resolved_visual_qa_path,
        ),
    }
    if creator_override_full_deck:
        candidate_extra["full_deck_qa_state"] = (
            "FULL_DECK_QA_PASS_CANDIDATE"
        )
        candidate_extra["full_deck_qa_passed"] = True
        candidate_extra["visual_qa_status"] = "QA_PASSED"
        candidate_extra["promotion_blocker"] = "fresh_full_deck_creator_approval_required"
    if not preaudit_reentry:
        update_active_attempt(status="QA_PASSED")
    if (
        not preaudit_reentry
        and current_proof_status != GenerationStatus.CREATOR_APPROVED_PROOF
    ):
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

    approval_raw_path = (
        creator_approval_path
        or (
            current_state.get("creator_approval_path")
            if preaudit_reentry
            else None
        )
        or "creator-proof-approval.json"
    )
    approval_binding: dict[str, str] | None = None
    approval_bytes: bytes | None = None
    try:
        (
            resolved_approval_path,
            approval_binding,
            approval_bytes,
        ) = _read_full_deck_approval_file(
            carousel_dir,
            approval_raw_path,
            allow_legacy_package_prefix=preaudit_reentry,
        )
    except ValueError:
        if preaudit_reentry:
            raise ValueError(
                "Creator-override pre-audit re-entry is missing or has an unsafe "
                "full-deck approval binding."
            )
        resolved_approval_path = resolve_package_artifact_path(
            carousel_dir,
            approval_raw_path,
            "creator-proof-approval.json",
        )
        if resolved_approval_path.exists():
            raise ValueError(
                "Full-deck creator approval must be a safe package-contained file."
            )
    if preaudit_reentry:
        (
            recorded_approval_path,
            recorded_approval_binding,
            _,
        ) = _read_full_deck_approval_file(
            carousel_dir,
            current_state.get("creator_approval_path"),
            allow_legacy_package_prefix=True,
        )
        if (
            resolved_approval_path.resolve() != recorded_approval_path.resolve()
            or approval_binding != recorded_approval_binding
            or (
                current_state.get("creator_approval_sha256") is not None
                and current_state.get("creator_approval_sha256")
                != recorded_approval_binding["sha256"]
            )
        ):
            raise ValueError(
                "Creator-override pre-audit re-entry approval binding changed."
            )
    if not resolved_approval_path.exists():
        if preaudit_reentry:
            raise ValueError(
                "Creator-override pre-audit re-entry is missing its bound full-deck approval."
            )
        if not proof_only:
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
    try:
        approval = json.loads(approval_bytes or resolved_approval_path.read_bytes())
    except (json.JSONDecodeError, OSError) as exc:
        raise ValueError("Full-deck creator approval is malformed.") from exc
    approval_issues = validate_creator_approval(
        approval, expected_image_set_sha256=quarantine_extra["image_set_sha256"]
    )
    if approval_issues:
        if preaudit_reentry:
            raise ValueError(
                "Creator-override pre-audit re-entry full-deck approval is stale."
            )
        if not proof_only:
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

    assert approval_binding is not None
    approved_extra = {
        **candidate_extra,
        "proof_state": GenerationStatus.CREATOR_APPROVED_PROOF.value,
        "creator_approval_path": approval_binding["relative_path"],
        "creator_approval_sha256": approval_binding["sha256"],
    }
    if creator_override_full_deck:
        approved_extra["full_deck_qa_state"] = (
            "FULL_DECK_CREATOR_APPROVED"
        )
    if not preaudit_reentry:
        update_active_attempt(status="CREATOR_APPROVED")
    if (
        not preaudit_reentry
        and current_proof_status != GenerationStatus.CREATOR_APPROVED_PROOF
    ):
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

    if proof_only:
        update_active_attempt(status="BATCH_ALLOWED")
        return write_generation_state(
            carousel_dir,
            status=GenerationStatus.BATCH_ALLOWED,
            backend=BACKEND,
            generation_mode=GENERATION_MODE,
            slide_count=len(slides),
            reason=(
                "The selected proof has exact-image QA and explicit creator approval; "
                "full-batch generation is allowed, but no proof was published as a final."
            ),
            slides=quarantine_records,
            extra=approved_extra,
        )

    if not refresh_quality:
        if preaudit_reentry:
            return current_state
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
            str(
                resolve_package_artifact_path(
                    carousel_dir,
                    (
                        record["native_outputs"][output_format]
                        .get("model_native_source", {})
                        .get("path")
                        or record["native_outputs"][output_format]["path"]
                    ),
                    "",
                )
            )
            for record in quarantine_records
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
    review_path = carousel_dir / "review.json"
    if review_path.is_file():
        package["review"] = load_json(review_path)
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
            visual_qa_path=resolved_visual_qa_path,
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
        if creator_override_full_deck:
            audit_extra["full_deck_qa_state"] = "FULL_DECK_FINAL_AUDIT_FAILED"
        update_active_attempt(status="FINAL_AUDIT_FAILED")
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
        if creator_override_full_deck:
            audit_extra["full_deck_qa_state"] = "FULL_DECK_PUBLISH_READY"
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
        update_active_attempt(status="PROMOTED")
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
