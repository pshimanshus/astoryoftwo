# Codex Built-In Image Prompt - Slide 01 - Instagram post

Use the Codex built-in image generator. Do not use external API keys or external image API clients.

## How To Use This File

- This markdown file is the Codex handoff/checklist, not the exact text to paste into the image model.
- Paste the full prompt from `slide-01.prompt.txt` into the image generator.
- Prompt file path: `/Users/himanshusharma/astoryoftwo-analysis/output/carousels/2026-06-27/road-hi-galat-hai/codex-image-prompts/instagram-post/slide-01.prompt.txt`.
- After generation, package the returned image with `scripts/package_generated_carousel.py` or the proof-specific workflow.

## Prompt Source

Paste the full prompt from `slide-01.prompt.txt`. This markdown file intentionally does not duplicate the prompt body, so `.prompt.txt` remains the only generation prompt source.

## Native Output Contract

- Native output format: Instagram post
- Required aspect ratio: 4:5
- Required final file: `/Users/himanshusharma/astoryoftwo-analysis/output/carousels/2026-06-27/road-hi-galat-hai/final/slide-01.png`
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

- Dossier: /Users/himanshusharma/astoryoftwo-analysis/output/carousels/2026-06-27/road-hi-galat-hai/identity-dossier.json
- Preflight: /Users/himanshusharma/astoryoftwo-analysis/output/carousels/2026-06-27/road-hi-galat-hai/identity-generation-preflight.md

## Actual Image Inputs

- /Users/himanshusharma/astoryoftwo-analysis/output/carousels/2026-06-27/road-hi-galat-hai/identity-face-contact-sheet.jpg
- config/references/identity/aachu/portrait-02.jpg
- config/references/identity/zuv/portrait-02.jpg
- config/references/identity/together/together-18.jpg
- config/references/identity/together/together-19.jpg
- config/references/identity/aachu/portrait-02.jpg
- config/references/identity/zuv/portrait-02.jpg
- config/references/identity/together/together-18.jpg
- config/references/identity/together/together-19.jpg
- /Users/himanshusharma/Desktop/Best Illustration/Screenshot 2026-06-13 at 1.06.24 PM.png
- /Users/himanshusharma/Desktop/Best Illustration/Screenshot 2026-06-13 at 1.06.32 PM.png
- /Users/himanshusharma/Desktop/Best Illustration/Screenshot 2026-06-13 at 1.06.28 PM.png
- config/references/style-lock/observational-intimacy-premium/slide-01.png
- config/references/style-lock/observational-intimacy-premium/slide-03.png
- config/references/style-lock/observational-intimacy-premium/slide-08.png

## Exact Slide Copy

left?
seedha?

## Expected Output

- Save packaged final to `/Users/himanshusharma/astoryoftwo-analysis/output/carousels/2026-06-27/road-hi-galat-hai/final/slide-01.png`.
- Source provenance should point to the Codex generated image copied into `/Users/himanshusharma/astoryoftwo-analysis/output/carousels/2026-06-27/road-hi-galat-hai/final/model-native-source/instagram-post-slide-01.png`.
