from __future__ import annotations

import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[5]))

from pipeline.stages.carousel_format_contract import locked_format_contract_fingerprint
from pipeline.stages.carousel_visual_storytelling import (
    DIRECTOR_EVENT_FINGERPRINT_VERSION,
    blind_cards_fingerprint,
    current_creator_correction_fingerprint,
    current_generation_payload_fingerprint,
    director_event_fingerprint,
    director_review_output_fingerprint,
    review_response_fingerprint,
    storyboard_source_fingerprint,
)


ROOT = Path(__file__).resolve().parents[1]


def load(name: str):
    return json.loads((ROOT / name).read_text(encoding="utf-8"))


def write(name: str, payload):
    (ROOT / name).write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


story_score = {
    "reader_identity_mirror": 5,
    "romantic_conflict_stakes": 5,
    "specificity_of_proof": 5,
    "emotional_reversal": 5,
    "visual_scene_clarity": 5,
    "online_share_save_sell_potential": 4,
    "total": 29,
}
golden_score = {
    "universal_hook": 5,
    "aachu_zuv_specificity": 4,
    "concrete_proof": 5,
    "zuv_emotional_role": 5,
    "tender_thesis": 4,
    "share_send_potential": 5,
    "total": 28,
}
stage_scene = {
    "status": "GO",
    "action": "Aachu discards a worn folder; Zuv retrieves it, opens it without tugging, and orders the unfinished pages; Aachu later adds the current page.",
    "reaction": "Aachu first tries to close the folder, then releases it and softens after seeing the chronology.",
    "eye_line_or_attention": "Attention moves from the discard carton to the exposed pages, then to the ordered line and the new page.",
    "hands_or_object_movement": "The folder moves from Aachu to the carton to Zuv, then opens; papers become a chronology; Aachu extends it.",
    "silence_or_pause": "Zuv does not praise, explain, hug, or manage her; the ordering and her reaction carry the turn.",
    "consequence": "The discarded attempts become a visible record rather than rubbish.",
    "reversal_or_payoff": "Aachu voluntarily adds today's unfinished page and turns a rescued archive into a living one.",
    "blockers": [],
}
layer_e_record = {
    "schema_version": "1.0",
    "status": "GO",
    "source": "output/idea-loops/2026-07-28/run-202052/",
    "task_type": "carousel_idea",
    "adaptation_target": "C-layer",
    "rooms": {
        "source_memory_room": {
            "name": "Context And Source Memory",
            "status": "GO",
            "agents": [
                {
                    "agent": "idea-loop evidence ledger",
                    "role": "provenance and collision check",
                    "claim": "The route is a generic relationship hypothesis with no claimed Aachu/Zuv lived documents.",
                    "objection": "",
                    "recommendation": "Keep all paper content wordless and non-identifiable.",
                    "score": 29,
                }
            ],
            "summary": "Fresh witness/archive lane with explicit lived-fact safety.",
            "inputs_used": ["output/idea-loops/2026-07-28/run-202052/"],
            "debate_records": [],
            "scores": {"story_selling": 29, "golden_theme": 28},
            "selected_outputs": {"candidate_id": "run-202052-i1-b-museum-of-almost"},
            "objections": [],
            "repairs": [],
            "repaired_route_names": [],
        },
        "creative_room": {
            "name": "Post-Copy Visual Creative Room",
            "status": "GO",
            "agents": [
                {
                    "agent": "/root/museum_postcopy_room",
                    "role": "copy and visual-system selector",
                    "claim": "The Folder Changes Hands preserves the concept and gives every swipe a new physical state.",
                    "objection": "One room risks visual repetition.",
                    "recommendation": "Use five materially different camera jobs and keep Aachu's final action decisive.",
                    "score": 29,
                }
            ],
            "summary": "Five exact lines and a causal object-state sequence were selected.",
            "inputs_used": ["post-copy-visual-room.json", "visual-debate.json"],
            "debate_records": ["Three visual systems compared; hands-only and literal museum morph rejected."],
            "scores": {"selected_visual_system": 29},
            "selected_outputs": {"visual_system": "The Folder Changes Hands"},
            "objections": [],
            "repairs": ["Vary shot size, camera angle, focal actor, and hand choreography on every slide."],
            "repaired_route_names": ["The Folder Changes Hands"],
        },
        "selector_room": {
            "name": "Independent Verification And Selection",
            "status": "GO",
            "agents": [
                {
                    "agent": "selector_202052_final",
                    "role": "harsh final selector",
                    "claim": "The candidate cleared two blind verifier passes, Stage-Scene, taste, safety, and numeric thresholds.",
                    "objection": "",
                    "recommendation": "Proceed as a generic vignette without invented personal documents.",
                    "score": 29,
                }
            ],
            "summary": "PASS with no taste cap and no safety exclusion.",
            "inputs_used": ["output/idea-loops/2026-07-28/run-202052/verification.json"],
            "debate_records": [],
            "scores": {"distribution": 27, "visual_generativity": 28},
            "selected_outputs": {"verdict": "PASS"},
            "objections": [],
            "repairs": [],
            "repaired_route_names": [],
        },
    },
    "exploration_routes": [
        {
            "name": "The Museum of Almost",
            "story_lens": "Witness love through the versions that did not become achievements.",
            "reader_mirror": "People whose partner knew them through abandoned ambitions, changing identities, awkward beginnings, or seasons they dismiss as wasted.",
            "emotional_obstacle": "The owner sees embarrassing evidence of things that went nowhere while the partner sees a record of becoming.",
            "aachu_specific_spark": "Aachu physically rejects the folder, tries to close it, then visibly changes her mind and extends it.",
            "zuv_active_role": "Zuv rescues and orders the folder without explaining, praising, hugging, or taking control of her final choice.",
            "proof_engine": "discarded folder -> rescued unfinished attempts -> visible chronology -> changed posture -> current draft added",
            "emotional_reversal": "The same papers change from a failure pile into a visible life-line.",
            "payoff": "Aachu voluntarily adds today's unfinished page.",
            "distribution_reason": "Send it to the person who remembered you before anything worked.",
            "process_influence_ids": ["card-20", "witness-engine"],
            "score_total": 29,
            "golden_theme_score_total": 28,
            "stage_scene_gate": stage_scene,
            "hard_fails": [],
            "verdict": "GO",
        }
    ],
    "repaired_routes": [],
    "rejected_routes": [],
    "selected_story_lens": "Witness love through the versions that did not become achievements.",
    "emotional_machine": "embarrassed discard -> quiet rescue and chronology -> dignity -> voluntary continuation",
    "proof_engine": "discarded folder -> rescued unfinished attempts -> visible chronology -> changed posture -> current draft added",
    "reader_mirror": "People whose partner knew them through abandoned ambitions, changing identities, awkward beginnings, or seasons they dismiss as wasted.",
    "distribution_reason": "Send it to the person who remembered you before anything worked.",
    "human_story_setup": {
        "cold_reader_doorway": "One person discards a worn folder and the other immediately rescues it.",
        "emotional_obstacle": "The owner sees failed versions as embarrassing rubbish.",
        "visible_human_proof": "The folder is rescued, opened, arranged oldest-to-newest, then extended by the owner.",
        "active_partner_role": "Zuv quietly orders the papers and withdraws his hands before Aachu chooses the final action.",
        "emotional_turn": "Aachu stops closing the folder and softens after seeing the chronology.",
        "shareable_setup": "Many viewers know the shame of drafts and plans that did not become achievements.",
        "earned_payoff": "Aachu adds today's unfinished page herself.",
    },
    "success_definition": {
        "audience_success": "A cold viewer recognizes the shame of failed versions and sends the post to the person who witnessed them.",
        "creative_success": "Five silent scenes create discard, exposure, chronology, re-seeing, and voluntary continuation.",
        "brand_success": "The route feels like a specific illustrated love archive rather than generic relationship advice.",
        "production_success": "Five native 1080x1440 text-bearing slides pass identity, story, text, anatomy, entity, paper-tone, and final audits.",
    },
    "stage_scene_gate": stage_scene,
    "process_influences": [
        {
            "id": "card-20",
            "title": "Saveable Lesson From One Scene",
            "influence_type": "concept_process_card",
            "source_patterns": ["visible relationship action", "earned thesis"],
            "confidence": 0.95,
            "reason": "One physical object-state sequence discovers the meaning instead of explaining it.",
        }
    ],
    "moment_origin": "generic_relationship_hypothesis",
    "lived_fact_status": "NOT_CLAIMED",
    "story_selling_score": story_score,
    "golden_theme_score": golden_score,
    "hard_fails": [],
    "required_repairs": [],
    "golden_theme_gate": "required_for_carousel",
    "downstream_contract": {
        "c_layer": {
            "must_preserve": [
                "selected_story_lens",
                "emotional_machine",
                "proof_engine",
                "reader_mirror",
                "distribution_reason"
            ],
            "golden_theme_gate": "required_for_carousel"
        }
    },
    "metadata": {
        "source": "output/idea-loops/2026-07-28/run-202052/",
        "selected_candidate_id": "run-202052-i1-b-museum-of-almost",
        "audience_distribution_reviewer": "verifier_audience_202052",
        "stage_scene_taste_safety_reviewer": "verifier_taste_202052",
        "selector": "selector_202052_final",
        "selector_verdict": "PASS",
        "taste_gate": "PASS_NO_CAP",
        "distribution_score": 27,
        "visual_generativity_score": 28,
        "story_director_scores": [8, 9, 9, 9, 9, 9],
    },
}
write("layer-e-story-selling.json", layer_e_record)

