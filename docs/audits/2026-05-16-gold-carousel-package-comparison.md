# Gold Carousel Package Comparison

date: 2026-05-16
gold_package: output/carousels/2026-05-09/he-didnt-marry-peace
candidate_package: output/carousels/2026-05-16/he-did-not-marry-low-maintenance-clean
status: candidate_falls_short
detail: docs/audits/2026-05-16-gold-carousel-package-anatomy.md

## Summary

The 2026-05-09 `he-didnt-marry-peace` package is the current gold reference
for illustrated carousel generation. It succeeds because the package is
product-first: a compact concept, strong character bible, seven-slide emotional
arc, concise image prompts, immediate generated PNGs at the package root, raw
copies under `source-generated/`, and a `preview.md`.

The 2026-05-16 clean rebuild fixed one important failure: it no longer treats an
identity image as a story photo. But it still falls short because it is
governance-first and too abstract. It has many audit artifacts, no generated
root slides, a compressed five-slide arc, and weaker wardrobe/motif anchors.

## What The Gold Package Does Better

1. Seven-slide arc instead of five.
   - Slide 1: hook.
   - Slides 2-4: escalating Aachu chaos.
   - Slide 5: Himanshu calm-husband reveal.
   - Slide 6: emotional turn.
   - Slide 7: save-worthy thesis.

2. Concrete character bible.
   - Aachu is not just "expressive"; she has soft curls, bridal jewelry,
     pink/coral/orange/red lehenga energy, mehendi, jasmine, expressive hands.
   - Himanshu is not just "calm"; he has dark wavy hair, ivory sherwani,
     pastel embroidery, grounded posture, soft amused eyes.

3. Visual motifs create continuity.
   - Spark versus steady diya flame.
   - Shoes, dupatta, chai, marigold, jasmine, terracotta steps.
   - These motifs make the carousel feel authored, not generated.

4. Prompts are compact but complete.
   - Each slide prompt has scene/backdrop, subject, style, composition/framing,
     exact text, brandmark, and constraints.
   - It avoids long contract language inside every prompt.

5. Final output is obvious.
   - `slide-01.png` through `slide-07.png` exist at the package root.
   - `source-generated/` preserves raw outputs.
   - `preview.md` displays the final carousel.

## Where The Candidate Falls Short

1. The five-slide arc compresses the story too much.
   - It jumps from hook to payoff without the satisfying escalation and soft
     turn that made the gold package work.

2. Identity-only is honest but visually underpowered.
   - The current identity image is a casual travel photo, not the wedding-style
     reference that powered the gold illustrations.
   - If using identity-only mode, the prompt must carry more concrete wardrobe,
     hair, jewelry, posture, and motif direction.

3. The candidate has too many process artifacts and no root-level slides.
   - This makes it look operationally complete but not creatively complete.

4. The prompt language is safer but less vivid.
   - "Small emotional storm" and "emotional weather" are weaker than the gold
     package's concrete scenes: no shoes, folded arms, handkerchief, water,
     breakfast moods, spark and diya.

5. The final generation path is not visible enough.
   - A good package should make generated images the center of the folder, not
     bury them behind audit gates.

## Required Changes For The Next Rebuild

- Use the gold folder as the package template.
- Use seven slides for this carousel family.
- Keep root-level normalized PNGs: `slide-01.png` ... `slide-07.png`.
- Preserve raw outputs under `source-generated/`.
- Add `preview.md`.
- Move audit artifacts out of the creator-facing surface or keep them secondary.
- Add a stronger character bible to the candidate prompt pack.
- Restore the calm-husband reveal slide and separate emotional turn slide.
- Use gold slide images as style references when generating related packages.

## Theme Architecture To Reuse

Do not reuse the `he didn't marry / he married / he married` wording as a
literal template. That repetition belongs to this specific carousel, not every
future carousel.

The reusable pattern is structural:

1. Open with one sharp, instantly readable relationship truth.
2. Show a specific behavior that proves the truth visually.
3. Escalate with a second behavior that is more memeable or more concrete.
4. Broaden into a daily-life rhythm so the viewer recognizes the couple
   dynamic, not just one joke.
5. Reveal the other partner's emotional role in the relationship.
6. Turn the joke into tenderness.
7. Land on one save-worthy emotional thesis.

In other words: preserve the theme grammar, not the sentence grammar. For this
family of carousels, the theme grammar is usually `chaotic-wife energy` meeting
`calm-husband steadiness`, but the copy can take many forms: a memory, a list of
tiny rituals, a then/now contrast, a POV confession, a travel moment, or a
single object that carries the story.

## File Anatomy Of The Gold Package

### `manifest.json`

The manifest stays simple. It identifies the package, format, status, and the
reference image set. The most important detail is that every reference image has
a role: couple likeness, full-body pose, seated pose, solo Himanshu, solo
Anchal. This tells the generator why each image exists.

### `concept.json`

This is the creative thesis and character bible. It defines:

- the human truth;
- the emotional arc;
- the visual meaning;
- the main metaphor;
- character roles and visual traits;
- what to avoid.

This file is compact but high-leverage. It gives the carousel a soul before the
slides exist.

### `slides.json`

This is not just copy. Each slide has:

- `copy`: the exact line on the slide;
- `role`: its job in the narrative;
- `visual`: a drawable scene;
- `emotion`: what the viewer should feel;
- `cta_intent`: why someone should swipe, save, or send.

The strong reusable part is this schema of intent, not the literal phrasing.

### `prompt-pack.json`

The prompt pack has one shared style prompt and then one compact prompt per
slide. Each slide prompt includes:

- asset type and slide number;
- scene/backdrop;
- subject action;
- style/medium;
- composition/framing;
- exact text;
- brandmark;
- constraints.

The prompts avoid long audit language. They speak in image-making terms.

### `copy.json`

The caption supports the carousel instead of explaining it. It is short, native,
and conversational. Alt text mirrors the visual story clearly.

### `review.json`

The review is a creative gate, not a bureaucracy gate. It scores theme
alignment, likeness prompting, simplicity, payoff, voice, hook, flow, and
non-generic quality. It also names generation risks before image generation.

### `final-approval.md`

The checklist is creator-facing and practical: does the copy feel like them,
are the jokes affectionate, is the final line true, is text readable, is slide
1 funny within one second, is slide 7 save/share-worthy?

### `storyboard.md`

The storyboard is the fastest human read. It strips everything down to slide
line plus visual. This makes it useful for approval before generation.

### `image-generation.json`

The generation record keeps provenance: status, generation mode, source
directory, normalized outputs, raw copies, and output size.

### `preview.md`

The preview is essential. It makes the folder immediately inspectable by
showing the root-level final slides in order.

### Root Slide PNGs And `source-generated/`

The root `slide-XX.png` files are the creator-facing final carousel assets,
normalized to `1080x1350`. `source-generated/` preserves raw generated copies.
This structure keeps the product visible while preserving provenance.

## Decision

The clean rebuild is not the final target. It should be rebuilt again into a
gold-aligned package before image generation.
