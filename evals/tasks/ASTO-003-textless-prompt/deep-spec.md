# ASTO-003 Deep Spec - Textless Prompt

## Why This Task Exists

Textless source-art prompts are one of the most dangerous carousel shortcuts in
this repo. They can look tasteful while violating the core production contract:
approved ON-IMAGE TEXT must be baked into the final raster from the start, with
only narrow repair allowed on an already text-bearing image. This task checks
whether an agent blocks the workaround rather than making the wording prettier.

## Starting Fixture

Fixture direction: **regression**. The protected current implementation is
expected to reject the seeded failure, so a single-pass `evals/runner.py review`
records this fixture as `guarded`. That guard result alone cannot award agent
solve credit: an isolated benchmark run must first apply a hidden code mutation
or pre-fix revision that makes the guard fail, then evaluate the agent patch.

The fixture should include a `prompt-pack.json` with approved slide text and an
active prompt under `codex-image-prompts/` that asks for clean blank space,
source art, or text placement afterward. A realistic fixture should avoid only
one phrase; include variants like "reserved paper space," "add typography
later," and "no readable text in this source." The fail-to-pass checker should
see `active_textless_prompt` from carousel doctor or a prompt-constraints fail.
The pass-to-pass checker should confirm text-bearing prompts with safe negative
warnings still pass.

## Failure Modes

- Agent permits textless source images as long as final audit promises text.
- Agent removes forbidden directive checks because they are too broad.
- Agent adds exact text to metadata but not the actual prompt body.
- Agent blocks every prompt that contains safe negative text guidance.
- Agent changes generated output instead of repairing active prompt logic.

## Checker Design

The deterministic checker should call `check_prompt_constraints` with expected
slide text and `inspect_carousel_package` on the fixture package. The
fail-to-pass behavior is that source-art directives become blockers. The
pass-to-pass behavior is that a correct prompt containing "Do not add extra
words" and exact ON-IMAGE TEXT remains valid. A hidden variant should alter the
phrase order and file name so the checker proves semantic coverage, not a
single hard-coded visible string.

## Anti-Gaming

Forbid changing `config/rules/on-image-text.md` to allow source-art workflows.
Forbid deleting prompts or marking packages publishable without prompt repair.
The checker should require either a repaired text-bearing active prompt or an
explicit blocked terminal state with reason and evidence.

## Severity Model

Critical: active textless prompt remains, exact text requirement weakened, or a
package is marked publishable. Major: block exists but lacks actionable reason.
Minor: duplicate warning text or overly broad message wording.
