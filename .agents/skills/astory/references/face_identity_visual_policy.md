# Face Identity and Visual Continuity Policy

The identity planning guide. Works with the gold-standard identity route in
`SKILL.md` and the character pages in `references/brain/pages/characters/`.

## Principle

Aachu and Zuv are recurring illustrated characters, not generic couple
placeholders. Every visual plan must protect: face visibility · hairstyle
continuity · body-language continuity · accessory anchors where natural · couple
chemistry · recurring-world consistency.

## Identity-safe framing

Prefer:
- mid-shot · medium-wide · 3/4 view
- side-by-side or diagonal blocking
- clear face visibility
- uncluttered background
- simple hand gestures

Use caution with:
- tiny wide shots · extreme top-down angles · crowded spaces
- heavy shadows on face · food covering mouth · hands covering face
- multiple background people · mirror/reflection shots · complex overlapping arms

## Accessory continuity anchors

When natural to the frame:
- Zuv: silver chain with a small round blue evil-eye pendant (neck/chest visible).
- Aachu: matching evil-eye bracelet on her right hand (wrist visible).
(Source: `references/brain/pages/run-lessons.md`.)

## Identity lock must specify

- how Aachu appears in this scene
- how Zuv appears in this scene
- what face/expression features matter
- what hairstyle/clothing/accessory continuity matters
- how close the camera should be
- whether the shot is identity-safe
- what must be checked by a human after generation

## Human gate

The model may propose identity-safe plans. The model must **not** self-certify
final face identity. Human approval is required before final image / export /
publish. (Final generation must still pass `gold_standard_identity_route_gate`
with raw face anchors loaded in context.)
