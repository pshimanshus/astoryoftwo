from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from typing import Any

import cv2
import numpy as np


def ease_in_out(value: float) -> float:
    value = max(0.0, min(1.0, value))
    return 0.5 - 0.5 * math.cos(math.pi * value)


def lift_then_return(progress: float) -> float:
    if progress <= 0.5:
        return ease_in_out(progress * 2)
    return ease_in_out((1 - progress) * 2)


def make_hand_mask(height: int, width: int) -> np.ndarray:
    mask = np.zeros((height, width), dtype=np.uint8)

    palm = np.array(
        [
            [410, 1138],
            [432, 1088],
            [466, 1038],
            [512, 991],
            [562, 948],
            [608, 907],
            [648, 881],
            [676, 892],
            [668, 929],
            [637, 977],
            [590, 1032],
            [534, 1085],
            [478, 1128],
        ],
        dtype=np.int32,
    )
    fingers = np.array(
        [
            [512, 1001],
            [558, 964],
            [612, 932],
            [654, 908],
            [666, 922],
            [629, 960],
            [575, 1001],
            [525, 1027],
        ],
        dtype=np.int32,
    )
    wrist = np.array(
        [
            [358, 1240],
            [394, 1168],
            [454, 1124],
            [493, 1148],
            [462, 1222],
            [419, 1286],
        ],
        dtype=np.int32,
    )

    cv2.fillPoly(mask, [palm], 255)
    cv2.fillPoly(mask, [fingers], 235)
    cv2.fillPoly(mask, [wrist], 120)
    cv2.ellipse(mask, (553, 986), (98, 36), -36, 0, 360, 230, -1)
    cv2.ellipse(mask, (622, 920), (62, 15), -39, 0, 360, 220, -1)
    cv2.ellipse(mask, (476, 1105), (95, 52), -40, 0, 360, 220, -1)

    # Keep the mask tight. A broad feather grabs hair/flower pixels and creates
    # the duplicated-flower ghosting that failed visual QA.
    flower_exclusion = np.zeros((height, width), dtype=np.uint8)
    cv2.ellipse(flower_exclusion, (661, 855), (86, 72), 0, 0, 360, 255, -1)
    cv2.ellipse(flower_exclusion, (660, 930), (100, 80), 0, 0, 360, 255, -1)
    mask[flower_exclusion > 0] = 0

    face_exclusion = np.zeros((height, width), dtype=np.uint8)
    cv2.ellipse(face_exclusion, (520, 855), (112, 145), -12, 0, 360, 255, -1)
    mask[face_exclusion > 0] = 0

    mask = cv2.GaussianBlur(mask, (31, 31), 0)
    return np.clip(mask.astype(np.float32) / 255.0, 0.0, 1.0)


def make_petal_sprite(size: int, tint: float) -> np.ndarray:
    canvas_w = int(size * 2.2)
    canvas_h = int(size * 1.35)
    rgb = np.zeros((canvas_h, canvas_w, 3), dtype=np.float32)
    alpha = np.zeros((canvas_h, canvas_w), dtype=np.uint8)

    cx = canvas_w // 2
    cy = canvas_h // 2
    pts = np.array(
        [
            [cx - size * 0.95, cy + size * 0.03],
            [cx - size * 0.55, cy - size * 0.48],
            [cx + size * 0.18, cy - size * 0.44],
            [cx + size * 0.92, cy - size * 0.02],
            [cx + size * 0.36, cy + size * 0.43],
            [cx - size * 0.42, cy + size * 0.34],
        ],
        dtype=np.int32,
    )

    peach = np.array([108, 146, 222], dtype=np.float32)
    rose = np.array([120, 112, 210], dtype=np.float32)
    fill = peach * (1 - tint) + rose * tint
    edge = np.array([72, 78, 128], dtype=np.float32)

    cv2.fillPoly(alpha, [pts], 220)
    alpha = cv2.GaussianBlur(alpha, (9, 9), 0)
    rgb[:] = fill
    cv2.polylines(rgb, [pts], True, edge.tolist(), 1, cv2.LINE_AA)
    cv2.line(
        rgb,
        (int(cx - size * 0.66), cy),
        (int(cx + size * 0.76), int(cy - size * 0.02)),
        edge.tolist(),
        1,
        cv2.LINE_AA,
    )
    wash = np.zeros((canvas_h, canvas_w), dtype=np.uint8)
    cv2.ellipse(wash, (cx, cy), (int(size * 0.46), int(size * 0.18)), -9, 0, 360, 70, -1)
    rgb = rgb * (1 - wash[:, :, None] / 255 * 0.24) + np.array([155, 184, 242]) * (
        wash[:, :, None] / 255 * 0.24
    )
    return np.dstack((rgb, alpha.astype(np.float32) / 255.0))


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
    alpha = np.clip(patch[:, :, 3:4] * opacity, 0.0, 1.0)
    frame[clip_top:clip_bottom, clip_left:clip_right] = (
        frame[clip_top:clip_bottom, clip_left:clip_right] * (1 - alpha) + patch[:, :, :3] * alpha
    )


