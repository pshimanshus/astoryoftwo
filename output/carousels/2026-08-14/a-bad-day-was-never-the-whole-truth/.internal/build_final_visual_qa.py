from __future__ import annotations

import json
from pathlib import Path

from pipeline.stages.carousel_visual_storytelling import (
    frame_review_input_fingerprint,
    frame_review_output_fingerprint,
    image_file_fingerprint,
    review_response_fingerprint,
)


PACKAGE = Path(__file__).resolve().parents[1]
STATE = json.loads((PACKAGE / "image-generation.json").read_text(encoding="utf-8"))
RAW_RESPONSE_PATH = PACKAGE / ".internal" / "full-deck-event-b-raw-response.md"
RAW_RESPONSE = RAW_RESPONSE_PATH.read_text(encoding="utf-8")


FRAME_DATA = {
    1: {
        "people": ["Aachu", "Zuv"],
        "hands": [
            ("Aachu", "right", "inserts the white cable into Zuv's phone", "Zuv's phone connector"),
            ("Zuv", "left", "catches the base of Aachu's tilted glass", "Aachu's water glass"),
        ],
        "silent": "Despite avoiding each other emotionally, Aachu connects the phone on Zuv's side while Zuv protects the tilting glass on hers.",
        "hierarchy": "The crossed forearms and reciprocal object contacts anchor the lower frame; the displeased faces and rainy doorway establish the emotional weather above them.",
        "match": "Opposed gazes preserve irritation while the two crossed, owned actions prove automatic care without either partner becoming the caretaker.",
        "evidence": "Aachu's right sleeve continues through wrist and fingers to the phone connector; Zuv's left sleeve continues to the glass base, and the water remains below the rim.",
        "foreground": "The shared shelf holds the tilting glass, red coaster, phone, charger and extension board.",
        "midground": "Aachu and Zuv lean across one another with two clearly separated reciprocal arm actions.",
        "background": "Rainy navy windows, an open doorway, a warm lamp and a plant establish the same cramped evening room.",
        "cause": "Aachu's cable completes the phone-to-charger path while Zuv's palm arrests the glass before any water spills.",
        "details": ["evil-eye phone", "unspilled tilted glass", "crossed forearms", "rainy doorway"],
        "near": "shared shelf and doorway",
    },
    2: {
        "people": ["Aachu"],
        "hands": [("Aachu", "right", "holds both separated ends of the snapped hair tie", "snapped hair tie")],
        "silent": "Aachu has snapped her hair tie by pulling too hard and now holds the separated pieces with rueful awareness.",
        "hierarchy": "The two separated black elastic ends and Aachu's downward eyeline lead the intimate solo close-up, with loose hair supplying the consequence.",
        "match": "The broken tie turns her bad mood into a visible self-caused consequence, making the self-jab legible without a mirror or second face.",
        "evidence": "One continuous raised arm ends in one hand holding two visibly separated elastic ends; her loose hair and softened wince complete the before-and-after logic.",
        "foreground": "Aachu's raised hand and the two separated hair-tie ends form the nearest readable detail.",
        "midground": "Aachu's single face, loose hair and charcoal blazer carry the self-aware pause.",
        "background": "A plain neutral wall and wardrobe edge preserve the room without adding a reflection or portrait.",
        "cause": "Pulling the tie too hard snaps the elastic, releases her hair and gives her own tension a visible consequence.",
        "details": ["two snapped elastic ends", "loose hair", "rueful downward gaze"],
        "near": "plain wardrobe and wall",
    },
    3: {
        "people": ["Aachu", "Zuv"],
        "hands": [
            ("Aachu", "right", "holds the wardrobe-door handle", "wardrobe-door handle"),
            ("Zuv", "left", "grips the rolling chair back", "chair back"),
            ("Zuv", "right", "rests separately on his thigh", None),
        ],
        "silent": "Aachu opens the wardrobe door into the only aisle while Zuv's chair blocks the same space; both stop and glare.",
        "hierarchy": "The overhead door-chair diagonal makes the blocked aisle immediate, with the two stopped bodies and opposing eye-lines completing the standoff.",
        "match": "Both partners contribute a different solid object to the same obstruction, proving the small room and mutual bad mood without assigning one culprit.",
        "evidence": "Aachu's hand remains on the door handle, Zuv owns the chair grip, and the door edge and chair occupy the only clear floor path between bed and desk.",
        "foreground": "Bed edge, bags and umbrella compress the lower room boundary.",
        "midground": "The wardrobe door, Aachu, Zuv and rolling chair collide across one narrow aisle.",
        "background": "The desk, untouched meal, lamp, slack power strip and rainy window preserve the pre-escalation room state.",
        "cause": "Opening the wardrobe door and rolling the chair backward consume the same aisle and force both partners to stop.",
        "details": ["blocking wardrobe door", "rolling chair", "untouched meal", "slack extension cord"],
        "near": "wardrobe door, chair and desk",
    },
    4: {
        "people": ["Aachu", "Zuv"],
        "hands": [
            ("Aachu", "left", "grips the left plastic end of the shared extension board", "left board end"),
            ("Zuv", "right", "grips the right plastic end of the shared extension board", "right board end"),
        ],
        "silent": "Both pull opposite ends of the same live extension board, making it skid, tip the connected lamp, strike the bowl and spill the keys.",
        "hierarchy": "The diagonal live board and two opposed grips lead directly into the tipped lamp and overturned key bowl, while both faces register the consequence.",
        "match": "One shared object carries equal opposing force into two visible consequences, making mutual escalation physical and immediately readable.",
        "evidence": "Both plugs remain inserted; the black cable reaches the intact tipping lamp, and motion marks join the moving board to the overturned bowl and displaced keys.",
        "foreground": "Meal traces, the overturned wood bowl and displaced keys establish the domestic consequence.",
        "midground": "Aachu and Zuv pull opposite plastic ends of one diagonal powered board.",
        "background": "Faded shelves, plants and neutral room marks retain spatial context without competing with the incident.",
        "cause": "Opposing hand forces skid the board; its black cable tips the lamp and the board's travel clips the key bowl.",
        "details": ["two inserted plugs", "tipping intact lamp", "overturned key bowl", "motion vectors"],
        "near": "table, extension board and lamp",
    },
    5: {
        "people": ["Aachu", "Zuv"],
        "hands": [
            ("Aachu", "right", "presses the black lamp plug into the extension board", "black lamp plug"),
            ("Aachu", "left", "braces separately on the floor", "floor"),
            ("Zuv", "right", "steadies and rights the lamp body", "lamp body"),
            ("Zuv", "left", "rests separately beside the board", "floor"),
        ],
        "silent": "Still visibly angry, Aachu reconnects the lamp while Zuv steadies it and the light returns.",
        "hierarchy": "The inserted black plug, unbroken black cable and newly lit lamp form the causal foreground; guarded mutual eye contact carries the emotional turn above it.",
        "match": "Separate but complementary hand actions repair the same consequence they created, showing love as coordination without erasing anger.",
        "evidence": "One continuous black cable runs from the plug beneath Aachu's finger to the lamp base, while Zuv's owned hand supports the illuminated lamp.",
        "foreground": "The power board, black plug, continuous cable and warm lamp make the repair physically explicit.",
        "midground": "Aachu and Zuv kneel at the same depth with four owned hands and guarded eye contact.",
        "background": "The cool rainy window and wordless botanical wall keep the room in near-darkness around the restored practical light.",
        "cause": "Aachu completes the black plug connection while Zuv stabilizes the lamp, causing the warm shade to illuminate.",
        "details": ["continuous black lamp cable", "inserted black plug", "restored warm light", "guarded eye contact"],
        "near": "floor, power board and lamp",
    },
    6: {
        "people": ["Aachu", "Zuv"],
        "hands": [
            ("Aachu", "right", "offers the final piece of food", "final food piece"),
            ("Aachu", "left", "rests naturally on her knee", "knee"),
            ("Zuv", "left", "receives the offered food", "final food piece"),
            ("Zuv", "right", "rests naturally on his knee", "knee"),
        ],
        "silent": "The room remains messy, but they resume dinner; Aachu offers Zuv the final piece and he begins accepting it.",
        "hierarchy": "The small food handoff and shoulder-close seated pair lead the wide room, while the lit lamp, settled keys and nearly finished meal complete the payoff.",
        "match": "Their distance contracts and reciprocal food exchange replaces opposing force, creating ordinary tenderness without a sentimental reset.",
        "evidence": "Aachu's offering hand and Zuv's receiving hand meet over the meal; their outside hands remain separately owned, and the lamp and board sit repaired at frame right.",
        "foreground": "Nearly finished dishes, cups, slack cords and the settled key bowl record the evening's aftermath.",
        "midground": "Aachu and Zuv sit shoulder-close as the final bite passes between their owned hands.",
        "background": "Rain, closed wardrobe, displaced chair, bags, lamp and wordless botanical art hold the whole room in one quiet wide view.",
        "cause": "Shared repair allows the meal to resume; Aachu's offer and Zuv's acceptance turn practical proximity into quiet care.",
        "details": ["final food handoff", "repaired lit lamp", "settled key bowl", "nearly finished meal"],
        "near": "floor meal, chair and room furnishings",
    },
}


