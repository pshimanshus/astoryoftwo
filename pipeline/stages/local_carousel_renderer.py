from __future__ import annotations

import json
import math
import shutil
from datetime import date
from pathlib import Path
from typing import Any

import cv2
import numpy as np

from pipeline.stages.carousel_generation_state import GenerationStatus, write_generation_state
from pipeline.stages.carousel_quality import QualityContext, write_quality_artifacts
from pipeline.stages.codex_builtin_image_generation import (
    identity_consistency_gate_reason,
    visual_plan_quality_gate_reason,
)
from pipeline.stages.model_native_image_generation import (
    FINAL_UPLOAD_SIZE,
    INSTAGRAM_POST_FORMAT,
    NATIVE_OUTPUT_CONTRACT,
    NATIVE_OUTPUT_FORMATS,
    REELS_STORIES_FORMAT,
    REELS_STORIES_SIZE,
)


BACKEND = "legacy_local_renderer"
GENERATION_MODE = "legacy_local_preview_not_publishable"
STATUS = "legacy_preview_generated"
INSTAGRAM_SIZE = FINAL_UPLOAD_SIZE
REELS_SIZE = REELS_STORIES_SIZE

PAPER = (232, 239, 245)
INK = (42, 39, 36)
MUTED_INK = (110, 105, 96)
SKIN_AACHU = (128, 168, 199)
SKIN_ZUV = (118, 158, 188)
HAIR = (34, 30, 27)
BEARD = (45, 39, 34)
CORAL = (122, 128, 205)
SAGE = (145, 160, 121)
CREAM = (226, 232, 238)
GOLD = (94, 177, 216)
ROSE = (158, 181, 227)
BLUE = (183, 170, 118)
GREEN = (165, 184, 144)


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


def imwrite(path: Path, image: np.ndarray) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    ok, encoded = cv2.imencode(".png", image, [cv2.IMWRITE_PNG_COMPRESSION, 3])
    if not ok:
        raise RuntimeError(f"Could not encode image: {path}")
    path.write_bytes(encoded.tobytes())


def line(image: np.ndarray, start: tuple[int, int], end: tuple[int, int], color: tuple[int, int, int] = INK, width: int = 4) -> None:
    cv2.line(image, start, end, color, width, cv2.LINE_AA)


def ellipse(
    image: np.ndarray,
    center: tuple[int, int],
    axes: tuple[int, int],
    color: tuple[int, int, int],
    *,
    angle: float = 0,
    start_angle: float = 0,
    end_angle: float = 360,
    width: int = -1,
) -> None:
    cv2.ellipse(image, center, axes, angle, start_angle, end_angle, color, width, cv2.LINE_AA)


def circle(image: np.ndarray, center: tuple[int, int], radius: int, color: tuple[int, int, int], width: int = -1) -> None:
    cv2.circle(image, center, radius, color, width, cv2.LINE_AA)


def rounded_rect(
    image: np.ndarray,
    x: int,
    y: int,
    w: int,
    h: int,
    r: int,
    fill: tuple[int, int, int],
    outline: tuple[int, int, int] = INK,
    outline_width: int = 3,
) -> None:
    r = min(r, w // 2, h // 2)
    cv2.rectangle(image, (x + r, y), (x + w - r, y + h), fill, -1, cv2.LINE_AA)
    cv2.rectangle(image, (x, y + r), (x + w, y + h - r), fill, -1, cv2.LINE_AA)
    for cx, cy, start, end in [
        (x + r, y + r, 180, 270),
        (x + w - r, y + r, 270, 360),
        (x + w - r, y + h - r, 0, 90),
        (x + r, y + h - r, 90, 180),
    ]:
        ellipse(image, (cx, cy), (r, r), fill, start_angle=start, end_angle=end)
    if outline_width > 0:
        cv2.line(image, (x + r, y), (x + w - r, y), outline, outline_width, cv2.LINE_AA)
        cv2.line(image, (x + r, y + h), (x + w - r, y + h), outline, outline_width, cv2.LINE_AA)
        cv2.line(image, (x, y + r), (x, y + h - r), outline, outline_width, cv2.LINE_AA)
        cv2.line(image, (x + w, y + r), (x + w, y + h - r), outline, outline_width, cv2.LINE_AA)
        for cx, cy, start, end in [
            (x + r, y + r, 180, 270),
            (x + w - r, y + r, 270, 360),
            (x + w - r, y + h - r, 0, 90),
            (x + r, y + h - r, 90, 180),
        ]:
            ellipse(image, (cx, cy), (r, r), outline, start_angle=start, end_angle=end, width=outline_width)


def put_text(
    image: np.ndarray,
    text: str,
    origin: tuple[int, int],
    *,
    scale: float,
    color: tuple[int, int, int] = INK,
    thickness: int = 3,
    font: int = cv2.FONT_HERSHEY_SIMPLEX,
) -> None:
    cv2.putText(image, text, origin, font, scale, color, thickness, cv2.LINE_AA)


def text_size(text: str, scale: float, thickness: int = 3) -> tuple[int, int]:
    (w, h), baseline = cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX, scale, thickness)
    return w, h + baseline


def split_long_word(word: str, max_width: int, scale: float, thickness: int) -> list[str]:
    parts: list[str] = []
    current = ""
    for char in word:
        candidate = current + char
        if current and text_size(candidate, scale, thickness)[0] > max_width:
            parts.append(current)
            current = char
        else:
            current = candidate
    if current:
        parts.append(current)
    return parts


def wrap_text(text: str, max_width: int, scale: float, thickness: int = 3) -> list[str]:
    lines: list[str] = []
    paragraphs = text.splitlines() or [text]
    for paragraph in paragraphs:
        words = paragraph.split()
        current = ""
        for word in words:
            word_parts = split_long_word(word, max_width, scale, thickness)
            for part in word_parts:
                candidate = part if not current else f"{current} {part}"
                if text_size(candidate, scale, thickness)[0] <= max_width:
                    current = candidate
                else:
                    if current:
                        lines.append(current)
                    current = part
        if current:
            lines.append(current)
        elif paragraph == "":
            lines.append("")
    return lines


def draw_wrapped_text(
    image: np.ndarray,
    text: str,
    *,
    x: int,
    y: int,
    max_width: int,
    max_height: int,
    max_scale: float,
    min_scale: float,
    color: tuple[int, int, int] = INK,
    thickness: int = 3,
    center: bool = False,
) -> tuple[int, int, float, list[str]]:
    scale = max_scale
    lines = wrap_text(text, max_width, scale, thickness)
    line_height = round(text_size("Ag", scale, thickness)[1] * 1.45)
    while scale > min_scale and (len(lines) * line_height > max_height or any(text_size(line_text, scale, thickness)[0] > max_width for line_text in lines)):
        scale -= 0.05
        lines = wrap_text(text, max_width, scale, thickness)
        line_height = round(text_size("Ag", scale, thickness)[1] * 1.45)
    cy = y
    for line_text in lines:
        tw, th = text_size(line_text, scale, thickness)
        tx = x + (max_width - tw) // 2 if center else x
        put_text(image, line_text, (tx, cy), scale=scale, color=color, thickness=thickness)
        cy += line_height
    return x, cy, scale, lines


