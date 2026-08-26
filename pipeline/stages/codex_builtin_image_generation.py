"""Codex-first carousel image handoff, quarantine, review, and promotion.

Codex owns image generation and decoded-pixel inspection. This module owns the
deterministic boundary around those calls: compile a prompt, quarantine exact
outputs, bind authored observations to bytes, enforce slide-local attempts,
reuse an approved proof, and promote only a complete audited deck.
"""

from __future__ import annotations

from io import BytesIO
import json
import os
import re
import shutil
from collections.abc import Callable
from pathlib import Path
from typing import Any

from PIL import Image, UnidentifiedImageError

from pipeline.stages.carousel_format_contract import (
    FORMAT_CONTRACT_FILENAME,
    SUPPORTED_NATIVE_FORMATS,
    expected_output_path,
    format_spec,
    locked_formats,
    normalize_requested_formats,
    source_dimensions_are_acceptable,
    write_format_contract,
)
from pipeline.stages.carousel_generation_inputs import (
    build_generation_inputs,
    canonical_fingerprint,
    effective_slide_prompt_fields,
    sha256_binding,
)
from pipeline.stages.carousel_generation_state import (
    STATE_SCHEMA_VERSION,
    GenerationStatus,
    initialize_generation_state,
    read_generation_state,
    write_v3_state,
)
from pipeline.stages.carousel_prompt_compiler import compile_image_prompt, extract_scene_summary
from pipeline.stages.carousel_visual_storytelling import physical_action_issue


MAX_SEMANTIC_ATTEMPTS = 2
STATE_FILE = "generation-state.json"
QUARANTINE_FOLDER = ".internal/visual-quarantine"
APPROVED_CANDIDATE_FOLDER = ".internal/approved-final-candidates"
PROMOTION_STAGING_FOLDER = ".internal/promotion-staging"
FINAL_AUDIT_CANDIDATE_FOLDER = ".internal/final-audit-candidate"
FINAL_MANIFEST_CANDIDATE = ".internal/final-manifest-candidate.json"
PROMPT_HANDOFF_ACTIVE_FOLDER = ".internal/compiled-prompts"
ATTEMPT_LEDGER = STATE_FILE
FULL_DECK_ATTEMPT_LEDGER = STATE_FILE
PASS = "PASS"


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    staging = path.with_name(path.name + ".tmp")
    staging.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    staging.replace(path)


def load_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"{path.name} must contain a JSON object.")
    return payload


def sha256_bytes(payload: bytes) -> str:
    return sha256_binding(payload).removeprefix("sha256:")


def _canonical_hash(value: Any) -> str:
    return canonical_fingerprint(value)


def remove_path_without_following(path: Path, *, package_root: Path) -> None:
    """Remove one package artifact without traversing a package-local symlink.

    A final symlink is safe to unlink.  A symlink in a parent component is not:
    passing it to ``rmtree`` would delete the resolved external directory.  We
    derive the relative path from the caller spelling (so macOS ``/var`` and
    ``/tmp`` aliases remain valid) and then walk only components below the
    resolved package root.
    """

    supplied_root = Path(os.path.abspath(Path(package_root).expanduser()))
    root = Path(package_root).expanduser().resolve(strict=True)
    supplied_path = Path(path).expanduser()
    if not supplied_path.is_absolute():
        supplied_path = supplied_root / supplied_path
    supplied_path = Path(os.path.abspath(supplied_path))
    try:
        relative = supplied_path.relative_to(supplied_root)
    except ValueError:
        try:
            relative = supplied_path.relative_to(root)
        except ValueError as exc:
            raise ValueError("Refusing to remove a path outside the carousel package.") from exc
    target = root / relative
    cursor = root
    for part in relative.parts[:-1]:
        cursor /= part
        if cursor.is_symlink():
            raise ValueError("Refusing to remove through a symlinked package directory.")
    if target.is_symlink() or target.is_file():
        target.unlink()
    elif target.exists():
        shutil.rmtree(target)


def package_relative_path(carousel_dir: Path, path: Path) -> str:
    root = Path(carousel_dir).resolve(strict=True)
    resolved = resolve_package_artifact_path(
        carousel_dir,
        path,
        "",
        require_file=True,
    )
    return resolved.relative_to(root).as_posix()


def resolve_package_artifact_path(
    carousel_dir: Path,
    raw_path: str | Path | None,
    default: str,
    *,
    require_file: bool = False,
) -> Path:
    package_path = Path(carousel_dir).expanduser()
    if package_path.is_symlink():
        raise ValueError("Carousel package path cannot itself be a symlink.")
    supplied_root = Path(os.path.abspath(package_path))
    root = package_path.resolve(strict=True)
    candidate = Path(raw_path or default).expanduser()
    if not candidate.is_absolute():
        candidate = supplied_root / candidate
    candidate = Path(os.path.abspath(candidate))
    try:
        relative = candidate.relative_to(supplied_root)
    except ValueError:
        try:
            relative = candidate.resolve(strict=require_file).relative_to(root)
        except (FileNotFoundError, OSError, ValueError) as exc:
            raise ValueError("Package artifact escaped the carousel directory.") from exc
    candidate = root / relative
    cursor = root
    for part in relative.parts:
        cursor = cursor / part
        if cursor.is_symlink():
            raise ValueError("Package artifacts cannot contain symlink path components.")
    resolved = candidate.resolve(strict=require_file)
    try:
        resolved.relative_to(root)
    except ValueError as exc:
        raise ValueError("Package artifact escaped the carousel directory.") from exc
    if require_file and not resolved.is_file():
        raise ValueError(f"Package artifact is not a regular file: {raw_path or default}")
    return resolved


def _slides(carousel_dir: Path) -> list[dict[str, Any]]:
    payload = json.loads((carousel_dir / "slides.json").read_text(encoding="utf-8"))
    if not isinstance(payload, list) or not payload:
        raise ValueError("slides.json must contain at least one slide.")
    records = [item for item in payload if isinstance(item, dict)]
    numbers = [int(item.get("slide", 0) or 0) for item in records]
    if numbers != list(range(1, len(records) + 1)):
        raise ValueError("slides.json slide numbers must be unique and sequential from 1.")
    return records


def _prompt_pack(carousel_dir: Path) -> dict[str, Any]:
    return load_json(carousel_dir / "prompt-pack.json")


def _prompt_slides(carousel_dir: Path) -> list[dict[str, Any]]:
    prompts = _prompt_pack(carousel_dir).get("slides")
    if not isinstance(prompts, list) or not prompts:
        raise ValueError("prompt-pack.json must contain slide prompts.")
    return [item for item in prompts if isinstance(item, dict)]


REQUIRED_IDENTITY_REFERENCE_ROLES = (
    "Aachu identity anchor",
    "Zuv identity anchor",
    "together face/scale anchor",
    "together body/posture anchor",
)
REQUIRED_IDENTITY_REFERENCE_COUNT = len(REQUIRED_IDENTITY_REFERENCE_ROLES)
REQUIRED_STYLE_REFERENCE_COUNT = 1


def _canonical_package_reference_paths(
    package_dir: Path,
    values: Any,
    *,
    label: str,
) -> list[str]:
    if not isinstance(values, list):
        raise ValueError(f"{label} must be a list of package-local paths.")
    result: list[str] = []
    for value in values:
        path = resolve_package_artifact_path(
            package_dir,
            str(value),
            "",
            require_file=True,
        )
        result.append(package_relative_path(package_dir, path))
    return result


def _package_reference_bindings(carousel_dir: Path) -> list[dict[str, Any]]:
    prompt_pack = _prompt_pack(carousel_dir)
    raw: list[tuple[str, str]] = []
    for key, role in (
        ("identity_reference_images", "identity"),
        ("identity_dossier_reference_images", "identity"),
        ("style_reference_images", "style"),
    ):
        raw.extend((str(value), role) for value in prompt_pack.get(key, []))
    for slide in _slides(carousel_dir):
        raw.extend((str(value), "story") for value in slide.get("source_images", []))
    by_path: dict[str, dict[str, Any]] = {}
    for value, role in raw:
        path = resolve_package_artifact_path(carousel_dir, value, "", require_file=True)
        relative = package_relative_path(carousel_dir, path)
        record = by_path.setdefault(
            relative,
            {"path": relative, "sha256": sha256_binding(path.read_bytes()), "roles": []},
        )
        if role not in record["roles"]:
            record["roles"].append(role)
    return [by_path[key] for key in sorted(by_path)]


