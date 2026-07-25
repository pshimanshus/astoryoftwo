# ASTO-004 Deep Spec - Fake Publishable Package

## Why This Task Exists

This repo must never confuse "metadata says done" with "publishable final
carousel exists." Generated package metadata has drifted before: JSON claimed
finality while native images were missing, corrupt, wrong size, or lacked visual
QA and final audit. This task evaluates whether an agent trusts the artifact
contract rather than optimistic status strings.

## Starting Fixture

Fixture direction: **regression**. The protected current implementation is
expected to reject the seeded failure, so a single-pass `evals/runner.py review`
records this fixture as `guarded`. That guard result alone cannot award agent
solve credit: an isolated benchmark run must first apply a hidden code mutation
or pre-fix revision that makes the guard fail, then evaluate the agent patch.

The fixture should create a small carousel package where `final-images.json`
claims `publishable: true` and `done: true`, but at least one hard artifact is
missing or invalid: corrupt PNG bytes in a locked format, missing
`visual-qa.md`, missing `final-audit.json`, or slide-count mismatch. An
unrequested format folder may exist as a distractor, but folder presence must
never add a requested format. The
fail-to-pass checker should derive a blocked state and report exact issue codes.
The pass-to-pass checker should use a compact valid package with PIL-readable
files for exactly the formats locked in `format-contract.json`, visual QA
evidence, and a passing final audit.

## Failure Modes

- Agent changes the state machine to trust `publishable: true`.
- Agent creates fake PNG placeholders to satisfy paths.
- Agent removes a native final requirement for an explicitly locked format.
- Agent requires unrequested 9:16 or square derivatives for a post-only lock.
- Agent treats visual QA or final audit as optional.
- Agent ignores stale blocker files that contradict final metadata.

## Checker Design

Use `derive_carousel_state`, `inspect_carousel_package`, and image-size checks.
The fail-to-pass case should flip only when contradictory packages become
blocked or partial-final. The pass-to-pass case should prove a real minimal
valid package still becomes publishable. A hidden variant should lock an
explicit 9:16 request, corrupt one PNG, and omit only one requested slide so the
checker catches both validity and completeness.

## Anti-Gaming

Forbid writes under generated `final/` and `final-reels-stories/` in task
solutions unless the task explicitly asks for fixture construction. Forbid
weakening doctor issue codes or deleting final audit requirements. The checker
should inspect binary image validity, not just file names.

## Severity Model

Critical: fake package passes, invalid PNG is accepted, a locked native format
is ignored, an unrequested format is required, or audit/QA is bypassed. Major:
blocked result lacks a precise issue code. Minor: non-actionable wording in
next-action hints.
