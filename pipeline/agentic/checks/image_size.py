"""Image size check — is this a real native image export?

Catches "single image resized into the other format" failures by
requiring the exact native pixel dimensions for the requested surface.
"""

from __future__ import annotations

from pathlib import Path

from PIL import Image

from pipeline.agentic.contracts import WorkflowGate


EXACT_DIMENSIONS = {
    "3:4": (1080, 1440),
    "9:16": (1080, 1920),
    "1:1": (1080, 1080),
    "square": (1080, 1080),
    "square_1080": (1080, 1080),
}


def check_image_size(image_path: Path, aspect: str) -> WorkflowGate:
    image_path = Path(image_path)
    if aspect not in EXACT_DIMENSIONS:
        return WorkflowGate(
            name="image_size",
            status="FAIL",
            reason=f"unknown aspect '{aspect}' (expected one of {sorted(EXACT_DIMENSIONS)})",
        )
    if not image_path.exists():
        return WorkflowGate(
            name="image_size",
            status="FAIL",
            reason=f"image missing: {image_path}",
        )

    exact_w, exact_h = EXACT_DIMENSIONS[aspect]
    with Image.open(image_path) as img:
        width, height = img.size

    if (width, height) != (exact_w, exact_h):
        return WorkflowGate(
            name="image_size",
            status="FAIL",
            reason=f"{width}x{height} != exact {exact_w}x{exact_h} for {aspect}",
            evidence_paths=[str(image_path)],
        )
    return WorkflowGate(
        name="image_size",
        status="PASS",
        reason=f"{width}x{height} matches exact {aspect}",
        evidence_paths=[str(image_path)],
    )
