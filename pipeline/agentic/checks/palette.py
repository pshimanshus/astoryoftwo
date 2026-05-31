"""Palette check — does this slide read as warm ivory or has it drifted yellow?

Two measurements, both must pass:
1. Median paper RGB is within `TOLERANCE` of the warm-ivory target.
2. The fraction of yellow-band pixels (hue 35-65°, saturation ≥ 0.35)
   stays below `YELLOW_BAND_PIXEL_LIMIT`.

A FAIL gate carries the measured values in `reason` so the runner can
inject them back into the next regeneration prompt.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
from PIL import Image

from pipeline.agentic.contracts import WorkflowGate


IVORY_TARGET_RGB = (245, 240, 228)
TOLERANCE = 18
YELLOW_BAND_HUE_RANGE = (35.0, 65.0)
YELLOW_BAND_SAT_MIN = 0.35
YELLOW_BAND_PIXEL_LIMIT = 0.06
SAMPLE_LIMIT = 200_000
SAMPLE_FRACTION = 0.04


def _hsv_yellow_fraction(arr: np.ndarray) -> float:
    rgb = arr[..., :3].astype(np.float32) / 255.0
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
        img = img.convert("RGB")
        arr = np.array(img)

    sample = arr.reshape(-1, 3)
    if sample.shape[0] > SAMPLE_LIMIT:
        rng = np.random.default_rng(0)
        idx = rng.choice(
            sample.shape[0],
            size=max(1, int(sample.shape[0] * SAMPLE_FRACTION)),
            replace=False,
        )
        sample = sample[idx]
    median = np.median(sample, axis=0)
    deltas = np.abs(median - np.array(IVORY_TARGET_RGB))
    median_ok = bool((deltas <= TOLERANCE).all())

    yellow_fraction = _hsv_yellow_fraction(arr)
    yellow_ok = yellow_fraction <= YELLOW_BAND_PIXEL_LIMIT

    if median_ok and yellow_ok:
        return WorkflowGate(
            name="palette",
            status="PASS",
            reason=(
                f"median RGB={median.astype(int).tolist()} within ±{TOLERANCE}; "
                f"yellow_fraction={yellow_fraction:.3f}"
            ),
            evidence_paths=[str(image_path)],
        )

    reasons: list[str] = []
    if not median_ok:
        reasons.append(
            f"median RGB={median.astype(int).tolist()} exceeds ±{TOLERANCE} from "
            f"ivory target {IVORY_TARGET_RGB}"
        )
    if not yellow_ok:
        reasons.append(
            f"yellow_fraction={yellow_fraction:.3f} above limit "
            f"{YELLOW_BAND_PIXEL_LIMIT}"
        )
    return WorkflowGate(
        name="palette",
        status="FAIL",
        reason="; ".join(reasons),
        evidence_paths=[str(image_path)],
    )
