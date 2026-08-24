from __future__ import annotations

import copy
from pathlib import Path

from PIL import Image

from pipeline.stages.carousel_quality import (
    validate_anatomy_inventory_check,
    validate_independent_reviewers,
    validate_scene_entity_integrity_check,
    validate_spatial_topology_check,
    validate_visual_richness_check,
)
from pipeline.stages.codex_builtin_image_generation import (
    image_set_sha256,
    sha256_binding,
    validate_exact_image_visual_qa,
)


def _candidate(tmp_path: Path) -> dict[str, object]:
    path = tmp_path / "candidate.png"
    Image.new("RGB", (1080, 1440), "ivory").save(path)
    return {
        "slide": 1,
        "copy": "Some days, love did not tell us what to do.",
        "attempt": 1,
        "native_outputs": {
            "instagram_post": {
                "path": "candidate.png",
                "sha256": sha256_binding(path.read_bytes()),
                "width": 1080,
                "height": 1440,
            }
        },
    }


def _passing_qa(candidate: dict[str, object]) -> dict[str, object]:
    copy_text = str(candidate["copy"])
    return {
        "schema_version": "carousel-pixel-qa/v1",
        "status": "PASS",
        "image_set_sha256": image_set_sha256([candidate]),
        "slides": [
            {
                "slide": 1,
                "native_outputs": copy.deepcopy(candidate["native_outputs"]),
                "checks": {
                    "semantic_action": {"status": "PASS", "evidence": "Both partners pull one shared map in opposite directions."},
                    "relationship_state": {"status": "PASS", "evidence": "Their conflict is visible while their shared table keeps them connected."},
                    "anatomy_spatial": {"status": "PASS", "evidence": "Two complete people have natural hands attached to the same map."},
                    "identity": {"status": "PASS", "evidence": "Both faces and whole-body proportions match Aachu and Zuv."},
                    "exact_text": {"status": "PASS", "expected": copy_text, "observed": copy_text, "evidence": "The rendered sentence matches exactly."},
                    "brandmark": {"status": "PASS", "observed": "@a.storyof.two", "evidence": "Tiny signature is visible at top-right."},
                    "style": {"status": "PASS", "evidence": "Warm ivory watercolor-and-ink rendering is consistent."},
                },
            }
        ],
    }


def test_actual_pixel_qa_passes_when_every_check_is_bound_to_exact_pixels(tmp_path: Path) -> None:
    candidate = _candidate(tmp_path)
    assert validate_exact_image_visual_qa(
        _passing_qa(candidate),
        [candidate],
        carousel_dir=tmp_path,
    ) == []


def test_semantic_failure_stops_before_identity_or_style_can_mask_it(tmp_path: Path) -> None:
    candidate = _candidate(tmp_path)
    qa = _passing_qa(candidate)
    qa["status"] = "FAIL"
    qa["slides"][0]["checks"]["semantic_action"] = {  # type: ignore[index]
        "status": "FAIL",
        "evidence": "They hold separate maps, so the shared-direction conflict is absent.",
    }
    issues = validate_exact_image_visual_qa(qa, [candidate], carousel_dir=tmp_path)
    assert issues == ["slide 1 semantic_action failed"]


def test_stale_pixel_hash_fails_before_subjective_checks(tmp_path: Path) -> None:
    candidate = _candidate(tmp_path)
    qa = _passing_qa(candidate)
    qa["slides"][0]["native_outputs"]["instagram_post"]["sha256"] = "sha256:stale"  # type: ignore[index]
    issues = validate_exact_image_visual_qa(qa, [candidate], carousel_dir=tmp_path)
    assert issues == ["slide 1 instagram_post QA sha256 is stale"]


def test_exact_copy_check_cannot_pass_without_observed_text(tmp_path: Path) -> None:
    candidate = _candidate(tmp_path)
    qa = _passing_qa(candidate)
    del qa["slides"][0]["checks"]["exact_text"]["observed"]  # type: ignore[index]

    assert validate_exact_image_visual_qa(
        qa,
        [candidate],
        carousel_dir=tmp_path,
    ) == ["slide 1 rendered copy is not exact"]


def test_compact_inventory_validators_keep_integrity_without_review_ceremony() -> None:
    assert validate_anatomy_inventory_check(
        {
            "slides": [
                {
                    "slide": 1,
                    "expected_arms": 4,
                    "observed_arms": 4,
                    "expected_hands": 4,
                    "observed_hands": 4,
                    "unexpected_limbs": [],
                    "duplicated_limbs": [],
                    "malformed_fingers": False,
                }
            ]
        },
        slide_count=1,
    ) == []
    assert validate_scene_entity_integrity_check(
        {"slides": [{"slide": 1, "expected_people": 2, "observed_people": 3}]},
        slide_count=1,
        ) == ["slide 1 expected 2 people but observed 3"]
    assert validate_spatial_topology_check(
        {"slides": [{"slide": 1, "status": "PASS", "evidence": "contact reads"}]},
        slide_count=1,
    ) == []
    assert validate_visual_richness_check(
        {
            "slides": [
                {
                    "slide": 1,
                    "foreground": "shared map",
                    "midground": "couple",
                    "background": "dining room",
                    "focal_action": "opposing pull",
                    "cause_effect": "paper tension shows conflict",
                    "posed_portrait": False,
                    "decorative_clutter": False,
                }
            ]
        },
        slide_count=1,
    ) == []
    assert validate_independent_reviewers({}) == []
