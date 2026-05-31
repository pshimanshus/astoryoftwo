from __future__ import annotations

import argparse
import math
from pathlib import Path

import cv2
import numpy as np


WIDTH = 1003
HEIGHT = 1568
FPS = 30
DURATION_SECONDS = 6


PROTECTED_RECTS = (
    (310, 190, 700, 575),  # handwritten copy
    (125, 650, 855, 1290),  # faces, hair, and hand-focus area
    (740, 1395, 980, 1545),  # brandmark corner
)


PETALS = (
    # x, start y, size, speed px/s, sway, rotation, opacity, phase
    (95, -90, 34, 40, 10, -24, 0.34, 0.02),
    (185, -245, 44, 33, 16, 18, 0.32, 0.23),
    (258, -390, 28, 45, 12, -12, 0.22, 0.41),
    (765, -170, 24, 36, 13, 20, 0.18, 0.16),
    (866, -35, 46, 38, 14, -30, 0.34, 0.51),
    (942, -320, 32, 42, 11, 28, 0.26, 0.69),
    (72, 420, 22, 32, 8, -18, 0.18, 0.78),
    (906, 810, 38, 34, 10, 16, 0.24, 0.36),
)


def ease_in_out(value: float) -> float:
    return 0.5 - 0.5 * math.cos(math.pi * value)


def ping_pong(progress: float) -> float:
    if progress <= 0.5:
        return ease_in_out(progress * 2)
    return ease_in_out((1 - progress) * 2)


def in_protected_area(x: float, y: float) -> bool:
    for left, top, right, bottom in PROTECTED_RECTS:
        if left <= x <= right and top <= y <= bottom:
            return True
    return False


def make_hand_mask(height: int, width: int) -> np.ndarray:
    mask = np.zeros((height, width), dtype=np.uint8)

    palm_and_fingers = np.array(
        [
            [434, 1120],
            [464, 1050],
            [510, 996],
            [558, 952],
            [606, 908],
            [641, 882],
            [661, 898],
            [649, 940],
            [622, 986],
            [582, 1032],
            [535, 1079],
            [484, 1122],
        ],
        dtype=np.int32,
    )
    thumb = np.array(
        [
            [523, 996],
            [573, 960],
            [614, 936],
            [626, 954],
            [590, 990],
            [538, 1020],
        ],
        dtype=np.int32,
    )

    cv2.fillPoly(mask, [palm_and_fingers], 255)
    cv2.fillPoly(mask, [thumb], 220)
    cv2.ellipse(mask, (525, 1054), (82, 48), -34, 0, 360, 230, -1)
    cv2.ellipse(mask, (592, 948), (78, 22), -41, 0, 360, 230, -1)
    cv2.ellipse(mask, (612, 920), (52, 14), -39, 0, 360, 205, -1)

    mask = cv2.GaussianBlur(mask, (61, 61), 0)
    return np.clip(mask.astype(np.float32) / 255.0, 0.0, 1.0)


def make_petal_sprite(size: int, color_shift: float) -> np.ndarray:
    canvas_w = int(size * 2.0)
    canvas_h = int(size * 1.25)
    rgb = np.zeros((canvas_h, canvas_w, 3), dtype=np.float32)

    cx = canvas_w // 2
    cy = canvas_h // 2
    pts = np.array(
        [
            [cx - size * 0.9, cy + size * 0.03],
            [cx - size * 0.45, cy - size * 0.48],
            [cx + size * 0.2, cy - size * 0.42],
            [cx + size * 0.88, cy - size * 0.03],
            [cx + size * 0.36, cy + size * 0.42],
            [cx - size * 0.42, cy + size * 0.36],
        ],
        dtype=np.int32,
    )

    peach = np.array([112, 143, 218], dtype=np.float32)
    rose = np.array([120, 118, 210], dtype=np.float32)
    fill = peach * (1 - color_shift) + rose * color_shift
    edge = np.array([72, 88, 135], dtype=np.float32)

    alpha = np.zeros((canvas_h, canvas_w), dtype=np.uint8)
    cv2.fillPoly(alpha, [pts], 210)
    alpha = cv2.GaussianBlur(alpha, (9, 9), 0)

    rgb[:, :, :] = fill

    cv2.polylines(rgb, [pts], True, edge.tolist(), 1, cv2.LINE_AA)
    cv2.line(
        rgb,
        (int(cx - size * 0.62), cy),
        (int(cx + size * 0.72), int(cy - size * 0.02)),
        edge.tolist(),
        1,
        cv2.LINE_AA,
    )
    inner = np.zeros((canvas_h, canvas_w), dtype=np.uint8)
    cv2.ellipse(
        inner,
        (cx, cy),
        (int(size * 0.42), int(size * 0.18)),
        -8,
        0,
        360,
        70,
        -1,
    )
    rgb = (
        rgb * (1 - inner[:, :, None] / 255 * 0.28)
        + np.array([155, 178, 238], dtype=np.float32)
        * (inner[:, :, None] / 255 * 0.28)
    )
    sprite = np.dstack((rgb, alpha.astype(np.float32) / 255.0))
    return sprite


