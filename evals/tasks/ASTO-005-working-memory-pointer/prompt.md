# Issue: Working Memory Became Durable Rule Memory

## Context

`memory/working.md` is supposed to be pointer-only, but a previous session wrote
long-term creator or engineering guidance directly into it. That makes working
memory a competing source of truth and weakens semantic memory.

## Task

Move the durable learning into the appropriate `memory/semantic/` file with
confidence and sources. Restore `memory/working.md` to a compact pointer
surface that tells future agents where durable memory lives.

## Acceptance Criteria

- Durable learning is preserved, not deleted.
- Semantic memory includes `confidence:` and `sources:`.
- `memory/working.md` is short and pointer-like.
- Recall and wiki-health tests pass.

## Constraints

Do not edit `AGENTS.md`. Do not delete `memory/episodic/`. Do not remove
semantic-memory confidence checks.