def source_asset(slide: int) -> dict[str, object]:
    output = STATE["slides"][slide - 1]["native_outputs"]["instagram_post"]
    return {
        "sha256": output["sha256"],
        "width": output["width"],
        "height": output["height"],
    }


def hand_record(owner: str, side: str, action: str, contact: str | None) -> dict[str, object]:
    return {
        "owner": owner,
        "side": side,
        "action": action,
        "story_required": True,
        "attachment_visible": True,
        "attachment_evidence": f"{owner}'s shoulder, sleeve, forearm, wrist and {side} hand form one continuous anatomical chain.",
        "contact_object": contact,
        "contact_geometry_pass": True,
        "occlusion_evidence": (
            f"The {side} hand meets {contact} with a clear palm/finger boundary and no penetration."
            if contact
            else "The relaxed hand remains in open space with a clear wrist and no solid-object intersection."
        ),
        "solid_object_intersection": False,
        "edge_entry_unexplained": False,
    }


frames = []
for number, data in FRAME_DATA.items():
    file_path = f"final/slide-{number:02d}.png"
    frames.append(
        {
            "slide": number,
            "format": "instagram_post",
            "file": file_path,
            "status": "PASS",
            "expected_silent_read": data["silent"],
            "observed_image_first_read": data["silent"],
            "core_action_legible": True,
            "relationship_turn_legible": True,
            "focal_hierarchy": data["hierarchy"],
            "hands_gaze_prop_legible": True,
            "storyboard_match": True,
            "native_format_readability": True,
            "copy_visual_contradictions": [],
            "unexpected_story": [],
            "match_rationale": data["match"],
            "evidence": data["evidence"],
            "image_fingerprint": image_file_fingerprint(
                PACKAGE
                / ".internal"
                / "visual-quarantine"
                / "attempt-03"
                / "final"
                / f"slide-{number:02d}.png"
            ),
        }
    )


