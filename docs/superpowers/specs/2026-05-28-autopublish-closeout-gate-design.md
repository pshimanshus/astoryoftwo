# Autopublish Closeout Gate Design

## Purpose

Make repo publishing the default end-of-session behavior without turning Git
into a blind background pusher. The gate should let Codex publish normal
project changes automatically, while blocking secrets, sensitive media, broken
tests, and unhealthy wiki/memory state.

## Recommended Approach

Use a deterministic CLI script, not a daemon:

```bash
venv/bin/python scripts/autopublish.py --session-note "short summary"
```

The script owns the mechanical closeout sequence: inspect changes, block risky
paths, scan changed text files for secret patterns, run tests, run wiki health,
stage all safe changes, commit, push the current branch, and write a compact
local log. Repository instructions then require future Codex sessions to run
this gate at the end of substantial work.

When the worktree contains unrelated changes, the caller must use repeated
`--include PATH` flags for the exact files or folders owned by the current
session. The script then gates and stages only those included paths.

## Safety Rules

- Block `.env`, `.env.*`, identity images, draft videos, raw corpus dumps,
  virtual environments, caches, logs, and generated image/video outputs if they
  appear in git status.
- Scan changed text files for live-looking tokens such as OpenAI keys, Apify
  keys, GitHub PATs, Anthropic keys, Slack tokens, and generic populated
  secret assignments.
- Ignore placeholder values such as `your_api_key_here`, `...`, `changeme`, and
  empty assignments.
- Run the full pytest suite before committing.
- Run `scripts/wiki_health.py --write --fix-index` before committing.
- Push only after all gates pass.

## Non-Goals

- No launch daemon, cron job, file watcher, or timed background publisher.
- No automatic bypass for failing tests or secret findings.
- No attempt to infer human ownership of mixed worktrees; future Codex sessions
  must inspect scope and pass `--include` for owned paths before invoking the
  gate.

## Files

- `scripts/autopublish.py`: CLI plus testable helper functions.
- `tests/test_autopublish.py`: path risk, secret scan, command plan, and commit
  message tests.
- `AGENTS.md`: standing closeout rule for future sessions.
- `memory/semantic/engineering-workflow-preferences.md`: durable creator
  preference for automatic safe publishing.
