"""Bridge locked scene plans into the hash-bound pixel-QA contract.

The prompt-facing plan and the review-facing contract deliberately use different
shapes.  The former directs the image model; the latter gives a reviewer a
small, exact list of observations to make against current decoded pixels.  This
module is the only bridge between the two so a reviewer cannot quietly select a
looser plan after generation.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

from pipeline.stages.carousel_visual_integrity import (
    validate_pre_generation_scene_contract,
)


PIXEL_QA_SCENE_CONTRACT_SCHEMA_VERSION = "carousel-pixel-qa-scene-contract/v1"


def _text(value: Any) -> str:
    return " ".join(str(value or "").strip().split())


def _record_id(prefix: str, index: int, record: Mapping[str, Any]) -> str:
    supplied = _text(record.get("id"))
    if supplied:
        return supplied
    owner = _text(record.get("owner")) or _text(record.get("subject"))
    side = _text(record.get("side"))
    suffix = "-".join(part.casefold().replace(" ", "-") for part in (owner, side) if part)
    return f"{prefix}-{suffix or index}"


def _required_contact_target(hand: Mapping[str, Any], *, index: int) -> dict[str, str]:
    raw = hand.get("contact_target")
    if not isinstance(raw, Mapping):
        raise ValueError(
            f"action-critical hand {index} needs contact_target with object and region; "
            "do not infer contact geometry from prose"
        )
    object_name = _text(raw.get("object"))
    region = _text(raw.get("region"))
    if not object_name or not region:
        raise ValueError(
            f"action-critical hand {index} contact_target needs non-empty object and region"
        )
    return {"object": object_name, "region": region}


def pixel_qa_scene_contract_from_pre_generation(
    contract: Mapping[str, Any],
    *,
    relationship_state: str = "",
) -> dict[str, list[dict[str, Any]]]:
    """Transform one valid locked plan into exact review observations.

    The output intentionally contains only declared facts.  It never guesses an
    action target, a screen face, an accessory location, or a body-support fact.
    """

    issues = validate_pre_generation_scene_contract(contract)
    if issues:
        raise ValueError("Pre-generation scene contract is unresolved: " + "; ".join(issues))

    transition = contract.get("transition")
    transition = transition if isinstance(transition, Mapping) else {}
    scene_action = _text(contract.get("scene_action_binding"))
    people = [_text(person) for person in contract.get("people", []) if _text(person)]
    state = _text(transition.get("to_phase")) if transition.get("required") else ""
    continuity = [
        {
            "id": "locked-scene",
            "planned_state": state or _text(relationship_state) or scene_action,
            "planned_job": (
                _text(transition.get("focal_moment"))
                if transition.get("required")
                else "prove the locked physical action"
            ),
            "planned_owner": " and ".join(people) or "declared scene subjects",
        }
    ]
    action_topology = contract.get("action_topology")
    if isinstance(action_topology, Mapping) and action_topology.get("applies"):
        continuity.append(
            {
                "id": "action-chronology",
                "planned_state": _text(action_topology.get("temporal_phase")),
                "planned_job": (
                    "door state "
                    + _text(action_topology.get("door_state"))
                    + "; return path "
                    + str(bool(action_topology.get("return_path_visible"))).lower()
                    + "; shared action "
                    + str(bool(action_topology.get("shared_action_visible"))).lower()
                ),
                "planned_owner": " and ".join(people) or "declared scene subjects",
            }
        )

    device_contract = contract.get("device_contract")
    device_contract = device_contract if isinstance(device_contract, Mapping) else {}
    objects: list[dict[str, Any]] = []
    for index, device in enumerate(device_contract.get("devices", []), start=1):
        if not isinstance(device, Mapping):
            continue
        object_name = _text(device.get("object"))
        owner = _text(device.get("owner"))
        visible_face = _text(device.get("visible_face"))
        orientation = _text(device.get("orientation"))
        use = _text(device.get("use"))
        if not all((object_name, owner, visible_face, orientation, use)):
            raise ValueError(f"story-critical device {index} cannot be transformed for pixel QA")
        planned_use = {"owner": owner, "use": use}
        screen_content = _text(device.get("screen_content"))
        if screen_content:
            planned_use["screen_content"] = screen_content
        objects.append(
            {
                "id": _record_id("device", index, device),
                "object": object_name,
                "planned_orientation": {
                    "visible_face": visible_face,
                    "orientation": orientation,
                },
                "planned_use": planned_use,
            }
        )

    spatial = contract.get("spatial_topology")
    if isinstance(spatial, Mapping):
        for person in spatial.get("people", []):
            if not isinstance(person, Mapping):
                continue
            subject = _text(person.get("person"))
            for plane in person.get("environment_planes", []):
                if not isinstance(plane, Mapping):
                    continue
                object_name = _text(plane.get("object"))
                relation = _text(plane.get("expected_relation"))
                if not subject or not object_name or not relation or object_name == "nearest solid environmental object":
                    continue
                objects.append(
                    {
                        "id": f"spatial-{subject.casefold()}-{object_name.casefold().replace(' ', '-')}",
                        "object": object_name,
                        "planned_orientation": {"subject": subject, "relation": relation},
                        "planned_use": {"boundary": object_name, "subject": subject, "relation": relation},
                    }
                )

    hand_map = contract.get("hand_map")
    hand_map = hand_map if isinstance(hand_map, Mapping) else {}
    hands: list[dict[str, Any]] = []
    for index, hand in enumerate(hand_map.get("hands", []), start=1):
        if not isinstance(hand, Mapping):
            continue
        if _text(hand.get("visibility")) not in {"focal_action", "visible_action"}:
            continue
        owner = _text(hand.get("owner"))
        side = _text(hand.get("side"))
        action = _text(hand.get("action"))
        if not all((owner, side, action)):
            raise ValueError(f"action-critical hand {index} cannot be transformed for pixel QA")
        hands.append(
            {
                "id": _record_id("hand", index, hand),
                "owner": owner,
                "side": side,
                "planned_action": action,
                "planned_contact_target": _required_contact_target(hand, index=index),
            }
        )

    scale_plan = contract.get("scale")
    scale_plan = scale_plan if isinstance(scale_plan, Mapping) else {}
    scale: list[dict[str, Any]] = []
    if scale_plan.get("required"):
        aachu = _text(scale_plan.get("aachu_height"))
        zuv = _text(scale_plan.get("zuv_height"))
        relative = _text(scale_plan.get("relative_height"))
        pose = _text(scale_plan.get("pose"))
        evidence = "; ".join(_text(item) for item in scale_plan.get("evidence", []) if _text(item))
        if not all((aachu, zuv, relative, pose, evidence)):
            raise ValueError("visible scale plan cannot be transformed for pixel QA")
        scale.append(
            {
                "id": "couple-scale",
                "subject": "Aachu and Zuv",
                "planned_scale": f"Aachu {aachu}; Zuv {zuv}; {relative}; pose {pose}",
                "planned_support": evidence,
            }
        )

    accessories: list[dict[str, Any]] = []
    for index, accessory in enumerate(contract.get("accessories", []), start=1):
        if not isinstance(accessory, Mapping):
            continue
        owner = _text(accessory.get("owner"))
        item = _text(accessory.get("item"))
        visibility = _text(accessory.get("visibility"))
        if not all((owner, item, visibility)):
            raise ValueError(f"accessory {index} cannot be transformed for pixel QA")
        location = _text(accessory.get("placement"))
        if visibility == "occluded":
            location = _text(accessory.get("occlusion_reason"))
        if not location:
            raise ValueError(f"accessory {index} cannot be transformed for pixel QA")
        record: dict[str, Any] = {
            "id": _record_id("accessory", index, accessory),
            "subject": owner,
            "item": item,
            "side": "right" if "right" in location.casefold() else "center",
            "planned_visibility": "hidden" if visibility == "occluded" else visibility,
            "planned_location": location,
        }
        if visibility == "occluded":
            record["planned_occlusion_reason"] = location
        accessories.append(record)

    return {
        "continuity": continuity,
        "object_integrity": objects,
        "action_critical_hands": hands,
        "scale": scale,
        "accessory_visibility": accessories,
    }


def expected_pixel_qa_contracts(slides: Sequence[Mapping[str, Any]]) -> dict[int, dict[str, list[dict[str, Any]]] | None] | None:
    """Return all transformed contracts or ``None`` for an all-legacy package.

    A partially adopted deck is blocked: it is unsafe for reviewers to compare
    only the slides that happened to receive a planning contract.
    """

    present = ["scene_contract" in slide and slide.get("scene_contract") is not None for slide in slides]
    if not any(present):
        return None
    if not all(present):
        raise ValueError("scene contracts must be supplied for every slide or for none of the deck")
    transformed: dict[int, dict[str, list[dict[str, Any]]] | None] = {}
    for position, slide in enumerate(slides, start=1):
        number = int(slide.get("slide", position) or position)
        raw = slide.get("scene_contract")
        if not isinstance(raw, Mapping):
            raise ValueError(f"slide {number} scene_contract must be an object")
        expected_scene = _text(
            slide.get("physical_action") or slide.get("visual") or slide.get("scene")
        )
        if expected_scene and _text(raw.get("scene_action_binding")) != expected_scene:
            raise ValueError(
                f"slide {number} scene_contract scene_action_binding does not match the locked scene"
            )
        expected_copy = _text(slide.get("copy"))
        if expected_copy and _text(raw.get("copy_action_binding")) != expected_copy:
            raise ValueError(
                f"slide {number} scene_contract copy_action_binding does not match the locked copy"
            )
        transformed[number] = pixel_qa_scene_contract_from_pre_generation(
            raw,
            relationship_state=_text(slide.get("relationship_state")),
        )
    return transformed


def select_independent_review_roles(
    contract: Mapping[str, Any],
    *,
    deck_review: bool = False,
    final_candidate: bool = False,
) -> list[str]:
    """Choose the narrow set of independent review roles required by risk."""

    roles = ["blind_scene_reader"]
    risk = contract.get("risk_flags")
    risk = risk if isinstance(risk, Mapping) else {}
    if risk.get("story_critical_device"):
        roles.append("object_geometry_reviewer")
    if risk.get("action_critical_hands"):
        roles.append("anatomy_contact_reviewer")
    spatial = contract.get("spatial_topology")
    if isinstance(spatial, Mapping) and spatial.get("solid_objects"):
        roles.append("spatial_topology_reviewer")
    if deck_review:
        roles.append("continuity_reviewer")
    if final_candidate:
        roles.append("finish_text_format_reviewer")
    roles.append("binding_registrar")
    return roles


__all__ = [
    "PIXEL_QA_SCENE_CONTRACT_SCHEMA_VERSION",
    "expected_pixel_qa_contracts",
    "pixel_qa_scene_contract_from_pre_generation",
    "select_independent_review_roles",
]
