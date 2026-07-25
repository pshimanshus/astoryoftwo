from pathlib import Path

from pipeline.layer_e.contracts import StoryRoute
from pipeline.layer_e.engine import run_layer_e
from pipeline.layer_e.scoring import detect_hard_fails, score_route
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


def test_layer_e_runs_human_story_council_before_writing():
    decision = run_layer_e(
        ROOT,
        {
            "task_type": "carousel_idea",
            "story_or_moment": (
                "Use three identity photos: a warm resort selfie, a cheek-kiss home "
                "photo, and a resort portrait. Think of the next 1M-view carousel."
            ),
            "constraints": [
                "no aesthetic-first carousel",
                "must define what success looks like before writing",
                "must run Layer E council discussion before copy",
            ],
            "requested_tone": "shareable human love story",
            "reference_images": [
                "identity_images/WhatsApp Image 2026-05-19 at 22.28.03.jpeg",
                "identity_images/WhatsApp Image 2026-05-19 at 22.28.04.jpeg",
                "identity_images/WhatsApp Image 2026-05-19 at 22.28.04 (1).jpeg",
            ],
        },
    )

    assert decision.selected_story_lens
    assert decision.human_story_setup["emotional_obstacle"]
    assert decision.human_story_setup["shareable_setup"]
    assert decision.human_story_setup["cold_reader_doorway"]
    assert decision.success_definition["audience_success"]
    assert decision.success_definition["creative_success"]
    assert decision.success_definition["brand_success"]
    assert decision.success_definition["production_success"]
    assert "this is us" in decision.success_definition["audience_success"].lower()

    story_room = decision.rooms["story_meaning_room"]
    audience_room = decision.rooms["audience_algorithm_room"]
    repair_room = decision.rooms["contrarian_repair_room"]
    synthesis_room = decision.rooms["final_synthesis_room"]

    assert story_room.inputs_used
    assert story_room.debate_records
    assert len(story_room.debate_records) >= 3
    assert any("human story" in item.lower() for item in story_room.debate_records)
    assert any("share" in item.lower() or "send" in item.lower() for item in audience_room.debate_records)
    assert repair_room.repaired_route_names
    assert synthesis_room.selected_outputs["human_story_setup"] == decision.human_story_setup["shareable_setup"]
    assert synthesis_room.selected_outputs["what_success_looks_like"] == decision.success_definition["audience_success"]


def test_story_selling_score_rejects_generic_filled_score_wrapper():
    route = StoryRoute(
        name="Filled But Generic",
        story_lens="A warm relationship idea about being loved fully.",
        reader_mirror="People in relationships will relate to this soft feeling.",
        emotional_obstacle="The idea risks becoming generic romance.",
        aachu_specific_spark="She brings expressive energy.",
        zuv_active_role="He responds with care.",
        proof_engine="A concrete behavior proves the relationship truth.",
        emotional_reversal="The surface becomes meaning.",
        payoff="Maybe love is being understood.",
        distribution_reason="People may save this because it feels nice.",
        process_influence_ids=["card-07"],
    )

    score = score_route(route)
    hard_fails = detect_hard_fails(route)

    assert score.total < 28
    assert "stage-scene gate has no drawable action/reaction proof" in hard_fails


def test_layer_e_decision_requires_stage_scene_and_golden_theme_gates():
    decision = run_layer_e(
        ROOT,
        {
            "task_type": "carousel_idea",
            "story_or_moment": (
                "Plate Stack Marriage Test: dinner, both done, Zuv silently slides "
                "his plate to Aachu, she deadpan stacks her plate on top and says "
                "dono rakh do, then he walks to the kitchen with both plates."
            ),
            "constraints": ["storyboard first", "no chore lecture"],
            "requested_tone": "ordinary married-life comedy",
            "reference_images": ["identity_images/aachu_zuv.png"],
        },
    )

    assert decision.stage_scene_gate["status"] == "GO"
    assert decision.stage_scene_gate["action"]
    assert decision.stage_scene_gate["hands_or_object_movement"]
    assert decision.golden_theme_score.total >= 28


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


def test_failed_date_mature_repair_is_scored_as_sendable_story_not_generic_moment():
    decision = run_layer_e(
        ROOT,
        {
            "task_type": "carousel_idea",
            "story_or_moment": (
                "Aachu and Zuv leave for a date in their car. A missing car key, "
                "rain, traffic, and three wrong turns make the reservation fail. "
                "Zuv gives her a minute without creating distance. They turn the "
                "failed plan into roadside chai, then the final callback shows both "
                "of them outside checking the closed apartment door before departure."
            ),
            "constraints": [
                "car only, never scooter",
                "mature mutual repair",
                "partner-send payoff",
            ],
            "requested_tone": "funny, familiar, and emotionally mature",
            "reference_images": ["identity_images/aachu_zuv.png"],
        },
    )

    assert decision.status == "GO"
    assert decision.selected_story_lens.startswith("Mature love does not remove")
    assert decision.story_selling_score.total >= 28
    assert decision.golden_theme_score.total >= 28
    assert decision.hard_fails == []
    assert decision.stage_scene_gate["status"] == "GO"
    assert "send this to the partner" in decision.distribution_reason.lower()
