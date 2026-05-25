#!/usr/bin/env python3
"""Render a lightweight illustrated storyboard preview for a carousel package.

This is a local QA preview, not the model-native final artwork. It creates
simple hand-drawn-style scene cards from slides.json so the story flow can be
reviewed before final Codex built-in image generation.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import cv2
import numpy as np


W, H = 1080, 1350
PAPER = (218, 234, 242)
INK = (41, 37, 32)
MUTED = (117, 105, 91)
WARM = (112, 178, 220)
ROSE = (105, 109, 206)
BLUE = (166, 139, 103)
SKIN_A = (105, 141, 196)
SKIN_B = (86, 116, 177)
HAIR = (45, 35, 30)
TABLE = (172, 126, 85)


def draw_text(canvas: np.ndarray, text: str, x: int, y: int, max_chars: int, scale: float = 1.0) -> int:
    words = text.replace("\n", " \n ").split()
    lines: list[str] = []
    current: list[str] = []
    for word in words:
        if word == "\n":
            if current:
                lines.append(" ".join(current))
                current = []
            continue
        candidate = " ".join([*current, word])
        if len(candidate) > max_chars and current:
            lines.append(" ".join(current))
            current = [word]
        else:
            current.append(word)
    if current:
        lines.append(" ".join(current))
    for line in lines:
        cv2.putText(canvas, line, (x, y), cv2.FONT_HERSHEY_SIMPLEX, scale, INK, 3, cv2.LINE_AA)
        y += int(74 * scale)
    return y


def line(canvas: np.ndarray, p1: tuple[int, int], p2: tuple[int, int], color: tuple[int, int, int] = INK, width: int = 4) -> None:
    cv2.line(canvas, p1, p2, color, width, cv2.LINE_AA)


def ellipse(
    canvas: np.ndarray,
    center: tuple[int, int],
    axes: tuple[int, int],
    color: tuple[int, int, int],
    width: int = -1,
) -> None:
    cv2.ellipse(canvas, center, axes, 0, 0, 360, color, width, cv2.LINE_AA)


def draw_person(canvas: np.ndarray, x: int, y: int, *, woman: bool, mood: str) -> None:
    skin = SKIN_A if woman else SKIN_B
    shirt = ROSE if woman else BLUE
    # Body
    ellipse(canvas, (x, y + 205), (80, 115), shirt, -1)
    ellipse(canvas, (x, y + 205), (80, 115), INK, 4)
    # Neck and face
    cv2.rectangle(canvas, (x - 22, y + 86), (x + 22, y + 130), skin, -1)
    ellipse(canvas, (x, y + 65), (64, 70), skin, -1)
    ellipse(canvas, (x, y + 65), (64, 70), INK, 4)
    # Hair
    if woman:
        ellipse(canvas, (x - 20, y + 58), (77, 85), HAIR, 11)
        line(canvas, (x - 62, y + 93), (x - 94, y + 210), HAIR, 12)
        line(canvas, (x + 54, y + 92), (x + 80, y + 190), HAIR, 9)
    else:
        ellipse(canvas, (x, y + 16), (58, 31), HAIR, -1)
        ellipse(canvas, (x, y + 91), (42, 22), HAIR, 8)
    # Face
    eye_y = y + 55
    cv2.circle(canvas, (x - 23, eye_y), 5, INK, -1, cv2.LINE_AA)
    cv2.circle(canvas, (x + 23, eye_y), 5, INK, -1, cv2.LINE_AA)
    if mood == "guarded":
        line(canvas, (x - 31, y + 40), (x - 9, y + 37), INK, 3)
        line(canvas, (x + 9, y + 37), (x + 31, y + 40), INK, 3)
        cv2.ellipse(canvas, (x, y + 88), (18, 8), 0, 10, 170, INK, 3, cv2.LINE_AA)
    elif mood == "laugh":
        cv2.ellipse(canvas, (x, y + 86), (26, 16), 0, 0, 180, INK, 4, cv2.LINE_AA)
        line(canvas, (x - 38, y + 40), (x - 12, y + 34), INK, 3)
        line(canvas, (x + 12, y + 34), (x + 38, y + 40), INK, 3)
    else:
        cv2.ellipse(canvas, (x, y + 85), (22, 11), 0, 0, 180, INK, 3, cv2.LINE_AA)
    # Arms
    line(canvas, (x - 67, y + 170), (x - 140, y + 245), INK, 5)
    line(canvas, (x + 67, y + 170), (x + 135, y + 235), INK, 5)


def draw_plate(canvas: np.ndarray, x: int, y: int, *, full: bool = False) -> None:
    ellipse(canvas, (x, y), (95, 35), (231, 224, 205), -1)
    ellipse(canvas, (x, y), (95, 35), INK, 4)
    colors = [(106, 143, 91), (205, 102, 72), (223, 183, 97)]
    points = [(x - 40, y - 6), (x, y + 3), (x + 42, y - 4), (x + 8, y - 13)]
    for idx, point in enumerate(points[: 4 if full else 2]):
        cv2.circle(canvas, point, 14, colors[idx % len(colors)], -1, cv2.LINE_AA)
        cv2.circle(canvas, point, 14, INK, 2, cv2.LINE_AA)


def draw_home(canvas: np.ndarray, slide: int) -> None:
    # Warm wall, kitchen window, couch, table.
    cv2.rectangle(canvas, (80, 255), (1000, 1060), (202, 225, 238), -1)
    cv2.rectangle(canvas, (80, 255), (1000, 1060), (130, 158, 179), 4)
    cv2.rectangle(canvas, (720, 310), (910, 520), (131, 190, 226), -1)
    cv2.rectangle(canvas, (720, 310), (910, 520), INK, 4)
    line(canvas, (815, 310), (815, 520), INK, 3)
    line(canvas, (720, 415), (910, 415), INK, 3)
    cv2.rectangle(canvas, (170, 790), (880, 1010), (168, 119, 111), -1)
    cv2.rectangle(canvas, (170, 790), (880, 1010), INK, 4)
    cv2.rectangle(canvas, (330, 850), (720, 950), TABLE, -1)
    cv2.rectangle(canvas, (330, 850), (720, 950), INK, 4)
    if slide in {2, 3, 4, 6}:
        draw_plate(canvas, 520, 890, full=slide in {3, 6})
    if slide in {1, 2, 6}:
        ellipse(canvas, (825, 370), (22, 60), (180, 220, 221), 2)
        line(canvas, (825, 430), (790, 500), (180, 220, 221), 3)
        line(canvas, (825, 430), (865, 500), (180, 220, 221), 3)
    if slide in {4, 5, 6}:
        for dx in [245, 785, 880]:
            cv2.circle(canvas, (dx, 735), 11, ROSE, -1, cv2.LINE_AA)
            cv2.circle(canvas, (dx, 735), 11, INK, 2, cv2.LINE_AA)


def render_slide(slide: dict[str, Any], out_path: Path) -> None:
    number = int(slide["slide"])
    canvas = np.zeros((H, W, 3), dtype=np.uint8)
    canvas[:, :] = PAPER
    # Subtle paper noise
    rng = np.random.default_rng(seed=number)
    noise = rng.normal(0, 3, canvas.shape).astype(np.int16)
    canvas[:] = np.clip(canvas.astype(np.int16) + noise, 0, 255).astype(np.uint8)

    top_text = str(slide["copy"])
    text_y = 118
    draw_text(canvas, top_text, 88, text_y, 31, 1.05 if number != 6 else 0.95)
    draw_home(canvas, number)

    woman_mood = "guarded" if number == 1 else "laugh" if number in {3, 5, 6} else "soft"
    man_mood = "soft"
    draw_person(canvas, 385, 555, woman=True, mood=woman_mood)
    draw_person(canvas, 690, 555, woman=False, mood=man_mood)

    if number == 2:
        line(canvas, (645, 770), (575, 845), BLUE, 8)
        draw_plate(canvas, 590, 840, full=True)
    elif number == 4:
        cv2.rectangle(canvas, (620, 830), (780, 895), (151, 116, 95), -1)
        cv2.rectangle(canvas, (620, 830), (780, 895), INK, 3)
        line(canvas, (705, 790), (590, 850), BLUE, 8)
    elif number == 5:
        line(canvas, (420, 780), (535, 850), ROSE, 8)
        line(canvas, (650, 780), (555, 850), BLUE, 8)
    elif number == 6:
        cv2.circle(canvas, (540, 455), 18, ROSE, -1, cv2.LINE_AA)
        cv2.putText(canvas, "life > numbers", (400, 1035), cv2.FONT_HERSHEY_SIMPLEX, 0.9, MUTED, 2, cv2.LINE_AA)

    cv2.putText(canvas, f"{number:02d}/06", (86, 1235), cv2.FONT_HERSHEY_SIMPLEX, 0.75, MUTED, 2, cv2.LINE_AA)
    cv2.putText(canvas, "@a.storyof.two", (725, 1235), cv2.FONT_HERSHEY_SIMPLEX, 0.75, MUTED, 2, cv2.LINE_AA)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    ok, encoded = cv2.imencode(".png", canvas, [cv2.IMWRITE_PNG_COMPRESSION, 3])
    if not ok:
        raise RuntimeError(f"Could not encode {out_path}")
    out_path.write_bytes(encoded.tobytes())


def make_contact_sheet(image_paths: list[Path], out_path: Path) -> None:
    thumbs = []
    for path in image_paths:
        img = cv2.imdecode(np.fromfile(str(path), dtype=np.uint8), cv2.IMREAD_COLOR)
        if img is None:
            raise RuntimeError(f"Could not read preview slide {path}")
        thumbs.append(cv2.resize(img, (324, 405), interpolation=cv2.INTER_AREA))
    sheet = np.zeros((2 * 405 + 24, 3 * 324 + 48, 3), dtype=np.uint8)
    sheet[:, :] = PAPER
    for idx, img in enumerate(thumbs):
        row = idx // 3
        col = idx % 3
        y = 8 + row * (405 + 8)
        x = 16 + col * (324 + 8)
        sheet[y : y + 405, x : x + 324] = img
    ok, encoded = cv2.imencode(".jpg", sheet, [cv2.IMWRITE_JPEG_QUALITY, 92])
    if not ok:
        raise RuntimeError(f"Could not encode {out_path}")
    out_path.write_bytes(encoded.tobytes())


def main() -> None:
    parser = argparse.ArgumentParser(description="Render local carousel storyboard preview")
    parser.add_argument("carousel_dir", type=Path)
    args = parser.parse_args()
    carousel_dir = args.carousel_dir
    slides = json.loads((carousel_dir / "slides.json").read_text(encoding="utf-8"))
    out_dir = carousel_dir / "illustrated-preview"
    paths: list[Path] = []
    for slide in slides:
        path = out_dir / f"slide-{int(slide['slide']):02d}.png"
        render_slide(slide, path)
        paths.append(path)
    make_contact_sheet(paths, out_dir / "contact-sheet.jpg")
    print(out_dir)


if __name__ == "__main__":
    main()
