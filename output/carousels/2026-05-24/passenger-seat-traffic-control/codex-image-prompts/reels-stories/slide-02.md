# Codex Built-In Image Prompt - Slide 02 - Reels/Stories

Use the Codex built-in image generator. Do not use external API keys or external image API clients.

## Native Output Contract

- Native output format: Reels/Stories
- Required aspect ratio: 9:16
- Required final file: `output/carousels/2026-05-24/passenger-seat-traffic-control/final-reels-stories/slide-02.png`
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

Maps said left in 300 meters.

## Prompt

Native output format: Reels/Stories. Generate a complete 9:16 vertical publishable story slide with all text and the tiny @a.storyof.two brandmark inside the image. Reframe the scene for the taller canvas; do not stretch, crop, or pad the Instagram post artwork.

A complete publishable illustrated carousel slide. Scene: simplified dashboard with a non-readable map-like phone shape showing only a generic left arrow and small distance hint, not a real app UI. Aachu leans forward studying the road like official navigator; Zuv drives safely, amused. The relationship proof is app logic versus her logic. Exact copy: Maps said left in 300 meters. Handwritten text in safe upper space, brandmark bottom-right. No readable streets, no UI details, no unsafe driving.

## Expected Output

- Save packaged final to `output/carousels/2026-05-24/passenger-seat-traffic-control/final-reels-stories/slide-02.png`.
- Source provenance should point to the Codex generated image copied into `output/carousels/2026-05-24/passenger-seat-traffic-control/final/model-native-source/reels-stories-slide-02.png`.
