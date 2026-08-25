# AI Command Center Design

last_updated: 2026-05-28
confidence: 0.78
sources:
- direct creator approval in Codex chat on 2026-05-28
- memory/semantic/engineering-workflow-preferences.md
- AGENTS.md
- scripts/analyze_prepost.py
- scripts/carousel.py
- scripts/create_substack_article_package.py
- scripts/wiki_health.py

## Goal

Create a small terminal command layer that lets the creator operate this repo
in plain English through Codex, without remembering every long script command.

## Scope

This design adds a Makefile, a concise ops playbook, three dependency-free
Python helper scripts, and a Make target for the safe autopublish gate. The
carousel target routes through the canonical Codex-first `scripts/carousel.py`
surface; article, pre-post, and wiki-health pipelines remain separate.

## Approach

Use a conservative wrapper layer:

- `Makefile` exposes stable one-word commands.
- `scripts/daily_creator_brief.py` summarizes current repo state.
- `scripts/jam_today.py` prepares carousel jam context and safe commands.
- `scripts/run_content_health.py` wraps the required wiki/memory health gate.
- `make publish` routes through `scripts/autopublish.py` when verified
  session publishing is appropriate.
- `docs/ai-ops-playbook.md` explains the English operating model.

## Data Flow

Codex or the creator runs `make brief`, chooses a route, then uses the matching
target. The targets call existing scripts and write outputs in the same
locations the repo already uses. Health is run at the end with a session note.

## Error Handling

The wrappers fail early when required paths are missing. They print the
underlying command before running or recommending it so a human can inspect the
action. `run_content_health.py` exits with the wiki-health status code.

## Testing

Tests should verify that the command surface files exist, help commands run,
and the Makefile exposes the expected targets. Full carousel/article generation
continues to be covered by existing pipeline tests.