def generator_prompt_text(slide_prompt: dict[str, Any], output_format: str) -> str:
    return compile_image_prompt(
        slide_number=int(slide_prompt["slide"]),
        slide_count=int(slide_prompt.get("slide_count") or 1),
        slide_copy=str(slide_prompt["text"]),
        visual=str(
            slide_prompt.get("scene")
            or extract_scene_summary(str(slide_prompt.get("prompt") or ""))
        ),
        format_key=output_format,
        style=str(slide_prompt.get("style") or "warm ivory paper, watercolor and loose ink"),
        negative=str(slide_prompt.get("negative_prompt") or ""),
        pose=slide_prompt.get("pose"),
        wardrobe=slide_prompt.get("wardrobe"),
        props=slide_prompt.get("props"),
        background=slide_prompt.get("background"),
        emotion=slide_prompt.get("emotion"),
    )


def prompt_handoff_relative_path(output_format: str, slide_number: int, kind: str = "generator") -> str:
    if kind != "generator":
        raise ValueError("Redundant Markdown handoffs were removed; use the compiled prompt.")
    folder = str(format_spec(output_format)["prompt_folder"])
    return f"{PROMPT_HANDOFF_ACTIVE_FOLDER}/{folder}/slide-{slide_number:02d}.prompt.txt"


def _current_compiled_prompt(carousel_dir: Path, number: int, output_format: str) -> str:
    slides = _slides(carousel_dir)
    prompts = {int(item["slide"]): item for item in _prompt_slides(carousel_dir)}
    prompt_pack = _prompt_pack(carousel_dir)
    slide = {int(item["slide"]): item for item in slides}[number]
    effective = effective_slide_prompt_fields(
        slide,
        prompts[number],
        shared_negative=str(prompt_pack.get("negative_prompt") or ""),
    )
    source = {
        **prompts[number],
        "text": str(slide.get("copy") or ""),
        "slide_count": len(slides),
        "style": str(prompt_pack.get("style_prompt") or "warm ivory paper, watercolor and loose ink"),
        "scene": effective["scene"],
        "negative_prompt": effective["negative_prompt"],
        "pose": effective["pose"],
        "wardrobe": effective["wardrobe"],
        "props": effective["props"],
        "background": effective["background"],
        "emotion": effective["emotion"],
    }
    return generator_prompt_text(source, output_format)


def build_compiled_prompt_handoff(
    carousel_dir: Path,
    *,
    slide_numbers: list[int],
    output_formats: list[str] | tuple[str, ...],
    **_: Any,
) -> dict[str, Any]:
    files: list[dict[str, Any]] = []
    for number in slide_numbers:
        for output_format in output_formats:
            relative = prompt_handoff_relative_path(output_format, number)
            path = carousel_dir / relative
            if not path.is_file() or path.is_symlink():
                raise ValueError(f"Missing compiled generator prompt: {path}")
            files.append(
                {
                    "slide": number,
                    "format": output_format,
                    "path": relative,
                    "sha256": sha256_binding(path.read_bytes()),
                }
            )
    references = _package_reference_bindings(carousel_dir)
    generation_references = [
        binding
        for binding in references
        if set(binding.get("roles") or []).intersection({"identity", "style"})
    ]
    context_references = [
        binding
        for binding in references
        if "story" in set(binding.get("roles") or [])
    ]
    payload = {
        "schema_version": "compiled-prompts/v3",
        "slides": list(slide_numbers),
        "formats": list(output_formats),
        "files": files,
        # Only these five files are image-generation attachments. Story images
        # are creator/model context used to author the locked slide fields; the
        # observed built-in boundary does not permit silently appending them.
        "reference_bindings": generation_references,
        "context_reference_bindings": context_references,
    }
    return {**payload, "fingerprint": canonical_fingerprint(payload)}


def compiled_prompt_handoff_integrity_issues(
    carousel_dir: Path,
    *,
    state: dict[str, Any] | None = None,
    **_: Any,
) -> list[str]:
    state = state or read_generation_state(carousel_dir)
    if state.get("schema_version") != STATE_SCHEMA_VERSION:
        return ["archived v2 packages are read-only"]
    issues: list[str] = []
    for number in state.get("selected_slides") or []:
        for output_format in state.get("selected_formats") or []:
            path = carousel_dir / prompt_handoff_relative_path(output_format, int(number))
            if not path.is_file() or path.is_symlink():
                issues.append(f"slide {number} {output_format} compiled prompt is missing")
                continue
            expected = _current_compiled_prompt(carousel_dir, int(number), output_format)
            if path.read_text(encoding="utf-8") != expected:
                issues.append(f"slide {number} {output_format} compiled prompt is stale")
    return issues


def visual_plan_quality_gate_reason(carousel_dir: Path) -> str | None:
    for slide in _slides(carousel_dir):
        if not str(slide.get("copy") or "").strip():
            return f"Slide {slide.get('slide')} is missing exact copy."
        action = str(slide.get("physical_action") or slide.get("visual") or "").strip()
        issue = physical_action_issue(action, copy=slide.get("copy"))
        if slide.get("needs_physical_action") is True or issue:
            return f"Slide {slide.get('slide')} {issue or 'needs a concrete physical action'}."
    return None


def identity_consistency_gate_reason(carousel_dir: Path) -> str | None:
    try:
        prompt_pack = _prompt_pack(carousel_dir)
        identity_values = [
            *(prompt_pack.get("identity_reference_images") or []),
            *(prompt_pack.get("identity_dossier_reference_images") or []),
        ]
        identity_paths = _canonical_package_reference_paths(
            carousel_dir,
            identity_values,
            label="identity references",
        )
        style_paths = _canonical_package_reference_paths(
            carousel_dir,
            prompt_pack.get("style_reference_images") or [],
            label="style references",
        )
        context = load_json(carousel_dir / "creative-context.json")
        selection = context.get("identity_reference_selection")
        selected = selection.get("selected_references") if isinstance(selection, dict) else None
        if not isinstance(selected, list):
            return "Four curated identity roles must be bound in creative-context.json."
        selected_paths: list[str] = []
        selected_roles: list[str] = []
        for record in selected:
            if not isinstance(record, dict):
                return "Each curated identity reference must bind one role and package-local path."
            selected_roles.append(str(record.get("role") or "").strip())
            selected_paths.extend(
                _canonical_package_reference_paths(
                    carousel_dir,
                    [record.get("path")],
                    label="curated identity references",
                )
            )
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        return str(exc)
    if len(identity_paths) != REQUIRED_IDENTITY_REFERENCE_COUNT:
        return (
            "Exactly four curated identity references are required "
            f"(found {len(identity_paths)})."
        )
    if len(set(identity_paths)) != REQUIRED_IDENTITY_REFERENCE_COUNT:
        return "The four curated identity references must be four distinct attachments."
    if len(style_paths) != REQUIRED_STYLE_REFERENCE_COUNT:
        return f"Exactly one style board is required (found {len(style_paths)})."
    if len(set(style_paths)) != REQUIRED_STYLE_REFERENCE_COUNT:
        return "The style board attachment must be distinct."
    if set(identity_paths).intersection(style_paths):
        return "Identity references and the style board must be distinct attachments."
    if len(selected_paths) != REQUIRED_IDENTITY_REFERENCE_COUNT or set(selected_paths) != set(
        identity_paths
    ):
        return "The four prompt-pack identity attachments must match the curated identity selection."
    if len(selected_roles) != REQUIRED_IDENTITY_REFERENCE_COUNT or set(selected_roles) != set(
        REQUIRED_IDENTITY_REFERENCE_ROLES
    ):
        return (
            "Exactly the Aachu, Zuv, together face/scale, and together body/posture "
            "identity roles are required."
        )
    return None


def pre_generation_review_gate_reason(carousel_dir: Path) -> str | None:
    return visual_plan_quality_gate_reason(carousel_dir) or identity_consistency_gate_reason(carousel_dir)


def infer_slide_count(carousel_dir: Path) -> int:
    return len(_slides(carousel_dir))


def proof_slide_from_gate(proof_gate: str | None, slides: list[dict[str, Any]]) -> int:
    if proof_gate:
        match = re.search(r"\bslide\s*(\d+)\b", str(proof_gate), flags=re.IGNORECASE)
        if match and any(int(slide["slide"]) == int(match.group(1)) for slide in slides):
            return int(match.group(1))
    return int(
        max(slides, key=lambda item: len(str(item.get("scene") or item.get("prompt") or "").split()))[
            "slide"
        ]
    )


def _candidate_record_path(carousel_dir: Path, slide: int, attempt: int) -> Path:
    return carousel_dir / QUARANTINE_FOLDER / f"slide-{slide:02d}" / f"attempt-{attempt:02d}" / "candidate.json"


def _approved_record_path(carousel_dir: Path, slide: int) -> Path:
    return carousel_dir / APPROVED_CANDIDATE_FOLDER / f"slide-{slide:02d}" / "candidate.json"


def _load_record(path: Path) -> dict[str, Any] | None:
    if not path.is_file() or path.is_symlink():
        return None
    try:
        return load_json(path)
    except (OSError, ValueError, json.JSONDecodeError):
        return None


