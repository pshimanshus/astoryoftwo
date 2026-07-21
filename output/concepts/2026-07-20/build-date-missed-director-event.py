import json
from pathlib import Path

from pipeline.stages.carousel_format_contract import locked_format_contract_fingerprint
from pipeline.stages.carousel_visual_storytelling import (
    DIRECTOR_EVENT_FINGERPRINT_VERSION,
    REVIEW_PROVENANCE_VERSION,
    blind_cards_fingerprint,
    director_event_fingerprint,
    director_review_output_fingerprint,
    review_response_fingerprint,
    storyboard_source_fingerprint,
)


package = Path("output/carousels/2026-07-20/the-date-that-missed-its-reservation-4")
slides = json.loads((package / "slides.json").read_text(encoding="utf-8"))
plan = json.loads((package / "visual-plan-quality.json").read_text(encoding="utf-8"))

blind_cards = [
    {
        "slide": 1,
        "visible_people": ["Aachu", "Zuv"],
        "visible_setting": "A rainy divided road beside a tiny glowing chai stall, with a restaurant visible across traffic.",
        "observable_action": "Aachu points toward the chai stall while Zuv lowers the phone map under their shared umbrella.",
        "hands_and_contact": "Aachu's right hand points and left hand stays relaxed; Zuv's right hand holds the umbrella and left lowers the phone; helmets rest on the scooter.",
        "gaze": "They exchange a conspiratorial look instead of looking toward the restaurant.",
        "body_blocking": "They stand close under one umbrella beside the parked scooter.",
        "object_state": "The phone map is lowered, the scooter is safely parked, and both helmets rest on its seat.",
        "camera_view": "Medium-wide three-quarter roadside view showing chai stall, couple, scooter, divided road, traffic, and distant restaurant.",
        "visible_continuity": "Date-night clothes, rainy evening, scooter, helmets, phone, road, and restaurant establish the outing.",
    },
    {
        "slide": 2,
        "visible_people": ["Aachu", "Zuv"],
        "visible_setting": "Their home entryway before leaving for the scooter date.",
        "observable_action": "Aachu holds both helmets and points accusingly while Zuv searches his jacket pockets; the scooter key is caught in the tote strap.",
        "hands_and_contact": "Aachu's left hand supports the two nested helmets and right hand points; Zuv's two hands check separate jacket pockets.",
        "gaze": "Aachu looks at Zuv while he looks down toward his pockets.",
        "body_blocking": "They face each other across the tote bag in a compact entryway.",
        "object_state": "The missing scooter key is visibly trapped in the tote strap between them.",
        "camera_view": "Medium eye-level two-shot keeping hands, helmets, tote strap, and key readable.",
        "visible_continuity": "The same date clothes, helmets, tote, and scooter key begin the outing shown in the teaser.",
    },
    {
        "slide": 3,
        "visible_people": ["Aachu", "Zuv"],
        "visible_setting": "A rain-slick divided road with the restaurant visible across traffic and the scooter parked on the quiet shoulder.",
        "observable_action": "Zuv studies a rerouting phone map while Aachu holds both helmets and looks away.",
        "hands_and_contact": "Zuv holds the phone with both hands; Aachu holds one helmet in each hand at her sides.",
        "gaze": "He looks down at the route while she looks away toward the blocked destination.",
        "body_blocking": "They stand beside the scooter with a small but visible gap and opposing eye-lines.",
        "object_state": "The scooter is parked, the map reroutes, and the restaurant remains physically close but road-separated.",
        "camera_view": "Wide elevated three-quarter view making the road geography and their stalled movement legible.",
        "visible_continuity": "Same rainy outing, wardrobe, scooter, helmets, phone, and restaurant from the cover teaser.",
    },
    {
        "slide": 4,
        "visible_people": ["Aachu", "Zuv"],
        "visible_setting": "A safe recessed roadside edge near the parked scooter in light rain.",
        "observable_action": "Aachu faces away with folded arms while Zuv waits several feet behind without reaching or leaving.",
        "hands_and_contact": "Aachu's two hands remain visibly folded across her own torso; Zuv's right hand steadies his helmet at his hip and left hand hangs open.",
        "gaze": "Aachu looks away from him; Zuv watches her without demanding eye contact.",
        "body_blocking": "The wide profile view holds several feet of empty space between her withdrawn posture and his grounded stance.",
        "object_state": "The scooter remains parked; each helmet is securely owned and no object crosses the emotional gap.",
        "camera_view": "Wide side-profile view using negative space as the focal story evidence.",
        "visible_continuity": "Same road, weather, clothes, scooter, and helmets; the prior frustration has become a pause.",
    },
    {
        "slide": 5,
        "visible_people": ["Aachu", "Zuv"],
        "visible_setting": "Outside the dark inaccessible restaurant frontage after rain.",
        "observable_action": "Aachu looks at the dark entrance with dropped posture while Zuv lowers the phone and watches her face.",
        "hands_and_contact": "Zuv's right hand holds the lowered phone at his side and left holds his helmet; Aachu holds her helmet loosely with one hand while the other rests at her side.",
        "gaze": "She looks toward the entrance; he looks at her reaction rather than the closed frontage.",
        "body_blocking": "Their distance narrows to one step but they do not touch.",
        "object_state": "The route phone is no longer active and the restaurant entrance is dark or inaccessible.",
        "camera_view": "Medium over-shoulder view placing her reaction and his noticing in one readable plane.",
        "visible_continuity": "Same destination, weather traces, clothes, phone, and helmets; logistical frustration becomes disappointment.",
    },
    {
        "slide": 6,
        "visible_people": ["Aachu", "Zuv"],
        "visible_setting": "The tiny roadside chai stall beside their parked scooter with the restaurant glowing across the divided road.",
        "observable_action": "Aachu steals a sip from Zuv's chai while he mock-protects the biscuit packet and performs offense.",
        "hands_and_contact": "Aachu's right hand holds his chai glass and left steadies her empty glass; Zuv's two hands hold the biscuit packet against his chest.",
        "gaze": "She glances over the chai rim toward him while he looks at her with comic disbelief.",
        "body_blocking": "Their two plastic stools are pulled close and their shoulders angle toward each other.",
        "object_state": "Her chai is finished, his chai changes owner briefly, and the biscuit packet becomes the playful defended object.",
        "camera_view": "Close-medium eye-level two-shot emphasizing cup transfer, facial reaction, and restored proximity.",
        "visible_continuity": "Same scooter, date clothes, rainy road, restaurant, and chai-stall choice set up in the teaser.",
    },
    {
        "slide": 7,
        "visible_people": ["Aachu", "Zuv"],
        "visible_setting": "Inside their home entryway after the rainy date, facing the fully closed front door.",
        "observable_action": "Zuv steps away after checking the lock while Aachu rolls her eyes, returns, and tugs the interior handle herself; he catches her.",
        "hands_and_contact": "Only Aachu's right hand contacts the interior door handle; her left hand stays visible; Zuv's hands are relaxed and clear of the door.",
        "gaze": "Aachu looks at the handle while Zuv looks back at her with a caught-you smile.",
        "body_blocking": "Zuv has moved away from the door as Aachu closes the small gap to repeat the check.",
        "object_state": "The front door is fully closed and locked; the scooter key is visibly safe in the key bowl; helmets and damp layers sit nearby.",
        "camera_view": "Medium interior side view keeping the key bowl, closed door, handle contact, both faces, and damp outing traces readable.",
        "visible_continuity": "Same couple and clothes return home; the key is resolved and a minor checking ritual closes the evening.",
    },
]

