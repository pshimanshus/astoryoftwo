# Codex Built-In Image Prompt - Slide 01 - Reels/Stories

Use the Codex built-in image generator. Do not use external API keys or external image API clients.

## How To Use This File

- This markdown file is the Codex handoff/checklist, not the exact text to paste into the image model.
- Attach/view the image references below, then paste only `output/carousels/2026-05-29/otp-expired-twice/codex-image-prompts/reels-stories/slide-01.prompt.txt` into the image generator.
- After generation, package the returned image with `scripts/package_generated_carousel.py` or the proof-specific workflow.

## Native Output Contract

- Native output format: Reels/Stories
- Required aspect ratio: 9:16
- Required final file: `output/carousels/2026-05-29/otp-expired-twice/final-reels-stories/slide-01.png`
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

- Dossier: output/carousels/2026-05-29/otp-expired-twice/identity-dossier.json
- Preflight: output/carousels/2026-05-29/otp-expired-twice/identity-generation-preflight.md

## Actual Image Inputs

Identity dossier references:
- output/carousels/2026-05-29/otp-expired-twice/identity-face-contact-sheet.jpg

Identity references:
- identity_images/aachu_zuv.png

Story/source references:

Style references:
- output/carousels/2026-05-19/main-kar-lungi/final/slide-01.png
- output/carousels/2026-05-19/love-carries-the-heavier-half/final/slide-03.png
- output/carousels/2026-05-16/he-learned-her-subtitles/final/slide-02.png

## Exact Slide Copy

30 seconds.

## Prompt

Native output format: Reels/Stories. Generate a complete 9:16 vertical publishable story slide with all text and the tiny @a.storyof.two brandmark inside the image. Reframe the scene for the taller canvas; do not stretch, crop, or pad the Instagram post artwork.

Slide 1 of 7 for OTP Expired Twice. Exact on-image text: 30 seconds.. Scene: Cozy home evening, low table or sofa edge. Aachu holds her phone close to the viewer with a large harmless app verification timer reading 30 seconds. Zuv sits beside her with his own phone showing a tiny OTP message. Both realize the countdown has turned a normal task into a mission. Pose/body language: Aachu leans forward, thumb ready to type, eyes wide at the timer. Zuv angles his phone toward her, brows lifted. Their shoulders are close but not posed. Wardrobe: Same relaxed home outfits across the carousel: casual kurta/top for Aachu, simple T-shirt or hoodie for Zuv. Props: Two color-coded phones only: her app/timer phone in foreground, his OTP phone beside it; no wallet, card, cart, bank logo, or money. Background: Warm lived-in home corner with sofa cushion or low table, minimal detail, lots of ivory negative space above. Emotion: tiny household pressure, funny alertness, shared focus Keep this as harmless household app verification, not finance or shopping. Make Aachu and Zuv equally involved in the pressure. Identity continuity lock: Match the selected Aachu/Zuv identity bundle exactly enough that both people read as the same recurring couple: Aachu with long dark hair, expressive eyes and brows, soft oval face, warm fair-medium South Asian skin, and playful dramatic energy; Zuv with dark wavy hair, thick brows, warm brown skin, rounded/oval face, trimmed beard and mustache, calm grounded expression, and gentle amused eyes. Both look suddenly alert, with Aachu more expressive and Zuv calm but pulled into the pressure. Keep both in the same cozy home outfits across all slides: Aachu in a soft casual kurta or relaxed top with loose hair and small jewelry; Zuv in a simple home T-shirt or hoodie. Do not invent formal, glam, wedding, office, travel, or restaurant styling. Same faces, hair, body proportions, outfit family, phone props, table/sofa setup, and relationship energy must continue across all seven slides. Use attached identity reference images and preserve face/reference details.

## Expected Output

- Save packaged final to `output/carousels/2026-05-29/otp-expired-twice/final-reels-stories/slide-01.png`.
- Source provenance should point to the Codex generated image copied into `output/carousels/2026-05-29/otp-expired-twice/final/model-native-source/reels-stories-slide-01.png`.
