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


PACKAGE = Path("output/carousels/2026-08-14/certain-of-you-lost-in-us-no-script-repair-01")
CARDS_PATH = PACKAGE / ".internal/event-a-blind-cards.json"
RAW_PATH = PACKAGE / ".internal/event-a-repair2-raw-response.md"


def load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


cards = load(CARDS_PATH)
slides = load(PACKAGE / "slides.json")
plan_path = PACKAGE / "visual-plan-quality.json"
plan = load(plan_path)
raw_response = RAW_PATH.read_text(encoding="utf-8")
director = plan["director_storyboard"]

director.update(
    {
        "status": "PASS",
        "event": "copy_hidden_storyboard_read",
        "copy_locked": True,
        "copy_hidden": True,
        "intent_hidden": True,
        "author_id": "/root",
        "reviewer_id": "/root/theater_repair2_event_a",
        "reviewer_evidence": "A fresh independent reviewer received only the six repaired observable cards and returned GO, explicitly passing the two owner-specific blank-page actions, straight cleated fly-line, equal curtain recovery and mark-free closed book.",
        "requested_formats": list(locked_formats(PACKAGE)),
        "format_contract_fingerprint": locked_format_contract_fingerprint(PACKAGE),
        "creator_correction_fingerprint": current_creator_correction_fingerprint(PACKAGE),
        "generation_payload_fingerprint": current_generation_payload_fingerprint(PACKAGE),
        "blind_cards": cards,
        "blind_input_fingerprint": blind_cards_fingerprint(cards),
        "source_fingerprint": storyboard_source_fingerprint(slides),
        "sequence_mode": "montage_with_arc",
        "physical_event": "A couple enters one theatre world, absorbs separate incoming demands, actively searches blank guidance, jointly recovers a failed curtain change and each moves one separate chair into the same next light.",
        "emotional_arc": "Steadiness amid change becomes chosen connection, coordinated strain, shared uncertainty, humor through reciprocal recovery and renewed agency.",
        "relationship_change": "They move from separate arrivals through divided attention and missing guidance into active shared repair and coordinated continuation.",
        "sequence_read": "A cold-open shows aligned movement inside separating scenery; chronology begins with separate wings, adds different demands, loses the script, makes the cue failure physical, shows both repairing it, and ends with both building the next scene.",
        "issues": [],
        "director_event_fingerprint_version": DIRECTOR_EVENT_FINGERPRINT_VERSION,
    }
)

