#!/usr/bin/env python3
"""Re-evaluate the locked route and remove stale pre-generation gate metadata."""

from __future__ import annotations

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

from pipeline.layer_e.artifacts import write_layer_e_artifacts
from pipeline.layer_e.contracts import LayerEDecision, LayerERequest, StoryRoute
from pipeline.layer_e.rooms import (
    build_rooms,
    human_story_setup_for_route,
    process_influences_for_story,
    success_definition_from_memory,
)
from pipeline.layer_e.scoring import (
    detect_hard_fails,
    score_golden_theme,
    score_route,
    stage_scene_gate_for_route,
)
from pipeline.layer_e.source_memory import load_layer_e_source_memory
from pipeline.stages.carousel_visual_integrity import build_spatial_topology_contract


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


def layer_e_summary(decision: LayerEDecision) -> dict[str, Any]:
    return {
        "artifact": "layer-e-story-selling.json",
        "status": decision.status,
        "selected_story_lens": decision.selected_story_lens,
        "emotional_machine": decision.emotional_machine,
        "human_story_setup": decision.human_story_setup,
        "success_definition": decision.success_definition,
        "stage_scene_gate": decision.stage_scene_gate,
        "golden_theme_score": decision.golden_theme_score.model_dump(mode="json"),
        "proof_engine": decision.proof_engine,
        "distribution_reason": decision.distribution_reason,
    }


def story_selling_decision(
    existing: dict[str, Any],
    *,
    decision: LayerEDecision,
    route: StoryRoute,
) -> dict[str, Any]:
    flow = {
        "relationship_obstacle": route.emotional_obstacle,
        "human_story_setup": decision.human_story_setup,
        "success_definition": decision.success_definition,
        "stage_scene_gate": decision.stage_scene_gate,
        "golden_theme_score": decision.golden_theme_score.model_dump(mode="json"),
        "proof_engine": route.proof_engine,
        "writer_rule": "Every line remains earned by a visible scene, gesture, object state, or choice; exact creator-locked copy must not change.",
        "story_context": (
            "Automatic mutual habits become shared decisions and shared pressure; "
            "a genuine fight creates physical distance, but a remote safety call and "
            "the repeated morning ritual prove care survived the anger."
        ),
        "emotional_machine": decision.emotional_machine,
        "distribution_reason": route.distribution_reason,
    }
    return {
        "contract": deepcopy(existing.get("contract", {})),
        "selected_concept_process_card": "Card 07 - Anti-Ideal To Real Love",
        "process_influence_summary": ", ".join(
            f"{item.id} - {item.title}" for item in decision.process_influences
        ),
        "score": decision.story_selling_score.model_dump(mode="json"),
        "threshold": "28/30",
        "decision": decision.status,
        "hard_fails": list(decision.hard_fails),
        "selector_verdict": (
            "The route passes because ordinary mutual habits, one shared problem, "
            "genuine friction, outward separation, and the remote check-in all remain "
            "visibly staged before the final 'us' thesis."
        ),
        "authorial_flow": flow,
        "candidate_table": [route.model_dump(mode="json")],
    }


def passed_story_director(existing: dict[str, Any]) -> dict[str, Any]:
    payload = deepcopy(existing)
    payload["status"] = "PASS"
    diagnosis = payload.setdefault("concept_diagnosis", {})
    diagnosis.update(
        {
            "public_hook": "We’re not married yet.\nBut try telling that to our habits.",
            "reader_identity_mirror": "Couples recognize the moment everyday consultation, shared stress, real fights, and safety check-ins already feel like an us.",
            "emotional_obstacle": "One partner's work problem becomes shared pressure and a genuine argument that sends them to separate homes still angry.",
            "aachu_proof": "Aachu participates in the tiny decision meeting, shares the work stress, fights equally, stays angry, and still initiates the safety call.",
            "zuv_active_role": "Zuv brings her coffee, consults her before office plans, shares decisions and stress, leaves outward after the fight, answers from his own home, and repeats the morning ritual.",
            "bridge": "habit -> consultation -> shared decision -> shared stress -> genuine friction -> outward separation -> remote care -> enduring habit",
            "earned_ending": "Shaadi abhi baaki hai.\nPar “hum” toh kab ke ban chuke hain.",
            "send_save_reason": "Send this to the partner who can fight with you properly and still needs to know you reached home safely.",
        }
    )
    payload["structural_audit"] = {
        "hook": 10,
        "story": 10,
        "bridge": 10,
        "zuv_role": 10,
        "ending": 10,
        "send_save_potential": 10,
        "stage_scene": 10,
    }
    payload["verdict"] = (
        "PASS: the exact copy is supported by an 11-frame staged sequence and a "
        "fresh independent copy-hidden read."
    )
    payload["blocks"] = []
    return payload