def _current_candidate(carousel_dir: Path, state: dict[str, Any], slide: int) -> dict[str, Any] | None:
    record = state["slides"].get(str(slide), {})
    attempt = int(record.get("attempts", 0) or 0)
    return _load_record(_candidate_record_path(carousel_dir, slide, attempt)) if attempt else None


def _approved_candidate(carousel_dir: Path, slide: int) -> dict[str, Any] | None:
    return _load_record(_approved_record_path(carousel_dir, slide))


def _binding_issues(carousel_dir: Path, candidate: dict[str, Any]) -> list[str]:
    issues: list[str] = []
    outputs = candidate.get("native_outputs")
    if not isinstance(outputs, dict):
        return ["candidate native_outputs are missing"]
    for output_format, binding in outputs.items():
        if not isinstance(binding, dict):
            issues.append(f"{output_format} binding is malformed")
            continue
        try:
            path = resolve_package_artifact_path(
                carousel_dir, binding.get("path"), "", require_file=True
            )
        except ValueError as exc:
            issues.append(str(exc))
            continue
        payload = path.read_bytes()
        try:
            dimensions = image_dimensions(payload)
        except ValueError as exc:
            issues.append(str(exc))
            continue
        if binding.get("sha256") != sha256_binding(payload):
            issues.append(f"{output_format} candidate hash is stale")
        if (binding.get("width"), binding.get("height")) != (
            dimensions["width"], dimensions["height"]
        ):
            issues.append(f"{output_format} candidate dimensions are stale")
        expected = target_size_for_format(output_format)
        if (dimensions["width"], dimensions["height"]) != expected:
            issues.append(f"{output_format} candidate is not native size")
        if binding.get("binding_sha256") != _asset_binding_fingerprint(
            int(candidate.get("slide") or 0),
            output_format,
            binding,
        ):
            issues.append(f"{output_format} candidate asset binding is stale")

    if candidate.get("schema_version") == "carousel-candidate/v1":
        evidence = candidate.get("source_evidence")
        if not isinstance(evidence, dict):
            issues.append("candidate source_evidence is missing")
            return issues
        if set(evidence) != set(outputs):
            issues.append("candidate source_evidence formats do not match native outputs")
        for output_format, output_binding in outputs.items():
            if not isinstance(output_binding, dict):
                continue
            raw_binding = evidence.get(output_format)
            if not isinstance(raw_binding, dict):
                issues.append(f"{output_format} source evidence is malformed")
                continue
            try:
                raw_path = resolve_package_artifact_path(
                    carousel_dir,
                    raw_binding.get("path"),
                    "",
                    require_file=True,
                )
            except ValueError as exc:
                issues.append(f"{output_format} source evidence: {exc}")
                continue
            raw_payload = raw_path.read_bytes()
            if raw_binding.get("sha256") != sha256_binding(raw_payload):
                issues.append(f"{output_format} raw source hash is stale")
            try:
                raw_dimensions = decoded_png_dimensions(raw_payload)
            except ValueError as exc:
                issues.append(f"{output_format} raw source is invalid: {exc}")
                continue
            if (raw_binding.get("width"), raw_binding.get("height")) != (
                raw_dimensions["width"],
                raw_dimensions["height"],
            ):
                issues.append(f"{output_format} raw source dimensions are stale")
            if raw_binding.get("accepted") is not True or not source_dimensions_are_acceptable(
                output_format,
                raw_dimensions["width"],
                raw_dimensions["height"],
            ):
                issues.append(f"{output_format} raw source violates the accepted size/aspect contract")
                continue
            try:
                normalized, normalized_dimensions, mode, _ = _normalize_source_for_format(
                    raw_payload,
                    output_format,
                )
            except ValueError as exc:
                issues.append(f"{output_format} raw source cannot be deterministically normalized: {exc}")
                continue
            if raw_binding.get("normalization") != mode:
                issues.append(f"{output_format} raw source normalization mode is stale")
            if output_binding.get("sha256") != sha256_binding(normalized):
                issues.append(
                    f"{output_format} native output does not match deterministic raw-source normalization"
                )
            if (output_binding.get("width"), output_binding.get("height")) != (
                normalized_dimensions["width"],
                normalized_dimensions["height"],
            ):
                issues.append(
                    f"{output_format} native output dimensions do not match raw-source normalization"
                )
    return issues


def _candidate_is_usable(
    carousel_dir: Path,
    state: dict[str, Any],
    candidate: dict[str, Any] | None,
) -> bool:
    if candidate is None or candidate.get("ingest_issues"):
        return False
    number = str(candidate.get("slide") or "")
    return bool(
        number in state.get("slides", {})
        and candidate.get("input_sha256")
        == state["slides"][number].get("input_sha256")
        and not _binding_issues(carousel_dir, candidate)
    )


def _proof_qa_validation_issues(
    carousel_dir: Path,
    qa: dict[str, Any],
    candidate: dict[str, Any],
) -> list[str]:
    try:
        from pipeline.stages.carousel_pixel_qa import validate_proof_qa

        return validate_proof_qa(
            carousel_dir,
            qa,
            expected_asset_bindings=[candidate],
        )
    except ImportError:
        return ["carousel pixel QA validator is unavailable"]


def current_proof_qa_issues(
    carousel_dir: Path,
    qa: dict[str, Any],
    *,
    state: dict[str, Any] | None = None,
) -> list[str]:
    """Validate proof QA against the exact current candidate record and bytes."""

    current_state = state or read_generation_state(carousel_dir)
    number = current_state.get("proof_slide")
    if number is None:
        return ["proof slide is not selected"]
    candidate = _current_candidate(carousel_dir, current_state, int(number))
    if candidate is None:
        return ["current proof candidate is missing"]
    if (
        int(candidate.get("slide") or 0) != int(number)
        or candidate.get("input_sha256")
        != current_state.get("slides", {}).get(str(number), {}).get("input_sha256")
    ):
        return ["current proof candidate record is stale or belongs to another slide"]
    binding_issues = _binding_issues(carousel_dir, candidate)
    if binding_issues:
        return binding_issues
    return _proof_qa_validation_issues(carousel_dir, qa, candidate)


def _proof_approved(carousel_dir: Path, state: dict[str, Any]) -> bool:
    number = state.get("proof_slide")
    if number is None:
        return False
    qa_path = carousel_dir / "proof-qa.json"
    current_candidate = _current_candidate(carousel_dir, state, int(number))
    approved_candidate = _approved_candidate(carousel_dir, int(number))
    if not qa_path.is_file() or current_candidate is None or approved_candidate is None:
        return False
    qa = _load_record(qa_path) or {}
    approval = qa.get("creator_approval")
    current_asset_bindings = {
        f"{int(number)}:{output_format}": binding.get("binding_sha256")
        for output_format, binding in sorted(
            (current_candidate.get("native_outputs") or {}).items()
        )
        if isinstance(binding, dict)
    }
    current_pixels = {
        output_format: {
            key: binding.get(key)
            for key in ("sha256", "width", "height")
        }
        for output_format, binding in sorted(
            (current_candidate.get("native_outputs") or {}).items()
        )
        if isinstance(binding, dict)
    }
    approved_pixels = {
        output_format: {
            key: binding.get(key)
            for key in ("sha256", "width", "height")
        }
        for output_format, binding in sorted(
            (approved_candidate.get("native_outputs") or {}).items()
        )
        if isinstance(binding, dict)
    }
    return bool(
        isinstance(approval, dict)
        and approval.get("approved") is True
        and str(approval.get("status") or "").upper() == "APPROVED"
        and approval.get("proof_input_sha256")
        == state["slides"][str(number)].get("input_sha256")
        and int(current_candidate.get("slide") or 0) == int(number)
        and int(approved_candidate.get("slide") or 0) == int(number)
        and current_candidate.get("input_sha256")
        == state["slides"][str(number)].get("input_sha256")
        and approved_candidate.get("input_sha256")
        == state["slides"][str(number)].get("input_sha256")
        and approval.get("proof_binding_sha256")
        == image_set_sha256([current_candidate])
        and approval.get("proof_qa_sha256")
        == canonical_fingerprint(_qa_without_approval(qa))
        and approval.get("asset_binding_hashes") == current_asset_bindings
        and approved_pixels == current_pixels
        and not _proof_qa_validation_issues(carousel_dir, qa, current_candidate)
        and not _binding_issues(carousel_dir, current_candidate)
        and not _binding_issues(carousel_dir, approved_candidate)
    )


def _approval_is_claimed(carousel_dir: Path, state: dict[str, Any]) -> bool:
    number = state.get("proof_slide")
    if number is None:
        return False
    qa = _load_record(carousel_dir / "proof-qa.json") or {}
    approval = qa.get("creator_approval")
    return bool(
        (
            isinstance(approval, dict)
            and approval.get("approved") is True
        )
        or state.get("slides", {}).get(str(number), {}).get("status")
        == "approved_candidate"
        or state.get("status") in {"batch_ready", "publish_ready"}
    )


