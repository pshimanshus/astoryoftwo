# Carousel Pipeline Structure Audit

date: 2026-05-16
scope: C-layer `/story` carousel pipeline, style memory, agent contracts, generated-output gates
status: superseded_by_model_native_pipeline

---

## Executive Summary

The folder had the right high-level idea but the wrong enforcement layer.
The earlier C-layer could create a storyboard, prompt pack, wiki updates, and
local stylized previews, but it did not force final generated images, recurring
Aachu/Zuv identity references, local typography, or storyboard-to-image parity.

The current corrected direction is:

> A soft illustrated archive of Aachu and Zuv's love, chaos, culture, and tiny rituals.

Update: the default final-image path is now model-native. The image model must
generate the illustration, exact handwritten-style copy, brandmark, faces,
outfits, and composition together in `final/slide-XX.png`. Local overlays under
`final-with-text/` are legacy fallback only.

That North Star now lives in `config/carousel_style_contract.json` and is
loaded by `pipeline/stages/carousel_contract.py`.

## Canonical Structure

### Identity And Style

- `config/carousel_style_contract.json`
  - Canonical Product Unshipped-like style contract.
  - Owns Aachu/Zuv character bible, negative prompt, model-native typography strategy,
    brandmark, content lanes, and North Star.
- `pipeline/stages/carousel_contract.py`
  - Loads and validates the canonical style contract.
  - Builds the Aachu/Zuv character bible text for prompt packs.
- `identity_images/`
  - Expected workspace folder for stable Aachu/Zuv identity references.
  - `pipeline/stages/codex_native_carousel.py` discovers images here when
    `--identity-image` is not supplied.

### Story And Package Generation

- `scripts/create_illustration_carousel.py`
  - Current top-level CLI for `/story`.
  - Accepts `--identity-image` and passes identity references into Codex-native
    and legacy Anthropic paths.
- `pipeline/stages/codex_native_carousel.py`
  - Current default no-API package builder.
  - Classifies content lanes such as Tiny Rituals, Chaotic Wife Calm Husband,
    Kashmiri Wife x Non-Kashmiri Husband, Wedding Origin Story, and Soft Love
    Notes.
  - For the anklet/shoes example, now routes to Tiny Rituals instead of the old
    generic travel arc.
- `pipeline/stages/c1_illustration_carousel.py`
  - Legacy Anthropic-backed C1-C6 runner.
  - Now accepts identity references in manifest, brief text, and image blocks.

### Quality Spine

- `pipeline/stages/carousel_quality.py`
  - Owns run ledger, stage reviews, final audit, wiki update, visual QA, wiki,
    working memory, and graph updates.
  - Now fails final audit when:
    - identity references are missing,
    - final generated images are missing,
    - final images exist without visual QA,
    - `visual-qa.md` has failed checks.
- `visual-qa.md`
  - Required per-carousel manual/agent review checklist for storyboard match,
    Aachu face, Zuv face, style, typography, and final output existence.

### Final Image Packaging

- `scripts/package_generated_carousel.py`
  - Copies generated images into `output/carousels/YYYY-MM-DD/<slug>/final/`.
  - Writes `final-images.json`.
- `scripts/render_carousel_text_overlays.py`
  - Legacy fallback only for deterministic local text overlays.
  - Writes `final-with-text/slide-XX.png` and `text-overlay.json`.

## Current Folder Review

### Root

- `AGENTS.md`: updated to describe stricter `/story` contract, identity refs,
  final images, local overlays, and visual QA.
- `CLAUDE.md`: retained platform guidance; replaced visible Apify key-like
  value with a placeholder.
- `.env`: present locally and should remain uncommitted/unread in normal audits.
- `.DS_Store`: present in several folders; safe to ignore, not part of product
  memory.

### `.claude/commands/`

- `.claude/commands/story.md`: updated to require style contract, identity
  refs, clean art, local typography, final-image packaging, and final audit
  failure until QA is present.

### `agents/`

The agent files are useful but mixed between older generic C-layer language and
newer Aachu/Zuv-specific requirements.

- Keep: C1-C7 decomposition, observer, stage reviewer, final auditor.
- Tighten next: C3 visual director, C4 prompt engineer, C6 reviewer, and final
  auditor should explicitly reference `config/carousel_style_contract.json`.
- Risk: older phrases like “desi storybook / photo-rooted” are acceptable only
  when nested under the Product Unshipped-like Aachu/Zuv style contract.

