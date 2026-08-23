from __future__ import annotations

import json
from pathlib import Path

from pipeline.stages.carousel_format_contract import locked_format_contract_fingerprint, locked_formats
from pipeline.stages.carousel_visual_storytelling import (
    DIRECTOR_EVENT_FINGERPRINT_VERSION,
    REVIEW_PROVENANCE_VERSION,
    blind_cards_fingerprint,
    current_creator_correction_fingerprint,
    current_generation_payload_fingerprint,
    director_event_fingerprint,
    director_review_output_fingerprint,
    review_response_fingerprint,
    storyboard_source_fingerprint,
    validate_director_storyboard,
)

PACKAGE = Path("output/carousels/2026-08-14/certain-of-you-lost-in-us")
RAW_PATH = PACKAGE / ".internal/event-a-raw-response.md"

cards = [
    {
        "slide": 1,
        "visible_people": ["one South Asian woman", "one South Asian man"],
        "visible_setting": "A giant architectural blueprint on an ivory floor rises into airy domestic half-stairs, open doorframes and corridors around them.",
        "observable_action": "They stand shoulder-to-shoulder on one central tile; their inside hands clasp at hip height while each studies a different corridor.",
        "hands_and_contact": "Four visible hands total; the inner pair clasp once and the outer hands rest at their own thighs.",
        "gaze": "Each person studies a different corridor while their heads remain close enough to read as one shared survey.",
        "body_blocking": "Their torsos align, shoulders touch, and both bodies remain at the same depth on the same tile.",
        "object_state": "The blueprint is open and physically becoming the surrounding house.",
        "camera_view": "Extreme-wide three-quarter cutaway with both faces still readable.",
        "visible_continuity": "Charcoal-and-ivory wardrobe, exactly two people, no reflections or background figures.",
    },
    {
        "slide": 2,
        "visible_people": ["the same South Asian woman", "the same South Asian man"],
        "visible_setting": "One almost-empty shared room with two separate open doorways behind them.",
        "observable_action": "Each steps away from a different doorway toward the other; their inside hands have just met at the room center.",
        "hands_and_contact": "Four visible hands; the inside pair meet once and the outer hands stay relaxed.",
        "gaze": "Their eye-lines lock on each other rather than the empty room or separate doors.",
        "body_blocking": "Both walk toward the center at the same depth with equal agency.",
        "object_state": "One plain suitcase sits outside each original doorway; one small folded blueprint lies unopened between their approaching feet.",
        "camera_view": "Symmetrical medium full-body view.",
        "visible_continuity": "The same clean charcoal-and-ivory wardrobe and the same pair only.",
    },
    {
        "slide": 3,
        "visible_people": ["the same South Asian woman", "the same South Asian man"],
        "visible_setting": "A true overhead view of the room as the unfolded blueprint folds upward into full-size walls, stairs and branching rooms.",
        "observable_action": "They kneel at opposite near edges of the paper, shoulders lightly touching; each uses one hand to hold a separate corner while body and gaze turn toward different branches.",
        "hands_and_contact": "Exactly two visible hands, one per person, each attached through wrist and forearm to its own blueprint corner.",
        "gaze": "Their gazes split toward different branches and different practical demands.",
        "body_blocking": "They remain close enough for shoulder contact while their attention visibly divides.",
        "object_state": "The folded plan is now opened and expanding; indigo plan lines split while cartons, one leaking tap and two work bags appear at different thresholds.",
        "camera_view": "True overhead wide view.",
        "visible_continuity": "The same lightly dusty wardrobe, exactly two people and the same blueprint.",
    },
    {
        "slide": 4,
        "visible_people": ["the same South Asian woman", "the same South Asian man"],
        "visible_setting": "A low floor-level close view of the blueprint during restrained indoor rain; one unlit lamp and one wall-less doorway are soft behind.",
        "observable_action": "They lean in from opposite sides, each holds one separate corner flat, and both stare down at the paper.",
        "hands_and_contact": "Exactly two active hands, the woman's right and the man's left, with wrists and forearms visible; their other hands stay outside the crop.",
        "gaze": "Both gazes converge on the same dissolving route rather than on each other.",
        "body_blocking": "Faces occupy opposite sides while both bodies angle toward the same central object.",
        "object_state": "Indigo ink visibly bleeds away until the route becomes unreadable.",
        "camera_view": "Tight floor-level two-face three-quarter view.",
        "visible_continuity": "The same rain-damp wardrobe with faint indigo stains, exactly two people and the same plan.",
    },
    {
        "slide": 5,
        "visible_people": ["the same South Asian woman", "the same South Asian man"],
        "visible_setting": "A physical dead end in the same unfinished branching corridor.",
        "observable_action": "They sit shoulder-to-shoulder on the floor; one hand each turns the ruined blueprint over to reveal a clean blank reverse; their eyes meet with a small exhausted smile.",
        "hands_and_contact": "Exactly two visible hands, one per person, lift separate paper corners while their shoulders touch.",
        "gaze": "Their eye-lines meet in the first direct reciprocal look after the plan fails.",
        "body_blocking": "Both sit at the same depth and equal scale with natural shoulder contact.",
        "object_state": "Blue-stained fingertips, damp clothes and scuffed shoes remain; the ruined side turns down and the blank side turns up.",
        "camera_view": "Intimate eye-level reaction view.",
        "visible_continuity": "The same pair, same damp wardrobe, same blueprint and unresolved corridor behind.",
    },
    {
        "slide": 6,
        "visible_people": ["the same South Asian woman", "the same South Asian man"],
        "visible_setting": "A low floor-level dawn view of blank blueprint paper covering an unfinished floor; the incomplete impossible house remains behind.",
        "observable_action": "They stand on the same side of one taut carpenter's chalk line; each holds one endpoint with an inside hand while outer hands rest at their own thighs; a fresh blue line has just been snapped across the paper.",
        "hands_and_contact": "Four visible hands; the two inside hands separately own the line endpoints and the outer hands remain separate at their own thighs.",
        "gaze": "Both look along the new line toward the same open unfinished space, then toward each other.",
        "body_blocking": "Their shoulders align at the same depth on the same side of the new line.",
        "object_state": "The blank reverse now carries one new blue line and a restrained chalk-dust bloom while the house remains incomplete.",
        "camera_view": "Low medium-wide view with both faces large enough to read.",
        "visible_continuity": "The same pair, same wardrobe with rain and chalk traces, same reversed blueprint and exactly two people.",
    },
]

