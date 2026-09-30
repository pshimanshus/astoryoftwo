# EP01 — Angle Coverage & Continuity Spec

companion to: `ep01-the-plate.md`
status: audit complete — one blocker before generation
authority: `config/references/identity/_dossier/identity-generation-preflight.md`

Video breaks identity in a way stills do not. A carousel slide only has to be
right once. Six shots have to be right *and* agree with each other. This document
says what each shot needs, what the packet already covers, and what is missing.

---

## What Each Shot Needs

| # | Who | Angle & distance | Lighting | Accessories in frame |
|---|---|---|---|---|
| 1 | Aachu | Rear three-quarter, seated cross-legged on floor, head turning to camera-left | Warm door-light from behind | Bag strap across chest **(plot-critical)**, right wrist possible |
| 2 | **Zuv** | **Front / near-front, standing, medium-wide, full upper body** | Doorway backlight, face in soft fill | **Neck and collar — locket and chain** |
| 3 | Aachu | Front, seated, **upward gaze** at a standing figure | Laptop glow + room ambient | Right wrist as she closes the laptop |
| 4 | Both | Two-shot, wide, him lowering to floor | Room ambient | Both possible |
| 5 | Both | **Hands are the subject**, faces mid-distance | Laptop glow returning | **Right wrist bracelet is centre-frame** |
| 6 | Both | Wide two-shot, seated, shoulders touching | **Underlit — screen glow from below** | Both possible |

## Coverage Audit

**Aachu — good.** `curated-v3/` provides master front, shallow three-quarter,
deeper three-quarter, and close smile, plus 15 `together/` frames. Shots 3–6 are
covered. Shot 1's rear three-quarter is not in the packet, but it is the lowest
identity-risk frame in the film, so interpolation is acceptable there.

**Zuv — sufficient. Do not expand.** The operational packet is one solo file,
`config/references/identity/zuv/portrait-07.jpg`, carried by the couple anchors
`together-18.jpg` and `together-16.jpg`.

An earlier draft of this document called that a blocker and proposed curating a
four-image Zuv packet from the 14 files in `~/Desktop/Identity Images /Zuv
Images/`. **Creator overruled it on 2026-09-05, and the standing rule is now:**

> More reference photographs cause more distortion, not less. Additional
> references make the model average across them instead of locking to one face.
> One clean anchor plus the couple frames is the correct input.

This matches what the preflight already specifies — the standard bundle is one
Zuv solo, not a packet. Aachu's `curated-v3` exists because solo Aachu
visible-face work needed view-specific selection, not because more is better.

Applies to the wedding photographs in `video/references/identity-evidence/` too:
they are provenance and cross-check material. **Do not add them to generation
calls.**

## Continuity Risks Specific To This Episode

**1. The accessories are in the hard-fail list, and shot 5 puts one of them
centre-frame.** The dossier fails any generation where Aachu's right-wrist
evil-eye bracelet changes side or design, or where Zuv's neck is visible without
the evil-eye locket and slim silver chain. Shot 5's subject is *her right hand
sliding a plate*. That bracelet will be the most legible object in the most
important shot. It must match the reference exactly, in all six frames.

**2. Two shots are lit from below by a laptop.** Every reference photograph is
daylight or ambient. Underlighting inverts the shadow pattern the face is
normally read by, and it is where identity drifts hardest. Shots 5 and 6 need
extra scrutiny at review, and possibly a first pass generated in neutral light to
lock the face before the lighting is applied.

**3. Nobody is sitting on a floor in any reference.** All identity anchors are
standing or seated on furniture. Shots 1 and 3–6 are floor-level, cross-legged
or knees-up. Body geometry, not face — but it affects proportion and scale, and
`together-16.jpg` (standing full-body) is the only scale anchor available.

**4. Wardrobe must hold across all six shots and mean something.** She is in the
clothes she went out in, with the bag strap still on — that is the plot. He is in
work clothes with the bag he sets down in shot 2. Neither changes. A wardrobe
drift here does not just break continuity, it breaks the reveal.

## Wardrobe & Light Continuity Lock

| Element | Locked value |
|---|---|
| Aachu wardrobe | Outdoor day clothes, unchanged, bag strap across chest shots 1–6, shoes still on |
| Zuv wardrobe | Work clothes, shoulder bag until he sets it down in shot 2, open collar showing locket and chain |
| Location | One flat, living room floor, sofa behind |
| Time | Continuous — a single unbroken evening |
| Key light | Warm doorway light shots 1–2, room ambient shots 3–4, laptop glow from below shots 5–6 |
| Props | One plate, half-eaten, cold; one laptop; two bags |

## Generation Order

Do not generate in story order. Generate in identity-risk order, so the hardest
face is locked before anything depends on it.

1. **Shot 2** — Zuv hero frame. Everything else inherits his face from here.
2. **Shot 3** — Aachu hero frame.
3. **Shots 4, 5, 6** — two-shots, inheriting both locked faces.
4. **Shot 1** — lowest risk, generated last, composed to rhyme with the
   already-final shot 6.

Every call attaches real photographs per the preflight. Pass `visual-check`
before any still is promoted to the motion stage.

## Status

**No blocker. Cleared to generate, starting with shot 2.**

Reference inputs are fixed at the standard bundle. Do not add photographs to a
call in the hope of improving likeness — that is the failure mode, not the fix.
If a face comes back wrong, change the prompt, the framing, or the lighting
approach; do not change the number of references.