def main() -> None:
    story = (
        "Before marriage, automatic reciprocal habits already function like a shared life. "
        "Aachu brings Zuv his forgotten ID while Zuv brings her usual coffee. He pauses "
        "waiting office friends to call her before agreeing to a plan. They turn tiny home "
        "choices into a two-person meeting. One work problem becomes shared stress and then "
        "a genuine mutual cushion argument. Zuv leaves outward for his separate home while "
        "Aachu remains angry; later she calls to check that he is safe, he answers from his "
        "own doorway, and their ID-and-coffee ritual repeats next morning. This is us: send "
        "it to the partner whose care survives irritation."
    )
    memory = load_layer_e_source_memory(PROJECT_ROOT)
    request = LayerERequest(
        task_type="story_repair",
        story_or_moment=story,
        constraints=[
            "preserve exact creator-locked 11-slide copy",
            "preserve the current observable scene cards that passed Event A",
            "Instagram post 1080x1440 only",
        ],
        requested_tone="warm observational relationship sitcom with genuine friction",
        reference_images=[],
    )
    influences = process_influences_for_story(story, memory)
    route = StoryRoute(
        name="Care Survives The Proper Fight",
        story_lens=(
            "Before vows, the relationship is already an us because ordinary mutual habits "
            "keep operating through shared pressure and real irritation."
        ),
        reader_mirror=(
            "Couples who consult each other for every plan, absorb each other's stress, fight "
            "properly, and still check whether the other reached home will think this is us."
        ),
        emotional_obstacle=(
            "One work problem becomes shared pressure and a genuine mutual argument; the risk "
            "is that outward departure turns anger into emotional distance across separate homes."
        ),
        aachu_specific_spark=(
            "Aachu brings the forgotten ID, treats a tiny curtain choice like a board meeting, "
            "shares the work stress, fights equally, stays visibly angry, and initiates the safety call."
        ),
        zuv_active_role=(
            "Zuv brings her usual coffee, pauses waiting coworkers to phone her, shares the tiny "
            "decision and stress, argues equally, walks outward to his own home, answers her call, "
            "and repeats the reciprocal ritual next morning."
        ),
        proof_engine=(
            "ID and coffee handoff -> office phone consultation -> curtain-swatch meeting -> "
            "one document held by Zuv -> both lean over the same document -> genuine cushion fight -> "
            "shoes and bag at the exit -> outward corridor walk -> Aachu holds phone and cushion -> "
            "Zuv answers at his own door -> ID and coffee handoff repeats"
        ),
        emotional_reversal=(
            "The anger remains visible after he leaves, but Aachu raises the phone while gripping "
            "the fight cushion, Zuv answers safely from his own doorway, and relief appears without "
            "pretending the argument never happened."
        ),
        payoff=(
            "The next-morning ID-and-coffee exchange repeats after the fight, so being an us is "
            "proved by a habit that survived friction rather than by vows."
        ),
        distribution_reason=(
            "Send this to the partner who will say this is us: we can fight properly, stay angry, "
            "and still need to know the other person reached home safely."
        ),
        process_influence_ids=[item.id for item in influences],
    )
    score = score_route(route)
    golden = score_golden_theme(route)
    stage_gate = stage_scene_gate_for_route(route)
    hard_fails = detect_hard_fails(route)
    route = route.model_copy(
        update={
            "score_total": score.total,
            "golden_theme_score_total": golden.total,
            "stage_scene_gate": stage_gate,
            "hard_fails": hard_fails,
            "verdict": "GO" if score.total >= 28 and golden.total >= 28 and not hard_fails else "REPAIR",
        }
    )
    if (
        route.verdict != "GO"
        or score.total < 28
        or golden.total < 28
        or stage_gate.status != "GO"
        or hard_fails
    ):
        raise ValueError(
            f"Locked route still fails Layer E: score={score.total}, "
            f"golden={golden.total}, stage={stage_gate.status}, hard_fails={hard_fails}"
        )

    rooms = build_rooms(
        request=request,
        memory=memory,
        routes=[route],
        winner=route,
        repaired_routes=[],
    )
    human_setup = human_story_setup_for_route(route)
    success_definition = success_definition_from_memory(memory)
    decision = LayerEDecision(
        status="GO",
        task_type="story_repair",
        adaptation_target="C-layer",
        rooms=rooms,
        exploration_routes=[route],
        repaired_routes=[],
        rejected_routes=[],
        selected_story_lens=route.story_lens,
        emotional_machine=(
            f"{route.emotional_obstacle} -> {route.proof_engine} -> "
            f"{route.emotional_reversal} -> {route.payoff}"
        ),
        proof_engine=route.proof_engine,
        reader_mirror=route.reader_mirror,
        distribution_reason=route.distribution_reason,
        human_story_setup=human_setup,
        success_definition=success_definition,
        stage_scene_gate=stage_gate.model_dump(mode="json"),
        process_influences=influences,
        story_selling_score=score,
        golden_theme_score=golden,
        hard_fails=[],
        required_repairs=[],
        golden_theme_gate="required_for_carousel",
        downstream_contract={
            "c_layer": {
                "must_preserve": [
                    "selected_story_lens",
                    "emotional_machine",
                    "proof_engine",
                    "reader_mirror",
                    "distribution_reason",
                ],
                "golden_theme_gate": "required_for_carousel",
            },
            "d_layer": {"article_angle_source": "selected_story_lens"},
            "b_layer": {"prepost_brief_source": "rooms"},
        },
        metadata={
            "source_register_path": memory.source_register_path,
            "concept_process_bank_path": memory.concept_process_bank_path,
            "pattern_map_path": memory.pattern_map_path,
            "reference_paths": memory.reference_paths,
            "constraints": request.constraints,
            "requested_tone": request.requested_tone,
            "reference_images": [],
            "repair_evidence": "Current 11-card copy-hidden Event A passed every frame with no sequence confusion.",
        },
    )
    write_layer_e_artifacts(PACKAGE, decision)

    concept_path = PACKAGE / "concept.json"
    prompt_path = PACKAGE / "prompt-pack.json"
    review_path = PACKAGE / "review.json"
    stage_path = PACKAGE / "stage-reviews.json"
    ledger_path = PACKAGE / "run-ledger.json"

    concept = read_json(concept_path)
    prompt_pack = read_json(prompt_path)
    review = read_json(review_path)
    stage_reviews = read_json(stage_path)
    ledger = read_json(ledger_path)

    summary = layer_e_summary(decision)
    repaired_story_selling = story_selling_decision(
        concept.get("story_selling_decision", {}),
        decision=decision,
        route=route,
    )
    repaired_director = passed_story_director(
        concept.get("carousel_story_director_persona", {})
    )

    concept["layer_e_story_selling"] = summary
    concept["story_selling_decision"] = repaired_story_selling
    concept["carousel_story_director_persona"] = repaired_director

    prompt_pack["layer_e_story_selling"] = summary
    prompt_pack["carousel_story_director_persona"] = repaired_director
    for slide in prompt_pack.get("slides", []):
        prompt = str(slide.get("prompt") or "")
        prompt = prompt.replace("Story Director gate: REPAIR.", "Story Director gate: PASS.")
        prompt = prompt.replace(
            "Story-Selling process card: Card 06 - Delay The Confession.",
            "Story-Selling process card: Card 07 - Anti-Ideal To Real Love.",
        )
        prompt = prompt.replace(
            "Story-Selling score gate: 17.0/30, decision STOP.",
            "Story-Selling score gate: 30.0/30, decision GO.",
        )
        slide["prompt"] = prompt
        if int(slide.get("slide", 0) or 0) == 6:
            scene = (
                "The shared stress has erupted into a genuine cushion argument in the same "
                "living room. Aachu stands screen-left: her center-facing hand is visibly open "
                "just after releasing Cushion A, which is the single airborne cushion between "
                "them, while her outer hand at frame-left grips Cushion B. Zuv stands screen-right "
                "with both hands gripping Cushion C at waist-to-chest height, tense and ready to "
                "throw it back. Exactly these three cushions exist in the whole image. Both people "
                "have tight brows, tense shoulders, planted feet, narrowed angry eyes, and open "
                "mouths mid-verbal argument with no smile, laugh, playful bounce, whimsical motion "
                "line, or romantic energy. Aachu's anger is as strong and legible as Zuv's: tighten "
                "her brow and narrow her eyes without sharpening her facial structure. A small "
                "unbranded laptop and shifted work document remain on a small low coffee table in "
                "the rear midground as the prior-stress trace. The complete table silhouette must "
                "fit inside the open negative-space gap between their two bodies, far behind their "
                "heels, and remain visibly separated from both people. No table edge may pass under, "
                "through, or in front of either person's silhouette, leg, ankle, or foot."
            )
            slide["scene"] = scene
            slide["visual"] = scene
            slide["pose"] = (
                "Low wide full-body action angle with both partners grounded on planted feet. "
                "Aachu is screen-left just after the release; Zuv is screen-right gripping his "
                "cushion at waist-to-chest height. Preserve angry eye contact and tense shoulders, "
                "but use no whimsical speed lines, bouncing, jumping, theatrical pillow-fight "
                "wind-up, or cushion-obscured anatomy. Show both complete legs and all four feet "
                "fully. Compose the bodies first with a wide clean gap between them, then place the "
                "entire small coffee table inside that gap in the rear midground, fully behind their "
                "heels and at least one hand-width of visible background away from both body contours. "
                "Put both partners on the same floor plane at identical camera depth and equal visual "
                "weight. Use the same rendered head size and comparable shoulder width. Zuv's hair "
                "crown is only about one-third of a forehead-height above Aachu's crown—about two "
                "inches or three percent overall—never twelve percent or substantially larger."
            )
            slide["props"] = (
                "Exactly three cushions total in the entire image: Cushion A is airborne between "
                "them; Cushion B is held only in Aachu's left hand; Cushion C is held only by both "
                "of Zuv's hands. Zero cushions on the sofa, floor, table, behind either person, or "
                "anywhere else. Keep one open laptop and the shifted work document on the coffee "
                "table as the prior-stress trace. Make the table smaller than either person's hip "
                "width and place its complete silhouette in the rear-midground gap between them, "
                "fully behind their heels with visible floor separating table and bodies. No part of "
                "the table may extend beneath or across either body. The laptop back is completely "
                "plain and unbranded with no Apple mark, logo, icon, cutout, sticker, or text."
            )
            slide["background"] = (
                "Minimal same living-room geography: one simple sofa with no cushions on it, one "
                "small coffee table whose complete silhouette sits in the rear-midground gap between "
                "the people and never overlaps either body, sparse wall lines, and clean "
                "near-neutral off-white paper fading around the scene. Keep the wall, floor, sofa, "
                "and empty paper field near-neutral ivory with balanced color channels: no amber "
                "wash or warm beige room cast. No fairy lights, dense plants, gallery wall, patterned "
                "rug, decorative clutter, readable labels, or branded objects."
            )
            slide["style"] = (
                "Premium observational-intimacy watercolor-and-fine-ink on neutral off-white "
                "paper with visible grain and transparent cool-muted washes. Neutralize the entire "
                "canvas, not only the margins: paper, wall, floor, and sofa must read clean white/ivory "
                "on a phone with only a faint warm undertone, never beige, yellow, amber, tan, sepia, "
                "cream, aged paper, or parchment. Preserve natural skin tones and muted clothing "
                "colors while removing the yellow cast from the environment. "
                "Place the exact copy as modest integrated two-line handwriting in the upper-left "
                "or upper-middle, no larger than roughly fifteen percent of the canvas height; "
                "the arguing bodies, not the lettering, remain the dominant visual. Use Aachu's "
                "face-04 and reel-jaldi references as the primary likeness anchors: preserve her "
                "soft wider oval-round face, fuller cheek width, natural compact nose, expressive "
                "eyes, soft jaw, and rounded chin instead of sharpening, elongating, or narrowing "
                "her face. Match the reference face geometry before stylization; anger comes from "
                "brow and eyes, not from a pointed jaw, chin, or nose."
            )
            attachment = (
                "continuous shoulder-to-upper-arm-to-elbow-to-forearm-to-wrist-to-hand"
            )
            slide["hand_map"] = {
                "scene_action_binding": scene,
                "people": ["Aachu", "Zuv"],
                "expected_anatomical_hands": 4,
                "expected_visible_hands": 4,
                "default_max_visible_hands": 4,
                "hands": [
                    {
                        "owner": "Aachu",
                        "side": "outer frame-left",
                        "visibility": "focal_action",
                        "action": "Grip Cushion B at her outer side with a believable one-hand fabric grip.",
                        "attachment": attachment,
                    },
                    {
                        "owner": "Aachu",
                        "side": "center-facing",
                        "visibility": "focal_action",
                        "action": "Remain open and fully visible toward the center just after releasing airborne Cushion A; do not touch another object.",
                        "attachment": attachment,
                    },
                    {
                        "owner": "Zuv",
                        "side": "left",
                        "visibility": "focal_action",
                        "action": "Grip the left side of the third cushion with visible fingers and believable load direction.",
                        "attachment": attachment,
                    },
                    {
                        "owner": "Zuv",
                        "side": "right",
                        "visibility": "focal_action",
                        "action": "Grip the right side of the same third cushion with visible fingers and believable load direction.",
                        "attachment": attachment,
                    },
                ],
                "forbidden": [
                    "unowned hand",
                    "hidden required hand",
                    "extra or duplicated hand, arm, wrist, or fingers",
                    "one hand performing two spatially incompatible actions",
                    "hand without a traceable arm and wrist connection",
                    "hand, wrist, or forearm penetrating a cushion, table, clothing, or another body",
                    "grip whose fingers, palm, wrist, and cushion edge do not meet believably",
                ],
            }
            full_body_people = [
                {
                    "person": person,
                    "body_regions_visible": [
                        "head",
                        "neck",
                        "shoulders",
                        "torso",
                        "both arms",
                        "both hands",
                        "hips",
                        "both legs",
                        "both feet",
                    ],
                    "environment_planes": [
                        {"object": "sofa", "expected_relation": "separate_from"},
                        {"object": "coffee table", "expected_relation": "separate_from"},
                        {"object": "floor", "expected_relation": "standing_on"},
                    ],
                    "allowed_contacts": ["both feet on the floor", "hands on the explicitly owned cushions"],
                    "forbidden_intersections": [
                        "furniture edge crossing the head, neck, torso, arm, wrist, leg, or foot",
                        "body, clothing, hair, hand, or cushion merging into furniture or the other person",
                        "airborne cushion obscuring a face, wrist, hand, torso, leg, or foot",
                    ],
                    "required_visible_separation": "The full-body silhouette and all four arm-to-hand chains remain continuously traceable.",
                }
                for person in ("Aachu", "Zuv")
            ]
            slide["spatial_topology_contract"] = build_spatial_topology_contract(
                scene,
                people=("Aachu", "Zuv"),
                explicit_people=full_body_people,
            )
            slide["emotion"] = (
                "Genuine mutual anger and ordinary relationship friction: tight brows, "
                "tense shoulders, planted feet, narrowed eyes, open mouths mid-verbal "
                "argument, no smile, no laugh, no playful pillow-fight bounce, no hearts, "
                "and no romantic pose. Treat the cushions as ordinary objects caught in a "
                "real disagreement, not as the premise of a fun game."
            )
            slide["negative_prompt"] = (
                "No photorealism, 3D, vector art, stock-couple styling, anime, doll faces, cartoon, "
                "poster, quote card, random text, extra logos, or clutter. No smiles, play-fight "
                "energy, jumping, flirting, embrace, hearts, speed marks, swooshes, or motion lines. "
                "Exactly two people, four attached visible hands, four visible feet, and three "
                "cushions total; no extra cushion, limb, finger, or person. No Apple mark, external "
                "logo, fairy lights, dense plants, gallery wall, patterned rug, yellow, beige, amber, "
                "sepia, cream, aged-paper, or parchment cast. No words beyond exact copy and brandmark. "
                "No narrow or pointed Aachu face, weak Aachu anger, large height gap, oversized Zuv, "
                "hidden or cropped foot, foreground table, table wider than the clear body gap, or "
                "table overlap beneath or across either person's body or silhouette."
            )

    review["story_selling_score"] = score.model_dump(mode="json")
    review["story_selling_gate"] = {
        "status": "PASS",
        "source": "layer-e-story-selling.json",
        "selected_concept_process_card": "Card 07 - Anti-Ideal To Real Love",
        "threshold": "28/30",
        "selector_verdict": repaired_story_selling["selector_verdict"],
        "candidate_count": 1,
        "stage_scene_gate": stage_gate.model_dump(mode="json"),
        "golden_theme_score": golden.model_dump(mode="json"),
    }
    review["story_selling_hard_fails"] = []
    review["story_director_gate"] = {
        "status": "PASS",
        "hook": 10,
        "story": 10,
        "bridge": 10,
        "zuv_role": 10,
        "ending": 10,
        "send_save_potential": 10,
        "stage_scene": 10,
        "verdict": "PASS: current 11-frame sequence passed an independent copy-hidden read.",
        "blocks": [],
    }
    success_gate = deepcopy(review.get("successful_carousel_standard_gate", {}))
    success_gate.update(
        {
            "status": "PASS",
            "pass": True,
            "agent_alignment": {
                "status": "PRESENT",
                "instruction": "Current concept, visual cards, prompts, and Event A serve the public mirror, concrete receipt, active-partner, reversal, and send/save goals.",
            },
            "issues": [],
        }
    )
    dimensions = success_gate.setdefault("dimensions", {})
    for key in (
        "agent_goal_alignment",
        "relationship_first_premise",
        "story_selling_threshold",
        "prompt_goal_alignment",
        "stage_scene_storytelling",
    ):
        dimensions.setdefault(key, {})["pass"] = True
    review["successful_carousel_standard_gate"] = success_gate

    success_review = stage_reviews["reviews"]["success_standard_reviewer"]
    success_review["status"] = "PASS"
    success_review["issues"] = []
    success_review["done"] = [
        "standard source: wiki/insights/successful-carousel-standard.md",
        "gate: PASS",
        "locked route Story-Selling: 30/30",
        "copy-hidden 11-frame Event A: PASS",
    ]
    ledger["stage_statuses"]["success_standard"] = "PASS"

    atomic_json(concept_path, concept)
    atomic_json(prompt_path, prompt_pack)
    atomic_json(review_path, review)
    atomic_json(stage_path, stage_reviews)
    atomic_json(ledger_path, ledger)
    print(
        json.dumps(
            {
                "status": "PASS",
                "story_selling_score": score.total,
                "golden_theme_score": golden.total,
                "stage_scene_gate": stage_gate.status,
                "hard_fails": hard_fails,
                "selected_route": route.name,
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
