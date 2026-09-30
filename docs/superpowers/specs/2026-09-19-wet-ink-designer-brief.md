> **Read this first.** You know the @a.storyof.two house style from the Instagram work. This brief is **not** for Instagram. It is for the **app** — a nine-screen prototype at `/Users/himanshusharma/astoryoftwo-analysis/app` that someone holds in their hand. The illustration style contract (`config/carousel_style_contract.json`), the palette rules, and the negative prompt that bans "3D / glossy / neon" govern **generated carousel artwork only**. They do not govern this product's UI, its motion, or its WebGL layer. Exactly one deliverable in this brief goes through the carousel pipeline (§9.1), and only that one obeys those rules in full.
>
> The app's theme is **Wet Ink**: the whole app is one sheet of paper in nine states. Real ink wicks into real fibre. Nothing glows. Nothing is a lit 3D room. Your job is to produce the *substrate* — the paper, the fibre, the edges, the masks, the marks — and the small set of drawn things that sit on it.

---

## 1. The one separation that must not blur

| | Instagram carousel output | This app |
|---|---|---|
| Authority | `config/carousel_style_contract.json`, `config/rules/palette.md`, `config/rules/identity.md` | `app/src/styles/tokens.css` (seven colours) + this brief |
| Output size | 1080×1440 | 390×844 CSS px, dpr capped [1,2] → author at **780×1688** |
| Medium | watercolour-and-ink illustration, ivory paper, no outlines | real-time WebGL paper substrate + DOM UI |
| 3D allowed | **No** (hard fail) | **Yes** — this is the whole point |
| Faces | Aachu & Zuv, identity gate mandatory | **no faces anywhere in the app's own assets** |

There is exactly one crossing point: the four illustrated slides the user sees on the reveal screen (§9.1). Those *are* carousel output, and every identity/palette rule applies to them unchanged.

---

## 2. Asset manifest — everything the build consumes

Deliver to `app/public/textures/`, `app/public/fonts/`, `app/public/art/`, `app/src/assets/svg/`. Exact filenames, because the code references them literally.

| # | File | Dimensions | Format | Colour space | POT / tiling | Budget | Tier |
|---|---|---|---|---|---|---|---|
| A1 | `textures/paper-base.webp` | 780×1688 | WebP lossy q85 | **sRGB** | no (screen-aligned) | ≤ 64 KB | all tiers, first paint |
| A2 | `textures/paper-nrm.webp` | 512×512 | WebP **lossless** | **non-colour data** | **POT, seamless** | ≤ 56 KB | 2, 3 |
| A3 | `textures/deckle-edge.webp` | 2048×256 | WebP **lossless**, grayscale | non-colour data | POT, tiles in U only | ≤ 24 KB | 2, 3 |
| A4 | `textures/ink-bloom-atlas.webp` | 2048×2048 | WebP lossy q90, grayscale | non-colour data | POT, 4×4 of 512² | ≤ 180 KB | **tier 2 only** |
| A5 | `textures/postmark.webp` | 512×512 | WebP **lossless**, alpha only | non-colour data | POT | ≤ 18 KB | 3 |
| A6 | `svg/arrow-nib.svg` | viewBox 0 0 160 96 | SVG, one filled `<path>` | — | — | ≤ 1.5 KB | all |
| A7 | `svg/grease-circle.svg` | viewBox 0 0 120 120 | SVG, one filled `<path>` | — | — | ≤ 1.2 KB | all |
| A8 | `svg/tear-path.svg` | viewBox 0 0 390 40 | SVG, one open `<path>` | — | — | ≤ 0.8 KB | 3 |
| A9 | `fonts/caveat-latin-400.woff2` + `-600.woff2` | — | woff2, subset | — | — | ≤ 28 KB both | all |
| A10 | `art/house-slide-0{1..4}.webp` | **1080×1440 master**, 540×720 web derivative | WebP q82 | sRGB | no | ≤ 95 KB each derivative | all |
| A11 | `art/gallery-0{1..9}.webp` | 512×512 | WebP q80 | sRGB | no | ≤ 30 KB each | all |

