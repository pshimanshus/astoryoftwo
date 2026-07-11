# Issue: Repeated Visual Plan Needs Shot Ladder

## Context

A carousel plan has warm copy, but every slide is the same medium two-shot in
the same room. If the text is hidden, the images are interchangeable. That
violates visual variety and scene-proof rules.

## Task

Repair the visual planning path so generation blocks until the storyboard has a
real shot ladder with varied camera distance, angle, action, props, setting
lane, and who is visible.

## Acceptance Criteria

- Repeated medium two-shot plans return REPAIR or BLOCK_GENERATION.
- Legitimate continuous scenes can pass when camera/action materially change.
- Visual plan quality records shot ladder evidence.
- Story-scene and illustration carousel tests pass.

## Constraints

Do not edit `AGENTS.md`. Do not lower the visual-variety threshold. Do not
approve quote-card visuals with characters added later.
