# Codex Built-In Image Prompt - Slide 05 - Reels/Stories

Use the Codex built-in image generator. Do not use external API keys or external image API clients.

## How To Use This File

- This markdown file is the Codex handoff/checklist, not the exact text to paste into the image model.
- Attach/view the image references below, then paste only `output/carousels/2026-05-30/one-brain-cell-at-home/codex-image-prompts/reels-stories/slide-05.prompt.txt` into the image generator.
- After generation, package the returned image with `scripts/package_generated_carousel.py` or the proof-specific workflow.

## Native Output Contract

- Native output format: Reels/Stories
- Required aspect ratio: 9:16
- Required final file: `output/carousels/2026-05-30/one-brain-cell-at-home/final-reels-stories/slide-05.png`
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

Dining checked.

## Prompt

Native output format: Reels/Stories. Generate a complete 9:16 vertical publishable story slide with all text and the tiny @a.storyof.two brandmark inside the image. Reframe the scene for the taller canvas; do not stretch, crop, or pad the Instagram post artwork.

ON-IMAGE TEXT: Dining checked.
SCENE: Dining/bar area search. Aachu checks around dining chairs/table. Zuv acts like a serious helper while guarding the hidden phone.
POSE/BODY LANGUAGE: Aachu near dining chair/table, Zuv near counter edge, both natural and readable.
WARDROBE: Same casual home outfits throughout: Aachu in oversized white shirt, blue jeans, small gold earrings, natural dark wavy hair; Zuv in navy hoodie or white tee with tan pants, short stubble, curly hair.
PROPS: dining chair, fruit bowl, mug, kitchen/bar counter in background
BACKGROUND: dining area, neutral ivory paper, no yellow wash
EMOTION: the search travels through the house
STYLE: creator-approved Observational Intimacy Premium A Story of Two watercolor-and-ink. Neutral warm ivory/off-white paper only, visible grain, fine ink/pencil linework, transparent watercolor blooms, muted denim/navy/off-white/camel/faded sage/soft coral, soft faded edges, clean upper-middle negative space.
IDENTITY: use the attached Aachu/Zuv identity reference images and identity contact sheet as actual face references. Faces must match; text-only identity descriptions are not enough.
STORY LOCK: phone-hiding prank only. Do not add a remote, second missing object, phone-in-pocket gag, or moral thesis.
FORMAT: native 4:5 Instagram carousel slide, exact readable hand-drawn text, tiny bottom-right @a.storyof.two brandmark.

## Expected Output

- Save packaged final to `output/carousels/2026-05-30/one-brain-cell-at-home/final-reels-stories/slide-05.png`.
- Source provenance should point to the Codex generated image copied into `output/carousels/2026-05-30/one-brain-cell-at-home/final/model-native-source/reels-stories-slide-05.png`.
