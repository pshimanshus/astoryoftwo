# Image Generation Blocker

status: SUPERSEDED_BY_CREATOR_CORRECTION

The creator rejected the metaphor after seeing the generated sequence. Stop
all generation, repair, packaging, and promotion for this route. See
`CREATOR-CORRECTION.md`.

The identity-referenced built-in generator was called twice for the locked
proof slide. Both attempts returned `1086x1448`, which is not an approved
carousel source size. The required source is native `1440x1920`, or already
exact `1080x1440`.

The two rejected proofs remain private under
`.internal/proof-candidates/`. They were not packaged or promoted as finals.
See `.internal/proof-dimension-rejection.json` for exact hashes and dimensions.

Prompt handoff:

- Instagram post prompts: `output/carousels/2026-07-30/the-museum-of-almost/codex-image-prompts/instagram-post`
- Paste-ready generator prompts: `.prompt.txt` files beside each `.md` handoff file.

Final images still required:

- `final/slide-01.png` through `slide-05.png` (Instagram post)

Rules:

- generate only the current-request formats listed above;
- generate every requested aspect ratio natively; do not derive one from another;
- use the watercolor-and-ink master prompt in each paste-ready `.prompt.txt`;
- use identity references as actual image inputs;
- preserve exact slide copy and `@a.storyof.two` inside the generated image;
- package generated sources with `scripts/package_generated_carousel.py`.

Proof gate:

- slide 05: `So she added today's unfinished page.`
- resume only in a generation path that can return an approved native size;
- do not crop, pad, stretch, or arbitrarily resize the rejected proofs.
