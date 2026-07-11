"""Deterministic local carousel image backend for fast dry-run checks.

This backend is intentionally not publishable final art. It exists so tests and
preview flows can verify native output plumbing without calling an image model.
"""

from __future__ import annotations

import hashlib
import json
from datetime import date
from pathlib import Path
from typing import Any

BACKEND = "local_dry_run"
GENERATION_MODE = "local_dry_run_not_publishable"
STATUS = "dry_run_generated"
INSTAGRAM_POST_SIZE = (1080, 1440)
REELS_STORIES_SIZE = (1080, 1920)


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


def image_deps() -> tuple[Any, Any]:
    try:
        import cv2
        import numpy as np
    except ImportError as exc:
        raise RuntimeError(
            "local_dry_run image backend requires optional dependencies cv2 and numpy. "
            "Install opencv-python and numpy, or use --image-backend codex-built-in."
        ) from exc
    return cv2, np


def write_png(path: Path, *, size: tuple[int, int], slide_number: int, copy: str, format_label: str) -> None:
    cv2, np = image_deps()
    width, height = size
    digest = hashlib.sha256(f"{slide_number}:{copy}:{format_label}".encode("utf-8")).digest()
    base = np.array([digest[0], digest[1], digest[2]], dtype=np.uint8)
    accent = np.array([digest[3], digest[4], digest[5]], dtype=np.uint8)

    y = np.linspace(0, 1, height, dtype=np.float32)[:, None, None]
    x = np.linspace(0, 1, width, dtype=np.float32)[None, :, None]
    canvas = (base * (0.58 + 0.24 * y) + accent * (0.18 + 0.18 * x) + 38).clip(0, 255).astype(np.uint8)
    canvas = np.repeat(canvas, 3, axis=1) if canvas.shape[1] == 1 else canvas

    cv2.rectangle(canvas, (48, 48), (width - 48, height - 48), (245, 241, 229), 8)
    cv2.putText(
        canvas,
        f"LOCAL DRY RUN - {format_label}",
        (72, 132),
        cv2.FONT_HERSHEY_SIMPLEX,
        1.15,
        (36, 35, 32),
        3,
        cv2.LINE_AA,
    )
    cv2.putText(
        canvas,
        f"Slide {slide_number:02d}",
        (72, 205),
        cv2.FONT_HERSHEY_SIMPLEX,
        1.6,
        (36, 35, 32),
        4,
        cv2.LINE_AA,
    )
    for index, line in enumerate(copy.replace("\n", " / ").split(" ")[:14]):
        cv2.putText(
            canvas,
            line[:26],
            (72, 300 + index * 50),
            cv2.FONT_HERSHEY_SIMPLEX,
            1.0,
            (36, 35, 32),
            2,
            cv2.LINE_AA,
        )

    path.parent.mkdir(parents=True, exist_ok=True)
    ok = cv2.imwrite(str(path), canvas)
    if not ok:
        raise RuntimeError(f"Failed to write dry-run image: {path}")


def slide_copy(slide: dict[str, Any]) -> str:
    return str(slide.get("text") or slide.get("copy") or slide.get("slide_copy") or "")


def slide_prompt(slide: dict[str, Any]) -> str:
    return str(slide.get("prompt") or slide.get("generation_prompt") or "")


def selected_option_ids(prompt_pack: dict[str, Any]) -> list[str]:
    option_ids = [
        str(item.get("option_id"))
        for item in prompt_pack.get("identity_selected_options", [])
        if isinstance(item, dict) and item.get("option_id")
    ]
    return option_ids or ["LOCAL_DRY_RUN"]


