# A Story of Two Eval Suite

This directory contains repo-local SWE-bench-style eval tasks for future
checkers and agents.

The suite tests whether an agent can preserve the project contract while
making realistic repository changes. It is not a generic model benchmark and it
does not replace the normal test suite. It wraps realistic issue prompts,
starting-state descriptions, path guards, required commands, deterministic
checkers, and rubric hooks.

## Quick Start

Validate task metadata:

```bash
venv/bin/python evals/runner.py validate
```

Run the bounded alignment review. It freezes registry order, materializes each
selected fixture once, checks its declared starting direction once, and stops:

```bash
venv/bin/python evals/runner.py review
venv/bin/python evals/runner.py review --suite smoke
```

List tasks:

```bash
venv/bin/python evals/runner.py list
venv/bin/python evals/runner.py list --suite smoke
```

Check one task after an agent has attempted it:

```bash
venv/bin/python evals/runner.py check ASTO-003-textless-prompt
```

Tasks with rubric hooks remain unresolved until an anchored review result is
supplied:

```bash
venv/bin/python evals/runner.py check ASTO-011-small-brief-no-framework-dump \
  --rubric-results /path/to/rubric-results.json
```

Rubric result files follow `evals/rubrics/review.schema.json`. Each review must
name distinct author and reviewer IDs, bind to the exact reviewed artifact with
`artifact_sha256`, score every rubric dimension, and cite at least one concrete
evidence anchor per dimension. A changed artifact makes the review stale.

For fixture-backed tasks, apply the fixture overlay to an isolated repo
checkout before giving the prompt to the agent. The checker should then run
against that prepared checkout, not against the fixture source directory.
Some fixture checkers are failure detectors that pass when the production gate
blocks a seeded unsafe state; others are solution checkers that fail until the
artifact is repaired. This is machine-readable in `fixture_contract` and
explained in the task's `deep-spec.md`:

- `solution` + `unresolved`: the materialized starter must fail before repair.
- `regression` + `guarded`: the current production gate must reject the seeded
  failure. A real agent benchmark must first apply a hidden code mutation or
  use a pre-fix revision; otherwise a no-op agent could receive false credit.

The `review` command validates this direction. It does not execute an agent,
retry failed tasks, or recursively review its own output.

Materialize a task's broken starting fixture into a scratch directory:

```bash
tmpdir=$(mktemp -d)
venv/bin/python evals/runner.py prepare ASTO-003-textless-prompt --output "$tmpdir"
```

Run only metadata and diff checks while developing a checker:

```bash
venv/bin/python evals/runner.py check ASTO-003-textless-prompt --skip-commands
```

Inject changed paths for checker development:

```bash
venv/bin/python evals/runner.py check ASTO-001-brandmark-drift \
  --skip-commands \
  --changed-path config/rules/brandmark.md \
  --changed-path AGENTS.md
```

## Task Anatomy

Each task lives at `evals/tasks/<task-id>/` and contains:

- `task.json`: stable metadata and checker configuration.
- `prompt.md`: the issue-like prompt given to the agent.
- `deep-spec.md`: evaluator-facing design notes: why the task exists,
  starting fixture, failure modes, checker design, anti-gaming, and severity.
- `fixtures/`: optional concrete broken starting-state files that can be
  materialized by `evals/runner.py prepare`.
- `fixture_contract`: whether the visible fixture is a repair target or a
  regression guard, its expected initial outcome, and the benchmark setup
  needed to prevent no-op credit.
- optional hidden checkers in future iterations.

The task metadata deliberately uses JSON instead of YAML so the harness can run
without adding a parser dependency.

Each task must declare:

- `fail_to_pass`: the seeded failure or regression that should flip after the
  agent's patch.
- `pass_to_pass`: behavior that must remain stable while fixing the failure.
- `deterministic_checkers`: executable checker names. Unknown names fail
  validation instead of becoming decorative labels.
- `rubric_checkers`: executable rubric-hook names. Unknown names fail
  validation, and the runner records rubric prechecks in the task report.

## Scoring

Critical failures make a task unresolved. Major failures also make the starter
tasks unresolved. Rubric checkers run after deterministic checks and add
artifact-level prechecks. A task with rubric hooks stays `PENDING` until an
evidence-bearing human or judge review is supplied, and a rubric never
overrides a failed mechanical contract check.

All `evals/**` paths are protected by the diff guard during task solving. A
solver cannot pass by editing its prompt, fixture, metadata, checker, rubric,
registry, or runner.

Mechanical gates should cover:

- forbidden paths such as `AGENTS.md`, `.env*`, identity references, logs,
  caches, and generated final media;
- focused tests or scripts the task must pass;
- structural package checks such as carousel doctor and image-size gates;
- instruction-surface and rule-authority checks.

Current named deterministic checkers are:

- `diff_guard`: forbidden/out-of-scope path protection.
- `brandmark_top_right_rule`: active brandmark rule authority.
- `carousel_doctor_fixture`: fixture-backed carousel doctor/state behavior.
- `autopublish_safety_fixture`: risky path and synthetic secret scanning.
- `creator_visible_copy`: creator-facing framework language leakage.
- `stale_artifact_fixture`: creator-correction stale-string blockers.
- `identity_stop_gate_fixture`: no identity eval, no next slide blockers.
- `score_rejection_fixture`: inflated rejected-concept calibration detection.
- `home_cinematic_fixture`: generic home/interior visual-plan detection.
- `public_name_boundary_fixture`: public Aachu/Zuv name leakage detection.
- `copy_visual_logic_fixture`: visual QA pass claims that contradict copy.
- `scene_entity_integrity_fixture`: duplicate/background-person inventory
  detection.
- `hand_object_integrity_fixture`: unowned or story-unnecessary hands,
  unexplained edge entry, and solid-object intersection detection.
- `whole_person_spatial_integrity_fixture`: whole-person silhouette,
  depth-order, body/environment merge, and solid-object topology detection.
- `format_snapback_fixture`: latest creator format correction vs generated
  output mismatch detection.
- `working_memory_pointer_fixture`: working-memory pointer-only enforcement.
- `creator_skill_routing_fixture`: creator skill stack routing coverage.
- `context_rule_truncation_fixture`: fail-loud required rule include truncation.
- `article_story_selling_fixture`: article Layer E / Story-Selling gate
  evidence.
- `prepost_layer_e_fixture`: pre-post Reel Layer E grounding coverage.
- `visual_variety_shot_ladder_fixture`: repeated-scene shot-ladder blocker.
- `small_brief_seed_fixture`: small creative seed preservation, format choice,
  scene object/reaction/payoff evidence, and no creator-solving handoff.

Rubric gates should cover:

- recognition and partner-sendability;
- scene proof instead of poster copy;
- preservation of the creator seed;
- no visible internal framework language;
- visual variety and relationship motion.

Current rubric hooks are:

- `creative_contract`: creator-visible copy and score-calibration prechecks,
  followed by an anchored 12-point review.
- `visual_variety`: visual-artifact prechecks followed by anchored scoring for
  image-first legibility, shot progression, continuity, blocking/spatial
  clarity, and text-image composition.

## Adding A Task

1. Start from a real repo failure, creator correction, review comment, or
   health diagnostic.
2. Reduce it to one issue-like prompt with one primary failure mode.
3. Write `task.json` with allowed paths, forbidden paths, required commands,
   and anti-gaming notes.
4. Add a concrete fixture overlay for smoke or high-risk tasks. The fixture
   should trigger an existing checker before the fix.
5. Write `deep-spec.md` before treating the task as real. It must name the
   fail-to-pass condition, pass-to-pass regression surface, hidden variant,
   anti-gaming strategy, and severity model.
6. Add or update deterministic tests/checkers before adding subjective rubrics.
7. Declare fixture direction. Regression guards require a hidden mutation or
   pre-fix revision before they can count as agent tasks.
8. Add a hidden variant when the visible task could be gamed by string matching.
9. Run `venv/bin/python evals/runner.py validate` and
   `venv/bin/python evals/runner.py review`.

Keep creative-quality judging separate from mechanical contract checks.

## Research Layer

The suite's research spine lives in:

- `evals/research/sources.json`
- `evals/research/failure-taxonomy.md`
- `evals/rubrics/creative-contract.md`
- `evals/rubrics/visual-storytelling.md`

Do not add a benchmark source as trivia. Each source must say what claim it
supports and how that claim changes this repo's eval design. The useful loop is
failure -> minimized fixture -> deterministic checker -> hidden variant ->
rubric only when the failure is inherently subjective.

For this repo, "failure" means a documented project event first: creator
correction, rejected concept, package blocker, wiki-health diagnostic,
autopublish block, memory proposal, or review finding. Add that evidence to
the Evidence Ledger section of `evals/research/failure-taxonomy.md` before
adding a new task, otherwise the task risks becoming a generic agent benchmark
instead of an @a.storyof.two contract eval.