**Totals that matter.** Entry JS is 88,579 B gzip today and CI fails above 92 KB — textures are *not* in that budget, but A1 + A9 are on the critical first-paint path, so 64 KB + 28 KB is the hard ceiling there. Steady-state VRAM budget is 1.5 MB (A1 0.2 MB + A2 1.0 MB + A3 0.25 MB), peaking 3.7 MB for ~2.5 s during record→printing.

**Not assets — do not produce these.** Halftone and riso dot screens, the Bayer/ordered dither matrix, the paper cockle/buckle, the ink lozenge shape, the ink-starved patchiness on the postmark, the crease shadows' animation, contact shadows, and the two-plate misregistration are all **generated in shader at runtime**. If you hand-draw them they will double-apply and look like a filter stack. See §11.

---

## 3. Per-asset production specs

### A1 · `paper-base.webp` — the sheet, and the entire reduced-motion fallback
This single image is doing three jobs, and the third is the one people forget: it is **every user's first painted frame on every tier**, and it is **the complete visual on `prefers-reduced-motion: reduce`, where no canvas ever mounts**. So it has to look finished on its own, with no shader on top. If it looks like a base layer waiting for effects, it has failed.

- 780×1688 (390×844 at dpr 2). It is never mipmapped and never tiled; non-POT is correct here.
- Content: one continuous sheet of warm paper. Visible fibre at ~0.4–0.8 mm feature scale, gentle crumple relief, and **three horizontal letter-fold creases** at y = 33.3% and 66.6% of the height, each ~6 px wide at 2x, rendered as a soft valley with a bright lip on the light side. The landing screen's fold-open animation hinges on exactly those two lines, so their positions are load-bearing, not compositional taste.
- The existing CSS it replaces is `radial-gradient(120% 80% at 50% 0%, #fbf7ee 0%, var(--paper) 55%, var(--paper-shadow) 100%)` in `app/src/components/PaperBackground.tsx`. Keep that top-to-bottom luminance ramp — bright at the top (`--paper-backlit #fbf3e2`), `--paper #f6f1e7` through the middle, `--paper-shadow #e7dfcf` at the bottom edge. The new image should read as *the same sheet, now actually made of paper*.
- **No baked lighting direction beyond that vertical ramp.** The runtime key light is at 14° elevation and its azimuth drifts ±6° over 9 s; a baked raking highlight will fight it and produce a visible double-shadow.
- **Paper-tone gate, non-negotiable:** run `pipeline/agentic/checks/palette.py` against this file before delivering. Same thresholds as the carousel: brightest-15% region median R ≥ 230, median saturation < 0.18, median blue/green ratio ≥ 0.85, yellow-band (hue 35–65°, sat ≥ 0.35) pixel fraction < 0.05. Paper that reads yellow/parchment on a phone is this project's most common rejection and it is a hard fail here too. When in doubt go **cooler**, not warmer.
- WebP q85. Check for banding in the smooth upper third at 100% on an OLED phone; if you see it, add ~1.5% monochrome dither before encoding rather than raising quality.

### A2 · `paper-nrm.webp` — fibre, and the reason any of this reads as paper
Channel-packed, and the packing is exact:

- **R** = tangent-space normal X, **G** = tangent-space normal Y (**OpenGL convention, +Y up**; a DirectX green-flip inverts every fibre under a 14° key and the sheet will look embossed inside-out), **B** = roughness remapped to the narrow band 0.88–0.96 around `--paper-roughness 0.92`, **A** = unused, leave fully opaque.
- 512×512, **seamless**, and here is the part that is easy to get wrong: **bake the machine direction in at 12° from horizontal** and make the tile seamless *at that orientation*. `--grain-direction: 12deg` is the spine of the whole theme — the ink wicks 1.8× further along it and the cockle ridges run parallel to it — and the shader does **zero UV rotation**, because rotating a tile breaks its seams.
- World scale: this tile maps to **40 mm** of real sheet, so it repeats roughly twice across the 390 px frame. Author fibre at that scale. Grain that reads correctly on your 27" display is roughly 4× too coarse on the phone.
- **Lossless WebP, no exceptions.** Lossy compression on a normal map at 14° raking incidence produces visible 8×8 terracing across the whole sheet — the low elevation angle is precisely what amplifies small normal error into a large shading error. This is the single most likely way the theme ships looking cheap.
- Source: start from a CC0 paper-card normal/roughness pair (Poly Haven `paper-card` or ambientCG), re-orient to 12°, re-tile, tint nothing. **Discard the source albedo entirely** — albedo comes from A1 and the tokens.

