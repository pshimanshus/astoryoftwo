"""Validate Codex-authored carousel pixel observations without claiming vision.

Codex performs the image inspection with ``view_image``.  This module only
checks that the resulting observations are complete, fail-fast, and bound to
the exact image bytes that were inspected.  Proof QA carries its quarantine
inventory because no final manifest exists yet.  Final QA carries no inventory;
it binds an inventory-only manifest by canonical fingerprints.
"""

from __future__ import annotations

import copy
import hashlib
import json
import re
from collections.abc import Mapping, Sequence
from pathlib import Path, PurePosixPath, PureWindowsPath
from typing import Any

from PIL import Image, UnidentifiedImageError

from pipeline.stages.carousel_format_contract import (
    format_spec,
    locked_format_contract_fingerprint,
    locked_formats,
)


PIXEL_QA_SCHEMA_VERSION = "carousel-pixel-qa/v2"
FINAL_MANIFEST_SCHEMA_VERSION = "carousel-final-images/v3"
PIXEL_QA_ORDER = (
    "physical_action",
    "relationship_state",
    "entity_spatial_integrity",
    "identity_wardrobe_accessories",
    "text_brandmark_style_dimensions",
)
INSPECTION_METHOD = "codex_view_image"
BRANDMARK = "@a.storyof.two"
_HASH_RE = re.compile(r"^sha256:[0-9a-f]{64}$")
_PROOF_PATH_RE = re.compile(
    r"^\.internal/visual-quarantine/slide-(\d{2})/attempt-(\d{2})/[^/]+\.png$"
)


