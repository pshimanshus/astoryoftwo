from __future__ import annotations

import hashlib
import json
from dataclasses import replace
from datetime import date
from pathlib import Path
from unittest.mock import patch

from PIL import Image

from pipeline.stages.carousel_quality import (
    QualityContext,
    structured_visual_qa_gate,
    validate_anatomy_inventory_check,
    validate_independent_reviewers,
    validate_scene_entity_integrity_check,
    validate_source_assets,
    validate_spatial_topology_check,
    validate_visual_richness_check,
)


def _write_image(path: Path, *, color: str = "ivory") -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    Image.new("RGB", (108, 144), color=color).save(path)


def _source_asset(path: Path, package_dir: Path) -> dict[str, object]:
    return {
        "path": str(path.relative_to(package_dir)),
        "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        "width": 108,
        "height": 144,
    }


def _anatomy_slide(path: Path, package_dir: Path) -> dict[str, object]:
    return {
        "slide": 1,
        "source_asset": _source_asset(path, package_dir),
        "expected_arms": 4,
        "observed_arms": 4,
        "expected_hands": 4,
        "observed_hands": 4,
        "visible_hands": [
            {
                "owner": "Aachu",
                "side": "left",
                "action": "holds the tissue",
                "story_required": True,
                "attachment_visible": True,
                "attachment_evidence": "wrist continues into her left sleeve",
                "contact_object": "tissue",
                "contact_geometry_pass": True,
                "occlusion_evidence": "fingertips overlap the near face of the tissue",
                "solid_object_intersection": False,
                "edge_entry_unexplained": False,
            },
            {
                "owner": "Aachu",
                "side": "right",
                "action": "steadies the tissue",
                "story_required": True,
                "attachment_visible": True,
                "attachment_evidence": "forearm continues into her right sleeve",
                "contact_object": "tissue",
                "contact_geometry_pass": True,
                "occlusion_evidence": "thumb sits in front of the tissue edge",
                "solid_object_intersection": False,
                "edge_entry_unexplained": False,
            },
            {
                "owner": "Zuv",
                "side": "left",
                "action": "offers his nicked thumb",
                "story_required": True,
                "attachment_visible": True,
                "attachment_evidence": "wrist continues into his rolled cuff",
                "contact_object": "tissue",
                "contact_geometry_pass": True,
                "occlusion_evidence": "nicked thumb meets the tissue without crossing its plane",
                "solid_object_intersection": False,
                "edge_entry_unexplained": False,
            },
            {
                "owner": "Zuv",
                "side": "right",
                "action": "rests beside his body",
                "story_required": True,
                "attachment_visible": True,
                "attachment_evidence": "forearm continues into his right cuff",
                "contact_object": None,
                "contact_geometry_pass": True,
                "occlusion_evidence": "open air separates the resting hand from nearby objects",
                "solid_object_intersection": False,
                "edge_entry_unexplained": False,
            },
        ],
        "unexpected_limbs": [],
        "duplicated_limbs": [],
        "malformed_fingers": False,
    }


def _richness_slide() -> dict[str, object]:
    return {
        "slide": 1,
        "foreground": "Their hands and the blood-marked tissue overlap in the foreground.",
        "midground": "Both partners hold a restrained, still-angry exchange by the lock.",
        "background": "The open landing and repair kit establish the interrupted departure.",
        "focal_action": "Aachu presses a tissue to Zuv's nicked thumb.",
        "story_details": ["snapped key near the lock", "open repair kit on the landing"],
        "cause_effect": "The broken key caused the nick, which interrupts their argument with care.",
        "posed_portrait": False,
        "decorative_clutter": False,
    }