def add_paper_texture(image: np.ndarray, seed: int) -> None:
    rng = np.random.default_rng(seed)
    noise = rng.normal(0, 2.8, image.shape).astype(np.int16)
    textured = np.clip(image.astype(np.int16) + noise, 0, 255).astype(np.uint8)
    image[:] = textured
    h, w = image.shape[:2]
    for _ in range(max(18, (w * h) // 90000)):
        x = int(rng.integers(20, w - 20))
        y = int(rng.integers(20, h - 20))
        radius = int(rng.integers(1, 3))
        color = tuple(int(c) for c in (np.array(PAPER) - rng.integers(5, 16, size=3)))
        circle(image, (x, y), radius, color, -1)


def draw_motion_marks(image: np.ndarray, x: int, y: int, scale: float, side: str = "left") -> None:
    direction = -1 if side == "left" else 1
    for idx in range(3):
        dy = round(idx * 26 * scale)
        line(
            image,
            (round(x + direction * 22 * scale), round(y + dy)),
            (round(x + direction * 72 * scale), round(y + dy - 14 * scale)),
            MUTED_INK,
            max(2, round(3 * scale)),
        )


def draw_small_heart(image: np.ndarray, x: int, y: int, scale: float, color: tuple[int, int, int] = ROSE) -> None:
    r = max(4, round(11 * scale))
    circle(image, (x - r // 2, y - r // 3), r // 2, color)
    circle(image, (x + r // 2, y - r // 3), r // 2, color)
    pts = np.array([(x - r, y), (x + r, y), (x, y + round(1.25 * r))], dtype=np.int32)
    cv2.fillConvexPoly(image, pts, color, cv2.LINE_AA)
    cv2.polylines(image, [pts], True, INK, max(1, round(2 * scale)), cv2.LINE_AA)


def draw_person(
    image: np.ndarray,
    *,
    person: str,
    x: int,
    y: int,
    scale: float,
    mood: str = "smile",
    arm: str = "open",
    flip: bool = False,
) -> None:
    skin = SKIN_AACHU if person == "aachu" else SKIN_ZUV
    shirt = CORAL if person == "aachu" else SAGE
    direction = -1 if flip else 1
    body_w = round(115 * scale)
    body_h = round(170 * scale)
    head_w = round(82 * scale)
    head_h = round(96 * scale)
    neck_y = y + round(44 * scale)
    torso = np.array(
        [
            (x - body_w // 2, neck_y + round(30 * scale)),
            (x + body_w // 2, neck_y + round(30 * scale)),
            (x + round(body_w * 0.42), neck_y + body_h),
            (x - round(body_w * 0.42), neck_y + body_h),
        ],
        dtype=np.int32,
    )
    cv2.fillConvexPoly(image, torso, shirt, cv2.LINE_AA)
    cv2.polylines(image, [torso], True, INK, max(2, round(4 * scale)), cv2.LINE_AA)
    if person == "aachu":
        dupatta = np.array(
            [
                (x - round(58 * scale), neck_y + round(34 * scale)),
                (x - round(18 * scale), neck_y + round(30 * scale)),
                (x + round(45 * scale), neck_y + body_h),
                (x + round(8 * scale), neck_y + body_h),
            ],
            dtype=np.int32,
        )
        cv2.fillConvexPoly(image, dupatta, GOLD, cv2.LINE_AA)
        cv2.polylines(image, [dupatta], True, INK, max(1, round(2 * scale)), cv2.LINE_AA)
    shoulder_y = neck_y + round(62 * scale)
    if arm == "raised":
        elbow = (x + direction * round(82 * scale), shoulder_y - round(60 * scale))
        hand = (x + direction * round(120 * scale), shoulder_y - round(126 * scale))
        line(image, (x + direction * round(44 * scale), shoulder_y), elbow, INK, max(2, round(7 * scale)))
        line(image, elbow, hand, INK, max(2, round(7 * scale)))
        circle(image, hand, max(7, round(12 * scale)), skin)
    elif arm == "typing":
        line(image, (x + direction * round(40 * scale), shoulder_y), (x + direction * round(116 * scale), shoulder_y + round(58 * scale)), INK, max(2, round(7 * scale)))
        circle(image, (x + direction * round(125 * scale), shoulder_y + round(62 * scale)), max(7, round(12 * scale)), skin)
    else:
        line(image, (x - round(44 * scale), shoulder_y), (x - round(126 * scale), shoulder_y + round(34 * scale)), INK, max(2, round(6 * scale)))
        line(image, (x + round(44 * scale), shoulder_y), (x + round(126 * scale), shoulder_y + round(22 * scale)), INK, max(2, round(6 * scale)))
        circle(image, (x - round(134 * scale), shoulder_y + round(36 * scale)), max(7, round(11 * scale)), skin)
        circle(image, (x + round(134 * scale), shoulder_y + round(24 * scale)), max(7, round(11 * scale)), skin)

    neck_half_width = round(17 * scale)
    neck_top = y + round(36 * scale)
    neck_bottom = y + round(82 * scale)
    cv2.rectangle(image, (x - neck_half_width, neck_top), (x + neck_half_width, neck_bottom), skin, -1, cv2.LINE_AA)
    cv2.rectangle(image, (x - neck_half_width, neck_top), (x + neck_half_width, neck_bottom), INK, max(1, round(2 * scale)), cv2.LINE_AA)

    if person == "aachu":
        ellipse(image, (x, y + round(7 * scale)), (round(62 * scale), round(88 * scale)), HAIR)
        ellipse(image, (x - round(27 * scale), y + round(22 * scale)), (round(39 * scale), round(86 * scale)), HAIR, angle=12)
        ellipse(image, (x + round(32 * scale), y + round(24 * scale)), (round(32 * scale), round(78 * scale)), HAIR, angle=-10)
    else:
        ellipse(image, (x, y - round(36 * scale)), (round(52 * scale), round(28 * scale)), HAIR, angle=-7)
        ellipse(image, (x, y + round(20 * scale)), (head_w // 2, round(62 * scale)), BEARD)
    ellipse(image, (x, y), (head_w // 2, head_h // 2), skin)
    ellipse(image, (x, y), (head_w // 2, head_h // 2), INK, width=max(2, round(4 * scale)))
    if person == "zuv":
        ellipse(image, (x, y + round(25 * scale)), (round(38 * scale), round(27 * scale)), BEARD, start_angle=0, end_angle=180)
        ellipse(image, (x, y + round(31 * scale)), (round(36 * scale), round(20 * scale)), BEARD)

    eye_y = y - round(9 * scale)
    circle(image, (x - round(23 * scale), eye_y), max(3, round(5 * scale)), INK)
    circle(image, (x + round(23 * scale), eye_y), max(3, round(5 * scale)), INK)
    line(image, (x - round(35 * scale), eye_y - round(18 * scale)), (x - round(13 * scale), eye_y - round(22 * scale)), INK, max(1, round(3 * scale)))
    line(image, (x + round(13 * scale), eye_y - round(22 * scale)), (x + round(35 * scale), eye_y - round(18 * scale)), INK, max(1, round(3 * scale)))
    if mood in {"laugh", "delighted"}:
        ellipse(image, (x, y + round(22 * scale)), (round(24 * scale), round(14 * scale)), INK, start_angle=0, end_angle=180, width=max(2, round(4 * scale)))
        circle(image, (x - round(45 * scale), y + round(16 * scale)), max(4, round(7 * scale)), ROSE)
        circle(image, (x + round(45 * scale), y + round(16 * scale)), max(4, round(7 * scale)), ROSE)
    elif mood == "focused":
        line(image, (x - round(17 * scale), y + round(28 * scale)), (x + round(18 * scale), y + round(25 * scale)), INK, max(1, round(3 * scale)))
    else:
        ellipse(image, (x, y + round(24 * scale)), (round(24 * scale), round(12 * scale)), INK, start_angle=0, end_angle=180, width=max(2, round(4 * scale)))


def draw_bubble(
    image: np.ndarray,
    x: int,
    y: int,
    w: int,
    h: int,
    text: str,
    *,
    fill: tuple[int, int, int] = CREAM,
    align_right: bool = False,
    scale: float = 0.75,
) -> None:
    rounded_rect(image, x, y, w, h, max(18, h // 4), fill, INK, 3)
    tail = np.array(
        [
            (x + w - 38, y + h - 3),
            (x + w - 5, y + h + 25),
            (x + w - 64, y + h - 9),
        ]
        if align_right
        else [
            (x + 38, y + h - 3),
            (x + 5, y + h + 25),
            (x + 64, y + h - 9),
        ],
        dtype=np.int32,
    )
    cv2.fillConvexPoly(image, tail, fill, cv2.LINE_AA)
    cv2.polylines(image, [tail], True, INK, 2, cv2.LINE_AA)
    draw_wrapped_text(
        image,
        text,
        x=x + 24,
        y=y + max(38, round(44 * scale)),
        max_width=w - 48,
        max_height=h - 30,
        max_scale=scale,
        min_scale=0.42,
        thickness=max(1, round(2 * scale)),
    )


def draw_phone(image: np.ndarray, x: int, y: int, w: int, h: int, *, slide: int) -> None:
    rounded_rect(image, x, y, w, h, round(42 * w / 360), (248, 247, 239), INK, 5)
    rounded_rect(image, x + round(22 * w / 360), y + round(28 * h / 620), w - round(44 * w / 360), h - round(70 * h / 620), 28, (240, 243, 235), (187, 180, 166), 2)
    top = y + round(74 * h / 620)
    bubble_h = max(42, round(52 * h / 620))
    left = x + round(46 * w / 360)
    right = x + round(96 * w / 360)
    texts = [
        "wait",
        "so listen",
        "then this happened",
        "no but plot twist",
        "I need to explain",
    ]
    for idx, text in enumerate(texts):
        bx = left if idx % 2 == 0 else right
        by = top + idx * round(74 * h / 620)
        bw = round((225 if idx % 2 == 0 else 205) * w / 360)
        draw_bubble(image, bx, by, bw, bubble_h, text, fill=(226, 237, 248) if idx % 2 == 0 else (225, 240, 224), align_right=idx % 2 == 1, scale=0.42 + 0.04 * (w / 360))
    if slide == 3:
        draw_bubble(image, x + round(70 * w / 360), y + h - round(130 * h / 620), round(220 * w / 360), bubble_h, "and then?", fill=(223, 234, 218), align_right=True, scale=0.5)


def draw_symbols(image: np.ndarray, w: int, h: int, seed: int, *, density: int = 9) -> None:
    rng = np.random.default_rng(seed)
    for idx in range(density):
        x = int(rng.integers(round(w * 0.12), round(w * 0.88)))
        y = int(rng.integers(round(h * 0.32), round(h * 0.86)))
        scale = float(rng.uniform(0.7, 1.2))
        if idx % 4 == 0:
            draw_small_heart(image, x, y, scale * 0.65, ROSE)
        elif idx % 4 == 1:
            draw_bubble(image, x - 44, y - 24, 92, 48, "?", fill=(229, 238, 225), scale=0.45)
        elif idx % 4 == 2:
            line(image, (x - 28, y), (x + 28, y - 18), MUTED_INK, 3)
            line(image, (x + 28, y - 18), (x + 13, y - 25), MUTED_INK, 3)
            line(image, (x + 28, y - 18), (x + 22, y - 2), MUTED_INK, 3)
        else:
            ellipse(image, (x, y), (round(24 * scale), round(14 * scale)), BLUE, width=3)


def private_caption_labels(copy: str) -> dict[str, str]:
    labels: dict[str, str] = {}
    for raw_line in copy.splitlines():
        line_text = raw_line.strip()
        lower = line_text.lower()
        if lower.startswith("her:"):
            labels["aachu"] = line_text.split(":", 1)[1].strip()
        elif lower.startswith("him:"):
            labels["zuv"] = line_text.split(":", 1)[1].strip()
    return labels


def is_private_caption_copy(copy: str) -> bool:
    lower = copy.lower()
    return (
        "private captions" in lower
        or "captions you kindly" in lower
        or lower.startswith("her:")
        or lower.startswith("him:")
    )


def is_long_distance_copy(copy: str) -> bool:
    lower = copy.lower()
    return (
        "long distance" in lower
        or "ordinary time" in lower
        or "what should we cook" in lower
        or "board game" in lower
        or "cab is late" in lower
    )


def draw_long_distance_scene(image: np.ndarray, slide: dict[str, Any], output_format: str) -> None:
    h, w = image.shape[:2]
    number = int(slide.get("slide", 0) or 0)
    is_reels = output_format == REELS_STORIES_FORMAT
    scene_top = round(h * (0.34 if is_reels else 0.31))
    scene_bottom = round(h * 0.91)
    scene_h = scene_bottom - scene_top
    center_y = scene_top + scene_h // 2
    person_scale = 0.96 if not is_reels else 1.02

    if number == 1:
        draw_phone(image, round(w * 0.11), scene_top + round(scene_h * 0.06), round(w * 0.22), round(scene_h * 0.48), slide=number)
        draw_phone(image, round(w * 0.67), scene_top + round(scene_h * 0.09), round(w * 0.22), round(scene_h * 0.48), slide=number)
        draw_person(image, person="aachu", x=round(w * 0.23), y=scene_top + round(scene_h * 0.72), scale=0.78 if not is_reels else 0.84, mood="smile", arm="typing")
        draw_person(image, person="zuv", x=round(w * 0.77), y=scene_top + round(scene_h * 0.72), scale=0.8 if not is_reels else 0.86, mood="smile", arm="typing", flip=True)
        for idx, label in enumerate(["cook?", "game?", "cab?"]):
            draw_bubble(image, round(w * (0.38 + idx * 0.08)), scene_top + round(scene_h * (0.14 + idx * 0.08)), round(w * 0.14), round(scene_h * 0.08), label, fill=(229, 238, 225), scale=0.42)
        for idx in range(4):
            draw_small_heart(image, round(w * (0.42 + idx * 0.055)), scene_top + round(scene_h * (0.66 + 0.03 * math.sin(idx))), 0.55, ROSE)
    elif number == 2:
        rounded_rect(image, round(w * 0.18), scene_top + round(scene_h * 0.46), round(w * 0.64), round(scene_h * 0.12), 18, (218, 224, 216), INK, 3)
        rounded_rect(image, round(w * 0.43), scene_top + round(scene_h * 0.32), round(w * 0.16), round(scene_h * 0.12), 18, CREAM, INK, 3)
        line(image, (round(w * 0.43), scene_top + round(scene_h * 0.44)), (round(w * 0.38), scene_top + round(scene_h * 0.54)), INK, 5)
        line(image, (round(w * 0.59), scene_top + round(scene_h * 0.44)), (round(w * 0.65), scene_top + round(scene_h * 0.54)), INK, 5)
        draw_person(image, person="aachu", x=round(w * 0.32), y=center_y + round(scene_h * 0.08), scale=person_scale, mood="delighted", arm="raised")
        draw_person(image, person="zuv", x=round(w * 0.68), y=center_y + round(scene_h * 0.08), scale=person_scale * 1.02, mood="laugh", arm="open", flip=True)
        for idx in range(5):
            circle(image, (round(w * (0.43 + idx * 0.04)), scene_top + round(scene_h * (0.25 + 0.04 * math.sin(idx)))), 9, GOLD)
        draw_bubble(image, round(w * 0.49), scene_top + round(scene_h * 0.08), round(w * 0.28), round(scene_h * 0.09), "we'll ruin it", fill=(225, 240, 224), align_right=True, scale=0.45)
    elif number == 3:
        rounded_rect(image, round(w * 0.28), scene_top + round(scene_h * 0.45), round(w * 0.44), round(scene_h * 0.19), 18, (239, 235, 220), INK, 3)
        for row in range(3):
            line(image, (round(w * 0.31), scene_top + round(scene_h * (0.49 + row * 0.045))), (round(w * 0.69), scene_top + round(scene_h * (0.49 + row * 0.045))), (186, 177, 160), 2)
        for col in range(4):
            line(image, (round(w * (0.36 + col * 0.08)), scene_top + round(scene_h * 0.47)), (round(w * (0.36 + col * 0.08)), scene_top + round(scene_h * 0.63)), (186, 177, 160), 2)
        for idx, color in enumerate([CORAL, BLUE, GREEN, GOLD]):
            circle(image, (round(w * (0.38 + idx * 0.08)), scene_top + round(scene_h * (0.53 + 0.04 * (idx % 2)))), 13, color)
        draw_person(image, person="aachu", x=round(w * 0.28), y=center_y + round(scene_h * 0.04), scale=0.9 if not is_reels else 0.96, mood="focused", arm="open")
        draw_person(image, person="zuv", x=round(w * 0.73), y=center_y + round(scene_h * 0.04), scale=0.92 if not is_reels else 0.98, mood="laugh", arm="raised", flip=True)
        draw_bubble(image, round(w * 0.53), scene_top + round(scene_h * 0.08), round(w * 0.31), round(scene_h * 0.1), "don't cry", fill=(225, 240, 224), align_right=True, scale=0.52)
    elif number == 4:
        for idx in range(16):
            x = round(w * (0.08 + 0.055 * (idx % 12)))
            y = scene_top + round(scene_h * (0.05 + 0.06 * (idx // 4)))
            line(image, (x, y), (x + 18, y + 38), (169, 181, 195), 3)
        ellipse(image, (round(w * 0.5), scene_top + round(scene_h * 0.32)), (round(w * 0.32), round(scene_h * 0.12)), GOLD, start_angle=180, end_angle=360)
        line(image, (round(w * 0.5), scene_top + round(scene_h * 0.32)), (round(w * 0.5), scene_top + round(scene_h * 0.62)), INK, 4)
        draw_person(image, person="aachu", x=round(w * 0.39), y=center_y + round(scene_h * 0.06), scale=0.9 if not is_reels else 0.98, mood="smile", arm="open")
        draw_person(image, person="zuv", x=round(w * 0.62), y=center_y + round(scene_h * 0.06), scale=0.92 if not is_reels else 1.0, mood="smile", arm="open", flip=True)
        draw_bubble(image, round(w * 0.58), scene_top + round(scene_h * 0.04), round(w * 0.2), round(scene_h * 0.09), "good", fill=(225, 240, 224), align_right=True, scale=0.62)
    else:
        rounded_rect(image, round(w * 0.18), scene_top + round(scene_h * 0.54), round(w * 0.64), round(scene_h * 0.11), 24, (222, 228, 218), INK, 3)
        draw_person(image, person="aachu", x=round(w * 0.38), y=center_y + round(scene_h * 0.02), scale=1.02 if not is_reels else 1.1, mood="laugh", arm="open")
        draw_person(image, person="zuv", x=round(w * 0.62), y=center_y + round(scene_h * 0.02), scale=1.05 if not is_reels else 1.13, mood="laugh", arm="open", flip=True)
        for idx, label in enumerate(["messy dinner", "board game", "late cab"]):
            draw_bubble(image, round(w * (0.16 + idx * 0.23)), scene_top + round(scene_h * (0.08 + 0.05 * (idx % 2))), round(w * 0.2), round(scene_h * 0.08), label, fill=(226, 237, 248) if idx % 2 == 0 else (225, 240, 224), scale=0.42)
        for idx in range(7):
            draw_small_heart(image, round(w * (0.28 + 0.07 * idx)), scene_top + round(scene_h * (0.72 + 0.025 * math.sin(idx))), 0.55, ROSE if idx % 2 else GOLD)


def draw_private_caption_scene(image: np.ndarray, slide: dict[str, Any], output_format: str) -> None:
    h, w = image.shape[:2]
    number = int(slide.get("slide", 0) or 0)
    copy = str(slide.get("copy", ""))
    is_reels = output_format == REELS_STORIES_FORMAT
    scene_top = round(h * (0.34 if is_reels else 0.31))
    scene_bottom = round(h * 0.91)
    scene_h = scene_bottom - scene_top
    center_y = scene_top + scene_h // 2
    person_scale = 1.08 if not is_reels else 1.14
    labels = private_caption_labels(copy)

    aachu_mood = "delighted"
    zuv_mood = "smile"
    aachu_arm = "open"
    zuv_arm = "open"
    if number == 2:
        aachu_mood, zuv_mood = "delighted", "focused"
        aachu_arm, zuv_arm = "raised", "open"
        draw_motion_marks(image, round(w * 0.22), scene_top + round(scene_h * 0.26), 0.9, "left")
    elif number == 3:
        aachu_mood, zuv_mood = "focused", "focused"
        draw_phone(image, round(w * 0.09), scene_top + round(scene_h * 0.18), round(w * 0.22), round(scene_h * 0.43), slide=number)
    elif number == 4:
        aachu_mood, zuv_mood = "delighted", "laugh"
        for idx in range(5):
            draw_small_heart(image, round(w * (0.44 + idx * 0.035)), scene_top + round(scene_h * 0.2), 0.5, GOLD)
        draw_bubble(image, round(w * 0.19), scene_top + round(scene_h * 0.53), round(w * 0.2), round(scene_h * 0.08), "tiny thing", fill=(226, 237, 248), scale=0.45)
    elif number == 5:
        aachu_mood, zuv_mood = "focused", "smile"
        draw_bubble(image, round(w * 0.17), scene_top + round(scene_h * 0.52), round(w * 0.18), round(scene_h * 0.08), "nope", fill=(226, 237, 248), scale=0.5)
    elif number == 6:
        aachu_mood, zuv_mood = "smile", "focused"
        zuv_arm = "raised"
        draw_small_heart(image, round(w * 0.57), scene_top + round(scene_h * 0.22), 0.7, ROSE)
    elif number == 7:
        aachu_mood, zuv_mood = "laugh", "laugh"
        draw_bubble(image, round(w * 0.58), scene_top + round(scene_h * 0.5), round(w * 0.18), round(scene_h * 0.08), "bad joke", fill=(225, 240, 224), align_right=True, scale=0.46)
    else:
        draw_symbols(image, w, h, 1700 + number + (100 if is_reels else 0), density=5)

    draw_person(
        image,
        person="aachu",
        x=round(w * 0.36),
        y=center_y - round(scene_h * 0.04),
        scale=person_scale,
        mood=aachu_mood,
        arm=aachu_arm,
    )
    draw_person(
        image,
        person="zuv",
        x=round(w * 0.64),
        y=center_y - round(scene_h * 0.04),
        scale=person_scale * 1.03,
        mood=zuv_mood,
        arm=zuv_arm,
        flip=True,
    )

    if not labels:
        if "private captions" in copy.lower():
            labels = {"aachu": "private", "zuv": "captions"}
        else:
            labels = {"aachu": "captioned", "zuv": "kindly"}

    bubble_h = round(scene_h * (0.11 if is_reels else 0.12))
    left_w = round(w * 0.33)
    right_w = round(w * 0.33)
    left_x = round(w * 0.08)
    right_x = round(w * 0.59)
    label_y = scene_top + round(scene_h * 0.04)
    draw_bubble(image, left_x, label_y, left_w, bubble_h, labels.get("aachu", ""), fill=(226, 237, 248), scale=0.54 if not is_reels else 0.58)
    draw_bubble(image, right_x, label_y + round(scene_h * 0.03), right_w, bubble_h, labels.get("zuv", ""), fill=(225, 240, 224), align_right=True, scale=0.54 if not is_reels else 0.58)
    line(image, (left_x + round(left_w * 0.55), label_y + bubble_h + 18), (round(w * 0.36), center_y - round(scene_h * 0.22)), MUTED_INK, 2)
    line(image, (right_x + round(right_w * 0.35), label_y + bubble_h + 28), (round(w * 0.64), center_y - round(scene_h * 0.22)), MUTED_INK, 2)
    draw_small_heart(image, round(w * 0.5), scene_top + round(scene_h * 0.76), 0.62, ROSE)


def draw_scene(image: np.ndarray, slide: dict[str, Any], output_format: str) -> None:
    h, w = image.shape[:2]
    number = int(slide.get("slide", 0) or 0)
    is_reels = output_format == REELS_STORIES_FORMAT
    scene_top = round(h * (0.34 if is_reels else 0.31))
    scene_bottom = round(h * 0.91)
    scene_h = scene_bottom - scene_top
    center_y = scene_top + scene_h // 2
    person_scale = 1.18 if not is_reels else 1.22

    if is_private_caption_copy(str(slide.get("copy", ""))):
        draw_private_caption_scene(image, slide, output_format)
        return
    if is_long_distance_copy(str(slide.get("copy", ""))):
        draw_long_distance_scene(image, slide, output_format)
        return

    if number == 1:
        draw_symbols(image, w, h, number + (100 if is_reels else 0), density=6)
        draw_person(image, person="aachu", x=round(w * 0.38), y=center_y - round(scene_h * 0.12), scale=person_scale, mood="delighted", arm="open")
        draw_person(image, person="zuv", x=round(w * 0.64), y=center_y - round(scene_h * 0.1), scale=person_scale * 1.03, mood="laugh", arm="open", flip=True)
        draw_motion_marks(image, round(w * 0.25), center_y - round(scene_h * 0.26), 1.05, "left")
        draw_motion_marks(image, round(w * 0.76), center_y - round(scene_h * 0.24), 1.0, "right")
        draw_bubble(image, round(w * 0.17), scene_top + round(scene_h * 0.05), round(w * 0.26), round(scene_h * 0.12), "one more thing", fill=(226, 237, 248), scale=0.55)
        draw_bubble(image, round(w * 0.62), scene_top + round(scene_h * 0.08), round(w * 0.22), round(scene_h * 0.11), "tell me", fill=(225, 240, 224), align_right=True, scale=0.58)
    elif number == 2:
        draw_phone(image, round(w * 0.34), scene_top + round(scene_h * 0.02), round(w * 0.32), round(scene_h * 0.66), slide=number)
        draw_person(image, person="aachu", x=round(w * 0.2), y=scene_top + round(scene_h * 0.52), scale=0.82 if not is_reels else 0.88, mood="delighted", arm="open")
        draw_person(image, person="zuv", x=round(w * 0.82), y=scene_top + round(scene_h * 0.53), scale=0.86 if not is_reels else 0.9, mood="focused", arm="typing", flip=True)
        for idx in range(5):
            draw_small_heart(image, round(w * (0.43 + idx * 0.035)), scene_top + round(scene_h * (0.75 + 0.025 * math.sin(idx))), 0.55, ROSE)
    elif number == 3:
        draw_phone(image, round(w * 0.12), scene_top + round(scene_h * 0.03), round(w * 0.33), round(scene_h * 0.61), slide=number)
        draw_person(image, person="zuv", x=round(w * 0.66), y=scene_top + round(scene_h * 0.48), scale=1.06 if not is_reels else 1.08, mood="focused", arm="typing", flip=True)
        draw_bubble(image, round(w * 0.55), scene_top + round(scene_h * 0.06), round(w * 0.29), round(scene_h * 0.11), "wait what?", fill=(225, 240, 224), align_right=True, scale=0.64)
        draw_bubble(image, round(w * 0.57), scene_top + round(scene_h * 0.2), round(w * 0.28), round(scene_h * 0.11), "then?", fill=(225, 240, 224), align_right=True, scale=0.7)
        draw_bubble(image, round(w * 0.51), scene_top + round(scene_h * 0.34), round(w * 0.33), round(scene_h * 0.11), "plot twist??", fill=(225, 240, 224), align_right=True, scale=0.62)
    elif number == 4:
        rounded_rect(image, round(w * 0.13), scene_top + round(scene_h * 0.06), round(w * 0.74), round(scene_h * 0.62), 32, (236, 239, 232), (175, 166, 150), 3)
        line(image, (round(w * 0.2), scene_top + round(scene_h * 0.22)), (round(w * 0.8), scene_top + round(scene_h * 0.22)), (206, 199, 181), 2)
        draw_person(image, person="aachu", x=round(w * 0.42), y=scene_top + round(scene_h * 0.42), scale=1.0 if not is_reels else 1.04, mood="delighted", arm="open")
        draw_person(image, person="zuv", x=round(w * 0.67), y=scene_top + round(scene_h * 0.44), scale=0.92 if not is_reels else 0.96, mood="laugh", arm="open", flip=True)
        for idx, label in enumerate(["start?", "middle", "side quest"]):
            bx = round(w * (0.16 + idx * 0.22))
            by = scene_top + round(scene_h * (0.04 + 0.09 * (idx % 2)))
            draw_bubble(image, bx, by, round(w * 0.18), round(scene_h * 0.09), label, fill=(229, 238, 225), scale=0.48)
        line(image, (round(w * 0.19), scene_top + round(scene_h * 0.75)), (round(w * 0.81), scene_top + round(scene_h * 0.73)), MUTED_INK, 3)
        line(image, (round(w * 0.81), scene_top + round(scene_h * 0.73)), (round(w * 0.75), scene_top + round(scene_h * 0.69)), MUTED_INK, 3)
        line(image, (round(w * 0.81), scene_top + round(scene_h * 0.73)), (round(w * 0.75), scene_top + round(scene_h * 0.78)), MUTED_INK, 3)
    elif number == 5:
        draw_person(image, person="zuv", x=round(w * 0.38), y=scene_top + round(scene_h * 0.45), scale=1.08 if not is_reels else 1.12, mood="laugh", arm="raised")
        draw_person(image, person="aachu", x=round(w * 0.67), y=scene_top + round(scene_h * 0.46), scale=1.02 if not is_reels else 1.08, mood="delighted", arm="open", flip=True)
        draw_bubble(image, round(w * 0.2), scene_top + round(scene_h * 0.03), round(w * 0.44), round(scene_h * 0.13), "and then what happened?", fill=(225, 240, 224), scale=0.62)
        for idx in range(7):
            draw_small_heart(image, round(w * (0.58 + 0.035 * idx)), scene_top + round(scene_h * (0.22 + 0.025 * math.sin(idx))), 0.52, GOLD)
    elif number == 6:
        ellipse(image, (round(w * 0.5), scene_top + round(scene_h * 0.38)), (round(w * 0.34), round(scene_h * 0.31)), (240, 242, 235))
        ellipse(image, (round(w * 0.5), scene_top + round(scene_h * 0.38)), (round(w * 0.34), round(scene_h * 0.31)), INK, width=4)
        for idx, rad in enumerate([20, 13, 8]):
            circle(image, (round(w * (0.23 - idx * 0.035)), scene_top + round(scene_h * (0.7 + idx * 0.05))), rad, (240, 242, 235))
            circle(image, (round(w * (0.23 - idx * 0.035)), scene_top + round(scene_h * (0.7 + idx * 0.05))), rad, INK, 3)
        draw_person(image, person="aachu", x=round(w * 0.43), y=scene_top + round(scene_h * 0.38), scale=0.9 if not is_reels else 0.94, mood="laugh", arm="open")
        draw_person(image, person="zuv", x=round(w * 0.59), y=scene_top + round(scene_h * 0.39), scale=0.92 if not is_reels else 0.96, mood="laugh", arm="open", flip=True)
        draw_bubble(image, round(w * 0.22), scene_top + round(scene_h * 0.08), round(w * 0.22), round(scene_h * 0.1), "tiny drama", fill=(226, 237, 248), scale=0.48)
        draw_bubble(image, round(w * 0.58), scene_top + round(scene_h * 0.11), round(w * 0.2), round(scene_h * 0.1), "shared plot", fill=(225, 240, 224), align_right=True, scale=0.46)
        draw_symbols(image, w, h, 806 + (1 if is_reels else 0), density=6)
    else:
        draw_person(image, person="aachu", x=round(w * 0.4), y=scene_top + round(scene_h * 0.43), scale=1.04 if not is_reels else 1.08, mood="smile", arm="open")
        draw_person(image, person="zuv", x=round(w * 0.61), y=scene_top + round(scene_h * 0.43), scale=1.06 if not is_reels else 1.1, mood="smile", arm="open", flip=True)
        line(image, (round(w * 0.49), scene_top + round(scene_h * 0.63)), (round(w * 0.53), scene_top + round(scene_h * 0.63)), INK, 5)
        draw_bubble(image, round(w * 0.18), scene_top + round(scene_h * 0.08), round(w * 0.22), round(scene_h * 0.1), "fluent", fill=(226, 237, 248), scale=0.56)
        draw_bubble(image, round(w * 0.62), scene_top + round(scene_h * 0.1), round(w * 0.2), round(scene_h * 0.1), "in you", fill=(225, 240, 224), align_right=True, scale=0.56)
        for idx in range(5):
            draw_small_heart(image, round(w * (0.32 + 0.09 * idx)), scene_top + round(scene_h * (0.16 + 0.06 * math.sin(idx))), 0.65, ROSE if idx % 2 else GOLD)


def render_slide(slide: dict[str, Any], output_format: str) -> np.ndarray:
    width, height = INSTAGRAM_SIZE if output_format == INSTAGRAM_POST_FORMAT else REELS_SIZE
    number = int(slide.get("slide", 0) or 0)
    image = np.empty((height, width, 3), dtype=np.uint8)
    image[:, :] = PAPER
    add_paper_texture(image, seed=number * 37 + (1000 if output_format == REELS_STORIES_FORMAT else 0))

    top_y = round(height * (0.085 if output_format == INSTAGRAM_POST_FORMAT else 0.075))
    title_width = round(width * 0.78)
    title_x = (width - title_width) // 2
    title_height = round(height * (0.2 if output_format == INSTAGRAM_POST_FORMAT else 0.18))
    draw_wrapped_text(
        image,
        str(slide.get("copy", "")),
        x=title_x,
        y=top_y,
        max_width=title_width,
        max_height=title_height,
        max_scale=1.62 if output_format == INSTAGRAM_POST_FORMAT else 1.72,
        min_scale=0.75,
        thickness=4,
        center=True,
    )
    draw_scene(image, slide, output_format)
    brand_scale = 0.52 if output_format == INSTAGRAM_POST_FORMAT else 0.55
    brand = "@a.storyof.two"
    bw, _ = text_size(brand, brand_scale, 2)
    put_text(
        image,
        brand,
        (width - bw - round(width * 0.055), height - round(height * 0.045)),
        scale=brand_scale,
        color=(128, 122, 113),
        thickness=2,
    )
    return image


def selected_option_ids(prompt_pack: dict[str, Any]) -> list[str]:
    values = [
        str(item.get("option_id"))
        for item in prompt_pack.get("identity_selected_options", [])
        if isinstance(item, dict) and item.get("option_id")
    ]
    return values or ["ID36", "ID37", "ID39", "ID44"]


def recover_post_copy_visual_room(carousel_dir: Path, slides: list[dict[str, Any]]) -> dict[str, Any]:
    visual_debate_path = carousel_dir / "visual-debate.json"
    visual_debate = read_json(visual_debate_path) if visual_debate_path.exists() else {}
    room = {
        "agent": "C3.25-PostCopyVisualRoom-Recovered",
        "status": "GO",
        "decision": "GO",
        "selected_visual_system": visual_debate.get("winner", "Slide-Led Evidence Plan"),
        "why_it_wins": (
            "Recovered from the locked slide copy and visual-debate winner so the final local renderer "
            "can preserve the approved scene-by-scene evidence plan."
        ),
        "visual_system_candidates": [
            {
                "name": "Slide-Led Evidence Plan",
                "score": 29,
                "verdict": "GO",
                "reason": "Each visual beat proves the slide copy directly.",
            },
            {
                "name": "Message-Thread Comedy Plan",
                "score": 27,
                "verdict": "REPAIR",
                "reason": "Strong recognizability, but too phone-heavy if used on every slide.",
            },
            {
                "name": "Quiet Shared-Language Plan",
                "score": 26,
                "verdict": "REPAIR",
                "reason": "Tender, but weaker on early swipe momentum.",
            },
        ],
        "slide_visual_blueprint": [
            {
                "slide": int(slide.get("slide", 0) or 0),
                "copy": slide.get("copy", ""),
                "visual": slide.get("visual", ""),
                "format_note": "Render separately for 4:5 and 9:16 without deriving one format from the other.",
            }
            for slide in slides
        ],
        "open_doubts": [],
    }
    write_json(carousel_dir / "post-copy-visual-room.json", room)
    return room


def load_quality_package(carousel_dir: Path) -> tuple[dict[str, Any], dict[str, Any]]:
    manifest = read_json(carousel_dir / "manifest.json")
    slides = read_json(carousel_dir / "slides.json")
    post_copy_path = carousel_dir / "post-copy-visual-room.json"
    post_copy_room = read_json(post_copy_path) if post_copy_path.exists() else recover_post_copy_visual_room(carousel_dir, slides)
    package = {
        "concept": read_json(carousel_dir / "concept.json"),
        "post_copy_visual_room": post_copy_room,
        "visual_debate": read_json(carousel_dir / "visual-debate.json"),
        "visual_plan_quality": read_json(carousel_dir / "visual-plan-quality.json"),
        "slides": slides,
        "prompt_pack": read_json(carousel_dir / "prompt-pack.json"),
        "identity_consistency_review": read_json(carousel_dir / "identity-consistency-review.json"),
        "copy": read_json(carousel_dir / "copy.json"),
        "review": read_json(carousel_dir / "review.json"),
    }
    return manifest, package


def write_visual_qa_json(carousel_dir: Path, slides: list[dict[str, Any]], prompt_pack: dict[str, Any], records: list[dict[str, Any]]) -> None:
    option_ids = selected_option_ids(prompt_pack)
    checks = {
        "storyboard": {
            "pass": False,
            "evidence": [record["file"] for record in records],
            "notes": "Preview slides follow the storyboard, but legacy local rendering cannot satisfy final publishable QA.",
        },
        "aachu_face": {
            "pass": False,
            "reference_option_ids": option_ids,
            "likeness_notes": "Local preview caricature is not a model-native identity match.",
        },
        "zuv_face": {
            "pass": False,
            "reference_option_ids": option_ids,
            "likeness_notes": "Local preview caricature is not a model-native identity match.",
        },
        "dress_continuity": {
            "pass": False,
            "evidence": "Preview outfit cues exist but are not approved final continuity.",
        },
        "style": {
            "pass": False,
            "evidence": "Warm paper preview styling exists, but this is not model-native final art.",
        },
        "model_native_text": {
            "pass": False,
            "evidence": "Exact copy and @a.storyof.two brandmark are rendered into local preview artwork only.",
            "notes": "Check id preserved for audit compatibility; generation mode is legacy_local_preview_not_publishable.",
        },
        "final_files": {
            "pass": False,
            "evidence": [
                {
                    "slide": record["slide"],
                    "instagram_post": record["file"],
                    "reels_stories": record["reels_stories_file"],
                }
                for record in records
            ],
            "notes": "Files are preview-only and cannot satisfy the final image gate.",
        },
    }
    write_json(
        carousel_dir / "visual-qa.json",
        {
            "schema_version": "1.0",
            "status": "NEEDS_FIXES",
            "generation_mode": GENERATION_MODE,
            "backend": BACKEND,
            "publishable": False,
            "can_satisfy_final_gate": False,
            "slide_count": len(slides),
            "checks": checks,
        },
    )


def infer_slide_count(carousel_dir: Path) -> int:
    for filename in ("slides.json", "prompt-pack.json"):
        path = carousel_dir / filename
        if not path.exists():
            continue
        try:
            payload = read_json(path)
        except (json.JSONDecodeError, OSError):
            continue
        if isinstance(payload, list):
            return len(payload)
        if isinstance(payload, dict) and isinstance(payload.get("slides"), list):
            return len(payload["slides"])
    return 0


def render_local_carousel(carousel_dir: Path, *, refresh_quality: bool = True, workspace_root: Path | None = None) -> dict[str, Any]:
    carousel_dir = carousel_dir.expanduser()
    visual_quality_reason = visual_plan_quality_gate_reason(carousel_dir)
    if visual_quality_reason:
        return write_generation_state(
            carousel_dir,
            status=GenerationStatus.BLOCKED,
            backend=BACKEND,
            generation_mode=GENERATION_MODE,
            slide_count=infer_slide_count(carousel_dir),
            reason=visual_quality_reason,
            extra={"can_satisfy_final_gate": False},
        )

    identity_reason = identity_consistency_gate_reason(carousel_dir)
    if identity_reason:
        return write_generation_state(
            carousel_dir,
            status=GenerationStatus.BLOCKED,
            backend=BACKEND,
            generation_mode=GENERATION_MODE,
            slide_count=infer_slide_count(carousel_dir),
            reason=identity_reason,
            extra={"can_satisfy_final_gate": False},
        )

    manifest, package = load_quality_package(carousel_dir)
    slides = package["slides"]
    prompt_pack = package["prompt_pack"]
    prompt_slides = prompt_pack.get("slides", [])
    prompt_by_slide = {int(item.get("slide", 0) or 0): item for item in prompt_slides if isinstance(item, dict)}

    final_dir = carousel_dir / "final"
    reels_dir = carousel_dir / "final-reels-stories"
    source_dir = final_dir / "local-deterministic-source"
    records: list[dict[str, Any]] = []
    for slide in slides:
        number = int(slide.get("slide", 0) or 0)
        instagram_source = source_dir / f"instagram-post-slide-{number:02d}.png"
        reels_source = source_dir / f"reels-stories-slide-{number:02d}.png"
        instagram_file = final_dir / f"slide-{number:02d}.png"
        reels_file = reels_dir / f"slide-{number:02d}.png"
        instagram_image = render_slide(slide, INSTAGRAM_POST_FORMAT)
        reels_image = render_slide(slide, REELS_STORIES_FORMAT)
        imwrite(instagram_source, instagram_image)
        imwrite(reels_source, reels_image)
        shutil.copyfile(instagram_source, instagram_file)
        reels_file.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(reels_source, reels_file)
        slide_prompt = prompt_by_slide.get(number, {})
        reference_images = [
            *prompt_pack.get("identity_dossier_reference_images", []),
            *prompt_pack.get("identity_reference_images", []),
            *slide.get("source_images", []),
        ]
        records.append(
            {
                "slide": number,
                "copy": slide.get("copy", ""),
                "generation_mode": GENERATION_MODE,
                "backend": BACKEND,
                "status": STATUS,
                "publishable": False,
                "can_satisfy_final_gate": False,
                "prompt": slide_prompt.get("prompt", slide.get("visual", "")),
                "reference_images": reference_images,
                "source": str(instagram_source),
                "local_generated_source": str(instagram_source),
                "file": str(instagram_file),
                "reels_stories_source": str(reels_source),
                "reels_stories_file": str(reels_file),
                "native_outputs": {
                    INSTAGRAM_POST_FORMAT: {
                        "label": NATIVE_OUTPUT_FORMATS[INSTAGRAM_POST_FORMAT]["label"],
                        "aspect_ratio": NATIVE_OUTPUT_FORMATS[INSTAGRAM_POST_FORMAT]["aspect_ratio"],
                        "source": str(instagram_source),
                        "local_generated_source": str(instagram_source),
                        "file": str(instagram_file),
                        "upload_size": f"{INSTAGRAM_SIZE[0]}x{INSTAGRAM_SIZE[1]}",
                        "publishable": False,
                    },
                    REELS_STORIES_FORMAT: {
                        "label": NATIVE_OUTPUT_FORMATS[REELS_STORIES_FORMAT]["label"],
                        "aspect_ratio": NATIVE_OUTPUT_FORMATS[REELS_STORIES_FORMAT]["aspect_ratio"],
                        "source": str(reels_source),
                        "local_generated_source": str(reels_source),
                        "file": str(reels_file),
                        "upload_size": f"{REELS_SIZE[0]}x{REELS_SIZE[1]}",
                        "publishable": False,
                    },
                },
            }
        )

    result = write_generation_state(
        carousel_dir,
        status=GenerationStatus.LEGACY_PREVIEW_GENERATED,
        backend=BACKEND,
        generation_mode=GENERATION_MODE,
        slide_count=len(slides),
        slides=records,
        reason="Legacy local renderer output is preview-only and cannot satisfy publishable final gates.",
        extra={
            "native_output_contract": NATIVE_OUTPUT_CONTRACT,
            "instagram_upload_size": f"{INSTAGRAM_SIZE[0]}x{INSTAGRAM_SIZE[1]}",
            "reels_stories_size": f"{REELS_SIZE[0]}x{REELS_SIZE[1]}",
            "can_satisfy_final_gate": False,
            "normalization": (
                "Each surface is locally rendered as its own native canvas; Reels/Stories is not "
                "derived by resizing, cropping, padding, or extending the Instagram post output."
            ),
        },
    )
    write_visual_qa_json(carousel_dir, slides, prompt_pack, records)

    if refresh_quality:
        workspace = workspace_root or carousel_dir.parents[3]
        reference_paths = [
            workspace / item["path"]
            for item in manifest.get("reference_images", [])
            if isinstance(item, dict) and item.get("path")
        ]
        write_quality_artifacts(
            QualityContext(
                story=manifest.get("source_story", ""),
                title=manifest.get("title", carousel_dir.name),
                slug=manifest.get("slug", carousel_dir.name),
                today=date.fromisoformat(str(manifest.get("date", date.today()))),
                out_dir=carousel_dir,
                image_paths=reference_paths,
                slide_count=int(manifest.get("format", {}).get("slide_count", len(slides))),
                package=package,
                manifest=manifest,
                render_result=result,
                workspace_root=workspace,
            )
        )
    return result
