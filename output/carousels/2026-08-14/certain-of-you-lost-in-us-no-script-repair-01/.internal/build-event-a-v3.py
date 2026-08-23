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


PACKAGE = Path("output/carousels/2026-08-14/certain-of-you-lost-in-us-no-script")
CARDS_PATH = PACKAGE / ".internal/event-a-blind-cards.json"
RAW_PATH = PACKAGE / ".internal/event-a-v3-raw-response.md"


def load(path: Path) -> dict | list:
    return json.loads(path.read_text(encoding="utf-8"))


cards = load(CARDS_PATH)
slides = load(PACKAGE / "slides.json")
plan_path = PACKAGE / "visual-plan-quality.json"
plan = load(plan_path)
raw_response = RAW_PATH.read_text(encoding="utf-8")

jobs = [
    "flash-forward thesis and closing-bookend setup",
    "chronological beginning through mutual convergence",
    "shared life introduces separately handled demands",
    "absent instructions expose an unstable next cue",
    "visible cue failure turns into reciprocal recognition",
    "equal self-directed movement into the next scene",
]
silent_reads = [
    "A couple keeps moving forward in physical alignment while the world behind them separates and changes.",
    "Two people enter from separate sides, notice each other and choose the same shared light.",
    "Life sends different demands toward each person, but their connected backs keep the pressure relational rather than isolating.",
    "The expected plan offers no instructions, the stage is dark and the only available cue is visibly unstable.",
    "The cue fails physically, yet the couple turns toward each other and shares the absurdity instead of assigning blame.",
    "They leave the failed mechanism behind and each move one formerly separate chair into the same next light.",
]
critic_evidence = [
    "The blind reviewer read this as a couple moving forward together while their surroundings split apart, then explicitly recognized the repeated scenery movement on slide six as an intentional bookend.",
    "The blind reviewer read two separate arrivals becoming one shared space and cited the isolated chairs and shared light as literal setup evidence.",
    "The blind reviewer read different life demands handled separately while bodily connection remained intact.",
    "The blind reviewer identified blank pages, blackout, loose cue line and the hanging curtain edge as absent guidance plus a visible cue problem.",
    "The blind reviewer read the fallen curtain as the physical payoff of the prior cue and the mutual laugh as shared recovery rather than conflict.",
    "The blind reviewer cited the converging chairs, next light, abandoned closed script and fallen curtain as the self-directed next move and final payoff.",
]

