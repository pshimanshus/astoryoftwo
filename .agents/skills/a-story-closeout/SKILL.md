---
name: a-story-closeout
description: Use at the end of substantial repo sessions, before committing, pushing, publishing, or when the worktree has mixed human and Codex changes.
---

# A Story Closeout

Use this repo skill for safe session closeout. It wraps `scripts/autopublish.py`
and the mandatory health gates.

## Load First

1. `memory/semantic/engineering-workflow-preferences.md`
2. `docs/ai-ops-playbook.md`
3. `scripts/autopublish.py`
4. `scripts/wiki_health.py`

## Operating Contract

- Inspect git status before staging.
- Do not silently stage unrelated human changes.
- Use `--include` for scoped publishing when the worktree is mixed.
- Block risky paths, live-looking secrets, failing tests, wiki-health failures,
  and unclear scope.
- Do not replace the gate with blind background pushing, timed daemons, or
  manual reminders.

## Useful Commands

```bash
make publish-dry-run NOTE="short summary" INCLUDE="path1 path2"
make publish NOTE="short summary" INCLUDE="path1 path2"
venv/bin/python scripts/autopublish.py --session-note "short summary" --include path1 --include path2
```