def _topology_slide() -> dict[str, object]:
    return {
        "slide": 1,
        "observed_people": 2,
        "evidence_views": {
            "full_frame": "Both complete figures occupy distinct volumes in the doorway scene.",
            "person_object_crop": "Zuv's shirt contour stays separate from the door and frame.",
            "focal_detail": "Hands, tissue, cuffs, and nearby surfaces have clear overlap order.",
        },
        "environment_planes": [
            {
                "object": "door and doorframe",
                "depth_order": "behind Zuv and separate from his body",
                "boundary_continuous": True,
            }
        ],
        "people": [
            {
                "person": "Aachu",
                "silhouette_traceable": True,
                "ambiguous_regions": [],
                "body_regions": [
                    {
                        "region": "head neck shoulders and torso",
                        "near_object": "interior wall",
                        "expected_relation": "in_front_of",
                        "observed_relation": "in_front_of",
                        "boundary_continuous": True,
                        "occlusion_order_clear": True,
                        "solid_object_intersection": False,
                        "morph_or_merge": False,
                        "evidence": "Her hair, shoulder, sleeve, and torso remain distinct from the wall wash.",
                    }
                ],
            },
            {
                "person": "Zuv",
                "silhouette_traceable": True,
                "ambiguous_regions": [],
                "body_regions": [
                    {
                        "region": "head neck right shoulder back and torso",
                        "near_object": "door and doorframe",
                        "expected_relation": "in_front_of",
                        "observed_relation": "in_front_of",
                        "boundary_continuous": True,
                        "occlusion_order_clear": True,
                        "solid_object_intersection": False,
                        "morph_or_merge": False,
                        "evidence": "His shirt contour remains continuous from shoulder to waist in front of the door.",
                    }
                ],
            },
        ],
        "ambiguous_regions": [],
        "unresolved_intersections": [],
    }


def _valid_qa(package_dir: Path) -> dict[str, object]:
    image_path = package_dir / "quarantine" / "slide-01.png"
    _write_image(image_path)
    anatomy = _anatomy_slide(image_path, package_dir)
    return {
        "schema_version": "2.1",
        "status": "PASS",
        "proof_state": "QA_PASS_CANDIDATE",
        "reviews": {
            "anatomy_entity_spatial_identity": {
                "reviewer_id": "anatomy-reviewer",
                "pass": True,
                "evidence": "Counted and attributed every visible limb, then compared both identities.",
            },
            "storytelling_richness_text_style": {
                "reviewer_id": "story-reviewer",
                "pass": True,
                "evidence": "Checked focal action, spatial layers, story details, exact text, and style.",
            },
        },
        "checks": {
            "storyboard": {"pass": True},
            "aachu_face": {
                "pass": True,
                "reference_option_ids": ["ID01"],
                "likeness_notes": "Oval face, expressive brows, long dark hair, and eye shape match ID01.",
            },
            "zuv_face": {
                "pass": True,
                "reference_option_ids": ["ID02"],
                "likeness_notes": "Curly hair, face shape, beard line, and grounded expression match ID02.",
            },
            "dress_continuity": {"pass": True},
            "style": {"pass": True},
            "scene_logic": {"pass": True},
            "scene_entity_integrity": {
                "pass": True,
                "slides": [
                    {
                        "slide": 1,
                        "expected_people": 2,
                        "observed_people": 2,
                        "expected_arms": 4,
                        "observed_arms": 4,
                        "expected_hands": 4,
                        "observed_hands": 4,
                        "unexpected_entities": [],
                        "unexpected_limbs": [],
                        "duplicated_limbs": [],
                        "evidence": "Only Aachu and Zuv appear, with four attributable arms and hands.",
                    }
                ],
            },
            "anatomy_inventory": {"pass": True, "slides": [anatomy]},
            "spatial_topology": {"pass": True, "slides": [_topology_slide()]},
            "visual_richness": {"pass": True, "slides": [_richness_slide()]},
            "integrated_final_text": {"pass": True},
            "final_files": {"pass": True},
            "visual_story_readability": {"pass": True},
        },
    }


def _context(package_dir: Path) -> QualityContext:
    return QualityContext(
        story="story",
        title="title",
        slug="slug",
        today=date(2026, 7, 20),
        out_dir=package_dir,
        image_paths=[],
        slide_count=1,
        package={},
        manifest={},
        render_result={},
        workspace_root=package_dir,
    )


