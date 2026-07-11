from __future__ import annotations

import json
from datetime import date
from pathlib import Path

import cv2
import numpy as np


OUT_ROOT = Path("output/carousels/2026-05-09/anchal-under-the-stars")
POST_SIZE = (1080, 1350)
STORY_SIZE = (1080, 1920)

SLIDES = [
    {
        "number": "01",
        "source": "/private/var/folders/02/gt7632z95lv6y_w6gpf1whsh0000gn/T/TemporaryItems/com.apple.Photos.NSItemProvider/uuid=E4A0A119-D6F3-4BFC-AF42-EE59708C426A&code=001&library=1&type=1&mode=1&loc=true&cap=true.jpeg/IMG_9602.jpeg",
        "title": ["ANCHAL", "UNDER THE STARS"],
        "eyebrow": "I PROPOSED TO",
        "story": "The cover: the whole sky above the moment.",
    },
    {
        "number": "02",
        "source": "/private/var/folders/02/gt7632z95lv6y_w6gpf1whsh0000gn/T/TemporaryItems/com.apple.Photos.NSItemProvider/uuid=92FA8C00-3D78-40EA-9944-DECC0E1B2403&code=001&library=1&type=1&mode=1&loc=true&cap=true.jpeg/IMG_9601.jpeg",
        "title": ["NO CROWD.", "NO STAGE."],
        "eyebrow": "",
        "story": "The private hand-hold before the yes.",
    },
    {
        "number": "03",
        "source": "/private/var/folders/02/gt7632z95lv6y_w6gpf1whsh0000gn/T/TemporaryItems/com.apple.Photos.NSItemProvider/uuid=9FC6E002-B3D2-4BE5-BF01-0DCC61B392D3&code=001&library=1&type=1&mode=1&loc=true&cap=true.jpeg/IMG_9599.jpeg",
        "title": ["JUST US,", "THE MOUNTAINS,"],
        "eyebrow": "",
        "story": "The soft face-to-face frame.",
    },
    {
        "number": "04",
        "source": "/private/var/folders/02/gt7632z95lv6y_w6gpf1whsh0000gn/T/TemporaryItems/com.apple.Photos.NSItemProvider/uuid=FF28C851-2C96-426A-AE4A-38E8BD94C72E&code=001&library=1&type=1&mode=1&loc=true&cap=true.jpeg/IMG_9600.jpeg",
        "title": ["AND A SKY", "FULL OF WITNESSES."],
        "eyebrow": "",
        "story": "The looking-out-together bridge slide.",
    },
    {
        "number": "05",
        "source": "/private/var/folders/02/gt7632z95lv6y_w6gpf1whsh0000gn/T/TemporaryItems/com.apple.Photos.NSItemProvider/uuid=00881A9E-6E64-469E-96AF-E7D651FC7D3B&code=001&library=1&type=1&mode=1&loc=true&cap=true.jpeg/IMG_9603.jpeg",
        "title": ["SHE SAID YES."],
        "eyebrow": "",
        "story": "The emotional payoff: Anchal smiling under the same sky.",
    },
]


def read_image(path: str) -> np.ndarray:
    data = np.fromfile(path, dtype=np.uint8)
    image = cv2.imdecode(data, cv2.IMREAD_COLOR)
    if image is None:
        raise RuntimeError(f"Could not read image: {path}")
    return image


def write_jpg(path: Path, image: np.ndarray, quality: int = 95) -> None:
    ok, encoded = cv2.imencode(".jpg", image, [cv2.IMWRITE_JPEG_QUALITY, quality])
    if not ok:
        raise RuntimeError(f"Could not encode image: {path}")
    path.write_bytes(encoded.tobytes())


