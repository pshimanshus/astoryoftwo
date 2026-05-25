# Carousel Quality Spine Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a deterministic review, audit, and wiki-learning spine around every Codex-native illustrated carousel package.

**Architecture:** Add a focused `pipeline/stages/carousel_quality.py` module that owns ledgers, reviewer reports, final audits, and wiki/memory updates. Wire it into `pipeline/stages/codex_native_carousel.py` after package creation and after asset rendering so final audit can inspect actual outputs.

**Tech Stack:** Python standard library, existing unittest suite, JSON/Markdown artifacts.

---

### Task 1: Add Failing Contract Tests

**Files:**
- Modify: `tests/test_illustration_carousel.py`

- [ ] Add a test that creates a Codex-native package and asserts `run-ledger.json`, `stage-reviews.json`, `final-audit.json`, and `wiki-update.md` exist.
- [ ] Assert `run-ledger.json` contains requirement IDs for desi storybook style, photo-rooted details, slide count, brandmark, negative prompt, and wiki enrichment.
- [ ] Assert `final-audit.json` reports a passing final gate for a no-render run with a skipped-render note.
- [ ] Assert `wiki/carousels/<slug>.md`, `wiki/index.md`, `memory/working.md`, and `memory/graph.json` are updated under a temporary workspace root.

### Task 2: Implement Quality Module

**Files:**
- Create: `pipeline/stages/carousel_quality.py`

- [ ] Add `QualityContext` dataclass with story, title, slug, today, output directory, image paths, slide count, package, manifest, render result, and workspace root.
- [ ] Add `build_run_ledger(context)` returning requirement IDs, stage map, source images, expected artifacts, and final gate placeholder.
- [ ] Add `build_stage_reviews(context, ledger)` returning deterministic reviewer reports.
- [ ] Add `build_final_audit(context, ledger, stage_reviews)` that checks required artifact existence and critical requirements.
- [ ] Add `write_quality_artifacts(context)` that writes ledger, reviews, audit, and wiki update.
- [ ] Add `update_wiki_memory(context, audit)` that creates `wiki/carousels/<slug>.md`, updates `wiki/index.md`, appends `memory/working.md`, and merges `memory/graph.json`.

### Task 3: Wire Native Builder

**Files:**
- Modify: `pipeline/stages/codex_native_carousel.py`

- [ ] Import `QualityContext` and `write_quality_artifacts`.
- [ ] After `image-generation.json` is written, call `write_quality_artifacts`.
- [ ] Pass workspace root derived from `output_root.parent.parent` when output root is `<workspace>/output/carousels`; otherwise use `output_root.parent` for temporary test roots.

### Task 4: Verify

**Files:**
- Test: `tests/test_illustration_carousel.py`

- [ ] Run the new tests and confirm they fail before implementation.
- [ ] Implement minimal code.
- [ ] Run `venv/bin/python -m unittest tests/test_illustration_carousel.py`.
- [ ] Inspect one generated temporary package structure through assertions, not manual hope.

### Self-Review

Coverage: The plan covers observer ledger, reviewer reports, final audit, wiki enrichment, memory enrichment, and tests. No placeholders remain. Types and paths are consistent with the existing Codex-native builder.
