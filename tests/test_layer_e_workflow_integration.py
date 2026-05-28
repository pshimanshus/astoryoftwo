import json
from datetime import date
from pathlib import Path

from pipeline.stages.codex_builtin_image_generation import prepare_codex_builtin_image_generation
from pipeline.stages.codex_native_carousel import create_codex_native_carousel


def write_identity(path: Path) -> None:
    path.write_bytes(b"\x89PNG\r\n\x1a\n")


def test_codex_native_carousel_writes_layer_e_room_artifact(tmp_path: Path):
    identity = tmp_path / "aachu_zuv.png"
    write_identity(identity)

    out_dir = create_codex_native_carousel(
        title="Plate Stack Marriage Test",
        story=(
            "Plate Stack Marriage Test: dinner, both done, Zuv silently slides "
            "his plate to Aachu, she stacks hers on top and says dono rakh do."
        ),
        image_paths=[],
        identity_image_paths=[identity],
        slide_count=7,
        output_root=tmp_path / "output" / "carousels",
        render_assets=False,
        today=date(2026, 5, 28),
    )

    layer_e = json.loads((out_dir / "layer-e-story-selling.json").read_text(encoding="utf-8"))
    concept = json.loads((out_dir / "concept.json").read_text(encoding="utf-8"))
    review = json.loads((out_dir / "review.json").read_text(encoding="utf-8"))

    assert layer_e["status"] == "GO"
    assert layer_e["selected_story_lens"]
    assert layer_e["human_story_setup"]["emotional_obstacle"]
    assert layer_e["success_definition"]["audience_success"]
    assert layer_e["stage_scene_gate"]["status"] == "GO"
    assert layer_e["golden_theme_score"]["total"] >= 28
    assert len(layer_e["rooms"]) >= 5
    assert len(layer_e["exploration_routes"]) >= 5
    assert any(item["id"] == "card-05" for item in layer_e["process_influences"])
    assert concept["layer_e_story_selling"]["artifact"] == "layer-e-story-selling.json"
    assert concept["layer_e_story_selling"]["selected_story_lens"] == layer_e["selected_story_lens"]
    assert concept["layer_e_story_selling"]["human_story_setup"] == layer_e["human_story_setup"]
    assert concept["layer_e_story_selling"]["success_definition"] == layer_e["success_definition"]
    assert concept["layer_e_story_selling"]["stage_scene_gate"] == layer_e["stage_scene_gate"]
    assert concept["layer_e_story_selling"]["golden_theme_score"] == layer_e["golden_theme_score"]
    assert review["story_selling_gate"]["source"] == "layer-e-story-selling.json"
    assert review["story_selling_gate"]["stage_scene_gate"]["status"] == "GO"


def test_image_handoff_blocks_missing_layer_e_artifact(tmp_path: Path):
    carousel = tmp_path / "carousel"
    carousel.mkdir()
    (carousel / "visual-plan-quality.json").write_text(
        json.dumps({"status": "PASS", "can_generate": True, "issues": []}),
        encoding="utf-8",
    )
    (carousel / "identity-consistency-review.json").write_text(
        json.dumps({"status": "PASS"}),
        encoding="utf-8",
    )
    (carousel / "prompt-pack.json").write_text(
        json.dumps(
            {
                "slides": [
                    {
                        "slide": 1,
                        "text": "test",
                        "prompt": "test prompt",
                        "visual": "test visual",
                        "style": "warm paper",
                        "negative_prompt": "none",
                    }
                ]
            }
        ),
        encoding="utf-8",
    )

    result = prepare_codex_builtin_image_generation(carousel)

    assert result["status"] == "blocked"
    assert "layer-e-story-selling.json" in result["reason"]
