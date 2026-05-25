# Codex Built-In Image Prompt - Slide 01 - Instagram post

Use the Codex built-in image generator. Do not use external API keys or external image API clients.

## Native Output Contract

- Native output format: Instagram post
- Required aspect ratio: 4:5
- Required final file: `output/carousels/2026-05-22/someone-stays-for-the-full-story/final/slide-01.png`
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

- Dossier: identity_images/_identity_dossier/identity-dossier.json
- Preflight: identity_images/_identity_dossier/identity-generation-preflight.md

## Actual Image Inputs

Identity dossier references:
- identity_images/_identity_dossier/identity-face-contact-sheet.jpg
- identity_images/WhatsApp Image 2026-05-19 at 22.28.01.jpeg
- identity_images/WhatsApp Image 2026-05-19 at 22.28.03 (1).jpeg
- identity_images/WhatsApp Image 2026-05-19 at 22.28.04 (1).jpeg
- identity_images/WhatsApp Image 2026-05-19 at 22.28.04 (5).jpeg

Identity references:
- identity_images/WhatsApp Image 2026-05-19 at 22.28.01.jpeg
- identity_images/WhatsApp Image 2026-05-19 at 22.28.03 (1).jpeg
- identity_images/WhatsApp Image 2026-05-19 at 22.28.04 (1).jpeg
- identity_images/WhatsApp Image 2026-05-19 at 22.28.04 (5).jpeg

Story/source references:

Style references:
- output/carousels/2026-05-19/main-kar-lungi/final/slide-01.png
- output/carousels/2026-05-19/love-carries-the-heavier-half/final/slide-03.png
- output/carousels/2026-05-16/he-learned-her-subtitles/final/slide-02.png
- /Users/himanshusharma/Downloads/Generated image 4.png
- /Users/himanshusharma/Downloads/Generated image 5.png

## Exact Slide Copy

Some people don’t tell stories.

## Prompt

Native output format: Instagram post. Generate a complete 4:5 vertical publishable carousel slide with all text and the tiny @a.storyof.two brandmark inside the image. Do not rely on cropping, padding, or resizing from another aspect ratio.

Use case: illustration-story. Asset type: complete publishable carousel slide 1 of 7. Generate as model-native publishable artwork with exact text and brandmark inside the image. This carousel is about a partner who tells the full dramatic version of every incident, and the love of someone who listens like all of it matters. Story context: Aachu does not merely tell an incident. She performs it with side plots, dramatic gestures, and a timeline that only she understands. The romantic obstacle is that her full version could be treated as too long, too much, or inconvenient. Zuv’s active love is listening like the whole version matters, phone down, leaning in, choosing to stay with the complete story. Golden theme: universal relationship truth -> Aachu expressive proof -> Zuv active patient care -> tender acceptance thesis. Selected process card: Card 13 - The Way He Stays, blended with Card 12 - The Thing She Brings. Story-selling score: 29/30. Golden-theme score: 29/30. Exact slide copy: Some people don’t tell stories. Scene to draw: Aachu mid-story in a warm open room, seated but almost standing from excitement, hands lifted mid-air, eyebrows alive, one clear speech swoosh beginning from her. Zuv is present but quieter at frame edge, already looking at her instead of away. Identity continuity lock: use the selected identity references as actual face, hair, body-proportion, posture, and outfit references. Aachu is expressive and animated, never mocked. Zuv is active through attention: leaning in, phone down, amused, patient, fully present. Face identity contract: {"Aachu/Anchal": {"non_negotiable": ["long dark hair", "expressive eyes and brows", "warm fair-medium skin tone", "soft oval/round face structure", "fuller lips and expressive smile", "playful dramatic energy under the softness", "slightly smaller/petite presence relative to Himanshu"], "expression_range": ["animated storyteller", "dramatic reenactment face", "confident explainer", "softly received smile"], "clothing_and_detail_anchors": ["red-coral printed sleeveless top from selected identity references", "blue jeans", "loose long dark hair", "silver watch/bracelet when visible"]}, "Himanshu/Zuv": {"non_negotiable": ["dark wavy hair with visible volume", "thick dark brows", "warm brown skin tone", "rounded/oval smiling face structure", "trimmed full beard and mustache", "calm grounded expression, not a generic model face", "medium-tall broader build relative to Aachu"], "expression_range": ["soft amused smile", "patient attentive look", "phone-down listening face", "choosing-to-stay warmth"], "clothing_and_detail_anchors": ["white/cream restaurant shirt or zip-collar top", "dark trousers", "black watch", "visible neck chain when natural"]}} Outfit lock: Aachu wears the red-coral printed sleeveless top with blue jeans and loose long dark hair; Zuv wears the white/cream shirt or zip-collar top with dark trousers. Keep outfits consistent across all slides. Shared style: Create a complete publishable @a.storyof.two social slide in the established Aachu/Zuv illustrated carousel look: soft hand-drawn flat vector warmth with desi storybook texture, warm off-white paper, imperfect black outlines, slightly uneven strokes, matte muted colors, generous breathing room, expressive faces, and one clear visual idea. Use Product Unshipped-like simplicity adapted for a desi love story. Render exact handwritten-style black slide copy inside the artwork and add the tiny low-contrast handwritten brandmark @a.storyof.two at bottom-right. Negative prompt: No photorealism, no 3D, no glossy AI look, no stock Indian couple, no Canva quote-card, no crowded background, no repeated props, no generic romance poster, no mean joke, no phone distraction except the face-down phone on slide 5 or 6, no extra text. Composition: leave generous warm paper whitespace for the short handwritten copy; make the scene readable at Instagram carousel size; do not create a separate quote panel.

## Expected Output

- Save packaged final to `output/carousels/2026-05-22/someone-stays-for-the-full-story/final/slide-01.png`.
- Source provenance should point to the Codex generated image copied into `output/carousels/2026-05-22/someone-stays-for-the-full-story/final/model-native-source/instagram-post-slide-01.png`.