### `config/`

- `config/carousel_style_contract.json`: canonical source for carousel visuals.
- `config/voice.md`: still describes the broader channel; useful but more
  generic than the carousel North Star.
- `config/skills/illustration-carousel-framework.md`: updated to reference the
  canonical contract and final-output gates.
- `config/skills/*`: B-layer/pre-post skills remain valid and separate.

### `pipeline/stages/`

- `codex_native_carousel.py`: active default C-layer builder.
- `carousel_contract.py`: new style contract loader.
- `carousel_quality.py`: active quality/audit/memory writer.
- `c1_illustration_carousel.py`: legacy Anthropic path; identity-aware now.
- `b1_prepost.py`: separate B-layer pipeline, not part of carousel fixes.

### `scripts/`

- Canonical active scripts:
  - `create_illustration_carousel.py`
  - `package_generated_carousel.py`
  - `render_carousel_text_overlays.py`
- Legacy or one-off scripts:
  - `create_star_proposal_carousel.py`
  - `package_star_proposal_generated_carousel.py`
  - `render_first_date_ladakh_carousel.py`
  - `create_he_didnt_marry_calm_carousel.py`
- Recommendation: keep one-off scripts as historical experiments, but mark them
  as non-canonical or move to `scripts/legacy/` in a later cleanup.

### `tests/`

- `tests/test_illustration_carousel.py`: now covers style contract, CLI identity
  references, identity discovery, Tiny Rituals routing, storyboard/prompt
  consistency, clean-art prompts, generated-image packaging, overlay manifest,
  final-audit failure without final images, and legacy identity manifest.

### `docs/`

- `docs/superpowers/plans/2026-05-16-carousel-generation-loop-fix.md`:
  full implementation plan.
- `docs/superpowers/plans/2026-05-16-carousel-generation-loop-remaining-fixes.md`:
  running checklist that was partly completed during implementation.
- `docs/audits/2026-05-16-carousel-pipeline-structure-audit.md`:
  this structure and health audit.

### `wiki/` And `memory/`

- `wiki/index.md`, `wiki/carousels/*`, `memory/working.md`, and
  `memory/graph.json` are updated by the quality spine.
- Followup: old carousel wiki pages created before the stricter audit may need
  re-audit so stale `PASS_WITH_NOTES` statuses do not imply final readiness.

### `output/`

- `output/carousels/2026-05-16/love-kept-the-same-posture/` is now stale under
  the stricter rules unless it has:
  - identity references in `manifest.json`,
  - `final/slide-XX.png`,
  - `final-with-text/slide-XX.png` when text is applied,
  - `final-images.json`,
  - `text-overlay.json`,
  - `visual-qa.md`,
  - a fresh `final-audit.json`.

## Non-Generic Memory That Must Stay

- Aachu/Zuv North Star.
- Aachu as spark, Zuv as steady flame.
- Product Unshipped-like soft flat illustration, not generic desi stock art.
- Model-native handwritten copy and brandmark, not default local overlays.
- Identity image required for face consistency.
- Content lanes:
  - Wedding Origin Story
  - Kashmiri Wife x Non-Kashmiri Husband
  - Chaotic Wife, Calm Husband
  - Soft Love Notes
  - Tiny Rituals
  - Himanshu POV
  - Aachu POV

## Health Gates Going Forward

Every `/story` run should be considered incomplete until:

1. `manifest.json` has `identity_references`.
2. `prompt-pack.json` has `identity_reference_images`, `character_bible`, and
   clean-art prompts with no “Text overlay verbatim” instruction.
3. `slides.json`, `prompt-pack.json`, and `storyboard.md` share the same slide
   copy from one source of truth.
4. `final/slide-XX.png` files exist for every slide.
5. `final-images.json` records `generation_mode=model_native_publishable`.
6. `visual-qa.md` has no failed checks.
7. `final-audit.json` is not `PASS` until image, identity, style, typography,
   and storyboard checks are satisfied.

## Remaining Cleanup

- Re-audit `love-kept-the-same-posture` under the new gates.
- Move one-off renderer scripts into `scripts/legacy/` or annotate them as
  non-canonical.
- Update C-layer agent markdown files to explicitly reference
  `config/carousel_style_contract.json`.
- Add a small README in `identity_images/` once the canonical Aachu/Zuv face
  reference is stored there.
