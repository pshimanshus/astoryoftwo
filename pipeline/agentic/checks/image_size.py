"""Image size + aspect check — is this a real native 4:5 or 9:16 export?

Catches "single image resized into the other format" failures by
asserting both ratio (within tolerance) and minimum dimensions.
"""

from __future__ import annotations

from pathlib import Path

from PIL import Image

from pipeline.agentic.contracts import WorkflowGate


ASPECT_TARGETS = {
    "4:5": (4 / 5, 0.01),
    "9:16": (9 / 16, 0.01),
}
MIN_DIMENSIONS = {
    "4:5": (1080, 1350),
    "9:16": (1080, 1920),
}


def check_image_size(image_path: Path, aspect: str) -> WorkflowGate:
    image_path = Path(image_path)
    if aspect not in ASPECT_TARGETS:
        return WorkflowGate(
            name="image_size",
            status="FAIL",
            reason=f"unknown aspect '{aspect}' (expected one of {sorted(ASPECT_TARGETS)})",
        )
    if not image_path.exists():
        return WorkflowGate(
            name="image_size",
            status="FAIL",
            reason=f"image missing: {image_path}",
        )

    target_ratio, tol = ASPECT_TARGETS[aspect]
    min_w, min_h = MIN_DIMENSIONS[aspect]
    with Image.open(image_path) as img:
        width, height = img.size

    actual_ratio = width / height
    if abs(actual_ratio - target_ratio) > tol:
        return WorkflowGate(
            name="image_size",
            status="FAIL",
            reason=(
                f"{width}x{height} ratio {actual_ratio:.3f} != target "
                f"{target_ratio:.3f} (tol ±{tol})"
            ),
            evidence_paths=[str(image_path)],
        )
    if width < min_w or height < min_h:
        return WorkflowGate(
            name="image_size",
            status="FAIL",
            reason=f"{width}x{height} below minimum {min_w}x{min_h} for {aspect}",
            evidence_paths=[str(image_path)],
        )
    return WorkflowGate(
        name="image_size",
        status="PASS",
        reason=f"{width}x{height} matches {aspect}",
        evidence_paths=[str(image_path)],
    )