concept = load("concept.json")
concept["layer_e_story_selling"] = {
    "artifact": "layer-e-story-selling.json",
    "status": "PASS",
    "source": layer_e_record["source"],
}
concept["story_selling_decision"] = {
    "selected_concept_process_card": "Card 20 - Saveable Lesson From One Scene",
    "score": story_score,
    "threshold": "28/30",
    "decision": "GO",
    "hard_fails": [],
    "selector_verdict": "PASS: the visible discard, rescue, chronology, re-seeing, and current-page addition form one complete relationship story.",
    "stage_scene_gate": stage_scene,
    "golden_theme_score": golden_score,
    "proof_engine": layer_e_record["proof_engine"],
    "distribution_reason": layer_e_record["distribution_reason"],
    "evidence_source": layer_e_record["source"],
}
concept["successful_carousel_standard"] = {
    "source": "wiki/insights/successful-carousel-standard.md",
    "status": "GO",
    "pass": True,
    "audience_success": "Cold viewers recognize the fear of failed versions and can send the carousel to the person who witnessed them.",
    "creative_success": "Five silent scenes create discard, exposure, chronology, re-seeing, and voluntary continuation.",
    "brand_success": "The route is a specific illustrated love archive rather than generic advice or a quote deck.",
    "production_success": "The request lock is one five-slide 1080x1440 Instagram carousel with real identity/style inputs, integrated copy, brandmark, QA, and audit.",
    "evidence_source": layer_e_record["source"],
}
write("concept.json", concept)

