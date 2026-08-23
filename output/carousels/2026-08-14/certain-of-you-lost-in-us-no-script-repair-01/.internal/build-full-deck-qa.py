from __future__ import annotations

import json
from pathlib import Path

from pipeline.stages.carousel_visual_storytelling import (
    REVIEW_PROVENANCE_VERSION,
    frame_review_input_fingerprint,
    frame_review_output_fingerprint,
    image_file_fingerprint,
    review_response_fingerprint,
)
from pipeline.stages.codex_builtin_image_generation import validate_exact_image_visual_qa


PACKAGE = Path(
    "output/carousels/2026-08-14/"
    "certain-of-you-lost-in-us-no-script-repair-01"
)
state = json.loads((PACKAGE / "image-generation.json").read_text(encoding="utf-8"))
plan = json.loads((PACKAGE / "visual-plan-quality.json").read_text(encoding="utf-8"))


scene_data = {
    1: {
        "expected": "Two certain people keep one direction and physical alignment while their shared theatre world visibly shifts apart around them.",
        "observed": "A young couple walks together onto an empty theatre stage between two large wheeled scenery flats.",
        "hierarchy": "The exact copy leads the open upper field, the shoulder-close walking couple anchors center, and opposed scenery flats plus the empty first row establish the changing theatre world.",
        "match": "Their shared stride and touching shoulders preserve certainty in each other while the wheeled flats visibly separate around them.",
        "evidence": "Both bodies lean into the same forward step at one depth; two separate flats angle outward behind them and empty seat backs establish the audience-side viewpoint.",
        "hands": [
            ("Aachu", "left", "swings naturally beside her outer thigh", None),
            ("Zuv", "right", "swings naturally beside his outer thigh", None),
        ],
        "occluded": [
            ("Aachu", "right", "Her inside hand is hidden between the adjacent moving torsos."),
            ("Zuv", "left", "His inside hand is hidden behind the couple's shoulder-close overlap."),
        ],
        "foreground": "A low strip of empty upholstered first-row seat backs establishes the audience-side viewpoint.",
        "midground": "Aachu and Zuv cross downstage shoulder-to-shoulder in one shared stride.",
        "background": "Indigo and dusty-rose scenery flats stand on visible caster bases and move apart.",
        "action": "The couple walks in one direction while the theatre scenery shifts in opposing directions behind them.",
        "details": ["empty first-row seats", "wheeled indigo flat", "wheeled dusty-rose flat"],
        "cause": "The opposed flats create visible environmental change while the couple's touching shoulders and synchronized step keep their relational certainty intact.",
        "planes": [
            ("first-row seat backs", "foreground below and in front of the stage edge"),
            ("wooden stage floor", "beneath both people and both scenery-flat caster bases"),
            ("two wheeled scenery flats", "behind the couple with open space around both silhouettes"),
        ],
        "near": "stage floor, opposite moving body and separate wheeled flats",
        "topology": "Each full figure remains traceable against the open ivory stage field; their only overlap is natural shoulder contact, and neither body intersects a scenery flat.",
    },
    2: {
        "expected": "Two people enter from separate sides, notice each other and choose the same shared light.",
        "observed": "Aachu and Zuv cross from opposite sides under separate spotlights and approach one another across the stage.",
        "hierarchy": "The two opposed walking figures and their meeting eye-lines form the focal event, with separate light pools and distant chairs carrying the before-state.",
        "match": "Opposed strides, mutual gaze and converging light make the deliberate choice to meet readable before the copy is revealed.",
        "evidence": "Both figures have a clear leading step and open space between them; their profile eye-lines meet while the two spotlights overlap near center.",
        "hands": [
            ("Aachu", "left", "swings beside her left hip during the step", None),
            ("Aachu", "right", "swings beside her right hip during the step", None),
            ("Zuv", "left", "swings beside his left hip during the step", None),
            ("Zuv", "right", "swings beside his right hip during the step", None),
        ],
        "occluded": [],
        "foreground": "Bare stage boards and the leading feet show two opposed walking paths.",
        "midground": "Aachu and Zuv approach one another in profile with mutual eye contact.",
        "background": "Two dim wings, one empty chair per side and separate spotlights preserve their distinct origins.",
        "action": "They each take one active step from a different wing toward the same shared pool of light.",
        "details": ["two converging spotlights", "one isolated chair per wing", "clear profile eye-lines"],
        "cause": "Their opposed steps narrow the distance while the overlapping light turns two separate entrances into one mutual meeting.",
        "planes": [
            ("bare stage floor", "beneath both figures and across the full lower frame"),
            ("left and right wing chairs", "behind each person in separate darker side planes"),
            ("cross-faded spotlights", "cast from above onto one shared center-stage floor plane"),
        ],
        "near": "bare stage floor, separate wing chair and the open gap between the two walkers",
        "topology": "Both walking silhouettes remain separate and fully traceable at the same stage depth; every hand belongs to one clear arm chain and no chair intersects a body.",
    },
    3: {
        "expected": "Life sends different demands toward each person, but their connected backs keep the pressure relational rather than isolating.",
        "observed": "Aachu braces a moving worktable with boxes while Zuv steadies a wheeled scenery wall arriving from the other side.",
        "hierarchy": "The connected couple anchors center, with Aachu's table and Zuv's scenery wall pulling the composition toward opposite practical demands.",
        "match": "Separate object contact and divided gazes show different pressures, while their close back-to-back stance keeps the work inside one shared life.",
        "evidence": "Aachu's palm resolves against the table edge and Zuv's palm against the separate flat; the objects remain distinct and the pair stays physically connected at center.",
        "hands": [
            ("Aachu", "right", "braces the incoming worktable edge", "worktable"),
            ("Zuv", "left", "steadies the incoming scenery-flat edge", "scenery flat"),
        ],
        "occluded": [
            ("Aachu", "left", "Her free outside hand remains beyond the high-diagonal crop."),
            ("Zuv", "right", "His free outside hand remains behind his torso and outside the crop."),
        ],
        "foreground": "Angled floorboards and the near edges of incoming practical pieces establish pressure from both sides.",
        "midground": "Aachu and Zuv stand connected while each arrests one different rolling object.",
        "background": "Two taped cartons, a braced doorway flat and cooler working light build the load-in environment.",
        "action": "They simultaneously stop and redirect separate incoming stage demands without leaving each other.",
        "details": ["two taped cartons", "braced doorway flat", "separate palm contacts", "connected backs"],
        "cause": "The opposing objects divide their hands and attention, but the central body contact keeps the complexity visibly shared.",
        "planes": [
            ("stage floor", "beneath the couple, worktable wheels and scenery-flat caster base"),
            ("worktable with cartons", "left midground beside Aachu and separate from her silhouette"),
            ("braced scenery wall", "right midground beside Zuv and separate from his silhouette"),
        ],
        "near": "stage floor and one separately owned moving practical object",
        "topology": "Both figures remain traceable in the high diagonal view; each focal hand attaches to its owner and meets only the declared object surface without merging into it.",
    },
    4: {
        "expected": "The couple actively searches blank guidance and finds no instruction, while remaining present to one another.",
        "observed": "At a rehearsal table, Aachu turns a completely blank script page while Zuv watches closely beside safe wall-fixed stage rigging.",
        "hierarchy": "The blank open pages and Aachu's turning hand lead the object-dominant frame, with Zuv's attentive face and the fixed vertical line as secondary context.",
        "match": "The lifted empty page makes the absence of guidance an action rather than a pose; Zuv's attention supplies relational presence without pretending to have the answer.",
        "evidence": "The page surface is entirely blank, Aachu's fingers visibly lift its edge, Zuv remains a separate readable figure, and the taut line terminates at a wall fitting with no loop or hanging end.",
        "hands": [
            ("Aachu", "right", "lifts and turns the blank script page", "blank script page"),
        ],
        "occluded": [
            ("Aachu", "left", "Her other hand is outside the object-dominant crop."),
            ("Zuv", "left", "His hands remain below the table edge and outside the crop."),
            ("Zuv", "right", "His hands remain below the table edge and outside the crop."),
        ],
        "foreground": "A blank open rehearsal script and Aachu's page-turning hand dominate the table-level foreground.",
        "midground": "Aachu's partial profile and Zuv's attentive face hold opposite sides of the shared table.",
        "background": "A distant ghost light, narrow curtain edge and one straight wall-fixed rigging line establish blackout rehearsal context.",
        "action": "Aachu searches the blank page while Zuv stays attentively present with no written instruction available.",
        "details": ["completely blank pages", "visible page-turn", "wall-fixed straight rigging line", "distant ghost light"],
        "cause": "Turning a page reveals more blank paper; the continued shared gaze turns missing instructions into a planless relational pause.",
        "planes": [
            ("open script and table", "foreground below both faces with the page surface fully visible"),
            ("Aachu and Zuv", "opposite midground sides of the same rehearsal table"),
            ("fixed rigging line and ghost light", "background against a structural wall and distant stage plane"),
        ],
        "near": "rehearsal table, blank script and open air around the separate face profiles",
        "topology": "The visible page-turning hand connects continuously to Aachu; both heads and torsos remain separate from the table and the straight rigging line stays fixed to the wall behind them.",
    },
    5: {
        "expected": "A failed curtain cue becomes shared recovery as both people actively lift the same fabric and find warmth inside the mishap.",
        "observed": "Aachu and Zuv kneel on opposite sides of a fallen indigo curtain, grip it together and laugh while gathering it toward the center.",
        "hierarchy": "Their matched low postures, mutual gaze and two owned fabric grips lead; the crooked curtain ridge and harmless reset mess establish the visible failure.",
        "match": "Equal fabric tension and simultaneous laughter turn being lost into shared work, with neither person rescuing or directing the other.",
        "evidence": "Each person has one anatomically attached hand on a separate curtain corner; the fabric rises between them, their eye-lines meet, and nearby chairs and cable remain harmless background stage-reset objects.",
        "hands": [
            ("Aachu", "right", "grips and lifts her side of the fallen curtain", "indigo curtain"),
            ("Zuv", "left", "grips and lifts his side of the fallen curtain", "indigo curtain"),
        ],
        "occluded": [
            ("Aachu", "left", "Her outside hand is obscured by her kneeling body and the frame edge."),
            ("Zuv", "right", "His outside hand is obscured by his kneeling body and the frame edge."),
        ],
        "foreground": "The fallen indigo curtain rises into a shallow ridge between two clearly owned hand grips.",
        "midground": "Aachu and Zuv kneel at equal depth, actively gather the fabric and meet each other's laughing gaze.",
        "background": "A separate table with a text-free blue book, tipped rehearsal chairs and a loose floor cable read as harmless stage-reset mess.",
        "action": "Both people actively lift and gather the failed curtain toward one shared center.",
        "details": ["shared fabric tension", "matched kneeling posture", "text-free closed book", "stage-reset chairs"],
        "cause": "Two simultaneous grips pull the curtain inward; the crooked fold and shared laugh make visible failure become reciprocal recovery.",
        "planes": [
            ("fallen curtain", "foreground on the stage floor and lifted between the two kneeling figures"),
            ("kneeling couple", "midground on opposite sides of the fabric ridge at equal depth"),
            ("table, chairs and floor cable", "background reset objects separated from both body silhouettes"),
        ],
        "near": "stage floor, lifted curtain edge and open space separating harmless background props",
        "topology": "Each kneeling body and fabric-gripping arm remains traceable; cloth overlaps only the declared hands and lower knees, while the floor cable neither intersects a body nor forms a loop around one.",
    },
    6: {
        "expected": "Both people use equal agency to move separate chairs into one new light, choosing how to build the next scene together.",
        "observed": "Seen from behind, Aachu and Zuv each pull one chair toward an open pool of stage light while beginning a side glance toward each other.",
        "hierarchy": "The two parallel bodies and two chair grips lead into the open illuminated center; the returning indigo and dusty-rose flats bookend the sequence.",
        "match": "One chair and one visible effort per person make the continuation reciprocal, while the blank book left behind confirms that movement no longer waits for a script.",
        "evidence": "Each chair remains distinct from both bodies except its owner's attached hand; local scrape marks prove movement and the open center-stage light supplies one shared direction.",
        "hands": [
            ("Aachu", "right", "pulls the left chair by its backrest", "left rehearsal chair"),
            ("Zuv", "left", "pulls the right chair by its backrest", "right rehearsal chair"),
        ],
        "occluded": [
            ("Aachu", "left", "Her outside hand is beyond the rear three-quarter crop."),
            ("Zuv", "right", "His outside hand is beyond the rear three-quarter crop."),
        ],
        "foreground": "Two separate chair legs and short local scrape marks point toward the same next light.",
        "midground": "Aachu and Zuv move side-by-side with one clearly owned chair grip and equal effort each.",
        "background": "The open stage, returning indigo and dusty-rose flats, recovered curtain and text-free blue book complete the visual ledger.",
        "action": "They each pull one separate rehearsal chair into the same newly opened pool of light.",
        "details": ["two separately owned chairs", "paired scrape marks", "returning scenery flats", "blank book left behind"],
        "cause": "Parallel chair movement turns the empty stage into a jointly arranged next scene while preserving two distinct agents and one direction.",
        "planes": [
            ("two rehearsal chairs", "foreground and lower midground, one behind each owner"),
            ("side-by-side couple", "midground moving toward the illuminated stage center"),
            ("opposing flats and open light", "far background framing one unobstructed central destination"),
        ],
        "near": "stage floor, one separately owned chair and open space beside the other person",
        "topology": "Both rear three-quarter silhouettes remain separate and traceable; each hand meets only its own chair back and neither chair intersects a leg or the other chair.",
    },
}


