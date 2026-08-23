from __future__ import annotations

import json
from pathlib import Path

from pipeline.stages.carousel_visual_storytelling import (
    REVIEW_PROVENANCE_VERSION,
    director_event_fingerprint,
    frame_review_input_fingerprint,
    frame_review_output_fingerprint,
    image_file_fingerprint,
    review_response_fingerprint,
)


PACKAGE = Path("output/carousels/2026-08-14/certain-of-you-lost-in-us-no-script")
STATE = json.loads((PACKAGE / "image-generation.json").read_text(encoding="utf-8"))
PLAN = json.loads((PACKAGE / "visual-plan-quality.json").read_text(encoding="utf-8"))
OUTPUT = STATE["slides"][0]["native_outputs"]["instagram_post"]
FINAL_REL = OUTPUT["path"]
FINAL_PATH = PACKAGE / FINAL_REL
ATTEMPT_ROOT = FINAL_PATH.parents[1]
FRAME_REL = FINAL_PATH.relative_to(ATTEMPT_ROOT).as_posix()
SOURCE_ASSET = {
    "sha256": OUTPUT["sha256"],
    "width": OUTPUT["width"],
    "height": OUTPUT["height"],
}

raw_event_b_path = PACKAGE / ".internal/proof-attempt-01-event-b-raw-response.md"
raw_event_b = raw_event_b_path.read_text(encoding="utf-8")

frames = [
    {
        "slide": 1,
        "format": "instagram_post",
        "file": FRAME_REL,
        "status": "REPAIR",
        "expected_silent_read": "A couple moves forward in physical alignment while two wheeled scenery flats visibly move apart behind them, making certainty in each other coexist with a shifting shared world.",
        "observed_image_first_read": "A warmly affectionate couple walks toward the audience between two painted scenery flats in a theatre, but the panels and couple read as static and posed.",
        "core_action_legible": False,
        "relationship_turn_legible": False,
        "focal_hierarchy": "The exact quote and centered couple lead; the two scenery flats establish theatre location but not a changing-stage event.",
        "hands_gaze_prop_legible": True,
        "storyboard_match": False,
        "native_format_readability": True,
        "copy_visual_contradictions": [],
        "unexpected_story": ["The scene reads as a posed romantic quote-card portrait rather than an active shared scene change."],
        "match_rationale": "Theatre geography, shoulder contact, exact copy and palette survive, but static panels, soft mutually absorbed gazes and an embrace-like hidden arm remove the intended lost-inside-a-moving-life contradiction.",
        "evidence": "The caster wheels, wooden stage and seat backs are visible; both bodies face front, Aachu looks down-left, Zuv looks toward her, and neither visible hand acts on the changing world.",
        "image_fingerprint": image_file_fingerprint(FINAL_PATH),
    }
]

readability = {
    "pass": False,
    "status": "REPAIR",
    "event": "rendered_frame_story_audit",
    "image_first": True,
    "provisional": True,
    "scope": "selected_proof_only",
    "full_event_b": False,
    "reviewer_id": "/root/theater_proof_event_b",
    "reviewer_evidence": "A fresh image-first reviewer found exact copy, correct brandmark and clear theatre geography, but judged the rendered frame a static posed quote card with no legible scene-change action or visual proof of disorientation.",
    "source_director_event_fingerprint": director_event_fingerprint(PLAN),
    "reviewed_native_formats": ["instagram_post"],
    "sequence_read": "The render shows an affectionate couple walking together on a theatre stage between two scenic panels, without a visible scene change.",
    "relationship_turn": "Security is visible through closeness, but uncertainty inside a changing shared world is not visually legible.",
    "setup_payoff_evidence": "The two coloured wheeled flats and empty seat backs establish the theatre motif, but no moving-object state is proven in the pixels.",
    "weakest_frame": "The only rendered proof is the weakest frame because the quote carries the narrative while the couple and scenery remain posed and static.",
    "repair_decision": "Repair the exact proof by restoring actual faces and converting the static portrait into an unmistakable equal scene-change action while preserving copy, brandmark, palette, wardrobe and anatomy.",
    "frames": frames,
    "issues": [
        "Aachu and Zuv identity fidelity is below lock quality.",
        "The changing-stage action and emotional contradiction are not image-first legible.",
    ],
    "review_provenance": {
        "schema_version": REVIEW_PROVENANCE_VERSION,
        "reviewer_task_id": "/root/theater_proof_event_b",
        "reviewer_run_id": "event-b-run-9b76f821-5d87-4b87-b9c4-f401f95c4cb4",
        "input_fingerprint": frame_review_input_fingerprint(frames),
        "raw_response_artifact": ".internal/proof-attempt-01-event-b-raw-response.md",
        "raw_response_fingerprint": review_response_fingerprint(raw_event_b),
        "output_fingerprint": "",
    },
}
readability["review_provenance"]["output_fingerprint"] = frame_review_output_fingerprint(readability)

