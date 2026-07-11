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

List tasks:

```bash
venv/bin/python evals/runner.py list
venv/bin/python evals/runner.py list --suite smoke
```

Check one task after an agent has attempted it:

```bash
venv/bin/python evals/runner.py check ASTO-003-textless-prompt
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
- optional fixtures or hidden checkers in future iterations.

The task metadata deliberately uses JSON instead of YAML so the harness can run
without adding a parser dependency.

## Scoring

Critical failures make a task unresolved. Major failures also make the starter
tasks unresolved. Rubric checkers may add useful judgment for creative quality,
but they must not override failed mechanical contract checks.

Mechanical gates should cover:

- forbidden paths such as `AGENTS.md`, `.env*`, identity references, logs,
  caches, and generated final media;
- focused tests or scripts the task must pass;
- structural package checks such as carousel doctor and image-size gates;
- instruction-surface and rule-authority checks.

Rubric gates should cover:

- recognition and partner-sendability;
- scene proof instead of poster copy;
- preservation of the creator seed;
- no visible internal framework language;
- visual variety and relationship motion.

## Adding A Task

1. Start from a real repo failure, creator correction, review comment, or
   health diagnostic.
2. Reduce it to one issue-like prompt with one primary failure mode.
3. Write `task.json` with allowed paths, forbidden paths, required commands,
   and anti-gaming notes.
4. Write `deep-spec.md` before treating the task as real. It must name the
   fail-to-pass condition, pass-to-pass regression surface, hidden variant,
   anti-gaming strategy, and severity model.
5. Add or update deterministic tests/checkers before adding subjective rubrics.
6. Add a hidden variant when the visible task could be gamed by string matching.
7. Run `venv/bin/python evals/runner.py validate`.

Keep creative-quality judging separate from mechanical contract checks.

## Research Layer

The suite's research spine lives in:

- `evals/research/sources.json`
- `evals/research/failure-taxonomy.md`
- `evals/rubrics/creative-contract.md`

Do not add a benchmark source as trivia. Each source must say what claim it
supports and how that claim changes this repo's eval design. The useful loop is
failure -> minimized fixture -> deterministic checker -> hidden variant ->
rubric only when the failure is inherently subjective.
