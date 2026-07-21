from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from PIL import Image

from pipeline.stages.carousel_format_contract import (
    SUPPORTED_NATIVE_FORMATS,
    expected_output_relative_path,
    format_spec,
    locked_formats,
)

EXPECTED_FINAL_ASSETS = {
    output_format: {
        "default_path": (
            f"{format_spec(output_format)['folder']}/slide-{{slide:02d}}.png"
        ),
        "size": format_spec(output_format)["target_size"],
        "label": format_spec(output_format)["label"],
    }
    for output_format in SUPPORTED_NATIVE_FORMATS
}


@dataclass(frozen=True)
class FinalAssetIssue:
    code: str
    severity: str
    path: str
    reason: str


@dataclass(frozen=True)
class FinalAssetReport:
    ok: bool
    issues: list[FinalAssetIssue]


def _read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}


def _slide_number(record: dict[str, Any], fallback: int) -> int:
    raw = record.get("slide", fallback)
    try:
        return int(raw)
    except (TypeError, ValueError):
        return fallback


def _expected_path_for_slide(
    record: dict[str, Any],
    slide: int,
    asset_key: str,
) -> str:
    del record
    return expected_output_relative_path(asset_key, slide)


def _manifest_slide_records(package_dir: Path) -> list[dict[str, Any]]:
    final_images = _read_json(package_dir / "final-images.json")

    slides = final_images.get("slides")
    if isinstance(slides, list) and slides:
        return [slide for slide in slides if isinstance(slide, dict)]

    slide_count = final_images.get("slide_count")
    if isinstance(slide_count, int) and slide_count > 0:
        return [{"slide": index} for index in range(1, slide_count + 1)]

    # Last-resort slide-number inference uses only folders selected by the
    # current-request contract; folder presence never selects a format.
    detected_numbers: set[int] = set()
    for output_format in locked_formats(package_dir):
        folder = str(format_spec(output_format)["folder"])
        for path in sorted((package_dir / folder).glob("slide-*.png")):
            try:
                detected_numbers.add(int(path.stem.replace("slide-", "")))
            except ValueError:
                continue

    return [{"slide": number} for number in sorted(detected_numbers)]


def _validate_one_image(
    package_dir: Path,
    relative_path: str,
    expected_size: tuple[int, int],
    label: str,
) -> list[FinalAssetIssue]:
    path = package_dir / relative_path

    if not path.exists():
        return [
            FinalAssetIssue(
                code="missing_final_image_asset",
                severity="blocker",
                path=relative_path,
                reason=f"{label} final image is missing.",
            )
        ]

    if not path.is_file():
        return [
            FinalAssetIssue(
                code="invalid_final_image_asset",
                severity="blocker",
                path=relative_path,
                reason=f"{label} final image path exists but is not a file.",
            )
        ]

    try:
        with Image.open(path) as image:
            actual_size = image.size
            image.load()
    except Exception as exc:
        return [
            FinalAssetIssue(
                code="invalid_final_image_asset",
                severity="blocker",
                path=relative_path,
                reason=f"{label} final image is not a valid readable image: {exc}",
            )
        ]

    if actual_size != expected_size:
        return [
            FinalAssetIssue(
                code="wrong_final_image_dimensions",
                severity="blocker",
                path=relative_path,
                reason=(
                    f"{label} final image must be exactly "
                    f"{expected_size[0]}x{expected_size[1]}, got "
                    f"{actual_size[0]}x{actual_size[1]}."
                ),
            )
        ]

    return []


def validate_publishable_final_assets(package_dir: Path) -> FinalAssetReport:
    """
    Validates the final generated assets required before a carousel package
    can be considered publishable.

    Required per slide: exactly the formats locked in format-contract.json.

    This intentionally checks real image readability, not just file existence.
    """
    package_dir = Path(package_dir)
    issues: list[FinalAssetIssue] = []

    slide_records = _manifest_slide_records(package_dir)
    if not slide_records:
        return FinalAssetReport(
            ok=False,
            issues=[
                FinalAssetIssue(
                    code="missing_final_slide_manifest",
                    severity="blocker",
                    path="final-images.json",
                    reason=(
                        "Cannot validate publishable final assets because "
                        "final-images.json has no slides or slide_count, and "
                        "no final slide files could be inferred."
                    ),
                )
            ],
        )

    for fallback_index, record in enumerate(slide_records, start=1):
        slide = _slide_number(record, fallback_index)

        for asset_key in locked_formats(package_dir):
            contract = EXPECTED_FINAL_ASSETS[asset_key]
            relative_path = _expected_path_for_slide(record, slide, asset_key)
            issues.extend(
                _validate_one_image(
                    package_dir=package_dir,
                    relative_path=relative_path,
                    expected_size=contract["size"],
                    label=f"{contract['label']} slide {slide}",
                )
            )

    return FinalAssetReport(ok=not issues, issues=issues)
