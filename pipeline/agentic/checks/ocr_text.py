"""OCR check — does the rendered on-image text match `slides.md`?

Uses easyocr if available. easyocr is a large dependency (pulls torch),
so it is imported lazily and the check degrades to a SKIP status if
easyocr is not installed. SKIP is treated as a soft non-blocker by the
runner; PASS/FAIL are hard signals.

Install with: venv/bin/pip install easyocr
"""

from __future__ import annotations

import re
from functools import lru_cache
from pathlib import Path
from typing import Any

from pipeline.agentic.contracts import WorkflowGate


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

    if expected in detected:
        return WorkflowGate(
            name="ocr_text",
            status="PASS",
            reason="expected text found verbatim",
            evidence_paths=[str(image_path)],
        )

    return WorkflowGate(
        name="ocr_text",
        status="FAIL",
        reason=(
            f"expected '{expected_text}' not found; "
            f"detected: '{detected[:160]}'"
        ),
        evidence_paths=[str(image_path)],
    )