def point_inside(rects: list[list[int]], x: float, y: float) -> bool:
    return any(left <= x <= right and top <= y <= bottom for left, top, right, bottom in rects)


def apply_falling_petals(frame: np.ndarray, actor: dict[str, Any], rects: list[list[int]], t: float, duration: float) -> None:
    height, width = frame.shape[:2]
    travel = height + 460
    for idx, petal in enumerate(actor["petals"]):
        phase = float(petal["phase"])
        loop = (t / duration + phase) % 1.0
        y = -230 + loop * travel
        x = float(petal["x"]) + float(petal["sway"]) * math.sin((loop * 2.1 + phase) * math.tau)
        x += 7 * math.sin((loop * 5.2 + idx * 0.13) * math.tau)

        if point_inside(rects, x, y):
            continue

        edge_fade = min(1.0, max(0.0, y / 120), max(0.0, (height - y) / 140))
        flutter = 28 * math.sin((loop * 2.5 + phase) * math.tau)
        rotation = float(petal["rotation"]) + flutter
        sprite = rotate_sprite(make_petal_sprite(int(petal["size"]), 0.18 + (idx % 4) * 0.11), rotation)
        opacity = float(petal["opacity"]) * edge_fade

        # A faint second imprint makes the downward motion legible without adding
        # digital-looking motion lines.
        composite_rgba(frame, sprite, x, y - 15, opacity * 0.22)
        composite_rgba(frame, sprite, x, y, opacity)


