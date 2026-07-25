# A Story of Two SWE-Bench-Style Evals

last_updated: 2026-07-25
confidence: 0.96
sources:
- AGENTS.md
- config/rules/
- config/skill-systems.json
- evals/research/failure-taxonomy.md
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

## Current Eval Principles

Use these principles when adding or reviewing tasks:

- Evidence first: every task starts from a documented repo failure, creator
  correction, audit finding, blocker, or external eval practice.
- Directional task design: the prompt states what behavior must change, the
  `fail_to_pass` field names the broken behavior, and `pass_to_pass` names the
  regression surface that must stay valid.
- Explicit fixture direction: a `solution` fixture starts unresolved and must
  be repaired; a `regression` fixture starts guarded because the current gate
  rejects it. Regression fixtures require a hidden code mutation or pre-fix
  revision before they can award agent solve credit.
- Concrete fixtures: high-risk tasks carry a materialized starting state that a
  checker can run against in an isolated checkout.
- Grader over vibe: deterministic checkers inspect files, states, counts,
  statuses, paths, and structured evidence before any rubric judge is used.
- Rubric separation: creative-quality judging may score recognition,
  sendability, scene proof, and voice, but it never overrides a failed
  mechanical gate.
- Anti-gaming: hidden variants change names, phrasing, fields, locations, and
  failure examples while preserving the same contract.
- No-op resistance: a task cannot count as an agent benchmark merely because a
  current regression guard already passes on its bad fixture.
- Before/after proof: certified repair requires an evaluator-owned unresolved
  baseline, a changed workspace, an update to at least one declared solution
  file, and every baseline failure flipping to `PASS`.
- Prompt-checker alignment: review misleading prompts, overly strict tests,
  underspecified prompts, and low-coverage tests as separate failure classes.
- Observable reports: every failure should return a code, severity, message,
  and evidence list so a future agent can repair the actual contract breach.

## Eval Types In This Repo

Unit tests check a single function or gate, such as prompt constraints or image
size.

Integration tests check a workflow, such as article packaging, pre-post Reel
analysis, Agentic OS context loading, or carousel doctor.

Golden artifacts should be used sparingly for stable JSON/package shapes, not
for open-ended creative taste.

Rubric evals judge subjective creative quality with anchored criteria. They are
useful for scene proof, recognition, sendability, and voice, but they must stay
separate from mechanical contract checks. Mechanical prechecks cannot award a
rubric pass; the task remains pending until an evidence-bearing human or judge
review is supplied.

Agent task evals combine all of this: a prompt, a starting state, allowed and
forbidden changes, required commands, deterministic gates, rubric hooks, and a
resolved/unresolved result.

## What To Evaluate

High-value failure modes:

- `AGENTS.md` edited to hide downstream drift.
- `config/rules/` losing canonical authority.
- carousel work skipping small brief, format choice, human draft, concept lock,
  copy lock, proof lock, visual QA, or final audit;
- image packages claiming final without every format locked by the current
  request: default post/carousel `1080x1440`, explicit Story/Reel
  `1080x1920`, or explicit square `1080x1080`;
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
- stale downstream artifacts carrying old copy/route/prompt text after a
  creator correction;
- identity proof batches continuing without structured reference IDs and
  likeness notes;
- concept-room score inflation after the creator rejects a route as unsendable
  or far below the winning-carousel bar;
- home/interior visual prompts that say "cozy" but omit camera, motivated
  light, blocking, object continuity, and lived-in story evidence;
- internal Aachu/Zuv names leaking into public slide copy;
- copy-visual contradictions where clothing, gaze, object state, or action
  disproves the exact slide text.
- duplicate background characters, reflected figures, or extra actors in a
  supposedly two-person scene;
- anonymous hands, unexplained edge-entry limbs, or hand/object intersections
  that survive broad visual QA.
- whole-person spatial topology failures where a body merges into a solid
  object despite correct people and hand counts.
- stale or agent-inferred human approvals that unlock copy, image, or publish
  stages after the approved artifact hash changes.

## Starter Suites

`smoke` covers the fastest dangerous failures:

- brandmark drift;
- textless prompt;
- fake publishable package;
- autopublish risky paths;
- identity eval stop gate;
- duplicate background characters;
- hand/object integrity;
- whole-person spatial integrity.

`contract` covers instruction, memory, Agentic OS, article, prepost, and
closeout behavior.

`carousel` covers package and visual-production gates.

`creative` covers creator-facing behavior where deterministic checks are not
enough.

`full` runs every starter task.

## Checker Architecture

The initial harness lives in `evals/`:

- `evals/schemas.py` loads and validates task metadata.
- `evals/runner.py` lists, validates, inspects, freezes baselines, and grades
  attempts.
- `evals/attempts.py` snapshots the prepared workspace, verifies hidden
  mutation evidence, and enforces fail-to-pass transitions.
- `evals/review.py` performs one registry-ordered fixture-direction pass with
  no retry or recursive self-review.
- `evals/checkers/diff_guard.py` blocks forbidden and out-of-scope paths.
- `evals/checkers/deterministic.py` runs required commands.
- `evals/checkers/carousel_package.py` wraps carousel doctor and carousel
  state.
- `evals/checkers/creative_rubric.py` provides deterministic prechecks for
  creator-visible framework leakage.
