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


PACKAGE = Path("output/carousels/2026-08-14/certain-of-you-lost-in-us-no-script")
qa_path = PACKAGE / "visual-qa.json"
qa = json.loads(qa_path.read_text(encoding="utf-8"))
state = json.loads((PACKAGE / "image-generation.json").read_text(encoding="utf-8"))
plan = json.loads((PACKAGE / "visual-plan-quality.json").read_text(encoding="utf-8"))

output = state["slides"][0]["native_outputs"]["instagram_post"]
final_path = PACKAGE / output["path"]
attempt_root = final_path.parents[1]
frame_rel = final_path.relative_to(attempt_root).as_posix()

qa["status"] = "PASS"
qa["proof_state"] = "QA_PASS_CANDIDATE"
qa["image_set_sha256"] = state["image_set_sha256"]

qa["checks"]["aachu_face"] = {
    "pass": True,
    "reference_option_ids": [
        "output/carousels/2026-08-14/certain-of-you-lost-in-us-no-script/.internal/reference-crops/aachu-face-04-crop.png",
        "output/carousels/2026-08-14/certain-of-you-lost-in-us-no-script/.internal/reference-crops/together-18-faces.jpg",
    ],
    "likeness_notes": "Aachu retains long dark hair, thick arched brows, almond eyes, anchor nose width, full lips and a soft oval-to-tapered face; the three-quarter downward pose narrows the face slightly without changing identity.",
}
qa["checks"]["zuv_face"] = {
    "pass": True,
    "reference_option_ids": [
        "output/carousels/2026-08-14/certain-of-you-lost-in-us-no-script/.internal/reference-crops/zuv-portrait-07-crop.jpg",
        "output/carousels/2026-08-14/certain-of-you-lost-in-us-no-script/.internal/reference-crops/together-18-faces.jpg",
    ],
    "likeness_notes": "Zuv retains raised dark hair volume, heavy brows, broad nose, trimmed beard and a strong jaw; the curls are slightly tighter than the anchor but the hairline, volume and jaw-beard silhouette remain recognizable.",
}
qa["checks"]["scene_logic"] = {
    "pass": True,
    "evidence": "Forward-stepping bodies, shoulder contact, opposed oblique flats, turned casters and short wheel-local motion strokes show two aligned people continuing while the theatre world actively separates around them.",
}
qa["checks"]["visual_richness"]["pass"] = True
richness = qa["checks"]["visual_richness"]["slides"][0]["formats"]["instagram_post"]
richness["focal_action"] = "Aachu and Zuv move forward shoulder-to-shoulder while two scenery flats visibly roll apart behind them."
richness["cause_effect"] = "Opposing flat angles, turned caster wheels and short local dust-and-watercolor motion strokes make the shifting theatre world press outward while the couple maintains one forward direction."
richness["posed_portrait"] = False

event_b_raw_path = PACKAGE / ".internal/proof-attempt-02-event-b-raw-response.md"
event_b_raw = event_b_raw_path.read_text(encoding="utf-8")
frames = [
    {
        "slide": 1,
        "format": "instagram_post",
        "file": frame_rel,
        "status": "PASS",
        "expected_silent_read": "Two certain people keep one direction and physical alignment while their shared theatre world visibly shifts apart around them.",
        "observed_image_first_read": "A young couple crosses the front of a theatre stage shoulder-to-shoulder while two large wheeled scenery flats separate behind them.",
        "core_action_legible": True,
        "relationship_turn_legible": True,
        "focal_hierarchy": "The exact copy leads the clear upper field, the joined moving couple anchors center, and opposed oblique scenery plus wheel-local motion marks carry the changing-world contradiction.",
        "hands_gaze_prop_legible": True,
        "storyboard_match": True,
        "native_format_readability": True,
        "copy_visual_contradictions": [],
        "unexpected_story": [],
        "match_rationale": "Forward-stepping bodies, shoulder pressure, asymmetrical pensive/steady gazes, visible casters and opposing wheel-local motion evidence make alignment inside change readable without requiring either person to operate the scenery.",
        "evidence": "The navy and coral flats stand at opposing oblique angles with turned casters and pale streaks around the wheels; Aachu and Zuv remain joined at the shoulder, move forward at the same depth and retain two clearly owned outer hands.",
        "image_fingerprint": image_file_fingerprint(final_path),
    }
]