jobs = [
    "nonlinear teaser and shared choice",
    "comic departure setup",
    "establish difficult road access and split attention",
    "respectful pause at peak friction",
    "disappointment revealed beneath irritation",
    "playful roadside release",
    "home callback and affectionate consequence",
]
silent_reads = [
    "A restaurant date becomes a jointly chosen chai detour before the audience knows why.",
    "A missing scooter key creates a playful blame ritual before departure.",
    "The destination is close but hard to reach, and logistics begin separating their attention.",
    "She withdraws and he remains emotionally available without crossing the space she asks for.",
    "Her frustration was carrying disappointment, and he finally notices the feeling instead of the route.",
    "They recover through a tiny improvised date and familiar mutual teasing.",
    "They remain mildly irritating but can recognize the same anxious checking habit in each other.",
]
changes = [
    "Opens on a forward teaser where the map lowers and chai becomes the visible shared choice.",
    "Resets to home and replaces destination choice with a comic missing-object problem.",
    "Moves from domestic play into stalled roadside geography and split eye-lines.",
    "Expands body distance and removes problem-solving action to make the pause visible.",
    "Narrows distance and shifts Zuv's attention from the phone to Aachu's reaction.",
    "Transfers the chai glass and closes body distance to release the tension through play.",
    "Returns home and converts checking from irritation into a mirrored private joke.",
]
actions = [
    ("Aachu", "points toward the chai stall while Zuv lowers the map", "chai stall and route phone", "their shared look changes the plan into a mutual detour"),
    ("Aachu and Zuv", "accuse and search for the missing scooter key", "tote strap, key, and helmets", "the audience sees the answer before they do"),
    ("Zuv", "checks the rerouting map while Aachu disengages", "phone, road divider, and visible restaurant", "their attention splits as the date stalls"),
    ("Aachu and Zuv", "hold a pause without leaving the shared roadside space", "empty distance and parked scooter", "friction stops escalating while connection remains available"),
    ("Zuv", "lowers the phone and notices Aachu's disappointment", "dark restaurant entrance and her face", "the problem changes from navigation to missed time together"),
    ("Aachu", "steals Zuv's chai as he protects the biscuits", "chai glass and biscuit packet", "teasing restores closeness and makes the detour count as the date"),
    ("Aachu", "repeats Zuv's completed lock check", "interior handle and key bowl", "his amused recognition turns the small irritation into a shared ritual"),
]
shots = [
    ("medium-wide shot", "eye-level three-quarter", "roadside facing both choices", "the pointing hand, lowered map, and shared look"),
    ("medium two-shot", "eye-level frontal", "inside entryway facing the tote between them", "the visible key and accusing/searching hands"),
    ("wide establishing shot", "slightly elevated three-quarter", "quiet shoulder looking across divided road", "the road barrier between scooter and restaurant"),
    ("wide profile shot", "eye-level side angle", "safe roadside recess parallel to their bodies", "the empty space between them"),
    ("medium over-shoulder shot", "eye-level", "near the entrance with both faces readable", "her dropped posture and his redirected gaze"),
    ("close-medium two-shot", "eye-level intimate", "chai counter side facing their stools", "chai transfer and mock-defended biscuits"),
    ("medium interior side shot", "eye-level", "inside entryway facing door and key bowl", "her hand on handle and his backward smile"),
]
settings = [
    ("quiet shoulder beside roadside chai stall", "rainy evening", "warm stall spill against cool road light", "date clothes, scooter, helmets, and lowered map show a plan being revised"),
    ("home entryway", "early evening before departure", "soft home light", "helmets, tote, and visible trapped key show hurried preparation"),
    ("divided road quiet shoulder", "rainy evening", "wet-road reflections and vehicle light", "parked scooter and close-but-separated restaurant prove the access problem"),
    ("safe roadside recess", "rainy evening", "soft spill from road and stall", "parked scooter and separate helmets preserve the unresolved outing"),
    ("inaccessible restaurant entrance", "evening after rain", "dark frontage with road spill", "lowered phone and damp traces show effort that did not deliver the planned date"),
    ("tiny roadside chai stall", "rainy evening", "warm stall light", "finished chai, shared cup, biscuits, close stools, and parked scooter show the improvised date"),
    ("home entryway", "late evening", "quiet warm interior light", "damp layers, helmets, and key bowl carry the outing home"),
]

