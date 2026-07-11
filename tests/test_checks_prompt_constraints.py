"""Prompt-constraints gate tests."""

from __future__ import annotations

from pathlib import Path

import pytest

from pipeline.agentic.checks.prompt_constraints import (
    REQUIRED_FRAGMENT_TABLE,
    REQUIRED_FRAGMENTS,
    check_prompt_constraints,
)
from pipeline.agentic.rule_includes import expand_rule_includes


REPO_ROOT = Path(__file__).resolve().parents[1]


def _compose_prompt_with_all_fragments() -> str:
    """Minimal prompt that includes every canonical fragment."""
    return "\n".join(
        [
            "Generate an illustration.",
            "PALETTE: warm ivory paper.",
            "HARD FAIL: yellow, sepia, parchment.",
            "Style lock: Observational Intimacy Premium.",
            "ON-IMAGE TEXT: dumber",
            "Each identity reference image must be attached to the call.",
            "Preserve Aachu and Zuv face identity.",
            "PAPER TONE LOCK: neutral off-white paper only.",
            "STAGE-SCENE / VISUAL RECEIPT: text completes the scene.",
            "SHOT LADDER / VISUAL VARIETY: vary camera, action, and who is visible.",
            "RELATIONSHIP MOTION: do not make Zuv the default caretaker.",
            "Aachu is 5'6\" and Zuv is 5'8\".",
            "Brandmark: tiny handwritten @a.storyof.two in top-right.",
            "No split-screen divider may appear in final art.",
        ]
    )


def _compose_text_bearing_prompt() -> str:
    return "\n".join(
        [
            _compose_prompt_with_all_fragments(),
            "Create ONE final @a.storyof.two carousel slide.",
            "ON-IMAGE TEXT MUST BE GENERATED INSIDE THE ILLUSTRATION FROM THE START.",
            "Hand-letter the exact slide text:",
            "Rule no. 1",
            "The blanket belongs to whoever pulls harder.",
            "Brandmark: generate exactly one tiny handwritten @a.storyof.two in the top-right corner.",
            "Do not generate a blank/textless source scene.",
            "No textless source art is allowed.",
        ]
    )


def test_passes_when_all_required_fragments_present(tmp_path: Path) -> None:
    path = tmp_path / "slide-01.prompt.txt"
    path.write_text(_compose_prompt_with_all_fragments(), encoding="utf-8")
    gate = check_prompt_constraints(path)
    assert gate.status == "PASS", gate.reason


@pytest.mark.parametrize("fragment", [f for f, _ in REQUIRED_FRAGMENT_TABLE])
def test_fails_when_any_single_fragment_missing(tmp_path: Path, fragment: str) -> None:
    """Drop each fragment one at a time and confirm the gate catches it."""
    prompt = _compose_prompt_with_all_fragments().replace(fragment, "PLACEHOLDER")
    path = tmp_path / "slide.prompt.txt"
    path.write_text(prompt, encoding="utf-8")
    gate = check_prompt_constraints(path)
    assert gate.status == "FAIL"
    assert fragment in gate.reason


def test_fails_when_prompt_file_missing(tmp_path: Path) -> None:
    gate = check_prompt_constraints(tmp_path / "missing.prompt.txt")
    assert gate.status == "FAIL"
    assert "missing" in gate.reason.lower()


def test_failure_reason_names_why_each_fragment_matters(tmp_path: Path) -> None:
    """The FAIL reason should carry both the fragment and why it matters."""
    prompt = _compose_prompt_with_all_fragments().replace("warm ivory", "REPLACED")
    path = tmp_path / "slide.prompt.txt"
    path.write_text(prompt, encoding="utf-8")
    gate = check_prompt_constraints(path)
    assert "warm ivory" in gate.reason
    assert "palette" in gate.reason.lower()


