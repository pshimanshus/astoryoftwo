# ASTO-002 Deep Spec - Format Snapback

## Why This Task Exists

The project has repeatedly failed by letting repo defaults override the
creator's current instruction. Native 3:4 and 9:16 finals are production gates
when a full carousel is requested, but they become wrong when the creator
corrects the canvas to a square proof or a single format. This task evaluates
whether an agent understands precedence, not just dimensions. The desired skill
is to preserve strong defaults while honoring the latest explicit correction.

## Starting Fixture

The fixture should model a request history: first a normal carousel request,
then a correction like "no, only one square proof for slide 3." A workflow
function, prompt compiler, or package writer still emits `instagram_post` and
`reels_stories` jobs. The fail-to-pass check should assert that corrected
single-format requests do not produce unrequested native post/story outputs.
The pass-to-pass check should assert that ordinary carousel requests still
require separate native `1080x1440` and `1080x1920` outputs and exact dimension
gates.

## Failure Modes

- Agent makes square the global default.
- Agent removes native final requirements for real carousel work.
- Agent silently generates extra Story/Reel outputs after the correction.
- Agent accepts ambiguous format language instead of asking for exact canvas.
- Agent changes docs only while generation code still snaps back.

## Checker Design

The deterministic checker should use a small synthetic request object or CLI
fixture and inspect planned output jobs, not generated media. The fail-to-pass
case flips when the planner respects the latest correction. The pass-to-pass
case keeps existing `tests/test_creator_workflow_contract.py`,
`tests/test_carousel_prompt_compiler.py`, and image-size tests green. A hidden variant
should use a different correction order, such as "actually make this a
Story only," to prove the logic is precedence-based rather than square-specific.

## Anti-Gaming

Forbid edits that weaken dimension rules, remove multi-format finals from
normal carousel packages, or special-case the exact visible fixture text.
Require evidence that the current creator instruction, attached references, and
immediate corrections are read before output formats are locked.

## Severity Model

Critical: wrong format generated, default finals removed, or ambiguous canvas
accepted. Major: docs repaired but code path not covered. Minor: unclear error
message when asking for the exact canvas.