def rotate_sprite(sprite: np.ndarray, angle: float) -> np.ndarray:
    height, width = sprite.shape[:2]
    center = (width / 2, height / 2)
    matrix = cv2.getRotationMatrix2D(center, angle, 1.0)
    cos = abs(matrix[0, 0])
    sin = abs(matrix[0, 1])
    new_width = int(height * sin + width * cos)
    new_height = int(height * cos + width * sin)
    matrix[0, 2] += new_width / 2 - center[0]
    matrix[1, 2] += new_height / 2 - center[1]
    return cv2.warpAffine(
        sprite,
        matrix,
        (new_width, new_height),
        flags=cv2.INTER_LINEAR,
        borderMode=cv2.BORDER_CONSTANT,
        borderValue=(0, 0, 0, 0),
    )


def composite_rgba(frame: np.ndarray, sprite: np.ndarray, x: float, y: float, opacity: float) -> None:
    sprite_h, sprite_w = sprite.shape[:2]
    left = int(round(x - sprite_w / 2))
    top = int(round(y - sprite_h / 2))
    right = left + sprite_w
    bottom = top + sprite_h

    clip_left = max(0, left)
    clip_top = max(0, top)
    clip_right = min(frame.shape[1], right)
    clip_bottom = min(frame.shape[0], bottom)
    if clip_left >= clip_right or clip_top >= clip_bottom:
        return

    sx1 = clip_left - left
    sy1 = clip_top - top
    sx2 = sx1 + (clip_right - clip_left)
    sy2 = sy1 + (clip_bottom - clip_top)

    patch = sprite[sy1:sy2, sx1:sx2]
    alpha = (patch[:, :, 3:4] * opacity).clip(0, 1)
    frame[clip_top:clip_bottom, clip_left:clip_right] = (
        frame[clip_top:clip_bottom, clip_left:clip_right] * (1 - alpha)
        + patch[:, :, :3] * alpha
    )


def apply_falling_petals(frame: np.ndarray, frame_index: int, total_frames: int) -> None:
    duration = total_frames / FPS
    t = frame_index / FPS
    travel_height = HEIGHT + 520

    for idx, (x, start_y, size, speed, sway, base_rotation, opacity, phase) in enumerate(PETALS):
        y = ((start_y + speed * t + 260) % travel_height) - 260
        drift = sway * math.sin((t * 0.42 + phase) * math.tau)
        flutter = 8 * math.sin((t * 0.75 + phase * 1.7) * math.tau)
        petal_x = x + drift
        petal_y = y
        if in_protected_area(petal_x, petal_y):
            continue

        angle = base_rotation + flutter + 12 * math.sin((t * 0.28 + phase) * math.tau)
        sprite = make_petal_sprite(int(size), color_shift=0.25 + 0.2 * (idx % 3))
        rotated = rotate_sprite(sprite, angle)
        edge_fade = 1.0
        if petal_y < 40:
            edge_fade = max(0.0, petal_y / 40)
        elif petal_y > HEIGHT - 60:
            edge_fade = max(0.0, (HEIGHT - petal_y) / 60)
        composite_rgba(frame, rotated, petal_x, petal_y, opacity * edge_fade)


