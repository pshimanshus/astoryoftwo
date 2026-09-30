# Style Prompt — Higgsfield Models

status: ACTIVE for the video line on Higgsfield
scope: **Higgsfield models only** (nano_banana_pro / nano_banana_2 / seedream / gpt_image_2)
do not change: `config/carousel_style_contract.json` — the carousel path is unaffected

## SETTLED 2026-09-05 — Higgsfield Cannot Produce This Style

Tested conclusively. The repo's canonical master prompt was run **verbatim** on
`nano_banana` — same template, same HOUSE STYLE, same ESSENTIAL NEGATIVES that
produce the account's published work on Codex ImageGen. Result: heavy ink
outlines on every form, a drawn border with paper margin, comic-book register,
and the mandatory locket dropped. The exact opposite of the target.

Three further attempts with corrected, model-specific wording got closer but
never arrived: full-bleed failed every single time, because the model renders
*a watercolour painting as an object* rather than *a photograph finished as
watercolour*. That is a category difference no prompt reaches.

**Conclusion: stills come from Codex. Motion comes from Higgsfield.** Do not
spend further credits chasing the still register here. The blocks below remain
useful only for throwaway tests and previews, never for shipped frames.

## Why This File Exists

On 2026-09-05 the first Higgsfield render of EP01 shot 2 came back **cartoonish**:
drawn outlines around every form, flat fills inside them, a comic/graphic-novel
face. Style board attached, prompt taken verbatim from the style contract.

The board was not the problem. The board is correct. The prompt was.

**The phrase `fine graphite and ink contours`** — copied straight from the style
contract's `generation_prompt` — reads to these models as *line art*. It produced
exactly what it says: contours. The account's actual visual style has **no
linework whatsoever**.

The contract's prompt is **model-tuned**. It evidently behaves on the ImageGen
path the carousel line uses. It does not transfer. That is what this file fixes,
and it is why the shared contract stays untouched.

## What The Style Actually Is

Read the evidence in `video/references/style-evidence/` and the style board at
`config/references/style-lock/cinematic-observational-watercolor-v1/contact-sheet.png`.

It is a **photograph finished as a painting** — not a drawing:

| Real style | What "ink contours" produced |
|---|---|
| Photographic anatomy, proportion, readable likeness | Stylised, cartoon proportions |
| Real skin texture, pores, tone variation | Flat skin fills |
| Real fabric weave — knit, denim, corduroy | Flat cloth shapes |
| Form defined by **value and edge** | Form defined by **outline** |
| No lines anywhere | Ink contour on every form |
| Background dissolving into loose wash | Background drawn and outlined |

## Positive Style Block — use verbatim

```text
Photographic realism finished as watercolour and gouache on warm ivory paper with visible paper tooth. Real human anatomy, true proportion and photographic likeness; genuine skin texture with pores and natural tone variation; real fabric weave — knit, denim, corduroy, cotton — rendered as painted surface rather than drawn shape. Form is defined entirely by value, edge and pigment: there are no outlines of any kind anywhere in the image. Soft dry-brush edges, transparent layered washes, visible pigment granulation settling into the paper. Subjects held sharp and fully detailed; the background dissolving into loose impressionistic wash and soft broken dabs. Naturalistic motivated light, gentle contrast, restrained muted palette of cream, olive, denim blue, warm grey, terracotta and natural skin tone.
```

## Negative Block — use verbatim, do not trim

The first clause is the one that matters. Everything after it was earned from a
real failure.

```text
No ink outlines, no line art, no drawn contours, no linework of any kind, no comic or graphic-novel look, no cel shading, no flat colour fills, no cartoon, no anime, no storybook illustration, no clip art. No drawn border, frame, panel edge or vignette around the image — the painting bleeds to the edge of the canvas. No photorealistic 3D render, no glossy AI-stock, no beauty-filter smoothing, no plastic skin. No yellow, mustard, sepia, parchment or beige paper. No text, words, lettering or watermark. No extra people, duplicate figures, reflections, silhouettes, extra limbs or malformed hands.
```

## Standing Rules

1. **Never paste the carousel contract's `generation_prompt` into a Higgsfield
   call.** Use the blocks above. The contract stays authoritative for the
   carousel path and for identity/palette policy; only its model-facing style
   wording is wrong here.
2. **"No outlines" is the load-bearing instruction.** If a render comes back
   cartoonish, that clause was weakened or dropped. Restore it before changing
   anything else.
3. **"Bleeds to the edge of the canvas"** prevents the drawn picture-frame border
   that appeared in attempt 1 — a hard fail for a video frame.
4. The style board still gets attached on every call. It was always right.