### A3 · `deckle-edge.webp` — the sheet's edge profile
Grayscale height/alpha strip. U tiles along the sheet edge; V is the profile, 0 at the outside (air) through 1 at solid paper, with the transition occupying the middle ~40% of the height. Irregular at a 3–14 mm period, no repeating signature bump — if the eye can find the loop, the sheet reads as wallpaper. Used for the sheet's outer edge and the torn card edges. Lossless.

### A4 · `ink-bloom-atlas.webp` — tier-2 only, the recorded version of the live solve
Fetched **only** when the device can't run the fluid solve (no WebGL2, no `EXT_color_buffer_half_float`, or sustained perf decline). 2048×2048, **4×4 grid of 16 frames at 512²**, read left-to-right, top-to-bottom, played at 12 fps to cover ~1.3 s of bloom.

> Production note: the theme spec says 24 frames. 24 does not fit a power-of-two sheet at a usable frame size — 16×512² does, and the difference is invisible at 390 px through a soft ink mask. If 24 turns out to matter, the upgrade is a second 2048² sheet, not smaller frames.

Each frame is a single ink drop wicking outward on paper, grayscale, 0 = dry paper, 1 = saturated ink. **The lozenge must be anisotropic: 1.8× longer along the 12° grain axis than across it**, matching A2's orientation exactly. Edges are fractal and fibrous, never a soft Gaussian circle — the whole reason for this asset is that a Gaussian blur does not look like ink on paper. Render offline at high quality; this is where you can afford fidelity you cannot afford at runtime. Single channel — encode grayscale, do not ship RGB.

### A5 · `postmark.webp` — alpha only, and deliberately clean
512×512, **alpha channel only** (the shader tints it `--accent` and applies its own fbm-thresholded erosion for ink starvation). Hand-drawn circular postmark, ~460 px diameter inside the frame, with the @a.storyof.two mark or a simple date-ring — text inside it must stay legible when it lands at 6° rotation and roughly 90 px on screen, which means no type smaller than ~1/12 of the diameter.

**Do not pre-distress it.** Deliver a full, clean ink impression. The patchiness is procedural and will double-apply over hand-drawn patchiness, producing a stamp that looks dissolved rather than ink-starved.

### A6–A8 · The hand-drawn vectors
All three are **filled variable-width outline paths**, not strokes. A constant-width `stroke` has no nib pressure and reads as a computer line; the app currently uses one in `HandDrawnArrow.tsx` and replacing it is an explicit part of the theme.

- **A6 `arrow-nib.svg`** — replaces the existing arrow on the landing and review screens. Thin at entry, swelling through the curve, thin at release, with the arrowhead as part of the same closed path. Single `<path>`, no groups, no transforms, `fill="currentColor"` so it inherits `--ink`. It is revealed by a sweeping `clipPath` over 1.1 s with a dwell at 85% — so **draw it as if a right hand made it in one stroke, left to right**, and keep the path's point order in that same drawing direction.
- **A7 `grease-circle.svg`** — the editorial "this one" mark that circles a selected photo. Slightly open circle, overshooting itself at the close, heavier at the start of the stroke. Same drawing-direction rule: it draws in 0.22 s and **erases in 0.14 s in reverse**, and that asymmetry only reads as a real hand if the path order is the hand's order.
- **A8 `tear-path.svg`** — a single open polyline across 390 px describing the *macro* jaggedness of a sheet torn from a pad. 20–40 points. The shader warps it with fbm at higher frequency, so give it the big irregular rhythm only; fine whisker detail is cut (imperceptible at 390 px, expensive to tune).

