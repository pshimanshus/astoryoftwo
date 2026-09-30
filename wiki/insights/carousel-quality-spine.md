# Carousel Quality Spine

last_updated: 2026-09-04
confidence: 0.95
status: derived pointer
sources:
- config/skill-systems.json
- config/skills/carousel-jam-autopilot.md
- config/rules/visual-variety.md

## Current Operating Shape

The active carousel spine has exactly four gates: concept; exact copy + native
format; actual-pixel proof + creator approval; and final package QA. Internal
checks support those gates but do not create agent rooms, ledgers, scorecards,
or additional approval states.

The canonical workflow is registered under `carousel_jam` in
`config/skill-systems.json`. Its compact operating instructions live in
`config/skills/carousel-jam-runtime-context.md` and
`config/skills/carousel-jam-autopilot.md`.

## Illustration Quality Pointers

The active visual profile is Cinematic Observational Watercolor v1. This page
does not define it:

- `config/rules/palette.md` owns finish and palette;
- `config/rules/visual-variety.md` owns cinematic frame and sequence semantics;
- `config/carousel_style_contract.json` owns the single machine profile;
- `config/references/style-lock/cinematic-observational-watercolor-v1/` owns
  approved visual evidence and provenance;
- `config/rules/identity.md` owns real-photo identity and scale; and
- exact text, brandmark, and dimensions remain in their matching rule files.

## Historical Note

The 2026-05 quality-spine design used a Jarvis observer, run ledger, stage
reviews, wiki-update artifacts, and `PASS_WITH_NOTES`. Those are historical
provenance only and are not the current default production contract. Current
generation is fail-closed: an image that misses story meaning, cinematic depth,
entity/anatomy/spatial integrity, identity, exact text, brandmark, palette, or
requested native dimensions remains quarantined and cannot be promoted.