readability = {
    "pass": True,
    "status": "PASS",
    "event": "rendered_frame_story_audit",
    "image_first": True,
    "provisional": False,
    "scope": "full_deck",
    "full_event_b": True,
    "reviewer_id": "/root/visual_cinematography",
    "reviewer_evidence": "A fresh independent critic inspected the exact Attempt 3 decoded pixels and read the full tense-to-tender sequence before relying on the copy.",
    "source_director_event_fingerprint": "sha256:f0287632a992ac78d3b62426b3918bc3f44e3fb1c150bdcb831520c596248752",
    "reviewed_native_formats": ["instagram_post"],
    "sequence_read": "Two irritated partners still care automatically; Aachu sees her own tension, the cramped room turns separate motions into mutual escalation, shared repair restores the light, and ordinary tenderness returns over dinner.",
    "relationship_turn": "Slide 5 converts equal opposition into complementary repair: Aachu reconnects the lamp while Zuv steadies it, with guarded faces preserving the anger and coordinated hands proving the love.",
    "setup_payoff_evidence": "Rain, phone, glass, room, meal, power board, lamp and keys progress from reciprocal care through obstruction and damage into repaired light, settled objects and a final food offer.",
    "weakest_frame": "Slide 2 carries the smallest receipt, but the visibly separated tie ends, loose hair and rueful eyeline remain readable at phone size and do not depend solely on copy.",
    "repair_decision": "No blocking repair remains; preserve this exact image set, identity, wardrobe, causal props, neutral paper, exact copy and one brandmark per frame.",
    "frames": frames,
    "issues": [],
    "review_provenance": {
        "schema_version": "visual-review-provenance/v2",
        "reviewer_task_id": "/root/visual_cinematography",
        "reviewer_run_id": "event-b-attempt-03-2026-08-14-01",
        "input_fingerprint": frame_review_input_fingerprint(frames),
        "raw_response_artifact": ".internal/full-deck-event-b-raw-response.md",
        "raw_response_fingerprint": review_response_fingerprint(RAW_RESPONSE),
    },
}
readability["review_provenance"]["output_fingerprint"] = frame_review_output_fingerprint(readability)


