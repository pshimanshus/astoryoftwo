---
name: a-story-closeout
description: Safely close out substantial A Story repo sessions, mixed worktrees, publish attempts, staging, commits, pushes, and PR-ready changes. Use before committing, pushing, publishing, running autopublish, or summarizing completed repo work; do not use for creative drafting unless the session is ready for verification and closeout.
---

# A Story Closeout

## Overview

Use this repo skill for safe session closeout. It wraps `scripts/autopublish.py`
and the mandatory health gates.

## Load First

1. `AGENTS.md`
2. `memory/semantic/engineering-workflow-preferences.md`
3. `docs/ai-ops-playbook.md`
4. `scripts/autopublish.py`
5. `scripts/wiki_health.py`

## Operating Contract

- Inspect git status before staging.
- Do not silently stage unrelated human changes.
- Use `--include` for scoped publishing when the worktree is mixed.
- Block risky paths, live-looking secrets, failing tests, wiki-health failures,
  and unclear scope.
- Do not replace the gate with blind background pushing, timed daemons, or
  manual reminders.
- Report any validation that could not run.

## Workflow

1. Inspect `git status --short` and separate Codex changes from unrelated human
   or generated changes.
2. Choose scoped `--include` paths when the worktree is mixed.
3. Run the smallest relevant tests and health gates for the touched surfaces.
4. Run `publish-dry-run` before `publish` unless the creator explicitly asked
   only for a local summary.
5. Commit, push, or publish only when the gate passes and scope is clear.

## Useful Commands

```bash
make publish-dry-run NOTE="short summary" INCLUDE="path1 path2"
make publish NOTE="short summary" INCLUDE="path1 path2"
venv/bin/python scripts/autopublish.py --session-note "short summary" --include path1 --include path2
```
