"""Image-size gate tests — synthesized PIL fixtures."""

from __future__ import annotations

from pathlib import Path

from PIL import Image

from pipeline.agentic.checks.image_size import check_image_size


def _save_blank(path: Path, size: tuple[int, int]) -> Path:
    Image.new("RGB", size, color=(245, 240, 228)).save(path)
    return path


def test_passes_for_exact_instagram_post_1080x1350(tmp_path: Path) -> None:
    path = _save_blank(tmp_path / "post.png", (1080, 1350))
    gate = check_image_size(path, "4:5")
    assert gate.status == "PASS"
    assert "1080x1350" in gate.reason
    assert "exact" in gate.reason.lower()


def test_fails_for_instagram_post_larger_than_exact(tmp_path: Path) -> None:
    path = _save_blank(tmp_path / "post-big.png", (1440, 1800))
    gate = check_image_size(path, "4:5")
    assert gate.status == "FAIL"
    assert "1080x1350" in gate.reason
    assert "exact" in gate.reason.lower()


def test_passes_for_exact_reels_stories_1080x1920(tmp_path: Path) -> None:
    path = _save_blank(tmp_path / "reel.png", (1080, 1920))
    gate = check_image_size(path, "9:16")
    assert gate.status == "PASS"
    assert "1080x1920" in gate.reason
    assert "exact" in gate.reason.lower()


def test_fails_for_reels_stories_larger_than_exact(tmp_path: Path) -> None:
    path = _save_blank(tmp_path / "reel-big.png", (1440, 2560))
    gate = check_image_size(path, "9:16")
    assert gate.status == "FAIL"
    assert "1080x1920" in gate.reason
    assert "exact" in gate.reason.lower()


def test_passes_for_exact_square_1080(tmp_path: Path) -> None:
    path = _save_blank(tmp_path / "square.png", (1080, 1080))
    gate = check_image_size(path, "square_1080")
    assert gate.status == "PASS"
    assert "exact" in gate.reason.lower()


def test_fails_square_1080_when_dimensions_are_not_exact(tmp_path: Path) -> None:
    path = _save_blank(tmp_path / "wrong-square.png", (1024, 1024))
    gate = check_image_size(path, "square_1080")
    assert gate.status == "FAIL"
    assert "exact" in gate.reason.lower()


def test_fails_square_1080_when_generated_tall(tmp_path: Path) -> None:
    path = _save_blank(tmp_path / "wrong-tall.png", (978, 1608))
    gate = check_image_size(path, "square_1080")
    assert gate.status == "FAIL"
    assert "1080x1080" in gate.reason


def test_fails_when_dimensions_are_wrong_for_requested_format(tmp_path: Path) -> None:
    path = _save_blank(tmp_path / "square.png", (1080, 1080))
    gate = check_image_size(path, "4:5")
    assert gate.status == "FAIL"
    assert "1080x1350" in gate.reason
    assert "exact" in gate.reason.lower()


def test_fails_when_passing_4x5_image_through_9x16_gate(tmp_path: Path) -> None:
    """The 'one image resized into both formats' failure mode."""
    path = _save_blank(tmp_path / "post.png", (1080, 1350))
    gate = check_image_size(path, "9:16")
    assert gate.status == "FAIL"


def test_fails_when_dimensions_are_not_exact_even_with_correct_ratio(tmp_path: Path) -> None:
    path = _save_blank(tmp_path / "too-small.png", (720, 900))  # correct ratio, too small
    gate = check_image_size(path, "4:5")
    assert gate.status == "FAIL"
    assert "exact" in gate.reason.lower()


def test_fails_when_image_missing(tmp_path: Path) -> None:
    gate = check_image_size(tmp_path / "missing.png", "4:5")
    assert gate.status == "FAIL"
    assert "missing" in gate.reason.lower()


def test_fails_on_unknown_aspect(tmp_path: Path) -> None:
    path = _save_blank(tmp_path / "img.png", (1080, 1350))
    gate = check_image_size(path, "2:3")
    assert gate.status == "FAIL"
    assert "unknown aspect" in gate.reason.lower()
