# Codex Built-In Image Prompt - Slide 03 - Instagram post

Use the Codex built-in image generator. Do not use external API keys or external image API clients.

## Native Output Contract

- Native output format: Instagram post
- Required aspect ratio: 4:5
- Required final file: `output/carousels/2026-05-24/passenger-seat-traffic-control/final/slide-03.png`
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

- Dossier: output/carousels/2026-05-24/passenger-seat-traffic-control/identity-dossier.json
- Preflight: output/carousels/2026-05-24/passenger-seat-traffic-control/identity-generation-preflight.md

## Actual Image Inputs

Identity dossier references:
- output/carousels/2026-05-24/passenger-seat-traffic-control/identity-face-contact-sheet.jpg
- identity_images/aachu_zuv.png

Identity references:
- identity_images/aachu_zuv.png

Story/source references:

Style references:
- output/carousels/2026-05-19/main-kar-lungi/final/slide-01.png
- output/carousels/2026-05-19/love-carries-the-heavier-half/final/slide-03.png
- output/carousels/2026-05-16/he-learned-her-subtitles/final/slide-02.png

## Exact Slide Copy

She said, "LEFT-LEFT-LEFT now."

## Prompt

Native output format: Instagram post. Generate a complete 4:5 vertical publishable carousel slide with all text and the tiny @a.storyof.two brandmark inside the image. Do not rely on cropping, padding, or resizing from another aspect ratio.

A complete publishable illustrated carousel slide. Scene: Aachu dramatically points left from the passenger seat with harmless motion lines and wide expressive eyes, saying the turn is urgent; Zuv remains composed and safe, glancing lightly toward the road, amused not annoyed. No panic, no collision, no steering-wheel grabbing. Exact copy: She said, "LEFT-LEFT-LEFT now." Put text in clear warm-paper zone. Tiny @a.storyof.two brandmark bottom-right.

## Expected Output

- Save packaged final to `output/carousels/2026-05-24/passenger-seat-traffic-control/final/slide-03.png`.
- Source provenance should point to the Codex generated image copied into `output/carousels/2026-05-24/passenger-seat-traffic-control/final/model-native-source/instagram-post-slide-03.png`.
