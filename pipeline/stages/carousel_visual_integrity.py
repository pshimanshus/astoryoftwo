"""Pre-generation anatomy, spatial-topology, and visual-richness contracts.

These contracts make ambiguous scene prose explicit before an image prompt is
compiled.  They do not claim that generated pixels are correct; the separate
post-generation visual QA gate must still inspect and hash-bind every image.
"""

from __future__ import annotations

from typing import Any


DEFAULT_PEOPLE = ("Aachu", "Zuv")
SOLID_OBJECT_TERMS = (
    "doorframe",
    "door",
    "wall",
    "car window",
    "car roof",
    "car",
    "roadside barrier",
    "barrier",
    "stall ledge",
    "stall",
    "stool",
    "moving box",
    "box",
    "table",
    "chair",
    "sofa",
    "bed",
    "counter",
    "floor",
    "window",
)


def infer_scene_people(scene: str) -> tuple[str, ...]:
    lower = scene.lower()
    inferred: list[str] = []
    if any(token in lower for token in ("aachu", "anchal", "the woman")):
        inferred.append("Aachu")
    if any(token in lower for token in ("zuv", "himanshu", "the man")):
        inferred.append("Zuv")
    if not inferred and any(token in lower for token in ("couple", "both", "they", "their")):
        inferred.extend(DEFAULT_PEOPLE)
    return tuple(inferred)