def test_schema_v2_full_evidence_passes(tmp_path: Path) -> None:
    qa = _valid_qa(tmp_path)
    (tmp_path / "visual-qa.json").write_text(json.dumps(qa), encoding="utf-8")

    with patch("pipeline.stages.carousel_quality.validate_frame_readability", return_value=[]):
        result = structured_visual_qa_gate(_context(tmp_path))

    assert result["pass"], result["failed"]


def test_structured_visual_qa_accepts_explicit_package_contained_path(
    tmp_path: Path,
) -> None:
    (tmp_path / "visual-qa.json").write_text(
        json.dumps({"schema_version": "2.1", "status": "FAIL"}),
        encoding="utf-8",
    )
    alternate = tmp_path / ".internal" / "full-deck-visual-qa.json"
    alternate.parent.mkdir(parents=True)
    alternate.write_text(json.dumps(_valid_qa(tmp_path)), encoding="utf-8")
    context = replace(_context(tmp_path), visual_qa_path=alternate)

    with patch(
        "pipeline.stages.carousel_quality.validate_frame_readability",
        return_value=[],
    ):
        result = structured_visual_qa_gate(context)

    assert result["pass"], result["failed"]
    assert result["path"] == str(alternate)


def test_structured_visual_qa_rejects_external_explicit_path(
    tmp_path: Path,
) -> None:
    package = tmp_path / "package"
    package.mkdir()
    external = tmp_path / "external-qa.json"
    external.write_text(json.dumps(_valid_qa(package)), encoding="utf-8")
    context = replace(_context(package), visual_qa_path=external)

    result = structured_visual_qa_gate(context)

    assert not result["pass"]
    assert "inside the carousel package" in " ".join(result["failed"])


def test_structured_visual_qa_rejects_traversal_and_symlink_paths(
    tmp_path: Path,
) -> None:
    package = tmp_path / "package"
    package.mkdir()
    qa = package / ".internal" / "full-deck-visual-qa.json"
    qa.parent.mkdir()
    qa.write_text(json.dumps(_valid_qa(package)), encoding="utf-8")

    traversal_result = structured_visual_qa_gate(
        replace(
            _context(package),
            visual_qa_path=Path("../outside-qa.json"),
        )
    )
    linked = package / "linked-qa.json"
    linked.symlink_to(qa)
    symlink_result = structured_visual_qa_gate(
        replace(_context(package), visual_qa_path=Path("linked-qa.json"))
    )

    assert not traversal_result["pass"]
    assert "traverse outside" in " ".join(traversal_result["failed"])
    assert not symlink_result["pass"]
    assert "symlinks" in " ".join(symlink_result["failed"])


def test_boolean_only_pose_anatomy_is_rejected(tmp_path: Path) -> None:
    qa = _valid_qa(tmp_path)
    checks = qa["checks"]
    assert isinstance(checks, dict)
    checks.pop("anatomy_inventory")
    checks["pose_anatomy"] = True
    (tmp_path / "visual-qa.json").write_text(json.dumps(qa), encoding="utf-8")

    with patch("pipeline.stages.carousel_quality.validate_frame_readability", return_value=[]):
        result = structured_visual_qa_gate(_context(tmp_path))

    assert not result["pass"]
    assert "boolean-only pose_anatomy" in " ".join(result["failed"])


def test_schema_before_2_1_visual_qa_is_rejected(tmp_path: Path) -> None:
    qa = _valid_qa(tmp_path)
    qa["schema_version"] = "2.0"
    (tmp_path / "visual-qa.json").write_text(json.dumps(qa), encoding="utf-8")

    with patch("pipeline.stages.carousel_quality.validate_frame_readability", return_value=[]):
        result = structured_visual_qa_gate(_context(tmp_path))

    assert not result["pass"]
    assert "schema_version must be at least 2.1" in " ".join(result["failed"])


