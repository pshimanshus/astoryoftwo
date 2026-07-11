from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import subprocess
import sys
from typing import Any

from pipeline.stages.carousel_contract import load_style_contract


def build_integrated_text_manifest(slides: list[dict[str, Any]]) -> dict[str, Any]:
    contract = load_style_contract()
    typography = contract.get("legacy_typography", contract["typography"])
    return {
        "typography": typography,
        "composition_role": "publishable_final_illustration_with_text",
        "renderer": {
            "font_role": "hand_drawn_storybook",
            "font_engine": "macos_coretext_noteworthy",
            "panel_style": "no_quote_card_panel",
            "placement": "integrated final-image text placement in reserved illustrated paper whitespace",
            "brandmark_style": "subtle_but_readable",
        },
        "slides": [
            {
                "slide": int(slide["slide"]),
                "text": slide["copy"],
                "brandmark": contract["brandmark"],
                "placement": typography["placement"],
                "composition_role": "final_illustration_with_integrated_typography",
                "text_layout": slide.get("text_layout", {}),
            }
            for slide in slides
        ],
    }


def render_with_macos_storybook_renderer(carousel_dir: Path, manifest: dict[str, Any]) -> dict[str, Any] | None:
    if sys.platform != "darwin":
        return None
    helper = Path(__file__).with_name("render_storybook_text_overlays.swift")
    if not helper.exists():
        return None

    input_path = carousel_dir / ".text-overlay-input.json"
    input_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    env = os.environ.copy()
    env.setdefault("CLANG_MODULE_CACHE_PATH", "/private/tmp/swift-module-cache")
    result = subprocess.run(
        ["swift", str(helper), str(carousel_dir), str(input_path)],
        text=True,
        capture_output=True,
        env=env,
        check=False,
    )
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or "Storybook integrated text renderer failed.")
    return json.loads(result.stdout)


def build_overlay_manifest(slides: list[dict[str, Any]]) -> dict[str, Any]:
    return build_integrated_text_manifest(slides)


def render_integrated_text(carousel_dir: Path) -> dict[str, Any]:
    slides = json.loads((carousel_dir / "slides.json").read_text(encoding="utf-8"))
    manifest = build_integrated_text_manifest(slides)
    final_dir = carousel_dir / "final"
    out_dir = carousel_dir / "final-with-text"
    missing = [
        final_dir / f"slide-{int(record['slide']):02d}.png"
        for record in manifest["slides"]
        if not (final_dir / f"slide-{int(record['slide']):02d}.png").exists()
    ]
    if missing:
        raise FileNotFoundError("Missing source final images for integrated text pass: " + ", ".join(str(path) for path in missing))

    swift_result = render_with_macos_storybook_renderer(carousel_dir, manifest)
    if swift_result is not None:
        return swift_result

    try:
        import cv2
        import numpy as np
    except ImportError as exc:
        raise RuntimeError(f"OpenCV render dependency unavailable: {exc}") from exc

    out_dir.mkdir(parents=True, exist_ok=True)

    def read_image(path: Path) -> Any:
        image = cv2.imdecode(np.fromfile(str(path), dtype=np.uint8), cv2.IMREAD_COLOR)
        if image is None:
            raise RuntimeError(f"Could not read image: {path}")
        return image

    def wrap(text: str, limit: int = 32) -> list[str]:
        lines: list[str] = []
        current: list[str] = []
        for word in text.split():
            candidate = " ".join([*current, word])
            if len(candidate) > limit and current:
                lines.append(" ".join(current))
                current = [word]
            else:
                current.append(word)
        if current:
            lines.append(" ".join(current))
        return lines

    def write_png(path: Path, image: Any) -> None:
        ok, encoded = cv2.imencode(".png", image)
        if not ok:
            raise RuntimeError(f"Could not encode {path}")
        path.write_bytes(encoded.tobytes())

    def draw_story_text(image: Any, lines: list[str], x: int, y: int, scale: float, line_gap: int) -> None:
        font = cv2.FONT_HERSHEY_SIMPLEX
        shadow_color = (248, 244, 235)
        ink_color = (31, 35, 38)
        thickness = max(2, round(scale * 2.0))
        shadow_thickness = thickness + 2
        for line in lines:
            cv2.putText(image, line, (x + 2, y + 2), font, scale, shadow_color, shadow_thickness, cv2.LINE_AA)
            cv2.putText(image, line, (x, y), font, scale, ink_color, thickness, cv2.LINE_AA)
            y += line_gap

    def draw_brandmark(image: Any, text: str, margin_x: int, margin_y: int, scale: float) -> None:
        font = cv2.FONT_HERSHEY_SCRIPT_SIMPLEX
        color = (87, 83, 77)
        thickness = max(1, round(scale * 1.5))
        size, _ = cv2.getTextSize(text, font, scale, thickness)
        x = image.shape[1] - margin_x - size[0]
        y = image.shape[0] - margin_y
        cv2.putText(image, text, (x, y), font, scale, color, thickness, cv2.LINE_AA)

    rendered = []
    for record in manifest["slides"]:
        source = final_dir / f"slide-{record['slide']:02d}.png"
        image = read_image(source)
        h, w = image.shape[:2]
        lines = wrap(record["text"], limit=34)
        margin_x = round(w * 0.07)
        margin_y = round(h * 0.055)
        scale = max(0.84, w / 1080 * 1.02)
        line_gap = round(64 * scale)
        draw_story_text(image, lines, margin_x + 22, margin_y + round(72 * scale), scale, line_gap)
        draw_brandmark(image, record["brandmark"], margin_x, margin_y, max(0.48, w / 1080 * 0.58))
        target = out_dir / f"slide-{record['slide']:02d}.png"
        write_png(target, image)
        rendered.append({"slide": record["slide"], "source": str(source), "file": str(target)})

    result = {
        "status": "rendered",
        "composition_role": manifest["composition_role"],
        "typography": manifest["typography"],
        "renderer": manifest["renderer"],
        "slides": rendered,
    }
    (carousel_dir / "text-overlay.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    (carousel_dir / "integrated-text-pass.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    return result


def render_overlays(carousel_dir: Path) -> dict[str, Any]:
    return render_integrated_text(carousel_dir)


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Apply an integrated exact-text pass to carousel art. This creates unified "
            "text-bearing illustration outputs; it is not a quote-card overlay workflow."
        )
    )
    parser.add_argument("carousel_dir", type=Path)
    args = parser.parse_args()
    result = render_integrated_text(args.carousel_dir)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