def _revoke_stale_proof_approval(
    carousel_dir: Path,
    state: dict[str, Any],
) -> dict[str, Any]:
    number = int(state["proof_slide"])
    qa_path = carousel_dir / "proof-qa.json"
    qa = _load_record(qa_path)
    if qa is not None and "creator_approval" in qa:
        qa.pop("creator_approval", None)
        write_json(qa_path, qa)
    remove_path_without_following(
        carousel_dir / APPROVED_CANDIDATE_FOLDER / f"slide-{number:02d}",
        package_root=carousel_dir,
    )
    _retract_public_finals(carousel_dir)

    current = _current_candidate(carousel_dir, state, number)
    reusable = _candidate_is_usable(carousel_dir, state, current)
    attempts = int(state["slides"][str(number)].get("attempts", 0) or 0)
    state["slides"][str(number)]["status"] = "qa_required" if reusable else "failed"
    return write_v3_state(
        carousel_dir,
        {
            **state,
            "status": "proof_qa_required" if reusable else "proof_failed",
            "next_action": (
                "review_proof_pixels"
                if reusable
                else (
                    "repair_visual_premise"
                    if attempts >= MAX_SEMANTIC_ATTEMPTS
                    else "retry_selected_slides"
                )
            ),
            "selected_slides": [number],
            "reason": (
                "Creator proof approval bindings are stale; proof QA and approval must be renewed."
            ),
        },
    )


def _delete_slide_work(carousel_dir: Path, number: int) -> None:
    remove_path_without_following(
        carousel_dir / QUARANTINE_FOLDER / f"slide-{number:02d}",
        package_root=carousel_dir,
    )
    remove_path_without_following(
        carousel_dir / APPROVED_CANDIDATE_FOLDER / f"slide-{number:02d}",
        package_root=carousel_dir,
    )
    for output_format in SUPPORTED_NATIVE_FORMATS:
        remove_path_without_following(
            carousel_dir / prompt_handoff_relative_path(output_format, number),
            package_root=carousel_dir,
        )


def _retract_public_finals(carousel_dir: Path) -> None:
    for output_format in SUPPORTED_NATIVE_FORMATS:
        remove_path_without_following(
            carousel_dir / str(format_spec(output_format)["folder"]),
            package_root=carousel_dir,
        )
    for filename in ("final-images.json", "visual-qa.json", "final-audit.json"):
        remove_path_without_following(carousel_dir / filename, package_root=carousel_dir)
    remove_path_without_following(
        carousel_dir / FINAL_MANIFEST_CANDIDATE,
        package_root=carousel_dir,
    )


def reconcile_package_state(package_dir: Path) -> dict[str, Any]:
    """Apply semantic invalidation to a writable v3 package."""

    package_dir = Path(package_dir).expanduser()
    state = read_generation_state(package_dir)
    if not state:
        return initialize_generation_state(package_dir)
    if state.get("schema_version") != STATE_SCHEMA_VERSION:
        # Archived state stays inspectable but is never migrated implicitly.
        return state
    try:
        inputs = build_generation_inputs(package_dir)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        _retract_public_finals(package_dir)
        return write_v3_state(
            package_dir,
            {**state, "status": "blocked", "next_action": "repair_inputs", "reason": str(exc)},
        )

    old_slides = state.get("slides") or {}
    current_slides = inputs["slides"]
    numbers_changed = set(old_slides) != set(current_slides)
    format_changed = state.get("format_sha256") != inputs["format_sha256"]
    fingerprint_keys = (
        "source_sha256",
        "prompt_sha256",
        "references_sha256",
        "input_sha256",
    )
    changed = {
        number
        for number in set(old_slides).intersection(current_slides)
        if any(
            old_slides[number].get(key) != current_slides[number][key]
            for key in fingerprint_keys
        )
    }
    component_equal_but_input_changed = any(
        all(
            old_slides[number].get(key) == current_slides[number][key]
            for key in ("source_sha256", "prompt_sha256", "references_sha256")
        )
        for number in changed
    )
    every_prompt_changed = bool(current_slides) and all(
        old_slides.get(number, {}).get("prompt_sha256") != record["prompt_sha256"]
        for number, record in current_slides.items()
    )
    every_reference_changed = bool(current_slides) and all(
        old_slides.get(number, {}).get("references_sha256")
        != record["references_sha256"]
        for number, record in current_slides.items()
    )
    global_change = bool(
        numbers_changed
        or format_changed
        or component_equal_but_input_changed
        or every_prompt_changed
        or every_reference_changed
    )
    invalid = set(current_slides) if global_change else changed

    if not invalid and state.get("status") == "awaiting_creator_proof_approval":
        proof_qa = _load_record(package_dir / "proof-qa.json") or {}
        proof_issues = current_proof_qa_issues(
            package_dir,
            proof_qa,
            state=state,
        )
        if proof_issues:
            number = int(state["proof_slide"])
            state["slides"][str(number)]["status"] = "qa_required"
            return write_v3_state(
                package_dir,
                {
                    **state,
                    "status": "proof_qa_required",
                    "next_action": "repair_proof_qa",
                    "selected_slides": [number],
                    "reason": "; ".join(proof_issues),
                },
            )

    if (
        not invalid
        and _approval_is_claimed(package_dir, state)
        and not _proof_approved(package_dir, state)
    ):
        return _revoke_stale_proof_approval(package_dir, state)

    # Final pixels are another input to the publish claim. Tampering revokes it
    # even when creative inputs are unchanged.
    if not invalid and state.get("status") == GenerationStatus.PUBLISH_READY.value:
        manifest = _load_record(package_dir / "final-images.json")
        stored_audit = _load_record(package_dir / "final-audit.json")
        try:
            from pipeline.stages.carousel_quality import build_final_audit

            current_audit = build_final_audit(package_dir, write=False)
        except (OSError, ValueError, json.JSONDecodeError) as exc:
            current_audit = {"status": "FAIL", "issues": [str(exc)]}
        approved_candidates = {
            int(number): _approved_candidate(package_dir, int(number))
            for number in state.get("slides", {})
        }
        complete_approved = all(
            candidate is not None for candidate in approved_candidates.values()
        )
        approved_binding_stale = any(
            _binding_issues(package_dir, candidate)
            for candidate in approved_candidates.values()
            if candidate is not None
        )
        manifest_binding_stale = bool(
            manifest is not None
            and any(
                _binding_issues(package_dir, record)
                for record in (manifest.get("slides") or [])
                if isinstance(record, dict)
            )
        )
        expected_manifest = (
            _prospective_manifest(
                package_dir,
                {
                    number: candidate
                    for number, candidate in approved_candidates.items()
                    if candidate is not None
                },
                state=state,
            )
            if complete_approved
            else None
        )
        manifest_is_exact = manifest is not None and manifest == expected_manifest
        audit_stale = stored_audit is None or current_audit.get("status") != PASS
        if not manifest_is_exact or not complete_approved or approved_binding_stale or manifest_binding_stale:
            _retract_public_finals(package_dir)
            return write_v3_state(
                package_dir,
                {
                    **state,
                    "status": "final_qa_failed",
                    "next_action": "restore_or_regenerate_tampered_final",
                    "reason": "Published final evidence no longer matches its bound audit: "
                    + "; ".join(
                        current_audit.get("issues")
                        or ["final pixels, manifest, QA, or audit binding is stale"]
                    ),
                },
            )
        if audit_stale:
            # The normalized approved candidates and exact public manifest are
            # still trustworthy.  Retract only the public claim, preserve every
            # candidate/attempt, and rebuild the hidden review inventory so a
            # corrected QA can be bound without another generation call.
            _retract_public_finals(package_dir)
            for record in state["slides"].values():
                record["status"] = "approved_candidate"
            repaired = write_v3_state(
                package_dir,
                {
                    **state,
                    "status": "final_qa_required",
                    "next_action": "repair_final_qa",
                    "selected_slides": sorted(int(value) for value in state["slides"]),
                    "reason": "Published final QA or audit binding is stale; approved pixels were preserved: "
                    + "; ".join(
                        current_audit.get("issues")
                        or ["stored final audit is missing"]
                    ),
                },
            )
            _write_manifest_candidate_if_complete(package_dir, repaired)
            return repaired
        return state
    if not invalid:
        return state

    _retract_public_finals(package_dir)
    prior_status = str(state.get("status") or "draft")
    selected = {int(value) for value in state.get("selected_slides") or []}
    invalid_numbers = {int(value) for value in invalid}
    proof_slide = state.get("proof_slide")
    proof_invalid = proof_slide is not None and int(proof_slide) in invalid_numbers
    for number in invalid_numbers:
        _delete_slide_work(package_dir, number)
    if global_change or proof_invalid:
        remove_path_without_following(
            package_dir / "proof-qa.json", package_root=package_dir
        )
    if global_change:
        remove_path_without_following(
            package_dir / APPROVED_CANDIDATE_FOLDER, package_root=package_dir
        )
        remove_path_without_following(
            package_dir / QUARANTINE_FOLDER, package_root=package_dir
        )
        remove_path_without_following(
            package_dir / PROMPT_HANDOFF_ACTIVE_FOLDER, package_root=package_dir
        )

    next_slide_state: dict[str, Any] = {}
    for number, fingerprints in current_slides.items():
        previous = old_slides.get(number, {})
        next_slide_state[number] = {
            "status": "draft" if number in invalid else previous.get("status", "draft"),
            "attempts": 0 if number in invalid else int(previous.get("attempts", 0) or 0),
            **fingerprints,
        }
    selected_survives = bool(selected) and not selected.intersection(invalid_numbers)
    proof_still_approved = _proof_approved(
        package_dir,
        {**state, "slides": next_slide_state},
    )
    if selected_survives and prior_status in {
        "handoff_ready",
        "proof_qa_required",
        "final_qa_required",
    }:
        status = prior_status
        next_action = str(state.get("next_action") or "continue_current_slide")
        selected_slides = sorted(selected)
    elif proof_still_approved:
        status = "batch_ready"
        next_action = "prepare_remaining_slides"
        selected_slides = []
    else:
        status = "draft"
        next_action = "prepare_riskiest_proof"
        selected_slides = []
    reason = (
        "Shared generation inputs changed; all slide candidates were invalidated."
        if global_change
        else "Changed slide inputs invalidated only slides: "
        + ", ".join(str(value) for value in sorted(invalid_numbers))
    )
    return write_v3_state(
        package_dir,
        {
            "status": status,
            "next_action": next_action,
            "proof_slide": proof_slide,
            "selected_slides": selected_slides,
            "selected_formats": inputs["selected_formats"],
            "format_sha256": inputs["format_sha256"],
            "slides": next_slide_state,
            "reason": reason,
        },
    )