- `evals/checkers/rubric.py` executes declared rubric hooks as report-visible
  prechecks and validates supplied anchored rubric results.
- `evals/checkers/task_specific.py` maps task metadata checker names to
  executable project-specific checks.
- `evals/checkers/report.py` aggregates severity and resolved status.
- `evals/tasks/*/deep-spec.md` records evaluator intent so tasks do not decay
  into one-line labels.
- `evals/tasks/*/fixtures/` stores concrete broken starting states for tasks
  that can be materialized locally.
- `evals/research/failure-taxonomy.md` stores the project taxonomy plus the
  canonical Evidence Ledger from memory, audits, concept rejections, package
  blockers, and diagnostics.
- `evals/rubrics/` stores anchored subjective rubrics.

Future iterations should add:

- hidden mutation packs or pinned pre-fix revisions for every regression task;
- hidden task variants;
- JSONL run logs with model/agent metadata;
- per-task timeout and resource limits;
- calibrated human/judge rubric files.

The first executable fixture layer supports:

```bash
venv/bin/python evals/runner.py prepare ASTO-003-textless-prompt --output /tmp/asto-eval
```

This writes the visible task prompt plus fixture overlay files into a scratch
directory. In a full agent benchmark, apply the overlay to an isolated repo
checkout before running the task prompt. For tasks whose `fixture_contract`
uses `hidden_code_mutation_required`, the overlay alone is not a valid agent
starting state because the current guard already catches the failure.

Run the finite alignment review with:

```bash
venv/bin/python evals/runner.py review
```

The command snapshots the selected registry entries, reviews each exactly once
in registry order, reports direction mismatches, and exits. A new review run is
needed only when the task inventory or reviewed files change.

## Certified Repair Lifecycle

`review` and `check` are suite-development tools. Neither can award agent solve
credit. Certified repair uses an evaluator-owned baseline record:

```bash
venv/bin/python evals/runner.py baseline ASTO-001-brandmark-drift \
  --record /trusted-eval-state/ASTO-001-baseline.json

# Run the agent once against the prepared isolated checkout.

venv/bin/python evals/runner.py grade ASTO-001-brandmark-drift \
  --baseline /trusted-eval-state/ASTO-001-baseline.json
```

The baseline command runs task-specific deterministic checkers before the
agent. It writes a record only when the starting state is actually unresolved.
For regression fixtures it also requires a hidden mutation manifest whose file
digests match the mutated workspace and whose paths include a declared
production solution file.

The grade command compares the final workspace to the frozen hash snapshot. A
certified pass requires a non-empty patch, at least one changed
`expected_files_changed` path that remains present, all baseline failures
flipped to `PASS`, all final deterministic checks and commands passing, no
protected harness changes, and completed artifact-bound rubric review where
declared. The evaluator owns the baseline and mutation records outside the
solver workspace.

For adversarial runs, execute `runner.py` from a read-only trusted harness copy
and pass `--workspace-root` for the isolated solver checkout. The runner binds
the `evals` package to the trusted location before adding the solver checkout
to the production-module import path.

## Task Quality Bar

A task is not accepted merely because it has a prompt and a test command. It
must identify:

- the project failure it represents;
- the exact starting fixture;
- the structured `fail_to_pass` behavior that should change;
- the structured `pass_to_pass` behavior that must remain stable;
- allowed and forbidden files;
- realistic anti-gaming risks;
- severity levels;
- whether rubric review is needed and what observable evidence the rubric
  should score.
- for smoke/high-risk tasks, a fixture overlay that demonstrably triggers a
  local checker in the direction declared by `fixture_contract`;
- a clear statement of whether the task is a runnable solution fixture or a
  regression guard that still needs an isolated broken-code baseline;
- no solver write access to `evals/**`.
- a demonstrated `baseline -> agent patch -> grade` transition before the task
  is reported as benchmark-ready.

This bar exists because shallow evals teach agents to satisfy labels. The goal
is to test whether an agent can preserve the repo's contract under realistic
pressure.

## Research Memory Loop

Treat eval research as living memory:

1. Capture a failure or external eval practice.
2. Record source, date checked, claim, confidence, and why it matters here.
3. Add repo failures to the Evidence Ledger in
   `evals/research/failure-taxonomy.md` before turning them into tasks.
4. Convert recurring failures into task fixtures.
5. Prefer deterministic checkers first.
6. Add rubric review only when the failure is inherently subjective.
7. Re-run smoke evals before merging agent workflow changes.

Suggested durable surfaces:

- `memory/semantic/eval-research.md`
- `evals/research/sources.json`
- `evals/research/failure-taxonomy.md`

## Merge Gate

Before merging substantial agent-workflow changes:

```bash
venv/bin/python -m pytest tests/test_eval_task_metadata.py tests/test_eval_runner.py -q
venv/bin/python evals/runner.py validate
venv/bin/python evals/runner.py review
venv/bin/python evals/runner.py list --suite smoke
venv/bin/python scripts/agentic_os.py health
```

When a merge claims to fix a represented failure, also run `grade` for that
task against an evaluator-owned failing baseline. Passing `review` is not
evidence that the change fixed anything.

For tasks that modify rules, memory, context, skills, or workflow docs, also run
wiki health and the safe closeout flow described in `AGENTS.md`.
