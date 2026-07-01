#!/usr/bin/env python3
"""Render local illustrated draft slides for a carousel package.

This creates actual raster PNG slides from slides.json in the final carousel
folders. It is a deterministic local renderer for review and posting drafts,
not a substitute for face-accurate final image generation.
"""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

import cv2
import numpy as np


PAPER = (218, 234, 242)
PAPER_DARK = (205, 222, 232)
INK = (38, 35, 31)
MUTED = (112, 101, 88)
LINE = (57, 51, 45)
WALL = (205, 229, 239)
WINDOW = (136, 190, 222)
FLOOR = (193, 173, 145)
TABLE = (159, 113, 78)
COUCH = (151, 112, 108)
ROSE = (107, 113, 205)
TEAL = (152, 130, 86)
DUPATTA = (107, 148, 193)
SKIN_A = (105, 142, 198)
SKIN_Z = (92, 123, 184)
HAIR = (43, 34, 30)
FOOD_GREEN = (96, 143, 92)
FOOD_RED = (203, 96, 76)
FOOD_GOLD = (222, 177, 91)
PHONE = (61, 62, 65)


@dataclass(frozen=True)
class FormatSpec:
    key: str
    output_dir: str
    width: int
    height: int
    text_top: int
    text_max_height: int
    scene_top: int
    scene_bottom: int
    footer_y: int
    text_scale: float
    scene_scale: float


POST = FormatSpec(
    key="instagram_post",
    output_dir="final",
    width=1080,
    height=1350,
    text_top=96,
    text_max_height=190,
    scene_top=300,
    scene_bottom=1130,
    footer_y=1245,
    text_scale=1.04,
    scene_scale=1.0,
)

STORY = FormatSpec(
    key="reels_stories",
    output_dir="final-reels-stories",
    width=1080,
    height=1920,
    text_top=160,
    text_max_height=280,
    scene_top=530,
    scene_bottom=1640,
    footer_y=1800,
    text_scale=1.16,
    scene_scale=1.14,
)


def write_json(path: Path, data: Any) -> None:
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


def write_png(path: Path, image: np.ndarray) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    ok, data = cv2.imencode(".png", image, [cv2.IMWRITE_PNG_COMPRESSION, 3])
    if not ok:
        raise RuntimeError(f"Could not encode {path}")
    path.write_bytes(data.tobytes())


def text_size(text: str, scale: float, thickness: int) -> tuple[int, int]:
    (width, height), baseline = cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX, scale, thickness)
    return width, height + baseline


def wrap_text(text: str, max_width: int, scale: float, thickness: int) -> list[str]:
    lines: list[str] = []
    for paragraph in text.splitlines() or [""]:
        words = paragraph.split()
        if not words:
            lines.append("")
            continue
        current = words[0]
        for word in words[1:]:
            candidate = f"{current} {word}"
            if text_size(candidate, scale, thickness)[0] <= max_width:
                current = candidate
            else:
                lines.append(current)
                current = word
        lines.append(current)
    return lines