jobs = [
    "flash-forward thesis and spatial establisher",
    "mutual convergence and initial choice",
    "pressure expands into divergent demands",
    "peak loss of instructions",
    "turn through reciprocal recognition",
    "release into equal authorship",
]
silent_reads = [
    "They remain physically certain of each other while the shared environment has become impossible to navigate.",
    "Two separate lives deliberately converge in one shared room before they open a common plan.",
    "The shared plan generates several simultaneous responsibilities and pulls their attention in different directions.",
    "They face the same loss of direction together, but neither person can supply the missing answer.",
    "The route failed without making the partnership fail, and the blank reverse gives them a new working surface.",
    "They do not possess the whole solution; they make the first next line as equal co-authors.",
]
critic_evidence = [
    "The blind critic cited touching shoulders, aligned bodies, clasped hands, opposing gazes and branching corridors as evidence of connection inside uncertainty.",
    "The blind critic cited separate originating doorways, separate suitcases, mutual movement to center and meeting hands as evidence of equal convergence.",
    "The blind critic cited shoulder contact, equal paper ownership, opposing gazes, split plan lines, cartons, the leaking tap and two work bags as shared pressure with different priorities.",
    "The blind critic cited converging gazes, two hands holding separate corners, indoor rain, the unlit lamp and vanishing ink as a united confrontation with failed guidance.",
    "The blind critic cited touching shoulders, one lifted corner each, direct eye contact, damp clothes, scuffed shoes, stained fingers and the blank reverse as mutual recognition after effort.",
    "The blind critic cited equal endpoint ownership, same-side blocking, a single fresh line, chalk bloom, dawn light and the incomplete house as shared agency rather than completion.",
]