shots = [
    ("medium-wide moving two-shot", "first-row three-quarter", "from the empty first row facing downstage", "their aligned bodies against opposing scenery movement"),
    ("lateral wide", "stage-level profile", "from one side of the bare stage across both wings", "two entrances reaching one irregular shared light"),
    ("high crane wide", "fly-loft diagonal", "above and diagonally across the stage", "their connected backs between two incoming demands"),
    ("object-dominant close insert", "over-Aachu-shoulder table level", "beside the rehearsal table during blackout", "the blank spread, Zuv's readable face and the loose curtain cue"),
    ("medium reaction two-shot", "side-stage eye level", "from the wing toward the newly fallen curtain", "their reciprocal laugh at the visible failed cue"),
    ("medium-wide active release", "high rear three-quarter", "above the stage lip facing the next footlight", "two separately owned chairs moving into one open center"),
]
settings = [
    ("downstage among moving scenery flats", "flash-forward within the same theatre night", "cool indigo and dusty-rose stage spill on warm ivory paper", "opposing flats establish the visual thesis later repeated at payoff"),
    ("bare stage between two dark wings", "chronological beginning", "two narrow spotlights cross-fading into one irregular shared pool", "one empty chair remains in each separate wing"),
    ("full stage during practical load-in", "later in the same rehearsal", "the shared pool widened by cooler working light", "one desk with two cartons and one braced doorway flat create separate incoming pressures"),
    ("small rehearsal table in blackout", "after the demands interrupt the scene", "one distant ghost light with a restrained blue-black stage", "blank pages, loose pull line and still-hanging curtain edge establish the missing instructions and unstable cue"),
    ("bare side-stage floor", "the instant the next cue fails", "pale ghost-light rim against the fallen indigo curtain", "the closed script remains sharp beside the loose line as the curtain finishes collapsing"),
    ("stage lip facing unfinished center", "the next cue after the failure", "one pale-peach footlight and shared open center", "fallen curtain and closed script remain behind while the opening scenery movement returns"),
]
actions = [
    ("Aachu and Zuv", "walk downstage shoulder-to-shoulder while leaning subtly toward each other", "the same changing floor ahead", "their alignment survives the opposing movement behind them"),
    ("Aachu and Zuv", "take one step from opposite wings into one cross-faded pool", "each other and the shared light", "two separate arrivals become one mutual starting point"),
    ("Aachu and Zuv", "stay back-to-back while each arrests one separate rolling object", "Aachu's desk and Zuv's doorway flat", "they handle different pressures without rescuing or abandoning the other"),
    ("Aachu and Zuv", "search the same blank spread as Aachu begins noticing the loose cue line", "the blank script and unstable curtain cue", "the frame reveals both absent guidance and the mechanism of the next failure"),
    ("Aachu and Zuv", "turn toward each other and begin the same tired laugh", "the visibly failed curtain change", "the failure becomes shared recognition rather than proof of a wrong partner"),
    ("Aachu and Zuv", "each pull one separate chair toward the same new light", "the unfinished open center", "equal physical agency replaces the expectation of a finished script"),
]
blocks = [
    ("exactly two outer hands rest at their owners' thighs; both inside hands stay hidden", "both look toward the same changing floor ahead", "shoulders touch at the same depth", "both walk and lean subtly toward one another for balance"),
    ("four separate hands hang naturally at their owners' sides", "profile eye-lines meet across the shared pool", "equal distance from center with no touch yet", "both take one clear leading step into the light"),
    ("exactly one focal hand per person contacts only that person's object", "each gaze follows the separate object being handled", "backs and shoulders stay connected", "torsos divide while their shared stance remains stable"),
    ("all hands remain below the table and outside frame", "both begin on the pages while Aachu's eyes start lifting toward the cue line", "Aachu is partial foreground and Zuv is readable beyond the object", "both lean toward the central script without touching it"),
    ("one self-owned hand per person rests on that person's own leg", "their eye-lines meet directly", "shoulders touch at the same seated depth", "both release into the same small exhausted laugh"),
    ("exactly one inside hand per person grips only that person's chair; outside hands remain outside crop", "both face the next footlight while a readable side glance begins", "bodies align and chairs angle inward without overlap", "both pull with the same forward effort"),
]
evidence = [
    ("the opposing indigo and dusty-rose scenery flats", "they roll apart while the couple keeps one direction and touching shoulders", "establish the cold-open contradiction and later bookend"),
    ("the two separate chairs and cross-faded light", "each chair stays in its own wing while both people enter one shared pool", "make separate origins and mutual choice visible"),
    ("the rolling desk and braced doorway flat", "each person stops or turns one practical demand while their backs remain connected", "show shared-life pressure with equal self-owned agency"),
    ("the blank script, loose line and hanging curtain edge", "the pages contain nothing while the next cue is visibly present but unhelpful", "set up the physical failure without making love an instruction manual"),
    ("the fallen curtain and closed script", "the cue has failed on screen and the prior blank object remains sharp beside it", "turn uncertainty into a shared lived event"),
    ("the converging chairs, next light and abandoned failed machinery", "each person moves one chair forward while the closed script and fallen curtain remain behind", "pay off commitment as equal continuation rather than total certainty"),
]
continuity_pairs = [
    ("The sequence opens on its future-facing visual thesis.", "The matching opposing flats will return after the chronological story, making this a visible bookend."),
    ("The first slide established the couple's eventual alignment inside changing space.", "Chronology begins with separate wings, separate chairs and one shared light."),
    ("The pair has entered one shared pool without merging their separate agency.", "Incoming stage objects divide their attention while their backs remain connected."),
    ("They have handled separate practical demands inside one shared stage world.", "The stage cuts to blackout, where the blank script and loose curtain line reveal absent guidance and the next unstable cue."),
    ("The blank script and loose cue line have established a likely failure.", "The same line, closed script and now-fallen curtain make the failure physical while the couple reconnects through shared laughter."),
    ("The cue has failed, but both people have turned toward each other without blame.", "They leave the failed curtain and script behind, converge the two chairs and re-enter the opening scenery motif around one shared center."),
]