---

## 4. Type and layout

**There is a live bug you need to know about before you set any type: Caveat is never loaded.** `app/index.html` has no font link and there is no `@font-face` anywhere in the project, so `--font-hand: 'Caveat', 'Bradley Hand', cursive` currently resolves to Bradley Hand on iOS and to a generic system cursive on Android. The app's entire handwriting layer is, today, not rendering as designed on most devices. Deliver **A9**: Caveat 400 and 600, latin subset (U+0000–00FF, U+2018-2019, U+201C-201D, U+2026), woff2, `font-display: swap`, ≤ 28 KB combined, self-hosted — not a Google Fonts `<link>`, which adds a third-party round trip to first paint on a screen that is meant to feel like paper appearing.

**Georgia has the same exposure in the other direction.** `--font-body: 'Georgia', 'Times New Roman', serif` — Georgia ships on iOS and Windows but **not on Android**, which falls back to Noto Serif with noticeably different metrics and a lighter colour. Review every screen on a real Android device at 390 px and record whether the fallback is acceptable. If it is not, the fix is a subsetted serif webfont and that is a decision for the creator, not a silent substitution. **Flagged as an open question, not something you resolve alone.**

Roles, unchanged from what ships today — do not reassign them:
- **Caveat** — the seconds counter on record, the carousel caption (22 px), the brandmark. Anything that is the app's own handwriting.
- **Georgia** — all prompts, all body copy, all button labels. The voice of the product.
- Copy itself lives in `app/src/content/copy.ts` and is **not yours to change**. It is written and approved. If a layout can't hold a line, the layout moves.

**Layout constants.** 390×844 inside a `PhoneFrame` with a 44 px corner radius and a 10 px black bezel. `--space: 16px`, `--radius: 20px`. Respect a 16 px minimum side gutter and keep every touch target ≥ 44×44. Text is never rendered in WebGL — Caveat and Georgia stay crisp, selectable DOM, and the canvas is `aria-hidden` for its entire life.

---

## 5. Palette discipline

`app/src/styles/tokens.css` is the **only** colour authority for the app surface. Seven values:

```
--paper #f6f1e7   --paper-shadow #e7dfcf   --ink #2b2622
--ink-soft #6b6258   --accent #c2462f   --hairline #d8cfbd
```

Plus exactly **three** derivations, each an observed condition of an existing token, not a new brand colour:

```
--ink-wet       #1c1814   -- --ink while wet; dries to --ink over 1800ms
--paper-backlit #fbf3e2   -- --paper with light behind it, at the page-turn apex
--overprint     #241b19   -- Beer-Lambert product of --ink over --accent;
                             exists only where both plates touched the same fibre
```

Rules that get checked:
- **No asset may contain a colour outside those ten.** Deliver a swatch strip with each raster asset showing its sampled dominant colours against the token hexes; anything beyond ΔE 4 of a token is a revision.
- **Nothing emits light.** Emissive is 0.0 everywhere. No bloom, no glow, no environment map, no reflections — reflections turn paper into plastic.
- **Shadows tint to `--paper-shadow`, never to grey and never to black.**
- **`--accent` is rationed.** In the whole app it appears on: the "begin" button, the star impressions, the second riso plate, the postmark, and the active mic state. That is the complete list. A sixth use dilutes the five.
- **Grain belongs to the sheet and to the printed artefact, never to controls.** `MicButton`, the carousel chrome, the star row, the `HelloScreen` inputs and the share-target buttons stay clean flat `--paper`/`--ink`/`--accent` with no paper texture. The moment fibre creeps onto a button, the app stops being made of paper and starts being a paper-themed skin. This is the single easiest rule to break by accident.

---

## 6. Depth-layer separation of illustrated art

**Zero layers. Not in scope. Do not produce it.**

