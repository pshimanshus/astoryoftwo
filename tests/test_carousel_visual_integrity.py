from __future__ import annotations

from copy import deepcopy

from pipeline.stages.carousel_visual_integrity import (
    SCENE_CONTRACT_SCHEMA_VERSION,
    build_pre_generation_scene_contract,
    scene_contract_prompt,
    validate_pre_generation_scene_contract,
)


def _hand_map() -> dict[str, object]:
    return {
        "people": ["Aachu", "Zuv"],
        "hands": [
            {
                "owner": "Aachu",
                "side": "right",
                "visibility": "focal_action",
                "action": "hold",
                "target": "the folded paper map's left edge",
                "contact_target": {"object": "folded paper map", "region": "left edge"},
                "attachment": "continuous right shoulder-to-arm-to-wrist-to-hand",
            },
            {
                "owner": "Zuv",
                "side": "left",
                "visibility": "focal_action",
                "action": "hold",
                "target": "the folded paper map's right edge",
                "contact_target": {"object": "folded paper map", "region": "right edge"},
                "attachment": "continuous left shoulder-to-arm-to-wrist-to-hand",
            },
        ],
        "forbidden": ["extra hand", "swapped map ownership"],
    }


def _accessories() -> list[dict[str, object]]:
    return [
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
            "occlusion_reason": "his closed collar covers the centered chain",
        },
    ]


def _contract(scene: str = "Aachu and Zuv pull one folded paper map in opposite directions.") -> dict[str, object]:
    return build_pre_generation_scene_contract(
        scene,
        hand_map=_hand_map(),
        accessories=_accessories(),
    )


def test_contract_keeps_explicit_hand_targets_and_conditional_accessories() -> None:
    contract = _contract()

    assert contract["schema_version"] == SCENE_CONTRACT_SCHEMA_VERSION
    assert validate_pre_generation_scene_contract(contract) == []
    prompt = scene_contract_prompt(contract)
    assert "visibility=focal_action; hold -> the folded paper map's left edge" in prompt
    assert "Accessory — Aachu: evil-eye bracelet; worn; visible; right wrist." in prompt
    assert "occluded because his closed collar covers the centered chain" in prompt


def test_action_critical_hand_cannot_fall_back_to_generic_action_or_target() -> None:
    contract = _contract()
    hand = contract["hand_map"]["hands"][0]  # type: ignore[index]
    hand["action"] = "Perform only this owner's action explicitly described in the scene"
    hand["target"] = "object"

    issues = validate_pre_generation_scene_contract(contract)

    assert "action-critical hand 1 uses a generic action fallback" in issues
    assert "action-critical hand 1 uses a generic target fallback" in issues


def test_action_critical_hand_requires_structured_contact_target() -> None:
    contract = _contract()
    contract["hand_map"]["hands"][0].pop("contact_target")  # type: ignore[index]

    assert "action-critical hand 1 is missing structured contact_target" in validate_pre_generation_scene_contract(contract)


def test_story_critical_device_requires_face_orientation_and_use() -> None:
    contract = _contract("Aachu and Zuv compare a phone map before crossing the road.")

    issues = validate_pre_generation_scene_contract(contract)

    assert "story-critical device plan has no device record" in issues


def test_risk_flags_cannot_disable_a_phone_or_hand_contract_in_scene_prose() -> None:
    contract = _contract("Aachu holds a phone map while Zuv points toward the road.")
    contract["risk_flags"]["story_critical_device"] = False  # type: ignore[index]
    contract["risk_flags"]["action_critical_hands"] = False  # type: ignore[index]

    issues = validate_pre_generation_scene_contract(contract)

    assert "risk_flags.story_critical_device cannot disable a scene-required contract" in issues
    assert "risk_flags.action_critical_hands cannot disable a scene-required contract" in issues


def test_rear_camera_face_can_never_carry_screen_ui() -> None:
    contract = build_pre_generation_scene_contract(
        "Aachu and Zuv compare a phone map before crossing the road.",
        hand_map=_hand_map(),
        accessories=_accessories(),
        devices=[
            {
                "object": "phone",
                "owner": "Zuv",
                "visible_face": "rear_camera",
                "orientation": "back facing Aachu",
                "use": "show the route map",
                "ui_visible": True,
                "screen_content": "map UI",
            }
        ],
    )

    issues = validate_pre_generation_scene_contract(contract)

    assert "story-critical device 1 places screen content on a rear-camera/back face" in issues
    assert "story-critical device 1 exposes UI without front_screen visible_face" in issues


def test_general_transition_requires_source_destination_and_visible_evidence() -> None:
    contract = _contract("Aachu turns back after leaving and joins Zuv at the door.")
    contract["transition"] = {"required": True}

    issues = validate_pre_generation_scene_contract(contract)

    assert "temporal transition is missing from_phase" in issues
    assert "temporal transition is missing to_phase" in issues
    assert "temporal transition is missing visible_evidence" in issues


def test_visible_standing_scale_requires_evidence_and_rejects_crouched_pose() -> None:
    scene = "Aachu and Zuv stand upright with visible legs beside the apartment doorframe."
    contract = _contract(scene)
    scale = contract["scale"]  # type: ignore[index]
    assert scale["required"] is True

    issues = validate_pre_generation_scene_contract(contract)
    assert "visible scale plan is missing aachu_height" in issues
    assert "visible scale plan is missing evidence" in issues

    valid = deepcopy(contract)
    valid["scale"] = {
        "required": True,
        "aachu_height": "5'6\"",
        "zuv_height": "5'8\"",
        "relative_height": "Zuv is only slightly taller than Aachu",
        "pose": "upright standing",
        "evidence": ["visible proportional legs and feet", "doorframe for adult scale"],
    }
    assert validate_pre_generation_scene_contract(valid) == []

    valid["scale"]["pose"] = "a crouched pose beside the doorframe"
    assert "scene contract permits a prohibited crouched or cramped pose" in validate_pre_generation_scene_contract(valid)


def test_occluded_accessory_needs_a_reason_and_visible_accessory_needs_fixed_placement() -> None:
    contract = _contract()
    contract["accessories"][0]["placement"] = "left wrist"  # type: ignore[index]
    contract["accessories"][1].pop("occlusion_reason")  # type: ignore[index]

    issues = validate_pre_generation_scene_contract(contract)

    assert "Aachu visible accessory placement is missing or incorrect" in issues
    assert "Zuv occluded accessory is missing occlusion_reason" in issues
