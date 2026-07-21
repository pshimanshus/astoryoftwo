from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from pipeline.stages.carousel_format_contract import (
    FORMAT_SPECS,
    INSTAGRAM_POST_FORMAT,
    REELS_STORIES_FORMAT,
    SQUARE_FORMAT,
    native_output_contract,
)


DEFAULT_MODEL = "disabled-legacy-api-model"
DEFAULT_SIZE = "1440x1920"
REELS_STORIES_REQUEST_SIZE = "1080x1920"
SQUARE_REQUEST_SIZE = "1080x1080"
INSTAGRAM_POST_SOURCE_SIZE = (1440, 1920)
FINAL_UPLOAD_SIZE = (1080, 1440)
REELS_STORIES_SIZE = (1080, 1920)
SQUARE_SIZE = (1080, 1080)
MAX_REFERENCE_IMAGES = 16
MAX_IDENTITY_REFERENCES_WITH_STYLE = 4
MAX_STYLE_REFERENCES_WITH_IDENTITY = 2
NATIVE_OUTPUT_FORMAT_ORDER = [INSTAGRAM_POST_FORMAT, REELS_STORIES_FORMAT, SQUARE_FORMAT]
# Compatibility export only. Runtime code must build a contract from the package's
# locked current-request formats instead of treating this post-only default as global.
NATIVE_OUTPUT_CONTRACT = native_output_contract()
LEGACY_API_IMAGE_GENERATION_DISABLED_REASON = (
    "Legacy API carousel image generation is disabled for @a.storyof.two. "
    "Use the Codex built-in identity-reference handoff instead: "
    "scripts/create_illustration_carousel.py --generate-images --image-backend codex-built-in."
)
NATIVE_OUTPUT_FORMATS = {
    INSTAGRAM_POST_FORMAT: {
        "label": "Instagram post",
        "aspect_ratio": "3:4",
        "upload_size": f"{FINAL_UPLOAD_SIZE[0]}x{FINAL_UPLOAD_SIZE[1]}",
        "source_size": INSTAGRAM_POST_SOURCE_SIZE,
        "source_size_label": f"{INSTAGRAM_POST_SOURCE_SIZE[0]}x{INSTAGRAM_POST_SOURCE_SIZE[1]}",
        "target_size": FINAL_UPLOAD_SIZE,
        "request_size": DEFAULT_SIZE,
    },
    REELS_STORIES_FORMAT: {
        "label": "Reels/Stories",
        "aspect_ratio": "9:16",
        "upload_size": f"{REELS_STORIES_SIZE[0]}x{REELS_STORIES_SIZE[1]}",
        "source_size": REELS_STORIES_SIZE,
        "source_size_label": f"{REELS_STORIES_SIZE[0]}x{REELS_STORIES_SIZE[1]}",
        "target_size": REELS_STORIES_SIZE,
        "request_size": REELS_STORIES_REQUEST_SIZE,
    },
    SQUARE_FORMAT: {
        "label": FORMAT_SPECS[SQUARE_FORMAT]["label"],
        "aspect_ratio": FORMAT_SPECS[SQUARE_FORMAT]["aspect_ratio"],
        "upload_size": f"{SQUARE_SIZE[0]}x{SQUARE_SIZE[1]}",
        "source_size": SQUARE_SIZE,
        "source_size_label": f"{SQUARE_SIZE[0]}x{SQUARE_SIZE[1]}",
        "target_size": SQUARE_SIZE,
        "request_size": SQUARE_REQUEST_SIZE,
    },
}


def write_json(path: Path, data: Any) -> None:
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


def collect_existing_paths(raw_paths: list[Any], seen: set[str]) -> list[Path]:
    paths: list[Path] = []
    for raw_path in raw_paths:
        path = Path(str(raw_path)).expanduser()
        marker = str(path)
        if marker not in seen and path.exists():
            paths.append(path)
            seen.add(marker)
    return paths