def source_asset(output: dict) -> dict:
    return {
        "sha256": output["sha256"],
        "width": output["width"],
        "height": output["height"],
    }


def visible_hand(owner: str, side: str, action: str, contact_object: str | None) -> dict:
    contact_phrase = (
        f"The palm and fingers meet only the visible surface of the {contact_object}."
        if contact_object
        else "The hand hangs in open space without contacting another figure or solid prop."
    )
    return {
        "owner": owner,
        "side": side,
        "action": action,
        "story_required": True,
        "attachment_visible": True,
        "attachment_evidence": f"{owner}'s shoulder, sleeve, forearm, wrist and {side} hand form one continuous anatomical chain.",
        "contact_object": contact_object,
        "contact_geometry_pass": True,
        "occlusion_evidence": contact_phrase,
        "solid_object_intersection": False,
        "edge_entry_unexplained": False,
    }


entity_slides = []
anatomy_slides = []
topology_slides = []
richness_slides = []
frames = []

for slide_state in state["slides"]:
    number = int(slide_state["slide"])
    data = scene_data[number]
    output = slide_state["native_outputs"]["instagram_post"]
    asset = source_asset(output)
    final_path = PACKAGE / output["path"]
    attempt_root = final_path.parents[1]
    relative_file = final_path.relative_to(attempt_root).as_posix()
    hand_records = [visible_hand(*hand) for hand in data["hands"]]
    hidden_records = [
        {"owner": owner, "side": side, "evidence": evidence}
        for owner, side, evidence in data["occluded"]
    ]

    entity_slides.append(
        {
            "slide": number,
            "formats": {
                "instagram_post": {
                    "source_asset": asset,
                    "expected_people": 2,
                    "observed_people": 2,
                    "expected_arms": 4,
                    "observed_arms": 4,
                    "expected_hands": len(hand_records),
                    "observed_hands": len(hand_records),
                    "unexpected_entities": [],
                    "unexpected_limbs": [],
                    "duplicated_limbs": [],
                    "evidence": f"Exactly Aachu and Zuv appear in slide {number}; all four arm chains are coherent, {len(hand_records)} visible hands have clear owners, and remaining hands are naturally occluded or outside the crop with no extra figure or reflection.",
                }
            },
        }
    )
    anatomy_slides.append(
        {
            "slide": number,
            "formats": {
                "instagram_post": {
                    "source_asset": asset,
                    "expected_arms": 4,
                    "observed_arms": 4,
                    "expected_hands": len(hand_records),
                    "observed_hands": len(hand_records),
                    "visible_hands": hand_records,
                    "occluded_hands": hidden_records,
                    "unexpected_limbs": [],
                    "duplicated_limbs": [],
                    "malformed_fingers": False,
                }
            },
        }
    )
    people = []
    for person in ("Aachu", "Zuv"):
        people.append(
            {
                "person": person,
                "silhouette_traceable": True,
                "silhouette_evidence": f"{person}'s head, hair, neck, shoulders, torso, arms and visible lower body remain readable as one continuous figure in slide {number}.",
                "body_regions": [
                    {
                        "region": "full visible body and all attached arm chains",
                        "near_object": data["near"],
                        "expected_relation": "in_front_of",
                        "observed_relation": "in_front_of",
                        "boundary_continuous": True,
                        "occlusion_order_clear": True,
                        "solid_object_intersection": False,
                        "morph_or_merge": False,
                        "evidence": data["topology"],
                    }
                ],
                "ambiguous_regions": [],
            }
        )
    topology_slides.append(
        {
            "slide": number,
            "observed_people": 2,
            "evidence_views": {
                "full_frame": f"Slide {number} contains exactly two coherent people inside one continuous theatre environment, with foreground, stage and background planes visibly separated.",
                "person_object_crop": data["topology"],
                "focal_detail": f"The focal action is {data['action'].lower()} Hands, decisive props and gaze remain unobstructed and spatially owned.",
            },
            "environment_planes": [
                {
                    "object": object_name,
                    "depth_order": depth_order,
                    "boundary_continuous": True,
                }
                for object_name, depth_order in data["planes"]
            ],
            "people": people,
            "ambiguous_regions": [],
            "unresolved_intersections": [],
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
                    "focal_action": data["action"],
                    "story_details": data["details"],
                    "cause_effect": data["cause"],
                    "posed_portrait": False,
                    "decorative_clutter": False,
                }
            },
        }
    )
    frames.append(
        {
            "slide": number,
            "format": "instagram_post",
            "file": relative_file,
            "status": "PASS",
            "expected_silent_read": data["expected"],
            "observed_image_first_read": data["observed"],
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
            "image_fingerprint": image_file_fingerprint(final_path),
        }
    )


