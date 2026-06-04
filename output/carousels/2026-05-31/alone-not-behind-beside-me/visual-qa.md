# Visual QA

Status: `PROOF_READY_FOR_CREATOR_REVIEW`

No final PNGs have been accepted yet. A model-native slide 5 Instagram-post
proof has been generated and saved for creator review:

`output/carousels/2026-05-31/alone-not-behind-beside-me/proofs/slide-05-instagram-post-proof-v2.png`

A continuity-correct slide 6 humor proof has also been generated and saved:

`output/carousels/2026-05-31/alone-not-behind-beside-me/proofs/slide-06-instagram-post-proof-v2.png`

## Proof QA

- Image size: PASS — `1122x1402` matches native 4:5.
- Palette: PASS — paper RGB `(239,234,224)`, paper saturation `0.061`, paper B/G `0.957`, yellow-band fraction `0.004`.
- Main text: PASS — exact readable line, `Turns out, the view feels better with you by my side.`
- Brandmark: PASS — bottom-right `@a.storyof.two`.
- Wardrobe continuity: PASS_FOR_REVIEW — this proof establishes the sequence outfit lock: Aachu in white shirt, denim, blue-red scarf, cream tote; Zuv in navy top, tan pants, white sneakers, watch.
- Style: PASS_FOR_REVIEW — premium watercolor-and-ink feel is closer than earlier variants.

## Slide 6 Humor Proof QA

- Image size: PASS — `1122x1402` matches native 4:5.
- Palette: PASS — paper RGB `(243,234,218)`, paper saturation `0.101`, paper B/G `0.932`, yellow-band fraction `0.024`.
- Main text: PASS — exact readable line, `Next time, car se.`
- Wardrobe continuity: PASS_FOR_REVIEW — Aachu keeps white shirt, denim, blue-red scarf, cream tote and travel footwear; Zuv keeps navy top, tan pants, white sneakers and wristwatch.
- Style: PASS_FOR_REVIEW — humor reads as a small desi deadpan after the tender beat, without a new costume or prop gag.

## Continuity Repair

The prompt pack has been repaired so every slide uses the same clothes. Any
proof generated before this wardrobe lock is rejected for continuity review and
must not be packaged as final.

## Required Proof

Generate slide 5 first:

`Turns out, the view feels better with you by my side.`

It must pass:

- Aachu/Zuv identity match from actual references
- neutral warm ivory/off-white paper, not yellow/parchment
- premium Observational Intimacy watercolor-and-ink style
- exact readable on-image text
- tiny bottom-right `@a.storyof.two`
- natural seated pose and correct height/body scale

Full batch is blocked until proof passes.

Current decision: proof is ready for creator taste approval before generating
the remaining 5 slides and the separate 9:16 set.
