# Codex Built-In Image Prompt - Slide 05 - Reels/Stories

Use the Codex built-in image generator. Do not use external API keys or external image API clients.

## How To Use This File

- This markdown file is the Codex handoff/checklist, not the exact text to paste into the image model.
- Paste the full prompt from `slide-05.prompt.txt` into the image generator.
- Prompt file path: `output/carousels/2026-07-03/still-learning-love-2/codex-image-prompts/reels-stories/slide-05.prompt.txt`.
- After generation, package the returned image with `scripts/package_generated_carousel.py` or the proof-specific workflow.

## Prompt Source

Paste the full prompt from `slide-05.prompt.txt`. This markdown file intentionally does not duplicate the prompt body, so `.prompt.txt` remains the only generation prompt source.

## Native Output Contract

- Native output format: Reels/Stories
- Required generated source size: 1080x1920 px (mandatory; generate this source size, not just this ratio)
- Required final upload/export size: 1080x1920 px
- Required aspect ratio: 9:16
- Required final file: `output/carousels/2026-07-03/still-learning-love-2/final-reels-stories/slide-05.png`
- Each slide must have separate generated sources per surface: one Instagram post source generated at 1440x1920 for deterministic export to 1080x1440, and one Reels/Stories image generated exactly at 1080x1920. Reels/Stories output must never be derived from the Instagram post image.
- Generate this format as its own artwork. Do not create it by resizing another social format.

## Hard Gate

- The paste-ready `.prompt.txt` must include the @a.storyof.two watercolor-and-ink master prompt structure.
- Before any slide generation, read `identity-generation-preflight.md` and load/view `identity-face-contact-sheet.jpg`.
- Preserve the carousel story-director spine embedded in `prompt-pack.json`: hook, setup, proof, bridge, active Zuv role, earned ending, and send/save reason.
- Before calling image generation, load/view every identity reference listed below so they are actual image inputs in the Codex context.
- Use the selected identity images as face, hair, expression, body proportion, posture, and relationship-energy references.
- Do not accept generic Aachu/Zuv faces.
- Keep the exact slide copy and tiny `@a.storyof.two` brandmark inside the generated image.

## Identity Dossier

- Dossier: output/carousels/2026-07-03/still-learning-love-2/identity-dossier.json
- Preflight: output/carousels/2026-07-03/still-learning-love-2/identity-generation-preflight.md

## Actual Image Inputs

- output/carousels/2026-07-03/still-learning-love-2/identity-face-contact-sheet.jpg
- config/references/identity/aachu/face-05.png
- config/references/identity/together/together-20.jpg
- config/references/identity/zuv/portrait-07.jpg
- config/references/identity/together/together-20.jpg
- config/references/identity/aachu/face-05.png
- config/references/identity/zuv/portrait-07.jpg
- /Users/himanshusharma/Desktop/ss/Screenshot 2026-07-03 at 6.05.07 PM.png
- /Users/himanshusharma/Desktop/ss/Screenshot 2026-07-03 at 6.05.03 PM.png
- /Users/himanshusharma/Desktop/ss/Screenshot 2026-07-03 at 6.04.58 PM.png
- /Users/himanshusharma/Desktop/ss/Screenshot 2026-07-03 at 6.04.55 PM.png
- /Users/himanshusharma/Desktop/ss/Screenshot 2026-07-03 at 6.04.50 PM.png
- /Users/himanshusharma/Desktop/ss/Screenshot 2026-07-03 at 6.04.41 PM.png
- /Users/himanshusharma/Desktop/ss/Screenshot 2026-07-03 at 6.04.34 PM.png
- /Users/himanshusharma/Desktop/ss/Screenshot 2026-07-03 at 6.04.29 PM.png
- config/references/style-lock/observational-intimacy-premium/slide-01.png
- config/references/style-lock/observational-intimacy-premium/slide-03.png
- config/references/style-lock/observational-intimacy-premium/slide-08.png
- config/references/style-lock/observational-intimacy-premium/slide-02.png
- config/references/style-lock/observational-intimacy-premium/slide-04.png
- config/references/style-lock/observational-intimacy-premium/slide-05.png
- config/references/style-lock/observational-intimacy-premium/slide-06.png
- config/references/style-lock/observational-intimacy-premium/slide-07.png

## Exact Slide Copy

we talk about saying sorry,
but never apologies when we should.

## Expected Output

- Save packaged final to `output/carousels/2026-07-03/still-learning-love-2/final-reels-stories/slide-05.png`.
- Source provenance should point to the Codex generated image copied into `output/carousels/2026-07-03/still-learning-love-2/final/model-native-source/reels-stories-slide-05.png`.