def build_hand_ownership_map(
    scene: str,
    *,
    people: tuple[str, ...] | None = None,
    explicit_hands: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Return a fail-closed hand inventory for one generated frame.

    When a storyboard does not provide a bespoke hand plan, only the two hands
    needed for the focal action may be visible.  Non-focal hands must be fully
    attached and relaxed or completely outside the frame; the model is never
    invited to invent another hand to satisfy secondary prose.
    """

    if people is None:
        people = infer_scene_people(scene)

    focal_slots = {
        (people[0], "right") if people else ("", ""),
        (people[1], "left") if len(people) > 1 else ("", ""),
    }
    hands = explicit_hands or [
        {
            "owner": person,
            "side": side,
            "visibility": "focal_action" if (person, side) in focal_slots else "out_of_frame",
            "action": (
                "Perform only this owner's action explicitly described in the scene"
                if (person, side) in focal_slots
                else "Stay completely outside the frame; do not enter from a wall, door, or body edge"
            ),
            "attachment": "continuous shoulder-to-upper-arm-to-elbow-to-forearm-to-wrist-to-hand",
        }
        for person in people
        for side in ("left", "right")
    ]
    return {
        "scene_action_binding": scene.strip(),
        "people": list(people),
        "expected_anatomical_hands": 2 * len(people),
        "expected_visible_hands": min(2, 2 * len(people)),
        "default_max_visible_hands": min(2, 2 * len(people)),
        "hands": hands,
        "forbidden": [
            "unowned hand",
            "hand with no narrative purpose in the locked scene",
            "hand without a visible or naturally occluded wrist/forearm connection",
            "extra or duplicated hand, arm, wrist, or fingers",
            "one hand performing two spatially incompatible actions",
            "anonymous hand entering from the door, wall, frame edge, or another body",
            "hand, wrist, or forearm penetrating a box, door, table, clothing, or other solid object",
            "load-bearing grip whose fingers, palm, wrist, or object edge do not meet believably",
        ],
    }


def hand_ownership_prompt(contract: dict[str, Any]) -> str:
    lines = [
        "HAND OWNERSHIP MAP (HARD GATE):",
        f"Scene action binding: {contract.get('scene_action_binding', '')}",
        (
            "The two people have exactly four anatomical hands total. By default show no more than "
            f"{contract.get('default_max_visible_hands', 2)} focal hands; non-focal hands must be "
            "naturally attached and relaxed or completely outside the frame."
        ),
        (
            "Every visible hand must be required by the locked scene. Trace owner -> arm -> wrist -> hand, "
            "then inspect hand -> object contact, overlap order, and load direction. Solid objects may occlude "
            "a limb, but a hand or forearm may never pass through them."
        ),
    ]
    for hand in contract.get("hands", []):
        if not isinstance(hand, dict):
            continue
        lines.append(
            "- {owner} {side} hand: visibility={visibility}; action={action}; attachment={attachment}.".format(
                owner=hand.get("owner", "UNKNOWN"),
                side=hand.get("side", "UNKNOWN"),
                visibility=hand.get("visibility", "unspecified"),
                action=hand.get("action", "unspecified"),
                attachment=hand.get("attachment", "unspecified"),
            )
        )
    forbidden = "; ".join(str(item) for item in contract.get("forbidden", []))
    lines.append(f"Reject and regenerate for: {forbidden}.")
    return "\n".join(lines)


def build_spatial_topology_contract(
    scene: str,
    *,
    people: tuple[str, ...] | None = None,
    explicit_people: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Declare whole-person depth and solid-object boundaries before generation."""

    people = infer_scene_people(scene) if people is None else people
    lower = scene.lower()
    objects = [term for term in SOLID_OBJECT_TERMS if term in lower]
    if "doorframe" in objects and "door" in objects:
        objects.remove("door")
        objects.insert(0, "door")
    near_objects = objects or ["nearest solid environmental object"]
    doorway_scene = any(term in lower for term in ("door", "doorframe", "doorway", "threshold"))
    person_records = explicit_people or [
        {
            "person": person,
            "body_regions_visible": ["head", "neck", "shoulders", "torso"],
            "environment_planes": [
                {
                    "object": item,
                    "expected_relation": "in_front_of" if doorway_scene else "separate_from",
                }
                for item in near_objects
            ],
            "allowed_contacts": [],
            "forbidden_intersections": [
                "solid-object boundary crossing the head, neck, shoulder, back, torso, or visible limb",
                "body, clothing, hair, or silhouette merging into architecture or furniture",
                "ambiguous in-front-of versus behind versus inside relationship",
            ],
            "required_visible_separation": (
                "A continuous readable contour or value boundary separates the whole person from nearby solid objects."
            ),
        }
        for person in people
    ]
    return {
        "scene_action_binding": scene.strip(),
        "people": person_records,
        "solid_objects": near_objects,
        "review_order": [
            "whole-frame person silhouette",
            "environment planes and boundaries",
            "person-object front/behind/contact relationship",
            "occlusion continuation",
            "local limb and hand anatomy",
        ],
        "forbidden": [
            "person absorbed by or morphed into a door, wall, furniture, box, floor, or other solid object",
            "doorframe, wall, furniture, or container edge running through a head, shoulder, back, torso, or limb",
            "untraceable body volume hidden behind painterly texture",
            "architecture bending, changing thickness, or replacing part of a person's silhouette",
            "unresolved depth relationship labeled as probably correct",
        ],
    }


def spatial_topology_prompt(contract: dict[str, Any]) -> str:
    lines = [
        "WHOLE-PERSON SPATIAL TOPOLOGY (HARD GATE):",
        f"Scene action binding: {contract.get('scene_action_binding', '')}",
        (
            "First construct each person as a coherent volume, then construct doors, walls, furniture, containers, "
            "floor, and other solid planes. Keep every front/behind/contact relationship explicit."
        ),
    ]
    for person in contract.get("people", []):
        if not isinstance(person, dict):
            continue
        planes = ", ".join(
            f"{item.get('object', 'object')}={item.get('expected_relation', 'separate_from')}"
            for item in person.get("environment_planes", [])
            if isinstance(item, dict)
        )
        contacts = ", ".join(str(item) for item in person.get("allowed_contacts", [])) or "none"
        lines.append(
            "- {name}: visible regions={regions}; environment relations={planes}; allowed contacts={contacts}; "
            "required separation={separation}".format(
                name=person.get("person", "UNKNOWN"),
                regions=", ".join(str(item) for item in person.get("body_regions_visible", [])),
                planes=planes or "no nearby solid plane",
                contacts=contacts,
                separation=person.get("required_visible_separation", "continuous readable silhouette"),
            )
        )
        for forbidden in person.get("forbidden_intersections", []):
            lines.append(f"  Reject: {forbidden}.")
    lines.append(
        "Inspect in this order: " + " -> ".join(str(item) for item in contract.get("review_order", [])) + "."
    )
    lines.append("Reject and regenerate for: " + "; ".join(str(item) for item in contract.get("forbidden", [])) + ".")
    return "\n".join(lines)


def build_action_topology_contract(scene: str, slide_copy: str = "") -> dict[str, Any]:
    """Lock chronology, camera side, and shared action for door/lock beats.

    A coherent person silhouette is not enough when a scene can be staged on
    the wrong side of a door or at the wrong point in the story.  The contract
    is activated only for copy that explicitly describes checking/locking and
    returning or doing the action together.
    """

    scene_text = " ".join(str(scene).strip().split())
    copy_text = " ".join(str(slide_copy).strip().split())
    scene_lower = scene_text.lower()
    copy_lower = copy_text.lower()
    requires_check = any(
        token in copy_lower for token in ("check the lock", "checked the lock", "checked it")
    )
    requires_return = any(
        token in copy_lower for token in ("went back", "came back", "returned")
    )
    requires_shared_action = any(
        token in copy_lower for token in ("with him", "with her", "together")
    )
    applies = requires_check and (requires_return or requires_shared_action)
    if not applies:
        return {
            "applies": False,
            "scene_action_binding": scene_text,
            "copy_action_binding": copy_text,
            "issues": [],
        }

    camera_side = (
        "outside"
        if any(
            token in scene_lower
            for token in ("from outside", "viewed entirely from outside", "corridor", "landing")
        )
        else "inside"
        if any(
            token in scene_lower
            for token in ("from inside", "viewed entirely from inside", "interior")
        )
        else ""
    )
    temporal_phase = (
        "before_departure"
        if any(
            token in scene_lower
            for token in ("before leaving", "before departure", "moment they left", "left for the date")
        )
        else "after_return"
        if any(
            token in scene_lower
            for token in ("back home after", "after the date", "after returning")
        )
        else ""
    )
    door_state = (
        "fully_closed"
        if any(
            token in scene_lower
            for token in ("fully closed", "closed exterior door", "door has closed")
        )
        else "open"
        if "open door" in scene_lower
        else ""
    )
    return_path_visible = any(
        token in scene_lower
        for token in (
            "came back",
            "comes back",
            "returned",
            "returns",
            "turns back",
            "turned and came back",
            "returning body direction",
        )
    )
    shared_action_visible = any(
        token in scene_lower
        for token in (
            "both participate",
            "both check",
            "check together",
            "checks with him",
            "checks with her",
            "joins him",
            "joins her",
            "tests the same closed handle",
        )
    )
    solo_action_contradiction = (
        any(token in scene_lower for token in ("herself", "himself"))
        and any(
            token in scene_lower
            for token in ("watches", "watching", "catches her", "catches him", "glances back")
        )
        and not shared_action_visible
    )

    issues: list[str] = []
    if not camera_side:
        issues.append("camera side of the door is not explicit")
    if not temporal_phase:
        issues.append("temporal phase is not explicit")
    if not door_state:
        issues.append("door state is not explicit")
    if requires_return and not return_path_visible:
        issues.append("copy says someone went back, but the return path is not visibly staged")
    if requires_shared_action and not shared_action_visible:
        issues.append("copy says the check is shared, but both people do not visibly participate")
    if solo_action_contradiction:
        issues.append("scene turns the shared check into one person acting while the other watches")

    return {
        "applies": True,
        "scene_action_binding": scene_text,
        "copy_action_binding": copy_text,
        "camera_side": camera_side,
        "temporal_phase": temporal_phase,
        "door_state": door_state,
        "return_path_visible": return_path_visible,
        "shared_action_visible": shared_action_visible,
        "forbidden": [
            "camera on an unstated or contradictory side of the door",
            "post-date arrival substituted for a before-departure callback",
            "inside-house staging substituted for an outside-corridor action",
            "one partner checks alone while the other merely watches",
            "copy says someone went back but no prior direction or return path is visible",
        ],
        "issues": issues,
    }


def action_topology_prompt(contract: dict[str, Any]) -> str:
    if contract.get("applies") is not True:
        return ""
    lines = [
        "ACTION CHRONOLOGY AND DOOR-SIDE CONTRACT (HARD GATE):",
        f"Copy action binding: {contract.get('copy_action_binding', '')}",
        f"Scene action binding: {contract.get('scene_action_binding', '')}",
        f"Camera side: {contract.get('camera_side', '')}.",
        f"Temporal phase: {contract.get('temporal_phase', '')}.",
        f"Door state: {contract.get('door_state', '')}.",
        f"Return path visibly staged: {bool(contract.get('return_path_visible'))}.",
        f"Shared checking action visibly staged: {bool(contract.get('shared_action_visible'))}.",
        (
            "The frame must show the verbs and chronology in the copy, not merely the same "
            "people and door. Preserve who moved away, who returned, which side of the closed "
            "door the camera occupies, and whether the final action is shared or solo."
        ),
        "Reject and regenerate for: "
        + "; ".join(str(item) for item in contract.get("forbidden", []))
        + ".",
    ]
    return "\n".join(lines)


def build_visual_richness_contract(scene: str) -> dict[str, Any]:
    return {
        "scene_action_binding": scene.strip(),
        "depth_layers": ["foreground", "midground", "background"],
        "focal_action": "one instantly readable relationship action that proves the copy",
        "story_detail_count": {"minimum": 2, "maximum": 4},
        "cause_effect": "show the incident, reaction, or aftermath that earns this beat",
        "posed_portrait_allowed": False,
        "decorative_clutter_allowed": False,
    }


def visual_richness_prompt(contract: dict[str, Any]) -> str:
    detail_count = contract.get("story_detail_count", {})
    return "\n".join(
        [
            "VISUAL RICHNESS CONTRACT (HARD GATE):",
            f"Scene action binding: {contract.get('scene_action_binding', '')}",
            "Build readable foreground, midground, and background layers; each layer must support the same moment.",
            f"Focal action: {contract.get('focal_action', '')}.",
            (
                "Include "
                f"{detail_count.get('minimum', 2)}-{detail_count.get('maximum', 4)} story-relevant environmental details, "
                "not random decoration."
            ),
            f"Cause and effect: {contract.get('cause_effect', '')}.",
            "Reject a sparse two-person pose beside text, an empty portrait backdrop, or decorative clutter without story evidence.",
        ]
    )