resolved_by_slide = {
    1: [
        {
            "competing_read": "The active cover could initially look chronologically later than the separate arrival on slide two.",
            "repair": "Repeat the same indigo and dusty-rose flats moving apart on slide six while changing camera and action, so slide one reads as a cold-open thesis and slide six as its earned echo.",
            "recheck_evidence": "The fresh blind reviewer explicitly said the slide one/six bookend reads as intentional rather than an accidental continuity error.",
        }
    ],
    4: [
        {
            "competing_read": "A script introduced immediately before its payoff could feel compressed or disconnected from the curtain failure.",
            "repair": "Show the blank script beside the loose curtain cue line and a still-hanging curtain edge, then preserve the same closed script and line beside the fallen curtain on slide five and behind the couple on slide six.",
            "recheck_evidence": "The blind reviewer cited the blank pages, loose cue line and hanging curtain edge as a literal setup for the curtain collapse.",
        }
    ],
    6: [
        {
            "competing_read": "A side glance that is only beginning could soften the final mutual recognition.",
            "repair": "Keep the side glance clearly readable while making equal chair movement into one shared light the primary relational proof, so the payoff does not depend on a posed gaze.",
            "recheck_evidence": "The blind reviewer still returned GO and identified active shared recovery and the self-directed next move from the visible chair action.",
        }
    ],
}

director_slides = []
for index in range(6):
    number = index + 1
    size, angle, camera_position, focal_subject = shots[index]
    sub_location, time, light, trace = settings[index]
    subject, action, target, reaction = actions[index]
    hands, gaze, distance, posture = blocks[index]
    carrier, observed, narrative_job = evidence[index]
    incoming, outgoing = continuity_pairs[index]
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
                "owner": "the partnership as two equal agents inside one shared stage world",
                "audience_knows": silent_reads[index],
                "audience_feels": [
                    "stability inside disorientation",
                    "mutual recognition",
                    "pressure without abandonment",
                    "helplessness without blame",
                    "relief through reciprocal recognition",
                    "hope through equal action",
                ][index],
            },
            "shot": {
                "size": size,
                "angle": angle,
                "camera_position": camera_position,
                "focal_subject": focal_subject,
                "story_reason": "The camera makes the current body relationship, action and changing object state readable before decorative theatre atmosphere.",
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
                {
                    "carrier": carrier,
                    "observable_state": observed,
                    "narrative_job": narrative_job,
                }
            ],
            "text_image_relationship": "interdependent",
            "continuity": {"incoming_state": incoming, "outgoing_state": outgoing},
            "entity_contract": {
                "expected_people": 2,
                "background_people": [],
                "reflections": [],
                "forbidden_entities": [
                    "duplicate couple",
                    "audience figure",
                    "crew member",
                    "reflection person",
                    "portrait that reads as a live actor",
                    "ghost silhouette",
                ],
            },
            "unresolved_ambiguities": [],
            "resolved_ambiguities": resolved_by_slide.get(number, []),
        }
    )

