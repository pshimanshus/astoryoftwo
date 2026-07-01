# Agentic Pipeline Dedupe Review

Date: 2026-06-30

Status: first cleanup batch executed after review.

Scope reviewed:

- `pipeline/agentic/`
- `pipeline/layer_e/`
- `pipeline/stages/`
- `scripts/`
- `scripts/legacy/`
- `tests/`
- `Makefile`
- `config/skill-systems.json`
- `AGENTS.md`
- repo-scoped skills under `.agents/skills/`
- prior audit: `docs/audits/2026-05-16-carousel-pipeline-structure-audit.md`

## Executive Decision

The Agentic OS control plane is not the main duplication problem. It has a clear active shape:

- `scripts/agentic_os.py` is the unified CLI for context, registry, memory search/recall, learning proposals, skill usage, carousel doctor, and health.
- `pipeline/agentic/` owns reusable control-plane primitives and checks.
- `pipeline/layer_e/` owns the story-selling council and is actively integrated into carousel, article, and pre-post workflows.
- `pipeline/stages/` owns concrete workflow builders and package writers.

The real dedupe targets are:

1. root-level one-off carousel scripts that bypass the canonical C-layer path;
2. final-image validation logic spread across multiple modules;
3. a huge mixed carousel test file that hides ownership;
4. legacy/active C-layer artifact writing overlap;
5. unprotected or stale utility scripts;
6. an empty test file that gives a false sense of coverage.

Do not delete generated/corpus/reference files as part of this cleanup. The current worktree already contains many unrelated deletions and output changes.

## Keep As Active

These scripts are required by Make, AGENTS, skill systems, tests, or current workflow docs:

- `scripts/agentic_os.py`
- `scripts/analyze_prepost.py`
- `scripts/autopublish.py`
- `scripts/carousel_doctor.py`
- `scripts/create_illustration_carousel.py`
- `scripts/create_substack_article_package.py`
- `scripts/daily_creator_brief.py`
- `scripts/jam_today.py`
- `scripts/package_generated_carousel.py`
- `scripts/render_carousel_text_overlays.py`
- `scripts/run_content_health.py`
- `scripts/wiki_health.py`

These are also active, but are subsystem utilities rather than daily user commands:

- `scripts/analyze_story_canon.py`
- `scripts/build_romance_story_selling_skill.py`
- `scripts/build_story_source_register.py`
- `scripts/ingest_story_canon.py`
- `scripts/story_canon_policy.py`
- `scripts/backfill_layer_e_artifacts.py`
- `scripts/scrape_instagram.py`
- `scripts/start_agentic_session.py`

`scripts/build_identity_dossier.py` should stay only if it gets a CLI smoke test. The underlying module `pipeline/stages/identity_dossier.py` is active, but the script wrapper currently has no direct protection.

## Remove Or Quarantine

### Root One-Off Carousel Scripts

These should not remain in root `scripts/`:

- `scripts/create_star_proposal_carousel.py`
- `scripts/package_star_proposal_generated_carousel.py`

Evidence:

- They have only two external references each: the permissive test allowlist and the old 2026-05-16 audit.
- `scripts/create_star_proposal_carousel.py` hardcodes transient private Apple Photos temp paths and a single `output/carousels/2026-05-09/anchal-under-the-stars` destination.
- `scripts/package_star_proposal_generated_carousel.py` hardcodes a generated image directory and only packages one historical proposal deck.
- `config/carousel_style_contract.json` already says the approved path is `scripts/create_illustration_carousel.py` and one-off renderers are not allowed unless explicitly approved as legacy fixtures.

Decision:

- Moved to `scripts/legacy/` after confirming they were non-canonical root scripts.
- Updated `tests/test_illustration_carousel.py::test_no_uncontracted_one_off_carousel_generator_scripts` so the root allowlist is only:
  - `carousel_doctor.py`
  - `create_illustration_carousel.py`
  - `package_generated_carousel.py`
  - `render_carousel_text_overlays.py`
- Add a small assertion that the star proposal scripts, if kept, live under `scripts/legacy/`.

### Stale Deep Post Analysis Script

`scripts/deep_post_analysis.py` should be moved to `scripts/legacy/` or removed.

Evidence:

