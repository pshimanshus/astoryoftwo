from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from pipeline.stages.carousel_format_contract import (
    FORMAT_CONTRACT_FILENAME,
    expected_frame_bindings,
    locked_format_contract_fingerprint,
    locked_formats,
    write_format_contract,
)
from pipeline.stages.carousel_visual_storytelling import (
    DIRECTOR_EVENT_FINGERPRINT_VERSION,
    REVIEW_PROVENANCE_VERSION,
    blind_cards_fingerprint,
    current_creator_correction_fingerprint,
    current_generation_payload_fingerprint,
    director_event_fingerprint,
    director_review_output_fingerprint,
    frame_review_input_fingerprint,
    frame_review_output_fingerprint,
    image_file_fingerprint,
    review_response_fingerprint,
    storyboard_source_fingerprint,
)


def _read_slides(package: Path) -> list[dict[str, Any]]:
    path = package / "slides.json"
    if path.exists():
        payload = json.loads(path.read_text(encoding="utf-8"))
        if isinstance(payload, list):
            return payload
        if isinstance(payload, dict) and isinstance(payload.get("slides"), list):
            return payload["slides"]
    slides = [
        {
            "slide": 1,
            "copy": "Test relationship beat.",
            "role": "single directed beat",
            "visual": "One partner visibly acts and the other visibly reacts.",
            "emotion": "specific recognition",
            "continuity_lock": "single test frame",
        }
    ]
    path.write_text(json.dumps(slides), encoding="utf-8")
    return slides


