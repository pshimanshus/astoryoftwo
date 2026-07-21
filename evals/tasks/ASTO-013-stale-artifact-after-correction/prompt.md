# Rebuild Stale Carousel Artifacts After Correction

## Context

A creator corrected a carousel route after the package had already produced
`slides.json`, `copy.json`, `post-copy-visual-room.json`, `visual-debate.json`,
`visual-plan-quality.json`, `identity-consistency-review.json`, `prompt-pack.json`,
`review.json`, `manifest.json`, and `image-generation.json`. The package still
contains old rejected phrases in some generation-facing files.

This mirrors a real project failure recorded in
`memory/semantic/engineering-workflow-preferences.md`: stale downstream
artifacts after a creator correction are a production bug. If stale copy or
old visual direction remains, the next image proof will be wrong even if the
new top-level copy looks correct.

## Task

Repair the workflow so a creator correction invalidates stale downstream
artifacts before image generation. Add or update deterministic checks that
scan for old route phrases across every generation-facing artifact and block
the package until all artifacts are rebuilt from the corrected source of truth.

## Acceptance Criteria

- Old rejected route phrases in prompt packs, visual plans, reviews, manifests,
  and image-generation state block generation.
- The package records a stale-string audit or equivalent evidence with the
  searched phrases and affected files.
- Once all artifacts agree with the corrected source, a valid package can
  proceed to proof or handoff.
- Focused carousel workflow/state tests pass.

## Constraints

Do not edit `AGENTS.md`. Do not generate or fake final images. Do not delete
creator-correction evidence to make the checker quiet. Keep the fix scoped to
package state, workflow doctor, tests, and relevant memory/eval surfaces.
