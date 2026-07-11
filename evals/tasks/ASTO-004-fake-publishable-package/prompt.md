# Issue: Fake Publishable Carousel Package

## Context

A carousel package claims `publishable: true`, but the actual final assets are
missing, invalid, wrong size, or missing visual QA and final audit evidence.
The repo must trust artifacts, not optimistic JSON labels.

## Task

Repair carousel state or doctor logic so contradictory packages become blocked
or partial-final with precise issue codes. A real valid package should still be
able to become publishable.

## Acceptance Criteria

- Corrupt or missing native final PNGs block publishable status.
- Missing 9:16 finals, visual QA, or final audit block publishable status.
- Minimal valid packages with both native formats still pass.
- Carousel state and workflow doctor tests pass.

## Constraints

Do not edit `AGENTS.md`. Do not create fake final media. Do not remove native
1080x1440 or 1080x1920 requirements.
