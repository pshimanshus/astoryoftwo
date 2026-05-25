# Carousel Quality Spine

last_updated: 2026-05-10
confidence: 0.7
sources:
- docs/superpowers/specs/2026-05-10-carousel-quality-spine-design.md
- docs/superpowers/plans/2026-05-10-carousel-quality-spine.md
- pipeline/stages/carousel_quality.py

---

## Insight

The C-layer carousel workflow needs a review spine around the creative agents:
Jarvis observes requirements, stage reviewers compare expected vs actual output,
and a final auditor checks whether the package is ready or needs fixes.

## Operating Rule

Every Codex-native carousel package should write:

- `run-ledger.json`
- `stage-reviews.json`
- `final-audit.json`
- `wiki-update.md`

The package should also add a carousel page to `wiki/carousels/`, link it from
`wiki/index.md`, append `memory/working.md`, and update `memory/graph.json`.

## Creative Memory

The approved default visual style remains desi storybook / photo-rooted
illustration: soft hand-drawn, imperfect black outlines, matte muted colors,
large whitespace, and real photo details preserved before decorative elements.

## Failure Memory

Runs should prefer `PASS_WITH_NOTES` over vague success when rendering is
skipped, local generation is partial, or any limitation needs to carry forward.
Critical misses become `NEEDS_FIXES`.
