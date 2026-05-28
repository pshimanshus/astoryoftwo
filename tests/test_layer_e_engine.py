from pathlib import Path

from pipeline.layer_e.engine import run_layer_e
from pipeline.layer_e.source_memory import load_layer_e_source_memory


ROOT = Path(__file__).resolve().parents[1]


def test_source_memory_loads_story_canon_learning_outputs():
    memory = load_layer_e_source_memory(ROOT)

    assert memory.source_register_path == "config/references/story-selling-canon/source-register.json"
    assert memory.concept_process_bank_path.endswith("concept-process-bank.json")
    assert memory.pattern_map_path.endswith("pattern-map.json")
    assert len(memory.process_cards) >= 20
    assert "wiki/insights/successful-carousel-standard.md" in memory.reference_paths
    assert "story-selling-online.md" in memory.reference_paths
    assert any(item.source_ids for item in memory.carousel_adapters)


def test_plate_stack_layer_e_runs_rooms_and_synthesizes_story_lens():
    decision = run_layer_e(
        ROOT,
        {
            "task_type": "carousel_idea",
            "story_or_moment": (
                "Plate Stack Marriage Test: dinner, both done, Zuv silently slides "
                "his plate to Aachu, she deadpan stacks her plate on top and says "
                "dono rakh do, then he walks to the kitchen with both plates."
            ),
            "constraints": [
                "storyboard first",
                "no chore lecture",
                "no best husband",
                "allowed copy only",
            ],
            "requested_tone": "ordinary married-life comedy",
            "reference_images": ["identity_images/aachu_zuv.png"],
        },
    )

    assert decision.status == "GO"
    assert decision.selected_story_lens
    assert decision.emotional_machine
    assert decision.proof_engine
    assert decision.reader_mirror
    assert decision.distribution_reason
    assert len(decision.rooms) >= 5
    assert len(decision.exploration_routes) >= 5
    assert any(influence.id == "card-05" for influence in decision.process_influences)
    assert decision.story_selling_score.total >= 28
    assert decision.hard_fails == []
    assert decision.adaptation_target == "C-layer"
    assert "dono rakh do" in decision.emotional_machine.lower()
    assert "send" in decision.distribution_reason.lower() or "save" in decision.distribution_reason.lower()


def test_layer_e_blocks_pretty_moment_without_obstacle_or_zuv_role():
    decision = run_layer_e(
        ROOT,
        {
            "task_type": "carousel_idea",
            "story_or_moment": "A pretty dinner table with a nice plate and warm light.",
            "constraints": [],
            "requested_tone": "romantic",
            "reference_images": [],
        },
    )

    assert decision.status in {"REPAIR", "STOP"}
    assert "no emotional obstacle" in decision.hard_fails
    assert "zuv has no active emotional role" in decision.hard_fails
    assert decision.story_selling_score.total < 28