The depth-map 2.5D parallax on the reveal screen was considered and **cut deliberately**: at the sub-2% displacement that keeps it tasteful it is invisible on a 390 px frame, and above that it becomes the 2018 fake-3D-photo trick, which is the opposite of intimate. The reveal's payoff is instead the *residual paper cockle* from the record screen raking across the finished piece — which is free, is the concept's own thesis, and needs no new art.

So: **the four house slides ship flat, single-layer, fully composited, at 1080×1440.** No PSD layer exports, no alpha cut-outs, no depth maps, no background plates.

For the record only, if parallax is ever revived it would be 3 layers, not 5 — background wash / figures / foreground prop — each a straight-alpha PNG with 64 px of painted bleed beyond its silhouette and a 4-band greyscale depth map. **Do not build this now.** It is here so nobody rediscovers it as a new idea in month two.

---

## 7. Per-screen art direction

Nine screens, one sheet. The sheet is never cut and never cross-faded; each step is that same sheet changing state.

**1 · landing** — `LandingScreen.tsx`. The sheet arrives **folded in three**, creases from A1. Zero WebGL on this screen, permanently: it must never pay for the 3D chunk. Your assets here are A1 and A6 only. The "+" button sits on the top panel. The disclaimer overlay card is the *same folded paper*, not flat `--paper`.

**2 · hello** — `HelloScreen.tsx`. The sheet is now flat and matches the fold-open's final state exactly. Choosing a relationship chip **debosses** the sheet 0.5 mm under it; committing a name field seeds wet ink at the field's baseline. Your names soak into the sheet you will send. All DOM is byte-identical to today — same chips, same `--hairline` borders. Only the surface under them changes. Chips and inputs get **no** paper texture (§5).

**3 · photos** — `PhotoSelectScreen.tsx`. The 3-column grid becomes a **contact sheet**: gutters show fibre, cells read as printed cells. The accent outline and ✓ badge are removed and replaced by **A7**, the grease-pencil circle — the actual editorial gesture for "this one". Selected cells lift 0.4 mm off the sheet with a real contact shadow. Unselected keep their 0.85 opacity and read as unprinted.

**4 · review** — `PhotoReviewScreen.tsx`. The chosen photos are **laid onto** the sheet at a 1.5° random rotation, top-left corner curling, sheet bowing underneath. Each is run through an ordered-Bayer dither quantised toward `--ink`/`--paper`/`--accent`, so a stranger's photograph reads as *printed onto* the sheet. This is what stitches a user's own pictures into the brand — and it is why A11's tonal range matters (§9.2).

**5 · record** — `RecordScreen.tsx`. **The signature screen.** The sheet is clear. The live mic RMS drives a real ink nib at the sheet's centre; silence lifts the nib and nothing is injected, so a pause reads as the sheet waiting — which matters, because the copy already says "take your time." Ink wicks in a lozenge, longer along the 12° grain. Where the user paused and ink pooled it is genuinely darker (Beer-Lambert absorption, not more opacity). The sheet **cockles** into ridges parallel to the grain, caught by the raking key; the Caveat seconds counter sits on that buckled paper and its baseline tilts as a ridge passes under it. Your assets: A2 (fibre, orientation critical), A4 (tier-2 recording of the same thing).

**6 · printing** — `PrintingScreen.tsx`. The sheet becomes a **two-plate riso press**. Plate one lays `--ink` at 105° with the dot radius ramping 4.2 px → 0.9 px, so the greeting copy literally resolves from coarse to crisp. The image **completes in one colour and the press stops** — the sheet looks finished. Then plate two drops `--accent` at 45°, misregistered by 1.7 px, and the camera pushes to macro on one overlap region and holds 400 ms: two dot grids at different angles, neither aligned, and in the overlap a warm dark `--overprint` that is on neither plate. That 400 ms frame is the screenshot, and it is the only macro moment in the app. **Both screens are shader-generated — you produce no halftone assets.**

**7 · reveal** — `RevealScreen.tsx`. The printing→reveal transition is **the page turn**. At the apex, edge-on to the raking key, the printed ink glows *through* from the other side, mirrored, against `--paper-backlit`. After the turn the slides are crisp DOM `<img>` — **A10**, your four illustrations. The record screen's residual cockle rakes visibly across the finished piece.

