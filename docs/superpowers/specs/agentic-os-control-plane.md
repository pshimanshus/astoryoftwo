# Agentic OS Control Plane

last_updated: 2026-05-31
confidence: 0.88
sources:
- docs/superpowers/plans/creative-os-master-plan.md
- AGENTS.md
- config/rules/
- pipeline/agentic/checks/

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

## Canonical Rules Layer

Every constraint that drives generation lives in exactly one file under
`config/rules/`. Skill files, prompt templates, and context sections compose
rules via `{{rule:NAME}}` markers; `pipeline/agentic/rule_includes.py`
expands the markers against the canonical files. The context loader runs the
expander on every section before token estimation, so a rule edit propagates
immediately to every session.

Required rules in the default profile: palette, identity, on-image-text,
brandmark, voice, golden-theme, story-selling. brand-zone is optional and
applies only to sponsored carousels.

Safety net: `RequiredSectionTruncatedError` raises when a required section
that uses `{{rule:NAME}}` markers would be cut mid-content by the budget.
Silent truncation of constraint text is unsafe and the loader refuses it.

Known migration gap: existing `config/skills/*.md` files still inline rule
text. The activation plan's Task 9 migrates them to `{{rule:NAME}}`
includes. Until that lands, `config/rules/` is canonical at the context-pack
level but skill files carry their own copies.

## Deterministic Gates Layer

`pipeline/agentic/checks/` carries the runtime gates the workflow runner
uses to PASS / FAIL a slide on measurement rather than LLM opinion:

- `check_palette` — paper-region warm-ivory tolerance + yellow-band fraction.
  Calibrated against the 8 approved Observational Intimacy Premium slides on
  2026-05-31. Both axes must hold; FAIL reason carries the measured values.
- `check_ocr_text` — OCR vs. `slides.md` with fuzzy partial-ratio tolerance
  for handwritten variation. Degrades to STOP (soft skip) when easyocr is
  not installed; install with `venv/bin/pip install easyocr`.
- `check_image_size` — exact native pixel dimensions: 1080x1350 for
  post/carousel, 1080x1920 for Story/Reel, and 1080x1080 for explicit square.
  Rejects same-ratio/minimum-size variants instead of resizing them.
- `check_prompt_constraints` — compiled prompt contains 8 canonical
  fragments. Catches prompt-compile drift before generation. An upstream
  test (`tests/test_checks_prompt_constraints.py::
  test_required_fragments_are_present_in_rule_files`) guarantees every
  required fragment lives in some `config/rules/*.md` file.

Each gate returns a typed `WorkflowGate` from `pipeline/agentic/contracts.py`.

## Workflow Runner (planned — activation sprint)

The current control plane is read-only (context, registry, search, recall,
capture-learning, evaluate-learning, health). The activation plan adds an
executable runner that drives `skill-systems.json:carousel_jam` as a typed
state machine with pause-resume semantics, per-state agent invocation with
typed I/O, deterministic gates wired in next to LLM gates, and five
explicit human pauses (concept-lock, copy-lock, visual-plan-lock,
proof-approval, final-approval). Spec evolves as the runner lands; the
durable contract is in `docs/superpowers/plans/2026-05-31-agentic-os-
activation-sprint.md`.

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
