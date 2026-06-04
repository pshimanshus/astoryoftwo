# Codex Built-In Image Prompt - Slide 05 - Reels/Stories

Use the Codex built-in image generator. Do not use external API keys or external image API clients.

## How To Use This File

- This markdown file is the Codex handoff/checklist, not the exact text to paste into the image model.
- Attach/view the image references below, then paste only `output/carousels/2026-05-31/alone-not-behind-beside-me/codex-image-prompts/reels-stories/slide-05.prompt.txt` into the image generator.
- After generation, package the returned image with `scripts/package_generated_carousel.py` or the proof-specific workflow.

## Native Output Contract

- Native output format: Reels/Stories
- Required aspect ratio: 9:16
- Required final file: `output/carousels/2026-05-31/alone-not-behind-beside-me/final-reels-stories/slide-05.png`
- Each slide must have two separate native generated sources: one 4:5 Instagram post image and one 9:16 Reels/Stories image. Reels/Stories output must never be derived by resizing, cropping, or padding the Instagram post image.
- Generate this format as its own artwork. Do not create it by resizing another generated slide.

## Hard Gate

- The paste-ready `.prompt.txt` must include the @a.storyof.two watercolor-and-ink master prompt structure.
- Before any slide generation, read `identity-generation-preflight.md` and load/view `identity-face-contact-sheet.jpg`.
- Preserve the carousel story-director spine embedded in `prompt-pack.json`: hook, setup, proof, bridge, active Zuv role, earned ending, and send/save reason.
- Before calling image generation, load/view every identity reference listed below so they are actual image inputs in the Codex context.
- Use the selected identity images as face, hair, expression, body proportion, posture, and relationship-energy references.
- Do not accept generic Aachu/Zuv faces.
- Keep the exact slide copy and tiny `@a.storyof.two` brandmark inside the generated image.

## Identity Dossier

- Dossier: output/carousels/2026-05-31/alone-not-behind-beside-me/identity-dossier.json
- Preflight: output/carousels/2026-05-31/alone-not-behind-beside-me/identity-generation-preflight.md

## Actual Image Inputs

Identity dossier references:
- output/carousels/2026-05-31/alone-not-behind-beside-me/identity-face-contact-sheet.jpg

Identity references:
- config/references/identity/aachu/portrait-02.jpg
- config/references/identity/together/together-18.jpg
- config/references/identity/together/together-19.jpg
- config/references/identity/together/together-21.jpg

Story/source references:
- /Users/himanshusharma/Downloads/WhatsApp Image 2026-05-30 at 03.49.04.jpeg

Style references:
- config/references/style-lock/observational-intimacy-premium/contact-sheet.png
- config/references/style-lock/observational-intimacy-premium/slide-01.png
- config/references/style-lock/observational-intimacy-premium/slide-02.png
- config/references/style-lock/observational-intimacy-premium/slide-03.png
- config/references/style-lock/observational-intimacy-premium/slide-04.png
- config/references/style-lock/observational-intimacy-premium/slide-05.png
- config/references/style-lock/observational-intimacy-premium/slide-06.png
- config/references/style-lock/observational-intimacy-premium/slide-07.png
- config/references/style-lock/observational-intimacy-premium/slide-08.png
- config/references/style-lock/observational-intimacy-premium/favourite-calm-sky.png
- config/references/style-lock/observational-intimacy-premium/home-person-seaside.png

## Exact Slide Copy

Turns out, the view feels better with you by my side.

## Prompt

Native output format: Reels/Stories. Generate a complete 9:16 vertical publishable story slide with all text and the tiny @a.storyof.two brandmark inside the image. Reframe the scene for the taller canvas; do not stretch, crop, or pad the Instagram post artwork.

Scene: Aachu and Zuv sit shoulder-to-shoulder at a soft overlook after the climb, middle-lower in frame. The view is gentle and secondary; the real subject is the quiet relief of being by each other's side. Preserve exact text in upper-middle negative space.

## Expected Output

- Save packaged final to `output/carousels/2026-05-31/alone-not-behind-beside-me/final-reels-stories/slide-05.png`.
- Source provenance should point to the Codex generated image copied into `output/carousels/2026-05-31/alone-not-behind-beside-me/final/model-native-source/reels-stories-slide-05.png`.