def write_visual_qa_json(carousel_dir: Path, prompt_pack: dict[str, Any], records: list[dict[str, Any]]) -> None:
    option_ids = selected_option_ids(prompt_pack)
    final_file_evidence = [
        {
            "slide": record["slide"],
            "instagram_post": record["file"],
            "reels_stories": record["reels_stories_file"],
        }
        for record in records
    ]
    write_json(
        carousel_dir / "visual-qa.json",
        {
            "schema_version": "1.0",
            "status": "NEEDS_FIXES",
            "generation_mode": GENERATION_MODE,
            "backend": BACKEND,
            "publishable": False,
            "can_satisfy_final_gate": False,
            "slide_count": len(records),
            "checks": {
                "storyboard": {
                    "pass": False,
                    "evidence": final_file_evidence,
                    "notes": "Dry-run images verify file plumbing only; they do not prove final storyboard art quality.",
                },
                "aachu_face": {
                    "pass": False,
                    "reference_option_ids": option_ids,
                    "likeness_notes": "Dry-run placeholder cannot verify Aachu face likeness.",
                },
                "zuv_face": {
                    "pass": False,
                    "reference_option_ids": option_ids,
                    "likeness_notes": "Dry-run placeholder cannot verify Zuv face likeness.",
                },
                "dress_continuity": {
                    "pass": False,
                    "evidence": "Dry-run placeholder cannot verify wardrobe continuity.",
                },
                "style": {
                    "pass": False,
                    "evidence": "Dry-run placeholder cannot verify watercolor-and-ink final style.",
                },
                "scene_logic": {
                    "pass": False,
                    "evidence": "Dry-run placeholder cannot verify whether visible clothes, props, and body action prove the exact copy.",
                },
                "pose_anatomy": {
                    "pass": False,
                    "evidence": "Dry-run placeholder cannot verify natural flattering Aachu/Zuv pose anatomy.",
                },
                "integrated_final_text": {
                    "pass": False,
                    "evidence": "Dry-run placeholder includes text only for plumbing; it is not integrated final-image typography.",
                },
                "final_files": {
                    "pass": False,
                    "evidence": final_file_evidence,
                    "notes": "Files exist in both native sizes, but are non-publishable dry-run placeholders.",
                },
            },
        },
    )


def infer_workspace_root_from_carousel_dir(carousel_dir: Path) -> Path:
    resolved = carousel_dir.expanduser().resolve()
    for candidate in [resolved, *resolved.parents]:
        if (candidate / "AGENTS.md").exists() or (candidate / "config" / "carousel_style_contract.json").exists():
            return candidate

    date_dir = resolved.parent
    if (
        len(date_dir.name) == 10
        and date_dir.name[4] == "-"
        and date_dir.name[7] == "-"
        and date_dir.parent != date_dir
    ):
        return date_dir.parent

    for parent in resolved.parents:
        if parent.name == "out":
            return parent.parent
        if parent.name == "carousels" and parent.parent.name == "output":
            return parent.parent.parent

    return resolved.parent if resolved.parent != resolved else Path.cwd()


def refresh_quality_artifacts(carousel_dir: Path, prompt_pack: dict[str, Any], result: dict[str, Any]) -> None:
    from pipeline.stages.carousel_quality import QualityContext, write_quality_artifacts

    manifest = load_json(carousel_dir / "manifest.json")
    package = {
        "concept": load_json(carousel_dir / "concept.json"),
        "post_copy_visual_room": load_json(carousel_dir / "post-copy-visual-room.json"),
        "visual_debate": load_json(carousel_dir / "visual-debate.json"),
        "visual_plan_quality": load_json(carousel_dir / "visual-plan-quality.json"),
        "slides": load_json(carousel_dir / "slides.json"),
        "prompt_pack": prompt_pack,
        "identity_consistency_review": load_json(carousel_dir / "identity-consistency-review.json"),
        "copy": load_json(carousel_dir / "copy.json"),
        "review": load_json(carousel_dir / "review.json"),
    }
    write_quality_artifacts(
        QualityContext(
            story=manifest["source_story"],
            title=manifest["title"],
            slug=manifest["slug"],
            today=date.fromisoformat(str(manifest["date"])),
            out_dir=carousel_dir,
            image_paths=[
                Path(item["path"])
                for item in manifest.get("reference_images", [])
                if isinstance(item, dict) and item.get("path")
            ],
            slide_count=len(prompt_pack.get("slides") or []),
            package=package,
            manifest=manifest,
            render_result=result,
            workspace_root=infer_workspace_root_from_carousel_dir(carousel_dir),
        )
    )


