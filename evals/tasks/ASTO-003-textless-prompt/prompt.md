# Issue: Textless Source-Art Prompt Escaped

## Context

A carousel package has approved slide copy, but an active image prompt asks for
clean source art, blank paper space, or typography to be added later. For
@a.storyof.two narrative slides, the exact ON-IMAGE TEXT must be generated into
the raster from the start.

## Task

Repair the prompt constraints and package doctor behavior so source-art or
text-later prompts block generation unless the active prompt is converted into
a text-bearing prompt.

## Acceptance Criteria

- Source-art directives fail with an actionable reason.
- Safe text-bearing prompts with exact slide text still pass.
- Carousel doctor reports no active textless prompt on repaired packages.
- Existing prompt-constraint tests remain meaningful.

## Constraints

Do not edit `AGENTS.md`. Do not weaken `config/rules/on-image-text.md`. Do not
mark a textless package publishable.
