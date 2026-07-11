# A Story of Two SWE-Bench-Style Evals

last_updated: 2026-07-04
confidence: 0.82
sources:
- AGENTS.md
- config/rules/
- config/skill-systems.json
- scripts/agentic_os.py
- scripts/autopublish.py
- pipeline/agentic/workflow_doctor.py
- evals/

## Purpose

This eval system measures whether future agents can preserve the
@a.storyof.two project contract while making realistic repo changes. It is
SWE-bench-style because each task is an issue-like prompt against a repository
state, and the result is judged by the patch plus deterministic checks.

The suite is local-first. It does not depend on a hosted eval product, and it
uses the repo's existing Python test/runtime stack.

## Eval Types In This Repo

Unit tests check a single function or gate, such as prompt constraints or image
size.

Integration tests check a workflow, such as article packaging, pre-post Reel
analysis, Agentic OS context loading, or carousel doctor.

Golden artifacts should be used sparingly for stable JSON/package shapes, not
for open-ended creative taste.

Rubric evals judge subjective creative quality with anchored criteria. They are
useful for scene proof, recognition, sendability, and voice, but they must stay
separate from mechanical contract checks.

Agent task evals combine all of this: a prompt, a starting state, allowed and
forbidden changes, required commands, deterministic gates, rubric hooks, and a
resolved/unresolved result.

## What To Evaluate

High-value failure modes:

- `AGENTS.md` edited to hide downstream drift.
- `config/rules/` losing canonical authority.
- carousel work skipping small brief, format choice, human draft, concept lock,
  copy lock, proof lock, visual QA, or final audit;
- image packages claiming final without native `1080x1440` and `1080x1920`
  outputs;
- textless source-art prompts that add narrative text later;
- missing actual identity references for final art;
- generated output churn treated as source truth;
- `memory/working.md` becoming durable memory instead of a pointer surface;
- wiki health and Agentic OS health skipped after rule, memory, context, or
  workflow changes;
- autopublish staging secrets, identity images, generated finals, logs, or
  cache files;
- creative replies exposing internal framework terms instead of helping the
  creator move from seed to alive route.

## Starter Suites

`smoke` covers the fastest dangerous failures:

- brandmark drift;
- textless prompt;
- fake publishable package;
- autopublish risky paths.

`contract` covers instruction, memory, Agentic OS, article, prepost, and
closeout behavior.

`carousel` covers package and visual-production gates.

`creative` covers creator-facing behavior where deterministic checks are not
enough.

`full` runs every starter task.

## Checker Architecture

The initial harness lives in `evals/`:

- `evals/schemas.py` loads and validates task metadata.
- `evals/runner.py` lists, validates, and checks tasks.
- `evals/checkers/diff_guard.py` blocks forbidden and out-of-scope paths.
- `evals/checkers/deterministic.py` runs required commands.
- `evals/checkers/carousel_package.py` wraps carousel doctor and carousel
  state.
- `evals/checkers/creative_rubric.py` provides deterministic prechecks for
  creator-visible framework leakage.
- `evals/checkers/report.py` aggregates severity and resolved status.
- `evals/tasks/*/deep-spec.md` records evaluator intent so tasks do not decay
  into one-line labels.
- `evals/research/` stores the source ledger and project failure taxonomy.
- `evals/rubrics/` stores anchored subjective rubrics.

Future iterations should add:

- setup patches or fixture builders;
- hidden task variants;
- JSONL run logs with model/agent metadata;
- patch-apply checks;
- per-task timeout and resource limits;
- calibrated human/judge rubric files.

## Task Quality Bar

A task is not accepted merely because it has a prompt and a test command. It
must identify:

- the project failure it represents;
- the exact starting fixture;
- the fail-to-pass behavior that should change;
- the pass-to-pass behavior that must remain stable;
- allowed and forbidden files;
- realistic anti-gaming risks;
- severity levels;
- whether rubric review is needed and what observable evidence the rubric
  should score.

This bar exists because shallow evals teach agents to satisfy labels. The goal
is to test whether an agent can preserve the repo's contract under realistic
pressure.

## Research Memory Loop

Treat eval research as living memory:

1. Capture a failure or external eval practice.
2. Record source, date checked, claim, confidence, and why it matters here.
3. Convert recurring failures into task fixtures.
4. Prefer deterministic checkers first.
5. Add rubric review only when the failure is inherently subjective.
6. Re-run smoke evals before merging agent workflow changes.

Suggested durable surfaces:

- `memory/semantic/eval-research.md`
- `evals/research/sources.json`
- `evals/research/failure-taxonomy.md`

## Merge Gate

Before merging substantial agent-workflow changes:

```bash
venv/bin/python -m pytest tests/test_eval_task_metadata.py tests/test_eval_runner.py -q
venv/bin/python evals/runner.py validate
venv/bin/python evals/runner.py list --suite smoke
venv/bin/python scripts/agentic_os.py health
```

For tasks that modify rules, memory, context, skills, or workflow docs, also run
wiki health and the safe closeout flow described in `AGENTS.md`.