- It has no current external references.
- It depends on `ANTHROPIC_API_KEY`.
- It is tied to `corpus/posts/2026-05-09-posts.json` and `output/reports/2026-05-09-deep-post-analysis.md`.
- Current pre-post and analysis routes go through `scripts/analyze_prepost.py`, `scripts/scrape_instagram.py`, and the Agentic OS/skill surfaces.

Decision:

- Quarantined as `scripts/legacy/deep_post_analysis.py` for historical reproducibility.

### Empty Test File

`tests/test_identity_dossier.py` is empty.

Decision:

- Populated with real tests for `pipeline/stages/identity_dossier.py`, because identity dossier generation is now part of `create_codex_native_carousel()`.

Minimum useful tests:

- readable image inventory excludes `_identity_dossier`;
- selected images are preserved in `selected_generation_options`;
- `build_identity_dossier_artifacts()` writes `identity-dossier.json`, `identity-generation-preflight.md`, and `identity-face-contact-sheet.jpg`;
- no identity images returns an explicit non-ready status without crashing.

## Dedupe By Refactor

### Final Asset Validation

Current ownership is split:

- `pipeline/agentic/checks/final_assets.py` validates readable final assets and native dimensions before publishable state is trusted.
- `pipeline/agentic/checks/image_size.py` validates exact dimensions for individual gate checks.
- `pipeline/stages/carousel_quality.py::final_image_gate()` validates `final-images.json`, native outputs, source provenance, missing files, and final audit evidence.
- `pipeline/agentic/workflow_doctor.py` checks contradictions and missing folders before state derivation.

This duplication is understandable historically, but it should converge.

Decision:

- Keep `workflow_doctor.py` as the contradiction inspector.
- Keep `carousel_state.py` as the state summarizer.
- Make `pipeline/agentic/checks/final_assets.py` the shared low-level final asset contract.
- Refactor `carousel_quality.final_image_gate()` to call the shared final-asset validator for readability and dimensions, while keeping its existing manifest/provenance checks.
- Optionally make `check_image_size()` reuse the same dimension constants.

Do not collapse doctor/state/final-audit into one module. They answer different questions:

- doctor: "Is this package internally contradictory?"
- final assets: "Are final files real, readable, and native-sized?"
- final audit: "Does the package satisfy publish requirements?"
- state: "What should the next action be?"

### Legacy Anthropic C1 Vs Codex-Native C-Layer

Current overlap:

- `pipeline/stages/c1_illustration_carousel.py` contains legacy Anthropic agent orchestration plus manifest/package writers.
- `pipeline/stages/codex_native_carousel.py` is the active no-API builder.
- `pipeline/stages/carousel_package_writer.py` is the active Codex-native artifact writer.
- `scripts/create_illustration_carousel.py` still exposes `--mode anthropic`.

Decision:

- Keep Anthropic mode only as a legacy adapter while tests still cover manifest compatibility and package validation.
- Stop adding new rules, quality artifacts, and package structure to the legacy writer.
- Move shared constants such as artifact contract, slide count bounds, and slug/slide validation into a small neutral module only if a future change touches both paths.
- New work should target `codex_native_carousel.py` and `carousel_package_writer.py`.

### Carousel Lane Registry

`pipeline/stages/carousel_lanes.py` is 4,475 lines and contains many repeated patterns:

- `is_*_story()` classifiers;
- `build_*_slides()` functions;
- `build_*_concept_selection()` functions;
- large exact copy/visual regression content.

Decision:

- Do not rewrite this file during script/test cleanup.
- It should be converted later to a data-driven lane registry:
  - lane id;
  - classifier tokens/predicate;
  - slide template builder;
  - concept-selection fixture;
  - expected content-lane contract.
- Move one lane at a time and keep story-lane regression tests green after each move.

## Tests: Required Or Not

Required and active:

- `tests/test_agentic_context_loader.py`
- `tests/test_context_loader_truncation.py`
- `tests/test_agentic_skill_registry.py`
- `tests/test_agentic_workflow_integration.py`
- `tests/test_agentic_learning_eval_cli.py`
- `tests/test_workflow_state.py`
- `tests/test_carousel_state_contract.py`
- `tests/test_carousel_workflow_doctor.py`
- `tests/test_carousel_doctor_cli.py`
- `tests/test_carousel_generation_state.py`
- `tests/test_carousel_prompt_compiler.py`
- `tests/test_checks_image_size.py`
- `tests/test_checks_ocr_text.py`
- `tests/test_checks_palette.py`
- `tests/test_checks_prompt_constraints.py`
- `tests/test_layer_e_engine.py`
- `tests/test_layer_e_workflow_integration.py`
- `tests/test_layer_e_backfill.py`
- `tests/test_wiki_health.py`
- `tests/test_autopublish.py`
- `tests/test_ai_command_center.py`
- `tests/test_creator_workflow_contract.py`
- `tests/test_codex_project_surfaces.py`
- `tests/test_instruction_surface_contract.py`

