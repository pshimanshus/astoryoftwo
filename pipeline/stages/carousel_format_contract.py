"""Authoritative current-request canvas contract for carousel image outputs.

The contract is intentionally independent of generated folders.  A folder is
evidence that pixels exist, not evidence that the creator requested that
surface.  Callers must lock formats from the current request and then use the
helpers in this module for generation, packaging, QA, and final-audit paths.
"""

from __future__ import annotations

import json
import hashlib
from pathlib import Path
from typing import Any, Iterable


FORMAT_CONTRACT_FILENAME = "format-contract.json"
FORMAT_CONTRACT_SCHEMA_VERSION = "1.0"

INSTAGRAM_POST_FORMAT = "instagram_post"
REELS_STORIES_FORMAT = "reels_stories"
SQUARE_FORMAT = "square"

SUPPORTED_NATIVE_FORMATS = (
    INSTAGRAM_POST_FORMAT,
    REELS_STORIES_FORMAT,
    SQUARE_FORMAT,
)
DEFAULT_NATIVE_FORMATS = (INSTAGRAM_POST_FORMAT,)

FORMAT_SPECS: dict[str, dict[str, Any]] = {
    INSTAGRAM_POST_FORMAT: {
        "label": "Instagram post",
        "aspect_ratio": "3:4",
        "folder": "final",
        "prompt_folder": "instagram-post",
        "source_prefix": "instagram-post",
        "source_size": (1440, 1920),
        "allowed_source_sizes": ((1440, 1920), (1080, 1440)),
        "target_size": (1080, 1440),
        "request_size": "1440x1920",
    },
    REELS_STORIES_FORMAT: {
        "label": "Reels/Stories",
        "aspect_ratio": "9:16",
        "folder": "final-reels-stories",
        "prompt_folder": "reels-stories",
        "source_prefix": "reels-stories",
        "source_size": (1080, 1920),
        "allowed_source_sizes": ((1080, 1920),),
        "target_size": (1080, 1920),
        "request_size": "1080x1920",
    },
    SQUARE_FORMAT: {
        "label": "Square",
        "aspect_ratio": "1:1",
        "folder": "final-square",
        "prompt_folder": "square",
        "source_prefix": "square",
        "source_size": (1080, 1080),
        "allowed_source_sizes": ((1080, 1080),),
        "target_size": (1080, 1080),
        "request_size": "1080x1080",
    },
}


def normalize_requested_formats(formats: Iterable[str] | None) -> tuple[str, ...]:
    """Validate and return formats in canonical order.

    ``None`` is the only defaulting signal and means the 3:4 post canvas.  An
    explicitly empty collection is invalid because it cannot describe a
    generation request.
    """

    if formats is None:
        return DEFAULT_NATIVE_FORMATS
    requested = [str(value).strip() for value in formats]
    if not requested or any(not value for value in requested):
        raise ValueError("At least one current-request output format must be locked.")
    unsupported = sorted(set(requested) - set(SUPPORTED_NATIVE_FORMATS))
    if unsupported:
        raise ValueError("Unsupported current-request output format(s): " + ", ".join(unsupported))
    requested_set = set(requested)
    return tuple(value for value in SUPPORTED_NATIVE_FORMATS if value in requested_set)


def format_spec(output_format: str) -> dict[str, Any]:
    try:
        return FORMAT_SPECS[output_format]
    except KeyError as exc:
        raise ValueError(f"Unsupported current-request output format: {output_format}") from exc


def _public_spec(output_format: str) -> dict[str, Any]:
    spec = format_spec(output_format)
    source_width, source_height = spec["source_size"]
    width, height = spec["target_size"]
    return {
        "format": output_format,
        "label": spec["label"],
        "aspect_ratio": spec["aspect_ratio"],
        "folder": spec["folder"],
        "source_size": f"{source_width}x{source_height}",
        "target_size": f"{width}x{height}",
    }


def build_format_contract(
    formats: Iterable[str] | None = None,
    *,
    source: str = "current_request",
) -> dict[str, Any]:
    locked = normalize_requested_formats(formats)
    return {
        "schema_version": FORMAT_CONTRACT_SCHEMA_VERSION,
        "status": "LOCKED",
        "source": source,
        "default_applied": formats is None,
        "requested_formats": list(locked),
        "formats": [_public_spec(output_format) for output_format in locked],
        "rule": (
            "Generate only the formats locked by the current request. Generate each requested "
            "aspect ratio from its own native source; never infer another output from folders "
            "or derive one aspect ratio by cropping, padding, stretching, or extending another."
        ),
    }


def validate_format_contract(contract: Any) -> tuple[str, ...]:
    if not isinstance(contract, dict):
        raise ValueError("format-contract.json must contain a JSON object.")
    if contract.get("status") != "LOCKED":
        raise ValueError("format-contract.json status must be LOCKED.")
    locked = normalize_requested_formats(contract.get("requested_formats", []))
    entries = contract.get("formats")
    if not isinstance(entries, list) or len(entries) != len(locked):
        raise ValueError("format-contract.json formats must describe every locked format exactly once.")
    for output_format, entry in zip(locked, entries, strict=True):
        expected = _public_spec(output_format)
        if not isinstance(entry, dict) or any(entry.get(key) != value for key, value in expected.items()):
            raise ValueError(f"format-contract.json has a stale or invalid {output_format} definition.")
    return locked


