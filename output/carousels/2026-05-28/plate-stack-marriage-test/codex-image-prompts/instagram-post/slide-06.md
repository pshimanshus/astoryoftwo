# Codex Built-In Image Prompt - Slide 06 - Instagram post

Use the Codex image tool. Do not use external credentials or external image clients.

## How To Use This File

- This markdown file is the Codex handoff/checklist, not the exact text to paste into the image model.
- Attach/view the image references below, then paste only `output/carousels/2026-05-28/plate-stack-marriage-test/codex-image-prompts/instagram-post/slide-06.prompt.txt` into the image generator.
- After generation, package the returned image with `scripts/package_generated_carousel.py` or the proof-specific workflow.

## Native Output Contract

- Native output format: Instagram post
- Required aspect ratio: 4:5
- Required final file: `output/carousels/2026-05-28/plate-stack-marriage-test/final/slide-06.png`
- Each slide must have two separate native generated sources: one 4:5 Instagram post image and one 9:16 Reels/Stories image. Reels/Stories output must never be derived by resizing, cropping, or padding the Instagram post image.
- Generate this format as its own artwork. Do not create it by resizing another generated slide.

## Hard Gate

- Before any slide generation, read `identity-generation-preflight.md` and load/view `identity-face-contact-sheet.jpg`.
- Preserve the carousel story-director spine embedded in `prompt-pack.json`: hook, setup, proof, bridge, active Zuv role, earned ending, and send/save reason.
- Before calling image generation, load/view every identity reference listed below so they are actual image inputs in the Codex context.
- Use the selected identity images as face, hair, expression, body proportion, posture, and relationship-energy references.
- Do not accept generic Aachu/Zuv faces.
- Keep the exact slide copy and tiny `@a.storyof.two` brandmark inside the generated image.

## Identity Dossier

- Dossier: output/carousels/2026-05-28/plate-stack-marriage-test/identity-dossier.json
- Preflight: output/carousels/2026-05-28/plate-stack-marriage-test/identity-generation-preflight.md

## Actual Image Inputs

Identity dossier references:
- output/carousels/2026-05-28/plate-stack-marriage-test/identity-face-contact-sheet.jpg

Identity references:
- identity_images/aachu_zuv.png

Story/source references:
- output/carousels/2026-05-28/plate-stack-marriage-test/proof/slide-06-proof-v5-story-repair.png
- output/carousels/2026-05-28/plate-stack-marriage-test/proof/slide-06-proof-v4-identity-4x5.png

Style references:
- output/carousels/2026-05-19/main-kar-lungi/final/slide-01.png
- output/carousels/2026-05-28/plate-stack-marriage-test/proof/slide-06-proof-v4-identity-4x5.png

## Exact Slide Copy

dono rakh do.

## Prompt

Native output format: Instagram post. Generate a complete 4:5 vertical publishable carousel slide with all text and the tiny @a.storyof.two brandmark inside the image. Do not rely on cropping, padding, or resizing from another aspect ratio.

Use case: illustration-story. Asset type: complete publishable Instagram carousel proof slide. Slide 6 of 7. Exact text: `dono rakh do.` as one tiny handwritten speech bubble near Aachu. Scene: close-up on hands and stacked plates with both faces partly visible; Aachu calmly stacks her own plate on top of Zuv's plate and gives or pushes the stack back into Zuv's hands while one hand reaches toward or returns to her phone; Zuv looks lightly outplayed, not humiliated or heroic. Identity continuity lock: use identity_images/aachu_zuv.png as actual visual reference before everything; preserve Aachu's long dark hair, expressive warm Indian face, and Zuv's dark wavy hair, beard/stubble, warm rounded Indian face. Style: match Main Kar Lungi hand-drawn warm paper and proof v4's 4:5 spacing; use proof v5 only for corrected plate-stack/phone action. Add tiny @a.storyof.two bottom-right. No other words.

## Expected Output

- Save packaged final to `output/carousels/2026-05-28/plate-stack-marriage-test/final/slide-06.png`.
- Source provenance should point to the Codex generated image copied into `output/carousels/2026-05-28/plate-stack-marriage-test/final/model-native-source/instagram-post-slide-06.png`.