Keep these because they protect current command surfaces, closeout gates, rule/context surfaces, and package state transitions.

Needs split, not deletion:

- `tests/test_illustration_carousel.py`

Use `docs/superpowers/plans/2026-06-30-test-illustration-carousel-split.md`. The tests are mostly required, but the file is not. Split by workflow ownership.

Needs action:

- `tests/test_identity_dossier.py`

Populate or remove. Preferred is populate.

## Implementation Order

1. Quarantine root one-off carousel scripts:
   - move `scripts/create_star_proposal_carousel.py` to `scripts/legacy/create_star_proposal_carousel.py`;
   - move `scripts/package_star_proposal_generated_carousel.py` to `scripts/legacy/package_star_proposal_generated_carousel.py`;
   - update the root-script allowlist test.

2. Quarantine or remove `scripts/deep_post_analysis.py`.

3. Populate `tests/test_identity_dossier.py` with real identity dossier coverage.

4. Split `tests/test_illustration_carousel.py` using the saved split plan.

5. Refactor final asset validation:
   - keep `workflow_doctor`, `carousel_state`, and `carousel_quality` separate;
   - reuse `validate_publishable_final_assets()` inside the final audit gate for readability and dimension evidence.

6. Add a small script-surface contract test:
   - active command-center scripts must be in Make or `config/skill-systems.json`;
   - root `scripts/*carousel*.py` must not include one-off historical decks;
   - legacy scripts must not be imported by active workflow code.

7. Leave `carousel_lanes.py` for a later lane-registry migration, after the tests are split.

## Do Not Deduplicate

Do not merge these just because names overlap:

- `scripts/wiki_health.py` and `scripts/run_content_health.py`
  - one is the raw CLI wrapper; the other is the safe command-center default.
- `scripts/carousel_doctor.py` and `scripts/agentic_os.py carousel-doctor`
  - one is a focused CLI, the other is the unified Agentic OS surface.
- `pipeline/agentic/workflow_doctor.py` and `pipeline/agentic/carousel_state.py`
  - doctor finds contradictions; state derives the next action.
- `pipeline/layer_e/` and `config/skills/romance-story-selling-engine.md`
  - one is executable deterministic logic; the other is the human-readable skill/rule surface.
- prompt constraint, OCR, palette, image-size checks
  - these are separate gates with separate failure modes.

## Validation Commands

After the first cleanup batch:

```bash
venv/bin/python -m pytest \
  tests/test_illustration_carousel.py::IllustrationCarouselTests::test_no_uncontracted_one_off_carousel_generator_scripts \
  tests/test_ai_command_center.py \
  tests/test_carousel_doctor_cli.py \
  tests/test_layer_e_backfill.py \
  tests/test_agentic_workflow_integration.py \
  -q
```

After test split:

```bash
venv/bin/python -m pytest \
  tests/test_illustration_carousel.py \
  tests/test_carousel_state_contract.py \
  tests/test_carousel_workflow_doctor.py \
  tests/test_carousel_prompt_compiler.py \
  tests/test_checks_image_size.py \
  tests/test_checks_prompt_constraints.py \
  -q
```

After final-asset refactor:

```bash
venv/bin/python -m pytest \
  tests/test_carousel_state_contract.py \
  tests/test_carousel_workflow_doctor.py \
  tests/test_checks_image_size.py \
  tests/test_illustration_carousel.py::IllustrationCarouselTests::test_package_codex_builtin_outputs_writes_model_native_manifest \
  tests/test_illustration_carousel.py::IllustrationCarouselTests::test_final_audit_rejects_local_placeholder_final_images \
  tests/test_illustration_carousel.py::IllustrationCarouselTests::test_final_audit_accepts_identity_only_generated_carousel \
  -q
```

Always finish with:

```bash
venv/bin/python scripts/agentic_os.py health
```