def cover_resize(image: np.ndarray, width: int, height: int) -> np.ndarray:
    h, w = image.shape[:2]
    scale = max(width / w, height / h)
    resized = cv2.resize(image, (round(w * scale), round(h * scale)), interpolation=cv2.INTER_LANCZOS4)
    rh, rw = resized.shape[:2]
    y = max(0, (rh - height) // 2)
    x = max(0, (rw - width) // 2)
    return resized[y : y + height, x : x + width]


def contain_resize(image: np.ndarray, width: int, height: int) -> np.ndarray:
    h, w = image.shape[:2]
    scale = min(width / w, height / h)
    return cv2.resize(image, (round(w * scale), round(h * scale)), interpolation=cv2.INTER_LANCZOS4)


def grade_night_photo(image: np.ndarray) -> np.ndarray:
    img = image.astype(np.float32) / 255.0
    img = np.clip((img - 0.5) * 1.08 + 0.5, 0.0, 1.0)
    img[:, :, 0] = np.clip(img[:, :, 0] * 1.07, 0.0, 1.0)
    img[:, :, 1] = np.clip(img[:, :, 1] * 0.95, 0.0, 1.0)
    img[:, :, 2] = np.clip(img[:, :, 2] * 1.02, 0.0, 1.0)

    img8 = (img * 255).astype(np.uint8)
    hsv = cv2.cvtColor(img8, cv2.COLOR_BGR2HSV).astype(np.float32)
    hsv[:, :, 1] = np.clip(hsv[:, :, 1] * 1.08, 0, 255)
    hsv[:, :, 2] = np.clip(hsv[:, :, 2] * 1.03, 0, 255)
    img8 = cv2.cvtColor(hsv.astype(np.uint8), cv2.COLOR_HSV2BGR)

    blur = cv2.GaussianBlur(img8, (0, 0), sigmaX=1.1)
    return cv2.addWeighted(img8, 1.16, blur, -0.16, 0)


def make_canvas(image: np.ndarray, size: tuple[int, int]) -> np.ndarray:
    target_w, target_h = size
    background = cover_resize(image, target_w, target_h)
    blur_size = max(45, (min(target_w, target_h) // 18) | 1)
    background = cv2.GaussianBlur(background, (blur_size, blur_size), 0)
    background = cv2.addWeighted(background, 0.48, np.zeros_like(background), 0.52, 0)

    foreground = contain_resize(image, target_w, target_h)
    canvas = background.copy()
    fh, fw = foreground.shape[:2]
    x = (target_w - fw) // 2
    y = (target_h - fh) // 2
    canvas[y : y + fh, x : x + fw] = foreground
    return canvas


def add_top_gradient(image: np.ndarray, height: int = 780) -> np.ndarray:
    out = image.copy()
    h, w = out.shape[:2]
    overlay = out.copy()
    for y in range(min(height, h)):
        alpha = 0.50 * (1 - y / height)
        overlay[y, :] = (overlay[y, :] * (1 - alpha)).astype(np.uint8)
    return cv2.addWeighted(overlay, 1.0, out, 0.0, 0)


def draw_text(image: np.ndarray, text: str, xy: tuple[int, int], scale: float, thickness: int) -> None:
    x, y = xy
    cv2.putText(
        image,
        text,
        (x + 3, y + 3),
        cv2.FONT_HERSHEY_SIMPLEX,
        scale,
        (0, 0, 0),
        thickness + 2,
        cv2.LINE_AA,
    )
    cv2.putText(
        image,
        text,
        (x, y),
        cv2.FONT_HERSHEY_SIMPLEX,
        scale,
        (244, 244, 238),
        thickness,
        cv2.LINE_AA,
    )


def draw_text_overlay(image: np.ndarray, slide: dict[str, object]) -> np.ndarray:
    out = add_top_gradient(image)
    h, w = out.shape[:2]
    margin = round(w * 0.08)
    y = round(h * 0.11)
    scale = w / 1080
    if slide["eyebrow"]:
        draw_text(out, str(slide["eyebrow"]), (margin, y), 0.52 * scale, 2)
        y += round(52 * scale)

    for line in slide["title"]:
        draw_text(out, str(line), (margin, y), 0.86 * scale, 3)
        y += round(58 * scale)

    footer_y = h - round(h * 0.055)
    draw_text(out, f"{slide['number']} / 05", (margin, footer_y), 0.42 * scale, 1)
    draw_text(out, "@A.STORYOF.TWO", (w - round(330 * scale), footer_y), 0.42 * scale, 1)
    return out


def export_slide(slide: dict[str, object]) -> dict[str, str]:
    source = read_image(str(slide["source"]))
    graded = grade_night_photo(source)
    post_clean = make_canvas(graded, POST_SIZE)
    post_text = draw_text_overlay(post_clean, slide)
    story_clean = make_canvas(graded, STORY_SIZE)
    story_text = draw_text_overlay(story_clean, slide)

    n = str(slide["number"])
    paths = {
        "post_clean": f"post-1080x1350-clean/slide-{n}.jpg",
        "post_text": f"post-1080x1350-text/slide-{n}.jpg",
        "story_clean": f"story-1080x1920-clean/slide-{n}.jpg",
        "story_text": f"story-1080x1920-text/slide-{n}.jpg",
    }

    write_jpg(OUT_ROOT / paths["post_clean"], post_clean)
    write_jpg(OUT_ROOT / paths["post_text"], post_text)
    write_jpg(OUT_ROOT / paths["story_clean"], story_clean)
    write_jpg(OUT_ROOT / paths["story_text"], story_text)
    return paths


def make_contact_sheet(image_paths: list[Path], out_path: Path) -> None:
    thumbs = []
    for path in image_paths:
        img = cv2.imdecode(np.fromfile(str(path), dtype=np.uint8), cv2.IMREAD_COLOR)
        thumbs.append(cv2.resize(img, (324, 405), interpolation=cv2.INTER_AREA))

    gap = 24
    sheet = np.full((405 + gap * 2, len(thumbs) * 324 + (len(thumbs) + 1) * gap, 3), 18, dtype=np.uint8)
    x = gap
    for thumb in thumbs:
        sheet[gap : gap + 405, x : x + 324] = thumb
        x += 324 + gap
    write_jpg(out_path, sheet, quality=92)


def main() -> None:
    for subdir in [
        "post-1080x1350-clean",
        "post-1080x1350-text",
        "story-1080x1920-clean",
        "story-1080x1920-text",
    ]:
        (OUT_ROOT / subdir).mkdir(parents=True, exist_ok=True)

    exported = []
    for slide in SLIDES:
        paths = export_slide(slide)
        exported.append({**slide, "outputs": paths})

    make_contact_sheet(
        [OUT_ROOT / item["outputs"]["post_text"] for item in exported],
        OUT_ROOT / "preview-post-text.jpg",
    )
    make_contact_sheet(
        [OUT_ROOT / item["outputs"]["post_clean"] for item in exported],
        OUT_ROOT / "preview-post-clean.jpg",
    )

    manifest = {
        "date": str(date.today()),
        "slug": "anchal-under-the-stars",
        "title": "Anchal Under The Stars",
        "channel": "@a.storyof.two",
        "concept": "Proposal carousel using the real night-sky photos: private, cinematic, emotional.",
        "format": {
            "platform": "Instagram",
            "type": "carousel",
            "slide_count": 5,
            "post_size": "1080x1350",
            "story_size": "1080x1920",
        },
        "sets": {
            "post_text": "post-1080x1350-text/",
            "post_clean": "post-1080x1350-clean/",
            "story_text": "story-1080x1920-text/",
            "story_clean": "story-1080x1920-clean/",
        },
        "slides": exported,
    }
    (OUT_ROOT / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")

    copy = {
        "carousel_title": "Anchal Under The Stars",
        "slide_text": ["I proposed to Anchal under the stars.", "No crowd. No stage.", "Just us, the mountains,", "and a sky full of witnesses.", "She said yes."],
        "caption": "Under a sky full of witnesses, I asked my favorite person to be forever. She said yes.",
        "alt_caption": "No crowd. No stage. Just us, the mountains, and the stars. I proposed to Anchal under this sky.",
        "hashtags": ["#AStoryOfTwo", "#Proposal", "#UnderTheStars", "#CoupleTravel", "#NightSky", "#EngagementStory"],
    }
    (OUT_ROOT / "copy.json").write_text(json.dumps(copy, indent=2), encoding="utf-8")

    storyboard = [
        "# Anchal Under The Stars",
        "",
        "A 5-slide proposal carousel built from the supplied night-sky photos.",
        "",
        "## Slide Flow",
    ]
    for item in exported:
        title = " ".join(item["title"])
        storyboard.append(f"- {item['number']}: {title} - {item['story']}")
    storyboard.extend(
        [
            "",
            "## Recommended Caption",
            "",
            copy["caption"],
            "",
            "## Export Sets",
            "",
            "- `post-1080x1350-text/`: exact 1080x1350 with text",
            "- `post-1080x1350-clean/`: exact 1080x1350 photo-only",
            "- `story-1080x1920-text/`: exact 1080x1920 with text",
            "- `story-1080x1920-clean/`: exact 1080x1920 photo-only",
        ]
    )
    (OUT_ROOT / "storyboard.md").write_text("\n".join(storyboard) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
