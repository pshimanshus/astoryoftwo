"""Palette gate tests — synthesized Pillow fixtures, no real carousel files."""

from __future__ import annotations

from pathlib import Path

import numpy as np
from PIL import Image

from pipeline.agentic.checks.palette import (
    IVORY_TARGET_RGB,
    check_palette,
)


def _save_solid(path: Path, rgb: tuple[int, int, int], size: tuple[int, int] = (256, 256)) -> Path:
    Image.new("RGB", size, color=rgb).save(path)
    return path


def test_palette_passes_for_ivory_image(tmp_path: Path) -> None:
    path = _save_solid(tmp_path / "ivory.png", IVORY_TARGET_RGB)
    gate = check_palette(path)
    assert gate.status == "PASS"
    assert "within" in gate.reason
    assert str(path) in gate.evidence_paths


def test_palette_passes_within_tolerance(tmp_path: Path) -> None:
    nudged = (IVORY_TARGET_RGB[0] - 10, IVORY_TARGET_RGB[1] + 5, IVORY_TARGET_RGB[2] + 8)
    path = _save_solid(tmp_path / "ivory-nudged.png", nudged)
    gate = check_palette(path)
    assert gate.status == "PASS"


def test_palette_fails_for_yellow_image(tmp_path: Path) -> None:
    path = _save_solid(tmp_path / "yellow.png", (240, 220, 90))
    gate = check_palette(path)
    assert gate.status == "FAIL"
    reason = gate.reason.lower()
    assert "yellow_fraction" in reason or "exceeds" in reason


def test_palette_fails_for_parchment_image(tmp_path: Path) -> None:
    path = _save_solid(tmp_path / "parchment.png", (228, 200, 140))
    gate = check_palette(path)
    assert gate.status == "FAIL"


def test_palette_fails_when_image_missing(tmp_path: Path) -> None:
    gate = check_palette(tmp_path / "does-not-exist.png")
    assert gate.status == "FAIL"
    assert "missing" in gate.reason.lower()


def test_palette_passes_with_mostly_ivory_some_color(tmp_path: Path) -> None:
    """A real illustration has color accents; mostly-ivory should still pass."""
    arr = np.full((512, 512, 3), IVORY_TARGET_RGB, dtype=np.uint8)
    # Add a navy patch (well outside yellow band) over ~10% of the image
    arr[50:150, 50:200] = (40, 60, 110)
    path = tmp_path / "ivory-with-navy.png"
    Image.fromarray(arr).save(path)
    gate = check_palette(path)
    assert gate.status == "PASS"


def test_palette_fails_when_paper_is_yellow_field(tmp_path: Path) -> None:
    """Field-of-mustard background should fail by yellow-fraction even if median is in tol."""
    arr = np.full((512, 512, 3), (240, 200, 80), dtype=np.uint8)
    path = tmp_path / "mustard.png"
    Image.fromarray(arr).save(path)
    gate = check_palette(path)
    assert gate.status == "FAIL"