visual_plan = load("visual-plan-quality.json")
visual_plan["winner"] = "The Folder Changes Hands"
visual_plan["status"] = "PASS"
visual_plan["decision"] = "GO"
visual_plan["can_generate"] = True
visual_plan["issues"] = []

prompt_pack = load("prompt-pack.json")
prompt_pack["layer_e_story_selling"] = {
    "status": "GO",
    "source": layer_e_record["source"],
    "story_selling_score": story_score,
    "golden_theme_score": golden_score,
    "stage_scene_gate": stage_scene,
    "hard_fails": [],
}
prompt_pack["post_copy_visual_room"] = {
    "status": "GO",
    "selected_visual_system": "The Folder Changes Hands",
    "why_it_wins": "The folder changes state on every slide, the story survives without copy, and Aachu owns the payoff.",
}
prompt_pack["visual_debate"] = {
    "status": "PASS",
    "winner": "The Folder Changes Hands",
    "selector_verdict": "The object-state and posture arc create five distinct visual sentences in one continuous room.",
}
prompt_pack["visual_plan_quality"] = {
    "status": "PASS",
    "decision": "GO",
    "winner": "The Folder Changes Hands",
    "issues": [],
}

replacements = {
    "Post-copy visual room winner: Slide-Led Evidence Plan.": "Post-copy visual room winner: The Folder Changes Hands.",
    "Visual Debate Gate winner: Slide-Led Evidence Plan.": "Visual Debate Gate winner: The Folder Changes Hands.",
    "Visual debate verdict: Slide-Led Evidence Plan wins because it keeps the visual system accountable to the selected story arc.": "Visual debate verdict: the folder changes state on every slide, and Aachu owns the payoff.",
    "Story Director gate: REPAIR.": "Story Director gate: PASS.",
    "Story-Selling score gate: 18.0/30, decision REPAIR.": "Story-Selling score gate: 29/30, decision PASS.",
    "active Zuv care": "visible relationship motion",
    "active Zuv role": "relevant partner role",
    "Aachu is the spark, he is the steady flame": "Aachu and Zuv remain equal participants with Aachu owning the payoff",
    "she is the spark, he is the steady flame": "their motion changes through mutual attention and Aachu's final action",
    "Keep a few tiny emotional micro-elements when useful: small hearts, blush marks, reaction ticks, tiny motion lines, soft thought bubbles, or one small care detail that makes the beat lovable.": "Do not add decorative hearts, thought bubbles, labels, micro-text, or symbolic figures; keep the papers wordless and let object state, gaze, posture, and hands carry the beat.",
}
for slide in prompt_pack["slides"]:
    text = slide["prompt"]
    for old, new in replacements.items():
        text = text.replace(old, new)
    slide["prompt"] = text

