# Rejected Textless Source Prompt

status: REJECTED_HARD_FAIL
date: 2026-06-30

`square-proof-slide-04.prompt.txt` was moved out of the active
`codex-image-prompts/` path because it instructed generation of source art with
no text or brandmark, then asked for exact text to be added afterward.

That violates the current @a.storyof.two rule: every generated proof, concept,
carousel slide, or final raster must already contain the exact slide text and
the tiny top-right `@a.storyof.two` brandmark. If exact text cannot be rendered,
the package must remain blocked or retry with a text-bearing prompt.