def apply_hand_lift(base: np.ndarray, clean: np.ndarray, hand_mask: np.ndarray, progress: float) -> np.ndarray:
    lift = ping_pong(progress)
    if lift < 0.001:
        return base.copy()

    dx = 5.0 * lift
    dy = -14.0 * lift
    rotation = -1.1 * lift
    center = (468, 1105)

    matrix = cv2.getRotationMatrix2D(center, rotation, 1.0)
    matrix[0, 2] += dx
    matrix[1, 2] += dy

    hand_alpha = hand_mask[:, :, None]
    premultiplied_hand = base * hand_alpha
    shifted_hand = cv2.warpAffine(
        premultiplied_hand,
        matrix,
        (base.shape[1], base.shape[0]),
        flags=cv2.INTER_LINEAR,
        borderMode=cv2.BORDER_REFLECT,
    )
    shifted_alpha = cv2.warpAffine(
        hand_mask,
        matrix,
        (base.shape[1], base.shape[0]),
        flags=cv2.INTER_LINEAR,
        borderMode=cv2.BORDER_CONSTANT,
        borderValue=0,
    )[:, :, None]

    original_hide = hand_alpha * (0.62 * lift)
    frame = base * (1 - original_hide) + clean * original_hide

    overlay_alpha = np.clip(shifted_alpha * (0.86 * lift), 0.0, 1.0)
    frame = frame * (1 - overlay_alpha) + shifted_hand * overlay_alpha
    return frame


def render(base_path: Path, output_path: Path, preview_dir: Path) -> None:
    base_bgr = cv2.imread(str(base_path), cv2.IMREAD_COLOR)
    if base_bgr is None:
        raise FileNotFoundError(base_path)
    if base_bgr.shape[1] != WIDTH or base_bgr.shape[0] != HEIGHT:
        raise ValueError(f"Expected {WIDTH}x{HEIGHT}, got {base_bgr.shape[1]}x{base_bgr.shape[0]}")

    base = base_bgr.astype(np.float32)
    hand_mask = make_hand_mask(HEIGHT, WIDTH)
    inpaint_mask = (hand_mask > 0.17).astype(np.uint8) * 255
    clean = cv2.inpaint(base_bgr, inpaint_mask, 3, cv2.INPAINT_TELEA).astype(np.float32)

    total_frames = FPS * DURATION_SECONDS
    output_path.parent.mkdir(parents=True, exist_ok=True)
    preview_dir.mkdir(parents=True, exist_ok=True)

    writer = None
    for codec in ("mp4v", "avc1"):
        fourcc = cv2.VideoWriter_fourcc(*codec)
        candidate = cv2.VideoWriter(str(output_path), fourcc, FPS, (WIDTH, HEIGHT))
        if candidate.isOpened():
            writer = candidate
            break
        candidate.release()
    if writer is None:
        raise RuntimeError("OpenCV could not open an MP4 writer.")

    preview_frames = {0, total_frames // 2, total_frames - 1}
    for frame_index in range(total_frames):
        progress = frame_index / total_frames
        frame = apply_hand_lift(base, clean, hand_mask, progress)
        apply_falling_petals(frame, frame_index, total_frames)

        frame_u8 = np.clip(frame, 0, 255).astype(np.uint8)
        writer.write(frame_u8)
        if frame_index in preview_frames:
            cv2.imwrite(str(preview_dir / f"falling-petals-hand-frame-{frame_index:03d}.png"), frame_u8)

    writer.release()


def main() -> None:
    parser = argparse.ArgumentParser(description="Render a subtle falling-petals hand-lift loop.")
    parser.add_argument("--base", type=Path, default=Path("frame-03.png"))
    parser.add_argument("--output", type=Path, default=Path("tum-toh-dil-ho-falling-petals-hand.mp4"))
    parser.add_argument("--preview-dir", type=Path, default=Path("python-preview-frames"))
    args = parser.parse_args()

    render(args.base, args.output, args.preview_dir)


if __name__ == "__main__":
    main()
