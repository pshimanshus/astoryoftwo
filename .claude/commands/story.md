# /story

Create a 4-5 slide illustrated Instagram carousel for `@a.storyof.two` from
the pictures and story the user shares in the current conversation.

## User Input Shape

The user may write:

```text
/story
title: optional title
slides: 4 or 5
<the story, memory, or moment>
```

They may attach pictures directly in the chat or provide local image paths.

## Required Behavior

When the user invokes `/story`:

1. Use the supplied pictures as visual references.
2. Use the supplied story as the emotional source of truth.
3. Use `config/carousel_style_contract.json` as the canonical style, character,
   typography, negative-prompt, and North Star contract.
4. Require Aachu/Zuv identity references. Prefer `--identity-image` or files in
   `identity_images/`; never treat scene photos alone as enough for face
   consistency.
5. Default to 5 slides; allow only 4 or 5 slides.
6. Follow the `@a.storyof.two` folder context, especially `AGENTS.md`,
   `config/voice.md`, `memory/working.md`, `memory/graph.json`, and the
   C-layer carousel agents.
7. Create a complete illustrated carousel package with:
   - `manifest.json`
   - `concept.json`
   - `slides.json`
   - `prompt-pack.json`
   - `copy.json`
   - `review.json`
   - `storyboard.md`
   - `final-approval.md`
   - `final-images.json`
   - `run-ledger.json`
   - `stage-reviews.json`
   - `final-audit.json`
   - `visual-qa.md`
   - `wiki-update.md`
8. Generate clean art first. Do not ask the image model to render final slide
   typography. Apply final copy and brandmark through the local overlay step.
9. Copy final generated images into the package under `final/slide-XX.png`.
   When text overlays are applied, write `final-with-text/slide-XX.png`.
10. The final audit must be `NEEDS_FIXES` until final images, identity
    references, local typography, and visual QA are present.
11. Never create one-off carousel renderer scripts or filtered-photo collages as
    final carousel art. Identity photos are likeness references; final slides
    must be generated scene illustrations or explicitly marked non-postable
    mockups.
12. Before calling an output postable, verify it satisfies the
    `production_gate` in `config/carousel_style_contract.json`.

## Local CLI Equivalent

```bash
python scripts/create_illustration_carousel.py \
  --story "story text here" \
  --image /path/to/photo-1.jpg \
  --image /path/to/photo-2.jpg \
  --identity-image /path/to/aachu-zuv-reference.jpg \
  --slide-count 5
```

## Style

The output must feel like a soft illustrated archive of Aachu and Zuv's love,
chaos, culture, and tiny rituals. Use Product Unshipped-like soft flat
illustration adapted for a desi love story: imperfect outlines, matte muted
colors, large whitespace, minimal scenes, and recurring Aachu/Zuv identity.