def test_zuv_morphed_into_door_fails_whole_person_spatial_topology() -> None:
    record = _topology_slide()
    people = record["people"]
    assert isinstance(people, list)
    zuv = people[1]
    assert isinstance(zuv, dict)
    regions = zuv["body_regions"]
    assert isinstance(regions, list)
    region = regions[0]
    assert isinstance(region, dict)
    region.update(
        {
            "observed_relation": "touching",
            "boundary_continuous": False,
            "occlusion_order_clear": False,
            "solid_object_intersection": True,
            "morph_or_merge": True,
            "evidence": "The door plane absorbs Zuv's shoulder, back, torso, and shirt edge.",
        }
    )
    zuv["silhouette_traceable"] = False
    zuv["ambiguous_regions"] = ["right shoulder/back/torso against door"]
    record["ambiguous_regions"] = ["Zuv and door share an unresolved boundary"]
    record["unresolved_intersections"] = ["door edge enters Zuv's torso"]

    issues = validate_spatial_topology_check({"slides": [record]}, slide_count=1)

    joined = " ".join(issues).lower()
    assert "silhouette is not fully traceable" in joined
    assert "expected in_front_of but observed touching" in joined
    assert "boundary is not continuous" in joined
    assert "ambiguous occlusion order" in joined
    assert "intersects or may intersect a solid object" in joined
    assert "morphs or merges into the environment" in joined


def test_declared_single_point_shoulder_contact_passes_spatial_topology() -> None:
    record = _topology_slide()
    people = record["people"]
    assert isinstance(people, list)
    zuv = people[1]
    assert isinstance(zuv, dict)
    regions = zuv["body_regions"]
    assert isinstance(regions, list)
    region = regions[0]
    assert isinstance(region, dict)
    region.update(
        {
            "region": "right shoulder contact point",
            "expected_relation": "touching",
            "observed_relation": "touching",
            "evidence": "Only the outer shoulder touches the frame; the back and torso remain separate.",
        }
    )

    assert validate_spatial_topology_check({"slides": [record]}, slide_count=1) == []


def test_declared_partial_occlusion_passes_when_continuation_is_clear() -> None:
    record = _topology_slide()
    people = record["people"]
    assert isinstance(people, list)
    zuv = people[1]
    assert isinstance(zuv, dict)
    regions = zuv["body_regions"]
    assert isinstance(regions, list)
    region = regions[0]
    assert isinstance(region, dict)
    region.update(
        {
            "region": "left forearm behind tissue",
            "near_object": "tissue",
            "expected_relation": "occluded_by",
            "observed_relation": "occluded_by",
            "evidence": "The forearm contour continues naturally on both sides of the small tissue occlusion.",
        }
    )

    assert validate_spatial_topology_check({"slides": [record]}, slide_count=1) == []


def test_boolean_only_spatial_topology_is_rejected(tmp_path: Path) -> None:
    qa = _valid_qa(tmp_path)
    checks = qa["checks"]
    assert isinstance(checks, dict)
    checks["spatial_topology"] = True
    (tmp_path / "visual-qa.json").write_text(json.dumps(qa), encoding="utf-8")

    with patch("pipeline.stages.carousel_quality.validate_frame_readability", return_value=[]):
        result = structured_visual_qa_gate(_context(tmp_path))

    assert not result["pass"]
    assert any("spatial_topology" in issue for issue in result["failed"])


def test_unattached_extra_door_hand_is_rejected(tmp_path: Path) -> None:
    image_path = tmp_path / "quarantine" / "slide-01.png"
    _write_image(image_path)
    record = _anatomy_slide(image_path, tmp_path)
    record["observed_hands"] = 5
    visible_hands = record["visible_hands"]
    assert isinstance(visible_hands, list)
    visible_hands.append(
        {
            "owner": "",
            "side": "right",
            "action": "touches the door",
            "story_required": False,
            "attachment_visible": False,
            "attachment_evidence": "",
            "contact_object": "door",
            "contact_geometry_pass": False,
            "occlusion_evidence": "",
            "solid_object_intersection": True,
            "edge_entry_unexplained": True,
        }
    )

    issues = validate_anatomy_inventory_check({"slides": [record]}, slide_count=1)

    joined = " ".join(issues).lower()
    assert "expected 4 hands but observed 5" in joined
    assert "has no owner" in joined
    assert "not visibly attached" in joined
    assert "not required by the locked scene" in joined
    assert "fails hand-object contact geometry" in joined
    assert "unexplained edge entry" in joined


