"""Configuration-level integration checks for the non-AI-image skill."""

from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_non_ai_image_skill_registry_routes_to_one_entrypoint_and_canonical_rules() -> None:
    systems = json.loads((ROOT / "config" / "skill-systems.json").read_text(encoding="utf-8"))
    workflow = systems["systems"]["non_ai_image_skill"]

    assert workflow["components"] == [".agents/skills/non-ai-image-skill/SKILL.md"]
    assert {
        "config/rules/scene-entity-integrity.md",
        "config/rules/identity.md",
        "config/carousel_style_contract.json",
    }.issubset(workflow["source_references"])
    assert workflow["gates"] == [
        "locked_scene_and_applicable_risk_contracts",
        "current_pixel_evidence_bound",
        "focused_visual_reviews_complete",
        "existing_carousel_proof_creator_final_gates",
    ]


def test_main_direct_visual_skill_applies_non_ai_image_guard_to_locked_production() -> None:
    direct_visual = (
        ROOT / ".agents" / "skills" / "a-story-direct-visual-story" / "SKILL.md"
    ).read_text(encoding="utf-8")

    assert "$non-ai-image-skill" in direct_visual
    assert "Store the resulting `scene_contract` with every slide before" in direct_visual
    assert "blind scene read" in direct_visual
    assert "scene-contract hash" in direct_visual


def test_visual_contracts_keep_phone_pixel_evidence_and_kneeling_scope_explicit() -> None:
    scene_integrity = (ROOT / "config" / "rules" / "scene-entity-integrity.md").read_text(
        encoding="utf-8"
    ).lower()
    identity = (ROOT / "config" / "rules" / "identity.md").read_text(encoding="utf-8").lower()
    style_contract = json.loads((ROOT / "config" / "carousel_style_contract.json").read_text(encoding="utf-8"))

    assert "display belongs" in scene_integrity
    assert "on the front surface" in scene_integrity
    assert "rear camera lenses on one visible face" in scene_integrity
    assert "current decoded pixels" in scene_integrity
    assert "uncertain and block promotion" in scene_integrity
    assert "motivated kneeling pose is permitted only" in identity
    assert "does not permit a deep crouch" in identity
    assert "phone display content on a rear camera face" in style_contract["shared_negative_prompt"]
    assert "current decoded pixels" in style_contract["visual_story_policy"]["pixel_evidence_rule"]
