from __future__ import annotations

import json
import os
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


PACKAGE = Path(
    os.environ.get(
        "MOONWATER_PACKAGE",
        "output/carousels/2026-08-23/certain-of-you-lost-in-us-moonwater",
    )
)
CARDS_PATH = PACKAGE / ".internal/event-a-v2-blind-cards.json"
RAW_PATH = PACKAGE / ".internal/event-a-v3-raw-response.md"


def load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


cards = load(CARDS_PATH)
slides = load(PACKAGE / "slides.json")
plan_path = PACKAGE / "visual-plan-quality.json"
plan = load(plan_path)
raw_response = RAW_PATH.read_text(encoding="utf-8")

jobs = [
    "flash-forward contradiction and circular-wake thesis",
    "chronological shared arrival with the recurring object set",
    "rising domestic pressure and equal self-owned preparation",
    "equal effort produces visible circular failure",
    "reciprocal recognition becomes a matched physical reset",
    "the matched reset produces one coordinated next stroke",
]
silent_reads = [
    "Two people remain physically aligned on a familiar object while their shared home has become unfamiliar water.",
    "The same pair bring the central table and its surrounding domestic objects into one dry home together.",
    "As water rises, each person secures one necessary object while both keep their shared table stable.",
    "They work equally but in opposite directions, visibly spinning their raft instead of moving it forward.",
    "They reconnect, lift both complete oars and pause them at matching positions on opposite outer sides.",
    "They turn the matched start into synchronized thrust that breaks visibly through the old circular wake.",
]
shots = [
    ("extreme-wide", "high-corner cutaway", "above one apartment corner", "aligned couple, table-raft and circular wake"),
    ("lateral wide", "doorway level", "inside the room facing the single entrance", "one believable table-carrying axis"),
    ("wide", "true overhead", "directly above the flooding room", "four separately owned hands stabilizing and salvaging"),
    ("medium-wide hero", "top-down", "above the open-water raft", "opposed oar strokes and circular whirl"),
    ("wider two-shot", "water-level oblique", "beside the rear raft edge", "four hands, two complete oars and matched catch positions"),
    ("medium-wide", "rear three-quarter above water", "behind the raft facing the open horizon", "parallel strokes breaking through the old circle"),
]
settings = [
    ("flooded apartment dissolving into open water", "midnight flash-forward", "indigo moonwater on warm ivory paper", "centered lamp, parallel resting oars and three drifting room fragments establish the later object state"),
    ("dry almost-empty apartment", "chronological beginning", "soft neutral daylight with a finger-high blue threshold line", "table, lamp, oars, shelf and rug begin in ordinary positions"),
    ("same apartment in ankle-deep water", "later the same night", "silver-blue reflected light", "the lamp and oars change from waiting objects to secured supplies"),
    ("moonlit open water", "after the room dissolves", "deep indigo water and the lamp's small warm pool", "the table is now the raft and the oars visibly create the circle"),
    ("rear edge of the same raft", "moments after the failed strokes", "soft lamp light against widening moonwater", "the complete oars change from opposition to identical catch positions"),
    ("open water with no shore", "pale-peach dawn", "dawn warms the same restrained palette", "straight wakes cut through the old circle as the exact room fragments fade behind"),
]
actions = [
    ("Aachu and Zuv", "kneel shoulder-to-shoulder while the table turns without advancing", "the shared open water ahead", "their bodily alignment contrasts with the circular wake"),
    ("Aachu and Zuv", "carry one table through one doorway, one backward and one forward", "the center of the dry room", "one shared object enters on a physically credible axis"),
    ("Aachu and Zuv", "secure the lamp and tied oars while each braces the table", "two separate recurring objects and one shared stable surface", "both necessary objects reach the table before the room disappears"),
    ("Aachu and Zuv", "apply equal strokes in opposite longitudinal directions", "their separately owned oars", "the raft produces torque, a circular whirl and no forward wake"),
    ("Aachu and Zuv", "lift both blades and pause them at matching forward catch positions", "opposite outer sides of the same raft", "a shared laugh becomes an observable reciprocal reset"),
    ("Aachu and Zuv", "sweep both blades backward in the same phase", "the open water beyond the old circle", "two straight wakes carry the raft through a visible break"),
]
blocking = [
    ("two outer palms on the table; inside hands hidden", "both toward the same open water", "inside shoulders touching", "same-depth kneeling with readable three-quarter faces"),
    ("four hands on opposite short table ends", "small smile over the tabletop", "table-length separation on one doorway axis", "Aachu walks backward while Zuv follows forward"),
    ("four hands visible: lamp, table, tied oars, table", "split toward separately owned tasks", "opposite table sides", "hips brace the same level surface"),
    ("four hands in two separate complete oar grips", "both toward the spinning water", "opposite raft ends", "equal lean in counter-rotating actions"),
    ("four hands and both complete oars fully visible", "direct side glance during the laugh", "shoulders touching", "both blades raised at identical outer-side catch positions"),
    ("four hands in two complete non-crossing grips", "brief side glance while stroking", "side-by-side at the rear", "matching backward sweep from the prior catch pose"),
]
evidence = [
    ("the circular wake around the table", "it turns around an aligned couple without a forward exit", "make certainty in each other coexist with disorientation inside the shared space"),
    ("the single doorway and shared table", "one person walks backward while the other follows forward", "make the shared beginning physically credible and mutual"),
    ("the recurring lamp and tied oars", "each person secures one while both stabilize the table", "introduce later raft tools through equal self-owned action"),
    ("the opposed oars and circular whirl", "one blade moves backward and the other forward", "make equal effort and conflicting method produce the visible problem"),
    ("the matched complete oars", "both blades pause clear of water at identical forward catch positions", "make reciprocal recognition cause a new shared starting state"),
    ("the two straight wakes crossing the old circle", "both blades move backward at matching angles and timing", "make coordinated experimentation the visible payoff without showing a destination"),
]
continuity = [
    ("The story opens on its future object state.", "Slide two rewinds to the same table, lamp, oars, doorway, shelf and rug in a dry room."),
    ("The cover showed these ordinary objects transformed by water.", "A finger-high waterline begins the transformation while the pair carry the table on one axis."),
    ("The dry room established the lamp, oars, shelf and rug.", "Rising water makes the lamp and oars require separate but simultaneous action."),
    ("Both recurring tools were secured on the shared table.", "The room disappears and opposed use of the two oars creates the circular wake previewed on the cover."),
    ("The opposed strokes produced an unmistakable circle.", "They bring both complete oars to a matched catch pose while the old circle remains visible."),
    ("The prior frame established the exact matched start pose.", "They sweep backward together and leave two straight wakes through the old circle toward an unfinished horizon."),
]