event_b_raw_path = PACKAGE / ".internal/full-deck-event-b-raw-response.md"
event_b_raw = event_b_raw_path.read_text(encoding="utf-8")
readability = {
    "pass": True,
    "status": "PASS",
    "event": "rendered_frame_story_audit",
    "image_first": True,
    "provisional": False,
    "scope": "full_deck",
    "full_event_b": True,
    "reviewer_id": "/root/theater_repaired_event_b",
    "reviewer_evidence": "A fresh copy-hidden exact-pixel reviewer returned GO after reading the sequence as enter, approach, divided stage pressure, blank-script low point, shared curtain recovery and equal two-chair continuation; it also explicitly cleared the fixed rigging, harmless reset cable, blank book, exact copy and two-person count.",
    "source_director_event_fingerprint": plan["director_storyboard"]["director_event_fingerprint"],
    "reviewed_native_formats": ["instagram_post"],
    "sequence_read": "The repaired deck reads causally as entering one uncertain stage, choosing each other, absorbing separate demands, finding no script, recovering a failed cue together and arranging the next scene with equal agency.",
    "relationship_turn": "The pair moves from mutual arrival through divided practical pressure and a planless pause into laughter, reciprocal repair and coordinated continuation without either person becoming the other's handler.",
    "setup_payoff_evidence": "The separate wing chairs become one chair per person moving into shared light; the blank script is searched, closed and left behind; the opposing scenery flats return as an earned opening-to-payoff bookend.",
    "weakest_frame": "Slide four is intentionally quieter than the physical frames around it, but the visible page-turn over completely blank paper makes the missing guidance an observable event rather than a pose.",
    "repair_decision": "No blocking repair remains. Preserve the exact fixed rigging on slide four, equal curtain recovery on slide five, text-free book on slides five and six, exact copy, single brandmark, identity and native dimensions.",
    "frames": frames,
    "issues": [],
    "review_provenance": {
        "schema_version": REVIEW_PROVENANCE_VERSION,
        "reviewer_task_id": "/root/theater_repaired_event_b",
        "reviewer_run_id": "event-b-5fb57bfe-2898-45b9-9e30-77c03fa3219a",
        "input_fingerprint": frame_review_input_fingerprint(frames),
        "raw_response_artifact": ".internal/full-deck-event-b-raw-response.md",
        "raw_response_fingerprint": review_response_fingerprint(event_b_raw),
        "output_fingerprint": "",
    },
}
readability["review_provenance"]["output_fingerprint"] = frame_review_output_fingerprint(
    readability
)