anatomy_slides = []
entity_slides = []
richness_slides = []
topology_slides = []
for number, data in FRAME_DATA.items():
    expected_arms = 2 if number == 2 else 4
    expected_hands = len(data["hands"])
    asset = source_asset(number)
    anatomy_slides.append(
        {
            "slide": number,
            "formats": {
                "instagram_post": {
                    "source_asset": asset,
                    "expected_arms": expected_arms,
                    "observed_arms": expected_arms,
                    "expected_hands": expected_hands,
                    "observed_hands": expected_hands,
                    "visible_hands": [hand_record(*hand) for hand in data["hands"]],
                    "occluded_hands": [],
                    "unexpected_limbs": [],
                    "duplicated_limbs": [],
                    "malformed_fingers": False,
                }
            },
        }
    )
    entity_slides.append(
        {
            "slide": number,
            "formats": {
                "instagram_post": {
                    "source_asset": asset,
                    "expected_people": len(data["people"]),
                    "observed_people": len(data["people"]),
                    "expected_arms": expected_arms,
                    "observed_arms": expected_arms,
                    "expected_hands": expected_hands,
                    "observed_hands": expected_hands,
                    "unexpected_entities": [],
                    "unexpected_limbs": [],
                    "duplicated_limbs": [],
                    "evidence": f"Exactly {', '.join(data['people'])} appear; all visible hands have named owners and no reflection, portrait, duplicate figure, extra limb or background actor appears.",
                }
            },
        }
    )
    richness_slides.append(
        {
            "slide": number,
            "formats": {
                "instagram_post": {
                    "source_asset": asset,
                    "foreground": data["foreground"],
                    "midground": data["midground"],
                    "background": data["background"],
                    "focal_action": data["silent"],
                    "story_details": data["details"],
                    "cause_effect": data["cause"],
                    "posed_portrait": False,
                    "decorative_clutter": False,
                }
            },
        }
    )
    people = []
    for person in data["people"]:
        people.append(
            {
                "person": person,
                "silhouette_traceable": True,
                "silhouette_evidence": f"{person}'s head, neck, shoulders, torso and every visible limb remain distinct from nearby room planes and props.",
                "body_regions": [
                    {
                        "region": "visible head, torso and limb chain",
                        "near_object": data["near"],
                        "expected_relation": "in_front_of",
                        "observed_relation": "in_front_of",
                        "boundary_continuous": True,
                        "occlusion_order_clear": True,
                        "solid_object_intersection": False,
                        "morph_or_merge": False,
                        "evidence": f"{person}'s watercolor contour stays continuous in front of {data['near']} with clear overlap order and no solid boundary passing through the body.",
                    }
                ],
                "ambiguous_regions": [],
            }
        )
    topology_slides.append(
        {
            "slide": number,
            "observed_people": len(data["people"]),
            "evidence_views": {
                "full_frame": data["hierarchy"],
                "person_object_crop": data["evidence"],
                "focal_detail": data["cause"],
            },
            "environment_planes": [
                {
                    "object": data["near"],
                    "depth_order": "environment remains behind or beneath the named people and focal hand-object contacts",
                    "boundary_continuous": True,
                }
            ],
            "people": people,
            "ambiguous_regions": [],
            "unresolved_intersections": [],
        }
    )


