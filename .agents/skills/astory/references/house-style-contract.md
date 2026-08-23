# A Story House Style Contract

Use this contract for every final `@a.storyof.two` illustration.

## Output Surface

- Final illustration: native `1080x1350 px` portrait.
- Every imagegen prompt must explicitly include `1080x1350 px`.
- Do not resize, crop, pad, or extend another surface into the final portrait.

## Identity

Faces are highest priority. Final generation must use actual identity references made visible to Codex. Text-only descriptions are not sufficient.

Preserve:
- eye shape
- eyebrow shape
- nose
- lips
- jawline
- cheek structure
- hairline
- skin tone
- beard shape
- hairstyle
- body type

Do not:
- merge Aachu and Zuv features
- invent new faces
- over-beautify into different people
- change ethnicity, age, facial proportions, skin tone, or hairstyle identity

## Illustration Style

Premium hand-drawn romantic editorial watercolor-and-ink illustration. Soft transparent watercolor blooms, fine ink and pencil linework, warm neutral ivory/off-white paper, visible paper grain, delicate sketch texture, gentle crosshatching, imperfect organic edges, and soft faded edges.

The result must feel intimate, tender, cozy, stylish, rich, editorial, emotionally warm, and premium. It must not look like a generic AI watercolor, quote-card, poster, anime, 3D render, flat vector, photorealistic portrait, or children's cartoon.

## Palette

Use neutral warm ivory and soft off-white paper. Avoid yellow, mustard, sepia, beige/tan dominance, parchment, coffee-stained, heavy cream, neon colors, harsh contrast, and glossy digital finish.

Allowed accents: muted denim blue, soft navy, off-white cotton, faded sage, peach blush, dusty coral, warm camel used lightly.

## Composition

Leave generous warm negative space in the upper-middle for integrated on-image text. Place the couple in the lower or middle-lower canvas unless the scene requires otherwise. Backgrounds are present but secondary and fade into the paper.

## Text

Render exact on-image text inside the illustration as readable, polished, hand-drawn typography. Preserve spelling, line breaks, punctuation, capitalization, and wording exactly. Do not add extra words, random letters, labels, UI, speech bubbles, or platform artifacts unless explicitly requested.

## Brandmark

Every final illustration includes tiny low-contrast handwritten `@a.storyof.two` in the top-right corner as part of the artwork.

## Scene Logic

The scene must visually prove the written line. Clothing state, props, hands, body position, and eyeline must not contradict the text. Poses must be natural, flattering, and physically believable.

Visual setting is a hard gate, not decoration. The environment, body logic,
camera angle, prop placement, and negative space must make concrete sense for
the locked beat; otherwise reject with `VISUAL_SETTING_CONTRADICTION` or
`SCENE_LOGIC_CONTRADICTION` before prompt lock or image QA acceptance.