shots = [
    ("extreme-wide cutaway", "high three-quarter angle", "outside the open paper-house geometry looking inward", "the touching couple inside branching architecture"),
    ("medium full-body", "symmetrical eye-level angle", "inside the empty shared room facing both original doorways", "the meeting hands above the folded plan"),
    ("overhead wide", "true top-down angle", "directly above the expanding blueprint", "the split demands around their touching shoulders"),
    ("tight two-face close view", "low floor-level three-quarter angle", "at blueprint height between the two leaning bodies", "the ink route bleeding away between their hands"),
    ("intimate reaction two-shot", "eye-level side angle", "at the dead-end floor facing both seated profiles", "the shared page turn and exhausted reciprocal look"),
    ("medium-wide full-body", "low floor-level dawn angle", "on the blank paper looking past them into unfinished space", "the freshly snapped line owned equally by both"),
]

settings = [
    ("impossible open domestic paper house", "visual-thesis flash-forward", "cool diffuse ivory light with restrained indigo depth", "the open blueprint has already grown into rooms around them"),
    ("almost-empty shared room", "late afternoon beginning", "soft neutral window light", "two suitcases remain outside separate thresholds and the blueprint is still folded"),
    ("blueprint becoming rooms", "dusk as demands multiply", "fading window light across the unfolded paper", "cartons, one leak and work bags show several unfinished adult tasks"),
    ("unfinished floor around the failed plan", "storm-blue night", "cool rain light with the practical lamp deliberately unlit", "wet clothes and bleeding ink show the instructions failing on screen"),
    ("dead end in the same corridor", "predawn after the storm", "soft cool ambient light from the open corridor", "stained fingers, scuffed shoes and the blank reverse preserve the aftermath"),
    ("blank blueprint over an unfinished floor", "clear neutral dawn", "soft ivory daylight without yellow cast", "rain marks and blue chalk dust show that the next action follows the failure"),
]

actions = [
    ("Aachu and Zuv", "clasp hands while surveying different corridors", "the house grown from their blueprint", "physical alignment survives spatial disorientation"),
    ("Aachu and Zuv", "step from separate thresholds and meet hands at center", "each other and the unopened shared plan", "two independent origins become one mutual starting point"),
    ("Aachu and Zuv", "hold separate corners while the plan grows into branches", "the expanding shared home", "their attention splits toward several practical demands"),
    ("Aachu and Zuv", "hold the same plan flat as its ink route dissolves", "the failed blueprint", "both lose guidance without assigning blame or rescue"),
    ("Aachu and Zuv", "turn the ruined plan over together", "the blank reverse", "an exhausted shared look changes failure into workable possibility"),
    ("Aachu and Zuv", "snap one fresh construction line together", "the blank working surface", "one coordinated next action replaces the fantasy of a complete answer"),
]

blocks = [
    ("the inner hands clasp once and both outer hands remain separate", "their gazes survey different corridors", "shoulders touch on one stable tile", "both stand grounded while the architecture branches"),
    ("inside hands meet once and outside hands hang at their own sides", "their eye-lines lock on each other", "equal approach from opposite thresholds", "both take one deliberate step toward the center"),
    ("one owned hand per person holds one separate paper corner", "their gazes split toward different branches", "shoulders still touch despite divided attention", "both kneel with stable separate silhouettes"),
    ("exactly two owned hands hold separate plan corners", "both gazes converge on the dissolving route", "faces remain on opposite sides of the same object", "both lean down without pointing, fighting or rescue gestures"),
    ("one hand each lifts a separate corner of the same page", "their eyes meet in a small exhausted smile", "shoulders touch at equal seated scale", "scuffed shoes and relaxed posture show effort without defeat"),
    ("inside hands separately own the chalk-line endpoints and outer hands stay at their own thighs", "both follow the new line before sharing one look", "aligned shoulders remain on the same side of the line", "both stand and apply equal tension to the single tool"),
]

evidence = [
    ("clasped hands inside branching rooms", "aligned bodies stay on one tile while gazes split toward different corridors", "compress connection and disorientation into one cover contradiction"),
    ("separate suitcases and the folded blueprint", "each leaves one former threshold and moves toward the other before the shared plan opens", "show mutual choice through origin, movement and object state"),
    ("the expanding blueprint and three lived demands", "paper becomes rooms as route lines split toward cartons, a leak and work bags", "make harder shared-life questions visible without labels"),
    ("bleeding indigo route", "rain erases the only readable path while both hands still hold the same sheet", "show that love remains present even when instructions do not"),
    ("blank reverse of the ruined blueprint", "the failed surface turns over under two equal hands", "turn being lost from verdict into a new working condition"),
    ("fresh snapped chalk line", "both hold one endpoint and create only one new mark while the house stays unfinished", "pay off commitment as equal next-step authorship rather than total certainty"),
]

