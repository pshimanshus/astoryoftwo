"""Required context stays complete; optional excerpts cannot exhaust its budget."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from pipeline.agentic.context_loader import (
    RequiredSectionTruncatedError,
    assemble_context_pack,
)
from pipeline.agentic.rule_includes import clear_rule_cache


@pytest.fixture(autouse=True)
def _reset_cache():
    clear_rule_cache()
    yield
    clear_rule_cache()


def _scaffold(tmp_path: Path, *, budget: int, sections: list[dict]) -> None:
    (tmp_path / "config" / "rules").mkdir(parents=True)
    (tmp_path / "config" / "rules" / "palette.md").write_text(
        "PALETTE: warm ivory only.\n"
        "HARD FAIL: yellow, mustard, sepia, parchment, tan, beige.\n"
        + ("PADDING WORD " * 200),  # pad so expansion is large
        encoding="utf-8",
    )
    manifest = {
        "default_profile": "test",
        "profiles": {
            "test": {
                "budget_tokens": budget,
                "sections": sections,
            }
        },
    }
    (tmp_path / "config" / "agentic_context_manifest.json").write_text(
        json.dumps(manifest), encoding="utf-8"
    )


def test_required_rule_section_raises_when_truncated(tmp_path: Path) -> None:
    """If a required section uses {{rule:NAME}} and the expanded content
    exceeds the budget, the loader must raise rather than silently
    chopping the rule mid-string."""
    section_path = tmp_path / "skill.md"
    section_path.write_text("Skill body. {{rule:palette}}", encoding="utf-8")

    _scaffold(
        tmp_path,
        budget=20,  # absurdly small; ensures truncation
        sections=[
            {"id": "skill", "path": "skill.md", "kind": "skill", "required": True}
        ],
    )

    with pytest.raises(RequiredSectionTruncatedError) as exc_info:
        assemble_context_pack(tmp_path)

    msg = str(exc_info.value)
    assert "skill" in msg
    assert "palette" in msg


def test_optional_rule_section_truncates_silently(tmp_path: Path) -> None:
    """Optional sections may truncate — they are not load-bearing."""
    section_path = tmp_path / "skill.md"
    section_path.write_text("Skill body. {{rule:palette}}", encoding="utf-8")

    _scaffold(
        tmp_path,
        budget=20,
        sections=[
            {"id": "skill", "path": "skill.md", "kind": "skill", "required": False}
        ],
    )

    pack = assemble_context_pack(tmp_path)
    assert len(pack.sections) == 1
    assert pack.sections[0].truncated is True


def test_required_plain_section_cannot_be_truncated(tmp_path: Path) -> None:
    (tmp_path / "section.md").write_text("Plain section. " * 500)
    _scaffold(tmp_path, budget=20, sections=[
        {"id": "plain", "path": "section.md", "kind": "skill", "required": True}
    ])
    with pytest.raises(RequiredSectionTruncatedError, match="plain"):
        assemble_context_pack(tmp_path)


def test_optional_content_cannot_starve_later_required_section(tmp_path: Path) -> None:
    (tmp_path / "optional.md").write_text("optional " * 100)
    (tmp_path / "required.md").write_text("CRITICAL RULE")
    _scaffold(tmp_path, budget=20, sections=[
        {"id": "optional", "path": "optional.md", "kind": "reference", "required": False},
        {"id": "required", "path": "required.md", "kind": "rule", "required": True},
    ])
    pack = assemble_context_pack(tmp_path)
    assert pack.sections[1].content == "CRITICAL RULE"
    assert not pack.sections[1].truncated
    assert pack.estimated_tokens <= 20


def test_optional_section_max_tokens_prevents_greedy_context(tmp_path: Path) -> None:
    (tmp_path / "first.md").write_text("first optional " * 100)
    (tmp_path / "second.md").write_text("SECOND OPTIONAL")
    _scaffold(tmp_path, budget=40, sections=[
        {
            "id": "first",
            "path": "first.md",
            "kind": "reference",
            "required": False,
            "max_tokens": 5,
        },
        {
            "id": "second",
            "path": "second.md",
            "kind": "reference",
            "required": False,
        },
    ])
    pack = assemble_context_pack(tmp_path)
    loaded = {section.id: section for section in pack.sections}
    assert loaded["first"].estimated_tokens <= 5
    assert loaded["first"].truncated is True
    assert loaded["second"].content == "SECOND OPTIONAL"


def test_missing_required_file_after_full_budget_is_reported(tmp_path: Path) -> None:
    (tmp_path / "first.md").write_text("x" * 80)
    _scaffold(tmp_path, budget=20, sections=[
        {"id": "first", "path": "first.md", "kind": "rule", "required": True},
        {"id": "missing", "path": "missing.md", "kind": "rule", "required": True},
    ])
    with pytest.raises(FileNotFoundError, match="missing.md"):
        assemble_context_pack(tmp_path)


@pytest.mark.parametrize("budget", [0, 1, 7, 8, 20])
def test_optional_truncation_marker_fits_budget(budget: int) -> None:
    from pipeline.agentic.context_loader import estimate_tokens, trim_to_budget
    content, truncated = trim_to_budget("large text " * 100, budget)
    assert truncated
    assert estimate_tokens(content) <= budget


def test_repository_task_profiles_preserve_all_required_content() -> None:
    from pipeline.agentic.context_loader import load_manifest
    root = Path(__file__).resolve().parents[1]
    manifest = load_manifest(root)
    assert manifest["default_profile"] == "ideation"
    for name, profile in manifest["profiles"].items():
        pack = assemble_context_pack(root, name)
        loaded = {section.id: section for section in pack.sections}
        for item in profile["sections"]:
            if item.get("required", True):
                assert item["id"] in loaded
                assert not loaded[item["id"]].truncated
                assert loaded[item["id"]].content
        assert pack.estimated_tokens <= pack.budget_tokens
    idea = assemble_context_pack(root)
    assert not any(section.kind == "identity_reference" for section in idea.sections)
