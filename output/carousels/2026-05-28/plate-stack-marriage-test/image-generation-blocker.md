# Image Generation Blocker

status: HANDOFF_READY_IMAGES_PENDING

Final PNGs are pending Codex image tool generation.

This package is ready for the Codex image tool. The repo never calls an
external image service or asks for image-generation credentials; Codex should
create the identity-referenced artwork in the agent session using these files.

Prompt handoff:

- Instagram post prompts: `output/carousels/2026-05-28/plate-stack-marriage-test/codex-image-prompts/instagram-post`
- Paste-ready generator prompts: `.prompt.txt` files beside each `.md` handoff file.

Final images still required:

- `final/slide-01.png` through `slide-07.png`
- `final-reels-stories/slide-01.png` through `slide-07.png`

Rules:

- generate separate native 4:5 and native 9:16 images;
- do not derive one aspect ratio from the other;
- use identity references as actual image inputs;
- preserve exact slide copy and `@a.storyof.two` inside the generated image;
- package generated sources with `scripts/package_generated_carousel.py`.

Proof-first recommendation:

- slide 06: `dono rakh do.`
- paste only this proof prompt after attaching references: `output/carousels/2026-05-28/plate-stack-marriage-test/codex-image-prompts/instagram-post/slide-06.prompt.txt`