def existing_reference_paths(prompt_pack: dict[str, Any]) -> list[Path]:
    seen: set[str] = set()
    dossier_paths = collect_existing_paths(prompt_pack.get("identity_dossier_reference_images", []), seen)
    identity_paths = collect_existing_paths(prompt_pack.get("identity_reference_images", []), seen)
    style_paths = collect_existing_paths(prompt_pack.get("style_reference_images", []), seen)

    if not identity_paths and not dossier_paths:
        return style_paths[:MAX_REFERENCE_IMAGES]

    style_budget = min(
        len(style_paths),
        MAX_STYLE_REFERENCES_WITH_IDENTITY,
        MAX_REFERENCE_IMAGES - 1,
    )
    identity_budget = min(
        len(identity_paths),
        MAX_IDENTITY_REFERENCES_WITH_STYLE,
        max(0, MAX_REFERENCE_IMAGES - style_budget - len(dossier_paths)),
    )
    return [
        *dossier_paths[:MAX_REFERENCE_IMAGES],
        *identity_paths[:identity_budget],
        *style_paths[:style_budget],
    ][:MAX_REFERENCE_IMAGES]


def prompt_for_native_format(prompt: str, format_key: str) -> str:
    if format_key == INSTAGRAM_POST_FORMAT:
        return (
            "Native output format: Instagram post. Generate a complete 3:4 vertical "
            "carousel source at 1440x1920 with all text and the tiny @a.storyof.two brandmark "
            "inside the image; the package exporter will downsample proportionally to the "
            "1080x1440 publish file. Do not rely on cropping, padding, or resizing from another "
            "aspect ratio.\n\n"
            f"{prompt}"
        )
    if format_key == REELS_STORIES_FORMAT:
        return (
            "Native output format: Reels/Stories. Generate a complete 9:16 vertical "
            "publishable story slide with all text and the tiny @a.storyof.two brandmark inside the image. "
            "Reframe the scene for the taller canvas; do not stretch, crop, or pad the Instagram post artwork.\n\n"
            f"{prompt}"
        )
    if format_key == SQUARE_FORMAT:
        return (
            "Native output format: Square. Generate a complete 1:1 publishable social "
            "slide at 1080x1080 with all text and the tiny @a.storyof.two brandmark inside "
            "the image. Compose natively for the square canvas; do not crop, stretch, or pad "
            "artwork made for another aspect ratio.\n\n"
            f"{prompt}"
        )
    raise ValueError(f"Unsupported native output format: {format_key}")


def request_size_for_native_format(format_key: str, instagram_post_request_size: str) -> str:
    if format_key == INSTAGRAM_POST_FORMAT:
        return instagram_post_request_size
    if format_key == REELS_STORIES_FORMAT:
        return REELS_STORIES_REQUEST_SIZE
    if format_key == SQUARE_FORMAT:
        return SQUARE_REQUEST_SIZE
    raise ValueError(f"Unsupported native output format: {format_key}")


def decode_png(image_bytes: bytes) -> Any:
    import cv2
    import numpy as np

    source = cv2.imdecode(np.frombuffer(image_bytes, dtype=np.uint8), cv2.IMREAD_COLOR)
    if source is None:
        raise RuntimeError("Native image bytes could not be decoded as an image.")
    return source


def normalize_native_output(image_bytes: bytes, width: int, height: int) -> bytes:
    source = decode_png(image_bytes)
    source_height, source_width = source.shape[:2]
    if (source_width, source_height) != (width, height):
        raise RuntimeError(
            "Generated image dimensions do not match the exact native target: "
            f"source={source_width}x{source_height}, target={width}x{height}."
        )
    return image_bytes


def write_blocked_status(carousel_dir: Path, reason: str) -> dict[str, Any]:
    result = {
        "status": "BLOCKED",
        "reason": reason,
        "generation_mode": "model_native_publishable",
    }
    write_json(carousel_dir / "image-generation.json", result)
    write_json(carousel_dir / "final-images.json", result)
    return result


def identity_consistency_gate_reason(carousel_dir: Path) -> str | None:
    review_path = carousel_dir / "identity-consistency-review.json"
    if not review_path.exists():
        return "identity-consistency-review.json is required before model-native image generation."
    review = json.loads(review_path.read_text(encoding="utf-8"))
    if review.get("status") != "PASS":
        issues = review.get("issues") or ["identity consistency review did not pass"]
        return "identity-consistency-review.json did not pass: " + "; ".join(str(issue) for issue in issues)
    return None


def generate_model_native_images(
    carousel_dir: Path,
    *,
    api_key: str | None = None,
    client: Any | None = None,
    model: str = DEFAULT_MODEL,
    size: str = DEFAULT_SIZE,
) -> dict[str, Any]:
    carousel_dir = carousel_dir.expanduser()
    return write_blocked_status(carousel_dir, LEGACY_API_IMAGE_GENERATION_DISABLED_REASON)