def _require_v3(package_dir: Path) -> dict[str, Any]:
    state = reconcile_package_state(package_dir)
    if state.get("schema_version") != STATE_SCHEMA_VERSION:
        raise ValueError("Archived v2 carousel packages are read-only; create a new v3 package.")
    return state


def prepare_codex_builtin_image_generation(
    carousel_dir: Path,
    *,
    proof_slide: int | None = None,
    formats: list[str] | None = None,
) -> dict[str, Any]:
    carousel_dir = Path(carousel_dir).expanduser()
    # Reject archived packages before changing their format contract or any
    # other byte. Archived v2 remains read-only auditable.
    state = _require_v3(carousel_dir)
    if formats is not None:
        write_format_contract(
            carousel_dir,
            list(normalize_requested_formats(formats)),
            source="creator_request",
            replace=True,
        )
        state = _require_v3(carousel_dir)
    reason = pre_generation_review_gate_reason(carousel_dir)
    if reason:
        next_action = (
            "lock_visible_actions"
            if visual_plan_quality_gate_reason(carousel_dir)
            else "attach_four_curated_identity_references_and_one_style_board"
        )
        return write_v3_state(
            carousel_dir,
            {**state, "status": "blocked", "next_action": next_action, "reason": reason},
        )

    slides = _slides(carousel_dir)
    prompts = _prompt_slides(carousel_dir)
    valid = {int(item["slide"]) for item in prompts}
    if proof_slide is not None:
        selected = [int(proof_slide)]
        if state.get("proof_slide") not in (None, int(proof_slide)) and _proof_approved(carousel_dir, state):
            raise ValueError("A different proof is already approved; change inputs to invalidate it first.")
        proof_number = int(proof_slide)
    elif state.get("status") == "proof_failed":
        proof_number = int(state.get("proof_slide") or 0)
        selected = [proof_number]
    elif _proof_approved(carousel_dir, state):
        proof_number = int(state["proof_slide"])
        failed = [
            int(number)
            for number, record in state["slides"].items()
            if record.get("status") == "failed"
        ]
        selected = failed or [
            int(number)
            for number in state["slides"]
            if not _candidate_is_usable(
                carousel_dir,
                state,
                _approved_candidate(carousel_dir, int(number)),
            )
            and not _candidate_is_usable(
                carousel_dir,
                state,
                _current_candidate(carousel_dir, state, int(number)),
            )
        ]
    else:
        proof_number = int(
            state.get("proof_slide")
            or proof_slide_from_gate(_prompt_pack(carousel_dir).get("proof_gate"), prompts)
        )
        selected = [proof_number]
    if not selected:
        return write_v3_state(
            carousel_dir,
            {
                **state,
                "status": "final_qa_required",
                "next_action": "review_final_pixels",
                "selected_slides": [],
            },
        )
    if any(number not in valid for number in selected):
        raise ValueError("Selected slides are not present in prompt-pack.json.")
    exhausted = [
        number
        for number in selected
        if int(state["slides"][str(number)].get("attempts", 0)) >= MAX_SEMANTIC_ATTEMPTS
    ]
    if exhausted:
        is_proof = proof_number in exhausted
        return write_v3_state(
            carousel_dir,
            {
                **state,
                "status": "proof_failed" if is_proof else "final_qa_failed",
                "next_action": "repair_visual_premise",
                "selected_slides": exhausted,
                "reason": "Maximum two semantic image attempts reached for: "
                + ", ".join(str(value) for value in exhausted),
            },
        )

    for number in selected:
        for output_format in state["selected_formats"]:
            prompt_text = _current_compiled_prompt(carousel_dir, number, output_format)
            path = carousel_dir / prompt_handoff_relative_path(output_format, number)
            path.parent.mkdir(parents=True, exist_ok=True)
            write_target = path.with_name(path.name + ".tmp")
            write_target.write_text(prompt_text, encoding="utf-8")
            write_target.replace(path)
        state["slides"][str(number)]["status"] = "handoff_ready"
    state.pop("reason", None)
    return write_v3_state(
        carousel_dir,
        {
            **state,
            "status": "handoff_ready",
            "next_action": "generate_selected_slides",
            "proof_slide": proof_number,
            "selected_slides": selected,
        },
    )


def image_dimensions(image_bytes: bytes) -> dict[str, int]:
    if len(image_bytes) < 24 or image_bytes[:8] != b"\x89PNG\r\n\x1a\n":
        raise ValueError("Generated output must be a PNG.")
    return {
        "width": int.from_bytes(image_bytes[16:20], "big"),
        "height": int.from_bytes(image_bytes[20:24], "big"),
    }


def decoded_png_dimensions(image_bytes: bytes) -> dict[str, int]:
    """Decode the complete PNG before trusting its dimensions."""

    if len(image_bytes) < 8 or image_bytes[:8] != b"\x89PNG\r\n\x1a\n":
        raise ValueError("Generated output must be a PNG.")
    try:
        with Image.open(BytesIO(image_bytes)) as image:
            if image.format != "PNG":
                raise ValueError("Generated output must be a PNG.")
            image.load()
            width, height = image.size
    except (UnidentifiedImageError, OSError, SyntaxError) as exc:
        raise ValueError("Generated output must be a decodable PNG.") from exc
    return {"width": int(width), "height": int(height)}


def target_size_for_format(output_format: str) -> tuple[int, int]:
    width, height = format_spec(output_format)["target_size"]
    return int(width), int(height)


def _normalize_source_for_format(
    image_bytes: bytes,
    output_format: str,
) -> tuple[bytes, dict[str, int], str, str | None]:
    dimensions = decoded_png_dimensions(image_bytes)
    width, height = dimensions["width"], dimensions["height"]
    target_width, target_height = target_size_for_format(output_format)
    if not source_dimensions_are_acceptable(output_format, width, height):
        raise ValueError(
            f"{output_format} source {width}x{height} is outside its safe native-source contract."
        )
    if (width, height) == (target_width, target_height):
        return image_bytes, dimensions, "native_exact", None
    # Only Instagram post can reach this branch. The source is exact 3:4 and
    # larger than the target, so LANCZOS is a pure downsample: no crop, pad,
    # stretch, or upscale.
    with Image.open(BytesIO(image_bytes)) as image:
        image.load()
        normalized = image.resize(
            (target_width, target_height),
            resample=Image.Resampling.LANCZOS,
        )
        output = BytesIO()
        normalized.save(output, format="PNG", optimize=False, compress_level=9)
    payload = output.getvalue()
    exact = decoded_png_dimensions(payload)
    if (exact["width"], exact["height"]) != (target_width, target_height):
        raise ValueError("Deterministic source normalization produced the wrong dimensions.")
    return (
        payload,
        exact,
        "lanczos_downsample",
        f"downsampled from {width}x{height} without crop, pad, stretch, or upscale",
    )


