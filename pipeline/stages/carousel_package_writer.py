"""Small, deterministic writer for carousel work-in-progress packages.

The package is intentionally boring. Creative context, exact slide copy, the
format lock, and compact prompts are the only inputs needed before pixels
exist. Generation state and QA artifacts are written later by the image
handoff. Historical review rooms, scorecards, ledgers, and agent transcripts
do not belong in the default package.
"""

from __future__ import annotations

from copy import deepcopy
import hashlib
import json
import shutil
from datetime import date
from pathlib import Path
from typing import Any

from pipeline.stages.carousel_format_contract import (
    build_format_contract,
    write_format_contract,
)


HOT_PATH_ARTIFACTS = (
    "creative-context.json",
    "format-contract.json",
    "slides.json",
    "prompt-pack.json",
)


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


def _paths(items: list[Path], role: str) -> list[dict[str, str]]:
    return [{"path": str(path), "role": role} for path in items]


def _materialize_reference(
    out_dir: Path,
    raw_path: str | Path,
    *,
    category: str,
    cache: dict[tuple[str, str], str],
) -> str:
    """Copy a selected reference into the package and return its relative path."""

    source = Path(raw_path).expanduser()
    if not source.is_absolute():
        source = source.resolve()
    if not source.is_file():
        raise FileNotFoundError(f"Missing selected {category} reference: {source}")
    key = (str(source), category)
    if key in cache:
        return cache[key]
    digest = hashlib.sha256(source.read_bytes()).hexdigest()[:20]
    suffix = source.suffix.lower() or ".bin"
    relative = Path(".internal") / "references" / category / f"{digest}{suffix}"
    destination = out_dir / relative
    destination.parent.mkdir(parents=True, exist_ok=True)
    if not destination.exists():
        shutil.copy2(source, destination)
    value = relative.as_posix()
    cache[key] = value
    return value


def _localize_path_list(
    out_dir: Path,
    values: Any,
    *,
    category: str,
    cache: dict[tuple[str, str], str],
) -> list[str]:
    if not isinstance(values, list):
        return []
    return [
        _materialize_reference(out_dir, value, category=category, cache=cache)
        for value in values
        if str(value).strip()
    ]


def _localize_path_records(
    out_dir: Path,
    records: Any,
    *,
    category: str,
    cache: dict[tuple[str, str], str],
) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    for record in records if isinstance(records, list) else []:
        if not isinstance(record, dict) or not str(record.get("path") or "").strip():
            continue
        current = dict(record)
        current["path"] = _materialize_reference(
            out_dir,
            current["path"],
            category=category,
            cache=cache,
        )
        result.append(current)
    return result


def build_manifest(
    *,
    title: str,
    slug: str,
    story: str,
    image_paths: list[Path],
    identity_image_paths: list[Path],
    identity_reference_selection: dict[str, Any],
    identity_dossier: dict[str, Any],
    slide_count: int,
    today: date,
    requested_formats: list[str] | tuple[str, ...] | None = None,
) -> dict[str, Any]:
    """Build the creative-context payload (legacy function name retained)."""

    format_contract = build_format_contract(
        requested_formats,
        source=("creator_request" if requested_formats is not None else "instagram_post_default"),
    )
    return {
        "schema_version": "carousel-creative-context/v2",
        "date": str(today),
        "slug": slug,
        "title": title,
        "channel": "@a.storyof.two",
        "source_story": story,
        "slide_count": slide_count,
        "status": "copy_and_format_locked",
        "requested_formats": list(format_contract["requested_formats"]),
        "format_contract": format_contract,
        "reference_images": _paths(image_paths, "current story reference"),
        "identity_references": _paths(
            identity_image_paths,
            "Aachu/Zuv identity and wardrobe reference",
        ),
        "identity_reference_selection": identity_reference_selection,
        "identity_dossier": {
            "path": identity_dossier.get("path"),
            "preflight_path": identity_dossier.get("preflight_path"),
            "contact_sheet_path": identity_dossier.get("contact_sheet_path"),
            "status": identity_dossier.get("status"),
        },
        "artifacts": list(HOT_PATH_ARTIFACTS),
    }


def _minimal_slide(slide: dict[str, Any]) -> dict[str, Any]:
    """Keep scene evidence and exact copy; discard internal scoring debris."""

    keep = (
        "slide",
        "role",
        "copy",
        "visual",
        "emotion",
        "physical_action",
        "relationship_state",
        "camera",
        "focal_hierarchy",
        "setting",
        "composition",
        "wardrobe",
        "pose",
        "props",
        "background",
        "source_images",
        "continuity_lock",
        "negative_prompt",
        "needs_physical_action",
    )
    result = {key: slide[key] for key in keep if key in slide and slide[key] not in (None, "", [])}
    if not isinstance(result.get("slide"), int):
        result["slide"] = int(slide.get("slide", 0) or 0)
    result["copy"] = str(slide.get("copy") or "")
    result["visual"] = str(slide.get("visual") or slide.get("physical_action") or "")
    return result


