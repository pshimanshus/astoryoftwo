"""OCR gate tests.

The OCR module degrades to a STOP (soft-skip) gate when easyocr is not
installed. Hard-mode tests (PASS/FAIL) are skipped in that case so the
suite stays fast and offline-friendly. To exercise the hard path:

    venv/bin/pip install easyocr
    venv/bin/python -m pytest tests/test_checks_ocr_text.py -q
"""

from __future__ import annotations

from pathlib import Path

import pytest
from PIL import Image, ImageDraw

from pipeline.agentic.checks.ocr_text import _easyocr_available, check_ocr_text


easyocr_required = pytest.mark.skipif(
    not _easyocr_available(),
    reason="easyocr not installed; pip install easyocr to run hard-mode OCR tests",
)


def _render_text_image(
    path: Path,
    text: str,
    *,
    size: tuple[int, int] = (640, 480),
    color: tuple[int, int, int] = (40, 40, 40),
    bg: tuple[int, int, int] = (245, 240, 228),
) -> Path:
    img = Image.new("RGB", size, color=bg)
    draw = ImageDraw.Draw(img)
    # Use default PIL font; size is small but easyocr handles it.
    try:
        from PIL import ImageFont
        font = ImageFont.load_default(size=48)
    except TypeError:  # older Pillow
        font = None
    draw.text((40, size[1] // 2 - 24), text, fill=color, font=font)
    img.save(path)
    return path


def test_gate_returns_stop_when_easyocr_unavailable(tmp_path, monkeypatch) -> None:
    """Force the unavailable path to verify graceful degradation."""
    import pipeline.agentic.checks.ocr_text as ocr_mod

    monkeypatch.setattr(ocr_mod, "_easyocr_available", lambda: False)
    path = _render_text_image(tmp_path / "hello.png", "hello")
    gate = check_ocr_text(path, "hello")
    assert gate.status == "STOP"
    assert "easyocr" in gate.reason.lower()


def test_gate_fails_in_publish_mode_when_easyocr_unavailable(tmp_path, monkeypatch) -> None:
    import pipeline.agentic.checks.ocr_text as ocr_mod

    monkeypatch.setattr(ocr_mod, "_easyocr_available", lambda: False)
    path = _render_text_image(tmp_path / "hello.png", "hello")
    gate = check_ocr_text(path, "hello", publish_mode=True)
    assert gate.status == "FAIL"
    assert "publish" in gate.reason.lower()
    assert "easyocr" in gate.reason.lower()


def test_gate_fails_when_image_missing(tmp_path) -> None:
    gate = check_ocr_text(tmp_path / "missing.png", "anything")
    assert gate.status == "FAIL"
    assert "missing" in gate.reason.lower()


def test_gate_passes_when_no_expected_text(tmp_path, monkeypatch) -> None:
    """Empty expected text always passes (the slide has no on-image text)."""
    import pipeline.agentic.checks.ocr_text as ocr_mod

    # Force easyocr available + stub the reader to avoid downloading models.
    monkeypatch.setattr(ocr_mod, "_easyocr_available", lambda: True)

    class _StubReader:
        def readtext(self, _path, detail=0):
            return []

    monkeypatch.setattr(ocr_mod, "_reader", lambda: _StubReader())

    path = _render_text_image(tmp_path / "blank.png", "")
    gate = check_ocr_text(path, "")
    assert gate.status == "PASS"


def test_gate_fails_with_stubbed_reader_when_text_missing(tmp_path, monkeypatch) -> None:
    """Hard-fail path without easyocr: stub the reader to return unrelated text."""
    import pipeline.agentic.checks.ocr_text as ocr_mod

    monkeypatch.setattr(ocr_mod, "_easyocr_available", lambda: True)

    class _StubReader:
        def readtext(self, _path, detail=0):
            return ["some other text entirely"]

    monkeypatch.setattr(ocr_mod, "_reader", lambda: _StubReader())

    path = _render_text_image(tmp_path / "drift.png", "anything")
    gate = check_ocr_text(path, "dumber")
    assert gate.status == "FAIL"
    assert "dumber" in gate.reason


def test_gate_passes_with_stubbed_reader_when_text_matches(tmp_path, monkeypatch) -> None:
    import pipeline.agentic.checks.ocr_text as ocr_mod

    monkeypatch.setattr(ocr_mod, "_easyocr_available", lambda: True)

    class _StubReader:
        def readtext(self, _path, detail=0):
            return ["she", "noticed"]

    monkeypatch.setattr(ocr_mod, "_reader", lambda: _StubReader())

    path = _render_text_image(tmp_path / "match.png", "she noticed")
    gate = check_ocr_text(path, "she noticed")
    assert gate.status == "PASS"


def test_gate_passes_under_fuzzy_match_for_one_character_ocr_error(tmp_path, monkeypatch) -> None:
    """Real-world OCR error: 'noticed' read as 'noticei'. Should still PASS
    via fuzzy match because the typography on phone-screen is fine."""
    import pipeline.agentic.checks.ocr_text as ocr_mod

    monkeypatch.setattr(ocr_mod, "_easyocr_available", lambda: True)

    class _StubReader:
        def readtext(self, _path, detail=0):
            return ["she noticei"]

    monkeypatch.setattr(ocr_mod, "_reader", lambda: _StubReader())

    path = _render_text_image(tmp_path / "noticei.png", "she noticed")
    gate = check_ocr_text(path, "she noticed")
    assert gate.status == "PASS"
    assert "fuzzy token-set match" in gate.reason
    assert "similarity" in gate.reason


def test_gate_fails_for_single_word_swap_no_fuzzy_pass(tmp_path, monkeypatch) -> None:
    """'dumber' vs 'dumbest' was a partial_ratio false positive. With
    token_set_ratio + single-word strict mode, it correctly FAILS."""
    import pipeline.agentic.checks.ocr_text as ocr_mod

    monkeypatch.setattr(ocr_mod, "_easyocr_available", lambda: True)

    class _StubReader:
        def readtext(self, _path, detail=0):
            return ["dumbest"]

    monkeypatch.setattr(ocr_mod, "_reader", lambda: _StubReader())

    path = _render_text_image(tmp_path / "swap.png", "dumbest")
    gate = check_ocr_text(path, "dumber")
    assert gate.status == "FAIL"
    assert "single-word" in gate.reason


def test_gate_passes_for_word_drop_in_multi_word_phrase(tmp_path, monkeypatch) -> None:
    """OCR misses one word in a long phrase — token_set tolerates this."""
    import pipeline.agentic.checks.ocr_text as ocr_mod

    monkeypatch.setattr(ocr_mod, "_easyocr_available", lambda: True)

    class _StubReader:
        def readtext(self, _path, detail=0):
            return ["the menu was just formality"]

    monkeypatch.setattr(ocr_mod, "_reader", lambda: _StubReader())

    path = _render_text_image(tmp_path / "drop.png", "the menu was just a formality")
    gate = check_ocr_text(path, "the menu was just a formality")
    assert gate.status == "PASS"


def test_gate_passes_under_fuzzy_match_for_minor_word_swap(tmp_path, monkeypatch) -> None:
    """OCR reads a small variant like 'the' vs 'tho' — still close enough."""
    import pipeline.agentic.checks.ocr_text as ocr_mod

    monkeypatch.setattr(ocr_mod, "_easyocr_available", lambda: True)

    class _StubReader:
        def readtext(self, _path, detail=0):
            return ["he didnt marry organized"]

    monkeypatch.setattr(ocr_mod, "_reader", lambda: _StubReader())

    path = _render_text_image(tmp_path / "near.png", "he didn't marry organized")
    gate = check_ocr_text(path, "he didn't marry organized")
    # Either exact substring (after normalization removes the apostrophe difference)
    # or fuzzy partial match must pass.
    assert gate.status == "PASS"


def test_gate_fails_when_fuzzy_similarity_below_threshold(tmp_path, monkeypatch) -> None:
    """Detected text is unrelated to expected — should not fuzzy-pass."""
    import pipeline.agentic.checks.ocr_text as ocr_mod

    monkeypatch.setattr(ocr_mod, "_easyocr_available", lambda: True)

    class _StubReader:
        def readtext(self, _path, detail=0):
            return ["completely unrelated wording about plants"]

    monkeypatch.setattr(ocr_mod, "_reader", lambda: _StubReader())

    path = _render_text_image(tmp_path / "drift.png", "she noticed")
    gate = check_ocr_text(path, "she noticed")
    assert gate.status == "FAIL"
    assert "similarity" in gate.reason


@easyocr_required
def test_gate_passes_for_real_render(tmp_path: Path) -> None:
    """Real easyocr round-trip. Skipped when easyocr is not installed."""
    path = _render_text_image(tmp_path / "real.png", "dumber")
    gate = check_ocr_text(path, "dumber")
    assert gate.status == "PASS", gate.reason


@easyocr_required
def test_gate_fails_for_real_drift(tmp_path: Path) -> None:
    path = _render_text_image(tmp_path / "drift.png", "dumber")
    gate = check_ocr_text(path, "she noticed")
    assert gate.status == "FAIL"
