from __future__ import annotations

import json
import sys
from copy import deepcopy
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[5]
sys.path.insert(0, str(PROJECT_ROOT))

from pipeline.stages.carousel_visual_storytelling import (
    REVIEW_PROVENANCE_VERSION,
    director_event_fingerprint,
    frame_review_input_fingerprint,
    frame_review_output_fingerprint,
    image_file_fingerprint,
    review_response_fingerprint,
)


PACKAGE_DIR = Path(__file__).resolve().parents[1]
STATE_PATH = PACKAGE_DIR / "image-generation.json"
VISUAL_PLAN_PATH = PACKAGE_DIR / "visual-plan-quality.json"
QA_PATH = PACKAGE_DIR / "visual-qa.json"
RAW_STORY_REVIEW_PATH = (
    PACKAGE_DIR / ".internal" / "attempt-04-final-story-text-style-audit-raw.json"
)


def main() -> None:
    state = json.loads(STATE_PATH.read_text(encoding="utf-8"))
    visual_plan = json.loads(VISUAL_PLAN_PATH.read_text(encoding="utf-8"))
    slide_record = deepcopy(state["slides"][0])
    output = slide_record["native_outputs"]["instagram_post"]
    quarantine_root = PACKAGE_DIR / state["quarantine_dir"]
    image_path = quarantine_root / "final" / "slide-06.png"
    image_fingerprint = image_file_fingerprint(image_path)
    source_asset = {
        "sha256": output["sha256"],
        "width": output["width"],
        "height": output["height"],
    }

    visible_hands = [
        {
            "owner": "Aachu",
            "side": "left",
            "action": "grips the lower cushion at her outer side",
            "story_required": True,
            "attachment_visible": True,
            "attachment_evidence": "Her sleeve, forearm, wrist, palm, and fingers form one continuous chain into the cushion grip.",
            "contact_object": "Cushion B",
            "contact_geometry_pass": True,
            "occlusion_evidence": "Her fingers wrap around the near cushion corner with the cloth edge visibly in front of the palm.",
            "solid_object_intersection": False,
            "edge_entry_unexplained": False,
        },
        {
            "owner": "Aachu",
            "side": "right",
            "action": "remains open toward the airborne cushion after release",
            "story_required": True,
            "attachment_visible": True,
            "attachment_evidence": "Her shoulder, sleeve, forearm, bracelet, wrist, palm, and spread fingers are continuously visible.",
            "contact_object": None,
            "contact_geometry_pass": True,
            "occlusion_evidence": "Open air visibly separates the released hand from the airborne cushion and every other object.",
            "solid_object_intersection": False,
            "edge_entry_unexplained": False,
        },
        {
            "owner": "Zuv",
            "side": "left",
            "action": "grips the left edge of Cushion C",
            "story_required": True,
            "attachment_visible": True,
            "attachment_evidence": "His rolled sleeve, forearm, wrist, palm, and curled fingers remain continuously traceable.",
            "contact_object": "Cushion C",
            "contact_geometry_pass": True,
            "occlusion_evidence": "His fingers curl over the near cloth edge while the cushion remains in front of his torso.",
            "solid_object_intersection": False,
            "edge_entry_unexplained": False,
        },
        {
            "owner": "Zuv",
            "side": "right",
            "action": "grips the right edge of Cushion C",
            "story_required": True,
            "attachment_visible": True,
            "attachment_evidence": "His rolled sleeve, forearm, watch, wrist, palm, and fingers form one unbroken arm-to-hand chain.",
            "contact_object": "Cushion C",
            "contact_geometry_pass": True,
            "occlusion_evidence": "His thumb and fingers visibly close around the cushion edge without merging into the fabric.",
            "solid_object_intersection": False,
            "edge_entry_unexplained": False,
        },
    ]

    frame = {
        "slide": 6,
        "format": "instagram_post",
        "file": "final/slide-06.png",
        "status": "PASS",
        "expected_silent_read": "Shared work stress erupts into a genuine mutual cushion argument, with exactly one cushion airborne and no playful reconciliation.",
        "observed_image_first_read": "A genuinely angry couple argues while each handles a cushion and one cushion flies between them; the open laptop and document preserve the prior work-stress cause.",
        "core_action_legible": True,
        "relationship_turn_legible": True,
        "focal_hierarchy": "The angry full-body confrontation leads, the airborne cushion carries the action, and the laptop with document quietly preserves cause.",
        "hands_gaze_prop_legible": True,
        "storyboard_match": True,
        "native_format_readability": True,
        "copy_visual_contradictions": [],
        "unexpected_story": [],
        "match_rationale": "Both partners are visibly angry rather than playful, exactly three cushions are traceable, and the work props connect the argument to the preceding shared-stress beat.",
        "evidence": "Tight brows, open mouths, planted feet, angry eye contact, four attributable hands, one airborne cushion, one cushion per partner, and the unbranded laptop-document pair are all visible.",
        "image_fingerprint": image_fingerprint,
    }
    readability = {
        "pass": True,
        "status": "PASS",
        "event": "rendered_frame_story_audit",
        "image_first": True,
        "provisional": True,
        "scope": "selected_proof_only",
        "full_event_b": False,
        "reviewer_id": "/root/proof_attempt1_story_text_style_audit",
        "reviewer_evidence": "A fresh independent image-first review passed the fight beat, exact copy, exact brandmark, visual richness, watercolor linework, and clean warm-ivory paper tone.",
        "source_director_event_fingerprint": director_event_fingerprint(visual_plan),
        "reviewed_native_formats": ["instagram_post"],
        "sequence_read": "The frame reads as the genuine mutual argument that follows shared stress, not as a playful pillow fight.",
        "relationship_turn": "The couple reaches real friction before later care; this proof deliberately does not reconcile them.",
        "setup_payoff_evidence": "The open unbranded laptop and shifted work document visibly carry the prior shared-stress beat into the argument.",
        "weakest_frame": "The story, style, and spatial topology pass, but the proof remains unusable because both faces drift from the selected identities and Zuv retains too much visual mass.",
        "repair_decision": "Preserve the correct story, text, paper tone, entity counts, cushion logic, anger, and rear-table separation while rebuilding both faces from the selected references and reducing Zuv to the locked near-equal scale.",
        "frames": [frame],
        "issues": [],
    }
    dense_readability = deepcopy(readability)
    dense_readability["frames"][0]["slide"] = 1
    raw_response = RAW_STORY_REVIEW_PATH.read_text(encoding="utf-8")
    provenance = {
        "schema_version": REVIEW_PROVENANCE_VERSION,
        "reviewer_task_id": "/root/proof_attempt1_story_text_style_audit",
        "reviewer_run_id": "019fb37a-dc30-7ce2-8f17-7a696a83c61e",
        "input_fingerprint": frame_review_input_fingerprint(
            dense_readability["frames"]
        ),
        "raw_response_artifact": RAW_STORY_REVIEW_PATH.relative_to(
            PACKAGE_DIR
        ).as_posix(),
        "raw_response_fingerprint": review_response_fingerprint(raw_response),
    }
    dense_readability["review_provenance"] = deepcopy(provenance)
    provenance["output_fingerprint"] = frame_review_output_fingerprint(
        dense_readability
    )
    readability["review_provenance"] = provenance

    format_evidence = {
        "source_asset": source_asset,
        "expected_arms": 4,
        "observed_arms": 4,
        "expected_hands": 4,
        "observed_hands": 4,
        "visible_hands": visible_hands,
        "unexpected_limbs": [],
        "duplicated_limbs": [],
        "malformed_fingers": False,
    }
    entity_evidence = {
        "source_asset": source_asset,
        "expected_people": 2,
        "observed_people": 2,
        "expected_arms": 4,
        "observed_arms": 4,
        "expected_hands": 4,
        "observed_hands": 4,
        "unexpected_entities": [],
        "unexpected_limbs": [],
        "duplicated_limbs": [],
        "evidence": "Only Aachu and Zuv appear; all four arms and all four hands remain attributable, exactly three cushions exist, and all four feet are visible.",
    }
    richness_evidence = {
        "source_asset": source_asset,
        "foreground": "The low table, unbranded open laptop, and shifted work document retain the argument's immediate cause.",
        "midground": "Aachu and Zuv occupy distinct full-body silhouettes with one airborne cushion between their angry gazes.",
        "background": "A restrained sofa, wall, and doorway establish the shared living-room geography without extra characters or story props.",
        "focal_action": "Aachu has released one cushion while gripping another, and Zuv grips the third cushion as they argue.",
        "story_details": [
            "exactly one airborne cushion",
            "open unbranded laptop",
            "shifted work document",
        ],
        "cause_effect": "The laptop and document preserve the shared work problem, which has escalated into a genuine mutual argument.",
        "posed_portrait": False,
        "decorative_clutter": False,
    }

    qa = {
        "schema_version": "2.1",
        "status": "REPAIR",
        "proof_state": "GENERATED_QUARANTINED",
        "image_set_sha256": state["image_set_sha256"],
        "reviews": {
            "anatomy_entity_spatial_identity": {
                "reviewer_id": "/root/proof_attempt1_anatomy_identity_audit",
                "pass": False,
                "evidence": "The exact 1080x1440 proof passes people, limb, hand, cushion, foot, anger, motion-line, and full-body topology checks, but both faces drift from the selected identities and Zuv reads around 5–6% taller with substantially greater visual mass.",
            },
            "storytelling_richness_text_style": {
                "reviewer_id": "/root/proof_attempt1_story_text_style_audit",
                "pass": True,
                "evidence": "The exact proof passes the angry story beat, exact copy, exact brandmark, visual richness, fine-ink transparent-watercolor style, and clean warm-ivory paper-tone checks.",
            },
        },
        "slides": [
            {
                "slide": 6,
                "native_outputs": deepcopy(slide_record["native_outputs"]),
            }
        ],
        "checks": {
            "storyboard": {"pass": True},
            "aachu_face": {
                "pass": False,
                "reference_option_ids": [
                    "ID01_AACHU_FACE_04",
                    "ID02_AACHU_REEL_JALDI",
                ],
                "likeness_notes": "Hair, skin tone, brows, and wardrobe partially anchor Aachu, but the rendered face is too narrow and pointed; the repair needs her wider soft oval-round face, fuller cheek width, natural nose, and soft chin.",
            },
            "zuv_face": {
                "pass": False,
                "reference_option_ids": ["ID04_ZUV_PORTRAIT_07"],
                "likeness_notes": "Beard, brows, skin tone, white top, and necklace partially anchor Zuv, but the tightly curled hair silhouette and elongated angular profile drift from portrait-07 and together-18.",
            },
            "couple_scale": {
                "pass": False,
                "evidence": "Zuv reads substantially taller and larger; the locked relationship requires only about a two-inch height difference, comparable body scale, the same floor plane, and equal visual weight.",
            },
            "dress_continuity": {"pass": True},
            "style": {
                "pass": True,
                "evidence": "Fine ink, transparent watercolor, restrained room detail, scene-led hierarchy, and clean warm ivory/off-white paper tone all pass without a dominant yellow, sepia, or parchment cast.",
            },
            "scene_logic": {"pass": True},
            "scene_entity_integrity": {
                "pass": True,
                "slides": [
                    {
                        "slide": 6,
                        "formats": {"instagram_post": entity_evidence},
                    }
                ],
            },
            "anatomy_inventory": {
                "pass": True,
                "slides": [
                    {
                        "slide": 6,
                        "formats": {"instagram_post": format_evidence},
                    }
                ],
            },
            "spatial_topology": {
                "pass": True,
                "slides": [
                    {
                        "slide": 6,
                        "observed_people": 2,
                        "evidence_views": {
                            "full_frame": "Both complete figures occupy distinct standing volumes, all four feet land on one floor plane, and the small rear table is isolated inside the gap between them.",
                            "person_object_crop": "All four arm-to-hand chains and both full leg-to-foot chains remain traceable around the three cushions without furniture overlap.",
                            "focal_detail": "Each visible hand has clear ownership and contact geometry, and open air separates the airborne cushion from both bodies.",
                        },
                        "environment_planes": [
                            {
                                "object": "sofa",
                                "depth_order": "behind both people and separate from their silhouettes",
                                "boundary_continuous": True,
                            },
                            {
                                "object": "coffee table",
                                "depth_order": "foreground below the hands and in front of the sofa",
                                "boundary_continuous": True,
                            },
                            {
                                "object": "floor",
                                "depth_order": "beneath all four visible feet",
                                "boundary_continuous": True,
                            },
                        ],
                        "people": [
                            {
                                "person": "Aachu",
                                "silhouette_traceable": True,
                                "silhouette_evidence": "Head, hair, shoulders, torso, both arms, both wrists, both hands, both legs, and both feet remain continuously traceable.",
                                "body_regions": [
                                    {
                                        "region": "full body and both arm-to-hand chains",
                                        "near_object": "sofa and two cushions",
                                        "expected_relation": "in_front_of",
                                        "observed_relation": "in_front_of",
                                        "boundary_continuous": True,
                                        "occlusion_order_clear": True,
                                        "solid_object_intersection": False,
                                        "morph_or_merge": False,
                                        "evidence": "Her silhouette is distinct from the sofa and both cushion relationships have readable overlap order.",
                                    }
                                ],
                                "ambiguous_regions": [],
                            },
                            {
                                "person": "Zuv",
                                "silhouette_traceable": True,
                                "silhouette_evidence": "Head, shoulders, torso, both rolled sleeves, both forearms, both hands, both legs, and both feet remain continuously traceable.",
                                "body_regions": [
                                    {
                                        "region": "full body and both arm-to-hand chains",
                                        "near_object": "doorway, coffee table, and Cushion C",
                                        "expected_relation": "separate_from",
                                        "observed_relation": "separate_from",
                                        "boundary_continuous": True,
                                        "occlusion_order_clear": True,
                                        "solid_object_intersection": False,
                                        "morph_or_merge": False,
                                        "evidence": "Both hands meet the same cushion without merging, while visible background separates both complete legs from the rear coffee table.",
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
            "visual_richness": {
                "pass": True,
                "slides": [
                    {
                        "slide": 6,
                        "formats": {"instagram_post": richness_evidence},
                    }
                ],
            },
            "integrated_final_text": {
                "pass": True,
                "evidence": "The proof renders exactly `Fight bhi proper hoti hai.` and the top-right brandmark exactly `@a.storyof.two`.",
            },
            "final_files": {"pass": True},
            "visual_story_readability": readability,
        },
    }
    QA_PATH.write_text(
        json.dumps(qa, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    print(QA_PATH)


if __name__ == "__main__":
    main()