def test_forearm_penetrating_box_is_rejected_even_when_hand_count_matches(tmp_path: Path) -> None:
    image_path = tmp_path / "slide-01.png"
    _write_image(image_path)
    record = _anatomy_slide(image_path, tmp_path)
    visible_hands = record["visible_hands"]
    assert isinstance(visible_hands, list)
    hand = visible_hands[3]
    assert isinstance(hand, dict)
    hand.update(
        {
            "action": "supports the moving box",
            "contact_object": "moving box",
            "contact_geometry_pass": False,
            "occlusion_evidence": "forearm disappears through the solid upper box wall",
            "solid_object_intersection": True,
        }
    )

    issues = validate_anatomy_inventory_check({"slides": [record]}, slide_count=1)

    joined = " ".join(issues).lower()
    assert "fails hand-object contact geometry" in joined
    assert "intersects or may intersect a solid object" in joined


def test_duplicate_limb_and_malformed_fingers_are_rejected(tmp_path: Path) -> None:
    image_path = tmp_path / "slide-01.png"
    _write_image(image_path)
    record = _anatomy_slide(image_path, tmp_path)
    record["duplicated_limbs"] = ["Zuv right forearm"]
    record["malformed_fingers"] = ["Aachu left hand has six fingers"]

    issues = validate_anatomy_inventory_check({"slides": [record]}, slide_count=1)

    joined = " ".join(issues).lower()
    assert "duplicated limbs" in joined
    assert "malformed fingers" in joined


def test_scene_entity_integrity_rejects_extra_hand_even_with_two_people() -> None:
    issues = validate_scene_entity_integrity_check(
        {
            "slides": [
                {
                    "slide": 1,
                    "expected_people": 2,
                    "observed_people": 2,
                    "expected_arms": 4,
                    "observed_arms": 4,
                    "expected_hands": 4,
                    "observed_hands": 5,
                    "unexpected_entities": [],
                    "unexpected_limbs": ["unattached hand on the door"],
                    "duplicated_limbs": [],
                    "evidence": "Two people are present, but a fifth hand appears beside the door lock.",
                }
            ]
        },
        slide_count=1,
    )

    joined = " ".join(issues).lower()
    assert "expected 4 hands but observed 5" in joined
    assert "unattached hand on the door" in joined


def test_sparse_posed_portrait_fails_visual_richness() -> None:
    record = _richness_slide()
    record.update(
        {
            "foreground": "",
            "midground": "couple",
            "background": "",
            "story_details": [],
            "posed_portrait": True,
        }
    )

    issues = validate_visual_richness_check({"slides": [record]}, slide_count=1)

    joined = " ".join(issues).lower()
    assert "foreground" in joined
    assert "2-4 story_details" in joined
    assert "posed_portrait" in joined


def test_changed_image_invalidates_sha256_bound_qa(tmp_path: Path) -> None:
    image_path = tmp_path / "slide-01.png"
    _write_image(image_path)
    anatomy = {"slides": [_anatomy_slide(image_path, tmp_path)]}
    _write_image(image_path, color="navy")

    issues = validate_source_assets(anatomy, package_dir=tmp_path, slide_count=1)

    assert "SHA-256 is missing or stale" in " ".join(issues)


def test_reviews_must_be_independent_and_both_pass() -> None:
    issues = validate_independent_reviewers(
        {
            "anatomy_entity_spatial_identity": {
                "reviewer_id": "same-reviewer",
                "pass": True,
                "evidence": "Counted every limb and checked both identities against references.",
            },
            "storytelling_richness_text_style": {
                "reviewer_id": "same-reviewer",
                "pass": False,
                "evidence": "The scene is sparse and does not provide enough story evidence.",
            },
        }
    )

    joined = " ".join(issues).lower()
    assert "must pass" in joined
    assert "must be independent" in joined
