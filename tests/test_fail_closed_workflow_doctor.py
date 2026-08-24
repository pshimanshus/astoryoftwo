from __future__ import annotations

from pipeline.stages.carousel_visual_storytelling import first_failed_pixel_gate


def test_pixel_gate_order_stops_at_semantic_action() -> None:
    qa = {
        "checks": {
            "semantic_action": {"pass": False},
            "relationship_state": {"pass": False},
            "entity_anatomy_spatial": {"pass": False},
            "identity": {"pass": False},
            "text_style_dimensions": {"pass": False},
        }
    }

    gate = first_failed_pixel_gate(qa)

    assert gate is not None
    assert gate[0] == "semantic_action"


def test_pixel_gate_order_reaches_relationship_only_after_semantic_passes() -> None:
    qa = {
        "checks": {
            "semantic_action": {"pass": True},
            "relationship_state": {"pass": False},
            "identity": {"pass": False},
        }
    }

    assert first_failed_pixel_gate(qa)[0] == "relationship_state"


def test_legacy_frame_fields_still_identify_semantic_failure() -> None:
    qa = {
        "checks": {
            "visual_story_readability": {
                "frames": [
                    {
                        "slide": 4,
                        "core_action_legible": False,
                        "relationship_turn_legible": True,
                    }
                ]
            }
        }
    }

    gate = first_failed_pixel_gate(qa)

    assert gate == (
        "semantic_action",
        "semantic_action failed on rendered slide 4 (core_action_legible).",
    )


def test_missing_evidence_is_not_misreported_as_a_failed_visual() -> None:
    assert first_failed_pixel_gate({"status": "PENDING"}) is None