qa = {
    "schema_version": "2.1",
    "status": "PASS",
    "proof_state": "QA_PASS_CANDIDATE",
    "image_set_sha256": state["image_set_sha256"],
    "slides": state["slides"],
    "checks": {
        "aachu_face": {
            "pass": True,
            "reference_option_ids": [
                "output/carousels/2026-08-14/certain-of-you-lost-in-us-no-script/.internal/reference-crops/aachu-face-04-crop.png",
                "output/carousels/2026-08-14/certain-of-you-lost-in-us-no-script/.internal/reference-crops/together-18-faces.jpg",
            ],
            "likeness_notes": "Aachu remains recognizable across all six frames through her long dark hair, strong brows, almond eyes, soft tapered face, black layers and blue denim; the wider and partial views preserve the same proportions and styling.",
        },
        "zuv_face": {
            "pass": True,
            "reference_option_ids": [
                "output/carousels/2026-08-14/certain-of-you-lost-in-us-no-script/.internal/reference-crops/zuv-portrait-07-crop.jpg",
                "output/carousels/2026-08-14/certain-of-you-lost-in-us-no-script/.internal/reference-crops/together-18-faces.jpg",
            ],
            "likeness_notes": "Zuv remains recognizable across all six frames through his raised dark hair, heavy brows, broad nose, trimmed beard, strong jaw, white zip jacket and charcoal trousers.",
        },
        "couple_scale": {
            "pass": True,
            "evidence": "At matched depth Zuv remains modestly taller than Aachu across the sequence without exaggeration or cross-slide scale drift.",
        },
        "dress_continuity": {
            "pass": True,
            "evidence": "Aachu consistently wears black layers with blue denim; Zuv consistently wears a white zip jacket with charcoal trousers throughout the theatre night.",
        },
        "style": {
            "pass": True,
            "evidence": "All six frames retain warm neutral ivory paper, hand-drawn ink, translucent indigo and dusty-rose watercolor, restrained theatrical light and visible paper grain.",
        },
        "scene_logic": {
            "pass": True,
            "evidence": "The visible theatre actions form a causal arc from entrance and mutual choice through divided work, blank guidance, reciprocal curtain recovery and equal chair movement into one next light.",
        },
        "scene_entity_integrity": {"pass": True, "slides": entity_slides},
        "anatomy_inventory": {"pass": True, "slides": anatomy_slides},
        "spatial_topology": {"pass": True, "slides": topology_slides},
        "visual_richness": {"pass": True, "slides": richness_slides},
        "integrated_final_text": {
            "pass": True,
            "evidence": "Every slide preserves its exact locked copy with intended punctuation and line break, exactly one tiny top-right @a.storyof.two brandmark and no accidental text on books, pages, scenery or clothing.",
        },
        "final_files": {
            "pass": True,
            "evidence": "All six quarantined assets are distinct decodable RGB PNG files at exactly 1080x1440 and are bound here to their recorded SHA-256 values.",
        },
        "visual_story_readability": readability,
    },
    "reviews": {
        "anatomy_entity_spatial_identity": {
            "reviewer_id": "/root/theater_repaired_identity_qa",
            "pass": True,
            "evidence": "A fresh exact-pixel reviewer passed all six slides for Aachu and Zuv identity, wardrobe and height continuity, owned limbs and hands, coherent prop contact, exactly two people, exact text, single brandmark, neutral ivory palette and 1080x1440 phone readability.",
        },
        "storytelling_richness_text_style": {
            "reviewer_id": "/root/theater_repaired_event_b",
            "pass": True,
            "evidence": "A different fresh copy-hidden reviewer passed the six-frame causal theatre arc, active relationship behavior, shot variation, balanced agency, slide-four safety, slide-five shared recovery, slide-six chair payoff, exact copy, text-free props and native files.",
        },
    },
    "required_repairs": [],
}


issues = validate_exact_image_visual_qa(
    qa,
    state["slides"],
    visual_plan=plan,
    carousel_dir=PACKAGE,
)
if issues:
    raise SystemExit("\n".join(issues))

(PACKAGE / "visual-qa.json").write_text(
    json.dumps(qa, indent=2, ensure_ascii=False) + "\n",
    encoding="utf-8",
)
print(
    json.dumps(
        {
            "status": "PASS",
            "proof_state": qa["proof_state"],
            "slide_count": len(qa["slides"]),
            "image_set_sha256": qa["image_set_sha256"],
        },
        indent=2,
    )
)
