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
- A missing or corrupt file in any current-request format blocks publishable
  status.
- Missing visual QA or final audit blocks publishable status.
- A minimal post-only package passes with only 1080x1440 when that is the
  locked request; explicit Story/Reel or square requests require their own
  native files.
- Carousel state and workflow doctor tests pass.

## Constraints

Do not edit `AGENTS.md`. Do not create fake final media. Do not infer requested
formats from folders. Do not weaken the native dimensions of any locked format.
