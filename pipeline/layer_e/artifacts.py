from __future__ import annotations

import json
from pathlib import Path

from pydantic import ValidationError

from pipeline.layer_e.contracts import LayerEDecision


JSON_ARTIFACT = "layer-e-story-selling.json"
MD_ARTIFACT = "layer-e-story-selling.md"


def write_layer_e_artifacts(out_dir: Path, decision: LayerEDecision) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    payload = decision.model_dump(mode="json")
    (out_dir / JSON_ARTIFACT).write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    lines = [
        "# Layer E Story-Selling Decision",
        "",
        f"Status: {decision.status}",
        f"Selected story lens: {decision.selected_story_lens}",
        f"Score: {decision.story_selling_score.total}/30",
        "",
        "## Emotional Machine",
        "",
        decision.emotional_machine,
        "",
        "## Rooms",
        "",
    ]
    for key, room in decision.rooms.items():
        lines.append(f"- `{key}`: {room.status} - {room.summary}")
    lines.extend(
        [
            "",
            "## Process Influences",
            "",
            *[f"- `{item.id}`: {item.title} ({item.influence_type})" for item in decision.process_influences],
            "",
        ]
    )
    (out_dir / MD_ARTIFACT).write_text("\n".join(lines), encoding="utf-8")


def load_layer_e_decision(out_dir: Path) -> LayerEDecision:
    path = out_dir / JSON_ARTIFACT
    return LayerEDecision.model_validate_json(path.read_text(encoding="utf-8"))


def layer_e_gate_reason(out_dir: Path) -> str | None:
    path = out_dir / JSON_ARTIFACT
    if not path.exists():
        return f"{JSON_ARTIFACT} is required before Codex built-in image generation."
    try:
        decision = load_layer_e_decision(out_dir)
    except (OSError, ValidationError, json.JSONDecodeError) as exc:
        return f"{JSON_ARTIFACT} could not be loaded: {exc}"
    if decision.status != "GO":
        repairs = decision.required_repairs or ["Layer E did not return GO"]
        return f"{JSON_ARTIFACT} is {decision.status}: " + "; ".join(repairs)
    if decision.hard_fails:
        return f"{JSON_ARTIFACT} has hard fails: " + "; ".join(decision.hard_fails)
    if decision.story_selling_score.total < 28:
        return f"{JSON_ARTIFACT} score is below 28/30."
    if decision.golden_theme_gate == "required_for_carousel" and decision.golden_theme_score.total < 28:
        return f"{JSON_ARTIFACT} Golden Theme score is below 28/30."
    if not decision.success_definition.get("audience_success"):
        return f"{JSON_ARTIFACT} is missing the successful-carousel success definition."
    if not decision.human_story_setup.get("emotional_obstacle"):
        return f"{JSON_ARTIFACT} is missing the Layer E human story setup."
    stage_gate = decision.stage_scene_gate or {}
    if stage_gate.get("status") != "GO":
        blockers = stage_gate.get("blockers") or ["Stage-Scene Gate did not return GO"]
        return f"{JSON_ARTIFACT} Stage-Scene Gate is blocked: " + "; ".join(blockers)
    return None
