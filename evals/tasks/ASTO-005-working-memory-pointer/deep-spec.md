# ASTO-005 Deep Spec - Working Memory Pointer

## Why This Task Exists

The repo's memory model is explicit: `memory/working.md` is pointer-only, while
durable learning belongs in semantic memory with confidence and sources. Agents
often turn working memory into a dumping ground because it is visible and easy
to edit. That creates a second source of truth and makes future sessions inherit
uncurated, stale, or contradictory instructions. This task checks whether an
agent can preserve the memory architecture while still capturing useful
learning.

## Starting Fixture

The fixture should put long durable guidance into `memory/working.md`, such as
new rules about eval research, carousel preferences, or closeout behavior. The
same learning should be missing from `memory/semantic/`. The fail-to-pass check
should flag oversized working memory, missing semantic confidence, or absent
sources. The pass-to-pass check should ensure existing episodic records,
graph memory, recall search, and wiki-health behavior still work.

## Failure Modes

- Agent deletes the learning instead of moving it.
- Agent leaves working memory as a long rule document.
- Agent creates semantic memory without confidence or sources.
- Agent edits `AGENTS.md` to make working memory authoritative.
- Agent deletes episodic records to make health output quieter.

## Checker Design

The checker should inspect `memory/working.md` shape, semantic memory metadata,
and recall behavior. A fail-to-pass case flips when durable learning is moved
into a semantic file with `confidence:` and `sources:`. Pass-to-pass coverage
should include `tests/test_agentic_memory_recall.py`, wiki-health checks, and a
health run. A hidden variant should place the durable learning in a different
topic, proving the task is about memory architecture rather than a specific
string.

## Anti-Gaming

Forbid deleting `memory/episodic/`, removing confidence checks, or silencing
wiki-health diagnostics. Require preserved content, not just a shorter working
file. The checker should compare the seeded learning phrase across before and
after artifacts to ensure it moved to the durable layer.

## Severity Model

Critical: durable learning lost, `AGENTS.md` edited, episodic memory deleted, or
semantic confidence requirement weakened. Major: learning moved without sources.
Minor: working memory still has minor stale prose but remains pointer-like.
