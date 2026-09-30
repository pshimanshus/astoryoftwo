from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from pipeline.stages.carousel_visual_integrity import (
    build_hand_ownership_map,
    hand_is_visible,
)
from pipeline.stages.carousel_sequence import package_sequence_inputs, sequence_input_fingerprint


def synthetic_route_story_plan() -> dict[str, Any]:
    """Planning input for synthetic route fixtures, never visual evidence."""

    return {
        "theme": "Choosing each other does not choose every shared direction.",
        "recognition": "Partners who trust the relationship while learning ordinary decisions together.",
        "sequence_mode": "relationship_change",
        "opening_promise": "How will two people who choose each other choose one way forward?",
        "mismatch": "Their commitment is certain while their preferred directions differ.",
        "turn_or_accumulation": "Separate choices become a shared physical route on the map.",
        "payoff": "Both partners finish the map action together instead of pulling apart.",
        "send_reason": "We can be certain of us and still be learning our way.",
    }


def synthetic_route_sequence_review(package: Path) -> dict[str, Any]:
    """Fabricated QA for the four-card key/doors/map lifecycle fixture only.

    The test images are solid fills. These authored scenario observations test
    schema and freshness plumbing; they are NOT observations of actual pixels.
    Never use this helper as production review evidence.
    """

    context, slides = package_sequence_inputs(package)
    assert len(slides) == 4
    assert context["story_plan"]["theme"] == synthetic_route_story_plan()["theme"]
    return {
        "schema_version": "carousel-sequence-review/v1",
        "synthetic_fixture": True,
        "source_sha256": sequence_input_fingerprint(context, slides),
        "formats": {
            "instagram_post": {
                "status": "PASS",
                "hook_observed": "The offered house key establishes commitment and asks how their shared life will proceed.",
                "transitions": [
                    {"from_slide": 1, "to_slide": 2, "development_observed": "The accepted key gives way to opposite pointing directions around a moving box; certainty about each other meets uncertainty about a choice."},
                    {"from_slide": 2, "to_slide": 3, "development_observed": "The separate doorways become opposing grips on one map, making the disagreement a shared problem rather than two unrelated choices."},
                    {"from_slide": 3, "to_slide": 4, "development_observed": "Opposing map grips become adjacent fingers tracing one route, changing the action from pulling apart to choosing together."},
                ],
                "copy_image": [
                    {"slide": 1, "kind": slides[0]["copy_image_relation"]["kind"], "observed": "The line names certainty while the key handoff supplies a concrete shared-home commitment."},
                    {"slide": 2, "kind": slides[1]["copy_image_relation"]["kind"], "observed": "The line names two directions and the two pointing arms establish their incompatible immediate choices."},
                    {"slide": 3, "kind": slides[2]["copy_image_relation"]["kind"], "observed": "The words deny an automatic answer while opposing map grips show why loving each other does not settle the route."},
                    {"slide": 4, "kind": "wordless", "observed": "The adjacent tracing fingers complete the answer without an added sentence; only the brandmark remains."},
                ],
                "coherence_observed": "The key establishes a shared home, the box opens the choice, and the map stays the contested object until both fingers align.",
                "redundancy_observed": "Commitment, incompatible directions, physical disagreement and coordinated choice supply four distinct states; the sequence stops at the shared route.",
                "closure": {"setup_slides": [1, 2, 3], "ending_slide": 4, "observed": "Their aligned fingers answer the separate directions and release the map tension without undoing the opening commitment."},
                "issues": [],
            },
        },
    }


def cinematic_slide_fields(
    slide_number: int,
    slide_count: int,
) -> dict[str, Any]:
    """Return specific canonical direction suitable for production fixtures."""

    return {
        "role": (
            "cover",
            "deepening",
            "turn",
            "payoff",
        )[(slide_number - 1) % 4],
        "relationship_state": "Their disagreement remains connected through one shared task.",
        "camera": {
            "shot_size": (
                "wide environmental geography frame",
                "medium action two-person frame",
                "close evidence and microexpression frame",
                "medium-wide two-person payoff frame",
            )[(slide_number - 1) % 4],
            "position": "doorway-height three-quarter view from the room's left side",
            "negative_space": "quiet upper-left plaster wall reserved for the exact copy",
        },
        "focal_hierarchy": (
            "First read their shared hand action, second read their opposing gaze, "
            "then the protected upper-left copy space."
        ),
        "setting": {
            "place": "the worn dining-table corner beside the kitchen doorway",
            "time": "late monsoon afternoon",
            "motivated_light": (
                "cool window light enters from frame left and catches the shared object"
            ),
            "depth_layers": {
                "foreground": "an out-of-focus chair edge locates the viewer inside the room",
                "midground": "Aachu and Zuv act on the shared object across the table",
                "background": "an open kitchen doorway preserves the lived domestic consequence",
            },
        },
        "visual_richness": {
            "scene_action_binding": "The locked physical action remains the focal event.",
            "point_of_view": "The frame follows Aachu noticing that disagreement can stay tender.",
            "before_frame": "The shared object lay still between them before both reached for it.",
            "after_frame": "Their opposing grip loosens as they begin choosing one direction.",
            "continuation_pull": (
                "The unresolved direction asks what choice they will make next."
                if slide_number < slide_count
                else "The released tension reveals the final shared decision."
            ),
            "story_evidence": [
                {
                    "carrier": "creased shared map",
                    "observable_state": "its center fold pulls taut between their hands",
                    "narrative_job": "proves both people are invested in one difficult choice",
                },
                {
                    "carrier": "two cooling tea cups",
                    "observable_state": "both cups sit untouched beside the opened route",
                    "narrative_job": "proves the conversation has lasted beyond a posed instant",
                },
            ],
            "posed_portrait_allowed": False,
            "decorative_clutter_allowed": False,
        },
    }


