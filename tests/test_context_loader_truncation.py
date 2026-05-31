"""Tests for context_loader's required-section truncation guard.

The guard prevents the budget from silently mutilating a rule-include
section (which could drop "HARD FAIL: yellow" mid-string and produce a
broken prompt).
"""

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


def test_required_section_without_rule_includes_truncates_silently(tmp_path: Path) -> None:
    """Required sections without {{rule:NAME}} references can still
    truncate — only rule-include sections need the safety net, because
    other sections (large reference docs, transcripts) commonly exceed
    the budget and that is expected behavior."""
    section_path = tmp_path / "section.md"
    section_path.write_text("Plain section. " * 500, encoding="utf-8")

    _scaffold(
        tmp_path,
        budget=20,
        sections=[
            {"id": "plain", "path": "section.md", "kind": "skill", "required": True}
        ],
    )

    pack = assemble_context_pack(tmp_path)
    assert len(pack.sections) == 1
    assert pack.sections[0].truncated is True
