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

Fixture direction: **solution**. A single-pass `evals/runner.py review` must
observe the materialized starter as `unresolved`. The task becomes resolved
only after the agent repairs the fixture-backed repository state and the named
checker passes.

The visible fixture writes durable correction guidance directly into
`memory/working.md` and leaves the semantic memory file without the matching
learning. The fail-to-pass check flags durable policy in working memory,
missing semantic preservation, missing confidence, or absent sources. The
pass-to-pass check preserves episodic records, graph memory, recall search, and
wiki-health behavior.

## Failure Modes

- Agent deletes the learning instead of moving it.
- Agent leaves working memory as a long rule document.
- Agent creates semantic memory without confidence or sources.
- Agent edits `AGENTS.md` to make working memory authoritative.
- Agent deletes episodic records to make health output quieter.

## Checker Design

The checker inspects `memory/working.md` shape, semantic memory metadata, and
recall behavior. A fail-to-pass case flips when durable learning is moved
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
