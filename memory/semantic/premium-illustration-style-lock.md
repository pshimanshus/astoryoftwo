# Premium Illustration Style Lock

last_updated: 2026-05-31
status: creator_approved
confidence: 1.0

## Approved Reference

The creator-approved style target is the corrected Observational Intimacy
premium carousel:

- repo reference bundle: `config/references/style-lock/observational-intimacy-premium/`
- package: `output/illustrations/2026-05-30/observational-intimacy-premium/`
- contact sheet: `output/illustrations/2026-05-30/observational-intimacy-premium/contact-sheet.png`
- final slides: `output/illustrations/2026-05-30/observational-intimacy-premium/carousel-ready-977x1610/`

Use these slides as the default style reference for future @a.storyof.two
illustration-story generation in this folder.

## Non-Negotiable Style Traits

- warm ivory paper with visible paper grain;
- premium hand-drawn romantic watercolor-and-ink, not flat vector, cartoon, or
  generic AI watercolor;
- richly layered transparent watercolor blooms with deeper navy, muted denim,
  camel, terracotta, sage, and dusty coral accents;
- fine graphite/ink linework, controlled crosshatching, subtle construction
  lines, and tactile detail in fabric, hair, props, wood, ceramic, shoes, bags,
  chargers, scarves, and denim;
- identity-first Aachu/Zuv faces with expressive eyes, real-person warmth,
  preserved hair silhouettes, and no over-beautified generic model drift;
- native 4:5 for Instagram posts, separate native 9:16 for Reels/Stories, and
  tall vertical 977x1610-style proof composition only when a proof/reference
  surface is requested;
- clean upper-middle negative space for exact readable hand-drawn text;
- tiny low-contrast handwritten `@a.storyof.two` brandmark at bottom-right;
- premium hand-drawn storybook typography like the approved set: neat,
  readable, dark charcoal, slightly imperfect, integrated into the paper.
- shared brief images are mood/composition/story references only unless the
  creator explicitly says otherwise; Aachu/Zuv identity references remain the
  face, expression, posture, and wardrobe anchors.

## New QA Learning

Beautiful art is not enough. Every slide must pass a copy-visual logic check:
the body, clothing, props, and blocking must visibly prove the exact line.

## 2026-05-30 Failed Proof Correction

The first phone-prank proof generated on 2026-05-30 failed. The creator
explicitly rejected it for two hard reasons:

- the paper/background read yellowish/parchment instead of premium neutral
  warm ivory/off-white;
- Aachu/Zuv faces did not match the identity references and looked like generic
  illustrated South Asian characters.

This is a hard style and identity failure, not a subjective minor note.

Future generation must treat these as STOP conditions:

- any yellow, mustard, sepia, beige/tan, parchment, coffee-stained, or heavy
  cream cast across the page;
- any face drift, generic model face, over-beautified face, wrong nose/eyes,
  wrong jaw/cheek structure, wrong beard/hair silhouette, or identity that
  does not clearly read as the selected Aachu/Zuv reference;
- any "final" generation attempted from text-only identity descriptions
  without actual identity reference images attached/available to the image
  model.

If the current image-generation path cannot use the Aachu/Zuv identity
references and the Observational Intimacy Premium style references as actual
image inputs, do not generate final illustrations. Mark the package blocked
for identity/style-reference generation instead.

Hard fails:

- the copy says socks before pants, but Zuv is already wearing pants;
- a character pose makes Aachu or Zuv look crouched, cramped, unflattering, or
  anatomically awkward;
- the paper reads yellowish/parchment/sepia instead of neutral premium
  off-white ivory;
- the faces do not match the selected Aachu/Zuv identity bundle;
- text can only be understood because of the written line, while the scene
  visually proves something else;
- the slide is premium-looking but the action/reaction/props contradict the
  story beat.

For future visual QA, require explicit `scene_logic` and `pose_anatomy` checks
before accepting final art. Also require explicit `paper_tone` and
`identity_match` checks before accepting or even batch-generating final art.

## 2026-05-31 Height And Face Lock Correction

The Private Captions fresh carousel attempt was stopped after the creator
rejected early proofs for face mismatch and height mismatch. This is a hard
identity failure, not a style nit.

Hard lock:

- Himanshu/Zuv is 5'8".
- Aanchal/Aachu is 5'6".
- The difference is only two inches; they should read close in height when
  standing on the same plane.
- Aanchal should never be scaled down to shoulder/chin level beside Himanshu.
- Himanshu should not become tall, lanky, chiseled, or model-like.
- Use a standing/together identity reference as the scale anchor whenever both
  bodies are visible.

Future generation must not batch a carousel after this kind of correction.
First create one corrected proof that uses actual identity images as inputs and
passes face match, body proportion, and the 5'8" vs 5'6" height relationship.
If the available image-generation path ignores the identity/style references or
produces an unrelated artifact, mark the package blocked and switch to a
reference-capable generation path instead of continuing.
