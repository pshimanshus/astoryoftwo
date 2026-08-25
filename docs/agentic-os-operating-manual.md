# Agentic OS Operating Manual

Updated: 2026-08-24
Status: current compact contract

## Purpose

Agentic OS loads project rules and memory, reports workflow health, searches
durable knowledge, diagnoses packages, and proposes learning updates. It is a
control plane around creative work, not a creative council.

## Commands

```bash
venv/bin/python scripts/agentic_os.py context --render
venv/bin/python scripts/agentic_os.py skill-system carousel_jam
venv/bin/python scripts/agentic_os.py index-memory
venv/bin/python scripts/agentic_os.py search "visual first carousel"
venv/bin/python scripts/agentic_os.py recall "one concrete couple moment"
venv/bin/python scripts/agentic_os.py carousel-doctor output/carousels/<date>/<slug>
venv/bin/python scripts/agentic_os.py health
```

Use the first command to inspect what the runtime actually loads. Use
`skill-system` to inspect active components, gates, agents, and artifacts. Use
the doctor on a real package; do not infer health from filenames or old output.

## Authority

1. Current creator instruction.
2. Nearest `AGENTS.md`.
3. `config/rules/`.
4. Active skill and workflow registry.
5. Semantic memory and wiki.
6. Historical output and reports.

Generated packages, old audits, and past plans never override a current rule.

## Context

`config/agentic_context_manifest.json` defines budgeted profiles. Required rule
includes must not be silently truncated. Keep the common context small; load a
long reference only for a specific diagnosis, comparison, or final audit.

## Workflow Registry

`config/skill-systems.json` is the machine-readable router. The ordinary
`carousel_jam` system has four gates and no default agents. The separate
`instagram_idea_loop` owns deep parallel discovery and verification when the
creator explicitly requests it. Article, prepost, and wiki-health systems keep
their own components and gates.

## Carousel State

The public sequence is:

```text
draft -> handoff_ready -> proof_qa_required
  -> awaiting_creator_proof_approval -> batch_ready
  -> final_qa_required -> publish_ready
```

`blocked`, `proof_failed`, and `final_qa_failed` are repair states. These ten
names are the complete public vocabulary; creator locks remain the four gates,
not extra lifecycle states.

The doctor trusts current files and hash-bound pixel observations:

- a missing input yields `blocked` with the specific missing input;
- placeholder copy-only scenes yield `blocked` with
  `define_physical_actions`;
- a ready compact prompt handoff yields `handoff_ready`;
- quarantined proof bytes without bound QA yield `proof_qa_required`;
- a semantic proof failure yields `proof_failed` and
  `repair_visual_premise`;
- a passed proof awaiting the creator yields
  `awaiting_creator_proof_approval`;
- creator-approved proof reuse unlocks `batch_ready`;
- quarantined remaining candidates yield `final_qa_required`;
- failed complete-deck QA yields `final_qa_failed`;
- a final QA PASS remains `final_qa_required` with next action `finalize_deck`;
- only current final files, hashes, dimensions, visual QA, and final audit yield
  `publish_ready`.

Do not create separate approval, review, run, provenance, and package states.
Archived v2 packages are read-only auditable; new writes use v3.

## Learning

Learning is proposal-only. A run may suggest a correction; it must not silently
rewrite rules, skills, memory, or context. Durable creator corrections go to
the narrowest canonical rule and, when useful, one semantic-memory entry plus a
regression test. `memory/working.md` remains pointer-only.

## Health and Closeout

For instruction, workflow, context, memory, or Agentic OS changes:

```bash
venv/bin/python scripts/agentic_os.py health
venv/bin/python scripts/wiki_health.py --write --fix-index \
  --session-note "short description"
```

Inspect `git status --short`, keep unrelated creator work out of the change,
run focused tests, then use the safe closeout gate. Never publish live-looking
secrets, identity reference media, a mixed worktree, or unverified final art.

## Anti-Sprawl Rules

- One active workflow per job.
- One state record while generation is in progress.
- One final manifest after completion.
- No agent room unless a named task benefits from independent parallel work.
- No scores or prose certification as a substitute for inspecting pixels.
- No full test suite inside a production command.
- No new instruction file when an existing canonical surface can hold the rule.
- No raw response or internal deliberation in a publishable package.
