from __future__ import annotations

import json
from pathlib import Path

import pytest
from PIL import Image

from pipeline.agentic.checks.final_assets import validate_publishable_final_assets
from pipeline.stages.carousel_format_contract import (
    INSTAGRAM_POST_FORMAT,
    REELS_STORIES_FORMAT,
    SQUARE_FORMAT,
    expected_frame_bindings,
    expected_output_path,
    format_contract_fingerprint,
    locked_formats,
    write_format_contract,
)


def _write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload), encoding="utf-8")


def _write_png(path: Path, size: tuple[int, int]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    Image.new("RGB", size, "white").save(path)


def _publishable_package(tmp_path: Path, formats: list[str]) -> Path:
    package = tmp_path / "carousel"
    write_format_contract(package, formats, source="test_request")
    _write_json(package / "final-images.json", {"slide_count": 1, "slides": [{"slide": 1}]})
    return package


def test_default_contract_is_post_only_and_never_infers_reels_folder(tmp_path: Path) -> None:
    package = tmp_path / "carousel"
    (package / "final-reels-stories").mkdir(parents=True)
    _write_png(package / "final-reels-stories" / "slide-01.png", (1080, 1920))

    assert locked_formats(package) == (INSTAGRAM_POST_FORMAT,)


def test_legacy_explicit_request_metadata_wins_over_generated_folders(tmp_path: Path) -> None:
    package = tmp_path / "carousel"
    _write_json(package / "image-generation.json", {"requested_formats": [SQUARE_FORMAT]})
    _write_png(package / "final" / "slide-01.png", (1080, 1440))

    assert locked_formats(package) == (SQUARE_FORMAT,)


def test_contract_exposes_canonical_paths_dimensions_and_stable_fingerprint(tmp_path: Path) -> None:
    package = tmp_path / "carousel"
    contract = write_format_contract(
        package,
        [REELS_STORIES_FORMAT, INSTAGRAM_POST_FORMAT, SQUARE_FORMAT],
        source="test_request",
    )

    assert locked_formats(package) == (
        INSTAGRAM_POST_FORMAT,
        REELS_STORIES_FORMAT,
        SQUARE_FORMAT,
    )
    bindings = expected_frame_bindings(package, 1)
    assert bindings[(1, INSTAGRAM_POST_FORMAT)] == {
        "relative_path": "final/slide-01.png",
        "dimensions": (1080, 1440),
        "width": 1080,
        "height": 1440,
    }
    assert bindings[(1, REELS_STORIES_FORMAT)]["relative_path"] == (
        "final-reels-stories/slide-01.png"
    )
    assert bindings[(1, SQUARE_FORMAT)]["relative_path"] == "final-square/slide-01.png"
    assert format_contract_fingerprint(contract) == format_contract_fingerprint(
        [INSTAGRAM_POST_FORMAT, REELS_STORIES_FORMAT, SQUARE_FORMAT]
    )


def test_explicit_contract_cannot_be_silently_replaced(tmp_path: Path) -> None:
    package = tmp_path / "carousel"
    write_format_contract(package, [REELS_STORIES_FORMAT], source="creator_request")

    with pytest.raises(ValueError, match="already locked"):
        write_format_contract(package, [INSTAGRAM_POST_FORMAT], source="implicit_default")


@pytest.mark.parametrize(
    ("output_format", "size"),
    [
        (INSTAGRAM_POST_FORMAT, (1080, 1440)),
        (REELS_STORIES_FORMAT, (1080, 1920)),
        (SQUARE_FORMAT, (1080, 1080)),
    ],
)
def test_single_requested_format_passes_without_unrequested_outputs(
    tmp_path: Path, output_format: str, size: tuple[int, int]
) -> None:
    package = _publishable_package(tmp_path, [output_format])
    _write_png(expected_output_path(package, output_format, 1), size)

    report = validate_publishable_final_assets(package)

    assert report.ok, report.issues


def test_explicit_multi_format_requires_every_locked_output(tmp_path: Path) -> None:
    package = _publishable_package(
        tmp_path,
        [INSTAGRAM_POST_FORMAT, REELS_STORIES_FORMAT, SQUARE_FORMAT],
    )
    _write_png(expected_output_path(package, INSTAGRAM_POST_FORMAT, 1), (1080, 1440))
    _write_png(expected_output_path(package, REELS_STORIES_FORMAT, 1), (1080, 1920))

    report = validate_publishable_final_assets(package)

    assert not report.ok
    assert any(issue.path == "final-square/slide-01.png" for issue in report.issues)


def test_unrequested_extra_output_is_not_required_or_used_as_format_inference(tmp_path: Path) -> None:
    package = _publishable_package(tmp_path, [INSTAGRAM_POST_FORMAT])
    _write_png(expected_output_path(package, INSTAGRAM_POST_FORMAT, 1), (1080, 1440))
    _write_png(expected_output_path(package, REELS_STORIES_FORMAT, 1), (10, 10))

    report = validate_publishable_final_assets(package)

    assert report.ok, report.issues
