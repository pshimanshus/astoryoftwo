"""Single local builder for the @a.storyof.two carousel hot path.

This module creates the copy/format/prompt contract. It does not pretend that
planning artifacts are visual proof and it does not run an agent room. Real
image generation, pixel QA, creator proof approval, and final promotion happen
in :mod:`codex_builtin_image_generation`.
"""

from __future__ import annotations

import json
from datetime import date
from pathlib import Path
from typing import Any

from pipeline.stages.c1_illustration_carousel import (
    DEFAULT_SLIDE_COUNT,
    normalize_image_paths,
    slugify_title,
    validate_slide_count,
)
from pipeline.stages.carousel_contract import load_style_contract
from pipeline.stages.carousel_lanes import (
    build_identity_reference_selection,
    build_slides,
    discover_identity_images,
    infer_title,
    infer_workspace_root,
    select_identity_reference_bundle,
)
from pipeline.stages.carousel_package_writer import (
    build_manifest,
    try_render_assets,
    write_package,
)
from pipeline.stages.carousel_visual_storytelling import physical_action_issue


def load_creative_baseline(path: str | Path | None) -> dict[str, Any] | None:
    if not path:
        return None
    baseline_path = Path(path).expanduser()
    if not baseline_path.is_file():
        raise FileNotFoundError(f"Creative brief not found: {baseline_path}")
    payload = json.loads(baseline_path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("Creative brief must be a JSON object.")
    return payload


def build_local_creative_baseline_record(
    *,
    story: str,
    title: str,
    slides: list[dict[str, Any]],
    style_brief: str | None,
) -> dict[str, Any]:
    return {
        "schema_version": "carousel-creative-brief/v2",
        "source": "creator_or_local_draft",
        "title": title,
        "story": story,
        "style_brief": style_brief or "",
        "slides": [
            {
                "slide": int(slide["slide"]),
                "copy": str(slide["copy"]),
                "visual": str(slide["visual"]),
            }
            for slide in slides
        ],
    }


def slides_from_creative_baseline(
    baseline: dict[str, Any] | None,
    image_paths: list[Path],
) -> list[dict[str, Any]] | None:
    if not baseline:
        return None
    raw_slides = baseline.get("slides")
    if not isinstance(raw_slides, list) or not raw_slides:
        return None
    slides: list[dict[str, Any]] = []
    for index, item in enumerate(raw_slides, start=1):
        if not isinstance(item, dict):
            raise ValueError(f"Creative brief slide {index} must be an object.")
        copy = str(item.get("copy") or item.get("text") or "")
        visual = str(
            item.get("visual")
            or item.get("physical_action")
            or item.get("scene")
            or ""
        )
        if not copy or not visual:
            raise ValueError(
                f"Creative brief slide {index} needs exact copy and a visible physical action."
            )
        action_issue = physical_action_issue(
            item.get("physical_action") or visual,
            copy=copy,
        )
        if action_issue:
            raise ValueError(f"Creative brief slide {index} {action_issue}.")
        slide = {
            "slide": index,
            "role": str(item.get("role") or "story_beat"),
            "copy": copy,
            "visual": visual,
            "physical_action": str(item.get("physical_action") or visual),
            "relationship_state": str(item.get("relationship_state") or ""),
            "emotion": str(item.get("emotion") or ""),
            "camera": str(item.get("camera") or ""),
            "focal_hierarchy": str(item.get("focal_hierarchy") or ""),
            "setting": str(item.get("setting") or ""),
            "source_images": [str(path) for path in image_paths],
        }
        slides.append(slide)
    return slides


def _slide_prompt(
    slide: dict[str, Any],
    *,
    style_prompt: str,
    identity_images: list[Path],
) -> dict[str, Any]:
    scene = str(slide.get("physical_action") or slide["visual"])
    camera = str(slide.get("camera") or "clear observational medium-wide framing")
    focal = str(slide.get("focal_hierarchy") or "the couple's physical action reads first")
    prompt = "\n".join(
        (
            f"SCENE: {scene}",
            f"CAMERA: {camera}. FOCAL ORDER: {focal}.",
            "IDENTITY: Render Aachu and Zuv as the same whole people shown in the attached "
            "identity references; preserve faces, hair, proportions, posture, wardrobe, and accessories.",
            f"STYLE: {style_prompt}",
            f"TEXT: Render exactly: {slide['copy']}",
            "BRANDMARK: Render the tiny low-contrast @a.storyof.two at top-right.",
            "HARD FAILS: no extra people or limbs, malformed hands, contradictory action, "
            "illegible or invented text, photorealism, 3D, glossy vector art, collage, or quote card.",
        )
    )
    return {
        "slide": int(slide["slide"]),
        "text": str(slide["copy"]),
        "scene": scene,
        "prompt": prompt,
        "negative_prompt": (
            "extra people, extra arms, duplicated hands, malformed fingers, impossible contact, "
            "wrong identity, wrong wardrobe, invented text, misspelling, missing brandmark"
        ),
        "identity_reference_images": [str(path) for path in identity_images],
    }


def build_package(
    *,
    story: str,
    image_paths: list[Path],
    identity_image_paths: list[Path],
    identity_reference_selection: dict[str, Any],
    identity_dossier: dict[str, Any],
    title: str,
    slide_count: int,
    style_brief: str | None,
    layer_e_decision: Any | None = None,
    creative_baseline: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Create one human-readable slide plan and its compact prompt pack."""

    del layer_e_decision  # Historical compatibility; no default scoring layer.
    contract = load_style_contract()
    slides = slides_from_creative_baseline(creative_baseline, image_paths)
    if slides is None:
        slides = build_slides(story, image_paths, slide_count)
    for slide in slides:
        slide.setdefault("physical_action", str(slide.get("visual") or ""))
        slide.setdefault("relationship_state", str(slide.get("emotion") or ""))
    style_prompt = str(
        style_brief
        or contract.get("compact_style_prompt")
        or contract.get("shared_style_prompt")
        or "warm ivory paper, watercolor and loose ink, intimate lived-in scene"
    )
    style_reference_limit = int(contract.get("style_reference_attachment_limit", 3))
    style_references = [
        str(path)
        for value in contract.get("style_references", [])
        if (path := Path(str(value))).is_file()
    ][:style_reference_limit]
    prompts = [
        _slide_prompt(slide, style_prompt=style_prompt, identity_images=identity_image_paths)
        for slide in slides
    ]
    return {
        "creative_context": build_local_creative_baseline_record(
            story=story,
            title=title,
            slides=slides,
            style_brief=style_brief,
        ),
        "slides": slides,
        "prompt_pack": {
            "schema_version": "carousel-prompt-pack/v2",
            "generation_mode": "model_native_publishable",
            "brandmark": "@a.storyof.two",
            "style_prompt": style_prompt,
            "shared_negative_prompt": (
                "extra people, extra limbs, malformed hands, wrong identity, wrong wardrobe, "
                "invented copy, missing brandmark, photorealism, 3D, glossy vector, collage"
            ),
            "style_reference_images": style_references,
            "identity_reference_images": [str(path) for path in identity_image_paths],
            "identity_dossier_reference_images": [],
            "slides": prompts,
        },
        "identity_reference_selection": identity_reference_selection,
        "identity_dossier": identity_dossier,
    }


def create_codex_native_carousel(
    *,
    story: str,
    image_paths: list[str | Path],
    identity_image_paths: list[str | Path] | None = None,
    title: str | None = None,
    slide_count: int = DEFAULT_SLIDE_COUNT,
    style_brief: str | None = None,
    output_root: Path = Path("output") / "carousels",
    render_assets: bool = False,
    today: date | None = None,
    creative_baseline_path: str | Path | None = None,
    requested_formats: list[str] | None = None,
) -> Path:
    if not story.strip():
        raise ValueError("Story is required.")
    creative_baseline = load_creative_baseline(creative_baseline_path)
    if creative_baseline and isinstance(creative_baseline.get("slides"), list):
        slide_count = len(creative_baseline["slides"])
    validate_slide_count(slide_count)
    today = today or date.today()
    output_root = Path(output_root)
    workspace_root = infer_workspace_root(output_root)

    story_paths = normalize_image_paths(image_paths)
    explicit_identity = identity_image_paths is not None
    identity_candidates = (
        normalize_image_paths(identity_image_paths or [])
        if explicit_identity
        else discover_identity_images(workspace_root)
    )
    identity_paths = select_identity_reference_bundle(
        identity_candidates,
        explicit=explicit_identity,
    )
    selection = build_identity_reference_selection(
        candidate_paths=identity_candidates,
        selected_paths=identity_paths,
        explicit=explicit_identity,
    )

    final_title = infer_title(story, title)
    dated_root = output_root / str(today)
    out_dir = dated_root / slugify_title(final_title)
    suffix = 2
    while out_dir.exists():
        out_dir = dated_root / f"{slugify_title(final_title)}-{suffix}"
        suffix += 1

    package = build_package(
        story=story,
        image_paths=story_paths,
        identity_image_paths=identity_paths,
        identity_reference_selection=selection,
        identity_dossier={"status": "not_required", "path": None},
        title=final_title,
        slide_count=slide_count,
        style_brief=style_brief,
        creative_baseline=creative_baseline,
    )
    context = build_manifest(
        title=final_title,
        slug=out_dir.name,
        story=story,
        image_paths=story_paths,
        identity_image_paths=identity_paths,
        identity_reference_selection=selection,
        identity_dossier={"status": "not_required", "path": None},
        slide_count=len(package["slides"]),
        today=today,
        requested_formats=requested_formats,
    )
    context["style_brief"] = style_brief or ""
    context["identity_reference_status"] = (
        "attached" if identity_paths else "explicitly_unavailable"
    )
    write_package(out_dir, context, package)

    if render_assets:
        # Kept as an explicit compatibility no-op. It never creates final art.
        try_render_assets(out_dir, package["slides"])
    return out_dir


__all__ = [
    "build_local_creative_baseline_record",
    "build_manifest",
    "build_package",
    "create_codex_native_carousel",
    "load_creative_baseline",
    "slides_from_creative_baseline",
    "try_render_assets",
]
