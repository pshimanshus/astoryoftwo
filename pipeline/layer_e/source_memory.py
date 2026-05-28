from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from pipeline.layer_e.cards import load_concept_process_cards
from pipeline.layer_e.contracts import LayerESourceMemory, SourcePattern


REFERENCE_DIR = Path("config/references/story-selling-canon")
SUCCESSFUL_STANDARD = Path("wiki/insights/successful-carousel-standard.md")
GOLD_THEME = Path("wiki/themes/calm-enough-for-chaos.md")
VIRAL_ANALYSIS = Path("output/reports/2026-05-17-he-didnt-marry-peace-viral-theme-analysis.md")
IDEA_PREFERENCES = Path("memory/semantic/carousel-idea-preferences.md")


def latest_story_canon_output(root: Path) -> Path:
    base = root / "output" / "story-canon"
    dated = sorted(path for path in base.iterdir() if path.is_dir())
    if not dated:
        raise FileNotFoundError("No output/story-canon/<date> directory found.")
    return dated[-1]


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _excerpt(path: Path, limit: int = 1600) -> str:
    if not path.exists():
        return ""
    text = path.read_text(encoding="utf-8")
    return text[:limit]


def _patterns(pattern_map: dict[str, Any], key: str) -> list[SourcePattern]:
    results: list[SourcePattern] = []
    for item in pattern_map.get(key, []):
        results.append(
            SourcePattern(
                id=str(item.get("id", "")),
                title=str(item.get("title", "")),
                schema_name=str(item.get("schema", key)),
                source_ids=[str(value) for value in item.get("source_ids", [])],
                confidence=float(item.get("confidence", 0.5)),
                summary=str(item.get("summary", "")),
                steps={str(k): str(v) for k, v in item.get("steps", {}).items()},
            )
        )
    return results


def load_layer_e_source_memory(root: Path) -> LayerESourceMemory:
    root = root.resolve()
    latest = latest_story_canon_output(root)
    source_register = REFERENCE_DIR / "source-register.json"
    concept_bank = latest / "concept-process-bank.json"
    pattern_map_path = latest / "pattern-map.json"
    pattern_map = _read_json(root / pattern_map_path)
    reference_paths = [
        str(SUCCESSFUL_STANDARD),
        str(GOLD_THEME),
        str(VIRAL_ANALYSIS),
        str(IDEA_PREFERENCES),
        str(REFERENCE_DIR / "source-policy.md"),
        str(REFERENCE_DIR / "a-story-of-two-adaptation.md"),
        str(REFERENCE_DIR / "concept-process-cards.md"),
        str(REFERENCE_DIR / "rubric.md"),
        str(REFERENCE_DIR / "romance-novel-canon.md"),
        str(REFERENCE_DIR / "romance-film-canon.md"),
        str(REFERENCE_DIR / "story-selling-online.md"),
        "story-selling-online.md",
    ]
    return LayerESourceMemory(
        source_register_path=str(source_register),
        concept_process_bank_path=str(concept_bank),
        pattern_map_path=str(pattern_map_path),
        reference_paths=reference_paths,
        process_cards=load_concept_process_cards(root, root / concept_bank),
        romance_arcs=_patterns(pattern_map, "romance_arc"),
        film_scene_engines=_patterns(pattern_map, "scene_engine"),
        online_story_patterns=_patterns(pattern_map, "story_selling_online"),
        carousel_adapters=_patterns(pattern_map, "carousel_adapter"),
        success_standard_excerpt=_excerpt(root / SUCCESSFUL_STANDARD),
        creator_preference_excerpt=_excerpt(root / IDEA_PREFERENCES),
    )