def _minimal_prompt_pack(prompt_pack: dict[str, Any], slides: list[dict[str, Any]]) -> dict[str, Any]:
    """Strip embedded upstream artifacts while preserving generator inputs."""

    prompts = prompt_pack.get("slides")
    if not isinstance(prompts, list):
        prompts = []
    minimal_prompts: list[dict[str, Any]] = []
    slide_copy = {int(slide["slide"]): slide["copy"] for slide in slides}
    for prompt in prompts:
        if not isinstance(prompt, dict):
            continue
        number = int(prompt.get("slide", 0) or 0)
        if number not in slide_copy:
            continue
        record = {
            "slide": number,
            "text": slide_copy[number],
            "scene": str(prompt.get("scene") or prompt.get("visual") or ""),
            "prompt": str(prompt.get("prompt") or ""),
        }
        minimal_prompts.append(record)
    return {
        "schema_version": "carousel-prompt-pack/v2",
        "generation_mode": "model_native_publishable",
        "brandmark": "@a.storyof.two",
        "style_prompt": str(
            prompt_pack.get("style_prompt")
            or prompt_pack.get("shared_style_prompt")
            or ""
        ),
        "negative_prompt": str(prompt_pack.get("shared_negative_prompt") or ""),
        "style_reference_images": list(prompt_pack.get("style_reference_images") or []),
        "identity_reference_images": list(prompt_pack.get("identity_reference_images") or []),
        "identity_dossier_reference_images": list(
            prompt_pack.get("identity_dossier_reference_images") or []
        ),
        "slides": minimal_prompts,
    }


def write_package(out_dir: Path, manifest: dict[str, Any], package: dict[str, Any]) -> None:
    """Write only the pre-proof hot-path contract."""

    out_dir.mkdir(parents=True, exist_ok=True)
    contract = manifest.get("format_contract") if isinstance(manifest, dict) else None
    requested = contract.get("requested_formats") if isinstance(contract, dict) else None
    source = str(contract.get("source") or "package") if isinstance(contract, dict) else "package"
    write_format_contract(out_dir, requested, source=source, replace=True)

    cache: dict[tuple[str, str], str] = {}
    creative_context = deepcopy(manifest)
    creative_context["reference_images"] = _localize_path_records(
        out_dir,
        creative_context.get("reference_images"),
        category="story",
        cache=cache,
    )
    creative_context["identity_references"] = _localize_path_records(
        out_dir,
        creative_context.get("identity_references"),
        category="identity",
        cache=cache,
    )
    selection = creative_context.get("identity_reference_selection")
    if isinstance(selection, dict):
        selection["selected_references"] = _localize_path_records(
            out_dir,
            selection.get("selected_references"),
            category="identity",
            cache=cache,
        )
    creative_context.pop("format_contract", None)
    write_json(out_dir / "creative-context.json", creative_context)

    slides = [_minimal_slide(slide) for slide in package.get("slides", [])]
    for slide in slides:
        slide["source_images"] = _localize_path_list(
            out_dir,
            slide.get("source_images"),
            category="story",
            cache=cache,
        )
        if not slide["source_images"]:
            slide.pop("source_images", None)
    if not slides or any(not slide.get("copy") or not slide.get("visual") for slide in slides):
        raise ValueError("Every carousel slide needs exact copy and one visible physical scene.")
    write_json(out_dir / "slides.json", slides)
    prompt_pack = deepcopy(package.get("prompt_pack", {}))
    prompt_pack["style_reference_images"] = _localize_path_list(
        out_dir,
        prompt_pack.get("style_reference_images"),
        category="style",
        cache=cache,
    )
    prompt_pack["identity_reference_images"] = _localize_path_list(
        out_dir,
        prompt_pack.get("identity_reference_images"),
        category="identity",
        cache=cache,
    )
    prompt_pack["identity_dossier_reference_images"] = _localize_path_list(
        out_dir,
        prompt_pack.get("identity_dossier_reference_images"),
        category="identity-dossier",
        cache=cache,
    )
    write_json(
        out_dir / "prompt-pack.json",
        _minimal_prompt_pack(prompt_pack, slides),
    )

    # Import at the write boundary so the package writer remains independent of
    # the image lifecycle module during module import. Every new package starts
    # with the canonical compact v3 state; legacy v2 is read-only.
    from pipeline.stages.codex_builtin_image_generation import initialize_generation_state

    initialize_generation_state(out_dir)
