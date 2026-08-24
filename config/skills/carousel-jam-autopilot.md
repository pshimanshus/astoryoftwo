# Carousel Jam Autopilot

last_updated: 2026-08-23
status: four-gate production path

## Outcome

Move one approved idea to actual publishable images with the fewest useful
stops. A normal run produces only the files needed to generate, inspect, and
publish the current carousel.

## Dynamic Routing

- If the creator supplies a clear seed and copy, preserve it and move directly
  toward locks.
- If the seed is loose, offer one alive route and repair it conversationally.
- If the creator explicitly asks for a deep, independently verified search,
  route to `$a-story-instagram-idea-loop`; it is never the default.
- If a bounded identity, visual-risk, or final-skeptic audit would genuinely
  benefit from a helper agent, give it one non-overlapping job. Do not create a
  standing room, cast of personas, or debate artifact.
- If required identity/style images are unavailable, stop at the one missing
  input instead of building a speculative package.

## Gate 1 — Concept

Preserve the raw lived event before universalizing it: who acted, where, what
object or condition changed, what the other person noticed, and what the
consequence was. Lock one concept only when it has:

- a cold-viewer recognition mirror;
- `before -> pressure/choice -> after`;
- at least one drawable relationship receipt;
- an earned ending and natural send reason.

This is a human creative decision, not a numeric score. Do not generate 5-10
routes, a tournament, or debate unless the creator explicitly asks.

Persist the surviving facts, one-sentence concept, protected architecture,
creator corrections, and reference availability in `creative-context.json`.

## Gate 2 — Copy + Format

Lock exact on-image text and the requested native canvas set together:

- 1080x1440 `instagram_post` is the no-canvas default;
- 1080x1920 `reels_stories` is explicit-only;
- 1080x1080 `square` is explicit-only.

Write `format-contract.json` and `slides.json`. Each slide has one story role and
one physical-event sentence: subject, action, target/object, and visible
reaction or changed state. Include concise camera, hands/contact, gaze, body
distance, expected people, wardrobe-reference, and text-zone facts only when
they affect the frame.

Compile `prompt-pack.json` and `.prompt.txt` files only after this gate passes.
Prompts contain physical event, camera/focal hierarchy, attached reference
roles, wardrobe, compact house style, exact text, tiny top-right brandmark,
dimensions, and essential negatives. Lifecycle rules, hashes, QA rubrics, agent
instructions, and upstream JSON do not belong in the generator prompt.

## Gate 3 — Proof Pixels + Creator

Choose the frame most likely to fail semantically or visually. Attach the actual
selected Aachu/Zuv identity images and chosen style references, then generate
only that proof in each requested native format.

Quarantine the candidate. Inspect decoded current pixels and write
`proof-qa.json` bound to file path, SHA-256, and dimensions. Check, in order:

1. intended physical event and relationship state are visibly readable;
2. expected people/entities, continuous silhouettes, spatial depth, hands and
   object contact are coherent;
3. both identities match the attached reference IDs in face, hair, height,
   proportions, posture, expression, and wardrobe;
4. exact text, `@a.storyof.two`, house style, and dimensions pass.

If the semantic idea fails, repair the physical premise or staging before prompt
adjectives. Permit two total semantic attempts for one premise. After attempt
two, set `proof_failed` with next action `repair_visual_premise`.

Only a passed pixel audit plus explicit creator approval unlocks the rest of the
deck. A model output must not be displayed as approved before this gate.

## Gate 4 — Final Package QA

Generate remaining slides with the same locks. Produce no unrequested format.
Run the proof checks on every current final asset and bind results to exact
package-relative path, format, dimensions, and hash in `visual-qa.json`.

Then write:

- `final-images.json`: only final files and their current hashes/dimensions;
- `final-audit.json`: PASS only when files, formats, copy, brandmark, identity,
  anatomy/spatial integrity, visible story, and QA all agree.

Public final folders are:

- `final/slide-XX.png` for requested/default 1080x1440 post;
- `final-reels-stories/slide-XX.png` only for requested 1080x1920 Story/Reel;
- `final-square/slide-XX.png` only for requested 1080x1080 square.

## States

Use one current state and one next action:

- `awaiting_concept_approval`
- `awaiting_copy_format_approval`
- `handoff_ready`
- `proof_failed` -> `repair_visual_premise`
- `awaiting_creator_proof_approval`
- `generating_remaining_slides`
- `final_qa_failed` -> repair the named slide/check
- `final`
- `blocked` -> request the named missing input

Do not let a failed proof report `handoff_ready` or let a partial deck report
`final`. Do not create separate ledgers for creator decisions, generation state,
review state, and package state.

## One Command

`make carousel STORY="..." TITLE="..."` creates the compact package and prepares
the proof handoff. It must not run the repository test suite or Agentic OS health
as a production preflight. Those checks belong to `make test` and maintenance.

Do not stop at a prompt handoff when generation is available. If generation is
unavailable, report `handoff_ready`; if a required reference or lock is missing,
report `blocked` and name only that blocker.