def apply_localized_warp(
    base: np.ndarray,
    hand_mask: np.ndarray,
    hand_underpaint: np.ndarray,
    actor: dict[str, Any],
    progress: float,
) -> np.ndarray:
    lift = lift_then_return(progress)
    if lift <= 0.001:
        return base.copy()

    dx = float(actor["dx"]) * lift
    dy = float(actor["dy"]) * lift
    strength = float(actor["strength"])
    rotation = float(actor.get("rotation", 0.0)) * lift
    hide_original = float(actor.get("hide_original", 0.0)) * lift

    height, width = base.shape[:2]
    center = (488, 1118)
    matrix = cv2.getRotationMatrix2D(center, rotation, 1.0)
    matrix[0, 2] += dx
    matrix[1, 2] += dy

    # Pull a real layer from the original hand, then move that layer. This is
    # intentionally more visible than the earlier optical warp; otherwise the
    # gesture reads as a still image.
    source_alpha = hand_mask[:, :, None]
    hand_layer = base * source_alpha
    moved_hand = cv2.warpAffine(
        hand_layer,
        matrix,
        (width, height),
        flags=cv2.INTER_LINEAR,
        borderMode=cv2.BORDER_REFLECT,
    )
    moved_alpha = cv2.warpAffine(
        hand_mask,
        matrix,
        (width, height),
        flags=cv2.INTER_LINEAR,
        borderMode=cv2.BORDER_CONSTANT,
        borderValue=0,
    )[:, :, None]

    hidden_alpha = np.clip(source_alpha * hide_original, 0.0, 0.78)
    frame = base * (1 - hidden_alpha) + hand_underpaint * hidden_alpha

    # A smaller puppet warp under the lifted layer keeps the wrist/forearm from
    # feeling like a hard sticker cutout.
    grid_x, grid_y = np.meshgrid(np.arange(width, dtype=np.float32), np.arange(height, dtype=np.float32))
    vertical_weight = np.clip((1260 - grid_y) / 440, 0.0, 1.0)
    weight = hand_mask * vertical_weight * lift
    map_x = grid_x - dx * 0.34 * weight
    map_y = grid_y - dy * 0.34 * weight
    puppet = cv2.remap(base, map_x, map_y, cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
    puppet_alpha = np.clip(source_alpha * 0.26 * lift, 0.0, 0.28)
    frame = frame * (1 - puppet_alpha) + puppet * puppet_alpha

    layer_alpha = np.clip(moved_alpha * strength * lift, 0.0, 0.96)
    frame = frame * (1 - layer_alpha) + moved_hand * layer_alpha
    return frame


def apply_localized_deform(base: np.ndarray, hand_mask: np.ndarray, actor: dict[str, Any], progress: float) -> np.ndarray:
    lift = lift_then_return(progress)
    if lift <= 0.001:
        return base.copy()

    dx = float(actor["dx"]) * lift
    dy = float(actor["dy"]) * lift
    rotation = float(actor.get("rotation", 0.0)) * lift
    strength = float(actor.get("strength", 1.0))

    height, width = base.shape[:2]
    grid_x, grid_y = np.meshgrid(np.arange(width, dtype=np.float32), np.arange(height, dtype=np.float32))
    pivot_x = 430.0
    pivot_y = 1195.0

    # Finger area moves most; wrist moves least. This creates a clean deformation
    # from the original pixels instead of a duplicated lifted copy.
    vertical_weight = np.clip((1260 - grid_y) / 430, 0.0, 1.0)
    horizontal_weight = np.clip((grid_x - 340) / 300, 0.0, 1.0)
    weight = np.clip(hand_mask * (0.35 + 0.65 * vertical_weight * horizontal_weight) * strength, 0.0, 1.0)

    theta = math.radians(rotation)
    rel_x = grid_x - pivot_x
    rel_y = grid_y - pivot_y
    rot_x = rel_x * math.cos(theta) - rel_y * math.sin(theta) + pivot_x
    rot_y = rel_x * math.sin(theta) + rel_y * math.cos(theta) + pivot_y

    target_x = rot_x + dx * vertical_weight
    target_y = rot_y + dy * vertical_weight
    map_x = grid_x * (1 - weight) + target_x * weight
    map_y = grid_y * (1 - weight) + target_y * weight

    warped = cv2.remap(base, map_x, map_y, cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
    alpha = np.clip(hand_mask[:, :, None] * (0.96 * lift), 0.0, 0.96)
    return base * (1 - alpha) + warped * alpha


def draw_contact_sheet(frames: list[tuple[int, np.ndarray]], output: Path) -> None:
    thumbs = []
    for idx, frame in frames:
        thumb = cv2.resize(frame, (251, 392), interpolation=cv2.INTER_AREA)
        cv2.rectangle(thumb, (0, 0), (250, 34), (248, 237, 218), -1)
        cv2.putText(thumb, f"frame {idx}", (12, 23), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (36, 33, 30), 1, cv2.LINE_AA)
        thumbs.append(thumb)
    sheet = np.concatenate(thumbs, axis=1)
    cv2.imwrite(str(output), sheet)


def write_gif(frames: list[np.ndarray], output: Path, fps: int) -> None:
    animation = cv2.Animation()
    animation.frames = frames
    animation.durations = [int(1000 / fps)] * len(frames)
    animation.loop_count = 0
    if not cv2.imwriteanimation(str(output), animation):
        raise RuntimeError(f"Could not write animated preview: {output}")


def render(plan_path: Path) -> dict[str, Any]:
    plan = json.loads(plan_path.read_text())
    canvas = plan["canvas"]
    width = int(canvas["width"])
    height = int(canvas["height"])
    fps = int(canvas["fps"])
    duration_seconds = int(canvas["duration_seconds"])
    total_frames = fps * duration_seconds

    base_path = plan_path.parent / plan["base_image"]
    base_bgr = cv2.imread(str(base_path), cv2.IMREAD_COLOR)
    if base_bgr is None:
        raise FileNotFoundError(base_path)
    if base_bgr.shape[:2] != (height, width):
        raise ValueError(f"Expected {width}x{height}, got {base_bgr.shape[1]}x{base_bgr.shape[0]}")

    # MP4 encoders expect even dimensions. Crop the final encoded frame by one
    # pixel on the right; the still previews and source art stay untouched.
    mp4_width = width if width % 2 == 0 else width - 1
    base = base_bgr.astype(np.float32)
    hand_mask = make_hand_mask(height, width)
    underpaint_mask = (hand_mask > 0.13).astype(np.uint8) * 255
    underpaint_mask = cv2.dilate(underpaint_mask, np.ones((7, 7), dtype=np.uint8), iterations=1)
    hand_underpaint = cv2.inpaint(base_bgr, underpaint_mask, 4, cv2.INPAINT_TELEA).astype(np.float32)

    outputs = plan["outputs"]
    mp4_path = plan_path.parent / outputs["mp4"]
    gif_path = plan_path.parent / outputs["gif_preview"]
    preview_dir = plan_path.parent / outputs["preview_dir"]
    contact_sheet_path = plan_path.parent / outputs["contact_sheet"]
    preview_dir.mkdir(parents=True, exist_ok=True)

    writer = cv2.VideoWriter(str(mp4_path), cv2.VideoWriter_fourcc(*"mp4v"), fps, (mp4_width, height))
    if not writer.isOpened():
        raise RuntimeError(f"Could not open MP4 writer: {mp4_path}")

    proof_indices = set(int(item) for item in plan["qa"]["proof_frames"])
    proof_frames: list[tuple[int, np.ndarray]] = []
    gif_frames: list[np.ndarray] = []
    encoded_checks: dict[int, np.ndarray] = {}

    hand_actor = next(actor for actor in plan["actors"] if actor["type"] in {"localized_warp", "localized_deform"})
    petal_actor = next(actor for actor in plan["actors"] if actor["type"] == "falling_petals")

    for frame_index in range(total_frames):
        t = frame_index / fps
        progress = frame_index / total_frames
        if hand_actor["type"] == "localized_warp":
            frame = apply_localized_warp(base, hand_mask, hand_underpaint, hand_actor, progress)
        else:
            frame = apply_localized_deform(base, hand_mask, hand_actor, progress)
        apply_falling_petals(frame, petal_actor, plan["protected_rects"], t, duration_seconds)
        frame_u8 = np.clip(frame, 0, 255).astype(np.uint8)

        writer.write(frame_u8[:, :mp4_width])

        if frame_index in proof_indices:
            proof_path = preview_dir / f"motion-unlock-frame-{frame_index:03d}.png"
            cv2.imwrite(str(proof_path), frame_u8)
            proof_frames.append((frame_index, frame_u8))
            encoded_checks[frame_index] = frame_u8[:, :mp4_width]

        if frame_index % 3 == 0:
            gif_frames.append(cv2.resize(frame_u8, (376, 588), interpolation=cv2.INTER_AREA))

    writer.release()
    draw_contact_sheet(proof_frames, contact_sheet_path)
    write_gif(gif_frames, gif_path, fps=10)

    # Read the encoded MP4 back, because generated frames are not enough.
    cap = cv2.VideoCapture(str(mp4_path))
    decoded: dict[int, np.ndarray] = {}
    for idx in sorted(proof_indices):
        cap.set(cv2.CAP_PROP_POS_FRAMES, idx)
        ok, decoded_frame = cap.read()
        if ok:
            decoded[idx] = decoded_frame
    cap.release()

    first = min(decoded)
    middle = min(decoded, key=lambda value: abs(value - total_frames // 2))
    if first == middle and len(decoded) > 1:
        middle = sorted(decoded)[1]
    diff = np.abs(decoded[first].astype(np.int16) - decoded[middle].astype(np.int16))
    hand_crop = diff[850:1165, 410:710]
    changed_px = int((diff.max(axis=2) > 8).sum())
    hand_crop_mean = float(hand_crop.mean())

    motion_pass = changed_px >= int(plan["qa"]["minimum_changed_pixels_gt8_between_keyframes"]) and hand_crop_mean >= float(
        plan["qa"]["minimum_hand_crop_mean_diff"]
    )
    result = {
        "mp4": str(mp4_path),
        "gif_preview": str(gif_path),
        "contact_sheet": str(contact_sheet_path),
        "decoded_width": int(decoded[first].shape[1]),
        "decoded_height": int(decoded[first].shape[0]),
        "fps": fps,
        "frames": total_frames,
        "changed_pixels_gt8_first_to_mid": changed_px,
        "hand_crop_mean_diff_first_to_mid": round(hand_crop_mean, 3),
        "passes_motion_threshold": motion_pass,
        "visual_artifact_gate": {
            "status": "REQUIRES_HUMAN_REVIEW",
            "publishable": False,
            "hard_fails": plan["qa"].get("hard_visual_fails", []),
            "note": "Pixel motion is not a publish gate. Inspect the GIF/proof sheet for ghosting, duplicated limbs, flower drag, face smear, and muddy wrist before approval.",
        },
    }
    qa_path = plan_path.parent / "motion-visual-qa.json"
    qa_path.write_text(json.dumps(result, indent=2) + "\n")
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description="Render a Lottie/Rive-inspired motion plan for a still illustration.")
    parser.add_argument("--plan", type=Path, default=Path("motion-plan.json"))
    args = parser.parse_args()
    result = render(args.plan)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