def write_format_contract(
    package_dir: Path,
    formats: Iterable[str] | None = None,
    *,
    source: str = "current_request",
    replace: bool = False,
) -> dict[str, Any]:
    """Persist the request contract, protecting an explicit prior lock.

    A later explicit request may replace the synthesized post default.  An
    already-explicit lock requires ``replace=True`` so corrections are visible
    rather than accidental.
    """

    package_dir = Path(package_dir)
    path = package_dir / FORMAT_CONTRACT_FILENAME
    contract = build_format_contract(formats, source=source)
    if path.exists():
        existing = json.loads(path.read_text(encoding="utf-8"))
        existing_formats = validate_format_contract(existing)
        requested_formats = tuple(contract["requested_formats"])
        if existing_formats == requested_formats:
            return existing
        if not replace and not (existing.get("default_applied") is True and formats is not None):
            raise ValueError(
                "Current-request format contract is already locked to "
                + ", ".join(existing_formats)
                + "; pass replace=True only for an explicit creator correction."
            )
    package_dir.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(contract, indent=2, ensure_ascii=False), encoding="utf-8")
    return contract


def _legacy_explicit_formats(package_dir: Path) -> tuple[str, ...] | None:
    """Read explicit request metadata from old artifacts without folder inference."""

    for filename in ("image-generation.json", "final-images.json", "manifest.json"):
        path = package_dir / filename
        if not path.exists():
            continue
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            continue
        if not isinstance(payload, dict):
            continue
        requested = payload.get("requested_formats")
        if requested is None and isinstance(payload.get("format_contract"), dict):
            requested = payload["format_contract"].get("requested_formats")
        if isinstance(requested, list):
            return normalize_requested_formats(requested)
    return None


def load_format_contract(package_dir: Path) -> dict[str, Any]:
    """Load the authoritative lock or synthesize the post-only legacy default."""

    package_dir = Path(package_dir)
    path = package_dir / FORMAT_CONTRACT_FILENAME
    if path.exists():
        contract = json.loads(path.read_text(encoding="utf-8"))
        validate_format_contract(contract)
        return contract
    legacy = _legacy_explicit_formats(package_dir)
    if legacy is not None:
        return build_format_contract(legacy, source="legacy_explicit_request_metadata")
    return build_format_contract(None, source="legacy_post_default")


def locked_formats(package_dir: Path) -> tuple[str, ...]:
    return validate_format_contract(load_format_contract(package_dir))


def native_output_contract(formats: Iterable[str] | None = None) -> dict[str, Any]:
    locked = normalize_requested_formats(formats)
    return {
        "formats": list(locked),
        "workers": [f"{output_format}_output" for output_format in locked]
        + ["identity_visual_qa"],
        "rule": build_format_contract(locked)["rule"],
    }


def format_contract_fingerprint(contract_or_formats: Any) -> str:
    """Return a stable digest of the locked formats and canonical canvas specs."""

    if isinstance(contract_or_formats, dict):
        locked = validate_format_contract(contract_or_formats)
    else:
        locked = normalize_requested_formats(contract_or_formats)
    payload = {
        "requested_formats": list(locked),
        "formats": [_public_spec(output_format) for output_format in locked],
    }
    encoded = json.dumps(
        payload,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return "sha256:" + hashlib.sha256(encoded).hexdigest()


def locked_format_contract_fingerprint(package_dir: Path) -> str:
    return format_contract_fingerprint(load_format_contract(package_dir))


def expected_output_relative_path(output_format: str, slide_number: int) -> str:
    spec = format_spec(output_format)
    return f"{spec['folder']}/slide-{int(slide_number):02d}.png"


def expected_output_path(package_dir: Path, output_format: str, slide_number: int) -> Path:
    return Path(package_dir) / expected_output_relative_path(output_format, slide_number)


def expected_source_relative_path(output_format: str, slide_number: int) -> str:
    spec = format_spec(output_format)
    return f"final/model-native-source/{spec['source_prefix']}-slide-{int(slide_number):02d}.png"


def expected_source_path(package_dir: Path, output_format: str, slide_number: int) -> Path:
    return Path(package_dir) / expected_source_relative_path(output_format, slide_number)


def expected_frame_bindings(
    package_dir: Path,
    slide_count: int,
    locked_output_formats: Iterable[str] | None = None,
) -> dict[tuple[int, str], dict[str, Any]]:
    """Map each requested frame to its canonical package path and dimensions."""

    formats = (
        normalize_requested_formats(locked_output_formats)
        if locked_output_formats is not None
        else locked_formats(package_dir)
    )
    bindings: dict[tuple[int, str], dict[str, Any]] = {}
    for slide_number in range(1, int(slide_count) + 1):
        for output_format in formats:
            width, height = format_spec(output_format)["target_size"]
            bindings[(slide_number, output_format)] = {
                "relative_path": expected_output_relative_path(output_format, slide_number),
                "dimensions": (width, height),
                "width": width,
                "height": height,
            }
    return bindings