**8 · rate** — `RateScreen.tsx`. The stars are not glyphs on paper, they are **stamped into it** — a 0.5 mm deboss with `--accent` ink filling the impression. The ★ characters stay as DOM hit targets with their `aria-label`, rendered in `--paper` against the ink-filled hole, so what you see is the hole, not the character. **The unforgiving rule:** re-tapping to a *lower* rating leaves the extra impressions as **blind embossing with no ink**, because you cannot un-press paper. Expect at least one user to report this as a bug. It is not.

**9 · send** — `SendScreen.tsx`. The sheet is **torn from the pad** (A8 + A3), **folded in three** on the same hinges as the landing fold, and **sealed** with A5 at 6°. The rating impression from the previous screen is visible in the folded corner — the rating is physically on the letter, not hidden in state. The share list rises as DOM buttons over the folded letter, which stays visible behind them, folded, waiting. The existing note — "no downloads — this is meant to be given, not saved" — is now literally true on screen: nothing in this app ever travels toward the viewer. It leaves.

---

## 8. What the paper remembers

One rule that crosses every screen, because it is the concept in one sentence: **every mark is permanent within a session.** Ink dries and stays. A pressed impression never lifts. 18% of the record screen's cockle survives drying and is still raking across the finished carousel four screens later. Nothing you design may assume a clean sheet after step 2.

---

## 9. Assets made with the house illustration pipeline

### 9.1 · A10 — the four reveal slides (`art/house-slide-01..04.webp`)

These replace the `picsum.photos` placeholders currently in `app/src/content/houseSlides.ts`. They are the only asset in this brief that is genuine carousel output, and **every rule in `config/rules/identity.md`, `config/rules/palette.md` and `config/carousel_style_contract.json` applies to them without exception.** Produce them through `scripts/carousel.py` on the four-gate v3 package contract — not by hand, not ad hoc.

**Non-negotiables, restated because they are the things that get skipped:**
- **Exactly four actual Aachu/Zuv photographs attached to every generation call**, selected from `config/references/identity/` in the four bundle roles: face anchor, body/posture anchor, wardrobe/context anchor, emotion/detail anchor. Generated character charts, contact sheets and prior illustrations are supplemental comparison aids only and can never occupy one of the four slots. Text-only identity is `BLOCKED_FOR_IDENTITY_STYLE_REFERENCES`, never "final".
- **Signature accessory gate.** Aachu's evil-eye bracelet on her **right** wrist whenever that wrist or forearm is visible; Zuv's small round evil-eye locket on a slim silver chain whenever his neck, open collar or upper chest is visible. A visible neck without the locket is a hard fail. Credible occlusion is allowed only if the prompt and QA record it as hidden.
- **Height gate.** Zuv 5'8", Aachu 5'6". Eye-line and shoulder positions in any two-shot must reflect that two-inch difference. Aachu reading tiny or Zuv reading oversized is a regenerate.
- **Identity eval stop gate.** Proof slide 01 first, structured `identity-consistency-review.json` or `visual-qa.json` with reference IDs and specific likeness notes, creator review — *then* the remaining three. No identity eval, no next slide. "Looks good" is not an identity pass.
- **Paper tone lock.** If the paper reads yellow/parchment on a phone, reject even if everything else passes. Default cooler.

**Story beats** — these four slides are the generic house story shown to every user while their own story is "drawing", so they must feel like the channel, not like this one user:

1. the day one of them first really saw the other
2. a small ordinary shared ritual (the mid-beat)
3. a moment of friction resolved without words (the mid-beat)
4. and still, the two of them

Captions are already templated in `houseSlides.ts` and are **integrated final text on the image** per the contract's `strategy: integrated_final_text` — `#2a2621` on `#fbf4e8`, max 18 words, max 3 lines, generous clean upper-middle paper space, never covering faces, hands, props or gestures. Tiny low-contrast handwritten `@a.storyof.two` at top-right.

**Exact generation prompt** — the locked style profile verbatim, with the scene appended. Do not paraphrase the style clause:

