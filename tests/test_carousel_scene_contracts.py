from __future__ import annotations

from copy import deepcopy

import pytest

from pipeline.stages.carousel_prompt_compiler import compile_image_prompt
from pipeline.stages.carousel_scene_contracts import (
    expected_pixel_qa_contracts,
    pixel_qa_scene_contract_from_pre_generation,
    select_independent_review_roles,
)
from pipeline.stages.carousel_visual_integrity import build_pre_generation_scene_contract


def _locked_contract() -> dict[str, object]:
    scene = (
        "Aachu and Zuv stand upright at the apartment doorframe while Aachu holds "
        "a phone with the route map facing Zuv."
    )
    return build_pre_generation_scene_contract(
        scene,
        "We checked the route together.",
        hand_map={
            "people": ["Aachu", "Zuv"],
            "hands": [
                {
                    "owner": "Aachu",
                    "side": "right",
                    "visibility": "focal_action",
                    "action": "hold the phone steady for Zuv",
                    "target": "the phone's right edge",
                    "contact_target": {"object": "phone", "region": "right edge"},
                    "attachment": "continuous right shoulder-to-elbow-to-wrist-to-hand",
                }
            ],
        },
        devices=[
            {
                "object": "phone",
                "owner": "Aachu",
                "visible_face": "front_screen",
                "orientation": "portrait screen facing Zuv",
                "use": "show the route together",
                "ui_visible": True,
                "screen_content": "a route map",
            }
        ],
        scale={
            "aachu_height": "5 ft 6 in",
            "zuv_height": "5 ft 8 in",
            "relative_height": "Zuv is only slightly taller than Aachu",
            "pose": "upright standing",
            "evidence": ["both pairs of feet meet the floor", "the doorframe establishes adult scale"],
        },
        accessories=[
            {
                "owner": "Aachu",
                "item": "evil-eye bracelet",
                "worn": True,
                "visibility": "visible",
                "placement": "right wrist",
            },
            {
                "owner": "Zuv",
                "item": "small round evil-eye locket on a slim silver chain",
                "worn": True,
                "visibility": "occluded",
                "occlusion_reason": "his closed collar covers the chain",
            },
        ],
    )


def test_locked_plan_transforms_to_exact_pixel_observations_and_review_roles() -> None:
    contract = _locked_contract()

    transformed = pixel_qa_scene_contract_from_pre_generation(
        contract,
        relationship_state="shared practical care",
    )

    assert transformed["continuity"] == [
        {
            "id": "locked-scene",
            "planned_state": "shared practical care",
            "planned_job": "prove the locked physical action",
            "planned_owner": "Aachu and Zuv",
        }
    ]
    assert transformed["object_integrity"][0]["planned_orientation"] == {
        "visible_face": "front_screen",
        "orientation": "portrait screen facing Zuv",
    }
    assert {
        record["id"] for record in transformed["object_integrity"]
    } == {
        "device-aachu",
        "spatial-aachu-door",
        "spatial-aachu-doorframe",
        "spatial-zuv-door",
        "spatial-zuv-doorframe",
    }
    assert transformed["action_critical_hands"][0]["planned_contact_target"] == {
        "object": "phone",
        "region": "right edge",
    }
    assert transformed["accessory_visibility"][1]["planned_visibility"] == "hidden"
    assert select_independent_review_roles(contract, deck_review=True, final_candidate=True) == [
        "blind_scene_reader",
        "object_geometry_reviewer",
        "anatomy_contact_reviewer",
        "spatial_topology_reviewer",
        "continuity_reviewer",
        "finish_text_format_reviewer",
        "binding_registrar",
    ]


def test_adapter_refuses_to_guess_missing_contact_geometry() -> None:
    contract = _locked_contract()
    hand = contract["hand_map"]["hands"][0]  # type: ignore[index]
    hand.pop("contact_target")

    with pytest.raises(ValueError, match="contact_target"):
        pixel_qa_scene_contract_from_pre_generation(contract)


def test_deck_cannot_mix_contract_and_legacy_review_modes() -> None:
    contract = _locked_contract()

    with pytest.raises(ValueError, match="every slide or for none"):
        expected_pixel_qa_contracts(
            [
                {"slide": 1, "scene_contract": contract},
                {"slide": 2, "physical_action": "Legacy scene"},
            ]
        )

    transformed = expected_pixel_qa_contracts(
        [
            {"slide": 1, "scene_contract": contract},
            {"slide": 2, "scene_contract": deepcopy(contract)},
        ]
    )
    assert transformed is not None
    assert set(transformed) == {1, 2}


def test_contract_cannot_be_reused_after_locked_copy_or_scene_changes() -> None:
    contract = _locked_contract()
    stale = deepcopy(contract)
    stale["copy_action_binding"] = "A different relationship moment."

    with pytest.raises(ValueError, match="copy_action_binding does not match"):
        compile_image_prompt(
            slide_number=1,
            slide_count=1,
            slide_copy="We checked the route together.",
            visual=str(contract["scene_action_binding"]),
            format_key="instagram_post",
            style="warm ivory watercolor",
            negative="no extra limbs",
            scene_contract=stale,
        )

    with pytest.raises(ValueError, match="locked scene"):
        expected_pixel_qa_contracts(
            [
                {
                    "slide": 1,
                    "copy": "We checked the route together.",
                    "physical_action": "A different action at the same door.",
                    "scene_contract": contract,
                }
            ]
        )