anatomy = {
    "source_asset": SOURCE_ASSET,
    "expected_arms": 4,
    "observed_arms": 4,
    "expected_hands": 2,
    "observed_hands": 2,
    "visible_hands": [
        {
            "owner": "Aachu",
            "side": "left",
            "action": "hangs at her own outer thigh",
            "story_required": True,
            "attachment_visible": True,
            "attachment_evidence": "Her shoulder, sleeve, forearm, wrist and five-finger hand form one continuous chain.",
            "contact_object": None,
            "contact_geometry_pass": True,
            "occlusion_evidence": "The hand hangs free of scenery, clothing edges and Zuv with open stage-floor space around it.",
            "solid_object_intersection": False,
            "edge_entry_unexplained": False,
        },
        {
            "owner": "Zuv",
            "side": "right",
            "action": "hangs at his own outer thigh",
            "story_required": True,
            "attachment_visible": True,
            "attachment_evidence": "His shoulder, sleeve, forearm, wrist and five-finger hand form one continuous chain.",
            "contact_object": None,
            "contact_geometry_pass": True,
            "occlusion_evidence": "The hand hangs free of the dusty-rose flat, trousers and Aachu with readable open space.",
            "solid_object_intersection": False,
            "edge_entry_unexplained": False,
        },
    ],
    "occluded_hands": [
        {"owner": "Aachu", "side": "right", "evidence": "Her inside hand is fully hidden between the adjacent torsos."},
        {"owner": "Zuv", "side": "left", "evidence": "His inside hand is fully hidden behind the overlapping upper bodies."},
    ],
    "unexpected_limbs": [],
    "duplicated_limbs": [],
    "malformed_fingers": False,
}

entity = {
    "source_asset": SOURCE_ASSET,
    "expected_people": 2,
    "observed_people": 2,
    "expected_arms": 4,
    "observed_arms": 4,
    "expected_hands": 2,
    "observed_hands": 2,
    "unexpected_entities": [],
    "unexpected_limbs": [],
    "duplicated_limbs": [],
    "evidence": "Exactly Aachu and Zuv appear; four coherent arms resolve into two visible outer hands and two naturally occluded inside hands, with no audience, crew, reflections or duplicate people.",
}

richness = {
    "source_asset": SOURCE_ASSET,
    "foreground": "A low strip of empty dark upholstered first-row seat backs establishes the audience-side point of view.",
    "midground": "Aachu and Zuv occupy the stage center in locked black-denim and white-charcoal wardrobe.",
    "background": "One indigo and one dusty-rose scenery flat stand on visible caster wheels against watercolor stage spill.",
    "focal_action": "The intended aligned walk is present only weakly; the body language currently reads as a static affectionate portrait.",
    "story_details": ["empty first-row seat backs", "visible caster wheels", "indigo scenery flat", "dusty-rose scenery flat"],
    "cause_effect": "The wheeled flats imply a changeable theatre world, but their motion does not visibly affect the couple in the current pixels.",
    "posed_portrait": False,
    "decorative_clutter": False,
}