director_slides = []
for index in range(6):
    number = index + 1
    size, angle, camera_position, focal_subject = shots[index]
    sub_location, time, light, trace = settings[index]
    subject, action, target, reaction = actions[index]
    hands, gaze, distance, posture = blocking[index]
    carrier, observed, narrative_job = evidence[index]
    incoming, outgoing = continuity[index]
    director_slides.append(
        {
            "slide": number,
            "status": "PASS",
            "inference_match": True,
            "narrative_job": jobs[index],
            "silent_read": silent_reads[index],
            "change_from_previous": outgoing,
            "critic_evidence": "The fresh blind reviewer returned PASS and specifically found this frame legible inside the complete table-to-raft, circle-to-straight-wake sequence.",
            "staged_action": {"subject": subject, "action": action, "target_or_object": target, "reaction_or_consequence": reaction},
            "pov": {"owner": "the partnership as two equal agents", "audience_knows": silent_reads[index], "audience_feels": ["wonder", "certainty", "pressure", "bafflement", "recognition", "earned hope"][index]},
            "shot": {"size": size, "angle": angle, "camera_position": camera_position, "focal_subject": focal_subject, "story_reason": "The camera makes body relationship, object ownership and current cause-and-effect readable before atmosphere."},
            "blocking": {"hands": hands, "gaze": gaze, "body_distance": distance, "posture_or_feet": posture},
            "setting": {"sub_location": sub_location, "time": time, "motivated_light": light, "story_trace": trace},
            "story_evidence": [{"carrier": carrier, "observable_state": observed, "narrative_job": narrative_job}],
            "text_image_relationship": "interdependent",
            "continuity": {"incoming_state": incoming, "outgoing_state": outgoing},
            "entity_contract": {"expected_people": 2, "background_people": [], "reflections": [], "forbidden_entities": ["duplicate couple", "rescuer", "child", "background figure", "reflection person", "silhouette person", "unassigned hand", "unassigned oar"]},
            "unresolved_ambiguities": [],
            "resolved_ambiguities": [],
        }
    )

