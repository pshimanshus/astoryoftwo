from __future__ import annotations

from pathlib import Path

from PIL import Image

from pipeline.stages.carousel_visual_storytelling import (
    ExpectedFrameAsset,
    current_creator_correction_fingerprint,
    generation_payload_fingerprint,
    image_file_fingerprint,
    storyboard_source_fingerprint,
    validate_director_storyboard,
    validate_frame_readability,
)


def write_png(path: Path, size: tuple[int, int] = (1080, 1440), color: str = "ivory") -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    Image.new("RGB", size, color).save(path)


def action_slides() -> dict:
    return {
        "slides": [
            {
                "slide": 1,
                "copy": "We both knew who.",
                "physical_action": "Aachu and Zuv pull the dining table toward opposite walls, stretching the tablecloth between them.",
            },
            {
                "slide": 2,
                "copy": "We were still learning how.",
                "physical_action": "They stop, meet each other's eyes, and carry the same table together toward the window.",
            },
        ]
    }


def passing_frame(path: str, digest: str, *, slide: int = 1) -> dict:
    return {
        "slide": slide,
        "format": "instagram_post",
        "file": path,
        "status": "PASS",
        "core_action_legible": True,
        "relationship_turn_legible": True,
        "observed_image_first_read": "They pull one table in opposite directions and visibly disagree about where their shared life should go.",
        "evidence": "Both hands grip opposite table edges; the stretched cloth and diverging feet make the conflict readable.",
        "image_fingerprint": digest,
    }


def test_storyboard_fingerprint_tracks_copy_and_physical_action() -> None:
    slides = action_slides()
    first = storyboard_source_fingerprint(slides)
    slides["slides"][0]["physical_action"] = "They now carry the same table together."

    assert storyboard_source_fingerprint(slides) != first


def test_generation_payload_fingerprint_is_stable_for_key_order() -> None:
    assert generation_payload_fingerprint({"b": 2, "a": 1}) == generation_payload_fingerprint(
        {"a": 1, "b": 2}
    )


def test_empty_creator_correction_state_is_stable(tmp_path: Path) -> None:
    assert current_creator_correction_fingerprint(tmp_path) == current_creator_correction_fingerprint(
        tmp_path
    )


def test_preflight_accepts_concrete_actions_without_event_a_provenance() -> None:
    slides = action_slides()
    direction = {
        "slides": [
            {"slide": 1, "physical_action": slides["slides"][0]["physical_action"]},
            {"slide": 2, "physical_action": slides["slides"][1]["physical_action"]},
        ],
        "requested_formats": ["instagram_post"],
    }

    issues = validate_director_storyboard(
        direction,
        slide_count=2,
        expected_slides=slides,
        expected_formats=["instagram_post"],
    )

    assert issues == []


def test_preflight_rejects_mood_instead_of_physical_action() -> None:
    issues = validate_director_storyboard(
        {"slides": [{"slide": 1, "physical_action": "dreamy romantic room"}]},
        slide_count=1,
    )

    assert any("concrete physical action" in issue for issue in issues)


def test_preflight_rejects_format_drift() -> None:
    issues = validate_director_storyboard(
        {
            "requested_formats": ["square"],
            "slides": [
                {
                    "slide": 1,
                    "physical_action": "They pull the dining table toward opposite walls while the dinner plates slide apart.",
                }
            ],
        },
        slide_count=1,
        expected_formats=["instagram_post"],
    )

    assert any("format lock" in issue for issue in issues)


def test_pixel_read_passes_without_event_a_or_reviewer_provenance(tmp_path: Path) -> None:
    image = tmp_path / "final" / "slide-01.png"
    write_png(image)
    check = {
        "status": "PASS",
        "pass": True,
        "image_first": True,
        "frames": [passing_frame("final/slide-01.png", image_file_fingerprint(image))],
        "issues": [],
    }

    issues = validate_frame_readability(
        check,
        slide_count=1,
        required_formats=["instagram_post"],
        expected_frame_bindings={
            (1, "instagram_post"): ExpectedFrameAsset(
                "final/slide-01.png", (1080, 1440)
            )
        },
        package_dir=tmp_path,
        require_files=True,
    )

    assert issues == []


def test_pixel_read_fails_fast_on_unreadable_action(tmp_path: Path) -> None:
    image = tmp_path / "final" / "slide-01.png"
    write_png(image)
    frame = passing_frame("final/slide-01.png", image_file_fingerprint(image))
    frame["core_action_legible"] = False
    frame["relationship_turn_legible"] = False

    issues = validate_frame_readability(
        {"status": "FAIL", "pass": False, "frames": [frame]},
        slide_count=1,
        required_formats=["instagram_post"],
    )

    assert issues == [
        "semantic_action failed on rendered slide 1 (core_action_legible)."
    ]


def test_pixel_read_rejects_stale_image_hash(tmp_path: Path) -> None:
    image = tmp_path / "final" / "slide-01.png"
    write_png(image)
    frame = passing_frame("final/slide-01.png", "sha256:" + "0" * 64)

    issues = validate_frame_readability(
        {"status": "PASS", "pass": True, "frames": [frame]},
        slide_count=1,
        required_formats=["instagram_post"],
        expected_frame_bindings={
            (1, "instagram_post"): ExpectedFrameAsset(
                "final/slide-01.png", (1080, 1440)
            )
        },
        package_dir=tmp_path,
        require_files=True,
    )

    assert any("image_fingerprint is missing or stale" in issue for issue in issues)


def test_pixel_read_rejects_wrong_dimensions(tmp_path: Path) -> None:
    image = tmp_path / "final" / "slide-01.png"
    write_png(image, (1080, 1080))

    issues = validate_frame_readability(
        {
            "status": "PASS",
            "pass": True,
            "frames": [passing_frame("final/slide-01.png", image_file_fingerprint(image))],
        },
        slide_count=1,
        required_formats=["instagram_post"],
        expected_frame_bindings={
            (1, "instagram_post"): ExpectedFrameAsset(
                "final/slide-01.png", (1080, 1440)
            )
        },
        package_dir=tmp_path,
        require_files=True,
    )

    assert any("dimensions are 1080x1080" in issue for issue in issues)


def test_pixel_read_rejects_path_escape(tmp_path: Path) -> None:
    outside = tmp_path.parent / "outside.png"
    write_png(outside)
    frame = passing_frame("../outside.png", image_file_fingerprint(outside))

    issues = validate_frame_readability(
        {"status": "PASS", "pass": True, "frames": [frame]},
        slide_count=1,
        required_formats=["instagram_post"],
        package_dir=tmp_path,
        require_files=True,
    )

    assert any("must not escape" in issue for issue in issues)


def test_pixel_read_requires_every_locked_frame(tmp_path: Path) -> None:
    image = tmp_path / "final" / "slide-01.png"
    write_png(image)
    issues = validate_frame_readability(
        {
            "status": "PASS",
            "pass": True,
            "frames": [passing_frame("final/slide-01.png", image_file_fingerprint(image))],
        },
        slide_count=2,
        required_formats=["instagram_post"],
        package_dir=tmp_path,
        require_files=True,
    )

    assert any("2:instagram_post" in issue for issue in issues)
