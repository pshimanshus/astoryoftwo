"""Tests for the canonical rule include expander."""

from __future__ import annotations

from pathlib import Path

import pytest

from pipeline.agentic.rule_includes import (
    clear_rule_cache,
    expand_rule_includes,
    rule_names_referenced,
)


@pytest.fixture(autouse=True)
def _reset_cache():
    clear_rule_cache()
    yield
    clear_rule_cache()


def _make_rules_dir(tmp_path: Path) -> Path:
    rules_dir = tmp_path / "config" / "rules"
    rules_dir.mkdir(parents=True)
    return rules_dir


def test_expander_replaces_known_rule(tmp_path: Path) -> None:
    rules_dir = _make_rules_dir(tmp_path)
    (rules_dir / "palette.md").write_text(
        "PALETTE: warm ivory only.\nHARD FAIL: yellow, sepia, parchment.\n",
        encoding="utf-8",
    )

    text = "Before. {{rule:palette}} After."
    out = expand_rule_includes(text, tmp_path)

    assert "warm ivory only" in out
    assert "HARD FAIL: yellow" in out
    assert "{{rule:" not in out
    assert out.startswith("Before. ")
    assert out.endswith(" After.")


def test_expander_replaces_multiple_distinct_rules(tmp_path: Path) -> None:
    rules_dir = _make_rules_dir(tmp_path)
    (rules_dir / "palette.md").write_text("PALETTE_BODY", encoding="utf-8")
    (rules_dir / "identity.md").write_text("IDENTITY_BODY", encoding="utf-8")

    text = "A {{rule:palette}} B {{rule:identity}} C {{rule:palette}} D"
    out = expand_rule_includes(text, tmp_path)

    assert out == "A PALETTE_BODY B IDENTITY_BODY C PALETTE_BODY D"


def test_expander_raises_on_unknown_rule(tmp_path: Path) -> None:
    _make_rules_dir(tmp_path)
    text = "{{rule:does_not_exist}}"

    with pytest.raises(FileNotFoundError) as exc_info:
        expand_rule_includes(text, tmp_path)

    assert "does_not_exist" in str(exc_info.value)


def test_expander_rejects_path_traversal_rule_name(tmp_path: Path) -> None:
    _make_rules_dir(tmp_path)
    secret = tmp_path / "config" / "secret.md"
    secret.write_text("DO_NOT_INCLUDE", encoding="utf-8")

    with pytest.raises(ValueError) as exc_info:
        expand_rule_includes("{{rule:../secret}}", tmp_path)

    assert "Invalid rule include" in str(exc_info.value)


def test_rule_names_referenced_rejects_path_traversal_marker() -> None:
    with pytest.raises(ValueError) as exc_info:
        rule_names_referenced("{{rule:../../secret}}")

    assert "Invalid rule include" in str(exc_info.value)


def test_expander_strips_trailing_whitespace_from_rule_files(tmp_path: Path) -> None:
    rules_dir = _make_rules_dir(tmp_path)
    (rules_dir / "voice.md").write_text("VOICE_BODY\n\n\n", encoding="utf-8")

    text = "[{{rule:voice}}]"
    out = expand_rule_includes(text, tmp_path)

    assert out == "[VOICE_BODY]"


def test_rule_names_referenced_returns_sorted_unique() -> None:
    text = "{{rule:palette}} and {{rule:identity}} and {{rule:palette}}"
    assert rule_names_referenced(text) == ["identity", "palette"]


def test_rule_names_referenced_returns_empty_when_no_includes() -> None:
    assert rule_names_referenced("plain text with no markers") == []


def test_expander_resolves_repository_rules(tmp_path: Path) -> None:
    """End-to-end: expand against the real config/rules/ directory in this repo."""
    repo_root = Path(__file__).resolve().parents[1]
    text = "PROMPT START\n{{rule:palette}}\n{{rule:on-image-text}}\n{{rule:brandmark}}\nPROMPT END"

    out = expand_rule_includes(text, repo_root)

    assert "warm ivory" in out
    assert "HARD FAIL: yellow" in out
    assert "ON-IMAGE TEXT" in out
    assert "@a.storyof.two" in out
    assert "{{rule:" not in out