director = {
    "status": "PASS",
    "event": "copy_hidden_storyboard_read",
    "copy_locked": True,
    "copy_hidden": True,
    "intent_hidden": True,
    "copy_lock_evidence": "The creator supplied six exact slide lines; slides.json preserved them verbatim before the independent observable-card review.",
    "author_id": "/root",
    "reviewer_id": "/root/moonwater_event_a_v3",
    "reviewer_evidence": "A fresh collaboration agent received only the six copy-hidden observable frame cards after the v2 repairs and independently returned PASS with image-only causality, continuity and anatomy findings.",
    "requested_formats": list(locked_formats(PACKAGE)),
    "format_contract_fingerprint": locked_format_contract_fingerprint(PACKAGE),
    "creator_correction_fingerprint": current_creator_correction_fingerprint(PACKAGE),
    "generation_payload_fingerprint": current_generation_payload_fingerprint(PACKAGE),
    "blind_cards": cards,
    "blind_input_fingerprint": blind_cards_fingerprint(cards),
    "source_fingerprint": storyboard_source_fingerprint(slides),
    "sequence_mode": "causal_sequence",
    "physical_event": "They carry one table into a dry home, secure a lamp and two oars as water rises, turn the table into a raft, spin through opposed strokes, reset both oars together and make one synchronized stroke through the old circle.",
    "emotional_arc": "Shared certainty meets accumulating demands, equal but conflicting effort, reciprocal recognition, and one earned coordinated experiment.",
    "relationship_change": "They move from mutual arrival through divided methods into an observable shared reset and equal continuation.",
    "sequence_read": "A flash-forward previews the circle; chronology then introduces every recurring object, raises the water, explains the circle, shows the matched reset and pays it off with two straight wakes.",
    "visual_variables": ["water and room dissolution", "oar alignment and wake geometry"],
    "hero_receipt_slide": 4,
    "setup_payoff_ledger": [
        {"setup": "Two oars lean beside the shelf, are lifted together from the rising water, and later create one circular whirl through opposed strokes.", "payoff": "Both complete oars pause at identical catch positions and then create two straight parallel wakes through the old circle.", "changed_meaning": "The same effort changes from disorienting torque to coordinated experimentation without promising a known destination."},
        {"setup": "The table, lamp, doorway, shelf and pale rug begin as ordinary parts of one dry room.", "payoff": "The table becomes the raft, the lamp becomes its center, and the exact doorway, shelf and rug dissolve far behind at dawn.", "changed_meaning": "A familiar shared home becomes unfamiliar life while the chosen partnership remains recognizable."},
    ],
    "object_motif_ledger": [
        {"object": "the wooden dining table", "initial_state": "carried through one doorway into a dry room", "later_state": "floating as the stable raft beneath both people", "story_job": "carry the shared-life world from ordinary choice into unfamiliar conditions"},
        {"object": "the two wooden oars", "initial_state": "resting beside the shelf and then secured from rising water", "later_state": "opposed during the circular failure, matched at the reset, and synchronized at dawn", "story_job": "make changing method and equal agency physically legible"},
        {"object": "the ordinary lamp", "initial_state": "unplugged on the dry floor", "later_state": "caught, secured at raft center, and dim beside dawn", "story_job": "preserve one recognizable domestic center through the impossible transformation"},
    ],
    "slides": director_slides,
    "issues": [],
    "director_event_fingerprint_version": DIRECTOR_EVENT_FINGERPRINT_VERSION,
    "review_provenance": {
        "schema_version": REVIEW_PROVENANCE_VERSION,
        "author_task_id": "/root",
        "author_run_id": "moonwater-author-run-20260823-03",
        "reviewer_task_id": "/root/moonwater_event_a_v3",
        "reviewer_run_id": "EA-MOONWATER-20260823-V3",
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
done_line = "fresh copy-hidden moonwater director_storyboard Event A v3: PASS"
if done_line not in review.setdefault("done", []):
    review["done"].append(done_line)
stage_path.write_text(json.dumps(stage, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
print(json.dumps({"status": "PASS", "reviewer_task_id": director["reviewer_id"], "director_event_fingerprint": director["director_event_fingerprint"]}, indent=2))
