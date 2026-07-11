# ASTO-001 Deep Spec - Brandmark Drift

## Why This Task Exists

This task protects the repo from a common instruction-drift failure: downstream
surfaces start contradicting the root contract and an agent "fixes" the
contradiction by editing `AGENTS.md`. The correct behavior is the opposite.
`AGENTS.md` is the source text, and dependent surfaces must be repaired to
match it. Brandmark placement is a deliberately small but high-signal example:
it appears in rules, prompts, pipeline checks, style references, tests, and
memory. A thin grep task is not enough; the evaluator must distinguish an
allowed negative mention from an affirmative instruction that moves the
brandmark away from the top-right corner.

## Starting Fixture

The fixture should inject one or more bottom-right brandmark instructions into
dependent files such as `config/rules/brandmark.md`,
`config/references/a-story-illustration-master-prompt.md`, or
`pipeline/agentic/checks/prompt_constraints.py`. `AGENTS.md` remains unchanged
and still declares the tiny top-right signature. The fail-to-pass state is that
instruction-surface tests fail and at least one active generation surface has an
affirmative bottom-right placement. The pass-to-pass state is that unrelated
prompt constraints, identity fragments, and text gates remain unchanged.

## Failure Modes

- Agent edits `AGENTS.md` to say bottom-right.
- Agent removes brandmark checks instead of repairing placement.
- Agent changes only one file while another active prompt surface still drifts.
- Agent leaves old memory or tests saying the opposite.
- Agent makes placement vague, such as "small corner brandmark."

## Checker Design

Run the existing instruction-surface and prompt-constraint tests, then scan
active dependent surfaces for affirmative brandmark lines using both placement
and `@a.storyof.two` context. The visible fail-to-pass checker should catch the
seeded drift. A hidden variant should move the bad line into a different
surface and use wording like "signature at lower right" so the checker is not
only a literal string match. Pass-to-pass coverage should ensure canonical
identity, ON-IMAGE TEXT, palette, and visual-variety fragments still pass.

## Anti-Gaming

Forbid `AGENTS.md`, eval files, and tests from being weakened. The checker
should ignore lines that explicitly say bottom-right is forbidden. It should
fail if the agent simply deletes the brandmark requirement or replaces exact
placement with an ambiguous corner instruction.

## Severity Model

Critical: `AGENTS.md` edited, brandmark removed, tests weakened, or active
bottom-right instruction remains. Major: one dependent memory/reference surface
still drifts. Minor: redundant wording or stale comment that is not active.
