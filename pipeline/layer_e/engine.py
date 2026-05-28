from __future__ import annotations

from pathlib import Path
from typing import Any

from pipeline.layer_e.contracts import LayerEDecision, LayerERequest
from pipeline.layer_e.rooms import build_rooms, generate_exploration_routes, process_influences_for_story
from pipeline.layer_e.scoring import detect_hard_fails, score_route, status_for
from pipeline.layer_e.source_memory import load_layer_e_source_memory


def _adaptation_target(task_type: str) -> str:
    if task_type in {"carousel_idea", "story_repair"}:
        return "C-layer"
    if task_type == "article_angle":
        return "D-layer"
    if task_type == "prepost_reel":
        return "B-layer"
    return "diagnostic"


def _golden_theme_gate(task_type: str) -> str:
    return "required_for_carousel" if task_type in {"carousel_idea", "story_repair"} else "not_applicable"


def run_layer_e(root: Path, request: dict[str, Any] | LayerERequest) -> LayerEDecision:
    parsed = request if isinstance(request, LayerERequest) else LayerERequest.model_validate(request)
    memory = load_layer_e_source_memory(root)
    influences = process_influences_for_story(parsed.story_or_moment, memory)
    routes = generate_exploration_routes(parsed.story_or_moment, influences)
    winner = max(routes, key=lambda route: route.score_total)
    score = score_route(winner)
    hard_fails = detect_hard_fails(winner)
    status = status_for(score, hard_fails)
    rooms = build_rooms(routes)
    rejected = [route for route in routes if route.name != winner.name and route.verdict != "GO"]
    repaired = [route for route in routes if route.name != winner.name and route.verdict == "GO"][:2]
    required_repairs = [] if status == "GO" else [
        "Repair the story route until it has obstacle, proof, active Zuv role, reversal, and send/save reason."
    ]
    return LayerEDecision(
        status=status,
        task_type=parsed.task_type,
        adaptation_target=_adaptation_target(parsed.task_type),
        rooms=rooms,
        exploration_routes=routes,
        repaired_routes=repaired,
        rejected_routes=rejected,
        selected_story_lens=winner.story_lens,
        emotional_machine=(
            f"{winner.emotional_obstacle} -> {winner.proof_engine} -> {winner.emotional_reversal} -> {winner.payoff}"
        ),
        proof_engine=winner.proof_engine,
        reader_mirror=winner.reader_mirror,
        distribution_reason=winner.distribution_reason,
        process_influences=influences,
        story_selling_score=score,
        hard_fails=hard_fails,
        required_repairs=required_repairs,
        golden_theme_gate=_golden_theme_gate(parsed.task_type),
        downstream_contract={
            "c_layer": {
                "must_preserve": [
                    "selected_story_lens",
                    "emotional_machine",
                    "proof_engine",
                    "reader_mirror",
                    "distribution_reason",
                ],
                "golden_theme_gate": _golden_theme_gate(parsed.task_type),
            },
            "d_layer": {"article_angle_source": "selected_story_lens"},
            "b_layer": {"prepost_brief_source": "rooms"},
        },
        metadata={
            "source_register_path": memory.source_register_path,
            "concept_process_bank_path": memory.concept_process_bank_path,
            "pattern_map_path": memory.pattern_map_path,
            "reference_paths": memory.reference_paths,
            "constraints": parsed.constraints,
            "requested_tone": parsed.requested_tone,
            "reference_images": parsed.reference_images,
        },
    )
