# Eval Research Memory

last_updated: 2026-07-04
confidence: 0.78
sources:
- docs/evals/a-story-swebench-style-evals.md
- evals/README.md
- AGENTS.md

## Durable Learning

This repo should evaluate agent behavior with local SWE-bench-style tasks:
issue-like prompts, fixed starting-state descriptions, allowed and forbidden
changes, deterministic checkers, and explicit pass criteria.

Mechanical contract gates must remain separate from creative-quality judging.
Creative rubrics can review recognition, scene proof, voice, sendability, and
format fit, but they must not override hard failures such as edited `AGENTS.md`,
secret leaks, missing identity references, wrong native dimensions, textless
source-art prompts, missing visual QA, or fake final audit claims.

The eval suite should evolve from real failures: creator corrections, failed
carousel packages, wiki-health diagnostics, review comments, closeout blocks,
and instruction drift. Each recurring failure should become a minimized fixture
and then a deterministic checker before it becomes a subjective rubric.

Every stable task should include a deep evaluator spec with fail-to-pass,
pass-to-pass, hidden variant, anti-gaming, and severity notes. A task prompt
alone is not enough; shallow task labels encourage benchmark gaming and do not
teach future checkers what behavior matters.

## Current Starter Suites

- `smoke`: fastest dangerous failures.
- `contract`: instruction, rule, memory, Agentic OS, and closeout behavior.
- `carousel`: package and image-production gates.
- `creative`: creator-facing behavior with rubric hooks.
- `full`: all starter tasks.
