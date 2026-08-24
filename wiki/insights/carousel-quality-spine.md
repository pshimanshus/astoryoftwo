# Carousel Quality Spine

last_updated: 2026-05-31
confidence: 0.82
sources:
- docs/superpowers/specs/2026-05-10-carousel-quality-spine-design.md
- docs/superpowers/plans/creative-os-master-plan.md
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

The approved default visual style is now the Observational Intimacy Premium
watercolor-and-ink lock: warm ivory paper with visible grain, fine ink/pencil
linework, transparent watercolor blooms, muted vintage palette, tactile
clothing/props, upper-middle handwritten text, tiny bottom-right
`@a.storyof.two` brandmark, and Aachu/Zuv identity references anchoring faces,
expressions, posture, and wardrobe.

## Failure Memory

Runs should prefer `PASS_WITH_NOTES` over vague success when rendering is
skipped, local generation is partial, or any limitation needs to carry forward.
Critical misses become `NEEDS_FIXES`.

## Identity-Scale Learning

The 2026-05-31 Private Captions fresh run added a stricter identity gate:
height and body scale are part of likeness. Himanshu/Zuv is 5'8" and
Aanchal/Aachu is 5'6"; generated scenes must show only a slight two-inch
difference when both stand on the same plane. If faces or height drift, stop
batch generation, reject the proofs, and require one corrected reference-based
proof before continuing.
