# Issue: Format Snapback After Creator Correction

## Context

The creator first asked for a carousel, then corrected the request to one
specific canvas. The workflow still snapped back to repo defaults and planned
both 3:4 post output and 9:16 story output. That is wrong for corrected
single-format work.

## Task

Repair format inference so the latest explicit creator instruction wins over
default workflow assumptions. Keep the post-only default and the native gates
for any Story/Reel or square format the creator explicitly requests. Update the
seeded `request-state.json` plan to show the corrected output set after the
repair.

## Acceptance Criteria

- A corrected single-format request does not generate unrequested formats.
- The seeded request-state artifact records only the latest requested output.
- Ambiguous corrections ask for exact canvas instead of guessing.
- Normal post/carousel runs default to only native 1080x1440.
- Native 1080x1920 or 1080x1080 outputs are generated only when explicitly
  requested.
- Focused prompt compiler and workflow contract tests pass.

## Constraints

Do not edit `AGENTS.md`. Do not make square the global default. Do not restore
automatic multi-format derivatives. Do not remove native final gates for
formats that the creator actually requested.