updates = {
    4: {
        "status": "PASS",
        "inference_match": True,
        "narrative_job": "absent instructions force an active shared search",
        "silent_read": "A blackout leaves them actively searching a blank script while fixed theatre machinery offers no answer.",
        "change_from_previous": "The practical load-in cuts to blackout, where they turn and test a blank script instead of receiving instructions.",
        "critic_evidence": "The fresh blind reviewer read active searching, not a passive tableau, and explicitly found the straight flush-fixed line to be stage machinery rather than a noose.",
        "staged_action": {
            "subject": "Aachu and Zuv",
            "action": "turn one blank page while pressing the opposite blank page corner flat",
            "target_or_object": "the completely blank rehearsal script",
            "reaction_or_consequence": "their complementary actions reveal that no instruction exists",
        },
        "pov": {
            "owner": "the partnership as two equal agents inside one shared stage world",
            "audience_knows": "They are actively looking for an answer and the pages contain none.",
            "audience_feels": "helplessness without blame",
        },
        "shot": {
            "size": "object-dominant close insert",
            "angle": "over-Aachu-shoulder table level",
            "camera_position": "beside the rehearsal table during blackout",
            "focal_subject": "two separately owned hands acting on opposite blank pages and two searching faces",
            "story_reason": "Active hands make the absence of guidance legible before the blackout atmosphere.",
        },
        "blocking": {
            "hands": "exactly Aachu's right hand turns the right page and Zuv's left index finger and palm press the left page corner flat; all other hands stay outside frame",
            "gaze": "both remain on the blank spread",
            "body_distance": "Aachu is partial foreground and Zuv is readable beyond the central object",
            "posture_or_feet": "both lean into the search without touching each other or the fixed wall machinery",
        },
        "setting": {
            "sub_location": "small rehearsal table in blackout",
            "time": "after the demands interrupt the scene",
            "motivated_light": "one distant ghost light with restrained blue-black stage depth",
            "story_trace": "two separately owned hands search blank pages beside a straight taut wall-cleated fly-line and still-hanging curtain edge, with no hanging loop",
        },
        "story_evidence": [
            {
                "carrier": "the actively turned blank page and separately pressed blank page corner",
                "observable_state": "both people search, but the pages remain completely empty",
                "narrative_job": "make absent guidance visible through behavior rather than a static prop",
            }
        ],
        "text_image_relationship": "interdependent",
        "continuity": {
            "incoming_state": "They have handled separate practical demands inside one shared stage world.",
            "outgoing_state": "Their active search finds no instruction, while the fixed technical cue remains ready to fail.",
        },
        "entity_contract": director["slides"][3]["entity_contract"],
        "unresolved_ambiguities": [],
        "resolved_ambiguities": [
            {
                "competing_read": "A hanging cue line could resemble a noose or self-harm symbol.",
                "repair": "Make the line single, straight, taut, vertical, flush to the wall and visibly fixed into a metal cleat, with no loose section, loop, knot, curve, coil or rope end.",
                "recheck_evidence": "The fresh blind reviewer explicitly passed this geometry as theatre machinery rather than a noose.",
            }
        ],
    },
    5: {
        "status": "PASS",
        "inference_match": True,
        "narrative_job": "visible cue failure turns into equal shared recovery",
        "silent_read": "The curtain has failed, and both people actively lift and fold it together until the crooked recovery triggers reciprocal laughter.",
        "change_from_previous": "The fixed cue fails physically, then each person owns one curtain corner and moves it toward the same center.",
        "critic_evidence": "The fresh blind reviewer cited the kneeling bodies, separately owned corners, lifted fabric ridge and dust marks as active recovery rather than a posed portrait.",
        "staged_action": {
            "subject": "Aachu and Zuv",
            "action": "each lift one separately owned curtain corner into one crooked fold",
            "target_or_object": "the fallen indigo curtain",
            "reaction_or_consequence": "the shared mishap becomes tired mutual laughter instead of blame",
        },
        "pov": {
            "owner": "the partnership as two equal agents inside one shared stage world",
            "audience_knows": "The cue failed, but they are jointly handling its aftermath.",
            "audience_feels": "relief through reciprocal recovery",
        },
        "shot": {
            "size": "medium-wide active recovery two-shot",
            "angle": "low side-stage eye level",
            "camera_position": "from the wing across the newly fallen curtain",
            "focal_subject": "two separately owned curtain corners moving into one crooked fold",
            "story_reason": "The active fabric recovery must read before the shared laugh.",
        },
        "blocking": {
            "hands": "exactly one inside hand per person grips only that person's curtain corner; outside hands remain outside crop",
            "gaze": "their eye-lines meet at the instant the fold lands crooked",
            "body_distance": "they kneel at the same depth on opposite sides of the central fabric ridge",
            "posture_or_feet": "both bodies lean into the same lifting effort",
        },
        "setting": {
            "sub_location": "bare side-stage floor",
            "time": "immediately after the cue failure",
            "motivated_light": "pale ghost-light rim against the fallen indigo curtain",
            "story_trace": "a shallow moving fabric ridge and two short fresh dust marks prove shared recovery; the featureless blank closed script remains on a separate table",
        },
        "story_evidence": [
            {
                "carrier": "the lifted curtain corners, crooked center fold and dust marks",
                "observable_state": "both people are physically recovering the same failed object with equal agency",
                "narrative_job": "turn uncertainty into shared action and recognition",
            }
        ],
        "text_image_relationship": "interdependent",
        "continuity": {
            "incoming_state": "Their active search found no instruction while the technical cue remained ready.",
            "outgoing_state": "The cue has failed, but both people jointly recover its aftermath and reconnect through laughter.",
        },
        "entity_contract": director["slides"][4]["entity_contract"],
        "unresolved_ambiguities": [],
        "resolved_ambiguities": [
            {
                "competing_read": "A seated laughing couple could collapse into a generic backstage portrait at phone size.",
                "repair": "Kneel them on opposite sides of the fallen curtain, give each one separately owned moving corner, and show a lifted ridge plus local dust marks before the laugh.",
                "recheck_evidence": "The fresh blind reviewer explicitly passed the beat as active shared recovery rather than posing.",
            }
        ],
    },
    6: {
        "critic_evidence": "The fresh blind reviewer read equal chair movement into the next light and explicitly passed the featureless closed book as completely blank and secondary.",
        "setting": {
            "sub_location": "stage lip facing unfinished center",
            "time": "the next cue after shared recovery",
            "motivated_light": "one pale-peach footlight and shared open center",
            "story_trace": "the pooled recovered curtain and featureless mark-free closed script remain behind while the opening scenery movement returns",
        },
        "story_evidence": [
            {
                "carrier": "the converging chairs, next light and abandoned blank script",
                "observable_state": "each person moves one chair forward while the recovered curtain and mark-free closed book remain behind",
                "narrative_job": "pay off commitment as equal continuation rather than total certainty",
            }
        ],
        "continuity": {
            "incoming_state": "They have actively recovered the failed curtain together without blame.",
            "outgoing_state": "They leave the blank script behind, converge the two chairs and re-enter the opening scenery motif around one shared center.",
        },
        "unresolved_ambiguities": [],
        "resolved_ambiguities": [
            {
                "competing_read": "A labeled prop book would violate the exact-text lock.",
                "repair": "Keep the small dark-indigo closed book completely featureless and blank, with no title, icon, marks, letters or pseudo-text.",
                "recheck_evidence": "The fresh blind reviewer explicitly passed the observable specification as mark-free and unambiguous.",
            }
        ],
    },
}