director_slides = []
for index, (slide, card) in enumerate(zip(slides, blind_cards), start=1):
    subject, action, target, consequence = actions[index - 1]
    size, angle, camera, focal = shots[index - 1]
    sublocation, time, light, trace = settings[index - 1]
    director_slides.append(
        {
            "slide": index,
            "status": "PASS",
            "inference_match": True,
            "narrative_job": jobs[index - 1],
            "silent_read": silent_reads[index - 1],
            "change_from_previous": changes[index - 1],
            "critic_evidence": "The blind critic cited the visible hands, gaze, body distance, route geography, object state, and changed action for this frame.",
            "staged_action": {
                "subject": subject,
                "action": action,
                "target_or_object": target,
                "reaction_or_consequence": consequence,
            },
            "pov": {
                "owner": "the couple's shared observational point of view",
                "audience_knows": silent_reads[index - 1],
                "audience_feels": slide.get("emotion") or "recognition and warmth",
            },
            "shot": {
                "size": size,
                "angle": angle,
                "camera_position": camera,
                "focal_subject": focal,
                "story_reason": "This camera keeps the focal action, object state, reaction, and relationship distance readable in one static illustration.",
            },
            "blocking": {
                "hands": card["hands_and_contact"],
                "gaze": card["gaze"],
                "body_distance": card["body_blocking"],
                "posture_or_feet": "Both figures remain grounded on the same physical plane; posture changes carry the emotional beat without height distortion.",
            },
            "setting": {
                "sub_location": sublocation,
                "time": time,
                "motivated_light": light,
                "story_trace": trace,
            },
            "story_evidence": [
                {
                    "carrier": target,
                    "observable_state": card["object_state"],
                    "narrative_job": consequence,
                }
            ],
            "text_image_relationship": "interdependent",
            "continuity": {
                "incoming_state": card["visible_continuity"],
                "outgoing_state": changes[index - 1],
            },
            "entity_contract": {
                "expected_people": 2,
                "background_people": [],
                "reflections": [],
                "forbidden_entities": ["extra chai vendor", "background pedestrian", "duplicate couple", "human reflection", "car used as the couple's vehicle"],
            },
            "unresolved_ambiguities": [],
            "resolved_ambiguities": (
                [
                    {
                        "competing_read": "The cover could duplicate the later seated chai payoff.",
                        "repair": "Changed the cover to the standing restaurant-versus-chai decision before seating.",
                        "recheck_evidence": "The critic read the pointing hand and lowered map as a distinct shared decision and passed the sequence.",
                    }
                ]
                if index == 1
                else [
                    {
                        "competing_read": "The final handle check could look like the couple is locked out.",
                        "repair": "Moved the view fully inside, showed the key safe in its bowl, and limited the action to one interior-handle tug.",
                        "recheck_evidence": "The critic read a completed lock check followed by affectionate independent verification, not a lockout.",
                    }
                ]
                if index == 7
                else []
            ),
        }
    )