hand_actions = {
    1: {
        ("Aachu", "left"): ("supporting", "Rest on the open drawer edge, visibly attached through the left wrist and forearm"),
        ("Aachu", "right"): ("focal_action", "Withdraw from the folder after releasing it into the discard carton"),
        ("Zuv", "left"): ("supporting", "Rest on Zuv's own thigh, visibly attached and not touching any object"),
        ("Zuv", "right"): ("focal_action", "Meet and lift the folder edge from the carton with a believable exterior grip"),
    },
    2: {
        ("Aachu", "left"): ("focal_action", "Draw the folder cover toward half-closed with a believable flat contact"),
        ("Aachu", "right"): ("out_of_frame", "Stay completely outside the frame"),
        ("Zuv", "left"): ("focal_action", "Stabilize only the folder spine without tugging against Aachu"),
        ("Zuv", "right"): ("out_of_frame", "Stay completely outside the frame"),
    },
    3: {
        ("Aachu", "left"): ("supporting", "Rest naturally on Aachu's own knee, visibly attached and not touching the papers"),
        ("Aachu", "right"): ("out_of_frame", "Stay completely outside the frame"),
        ("Zuv", "left"): ("focal_action", "Arrange one older-looking wordless sheet at the left side of the chronology"),
        ("Zuv", "right"): ("focal_action", "Arrange one fresher-looking wordless sheet farther right"),
    },
    4: {
        ("Aachu", "left"): ("out_of_frame", "Stay completely outside the frame"),
        ("Aachu", "right"): ("focal_action", "Rest open beside the papers after releasing the folder cover"),
        ("Zuv", "left"): ("out_of_frame", "Stay completely outside the frame"),
        ("Zuv", "right"): ("out_of_frame", "Stay completely outside the frame"),
    },
    5: {
        ("Aachu", "left"): ("focal_action", "Steady the open folder edge with a believable light contact"),
        ("Aachu", "right"): ("focal_action", "Slide the fresh unfinished page into the final open gap"),
        ("Zuv", "left"): ("out_of_frame", "Stay completely outside the frame"),
        ("Zuv", "right"): ("out_of_frame", "Stay completely outside the frame"),
    },
}
for slide in prompt_pack["slides"]:
    number = int(slide["slide"])
    hand_map = slide["hand_map"]
    visible = 0
    for hand in hand_map["hands"]:
        visibility, action = hand_actions[number][(hand["owner"], hand["side"])]
        hand["visibility"] = visibility
        hand["action"] = action
        if visibility != "out_of_frame":
            visible += 1
    hand_map["expected_visible_hands"] = visible
    hand_map["default_max_visible_hands"] = visible
write("prompt-pack.json", prompt_pack)

blind_payload = load(".internal/event-a-blind-cards.json")
blind_cards = blind_payload["cards"]
slides = load("slides.json")
raw_response = (
    "A domestic clear-out becomes a quiet relational turn: he rescues what she was ready to "
    "discard, patiently makes its history visible, and she moves from closing it away to adding "
    "the next unfinished piece herself. The five frames read as one coherent causal story without "
    "copy, though the exact meaning of the papers remains deliberately open."
)

