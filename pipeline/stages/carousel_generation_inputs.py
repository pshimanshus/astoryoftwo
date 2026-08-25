"""Canonical, slide-local fingerprints for the carousel generation hot path.

The state machine stores these digests instead of serializing creative inputs.
JSON formatting and object-key order therefore cannot invalidate generated
work, while a real semantic, prompt, reference, format, or brand change does.
"""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
from typing import Any

from pipeline.stages.carousel_format_contract import (
    locked_format_contract_fingerprint,
    locked_formats,
)
from pipeline.stages.carousel_prompt_compiler import compile_image_prompt, extract_scene_summary


INPUT_SCHEMA_VERSION = "carousel-generation-inputs/v2"
REFERENCE_BINDING_SCHEMA_VERSION = "carousel-reference-bindings/v1"
PROMPT_COMPILER_VERSION = "carousel-prompt-compiler/v3"
BRAND_CONTRACT_VERSION = "a-story-brand/v1"

SLIDE_SOURCE_FIELDS = (
    "slide",
    "role",
    "copy",
    "visual",
    "physical_action",
    "relationship_state",
    "scene",
    "composition",
    "camera",
    "focal_hierarchy",
    "setting",
    "wardrobe",
    "pose",
    "props",
    "background",
    "emotion",
    "continuity_lock",
    "negative_prompt",
)


def canonical_json_bytes(value: Any) -> bytes:
    """Encode JSON semantics, independent of whitespace and key order."""

    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


def sha256_binding(payload: bytes) -> str:
    return "sha256:" + hashlib.sha256(payload).hexdigest()


def canonical_fingerprint(value: Any) -> str:
    return sha256_binding(canonical_json_bytes(value))


def _read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _package_file(package_dir: Path, raw_path: Any, *, role: str) -> Path:
    package_path = Path(package_dir).expanduser()
    if package_path.is_symlink():
        raise ValueError("carousel package path cannot itself be a symlink")
    supplied_root = Path(os.path.abspath(package_path))
    root = package_path.resolve(strict=True)
    path = Path(str(raw_path)).expanduser()
    if not path.is_absolute():
        path = supplied_root / path
    path = Path(os.path.abspath(path))
    lexical_relative: Path | None = None
    for candidate_root in (supplied_root, root):
        try:
            lexical_relative = path.relative_to(candidate_root)
            break
        except ValueError:
            continue
    if lexical_relative is not None:
        cursor = root
        for part in lexical_relative.parts:
            cursor /= part
            if cursor.is_symlink():
                raise ValueError(
                    f"{role} reference cannot contain package-local symlink components: {raw_path}"
                )
    try:
        resolved = path.resolve(strict=True)
        resolved.relative_to(root)
    except (FileNotFoundError, OSError, ValueError) as exc:
        raise ValueError(
            f"{role} reference is missing or outside the carousel package: {raw_path}"
        ) from exc
    if not resolved.is_file():
        raise ValueError(f"{role} reference is not a regular file: {raw_path}")
    return resolved


def _reference_bindings(
    package_dir: Path,
    values: list[Any],
    *,
    role: str,
) -> list[dict[str, str]]:
    by_role_and_path: dict[tuple[str, str], dict[str, str]] = {}
    root = package_dir.resolve(strict=True)
    for raw_path in values:
        path = _package_file(package_dir, raw_path, role=role)
        relative = path.relative_to(root).as_posix()
        binding = {
            "role": role,
            "path": relative,
            "sha256": sha256_binding(path.read_bytes()),
        }
        by_role_and_path[(role, relative)] = binding
    return [
        by_role_and_path[key]
        for key in sorted(by_role_and_path)
    ]