qa = {
    "schema_version": "2.1",
    "status": "REPAIR",
    "proof_state": "GENERATED_QUARANTINED",
    "image_set_sha256": STATE["image_set_sha256"],
    "slides": [
        {
            "slide": 1,
            "native_outputs": {
                "instagram_post": {
                    "path": FINAL_REL,
                    "sha256": OUTPUT["sha256"],
                    "width": OUTPUT["width"],
                    "height": OUTPUT["height"],
                    "normalization": OUTPUT.get("normalization"),
                    "model_native_source": OUTPUT.get("model_native_source"),
                }
            },
        }
    ],
    "checks": {
        "aachu_face": {
            "pass": False,
            "reference_option_ids": [
                "output/carousels/2026-08-14/certain-of-you-lost-in-us-no-script/.internal/reference-crops/aachu-face-04-crop.png",
                "output/carousels/2026-08-14/certain-of-you-lost-in-us-no-script/.internal/reference-crops/together-18-faces.jpg",
            ],
            "likeness_notes": "The face reads narrower and more pointed than the fuller oval anchor, with altered eyes, nose and smile.",
        },
        "zuv_face": {
            "pass": False,
            "reference_option_ids": [
                "output/carousels/2026-08-14/certain-of-you-lost-in-us-no-script/.internal/reference-crops/zuv-portrait-07-crop.jpg",
                "output/carousels/2026-08-14/certain-of-you-lost-in-us-no-script/.internal/reference-crops/together-18-faces.jpg",
            ],
            "likeness_notes": "The generated face is slimmer and the dense uniform ringlets replace the anchor's thick swept-up loose texture and broader jaw-cheek structure.",
        },
        "couple_scale": {"pass": True, "evidence": "Zuv reads modestly taller at the same depth without an exaggerated gap."},
        "dress_continuity": {"pass": True, "evidence": "Aachu wears black overshirt, black top and blue jeans; Zuv wears a white zip jacket and charcoal trousers."},
        "style": {"pass": True, "evidence": "Neutral off-white paper, transparent indigo and dusty-rose watercolor, fine ink and visible grain pass."},
        "scene_logic": {"pass": False, "evidence": "Theatre location is clear, but the changing scenery and felt disorientation remain static rather than causal."},
        "scene_entity_integrity": {"pass": True, "slides": [{"slide": 1, "formats": {"instagram_post": entity}}]},
        "anatomy_inventory": {"pass": True, "slides": [{"slide": 1, "formats": {"instagram_post": anatomy}}]},
        "spatial_topology": {
            "pass": True,
            "slides": [
                {
                    "slide": 1,
                    "observed_people": 2,
                    "evidence_views": {
                        "full_frame": "Two coherent bodies stand on one stage plane between two separate wheeled flats and in front of one separate row of seats.",
                        "person_object_crop": "Both body silhouettes remain fully inside the open space between the two flats with no scenery edge crossing either person.",
                        "focal_detail": "Each visible outer hand connects through a continuous wrist and forearm and remains free of solid props.",
                    },
                    "environment_planes": [
                        {"object": "wooden stage floor", "depth_order": "beneath both people and both scenery-flat caster bases", "boundary_continuous": True},
                        {"object": "indigo scenery flat", "depth_order": "behind and left of Aachu with open space between", "boundary_continuous": True},
                        {"object": "dusty-rose scenery flat", "depth_order": "behind and right of Zuv with open space between", "boundary_continuous": True},
                        {"object": "empty seat backs", "depth_order": "foreground below and in front of the stage edge", "boundary_continuous": True},
                    ],
                    "people": [
                        {
                            "person": "Aachu",
                            "silhouette_traceable": True,
                            "silhouette_evidence": "Head, hair, neck, shoulders, torso, sleeves, visible left hand, jeans and lower body remain traceable against the off-white stage field.",
                            "body_regions": [
                                {
                                    "region": "full visible body and outer arm chain",
                                    "near_object": "indigo flat, stage floor, Zuv and foreground seats",
                                    "expected_relation": "in_front_of",
                                    "observed_relation": "in_front_of",
                                    "boundary_continuous": True,
                                    "occlusion_order_clear": True,
                                    "solid_object_intersection": False,
                                    "morph_or_merge": False,
                                    "evidence": "Her outline remains separate from the left flat and seats while Zuv naturally overlaps only at the shoulder and torso edge.",
                                }
                            ],
                            "ambiguous_regions": [],
                        },
                        {
                            "person": "Zuv",
                            "silhouette_traceable": True,
                            "silhouette_evidence": "Head, hair, neck, shoulders, jacket, visible right arm and hand, trousers and lower body remain traceable.",
                            "body_regions": [
                                {
                                    "region": "full visible body and outer arm chain",
                                    "near_object": "dusty-rose flat, stage floor, Aachu and foreground seats",
                                    "expected_relation": "in_front_of",
                                    "observed_relation": "in_front_of",
                                    "boundary_continuous": True,
                                    "occlusion_order_clear": True,
                                    "solid_object_intersection": False,
                                    "morph_or_merge": False,
                                    "evidence": "His outline remains separate from the right flat and seats while the couple overlap reads as natural shoulder contact.",
                                }
                            ],
                            "ambiguous_regions": [],
                        },
                    ],
                    "ambiguous_regions": [],
                    "unresolved_intersections": [],
                }
            ],
        },
        "visual_richness": {"pass": False, "slides": [{"slide": 1, "formats": {"instagram_post": richness}}]},
        "integrated_final_text": {"pass": True, "evidence": "Exact two-line copy and exactly one tiny top-right @a.storyof.two brandmark are visible."},
        "final_files": {"pass": True, "evidence": "The quarantined proof is a decodable 1080x1440 PNG bound to its recorded SHA-256."},
        "visual_story_readability": readability,
    },
    "reviews": {
        "anatomy_entity_spatial_identity": {
            "reviewer_id": "/root/theater_proof_identity_qa",
            "pass": False,
            "evidence": "Exact dimensions, anatomy, topology, wardrobe, text, brandmark, paper and scale pass, but both faces drift from the actual identity anchors, especially Zuv's hair silhouette and Aachu's face shape.",
        },
        "storytelling_richness_text_style": {
            "reviewer_id": "/root/theater_proof_event_b",
            "pass": False,
            "evidence": "Theatre location, exact copy, brandmark and palette pass, but the scenery reads static and the centered affectionate pose behaves as a quote card instead of an active visual contradiction.",
        },
    },
    "required_repairs": [
        "Restore Aachu's fuller oval anchor face and Zuv's swept-up loose-textured hair plus broader jaw and cheeks.",
        "Make the scenery change physically active and the couple's forward effort legible before the copy.",
        "Preserve exact copy, one brandmark, neutral paper, wardrobe, two visible owned hands, clean anatomy and 3:4 canvas.",
    ],
}

(PACKAGE / "visual-qa.json").write_text(json.dumps(qa, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
print(json.dumps({"status": "REPAIR", "image_set_sha256": qa["image_set_sha256"]}, indent=2))
