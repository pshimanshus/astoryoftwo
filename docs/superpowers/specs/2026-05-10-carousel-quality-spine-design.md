# Carousel Quality Spine Design

## Goal

Add a reliability spine to the C-layer carousel pipeline so every `/story` run records what was expected, what was produced, what reviewers checked, and what the system should learn for the next run.

## Approved Approach

Keep the current desi storybook / photo-rooted carousel style as the default. Add a Jarvis-style observer, stage review reports, a final contract audit, and wiki/memory enrichment around the existing Codex-native package builder.

## Architecture

The native builder remains the entry point. A new quality module creates a requirements ledger from the story, source photos, generated slide plan, prompt pack, copy pack, and review data. It then emits deterministic reviewer reports for intake, story, arc, visual direction, prompts, copy, assets, wiki learning, and final audit.

The output package gains these artifacts:

- `run-ledger.json`: requirement IDs, source inputs, required files, stage statuses, and final gate.
- `stage-reviews.json`: reviewer findings for each stage.
- `final-audit.json`: PASS / PASS_WITH_NOTES / NEEDS_FIXES / BLOCKED contract result.
- `wiki-update.md`: run summary with learnings, failures, fixes, and links to generated artifacts.

The wiki is updated on every successful package write:

- `wiki/carousels/<slug>.md`: carousel-specific memory page.
- `wiki/index.md`: links the latest carousel page.
- `memory/working.md`: appends latest C-layer run status.
- `memory/graph.json`: records carousel entity, source images, and theme relationships.

## Review Contract

Every run must verify:

- slide count is exactly 4 or 5
- generated prompt slide count matches the slide plan
- each slide has copy, role, visual direction, emotion, CTA intent, and source image list
- prompt pack has shared style prompt, negative prompt, and one prompt per slide
- style prompt preserves desi storybook / photo-rooted direction
- negative prompt blocks photorealism, 3D rendering, generic stock couples, and quote-card layout
- brandmark is specified as `@a.storyof.two`, tiny, low-contrast, bottom-right
- final output files exist
- generated package links back into the wiki and memory system

## Failure Model

The system should not pretend a run is perfect. It can pass with notes when local rendering is skipped or unavailable, but it must mark missing required artifacts, invalid slide counts, absent prompt constraints, missing source images, or missing wiki updates as failures.

## Non-Goals

This change does not replace the current illustration style, add external API dependencies, or require real image generation to pass artifact creation. It strengthens package verification and learning around the existing workflow.