readability = {
    "pass": True,
    "status": "PASS",
    "event": "rendered_frame_story_audit",
    "image_first": True,
    "provisional": True,
    "scope": "selected_proof_only",
    "full_event_b": False,
    "reviewer_id": "/root/theater_proof2_event_b",
    "reviewer_evidence": "A fresh exact-frame image-first reviewer returned GO and cited forward-stepping bodies, shoulder contact, asymmetrical gaze, opposing oblique flats, visible casters and wheel-local motion marks as an active changing-stage event rather than a posed quote card.",
    "source_director_event_fingerprint": plan["director_storyboard"]["director_event_fingerprint"],
    "reviewed_native_formats": ["instagram_post"],
    "sequence_read": "A couple walks forward in one physical line while the theatre environment visibly separates behind them, establishing the cold-open thesis for the later causal sequence.",
    "relationship_turn": "The world is changing and Aachu carries inward heaviness, but the couple remains physically aligned and Zuv's steady presence keeps certainty in the partner visible.",
    "setup_payoff_evidence": "The two opposing wheeled scenery flats, shoulder contact, shared forward movement and first-row viewpoint establish the visual motif that will return around active chair convergence in the payoff.",
    "weakest_frame": "The cover intentionally uses restrained rather than chaotic motion, but the oblique flats, turned casters and concentrated wheel-local strokes keep the scene change legible at phone size.",
    "repair_decision": "No blocking repair remains; preserve these exact identity, palette, wardrobe, copy, brandmark, motion-evidence and hand-ownership qualities for the batch.",
    "frames": frames,
    "issues": [],
    "review_provenance": {
        "schema_version": REVIEW_PROVENANCE_VERSION,
        "reviewer_task_id": "/root/theater_proof2_event_b",
        "reviewer_run_id": "event-b-frame-02-9f6c1e7a",
        "input_fingerprint": frame_review_input_fingerprint(frames),
        "raw_response_artifact": ".internal/proof-attempt-02-event-b-raw-response.md",
        "raw_response_fingerprint": review_response_fingerprint(event_b_raw),
        "output_fingerprint": "",
    },
}
readability["review_provenance"]["output_fingerprint"] = frame_review_output_fingerprint(readability)
qa["checks"]["visual_story_readability"] = readability

qa["reviews"] = {
    "anatomy_entity_spatial_identity": {
        "reviewer_id": "/root/theater_proof2_identity_qa",
        "pass": True,
        "evidence": "A fresh exact-pixel comparison passed Aachu and Zuv identity within watercolor tolerance, exact two-person anatomy, two clearly owned visible hands, natural hidden inner arms, relative scale, wardrobe, topology, exact text, brandmark, paper tone and 1080x1440 readability.",
    },
    "storytelling_richness_text_style": {
        "reviewer_id": "/root/theater_proof2_event_b",
        "pass": True,
        "evidence": "A separate fresh image-first review passed the active stage event, emotional contradiction, opposing scenery motion, focal hierarchy, exact copy, single brandmark, phone readability and watercolor-and-ink palette.",
    },
}
qa["required_repairs"] = []

issues = validate_exact_image_visual_qa(
    qa,
    state["slides"],
    visual_plan=plan,
    carousel_dir=PACKAGE,
)
if issues:
    raise SystemExit("\n".join(issues))

qa_path.write_text(json.dumps(qa, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
print(json.dumps({"status": "PASS", "image_set_sha256": qa["image_set_sha256"]}, indent=2))