def passing_cinematic_story_frame(package: Path, slide_number: int) -> dict[str, Any]:
    """Return image-first cinematic observations mapped to the locked slide plan."""

    payload = json.loads((package / "slides.json").read_text(encoding="utf-8"))
    slides = payload.get("slides") if isinstance(payload, dict) else payload
    slide = next(
        item
        for item in slides
        if isinstance(item, dict) and int(item.get("slide", 0) or 0) == slide_number
    )
    richness = slide.get("visual_richness") or {}
    setting = slide.get("setting") or {}
    depth = setting.get("depth_layers") or {}
    review = {
        "status": "PASS",
        "evidence": "The decoded pixels show a layered, asymmetrical caught event with visible temporal consequence.",
        "frame_reads_as_caught_event": True,
        "before_after_implied": True,
        "motivated_light_observed": str(
            setting.get("motivated_light")
            or "cool window light enters from frame left across the focal hands"
        ),
        "depth_layers_observed": {
            key: str(depth.get(key) or fallback)
            for key, fallback in {
                "foreground": "soft chair edge anchors the near plane",
                "midground": "the couple and shared action occupy the focal plane",
                "background": "the kitchen doorway supplies lived context",
            }.items()
        },
        "focal_action_clear": True,
        "story_evidence": [dict(item) for item in richness.get("story_evidence") or []],
        "posed_portrait": False,
        "decorative_clutter": False,
        "generic_ai_tells": [],
    }
    if slide_number == len(slides):
        review["final_payoff_observed"] = "Their softened grip visibly resolves the shared decision."
    else:
        review["continuation_pull_observed"] = str(
            richness.get("continuation_pull")
            or "Their unresolved grip leaves the next choice visibly open."
        )
    return review


def passing_entity_spatial_integrity(package: Path, slide_number: int) -> dict[str, Any]:
    """Return explicit per-hand pixel observations matching one slide plan."""

    payload = json.loads((package / "slides.json").read_text(encoding="utf-8"))
    slides = payload.get("slides") if isinstance(payload, dict) else payload
    slide = next(
        item
        for item in slides
        if isinstance(item, dict) and int(item.get("slide", 0) or 0) == slide_number
    )
    scene = str(
        slide.get("physical_action")
        or slide.get("visual")
        or slide.get("scene")
        or ""
    )
    hand_map = slide.get("hand_map")
    if not isinstance(hand_map, dict):
        hand_map = build_hand_ownership_map(scene)
    people = [str(value) for value in hand_map.get("people", [])]
    visible_hands: list[dict[str, Any]] = []
    for hand in hand_map.get("hands", []):
        if not isinstance(hand, dict) or not hand_is_visible(hand):
            continue
        owner = str(hand.get("owner") or "person")
        side = str(hand.get("side") or "hand")
        visible_hands.append(
            {
                "owner": owner,
                "side": side,
                "story_required": True,
                "attachment_traceable": True,
                "contact_geometry_pass": True,
                "solid_object_intersection": False,
                "malformed_or_extra_fingers": False,
                "contact": str(hand.get("contact") or "no unintended object contact"),
                "evidence": (
                    f"{owner}'s {side} forearm and wrist continue cleanly into the visible hand."
                ),
            }
        )
    return {
        "status": "PASS",
        "evidence": "Every planned person and visible hand has explicit ownership, anatomy, and contact evidence.",
        "expected_people": len(people),
        "observed_people": len(people),
        "observed_people_names": people,
        "unexpected_entities": [],
        "unexpected_limbs": [],
        "duplicated_limbs": [],
        "ambiguous_contacts": [],
        "silhouette_evidence": "Every person has a continuous silhouette separated from nearby solid objects.",
        "visible_hands": visible_hands,
    }
