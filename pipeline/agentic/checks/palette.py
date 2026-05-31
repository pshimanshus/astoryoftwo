"""Palette check — does this slide read as warm ivory or has it drifted yellow?

Calibrated against the 8 approved Observational Intimacy Premium
reference slides on 2026-05-31 (config/references/style-lock/
observational-intimacy-premium/slide-{01..08}.png). All 8 must PASS.
Synthetic yellow / parchment / mustard fixtures must FAIL.

Two-stage check:

1. Paper region — defined as the brightest 15% of pixels by sum-of-
   channels brightness. This isolates the unobscured paper from the
   watercolor/ink content layered on top, which is the variable that
   actually drifts to yellow.

   - Paper median R must be at least 230.
   - Paper median saturation must be below 0.18.
   - Paper median blue/green ratio must be at least 0.85.
     (Yellow paper is high R+G low B; ratio drops below 0.85.)

2. Full-image yellow band — fraction of pixels with hue 35–65° and
   saturation ≥ 0.20 must stay below 0.05. Catches large yellow
   regions outside the strict paper area (washes, fills, etc.).

A FAIL gate's `reason` carries the measured values so the runner can
inject them back into the next regeneration prompt.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
from PIL import Image

from pipeline.agentic.contracts import WorkflowGate


PAPER_PERCENTILE = 85  # brightest 15% of pixels treated as paper
PAPER_R_MIN = 230
PAPER_SATURATION_MAX = 0.18
PAPER_BLUE_GREEN_RATIO_MIN = 0.85
YELLOW_BAND_HUE_RANGE = (35.0, 65.0)
YELLOW_BAND_SAT_MIN = 0.35  # calibrated 2026-05-31 against approved slide-07 sunset variant
YELLOW_BAND_PIXEL_LIMIT = 0.05


def _hsv_components(rgb_array: np.ndarray) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    rgb = rgb_array.astype(np.float32) / 255.0
    r, g, b = rgb[..., 0], rgb[..., 1], rgb[..., 2]
    mx = np.max(rgb, axis=-1)
    mn = np.min(rgb, axis=-1)
    diff = mx - mn
    safe_diff = np.where(diff == 0, 1, diff)
    hue = np.zeros_like(mx)
    mask_r = (diff > 0) & (mx == r)
    mask_g = (diff > 0) & (mx == g)
    mask_b = (diff > 0) & (mx == b)
    hue = np.where(mask_r, ((g - b) / safe_diff) % 6, hue)
    hue = np.where(mask_g, ((b - r) / safe_diff) + 2, hue)
    hue = np.where(mask_b, ((r - g) / safe_diff) + 4, hue)
    hue = (hue * 60.0) % 360.0
    sat = np.where(mx > 0, diff / np.where(mx == 0, 1, mx), 0)
    return hue, sat, mx


def _paper_region_stats(arr: np.ndarray) -> dict[str, float]:
    flat = arr.reshape(-1, 3)
    brightness = flat.sum(axis=1)
    threshold = np.percentile(brightness, PAPER_PERCENTILE)
    paper = flat[brightness >= threshold]
    paper_median = np.median(paper, axis=0)
    _, paper_sat, _ = _hsv_components(paper.reshape(-1, 1, 3))
    median_r, median_g, median_b = paper_median.tolist()
    blue_green_ratio = (median_b / median_g) if median_g > 0 else 0.0
    return {
        "r": float(median_r),
        "g": float(median_g),
        "b": float(median_b),
        "saturation": float(paper_sat.mean()),
        "blue_green_ratio": float(blue_green_ratio),
    }


def _full_image_yellow_fraction(arr: np.ndarray) -> float:
    hue, sat, _ = _hsv_components(arr)
    yellow_mask = (
        (hue >= YELLOW_BAND_HUE_RANGE[0])
        & (hue <= YELLOW_BAND_HUE_RANGE[1])
        & (sat >= YELLOW_BAND_SAT_MIN)
    )
    return float(yellow_mask.mean())


def check_palette(image_path: Path) -> WorkflowGate:
    image_path = Path(image_path)
    if not image_path.exists():
        return WorkflowGate(
            name="palette", status="FAIL", reason=f"image missing: {image_path}"
        )

    with Image.open(image_path) as img:
        arr = np.array(img.convert("RGB"))

    paper = _paper_region_stats(arr)
    yellow_fraction = _full_image_yellow_fraction(arr)

    paper_r_ok = paper["r"] >= PAPER_R_MIN
    paper_sat_ok = paper["saturation"] <= PAPER_SATURATION_MAX
    paper_ratio_ok = paper["blue_green_ratio"] >= PAPER_BLUE_GREEN_RATIO_MIN
    yellow_ok = yellow_fraction <= YELLOW_BAND_PIXEL_LIMIT

    reasons: list[str] = []
    if not paper_r_ok:
        reasons.append(
            f"paper R={paper['r']:.0f} below min {PAPER_R_MIN} "
            f"(image too dark / heavy wash)"
        )
    if not paper_sat_ok:
        reasons.append(
            f"paper saturation={paper['saturation']:.3f} above limit "
            f"{PAPER_SATURATION_MAX} (paper itself is not desaturated)"
        )
    if not paper_ratio_ok:
        reasons.append(
            f"paper blue/green={paper['blue_green_ratio']:.3f} below min "
            f"{PAPER_BLUE_GREEN_RATIO_MIN} (paper is reading yellow/golden)"
        )
    if not yellow_ok:
        reasons.append(
            f"yellow-band fraction={yellow_fraction:.3f} above limit "
            f"{YELLOW_BAND_PIXEL_LIMIT}"
        )

    measurement = (
        f"paper RGB=({paper['r']:.0f},{paper['g']:.0f},{paper['b']:.0f}); "
        f"paper sat={paper['saturation']:.3f}; "
        f"paper B/G={paper['blue_green_ratio']:.3f}; "
        f"yellow-band fraction={yellow_fraction:.3f}"
    )

    if not reasons:
        return WorkflowGate(
            name="palette",
            status="PASS",
            reason=measurement,
            evidence_paths=[str(image_path)],
        )

    return WorkflowGate(
        name="palette",
        status="FAIL",
        reason=measurement + "; failures: " + "; ".join(reasons),
        evidence_paths=[str(image_path)],
    )
