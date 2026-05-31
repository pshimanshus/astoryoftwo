"""Prompt-constraints check — does this compiled prompt include the
canonical hard-fail fragments from `config/rules/`?

Cheap regex check that catches the most common drift: a session
compiled a prompt that lost the "no yellow" rule, lost the ON-IMAGE
TEXT block, or lost the brandmark requirement. Run after
`prompt_compile` and before `proof_generation`.
"""

from __future__ import annotations

from pathlib import Path

from pipeline.agentic.contracts import WorkflowGate


REQUIRED_FRAGMENTS: tuple[str, ...] = (
    "warm ivory",
    "HARD FAIL: yellow",
    "ON-IMAGE TEXT",
    "@a.storyof.two",
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
    missing = [fragment for fragment in REQUIRED_FRAGMENTS if fragment not in text]
    if missing:
        return WorkflowGate(
            name="prompt_constraints",
            status="FAIL",
            reason=f"missing required fragments: {missing}",
            evidence_paths=[str(prompt_path)],
        )
    return WorkflowGate(
        name="prompt_constraints",
        status="PASS",
        reason="all required fragments present",
        evidence_paths=[str(prompt_path)],
    )