def _canonical_fingerprint(value: Any, *, namespace: str) -> str:
    payload = json.dumps(
        {"namespace": namespace, "payload": value},
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return "sha256:" + hashlib.sha256(payload).hexdigest()


def _sha256_file(path: Path) -> str:
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


def asset_binding_fingerprint(
    slide: int,
    output_format: str,
    binding: Mapping[str, Any],
) -> str:
    """Bind one manifest/proof asset without including mutable QA prose."""

    payload: dict[str, Any] = {
        "slide": int(slide),
        "format": str(output_format),
        "path": str(binding.get("path") or binding.get("relative_path") or ""),
        "sha256": str(binding.get("sha256") or ""),
        "width": binding.get("width"),
        "height": binding.get("height"),
    }
    if binding.get("input_fingerprint") is not None:
        payload["input_fingerprint"] = binding.get("input_fingerprint")
    return _canonical_fingerprint(payload, namespace="carousel-asset-binding/v1")


def manifest_fingerprint(manifest: Mapping[str, Any]) -> str:
    """Return a key-order-independent binding for an inventory-only manifest."""

    return _canonical_fingerprint(manifest, namespace="carousel-final-manifest/v3")


def _records(payload: Any) -> list[dict[str, Any]]:
    if isinstance(payload, list):
        return [item for item in payload if isinstance(item, dict)]
    if isinstance(payload, Mapping) and isinstance(payload.get("slides"), list):
        return [item for item in payload["slides"] if isinstance(item, dict)]
    return []


def _slide_number(record: Mapping[str, Any], fallback: int = 0) -> int:
    try:
        return int(record.get("slide") or record.get("slide_number") or fallback)
    except (TypeError, ValueError):
        return fallback


def _package_slides(package_dir: Path) -> list[dict[str, Any]]:
    path = package_dir / "slides.json"
    payload = json.loads(path.read_text(encoding="utf-8"))
    records = _records(payload)
    if not records:
        raise ValueError("slides.json must contain slide records")
    return records


def _slide_copy(record: Mapping[str, Any]) -> str:
    for key in ("copy", "text", "on_image_text", "slide_text"):
        value = record.get(key)
        if isinstance(value, str) and value:
            return value
    return ""


def _safe_package_file(package_dir: Path, raw_path: Any) -> tuple[Path | None, str | None]:
    value = str(raw_path or "").strip()
    if not value:
        return None, "path is missing"
    if PurePosixPath(value).is_absolute() or PureWindowsPath(value).is_absolute():
        return None, "path must be package-relative"
    relative = PurePosixPath(value.replace("\\", "/"))
    if ".." in relative.parts:
        return None, "path must not escape the package"

    root = package_dir.resolve(strict=True)
    candidate = package_dir.joinpath(*relative.parts)
    current = package_dir
    for part in relative.parts:
        current = current / part
        if current.is_symlink():
            return None, "path must not contain a symlink"
    try:
        resolved = candidate.resolve(strict=True)
        resolved.relative_to(root)
    except (FileNotFoundError, OSError, ValueError):
        return None, "path is missing or escaped the package"
    if not resolved.is_file():
        return None, "path is not a file"
    return resolved, None


def _binding_issues(
    package_dir: Path,
    *,
    slide: int,
    output_format: str,
    binding: Any,
    require_binding_fingerprint: bool,
) -> list[str]:
    prefix = f"slide {slide} {output_format}"
    if not isinstance(binding, Mapping):
        return [f"{prefix}: asset binding must be an object"]
    issues: list[str] = []
    path, path_issue = _safe_package_file(
        package_dir, binding.get("path") or binding.get("relative_path")
    )
    if path_issue:
        return [f"{prefix}: {path_issue}"]

    recorded_hash = str(binding.get("sha256") or "")
    if not _HASH_RE.fullmatch(recorded_hash):
        issues.append(f"{prefix}: SHA-256 must use canonical sha256:<64 lowercase hex> form")
    elif path is not None and recorded_hash != _sha256_file(path):
        issues.append(f"{prefix}: SHA-256 is stale")

    try:
        with Image.open(path) as image:
            dimensions = tuple(image.size)
            image.verify()
    except (UnidentifiedImageError, OSError, SyntaxError, ValueError):
        return issues + [f"{prefix}: file is not a decodable image"]

    try:
        recorded_dimensions = (int(binding.get("width")), int(binding.get("height")))
    except (TypeError, ValueError):
        issues.append(f"{prefix}: width and height must be integers")
        recorded_dimensions = None
    if recorded_dimensions is not None and recorded_dimensions != dimensions:
        issues.append(f"{prefix}: recorded dimensions are stale")
    try:
        expected = tuple(format_spec(output_format)["target_size"])
    except ValueError:
        issues.append(f"{prefix}: format is not supported")
    else:
        if dimensions != expected:
            issues.append(
                f"{prefix}: dimensions are {dimensions[0]}x{dimensions[1]}, "
                f"expected {expected[0]}x{expected[1]}"
            )

    if require_binding_fingerprint:
        expected_fingerprint = asset_binding_fingerprint(slide, output_format, binding)
        if binding.get("binding_sha256") != expected_fingerprint:
            issues.append(f"{prefix}: binding_sha256 is missing or stale")
    return issues


def _status(value: Any) -> str:
    if isinstance(value, Mapping):
        value = value.get("status") or value.get("verdict")
    if isinstance(value, bool):
        return "PASS" if value else "FAIL"
    return str(value or "").strip().upper()


def _gate_issue(check: Any, gate: str) -> str | None:
    if not isinstance(check, Mapping):
        return f"{gate} check is missing"
    status = _status(check)
    if status != "PASS":
        return f"{gate} is {status or 'missing a PASS/FAIL status'}"
    evidence = str(check.get("evidence") or check.get("observed") or "").strip()
    if len(evidence) < 8:
        return f"{gate} needs concrete observed pixel evidence"
    return None


def _review_checks(review: Any) -> Mapping[str, Any]:
    if not isinstance(review, Mapping):
        return {}
    checks = review.get("checks")
    return checks if isinstance(checks, Mapping) else {}


def _review_failure(
    review: Any,
    *,
    slide: int,
    output_format: str,
) -> tuple[str, str] | None:
    checks = _review_checks(review)
    for index, gate in enumerate(PIXEL_QA_ORDER):
        issue = _gate_issue(checks.get(gate), gate)
        if issue is None:
            continue
        downstream = [
            name
            for name in PIXEL_QA_ORDER[index + 1 :]
            if _status(checks.get(name)) == "PASS"
        ]
        suffix = (
            "; downstream PASS is invalid for " + ", ".join(downstream)
            if downstream
            else ""
        )
        return gate, f"slide {slide} {output_format}: {issue}{suffix}"
    return None


def first_failed_gate(qa: Any) -> tuple[str, str] | None:
    """Return the first missing/failed gate in exact slide/format order."""

    if not isinstance(qa, Mapping):
        return PIXEL_QA_ORDER[0], "pixel QA must contain an object"
    for index, record in enumerate(_records(qa), start=1):
        slide = _slide_number(record, index)
        reviews = record.get("reviews")
        if not isinstance(reviews, Mapping):
            return PIXEL_QA_ORDER[0], f"slide {slide}: per-format reviews are missing"
        for output_format in sorted(str(value) for value in reviews):
            failed = _review_failure(
                reviews[output_format], slide=slide, output_format=output_format
            )
            if failed is not None:
                return failed
    return None


def _inspection_issues(qa: Mapping[str, Any]) -> list[str]:
    inspection = qa.get("inspection")
    if not isinstance(inspection, Mapping):
        return ["inspection metadata is missing"]
    issues: list[str] = []
    if inspection.get("method") != INSPECTION_METHOD:
        issues.append(f"inspection.method must be {INSPECTION_METHOD}")
    if inspection.get("decoded_pixels_observed") is not True:
        issues.append("inspection.decoded_pixels_observed must be true")
    return issues


def _prompt_pack(package_dir: Path) -> Mapping[str, Any]:
    try:
        payload = json.loads((package_dir / "prompt-pack.json").read_text(encoding="utf-8"))
    except (FileNotFoundError, OSError, json.JSONDecodeError):
        return {}
    return payload if isinstance(payload, Mapping) else {}


def _attached_identity_references(package_dir: Path) -> set[str]:
    payload = _prompt_pack(package_dir)
    values = [
        *(payload.get("identity_reference_images") or []),
        *(payload.get("identity_dossier_reference_images") or []),
    ]
    return {str(value) for value in values if str(value).strip()}


def _identity_references_by_subject(package_dir: Path) -> dict[str, set[str]]:
    roles = {
        "Aachu identity anchor": "aachu",
        "Zuv identity anchor": "zuv",
        "together face/scale anchor": "together",
        "together body/posture anchor": "together",
    }
    try:
        payload = json.loads(
            (package_dir / "creative-context.json").read_text(encoding="utf-8")
        )
    except (FileNotFoundError, OSError, json.JSONDecodeError):
        return {}
    selection = payload.get("identity_reference_selection") if isinstance(payload, Mapping) else None
    selected = selection.get("selected_references") if isinstance(selection, Mapping) else None
    if not isinstance(selected, list):
        return {}
    result = {"aachu": set(), "zuv": set(), "together": set()}
    for record in selected:
        if not isinstance(record, Mapping):
            continue
        subject = roles.get(str(record.get("role") or ""))
        path = str(record.get("path") or "").strip()
        if subject and path:
            result[subject].add(path)
    return result


def _attached_style_references(package_dir: Path) -> set[str]:
    payload = _prompt_pack(package_dir)
    return {
        str(value)
        for value in payload.get("style_reference_images") or []
        if str(value).strip()
    }


def _review_contract_issues(
    package_dir: Path,
    review: Any,
    *,
    slide: int,
    output_format: str,
    expected_copy: str,
) -> list[str]:
    failed = _review_failure(review, slide=slide, output_format=output_format)
    if failed is not None:
        return [failed[1]]
    checks = _review_checks(review)
    prefix = f"slide {slide} {output_format}"
    issues: list[str] = []

    identity = checks["identity_wardrobe_accessories"]
    references = identity.get("references") if isinstance(identity, Mapping) else None
    attached = _attached_identity_references(package_dir)
    allowed_by_subject = _identity_references_by_subject(package_dir)
    if not isinstance(references, Mapping):
        issues.append(f"{prefix}: identity check must name its Aachu, Zuv, and together references")
    elif not allowed_by_subject or any(
        not allowed_by_subject.get(subject) for subject in ("aachu", "zuv", "together")
    ):
        issues.append(f"{prefix}: identity role bindings are missing or incomplete")
    else:
        for subject in ("aachu", "zuv", "together"):
            named = references.get(subject)
            if not isinstance(named, list) or not named or any(
                not isinstance(value, str) or not value.strip() for value in named
            ):
                issues.append(f"{prefix}: identity references.{subject} must be a non-empty list")
                continue
            unknown = [value for value in named if value not in attached]
            if unknown:
                issues.append(
                    f"{prefix}: identity references.{subject} contains an unattached reference"
                )
                continue
            named_set = set(named)
            allowed = allowed_by_subject[subject]
            role_mismatch = (
                not named_set.issubset(allowed)
                if subject == "together"
                else named_set != allowed
            )
            if role_mismatch:
                issues.append(
                    f"{prefix}: identity references.{subject} does not match its selected role"
                )

    finish = checks["text_brandmark_style_dimensions"]
    if finish.get("expected_text") != expected_copy:
        issues.append(f"{prefix}: expected_text is stale")
    if finish.get("observed_text") != expected_copy:
        issues.append(f"{prefix}: rendered text is not exact")
    if finish.get("observed_brandmark") != BRANDMARK:
        issues.append(f"{prefix}: exact top-right brandmark is not observed")
    named_style = finish.get("style_references")
    attached_style = _attached_style_references(package_dir)
    if not isinstance(named_style, list) or not named_style or any(
        not isinstance(value, str) or not value.strip() for value in named_style
    ):
        issues.append(f"{prefix}: finish check must name its attached style references")
    elif any(value not in attached_style for value in named_style):
        issues.append(f"{prefix}: finish check contains an unattached style reference")
    return issues


def _normalize_expected_bindings(
    expected: Any,
) -> dict[tuple[int, str], Mapping[str, Any]]:
    if expected is None:
        return {}
    if isinstance(expected, Mapping) and all(
        isinstance(key, tuple) and len(key) == 2 for key in expected
    ):
        return {
            (int(key[0]), str(key[1])): value
            for key, value in expected.items()
            if isinstance(value, Mapping)
        }
    result: dict[tuple[int, str], Mapping[str, Any]] = {}
    for index, record in enumerate(_records(expected), start=1):
        slide = _slide_number(record, index)
        outputs = record.get("native_outputs") or record.get("asset_bindings")
        if isinstance(outputs, Mapping):
            for output_format, binding in outputs.items():
                if isinstance(binding, Mapping):
                    result[(slide, str(output_format))] = binding
    return result


def _nested_forbidden_keys(value: Any, forbidden: set[str]) -> set[str]:
    found: set[str] = set()
    if isinstance(value, Mapping):
        for key, nested in value.items():
            key_text = str(key)
            if key_text in forbidden:
                found.add(key_text)
            found.update(_nested_forbidden_keys(nested, forbidden))
    elif isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        for nested in value:
            found.update(_nested_forbidden_keys(nested, forbidden))
    return found


def _exact_binding_match(
    actual: Mapping[str, Any], expected: Mapping[str, Any]
) -> bool:
    return all(
        actual.get(key) == expected.get(key)
        for key in ("path", "sha256", "width", "height")
    )


def _derived_binding(
    package_dir: Path,
    *,
    slide: int,
    output_format: str,
    source: Mapping[str, Any],
) -> dict[str, Any]:
    raw_path = source.get("path") or source.get("relative_path")
    path, issue = _safe_package_file(package_dir, raw_path)
    if issue or path is None:
        raise ValueError(f"slide {slide} {output_format}: {issue}")
    try:
        with Image.open(path) as image:
            width, height = image.size
            image.verify()
    except (UnidentifiedImageError, OSError, SyntaxError, ValueError) as exc:
        raise ValueError(
            f"slide {slide} {output_format}: current candidate is not a decodable image"
        ) from exc
    binding: dict[str, Any] = {
        "path": str(raw_path).replace("\\", "/"),
        "sha256": _sha256_file(path),
        "width": width,
        "height": height,
    }
    if source.get("input_fingerprint") is not None:
        binding["input_fingerprint"] = source.get("input_fingerprint")
    binding["binding_sha256"] = asset_binding_fingerprint(
        slide, output_format, binding
    )
    return binding


def bind_proof_qa(
    package_dir: Path,
    authored_qa: Any,
    current_candidates: Any,
) -> dict[str, Any]:
    """Attach repo-derived proof byte bindings to Codex-authored observations.

    Codex owns ``inspection`` and ``reviews``. The repo owns paths, hashes,
    dimensions, and binding fingerprints. A caller-supplied binding is accepted
    only when it already equals the derived binding; conflicting inventory is
    rejected instead of silently repaired.
    """

    if not isinstance(authored_qa, Mapping):
        raise ValueError("authored proof QA must contain an object")
    package_dir = Path(package_dir)
    source_bindings = _normalize_expected_bindings(current_candidates)
    if not source_bindings:
        raise ValueError("current proof candidate bindings are missing")
    slides = sorted({slide for slide, _ in source_bindings})
    if len(slides) != 1:
        raise ValueError("proof review must bind exactly one selected slide")
    selected = authored_qa.get("selected_slides")
    if selected is not None and selected != slides:
        raise ValueError("authored proof selected_slides does not match the current candidate")
    records = _records(authored_qa)
    record_map = {
        _slide_number(record, index): record
        for index, record in enumerate(records, start=1)
    }
    if set(record_map) != set(slides):
        raise ValueError("authored proof reviews do not match the current candidate slide")

    payload = copy.deepcopy(dict(authored_qa))
    payload["schema_version"] = PIXEL_QA_SCHEMA_VERSION
    payload["scope"] = "proof"
    payload["selected_slides"] = slides
    bound_records: list[dict[str, Any]] = []
    for slide in slides:
        authored_record = copy.deepcopy(record_map[slide])
        bound: dict[str, Any] = {}
        for (candidate_slide, output_format), source in sorted(source_bindings.items()):
            if candidate_slide != slide:
                continue
            derived = _derived_binding(
                package_dir,
                slide=slide,
                output_format=output_format,
                source=source,
            )
            supplied = (authored_record.get("asset_bindings") or {}).get(output_format)
            if supplied is not None and supplied != derived:
                raise ValueError(
                    f"slide {slide} {output_format}: authored asset binding conflicts with current bytes"
                )
            bound[output_format] = derived
        authored_record["slide"] = slide
        authored_record["asset_bindings"] = bound
        bound_records.append(authored_record)
    payload["slides"] = bound_records
    return payload


def bind_final_qa(authored_qa: Any, manifest: Any) -> dict[str, Any]:
    """Bind Codex-authored final observations to the hidden manifest exactly."""

    if not isinstance(authored_qa, Mapping):
        raise ValueError("authored final QA must contain an object")
    bindings, manifest_issues = _manifest_bindings(manifest)
    if manifest_issues:
        raise ValueError("; ".join(manifest_issues))
    slides = sorted({slide for slide, _ in bindings})
    selected = authored_qa.get("selected_slides")
    if selected is not None and selected != slides:
        raise ValueError("authored final selected_slides does not match the hidden manifest")
    expected_manifest_hash = manifest_fingerprint(manifest)
    supplied_manifest_hash = authored_qa.get("manifest_sha256")
    if supplied_manifest_hash is not None and supplied_manifest_hash != expected_manifest_hash:
        raise ValueError("authored final manifest_sha256 conflicts with the hidden manifest")
    expected_binding_hashes = {
        f"{slide}:{output_format}": asset_binding_fingerprint(slide, output_format, binding)
        for (slide, output_format), binding in sorted(bindings.items())
    }
    supplied_binding_hashes = authored_qa.get("asset_binding_hashes")
    if supplied_binding_hashes is not None and supplied_binding_hashes != expected_binding_hashes:
        raise ValueError("authored final asset_binding_hashes conflict with the hidden manifest")

    payload = copy.deepcopy(dict(authored_qa))
    payload["schema_version"] = PIXEL_QA_SCHEMA_VERSION
    payload["scope"] = "final"
    payload["selected_slides"] = slides
    payload["manifest_sha256"] = expected_manifest_hash
    payload["asset_binding_hashes"] = expected_binding_hashes
    return payload


def _common_schema_issues(
    qa: Any,
    *,
    scope: str,
) -> list[str]:
    if not isinstance(qa, Mapping):
        return ["pixel QA must contain an object"]
    issues: list[str] = []
    if qa.get("schema_version") != PIXEL_QA_SCHEMA_VERSION:
        issues.append(f"schema_version must be {PIXEL_QA_SCHEMA_VERSION}")
    if qa.get("scope") != scope:
        issues.append(f"scope must be {scope}")
    issues.extend(_inspection_issues(qa))
    return issues


def validate_proof_qa(
    package_dir: Path,
    qa: Any,
    *,
    expected_asset_bindings: Any = None,
) -> list[str]:
    """Validate proof observations and their exact quarantine asset bindings."""

    package_dir = Path(package_dir)
    issues = _common_schema_issues(qa, scope="proof")
    if not isinstance(qa, Mapping):
        return issues
    try:
        formats = tuple(locked_formats(package_dir))
        slide_records = _package_slides(package_dir)
    except (FileNotFoundError, OSError, ValueError, json.JSONDecodeError) as exc:
        return issues + [str(exc)]
    copies = {
        _slide_number(record, index): _slide_copy(record)
        for index, record in enumerate(slide_records, start=1)
    }
    selected = qa.get("selected_slides")
    if not isinstance(selected, list) or len(selected) != 1:
        issues.append("proof selected_slides must contain exactly one risky slide")
        selected_numbers: list[int] = []
    else:
        try:
            selected_numbers = [int(selected[0])]
        except (TypeError, ValueError):
            selected_numbers = []
            issues.append("proof selected_slides must contain an integer slide number")
    if selected_numbers and selected_numbers[0] not in copies:
        issues.append("proof selected_slides contains an unknown slide")

    records = _records(qa)
    record_numbers = [_slide_number(record, index) for index, record in enumerate(records, 1)]
    if record_numbers != selected_numbers:
        issues.append("proof slide records must match selected_slides exactly")
    expected_bindings = _normalize_expected_bindings(expected_asset_bindings)
    actual_bindings: dict[tuple[int, str], Mapping[str, Any]] = {}
    for index, record in enumerate(records, start=1):
        slide = _slide_number(record, index)
        bindings = record.get("asset_bindings")
        if not isinstance(bindings, Mapping) or set(bindings) != set(formats):
            issues.append(f"slide {slide}: asset_bindings must match locked formats exactly")
            bindings = {} if not isinstance(bindings, Mapping) else bindings
        reviews = record.get("reviews")
        if not isinstance(reviews, Mapping) or set(reviews) != set(formats):
            issues.append(f"slide {slide}: reviews must match locked formats exactly")
            reviews = {} if not isinstance(reviews, Mapping) else reviews
        for output_format in formats:
            binding = bindings.get(output_format)
            issues.extend(
                _binding_issues(
                    package_dir,
                    slide=slide,
                    output_format=output_format,
                    binding=binding,
                    require_binding_fingerprint=True,
                )
            )
            if isinstance(binding, Mapping):
                actual_bindings[(slide, output_format)] = binding
                proof_match = _PROOF_PATH_RE.fullmatch(str(binding.get("path") or ""))
                if proof_match is None or int(proof_match.group(1)) != slide:
                    issues.append(
                        f"slide {slide} {output_format}: proof path is not the slide-local quarantine candidate"
                    )
                elif not 1 <= int(proof_match.group(2)) <= 2:
                    issues.append(
                        f"slide {slide} {output_format}: the same visual premise exceeds two attempts"
                    )
                expected = expected_bindings.get((slide, output_format))
                if expected is not None and not _exact_binding_match(binding, expected):
                    issues.append(f"slide {slide} {output_format}: proof binding is not the current candidate")
            if output_format in reviews:
                issues.extend(
                    _review_contract_issues(
                        package_dir,
                        reviews[output_format],
                        slide=slide,
                        output_format=output_format,
                        expected_copy=copies.get(slide, ""),
                    )
                )
    if expected_bindings and set(actual_bindings) != set(expected_bindings):
        issues.append("proof asset coverage does not match the current candidate")
    if not issues and str(qa.get("status") or "").upper() != "PASS":
        issues.append("proof QA status must be PASS when every bound review passes")
    return list(dict.fromkeys(issues))


def _manifest_bindings(
    manifest: Any,
) -> tuple[dict[tuple[int, str], Mapping[str, Any]], list[str]]:
    if not isinstance(manifest, Mapping):
        return {}, ["final manifest must contain an object"]
    issues: list[str] = []
    if manifest.get("schema_version") != FINAL_MANIFEST_SCHEMA_VERSION:
        issues.append(f"final manifest schema_version must be {FINAL_MANIFEST_SCHEMA_VERSION}")
    allowed_top = {"schema_version", "selected_formats", "format_sha256", "slides"}
    unexpected_top = sorted(set(manifest) - allowed_top)
    if unexpected_top:
        issues.append(
            "final manifest contains non-inventory fields: " + ", ".join(unexpected_top)
        )
    bindings: dict[tuple[int, str], Mapping[str, Any]] = {}
    for index, record in enumerate(_records(manifest), start=1):
        slide = _slide_number(record, index)
        allowed_slide = {"slide", "input_sha256", "native_outputs"}
        unexpected_slide = sorted(set(record) - allowed_slide)
        if unexpected_slide:
            issues.append(
                f"final manifest slide {slide} contains non-inventory fields: "
                + ", ".join(unexpected_slide)
            )
        if not _HASH_RE.fullmatch(str(record.get("input_sha256") or "")):
            issues.append(f"final manifest slide {slide} input_sha256 is missing or malformed")
        outputs = record.get("native_outputs")
        if not isinstance(outputs, Mapping):
            issues.append(f"final manifest slide {slide} native_outputs is missing")
            continue
        for output_format, binding in outputs.items():
            key = (slide, str(output_format))
            if key in bindings:
                issues.append(f"final manifest repeats {slide}:{output_format}")
            if isinstance(binding, Mapping):
                bindings[key] = binding
                unexpected_binding = sorted(
                    set(binding)
                    - {"path", "sha256", "width", "height", "binding_sha256"}
                )
                if unexpected_binding:
                    issues.append(
                        f"final manifest {slide}:{output_format} contains non-inventory fields: "
                        + ", ".join(unexpected_binding)
                    )
            else:
                issues.append(f"final manifest {slide}:{output_format} binding is malformed")
    return bindings, issues


def validate_final_qa(
    package_dir: Path,
    qa: Any,
    manifest: Any,
) -> list[str]:
    """Validate complete-deck observations against a hidden/final inventory."""

    package_dir = Path(package_dir)
    issues = _common_schema_issues(qa, scope="final")
    if not isinstance(qa, Mapping):
        return issues
    try:
        formats = tuple(locked_formats(package_dir))
        slide_records = _package_slides(package_dir)
    except (FileNotFoundError, OSError, ValueError, json.JSONDecodeError) as exc:
        return issues + [str(exc)]
    copies = {
        _slide_number(record, index): _slide_copy(record)
        for index, record in enumerate(slide_records, start=1)
    }
    expected_keys = {
        (slide, output_format)
        for slide in copies
        for output_format in formats
    }
    bindings, manifest_issues = _manifest_bindings(manifest)
    issues.extend(manifest_issues)
    if isinstance(manifest, Mapping):
        if manifest.get("selected_formats") != list(formats):
            issues.append("final manifest selected_formats does not match the current lock")
        if manifest.get("format_sha256") != locked_format_contract_fingerprint(package_dir):
            issues.append("final manifest format_sha256 is missing or stale")
    if set(bindings) != expected_keys:
        issues.append("final manifest slide/format coverage does not match the locked deck")
    for (slide, output_format), binding in sorted(bindings.items()):
        if (slide, output_format) not in expected_keys:
            issues.append(f"final manifest contains unrequested asset {slide}:{output_format}")
        issues.extend(
            _binding_issues(
                package_dir,
                slide=slide,
                output_format=output_format,
                binding=binding,
                require_binding_fingerprint=True,
            )
        )

    if qa.get("manifest_sha256") != manifest_fingerprint(manifest):
        issues.append("visual QA manifest_sha256 is missing or stale")
    expected_binding_hashes = {
        f"{slide}:{output_format}": asset_binding_fingerprint(slide, output_format, binding)
        for (slide, output_format), binding in sorted(bindings.items())
    }
    declared_binding_hashes = qa.get("asset_binding_hashes")
    if declared_binding_hashes != expected_binding_hashes:
        issues.append("visual QA asset_binding_hashes are missing, incomplete, or stale")

    selected = qa.get("selected_slides")
    if selected != sorted(copies):
        issues.append("final selected_slides must contain the complete deck in order")
    records = _records(qa)
    record_numbers = [_slide_number(record, index) for index, record in enumerate(records, 1)]
    if record_numbers != sorted(copies):
        issues.append("final QA slide records must cover the complete deck exactly once in order")
    for index, record in enumerate(records, start=1):
        slide = _slide_number(record, index)
        forbidden = {"asset_bindings", "native_outputs", "path", "sha256", "width", "height"}
        duplicated = sorted(forbidden & set(record))
        if duplicated:
            issues.append(
                f"slide {slide}: final QA duplicates manifest inventory fields: {', '.join(duplicated)}"
            )
        reviews = record.get("reviews")
        nested_inventory = sorted(
            _nested_forbidden_keys(
                reviews,
                {"asset_bindings", "native_outputs", "path", "sha256", "width", "height"},
            )
        )
        if nested_inventory:
            issues.append(
                f"slide {slide}: final QA reviews duplicate manifest inventory fields: "
                + ", ".join(nested_inventory)
            )
        if not isinstance(reviews, Mapping) or set(reviews) != set(formats):
            issues.append(f"slide {slide}: reviews must match locked formats exactly")
            reviews = {} if not isinstance(reviews, Mapping) else reviews
        for output_format in formats:
            if output_format in reviews:
                issues.extend(
                    _review_contract_issues(
                        package_dir,
                        reviews[output_format],
                        slide=slide,
                        output_format=output_format,
                        expected_copy=copies.get(slide, ""),
                    )
                )
    if not issues and str(qa.get("status") or "").upper() != "PASS":
        issues.append("visual QA status must be PASS when every bound review passes")
    return list(dict.fromkeys(issues))


__all__ = [
    "BRANDMARK",
    "FINAL_MANIFEST_SCHEMA_VERSION",
    "INSPECTION_METHOD",
    "PIXEL_QA_ORDER",
    "PIXEL_QA_SCHEMA_VERSION",
    "asset_binding_fingerprint",
    "bind_final_qa",
    "bind_proof_qa",
    "first_failed_gate",
    "manifest_fingerprint",
    "validate_final_qa",
    "validate_proof_qa",
]
