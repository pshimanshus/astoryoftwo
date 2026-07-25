"""Structured gates for directed visual storytelling in carousel packages.

The validators in this module deliberately check evidence and lifecycle state,
not taste.  A fresh visual critic still has to perform the copy-hidden board
read and the rendered-frame audit.  These functions make that judgment
auditable and prevent a bare ``PASS`` flag from bypassing it.
"""

from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
import hashlib
import json
from pathlib import Path, PurePosixPath, PureWindowsPath
from typing import Any, Iterable, Mapping

from PIL import Image, UnidentifiedImageError

from pipeline.stages.carousel_format_contract import (
    DEFAULT_NATIVE_FORMATS,
    SUPPORTED_NATIVE_FORMATS,
    locked_formats,
)


DIRECTOR_STORYBOARD_KEY = "director_storyboard"
VISUAL_STORY_READABILITY_KEY = "visual_story_readability"
DIRECTOR_EVENT_FINGERPRINT_VERSION = "director-event/v2"
REVIEW_PROVENANCE_VERSION = "visual-review-provenance/v2"
CREATOR_CORRECTION_ARTIFACTS = (
    "creator-correction.json",
    "correction.json",
)


@dataclass(frozen=True)
class ExpectedFrameAsset:
    """Caller-resolved canonical asset binding for one slide/native format.

    Format resolution belongs to the package lifecycle.  The visual-story
    validator consumes that decision instead of guessing folders or canvases.
    Mapping values with the same ``relative_path`` and ``dimensions`` fields
    are accepted too, which keeps this API usable across pipeline modules.
    """

    relative_path: str
    dimensions: tuple[int, int]

_BLIND_CARD_FIELDS = {
    "slide",
    "visible_people",
    "visible_setting",
    "observable_action",
    "hands_and_contact",
    "gaze",
    "body_blocking",
    "object_state",
    "camera_view",
    "visible_continuity",
}
_BLIND_CARD_TEXT_FIELDS = (
    "visible_setting",
    "observable_action",
    "hands_and_contact",
    "gaze",
    "body_blocking",
    "object_state",
    "camera_view",
    "visible_continuity",
)

_PLACEHOLDERS = {
    "",
    "-",
    "?",
    "na",
    "n/a",
    "none",
    "null",
    "pending",
    "placeholder",
    "same as before",
    "some props",
    "tbd",
    "todo",
}

_VAGUE_WHOLE_VALUES = {
    "appropriate composition",
    "beautiful scene",
    "cozy home",
    "cozy room",
    "couple moment",
    "generic couple scene",
    "nice lighting",
    "romantic scene",
    "soft couple moment",
    "warm home",
    "warm room",
    "warm scene",
}

_TEXT_IMAGE_RELATIONSHIPS = {"additive", "counterpoint", "interdependent"}
_SEQUENCE_MODES = {
    "causal_sequence",
    "montage_with_arc",
    "reel_sequence",
    "single_image",
}


