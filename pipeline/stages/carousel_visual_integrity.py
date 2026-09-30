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


SCENE_CONTRACT_SCHEMA_VERSION = "carousel-pre-generation-scene-contract/v1"
DEVICE_TERMS = (
    "phone",
    "mobile",
    "smartphone",
    "tablet",
    "laptop",
    "camera",
    "device screen",
)
ACTION_CRITICAL_HAND_TERMS = (
    "hold",
    "holds",
    "holding",
    "hand",
    "hands",
    "point",
    "points",
    "pointing",
    "pull",
    "pulls",
    "pulling",
    "push",
    "pushes",
    "pushing",
    "pass",
    "passes",
    "passing",
    "give",
    "gives",
    "giving",
    "take",
    "takes",
    "taking",
    "open",
    "opens",
    "opening",
    "close",
    "closes",
    "closing",
    "lock",
    "locks",
    "locking",
    "check",
    "checks",
    "checking",
    "type",
    "types",
    "typing",
    "tap",
    "taps",
    "tapping",
    "touch",
    "touches",
    "touching",
    "reach",
    "reaches",
    "reaching",
    "grip",
    "grips",
    "gripping",
)
TRANSITION_TERMS = (
    "before ",
    "after ",
    "then ",
    "return",
    "returned",
    "returning",
    "went back",
    "comes back",
    "came back",
    "leaves",
    "left for",
    "leaving",
    "arrives",
    "arrived",
    "arrival",
    "departure",
    "moves from",
    "turns back",
)
GENERIC_HAND_ACTION_TERMS = (
    "perform only this owner's action explicitly described in the scene",
    "scene action",
    "focal action",
    "as described",
    "appropriate action",
    "natural action",
    "unspecified",
)
ACCESSORY_REQUIREMENTS = {
    "Aachu": {
        "item": "evil-eye bracelet",
        "body_region": "right wrist or forearm",
        "placement": "right wrist",
    },
    "Zuv": {
        "item": "small round evil-eye locket on a slim silver chain",
        "body_region": "neck, open collar, or upper chest",
        "placement": "centered at the neck on a slim silver chain",
    },
}


def _normalized_text(value: Any) -> str:
    return " ".join(str(value or "").strip().split())


def _contains_any(text: str, terms: tuple[str, ...]) -> bool:
    lowered = text.casefold()
    return any(term.casefold() in lowered for term in terms)


def _requires_device_contract(scene: str) -> bool:
    return _contains_any(scene, DEVICE_TERMS)


def _requires_action_hand_contract(scene: str) -> bool:
    return _contains_any(scene, ACTION_CRITICAL_HAND_TERMS)


def _requires_transition_contract(scene: str) -> bool:
    return _contains_any(scene, TRANSITION_TERMS)


