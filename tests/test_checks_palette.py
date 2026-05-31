"""Palette gate tests — synthesized fixtures + real-image calibration.

The real-image suite is the load-bearing one: all 8 approved
Observational Intimacy Premium reference slides MUST PASS. If a future
edit to the palette gate breaks any of those, the gate has regressed.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest
from PIL import Image

from pipeline.agentic.checks.palette import (
    PAPER_R_MIN,
    PAPER_SATURATION_MAX,
    check_palette,
)


REFERENCE_BUNDLE = Path(__file__).resolve().parents[1] / (
    "config/references/style-lock/observational-intimacy-premium"
)


def _save_solid(
    path: Path,
    rgb: tuple[int, int, int],
    size: tuple[int, int] = (512, 640),
) -> Path:
    Image.new("RGB", size, color=rgb).save(path)
    return path


# ─── Real-image calibration ─────────────────────────────────────────────

@pytest.fixture(scope="module")
def approved_slides() -> list[Path]:
    slides = sorted(REFERENCE_BUNDLE.glob("slide-*.png"))
    if not slides:
        pytest.skip("approved style-lock bundle not found in repo")
    return slides


def test_every_approved_slide_passes(approved_slides: list[Path]) -> None:
    """All 8 approved Observational Intimacy Premium slides MUST PASS.

    If a future palette-gate edit breaks any of these, the gate is
    rejecting the gold standard and must be retuned.
    """
    failures: list[tuple[str, str]] = []
    for slide in approved_slides:
        gate = check_palette(slide)
        if gate.status != "PASS":
            failures.append((slide.name, gate.reason))
    assert not failures, (
        "Palette gate rejects approved reference slides:\n"
        + "\n".join(f"  {name}: {reason}" for name, reason in failures)
    )


# ─── Synthetic FAIL fixtures (regression library) ───────────────────────

def test_fails_for_yellow_field(tmp_path: Path) -> None:
    """Solid yellow background — the canonical failure mode."""
    path = _save_solid(tmp_path / "yellow.png", (240, 220, 90))
    gate = check_palette(path)
    assert gate.status == "FAIL"
    assert "blue/green" in gate.reason or "yellow-band" in gate.reason


def test_fails_for_mustard(tmp_path: Path) -> None:
    path = _save_solid(tmp_path / "mustard.png", (210, 170, 60))
    gate = check_palette(path)
    assert gate.status == "FAIL"


def test_fails_for_parchment(tmp_path: Path) -> None:
    path = _save_solid(tmp_path / "parchment.png", (228, 200, 140))
    gate = check_palette(path)
    assert gate.status == "FAIL"


def test_fails_for_sepia(tmp_path: Path) -> None:
    path = _save_solid(tmp_path / "sepia.png", (210, 180, 140))
    gate = check_palette(path)
    assert gate.status == "FAIL"


def test_fails_for_coffee_stained(tmp_path: Path) -> None:
    path = _save_solid(tmp_path / "coffee.png", (190, 165, 130))
    gate = check_palette(path)
    assert gate.status == "FAIL"


def test_fails_for_heavy_cream(tmp_path: Path) -> None:
    """Cream-heavy reads yellow at phone-screen viewing distance."""
    path = _save_solid(tmp_path / "cream.png", (240, 225, 175))
    gate = check_palette(path)
    assert gate.status == "FAIL"


# ─── Synthetic PASS fixtures (regression library) ───────────────────────

def test_passes_for_ivory_solid(tmp_path: Path) -> None:
    """Slightly more ivory than the approved range — should pass cleanly."""
    path = _save_solid(tmp_path / "ivory.png", (248, 243, 232))
    gate = check_palette(path)
    assert gate.status == "PASS", gate.reason


def test_passes_for_ivory_with_navy_accents(tmp_path: Path) -> None:
    """Real illustrations have color accents over ivory paper."""
    arr = np.full((640, 512, 3), (248, 243, 232), dtype=np.uint8)
    arr[80:200, 80:300] = (40, 60, 110)
    arr[400:500, 200:400] = (160, 80, 70)  # terracotta accent
    path = tmp_path / "ivory-accents.png"
    Image.fromarray(arr).save(path)
    gate = check_palette(path)
    assert gate.status == "PASS", gate.reason


# ─── Edge cases ─────────────────────────────────────────────────────────

def test_fails_when_image_missing(tmp_path: Path) -> None:
    gate = check_palette(tmp_path / "does-not-exist.png")
    assert gate.status == "FAIL"
    assert "missing" in gate.reason.lower()


def test_reason_carries_measurements(tmp_path: Path) -> None:
    """PASS or FAIL, the reason must include measured values for repair."""
    path = _save_solid(tmp_path / "ivory.png", (248, 243, 232))
    gate = check_palette(path)
    assert "paper RGB" in gate.reason
    assert "yellow-band fraction" in gate.reason


def test_threshold_constants_documented_and_sane() -> None:
    """Tripwire: if a future edit relaxes thresholds, it must be deliberate."""
    assert PAPER_R_MIN == 230
    assert PAPER_SATURATION_MAX == 0.18