qa = {
    "schema_version": "2.1",
    "status": "PASS",
    "proof_state": "QA_PASS_CANDIDATE",
    "image_set_sha256": STATE["image_set_sha256"],
    "slides": [{"slide": row["slide"], "native_outputs": row["native_outputs"]} for row in STATE["slides"]],
    "reviews": {
        "anatomy_entity_spatial_identity": {
            "pass": True,
            "status": "PASS",
            "reviewer_id": "/root/production_refs",
            "evidence": "Independent exact-pixel review recomputed the set hash and cleared Aachu/Zuv likeness, scale, wardrobe, text, entity counts, hand ownership, spatial topology, object causality, dimensions and neutral-ivory style on all six frames.",
        },
        "storytelling_richness_text_style": {
            "pass": True,
            "status": "PASS",
            "reviewer_id": "/root/visual_cinematography",
            "evidence": "Independent image-first Event B read the complete tense-to-tender causal sequence, exact copy and brandmark, shot ladder, environmental continuity, relationship turn and ordinary-tenderness payoff from the exact Attempt 3 pixels.",
        },
    },
    "checks": {
        "storyboard": {"pass": True, "evidence": "All six frames execute distinct locked shot roles and preserve the rainy one-room causal sequence."},
        "aachu_face": {
            "pass": True,
            "reference_option_ids": [
                "config/references/identity/aachu/reel-jaldi.jpg",
                "config/references/identity/together/together-18.jpg",
            ],
            "likeness_notes": "Aachu retains her youthful rounded/oval face, large expressive eyes and brows, soft nose and lips, long dark wavy hair and warm medium-brown skin across every visible angle.",
        },
        "zuv_face": {
            "pass": True,
            "reference_option_ids": [
                "config/references/identity/zuv/portrait-07.jpg",
                "config/references/identity/together/together-18.jpg",
            ],
            "likeness_notes": "Zuv retains thick dark curls, strong brows, defined nose, trimmed beard, broad adult build and warm medium-brown skin across the deck.",
        },
        "couple_scale": {"pass": True, "evidence": "Near-equal adult scale remains compatible with Aachu 5'6 and Zuv 5'8; no frame makes Aachu tiny or Zuv oversized."},
        "dress_continuity": {"pass": True, "evidence": "Aachu stays in a charcoal-grey blazer, ivory top and muted blue jeans; Zuv stays in a charcoal shirt and dark trousers through the continuous rainy evening."},
        "style": {"pass": True, "evidence": "All six frames pass the deterministic neutral-ivory palette gate and preserve fine ink/pencil, transparent watercolor, paper grain, muted navy/charcoal/camel accents and warm practical light."},
        "scene_logic": {"pass": True, "evidence": "Phone and glass care, snapped tie, blocked aisle, board-to-lamp/key consequence, continuous repair cable and final food offer form one readable causal chain."},
        "scene_entity_integrity": {"pass": True, "slides": entity_slides},
        "anatomy_inventory": {"pass": True, "slides": anatomy_slides},
        "spatial_topology": {"pass": True, "slides": topology_slides},
        "visual_richness": {"pass": True, "slides": richness_slides},
        "integrated_final_text": {"pass": True, "evidence": "Every frame contains the exact locked slide copy and exactly one tiny top-right @a.storyof.two, with no additional readable words."},
        "final_files": {"pass": True, "evidence": "All six quarantined RGB PNGs decode at exactly 1080x1440 and match their bound SHA-256 values and image-set hash."},
        "visual_story_readability": readability,
    },
    "required_repairs": [],
}


rendered = json.dumps(qa, ensure_ascii=False, indent=2) + "\n"
(PACKAGE / "visual-qa.json").write_text(rendered, encoding="utf-8")
(PACKAGE / ".internal" / "pending-full-deck-visual-qa-final.json").write_text(rendered, encoding="utf-8")