def _shared_reference_bindings(
    package_dir: Path,
    prompt_pack: dict[str, Any],
    creative_context: dict[str, Any],
) -> list[dict[str, str]]:
    """Return canonical identity/style bindings from the real prompt-pack keys.

    Prompt-pack lists are the generation attachment authority after selected
    references have been localized into the package. The list order is not
    semantic; the binding role, package-relative path, and exact file bytes
    are. Keeping those three values in one sorted structure makes reference
    drift explicit in every slide fingerprint.
    """

    root = package_dir.resolve(strict=True)
    selection = creative_context.get("identity_reference_selection")
    selected = selection.get("selected_references") if isinstance(selection, dict) else []
    role_by_path: dict[str, str] = {}
    for record in selected if isinstance(selected, list) else []:
        if not isinstance(record, dict) or not record.get("path"):
            continue
        path = _package_file(package_dir, record["path"], role="identity selection")
        role_by_path[path.relative_to(root).as_posix()] = str(
            record.get("role") or "unassigned identity role"
        )

    identity_bindings: list[dict[str, str]] = []
    for raw_path in [
        *(prompt_pack.get("identity_reference_images") or []),
        *(prompt_pack.get("identity_dossier_reference_images") or []),
    ]:
        path = _package_file(package_dir, raw_path, role="identity")
        relative = path.relative_to(root).as_posix()
        identity_bindings.append(
            {
                "role": f"identity:{role_by_path.get(relative, 'unassigned identity role')}",
                "path": relative,
                "sha256": sha256_binding(path.read_bytes()),
            }
        )

    bindings = [
        *identity_bindings,
        *_reference_bindings(
            package_dir,
            list(prompt_pack.get("style_reference_images") or []),
            role="style",
        ),
    ]
    return sorted(
        bindings,
        key=lambda binding: (
            binding["role"],
            binding["path"],
            binding["sha256"],
        ),
    )


def _slide_source(slide: dict[str, Any], prompt: dict[str, Any]) -> dict[str, Any]:
    source = {
        key: slide[key]
        for key in SLIDE_SOURCE_FIELDS
        if key in slide and slide[key] not in (None, "", [])
    }
    # Prompt records are generator inputs too. Keep only slide-local semantics;
    # shared style, identity, and brand inputs are hashed separately below.
    source["prompt"] = {
        key: prompt[key]
        for key in (
            "slide",
            "text",
            "scene",
            "pose",
            "wardrobe",
            "props",
            "background",
            "emotion",
            "negative_prompt",
        )
        if key in prompt and prompt[key] not in (None, "", [])
    }
    return source


def _join_slide_directions(slide: dict[str, Any], keys: tuple[str, ...]) -> str:
    return "; ".join(
        str(slide[key]).strip()
        for key in keys
        if key in slide and slide[key] not in (None, "", [])
    )


def effective_slide_prompt_fields(
    slide: dict[str, Any],
    prompt: dict[str, Any],
    *,
    shared_negative: str,
) -> dict[str, str]:
    """Return the slide-authoritative generator fields for new v3 packages.

    ``prompt-pack.json`` retains the initial human-readable prompt record, but
    it is not a second authority for mutable slide semantics. A correction in
    ``slides.json`` must therefore change both the compiled bytes and their
    fingerprint instead of regenerating from a stale prompt-pack duplicate.
    """

    scene = str(
        slide.get("physical_action")
        or slide.get("visual")
        or slide.get("scene")
        or prompt.get("scene")
        or extract_scene_summary(str(prompt.get("prompt") or ""))
    )
    pose = _join_slide_directions(
        slide,
        ("pose", "composition", "camera", "focal_hierarchy"),
    )
    background = _join_slide_directions(
        slide,
        ("background", "setting", "continuity_lock"),
    )
    return {
        "scene": scene,
        "pose": pose,
        "wardrobe": str(slide.get("wardrobe") or ""),
        "props": str(slide.get("props") or ""),
        "background": background,
        "emotion": _join_slide_directions(
            slide,
            ("relationship_state", "emotion"),
        ),
        "negative_prompt": str(slide.get("negative_prompt") or shared_negative),
    }


def _compiled_prompt_fingerprint(
    *,
    slide: dict[str, Any],
    prompt: dict[str, Any],
    slide_count: int,
    formats: tuple[str, ...],
    style: str,
    negative: str,
) -> str:
    effective = effective_slide_prompt_fields(
        slide,
        prompt,
        shared_negative=negative,
    )
    prompt_bytes: list[dict[str, str]] = []
    for output_format in formats:
        compiled = compile_image_prompt(
            slide_number=int(slide["slide"]),
            slide_count=slide_count,
            # slides.json is the exact-copy authority. A stale prompt-pack text
            # field therefore invalidates only this slide but can never leak
            # old copy into a freshly compiled prompt.
            slide_copy=str(slide.get("copy") or ""),
            visual=effective["scene"],
            format_key=output_format,
            style=style,
            negative=effective["negative_prompt"],
            pose=effective["pose"],
            wardrobe=effective["wardrobe"],
            props=effective["props"],
            background=effective["background"],
            emotion=effective["emotion"],
        ).encode("utf-8")
        prompt_bytes.append(
            {
                "format": output_format,
                "sha256": sha256_binding(compiled),
            }
        )
    return canonical_fingerprint(
        {
            "compiler_version": PROMPT_COMPILER_VERSION,
            "compiled_prompts": prompt_bytes,
        }
    )