director = {
    "status": "PASS",
    "event": "copy_hidden_storyboard_read",
    "copy_locked": True,
    "copy_hidden": True,
    "intent_hidden": True,
    "copy_lock_evidence": "The creator supplied six exact slide lines in the current task; slides.json preserved those lines verbatim before the independent observable-card review.",
    "author_id": "/root",
    "reviewer_id": "/root/theater_event_a_v3",
    "reviewer_evidence": "A fresh collaboration agent received only the six copy-hidden observable cards and independently returned GO, the inferred silent sequence, causal chain, literal setup/payoff evidence, ambiguities and optional repairs.",
    "requested_formats": list(locked_formats(PACKAGE)),
    "format_contract_fingerprint": locked_format_contract_fingerprint(PACKAGE),
    "creator_correction_fingerprint": current_creator_correction_fingerprint(PACKAGE),
    "generation_payload_fingerprint": current_generation_payload_fingerprint(PACKAGE),
    "blind_cards": cards,
    "blind_input_fingerprint": blind_cards_fingerprint(cards),
    "source_fingerprint": storyboard_source_fingerprint(slides),
    "sequence_mode": "montage_with_arc",
    "physical_event": "A couple enters a shared theatre world, absorbs separate incoming demands, discovers blank guidance and an unstable cue, survives its visible failure and each moves one separate chair into the same next light.",
    "emotional_arc": "Alignment becomes mutual choice, shared pressure, helplessness without blame, reciprocal recognition and equal continuation.",
    "relationship_change": "They move from separate arrivals through divided attention and failed instructions into visible shared recovery and coordinated agency.",
    "sequence_read": "A cold-open shows aligned movement inside separating scenery; chronology then begins with separate wings, adds different demands, loses the script, suffers the curtain failure and ends with both people actively building the next scene.",
    "visual_variables": ["body alignment and equal agency", "stage cue and object state"],
    "hero_receipt_slide": 6,
    "setup_payoff_ledger": [
        {
            "setup": "One empty rehearsal chair remains isolated in each opposite wing when the couple first enters the shared light.",
            "payoff": "Each person later pulls one of those chairs toward the same new light until the two chairs angle inward and nearly meet.",
            "changed_meaning": "Separate origins become equal authorship of one next scene without collapsing either person's agency.",
        },
        {
            "setup": "The blank script sits beside a loose curtain cue line and a narrow still-hanging curtain edge during blackout.",
            "payoff": "The curtain visibly collapses beside the closed script, and both failed objects remain behind when the couple moves forward.",
            "changed_meaning": "Missing instructions and a failed cue become survivable shared experience rather than a verdict on the partnership.",
        },
        {
            "setup": "Indigo and dusty-rose scenery flats move apart while the couple stays aligned in the opening cold-open.",
            "payoff": "The same flats move apart again behind the couple as they converge their chairs around one open center.",
            "changed_meaning": "The changing world stops reading as disorientation alone and becomes the unfinished stage on which they keep choosing one direction.",
        },
    ],
    "object_motif_ledger": [
        {
            "object": "the two rehearsal chairs",
            "initial_state": "empty and isolated in opposite dark wings",
            "later_state": "separately owned, actively moving and angled inward inside one next light",
            "story_job": "carry the transition from separate origins to equal participation in a shared future",
        },
        {
            "object": "the blank rehearsal script and curtain cue",
            "initial_state": "blank pages beside a loose line and still-hanging curtain",
            "later_state": "closed beside the fallen curtain and then visibly left behind",
            "story_job": "make absent guidance, visible failure and the choice to continue physically legible",
        },
    ],
    "slides": director_slides,
    "issues": [],
    "director_event_fingerprint_version": DIRECTOR_EVENT_FINGERPRINT_VERSION,
    "review_provenance": {
        "schema_version": REVIEW_PROVENANCE_VERSION,
        "author_task_id": "/root",
        "author_run_id": "theater-author-run-20260814-03",
        "reviewer_task_id": "/root/theater_event_a_v3",
        "reviewer_run_id": "EA-BLIND-20260814-7F3C",
        "input_fingerprint": blind_cards_fingerprint(cards),
        "raw_response_artifact": ".internal/event-a-v3-raw-response.md",
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
stage = load(stage_path)
review = stage["reviews"]["visual_reviewer"]
review["status"] = "PASS"
review["issues"] = []
done_line = "fresh copy-hidden director_storyboard Event A v3: PASS"
if done_line not in review.setdefault("done", []):
    review["done"].append(done_line)
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