def _requires_scale_contract(scene: str, people: tuple[str, ...]) -> bool:
    if len(people) < 2:
        return False
    return _contains_any(
        scene,
        (
            "stand",
            "standing",
            "upright",
            "full body",
            "full-body",
            "visible legs",
            "visible feet",
            "doorframe",
            "doorway",
            "hallway",
        ),
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

    action_critical = _requires_action_hand_contract(scene)
    focal_slots = {
        (people[0], "right") if people else ("", ""),
        (people[1], "left") if len(people) > 1 else ("", ""),
    }
    hands = explicit_hands or ([] if action_critical else [
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
    ])
    return {
        "scene_action_binding": scene.strip(),
        "people": list(people),
        "action_critical": action_critical,
        "expected_anatomical_hands": 2 * len(people),
        "expected_visible_hands": len(
            [hand for hand in hands if hand.get("visibility") not in {"out_of_frame", "naturally_occluded"}]
        ),
        "default_max_visible_hands": len(
            [hand for hand in hands if hand.get("visibility") not in {"out_of_frame", "naturally_occluded"}]
        ),
        "hands": hands,
        "issues": (
            [
                "action-critical scene requires an explicit hand plan with owner, side, action, and target for each focal hand"
            ]
            if action_critical and not explicit_hands
            else []
        ),
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
            "- {owner} {side} hand: visibility={visibility}; action={action}; target={target}; attachment={attachment}.".format(
                owner=hand.get("owner", "UNKNOWN"),
                side=hand.get("side", "UNKNOWN"),
                visibility=hand.get("visibility", "unspecified"),
                action=hand.get("action", "unspecified"),
                target=hand.get("target", "unspecified"),
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


def build_device_contract(
    scene: str,
    *,
    devices: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Declare every story-critical device's physical face, orientation, and use.

    A phone is not a generic prop when its display, holder, or direction proves
    the beat.  In particular, a device may never show UI on its rear-camera or
    back face.  This is a scene-planning constraint, not a model preference.
    """

    normalized_devices = [item for item in devices or [] if isinstance(item, dict)]
    required = _requires_device_contract(scene)
    return {
        "required": required,
        "devices": normalized_devices,
        "required_fields": ["object", "owner", "visible_face", "orientation", "use"],
        "forbidden": [
            "screen UI, map, text, or app controls on a rear-camera or back face",
            "a device with an unstated visible face, orientation, or narrative use",
            "a story-critical device transferred to an unplanned owner",
        ],
    }


def build_scene_transition_contract(
    scene: str,
    slide_copy: str = "",
    *,
    transition: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Represent any story transition, rather than only door-lock chronology."""

    scene_text = _normalized_text(scene)
    copy_text = _normalized_text(slide_copy)
    required = _requires_transition_contract(f"{scene_text} {copy_text}")
    return {
        "required": required,
        "from_phase": _normalized_text((transition or {}).get("from_phase")),
        "to_phase": _normalized_text((transition or {}).get("to_phase")),
        "from_location": _normalized_text((transition or {}).get("from_location")),
        "to_location": _normalized_text((transition or {}).get("to_location")),
        "transition": _normalized_text((transition or {}).get("transition")),
        "visible_evidence": [
            _normalized_text(item)
            for item in (transition or {}).get("visible_evidence", [])
            if _normalized_text(item)
        ],
        "focal_moment": _normalized_text((transition or {}).get("focal_moment")),
        "forbidden": [
            "a later or earlier scene phase substituted for the planned moment",
            "a claimed return, arrival, departure, or change with no visible trace",
            "a transition that reverses the planned person, object, or direction of travel",
        ],
    }


def build_scale_accessory_contract(
    scene: str,
    *,
    people: tuple[str, ...] | None = None,
    scale: dict[str, Any] | None = None,
    accessories: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Record conditional scale evidence and the visibility state of worn anchors."""

    people = infer_scene_people(scene) if people is None else people
    scale = scale or {}
    records = [item for item in accessories or [] if isinstance(item, dict)]
    required_people = [person for person in people if person in ACCESSORY_REQUIREMENTS]
    return {
        "scale": {
            "required": _requires_scale_contract(scene, people),
            "aachu_height": _normalized_text(scale.get("aachu_height")),
            "zuv_height": _normalized_text(scale.get("zuv_height")),
            "relative_height": _normalized_text(scale.get("relative_height")),
            "pose": _normalized_text(scale.get("pose")),
            "evidence": [
                _normalized_text(item)
                for item in scale.get("evidence", [])
                if _normalized_text(item)
            ],
        },
        "accessories": records,
        "required_accessory_owners": required_people,
        "forbidden": [
            "a crouched, cramped, squatting, or folded pose used to conceal scale",
            "Aachu's bracelet moved from her right wrist or omitted when that wrist/forearm is visible",
            "Zuv's locket omitted or moved when his neck, open collar, or upper chest is visible",
            "an accessory silently treated as optional because it is outside the crop",
        ],
    }


def build_pre_generation_scene_contract(
    scene: str,
    slide_copy: str = "",
    *,
    people: tuple[str, ...] | None = None,
    hand_map: dict[str, Any] | None = None,
    devices: list[dict[str, Any]] | None = None,
    transition: dict[str, Any] | None = None,
    scale: dict[str, Any] | None = None,
    accessories: list[dict[str, Any]] | None = None,
    action_topology: dict[str, Any] | None = None,
    spatial_topology: dict[str, Any] | None = None,
    visual_richness: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Build the compact plan that must accompany a high-risk generation call.

    The caller may supply only the parts that their scene needs, but no required
    detail is invented from prose.  ``validate_pre_generation_scene_contract``
    is the fail-closed companion used immediately before compilation.
    """

    people = infer_scene_people(scene) if people is None else people
    effective_hands = hand_map or build_hand_ownership_map(scene, people=people)
    device_contract = build_device_contract(scene, devices=devices)
    transition_contract = build_scene_transition_contract(
        scene,
        slide_copy,
        transition=transition,
    )
    scale_accessory = build_scale_accessory_contract(
        scene,
        people=people,
        scale=scale,
        accessories=accessories,
    )
    return {
        "schema_version": SCENE_CONTRACT_SCHEMA_VERSION,
        "scene_action_binding": _normalized_text(scene),
        "copy_action_binding": _normalized_text(slide_copy),
        "people": list(people),
        "risk_flags": {
            "story_critical_device": device_contract["required"],
            "action_critical_hands": _requires_action_hand_contract(scene),
            "temporal_transition": transition_contract["required"],
            "visible_scale": scale_accessory["scale"]["required"],
            "accessory_visibility": bool(scale_accessory["required_accessory_owners"]),
        },
        "hand_map": effective_hands,
        "device_contract": device_contract,
        "transition": transition_contract,
        "scale": scale_accessory["scale"],
        "accessories": scale_accessory["accessories"],
        "required_accessory_owners": scale_accessory["required_accessory_owners"],
        "action_topology": action_topology or build_action_topology_contract(scene, slide_copy),
        "spatial_topology": spatial_topology or build_spatial_topology_contract(scene, people=people),
        "visual_richness": visual_richness or build_visual_richness_contract(scene),
        "forbidden": [
            *device_contract["forbidden"],
            *transition_contract["forbidden"],
            *scale_accessory["forbidden"],
        ],
    }


def _is_generic_hand_action(action: str) -> bool:
    normalized = action.casefold()
    return not normalized or any(term in normalized for term in GENERIC_HAND_ACTION_TERMS)


def validate_pre_generation_scene_contract(contract: Any) -> list[str]:
    """Return every blocking omission or contradiction in a scene plan."""

    if not isinstance(contract, dict):
        return ["pre-generation scene contract must be an object"]

    issues: list[str] = []
    if contract.get("schema_version") != SCENE_CONTRACT_SCHEMA_VERSION:
        issues.append(
            "pre-generation scene contract schema_version is missing or unsupported"
        )
    scene_binding = _normalized_text(contract.get("scene_action_binding"))
    if not scene_binding:
        issues.append("pre-generation scene contract is missing scene_action_binding")

    risk_flags = contract.get("risk_flags")
    if not isinstance(risk_flags, dict):
        issues.append("pre-generation scene contract is missing risk_flags")
        risk_flags = {}

    people = tuple(
        _normalized_text(item)
        for item in contract.get("people", [])
        if _normalized_text(item)
    )
    inferred_people = infer_scene_people(scene_binding)
    for person in inferred_people:
        if person not in people:
            issues.append(f"pre-generation scene contract is missing planned person {person}")

    expected_risks = {
        "story_critical_device": _requires_device_contract(scene_binding),
        "action_critical_hands": _requires_action_hand_contract(scene_binding),
        "temporal_transition": _requires_transition_contract(
            f"{scene_binding} {_normalized_text(contract.get('copy_action_binding'))}"
        ),
        "visible_scale": _requires_scale_contract(scene_binding, inferred_people),
        "accessory_visibility": bool(
            [person for person in inferred_people if person in ACCESSORY_REQUIREMENTS]
        ),
    }
    for risk_name, required in expected_risks.items():
        if required and risk_flags.get(risk_name) is not True:
            issues.append(f"risk_flags.{risk_name} cannot disable a scene-required contract")

    hand_map = contract.get("hand_map")
    if not isinstance(hand_map, dict):
        issues.append("pre-generation scene contract is missing hand_map")
        hand_map = {}
    hand_issues = hand_map.get("issues")
    if isinstance(hand_issues, list):
        issues.extend(_normalized_text(item) for item in hand_issues if _normalized_text(item))
    if expected_risks["action_critical_hands"] or risk_flags.get("action_critical_hands"):
        focal_hands = [
            item
            for item in hand_map.get("hands", [])
            if isinstance(item, dict)
            and str(item.get("visibility") or "").strip()
            in {"focal_action", "visible_action"}
        ]
        if not focal_hands:
            issues.append("action-critical hand plan has no focal hand records")
        for index, hand in enumerate(focal_hands, start=1):
            for field in ("owner", "side", "action", "target", "attachment"):
                if not _normalized_text(hand.get(field)):
                    issues.append(
                        f"action-critical hand {index} is missing explicit {field}"
                    )
            action = _normalized_text(hand.get("action"))
            if _is_generic_hand_action(action):
                issues.append(
                    f"action-critical hand {index} uses a generic action fallback"
                )
            target = _normalized_text(hand.get("target"))
            if target.casefold() in {"scene", "object", "someone", "something", "unspecified"}:
                issues.append(
                    f"action-critical hand {index} uses a generic target fallback"
                )
            contact_target = hand.get("contact_target")
            if not isinstance(contact_target, dict):
                issues.append(
                    f"action-critical hand {index} is missing structured contact_target"
                )
            else:
                for field in ("object", "region"):
                    if not _normalized_text(contact_target.get(field)):
                        issues.append(
                            f"action-critical hand {index} contact_target is missing {field}"
                        )

    device_contract = contract.get("device_contract")
    if not isinstance(device_contract, dict):
        issues.append("pre-generation scene contract is missing device_contract")
        device_contract = {}
    if expected_risks["story_critical_device"] or risk_flags.get("story_critical_device"):
        devices = [item for item in device_contract.get("devices", []) if isinstance(item, dict)]
        if not devices:
            issues.append("story-critical device plan has no device record")
        for index, device in enumerate(devices, start=1):
            for field in ("object", "owner", "visible_face", "orientation", "use"):
                if not _normalized_text(device.get(field)):
                    issues.append(f"story-critical device {index} is missing {field}")
            face = _normalized_text(device.get("visible_face")).casefold()
            screen_content = _normalized_text(device.get("screen_content"))
            ui_visible = device.get("ui_visible")
            if face in {"rear_camera", "rear camera", "back", "back_face", "rear"} and (
                ui_visible is True or screen_content
            ):
                issues.append(
                    f"story-critical device {index} places screen content on a rear-camera/back face"
                )
            if ui_visible is True and face != "front_screen":
                issues.append(
                    f"story-critical device {index} exposes UI without front_screen visible_face"
                )

    transition = contract.get("transition")
    if not isinstance(transition, dict):
        issues.append("pre-generation scene contract is missing transition")
        transition = {}
    if expected_risks["temporal_transition"] or risk_flags.get("temporal_transition"):
        for field in ("from_phase", "to_phase", "transition", "focal_moment"):
            if not _normalized_text(transition.get(field)):
                issues.append(f"temporal transition is missing {field}")
        if not any(_normalized_text(item) for item in transition.get("visible_evidence", [])):
            issues.append("temporal transition is missing visible_evidence")

    action_topology = contract.get("action_topology")
    if isinstance(action_topology, dict):
        issues.extend(
            "action chronology/topology: " + _normalized_text(item)
            for item in action_topology.get("issues", [])
            if _normalized_text(item)
        )

    scale = contract.get("scale")
    if not isinstance(scale, dict):
        issues.append("pre-generation scene contract is missing scale")
        scale = {}
    if expected_risks["visible_scale"] or risk_flags.get("visible_scale"):
        for field in ("aachu_height", "zuv_height", "relative_height", "pose"):
            if not _normalized_text(scale.get(field)):
                issues.append(f"visible scale plan is missing {field}")
        if not any(_normalized_text(item) for item in scale.get("evidence", [])):
            issues.append("visible scale plan is missing evidence")
    pose_text = " ".join(
        [_normalized_text(contract.get("scene_action_binding")), _normalized_text(scale.get("pose"))]
    ).casefold()
    if any(term in pose_text for term in ("crouch", "squat", "cramped", "folded pose")):
        issues.append("scene contract permits a prohibited crouched or cramped pose")

    required_accessory_owners = contract.get("required_accessory_owners")
    if not isinstance(required_accessory_owners, list):
        issues.append("pre-generation scene contract is missing required_accessory_owners")
        required_accessory_owners = []
    records = [item for item in contract.get("accessories", []) if isinstance(item, dict)]
    by_owner = {str(item.get("owner") or "").strip(): item for item in records}
    if expected_risks["accessory_visibility"] or risk_flags.get("accessory_visibility"):
        for owner in required_accessory_owners:
            owner_text = _normalized_text(owner)
            requirement = ACCESSORY_REQUIREMENTS.get(owner_text)
            record = by_owner.get(owner_text)
            if requirement is None:
                continue
            if record is None:
                issues.append(f"missing accessory visibility record for {owner_text}")
                continue
            if _normalized_text(record.get("item")).casefold() != requirement["item"].casefold():
                issues.append(f"{owner_text} accessory item does not match the identity anchor")
            if _normalized_text(record.get("worn")).casefold() not in {"true", "yes", "worn"} and record.get("worn") is not True:
                issues.append(f"{owner_text} accessory record must state that it is worn")
            visibility = _normalized_text(record.get("visibility")).casefold()
            if visibility not in {"visible", "occluded"}:
                issues.append(f"{owner_text} accessory visibility must be visible or occluded")
                continue
            if visibility == "visible" and _normalized_text(record.get("placement")).casefold() != requirement["placement"].casefold():
                issues.append(f"{owner_text} visible accessory placement is missing or incorrect")
            if visibility == "occluded" and not _normalized_text(record.get("occlusion_reason")):
                issues.append(f"{owner_text} occluded accessory is missing occlusion_reason")

    for forbidden in contract.get("forbidden", []):
        if "rear-camera" in _normalized_text(forbidden).casefold() and "ui" not in _normalized_text(forbidden).casefold():
            issues.append("scene contract weakens the rear-screen UI prohibition")
    return list(dict.fromkeys(issues))


def scene_contract_prompt(contract: dict[str, Any]) -> str:
    """Render only model-facing scene constraints, never QA or provenance state."""

    lines = ["LOCKED SCENE CONTRACT:"]
    hand_map = contract.get("hand_map", {})
    for hand in hand_map.get("hands", []) if isinstance(hand_map, dict) else []:
        if not isinstance(hand, dict):
            continue
        visibility = _normalized_text(hand.get("visibility"))
        action = _normalized_text(hand.get("action"))
        target = _normalized_text(hand.get("target"))
        contact_target = hand.get("contact_target")
        target_clause = f" -> {target}" if target else ""
        contact_clause = ""
        if isinstance(contact_target, dict):
            object_text = _normalized_text(contact_target.get("object"))
            region_text = _normalized_text(contact_target.get("region"))
            if object_text and region_text:
                contact_clause = f"; contact={object_text}:{region_text}"
        lines.append(
            "Hand — {owner} {side}: visibility={visibility}; {action}{target_clause}{contact_clause}; {attachment}.".format(
                owner=_normalized_text(hand.get("owner")),
                side=_normalized_text(hand.get("side")),
                visibility=visibility,
                action=action,
                target_clause=target_clause,
                contact_clause=contact_clause,
                attachment=_normalized_text(hand.get("attachment")),
            )
        )
    if isinstance(hand_map, dict) and hand_map.get("forbidden"):
        lines.append(
            "Hand guardrails: "
            + "; ".join(
                _normalized_text(item) for item in hand_map.get("forbidden", []) if _normalized_text(item)
            )
            + "."
        )

    device_contract = contract.get("device_contract", {})
    for device in device_contract.get("devices", []) if isinstance(device_contract, dict) else []:
        if not isinstance(device, dict):
            continue
        line = (
            "Device — {owner} uses {object}; visible face={face}; orientation={orientation}; use={use}."
        ).format(
            owner=_normalized_text(device.get("owner")),
            object=_normalized_text(device.get("object")),
            face=_normalized_text(device.get("visible_face")),
            orientation=_normalized_text(device.get("orientation")),
            use=_normalized_text(device.get("use")),
        )
        if _normalized_text(device.get("screen_content")):
            line += f" Screen content: {_normalized_text(device.get('screen_content'))}."
        lines.append(line)

    action_topology = contract.get("action_topology", {})
    if isinstance(action_topology, dict) and action_topology.get("applies"):
        lines.append(
            "Action chronology — camera={camera}; phase={phase}; door={door}; return path={returned}; "
            "shared action={shared}.".format(
                camera=_normalized_text(action_topology.get("camera_side")),
                phase=_normalized_text(action_topology.get("temporal_phase")),
                door=_normalized_text(action_topology.get("door_state")),
                returned=bool(action_topology.get("return_path_visible")),
                shared=bool(action_topology.get("shared_action_visible")),
            )
        )

    transition = contract.get("transition", {})
    if isinstance(transition, dict) and transition.get("required"):
        evidence = "; ".join(
            _normalized_text(item) for item in transition.get("visible_evidence", []) if _normalized_text(item)
        )
        lines.append(
            "Transition — {from_phase} at {from_location} -> {to_phase} at {to_location}; "
            "{transition}; focal moment={focal}; visible evidence={evidence}.".format(
                from_phase=_normalized_text(transition.get("from_phase")),
                from_location=_normalized_text(transition.get("from_location")),
                to_phase=_normalized_text(transition.get("to_phase")),
                to_location=_normalized_text(transition.get("to_location")),
                transition=_normalized_text(transition.get("transition")),
                focal=_normalized_text(transition.get("focal_moment")),
                evidence=evidence,
            )
        )

    scale = contract.get("scale", {})
    if isinstance(scale, dict) and scale.get("required"):
        lines.append(
            "Scale — Aachu={aachu}; Zuv={zuv}; relation={relation}; pose={pose}; evidence={evidence}.".format(
                aachu=_normalized_text(scale.get("aachu_height")),
                zuv=_normalized_text(scale.get("zuv_height")),
                relation=_normalized_text(scale.get("relative_height")),
                pose=_normalized_text(scale.get("pose")),
                evidence="; ".join(
                    _normalized_text(item) for item in scale.get("evidence", []) if _normalized_text(item)
                ),
            )
        )

    for accessory in contract.get("accessories", []):
        if not isinstance(accessory, dict):
            continue
        visibility = _normalized_text(accessory.get("visibility"))
        detail = _normalized_text(accessory.get("placement"))
        if visibility.casefold() == "occluded":
            detail = "occluded because " + _normalized_text(accessory.get("occlusion_reason"))
        lines.append(
            "Accessory — {owner}: {item}; worn; {visibility}; {detail}.".format(
                owner=_normalized_text(accessory.get("owner")),
                item=_normalized_text(accessory.get("item")),
                visibility=visibility,
                detail=detail,
            )
        )

    topology = contract.get("spatial_topology", {})
    if isinstance(topology, dict):
        for person in topology.get("people", []):
            if not isinstance(person, dict):
                continue
            relations = "; ".join(
                "{object}={relation}".format(
                    object=_normalized_text(item.get("object")),
                    relation=_normalized_text(item.get("expected_relation")),
                )
                for item in person.get("environment_planes", [])
                if isinstance(item, dict)
            )
            lines.append(
                "Spatial — {person}: {relations}; separation={separation}.".format(
                    person=_normalized_text(person.get("person")),
                    relations=relations or "no nearby solid plane",
                    separation=_normalized_text(person.get("required_visible_separation")),
                )
            )

    richness = contract.get("visual_richness", {})
    if isinstance(richness, dict):
        detail_count = richness.get("story_detail_count", {})
        if isinstance(detail_count, dict):
            detail_range = "{minimum}-{maximum}".format(
                minimum=_normalized_text(detail_count.get("minimum")),
                maximum=_normalized_text(detail_count.get("maximum")),
            )
        else:
            detail_range = ""
        lines.append(
            "Story proof — focal action={action}; cause/effect={cause}; use {details} relevant environmental details."
            .format(
                action=_normalized_text(richness.get("focal_action")),
                cause=_normalized_text(richness.get("cause_effect")),
                details=detail_range,
            )
        )

    lines.append(
        "Never place UI, map, text, or controls on a phone's rear-camera/back face. "
        "Never use a crouched, squatting, cramped, or folded pose to hide scale."
    )
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


__all__ = [
    "SCENE_CONTRACT_SCHEMA_VERSION",
    "action_topology_prompt",
    "build_action_topology_contract",
    "build_device_contract",
    "build_hand_ownership_map",
    "build_pre_generation_scene_contract",
    "build_scale_accessory_contract",
    "build_scene_transition_contract",
    "build_spatial_topology_contract",
    "build_visual_richness_contract",
    "hand_ownership_prompt",
    "infer_scene_people",
    "scene_contract_prompt",
    "spatial_topology_prompt",
    "validate_pre_generation_scene_contract",
    "visual_richness_prompt",
]
