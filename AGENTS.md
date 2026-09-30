# AGENTS.md - A Story of Two

Compact router. Load deeper files only for the current task.

## First Move

Normalize to goal, context, constraints, done-when. Ask only if unclear.
Before substantial edits: `git status --short --untracked-files=no`. Never
revert user or unrelated changes.

## Token Discipline

Use `config/agentic_context_manifest.json`: default `ideation`; use
`a-story-of-two` only for image production. Open long memory, wiki, output, and
research files only after targeted search.

## Instruction Precedence

Explicit user prompts override repo docs, skills, memory, and rules. The
closest `AGENTS.md` governs its subtree. Rules and docs do not override an explicit user request.

## Source Of Truth

Canonical rules: `config/rules/`. Workflow registry:
`config/skill-systems.json`. Durable creator corrections:
`memory/semantic/`. `memory/working.md is pointer-only`.

## Agentic OS Control Plane

Implementation: `pipeline/agentic/`. Learning proposals are draft-only.

```bash
venv/bin/python scripts/agentic_os.py context --render
venv/bin/python scripts/agentic_os.py skill-system carousel_jam
venv/bin/python scripts/agentic_os.py carousel-doctor output/carousels/<date>/<slug>
venv/bin/python scripts/wiki_health.py --write --fix-index --session-note "note"
```

Use `scripts/autopublish.py` with repeated `--include PATH` in mixed worktrees.

## Workflow Routing

Use repo skills when named or clearly matched: `$a-story-storytelling-hook`,
`$a-story-carousel-jam`, `$a-story-direct-visual-story`, `$a-story-article`,
`$a-story-prepost`.

## Creative Gates

Start with the alive human draft. Final art must keep Aachu/Zuv recognizable.
Default post/carousel output is `1080x1440`; make other formats only when asked.
Keep the tiny `@a.storyof.two` top-right signature.

## Review guidelines

Lead with serious findings: secrets, broken gates, missing tests, duplicated
rule authority, prompt drift, carousel regressions, risky Agentic OS or
autopublish changes.

## Do Not

Do not delete `corpus/posts/`, `corpus/reels/`, or `memory/episodic/`. Do not
commit `.env`. Do not treat generated `output/` churn as source truth. Do not
recreate `CLAUDE.md`. Use Codex Worktrees for parallel work, Browser for visual
QA, `/review` locally, GitHub `@codex review` when available, and Automations
only for scoped recurring checks.

## Pointers

`docs/ai-ops-playbook.md`, `docs/agentic-os-operating-manual.md`,
`docs/superpowers/plans/creative-os-master-plan.md`,
`docs/superpowers/plans/THE-PLAN.md`.