def _asset_binding_fingerprint(slide: int, output_format: str, binding: dict[str, Any]) -> str:
    try:
        from pipeline.stages.carousel_pixel_qa import asset_binding_fingerprint

        return asset_binding_fingerprint(slide, output_format, binding)
    except ImportError:
        return canonical_fingerprint(
            {
                "slide": slide,
                "format": output_format,
                "path": binding.get("path"),
                "sha256": binding.get("sha256"),
                "width": binding.get("width"),
                "height": binding.get("height"),
            }
        )


def reject_non_codex_builtin_sources(
    carousel_dir: Path, generated_paths_by_format: dict[str, list[str | Path]]
) -> None:
    package_root = resolve_package_artifact_path(carousel_dir, ".", "")
    for paths in generated_paths_by_format.values():
        for raw in paths:
            path = Path(raw).expanduser()
            # A fresh imagegen return may arrive through macOS' system aliases
            # (/var -> /private/var, /tmp -> /private/tmp).  Those parent
            # aliases are not controlled by the package.  Reject only an
            # explicitly supplied source-file symlink, then compare resolved
            # containment to keep all package-internal bytes non-recyclable.
            if path.is_symlink() or not path.is_file():
                raise FileNotFoundError(f"Missing or unsafe generated image: {path}")
            resolved = path.resolve(strict=True)
            if resolved == package_root or package_root in resolved.parents:
                raise ValueError(
                    "Existing package, quarantine, candidate, source-evidence, or final files "
                    "cannot be recycled as fresh imagegen output."
                )


def quarantine_generated_sources(
    carousel_dir: Path,
    *,
    slides: list[dict[str, Any]],
    output_formats: list[str] | tuple[str, ...],
    generated_paths_by_format: dict[str, list[str | Path]],
    attempts_by_slide: dict[str, int],
    input_fingerprints: dict[str, dict[str, str]] | None = None,
    **_: Any,
) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    input_fingerprints = input_fingerprints or {}
    for index, slide in enumerate(slides):
        number = int(slide["slide"])
        attempt = int(attempts_by_slide.get(str(number), 0)) + 1
        root = _candidate_record_path(carousel_dir, number, attempt).parent
        remove_path_without_following(root, package_root=carousel_dir)
        root.mkdir(parents=True)
        outputs: dict[str, Any] = {}
        source_evidence: dict[str, Any] = {}
        ingest_issues: list[str] = []
        for output_format in output_formats:
            source = Path(generated_paths_by_format[output_format][index]).expanduser()
            payload = source.read_bytes()
            raw_target = root / "source" / f"{output_format}.png"
            raw_target.parent.mkdir(parents=True, exist_ok=True)
            raw_target.write_bytes(payload)
            raw_binding: dict[str, Any] = {
                "path": package_relative_path(carousel_dir, raw_target),
                "sha256": sha256_binding(payload),
            }
            try:
                raw_dimensions = decoded_png_dimensions(payload)
                raw_binding.update(raw_dimensions)
                normalized_payload, dimensions, mode, note = _normalize_source_for_format(
                    payload,
                    output_format,
                )
            except ValueError as exc:
                raw_binding["accepted"] = False
                source_evidence[output_format] = raw_binding
                ingest_issues.append(f"slide {number} {output_format}: {exc}")
                continue
            raw_binding.update(
                {
                    "accepted": True,
                    "normalization": mode,
                }
            )
            if note:
                raw_binding["normalization_note"] = note
            source_evidence[output_format] = raw_binding
            target = root / f"{output_format}.png"
            target.write_bytes(normalized_payload)
            binding = {
                "path": package_relative_path(carousel_dir, target),
                "sha256": sha256_binding(normalized_payload),
                **dimensions,
            }
            binding["binding_sha256"] = _asset_binding_fingerprint(number, output_format, binding)
            outputs[output_format] = binding
        record = {
            "schema_version": "carousel-candidate/v1",
            "slide": number,
            "copy": str(slide.get("copy") or ""),
            "attempt": attempt,
            "input_sha256": input_fingerprints.get(str(number), {}).get("input_sha256", ""),
            "native_outputs": outputs,
            "source_evidence": source_evidence,
            "ingest_issues": ingest_issues,
        }
        write_json(root / "candidate.json", record)
        records.append(record)
    return records


def image_set_sha256(slides: list[dict[str, Any]]) -> str:
    return canonical_fingerprint(
        [
            {
                "slide": int(slide["slide"]),
                "input_sha256": slide.get("input_sha256"),
                "native_outputs": {
                    key: value.get("binding_sha256")
                    for key, value in sorted((slide.get("native_outputs") or {}).items())
                },
            }
            for slide in slides
        ]
    )


def current_proof_binding_sha256(package_dir: Path) -> str:
    state = _require_v3(Path(package_dir))
    number = state.get("proof_slide")
    if number is None:
        raise ValueError("No proof slide is selected.")
    candidate = _current_candidate(Path(package_dir), state, int(number)) or _approved_candidate(
        Path(package_dir), int(number)
    )
    if candidate is None or _binding_issues(Path(package_dir), candidate):
        raise ValueError("No current hash-bound proof candidate exists.")
    return image_set_sha256([candidate])


def _prospective_manifest(
    carousel_dir: Path,
    candidates: dict[int, dict[str, Any]],
    *,
    state: dict[str, Any] | None = None,
) -> dict[str, Any]:
    state = state or _require_v3(carousel_dir)
    records: list[dict[str, Any]] = []
    for number in sorted(candidates):
        candidate = candidates[number]
        outputs: dict[str, Any] = {}
        for output_format, source in sorted(candidate["native_outputs"].items()):
            binding = {
                "path": expected_output_path(carousel_dir, output_format, number).relative_to(
                    carousel_dir
                ).as_posix(),
                "sha256": source["sha256"],
                "width": source["width"],
                "height": source["height"],
            }
            binding["binding_sha256"] = _asset_binding_fingerprint(number, output_format, binding)
            outputs[output_format] = binding
        records.append(
            {
                "slide": number,
                "input_sha256": state["slides"][str(number)]["input_sha256"],
                "native_outputs": outputs,
            }
        )
    return {
        "schema_version": "carousel-final-images/v3",
        "selected_formats": list(state["selected_formats"]),
        "format_sha256": state["format_sha256"],
        "slides": records,
    }


def _all_deck_candidates(
    carousel_dir: Path,
    state: dict[str, Any],
    *,
    include_current: bool,
) -> dict[int, dict[str, Any]]:
    result: dict[int, dict[str, Any]] = {}
    for raw_number in state["slides"]:
        number = int(raw_number)
        candidate = _approved_candidate(carousel_dir, number)
        if not _candidate_is_usable(carousel_dir, state, candidate) and include_current:
            candidate = _current_candidate(carousel_dir, state, number)
        if _candidate_is_usable(carousel_dir, state, candidate):
            result[number] = candidate  # type: ignore[assignment]
    return result


def _write_manifest_candidate_if_complete(carousel_dir: Path, state: dict[str, Any]) -> None:
    candidates = _all_deck_candidates(carousel_dir, state, include_current=True)
    if set(candidates) == {int(value) for value in state["slides"]}:
        manifest = _prospective_manifest(carousel_dir, candidates)
        write_json(carousel_dir / FINAL_MANIFEST_CANDIDATE, manifest)
        # Build a private mirror with the exact eventual final paths. This lets
        # the repo validate Codex's final decoded-pixel observations without
        # creating a public final folder or manifest before the audit.
        audit_root = carousel_dir / FINAL_AUDIT_CANDIDATE_FOLDER
        remove_path_without_following(audit_root, package_root=carousel_dir)
        audit_root.mkdir(parents=True)
        for filename in (
            "creative-context.json",
            "format-contract.json",
            "slides.json",
            "prompt-pack.json",
        ):
            shutil.copyfile(carousel_dir / filename, audit_root / filename)
        references = carousel_dir / ".internal/references"
        if references.is_dir():
            shutil.copytree(references, audit_root / ".internal/references")
        for number, candidate in candidates.items():
            for output_format, binding in candidate["native_outputs"].items():
                source = resolve_package_artifact_path(
                    carousel_dir, binding["path"], "", require_file=True
                )
                target = expected_output_path(audit_root, output_format, number)
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(source, target)