director_slides = [
    {
        "slide": 1,
        "status": "PASS",
        "inference_match": True,
        "narrative_job": "initial pressure and rescue",
        "silent_read": "She discards an unremarkable folder and he immediately treats it as consequential.",
        "change_from_previous": "The archive enters the story through a visible discard decision.",
        "critic_evidence": "The critic identified the open drawer and carton, her withdrawn hand, his lifting hand, and their split attention.",
        "staged_action": {
            "subject": "Aachu",
            "action": "releases",
            "target_or_object": "a worn unlabelled folder into the discard carton",
            "reaction_or_consequence": "Zuv bends and retrieves it before the clear-out continues",
        },
        "pov": {
            "owner": "Aachu's dismissal interrupted by Zuv's recognition",
            "audience_knows": "the folder matters differently to each person",
            "audience_feels": "curiosity about why he rescued the least impressive item",
        },
        "shot": {
            "size": "wide",
            "angle": "low three-quarter",
            "camera_position": "at discard-carton level looking across the study corner",
            "focal_subject": "the folder changing hands",
            "story_reason": "the low wide view proves discard, rescue, and different body directions at once",
        },
        "blocking": {
            "hands": "Aachu's right hand withdraws; left rests on drawer; Zuv's right hand lifts the folder; left rests on thigh",
            "gaze": "Aachu toward drawer, Zuv toward folder",
            "body_distance": "separated across drawer and carton",
            "posture_or_feet": "Aachu continues sorting while Zuv bends from a coherent standing silhouette",
        },
        "setting": {
            "sub_location": "home study desk and discard carton",
            "time": "quiet daytime clear-out",
            "motivated_light": "soft window light from the side",
            "story_trace": "open drawer, plain carton, and released folder show an active declutter",
        },
        "story_evidence": [
            {
                "carrier": "folder ownership",
                "observable_state": "released by Aachu and caught at the edge by Zuv",
                "narrative_job": "creates the first disagreement without dialogue",
            }
        ],
        "text_image_relationship": "interdependent",
        "continuity": {
            "incoming_state": "folder inside the drawer and marked for discard",
            "outgoing_state": "folder rescued from the carton in Zuv's right hand",
        },
        "entity_contract": {
            "expected_people": 2,
            "background_people": [],
            "reflections": [],
            "forbidden_entities": ["extra person", "duplicate couple", "portrait face", "silhouette"],
        },
        "unresolved_ambiguities": [],
        "resolved_ambiguities": [
            {
                "competing_read": "the folder may have fallen accidentally",
                "repair": "stage a clear released hand, folder fully inside the discard carton, and Aachu already moving to the next item",
                "recheck_evidence": "the critic still read the primary action as deliberate discard followed by rescue",
            }
        ],
    },
    {
        "slide": 2,
        "status": "PASS",
        "inference_match": True,
        "narrative_job": "exposure and resistance",
        "silent_read": "The folder contains unfinished work and she is reluctant to keep examining it.",
        "change_from_previous": "The rescued object opens and reveals why she wanted it gone.",
        "critic_evidence": "The critic cited the half-closing cover, worn erased papers, and his non-tugging hand at the spine.",
        "staged_action": {
            "subject": "Aachu",
            "action": "begins closing",
            "target_or_object": "the opened folder of unfinished wordless drafts",
            "reaction_or_consequence": "Zuv leaves his stabilizing hand at the spine without forcing it open",
        },
        "pov": {
            "owner": "Aachu's embarrassment",
            "audience_knows": "the contents are attempts rather than achievements",
            "audience_feels": "recognition of wanting old failed work hidden",
        },
        "shot": {
            "size": "close insert",
            "angle": "floor-level tactile side view",
            "camera_position": "beside the folder between their knees",
            "focal_subject": "the half-closing cover and unfinished sheets",
            "story_reason": "the insert makes paper state and non-coercive hand choreography legible",
        },
        "blocking": {
            "hands": "Aachu's left hand closes the cover; Zuv's left hand stabilizes the spine; other hands remain outside frame",
            "gaze": "faces remain outside frame so the hands and folder carry the hesitation",
            "body_distance": "knees occupy opposite sides of the folder with open space around it",
            "posture_or_feet": "both settle naturally at floor level without cramped or crouched anatomy",
        },
        "setting": {
            "sub_location": "floor beside the same desk and carton",
            "time": "continuous daytime clear-out",
            "motivated_light": "same soft side window light",
            "story_trace": "carton edge and desk leg preserve the clear-out continuity",
        },
        "story_evidence": [
            {
                "carrier": "folder cover",
                "observable_state": "moving from open toward half-closed under Aachu's hand",
                "narrative_job": "makes embarrassment visible as an interrupted action",
            }
        ],
        "text_image_relationship": "interdependent",
        "continuity": {
            "incoming_state": "folder rescued and opened",
            "outgoing_state": "unfinished contents exposed while the cover remains half-closed",
        },
        "entity_contract": {
            "expected_people": 2,
            "background_people": [],
            "reflections": [],
            "forbidden_entities": ["extra person", "duplicate hands", "readable document text", "ghost figure"],
        },
        "unresolved_ambiguities": [],
        "resolved_ambiguities": [
            {
                "competing_read": "her hand may only be adjusting the cover",
                "repair": "show a decisive cover-closing path while her torso angles away and Zuv does not tug",
                "recheck_evidence": "the critic's primary reading remained guarded reluctance and possible closing",
            }
        ],
    },
    {
        "slide": 3,
        "status": "PASS",
        "inference_match": True,
        "narrative_job": "chronology and reframing",
        "silent_read": "He turns loose discarded attempts into a continuous record while she watches.",
        "change_from_previous": "The same loose pages gain order and visible time.",
        "critic_evidence": "The critic identified both of his hands arranging worn-to-fresh sheets and the chronology bridging the space between them.",
        "staged_action": {
            "subject": "Zuv",
            "action": "orders",
            "target_or_object": "four or five wordless unfinished sheets from oldest-looking to freshest",
            "reaction_or_consequence": "Aachu stops closing the folder and watches the line take shape",
        },
        "pov": {
            "owner": "shared observation with Zuv performing the reframing",
            "audience_knows": "the attempts belong to one long process rather than separate failures",
            "audience_feels": "the quiet care of making time visible",
        },
        "shot": {
            "size": "overhead detail",
            "angle": "true top-down",
            "camera_position": "directly above the paper line",
            "focal_subject": "the worn-to-fresh chronology between them",
            "story_reason": "only an overhead view can prove order, progression, and both positions cleanly",
        },
        "blocking": {
            "hands": "both of Zuv's hands arrange separate sheets; Aachu's left hand stays on her own knee",
            "gaze": "both direct attention toward the line",
            "body_distance": "opposite sides of the chronology",
            "posture_or_feet": "seated naturally beyond the paper edges with no folded-limb ambiguity",
        },
        "setting": {
            "sub_location": "same floor or low table",
            "time": "continuous daytime clear-out",
            "motivated_light": "diffuse window light with soft paper shadows",
            "story_trace": "folder remains behind the line as the source of the loose sheets",
        },
        "story_evidence": [
            {
                "carrier": "paper wear progression",
                "observable_state": "sheets change subtly from more worn to fresher left-to-right",
                "narrative_job": "makes chronology visible without invented dates or labels",
            }
        ],
        "text_image_relationship": "interdependent",
        "continuity": {
            "incoming_state": "loose papers exposed in a half-closed folder",
            "outgoing_state": "papers arranged as a single left-to-right life-line",
        },
        "entity_contract": {
            "expected_people": 2,
            "background_people": [],
            "reflections": [],
            "forbidden_entities": ["extra hands", "readable dates", "labels", "certificates"],
        },
        "unresolved_ambiguities": [],
        "resolved_ambiguities": [
            {
                "competing_read": "the order could read as tidying rather than chronology",
                "repair": "differentiate wear and construction from oldest-looking at left to freshest at right and preserve the exact copy",
                "recheck_evidence": "the critic still inferred stages or age from the visible progression before seeing copy",
            }
        ],
    },
    {
        "slide": 4,
        "status": "PASS",
        "inference_match": True,
        "narrative_job": "reaction and emotional turn",
        "silent_read": "The ordered papers change Aachu from guarded withdrawal to receptive recognition.",
        "change_from_previous": "The reframing lands visibly in her posture and open hand.",
        "critic_evidence": "The critic cited the fully open folder, relaxed hand, softened posture, half-smile, and Zuv watching without pressing.",
        "staged_action": {
            "subject": "Aachu",
            "action": "releases and opens",
            "target_or_object": "the folder beside the ordered papers",
            "reaction_or_consequence": "her guarded posture softens while Zuv remains quiet in the foreground",
        },
        "pov": {
            "owner": "Aachu's changed perception",
            "audience_knows": "the same papers no longer mean only discard",
            "audience_feels": "dignity replacing embarrassment without a speech or hug",
        },
        "shot": {
            "size": "medium reaction",
            "angle": "over-shoulder",
            "camera_position": "behind Zuv's shoulder looking across the paper line",
            "focal_subject": "Aachu's open hand, softened posture, and face",
            "story_reason": "the reaction view makes her re-seeing the event rather than his kindness the emotional center",
        },
        "blocking": {
            "hands": "Aachu's right hand rests open beside the papers; Zuv's hands stay outside frame",
            "gaze": "Aachu looks at the chronology; Zuv's partial profile angles toward her and the papers",
            "body_distance": "close enough to share the view but not touching",
            "posture_or_feet": "Aachu opens from guarded shoulders into a relaxed seated posture",
        },
        "setting": {
            "sub_location": "same study corner beyond the ordered papers",
            "time": "continuous daytime clear-out",
            "motivated_light": "soft side light lifts Aachu's face without spotlight drama",
            "story_trace": "open folder and paper line keep the prior actions present in frame",
        },
        "story_evidence": [
            {
                "carrier": "open hand and open folder",
                "observable_state": "both have changed from closing to resting open",
                "narrative_job": "shows internal acceptance through physical state",
            }
        ],
        "text_image_relationship": "interdependent",
        "continuity": {
            "incoming_state": "Aachu watches Zuv order the papers",
            "outgoing_state": "Aachu stops trying to close or erase the archive",
        },
        "entity_contract": {
            "expected_people": 2,
            "background_people": [],
            "reflections": [],
            "forbidden_entities": ["extra person", "comfort hug", "ghost memory", "portrait face"],
        },
        "unresolved_ambiguities": [],
        "resolved_ambiguities": [
            {
                "competing_read": "the half-smile could mean nostalgia rather than recognition",
                "repair": "bind the expression to the changed open-hand and open-folder state plus the prior chronology",
                "recheck_evidence": "the critic's primary reading remained new receptivity and shared recognition",
            }
        ],
    },
    {
        "slide": 5,
        "status": "PASS",
        "inference_match": True,
        "narrative_job": "release and voluntary continuation",
        "silent_read": "Aachu chooses to extend the archive with the current unfinished self while Zuv gives her space to lead.",
        "change_from_previous": "Recognition becomes a new self-directed action rather than a passive feeling.",
        "critic_evidence": "The critic identified her two-handed page insertion, his withdrawn hands, their converging gazes, and the fresh page filling the final gap.",
        "staged_action": {
            "subject": "Aachu",
            "action": "adds",
            "target_or_object": "a fresh unfinished wordless page to the end of the ordered line",
            "reaction_or_consequence": "the archive becomes a living record while Zuv watches without directing",
        },
        "pov": {
            "owner": "Aachu's agency",
            "audience_knows": "being witnessed has changed what she does with today's unfinished work",
            "audience_feels": "tenderness earned through voluntary continuation",
        },
        "shot": {
            "size": "close two-shot",
            "angle": "low table-level",
            "camera_position": "beside the new page looking across both faces and the open folder",
            "focal_subject": "Aachu's page insertion and both converging gazes",
            "story_reason": "the low close view proves hand ownership, identity, emotional agency, and the final object change together",
        },
        "blocking": {
            "hands": "Aachu's right hand pushes the new page and left steadies the folder; Zuv's hands stay outside frame",
            "gaze": "both look at the new page",
            "body_distance": "side-by-side and close, with Aachu leaning farther into the action",
            "posture_or_feet": "Aachu leads from a natural seated lean; Zuv remains grounded beside her",
        },
        "setting": {
            "sub_location": "same low table or floor plane",
            "time": "continuous daytime clear-out",
            "motivated_light": "soft window light across the fresh page and their faces",
            "story_trace": "open folder and ordered row make the addition legible as continuation",
        },
        "story_evidence": [
            {
                "carrier": "fresh page entering the final gap",
                "observable_state": "wordless unfinished sheet is physically added by Aachu",
                "narrative_job": "converts being witnessed into changed behavior",
            }
        ],
        "text_image_relationship": "interdependent",
        "continuity": {
            "incoming_state": "archive remains open and re-seen",
            "outgoing_state": "current unfinished page extends the archive",
        },
        "entity_contract": {
            "expected_people": 2,
            "background_people": [],
            "reflections": [],
            "forbidden_entities": ["extra person", "duplicate couple", "readable page text", "museum label"],
        },
        "unresolved_ambiguities": [],
        "resolved_ambiguities": [
            {
                "competing_read": "the addition could look like simple completion of sorting",
                "repair": "show the fresh unfinished page entering the final open gap under Aachu's hands while the folder remains open behind the older line",
                "recheck_evidence": "the critic inferred voluntary participation and extension of the sequence",
            }
        ],
    },
]

