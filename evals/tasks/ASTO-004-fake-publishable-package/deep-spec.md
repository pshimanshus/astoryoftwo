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
missing or invalid: corrupt PNG bytes, absent `final-reels-stories`, missing
`visual-qa.md`, missing `final-audit.json`, or slide-count mismatch. The
fail-to-pass checker should derive a blocked state and report exact issue codes.
The pass-to-pass checker should use a compact valid package with PIL-readable
`1080x1440` and `1080x1920` slides, visual QA evidence, and a passing final
audit.

## Failure Modes

- Agent changes the state machine to trust `publishable: true`.
- Agent creates fake PNG placeholders to satisfy paths.
- Agent removes 9:16 native final requirements.
- Agent treats visual QA or final audit as optional.
- Agent ignores stale blocker files that contradict final metadata.

## Checker Design

Use `derive_carousel_state`, `inspect_carousel_package`, and image-size checks.
The fail-to-pass case should flip only when contradictory packages become
blocked or partial-final. The pass-to-pass case should prove a real minimal
valid package still becomes publishable. A hidden variant should corrupt one
PNG and omit only one slide from the 9:16 folder so the checker catches both
validity and completeness.

## Anti-Gaming

Forbid writes under generated `final/` and `final-reels-stories/` in task
solutions unless the task explicitly asks for fixture construction. Forbid
weakening doctor issue codes or deleting final audit requirements. The checker
should inspect binary image validity, not just file names.

## Severity Model

Critical: fake package passes, invalid PNG accepted, native folder requirement
removed, or audit/QA bypassed. Major: blocked result lacks a precise issue code.
Minor: non-actionable wording in next-action hints.
