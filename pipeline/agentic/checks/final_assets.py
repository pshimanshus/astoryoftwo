from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from PIL import Image


EXPECTED_FINAL_ASSETS = {
    "instagram_post": {
        "default_path": "final/slide-{slide:02d}.png",
        "size": (1080, 1440),
        "label": "Instagram post",
    },
    "reels_stories": {
        "default_path": "final-reels-stories/slide-{slide:02d}.png",
        "size": (1080, 1920),
        "label": "Reels/Stories",
    },
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
    expected_files = record.get("expected_files") or {}

    if asset_key == "instagram_post":
        return (
            record.get("file")
            or expected_files.get("instagram_post")
            or EXPECTED_FINAL_ASSETS[asset_key]["default_path"].format(slide=slide)
        )

    if asset_key == "reels_stories":
        return (
            record.get("reels_stories_file")
            or expected_files.get("reels_stories")
            or EXPECTED_FINAL_ASSETS[asset_key]["default_path"].format(slide=slide)
        )

    raise ValueError(f"Unsupported asset key: {asset_key}")


def _manifest_slide_records(package_dir: Path) -> list[dict[str, Any]]:
    final_images = _read_json(package_dir / "final-images.json")

    slides = final_images.get("slides")
    if isinstance(slides, list) and slides:
        return [slide for slide in slides if isinstance(slide, dict)]

    slide_count = final_images.get("slide_count")
    if isinstance(slide_count, int) and slide_count > 0:
        return [{"slide": index} for index in range(1, slide_count + 1)]

    # Last-resort inference from files already present.
    detected_numbers: set[int] = set()
    for folder in ("final", "final-reels-stories"):
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

    Required per slide:
    - final/slide-XX.png => 1080x1440
    - final-reels-stories/slide-XX.png => 1080x1920

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

        for asset_key, contract in EXPECTED_FINAL_ASSETS.items():
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
