"""Deterministic local carousel image backend for fast dry-run checks.

This backend is intentionally not publishable final art. It exists so tests and
preview flows can verify native output plumbing without calling an image model.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

BACKEND = "local_dry_run"
GENERATION_MODE = "local_dry_run_not_publishable"
STATUS = "dry_run_generated"
INSTAGRAM_POST_SIZE = (1080, 1350)
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
            format_label="instagram_post 4:5",
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
    return result
