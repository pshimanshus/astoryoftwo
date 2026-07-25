# ASTO-002 Deep Spec - Format Snapback

## Why This Task Exists

The project has repeatedly failed by letting repo defaults override the
creator's current instruction. Native dimensions are production gates, but the
current-request format lock decides which gates apply: post/carousel defaults
to 3:4 only, while 9:16 and square are explicit-request-only. This task
evaluates whether an agent understands precedence, not just dimensions. The
desired skill is to preserve exact native gates without creating unrequested
derivatives.

## Starting Fixture

Fixture direction: **solution**. A single-pass `evals/runner.py review` must
observe the materialized starter as `unresolved`. The task becomes resolved
only after the agent repairs the fixture-backed repository state and the named
checker passes.

The visible fixture at `fixtures/output/evals/ASTO-002/request-state.json`
models a request history: first a normal carousel request, then a correction to
one square proof. The seeded state still emits `instagram_post` and
`reels_stories` jobs marked as not requested by the latest creator message. The
fail-to-pass check asserts that corrected single-format requests do not produce
unrequested native post/story outputs. The pass-to-pass check preserves the
post-only `1080x1440` default and exact `1080x1920` or `1080x1080` gates when
those formats are explicitly requested.

## Failure Modes

- Agent makes square the global default.
- Agent removes native final requirements for a requested format.
- Agent restores automatic post plus Story/Reel output for ordinary carousels.
- Agent silently generates extra Story/Reel outputs after the correction.
- Agent accepts ambiguous format language instead of asking for exact canvas.
- Agent changes docs only while generation code still snaps back.

## Checker Design

The deterministic checker uses the small synthetic request object and inspects
planned output jobs, not generated media. The fail-to-pass case flips when the
planner respects the latest correction. The pass-to-pass case keeps existing
`tests/test_creator_workflow_contract.py`,
`tests/test_carousel_prompt_compiler.py`, and image-size tests green. A hidden variant
should use a different correction order, such as "actually make this a
Story only," to prove the logic is precedence-based rather than square-specific.

## Anti-Gaming

Forbid edits that weaken dimension rules, restore automatic multi-format
finals, or special-case the exact visible fixture text.
Require evidence that the current creator instruction, attached references, and
immediate corrections are read before output formats are locked.

## Severity Model

Critical: wrong format generated, default finals removed, or ambiguous canvas
accepted. Major: docs repaired but code path not covered. Minor: unclear error
message when asking for the exact canvas.
