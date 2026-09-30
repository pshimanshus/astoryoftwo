# Character Lock — EP01 "The Plate"

status: LOCKED for this episode — change here, never in a single shot prompt
authority: identity itself stays owned by
`config/references/identity/_dossier/identity-generation-preflight.md`

A carousel slide only has to be right once. Six shots have to be right *and*
agree with each other. This file is the per-episode agreement: everything that
must be identical in frame 1 and frame 6, written down before generation so drift
is detectable rather than arguable.

Face structure is not specified here. Faces come from photographs, every call,
without exception. What follows is everything *else* that drifts.

---

## Zuv — this episode

| Element | Locked value | Visible in |
|---|---|---|
| Hair | Dark, wavy, slightly disordered from the day — not styled, not wet | all |
| Beard | Full, as in `portrait-07.jpg`, unchanged length across all six | all |
| **Neck** | **Evil-eye locket on slim silver chain, open collar** — hard-fail if absent | 2, 4, 5, 6 |
| Top | Everyday work shirt, worn-in, sleeves pushed up by the time he sits | all |
| Lower | Dark trousers, creased from a full day | all |
| Feet | Shoes on in shots 2–4; **off by shot 5** — he completed coming home, she never did | 2–6 |
| Bag | Shoulder bag, dark, set down in shot 2 and visible on the floor after | 2–6 |
| Height | 5'8", only slightly taller than Aachu when both stand | 2, 4 |

**Expression range needed.** Depleted, not sad. No crying, no hand-to-face
despair, no theatrical grief. Shot 2 is the deepest point: jaw slack, gaze
unfocused. By shot 6 it has softened by a few degrees and no more — he is not
healed, he is fed.

## Aachu — this episode

| Element | Locked value | Visible in |
|---|---|---|
| Hair | Dark, up in a loose knot that has been up all day and slipped | all |
| **Right wrist** | **Evil-eye bracelet, same side, same design** — hard-fail if wrong; centre-frame in shot 5 | 1, 3, 5, 6 |
| Top | The clothes she went out in — unchanged, not loungewear | all |
| **Bag** | **Strap still across her chest, all six shots.** She sat down and never took it off. This is the plot. | 1–6 |
| Feet | **Shoes still on, all six shots.** She never finished coming home. | 1–6 |
| Height | 5'6" | 4 |

**Expression range needed.** Shot 1: turning toward the door, neutral, tired.
Shot 3: recognition — she has clocked him. Understated; not concern, not alarm.
Shot 4: the question forming and not arriving — a fraction of mouth movement, no
more. Shots 5–6: nothing performed. She is as depleted as he is and the film
never says so out loud.

## The Two Details That Carry The Reveal

Everything else can shift a millimetre. These cannot:

1. **Her bag strap stays across her chest in every frame, including shot 6.**
2. **Her shoes stay on in every frame.** His come off.

That asymmetry *is* the ending. He arrived home and eventually landed. She never
did. If a generated frame quietly tidies either detail away — and it will want to,
because a woman sitting at home in outdoor shoes with a handbag on reads as
"wrong" to a model trained on tidy interiors — the episode loses its reveal and
the shot is rejected, however beautiful it is.

Legible, never emphasised. Never lit, centred, or found by the camera.

## Shared Environment Lock

| Element | Locked value |
|---|---|
| Location | One flat: living-room floor, sofa behind, front door camera-rear in shot 1 |
| Time | Continuous single evening, no ellipsis |
| Key light | Warm doorway light (1–2) → room ambient (3–4) → laptop glow from below (5–6) |
| Props | One plate, half-eaten and cold, fork resting; one laptop; two bags |
| Plate position | Beside her in 1–4, travels to him in 5, returns to her in 6 |

## Model Sheets

A drawn character sheet is a **supplemental continuity aid only**. Per the
preflight's generated-chart prohibition it never becomes face authority, and
every visible-face call still attaches actual photographs — including calls that
also reference an approved sheet.

Order: generate Zuv's sheet first (`video/storyboards/ep01-sheet-zuv-prompt.md`),
because he is the identity risk in this episode. Aachu's mirrors it and follows
only once Zuv's is creator-approved.

Both route through `scripts/render_gate.py` like any other shot.