```
Cinematic Observational Watercolor-and-ink story frame on neutral warm-ivory paper
grain: a candid, physically specific lived moment rather than a posed portrait;
believable motivated light; clear foreground, midground, and background; natural
asymmetry; precise microexpressions and body language; two to four narrative details
that imply the beat before and after; fine graphite and ink contours, transparent
layered pigment blooms, tactile fabric, hair, wood, and ceramic detail, a restrained
muted denim, navy, terracotta, sage, and skin-tone palette, and soft organic edges
fading into paper.

SCENE: <one observable physical event, stated as an action with a verb — not a mood,
not an adjective. e.g. "Aachu, mid-sentence, reaches across a cafe table and turns
Zuv's coffee cup so the handle faces him, without looking at it.">
IDENTITY: Aachu and Zuv per the four attached photographs. Aachu's evil-eye bracelet
on her right wrist (visible/occluded: <state which>). Zuv's round evil-eye locket on a
slim silver chain (visible/occluded: <state which>).
WARDROBE: <drawn from the attached identity photographs only — never a fixed menu.
State any conservative extension explicitly.>
ON-IMAGE TEXT: "<exact approved caption>" in #2a2621, upper-middle clean paper space,
max 3 lines, not covering faces, hands, props or gestures.
BRANDMARK: tiny low-contrast handwritten @a.storyof.two at top-right.
DIMENSIONS: 1080x1440.
```

Negative prompt — the locked one, verbatim, unchanged:

```
No photorealism, 3D, glossy AI-stock, generic-watercolor, vector, anime, doll faces,
generic couples, staged symmetry, clutter, empty depth, unmotivated glow, yellow,
mustard, sepia, parchment, beige, heavy-cream paper, posters, quote-cards, UI,
split-screens, extra people or limbs, duplicate couples, malformed hands, broken
contact, invented or misspelled copy, missing text or brandmark, unrequested logos.
```

**A framing problem you must design around.** `app/src/components/Carousel.tsx` sets `aspectRatio: '9/11'` (0.818) with `objectFit: 'cover'`, but the masters are 1080×1440 (0.75). The image is scaled to fill the width and **~8.3% of its height is cropped, ~4.2% off the top and ~4.2% off the bottom.** Until that component is changed to `3/4`, keep a **6% safe margin at top and bottom** with nothing load-bearing inside it — and note that the top-right brandmark currently sits *inside the crop zone*. Raise it. This mismatch is worth fixing in code, but design to survive it either way.

**Deliver both:** the 1080×1440 master into the normal carousel archive, and a 540×720 WebP q82 web derivative (≤ 95 KB) into `app/public/art/`. The app never loads the master — a 1080×1440 PNG on a 390 px frame is four times the pixels for no visible gain and a real memory cost on a mid-range phone.

### 9.2 · A11 — the nine sample gallery photos (`art/gallery-01..09.webp`)

These are **not** house illustrations and must not be generated by the illustration pipeline. They stand in for a stranger's camera roll in `app/src/content/sampleGallery.ts` (currently picsum placeholders). They must read as **ordinary phone photographs of an ordinary couple** — if they look illustrated, the review screen's dither has nothing to do and the "your photos become printed" beat dies.

Sourcing: licensed stock or the creator's own images. **Not scraped, and not photographs of identifiable people without a release** — these ship in a product people hold.

Art direction, driven by the dither pass they go through on the review screen:
- Mid-key. Histogram substantially inside 15–85% — blown highlights dither to flat paper and crushed shadows dither to a solid ink block, and both look broken.
- Clear subject/ground separation at **110 px** (the real cell size). Check them at that size, not at 512.
- Warm, domestic, unposed: hands, a table, a doorway, a shared meal, a walk. No stock-smile eye contact with the camera.
- 512×512 square, centre-safe composition (the grid crops to square), WebP q80, ≤ 30 KB each.

---

## 10. Delivery, naming, QA