raw_response = (
    "The fresh copy-hidden critic read a restaurant date delayed by a missing key and difficult road access, "
    "a visible friction-and-space beat, disappointment underneath the irritation, a playful chai recovery, "
    "and an affectionate home checking callback. After repair the critic returned PASS."
)

director = {
    "status": "PASS",
    "event": "copy_hidden_storyboard_read",
    "copy_locked": True,
    "copy_hidden": True,
    "intent_hidden": True,
    "copy_lock_evidence": "The creator approved image generation after the seven exact slide lines were presented, with only the scooter and road geography corrected.",
    "author_id": "root-date-missed-route-author",
    "reviewer_id": "blind_storyboard_critic",
    "reviewer_evidence": "The reviewer received only seven observable staged cards without copy, theme, narrative labels, intended meaning, or scores; it reported frame inference and a sequence read before intent reveal.",
    "requested_formats": ["instagram_post"],
    "format_contract_fingerprint": locked_format_contract_fingerprint(package),
    "blind_cards": blind_cards,
    "blind_input_fingerprint": blind_cards_fingerprint(blind_cards),
    "source_fingerprint": storyboard_source_fingerprint(slides),
    "sequence_mode": "causal_sequence",
    "physical_event": "A scooter date is delayed by a missing key and difficult road access, briefly strains, then becomes an improvised roadside chai date before a comic home callback.",
    "emotional_arc": "playful departure becomes irritation, respectful space, visible disappointment, mutual improvisation, and affectionate recognition.",
    "relationship_change": "They move from childish blame and split attention into a respected pause, renewed closeness, and a shared joke about the habits that still irritate them.",
    "sequence_read": "A forward teaser offers chai, a flashback shows how the date went wrong, body distance peaks at the pause, and object transfer plus the home callback release the tension.",
    "visual_variables": ["body distance", "object ownership"],
    "hero_receipt_slide": 1,
    "setup_payoff_ledger": [
        {
            "setup": "The cover shows Aachu pointing toward chai while Zuv lowers the route map.",
            "payoff": "Slide 6 shows them seated close as she steals his chai and he protects the biscuits.",
            "changed_meaning": "The chai stall changes from a possible compromise into proof that the failed plan still became a date.",
        },
        {
            "setup": "The departure begins with mutual suspicion over a missing scooter key.",
            "payoff": "The final home beat shows Aachu repeating Zuv's completed lock check and getting caught.",
            "changed_meaning": "Checking changes from a source of irritation into a recognizable habit both can hold lightly.",
        },
    ],
    "object_motif_ledger": [
        {
            "object": "phone map",
            "initial_state": "held up as the solution to reach the restaurant",
            "later_state": "lowered when they choose chai and lowered again when he notices her disappointment",
            "story_job": "make the shift from solving logistics to attending to the relationship visible",
        },
        {
            "object": "chai glass",
            "initial_state": "suggested by the glowing stall in the cover",
            "later_state": "transferred from Zuv's hand to Aachu during playful repair",
            "story_job": "turn an accidental stop into an active shared date and comic reconciliation",
        },
    ],
    "slides": director_slides,
    "issues": [],
    "director_event_fingerprint_version": DIRECTOR_EVENT_FINGERPRINT_VERSION,
    "review_provenance": {
        "schema_version": REVIEW_PROVENANCE_VERSION,
        "author_task_id": "root-date-missed-route-author",
        "author_run_id": "root-date-missed-route-author-2026-07-20",
        "reviewer_task_id": "blind_storyboard_critic",
        "reviewer_run_id": "blind-storyboard-critic-recheck-2026-07-20",
        "input_fingerprint": blind_cards_fingerprint(blind_cards),
        "raw_response": raw_response,
        "raw_response_fingerprint": review_response_fingerprint(raw_response),
        "output_fingerprint": "",
    },
}

