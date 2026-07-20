# Image Generation Blocker

status: PROOF_PASS_FINAL_EXPORTS_PENDING

Codex built-in image generation has produced a non-final proof set for the
approved Zuv POV direction. The proof set is visually usable for review, but it
is not publishable because exact native final dimensions are still missing.

Prompt handoff:

- Instagram post prompts: `output/carousels/2026-07-12/after-one-hour-with-you-zuv-pov/codex-image-prompts/instagram-post`
- Reels/Stories prompts: `output/carousels/2026-07-12/after-one-hour-with-you-zuv-pov/codex-image-prompts/reels-stories`
- Paste-ready generator prompts: `.prompt.txt` files beside each `.md` handoff file.

Generated proof outputs:

- 3:4 proof deck:
  `output/carousels/2026-07-12/after-one-hour-with-you-zuv-pov/non-final-proofs/instagram-post/slide-01.png`
  through `slide-07.png`
- 3:4 proof contact sheet:
  `output/carousels/2026-07-12/after-one-hour-with-you-zuv-pov/non-final-proofs/contact-sheet-instagram-post.png`
- 9:16 companion proof test:
  `output/carousels/2026-07-12/after-one-hour-with-you-zuv-pov/non-final-proofs/reels-stories/slide-01.png`
- Structured proof manifest:
  `output/carousels/2026-07-12/after-one-hour-with-you-zuv-pov/proof-generation.json`
- Structured proof QA:
  `output/carousels/2026-07-12/after-one-hour-with-you-zuv-pov/visual-qa.json`

Final images still required:

- `final/slide-01.png` through `slide-07.png`
- `final-reels-stories/slide-01.png` through `slide-07.png`

Rules:

- generate separate native 3:4 and native 9:16 images;
- do not derive one aspect ratio from the other;
- use the watercolor-and-ink master prompt in each paste-ready `.prompt.txt`;
- use identity references as actual image inputs;
- preserve exact slide copy and `@a.storyof.two` inside the generated image;
- package generated sources with `scripts/package_generated_carousel.py`.

Known final blockers:

- Instagram post proof outputs are `1086x1448`, not exact `1080x1440`.
- The one Reels/Stories proof test is `941x1672`, not exact `1080x1920`.
- `final/` and `final-reels-stories/` do not yet contain publishable final PNGs.
