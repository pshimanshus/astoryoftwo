"""OCR check — does the rendered on-image text match `slides.md`?

Uses easyocr if available. easyocr is a large dependency (pulls torch),
so it is imported lazily and the check degrades to a STOP status if
easyocr is not installed. STOP is treated as a soft non-blocker by the
runner; PASS/FAIL are hard signals.

Matching strategy (in order):
  1. Exact substring after normalization → PASS. The strongest signal.
  2. For multi-word expected text only: rapidfuzz token_set_ratio
     similarity ≥ 85 → PASS. token_set_ratio is robust to single-character
     OCR errors and word-order variation but rejects word swaps
     ('dumber' vs 'dumbest' scores ~77, not ~91 like partial_ratio).
  3. Otherwise → FAIL.

Single-word expected text skips the fuzzy fallback entirely — a model
that rendered the wrong word as a single-word slide is a real failure,
not OCR noise.

Install OCR backend with: venv/bin/pip install easyocr
"""

from __future__ import annotations

import re
from functools import lru_cache
from pathlib import Path
from typing import Any

from rapidfuzz import fuzz

from pipeline.agentic.contracts import WorkflowGate


SIMILARITY_THRESHOLD = 85  # rapidfuzz token_set_ratio score 0-100


@lru_cache(maxsize=1)
def _reader() -> Any:
    import easyocr  # noqa: WPS433  (lazy heavy import is intentional)

    return easyocr.Reader(["en"], gpu=False, verbose=False)


def _easyocr_available() -> bool:
    try:
        import easyocr  # noqa: F401
    except Exception:
        return False
    return True


def _normalize(text: str) -> str:
    return re.sub(r"\s+", " ", text.lower().strip())


def _is_single_word(text: str) -> bool:
    return " " not in text.strip()


def check_ocr_text(image_path: Path, expected_text: str) -> WorkflowGate:
    image_path = Path(image_path)
    if not image_path.exists():
        return WorkflowGate(
            name="ocr_text",
            status="FAIL",
            reason=f"image missing: {image_path}",
        )

    if not _easyocr_available():
        return WorkflowGate(
            name="ocr_text",
            status="STOP",
            reason=(
                "easyocr is not installed; install with `venv/bin/pip install easyocr` "
                "to enable on-image text verification. Treating as soft skip."
            ),
            evidence_paths=[str(image_path)],
        )

    reader = _reader()
    try:
        detections = reader.readtext(str(image_path), detail=0)
    except Exception as exc:
        return WorkflowGate(
            name="ocr_text",
            status="FAIL",
            reason=f"easyocr readtext failed: {exc}",
            evidence_paths=[str(image_path)],
        )

    detected = _normalize(" ".join(detections))
    expected = _normalize(expected_text)

    if not expected:
        return WorkflowGate(
            name="ocr_text",
            status="PASS",
            reason="no expected text for this slide",
        )

    # Strongest signal: exact substring after normalization.
    if expected in detected:
        return WorkflowGate(
            name="ocr_text",
            status="PASS",
            reason="expected text found verbatim",
            evidence_paths=[str(image_path)],
        )

    # Single-word slides skip the fuzzy fallback. A model that rendered
    # the wrong word is a real failure, not OCR noise.
    if _is_single_word(expected):
        return WorkflowGate(
            name="ocr_text",
            status="FAIL",
            reason=(
                f"expected single word '{expected_text}' not found in detected text "
                f"'{detected[:160]}'; single-word slides require exact match"
            ),
            evidence_paths=[str(image_path)],
        )

    # Multi-word fallback: token_set_ratio tolerates one-char OCR errors
    # and word-order variation, but rejects word swaps and unrelated text.
    similarity = fuzz.token_set_ratio(expected, detected)
    if similarity >= SIMILARITY_THRESHOLD:
        return WorkflowGate(
            name="ocr_text",
            status="PASS",
            reason=(
                f"fuzzy token-set match: similarity={similarity:.0f}/100 "
                f">= threshold {SIMILARITY_THRESHOLD}"
            ),
            evidence_paths=[str(image_path)],
        )

    return WorkflowGate(
        name="ocr_text",
        status="FAIL",
        reason=(
            f"expected '{expected_text}' not found; "
            f"detected: '{detected[:160]}'; "
            f"token-set similarity={similarity:.0f}/100 < threshold {SIMILARITY_THRESHOLD}"
        ),
        evidence_paths=[str(image_path)],
    )