def test_fails_when_prompt_contains_textless_source_art_directive(tmp_path: Path) -> None:
    prompt = "\n".join(
        [
            _compose_prompt_with_all_fragments(),
            "Asset type: square proof illustration for @a.storyof.two.",
            "This is source art for a proof; leave clean upper-middle paper space for exact text placement afterward.",
            "Text rule for source art:",
            "Do not include any text, lettering, brandmark, labels, signs, readable packaging words, random letters, watermarks, speech bubbles, or UI in this source image.",
            "Leave clean blank upper-middle space for the exact final text to be added immediately afterward.",
        ]
    )
    path = tmp_path / "square-proof-slide-04.prompt.txt"
    path.write_text(prompt, encoding="utf-8")

    gate = check_prompt_constraints(path)

    assert gate.status == "FAIL"
    assert "forbidden textless/source-art directive" in gate.reason
    assert "Do not include any text" in gate.reason


def test_passes_text_bearing_prompt_with_safe_negative_warnings(tmp_path: Path) -> None:
    path = tmp_path / "slide-02-text-bearing.prompt.txt"
    path.write_text(_compose_text_bearing_prompt(), encoding="utf-8")

    gate = check_prompt_constraints(
        path,
        expected_text="Rule no. 1\nThe blanket belongs to whoever pulls harder.",
    )

    assert gate.status == "PASS", gate.reason


def test_fails_when_expected_slide_text_is_missing(tmp_path: Path) -> None:
    path = tmp_path / "slide-02-text-bearing.prompt.txt"
    path.write_text(_compose_prompt_with_all_fragments(), encoding="utf-8")

    gate = check_prompt_constraints(
        path,
        expected_text="Rule no. 1\nThe blanket belongs to whoever pulls harder.",
    )

    assert gate.status == "FAIL"
    assert "expected slide text" in gate.reason


def test_required_fragments_match_expected_canonical_set() -> None:
    """Tripwire: any future change to the canonical set is intentional."""
    assert set(REQUIRED_FRAGMENTS) == {
        "warm ivory",
        "HARD FAIL: yellow",
        "Observational Intimacy Premium",
        "ON-IMAGE TEXT",
        "@a.storyof.two",
        "identity reference",
        "top-right",
        "Aachu",
        "Zuv",
        "PAPER TONE LOCK",
        "STAGE-SCENE / VISUAL RECEIPT",
        "SHOT LADDER / VISUAL VARIETY",
        "RELATIONSHIP MOTION",
        "Aachu is 5'6\"",
        "Zuv is 5'8\"",
        "No split-screen divider",
    }


def test_required_fragments_are_present_in_rule_files() -> None:
    """Every required fragment must live in at least one config/rules/*.md file.

    This is the upstream guarantee — if a future edit drops a fragment
    from the rule files, this fails before any production prompt fails.
    """
    rules_dir = REPO_ROOT / "config" / "rules"
    rule_corpus = "\n".join(
        path.read_text(encoding="utf-8") for path in rules_dir.glob("*.md")
    )

    missing = [fragment for fragment in REQUIRED_FRAGMENTS if fragment not in rule_corpus]
    assert not missing, (
        "Required prompt-constraints fragments are not present in any "
        f"config/rules/ file: {missing}. Either restore the fragment in "
        "the relevant rule file, or remove it from REQUIRED_FRAGMENT_TABLE "
        "in pipeline/agentic/checks/prompt_constraints.py with rationale."
    )


def test_passes_when_compiled_from_real_repo_rules(tmp_path: Path) -> None:
    """End-to-end: compose a prompt by expanding {{rule:NAME}} against the
    real repo rules dir, then verify it passes the constraints gate."""
    template = (
        "PROMPT START\n"
        "{{rule:palette}}\n"
        "{{rule:identity}}\n"
        "{{rule:on-image-text}}\n"
        "{{rule:brandmark}}\n"
        "{{rule:visual-variety}}\n"
        "{{rule:relationship-motion}}\n"
        "PROMPT END\n"
    )
    expanded = expand_rule_includes(template, REPO_ROOT)
    path = tmp_path / "compiled.prompt.txt"
    path.write_text(expanded, encoding="utf-8")
    gate = check_prompt_constraints(path)
    assert gate.status == "PASS", gate.reason
