"""Palette gate tests — synthesized fixtures + real-image calibration.

The real-image suite is the load-bearing one: all four approved Cinematic
Observational Watercolor v1 source frames and their contact sheet MUST PASS. If a future
edit to the palette gate breaks any of those, the gate has regressed.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest
from PIL import Image, UnidentifiedImageError

from pipeline.agentic.checks.palette import (
    PAPER_R_MIN,
    PAPER_SATURATION_MAX,
    check_palette,
)


REFERENCE_BUNDLE = Path(__file__).resolve().parents[1] / (
    "config/references/style-lock/cinematic-observational-watercolor-v1"
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
    slides = sorted(REFERENCE_BUNDLE.glob("source-*.png"))
    if not slides:
        pytest.skip("approved style-lock bundle not found in repo")
    return slides


def test_every_approved_slide_passes(approved_slides: list[Path]) -> None:
    """All four Cinematic Observational Watercolor v1 source frames MUST PASS.

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


def test_approved_contact_sheet_passes() -> None:
    gate = check_palette(REFERENCE_BUNDLE / "contact-sheet.png")
    assert gate.status == "PASS", gate.reason


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


def test_measurement_cache_is_content_bound_not_path_bound(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from pipeline.agentic.checks import palette

    palette._MEASUREMENTS.clear()
    calls: list[int] = []
    original = palette._paper_region_stats

    def count(arr):
        calls.append(1)
        return original(arr)

    monkeypatch.setattr(palette, "_paper_region_stats", count)
    first = _save_solid(tmp_path / "first.png", (248, 243, 232))
    second = tmp_path / "second.png"
    second.write_bytes(first.read_bytes())
    first_gate = check_palette(first)
    second_gate = check_palette(second)
    assert first_gate.status == second_gate.status == "PASS"
    assert first_gate.evidence_paths == [str(first)]
    assert second_gate.evidence_paths == [str(second)]
    assert len(calls) == 1
    _save_solid(first, (255, 220, 60))
    assert check_palette(first).status == "FAIL"
    assert len(calls) == 2


def test_cached_measurements_apply_current_decision_thresholds(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from pipeline.agentic.checks import palette

    palette._MEASUREMENTS.clear()
    path = _save_solid(tmp_path / "ivory.png", (248, 243, 232), size=(16, 16))
    assert check_palette(path).status == "PASS"
    original_measurements = next(iter(palette._MEASUREMENTS.values()))
    monkeypatch.setattr(palette, "PAPER_R_MIN", 255)

    gate = check_palette(path)

    assert gate.status == "FAIL"
    assert "below min 255" in gate.reason
    assert len(palette._MEASUREMENTS) == 1
    assert next(iter(palette._MEASUREMENTS.values())) is original_measurements


@pytest.mark.parametrize(
    ("parameter", "value"),
    [
        ("PAPER_PERCENTILE", 86),
        ("YELLOW_BAND_HUE_RANGE", (34.0, 66.0)),
        ("YELLOW_BAND_SAT_MIN", 0.36),
    ],
)
def test_analysis_parameters_are_part_of_measurement_cache_key(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, parameter: str, value: object
) -> None:
    from pipeline.agentic.checks import palette

    palette._MEASUREMENTS.clear()
    path = _save_solid(tmp_path / "ivory.png", (248, 243, 232), size=(16, 16))
    assert check_palette(path).status == "PASS"
    monkeypatch.setattr(palette, parameter, value)

    assert check_palette(path).status == "PASS"
    assert len(palette._MEASUREMENTS) == 2


def test_measurement_cache_is_bounded_and_keeps_only_numeric_measurements(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from pipeline.agentic.checks import palette

    palette._MEASUREMENTS.clear()
    monkeypatch.setattr(palette, "_MEASUREMENT_CACHE_LIMIT", 2)
    first = _save_solid(tmp_path / "first.png", (248, 243, 232), size=(16, 16))
    second = _save_solid(tmp_path / "second.png", (249, 244, 233), size=(16, 16))
    third = _save_solid(tmp_path / "third.png", (250, 245, 234), size=(16, 16))
    check_palette(first)
    first_key = next(iter(palette._MEASUREMENTS))
    check_palette(second)
    second_key = next(reversed(palette._MEASUREMENTS))
    check_palette(first)  # The recently used entry must survive eviction.
    check_palette(third)

    assert len(palette._MEASUREMENTS) == 2
    assert first_key in palette._MEASUREMENTS
    assert second_key not in palette._MEASUREMENTS
    for paper, yellow_fraction in palette._MEASUREMENTS.values():
        assert all(isinstance(value, float) for value in paper.values())
        assert isinstance(yellow_fraction, float)


def test_cached_pass_does_not_hide_missing_or_corrupt_current_bytes(tmp_path: Path) -> None:
    from pipeline.agentic.checks import palette

    palette._MEASUREMENTS.clear()
    path = _save_solid(tmp_path / "changing.png", (248, 243, 232), size=(16, 16))
    assert check_palette(path).status == "PASS"
    path.unlink()
    assert check_palette(path).status == "FAIL"
    path.write_bytes(b"not an image")

    # Preserve the existing decode-error behavior; corruption is not cached as
    # a measurement or masked by a previous successful check at this path.
    with pytest.raises(UnidentifiedImageError):
        check_palette(path)
    assert len(palette._MEASUREMENTS) == 1
