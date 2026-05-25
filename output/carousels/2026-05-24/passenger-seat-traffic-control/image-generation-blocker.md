# Image Generation Blocker

status: HANDOFF_READY_IMAGES_PENDING
date: 2026-05-24

The carousel package is corrected and ready for Codex built-in image generation.
The generated prompt handoff exists at:

- `codex-image-prompts/instagram-post/slide-01.md` through `slide-07.md`
- `codex-image-prompts/reels-stories/slide-01.md` through `slide-07.md`

Final images are not claimed yet because native generated PNG sources have not
been produced and packaged into:

- `final/slide-01.png` through `slide-07.png`
- `final-reels-stories/slide-01.png` through `slide-07.png`

Generation requirements:

- load `identity-generation-preflight.md`;
- load/view `identity-face-contact-sheet.jpg`;
- use `identity_images/aachu_zuv.png` as an actual identity reference;
- generate separate native `4:5` and native `9:16` outputs for every slide;
- do not derive one aspect ratio from the other;
- preserve exact slide copy and `@a.storyof.two` brandmark inside the image;
- block unsafe driving, nagging-wife, helpless-husband, panic, anger, readable
  map UI, plate numbers, and private route details.

The proof-first slide should be slide 4:

```text
Her foot found the invisible brake.
```

This is the riskiest visual beat and must pass before full-batch generation.