- Exact paths and filenames from §2 — the code references them literally.
- Every raster asset ships with: a PNG source at delivery resolution, the encoded WebP, and a one-line note stating its colour space (`sRGB` or `non-colour data`). Mis-tagging A2 or A3 as sRGB applies a gamma curve to normal vectors and the lighting will be subtly, unfixably wrong.
- SVGs: single `<path>` each, no `<g>`, no transforms, no inline styles, `fill="currentColor"`, viewBox as specified, run through SVGO.
- **Raking-light proof.** Deliver one render of A1+A2 lit by a single key at **14° elevation, 312° azimuth**, at 390×844, no other lights, no environment. If the fibre is invisible in that render, the maps are too soft; if it looks like stucco, too strong. That render is the acceptance artefact for the substrate, not a screenshot in your own lighting setup.
- **Paper-tone check.** `pipeline/agentic/checks/palette.py` run against A1 and every A10 derivative, output attached.
- **Size check.** Every file at or under its §2 budget, measured after encoding.
- **Phone check.** A1, A10 and A11 reviewed on a real phone at arm's length, not on a desktop display. "Heavy cream looks fine on the rendering screen and reads yellow at phone distance" is a documented failure in this project.

---

## 11. Do NOT produce — the brand-breaking directions, already rejected

These were considered and killed. Producing any of them is rework, not exploration.

**Rejected because they belong to no one:**
- Dark hero with an iridescent blob, gradient mesh, or aurora background.
- Volumetric god-ray light shafts and floating dust motes. This is Awwwards house style since 2019 and it is anonymous.
- Glassmorphism, frosted panels, neon, cyberpunk, chrome, glowing edges, border beams, "thinking orb" / voice-glow blobs.
- Bloom, chromatic aberration, lens flare, depth-of-field vignettes, film grain overlays as a *filter*.
- Any particle system.

**Rejected because they are the wrong object for this brand:**
- A modelled printing press, wooden desk, brass crank, coffee mugs, paper-path lever — any skeuomorphic machine. A machine is the wrong emotional register for a product whose copy says "this is meant to be given, not saved."
- A dark scene (`#15110d` as the *frame* colour rather than the surround behind the phone). Turning the frame dark to make something read is the moment this brand stops being paper.
- A lit room, a diorama, a tunnel book, illustrated figure cut-outs as depth layers.
- Illustrated characters anywhere in the app's own chrome. Aachu and Zuv appear in the four reveal slides and nowhere else.

**Rejected because the shader already does it and yours will double-apply:**
- Hand-drawn halftone or riso dot screens, or a drawn misregistration offset.
- A drawn Bayer/dither pattern or a pre-dithered photo.
- Pre-distressed, pre-eroded, or pre-ink-starved stamps and marks.
- Baked drop shadows, baked contact shadows, or a baked raking highlight on A1.
- Drawn paper buckle, cockle ridges, curl or fold shading beyond the three static creases.

**Rejected on craft grounds:**
- Constant-width stroked "hand-drawn" lines. Every drawn mark is a filled variable-width outline.
- Any colour outside the seven tokens and three derivations, including "just a slightly warmer paper" — that is the yellow-paper failure arriving by a side door.
- Paper texture on any button, input, chip, or control.
- Fine detail that is only legible above thumb scale. It gets zero budget and is not a reviewable feature.

---

## 12. Sequence — what to deliver first

The build is phased and the early phases ship on their own, so the assets are wanted in this order:

1. **A9** (Caveat woff2) and **A1** (paper base) — these two unblock Phase 0 and Phase 1, which ship with **zero three.js** and already make the app feel more like paper. A1 also completes the reduced-motion tier permanently.
2. **A2** (fibre normal/roughness) — unblocks Phase 2, the record screen, which is the kill gate for the entire theme.
3. **A4** (ink atlas) — tier-2 fallback, needed by the end of Phase 2 so iOS behaviour can be measured on real hardware in week one.
4. **A10** (four house slides) — Phase 3, and the long pole because of the identity stop-gate; start the proof slide early even though the asset lands later.
5. **A6, A7, A11** — Phase 4/5.
6. **A3, A5, A8** — Phase 6, cut first if the budget moves.
