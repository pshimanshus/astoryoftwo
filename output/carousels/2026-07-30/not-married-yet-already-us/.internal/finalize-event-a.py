#!/usr/bin/env python3
"""Persist the fresh copy-hidden Event A for this carousel package."""

from __future__ import annotations

import argparse
from copy import deepcopy
import json
from pathlib import Path
import tempfile
from typing import Any


SCRIPT_PATH = Path(__file__).resolve()
PROJECT_ROOT = next(
    parent for parent in SCRIPT_PATH.parents if (parent / "pipeline").is_dir()
)
PACKAGE = SCRIPT_PATH.parents[1]

import sys

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from pipeline.stages.carousel_format_contract import (
    locked_format_contract_fingerprint,
    locked_formats,
)
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


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def atomic_json(path: Path, payload: Any) -> None:
    with tempfile.NamedTemporaryFile(
        "w",
        encoding="utf-8",
        dir=path.parent,
        prefix=f".{path.name}.",
        suffix=".tmp",
        delete=False,
    ) as handle:
        json.dump(payload, handle, indent=2, ensure_ascii=False)
        handle.write("\n")
        staged = Path(handle.name)
    staged.replace(path)


CARDS = [
    {
        "slide": 1,
        "visible_people": ["the woman", "the man", "two distant office coworkers"],
        "visible_setting": "A warm office-building lobby and cafe area in morning light.",
        "observable_action": "The woman hands the man his forgotten ID lanyard while he gives her a takeaway coffee.",
        "hands_and_contact": "Each partner owns one clearly visible object and their free hands remain naturally readable.",
        "gaze": "The couple look at each other with tired, practiced amusement.",
        "body_blocking": "They meet at conversational distance in the foreground while the coworkers remain clearly background figures.",
        "object_state": "The ID lanyard moves toward the man and the coffee moves toward the woman.",
        "camera_view": "A medium-wide lobby establishing shot keeps both exchanges and the office context legible.",
        "visible_continuity": "The ID, coffee, office clothes, and background coworkers establish the next office beat.",
    },
    {
        "slide": 2,
        "visible_people": ["the man", "two office coworkers"],
        "visible_setting": "The same office morning, now beside a desk or meeting area.",
        "observable_action": "The man pauses two waiting coworkers with one raised finger while holding a phone to his ear.",
        "hands_and_contact": "One hand owns the phone at his ear and the other forms a clear one-minute gesture.",
        "gaze": "The man listens into the call while both coworkers look toward him for an answer.",
        "body_blocking": "The man stands slightly apart as the coworkers angle toward him in visible expectation.",
        "object_state": "A single plain phone is in active call position; office materials remain secondary.",
        "camera_view": "A medium office group shot gives the man and both waiting reactions equal readability.",
        "visible_continuity": "The same man, clothes, coworkers, and morning setting carry forward from the lobby.",
    },
    {
        "slide": 3,
        "visible_people": ["the woman", "the man"],
        "visible_setting": "A lived-in dining room that evening with a table, laptop, papers, pen, and two tiny fabric swatches.",
        "observable_action": "The couple sit opposite each other and lean over a small household choice like a formal meeting.",
        "hands_and_contact": "Both sets of hands point, hold a pen, or rest near separate papers without overlap.",
        "gaze": "Their eye-lines converge on the tiny fabric swatches and paperwork.",
        "body_blocking": "They mirror each other across the table with exaggerated serious posture.",
        "object_state": "Two small curtain swatches sit at the center as the visibly modest subject of the oversized meeting.",
        "camera_view": "A symmetrical medium-wide dining-table shot sells the two-person meeting geometry.",
        "visible_continuity": "This begins the evening sequence and locks the room, table objects, and outfits for the following slides.",
    },
    {
        "slide": 4,
        "visible_people": ["the woman", "the man"],
        "visible_setting": "The same dining room, table, and evening light.",
        "observable_action": "The man folds over one alarming work document while the woman looks up and notices the change.",
        "hands_and_contact": "The man grips the page with both hands; the woman pauses with her hands visibly separate across the table.",
        "gaze": "His gaze fixes on the document while hers fixes on his distressed face and posture.",
        "body_blocking": "His posture collapses inward while she remains upright across the table.",
        "object_state": "One work document and the laptop become the clear source of pressure; the household swatches recede.",
        "camera_view": "An over-table medium two-shot favors the man while preserving the woman's noticing reaction.",
        "visible_continuity": "The same evening wardrobe, table geography, laptop, papers, and pen remain traceable.",
    },
    {
        "slide": 5,
        "visible_people": ["the woman", "the man"],
        "visible_setting": "The same dining table moments later.",
        "observable_action": "Both partners now bend over the same work document and laptop with matching tension.",
        "hands_and_contact": "Each has distinct hands beside the same page, pointing to different parts without anatomical overlap.",
        "gaze": "Both eye-lines converge on the same problem.",
        "body_blocking": "Their furrowed brows, shoulders, and forward lean visibly mirror one another.",
        "object_state": "The same single problem document is now physically centered between both partners.",
        "camera_view": "A tighter overhead-leaning two-shot makes the shared stress pattern immediately visible.",
        "visible_continuity": "The document transfers from one person's isolated worry into one shared visual field.",
    },
    {
        "slide": 6,
        "visible_people": ["the woman", "the man"],
        "visible_setting": "The same living and dining area moments later, with the laptop and document still visible behind the action.",
        "observable_action": "The woman has just thrown one cushion and grips a second while the man grips a third with both hands, ready to throw back.",
        "hands_and_contact": "Exactly four traceable hands own exactly three cushions: one airborne, one in the woman's hand, and one in both of the man's hands.",
        "gaze": "They glare directly at each other with open mouths mid-argument and no smiles.",
        "body_blocking": "Both have planted feet, tense shoulders, tight brows, and opposing torsos with no playful bounce.",
        "object_state": "Exactly three cushions carry the escalation while the earlier work problem remains visible as the preceding trigger.",
        "camera_view": "A low wide full-body angle keeps both people, every limb, and all three cushions unobscured.",
        "visible_continuity": "The same room, evening outfits, laptop, work document, sofa, and coffee table remain recognizable.",
    },
    {
        "slide": 7,
        "visible_people": ["the woman", "the man"],
        "visible_setting": "The visibly messy same living room five minutes later, opening naturally toward the front door.",
        "observable_action": "The unsmiling man puts on his shoes with an office bag ready while the woman stands apart with folded arms and a briefly softened face.",
        "hands_and_contact": "His hands work at his own shoe and bag; her folded hands stay against her own body with no reaching contact.",
        "gaze": "Her guarded gaze follows him while he concentrates on leaving.",
        "body_blocking": "The physical distance and separate postures preserve unresolved anger even as concern appears.",
        "object_state": "All three fight cushions lie scattered in traceable positions and the office bag is prepared for departure.",
        "camera_view": "A medium-wide eye-level view includes both people, the room aftermath, his shoes, and the exit path.",
        "visible_continuity": "The same fight room and props remain while the man's outward departure begins.",
    },
    {
        "slide": 8,
        "visible_people": ["the woman", "the man"],
        "visible_setting": "A long apartment corridor seen from behind the departing man, with the open apartment door behind him.",
        "observable_action": "The man walks outward with his bag while the woman remains inside, sharply picks up one fallen cushion, and turns away.",
        "hands_and_contact": "His hand owns the bag; her hands own one cushion; neither person reaches toward the other.",
        "gaze": "His unsmiling profile faces down the corridor while her gaze turns back into the room.",
        "body_blocking": "His hips, feet, and shoulders all travel away; her smaller figure stays behind the threshold.",
        "object_state": "His office bag moves outward while the same cushion remains inside with her.",
        "camera_view": "A long wide corridor shot makes outward direction, separation, and the single doorway unambiguous.",
        "visible_continuity": "The same clothes, bag, cushion set, apartment door, and anger continue directly from the previous beat.",
    },
    {
        "slide": 9,
        "visible_people": ["the woman"],
        "visible_setting": "The same living-room sofa later that night after the man has left.",
        "observable_action": "The woman presses one plain phone to her ear while knotting a cushion with her free hand.",
        "hands_and_contact": "One hand holds the phone at her ear and the other visibly grips the cushion; both hands remain distinct.",
        "gaze": "Her eyes lower with concern even though her jaw and shoulders still hold irritation.",
        "body_blocking": "She sits alone and curled slightly inward rather than moving toward the door.",
        "object_state": "One of the same cushions rests in her lap, the work document remains nearby, and the phone is in live-call position.",
        "camera_view": "An intimate medium close-up keeps the phone-to-ear gesture, cushion grip, and mixed expression readable.",
        "visible_continuity": "The unchanged room, outfit, cushions, and work document prove that this call follows the departure.",
    },
    {
        "slide": 10,
        "visible_people": ["the man"],
        "visible_setting": "The man's separate modest home at night, just inside his own front door.",
        "observable_action": "He finishes unlocking his door while pressing one plain phone to his ear and visibly relaxing.",
        "hands_and_contact": "One hand owns the phone at his ear while the other remains near the ordinary key and lock.",
        "gaze": "His listening gaze and softened face angle into the call rather than toward another visible person.",
        "body_blocking": "His lowered shoulders and grounded stance show relief after arriving alone.",
        "object_state": "His office bag and evening outfit continue from the corridor; one ordinary key and one phone belong only to him.",
        "camera_view": "A medium doorway interior shot clearly establishes a different home without splitting the frame.",
        "visible_continuity": "The same man, bag, clothes, and active phone call answer the woman's preceding call from a separate location.",
    },
    {
        "slide": 11,
        "visible_people": ["the woman", "the man"],
        "visible_setting": "The office-building lobby and cafe again on the next morning.",
        "observable_action": "The woman again brings his ID lanyard while he again brings her coffee, both tired but gently amused.",
        "hands_and_contact": "Their two object exchanges repeat with clear ownership and naturally separate hands.",
        "gaze": "They share a quiet, knowing look after the previous night's conflict.",
        "body_blocking": "They stand comfortably close without a theatrical embrace or romantic pose.",
        "object_state": "The ID and coffee return in the same reciprocal arrangement as the opening frame.",
        "camera_view": "A medium-wide visual rhyme with frame one makes the bookend instantly recognizable.",
        "visible_continuity": "The repeated lobby, ID, coffee, and habitual exchange show the relationship ritual surviving the argument.",
    },
]


