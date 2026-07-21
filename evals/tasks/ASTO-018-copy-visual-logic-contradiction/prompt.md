# Block Copy-Visual Logic Contradictions

## Context

A slide passes style and identity, but the scene contradicts the approved
copy. Example patterns from repo memory: copy says "your socks on before your
pants" while the image already shows pants; a real roti-bite scene requires
Zuv looking at his father and not holding/offering the bite; visual symbols
carry meaning that the scene itself does not prove.

## Task

Strengthen visual planning and QA so exact slide copy must be proven by the
visible action, object state, clothing state, gaze, and cause/effect logic.
Attractive art, correct dimensions, and identity match cannot override broken
scene logic.

## Acceptance Criteria

- Each slide visual plan records the copy claim and the visible evidence that
  proves it.
- Visual QA returns REPAIR/STOP when clothing, object state, gaze, or action
  contradicts the copy.
- Approved copy is not rewritten to fit a wrong image unless the creator
  explicitly reopens copy.
- Focused visual/story tests pass.

## Constraints

Do not edit `AGENTS.md`. Do not generate final media. Do not weaken identity
or style gates. This task adds a scene-logic gate; it does not replace existing
text, brandmark, dimension, identity, or visual-variety checks.
