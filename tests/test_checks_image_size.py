"""Image-size gate tests — synthesized PIL fixtures."""

from __future__ import annotations

from pathlib import Path

from PIL import Image

from pipeline.agentic.checks.image_size import check_image_size


def _save_blank(path: Path, size: tuple[int, int]) -> Path:
    Image.new("RGB", size, color=(245, 240, 228)).save(path)
    return path


def test_passes_for_native_4x5_at_min(tmp_path: Path) -> None:
    path = _save_blank(tmp_path / "post.png", (1080, 1350))
    gate = check_image_size(path, "4:5")
    assert gate.status == "PASS"
    assert "1080x1350" in gate.reason


def test_passes_for_native_4x5_above_min(tmp_path: Path) -> None:
    path = _save_blank(tmp_path / "post-big.png", (1440, 1800))
    gate = check_image_size(path, "4:5")
    assert gate.status == "PASS"


def test_passes_for_native_9x16(tmp_path: Path) -> None:
    path = _save_blank(tmp_path / "reel.png", (1080, 1920))
    gate = check_image_size(path, "9:16")
    assert gate.status == "PASS"


def test_fails_when_aspect_ratio_wrong(tmp_path: Path) -> None:
    path = _save_blank(tmp_path / "square.png", (1080, 1080))
    gate = check_image_size(path, "4:5")
    assert gate.status == "FAIL"
    assert "ratio" in gate.reason.lower()


def test_fails_when_passing_4x5_image_through_9x16_gate(tmp_path: Path) -> None:
    """The 'one image resized into both formats' failure mode."""
    path = _save_blank(tmp_path / "post.png", (1080, 1350))
    gate = check_image_size(path, "9:16")
    assert gate.status == "FAIL"


def test_fails_below_minimum_dimensions(tmp_path: Path) -> None:
    path = _save_blank(tmp_path / "too-small.png", (720, 900))  # correct ratio, too small
    gate = check_image_size(path, "4:5")
    assert gate.status == "FAIL"
    assert "minimum" in gate.reason.lower()


def test_fails_when_image_missing(tmp_path: Path) -> None:
    gate = check_image_size(tmp_path / "missing.png", "4:5")
    assert gate.status == "FAIL"
    assert "missing" in gate.reason.lower()


def test_fails_on_unknown_aspect(tmp_path: Path) -> None:
    path = _save_blank(tmp_path / "img.png", (1080, 1350))
    gate = check_image_size(path, "1:1")
    assert gate.status == "FAIL"
    assert "unknown aspect" in gate.reason.lower()