DIRECTION = [
    {
        "job": "establish the reciprocal morning habit",
        "action": ("both partners", "exchange the forgotten ID and usual coffee", "ID lanyard and takeaway coffee", "their automatic familiarity becomes visible"),
        "pov": ("shared observer", "they already perform reciprocal care by habit", "amused recognition"),
        "shot": ("medium wide", "eye level", "from the lobby circulation path", "the reciprocal exchange", "establish both the habit and office world at once"),
        "blocking": ("each person's hands own one exchanged object", "mutual", "comfortable conversational distance", "relaxed mirrored stance"),
        "setting": ("office lobby cafe", "morning", "soft window light", "office coworkers and daily objects establish routine"),
        "evidence": ("ID and coffee", "each partner brings the exact thing the other needs", "prove reciprocal habit"),
        "people": 4,
        "background": ["two office coworkers"],
    },
    {
        "job": "prove automatic partner consultation at work",
        "action": ("the man", "pauses waiting coworkers to call his partner", "phone and one-minute hand gesture", "the coworkers wait with familiar impatience"),
        "pov": ("the waiting coworkers", "consulting her is his automatic first move", "affectionate exasperation"),
        "shot": ("medium group", "eye level", "beside the office meeting area", "the phone-to-ear and raised finger", "show both the habit and its social witness"),
        "blocking": ("one phone hand and one raised-finger hand", "coworkers toward him while he listens", "coworkers clustered across a small gap", "he stands centered and temporarily unavailable"),
        "setting": ("office meeting area", "same morning", "clean overhead office light softened by windows", "the same coworkers and wardrobe continue from the lobby"),
        "evidence": ("phone and waiting coworkers", "he interrupts the live plan to consult her", "make consultation behavior public and specific"),
        "people": 3,
        "background": [],
    },
    {
        "job": "domestic meeting escalation",
        "action": ("the couple", "debate a tiny home choice with mock-formal seriousness", "two curtain swatches, papers, laptop, and pen", "a small decision becomes a full shared process"),
        "pov": ("shared observer", "their partnership turns tiny choices into joint meetings", "recognition and gentle comedy"),
        "shot": ("medium wide", "slightly elevated", "centered across the dining table", "their mirrored formal posture", "contrast a tiny choice with oversized seriousness"),
        "blocking": ("all hands remain separate around papers and swatches", "both toward the swatches", "opposite sides of the table", "matching forward lean"),
        "setting": ("home dining table", "evening", "warm practical pendant light", "table objects lock the evening location"),
        "evidence": ("curtain swatches", "two tiny samples sit at the center of a full meeting", "prove the decision is small and jointly owned"),
        "people": 2,
        "background": [],
    },
    {
        "job": "individual problem setup",
        "action": ("the man", "absorbs an alarming work problem", "one work document and laptop", "the woman notices his sudden collapse"),
        "pov": ("the woman", "the pressure begins with him alone", "concern"),
        "shot": ("medium two shot", "slightly over table", "from the woman's side of the table", "his gripped document and folded posture", "separate the original owner of the problem before it spreads"),
        "blocking": ("his two hands grip the page while hers pause apart", "he sees the page and she sees him", "table width separates them", "his torso folds while hers turns alert"),
        "setting": ("same dining room", "same evening", "same warm pendant light", "unchanged table and outfits prove immediacy"),
        "evidence": ("work document", "only he grips the alarming page", "identify whose problem it starts as"),
        "people": 2,
        "background": [],
    },
    {
        "job": "shared stress transfer",
        "action": ("both partners", "study the same problem together", "the same document and laptop", "their posture and worry become mirrored"),
        "pov": ("shared observer", "his pressure has become theirs", "recognition of emotional merging"),
        "shot": ("tight two shot", "slightly overhead", "above the table edge", "the mirrored lean around one document", "make stress transfer visible without explanatory symbols"),
        "blocking": ("distinct hands flank the same page", "both converge on the same problem", "their shoulders nearly meet over the table", "matching tense forward lean"),
        "setting": ("same dining table", "moments later", "same pendant light", "same page and laptop carry the exact problem forward"),
        "evidence": ("mirrored bodies around one document", "both now hold visible tension over the same source", "prove shared stress"),
        "people": 2,
        "background": [],
    },
    {
        "job": "escalate shared stress into mutual argument",
        "action": ("both partners", "argue with opposing cushion throws", "exactly three cushions", "shared stress erupts into real conflict"),
        "pov": ("shared observer", "the fight is mutual, ordinary, and genuinely heated", "surprise without romanticizing anger"),
        "shot": ("low wide full body", "low angle", "from the open side of the living room", "both planted bodies and the airborne cushion", "prove genuine friction and preserve anatomy"),
        "blocking": ("four distinct hands own three traceable cushions", "direct glare between partners", "several feet of charged space", "planted feet, tense shoulders, open mouths, no smiles"),
        "setting": ("same living and dining area", "moments later", "same evening practical light", "the laptop and document remain visible as the pressure trace"),
        "evidence": ("cushions and body tension", "one cushion is airborne while both partners remain unsmiling and braced", "distinguish conflict from play"),
        "people": 2,
        "background": [],
    },
    {
        "job": "interrupt unresolved anger with visible concern",
        "action": ("the man", "puts on shoes and prepares to leave", "shoes, office bag, and scattered cushions", "the woman's guarded face softens despite unresolved anger"),
        "pov": ("shared observer", "departure is real but concern has not disappeared", "tension mixed with care"),
        "shot": ("medium wide", "eye level", "from inside the living room toward the exit", "his departure action and her separate reaction", "hold friction and care in the same physical frame"),
        "blocking": ("his hands stay with shoes and bag while hers remain folded", "she watches him and he looks down", "clear distance without contact", "he bends to leave while she stands closed off"),
        "setting": ("same living room near the exit", "five minutes later", "same light with slightly quieter room tone", "scattered cushions preserve the immediate aftermath"),
        "evidence": ("scattered cushions and packed bag", "the fight aftermath remains while he actively leaves", "prove care occurs before reconciliation"),
        "people": 2,
        "background": [],
    },
    {
        "job": "extend separation through outward departure",
        "action": ("the man", "walks outward down the corridor", "office bag and one cushion retained inside", "the woman turns away and gathers the aftermath"),
        "pov": ("behind the departing man", "the separation continues with no return gesture", "unresolved distance"),
        "shot": ("long wide", "rear three-quarter", "in the corridor behind the man", "his outward travel with her behind the threshold", "make direction and separation impossible to misread"),
        "blocking": ("his hand owns the bag and hers owns the cushion", "their gazes diverge", "corridor depth separates foreground and doorway", "his feet and hips move outward while her torso turns inward"),
        "setting": ("apartment corridor and open front door", "same night", "corridor practical light", "bag, clothes, door, and cushion continue the exit"),
        "evidence": ("feet, doorway, and bag", "all directional cues carry him away from her", "protect outward departure continuity"),
        "people": 2,
        "background": [],
    },
    {
        "job": "remote care initiation",
        "action": ("the woman", "calls from the sofa while still holding the fight cushion", "one phone, one cushion, and the work document", "concern overtakes part of her anger"),
        "pov": ("the woman", "she chooses contact without erasing the fight", "tender concern under irritation"),
        "shot": ("medium close up", "eye level", "from the opposite sofa arm", "phone at ear and knotted cushion", "keep mixed emotion and remote-call action legible"),
        "blocking": ("one hand at the phone and one gripping the cushion", "lowered concerned gaze", "alone on the sofa", "curled inward with residual jaw tension"),
        "setting": ("same living-room sofa", "later that night", "one warm lamp", "unchanged cushions, document, and outfit preserve aftermath"),
        "evidence": ("phone and cushion grip", "she contacts him while physically holding the argument residue", "prove care survives anger"),
        "people": 1,
        "background": [],
    },
    {
        "job": "remote care answer",
        "action": ("the man", "answers the live call after reaching his own home", "one phone, one ordinary key, and the office bag", "his shoulders visibly release"),
        "pov": ("the man", "her concern reaches him across separate homes", "relief"),
        "shot": ("medium single", "eye level", "inside his separate entryway", "phone at ear and softened posture", "answer the preceding call without a split screen"),
        "blocking": ("one phone hand and one key hand remain distinct", "listening gaze into the call", "he is alone in the entryway", "grounded stance with lowered shoulders"),
        "setting": ("his separate home entry", "same night", "cooler entry practical light", "same clothes and bag connect the corridor journey"),
        "evidence": ("phone, key, and bag", "the same departing man is now safely inside another home and answering", "prove distance and successful contact"),
        "people": 1,
        "background": [],
    },
    {
        "job": "pay off the reciprocal habit after conflict",
        "action": ("both partners", "repeat the ID-and-coffee exchange the next morning", "ID lanyard and takeaway coffee", "the ordinary ritual survives the friction"),
        "pov": ("shared observer", "their partnership is already lived rather than ceremonially declared", "earned warmth"),
        "shot": ("medium wide", "eye level", "from the same lobby circulation path as the opening", "the repeated reciprocal exchange", "close the arc through a visual rhyme rather than a romantic pose"),
        "blocking": ("each partner owns one offered object", "quiet mutual look", "comfortable habitual distance", "tired but open posture"),
        "setting": ("same office lobby cafe", "next morning", "soft morning window light", "the opening place and objects return with changed emotional meaning"),
        "evidence": ("repeated ID and coffee", "the exact opening ritual recurs after conflict", "prove enduring partnership through behavior"),
        "people": 2,
        "background": [],
    },
]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--reviewer-run-id", required=True)
    args = parser.parse_args()

    plan_path = PACKAGE / "visual-plan-quality.json"
    slides_path = PACKAGE / "slides.json"
    raw_path = PACKAGE / "event-a-blind-critic-raw.json"
    stage_path = PACKAGE / "stage-reviews.json"
    ledger_path = PACKAGE / "run-ledger.json"

    plan = read_json(plan_path)
    slides = read_json(slides_path)
    raw_text = raw_path.read_text(encoding="utf-8")
    raw = json.loads(raw_text)
    if raw.get("verdict") != "PASS":
        raise ValueError("The independent blind critic did not pass the route.")
    frame_reads = raw.get("frame_reads")
    if not isinstance(frame_reads, list) or len(frame_reads) != len(CARDS):
        raise ValueError("The independent response must cover all 11 frames.")
    if any(item.get("clarity") != "PASS" for item in frame_reads):
        raise ValueError("At least one blind frame remains unresolved.")

    directed_slides = []
    for card, authored, critic in zip(CARDS, DIRECTION, frame_reads, strict=True):
        if int(critic.get("frame", 0)) != card["slide"]:
            raise ValueError("Critic frame numbering does not match the blind cards.")
        action = authored["action"]
        pov = authored["pov"]
        shot = authored["shot"]
        blocking = authored["blocking"]
        setting = authored["setting"]
        evidence = authored["evidence"]
        directed_slides.append(
            {
                "slide": card["slide"],
                "status": "PASS",
                "inference_match": True,
                "narrative_job": authored["job"],
                "silent_read": critic["immediate_read"],
                "change_from_previous": (
                    "This opening frame establishes the recurring reciprocal ritual."
                    if card["slide"] == 1
                    else card["visible_continuity"]
                ),
                "critic_evidence": critic["immediate_read"],
                "staged_action": {
                    "subject": action[0],
                    "action": action[1],
                    "target_or_object": action[2],
                    "reaction_or_consequence": action[3],
                },
                "pov": {
                    "owner": pov[0],
                    "audience_knows": pov[1],
                    "audience_feels": pov[2],
                },
                "shot": {
                    "size": shot[0],
                    "angle": shot[1],
                    "camera_position": shot[2],
                    "focal_subject": shot[3],
                    "story_reason": shot[4],
                },
                "blocking": {
                    "hands": blocking[0],
                    "gaze": blocking[1],
                    "body_distance": blocking[2],
                    "posture_or_feet": blocking[3],
                },
                "setting": {
                    "sub_location": setting[0],
                    "time": setting[1],
                    "motivated_light": setting[2],
                    "story_trace": setting[3],
                },
                "story_evidence": [
                    {
                        "carrier": evidence[0],
                        "observable_state": evidence[1],
                        "narrative_job": evidence[2],
                    }
                ],
                "text_image_relationship": "interdependent",
                "continuity": {
                    "incoming_state": (
                        "The day begins with a familiar reciprocal habit."
                        if card["slide"] == 1
                        else CARDS[card["slide"] - 2]["visible_continuity"]
                    ),
                    "outgoing_state": card["visible_continuity"],
                },
                "entity_contract": {
                    "expected_people": authored["people"],
                    "background_people": authored["background"],
                    "reflections": [],
                    "forbidden_entities": [
                        "duplicate foreground people",
                        "unowned hands or limbs",
                        "mirrors or reflections that resemble extra people",
                    ],
                },
                "unresolved_ambiguities": [],
                "resolved_ambiguities": [],
            }
        )

    blind_hash = blind_cards_fingerprint(CARDS)
    author_task_id = "/root"
    author_run_id = "019fb36b-1433-7623-beee-a485df9730d2"
    reviewer_task_id = "/root/blind_storyboard_event_a"
    director = {
        "status": "PASS",
        "event": "copy_hidden_storyboard_read",
        "copy_locked": True,
        "copy_hidden": True,
        "intent_hidden": True,
        "copy_lock_evidence": "The exact 11-slide copy and the Instagram-post-only format contract were locked before the independent review.",
        "author_id": author_task_id,
        "reviewer_id": reviewer_task_id,
        "reviewer_evidence": "A fresh orchestrated critic received only the 11 observable frame cards in order and returned its inferred story before seeing slide copy, title, intent labels, or source files.",
        "requested_formats": list(locked_formats(PACKAGE)),
        "format_contract_fingerprint": locked_format_contract_fingerprint(PACKAGE),
        "creator_correction_fingerprint": current_creator_correction_fingerprint(PACKAGE),
        "generation_payload_fingerprint": current_generation_payload_fingerprint(PACKAGE),
        "blind_cards": deepcopy(CARDS),
        "blind_input_fingerprint": blind_hash,
        "source_fingerprint": storyboard_source_fingerprint(slides),
        "sequence_mode": "montage_with_arc",
        "physical_event": "A practiced office habit expands into shared household decisions and shared work stress, erupts as a cushion fight, separates the couple across two homes, and returns to the same morning ritual.",
        "emotional_arc": "Automatic ease becomes shared pressure, real anger, guarded concern, remote relief, and finally tired earned warmth.",
        "relationship_change": "The repeated closing ritual now proves that care and partnership survived genuine friction rather than existing only in conflict-free moments.",
        "sequence_read": raw["inferred_story"],
        "visual_variables": ["body distance", "object ownership"],
        "hero_receipt_slide": 6,
        "setup_payoff_ledger": [
            {
                "setup": "Frame 1 establishes the reciprocal ID-and-coffee morning ritual.",
                "payoff": "Frame 11 repeats the same exchange after the argument and remote check-in.",
                "changed_meaning": "An amusing habit becomes proof that their ordinary partnership survives friction.",
            },
            {
                "setup": "Frames 4 and 5 visibly transfer one work problem into shared stress.",
                "payoff": "Frames 6 through 10 convert that pressure into conflict, departure, and a concerned remote call.",
                "changed_meaning": "Shared emotional load is shown as both intimacy and the source of real friction.",
            },
        ],
        "object_motif_ledger": [
            {
                "object": "ID lanyard and takeaway coffee",
                "initial_state": "They are exchanged automatically in the opening office morning.",
                "later_state": "They return in the final office morning after the argument.",
                "story_job": "Bookend the sequence with reciprocal habit and prove enduring partnership.",
            },
            {
                "object": "three living-room cushions",
                "initial_state": "They become clearly owned projectiles during the genuine argument.",
                "later_state": "They remain scattered, one is gathered in anger, and one is gripped during the concerned call.",
                "story_job": "Carry the physical trace of conflict into the care beat without erasing the anger.",
            },
        ],
        "slides": directed_slides,
        "issues": [],
        "director_event_fingerprint_version": DIRECTOR_EVENT_FINGERPRINT_VERSION,
        "review_provenance": {
            "schema_version": REVIEW_PROVENANCE_VERSION,
            "author_task_id": author_task_id,
            "author_run_id": author_run_id,
            "reviewer_task_id": reviewer_task_id,
            "reviewer_run_id": args.reviewer_run_id,
            "input_fingerprint": blind_hash,
            "raw_response_artifact": raw_path.relative_to(PACKAGE).as_posix(),
            "raw_response_fingerprint": review_response_fingerprint(raw_text),
            "output_fingerprint": "",
        },
    }
    director["review_provenance"]["output_fingerprint"] = (
        director_review_output_fingerprint(director)
    )
    director["director_event_fingerprint"] = director_event_fingerprint(director)

    updated_plan = deepcopy(plan)
    updated_plan.update({"status": "PASS", "decision": "GO", "can_generate": True, "issues": []})
    updated_plan["director_storyboard"] = director
    issues = validate_director_storyboard(
        updated_plan,
        slide_count=len(slides),
        expected_slides=slides,
        expected_formats=locked_formats(PACKAGE),
        expected_format_contract_fingerprint=locked_format_contract_fingerprint(PACKAGE),
        expected_creator_correction_fingerprint=current_creator_correction_fingerprint(PACKAGE),
        expected_generation_payload_fingerprint=current_generation_payload_fingerprint(PACKAGE),
        provenance_package_dir=PACKAGE,
    )
    if issues:
        raise ValueError("Event A validation failed: " + "; ".join(issues))

    stage_reviews = read_json(stage_path)
    visual_review = stage_reviews["reviews"]["visual_reviewer"]
    visual_review["status"] = "PASS"
    visual_review["issues"] = []
    marker = "fresh copy-hidden director_storyboard Event A: PASS"
    if marker not in visual_review["done"]:
        visual_review["done"].append(marker)

    ledger = read_json(ledger_path)
    ledger["stage_statuses"]["visual"] = "PASS"

    atomic_json(plan_path, updated_plan)
    atomic_json(stage_path, stage_reviews)
    atomic_json(ledger_path, ledger)
    print(
        json.dumps(
            {
                "status": "PASS",
                "reviewer_task_id": reviewer_task_id,
                "reviewer_run_id": args.reviewer_run_id,
                "blind_input_fingerprint": blind_hash,
                "director_event_fingerprint": director["director_event_fingerprint"],
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