def ingest_generated_outputs(
    carousel_dir: Path,
    generated_paths_by_format: dict[str, list[str | Path]],
    *,
    proof_slide: int | None = None,
) -> dict[str, Any]:
    carousel_dir = Path(carousel_dir).expanduser()
    state = _require_v3(carousel_dir)
    if state.get("status") != "handoff_ready":
        raise ValueError("Prepare the compiled prompt before ingesting images.")
    handoff_issues = compiled_prompt_handoff_integrity_issues(carousel_dir, state=state)
    if handoff_issues:
        return write_v3_state(
            carousel_dir,
            {
                **state,
                "status": "blocked",
                "next_action": "recompile_prompt_handoff",
                "reason": "; ".join(handoff_issues),
            },
        )
    selected = [int(value) for value in state["selected_slides"]]
    if proof_slide is not None and selected != [int(proof_slide)]:
        raise ValueError("proof_slide does not match the active compiled handoff.")
    formats = list(state["selected_formats"])
    if set(generated_paths_by_format) != set(formats):
        raise ValueError("Generated formats must match the selected format contract exactly.")
    if any(len(generated_paths_by_format[value]) != len(selected) for value in formats):
        raise ValueError("Each format needs one image per selected slide.")
    reject_non_codex_builtin_sources(carousel_dir, generated_paths_by_format)
    slide_by_number = {int(item["slide"]): item for item in _slides(carousel_dir)}
    attempts = {
        number: int(record.get("attempts", 0) or 0)
        for number, record in state["slides"].items()
    }
    candidates = quarantine_generated_sources(
        carousel_dir,
        slides=[slide_by_number[number] for number in selected],
        output_formats=formats,
        generated_paths_by_format=generated_paths_by_format,
        attempts_by_slide=attempts,
        input_fingerprints=state["slides"],
    )
    failed_candidates = [candidate for candidate in candidates if candidate.get("ingest_issues")]
    for candidate in candidates:
        number = str(candidate["slide"])
        state["slides"][number]["attempts"] = candidate["attempt"]
        state["slides"][number]["status"] = (
            "failed" if candidate.get("ingest_issues") else "qa_required"
        )
    is_proof = selected == [int(state["proof_slide"])] and not _proof_approved(carousel_dir, state)
    if failed_candidates:
        failed_numbers = [int(candidate["slide"]) for candidate in failed_candidates]
        exhausted = [
            number
            for number in failed_numbers
            if int(state["slides"][str(number)]["attempts"]) >= MAX_SEMANTIC_ATTEMPTS
        ]
        state["status"] = "proof_failed" if is_proof else "final_qa_failed"
        state["selected_slides"] = failed_numbers
        state["next_action"] = (
            "repair_visual_premise" if exhausted else "retry_selected_slides"
        )
        state["reason"] = "; ".join(
            issue
            for candidate in failed_candidates
            for issue in candidate.get("ingest_issues") or []
        )
        remove_path_without_following(
            carousel_dir / FINAL_MANIFEST_CANDIDATE, package_root=carousel_dir
        )
        remove_path_without_following(
            carousel_dir / FINAL_AUDIT_CANDIDATE_FOLDER,
            package_root=carousel_dir,
        )
        return write_v3_state(carousel_dir, state)
    state["status"] = "proof_qa_required" if is_proof else "final_qa_required"
    state["next_action"] = "review_proof_pixels" if is_proof else "review_final_pixels"
    state.pop("reason", None)
    state = write_v3_state(carousel_dir, state)
    if not is_proof:
        _write_manifest_candidate_if_complete(carousel_dir, state)
    return state


def _bind_and_validate_qa(
    carousel_dir: Path,
    state: dict[str, Any],
    qa_path: Path,
    candidates: list[dict[str, Any]],
    *,
    proof: bool,
) -> tuple[dict[str, Any], list[str]]:
    authored = load_json(qa_path)
    try:
        if proof:
            from pipeline.stages.carousel_pixel_qa import bind_proof_qa, validate_proof_qa

            bound = bind_proof_qa(carousel_dir, authored, candidates)
            issues = validate_proof_qa(carousel_dir, bound)
        else:
            from pipeline.stages.carousel_pixel_qa import bind_final_qa, validate_final_qa

            manifest = load_json(carousel_dir / FINAL_MANIFEST_CANDIDATE)
            bound = bind_final_qa(authored, manifest)
            issues = validate_final_qa(
                carousel_dir / FINAL_AUDIT_CANDIDATE_FOLDER,
                bound,
                manifest,
            )
    except ValueError as exc:
        bound = authored
        issues = [str(exc)]
    except ImportError:
        # Integration fallback while the pixel-contract lane lands. It remains
        # fail-closed and cannot certify a PASS without that validator.
        bound = authored
        issues = ["carousel pixel QA validator is unavailable"]
    write_json(qa_path, bound)
    return bound, issues


def _first_explicit_semantic_failure(qa: dict[str, Any]) -> int | None:
    """Return only the first slide with an authored, explicit semantic FAIL.

    Missing/malformed checks are QA-contract defects, not evidence that new
    pixels are needed. They must route back to QA repair without spending an
    image attempt.
    """

    try:
        from pipeline.stages.carousel_pixel_qa import PIXEL_QA_ORDER
    except ImportError:
        return None
    records = qa.get("slides")
    if not isinstance(records, list):
        return None
    for record in records:
        if not isinstance(record, dict):
            continue
        try:
            number = int(record.get("slide"))
        except (TypeError, ValueError):
            continue
        reviews = record.get("reviews")
        if not isinstance(reviews, dict):
            continue
        for review in reviews.values():
            if not isinstance(review, dict):
                continue
            checks = review.get("checks")
            if not isinstance(checks, dict):
                continue
            for gate in PIXEL_QA_ORDER:
                check = checks.get(gate)
                if (
                    isinstance(check, dict)
                    and str(check.get("status") or "").strip().upper() == "FAIL"
                ):
                    return number
    return None


def _copy_approved_candidate(carousel_dir: Path, candidate: dict[str, Any]) -> dict[str, Any]:
    number = int(candidate["slide"])
    root = _approved_record_path(carousel_dir, number).parent
    outputs_in_place = candidate.get("native_outputs") or {}
    if outputs_in_place and all(
        str(binding.get("path") or "").startswith(
            f"{APPROVED_CANDIDATE_FOLDER}/slide-{number:02d}/"
        )
        for binding in outputs_in_place.values()
        if isinstance(binding, dict)
    ):
        # The approved proof is already the final candidate. Reuse its exact
        # normalized bytes; never delete the source directory before copying.
        return candidate
    remove_path_without_following(root, package_root=carousel_dir)
    root.mkdir(parents=True)
    outputs: dict[str, Any] = {}
    for output_format, binding in candidate["native_outputs"].items():
        source = resolve_package_artifact_path(
            carousel_dir, binding["path"], "", require_file=True
        )
        target = root / f"{output_format}.png"
        shutil.copyfile(source, target)
        current = {
            "path": package_relative_path(carousel_dir, target),
            "sha256": sha256_binding(target.read_bytes()),
            "width": binding["width"],
            "height": binding["height"],
        }
        current["binding_sha256"] = _asset_binding_fingerprint(number, output_format, current)
        outputs[output_format] = current
    approved = {**candidate, "native_outputs": outputs}
    write_json(root / "candidate.json", approved)
    return approved


def review_quarantined_outputs(
    carousel_dir: Path,
    *,
    qa_path: str | Path | None = None,
) -> dict[str, Any]:
    carousel_dir = Path(carousel_dir).expanduser()
    state = _require_v3(carousel_dir)
    proof = state.get("status") == "proof_qa_required"
    if state.get("status") not in {"proof_qa_required", "final_qa_required"}:
        raise ValueError("No quarantined candidate is awaiting pixel QA.")
    selected = [int(value) for value in state.get("selected_slides") or []]
    candidates = [_current_candidate(carousel_dir, state, number) for number in selected]
    if any(candidate is None for candidate in candidates):
        raise ValueError("Current quarantine candidate inventory is incomplete.")
    exact_candidates = [candidate for candidate in candidates if candidate is not None]
    default = "proof-qa.json" if proof else "visual-qa.json"
    path = resolve_package_artifact_path(carousel_dir, qa_path, default, require_file=True)
    bound_qa, issues = _bind_and_validate_qa(
        carousel_dir, state, path, exact_candidates, proof=proof
    )
    if issues:
        failed_number = _first_explicit_semantic_failure(bound_qa)
        if failed_number is None:
            state["status"] = "proof_qa_required" if proof else "final_qa_required"
            state["next_action"] = "repair_proof_qa" if proof else "repair_final_qa"
            state["reason"] = "; ".join(issues)
            return write_v3_state(carousel_dir, state)
        if str(failed_number) not in state["slides"]:
            state["status"] = "proof_qa_required" if proof else "final_qa_required"
            state["next_action"] = "repair_proof_qa" if proof else "repair_final_qa"
            state["reason"] = "Semantic QA names a slide outside the current generation state."
            return write_v3_state(carousel_dir, state)
        state["slides"][str(failed_number)]["status"] = "failed"
        exhausted = (
            [failed_number]
            if int(state["slides"][str(failed_number)]["attempts"])
            >= MAX_SEMANTIC_ATTEMPTS
            else []
        )
        state["status"] = "proof_failed" if proof else "final_qa_failed"
        state["next_action"] = (
            "repair_visual_premise" if exhausted else "retry_selected_slides"
        )
        state["selected_slides"] = [failed_number]
        state["reason"] = "; ".join(issues)
        remove_path_without_following(
            carousel_dir / FINAL_MANIFEST_CANDIDATE, package_root=carousel_dir
        )
        remove_path_without_following(
            carousel_dir / FINAL_AUDIT_CANDIDATE_FOLDER,
            package_root=carousel_dir,
        )
        return write_v3_state(carousel_dir, state)
    if proof:
        state["slides"][str(selected[0])]["status"] = "qa_passed"
        state["status"] = "awaiting_creator_proof_approval"
        state["next_action"] = "approve_proof"
    else:
        deck_candidates = _all_deck_candidates(
            carousel_dir,
            state,
            include_current=True,
        )
        if set(deck_candidates) != {int(value) for value in state["slides"]}:
            raise ValueError("Final QA passed without a complete usable candidate deck.")
        for candidate in deck_candidates.values():
            _copy_approved_candidate(carousel_dir, candidate)
            state["slides"][str(candidate["slide"])]["status"] = "approved_candidate"
        state["status"] = "final_qa_required"
        state["next_action"] = "finalize_deck"
    state.pop("reason", None)
    return write_v3_state(carousel_dir, state)


