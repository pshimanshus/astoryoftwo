# Codex Built-In Image Prompt - Slide 03 - Reels/Stories

Use the Codex built-in image generator. Do not use external API keys or external image API clients.

## How To Use This File

- This markdown file is the Codex handoff/checklist, not the exact text to paste into the image model.
- Attach/view the image references below, then paste only `output/carousels/2026-05-30/one-brain-cell-at-home/codex-image-prompts/reels-stories/slide-03.prompt.txt` into the image generator.
- After generation, package the returned image with `scripts/package_generated_carousel.py` or the proof-specific workflow.

## Native Output Contract

- Native output format: Reels/Stories
- Required aspect ratio: 9:16
- Required final file: `output/carousels/2026-05-30/one-brain-cell-at-home/final-reels-stories/slide-03.png`
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

- Dossier: output/carousels/2026-05-30/one-brain-cell-at-home/identity-dossier.json
- Preflight: output/carousels/2026-05-30/one-brain-cell-at-home/identity-generation-preflight.md

## Actual Image Inputs

Identity dossier references:
- output/carousels/2026-05-30/one-brain-cell-at-home/identity-face-contact-sheet.jpg

Identity references:
- identity_images/aachu_zuv.png

Story/source references:

Style references:
- config/references/style-lock/observational-intimacy-premium/contact-sheet.png
- config/references/style-lock/observational-intimacy-premium/slide-01.png
- config/references/style-lock/observational-intimacy-premium/slide-02.png

## Exact Slide Copy

It was in her pocket.

## Prompt

Native output format: Reels/Stories. Generate a complete 9:16 vertical publishable story slide with all text and the tiny @a.storyof.two brandmark inside the image. Reframe the scene for the taller canvas; do not stretch, crop, or pad the Instagram post artwork.

ON-IMAGE TEXT: It was in her pocket.
Scene: Zuv gently points toward the phone tucked in Aachu pocket. Aachu looks down and pulls the phone halfway out with a caught, guilty-laugh expression. Sofa cushions are slightly messy from the search. The reveal feels affectionate, never insulting.
Pose and blocking: Zuv relaxed and kind, pointing lightly toward her pocket; Aachu looking down at her own pocket with widened eyes and a soft embarrassed smile, one hand touching the phone.
Wardrobe: Same home outfits; Aachu shirt sleeve slightly rumpled from searching; pocket/phone placement readable.
Props: phone with small heart sticker halfway visible from Aachu pocket, lifted sofa cushion, coffee table edge, small plant
Background: warm apartment scene, lower detail background, clean upper-middle negative space for text
Emotion: caught and laughing
Identity continuity lock: preserve the same Aachu/Zuv faces, hair, Zuv stubble, Aachu expressive eyes, skin tones, body proportions, and couple energy across every slide. Story continuity rule: do not reveal the punchline too early; plant objects subtly in setup slides and make the next slide earn the reveal. Successful-carousel standard: the staged Aachu/Zuv behavior must prove the relationship truth before the text is read. Use the Observational Intimacy Premium watercolor-and-ink house style with warm ivory paper, visible paper grain, fine ink/pencil linework, transparent watercolor blooms, muted vintage palette, soft faded edges, exact handwritten text in clean upper-middle negative space, and only the tiny @a.storyof.two brandmark at bottom-right.

## Expected Output

- Save packaged final to `output/carousels/2026-05-30/one-brain-cell-at-home/final-reels-stories/slide-03.png`.
- Source provenance should point to the Codex generated image copied into `output/carousels/2026-05-30/one-brain-cell-at-home/final/model-native-source/reels-stories-slide-03.png`.