def build_generation_inputs(package_dir: Path) -> dict[str, Any]:
    """Build the canonical current input snapshot for every slide."""

    package_dir = Path(package_dir).expanduser()
    slides_payload = _read_json(package_dir / "slides.json")
    prompt_pack = _read_json(package_dir / "prompt-pack.json")
    creative_context = _read_json(package_dir / "creative-context.json")
    if not isinstance(slides_payload, list) or not slides_payload:
        raise ValueError("slides.json must contain at least one slide.")
    if not isinstance(prompt_pack, dict):
        raise ValueError("prompt-pack.json must contain a JSON object.")
    if not isinstance(creative_context, dict):
        raise ValueError("creative-context.json must contain a JSON object.")
    prompt_records = prompt_pack.get("slides")
    if not isinstance(prompt_records, list):
        raise ValueError("prompt-pack.json must contain slide prompts.")

    slides = [item for item in slides_payload if isinstance(item, dict)]
    numbers = [int(item.get("slide", 0) or 0) for item in slides]
    if numbers != list(range(1, len(slides) + 1)):
        raise ValueError("slides.json slide numbers must be unique and sequential from 1.")
    prompt_by_number = {
        int(item.get("slide", 0) or 0): item
        for item in prompt_records
        if isinstance(item, dict)
    }
    if set(prompt_by_number) != set(numbers):
        raise ValueError("prompt-pack.json must contain exactly one prompt per slide.")

    formats = tuple(locked_formats(package_dir))
    format_sha256 = locked_format_contract_fingerprint(package_dir)
    shared_reference_bindings = _shared_reference_bindings(
        package_dir,
        prompt_pack,
        creative_context,
    )
    shared = {
        "compiler_version": PROMPT_COMPILER_VERSION,
        "brand_contract_version": BRAND_CONTRACT_VERSION,
        "brandmark": str(prompt_pack.get("brandmark") or "@a.storyof.two"),
        "brandmark_placement": "top-right",
        "style_prompt": str(prompt_pack.get("style_prompt") or ""),
        "shared_negative_prompt": str(prompt_pack.get("negative_prompt") or ""),
        "reference_binding_schema_version": REFERENCE_BINDING_SCHEMA_VERSION,
        "shared_references": shared_reference_bindings,
        "formats": list(formats),
        "format_sha256": format_sha256,
        "slide_order": numbers,
    }
    shared_sha256 = canonical_fingerprint(shared)
    result_slides: dict[str, dict[str, str]] = {}
    style = str(
        prompt_pack.get("style_prompt")
        or "warm ivory paper, watercolor and loose ink"
    )
    negative = str(prompt_pack.get("negative_prompt") or "")
    for slide in slides:
        number = int(slide["slide"])
        prompt = prompt_by_number[number]
        source_sha256 = canonical_fingerprint(_slide_source(slide, prompt))
        prompt_sha256 = _compiled_prompt_fingerprint(
            slide=slide,
            prompt=prompt,
            slide_count=len(slides),
            formats=formats,
            style=style,
            negative=negative,
        )
        story_bindings = _reference_bindings(
            package_dir,
            list(slide.get("source_images") or []),
            role="story",
        )
        references_sha256 = canonical_fingerprint(
            {
                "schema_version": REFERENCE_BINDING_SCHEMA_VERSION,
                "shared": shared_reference_bindings,
                "story": story_bindings,
            }
        )
        input_sha256 = canonical_fingerprint(
            {
                "source_sha256": source_sha256,
                "prompt_sha256": prompt_sha256,
                "references_sha256": references_sha256,
                "shared_sha256": shared_sha256,
            }
        )
        result_slides[str(number)] = {
            "source_sha256": source_sha256,
            "prompt_sha256": prompt_sha256,
            "references_sha256": references_sha256,
            "input_sha256": input_sha256,
        }

    return {
        "schema_version": INPUT_SCHEMA_VERSION,
        "selected_formats": list(formats),
        "format_sha256": format_sha256,
        "shared_sha256": shared_sha256,
        "slides": result_slides,
    }


__all__ = [
    "BRAND_CONTRACT_VERSION",
    "INPUT_SCHEMA_VERSION",
    "PROMPT_COMPILER_VERSION",
    "build_generation_inputs",
    "canonical_fingerprint",
    "canonical_json_bytes",
    "sha256_binding",
]
