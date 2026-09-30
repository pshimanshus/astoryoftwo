# Carousel Jam Autopilot

last_updated: 2026-09-04
status: four-gate production path

Codex directly invokes ImageGen for the risky proof and every selected final
slide. It attaches exactly four identity references and one style board, opens
the decoded returns, and submits hash-bound QA. Prompt preparation alone is not
completion.

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

The illustration profile is not a free-form workflow input. Resolve its one
prompt, negative prompt, board, and board hash fail-closed through
`config/carousel_style_contract.json`. Normative finish and cinematic semantics
remain in `config/rules/palette.md` and `config/rules/visual-variety.md`; do not
duplicate them here.

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

Persist the surviving facts, one-sentence concept, protected architecture, and
reference availability in `creative-context.json`. Exact creator corrections
belong in the existing `creator-correction.json` surface.

For each correction, Codex calls `scripts/carousel.py feedback` automatically,
with the exact words, diagnosis, targeted scope, and change/preserve constraints.
Repair existing fields, then use `revise --feedback-id` and `feedback-status` to
record and verify the result. A saved correction is not an implemented fix.
Its regression case and LearningEvent are internal evidence, not another lock;
optional shadow judges and telemetry never delay illustration generation.

## Gate 2 — Copy + Format

For copy-only requests, apply the final-draft review in
`.agents/skills/a-story-storytelling-hook/SKILL.md` before delivering the exact
copy. Concept approval selects the direction; it does not certify an unwritten
or shortened sequence. No production package or image generation is needed
merely to deliver a draft in chat.

Lock exact on-image text and the requested native canvas set together:

- 1080x1440 `instagram_post` is the no-canvas default;
- 1080x1920 `reels_stories` is explicit-only;
- 1080x1080 `square` is explicit-only.

Write `format-contract.json` and `slides.json`. Each slide has one story role and
one physical-event sentence: subject, action, target/object, and visible
reaction or changed state. Include concise camera, hands/contact, gaze, body
distance, expected people, wardrobe-reference, and text-zone facts only when
they affect the frame.

Store point of view, before/after implication, continuation or final payoff,
motivated light, depth-layer jobs, and two to four story-evidence records in
the canonical `visual_richness`/camera/setting fields. Missing or generic
cinematic direction blocks before ImageGen.

For every person slide, `slides.json` also carries a complete left/right hand-
ownership map plus whole-person/object topology. The compiler embeds both in
the generation prompt and blocks before ImageGen if either is incomplete. Do
not replace the map with a generic "natural hands" negative.

Compile `prompt-pack.json` and `.prompt.txt` files only after this gate passes.
Prompts contain physical event, camera/focal hierarchy, attached reference
roles, wardrobe, compact house style, exact text, tiny top-right brandmark,
dimensions, and essential negatives. Lifecycle rules, hashes, QA rubrics, agent
instructions, and upstream JSON do not belong in the generator prompt.

The generator prompt continues to request the exact locked target. At ingest,
only `instagram_post` may accept an untouched exact-3:4 source from 1080x1440
through 1440x1920 inclusive, bind its source bytes/dimensions, and downsample it
once proportionally to exact 1080x1440. Never crop, pad, stretch, upscale,
accept a wrong ratio, or apply this accommodation to Story/Reel or square.

## Gate 3 — Proof Pixels + Creator

Choose the frame most likely to fail semantically or visually. The repo command
prepares the selected compiled prompt. Codex reads it and attaches exactly five
files: all four files in `identity-dossier.json.selected_generation_bundle`,
then the one canonical style contact sheet bound by the package. It calls image
generation only for that proof in each requested native format, immediately
ingests the returned file into quarantine, and inspects the decoded normalized
candidate pixels with `view_image` (or unchanged bytes when already exact).

This five-attachment boundary comes from the current built-in Codex runtime
smoke; do not describe it as an official platform limit. Do not append the
three individual style slides or silently remove an identity file.

Story images are pre-lock creative context, not extra imagegen attachments.
Inspect them before authoring the brief, encode their observable clothing,
object, setting, and continuity facts in the slide-authoritative fields, and
keep their package-local hashes as slide-local invalidation evidence. The
compiled handoff separates them as `context_reference_bindings`; do not imply
they guided a generation call unless the runtime actually received them.

