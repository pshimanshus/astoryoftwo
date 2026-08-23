# Codex Built-In Image Prompt - Slide 04 - Instagram post

Use the Codex built-in image generator. Do not use external API keys or external image API clients.

## How To Use This File

- This markdown file is the Codex handoff/checklist, not the exact text to paste into the image model.
- Paste the full prompt from `slide-04.prompt.txt` into the image generator.
- Prompt file path: `output/carousels/2026-08-23/certain-of-you-lost-in-us-moonwater/codex-image-prompts/instagram-post/slide-04.prompt.txt`.
- After generation, package the returned image with `scripts/package_generated_carousel.py` or the proof-specific workflow.

## Prompt Source

Paste the full prompt from `slide-04.prompt.txt`. This markdown file intentionally does not duplicate the prompt body, so `.prompt.txt` remains the only generation prompt source.

## Native Output Contract

- Native output format: Instagram post
- Required generated source size: 1440x1920 px (mandatory; generate this source size, not just this ratio)
- Required final upload/export size: 1080x1440 px
- Required aspect ratio: 3:4
- Required final file: `output/carousels/2026-08-23/certain-of-you-lost-in-us-moonwater/final/slide-04.png`
- Generate only the formats locked by the current request. Generate each requested aspect ratio from its own native source; never infer another output from folders or derive one aspect ratio by cropping, padding, stretching, or extending another.
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

- Dossier: output/carousels/2026-08-23/certain-of-you-lost-in-us-moonwater/identity-dossier.json
- Preflight: output/carousels/2026-08-23/certain-of-you-lost-in-us-moonwater/identity-generation-preflight.md

## Actual Image Inputs

- config/references/identity/together/together-18.jpg
- config/references/identity/aachu/face-04.png
- config/references/identity/zuv/portrait-07.jpg
- config/references/identity/together/together-18.jpg
- config/references/identity/aachu/face-04.png
- config/references/identity/zuv/portrait-07.jpg
- config/references/style-lock/observational-intimacy-premium/slide-01.png
- config/references/style-lock/observational-intimacy-premium/slide-03.png
- config/references/style-lock/observational-intimacy-premium/slide-08.png
- config/references/style-lock/observational-intimacy-premium/slide-02.png
- config/references/style-lock/observational-intimacy-premium/slide-04.png
- config/references/style-lock/observational-intimacy-premium/slide-05.png
- config/references/style-lock/observational-intimacy-premium/slide-06.png
- config/references/style-lock/observational-intimacy-premium/slide-07.png

## Exact Slide Copy

Some days, love did not tell us
what to do.

## Expected Output

- Save packaged final to `output/carousels/2026-08-23/certain-of-you-lost-in-us-moonwater/final/slide-04.png`.
- Source provenance should point to the Codex generated image copied into `output/carousels/2026-08-23/certain-of-you-lost-in-us-moonwater/final/model-native-source/instagram-post-slide-04.png`.
