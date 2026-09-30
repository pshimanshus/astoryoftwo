# EP01 · Shot 2 — Higgsfield Prompt (attempt 2)

status: READY — awaiting credits
supersedes: attempt 1, job `46f440c9-7370-4746-bea6-202e5293a509`
model: `nano_banana_pro` · 9:16 · 2k · 2 credits
style authority: `video/references/style-prompt-higgsfield.md`

## What Attempt 1 Got Wrong

| Fault | Cause | Fix in this prompt |
|---|---|---|
| Cartoon — outlines around every form | `fine graphite and ink contours`, copied from the carousel contract | Replaced with the photoreal-painted block; `no outlines of any kind` is now load-bearing |
| Drawn picture-frame border, art inset on paper | Nothing forbade it | `bleeds to the edge of the canvas`, plus explicit negative |
| Too tight — he filled the doorframe | "medium-wide" alone was too weak | Framing stated as a proportion of the frame, twice |
| Incoherent space — stairwell *and* living room both behind him | Camera position never fixed | Camera position stated explicitly; only the landing is visible through the door |
| Wardrobe drifted to denim-on-denim | Wardrobe under-specified | Colours named |

## Attachments

| Role | Value |
|---|---|
| Element (identity) | `<<<e4c9ff5b-0876-4c5b-8848-65f3e7ddaa0b>>>` — "zuv", already created |
| `medias` image_references | `79de07d8-fe5e-47ab-bf59-7983bff37568` — style board, already uploaded |

Both are permanent. No re-staging needed.

## Prompt

```text
Photographic realism finished as watercolour and gouache on warm ivory paper with visible paper tooth. A single man, <<<e4c9ff5b-0876-4c5b-8848-65f3e7ddaa0b>>>, stands alone in the open front doorway of a small lived-in Indian flat in the evening, just home from work and not yet stepped inside.

CAMERA AND FRAMING — hold this exactly: the camera is INSIDE the flat, at standing eye level, looking straight at the front door across an open room. The man is small in a tall vertical frame: his head reaches only about half the frame height and there is a large expanse of quiet empty wall and room above and around him. He is not close, not cropped, and does not fill the doorway. The painting bleeds to the edge of the canvas on all four sides.

Through the open door behind him there is only a dim stairwell landing — warm, low, out of focus. The living room is on the camera's side of the door and is therefore NOT visible behind him; nothing of a sofa, lamp or rug appears beyond the doorway.

He is exactly one person and the only person in the image. His work bag is still on his shoulder, his right hand hooked under the strap letting it slide down; his left arm hangs loose and slightly behind his hip, fingers relaxed. He is tired in an undramatic, depleted way: shoulders dropped, jaw slack, gaze unfocused toward the middle of the room. Not crying, not grieving, not touching his face.

Real human anatomy, true proportion and photographic likeness. Genuine skin texture with pores and natural tone variation. Real fabric weave rendered as painted surface rather than drawn shape: a worn-in dark olive cotton work shirt with the collar open and sleeves pushed up, charcoal creased trousers, leather shoes, both feet flat just inside the threshold. An evil-eye locket on a slim silver chain is clearly visible at his open collar.

Form is defined entirely by value, edge and pigment: there are no outlines of any kind anywhere in the image. Soft dry-brush edges, transparent layered washes, visible pigment granulation settling into the paper. The man is held sharp and fully detailed; the room and the stairwell dissolve into loose impressionistic wash and soft broken dabs. Naturalistic motivated light — warm dim landing light rimming his shoulder and hair, soft cool ambient fill from the flat keeping his face readable. Gentle contrast, restrained muted palette of cream, olive, denim blue, warm grey, terracotta and natural skin tone.

No ink outlines, no line art, no drawn contours, no linework of any kind, no comic or graphic-novel look, no cel shading, no flat colour fills, no cartoon, no anime, no storybook illustration, no clip art. No drawn border, frame, panel edge or vignette around the image. No photorealistic 3D render, no glossy AI-stock, no beauty-filter smoothing, no plastic skin. No yellow, mustard, sepia, parchment or beige paper. No text, words, lettering or watermark. No second person, no woman, no reflection, no silhouette on the stairs, no duplicate figures, no extra limbs, no malformed hands. No close-up crop, no tight framing, no living room visible through the doorway.
```

## Acceptance Checks

Style first this time — it is the thing that failed.

- [ ] **No outlines anywhere.** Form carried by value and edge only
- [ ] Reads as a painted photograph, not a drawing or comic panel
- [ ] Real skin texture and real fabric weave, not flat fills
- [ ] **Paint bleeds to all four edges** — no drawn border or inset panel
- [ ] He occupies roughly half the frame height, with real air above
- [ ] Only a dim stairwell landing behind him — no sofa, lamp or rug through the door
- [ ] Dark olive shirt, charcoal trousers — not denim-on-denim
- [ ] Locket and silver chain present at the open collar
- [ ] Exactly one person; no reflection or silhouette
- [ ] Both hands correct — right on the strap, left loose, five fingers
- [ ] Zero text in the image
- [ ] Warm ivory paper, not yellow or parchment
- [ ] **Likeness: is this Zuv?** — creator's call, not the agent's

## Note

Wardrobe locked here as dark olive shirt + charcoal trousers. This matches
`video/series/character-lock-ep01.md` and the style evidence better than attempt
1's denim-on-denim. Whatever ships becomes canon for shots 4, 5 and 6 — so if you
prefer the denim, say so before this runs, not after.
