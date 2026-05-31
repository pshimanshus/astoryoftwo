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
    ("bottom-right", "brandmark placement"),
    ("Aachu", "identity preservation — woman"),
    ("Zuv", "identity preservation — man"),
    ("No split-screen divider", "reference screenshot layout-device ban"),
)

REQUIRED_FRAGMENTS: tuple[str, ...] = tuple(
    fragment for fragment, _ in REQUIRED_FRAGMENT_TABLE
)


def check_prompt_constraints(prompt_path: Path) -> WorkflowGate:
    prompt_path = Path(prompt_path)
    if not prompt_path.exists():
        return WorkflowGate(
            name="prompt_constraints",
            status="FAIL",
            reason=f"prompt missing: {prompt_path}",
        )

    text = prompt_path.read_text(encoding="utf-8")
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

    return WorkflowGate(
        name="prompt_constraints",
        status="PASS",
        reason=f"all {len(REQUIRED_FRAGMENTS)} required fragments present",
        evidence_paths=[str(prompt_path)],
    )