def write_passing_director_storyboard(package: Path) -> dict[str, Any]:
    slides = _read_slides(package)
    prompt_pack_path = package / "prompt-pack.json"
    if not prompt_pack_path.exists():
        prompt_pack_path.write_text(
            json.dumps(
                {
                    "slides": [
                        {
                            "slide": int(slide.get("slide") or index),
                            "text": str(slide.get("copy") or slide.get("text") or ""),
                            "visual": str(slide.get("visual") or slide.get("scene") or ""),
                            "prompt": "Explicit test-only generation payload.",
                        }
                        for index, slide in enumerate(slides, start=1)
                    ]
                }
            ),
            encoding="utf-8",
        )
    if not (package / FORMAT_CONTRACT_FILENAME).exists():
        write_format_contract(
            package,
            locked_formats(package),
            source="test_fixture",
        )
    requested_formats = locked_formats(package)
    contract_fingerprint = locked_format_contract_fingerprint(package)
    plan_path = package / "visual-plan-quality.json"
    if plan_path.exists():
        payload = json.loads(plan_path.read_text(encoding="utf-8"))
        plan = payload if isinstance(payload, dict) else {}
    else:
        plan = {}
    director_slides = []
    for index, _slide in enumerate(slides, start=1):
        director_slides.append(
            {
                "slide": index,
                "status": "PASS",
                "inference_match": True,
                "narrative_job": f"directed test story beat {index}",
                "silent_read": "One partner performs a visible action and the other shows its relationship consequence.",
                "change_from_previous": (
                    "This first frame establishes the visible relationship state."
                    if index == 1
                    else "Action, focal evidence, and relationship pressure change from the prior frame."
                ),
                "critic_evidence": "The independent test critic cited action, reaction, hands, gaze, and object state.",
                "staged_action": {
                    "subject": "the acting partner",
                    "action": "performs the locked visible action",
                    "target_or_object": "the other partner or story object",
                    "reaction_or_consequence": "the relationship state visibly changes",
                },
                "pov": {
                    "owner": "the intended emotional point of view",
                    "audience_knows": "a concrete relationship event occurred",
                    "audience_feels": "specific recognition and earned tenderness",
                },
                "shot": {
                    "size": ["wide story shot", "medium relationship shot", "close evidence shot"][(index - 1) % 3],
                    "angle": "motivated eye-level angle",
                    "camera_position": "placed to keep action and reaction visible together",
                    "focal_subject": "the acting bodies and changed story evidence",
                    "story_reason": "The view makes the visible cause and consequence readable.",
                },
                "blocking": {
                    "hands": "Both intended hand actions are visible and attributable.",
                    "gaze": "The eye-line reaches the correct person or object.",
                    "body_distance": "The distance expresses the current relationship state.",
                    "posture_or_feet": "Feet and torso direction support the action.",
                },
                "setting": {
                    "sub_location": "the locked test location",
                    "time": "the locked test time",
                    "motivated_light": "light motivated by the visible environment",
                    "story_trace": "one visible trace proves the preceding event",
                },
                "story_evidence": [
                    {
                        "carrier": "the locked action or object state",
                        "observable_state": "its owner, position, and consequence are visible",
                        "narrative_job": "prove the relationship beat without copy",
                    }
                ],
                "text_image_relationship": "interdependent",
                "continuity": {
                    "incoming_state": "the preceding relationship and object state",
                    "outgoing_state": "the changed state motivating the next beat",
                },
                "entity_contract": {
                    "expected_people": 2,
                    "background_people": [],
                    "reflections": [],
                    "forbidden_entities": ["duplicate couple"],
                },
                "unresolved_ambiguities": [],
                "resolved_ambiguities": [],
            }
        )
    blind_cards = [
        {
            "slide": index,
            "visible_people": ["the acting partner", "the reacting partner"],
            "visible_setting": "The locked test location and its motivated light are visibly staged.",
            "observable_action": "One partner performs the locked physical action and changes the visible state.",
            "hands_and_contact": "Visible hands belong to named people and show their intended contact state.",
            "gaze": "Eye-lines visibly connect the correct person, action, or object.",
            "body_blocking": "Distance, posture, feet, and torso direction expose the relationship state.",
            "object_state": "The intended story evidence has a visible owner, position, and consequence.",
            "camera_view": "The test camera keeps the action, reaction, and relevant space readable.",
            "visible_continuity": "People, setting, evidence, and changed state remain traceable between frames.",
        }
        for index, _slide in enumerate(slides, start=1)
    ]
    raw_response = (
        "The independent fixture critic inferred the concrete action, reaction, "
        "continuity, and relationship change from the observable-only cards."
    )
    plan.update({"status": "PASS", "can_generate": True, "issues": []})
    plan["director_storyboard"] = {
        "status": "PASS",
        "event": "copy_hidden_storyboard_read",
        "copy_locked": True,
        "copy_hidden": True,
        "intent_hidden": True,
        "copy_lock_evidence": "The current slide source or documented text exception was locked before review.",
        "author_id": "test-route-author",
        "reviewer_id": "test-blind-director",
        "reviewer_evidence": "The fixture records an explicit copy-hidden semantic review by a separate test critic.",
        "requested_formats": list(requested_formats),
        "format_contract_fingerprint": contract_fingerprint,
        "creator_correction_fingerprint": current_creator_correction_fingerprint(
            package
        ),
        "generation_payload_fingerprint": current_generation_payload_fingerprint(
            package
        ),
        "blind_cards": blind_cards,
        "blind_input_fingerprint": blind_cards_fingerprint(blind_cards),
        "source_fingerprint": storyboard_source_fingerprint(slides),
        "sequence_mode": "single_image" if len(slides) == 1 else "causal_sequence",
        "physical_event": "The sequence moves through a concrete visible relationship event.",
        "emotional_arc": "Visible pressure changes into a legible response and payoff.",
        "relationship_change": "The partners move into a materially changed final state.",
        "sequence_read": "Every frame contributes new action, evidence, reaction, or consequence.",
        "visual_variables": ["body distance", "object ownership"],
        "hero_receipt_slide": min(2, len(slides)),
        "setup_payoff_ledger": (
            []
            if len(slides) == 1
            else [
                {
                    "setup": "The first frame establishes an incomplete visible action.",
                    "payoff": "The final frame reveals its relationship consequence.",
                    "changed_meaning": "Repeated evidence gains emotional meaning across the sequence.",
                }
            ]
        ),
        "object_motif_ledger": [
            {
                "object": "the test story evidence",
                "initial_state": "introduced with one owner or position",
                "later_state": "changed through visible action or consequence",
                "story_job": "prove causality and relationship change",
            }
        ],
        "slides": director_slides,
        "issues": [],
        "director_event_fingerprint_version": DIRECTOR_EVENT_FINGERPRINT_VERSION,
        "review_provenance": {
            "schema_version": REVIEW_PROVENANCE_VERSION,
            "author_task_id": "test-route-author",
            "author_run_id": "test-route-author-run",
            "reviewer_task_id": "test-blind-director",
            "reviewer_run_id": "test-blind-director-run",
            "input_fingerprint": blind_cards_fingerprint(blind_cards),
            "raw_response": raw_response,
            "raw_response_fingerprint": review_response_fingerprint(raw_response),
            "output_fingerprint": "",
        },
    }
    director = plan["director_storyboard"]
    director["review_provenance"]["output_fingerprint"] = (
        director_review_output_fingerprint(director)
    )
    director["director_event_fingerprint"] = director_event_fingerprint(director)
    plan_path.write_text(json.dumps(plan), encoding="utf-8")

    stage_reviews_path = package / "stage-reviews.json"
    if stage_reviews_path.exists():
        stage_payload = json.loads(stage_reviews_path.read_text(encoding="utf-8"))
        reviews = stage_payload.get("reviews") if isinstance(stage_payload, dict) else None
        visual_review = reviews.get("visual_reviewer") if isinstance(reviews, dict) else None
        if isinstance(visual_review, dict):
            stale_director_issue = (
                "visual-plan-quality.json missing structured director_storyboard evidence."
            )
            prior_issues = visual_review.get("issues")
            remaining_issues = (
                [
                    issue
                    for issue in prior_issues
                    if str(issue).strip() != stale_director_issue
                ]
                if isinstance(prior_issues, list)
                else []
            )
            visual_review["issues"] = remaining_issues
            if not remaining_issues:
                visual_review["status"] = "PASS"
                ledger_path = package / "run-ledger.json"
                if ledger_path.exists():
                    ledger = json.loads(ledger_path.read_text(encoding="utf-8"))
                    stage_statuses = (
                        ledger.get("stage_statuses")
                        if isinstance(ledger, dict)
                        else None
                    )
                    if isinstance(stage_statuses, dict):
                        stage_statuses["visual"] = "PASS"
                        ledger_path.write_text(json.dumps(ledger), encoding="utf-8")
            stage_reviews_path.write_text(json.dumps(stage_payload), encoding="utf-8")
    return plan


