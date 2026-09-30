# AGENTS.md — A Story of Two: Video

Project contract for agents doing video work. Scope is `video/` only.
The repo root `AGENTS.md` still applies; this file overrides it where they differ.

## What This Is

The moving-picture line for @a.storyof.two: illustrated short films of Aachu and
Zuv for YouTube (and cutdowns for Reels).

This is **not** the carousel pipeline with motion bolted on. Carousels are single
recognitions. Video is a **series with continuity** — the same two people, an arc
that accumulates across episodes, in the creator's own voice. That distinction is
not editorial taste. It is the thing that keeps the channel monetizable (see
"How This Will Fail", #1).

## Authority Chain — Never Duplicate, Always Point

Identity and style are already solved in this repo. Video inherits them. Do not
copy prose, palettes, or face descriptions into `video/`. If a rule needs to
change, change it at its source.

| Concern | Authority |
|---|---|
| Who Aachu and Zuv are | `config/references/identity/README.md` |
| Which photos to attach, every call | `config/references/identity/_dossier/identity-generation-preflight.md` |
| Machine face contract | `config/references/identity/_dossier/identity-dossier.json` |
| Active illustration profile | `config/references/a-story-premium-illustration-style-lock.md` |
| Finish and palette | `config/rules/palette.md` |
| Frame and sequence direction | `config/rules/visual-variety.md` |
| Text on image | `config/rules/on-image-text.md` |
| Brandmark placement | `config/rules/brandmark.md` |
| Scene/entity integrity | `config/rules/scene-entity-integrity.md` |

`video/references/` holds **evidence only** — creator-supplied stills that show
what "right" looks like. Evidence is not authority. When evidence and the chain
above disagree, the chain wins and the evidence gets re-cut.

## What Matters Most

- **Illustrated, never photoreal.** The watercolour-on-warm-ivory finish is not a
  style preference here, it is the load-bearing engineering decision. Photoreal AI
  couples collapse at the first emotional close-up because viewers read faces for
  authenticity and find nobody home. Stylised art carries the same structural
  forgiveness animation has always had. Every drift toward photorealism is a
  regression, not an upgrade.
- **Faces are still the product.** Same rule as stills: no visible Aachu or Zuv
  face generated without actual photographs attached to the call. Video makes this
  harder, not optional — a face that drifts between shot 2 and shot 5 destroys the
  recognition the whole channel runs on.
- **Continuity is a gate, not a nicety.** Wardrobe, hair, location, time of day,
  and emotional state must survive across every frame of an episode and be
  deliberately chosen across episodes. Write it down before generating; check it
  after.
- **Minimal dialogue, visual-first.** Carry meaning in image, composition, and
  sparse on-screen text — the way the carousels already do. This dodges AI voice
  uncanny valley, keeps the work legible to non-Hindi audiences, and preserves
  the option of a higher-RPM audience later without changing the craft now.
- **Keep intimacy wide.** Hold tenderness in body language, hands, posture, the
  space between two people, and distance shots. Sustained AI close-ups on eyes
  during the emotional beat are where retention dies. Illustration buys margin
  here; it does not buy infinite margin.
- **One episode, finished, beats a system that renders nothing.** The root
  `AGENTS.md` names "too much framework before the first human draft" as this
  repo's standing failure. It applies double here. Build the pilot by hand. Let
  the pipeline be extracted from work that already shipped.

## How This Will Fail

Predicted, not yet observed — this line has shipped nothing. Recorded so the
first failures are the interesting ones.

1. **Demonetisation by template.** YouTube's inauthentic-content policy (live
   2026-07-16) makes ineligible: "similar or repetitive content with low
   educational value, commentary, narratives, or minimal variation", "videos
   using identical storyline templates repeatedly", "AI-generated content made
   with generic or unoriginal templates", and content that "relies heavily on
   emotionally manipulative formulas". Three strikes is permanent YPP removal.
   A comfort-quote factory with two recurring AI characters matches that
   description almost exactly. An original series with real continuity and a
   named creator voice does not. Stay on the right side of that line
   deliberately, every episode.
2. **The intimacy cliff.** Emotional close-ups are where AI romance loses
   viewers. Mitigated by illustration and wide framing; not eliminated.
3. **Identity drift across shots.** The stills pipeline solves per-image
   identity. Nothing here yet solves per-sequence identity. Assume it breaks
   until a check proves otherwise.
4. **Format masquerading as story.** "They can talk about anything" is a format,
   not a series. If an episode could be reordered with any other episode and
   nothing would be lost, it is not an episode.
5. **Ad revenue as the plan.** Shorts RPM is roughly $0.03/1K views for an Indian
   audience against ~$0.25 for a US one; long-form in a decent niche runs $4–12.
   YouTube is this project's permanence and search layer, and it feeds the
   Instagram brand-deal business that already exists. It is not the income.

## Folder Structure

```
video/
  AGENTS.md            this file
  references/
    style-evidence/    creator-supplied illustrated stills — the look, as shipped
    identity-evidence/ creator-supplied photographs — the actual faces
  series/              story bible, character arcs, episode index
  storyboards/         per-episode frame breakdowns
```

Rendered output does not live here. It goes to `output/` with the rest of the
repo's artifacts, so generated work stays separated from human-authored source.

## Workflow

Nothing is automated yet, by design. The current order of work:

1. **Series bible** — who these two are across episodes, what accumulates.
2. **Episode storyboard** — every frame specified before a single one is generated.
3. **Character angle coverage** — the face/body views the storyboard actually
   needs, built off the real photographs under the existing preflight rules.
4. **Generate, assemble, review.**
5. **Only then**, extract whatever turned out to be repeatable into a command.

No `make` target exists for video. Do not invent one until step 5.

## First Move

Before acting, normalise the request into goal, context, constraints, done-when —
same as the root contract. Then check two things specifically:

- Does this episode have continuity with the ones around it, or is it a template?
- Does every visible face in it have real photographs attached to its generation
  call?

If either answer is no, fix that before anything else.
