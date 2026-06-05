---
name: a-story-wiki-health
description: Use when checking or repairing wiki, memory, Agentic OS context, skill registry, instruction drift, health artifacts, or session continuity.
---

# A Story Wiki Health

Use this repo skill for the wiki, memory, context, and instruction health loop.
It wraps the existing Agentic OS `wiki_health` system.

## Load First

1. `config/skill-systems.json` -> `wiki_health`
2. `scripts/agentic_os.py health`
3. `scripts/wiki_health.py`
4. `memory/working.md`
5. `memory/semantic/`
6. `wiki/index.md`

Use `venv/bin/python scripts/agentic_os.py skill-system wiki_health` for the
machine-readable workflow record.

## Operating Contract

- Run focused diagnostics before claiming the memory layer is healthy.
- If health returns NEEDS_HEAL, repair the failed check or leave the generated
  HEAL proposal as the next-session starting point.
- Keep learning proposal-only unless deterministic eval gates and human approval
  authorize changes.

## Useful Commands

```bash
venv/bin/python scripts/agentic_os.py health
venv/bin/python scripts/agentic_os.py context --render
venv/bin/python scripts/wiki_health.py --write --fix-index --session-note "short summary"
make health NOTE="short summary"
```