If image generation or `view_image` is unavailable, stop successfully at
`handoff_ready` and report `BLOCKED/NOT_RUN`. No prompt review, filename, model
claim, or authored expectation may substitute for pixel inspection.

Quarantine the candidate. Inspect decoded current pixels and write
`proof-qa.json` bound to file path, SHA-256, and dimensions. Check, in order:

1. intended physical event and relationship state are visibly readable;
2. the frame reads as a caught event with motivated light, distinct depth,
   story evidence, before/after implication, and continuation/payoff—not a
   staged, decorative, or generic-AI scene;
3. expected people/entities, continuous silhouettes, spatial depth, hands and
   object contact are coherent, with every visible hand individually traced as
   owner -> arm -> wrist -> hand -> contacted object;
4. both identities match the attached reference IDs in face, hair, height,
   proportions, posture, expression, and wardrobe;
5. exact text, `@a.storyof.two`, house style, deterministic palette, and
   dimensions pass.

If the semantic idea fails, repair the physical premise or staging before prompt
adjectives. Permit two total semantic attempts for one premise. After attempt
two, set `proof_failed` with next action `repair_visual_premise`.

Only a passed pixel audit plus explicit hash-bound creator approval unlocks the
rest of the deck. The approved proof becomes its final candidate and is omitted
from remaining-slide generation; if normalized, those exact normalized proof
bytes are reused without another resample. A model output must not be displayed as
approved before this gate.

The entity/spatial audit cannot pass on summary prose alone. It must inventory
every planned visible hand by owner and side and record attachment, contact
geometry, finger integrity, and solid-object intersection results.

## Gate 4 — Final Package QA

Generate remaining slides with the same locks. Produce no unrequested format.
Run the proof checks on every current candidate and bind observations to each
asset binding hash in `visual-qa.json`. The manifest owns the path, format,
dimensions, and file hash inventory; QA must not duplicate it.

Then write:

- `final-images.json`: file inventory, input fingerprints, hashes, and
  dimensions only;
- `visual-qa.json`: observed checks bound to the final-manifest fingerprint and
  per-asset binding hashes, with no copied inventory;
- `final-audit.json`: manifest/QA fingerprints, status, and issues only.

Public final folders are:

- `final/slide-XX.png` for requested/default 1080x1440 post;
- `final-reels-stories/slide-XX.png` only for requested 1080x1920 Story/Reel;
- `final-square/slide-XX.png` only for requested 1080x1080 square.

## States

Use one current state and one next action:

- `draft`
- `blocked`
- `handoff_ready`
- `proof_qa_required`
- `proof_failed`
- `awaiting_creator_proof_approval`
- `batch_ready`
- `final_qa_required`
- `final_qa_failed`
- `publish_ready`

Do not let a failed proof report `handoff_ready` or let a partial deck report
`publish_ready`. Do not create separate ledgers for creator decisions,
generation state, review state, and package state. Creator approval is embedded
in hash-bound `proof-qa.json`.

A passing `review` of final QA immediately runs the existing audit and atomic
promotion and returns `publish_ready`. Standalone `finalize` remains available
for recovery/diagnosis; it is not an extra routine step or creator gate.

## One Command

`make carousel STORY="..." CREATIVE_BRIEF="locked-brief.json" TITLE="..."`
creates the compact package and prepares the risky proof when the brief has
locked physical actions. Story-only input remains `draft`, names the missing
lock, and spends no generation call. It must not run the repository test suite,
Agentic OS health, wiki health, or network calls. Those checks belong to tests
and maintenance.

The routine image loop is six commands: create with `--prepare-proof`, ingest
proof, review proof, approve (which prepares the batch), ingest batch, and
review final (which promotes a passing deck). `status`, standalone `prepare`,
and standalone `finalize` are recovery/diagnostic surfaces.

Do not stop at a prompt handoff when Codex image generation and pixel viewing
are available. If either is unavailable, report `handoff_ready`; if a required
reference or lock is missing, report `blocked` and name only that blocker.
