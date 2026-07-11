from __future__ import annotations

import json
from pathlib import Path

import cv2
import numpy as np


SOURCE_DIR = Path("/Users/himanshusharma/.codex/generated_images/019e0dab-9c25-7be1-9cec-6dc3830ebb76")
OUT_DIR = Path("output/carousels/2026-05-09/anchal-under-the-stars-illustrated")
POST_SIZE = (1080, 1350)

SLIDES = [
    "ig_0499f896aef5e8ff0169ff6bca0ce881919bfe50d91c398061.png",
    "ig_0499f896aef5e8ff0169ff6c742e58819190a0289a64d437a9.png",
    "ig_0499f896aef5e8ff0169ff6cde36348191914e6c1d281a2dd9.png",
    "ig_0499f896aef5e8ff0169ff6d4990f08191b2b97a06a50d70bb.png",
    "ig_0499f896aef5e8ff0169ff6dbb10908191a301bdd288e42f89.png",
    "ig_0499f896aef5e8ff0169ff6e3230308191bbdf33eafad11f64.png",
    "ig_0499f896aef5e8ff0169ff6ea09e348191aeac17c13eee0b1b.png",
]

COPY = [
    "I proposed to Anchal under the stars.",
    "No crowd. No stage.",
    "Just us, the mountains,",
    "and a sky full of witnesses.",
    "She said yes.",
    "Maybe love is not finding the perfect sky.",
    "Maybe it's finding someone who makes every sky feel like forever.",
]


def read_png(path: Path) -> np.ndarray:
    image = cv2.imdecode(np.fromfile(str(path), dtype=np.uint8), cv2.IMREAD_UNCHANGED)
    if image is None:
        raise RuntimeError(f"Could not read {path}")
    if image.ndim == 2:
        image = cv2.cvtColor(image, cv2.COLOR_GRAY2BGR)
    if image.shape[2] == 4:
        alpha = image[:, :, 3:4].astype(np.float32) / 255.0
        rgb = image[:, :, :3].astype(np.float32)
        bg = np.full_like(rgb, 248)
        image = (rgb * alpha + bg * (1 - alpha)).astype(np.uint8)
    return image


def write_png(path: Path, image: np.ndarray) -> None:
    ok, data = cv2.imencode(".png", image)
    if not ok:
        raise RuntimeError(f"Could not encode {path}")
    path.write_bytes(data.tobytes())


def require_exact_size(image: np.ndarray, path: Path, size: tuple[int, int]) -> None:
    expected_w, expected_h = size
    h, w = image.shape[:2]
    if (w, h) != (expected_w, expected_h):
        raise RuntimeError(
            f"{path} is {w}x{h}; expected exact {expected_w}x{expected_h}. "
            "Regenerate natively instead of padding, cropping, or resizing."
        )


def make_preview(paths: list[Path], out_path: Path) -> None:
    thumbs = []
    for path in paths:
        image = read_png(path)
        thumbs.append(cv2.resize(image, (216, 270), interpolation=cv2.INTER_AREA))
    gap = 18
    width = len(thumbs) * 216 + (len(thumbs) + 1) * gap
    sheet = np.full((270 + gap * 2, width, 3), (244, 239, 229), dtype=np.uint8)
    x = gap
    for thumb in thumbs:
        sheet[gap : gap + 270, x : x + 216] = thumb
        x += 216 + gap
    write_png(out_path, sheet)


def main() -> None:
    source_out = OUT_DIR / "source-generated"
    ig_out = OUT_DIR / "instagram-1080x1350"
    for folder in [source_out, ig_out]:
        folder.mkdir(parents=True, exist_ok=True)

    slides = []
    ig_paths = []
    for index, filename in enumerate(SLIDES, start=1):
        source_path = SOURCE_DIR / filename
        image = read_png(source_path)
        require_exact_size(image, source_path, POST_SIZE)
        slide_name = f"slide-{index:02d}.png"

        source_copy = source_out / slide_name
        source_copy.write_bytes(source_path.read_bytes())

        ig_path = ig_out / slide_name
        write_png(ig_path, image)
        ig_paths.append(ig_path)

        slides.append(
            {
                "slide": index,
                "text": COPY[index - 1],
                "source": str(source_copy),
                "instagram": str(ig_path),
            }
        )

    make_preview(ig_paths, OUT_DIR / "preview-instagram.png")
    manifest = {
        "title": "I Proposed to Anchal Under the Stars",
        "style": "soft hand-drawn Indian wedding storybook illustration matching the provided carousel references",
        "format": {
            "instagram": "1080x1350",
            "aspect_ratio": "4:5",
        },
        "slides": slides,
        "caption": "No crowd. No stage. Just us, the mountains, and a sky full of witnesses. I proposed to Anchal under the stars.",
    }
    (OUT_DIR / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
