# Visual QA

Status: post-format draft illustrations created; not publishable.

## Checks

- Dimensions: PASS. All seven `final/slide-XX.png` files are `1080x1440`.
- Copy: PASS by visual inspection. Each slide has the intended handwritten text baked into the image.
- Brandmark: PASS by visual inspection. Each slide has a tiny `@a.storyof.two` brandmark in the top-right.
- Visual variety: PASS. Outfits, locations, and staging change across the sequence.
- Eye-lines: PASS. Before the payoff slide, Aachu and Zuv do not repeatedly look at each other.
- Slide 6 context: PASS. Uses the restaurant almost-meet setup with Aachu focused on food and Zuv entering.
- UI artifacts: PASS by visual inspection. No carousel arrows, page dots, browser chrome, or app UI kept in final slides.
- Face identity: NOT PASSED. No structured identity eval was run, no `identity-consistency-review.json` exists, and several slides show small/partial/back-facing faces that cannot be claimed as recognizable Aachu/Zuv final likeness.

## Notes

- OCR was not run; text was checked visually.
- Face identity was not evaluated against the identity bundle by a structured tool.
- `venv/bin/python scripts/agentic_os.py carousel-doctor output/carousels/2026-07-11/the-almosts-were-practicing` reports the package as blocked because required native `final-reels-stories/` outputs are missing.
- Native `1080x1920` story/reel companion slides were not generated in this pass.
- This folder contains a post-format draft illustration set, not a full publish closeout package.
