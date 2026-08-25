from __future__ import annotations

import copy
import json
from pathlib import Path

from PIL import Image

from pipeline.stages.carousel_quality import (
    validate_anatomy_inventory_check,
    validate_scene_entity_integrity_check,
    validate_spatial_topology_check,
)
from pipeline.stages.carousel_format_contract import write_format_contract
from pipeline.stages.codex_builtin_image_generation import sha256_binding
from pipeline.stages.carousel_pixel_qa import (
    asset_binding_fingerprint,
    bind_proof_qa,
    validate_proof_qa,
)


def _candidate(tmp_path: Path) -> dict[str, object]:
    write_format_contract(tmp_path, ["instagram_post"], source="test")
    copy_text = "Some days, love did not tell us what to do."
    (tmp_path / "slides.json").write_text(
        json.dumps([{"slide": 1, "copy": copy_text}]), encoding="utf-8"
    )
    refs = [
        "refs/aachu/face.png",
        "refs/zuv/face.png",
        "refs/together/face.png",
        "refs/together/body.png",
    ]
    style_ref = "refs/style/watercolor.png"
    for ref in [*refs, style_ref]:
        reference = tmp_path / ref
        reference.parent.mkdir(parents=True, exist_ok=True)
        Image.new("RGB", (32, 32), "ivory").save(reference)
    (tmp_path / "prompt-pack.json").write_text(
        json.dumps(
            {
                "identity_reference_images": refs,
                "style_reference_images": [style_ref],
                "slides": [{"slide": 1}],
            }
        ),
        encoding="utf-8",
    )
    (tmp_path / "creative-context.json").write_text(
        json.dumps(
            {
                "identity_reference_selection": {
                    "selected_references": [
                        {"path": refs[0], "role": "Aachu identity anchor"},
                        {"path": refs[1], "role": "Zuv identity anchor"},
                        {"path": refs[2], "role": "together face/scale anchor"},
                        {"path": refs[3], "role": "together body/posture anchor"},
                    ]
                }
            }
        ),
        encoding="utf-8",
    )
    path = (
        tmp_path
        / ".internal"
        / "visual-quarantine"
        / "slide-01"
        / "attempt-01"
        / "instagram_post.png"
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    Image.new("RGB", (1080, 1440), "ivory").save(path)
    return {
        "slide": 1,
        "copy": copy_text,
        "attempt": 1,
        "native_outputs": {
            "instagram_post": {
                "path": str(path.relative_to(tmp_path)),
                "sha256": sha256_binding(path.read_bytes()),
                "width": 1080,
                "height": 1440,
            }
        },
    }


def _passing_qa(candidate: dict[str, object]) -> dict[str, object]:
    copy_text = str(candidate["copy"])
    return {
        "status": "PASS",
        "inspection": {
            "method": "codex_view_image",
            "decoded_pixels_observed": True,
        },
        "selected_slides": [1],
        "slides": [
            {
                "slide": 1,
                "reviews": {
                    "instagram_post": {
                        "checks": {
                            "physical_action": {"status": "PASS", "evidence": "Both partners pull one shared map in opposite directions."},
                            "relationship_state": {"status": "PASS", "evidence": "Their conflict is visible while their shared table keeps them connected."},
                            "entity_spatial_integrity": {"status": "PASS", "evidence": "Two complete people have natural hands attached to the same map."},
                            "identity_wardrobe_accessories": {
                                "status": "PASS",
                                "evidence": "Both faces and whole-body proportions match Aachu and Zuv.",
                                "references": {
                                    "aachu": ["refs/aachu/face.png"],
                                    "zuv": ["refs/zuv/face.png"],
                                    "together": [
                                        "refs/together/face.png",
                                        "refs/together/body.png",
                                    ],
                                },
                            },
                            "text_brandmark_style_dimensions": {
                                "status": "PASS",
                                "expected_text": copy_text,
                                "observed_text": copy_text,
                                "observed_brandmark": "@a.storyof.two",
                                "style_references": ["refs/style/watercolor.png"],
                                "evidence": "The exact sentence, brandmark, style, and native dimensions are visible.",
                            },
                        }
                    }
                },
            }
        ],
    }


def test_actual_pixel_qa_passes_when_every_check_is_bound_to_exact_pixels(tmp_path: Path) -> None:
    candidate = _candidate(tmp_path)
    qa = bind_proof_qa(tmp_path, _passing_qa(candidate), [candidate])
    assert validate_proof_qa(
        tmp_path, qa, expected_asset_bindings=[candidate]
    ) == []


def test_semantic_failure_stops_before_identity_or_style_can_mask_it(tmp_path: Path) -> None:
    candidate = _candidate(tmp_path)
    qa = _passing_qa(candidate)
    qa["status"] = "FAIL"
    qa["slides"][0]["reviews"]["instagram_post"]["checks"]["physical_action"] = {  # type: ignore[index]
        "status": "FAIL",
        "evidence": "They hold separate maps, so the shared-direction conflict is absent.",
    }
    qa = bind_proof_qa(tmp_path, qa, [candidate])
    issues = validate_proof_qa(
        tmp_path, qa, expected_asset_bindings=[candidate]
    )
    assert issues == [
        "slide 1 instagram_post: physical_action is FAIL; downstream PASS is invalid for relationship_state, entity_spatial_integrity, identity_wardrobe_accessories, text_brandmark_style_dimensions"
    ]


def test_stale_pixel_hash_fails_before_subjective_checks(tmp_path: Path) -> None:
    candidate = _candidate(tmp_path)
    qa = _passing_qa(candidate)
    stale = copy.deepcopy(candidate["native_outputs"])
    stale["instagram_post"]["sha256"] = "sha256:" + "0" * 64  # type: ignore[index]
    stale["instagram_post"]["binding_sha256"] = asset_binding_fingerprint(  # type: ignore[index]
        1, "instagram_post", stale["instagram_post"]  # type: ignore[index]
    )
    qa = bind_proof_qa(tmp_path, qa, [candidate])
    qa["slides"][0]["asset_bindings"] = stale  # type: ignore[index]
    issues = validate_proof_qa(
        tmp_path, qa, expected_asset_bindings=[candidate]
    )
    assert "slide 1 instagram_post: SHA-256 is stale" in issues
    assert "slide 1 instagram_post: proof binding is not the current candidate" in issues


def test_exact_copy_check_cannot_pass_without_observed_text(tmp_path: Path) -> None:
    candidate = _candidate(tmp_path)
    qa = _passing_qa(candidate)
    del qa["slides"][0]["reviews"]["instagram_post"]["checks"]["text_brandmark_style_dimensions"]["observed_text"]  # type: ignore[index]

    qa = bind_proof_qa(tmp_path, qa, [candidate])
    assert validate_proof_qa(
        tmp_path, qa, expected_asset_bindings=[candidate]
    ) == ["slide 1 instagram_post: rendered text is not exact"]


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
