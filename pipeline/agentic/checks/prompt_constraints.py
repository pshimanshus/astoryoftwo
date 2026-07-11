"""Prompt-constraints check — does this compiled prompt include the
canonical hard-fail fragments from `config/rules/`?

Cheap regex check that catches the most common drift: a session
compiled a prompt that lost the "no yellow" rule, lost the ON-IMAGE
TEXT block, lost the brandmark requirement, or dropped identity /
height constraints. Run after `prompt_compile` and before
`proof_generation`.

Coverage philosophy: include the fragments that are load-bearing for
the most common rejection modes in this project. Each fragment must
also be present in at least one `config/rules/*.md` file (verified by
test_required_fragments_are_present_in_rule_files in
tests/test_checks_prompt_constraints.py), so if a rule file is edited
to drop a fragment, that test fails before production does.
"""

from __future__ import annotations

import re
from pathlib import Path

from pipeline.agentic.contracts import WorkflowGate


# Each entry: (fragment, why-it-matters). The why-it-matters string is
# surfaced in the FAIL reason so a session sees exactly what was lost.
REQUIRED_FRAGMENT_TABLE: tuple[tuple[str, str], ...] = (
    ("warm ivory", "paper-tone rule (palette)"),
    ("HARD FAIL: yellow", "yellow-drift hard-fail (palette)"),
    ("Observational Intimacy Premium", "creator-approved house style lock"),
    ("ON-IMAGE TEXT", "on-image-text contract"),
    ("@a.storyof.two", "brandmark requirement"),
    ("identity reference", "identity-image attachment rule"),
    ("top-right", "brandmark placement"),
    ("Aachu", "identity preservation — woman"),
    ("Zuv", "identity preservation — man"),
    ("PAPER TONE LOCK", "paper tone isolation lock"),
    ("STAGE-SCENE / VISUAL RECEIPT", "story-readable visual proof"),
    ("SHOT LADDER / VISUAL VARIETY", "carousel visual variety"),
    ("RELATIONSHIP MOTION", "relationship-motion gate"),
    ("Aachu is 5'6\"", "Aachu height lock"),
    ("Zuv is 5'8\"", "Zuv height lock"),
    ("No split-screen divider", "reference screenshot layout-device ban"),
)

REQUIRED_FRAGMENTS: tuple[str, ...] = tuple(
    fragment for fragment, _ in REQUIRED_FRAGMENT_TABLE
)

FORBIDDEN_DIRECTIVE_TABLE: tuple[tuple[re.Pattern[str], str], ...] = (
    (
        re.compile(r"\bdo not include any text\b", re.IGNORECASE),
        "Do not include any text",
    ),
    (
        re.compile(
            r"\bno text\s*,\s*no letters?\s*,\s*no brandmark\b",
            re.IGNORECASE,
        ),
        "no text, no letters, no brandmark",
    ),
    (
        re.compile(r"\bleave\b[^\n.]{0,120}\bblank\b", re.IGNORECASE),
        "leave blank",
    ),
    (
        re.compile(r"\badd(?:ed)?\b[^\n.]{0,120}\btext\b[^\n.]{0,120}\b(?:later|afterward)\b", re.IGNORECASE),
        "add text later",
    ),
    (
        re.compile(r"\btext\b[^\n.]{0,120}\badded\b[^\n.]{0,120}\b(?:later|afterward)\b", re.IGNORECASE),
        "text to be added later",
    ),
    (
        re.compile(r"\bexact text placement (?:afterward|later)\b", re.IGNORECASE),
        "exact text placement afterward",
    ),
    (
        re.compile(r"\bsource art for a proof\b", re.IGNORECASE),
        "source art for a proof",
    ),
    (
        re.compile(r"\btext rule for source art\b", re.IGNORECASE),
        "Text rule for source art",
    ),
)


def _squash_whitespace(text: str) -> str:
    return re.sub(r"\s+", " ", text.strip())


def _forbidden_directives(text: str) -> list[str]:
    return [
        label
        for pattern, label in FORBIDDEN_DIRECTIVE_TABLE
        if pattern.search(text)
    ]


def check_prompt_constraints(prompt_path: Path, *, expected_text: str | None = None) -> WorkflowGate:
    prompt_path = Path(prompt_path)
    if not prompt_path.exists():
        return WorkflowGate(
            name="prompt_constraints",
            status="FAIL",
            reason=f"prompt missing: {prompt_path}",
        )

    text = prompt_path.read_text(encoding="utf-8")
    forbidden = _forbidden_directives(text)
    if forbidden:
        detail = "; ".join(forbidden)
        return WorkflowGate(
            name="prompt_constraints",
            status="FAIL",
            reason=f"forbidden textless/source-art directive: {detail}",
            evidence_paths=[str(prompt_path)],
        )

    missing: list[tuple[str, str]] = [
        (fragment, why) for fragment, why in REQUIRED_FRAGMENT_TABLE if fragment not in text
    ]

    if missing:
        detail = "; ".join(f"'{fragment}' ({why})" for fragment, why in missing)
        return WorkflowGate(
            name="prompt_constraints",
            status="FAIL",
            reason=f"missing required fragments: {detail}",
            evidence_paths=[str(prompt_path)],
        )

    if expected_text and _squash_whitespace(expected_text) not in _squash_whitespace(text):
        return WorkflowGate(
            name="prompt_constraints",
            status="FAIL",
            reason="missing expected slide text",
            evidence_paths=[str(prompt_path)],
        )

    return WorkflowGate(
        name="prompt_constraints",
        status="PASS",
        reason=f"all {len(REQUIRED_FRAGMENTS)} required fragments present",
        evidence_paths=[str(prompt_path)],
    )
