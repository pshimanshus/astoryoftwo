"""Prompt-constraints gate tests."""

from __future__ import annotations

from pathlib import Path

from pipeline.agentic.checks.prompt_constraints import (
    REQUIRED_FRAGMENTS,
    check_prompt_constraints,
)


def _compose_prompt_with_all_fragments() -> str:
    """A minimal prompt that includes every canonical fragment."""
    return "\n".join(
        [
            "Generate an illustration.",
            "PALETTE: warm ivory paper.",
            "HARD FAIL: yellow, sepia, parchment.",
            "ON-IMAGE TEXT: dumber",
            "Brandmark: @a.storyof.two bottom-right.",
        ]
    )


def test_passes_when_all_required_fragments_present(tmp_path: Path) -> None:
    path = tmp_path / "slide-01.prompt.txt"
    path.write_text(_compose_prompt_with_all_fragments(), encoding="utf-8")
    gate = check_prompt_constraints(path)
    assert gate.status == "PASS"
    assert "all required" in gate.reason.lower()


def test_fails_when_yellow_rule_missing(tmp_path: Path) -> None:
    prompt = _compose_prompt_with_all_fragments().replace(
        "HARD FAIL: yellow, sepia, parchment.", "Use pleasant tones."
    )
    path = tmp_path / "slide-01.prompt.txt"
    path.write_text(prompt, encoding="utf-8")
    gate = check_prompt_constraints(path)
    assert gate.status == "FAIL"
    assert "HARD FAIL: yellow" in gate.reason


def test_fails_when_on_image_text_block_missing(tmp_path: Path) -> None:
    prompt = _compose_prompt_with_all_fragments().replace("ON-IMAGE TEXT: dumber", "")
    path = tmp_path / "slide-01.prompt.txt"
    path.write_text(prompt, encoding="utf-8")
    gate = check_prompt_constraints(path)
    assert gate.status == "FAIL"
    assert "ON-IMAGE TEXT" in gate.reason


def test_fails_when_brandmark_missing(tmp_path: Path) -> None:
    prompt = _compose_prompt_with_all_fragments().replace("@a.storyof.two", "@some_other_handle")
    path = tmp_path / "slide-01.prompt.txt"
    path.write_text(prompt, encoding="utf-8")
    gate = check_prompt_constraints(path)
    assert gate.status == "FAIL"
    assert "@a.storyof.two" in gate.reason


def test_fails_when_warm_ivory_missing(tmp_path: Path) -> None:
    prompt = _compose_prompt_with_all_fragments().replace("warm ivory", "soft golden")
    path = tmp_path / "slide-01.prompt.txt"
    path.write_text(prompt, encoding="utf-8")
    gate = check_prompt_constraints(path)
    assert gate.status == "FAIL"
    assert "warm ivory" in gate.reason


def test_fails_when_prompt_file_missing(tmp_path: Path) -> None:
    gate = check_prompt_constraints(tmp_path / "missing.prompt.txt")
    assert gate.status == "FAIL"
    assert "missing" in gate.reason.lower()


def test_required_fragments_match_expected_canonical_set() -> None:
    """Tripwire: if someone changes the canonical set, this fails loudly."""
    assert set(REQUIRED_FRAGMENTS) == {
        "warm ivory",
        "HARD FAIL: yellow",
        "ON-IMAGE TEXT",
        "@a.storyof.two",
    }


def test_passes_when_compiled_from_real_repo_rules(tmp_path: Path) -> None:
    """End-to-end: compose a prompt by expanding {{rule:NAME}} against the real repo
    rules dir, then verify it passes the constraints gate."""
    from pipeline.agentic.rule_includes import expand_rule_includes

    repo_root = Path(__file__).resolve().parents[1]
    template = (
        "PROMPT START\n"
        "{{rule:palette}}\n"
        "{{rule:on-image-text}}\n"
        "{{rule:brandmark}}\n"
        "PROMPT END\n"
    )
    expanded = expand_rule_includes(template, repo_root)
    path = tmp_path / "compiled.prompt.txt"
    path.write_text(expanded, encoding="utf-8")
    gate = check_prompt_constraints(path)
    assert gate.status == "PASS", gate.reason
