# Eval Research Memory

last_updated: 2026-07-21
confidence: 0.91
sources:
- docs/evals/a-story-swebench-style-evals.md
- evals/README.md
- evals/research/failure-taxonomy.md
- evals/research/sources.json
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

Smoke and high-risk tasks should also include fixture overlays. The first
fixture layer materializes broken files with `evals/runner.py prepare`, so a
checker can prove the starting state actually triggers package, prompt,
autopublish, or instruction-surface gates before any agent attempts a fix.

Fixture direction must be explicit. A solution fixture starts unresolved and
is repaired by the agent. A regression fixture starts guarded because the
current production validator catches the seeded failure. The latter is useful
as a contract regression, but it cannot award agent solve credit until an
isolated hidden code mutation or pre-fix revision makes the guard fail. This
distinction prevents no-op agents from inflating results.

Creative rubric prechecks are not creative-quality judgments. A rubric-bearing
task stays pending until a named reviewer supplies per-dimension scores and
concrete artifact evidence. Hard mechanical failures remain blocking regardless
of rubric score.

Use `venv/bin/python evals/runner.py review` for a bounded alignment pass. It
freezes registry order, inspects each selected fixture once, reports direction
mismatches, and stops; it does not retry or recursively review its own report.

Before adding or expanding eval tasks, inspect the repo's actual failure trail:
semantic memory, episodic/session health, Agentic OS learning events,
concept-rejection notes, package blockers, final audits, visual QA, wiki-health
diagnostics, and closeout safety tests. Each task should name the repetitive
mistake it covers and cite concrete evidence in
the Evidence Ledger in `evals/research/failure-taxonomy.md`; otherwise it is
likely to become generic one-line eval slop instead of a useful future-agent
contract.

## Current Starter Suites

- `smoke`: fastest dangerous failures.
- `contract`: instruction, rule, memory, Agentic OS, and closeout behavior.
- `carousel`: package and image-production gates.
- `creative`: creator-facing behavior with rubric hooks.
- `full`: all starter tasks.
