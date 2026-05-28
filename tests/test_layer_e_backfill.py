import json
from pathlib import Path

from scripts.backfill_layer_e_artifacts import backfill_layer_e_artifacts


def test_backfill_layer_e_artifacts_writes_decision_without_touching_existing_files(tmp_path: Path):
    carousel = tmp_path / "output" / "carousels" / "2026-05-28" / "plate-stack-marriage-test"
    carousel.mkdir(parents=True)
    sentinel = carousel / "final-approval.md"
    sentinel.write_text("keep me\n", encoding="utf-8")
    (carousel / "manifest.json").write_text(
        json.dumps(
            {
                "title": "Plate Stack Marriage Test",
                "source_story": "Zuv slides his plate to Aachu. She stacks hers on top and says dono rakh do.",
            }
        ),
        encoding="utf-8",
    )
    (carousel / "concept.json").write_text(
        json.dumps({"human_truth": "A tiny household joke becomes proof of comfort."}),
        encoding="utf-8",
    )
    (carousel / "storyboard.md").write_text("# Storyboard\n\nDono rakh do.", encoding="utf-8")

    result = backfill_layer_e_artifacts(carousel)

    layer_e = json.loads((carousel / "layer-e-story-selling.json").read_text(encoding="utf-8"))
    assert result["status"] == "GO"
    assert result["artifact"] == str(carousel / "layer-e-story-selling.json")
    assert layer_e["selected_story_lens"]
    assert "dono rakh do" in layer_e["emotional_machine"].lower()
    assert sentinel.read_text(encoding="utf-8") == "keep me\n"