def _stable_fingerprint(payload: Any, *, namespace: str) -> str:
    canonical = json.dumps(
        {"namespace": namespace, "payload": payload},
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return "sha256:" + hashlib.sha256(canonical).hexdigest()


def review_response_fingerprint(response: str) -> str:
    """Fingerprint an exact raw critic response without normalizing its text."""

    return _stable_fingerprint(
        str(response),
        namespace="visual-review-raw-response/v1",
    )


def generation_payload_fingerprint(prompt_pack: Any) -> str:
    """Bind Event A to the exact parsed generation-facing prompt package.

    The complete payload is covered deliberately.  A future generation field
    must not become an unbound escape hatch merely because this validator did
    not know its name when the Event A contract was written.
    """

    return _stable_fingerprint(
        prompt_pack,
        namespace="visual-generation-payload/v1",
    )


def current_generation_payload_fingerprint(package_dir: Path) -> str:
    """Return the current ``prompt-pack.json`` generation-payload digest.

    Lifecycle callers should treat ``ValueError`` as a blocker.  Missing or
    malformed prompt packs cannot be represented as a valid current payload.
    """

    path = Path(package_dir) / "prompt-pack.json"
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        raise ValueError(f"Missing required generation payload: {path}") from None
    except (json.JSONDecodeError, OSError) as exc:
        raise ValueError(f"Invalid generation payload {path}: {exc}") from exc
    if not isinstance(payload, dict):
        raise ValueError(f"Generation payload {path} must contain a JSON object.")
    return generation_payload_fingerprint(payload)


def current_creator_correction_fingerprint(package_dir: Path) -> str:
    """Fingerprint all current creator-correction state in a package.

    Both the canonical and legacy correction filenames are covered.  Parsed
    JSON is hashed when possible so semantic status/revision changes invalidate
    Event A without making harmless JSON formatting changes lifecycle events.
    Invalid JSON and non-file states are still represented deterministically so
    a later repair also invalidates the prior approval.
    """

    root = Path(package_dir)
    artifacts: list[dict[str, Any]] = []
    for filename in CREATOR_CORRECTION_ARTIFACTS:
        path = root / filename
        if not path.exists() and not path.is_symlink():
            continue
        entry: dict[str, Any] = {
            "name": filename,
            "symlink": path.is_symlink(),
        }
        try:
            raw = path.read_bytes()
        except OSError as exc:
            entry["unreadable"] = f"{type(exc).__name__}:{exc.errno}"
        else:
            try:
                entry["payload"] = json.loads(raw.decode("utf-8"))
            except (UnicodeDecodeError, json.JSONDecodeError):
                entry["raw_sha256"] = hashlib.sha256(raw).hexdigest()
        artifacts.append(entry)
    return _stable_fingerprint(
        artifacts,
        namespace="creator-correction-state/v1",
    )


EMPTY_CREATOR_CORRECTION_FINGERPRINT = _stable_fingerprint(
    [],
    namespace="creator-correction-state/v1",
)


def _director_payload(plan_or_director: Any) -> dict[str, Any] | None:
    if not isinstance(plan_or_director, dict):
        return None
    nested = plan_or_director.get(DIRECTOR_STORYBOARD_KEY)
    if isinstance(nested, dict):
        return nested
    return plan_or_director


def _without_director_self_hash(director: dict[str, Any]) -> dict[str, Any]:
    payload = deepcopy(director)
    payload.pop("director_event_fingerprint", None)
    return payload


def director_review_output_fingerprint(plan_or_director: Any) -> str | None:
    """Fingerprint Event A's complete structured review/reconciliation output.

    The provenance output digest is omitted to avoid hashing itself.  Inputs,
    raw-response evidence, reconciled director slides, ledgers, lock state, and
    the declared outcome remain covered.
    """

    director = _director_payload(plan_or_director)
    if director is None:
        return None
    payload = _without_director_self_hash(director)
    provenance = payload.get("review_provenance")
    if isinstance(provenance, dict):
        provenance.pop("output_fingerprint", None)
    return _stable_fingerprint(
        payload,
        namespace="director-review-output/v1",
    )


def director_event_fingerprint(plan_or_director: Any) -> str | None:
    """Fingerprint the complete approved Event A payload.

    Only ``director_event_fingerprint`` itself is excluded.  The version,
    source and blind-input fingerprints, exact blind cards, canvas/copy locks,
    complete director slides, ledgers, review provenance, reconciliation, and
    outcome are therefore all lifecycle-bound into Event B.
    """

    director = _director_payload(plan_or_director)
    if director is None:
        return None
    return _stable_fingerprint(
        _without_director_self_hash(director),
        namespace=DIRECTOR_EVENT_FINGERPRINT_VERSION,
    )


def _frame_file_value(frame: Mapping[str, Any]) -> Any:
    if frame.get("file") not in (None, ""):
        return frame.get("file")
    return frame.get("path")


def frame_review_input_fingerprint(frames: Any) -> str:
    """Fingerprint the exact image-first manifest shown to the Event B critic."""

    canonical: list[dict[str, Any]] = []
    if isinstance(frames, list):
        for frame in frames:
            if not isinstance(frame, dict):
                continue
            canonical.append(
                {
                    "slide": _slide_number(frame),
                    "format": str(frame.get("format") or ""),
                    "file": str(_frame_file_value(frame) or ""),
                    "image_fingerprint": str(frame.get("image_fingerprint") or ""),
                }
            )
    canonical.sort(key=lambda item: (item["slide"], item["format"], item["file"]))
    return _stable_fingerprint(
        canonical,
        namespace="rendered-frame-image-first-input/v1",
    )


def frame_review_output_fingerprint(check: Any) -> str | None:
    """Fingerprint Event B's complete structured output without self-reference."""

    if not isinstance(check, dict):
        return None
    payload = deepcopy(check)
    provenance = payload.get("review_provenance")
    if isinstance(provenance, dict):
        provenance.pop("output_fingerprint", None)
    return _stable_fingerprint(
        payload,
        namespace="rendered-frame-review-output/v1",
    )


def _normalized(value: Any) -> str:
    return " ".join(str(value or "").strip().lower().split())


def _concrete_text(value: Any, *, minimum_words: int = 3) -> bool:
    text = _normalized(value)
    if text in _PLACEHOLDERS or text in _VAGUE_WHOLE_VALUES:
        return False
    return len(text.split()) >= minimum_words


def _records(raw: Any) -> list[dict[str, Any]]:
    if isinstance(raw, list):
        return [item for item in raw if isinstance(item, dict)]
    if isinstance(raw, dict) and isinstance(raw.get("slides"), list):
        return [item for item in raw["slides"] if isinstance(item, dict)]
    return []


def _slide_number(record: dict[str, Any], fallback: int = 0) -> int:
    try:
        return int(record.get("slide") or record.get("slide_number") or fallback)
    except (TypeError, ValueError):
        return 0


def _canonical_storyboard_source(slides: Any) -> list[dict[str, Any]]:
    canonical: list[dict[str, Any]] = []
    for index, slide in enumerate(_records(slides), start=1):
        canonical.append(
            {
                "slide": _slide_number(slide, index),
                "copy": str(slide.get("copy") or slide.get("text") or ""),
                "role": str(slide.get("role") or ""),
                "visual": str(slide.get("visual") or slide.get("scene") or ""),
                "emotion": str(slide.get("emotion") or ""),
                "continuity_lock": str(slide.get("continuity_lock") or ""),
            }
        )
    return canonical


def storyboard_source_fingerprint(slides: Any) -> str:
    """Return a stable digest of the generation-facing slide source."""

    payload = json.dumps(
        _canonical_storyboard_source(slides),
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return "sha256:" + hashlib.sha256(payload).hexdigest()


def blind_cards_fingerprint(cards: Any) -> str:
    """Return a stable digest of the observable-only Event A payload."""

    canonical: list[dict[str, Any]] = []
    for index, card in enumerate(_records(cards), start=1):
        canonical.append(
            {
                "slide": _slide_number(card, index),
                "visible_people": [str(item) for item in card.get("visible_people", [])]
                if isinstance(card.get("visible_people"), list)
                else [],
                **{field: str(card.get(field) or "") for field in _BLIND_CARD_TEXT_FIELDS},
            }
        )
    payload = json.dumps(
        canonical,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return "sha256:" + hashlib.sha256(payload).hexdigest()


def requested_story_formats(package_dir: Path | None) -> tuple[str, ...]:
    """Compatibility accessor for the authoritative current-request lock.

    Rendered folders are never request metadata.  New callers should inject
    ``locked_formats(package_dir)`` directly into validators.
    """

    return locked_formats(package_dir) if package_dir is not None else DEFAULT_NATIVE_FORMATS


def story_formats_from_records(records: Any) -> tuple[str, ...]:
    """Resolve the native formats actually present in generation records."""

    present: set[str] = set()
    if isinstance(records, list):
        for record in records:
            if not isinstance(record, dict):
                continue
            native_outputs = record.get("native_outputs")
            if isinstance(native_outputs, dict):
                present.update(native_outputs)
    selected = tuple(
        output_format
        for output_format in SUPPORTED_NATIVE_FORMATS
        if output_format in present
    )
    unsupported = tuple(sorted(present - set(SUPPORTED_NATIVE_FORMATS)))
    return (*selected, *unsupported) or DEFAULT_NATIVE_FORMATS


def image_file_fingerprint(path: Path) -> str:
    """Return a content digest for one rendered frame."""

    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return "sha256:" + digest.hexdigest()


def _require_text(
    payload: dict[str, Any],
    field: str,
    issues: list[str],
    prefix: str,
    *,
    minimum_words: int = 3,
) -> None:
    if not _concrete_text(payload.get(field), minimum_words=minimum_words):
        issues.append(f"{prefix}.{field} needs concrete visual-story evidence.")


def _require_text_fields(
    payload: Any,
    fields: Iterable[str],
    issues: list[str],
    prefix: str,
    *,
    minimum_words: int = 1,
) -> None:
    if not isinstance(payload, dict):
        issues.append(f"{prefix} must be a structured object.")
        return
    for field in fields:
        _require_text(payload, field, issues, prefix, minimum_words=minimum_words)


def _valid_sha256(value: Any) -> bool:
    text = str(value or "")
    if not text.startswith("sha256:") or len(text) != len("sha256:") + 64:
        return False
    try:
        int(text.removeprefix("sha256:"), 16)
    except ValueError:
        return False
    return True


def _require_audit_id(
    payload: dict[str, Any],
    field: str,
    issues: list[str],
    prefix: str,
) -> str:
    value = str(payload.get(field) or "").strip()
    if not _concrete_text(value, minimum_words=1) or len(value) < 4:
        issues.append(f"{prefix}.{field} must record an orchestration-issued audit ID.")
    return value


def _validate_review_provenance(
    provenance: Any,
    *,
    prefix: str,
    expected_input_fingerprint: str,
    expected_output_fingerprint: str | None,
    require_author: bool,
    package_dir: Path | None,
) -> tuple[list[str], dict[str, str]]:
    """Validate auditable review-run evidence, not cryptographic identity.

    Task/run IDs remain declarations issued by orchestration; this validator
    can prove their presence, distinctness, and binding to exact inputs and
    outputs, but it cannot authenticate the human or model behind an ID.
    """

    if not isinstance(provenance, dict):
        return [f"{prefix} must be a structured object."], {}

    issues: list[str] = []
    if provenance.get("schema_version") != REVIEW_PROVENANCE_VERSION:
        issues.append(
            f"{prefix}.schema_version must be {REVIEW_PROVENANCE_VERSION}."
        )

    identity: dict[str, str] = {}
    if require_author:
        identity["author_task_id"] = _require_audit_id(
            provenance, "author_task_id", issues, prefix
        )
        identity["author_run_id"] = _require_audit_id(
            provenance, "author_run_id", issues, prefix
        )
    identity["reviewer_task_id"] = _require_audit_id(
        provenance, "reviewer_task_id", issues, prefix
    )
    identity["reviewer_run_id"] = _require_audit_id(
        provenance, "reviewer_run_id", issues, prefix
    )

    if require_author:
        if _normalized(identity["author_task_id"]) == _normalized(
            identity["reviewer_task_id"]
        ):
            issues.append(f"{prefix} author and reviewer task IDs must differ.")
        if _normalized(identity["author_run_id"]) == _normalized(
            identity["reviewer_run_id"]
        ):
            issues.append(f"{prefix} author and reviewer run IDs must differ.")

    input_fingerprint = str(provenance.get("input_fingerprint") or "")
    if not _valid_sha256(input_fingerprint):
        issues.append(f"{prefix}.input_fingerprint is missing or invalid.")
    elif input_fingerprint != expected_input_fingerprint:
        issues.append(f"{prefix}.input_fingerprint is stale for the exact review input.")

    raw_response_fingerprint = str(provenance.get("raw_response_fingerprint") or "")
    if not _valid_sha256(raw_response_fingerprint):
        issues.append(f"{prefix}.raw_response_fingerprint is missing or invalid.")

    has_inline_response = "raw_response" in provenance
    has_response_artifact = "raw_response_artifact" in provenance
    if has_inline_response == has_response_artifact:
        issues.append(
            f"{prefix} must provide exactly one critic response source: "
            "raw_response or raw_response_artifact."
        )
    elif has_inline_response:
        raw_response = provenance.get("raw_response")
        if not _concrete_text(raw_response):
            issues.append(f"{prefix}.raw_response must contain the exact critic response.")
        elif raw_response_fingerprint != review_response_fingerprint(str(raw_response)):
            issues.append(f"{prefix}.raw_response_fingerprint is stale for raw_response.")
    else:
        relative_artifact, artifact_path_issue = _safe_package_relative_path(
            provenance.get("raw_response_artifact")
        )
        if artifact_path_issue:
            issues.append(
                f"{prefix}.raw_response_artifact {artifact_path_issue}."
            )
        elif package_dir is None:
            issues.append(
                f"{prefix}.raw_response_artifact requires the package root for verification."
            )
        else:
            assert relative_artifact is not None
            artifact_path = _path_inside_package(package_dir, relative_artifact)
            if artifact_path is None:
                issues.append(
                    f"{prefix}.raw_response_artifact must stay inside the package root."
                )
            elif _path_has_symlink_component(package_dir, artifact_path):
                issues.append(
                    f"{prefix}.raw_response_artifact must be a regular package file, not a symlink."
                )
            elif not artifact_path.is_file():
                issues.append(
                    f"{prefix}.raw_response_artifact does not exist as a regular package file."
                )
            else:
                try:
                    artifact_response = artifact_path.read_text(encoding="utf-8")
                except (OSError, UnicodeDecodeError):
                    issues.append(
                        f"{prefix}.raw_response_artifact must be readable UTF-8 critic evidence."
                    )
                else:
                    if not _concrete_text(artifact_response):
                        issues.append(
                            f"{prefix}.raw_response_artifact must contain the exact critic response."
                        )
                    elif raw_response_fingerprint != review_response_fingerprint(
                        artifact_response
                    ):
                        issues.append(
                            f"{prefix}.raw_response_fingerprint is stale for raw_response_artifact."
                        )

    output_fingerprint = str(provenance.get("output_fingerprint") or "")
    if not _valid_sha256(output_fingerprint):
        issues.append(f"{prefix}.output_fingerprint is missing or invalid.")
    elif expected_output_fingerprint and output_fingerprint != expected_output_fingerprint:
        issues.append(
            f"{prefix}.output_fingerprint is stale for the structured review/reconciliation output."
        )

    return issues, identity


def _validate_numbered_records(
    records: list[dict[str, Any]],
    *,
    slide_count: int,
    prefix: str,
) -> tuple[list[str], set[int]]:
    issues: list[str] = []
    seen: set[int] = set()
    for index, record in enumerate(records, start=1):
        number = _slide_number(record)
        if number < 1 or number > slide_count:
            issues.append(f"{prefix} record {index} has invalid slide number {number!r}.")
        elif number in seen:
            issues.append(f"{prefix} repeats slide {number}.")
        else:
            seen.add(number)
    missing = sorted(set(range(1, slide_count + 1)) - seen)
    if missing:
        issues.append(f"{prefix} missing slide records: {', '.join(map(str, missing))}.")
    return issues, seen


def validate_director_storyboard(
    plan: Any,
    *,
    slide_count: int,
    expected_slides: Any | None = None,
    expected_formats: Iterable[str] | None = None,
    expected_format_contract_fingerprint: str | None = None,
    expected_creator_correction_fingerprint: str | None = None,
    expected_generation_payload_fingerprint: str | None = None,
    provenance_package_dir: Path | None = None,
) -> list[str]:
    """Return blocking issues for the pre-generation director event.

    ``plan`` is the existing ``visual-plan-quality.json`` payload.  The fresh
    copy-hidden review lives under ``director_storyboard`` so the established
    artifact remains the source of truth.
    """

    if not isinstance(plan, dict):
        return ["visual-plan-quality.json must be a structured object."]

    issues: list[str] = []
    if plan.get("status") != "PASS" or plan.get("can_generate") is not True:
        issues.append("visual-plan-quality.json must be PASS with can_generate true.")

    director = plan.get(DIRECTOR_STORYBOARD_KEY)
    if not isinstance(director, dict):
        return issues + [
            "visual-plan-quality.json missing structured director_storyboard evidence."
        ]

    if director.get("status") != "PASS":
        issues.append("director_storyboard.status must be PASS.")
    if director.get("event") != "copy_hidden_storyboard_read":
        issues.append(
            "director_storyboard.event must be copy_hidden_storyboard_read."
        )
    if director.get("copy_locked") is not True:
        issues.append(
            "director_storyboard.copy_locked must be true; pre-copy direction is advisory and must be rerun after copy lock."
        )
    if director.get("copy_hidden") is not True:
        issues.append("director_storyboard.copy_hidden must be true.")
    if director.get("intent_hidden") is not True:
        issues.append("director_storyboard.intent_hidden must be true.")
    _require_text(director, "copy_lock_evidence", issues, "director_storyboard")
    _require_text(director, "author_id", issues, "director_storyboard", minimum_words=1)
    _require_text(director, "reviewer_id", issues, "director_storyboard", minimum_words=1)
    _require_text(director, "reviewer_evidence", issues, "director_storyboard")
    author_id = str(director.get("author_id") or "")
    reviewer_id = str(director.get("reviewer_id") or "")
    if author_id and reviewer_id and _normalized(author_id) == _normalized(reviewer_id):
        issues.append(
            "director_storyboard reviewer must be independent from the route author."
        )

    requested_formats = director.get("requested_formats")
    if (
        not isinstance(requested_formats, list)
        or not requested_formats
        or not all(_concrete_text(item, minimum_words=1) for item in requested_formats)
    ):
        issues.append(
            "director_storyboard.requested_formats must be the canonical ordered canvas lock."
        )
        requested_formats = []
    elif len(set(requested_formats)) != len(requested_formats):
        issues.append("director_storyboard.requested_formats must not repeat formats.")
    if expected_formats is not None:
        expected_format_list = [str(item) for item in expected_formats]
        if requested_formats != expected_format_list:
            issues.append(
                "director_storyboard.requested_formats is stale for the current format contract."
            )

    format_contract_fingerprint = str(
        director.get("format_contract_fingerprint") or ""
    )
    if not _valid_sha256(format_contract_fingerprint):
        issues.append(
            "director_storyboard.format_contract_fingerprint is missing or invalid."
        )
    elif (
        expected_format_contract_fingerprint
        and format_contract_fingerprint != expected_format_contract_fingerprint
    ):
        issues.append(
            "director_storyboard.format_contract_fingerprint is stale for the current canvas lock."
        )

    recorded_correction_fingerprint = str(
        director.get("creator_correction_fingerprint") or ""
    )
    if not _valid_sha256(recorded_correction_fingerprint):
        issues.append(
            "director_storyboard.creator_correction_fingerprint is missing or invalid."
        )
    if not _valid_sha256(expected_creator_correction_fingerprint):
        issues.append(
            "director_storyboard validation requires the current creator-correction fingerprint."
        )
    elif recorded_correction_fingerprint != expected_creator_correction_fingerprint:
        issues.append(
            "director_storyboard.creator_correction_fingerprint is stale for the current creator-correction state."
        )

    recorded_generation_fingerprint = str(
        director.get("generation_payload_fingerprint") or ""
    )
    if not _valid_sha256(recorded_generation_fingerprint):
        issues.append(
            "director_storyboard.generation_payload_fingerprint is missing or invalid."
        )
    if not _valid_sha256(expected_generation_payload_fingerprint):
        issues.append(
            "director_storyboard validation requires the current prompt-pack generation-payload fingerprint."
        )
    elif recorded_generation_fingerprint != expected_generation_payload_fingerprint:
        issues.append(
            "director_storyboard.generation_payload_fingerprint is stale for the current prompt-pack.json."
        )

    blind_cards = director.get("blind_cards")
    if not isinstance(blind_cards, list):
        issues.append("director_storyboard.blind_cards must be an observable-only per-slide list.")
    else:
        blind_numbered_issues, _ = _validate_numbered_records(
            [item for item in blind_cards if isinstance(item, dict)],
            slide_count=slide_count,
            prefix="director_storyboard.blind_cards",
        )
        issues.extend(blind_numbered_issues)
        if len(blind_cards) != slide_count:
            issues.append(
                f"director_storyboard.blind_cards has {len(blind_cards)} records, expected {slide_count}."
            )
        for index, card in enumerate(blind_cards, start=1):
            if not isinstance(card, dict):
                issues.append(f"director_storyboard.blind_cards record {index} must be an object.")
                continue
            number = _slide_number(card, index)
            prefix = f"director_storyboard.blind_cards[{number}]"
            extra_fields = sorted(set(card) - _BLIND_CARD_FIELDS)
            if extra_fields:
                issues.append(
                    f"{prefix} contains intent/copy fields not allowed in the blind payload: "
                    + ", ".join(extra_fields)
                    + "."
                )
            people = card.get("visible_people")
            if not isinstance(people, list) or not all(
                _concrete_text(item, minimum_words=1) for item in people
            ):
                issues.append(f"{prefix}.visible_people must be a concrete list, even when empty.")
            for field in _BLIND_CARD_TEXT_FIELDS:
                _require_text(card, field, issues, prefix)

        recorded_blind_fingerprint = str(director.get("blind_input_fingerprint") or "")
        if not recorded_blind_fingerprint.startswith("sha256:"):
            issues.append("director_storyboard.blind_input_fingerprint is missing or invalid.")
        elif recorded_blind_fingerprint != blind_cards_fingerprint(blind_cards):
            issues.append("director_storyboard.blind_input_fingerprint is stale for blind_cards.")

    expected_blind_fingerprint = blind_cards_fingerprint(blind_cards)
    provenance_issues, provenance_identity = _validate_review_provenance(
        director.get("review_provenance"),
        prefix="director_storyboard.review_provenance",
        expected_input_fingerprint=expected_blind_fingerprint,
        expected_output_fingerprint=director_review_output_fingerprint(director),
        require_author=True,
        package_dir=provenance_package_dir,
    )
    issues.extend(provenance_issues)
    if provenance_identity:
        if author_id != provenance_identity.get("author_task_id"):
            issues.append(
                "director_storyboard.author_id must equal review_provenance.author_task_id."
            )
        if reviewer_id != provenance_identity.get("reviewer_task_id"):
            issues.append(
                "director_storyboard.reviewer_id must equal review_provenance.reviewer_task_id."
            )

    expected_fingerprint = (
        storyboard_source_fingerprint(expected_slides)
        if expected_slides is not None
        else None
    )
    actual_fingerprint = str(director.get("source_fingerprint") or "")
    if not actual_fingerprint.startswith("sha256:"):
        issues.append("director_storyboard.source_fingerprint is missing or invalid.")
    elif expected_fingerprint and actual_fingerprint != expected_fingerprint:
        issues.append(
            "director_storyboard.source_fingerprint is stale for the current slides/copy."
        )

    sequence_mode = director.get("sequence_mode")
    if sequence_mode not in _SEQUENCE_MODES:
        issues.append(
            "director_storyboard.sequence_mode must be one of: "
            + ", ".join(sorted(_SEQUENCE_MODES))
            + "."
        )
    _require_text(director, "physical_event", issues, "director_storyboard")
    _require_text(director, "emotional_arc", issues, "director_storyboard")
    _require_text(director, "relationship_change", issues, "director_storyboard")
    _require_text(director, "sequence_read", issues, "director_storyboard")

    variables = director.get("visual_variables")
    if not isinstance(variables, list) or not 1 <= len(variables) <= 2:
        issues.append("director_storyboard.visual_variables must name one or two authored variables.")
    elif not all(_concrete_text(item, minimum_words=1) for item in variables):
        issues.append("director_storyboard.visual_variables contains an empty placeholder.")

    hero_slide = director.get("hero_receipt_slide")
    if not isinstance(hero_slide, int) or not 1 <= hero_slide <= slide_count:
        issues.append("director_storyboard.hero_receipt_slide must name a valid slide.")

    setup_payoff = director.get("setup_payoff_ledger")
    if sequence_mode != "single_image":
        if not isinstance(setup_payoff, list) or not setup_payoff:
            issues.append("director_storyboard.setup_payoff_ledger needs at least one setup/payoff link.")
        else:
            for index, link in enumerate(setup_payoff, start=1):
                _require_text_fields(
                    link,
                    ("setup", "payoff", "changed_meaning"),
                    issues,
                    f"director_storyboard.setup_payoff_ledger[{index}]",
                )

    motif_ledger = director.get("object_motif_ledger")
    no_motif_reason = director.get("no_object_motif_reason")
    if isinstance(motif_ledger, list) and motif_ledger:
        for index, motif in enumerate(motif_ledger, start=1):
            _require_text_fields(
                motif,
                ("object", "initial_state", "later_state", "story_job"),
                issues,
                f"director_storyboard.object_motif_ledger[{index}]",
            )
    elif not _concrete_text(no_motif_reason):
        issues.append(
            "director_storyboard needs object_motif_ledger evidence or a concrete no_object_motif_reason."
        )

    slide_records = director.get("slides")
    if not isinstance(slide_records, list):
        return issues + ["director_storyboard.slides must be a per-slide list."]
    numbered_issues, _ = _validate_numbered_records(
        [item for item in slide_records if isinstance(item, dict)],
        slide_count=slide_count,
        prefix="director_storyboard.slides",
    )
    issues.extend(numbered_issues)
    if len(slide_records) != slide_count:
        issues.append(
            f"director_storyboard.slides has {len(slide_records)} records, expected {slide_count}."
        )

    shot_sizes: list[str] = []
    narrative_jobs: list[str] = []
    for index, record in enumerate(slide_records, start=1):
        if not isinstance(record, dict):
            issues.append(f"director_storyboard.slides record {index} must be an object.")
            continue
        number = _slide_number(record, index)
        prefix = f"director_storyboard.slides[{number}]"
        if record.get("status") != "PASS":
            issues.append(f"{prefix}.status must be PASS.")
        if record.get("inference_match") is not True:
            issues.append(f"{prefix}.inference_match must be true after the blind read.")
        for field in (
            "narrative_job",
            "silent_read",
            "change_from_previous",
            "critic_evidence",
        ):
            _require_text(record, field, issues, prefix)
        narrative_jobs.append(_normalized(record.get("narrative_job")))

        _require_text_fields(
            record.get("staged_action"),
            ("subject", "action", "target_or_object", "reaction_or_consequence"),
            issues,
            f"{prefix}.staged_action",
        )
        _require_text_fields(
            record.get("pov"),
            ("owner", "audience_knows", "audience_feels"),
            issues,
            f"{prefix}.pov",
        )
        shot = record.get("shot")
        _require_text_fields(
            shot,
            ("size", "angle", "camera_position", "focal_subject", "story_reason"),
            issues,
            f"{prefix}.shot",
        )
        if isinstance(shot, dict):
            shot_sizes.append(_normalized(shot.get("size")))
        _require_text_fields(
            record.get("blocking"),
            ("hands", "gaze", "body_distance", "posture_or_feet"),
            issues,
            f"{prefix}.blocking",
        )
        _require_text_fields(
            record.get("setting"),
            ("sub_location", "time", "motivated_light", "story_trace"),
            issues,
            f"{prefix}.setting",
        )

        evidence = record.get("story_evidence")
        if not isinstance(evidence, list) or not evidence:
            issues.append(f"{prefix}.story_evidence needs at least one visible carrier.")
        else:
            for evidence_index, item in enumerate(evidence, start=1):
                _require_text_fields(
                    item,
                    ("carrier", "observable_state", "narrative_job"),
                    issues,
                    f"{prefix}.story_evidence[{evidence_index}]",
                )

        relationship = record.get("text_image_relationship")
        if relationship not in _TEXT_IMAGE_RELATIONSHIPS:
            issues.append(
                f"{prefix}.text_image_relationship must be additive, counterpoint, or interdependent."
            )
        _require_text_fields(
            record.get("continuity"),
            ("incoming_state", "outgoing_state"),
            issues,
            f"{prefix}.continuity",
        )

        entity = record.get("entity_contract")
        if not isinstance(entity, dict):
            issues.append(f"{prefix}.entity_contract must be a structured object.")
        else:
            expected_people = entity.get("expected_people")
            if not isinstance(expected_people, int) or expected_people < 0:
                issues.append(f"{prefix}.entity_contract.expected_people must be a non-negative integer.")
            for field in ("background_people", "reflections", "forbidden_entities"):
                if not isinstance(entity.get(field), list):
                    issues.append(f"{prefix}.entity_contract.{field} must be a list.")

        unresolved_ambiguities = record.get(
            "unresolved_ambiguities",
            record.get("ambiguities"),
        )
        if not isinstance(unresolved_ambiguities, list):
            issues.append(
                f"{prefix}.unresolved_ambiguities must be a list, even when empty."
            )
        elif unresolved_ambiguities:
            issues.append(f"{prefix} still has unresolved blind-read ambiguity.")
        resolved_ambiguities = record.get("resolved_ambiguities")
        if not isinstance(resolved_ambiguities, list):
            issues.append(
                f"{prefix}.resolved_ambiguities must be a list, even when empty."
            )
        else:
            for ambiguity_index, ambiguity in enumerate(resolved_ambiguities, start=1):
                _require_text_fields(
                    ambiguity,
                    ("competing_read", "repair", "recheck_evidence"),
                    issues,
                    f"{prefix}.resolved_ambiguities[{ambiguity_index}]",
                )

    if slide_count > 1 and len({item for item in narrative_jobs if item}) < 2:
        issues.append("director_storyboard repeats one narrative job across the whole sequence.")
    if slide_count > 2 and len({item for item in shot_sizes if item}) < 2:
        if not _concrete_text(director.get("deliberate_shot_repetition_reason")):
            issues.append(
                "director_storyboard repeats one shot size without a deliberate story reason."
            )

    declared_issues = director.get("issues")
    if not isinstance(declared_issues, list):
        issues.append("director_storyboard.issues must be a list, even when empty.")
    elif declared_issues:
        issues.append("director_storyboard declares unresolved issues while claiming PASS.")

    if (
        director.get("director_event_fingerprint_version")
        != DIRECTOR_EVENT_FINGERPRINT_VERSION
    ):
        issues.append(
            "director_storyboard.director_event_fingerprint_version must be "
            f"{DIRECTOR_EVENT_FINGERPRINT_VERSION}."
        )
    recorded_event_fingerprint = str(
        director.get("director_event_fingerprint") or ""
    )
    expected_event_fingerprint = director_event_fingerprint(director)
    if not _valid_sha256(recorded_event_fingerprint):
        issues.append(
            "director_storyboard.director_event_fingerprint is missing or invalid."
        )
    elif recorded_event_fingerprint != expected_event_fingerprint:
        issues.append(
            "director_storyboard.director_event_fingerprint is stale for the complete approved Event A payload."
        )

    return issues


def _coerce_expected_asset(value: Any) -> ExpectedFrameAsset | None:
    if isinstance(value, ExpectedFrameAsset):
        return value
    if not isinstance(value, Mapping):
        return None
    relative_path = str(value.get("relative_path") or "")
    dimensions = value.get("dimensions")
    if (
        not isinstance(dimensions, (list, tuple))
        or len(dimensions) != 2
    ):
        width = value.get("width")
        height = value.get("height")
        dimensions = (width, height)
    try:
        width, height = (int(dimensions[0]), int(dimensions[1]))
    except (TypeError, ValueError, IndexError):
        return None
    if width <= 0 or height <= 0:
        return None
    return ExpectedFrameAsset(
        relative_path=relative_path,
        dimensions=(width, height),
    )


def _safe_package_relative_path(raw_path: Any) -> tuple[str | None, str | None]:
    """Return an exact canonical POSIX package-relative path or an error."""

    text = str(raw_path or "")
    if not text:
        return None, "is required"
    windows_path = PureWindowsPath(text)
    posix_path = PurePosixPath(text)
    if windows_path.is_absolute() or windows_path.drive or posix_path.is_absolute():
        return None, "must be package-relative, never absolute"
    if "\\" in text or any(part == ".." for part in posix_path.parts):
        return None, "must not contain traversal or platform-dependent separators"
    canonical = posix_path.as_posix()
    if canonical in {"", "."} or text != canonical:
        return None, "must be an exact canonical package-relative POSIX path"
    return canonical, None


def _path_inside_package(package_dir: Path, relative_path: str) -> Path | None:
    root = package_dir.resolve()
    candidate = root / Path(*PurePosixPath(relative_path).parts)
    resolved_candidate = candidate.resolve()
    try:
        resolved_candidate.relative_to(root)
    except ValueError:
        return None
    return candidate


def _path_has_symlink_component(package_dir: Path, candidate: Path) -> bool:
    """Reject evidence reached through any package-internal symlink component."""

    root = Path(package_dir).resolve()
    try:
        relative = candidate.relative_to(root)
    except ValueError:
        return True
    cursor = root
    for part in relative.parts:
        cursor = cursor / part
        if cursor.is_symlink():
            return True
    return False


def _normalize_expected_frame_bindings(
    bindings: Mapping[tuple[int, str], Any] | None,
    *,
    expected_keys: set[tuple[int, str]],
) -> tuple[dict[tuple[int, str], ExpectedFrameAsset], list[str]]:
    if bindings is None:
        return {}, [
            "visual_story_readability final audit requires caller-resolved expected_frame_bindings."
        ]
    if not isinstance(bindings, Mapping):
        return {}, ["expected_frame_bindings must be a keyed mapping."]

    normalized: dict[tuple[int, str], ExpectedFrameAsset] = {}
    issues: list[str] = []
    used_relative_paths: dict[str, tuple[int, str]] = {}
    for raw_key, raw_value in bindings.items():
        if (
            not isinstance(raw_key, tuple)
            or len(raw_key) != 2
            or not isinstance(raw_key[0], int)
        ):
            issues.append(
                "expected_frame_bindings keys must be (slide: int, format: str) tuples."
            )
            continue
        key = (raw_key[0], str(raw_key[1]))
        asset = _coerce_expected_asset(raw_value)
        if asset is None:
            issues.append(
                f"expected_frame_bindings[{key[0]}:{key[1]}] needs relative_path and positive dimensions."
            )
            continue
        canonical_path, path_issue = _safe_package_relative_path(asset.relative_path)
        if path_issue:
            issues.append(
                f"expected_frame_bindings[{key[0]}:{key[1]}].relative_path {path_issue}."
            )
            continue
        assert canonical_path is not None
        asset = ExpectedFrameAsset(canonical_path, asset.dimensions)
        if canonical_path in used_relative_paths:
            previous = used_relative_paths[canonical_path]
            issues.append(
                "expected_frame_bindings reuses canonical asset "
                f"{canonical_path} for {previous[0]}:{previous[1]} and {key[0]}:{key[1]}."
            )
        else:
            used_relative_paths[canonical_path] = key
        normalized[key] = asset

    missing = sorted(expected_keys - set(normalized))
    extra = sorted(set(normalized) - expected_keys)
    if missing:
        issues.append(
            "expected_frame_bindings missing required assets: "
            + ", ".join(f"{slide}:{fmt}" for slide, fmt in missing)
            + "."
        )
    if extra:
        issues.append(
            "expected_frame_bindings contains unlocked assets: "
            + ", ".join(f"{slide}:{fmt}" for slide, fmt in extra)
            + "."
        )
    return normalized, issues


def validate_frame_readability(
    check: Any,
    *,
    slide_count: int,
    required_formats: Iterable[str] = DEFAULT_NATIVE_FORMATS,
    expected_director_event_fingerprint: str | None = None,
    event_a_review_provenance: Mapping[str, Any] | None = None,
    event_a_creator_correction_fingerprint: str | None = None,
    expected_creator_correction_fingerprint: str | None = None,
    event_a_generation_payload_fingerprint: str | None = None,
    expected_generation_payload_fingerprint: str | None = None,
    expected_frame_bindings: Mapping[tuple[int, str], Any] | None = None,
    expected_storyboard_fingerprint: str | None = None,
    director_author_id: str | None = None,
    director_reviewer_id: str | None = None,
    package_dir: Path | None = None,
    provenance_package_dir: Path | None = None,
    require_files: bool = False,
) -> list[str]:
    """Return blockers for the post-generation rendered-frame event."""

    if not isinstance(check, dict):
        return ["visual_story_readability must be a structured object."]

    issues: list[str] = []
    if check.get("pass") is not True or check.get("status") != "PASS":
        issues.append("visual_story_readability must be PASS with pass true.")
    if check.get("event") != "rendered_frame_story_audit":
        issues.append(
            "visual_story_readability.event must be rendered_frame_story_audit."
        )
    if check.get("image_first") is not True:
        issues.append("visual_story_readability.image_first must be true.")
    _require_text(check, "reviewer_id", issues, "visual_story_readability", minimum_words=1)
    _require_text(check, "reviewer_evidence", issues, "visual_story_readability")
    reviewer_id = str(check.get("reviewer_id") or "")
    if director_author_id and _normalized(reviewer_id) == _normalized(director_author_id):
        issues.append(
            "visual_story_readability reviewer must be independent from the route author."
        )
    if director_reviewer_id and _normalized(reviewer_id) == _normalized(director_reviewer_id):
        issues.append(
            "visual_story_readability reviewer must be independent from the copy-hidden storyboard reviewer."
        )

    actual_director_event_fingerprint = str(
        check.get("source_director_event_fingerprint") or ""
    )
    if not _valid_sha256(actual_director_event_fingerprint):
        issues.append(
            "visual_story_readability.source_director_event_fingerprint is missing or invalid."
        )
    if expected_director_event_fingerprint is None:
        issues.append(
            "visual_story_readability requires the current complete director Event A fingerprint."
        )
    elif actual_director_event_fingerprint != expected_director_event_fingerprint:
        issues.append("visual_story_readability is stale for the complete current director Event A payload.")

    if not _valid_sha256(expected_creator_correction_fingerprint):
        issues.append(
            "visual_story_readability requires the current creator-correction fingerprint."
        )
    elif event_a_creator_correction_fingerprint != expected_creator_correction_fingerprint:
        issues.append(
            "visual_story_readability is stale because Event A does not bind the current creator-correction state."
        )
    if not _valid_sha256(expected_generation_payload_fingerprint):
        issues.append(
            "visual_story_readability requires the current prompt-pack generation-payload fingerprint."
        )
    elif event_a_generation_payload_fingerprint != expected_generation_payload_fingerprint:
        issues.append(
            "visual_story_readability is stale because Event A does not bind the current prompt-pack.json."
        )
    if expected_storyboard_fingerprint is not None:
        issues.append(
            "expected_storyboard_fingerprint is obsolete; bind Event B with expected_director_event_fingerprint."
        )

    _require_text(check, "sequence_read", issues, "visual_story_readability")
    _require_text(check, "relationship_turn", issues, "visual_story_readability")
    _require_text(check, "setup_payoff_evidence", issues, "visual_story_readability")
    _require_text(check, "weakest_frame", issues, "visual_story_readability")
    _require_text(check, "repair_decision", issues, "visual_story_readability")

    required_format_set = set(required_formats)
    if not required_format_set:
        issues.append("visual_story_readability requires at least one locked native format.")
    unsupported_formats = sorted(required_format_set - set(SUPPORTED_NATIVE_FORMATS))
    if unsupported_formats:
        issues.append(
            "visual_story_readability has unsupported requested formats: "
            + ", ".join(unsupported_formats)
            + "."
        )
    reviewed_formats = check.get("reviewed_native_formats")
    if not isinstance(reviewed_formats, list) or set(reviewed_formats) != required_format_set:
        issues.append(
            "visual_story_readability.reviewed_native_formats must cover exactly: "
            + ", ".join(sorted(required_format_set))
            + "."
        )

    frames = check.get("frames")
    if not isinstance(frames, list):
        return issues + ["visual_story_readability.frames must be a per-slide, per-format list."]

    expected_keys = {
        (slide, output_format)
        for slide in range(1, slide_count + 1)
        for output_format in required_format_set
    }
    normalized_bindings: dict[tuple[int, str], ExpectedFrameAsset] = {}
    if require_files or expected_frame_bindings is not None:
        normalized_bindings, binding_issues = _normalize_expected_frame_bindings(
            expected_frame_bindings,
            expected_keys=expected_keys,
        )
        issues.extend(binding_issues)
    if require_files and package_dir is None:
        issues.append(
            "visual_story_readability file-backed validation requires package_dir."
        )

    seen: set[tuple[int, str]] = set()
    used_resolved_files: dict[Path, tuple[int, str]] = {}
    used_file_identities: dict[tuple[int, int], tuple[int, str]] = {}
    used_image_digests: dict[str, tuple[int, str]] = {}
    for index, frame in enumerate(frames, start=1):
        if not isinstance(frame, dict):
            issues.append(f"visual_story_readability.frames record {index} must be an object.")
            continue
        number = _slide_number(frame)
        output_format = str(frame.get("format") or "")
        key = (number, output_format)
        prefix = f"visual_story_readability.frames[{number}:{output_format or '?'}]"
        if key not in expected_keys:
            issues.append(f"{prefix} is not a required slide/native-format pair.")
        elif key in seen:
            issues.append(f"visual_story_readability.frames repeats slide {number} {output_format}.")
        else:
            seen.add(key)

        if frame.get("status") != "PASS":
            issues.append(f"{prefix}.status must be PASS.")
        for field in (
            "expected_silent_read",
            "observed_image_first_read",
            "focal_hierarchy",
            "match_rationale",
            "evidence",
        ):
            _require_text(frame, field, issues, prefix)
        for field in (
            "core_action_legible",
            "relationship_turn_legible",
            "hands_gaze_prop_legible",
            "storyboard_match",
            "native_format_readability",
        ):
            if frame.get(field) is not True:
                issues.append(f"{prefix}.{field} must be true.")

        for field in ("copy_visual_contradictions", "unexpected_story"):
            values = frame.get(field)
            if not isinstance(values, list):
                issues.append(f"{prefix}.{field} must be a list.")
            elif values:
                issues.append(f"{prefix}.{field} must be empty before PASS.")

        if (
            frame.get("file") not in (None, "")
            and frame.get("path") not in (None, "")
            and str(frame.get("file")) != str(frame.get("path"))
        ):
            issues.append(f"{prefix}.file and .path cannot name different assets.")
        raw_file = _frame_file_value(frame)
        relative_file, relative_file_issue = _safe_package_relative_path(raw_file)
        if relative_file_issue:
            issues.append(f"{prefix}.file {relative_file_issue}.")

        expected_asset = normalized_bindings.get(key)
        if expected_asset is not None and relative_file != expected_asset.relative_path:
            issues.append(
                f"{prefix}.file must equal canonical package asset {expected_asset.relative_path}."
            )

        path: Path | None = None
        if package_dir is not None and relative_file is not None:
            path = _path_inside_package(package_dir, relative_file)
            if path is None:
                issues.append(f"{prefix}.file escapes the package root.")
            elif path in used_resolved_files:
                previous = used_resolved_files[path]
                issues.append(
                    f"{prefix}.file reuses the asset already bound to {previous[0]}:{previous[1]}."
                )
            else:
                used_resolved_files[path] = key

        actual_image_fingerprint: str | None = None
        if require_files and path is not None:
            if not path.exists():
                issues.append(
                    f"{prefix}.file does not exist: {relative_file}."
                )
            elif path.is_symlink():
                issues.append(f"{prefix}.file must be a regular package asset, not a symlink.")
            elif not path.is_file():
                issues.append(f"{prefix}.file must be a regular image file.")
            else:
                stat_result = path.stat()
                file_identity = (stat_result.st_dev, stat_result.st_ino)
                if file_identity in used_file_identities:
                    previous = used_file_identities[file_identity]
                    issues.append(
                        f"{prefix}.file is the same hardlinked asset as "
                        f"{previous[0]}:{previous[1]}; every expected frame needs distinct pixels."
                    )
                else:
                    used_file_identities[file_identity] = key
                actual_image_fingerprint = image_file_fingerprint(path)
                if actual_image_fingerprint in used_image_digests:
                    previous = used_image_digests[actual_image_fingerprint]
                    issues.append(
                        f"{prefix}.file duplicates the exact rendered bytes used by "
                        f"{previous[0]}:{previous[1]}; every expected frame needs distinct pixels."
                    )
                else:
                    used_image_digests[actual_image_fingerprint] = key
                try:
                    with Image.open(path) as image:
                        decoded_format = str(image.format or "").upper()
                        actual_dimensions = tuple(image.size)
                        image.verify()
                except (UnidentifiedImageError, OSError, SyntaxError, ValueError):
                    issues.append(f"{prefix}.file is not a decodable image.")
                else:
                    expected_suffix = PurePosixPath(relative_file).suffix.lower()
                    expected_decoder_format = {
                        ".png": "PNG",
                        ".jpg": "JPEG",
                        ".jpeg": "JPEG",
                        ".webp": "WEBP",
                    }.get(expected_suffix)
                    if expected_decoder_format and decoded_format != expected_decoder_format:
                        issues.append(
                            f"{prefix}.file bytes are {decoded_format or 'unknown'}, expected {expected_decoder_format}."
                        )
                    if (
                        expected_asset is not None
                        and actual_dimensions != expected_asset.dimensions
                    ):
                        issues.append(
                            f"{prefix}.file dimensions are {actual_dimensions[0]}x{actual_dimensions[1]}, "
                            f"expected {expected_asset.dimensions[0]}x{expected_asset.dimensions[1]}."
                        )

        recorded_fingerprint = str(frame.get("image_fingerprint") or "")
        if not _valid_sha256(recorded_fingerprint):
            issues.append(f"{prefix}.image_fingerprint is missing or invalid.")
        elif actual_image_fingerprint is not None:
            if recorded_fingerprint != actual_image_fingerprint:
                issues.append(f"{prefix}.image_fingerprint is stale for the rendered file.")

    missing = sorted(expected_keys - seen)
    if missing:
        missing_text = ", ".join(f"{slide}:{fmt}" for slide, fmt in missing)
        issues.append(
            "visual_story_readability.frames missing required records: " + missing_text + "."
        )
    if len(frames) != len(expected_keys):
        issues.append(
            f"visual_story_readability.frames has {len(frames)} records, expected {len(expected_keys)}."
        )

    declared_issues = check.get("issues")
    if not isinstance(declared_issues, list):
        issues.append("visual_story_readability.issues must be a list, even when empty.")
    elif declared_issues:
        issues.append("visual_story_readability declares unresolved issues while claiming PASS.")

    provenance_issues, event_b_identity = _validate_review_provenance(
        check.get("review_provenance"),
        prefix="visual_story_readability.review_provenance",
        expected_input_fingerprint=frame_review_input_fingerprint(frames),
        expected_output_fingerprint=frame_review_output_fingerprint(check),
        require_author=False,
        package_dir=provenance_package_dir or package_dir,
    )
    issues.extend(provenance_issues)
    if event_b_identity and reviewer_id != event_b_identity.get("reviewer_task_id"):
        issues.append(
            "visual_story_readability.reviewer_id must equal review_provenance.reviewer_task_id."
        )

    if not isinstance(event_a_review_provenance, Mapping):
        issues.append(
            "visual_story_readability requires the current Event A review_provenance to verify reviewer independence."
        )
    else:
        event_a_ids = {
            field: str(event_a_review_provenance.get(field) or "").strip()
            for field in (
                "author_task_id",
                "author_run_id",
                "reviewer_task_id",
                "reviewer_run_id",
            )
        }
        for field, value in event_a_ids.items():
            if not _concrete_text(value, minimum_words=1) or len(value) < 4:
                issues.append(
                    f"Event A review_provenance.{field} is required for Event B independence."
                )
        if event_b_identity:
            event_b_task = _normalized(event_b_identity.get("reviewer_task_id"))
            event_b_run = _normalized(event_b_identity.get("reviewer_run_id"))
            if event_b_task in {
                _normalized(event_a_ids["author_task_id"]),
                _normalized(event_a_ids["reviewer_task_id"]),
            }:
                issues.append(
                    "Event B reviewer task ID must differ from both the route author and Event A reviewer."
                )
            if event_b_run in {
                _normalized(event_a_ids["author_run_id"]),
                _normalized(event_a_ids["reviewer_run_id"]),
            }:
                issues.append(
                    "Event B reviewer run ID must differ from both the route author and Event A reviewer."
                )

    return issues


def director_reviewer_id(plan: Any) -> str | None:
    if not isinstance(plan, dict):
        return None
    director = plan.get(DIRECTOR_STORYBOARD_KEY)
    if not isinstance(director, dict):
        return None
    value = str(director.get("reviewer_id") or "").strip()
    return value or None


def director_author_id(plan: Any) -> str | None:
    if not isinstance(plan, dict):
        return None
    director = plan.get(DIRECTOR_STORYBOARD_KEY)
    if not isinstance(director, dict):
        return None
    value = str(director.get("author_id") or "").strip()
    return value or None


def director_source_fingerprint(plan: Any) -> str | None:
    if not isinstance(plan, dict):
        return None
    director = plan.get(DIRECTOR_STORYBOARD_KEY)
    if not isinstance(director, dict):
        return None
    value = str(director.get("source_fingerprint") or "").strip()
    return value or None


def director_creator_correction_fingerprint(plan: Any) -> str | None:
    if not isinstance(plan, dict):
        return None
    director = plan.get(DIRECTOR_STORYBOARD_KEY)
    if not isinstance(director, dict):
        return None
    value = str(director.get("creator_correction_fingerprint") or "").strip()
    return value or None


def director_generation_payload_fingerprint(plan: Any) -> str | None:
    if not isinstance(plan, dict):
        return None
    director = plan.get(DIRECTOR_STORYBOARD_KEY)
    if not isinstance(director, dict):
        return None
    value = str(director.get("generation_payload_fingerprint") or "").strip()
    return value or None


def director_review_provenance(plan: Any) -> dict[str, Any] | None:
    """Return a defensive copy of Event A's auditable review provenance."""

    if not isinstance(plan, dict):
        return None
    director = plan.get(DIRECTOR_STORYBOARD_KEY)
    if not isinstance(director, dict):
        return None
    provenance = director.get("review_provenance")
    if not isinstance(provenance, dict):
        return None
    return deepcopy(provenance)
