# Agentic OS Control Plane

last_updated: 2026-05-28
confidence: 0.86
sources:
- docs/superpowers/plans/2026-05-25-agentic-os-spine.md
- AGENTS.md
- CLAUDE.md

## Purpose

The Agentic OS spine is the executable control plane for identity context,
memory recall, skill-system composition, guarded learning, audit trails, and
workflow provenance. It keeps the existing C-layer carousel, D-layer article,
B-layer pre-post, and wiki systems as the product, then makes their hidden
setup queryable and testable.

## Entry Points

- Context manifest: `config/agentic_context_manifest.json`
- Skill-system registry: `config/skill-systems.json`
- CLI: `scripts/agentic_os.py`
- Python package: `pipeline/agentic/`
- Wiki health gate: `pipeline/stages/wiki_health.py`

## Commands

```bash
venv/bin/python scripts/agentic_os.py context --render
venv/bin/python scripts/agentic_os.py skill-system carousel_jam
venv/bin/python scripts/agentic_os.py index-memory
venv/bin/python scripts/agentic_os.py search "golden theme visual proof"
venv/bin/python scripts/agentic_os.py recall "make this love story more cinematic"
venv/bin/python scripts/agentic_os.py health
```

The legacy aliases `context`, `system`, and `index` remain available. The
written-plan aliases `skill-system` and `index-memory` are supported so future
sessions can follow either surface.

## Workflow Integration

- C-layer Anthropic context loading now uses the budgeted context manifest.
- C-layer Codex-native and Anthropic manifests record the Agentic OS contract.
- D-layer article packages write `source-memory-brief.md` and an `agentic_os`
  manifest section when recall is available.
- B-layer pre-post prompts include the resolved `prepost_reel` skill system and
  a ranked recall bundle.
- Wiki health fails if the control-plane files disappear.

## Learning Boundary

Learning is proposal-only. The control plane may capture a learning event,
snapshot a target, and create a proposal, but it must not silently overwrite
skills, memory, or workflow contracts. A proposal needs deterministic evaluation
through `pipeline/agentic/skill_eval.py` before any human-approved change is
applied.

## Non-Goals

- No blind background push daemon.
- No self-grading skill marketplace.
- No raw identity images inside context packs.
- No replacement of Layer E, C, D, B, or the wiki.
