"""Compact physical-scene preflight and rendered-pixel story validation.

Only files and pixels certify output. The default workflow does not require
agent provenance, task IDs, raw-response ledgers, or chained fingerprints.
"""

from __future__ import annotations

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
CREATOR_CORRECTION_ARTIFACTS = ("creator-correction.json", "correction.json")
BRANDMARK_PLACEMENT = "top-right"


@dataclass(frozen=True)
class ExpectedFrameAsset:
    relative_path: str
    dimensions: tuple[int, int]


def _stable_fingerprint(payload: Any, *, namespace: str) -> str:
    encoded = json.dumps(
        {"namespace": namespace, "payload": payload},
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return "sha256:" + hashlib.sha256(encoded).hexdigest()


def generation_payload_fingerprint(prompt_pack: Any) -> str:
    return _stable_fingerprint(prompt_pack, namespace="visual-generation-payload/v1")


def current_creator_correction_fingerprint(package_dir: Path) -> str:
    root = Path(package_dir)
    artifacts: list[dict[str, Any]] = []
    for filename in CREATOR_CORRECTION_ARTIFACTS:
        path = root / filename
        if not path.exists() and not path.is_symlink():
            continue
        entry: dict[str, Any] = {"name": filename, "symlink": path.is_symlink()}
        try:
            raw = path.read_bytes()
            entry["payload"] = json.loads(raw.decode("utf-8"))
        except (OSError, UnicodeDecodeError, json.JSONDecodeError):
            try:
                entry["raw_sha256"] = hashlib.sha256(path.read_bytes()).hexdigest()
            except OSError:
                entry["unreadable"] = True
        artifacts.append(entry)
    return _stable_fingerprint(artifacts, namespace="creator-correction-state/v1")


def _director_payload(plan_or_director: Any) -> dict[str, Any] | None:
    if not isinstance(plan_or_director, dict):
        return None
    nested = plan_or_director.get(DIRECTOR_STORYBOARD_KEY)
    return nested if isinstance(nested, dict) else plan_or_director


def _slide_number(record: Mapping[str, Any], fallback: int = 0) -> int:
    try:
        return int(record.get("slide") or record.get("slide_number") or fallback)
    except (TypeError, ValueError):
        return fallback


def _records(payload: Any) -> list[dict[str, Any]]:
    if isinstance(payload, list):
        return [item for item in payload if isinstance(item, dict)]
    if isinstance(payload, dict) and isinstance(payload.get("slides"), list):
        return [item for item in payload["slides"] if isinstance(item, dict)]
    return []


def _canonical_storyboard_source(slides: Any) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    for index, record in enumerate(_records(slides), start=1):
        result.append(
            {
                "slide": _slide_number(record, index),
                "copy": str(record.get("copy") or record.get("text") or ""),
                "physical_action": str(
                    record.get("physical_action")
                    or record.get("visual_sentence")
                    or record.get("visual")
                    or record.get("scene")
                    or ""
                ),
            }
        )
    return result


def storyboard_source_fingerprint(slides: Any) -> str:
    return _stable_fingerprint(_canonical_storyboard_source(slides), namespace="storyboard-source/v1")


def _frame_file_value(frame: Mapping[str, Any]) -> Any:
    return frame.get("file") if frame.get("file") not in (None, "") else frame.get("path")


def requested_story_formats(package_dir: Path | None) -> tuple[str, ...]:
    return tuple(locked_formats(package_dir)) if package_dir is not None else tuple(DEFAULT_NATIVE_FORMATS)


def story_formats_from_records(records: Any) -> tuple[str, ...]:
    values: list[str] = []
    if isinstance(records, list):
        for record in records:
            if isinstance(record, Mapping):
                value = str(record.get("format") or "")
                if value and value not in values:
                    values.append(value)
    return tuple(values)


def image_file_fingerprint(path: Path) -> str:
    return "sha256:" + hashlib.sha256(Path(path).read_bytes()).hexdigest()


PIXEL_QA_ORDER = (
    "semantic_action",
    "relationship_state",
    "entity_anatomy_spatial",
    "identity",
    "text_style_dimensions",
)
_PIXEL_GATE_ALIASES = {
    "semantic_action": ("semantic_action", "semantic_action_legible", "core_action_legible", "action_legible"),
    "relationship_state": ("relationship_state", "relationship_state_legible", "relationship_turn_legible"),
    "entity_anatomy_spatial": ("entity_anatomy_spatial", "entity_anatomy_spatial_integrity", "anatomy_spatial", "scene_entity_integrity", "anatomy_inventory", "spatial_topology"),
    "identity": ("identity", "identity_consistency", "identity_match"),
    "text_style_dimensions": ("text_style_dimensions", "exact_text_style_dimensions_brandmark", "integrated_text_style_dimensions", "exact_text", "brandmark", "style", "dimensions"),
}


def _explicit_pass_value(value: Any) -> bool | None:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        normalized = value.strip().lower()
        if normalized in {"pass", "passed", "true", "yes", "ok"}:
            return True
        if normalized in {"fail", "failed", "false", "no", "blocked"}:
            return False
    if isinstance(value, Mapping):
        if isinstance(value.get("pass"), bool):
            return bool(value["pass"])
        return _explicit_pass_value(value.get("status") or value.get("verdict"))
    return None


def _numbered_pixel_records(payload: Mapping[str, Any]) -> list[Mapping[str, Any]]:
    result: list[Mapping[str, Any]] = []
    for key in ("slides", "frames"):
        value = payload.get(key)
        if isinstance(value, list):
            result.extend(item for item in value if isinstance(item, Mapping))
    return result


def first_failed_pixel_gate(qa: Any) -> tuple[str, str] | None:
    """Return the earliest explicit pixel failure in the fixed QA order."""

    if not isinstance(qa, Mapping):
        return None
    checks = qa.get("checks")
    checks = checks if isinstance(checks, Mapping) else {}
    readability = checks.get(VISUAL_STORY_READABILITY_KEY)
    readability = readability if isinstance(readability, Mapping) else {}
    containers = (qa, checks, readability)
    records = [*_numbered_pixel_records(qa), *_numbered_pixel_records(readability)]
    reviews = qa.get("reviews") or qa.get("reviewers")
    reviews = reviews if isinstance(reviews, Mapping) else {}
    legacy_reviews = {
        "entity_anatomy_spatial": ("anatomy_entity_spatial_identity",),
        "identity": ("anatomy_entity_spatial_identity",),
        "text_style_dimensions": ("storytelling_richness_text_style",),
    }

    for gate in PIXEL_QA_ORDER:
        aliases = _PIXEL_GATE_ALIASES[gate]
        for container in containers:
            for alias in aliases:
                if alias in container and _explicit_pass_value(container[alias]) is False:
                    return gate, f"{gate} failed on the rendered pixels ({alias})."
        for record in records:
            slide = record.get("slide") or record.get("slide_number") or "?"
            record_checks = record.get("checks")
            record_checks = record_checks if isinstance(record_checks, Mapping) else {}
            for record_container in (record, record_checks):
                for alias in aliases:
                    if alias in record_container and _explicit_pass_value(record_container[alias]) is False:
                        return gate, f"{gate} failed on rendered slide {slide} ({alias})."
        for alias in legacy_reviews.get(gate, ()):
            if alias in reviews and _explicit_pass_value(reviews[alias]) is False:
                return gate, f"{gate} failed in the rendered-pixel review ({alias})."
    return None


def _physical_action(record: Mapping[str, Any]) -> str:
    staged = record.get("staged_action")
    if isinstance(staged, Mapping):
        values = [str(staged.get(key) or "").strip() for key in ("subject", "action", "target_or_object", "reaction_or_consequence")]
        if all(values):
            return " ".join(values)
    for key in ("physical_action", "visual_sentence", "observable_action", "visual", "scene", "silent_read"):
        value = record.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return ""


_ACTION_PLACEHOLDER_PREFIXES = (
    "draft needed",
    "placeholder",
    "same as copy",
    "scene needed",
    "tbd",
    "todo",
)


def physical_action_issue(action: Any, *, copy: Any = "") -> str | None:
    """Return why a proposed scene is not yet a concrete physical event."""

    text = " ".join(str(action or "").strip().split())
    normalized = text.lower().strip(" .:;!?-")
    normalized_copy = " ".join(str(copy or "").strip().lower().split()).strip(" .:;!?-")
    if not text or len(text.split()) < 6:
        return "needs a concrete physical action with subject, action, target, and visible consequence"
    if normalized.startswith(_ACTION_PLACEHOLDER_PREFIXES):
        return "contains a placeholder instead of a physical action"
    if normalized_copy and normalized == normalized_copy:
        return "repeats the slide copy instead of describing visible action"
    return None


_GENERIC_VISUAL_PHRASES = {
    "appropriate composition",
    "cozy home",
    "couple moment",
    "nice lighting",
    "some props",
    "warm scene",
}


def _generic_visual_text(value: Any, *, minimum_words: int = 3) -> bool:
    text = " ".join(str(value or "").strip().lower().split())
    return not text or text in _GENERIC_VISUAL_PHRASES or len(text.split()) < minimum_words


def validate_director_storyboard(
    plan: Any,
    *,
    slide_count: int,
    expected_slides: Any | None = None,
    expected_formats: Iterable[str] | None = None,
) -> list[str]:
    """Optional lightweight physical-action preflight.

    Current copy and canvas are validated by their own package artifacts, not
    by a second fingerprint graph.
    """
    if not isinstance(plan, dict):
        return ["visual direction must be a structured object."]
    payload = _director_payload(plan) or {}
    records = _records(payload)
    if not records:
        records = _records(plan)
    issues: list[str] = []
    if len(records) != slide_count:
        issues.append(f"visual direction has {len(records)} slide records, expected {slide_count}.")
    seen: set[int] = set()
    narrative_jobs: list[str] = []
    shot_sizes: list[str] = []
    for index, record in enumerate(records, start=1):
        slide = _slide_number(record, index)
        if slide in seen or not 1 <= slide <= slide_count:
            issues.append(f"visual direction has invalid or repeated slide {slide}.")
        seen.add(slide)
        action_issue = physical_action_issue(
            _physical_action(record),
            copy=record.get("copy") or record.get("text"),
        )
        if action_issue:
            issues.append(f"slide {slide} {action_issue}.")
        narrative_job = str(record.get("narrative_job") or "").strip().lower()
        if narrative_job:
            narrative_jobs.append(narrative_job)
        shot = record.get("shot")
        if isinstance(shot, Mapping):
            shot_size = str(shot.get("size") or "").strip().lower()
            if shot_size:
                shot_sizes.append(shot_size)
            if "camera_position" in shot and _generic_visual_text(shot.get("camera_position")):
                issues.append(f"slide {slide}.shot.camera_position is generic rather than physically specific.")
        if "silent_read" in record and _generic_visual_text(record.get("silent_read")):
            issues.append(f"slide {slide}.silent_read is generic rather than an observable action.")
        setting = record.get("setting")
        if isinstance(setting, Mapping) and "motivated_light" in setting:
            if _generic_visual_text(setting.get("motivated_light")):
                issues.append(f"slide {slide}.setting.motivated_light is generic rather than motivated by the scene.")
        evidence = record.get("story_evidence")
        if isinstance(evidence, list) and evidence:
            for evidence_index, item in enumerate(evidence, start=1):
                if not isinstance(item, Mapping) or any(
                    _generic_visual_text(item.get(field))
                    for field in ("carrier", "observable_state", "narrative_job")
                ):
                    issues.append(
                        f"slide {slide}.story_evidence[{evidence_index}] is generic rather than visible story proof."
                    )
                    break
    if slide_count > 1 and len(narrative_jobs) == len(records) and len(set(narrative_jobs)) < 2:
        issues.append("visual direction repeats one narrative job across the whole sequence.")
    if slide_count > 2 and len(shot_sizes) == len(records) and len(set(shot_sizes)) < 2:
        if not str(payload.get("deliberate_shot_repetition_reason") or "").strip():
            issues.append("visual direction repeats one shot size without a deliberate story reason.")
    if expected_slides is not None:
        expected_numbers = {
            _slide_number(record, index)
            for index, record in enumerate(_records(expected_slides), start=1)
        }
        if seen != expected_numbers:
            issues.append("visual direction slide numbers do not match slides.json.")
    if expected_formats is not None:
        requested = payload.get("requested_formats")
        if requested is not None and list(requested) != [str(item) for item in expected_formats]:
            issues.append("visual direction requested_formats does not match the current format lock.")
    return issues


def _safe_relative_path(raw: Any) -> tuple[str | None, str | None]:
    value = str(raw or "").strip()
    if not value:
        return None, "is missing"
    if PurePosixPath(value).is_absolute() or PureWindowsPath(value).is_absolute():
        return None, "must be package-relative"
    path = PurePosixPath(value.replace("\\", "/"))
    if ".." in path.parts:
        return None, "must not escape the package"
    return path.as_posix(), None


def _coerce_expected_asset(value: Any) -> ExpectedFrameAsset | None:
    if isinstance(value, ExpectedFrameAsset):
        return value
    if not isinstance(value, Mapping):
        return None
    path = value.get("relative_path") or value.get("path")
    dimensions = value.get("dimensions") or value.get("size")
    if not path or not isinstance(dimensions, (list, tuple)) or len(dimensions) != 2:
        return None
    try:
        return ExpectedFrameAsset(str(path), (int(dimensions[0]), int(dimensions[1])))
    except (TypeError, ValueError):
        return None


def validate_frame_readability(
    check: Any,
    *,
    slide_count: int,
    required_formats: Iterable[str] = DEFAULT_NATIVE_FORMATS,
    expected_frame_bindings: Mapping[tuple[int, str], Any] | None = None,
    package_dir: Path | None = None,
    require_files: bool = False,
) -> list[str]:
    """Validate image-first story evidence against the current frame files."""
    if not isinstance(check, dict):
        return ["visual_story_readability must be a structured object."]
    failed = first_failed_pixel_gate(check)
    if failed is not None:
        return [failed[1]]

    issues: list[str] = []
    if check.get("pass") is not True or str(check.get("status") or "").upper() != "PASS":
        issues.append("visual_story_readability must be PASS with pass true.")
    if check.get("image_first") is False:
        issues.append("visual_story_readability.image_first cannot be false.")

    formats = tuple(str(item) for item in required_formats)
    unsupported = sorted(set(formats) - set(SUPPORTED_NATIVE_FORMATS))
    if unsupported:
        issues.append("unsupported requested formats: " + ", ".join(unsupported))
    frames = check.get("frames")
    if not isinstance(frames, list):
        return issues + ["visual_story_readability.frames must be a per-slide, per-format list."]

    expected_keys = {(slide, output_format) for slide in range(1, slide_count + 1) for output_format in formats}
    normalized_bindings = {
        key: asset
        for key, raw in (expected_frame_bindings or {}).items()
        if (asset := _coerce_expected_asset(raw)) is not None
    }
    seen: set[tuple[int, str]] = set()
    used_hashes: set[str] = set()
    for index, frame in enumerate(frames, start=1):
        if not isinstance(frame, Mapping):
            issues.append(f"frame record {index} must be an object.")
            continue
        slide = _slide_number(frame, index)
        output_format = str(frame.get("format") or "")
        key = (slide, output_format)
        prefix = f"frame[{slide}:{output_format or '?'}]"
        if key not in expected_keys:
            issues.append(f"{prefix} is not a locked slide/format pair.")
        elif key in seen:
            issues.append(f"{prefix} is repeated.")
        seen.add(key)
        if frame.get("core_action_legible") is not True:
            issues.append(f"{prefix}.core_action_legible must be true.")
        if frame.get("relationship_turn_legible") is not True:
            issues.append(f"{prefix}.relationship_turn_legible must be true.")
        if not str(frame.get("observed_image_first_read") or "").strip():
            issues.append(f"{prefix}.observed_image_first_read is missing.")
        if not str(frame.get("evidence") or "").strip():
            issues.append(f"{prefix}.evidence is missing.")
        contradictions = frame.get("copy_visual_contradictions")
        if isinstance(contradictions, list) and contradictions:
            issues.append(
                f"{prefix}.copy_visual_contradictions: "
                + "; ".join(str(item) for item in contradictions if str(item).strip())
            )
        unexpected_story = frame.get("unexpected_story")
        if isinstance(unexpected_story, list) and unexpected_story:
            issues.append(
                f"{prefix}.unexpected_story: "
                + "; ".join(str(item) for item in unexpected_story if str(item).strip())
            )

        relative_path, path_issue = _safe_relative_path(_frame_file_value(frame))
        if path_issue:
            issues.append(f"{prefix}.file {path_issue}.")
            continue
        expected_asset = normalized_bindings.get(key)
        if expected_asset and relative_path != expected_asset.relative_path:
            issues.append(f"{prefix}.file must equal {expected_asset.relative_path}.")
        if package_dir is None:
            if require_files:
                issues.append("file-backed readability validation requires package_dir.")
            continue
        path = Path(package_dir) / str(relative_path)
        try:
            resolved = path.resolve(strict=True)
            resolved.relative_to(Path(package_dir).resolve(strict=True))
        except (FileNotFoundError, OSError, ValueError):
            issues.append(f"{prefix}.file is missing or outside the package.")
            continue
        if path.is_symlink() or not path.is_file():
            issues.append(f"{prefix}.file must be a regular package image.")
            continue
        digest = image_file_fingerprint(path)
        if digest in used_hashes:
            issues.append(f"{prefix}.file duplicates another reviewed frame's exact bytes.")
        used_hashes.add(digest)
        if str(frame.get("image_fingerprint") or "") != digest:
            issues.append(f"{prefix}.image_fingerprint is missing or stale.")
        try:
            with Image.open(path) as image:
                dimensions = tuple(image.size)
                image.verify()
        except (UnidentifiedImageError, OSError, SyntaxError, ValueError):
            issues.append(f"{prefix}.file is not a decodable image.")
            continue
        if expected_asset and dimensions != expected_asset.dimensions:
            issues.append(
                f"{prefix}.file dimensions are {dimensions[0]}x{dimensions[1]}, expected {expected_asset.dimensions[0]}x{expected_asset.dimensions[1]}."
            )

    missing = sorted(expected_keys - seen)
    if missing:
        issues.append("frames missing required records: " + ", ".join(f"{slide}:{fmt}" for slide, fmt in missing))
    if len(frames) != len(expected_keys):
        issues.append(f"frames has {len(frames)} records, expected {len(expected_keys)}.")
    if isinstance(check.get("issues"), list) and check["issues"]:
        issues.append("visual_story_readability declares unresolved issues while claiming PASS.")
    return issues
