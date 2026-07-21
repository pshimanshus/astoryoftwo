# Visual Storytelling Rubric

last_updated: 2026-07-21
confidence: 0.84
sources:
- AGENTS.md
- config/rules/visual-variety.md
- config/rules/relationship-motion.md
- config/rules/scene-entity-integrity.md
- memory/semantic/visual-director-intelligence.md
- evals/research/failure-taxonomy.md

## Use

Use this rubric only after deterministic text, format, identity, entity,
anatomy, topology, stale-artifact, and package gates pass. Review the actual
storyboard, proof, or structured visual artifact named in the rubric result.
Do not infer quality from prompt prose alone.

Each score needs at least one concrete evidence anchor: a slide number, frame,
visible action, object state, blocking relation, camera choice, or continuity
callback. Adjectives such as "beautiful," "cinematic," or "cozy" are not
evidence.

## Anchored Dimensions

Image-first story legibility, 0-3:

- 0: the scene becomes meaningless when copy is hidden.
- 1: generic couple activity suggests mood but not the intended event.
- 2: visible action and reaction communicate the main beat.
- 3: setup, pressure, consequence, and relationship change are legible from
  the frames themselves.

Shot progression, 0-3:

- 0: repeated camera distance, angle, posture, and narrative job.
- 1: cosmetic reframing without a new story function.
- 2: camera scale, angle, and subject visibility change with the beats.
- 3: every shot earns its place and the sequence has a readable visual arc.

Object and setting continuity, 0-3:

- 0: generic decoration or contradictory object states.
- 1: props exist but do not carry story information.
- 2: objects and room geography preserve cause, ownership, and continuity.
- 3: recurring objects or setting traces accumulate meaning and deliver a
  visible payoff.

Blocking and spatial clarity, 0-2:

- 0: gaze, hands, bodies, depth order, or contact cannot be reconstructed.
- 1: readable staging with minor ambiguity that does not change the story.
- 2: body distance, gaze, contact, movement, and occlusion clearly express the
  relationship beat.

Text-image composition, 0-1:

- 0: text competes with, covers, or merely labels the visual.
- 1: negative space and focal hierarchy let exact text complete the scene.

Pass requires at least 9/12, with no zero in image-first story legibility or
blocking and spatial clarity. A deterministic hard-gate failure always blocks
the task regardless of rubric total.

## Reviewer Independence

Record a reviewer ID and the exact reviewed artifact. The reviewer should not
be the agent that authored the artifact. Bind the result to the exact artifact
SHA-256 so the review becomes stale when the artifact changes. If no independent
review has been supplied, the eval remains `PENDING`; mechanical prechecks
cannot award creative-quality credit.