for slide_record in director["slides"]:
    number = int(slide_record["slide"])
    if number in updates:
        slide_record.update(updates[number])

director["setup_payoff_ledger"] = [
    {
        "setup": "One empty rehearsal chair remains isolated in each opposite wing when the couple first enters the shared light.",
        "payoff": "Each person later pulls one of those chairs toward the same next light until both angle inward.",
        "changed_meaning": "Separate origins become equal authorship of one next scene without collapsing either person's agency.",
    },
    {
        "setup": "They actively turn and test a completely blank script beside a straight fixed theatre fly-line and still-hanging curtain.",
        "payoff": "The curtain fails, both people actively fold it together, and the featureless blank script remains behind when they move forward.",
        "changed_meaning": "Missing instructions and visible failure become shared repair rather than a verdict on the partnership.",
    },
    {
        "setup": "Indigo and dusty-rose scenery flats move apart while the couple stays aligned in the opening cold-open.",
        "payoff": "The same flats open the center again as both people converge their chairs around one new light.",
        "changed_meaning": "The changing world becomes the unfinished stage on which they keep choosing one direction.",
    },
]
director["object_motif_ledger"] = [
    {
        "object": "the two rehearsal chairs",
        "initial_state": "empty and isolated in opposite dark wings",
        "later_state": "separately owned, actively moving and angled inward inside one next light",
        "story_job": "carry the transition from separate origins to equal participation in a shared future",
    },
    {
        "object": "the blank rehearsal script and curtain mechanism",
        "initial_state": "blank pages actively searched beside a straight fixed wall-cleated fly-line and still-hanging curtain",
        "later_state": "featureless and closed on a separate table while both people recover the fallen curtain, then visibly left behind",
        "story_job": "make absent guidance, visible failure, equal recovery and the choice to continue physically legible",
    },
]

director["review_provenance"] = {
    "schema_version": REVIEW_PROVENANCE_VERSION,
    "author_task_id": "/root",
    "author_run_id": "theater-repair-author-20260814-01",
    "reviewer_task_id": "/root/theater_repair2_event_a",
    "reviewer_run_id": "event-a-830C9C10-1557-4AF6-95B3-95BDC71E7689",
    "input_fingerprint": blind_cards_fingerprint(cards),
    "raw_response_artifact": ".internal/event-a-repair2-raw-response.md",
    "raw_response_fingerprint": review_response_fingerprint(raw_response),
    "output_fingerprint": "",
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
stage = load(stage_path)
visual_review = stage["reviews"]["visual_reviewer"]
visual_review["status"] = "PASS"
visual_review["issues"] = []
done_line = "fresh repaired copy-hidden director_storyboard Event A: PASS"
if done_line not in visual_review.setdefault("done", []):
    visual_review["done"].append(done_line)
stage_path.write_text(json.dumps(stage, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

print(
    json.dumps(
        {
            "status": "PASS",
            "reviewer_task_id": director["reviewer_id"],
            "reviewer_run_id": director["review_provenance"]["reviewer_run_id"],
            "director_event_fingerprint": director["director_event_fingerprint"],
        },
        indent=2,
    )
)
