# ASTO-009 Deep Spec - Article Story-Selling Gate

## Why This Task Exists

Substack article packages should not become generic essays detached from the
carousel/story source. The article workflow must preserve source integrity,
Layer E Story-Selling fit, love-theme logic, voice, and final publish approval.
This task evaluates whether an agent restores those gates without turning the
article pipeline into vague writing advice.

## Starting Fixture

Fixture direction: **solution**. A single-pass `evals/runner.py review` must
observe the materialized starter as `unresolved`. The task becomes resolved
only after the agent repairs the fixture-backed repository state and the named
checker passes.

The visible fixture is a generated article package whose `source-manifest.json`
and `editorial-gates.md` omit Layer E and Story-Selling contract evidence. The
fail-to-pass behavior is that generated package artifacts can lack the story
gate while still looking draft-ready. The pass-to-pass behavior is that
slugging, image discovery, source manifest shape, and final approval gates
remain stable.

## Failure Modes

- Agent adds the phrase "Story-Selling" only to docs, not generated artifacts.
- Agent removes source-integrity checks while adding a new gate.
- Agent leaves `TBD` placeholders in article output.
- Agent changes carousel image discovery or stable slugs.
- Agent cites the wrong voice path, such as stale `config/voice.md`.

## Checker Design

Use the existing article package test with an added fixture inspection. The
fail-to-pass check flips when generated artifacts include the Layer E JSON
artifact, Story-Selling contract references, and Gate 8. The pass-to-pass check
keeps slug paths, carousel image discovery, and source manifest artifacts
stable. A hidden variant should create a carousel missing optional files but
with enough source material to verify graceful handling.

## Anti-Gaming

Forbid replacing gates with generic "write well" prose. Require generated
artifact evidence, not just source-code strings. The checker should fail if a
gate exists but has no pass criteria or no relation to the source carousel.

## Severity Model

Critical: article package can publish without Story-Selling fit or source
integrity. Major: gate exists but generated manifest omits evidence paths.
Minor: wording is repetitive but the gate is enforceable.
