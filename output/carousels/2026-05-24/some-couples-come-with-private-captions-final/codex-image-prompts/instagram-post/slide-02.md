# Codex Built-In Image Prompt - Slide 02 - Instagram post

Use the Codex built-in image generator. Do not use external API keys or external image API clients.

## How To Use This File

- This markdown file is the Codex handoff/checklist, not the exact text to paste into the image model.
- Attach/view the image references below, then paste only `output/carousels/2026-05-24/some-couples-come-with-private-captions-final/codex-image-prompts/instagram-post/slide-02.prompt.txt` into the image generator.
- After generation, package the returned image with `scripts/package_generated_carousel.py` or the proof-specific workflow.

## Native Output Contract

- Native output format: Instagram post
- Required aspect ratio: 4:5
- Required final file: `output/carousels/2026-05-24/some-couples-come-with-private-captions-final/final/slide-02.png`
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

- Dossier: output/carousels/2026-05-24/some-couples-come-with-private-captions-final/identity-dossier.json
- Preflight: output/carousels/2026-05-24/some-couples-come-with-private-captions-final/identity-generation-preflight.md

## Actual Image Inputs

Identity dossier references:
- output/carousels/2026-05-24/some-couples-come-with-private-captions-final/identity-face-contact-sheet.jpg

Identity references:
- identity_images/aachu_zuv.png
- identity_images/WhatsApp Image 2026-05-19 at 22.28.04.jpeg
- identity_images/WhatsApp Image 2026-05-16 at 18.29.46.jpeg

Story/source references:

Style references:
- output/carousels/2026-05-19/main-kar-lungi/final/slide-01.png
- output/carousels/2026-05-19/love-carries-the-heavier-half/final/slide-03.png
- output/carousels/2026-05-16/he-learned-her-subtitles/final/slide-02.png

## Exact Slide Copy

being dramatic
taking it seriously

## Prompt

Native output format: Instagram post. Generate a complete 4:5 vertical publishable carousel slide with all text and the tiny @a.storyof.two brandmark inside the image. Do not rely on cropping, padding, or resizing from another aspect ratio.

Use case: illustrated private-caption carousel. Asset type: complete publishable slide 2 of 8, generated separately as native 4:5 Instagram post and native 9:16 Reels/Stories. Scene: warm home doorway with a half-packed tote. Aachu wears an oversized kurta or soft home outfit, loose dark hair, expressive dramatic face, doing a tiny theatrical exit while her slippers are still inside. Zuv wears a simple dark tee or home shirt, holding the door and her tote like this is a real mission, calm but fully invested. Place the lowercase label 'being dramatic' near Aachu and 'taking it seriously' near Zuv. Labels must be readable, small, and not over faces or hands. The behavior should prove the joke before the viewer reads the labels. Warm paper texture, hand-drawn linework, matte colors, tiny @a.storyof.two bottom-right. No arrows, no him/her prefixes, no Friends/sitcom copy, no mean framing.

## Expected Output

- Save packaged final to `output/carousels/2026-05-24/some-couples-come-with-private-captions-final/final/slide-02.png`.
- Source provenance should point to the Codex generated image copied into `output/carousels/2026-05-24/some-couples-come-with-private-captions-final/final/model-native-source/instagram-post-slide-02.png`.
