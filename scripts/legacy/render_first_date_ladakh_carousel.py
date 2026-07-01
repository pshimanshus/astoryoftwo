from __future__ import annotations

import json
from pathlib import Path

import cv2
import numpy as np


OUT_ROOT = Path("output/carousels/2026-05-10/from-first-date-to-ladakh")

SLIDES = [
    {
        "number": "01",
        "copy": "It started with two names on cups.",
        "source": "/Users/himanshusharma/Downloads/Photos Library.photoslibrary/resources/derivatives/8/8341940C-C58F-41E2-A4F7-387AC6120E5E_1_105_c.jpeg",
        "accent": (68, 128, 92),
    },
    {
        "number": "02",
        "copy": "By the second date, we were already a little unserious.",
        "source": "/Users/himanshusharma/Downloads/Photos Library.photoslibrary/resources/derivatives/5/5985BF66-4FCD-4BAC-BD4D-5EF9EE7819E8_1_105_c.jpeg",
        "inset": "/Users/himanshusharma/Downloads/Photos Library.photoslibrary/resources/derivatives/1/14273CAE-6BFD-4BE0-BDF2-77E7ADCC770F_1_105_c.jpeg",
        "accent": (166, 82, 74),
    },
    {
        "number": "03",
        "copy": "Then somehow, a date became a trip.",
        "source": "/Users/himanshusharma/Downloads/Photos Library.photoslibrary/resources/derivatives/5/50EF3CFA-5C6F-446E-837E-88A14672DFB1_1_105_c.jpeg",
        "accent": (180, 118, 66),
    },
    {
        "number": "04",
        "copy": "Ladakh made the story feel huge.",
        "source": "/Users/himanshusharma/Downloads/Photos Library.photoslibrary/resources/derivatives/9/9FE1A5B1-5D15-44FD-94EC-7E4A28BEDD3D_1_105_c.jpeg",
        "accent": (58, 122, 172),
    },
    {
        "number": "05",
        "copy": "But the point was still us.",
        "source": "/Users/himanshusharma/Downloads/Photos Library.photoslibrary/resources/derivatives/3/3F0CFF87-A5CF-450F-866A-55D226FD5E26_1_105_c.jpeg",
        "accent": (76, 128, 76),
    },
]


def read_image(path: str) -> np.ndarray:
    image = cv2.imdecode(np.fromfile(path, dtype=np.uint8), cv2.IMREAD_COLOR)
    if image is None:
        raise RuntimeError(f"Could not read image: {path}")
    return image


def write_jpg(path: Path, image: np.ndarray, quality: int = 88) -> None:
    ok, encoded = cv2.imencode(".jpg", image, [cv2.IMWRITE_JPEG_QUALITY, quality])
    if not ok:
        raise RuntimeError(f"Could not encode image: {path}")
    path.write_bytes(encoded.tobytes())