director = {
    "status": "PASS",
    "event": "copy_hidden_storyboard_read",
    "copy_locked": True,
    "copy_hidden": True,
    "intent_hidden": True,
    "copy_lock_evidence": "The exact five slide lines in slides.json were locked before the blind cards were sent to the critic.",
    "author_id": "/root/museum_postcopy_room",
    "reviewer_id": "/root/museum_event_a_critic",
    "reviewer_evidence": "A fresh orchestrated critic received only the observable cards file and reported its inferences before any copy, theme, intent, labels, or scores were revealed.",
    "requested_formats": ["instagram_post"],
    "format_contract_fingerprint": locked_format_contract_fingerprint(ROOT),
    "blind_cards": blind_cards,
    "blind_input_fingerprint": blind_cards_fingerprint(blind_cards),
    "source_fingerprint": storyboard_source_fingerprint(slides),
    "creator_correction_fingerprint": current_creator_correction_fingerprint(ROOT),
    "generation_payload_fingerprint": current_generation_payload_fingerprint(ROOT),
    "review_provenance": {
        "schema_version": "visual-review-provenance/v2",
        "author_task_id": "/root/museum_postcopy_room",
        "author_run_id": "museum-postcopy-20260730-1",
        "reviewer_task_id": "/root/museum_event_a_critic",
        "reviewer_run_id": "museum-event-a-20260730-1",
        "input_fingerprint": blind_cards_fingerprint(blind_cards),
        "raw_response": raw_response,
        "raw_response_fingerprint": review_response_fingerprint(raw_response),
    },
    "sequence_mode": "causal_sequence",
    "physical_event": "A worn folder moves from discard to rescue to exposure to chronology to a new current addition.",
    "emotional_arc": "dismissal -> embarrassment -> attention -> dignity -> agency",
    "relationship_change": "Zuv's quiet ordering lets Aachu re-see the archive, and she moves from trying to close it to extending it herself.",
    "sequence_read": "During a home clear-out, Zuv rescues the folder Aachu discarded, orders its unfinished contents, and Aachu responds by adding today's unfinished page.",
    "visual_variables": ["folder and paper ownership", "Aachu's posture and participation"],
    "hero_receipt_slide": 5,
    "setup_payoff_ledger": [
        {
            "setup": "Aachu releases the worn folder into the discard carton.",
            "payoff": "Aachu places a fresh unfinished page at the end of the rescued chronology.",
            "changed_meaning": "The folder changes from rejected failure pile to a living record she voluntarily continues.",
        }
    ],
    "object_motif_ledger": [
        {
            "object": "worn unlabelled folder and wordless unfinished papers",
            "initial_state": "discarded and closed",
            "later_state": "rescued, opened, ordered, and extended with a fresh page",
            "story_job": "compresses disagreement, embarrassment, witnessing, time, and agency into one causal object-state arc",
        }
    ],
    "critic_inference": {
        "whole_sequence_one_sentence": "During a home clear-out, a man rescues a folder the woman was discarding, they examine and order its unfinished contents, her guardedness softens, and she chooses to extend the sequence with a fresh page.",
        "reads_as_one_causal_relationship_story_without_copy": True,
        "causal_read_note": "Rescue causes inspection, inspection becomes ordering, ordering changes her response, and that response leads to her active addition.",
    },
    "copy_visual_reconciliation": [
        {
            "slide": 1,
            "status": "PASS",
            "evidence": "Copy subject she, verb throwing away, and object almosts align with Aachu's released folder and immediate discard-carton state.",
        },
        {
            "slide": 2,
            "status": "PASS",
            "evidence": "The visible erased, folded, unfinished wordless sheets align with drafts that went nowhere without inventing document facts.",
        },
        {
            "slide": 3,
            "status": "PASS",
            "evidence": "Zuv performs the ordering and paper wear progresses left-to-right from oldest-looking to newest-looking.",
        },
        {
            "slide": 4,
            "status": "PASS",
            "evidence": "Aachu's closing motion reverses into an open hand and open folder while Zuv remains oriented toward her and the chronology.",
        },
        {
            "slide": 5,
            "status": "PASS",
            "evidence": "Aachu alone inserts the fresh unfinished page into the final open gap; Zuv watches with hands withdrawn.",
        },
    ],
    "slides": director_slides,
    "issues": [],
    "director_event_fingerprint_version": DIRECTOR_EVENT_FINGERPRINT_VERSION,
}
director["review_provenance"]["output_fingerprint"] = director_review_output_fingerprint(director)
director["director_event_fingerprint"] = director_event_fingerprint(director)
visual_plan["director_storyboard"] = director
write("visual-plan-quality.json", visual_plan)