def _qa_without_approval(qa: dict[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in qa.items() if key != "creator_approval"}


def approve_proof(
    carousel_dir: Path,
    *,
    approved_by: str = "creator",
    proof_sha256: str,
) -> dict[str, Any]:
    carousel_dir = Path(carousel_dir).expanduser()
    state = _require_v3(carousel_dir)
    if state.get("status") != "awaiting_creator_proof_approval":
        raise ValueError("A passing current proof QA is required before approval.")
    if not str(approved_by).strip():
        raise ValueError("approved_by is required.")
    if not str(proof_sha256).strip():
        raise ValueError("proof_sha256 is required and must bind the current proof pixels.")
    number = int(state["proof_slide"])
    candidate = _current_candidate(carousel_dir, state, number)
    if (
        candidate is None
        or int(candidate.get("slide") or 0) != number
        or candidate.get("input_sha256") != state["slides"][str(number)]["input_sha256"]
        or _binding_issues(carousel_dir, candidate)
    ):
        raise ValueError("The current proof candidate is missing or stale.")
    current_sha = image_set_sha256([candidate])
    if proof_sha256 != current_sha:
        raise ValueError("proof_sha256 does not match the current proof pixels.")
    qa_path = carousel_dir / "proof-qa.json"
    qa = load_json(qa_path)
    issues = _proof_qa_validation_issues(carousel_dir, qa, candidate)
    if issues:
        raise ValueError("Proof QA is stale or incomplete: " + "; ".join(issues))
    approval = {
        "status": "APPROVED",
        "approved": True,
        "approved_by": str(approved_by).strip(),
        "proof_binding_sha256": current_sha,
        "proof_qa_sha256": canonical_fingerprint(_qa_without_approval(qa)),
        "proof_input_sha256": state["slides"][str(number)]["input_sha256"],
        "asset_binding_hashes": {
            f"{number}:{output_format}": binding["binding_sha256"]
            for output_format, binding in candidate["native_outputs"].items()
        },
    }
    qa["creator_approval"] = approval
    write_json(qa_path, qa)
    _copy_approved_candidate(carousel_dir, candidate)
    state["slides"][str(number)]["status"] = "approved_candidate"
    state["status"] = "batch_ready"
    state["next_action"] = "prepare_remaining_slides"
    state["selected_slides"] = []
    state.pop("reason", None)
    return write_v3_state(carousel_dir, state)


def finalize_codex_builtin_outputs(carousel_dir: Path) -> dict[str, Any]:
    carousel_dir = Path(carousel_dir).expanduser()
    state = _require_v3(carousel_dir)
    if state.get("status") != "final_qa_required" or state.get("next_action") != "finalize_deck":
        raise ValueError("A passing final pixel QA is required before promotion.")
    candidates = _all_deck_candidates(carousel_dir, state, include_current=False)
    expected = {int(value) for value in state["slides"]}
    if set(candidates) != expected:
        raise ValueError("Every slide needs an approved final candidate before promotion.")
    manifest = _prospective_manifest(carousel_dir, candidates)
    candidate_manifest = load_json(carousel_dir / FINAL_MANIFEST_CANDIDATE)
    if candidate_manifest != manifest:
        raise ValueError("The hidden final manifest candidate is stale.")
    qa_path = carousel_dir / "visual-qa.json"
    qa = load_json(qa_path)
    try:
        from pipeline.stages.carousel_pixel_qa import validate_final_qa

        qa_issues = validate_final_qa(
            carousel_dir / FINAL_AUDIT_CANDIDATE_FOLDER,
            qa,
            manifest,
        )
    except ImportError:
        qa_issues = ["carousel pixel QA validator is unavailable"]
    if qa_issues:
        return write_v3_state(
            carousel_dir,
            {
                **state,
                "status": "final_qa_failed",
                "next_action": "repair_final_qa",
                "reason": "; ".join(qa_issues),
            },
        )

    staging = carousel_dir / PROMOTION_STAGING_FOLDER
    audit_root = carousel_dir / FINAL_AUDIT_CANDIDATE_FOLDER
    remove_path_without_following(staging, package_root=carousel_dir)
    remove_path_without_following(audit_root, package_root=carousel_dir)
    try:
        for number, candidate in candidates.items():
            for output_format, binding in candidate["native_outputs"].items():
                source = resolve_package_artifact_path(
                    carousel_dir, binding["path"], "", require_file=True
                )
                target = staging / str(format_spec(output_format)["folder"]) / f"slide-{number:02d}.png"
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(source, target)
        audit_root.mkdir(parents=True)
        for filename in ("creative-context.json", "format-contract.json", "slides.json", "prompt-pack.json"):
            shutil.copyfile(carousel_dir / filename, audit_root / filename)
        reference_root = carousel_dir / ".internal/references"
        if reference_root.is_dir():
            shutil.copytree(reference_root, audit_root / ".internal/references")
        for output_format in state["selected_formats"]:
            folder = str(format_spec(output_format)["folder"])
            shutil.copytree(staging / folder, audit_root / folder)
        write_json(audit_root / "final-images.json", manifest)
        write_json(audit_root / "visual-qa.json", qa)

        from pipeline.stages.carousel_quality import build_final_audit

        audit = build_final_audit(audit_root, write=False)
        if audit.get("status") != PASS:
            write_json(carousel_dir / "final-audit.json", audit)
            return write_v3_state(
                carousel_dir,
                {
                    **state,
                    "status": "final_qa_failed",
                    "next_action": "repair_final_audit",
                    "reason": "; ".join(audit.get("issues") or ["final audit failed"]),
                },
            )
        # No public manifest exists before the hidden audit above passes.
        for output_format in state["selected_formats"]:
            folder = str(format_spec(output_format)["folder"])
            final_dir = carousel_dir / folder
            remove_path_without_following(final_dir, package_root=carousel_dir)
            (staging / folder).replace(final_dir)
        write_json(carousel_dir / "final-images.json", manifest)
        # Persist the exact canonical bindings computed by the same auditor
        # that certified the hidden package.  Do not re-hash JSON bytes using a
        # second convention at promotion time.
        write_json(carousel_dir / "final-audit.json", audit)
        state["status"] = "publish_ready"
        state["next_action"] = "publish"
        state["selected_slides"] = []
        for record in state["slides"].values():
            record["status"] = "publish_ready"
        state.pop("reason", None)
        return write_v3_state(carousel_dir, state)
    finally:
        remove_path_without_following(staging, package_root=carousel_dir)
        remove_path_without_following(audit_root, package_root=carousel_dir)


__all__ = [
    "APPROVED_CANDIDATE_FOLDER",
    "FINAL_MANIFEST_CANDIDATE",
    "MAX_SEMANTIC_ATTEMPTS",
    "approve_proof",
    "build_compiled_prompt_handoff",
    "compiled_prompt_handoff_integrity_issues",
    "current_proof_qa_issues",
    "current_proof_binding_sha256",
    "finalize_codex_builtin_outputs",
    "generator_prompt_text",
    "image_set_sha256",
    "ingest_generated_outputs",
    "initialize_generation_state",
    "prepare_codex_builtin_image_generation",
    "read_generation_state",
    "reconcile_package_state",
    "review_quarantined_outputs",
    "sha256_binding",
]