def draw_center_text(
    canvas: np.ndarray,
    text: str,
    *,
    top: int,
    max_width: int,
    max_height: int,
    preferred_scale: float,
) -> None:
    scale = preferred_scale
    thickness = 3
    while scale > 0.62:
        lines = wrap_text(text, max_width, scale, thickness)
        line_height = int(72 * scale)
        total_height = line_height * len(lines)
        widest = max((text_size(line, scale, thickness)[0] for line in lines), default=0)
        if total_height <= max_height and widest <= max_width:
            break
        scale -= 0.04

    lines = wrap_text(text, max_width, scale, thickness)
    line_height = int(74 * scale)
    y = top + max(0, (max_height - line_height * len(lines)) // 2) + int(48 * scale)
    for line in lines:
        width = text_size(line, scale, thickness)[0]
        x = (canvas.shape[1] - width) // 2
        cv2.putText(canvas, line, (x + 3, y + 3), cv2.FONT_HERSHEY_SIMPLEX, scale, (246, 242, 232), 6, cv2.LINE_AA)
        cv2.putText(canvas, line, (x, y), cv2.FONT_HERSHEY_SIMPLEX, scale, INK, thickness, cv2.LINE_AA)
        y += line_height


def line(canvas: np.ndarray, p1: tuple[int, int], p2: tuple[int, int], color: tuple[int, int, int] = LINE, width: int = 4) -> None:
    cv2.line(canvas, p1, p2, color, width, cv2.LINE_AA)


def ellipse(
    canvas: np.ndarray,
    center: tuple[int, int],
    axes: tuple[int, int],
    color: tuple[int, int, int],
    width: int = -1,
) -> None:
    cv2.ellipse(canvas, center, axes, 0, 0, 360, color, width, cv2.LINE_AA)


def rect(canvas: np.ndarray, p1: tuple[int, int], p2: tuple[int, int], color: tuple[int, int, int], width: int = -1) -> None:
    cv2.rectangle(canvas, p1, p2, color, width, cv2.LINE_AA)


class Scene:
    def __init__(self, canvas: np.ndarray, spec: FormatSpec) -> None:
        self.canvas = canvas
        self.spec = spec
        self.height = spec.scene_bottom - spec.scene_top

    def x(self, value: float) -> int:
        return round(value)

    def y(self, value: float) -> int:
        return round(self.spec.scene_top + value * (self.height / 830.0))

    def s(self, value: float) -> int:
        return max(1, round(value * self.spec.scene_scale))


def draw_plate(canvas: np.ndarray, x: int, y: int, scale: float = 1.0, *, full: bool = True, hero_bite: bool = False) -> None:
    sx = lambda value: max(1, round(value * scale))
    ellipse(canvas, (x, y), (sx(112), sx(40)), (229, 222, 202), -1)
    ellipse(canvas, (x, y), (sx(112), sx(40)), INK, sx(4))
    food = [
        (x - sx(50), y - sx(6), FOOD_GREEN),
        (x - sx(8), y + sx(6), FOOD_RED),
        (x + sx(42), y - sx(5), FOOD_GOLD),
        (x + sx(13), y - sx(18), FOOD_GREEN),
    ]
    count = 4 if full else 2
    for idx, (fx, fy, color) in enumerate(food[:count]):
        radius = sx(17 if hero_bite and idx == 2 else 14)
        cv2.circle(canvas, (fx, fy), radius, color, -1, cv2.LINE_AA)
        cv2.circle(canvas, (fx, fy), radius, INK, sx(2), cv2.LINE_AA)
    if hero_bite:
        cv2.circle(canvas, (x + sx(42), y - sx(5)), sx(25), (222, 201, 121), sx(4), cv2.LINE_AA)


def draw_person(
    canvas: np.ndarray,
    x: int,
    y: int,
    scale: float,
    *,
    woman: bool,
    mood: str,
    reach: str = "neutral",
) -> None:
    sx = lambda value: max(1, round(value * scale))
    skin = SKIN_A if woman else SKIN_Z
    shirt = ROSE if woman else TEAL

    ellipse(canvas, (x, y + sx(210)), (sx(82), sx(118)), shirt, -1)
    ellipse(canvas, (x, y + sx(210)), (sx(82), sx(118)), INK, sx(4))
    if woman:
        line(canvas, (x - sx(56), y + sx(145)), (x + sx(72), y + sx(290)), DUPATTA, sx(9))
    rect(canvas, (x - sx(23), y + sx(88)), (x + sx(23), y + sx(136)), skin, -1)
    ellipse(canvas, (x, y + sx(66)), (sx(64), sx(71)), skin, -1)
    ellipse(canvas, (x, y + sx(66)), (sx(64), sx(71)), INK, sx(4))

    if woman:
        ellipse(canvas, (x - sx(21), y + sx(60)), (sx(79), sx(87)), HAIR, sx(11))
        line(canvas, (x - sx(62), y + sx(94)), (x - sx(92), y + sx(218)), HAIR, sx(12))
        line(canvas, (x + sx(56), y + sx(94)), (x + sx(78), y + sx(196)), HAIR, sx(9))
    else:
        ellipse(canvas, (x, y + sx(17)), (sx(59), sx(31)), HAIR, -1)
        cv2.ellipse(canvas, (x, y + sx(92)), (sx(43), sx(22)), 0, 0, 180, HAIR, sx(8), cv2.LINE_AA)

    eye_y = y + sx(55)
    cv2.circle(canvas, (x - sx(23), eye_y), sx(5), INK, -1, cv2.LINE_AA)
    cv2.circle(canvas, (x + sx(23), eye_y), sx(5), INK, -1, cv2.LINE_AA)
    if mood == "hesitant":
        line(canvas, (x - sx(31), y + sx(39)), (x - sx(9), y + sx(36)), INK, sx(3))
        line(canvas, (x + sx(9), y + sx(36)), (x + sx(31), y + sx(39)), INK, sx(3))
        cv2.ellipse(canvas, (x, y + sx(88)), (sx(18), sx(8)), 0, 10, 170, INK, sx(3), cv2.LINE_AA)
    elif mood == "laugh":
        cv2.ellipse(canvas, (x, y + sx(86)), (sx(26), sx(16)), 0, 0, 180, INK, sx(4), cv2.LINE_AA)
        line(canvas, (x - sx(38), y + sx(40)), (x - sx(12), y + sx(34)), INK, sx(3))
        line(canvas, (x + sx(12), y + sx(34)), (x + sx(38), y + sx(40)), INK, sx(3))
    else:
        cv2.ellipse(canvas, (x, y + sx(85)), (sx(22), sx(11)), 0, 0, 180, INK, sx(3), cv2.LINE_AA)

    if reach == "offer_left":
        line(canvas, (x - sx(67), y + sx(172)), (x - sx(175), y + sx(250)), INK, sx(5))
        line(canvas, (x + sx(67), y + sx(170)), (x + sx(120), y + sx(226)), INK, sx(5))
    elif reach == "offer_right":
        line(canvas, (x + sx(67), y + sx(172)), (x + sx(175), y + sx(250)), INK, sx(5))
        line(canvas, (x - sx(67), y + sx(170)), (x - sx(120), y + sx(226)), INK, sx(5))
    elif reach == "eat":
        line(canvas, (x - sx(67), y + sx(170)), (x - sx(105), y + sx(100)), INK, sx(5))
        line(canvas, (x + sx(67), y + sx(170)), (x + sx(120), y + sx(228)), INK, sx(5))
    else:
        line(canvas, (x - sx(67), y + sx(170)), (x - sx(138), y + sx(245)), INK, sx(5))
        line(canvas, (x + sx(67), y + sx(170)), (x + sx(134), y + sx(238)), INK, sx(5))


def draw_room(scene: Scene, *, late_night: bool = False, kitchen: bool = False) -> None:
    c = scene.canvas
    rect(c, (80, scene.y(0)), (1000, scene.y(760)), WALL, -1)
    rect(c, (80, scene.y(0)), (1000, scene.y(760)), (130, 157, 176), scene.s(4))
    rect(c, (80, scene.y(620)), (1000, scene.y(760)), FLOOR, -1)

    rect(c, (720, scene.y(72)), (916, scene.y(260)), WINDOW, -1)
    rect(c, (720, scene.y(72)), (916, scene.y(260)), INK, scene.s(4))
    line(c, (818, scene.y(72)), (818, scene.y(260)), INK, scene.s(3))
    line(c, (720, scene.y(166)), (916, scene.y(166)), INK, scene.s(3))

    if kitchen:
        rect(c, (155, scene.y(550)), (925, scene.y(704)), TABLE, -1)
        rect(c, (155, scene.y(550)), (925, scene.y(704)), INK, scene.s(4))
        rect(c, (160, scene.y(280)), (405, scene.y(520)), (196, 216, 209), -1)
        rect(c, (160, scene.y(280)), (405, scene.y(520)), INK, scene.s(4))
    else:
        rect(c, (160, scene.y(500)), (900, scene.y(690)), COUCH, -1)
        rect(c, (160, scene.y(500)), (900, scene.y(690)), INK, scene.s(4))
        rect(c, (330, scene.y(585)), (730, scene.y(692)), TABLE, -1)
        rect(c, (330, scene.y(585)), (730, scene.y(692)), INK, scene.s(4))

    if late_night:
        for idx, x in enumerate([205, 300, 397, 735, 827, 918]):
            color = ROSE if idx % 2 else FOOD_GOLD
            cv2.circle(c, (x, scene.y(405 + (idx % 2) * 24)), scene.s(10), color, -1, cv2.LINE_AA)
            cv2.circle(c, (x, scene.y(405 + (idx % 2) * 24)), scene.s(10), INK, scene.s(2), cv2.LINE_AA)


def draw_scene(slide: dict[str, Any], canvas: np.ndarray, spec: FormatSpec) -> None:
    number = int(slide["slide"])
    scene = Scene(canvas, spec)

    if number == 1:
        draw_room(scene, kitchen=True)
        draw_person(canvas, 385, scene.y(245), spec.scene_scale, woman=True, mood="hesitant", reach="offer_right")
        draw_person(canvas, 690, scene.y(245), spec.scene_scale, woman=False, mood="soft", reach="offer_left")
        draw_plate(canvas, 535, scene.y(615), spec.scene_scale, full=True)
        line(canvas, (650, scene.y(515)), (575, scene.y(600)), TEAL, scene.s(7))
    elif number == 2:
        draw_room(scene)
        draw_person(canvas, 382, scene.y(220), spec.scene_scale, woman=True, mood="soft", reach="offer_right")
        draw_person(canvas, 698, scene.y(220), spec.scene_scale, woman=False, mood="soft", reach="offer_left")
        draw_plate(canvas, 540, scene.y(620), spec.scene_scale, full=True)
    elif number == 3:
        draw_room(scene)
        rect(canvas, (155, scene.y(520)), (925, scene.y(735)), TABLE, -1)
        rect(canvas, (155, scene.y(520)), (925, scene.y(735)), INK, scene.s(4))
        draw_person(canvas, 322, scene.y(160), spec.scene_scale * 0.9, woman=True, mood="laugh", reach="neutral")
        draw_person(canvas, 760, scene.y(160), spec.scene_scale * 0.9, woman=False, mood="soft", reach="offer_left")
        draw_plate(canvas, 540, scene.y(628), spec.scene_scale * 1.45, full=True, hero_bite=True)
        line(canvas, (690, scene.y(470)), (602, scene.y(588)), TEAL, scene.s(9))
        cv2.circle(canvas, (603, scene.y(620)), scene.s(8), FOOD_GOLD, -1, cv2.LINE_AA)
    elif number == 4:
        draw_room(scene)
        draw_person(canvas, 386, scene.y(220), spec.scene_scale, woman=True, mood="laugh", reach="eat")
        draw_person(canvas, 696, scene.y(220), spec.scene_scale, woman=False, mood="soft", reach="eat")
        draw_plate(canvas, 490, scene.y(615), spec.scene_scale * 1.12, full=True)
        rect(canvas, (654, scene.y(628)), (812, scene.y(684)), PHONE, -1)
        rect(canvas, (654, scene.y(628)), (812, scene.y(684)), INK, scene.s(3))
        line(canvas, (684, scene.y(510)), (545, scene.y(598)), TEAL, scene.s(8))
        line(canvas, (420, scene.y(510)), (470, scene.y(590)), ROSE, scene.s(7))
    else:
        draw_room(scene, late_night=True)
        cv2.circle(canvas, (855, scene.y(128)), scene.s(28), (220, 226, 204), -1, cv2.LINE_AA)
        cv2.circle(canvas, (866, scene.y(118)), scene.s(26), WINDOW, -1, cv2.LINE_AA)
        rect(canvas, (170, scene.y(520)), (910, scene.y(730)), (123, 108, 139), -1)
        rect(canvas, (170, scene.y(520)), (910, scene.y(730)), INK, scene.s(4))
        draw_person(canvas, 398, scene.y(190), spec.scene_scale * 0.96, woman=True, mood="laugh", reach="offer_right")
        draw_person(canvas, 675, scene.y(190), spec.scene_scale * 0.96, woman=False, mood="soft", reach="offer_left")
        draw_plate(canvas, 535, scene.y(628), spec.scene_scale * 1.05, full=True)
        cv2.circle(canvas, (468, scene.y(625)), scene.s(12), FOOD_GOLD, -1, cv2.LINE_AA)
        cv2.circle(canvas, (606, scene.y(625)), scene.s(12), FOOD_RED, -1, cv2.LINE_AA)


def render_slide(slide: dict[str, Any], spec: FormatSpec, out_path: Path) -> None:
    number = int(slide["slide"])
    canvas = np.zeros((spec.height, spec.width, 3), dtype=np.uint8)
    canvas[:, :] = PAPER
    rng = np.random.default_rng(seed=number * 17 + spec.height)
    noise = rng.normal(0, 2.4, canvas.shape).astype(np.int16)
    canvas[:] = np.clip(canvas.astype(np.int16) + noise, 0, 255).astype(np.uint8)

    # Soft deckled frame, not a quote-card panel.
    rect(canvas, (26, 26), (spec.width - 26, spec.height - 26), PAPER_DARK, 3)
    draw_center_text(
        canvas,
        str(slide["copy"]),
        top=spec.text_top,
        max_width=880,
        max_height=spec.text_max_height,
        preferred_scale=spec.text_scale,
    )
    draw_scene(slide, canvas, spec)

    total = int(slide.get("_total", 5))
    cv2.putText(canvas, f"{number:02d}/{total:02d}", (86, spec.footer_y), cv2.FONT_HERSHEY_SIMPLEX, 0.74, MUTED, 2, cv2.LINE_AA)
    brand = "@a.storyof.two"
    brand_width = text_size(brand, 0.74, 2)[0]
    cv2.putText(canvas, brand, (spec.width - brand_width - 86, spec.footer_y), cv2.FONT_HERSHEY_SIMPLEX, 0.74, MUTED, 2, cv2.LINE_AA)
    write_png(out_path, canvas)


def make_contact_sheet(image_paths: list[Path], out_path: Path, *, thumb: tuple[int, int]) -> None:
    cols = min(5, len(image_paths))
    rows = int(np.ceil(len(image_paths) / cols))
    gap = 12
    margin = 20
    sheet_width = margin * 2 + cols * thumb[0] + (cols - 1) * gap
    sheet_height = margin * 2 + rows * thumb[1] + (rows - 1) * gap
    sheet = np.zeros((sheet_height, sheet_width, 3), dtype=np.uint8)
    sheet[:, :] = PAPER
    for index, path in enumerate(image_paths):
        image = cv2.imdecode(np.fromfile(str(path), dtype=np.uint8), cv2.IMREAD_COLOR)
        if image is None:
            raise RuntimeError(f"Could not read {path}")
        resized = cv2.resize(image, thumb, interpolation=cv2.INTER_AREA)
        row = index // cols
        col = index % cols
        x = margin + col * (thumb[0] + gap)
        y = margin + row * (thumb[1] + gap)
        sheet[y : y + thumb[1], x : x + thumb[0]] = resized
    ok, data = cv2.imencode(".jpg", sheet, [cv2.IMWRITE_JPEG_QUALITY, 92])
    if not ok:
        raise RuntimeError(f"Could not encode {out_path}")
    out_path.write_bytes(data.tobytes())


def prompt_by_slide(prompt_pack: dict[str, Any]) -> dict[int, str]:
    prompts: dict[int, str] = {}
    for item in prompt_pack.get("slides", []):
        try:
            number = int(item.get("slide", 0))
        except (TypeError, ValueError):
            continue
        prompts[number] = str(item.get("prompt") or item.get("copy") or "")
    return prompts


def write_run_artifacts(carousel_dir: Path, slides: list[dict[str, Any]], outputs: dict[str, list[Path]]) -> None:
    source_dir = carousel_dir / "final" / "model-native-source"
    source_dir.mkdir(parents=True, exist_ok=True)
    prompt_pack_path = carousel_dir / "prompt-pack.json"
    prompt_pack = json.loads(prompt_pack_path.read_text(encoding="utf-8")) if prompt_pack_path.exists() else {}
    prompts = prompt_by_slide(prompt_pack)
    records: list[dict[str, Any]] = []
    for slide in slides:
        number = int(slide["slide"])
        post_file = carousel_dir / "final" / f"slide-{number:02d}.png"
        story_file = carousel_dir / "final-reels-stories" / f"slide-{number:02d}.png"
        post_source = source_dir / f"instagram-post-slide-{number:02d}.png"
        story_source = source_dir / f"reels-stories-slide-{number:02d}.png"
        post_source.write_bytes(post_file.read_bytes())
        story_source.write_bytes(story_file.read_bytes())
        records.append(
            {
                "slide": number,
                "copy": slide["copy"],
                "status": "legacy_preview_generated",
                "backend": "legacy_local_renderer",
                "generation_mode": "legacy_local_preview_not_publishable",
                "publishable": False,
                "local_draft_note": (
                    "Rendered locally as preview-only illustrated draft art. "
                    "Use codex-image-prompts for a face-accurate Codex built-in model pass before publishing."
                ),
                "source": str(post_source),
                "file": str(post_file),
                "reels_stories_source": str(story_source),
                "reels_stories_file": str(story_file),
                "native_outputs": {
                    "instagram_post": {"source": str(post_source), "file": str(post_file), "dimensions": [1080, 1350]},
                    "reels_stories": {"source": str(story_source), "file": str(story_file), "dimensions": [1080, 1920]},
                },
                "prompt": prompts.get(number, str(slide.get("visual", ""))),
            }
        )

    manifest = {
        "status": "legacy_preview_generated",
        "backend": "legacy_local_renderer",
        "generation_mode": "legacy_local_preview_not_publishable",
        "publishable": False,
        "can_satisfy_final_gate": False,
        "local_draft_disclosure": (
            "These are preview-only integrated illustrated PNG files rendered locally in separate native aspect ratios. "
            "They are not face-accurate AI image model outputs and cannot satisfy publishable final gates."
        ),
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "native_output_contract": {"formats": ["instagram_post", "reels_stories"]},
        "slides": records,
    }
    write_json(carousel_dir / "final-images.json", manifest)
    write_json(
        carousel_dir / "image-generation.json",
        {
            "status": "legacy_preview_generated",
            "backend": "legacy_local_renderer",
            "generation_mode": "legacy_local_preview_not_publishable",
            "publishable": False,
            "can_satisfy_final_gate": False,
            "local_draft_disclosure": manifest["local_draft_disclosure"],
            "outputs": {
                "instagram_post": [str(path) for path in outputs["instagram_post"]],
                "reels_stories": [str(path) for path in outputs["reels_stories"]],
            },
        },
    )
    write_json(
        carousel_dir / "visual-qa.json",
        {
            "status": "PREVIEW_ONLY_PENDING_MODEL_NATIVE_QA",
            "scope": "local_illustrated_draft",
            "publishable": False,
            "can_satisfy_final_gate": False,
            "checks": {
                "storyboard": {"pass": False, "notes": "Preview-only renderer used slides.json copy and scene intent; human final QA is still pending."},
                "aachu_face": {
                    "pass": False,
                    "reference_option_ids": ["ID45"],
                    "likeness_notes": "Simplified Aachu symbol is not face-accurate model-native identity evidence.",
                },
                "zuv_face": {
                    "pass": False,
                    "reference_option_ids": ["ID45"],
                    "likeness_notes": "Simplified Zuv symbol is not face-accurate model-native identity evidence.",
                },
                "dress_continuity": {"pass": False, "notes": "Local symbols are preview-only; model-native continuity QA is pending."},
                "style": {"pass": False, "notes": "Warm storybook preview exists; final style QA is pending on final text-bearing outputs."},
                "integrated_final_text": {"pass": False, "notes": "Text is locally rendered preview typography, not integrated final-text evidence."},
                "final_files": {"pass": False, "notes": "4:5 and 9:16 preview PNGs exist but are not publishable final files."},
            },
            "notes": [
                "Local renderer can preview copy, aspect, story, and composition.",
                "Run the Codex built-in image prompts with the identity contact sheet before final QA or publishing.",
            ],
        },
    )

    visual_lines = [
        "# Visual QA",
        "",
        "status: PREVIEW_ONLY_PENDING_MODEL_NATIVE_QA",
        "",
        "- [ ] Slide 1 final text-bearing image has human QA approval.",
        "- [ ] Slide 2 final text-bearing image has human QA approval.",
        "- [ ] Slide 3 final text-bearing image has human QA approval.",
        "- [ ] Slide 4 final text-bearing image has human QA approval.",
        "- [ ] Slide 5 final text-bearing image has human QA approval.",
        "- [ ] Aachu face is checked against the selected identity references.",
        "- [ ] Zuv face is checked against the selected identity references.",
        "- [ ] Clothing and dress details are checked on final text-bearing images.",
        "- [ ] Illustration style is checked on final text-bearing images.",
        "- [ ] Text and brandmark are checked on final text-bearing images.",
        "- [ ] Publishable final files exist in `final/` and `final-reels-stories/`.",
        "",
        "Note: this is a preview-only local illustrated render. It cannot satisfy final publishable QA; run the Codex built-in prompt pack before treating the set as final publishable.",
    ]
    (carousel_dir / "visual-qa.md").write_text("\n".join(visual_lines) + "\n", encoding="utf-8")


def render_carousel(carousel_dir: Path) -> dict[str, list[Path]]:
    slides = json.loads((carousel_dir / "slides.json").read_text(encoding="utf-8"))
    total = len(slides)
    for slide in slides:
        slide["_total"] = total

    outputs: dict[str, list[Path]] = {"instagram_post": [], "reels_stories": []}
    for spec in [POST, STORY]:
        for slide in slides:
            number = int(slide["slide"])
            out_path = carousel_dir / spec.output_dir / f"slide-{number:02d}.png"
            render_slide(slide, spec, out_path)
            outputs[spec.key].append(out_path)

    make_contact_sheet(outputs["instagram_post"], carousel_dir / "visual-qa-contact-sheet-instagram.jpg", thumb=(180, 225))
    make_contact_sheet(outputs["reels_stories"], carousel_dir / "visual-qa-contact-sheet-reels-stories.jpg", thumb=(162, 288))
    write_run_artifacts(carousel_dir, slides, outputs)
    return outputs


def main() -> None:
    parser = argparse.ArgumentParser(description="Render local illustrated draft carousel slides")
    parser.add_argument("carousel_dir", type=Path)
    args = parser.parse_args()
    outputs = render_carousel(args.carousel_dir.expanduser())
    print(json.dumps({key: [str(path) for path in value] for key, value in outputs.items()}, indent=2))


if __name__ == "__main__":
    main()
