# Codex Built-In Image Prompt - Slide 01 - Reels/Stories

Use the Codex built-in image generator. Do not use external API keys or external image API clients.

## How To Use This File

- This markdown file is the Codex handoff/checklist, not the exact text to paste into the image model.
- Attach/view the image references below, then paste only `output/carousels/2026-05-24/some-couples-come-with-private-captions-final/codex-image-prompts/reels-stories/slide-01.prompt.txt` into the image generator.
- After generation, package the returned image with `scripts/package_generated_carousel.py` or the proof-specific workflow.

## Native Output Contract

- Native output format: Reels/Stories
- Required aspect ratio: 9:16
- Required final file: `output/carousels/2026-05-24/some-couples-come-with-private-captions-final/final-reels-stories/slide-01.png`
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

some couples come with
private captions

## Prompt

Native output format: Reels/Stories. Generate a complete 9:16 vertical publishable story slide with all text and the tiny @a.storyof.two brandmark inside the image. Reframe the scene for the taller canvas; do not stretch, crop, or pad the Instagram post artwork.

Use case: illustrated private-caption carousel. Asset type: complete publishable slide 1 of 8, generated separately as native 4:5 Instagram post and native 9:16 Reels/Stories. Create an original @a.storyof.two hand-drawn scene at a busy city crossing after coffee. Aachu and Zuv walk together in a warm everyday city moment while background people reduce to soft linework and warm blur. Aachu wears a white wrap shirt, jeans, red bag or red shoes; Zuv wears a pale blue shirt and grey trousers. Their faces follow the Aachu/Zuv illustrated caricature identity: her long dark hair and expressive face, his dark wavy hair, thick brows, beard, calm smile. The hook text sits above them with generous whitespace. Render exact text: some couples come with\nprivate captions. Add tiny @a.storyof.two brandmark bottom-right. This is not a quote card; it is an illustrated moment that introduces the private-caption format. No Friends or sitcom visual language.

## Expected Output

- Save packaged final to `output/carousels/2026-05-24/some-couples-come-with-private-captions-final/final-reels-stories/slide-01.png`.
- Source provenance should point to the Codex generated image copied into `output/carousels/2026-05-24/some-couples-come-with-private-captions-final/final/model-native-source/reels-stories-slide-01.png`.