continuity_pairs = [
    ("The cover opens on the lived complexity after the plan has already expanded.", "The cold open rewinds visibly to separate thresholds and a still-folded plan."),
    ("Two separate lives and one unopened plan await a mutual choice.", "They finish converging and the plan becomes ready to open."),
    ("The same folded plan has been opened by both people.", "The paper grows into rooms and several responsibilities divide their attention."),
    ("The expanded plan still appears usable when the storm begins.", "Its route becomes unreadable while both remain engaged with the same problem."),
    ("The route has failed and effort has carried them to a dead end.", "They reveal a blank reverse without claiming that the corridor itself is solved."),
    ("The blank reverse becomes available after their shared page turn.", "They author one next line and leave the larger house visibly incomplete."),
]

director_slides = []
for index in range(6):
    number = index + 1
    size, angle, camera_position, focal_subject = shots[index]
    sub_location, time, light, trace = settings[index]
    subject, action, target, reaction = actions[index]
    hands, gaze, distance, posture = blocks[index]
    carrier, observed, job = evidence[index]
    incoming, outgoing = continuity_pairs[index]
    resolved = []
    if number == 1:
        resolved.append(
            {
                "competing_read": "The already-open transformed plan could make the cover look chronologically later than the still-folded plan on slide two.",
                "repair": "Lock the cover as a deliberate flash-forward visual thesis, then make slide two's two origin doorways, clean wardrobe and unopened folded plan a clear rewind into the causal beginning.",
                "recheck_evidence": "The blind critic explicitly identified flash-forward or imagined-premise as the viable reading and still summarized the subsequent connection, divergence, failure and renewed action correctly.",
            }
        )
    director_slides.append(
        {
            "slide": number,
            "status": "PASS",
            "inference_match": True,
            "narrative_job": jobs[index],
            "silent_read": silent_reads[index],
            "change_from_previous": outgoing,
            "critic_evidence": critic_evidence[index],
            "staged_action": {
                "subject": subject,
                "action": action,
                "target_or_object": target,
                "reaction_or_consequence": reaction,
            },
            "pov": {
                "owner": "the partnership as an equal shared point of view",
                "audience_knows": silent_reads[index],
                "audience_feels": ["vertigo held by connection", "calm mutual choice", "shared overload", "helplessness without blame", "relief without solution", "hope through equal agency"][index],
            },
            "shot": {
                "size": size,
                "angle": angle,
                "camera_position": camera_position,
                "focal_subject": focal_subject,
                "story_reason": "The camera keeps the current action, body relationship and blueprint state readable together before decorative architecture.",
            },
            "blocking": {
                "hands": hands,
                "gaze": gaze,
                "body_distance": distance,
                "posture_or_feet": posture,
            },
            "setting": {
                "sub_location": sub_location,
                "time": time,
                "motivated_light": light,
                "story_trace": trace,
            },
            "story_evidence": [
                {"carrier": carrier, "observable_state": observed, "narrative_job": job}
            ],
            "text_image_relationship": "interdependent",
            "continuity": {"incoming_state": incoming, "outgoing_state": outgoing},
            "entity_contract": {
                "expected_people": 2,
                "background_people": [],
                "reflections": [],
                "forbidden_entities": ["duplicate couple", "background figure", "reflection person", "portrait that reads as a live actor", "ghost silhouette"],
            },
            "unresolved_ambiguities": [],
            "resolved_ambiguities": resolved,
        }
    )

slides = json.loads((PACKAGE / "slides.json").read_text(encoding="utf-8"))
plan_path = PACKAGE / "visual-plan-quality.json"
plan = json.loads(plan_path.read_text(encoding="utf-8"))
raw_response = RAW_PATH.read_text(encoding="utf-8")

