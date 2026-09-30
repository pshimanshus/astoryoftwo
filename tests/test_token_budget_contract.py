from __future__ import annotations

import json
from pathlib import Path

from pipeline.agentic.context_loader import assemble_context_pack, estimate_tokens
from pipeline.stages.b1_prepost import build_stage_system_prompts


ROOT = Path(__file__).resolve().parents[1]


def _contract() -> dict:
    return json.loads((ROOT / "config/token_budget_contract.json").read_text(encoding="utf-8"))


def test_instruction_surfaces_stay_within_versioned_token_budgets() -> None:
    contract = _contract()

    assert contract["schema_version"] == "1.0"
    assert contract["estimator"] == "characters/4"
    for relative, maximum in contract["surfaces"].items():
        text = (ROOT / relative).read_text(encoding="utf-8")
        assert estimate_tokens(text) <= maximum, relative


def test_rendered_context_profiles_stay_within_task_specific_budgets() -> None:
    contract = _contract()

    for profile, maximum in contract["context_profiles"].items():
        pack = assemble_context_pack(ROOT, profile=profile)
        assert pack.budget_tokens == maximum, profile
        assert pack.estimated_tokens <= maximum, profile
        assert all(not section.truncated for section in pack.sections if section.required)


def test_fixed_prepost_prompts_stay_below_aggregate_budget() -> None:
    prompts = build_stage_system_prompts()
    maximum = _contract()["prompt_builders"]["prepost_fixed_total"]

    assert set(prompts) == {"combined_analysis", "independent_challenge", "synthesis"}
    assert sum(estimate_tokens(prompt) for prompt in prompts.values()) <= maximum
    combined = prompts["combined_analysis"]
    assert "Story Selling Canon Source Policy" not in combined
    assert "Concept Process Cards" not in combined


def test_rgignore_blocks_generated_search_surfaces() -> None:
    patterns = (ROOT / ".rgignore").read_text(encoding="utf-8").splitlines()

    assert "output/**" in patterns
    assert "video/**" in patterns
    assert ".worktrees/**" in patterns
    assert "app/node_modules/**" in patterns