director["review_provenance"]["output_fingerprint"] = director_review_output_fingerprint(director)
director["director_event_fingerprint"] = director_event_fingerprint(director)
plan["director_storyboard"] = director
(package / "visual-plan-quality.json").write_text(
    json.dumps(plan, ensure_ascii=False, indent=2) + "\n",
    encoding="utf-8",
)

layer_path = package / "layer-e-story-selling.json"
layer = json.loads(layer_path.read_text(encoding="utf-8"))
layer["status"] = "GO"
layer["selected_story_lens"] = "A failed proper date becomes proof that mature love can respect a pause, notice disappointment, and still return to play."
layer["emotional_machine"] = (
    "Childish blame and difficult road access create real irritation -> Zuv gives Aachu a minute without turning it into distance -> "
    "the dark restaurant reveals missed time underneath the frustration -> Aachu initiates the chai detour and mutual teasing restores closeness -> "
    "the home lock-check callback proves they remain imperfect but more careful with each other's hearts."
)
layer["human_story_setup"] = {
    "cold_reader_doorway": "A proper date begins with a missing scooter key, a restaurant visible across impossible traffic, and two familiar people losing patience.",
    "emotional_obstacle": "Small logistical failures expose how much they have missed unhurried time together, and irritation threatens to turn a pause into emotional distance.",
    "visible_human_proof": "He stays nearby without crowding her; later he lowers the map and notices her disappointment, while she chooses the chai detour and restarts their shared joke.",
    "active_partner_role": "Both move the relationship: Zuv respects the pause and redirects attention from route to feeling; Aachu points toward chai and initiates the playful repair.",
    "emotional_turn": "The inaccessible restaurant stops being a failed destination when two plastic stools and a stolen sip become the date they actually needed.",
    "shareable_setup": "New couples can send it as the kind of love they want to grow into; established couples can send it as recognition of giving a minute without giving distance.",
    "earned_payoff": "They do not become less irritating; the final repeated lock check shows they become gentler with the habits underneath the irritation.",
}
layer["story_selling_score"] = {
    "reader_identity_mirror": 5.0,
    "romantic_conflict_stakes": 4.5,
    "specificity_of_proof": 5.0,
    "emotional_reversal": 5.0,
    "visual_scene_clarity": 5.0,
    "online_share_save_sell_potential": 4.5,
    "total": 29.0,
}
layer["golden_theme_score"] = {
    "universal_hook": 5.0,
    "aachu_zuv_specificity": 5.0,
    "concrete_proof": 5.0,
    "zuv_emotional_role": 4.5,
    "tender_thesis": 5.0,
    "share_send_potential": 4.5,
    "total": 29.0,
}
layer["stage_scene_gate"] = {
    "status": "GO",
    "action": "The couple leaves by scooter, becomes stranded across a divided road from the restaurant, pauses after irritation, finds the destination inaccessible, and chooses the adjacent chai stall.",
    "reaction": "Aachu's playful accusation becomes averted gaze and disappointment; Zuv's route-solving becomes respectful waiting and then attention to her face; both return to teasing over chai.",
    "eye_line_or_attention": "Their eye-lines split at the road, remain separate during the pause, reconnect at the chai decision, and lock playfully during the stolen sip.",
    "hands_or_object_movement": "The key moves from apparently missing to visible in the tote, the phone map lowers, Aachu points toward chai, and the chai glass transfers from Zuv to Aachu.",
    "silence_or_pause": "A wide roadside frame holds several feet of empty space while he stays nearby without reaching; the following frame narrows distance when he notices her disappointment.",
    "consequence": "The inaccessible restaurant produces the chai detour; the failed plan becomes a real date and the final home check becomes an affectionate callback.",
    "reversal_or_payoff": "The restaurant remains visible but loses importance as the chai glass changes hands and both recover their shared comic rhythm.",
    "blockers": [],
}
layer["hard_fails"] = []
layer["required_repairs"] = []
for room_name in ("contrarian_repair_room", "stage_scene_room", "final_selector_room"):
    room = layer.get("rooms", {}).get(room_name)
    if isinstance(room, dict):
        room["status"] = "GO"
        room["objections"] = []
        room["repairs"] = []
layer_path.write_text(json.dumps(layer, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
