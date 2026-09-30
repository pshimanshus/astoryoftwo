# Production Workflow — Higgsfield Video Line

status: ACTIVE
plan: MAX · credits tracked per shot below
scope: EP01 "The Plate", and every episode after it

The pipeline is **still first, motion second**. A shot is never generated as
video from text. It is painted as a still, approved, and only then animated —
because identity is settled in the still and image-to-video inherits it.

---

## Standing Assets — created once, reused forever

| Asset | ID | Notes |
|---|---|---|
| Element `zuv` | `e4c9ff5b-0876-4c5b-8848-65f3e7ddaa0b` | Embed as `<<<e4c9ff5b-0876-4c5b-8848-65f3e7ddaa0b>>>` |
| Element `aachu` | `f04acf72-b0d4-4fda-8cb0-a5ac375ed1ef` | Embed as `<<<f04acf72-b0d4-4fda-8cb0-a5ac375ed1ef>>>` |
| Style board media | `79de07d8-fe5e-47ab-bf59-7983bff37568` | Attach as `image_references` on every still |

Elements are permanent and survive sessions. Never recreate them; never add more
photographs to one — reference minimalism is a standing rule.

## Costs — measured, not estimated

| Operation | Credits |
|---|---|
| Still, 2K, 9:16 | **2** |
| Video, 5s, 720p | **32.5** |
| Video, 5s, 1080p | **45** |

Motion is ~20× a still. That single ratio drives every decision below.

**Episode budget at 1080p:** 6 stills × 2 attempts (24) + 6 clips (270) = **~294**.

## The Cost Lever — read before animating anything

**Not every shot needs generated motion.** Shot 6 is "almost none — a breath, a
flicker of screen light." A still with a slow push-in added in the edit is
indistinguishable, and free.

Generate motion only where **motion is the story**:

| Shot | Motion | Generate? |
|---|---|---|
| 1 | Door swings, light wedge widens, her head turns | **Yes** — three moving elements |
| 2 | He sets the bag down | Marginal — edit push-in may serve |
| 3 | She closes the laptop | Marginal |
| 4 | He lowers to the floor; her mouth opens a fraction | **Yes** — the unasked question lives here |
| 5 | The plate slides; screen light returns | **Yes** — the gesture |
| 6 | A breath | No — edit motion, and it is the loop frame |

Three generated clips instead of six takes an episode from ~294 to **~160
credits**, with no visible loss. Decide per shot, never by default.

---

## Per-Shot Pipeline

Each shot runs the same five steps.

### 1 · Compose the prompt
Style language comes from `video/references/style-prompt-higgsfield.md` — never
from `config/carousel_style_contract.json`, whose "ink contours" wording produces
cartoon line art on these models. The load-bearing clause is *no outlines of any
kind*.

Scene, framing, motion and continuity come from
`video/storyboards/ep01-the-plate.md` and `video/series/character-lock-ep01.md`.

Structure every prompt in this order — these models weight early tokens hardest:

1. Style opener (photoreal-painted, warm ivory)
2. Scene + element placeholder(s)
3. **CAMERA AND FRAMING** — stated as a proportion of the frame, not an adjective
4. Continuity plants, marked *visible but never emphasised*
5. Anatomy / texture / accessory locks
6. No-outlines clause + light + palette
7. Full negative block

### 2 · Generate the still
`generate_image` · `nano_banana_pro` · `9:16` · `2k` · style board attached ·
`use_unlim: false`. Two attempts maximum on a premise; if it fails twice, rewrite
the scene rather than re-rolling.

### 3 · Review against acceptance checks
Inspect the returned pixels, never the prompt. Style checks come first — that is
what failed on the first attempt. Likeness is the creator's call, never the
agent's.

### 4 · Animate the approved still
`generate_video` · `seedance_2_5` · `mode: omni_reference` · approved still as
`start_image` · `9:16` · `5s` · `1080p` · `generate_audio: false`.

Motion briefs stay **small — one moving element per shot**. The still already
carries the composition; the video's only job is to make it breathe. Over-
prompted motion is where identity drifts and hands break.

### 5 · Record
Land the clip in `output/video/ep01/`, log the job id, credits spent, and the
review verdict.

---

## Assembly

Once all six clips exist:

- Cut in story order 1 → 6 at the timings in the storyboard
- **Composite all text in the edit, never in generation.** The timestamp card
  (`Year 3. A Thursday.`), the closing line (`Dono ne nahi pucha.`) and the
  `@a.storyof.two` brandmark are all overlaid. Generated tiny text comes back
  garbled and garbled copy is a hard fail
- Add edit-motion (slow push-in, parallax) to the shots that were not generated
- Shot 6 must rhyme with shot 1 so the loop reveals

## Hard Rules

1. Never paste the carousel style contract into a Higgsfield call.
2. Never add photographs to an element to improve likeness.
3. Never generate text into a frame.
4. Two generation attempts per premise, then rewrite the scene.
5. Motion prompts stay minimal — one moving element.
6. Preflight with `get_cost: true` before any generation whose price you have not
   already measured.
