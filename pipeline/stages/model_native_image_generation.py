from __future__ import annotations

import json
from pathlib import Path
from typing import Any


DEFAULT_MODEL = "disabled-legacy-api-model"
DEFAULT_SIZE = "1728x2160"
REELS_STORIES_REQUEST_SIZE = "1080x1920"
FINAL_UPLOAD_SIZE = (1080, 1350)
HD_MASTER_SIZE = (2160, 2700)
REELS_STORIES_SIZE = (1080, 1920)
MAX_REFERENCE_IMAGES = 16
MAX_IDENTITY_REFERENCES_WITH_STYLE = 4
MAX_STYLE_REFERENCES_WITH_IDENTITY = 2
INSTAGRAM_POST_FORMAT = "instagram_post"
REELS_STORIES_FORMAT = "reels_stories"
NATIVE_OUTPUT_FORMAT_ORDER = [INSTAGRAM_POST_FORMAT, REELS_STORIES_FORMAT]
NATIVE_OUTPUT_CONTRACT = {
    "formats": NATIVE_OUTPUT_FORMAT_ORDER,
    "workers": [
        "instagram_post_output",
        "reels_stories_output",
        "identity_visual_qa",
    ],
    "rule": (
        "Each slide must have two separate native generated sources: one 4:5 Instagram post "
        "image and one 9:16 Reels/Stories image. Reels/Stories output must never be derived "
        "by resizing, cropping, or padding the Instagram post image."
    ),
}
LEGACY_API_IMAGE_GENERATION_DISABLED_REASON = (
    "Legacy API carousel image generation is disabled for @a.storyof.two. "
    "Use the Codex built-in identity-reference handoff instead: "
    "scripts/create_illustration_carousel.py --generate-images --image-backend codex-built-in."
)
NATIVE_OUTPUT_FORMATS = {
    INSTAGRAM_POST_FORMAT: {
        "label": "Instagram post",
        "aspect_ratio": "4:5",
        "upload_size": f"{FINAL_UPLOAD_SIZE[0]}x{FINAL_UPLOAD_SIZE[1]}",
        "target_size": FINAL_UPLOAD_SIZE,
        "request_size": DEFAULT_SIZE,
    },
    REELS_STORIES_FORMAT: {
        "label": "Reels/Stories",
        "aspect_ratio": "9:16",
        "upload_size": f"{REELS_STORIES_SIZE[0]}x{REELS_STORIES_SIZE[1]}",
        "target_size": REELS_STORIES_SIZE,
        "request_size": REELS_STORIES_REQUEST_SIZE,
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
            "Native output format: Instagram post. Generate a complete 4:5 vertical "
            "publishable carousel slide with all text and the tiny @a.storyof.two brandmark inside the image. "
            "Do not rely on cropping, padding, or resizing from another aspect ratio.\n\n"
            f"{prompt}"
        )
    if format_key == REELS_STORIES_FORMAT:
        return (
            "Native output format: Reels/Stories. Generate a complete 9:16 vertical "
            "publishable story slide with all text and the tiny @a.storyof.two brandmark inside the image. "
            "Reframe the scene for the taller canvas; do not stretch, crop, or pad the Instagram post artwork.\n\n"
            f"{prompt}"
        )
    raise ValueError(f"Unsupported native output format: {format_key}")


def request_size_for_native_format(format_key: str, instagram_post_request_size: str) -> str:
    if format_key == INSTAGRAM_POST_FORMAT:
        return instagram_post_request_size
    if format_key == REELS_STORIES_FORMAT:
        return REELS_STORIES_REQUEST_SIZE
    raise ValueError(f"Unsupported native output format: {format_key}")


def decode_png(image_bytes: bytes) -> Any:
    import cv2
    import numpy as np

    source = cv2.imdecode(np.frombuffer(image_bytes, dtype=np.uint8), cv2.IMREAD_COLOR)
    if source is None:
        raise RuntimeError("Native image bytes could not be decoded as an image.")
    return source


def encode_png(image: Any) -> bytes:
    import cv2

    ok, encoded = cv2.imencode(".png", image, [cv2.IMWRITE_PNG_COMPRESSION, 3])
    if not ok:
        raise RuntimeError("Could not encode normalized carousel image.")
    return encoded.tobytes()


def cover_resize(image_bytes: bytes, width: int, height: int) -> bytes:
    import cv2

    source = decode_png(image_bytes)
    source_height, source_width = source.shape[:2]
    # Uniform scale only. Never non-uniformly stretch generated artwork to fit
    # the carousel canvas; crop is preferable to distorting people or text.
    scale = max(width / source_width, height / source_height)
    resized = cv2.resize(
        source,
        (round(source_width * scale), round(source_height * scale)),
        interpolation=cv2.INTER_LANCZOS4,
    )
    resized_height, resized_width = resized.shape[:2]
    x = max(0, (resized_width - width) // 2)
    y = max(0, (resized_height - height) // 2)
    cropped = resized[y : y + height, x : x + width]
    return encode_png(cropped)


def normalize_native_output(image_bytes: bytes, width: int, height: int) -> bytes:
    import cv2

    source = decode_png(image_bytes)
    source_height, source_width = source.shape[:2]
    source_aspect = source_width / source_height
    target_aspect = width / height
    if abs(source_aspect - target_aspect) > 0.02:
        raise RuntimeError(
            "Generated image aspect ratio does not match its native target: "
            f"source={source_width}x{source_height}, target={width}x{height}."
        )
    resized = cv2.resize(source, (width, height), interpolation=cv2.INTER_LANCZOS4)
    return encode_png(resized)


def paper_color(source: Any) -> Any:
    import cv2
    import numpy as np

    source_height, source_width = source.shape[:2]
    band = max(12, min(source_height, source_width) // 30)
    pixels = np.concatenate(
        [
            source[:band, :, :].reshape(-1, 3),
            source[-band:, :, :].reshape(-1, 3),
            source[:, :band, :].reshape(-1, 3),
            source[:, -band:, :].reshape(-1, 3),
        ]
    )
    hsv = cv2.cvtColor(pixels.reshape(-1, 1, 3), cv2.COLOR_BGR2HSV).reshape(-1, 3)
    paper_pixels = pixels[(hsv[:, 1] < 50) & (hsv[:, 2] > 185)]
    return np.median(paper_pixels if len(paper_pixels) else pixels, axis=0).astype("uint8")


def contain_on_paper(image_bytes: bytes, width: int, height: int) -> bytes:
    import cv2
    import numpy as np

    source = decode_png(image_bytes)
    source_height, source_width = source.shape[:2]
    scale = min(width / source_width, height / source_height)
    resized_width = round(source_width * scale)
    resized_height = round(source_height * scale)
    resized = cv2.resize(source, (resized_width, resized_height), interpolation=cv2.INTER_LANCZOS4)

    canvas = np.empty((height, width, 3), dtype=np.uint8)
    canvas[:, :] = paper_color(source)
    x = (width - resized_width) // 2
    y = (height - resized_height) // 2
    canvas[y : y + resized_height, x : x + resized_width] = resized
    return encode_png(canvas)


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
