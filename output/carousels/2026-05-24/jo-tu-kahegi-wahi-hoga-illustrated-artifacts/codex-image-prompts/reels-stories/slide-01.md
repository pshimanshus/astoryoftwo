# Codex Built-In Image Prompt - Slide 01 - Reels/Stories

Use the Codex built-in image generator. Do not use external API keys or external image API clients.

## How To Use This File

- This markdown file is the Codex handoff/checklist, not the exact text to paste into the image model.
- Attach/view the image references below, then paste only `output/carousels/2026-05-24/jo-tu-kahegi-wahi-hoga-illustrated-artifacts/codex-image-prompts/reels-stories/slide-01.prompt.txt` into the image generator.
- After generation, package the returned image with `scripts/package_generated_carousel.py` or the proof-specific workflow.

## Native Output Contract

- Native output format: Reels/Stories
- Required aspect ratio: 9:16
- Required final file: `output/carousels/2026-05-24/jo-tu-kahegi-wahi-hoga-illustrated-artifacts/final-reels-stories/slide-01.png`
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

- Dossier: output/carousels/2026-05-24/jo-tu-kahegi-wahi-hoga-illustrated-artifacts/identity-dossier.json
- Preflight: output/carousels/2026-05-24/jo-tu-kahegi-wahi-hoga-illustrated-artifacts/identity-generation-preflight.md

## Actual Image Inputs

Identity dossier references:
- output/carousels/2026-05-24/jo-tu-kahegi-wahi-hoga-illustrated-artifacts/identity-face-contact-sheet.jpg

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

Me with my
"jo tu kahegi wahi hoga"

## Prompt

Native output format: Reels/Stories. Generate a complete 9:16 vertical publishable story slide with all text and the tiny @a.storyof.two brandmark inside the image. Reframe the scene for the taller canvas; do not stretch, crop, or pad the Instagram post artwork.

Use case: complete publishable @a.storyof.two illustrated carousel slide. Asset type: native 4:5 Instagram post and separate native 9:16 Reels/Stories artwork for slide 1 of 6. Visual system: Soft Storybook Phrase-World Scenes in the established @a.storyof.two house style. Create a soft hand-drawn desi storybook full scene on warm off-white paper with imperfect black linework, matte muted colors, expressive recurring illustrated Aachu/Zuv faces, generous negative space, and tiny emotional micro-elements only where useful. The phrase-world appears as handwritten text integrated into the scene; the main visual must be Aachu and Zuv body language, not a prop surface. house-style illustrated scene consistency: @a.storyof.two final image prompts must stay soft desi storybook full scenes where Aachu/Zuv behavior carries the slide; paper artifacts, posters, receipts, labels, or stationery can only be tiny scene details, never the visual system. Warm full-scene @a.storyof.two illustration. Aachu is mid-decision in an ordinary Indian public-life moment, laughing with shy dramatic energy and one hand near her face. Zuv stands close beside her with dark wavy hair, beard, thick brows, and an amused calm smile, already adjusting the plan on his phone with willing theek-hai energy. Their body language is the whole visual proof. Render this exact handwritten-style slide copy inside the artwork, line-broken exactly: Me with my\n"jo tu kahegi wahi hoga". Add the tiny low-contrast handwritten @a.storyof.two brandmark at bottom-right inside the artwork. No photorealism, no pasted photo, no collage, no external logo, no copied reference layout, no stock Indian couple, no glossy AI look, no 3D, no anime, no Pixar/Disney style, no bossy-wife/defeated-husband framing, no generic perfect-boyfriend poster energy, no separate quote card.

## Expected Output

- Save packaged final to `output/carousels/2026-05-24/jo-tu-kahegi-wahi-hoga-illustrated-artifacts/final-reels-stories/slide-01.png`.
- Source provenance should point to the Codex generated image copied into `output/carousels/2026-05-24/jo-tu-kahegi-wahi-hoga-illustrated-artifacts/final/model-native-source/reels-stories-slide-01.png`.