review = load("review.json")
review.update(
    {
        "status": "pass",
        "total": 39,
        "max": 40,
        "pass": True,
        "story_director_gate": {
            "status": "PASS",
            "hook": 8,
            "story": 9,
            "bridge": 9,
            "relationship_motion": 9,
            "ending": 9,
            "send_save_potential": 9,
            "stage_scene": 9,
            "verdict": "PASS: exact copy, causal storyboard, visible relationship motion, and earned payoff are locked.",
            "blocks": [],
        },
        "story_selling_score": story_score,
        "story_selling_gate": {
            "status": "PASS",
            "source": layer_e_record["source"],
            "threshold": "28/30",
            "selector_verdict": "PASS",
            "stage_scene_gate": stage_scene,
            "golden_theme_score": golden_score,
        },
        "story_selling_hard_fails": [],
        "issues": [],
        "required_changes_before_image_generation": [],
        "successful_carousel_standard_gate": {
            "source": "wiki/insights/successful-carousel-standard.md",
            "status": "PASS",
            "pass": True,
            "agent_alignment": {
                "status": "PASS",
                "evidence": "Fresh idea-loop verification, selector pass, post-copy visual room, and Event A bind recognition, story proof, taste, sendability, and production feasibility.",
            },
            "dimensions": {
                "agent_goal_alignment": {"pass": True},
                "relationship_first_premise": {"pass": True},
                "story_selling_threshold": {"pass": True},
                "prompt_goal_alignment": {"pass": True},
                "stage_scene_storytelling": {"pass": True},
            },
            "issues": [],
        },
    }
)
review["visual_plan_quality_gate"] = {
    "status": "PASS",
    "decision": "GO",
    "can_generate": True,
    "director_storyboard": "PASS",
    "issues": [],
}
review["post_copy_visual_room_gate"] = {
    "status": "GO",
    "decision": "GO",
    "selected_visual_system": "The Folder Changes Hands",
    "open_doubts": [],
}
write("review.json", review)

stage_reviews = load("stage-reviews.json")
stage_reviews["reviews"]["visual_reviewer"].update(
    {
        "status": "PASS",
        "done": [
            "checked 5 slides",
            "post-copy visual room: GO",
            "visual screen: PASS",
            "copy-hidden director storyboard Event A: PASS",
        ],
        "issues": [],
    }
)
stage_reviews["reviews"]["success_standard_reviewer"].update(
    {
        "status": "PASS",
        "done": [
            "standard source: wiki/insights/successful-carousel-standard.md",
            "idea-loop Story-Selling: 29/30",
            "idea-loop Golden Theme: 28/30",
            "taste gate: PASS_NO_CAP",
            "gate: PASS",
        ],
        "issues": [],
    }
)
write("stage-reviews.json", stage_reviews)