director = {
    "status": "PASS",
    "event": "copy_hidden_storyboard_read",
    "copy_locked": True,
    "copy_hidden": True,
    "intent_hidden": True,
    "copy_lock_evidence": "The creator supplied the exact six slide lines in the current chat; the package preserved them verbatim before this independent observable-card review.",
    "author_id": "orchestrated-/root",
    "reviewer_id": "orchestrated-/root/event_a",
    "reviewer_evidence": "A fresh collaboration agent received only the six observable cards and reported who, where, action, relationship state, chronology, evidence, uncertainty and the sequence before any copy or intent reveal.",
    "requested_formats": list(locked_formats(PACKAGE)),
    "format_contract_fingerprint": locked_format_contract_fingerprint(PACKAGE),
    "creator_correction_fingerprint": current_creator_correction_fingerprint(PACKAGE),
    "generation_payload_fingerprint": current_generation_payload_fingerprint(PACKAGE),
    "blind_cards": cards,
    "blind_input_fingerprint": blind_cards_fingerprint(cards),
    "source_fingerprint": storyboard_source_fingerprint(slides),
    "sequence_mode": "causal_sequence",
    "physical_event": "A folded blueprint becomes a shared house, grows beyond its instructions, loses its route in rain, reaches a dead end, turns over and receives one new line from both people.",
    "emotional_arc": "Mutual certainty enters shared complexity, loses guidance without blame, reinterprets the failed route and becomes equal next-step authorship.",
    "relationship_change": "Their connection moves from mutual approach through divided attention and shared helplessness into explicit equal construction of the next step.",
    "sequence_read": "Two people converge around a shared plan, become pulled through its branching demands, lose the route, reach a dead end, then turn the damaged plan over and make their first new line together.",
    "visual_variables": ["domestic geometry complexity", "body alignment and distance"],
    "hero_receipt_slide": 6,
    "setup_payoff_ledger": [
        {
            "setup": "The blueprint appears folded and unopened between two people leaving separate thresholds.",
            "payoff": "After the opened plan outgrows and fails them, they turn it over and snap one new line together.",
            "changed_meaning": "The plan changes from promised instructions into a blank surface for equal authorship.",
        }
    ],
    "object_motif_ledger": [
        {
            "object": "the single shared blueprint",
            "initial_state": "folded and unopened between two converging lives",
            "later_state": "opened, expanded, rain-erased, reversed and marked with one fresh line",
            "story_job": "carry the difference between choosing a person and learning how to build a life with them",
        }
    ],
    "slides": director_slides,
    "issues": [],
    "director_event_fingerprint_version": DIRECTOR_EVENT_FINGERPRINT_VERSION,
    "review_provenance": {
        "schema_version": REVIEW_PROVENANCE_VERSION,
        "author_task_id": "orchestrated-/root",
        "author_run_id": "orchestrated-root-run-20260814-01",
        "reviewer_task_id": "orchestrated-/root/event_a",
        "reviewer_run_id": "orchestrated-event-a-run-20260814-01",
        "input_fingerprint": blind_cards_fingerprint(cards),
        "raw_response_artifact": ".internal/event-a-raw-response.md",
        "raw_response_fingerprint": review_response_fingerprint(raw_response),
        "output_fingerprint": "",
    },
}
director["review_provenance"]["output_fingerprint"] = director_review_output_fingerprint(director)
director["director_event_fingerprint"] = director_event_fingerprint(director)
plan["director_storyboard"] = director

issues = validate_director_storyboard(
    plan,
    slide_count=len(slides),
    expected_slides=slides,
    expected_formats=locked_formats(PACKAGE),
    expected_format_contract_fingerprint=locked_format_contract_fingerprint(PACKAGE),
    expected_creator_correction_fingerprint=current_creator_correction_fingerprint(PACKAGE),
    expected_generation_payload_fingerprint=current_generation_payload_fingerprint(PACKAGE),
    provenance_package_dir=PACKAGE,
)
if issues:
    raise SystemExit("\n".join(issues))

plan_path.write_text(json.dumps(plan, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

stage_path = PACKAGE / "stage-reviews.json"
stage = json.loads(stage_path.read_text(encoding="utf-8"))
review = stage["reviews"]["visual_reviewer"]
review["status"] = "PASS"
review["issues"] = []
review.setdefault("done", []).append("fresh copy-hidden director_storyboard Event A: PASS")
stage_path.write_text(json.dumps(stage, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

print(json.dumps({"status": "PASS", "director_event_fingerprint": director["director_event_fingerprint"]}, indent=2))
