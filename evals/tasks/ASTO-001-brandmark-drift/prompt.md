# Issue: Brandmark Placement Drift

## Context

The root contract says every final @a.storyof.two illustration uses a tiny
`@a.storyof.two` brandmark in the top-right corner. A downstream instruction
surface has drifted and now tells prompts or checks to place the brandmark in
the bottom-right corner.

## Task

Repair the dependent surfaces so the active rule, prompt, checker, and test
layers all follow the top-right placement. Treat `AGENTS.md` as source truth.

## Acceptance Criteria

- Active brandmark instructions use top-right placement.
- Negative examples may mention wrong placement only as forbidden behavior.
- Prompt-constraint and instruction-surface tests pass.
- No unrelated carousel, memory, or generated media files are changed.

## Constraints

Do not edit `AGENTS.md`. Do not weaken tests. Do not remove the brandmark
requirement to avoid the placement conflict.