def write_passing_story_readability(package: Path) -> dict[str, Any]:
    plan = write_passing_director_storyboard(package)
    slides = _read_slides(package)
    requested_formats = locked_formats(package)
    bindings = expected_frame_bindings(package, len(slides), requested_formats)
    frames = []
    for index, _slide in enumerate(slides, start=1):
        for output_format in requested_formats:
            binding = bindings[(index, output_format)]
            path = package / str(binding["relative_path"])
            if not path.exists():
                raise FileNotFoundError(path)
            frames.append(
                {
                    "slide": index,
                    "format": output_format,
                    "file": str(path.relative_to(package)),
                    "status": "PASS",
                    "expected_silent_read": plan["director_storyboard"]["slides"][index - 1]["silent_read"],
                    "observed_image_first_read": "The rendered frame shows the intended action, reaction, and relationship change.",
                    "core_action_legible": True,
                    "relationship_turn_legible": True,
                    "focal_hierarchy": "The story action reads before decorative detail.",
                    "hands_gaze_prop_legible": True,
                    "storyboard_match": True,
                    "native_format_readability": True,
                    "copy_visual_contradictions": [],
                    "unexpected_story": [],
                    "match_rationale": "Visible action, gaze, body distance, and evidence match the director card.",
                    "evidence": "A separate rendered-frame test reviewer inspected the current native file image-first.",
                    "image_fingerprint": image_file_fingerprint(path),
                }
            )
    qa_path = package / "visual-qa.json"
    if qa_path.exists():
        loaded = json.loads(qa_path.read_text(encoding="utf-8"))
        qa = loaded if isinstance(loaded, dict) else {}
    else:
        qa = {}
    checks = qa.setdefault("checks", {})
    raw_response = (
        "The separate rendered-frame fixture critic inspected the current files "
        "image-first and reported their visible action and relationship turn."
    )
    readability = {
        "pass": True,
        "status": "PASS",
        "event": "rendered_frame_story_audit",
        "image_first": True,
        "reviewer_id": "test-rendered-editor",
        "reviewer_evidence": "A second test critic inspected current image bytes before receiving intended copy or interpretation.",
        "source_director_event_fingerprint": plan["director_storyboard"]["director_event_fingerprint"],
        "reviewed_native_formats": list(requested_formats),
        "sequence_read": "The native frames preserve the intended action-to-consequence progression.",
        "relationship_turn": "The visible reaction changes the relationship state as directed.",
        "setup_payoff_evidence": "The initial visible state earns the final changed state.",
        "weakest_frame": "The first frame is least compressed but remains necessary and readable.",
        "repair_decision": "No visual-story repair is required for this explicit test fixture.",
        "frames": frames,
        "issues": [],
        "review_provenance": {
            "schema_version": REVIEW_PROVENANCE_VERSION,
            "reviewer_task_id": "test-rendered-editor",
            "reviewer_run_id": "test-rendered-editor-run",
            "input_fingerprint": frame_review_input_fingerprint(frames),
            "raw_response": raw_response,
            "raw_response_fingerprint": review_response_fingerprint(raw_response),
            "output_fingerprint": "",
        },
    }
    readability["review_provenance"]["output_fingerprint"] = (
        frame_review_output_fingerprint(readability)
    )
    checks["visual_story_readability"] = readability
    qa_path.write_text(json.dumps(qa), encoding="utf-8")
    return qa
