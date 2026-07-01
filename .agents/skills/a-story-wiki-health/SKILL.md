---
name: a-story-wiki-health
description: Use when checking or repairing wiki, memory, Agentic OS context, skill registry, instruction drift, health artifacts, session continuity, or A Story repo workflow surfaces. Also use when the creator asks to "explore everything", "create a workflow for this", update an existing repo-scoped skill, route a fuzzy A Story request, or make necessary workflow changes while fixing the nearest existing surface before considering anything new.
---

# A Story Wiki Health

## Overview

Use this repo skill for the wiki, memory, context, and instruction health loop.
It wraps the existing Agentic OS `wiki_health` system and owns skill-surface
repairs when the creator asks for workflow discovery or instruction drift work.

## Load First

1. `AGENTS.md`
2. `.agents/skills/*/SKILL.md`
3. `config/skill-systems.json` -> `wiki_health`
4. `scripts/agentic_os.py health`
5. `scripts/wiki_health.py`
6. `memory/working.md`
7. `memory/semantic/`
8. `wiki/index.md`

When editing a Codex skill, also load the system `skill-creator` instructions
and use its validator. Do not copy long skill-creator guidance into this repo
skill.

Use `venv/bin/python scripts/agentic_os.py skill-system wiki_health` for the
machine-readable workflow record.

## Operating Contract

- Run focused diagnostics before claiming the memory layer is healthy.
- For fuzzy workflow requests, first map the request to the nearest existing
  repo skill, workflow system, command, or rule surface.
- Do not create a new skill, workflow document, rule, reference, script, or
  asset if a similar thing already exists. Update the closest existing surface
  with the smallest durable change instead.
- Only create a new repo-scoped skill when the creator explicitly asks for a new
  skill and the existing skill registry has no close fit.
- If health returns NEEDS_HEAL, repair the failed check or leave the generated
  HEAL proposal as the next-session starting point.
- Keep learning proposal-only unless deterministic eval gates and human approval
  authorize changes.
- Preserve exact user-provided captions, prompts, paths, commands, IDs, and
  quoted copy.
- Keep `memory/working.md` pointer-only.
- Treat `config/rules/` as canonical for creative rules; link to canonical
  sources instead of duplicating them.
- Leave unrelated human, generated, or previous-agent worktree changes alone.

## Workflow

1. Inspect current repo skill files, workflow registry entries, and relevant
   instruction surfaces before editing.
2. Route the request to an existing skill or workflow when possible.
3. If an edit is needed, update the closest existing surface with the smallest
   durable change.
4. Validate changed skills with the skill-creator validator.
5. Run focused repo tests, Agentic OS health, and wiki health when instruction,
   workflow, memory, context, or Agentic OS surfaces changed.
6. Report changed paths and any generated health artifacts separately from
   source edits.

## Useful Commands

```bash
rg --files .agents/skills config/skills config/rules scripts tests
venv/bin/python scripts/agentic_os.py health
venv/bin/python scripts/agentic_os.py context --render
venv/bin/python scripts/agentic_os.py skill-system wiki_health
venv/bin/python scripts/agentic_os.py skill-usage
venv/bin/python scripts/agentic_os.py record-skill-run a-story-wiki-health --outcome blocked --note "short reason"
python3 /Users/himanshusharma/.codex/skills/.system/skill-creator/scripts/quick_validate.py .agents/skills/<skill-name>
venv/bin/python scripts/wiki_health.py --write --fix-index --session-note "short summary"
make health NOTE="short summary"
```