def cover_resize(image: np.ndarray, width: int, height: int) -> np.ndarray:
    h, w = image.shape[:2]
    scale = max(width / w, height / h)
    resized = cv2.resize(image, (round(w * scale), round(h * scale)), interpolation=cv2.INTER_LANCZOS4)
    rh, rw = resized.shape[:2]
    x = max(0, (rw - width) // 2)
    y = max(0, (rh - height) // 2)
    return resized[y : y + height, x : x + width]


def contain_resize(image: np.ndarray, width: int, height: int) -> np.ndarray:
    h, w = image.shape[:2]
    scale = min(width / w, height / h)
    return cv2.resize(image, (round(w * scale), round(h * scale)), interpolation=cv2.INTER_LANCZOS4)


def cartoonify(image: np.ndarray) -> np.ndarray:
    small = cv2.resize(image, None, fx=0.55, fy=0.55, interpolation=cv2.INTER_AREA)
    smooth = cv2.pyrMeanShiftFiltering(small, sp=18, sr=34)
    for _ in range(2):
        smooth = cv2.bilateralFilter(smooth, 9, 60, 60)

    gray = cv2.cvtColor(small, cv2.COLOR_BGR2GRAY)
    gray = cv2.medianBlur(gray, 7)
    edges = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_MEAN_C, cv2.THRESH_BINARY, 9, 5)
    edges = cv2.cvtColor(edges, cv2.COLOR_GRAY2BGR)

    poster = np.clip(np.round(smooth.astype(np.float32) / 32) * 32, 0, 255).astype(np.uint8)
    cartoon = cv2.bitwise_and(poster, edges)
    cartoon = cv2.resize(cartoon, (image.shape[1], image.shape[0]), interpolation=cv2.INTER_CUBIC)

    warm = np.full_like(cartoon, (232, 238, 246))
    return cv2.addWeighted(cartoon, 0.86, warm, 0.14, 0)


def make_canvas(source: np.ndarray) -> np.ndarray:
    width, height = 2160, 2700
    illustrated = cartoonify(source)
    bg = cover_resize(illustrated, width, height)
    bg = cv2.GaussianBlur(bg, (91, 91), 0)
    paper = np.full((height, width, 3), (232, 239, 246), dtype=np.uint8)
    canvas = cv2.addWeighted(bg, 0.34, paper, 0.66, 0)

    framed = contain_resize(illustrated, 1840, 1960)
    fh, fw = framed.shape[:2]
    x = (width - fw) // 2
    y = 560 if fh < 1800 else 500
    canvas[y : y + fh, x : x + fw] = cv2.addWeighted(
        framed,
        0.94,
        canvas[y : y + fh, x : x + fw],
        0.06,
        0,
    )
    return canvas


def add_inset(canvas: np.ndarray, path: str) -> np.ndarray:
    inset = cartoonify(read_image(path))
    inset = cover_resize(inset, 580, 760)
    x, y = 1420, 1760
    border = 28
    cv2.rectangle(
        canvas,
        (x - border, y - border),
        (x + inset.shape[1] + border, y + inset.shape[0] + border),
        (246, 241, 232),
        -1,
    )
    cv2.rectangle(
        canvas,
        (x - border, y - border),
        (x + inset.shape[1] + border, y + inset.shape[0] + border),
        (54, 48, 42),
        5,
        cv2.LINE_AA,
    )
    canvas[y : y + inset.shape[0], x : x + inset.shape[1]] = inset
    return canvas


def wrap_text(text: str, max_chars: int) -> list[str]:
    words = text.split()
    lines: list[str] = []
    current: list[str] = []
    for word in words:
        candidate = " ".join([*current, word])
        if len(candidate) > max_chars and current:
            lines.append(" ".join(current))
            current = [word]
        else:
            current.append(word)
    if current:
        lines.append(" ".join(current))
    return lines


def draw_text_block(image: np.ndarray, text: str, accent: tuple[int, int, int]) -> None:
    x = 145
    y = 190
    lines = wrap_text(text, 29)
    for line in lines:
        cv2.putText(image, line, (x + 4, y + 4), cv2.FONT_HERSHEY_SIMPLEX, 2.06, (250, 247, 240), 10, cv2.LINE_AA)
        cv2.putText(image, line, (x, y), cv2.FONT_HERSHEY_SIMPLEX, 2.06, (42, 38, 33), 5, cv2.LINE_AA)
        y += 128

    cv2.line(image, (x, y + 28), (x + 360, y + 28), accent, 14, cv2.LINE_AA)
    cv2.putText(
        image,
        "@a.storyof.two",
        (1560, 2545),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.78,
        (92, 86, 76),
        2,
        cv2.LINE_AA,
    )

def add_footer(image: np.ndarray, number: str) -> None:
    cv2.putText(image, f"{number} / 05", (145, 2545), cv2.FONT_HERSHEY_SIMPLEX, 0.78, (92, 86, 76), 2, cv2.LINE_AA)


def export_slide(slide: dict[str, object]) -> dict[str, str]:
    canvas = make_canvas(read_image(str(slide["source"])))
    if slide.get("inset"):
        canvas = add_inset(canvas, str(slide["inset"]))

    clean = canvas.copy()
    text_preview = canvas.copy()
    draw_text_block(text_preview, str(slide["copy"]), tuple(slide["accent"]))
    add_footer(text_preview, str(slide["number"]))
    add_footer(clean, str(slide["number"]))
    clean = cv2.resize(clean, (1080, 1350), interpolation=cv2.INTER_AREA)
    text_preview = cv2.resize(text_preview, (1080, 1350), interpolation=cv2.INTER_AREA)

    number = str(slide["number"])
    outputs = {
        "legacy_preview_clean": f"legacy-preview-clean/slide-{number}.jpg",
        "legacy_preview_text": f"legacy-preview-text/slide-{number}.jpg",
    }
    write_jpg(OUT_ROOT / outputs["legacy_preview_clean"], clean)
    write_jpg(OUT_ROOT / outputs["legacy_preview_text"], text_preview)
    return outputs


def make_preview(paths: list[Path], out_path: Path) -> None:
    thumbs = []
    for path in paths:
        image = read_image(str(path))
        thumbs.append(cv2.resize(image, (216, 270), interpolation=cv2.INTER_AREA))
    gap = 18
    sheet = np.full((270 + gap * 2, len(thumbs) * 216 + (len(thumbs) + 1) * gap, 3), (232, 239, 246), dtype=np.uint8)
    x = gap
    for thumb in thumbs:
        sheet[gap : gap + 270, x : x + 216] = thumb
        x += 216 + gap
    write_jpg(out_path, sheet, quality=86)


def main() -> None:
    for folder in ["legacy-preview-clean", "legacy-preview-text"]:
        (OUT_ROOT / folder).mkdir(parents=True, exist_ok=True)

    rendered = []
    preview_paths = []
    for slide in SLIDES:
        outputs = export_slide(slide)
        preview_paths.append(OUT_ROOT / outputs["legacy_preview_text"])
        rendered.append(
            {
                "slide": int(slide["number"]),
                "copy": slide["copy"],
                "source": slide["source"],
                "outputs": outputs,
                "status": "legacy_preview_generated",
                "backend": "legacy_local_renderer",
                "generation_mode": "legacy_local_preview_not_publishable",
                "publishable": False,
                "can_satisfy_final_gate": False,
            }
        )

    make_preview(preview_paths, OUT_ROOT / "preview-text.jpg")
    manifest = {
        "status": "legacy_preview_generated",
        "backend": "legacy_local_renderer",
        "generation_mode": "legacy_local_preview_not_publishable",
        "slide_count": len(rendered),
        "done": False,
        "publishable": False,
        "requires_human_generation": False,
        "can_satisfy_final_gate": False,
        "mode": "local_cv2_stylized_render",
        "reason": (
            "Legacy local preview render only. This script does not run the C-layer agent package, "
            "does not call model-native image generation, and cannot satisfy final publishable gates."
        ),
        "style": "cartoonified photo illustration with warm paper background and story text overlay",
        "slides": rendered,
    }
    payload = json.dumps(manifest, indent=2)
    (OUT_ROOT / "image-generation.json").write_text(payload, encoding="utf-8")
    (OUT_ROOT / "final-images.json").write_text(payload, encoding="utf-8")
    (OUT_ROOT / "preview.md").write_text(
        "\n".join(
            [
                "# Preview",
                "",
                "![text preview](preview-text.jpg)",
                "",
                "Text previews live in `legacy-preview-text/`.",
                "Clean previews live in `legacy-preview-clean/`.",
            ]
        )
        + "\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
