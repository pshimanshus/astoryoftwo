# Instagram carousel intelligence

This is the carousel-specific evidence surface for `@a.storyof.two`. It is
used at concept lock and keeps three claims separate:

1. **Official platform signals** — Meta's public explanations of ranking and
   recommendation systems:
   - https://transparency.meta.com/features/explaining-ranking/ig-feed/
   - https://transparency.meta.com/features/explaining-ranking/ig-feed-recommendations/
   - https://about.instagram.com/blog/announcements/instagram-ranking-explained
2. **Observed corpus patterns** — the verified local audit at
   `output/reports/2026-09-19-full-carousel-audit/`, covering 27 mapped sequences
   and 158 slide positions; source identity and mapping limits are recorded below.
3. **Hypotheses** — creative tests proposed from those observations.

## Saved sequence research

For the creator-requested depth of carousel analysis, start with
`memory/semantic/carousel-sequence-learnings.md`; the full archived close
reading is `wiki/insights/retrieved-carousel-pattern-analysis.md`, with every
mapped slide annotated in
`output/reports/2026-09-20-carousel-pattern-analysis/beat-notes.json`.
Analyse the actual hook, each swipe's new information, copy–image relationship,
conflict/mismatch, turn, payoff and whole-sequence completeness. Compare
contrasting examples and retain weaknesses, rather than returning general
relatability advice. These findings are research context, not new gates.

## Integrated use

After the first alive draft, retrieve one or two records with the public
`patterns` command and carry the selected mechanism into the brief's
`story_plan`, not into an image prompt as theory. `slides.json` then carries the
sequence mode, each swipe's `beat_delta`, and its explicit copy–image relation.
Use `sequence-check` to validate the handoff and its review fingerprint before
proof preparation. The final `visual-qa.json` must include the authored
whole-sequence review when this contract is enabled; individual frame QA cannot
substitute for transition and closure evidence.

The production contract supports intentional silent beats through
`copy_mode: wordless`. Empty copy without that lock remains invalid. The
`publication`, `insights` and `results` commands are research closeout tools:
they link an already published shortcode, retain dated native metric labels and
provenance, and write a descriptive result with limits and a next hypothesis.
They never publish, invent missing values, or promote a global creative rule.

The September 20 reinspection covers 158 mapped positions but 153 distinct
image hashes; some are local source counterparts. Three older seed mappings
are superseded by recovered pixels: `Dc5eniKic95` (husband alliance),
`DcRQEEjCSNo` (chores), and `DcG9gVzCfO7` (continuing commitment). The archive
preserves these limitations and distinguishes current inspection from saved
September 12 Insights. Read it before reusing the older prose as evidence.

## Interpretation and calibration

Meta does not publish a carousel-specific weighting table, ideal slide count,
or reach guarantee. This skill must not invent one. `Views`, `Viewers`,
`Shares`, `Saves`, `Profile visits`, and `Follows` remain separate native
labels. Reels and single-image posts are excluded from carousel calibration.

The concept-lock score is an internal creative readiness measure. It checks
addressability, visible scene proof, beat novelty, relationship motion,
payoff/reframe, send/save reason, and copy-visual cohesion. A score of 70/100
with minimum scene proof, relationship motion, and send/save scores is a
blocking editorial floor for new packages. It is not a prediction of
distribution and cannot support causal language when metric provenance,
age-band coverage, or direct visual evidence is incomplete.

Run the verified seed calibration with:

```bash
venv/bin/python scripts/carousel.py dry-run
```

The dry run writes `carousel-intelligence-dry-run.json` and
`carousel-intelligence-dry-run.md` beside the verified audit. Treat the gate
distribution as rubric calibration evidence, then revise thresholds only
through the creator feedback loop.

For a per-carousel calibration table with before/after gate classifications,
run:

```bash
venv/bin/python scripts/carousel.py calibrate
```

The calibration report records the historical audit coverage separately from
the slide files reproducible in the current workspace. Missing local slide
files are `data_gap` evidence and must never be silently counted as pixel
reviews.