def generate_local_dry_run_images(carousel_dir: Path) -> dict[str, Any]:
    carousel_dir = carousel_dir.expanduser()
    prompt_pack_path = carousel_dir / "prompt-pack.json"
    prompt_pack = load_json(prompt_pack_path)
    slides = prompt_pack.get("slides") or []
    if not slides:
        raise ValueError("prompt-pack.json does not include slide prompts.")

    records: list[dict[str, Any]] = []
    for fallback_number, slide in enumerate(slides, start=1):
        number = int(slide.get("slide") or fallback_number)
        copy = slide_copy(slide)
        prompt = slide_prompt(slide)
        instagram_path = carousel_dir / "final" / f"slide-{number:02d}.png"
        reels_path = carousel_dir / "final-reels-stories" / f"slide-{number:02d}.png"

        write_png(
            instagram_path,
            size=INSTAGRAM_POST_SIZE,
            slide_number=number,
            copy=copy,
            format_label="instagram_post 3:4",
        )
        write_png(
            reels_path,
            size=REELS_STORIES_SIZE,
            slide_number=number,
            copy=copy,
            format_label="reels_stories 9:16",
        )
        records.append(
            {
                "slide": number,
                "file": str(instagram_path),
                "reels_stories_file": str(reels_path),
                "copy": copy,
                "prompt": prompt,
                "status": STATUS,
                "backend": BACKEND,
                "generation_mode": GENERATION_MODE,
                "publishable": False,
                "source_backend": "prompt-pack.json",
                "source_prompt_pack": str(prompt_pack_path),
                "source_slide": number,
                "source_prompt": prompt,
                "provenance": {
                    "backend": BACKEND,
                    "source": str(prompt_pack_path),
                    "note": "Deterministic local dry-run placeholder; not publishable final art.",
                },
                "native_outputs": {
                    "instagram_post": {
                        "file": str(instagram_path),
                        "size": f"{INSTAGRAM_POST_SIZE[0]}x{INSTAGRAM_POST_SIZE[1]}",
                        "publishable": False,
                    },
                    "reels_stories": {
                        "file": str(reels_path),
                        "size": f"{REELS_STORIES_SIZE[0]}x{REELS_STORIES_SIZE[1]}",
                        "publishable": False,
                    },
                },
            }
        )

    result: dict[str, Any] = {
        "status": STATUS,
        "backend": BACKEND,
        "generation_mode": GENERATION_MODE,
        "slide_count": len(slides),
        "done": False,
        "requires_human_generation": False,
        "publishable": False,
        "reason": (
            "Deterministic local dry-run images were created for flow tests/previews only; "
            "they are not publish-ready final art."
        ),
        "native_output_contract": {
            "formats": ["instagram_post", "reels_stories"],
            "instagram_post": f"{INSTAGRAM_POST_SIZE[0]}x{INSTAGRAM_POST_SIZE[1]}",
            "reels_stories": f"{REELS_STORIES_SIZE[0]}x{REELS_STORIES_SIZE[1]}",
        },
        "source_prompt_pack": str(prompt_pack_path),
        "provenance": {
            "backend": BACKEND,
            "source": str(prompt_pack_path),
            "note": "Dry-run output is deterministic and non-publishable.",
        },
        "slides": records,
    }
    write_json(carousel_dir / "image-generation.json", result)
    write_json(carousel_dir / "final-images.json", result)
    write_visual_qa_json(carousel_dir, prompt_pack, records)
    refresh_quality_artifacts(carousel_dir, prompt_pack, result)
    return result
