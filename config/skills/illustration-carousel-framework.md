# Illustration Carousel Framework

Codex directly invokes ImageGen with each final compiled prompt and the locked
five-reference bundle. Every selected slide then passes returned-source ingest,
decoded-pixel review, hash-bound QA, approval, and atomic promotion.

## Purpose

Turn an approved @a.storyof.two story plus selected reference images into a
small, auditable set of publishable illustrated slides. This file defines the
production contract; it does not add creative approval gates.

## Four-Gate Contract

1. **Concept lock:** one lived relationship truth, causal change, and drawable
   receipt.
2. **Copy + format lock:** exact slide text and only the requested native
   canvases.
3. **Proof lock:** the riskiest candidate passes current-pixel story, integrity,
   identity, text, style, and dimension QA, then the creator approves it.
4. **Final lock:** all requested native files and the final manifest pass the
   same QA.

No agent-room, visual-debate, tournament score, reviewer-provenance graph,
run-ledger, stage-review ledger, or wiki-update artifact is required in the
default path. Deep idea search remains an explicit separate workflow.

## Minimal Artifacts

Create only what the current stage needs.

Before proof:

- `creative-context.json`: exact source facts, selected concept, creator
  corrections, reference roles, and protected story architecture;
- `format-contract.json`: request-derived formats and exact native dimensions;
- `slides.json`: the only per-slide authority, with ordered exact copy, one
  physical event, camera, setting/light/depth, and cinematic `visual_richness`;
- `prompt-pack.json`: compact immutable shared generation inputs only, with no
  copied slide prose;
- compiled package-relative `.prompt.txt` files.

After proof:

- quarantined proof PNG;
- `proof-qa.json`, bound to the proof path, SHA-256, and dimensions, including
  creator approval only after pixel QA passes.

After final generation:

- requested native final PNGs;
- `final-images.json`, containing only final path/hash/dimension records;
- `visual-qa.json`, containing per-file observed pixel evidence;
- `final-audit.json`.

Do not embed copies of upstream artifacts inside `prompt-pack.json`. Do not keep
raw model responses or discarded candidates in the publishable package. Failed
candidates remain quarantined until removal or archive.

## Native Formats

Resolve the set from the current request and corrections, never old output
folders:

| Format | Final size | Accepted returned source | Final folder |
| --- | ---: | --- | --- |
| `instagram_post` | 1080x1440 | exact 3:4 from 1080x1440 through 1440x1920 | `final/` |
| `reels_stories` | 1080x1920 | exact 1080x1920; explicit request only | `final-reels-stories/` |
| `square` | 1080x1080 | exact 1080x1080; explicit request only | `final-square/` |

The prompt always requests the exact final target and says `native 3:4` for an
Instagram post; it does not advertise the ingest accommodation. The repo may
quarantine an untouched larger `instagram_post` source only when its integer
dimensions are exact 3:4, no smaller than 1080x1440 and no larger than
1440x1920. Bind source path/hash/dimensions, then proportionally downsample once
to exact 1080x1440. Never crop, pad, stretch, upscale, accept a wrong ratio,
resample twice, derive another format, or add an unrequested format. This is an
observed built-in-runtime accommodation, not a published model guarantee.

## Scene Contract

Every slide has one visual sentence:

```text
specific subject + observable action + target/object + visible reaction or change
```

The sequence must show causal movement. Specify hands/contact, gaze, feet and
posture, body distance, object ownership/state, expected people, shot size,
camera reason, focal hierarchy, and text-safe space only to the degree they
change the frame. Track an object only when it locates the moment, changes the
action, reveals character, creates consequence, or pays off.

Use the canonical `slides.json` fields defined by
`config/rules/visual-variety.md`. Every slide also identifies point of view,
before/after implication, a continuation pull or final payoff, specific
motivated light, foreground/midground/background jobs, and two to four concrete
story-evidence records. Do not write parallel scene/composition aliases.

Every person slide also stores two generation inputs: a complete hand-
ownership map for both left/right hands and a whole-person/object topology map.
The image prompt must include them. Prompt compilation fails closed if a map is
missing or incomplete; a generic malformed-hands negative does not count.

Vary action, story job, setting, angle, or shot distance across adjacent slides.
Repeated medium couple poses with new text or wardrobe are a hard repair. Text
may complete the meaning; it may not be the sole story carrier.

Preserve the creator's approved architecture. In particular,
`Cover -> Cold Open -> Deepening -> Conflict -> Turn -> Payoff` is a first-class
structure and must not be padded or relabelled.

## Identity And Reference Contract

For both generation and editing, keep exactly five canonical references:

1. the four actual Aachu/Zuv/together files in
   `identity-dossier.json.selected_generation_bundle`;
2. one package-bound style board resolved from the active profile in
   `config/carousel_style_contract.json` and verified by its declared SHA-256.

Codex attaches all five actual files to every image-generation call. For an
edit, the separately bound target is image 1, followed by these five references
in canonical order. Filenames or text descriptions alone do not satisfy
identity. This is not a claim about an official platform limit. Do not attach
individual style slides in addition to the board or remove an identity role.
Use `prepare --operation-json PATH` for edits, send the exact compiled prompt,
and record every new call through `ingest --invocation-json PATH`. Invocation
evidence is `operator_recorded`; it is not independent server attestation.
Legacy receipts remain readable without invented evidence. The input and
record schemas live in `.agents/skills/astory/references/imagegen-contract.md`.

Use the identity/current-request images for the whole person:

- face structure, hair, expression, and skin tone;
- relative height and body proportions;
- posture and interaction style;
- wardrobe and accessories.

Wardrobe comes from attached current references first. Previous illustrations
are style evidence, never face identity evidence. If actual identity inputs
cannot be attached or likeness cannot be compared, set the package to `blocked`
or `IDENTITY_UNVERIFIED`; do not batch or call it final.

## House Image Contract

Resolve the only active machine prompt, negative prompt, board path, and board
hash from `config/carousel_style_contract.json`. Normative finish rules live in
`config/rules/palette.md`; cinematic frame and sequence rules live in
`config/rules/visual-variety.md`; exact text and brandmark rules live in their
matching rule files. Do not copy those instructions into this workflow file or
accept a free-form production substitute.

Outside references may contribute message, emotion, pose, or composition, but
must not import app chrome, engagement icons, carousel dots, or another
creator's distinctive style.

## Prompt Contract

Compile one prompt per slide only after Gate 2. It contains:

1. physical event and relationship state;
2. camera, setting, motivated light, depth, and focal hierarchy;
3. point of view, before/after implication, continuation/payoff, and story
   evidence;
4. attached identity/style reference roles and wardrobe choice;
5. the one active house-style profile;
6. exact on-image text and tiny top-right brandmark;
7. exact native dimensions;
8. essential negative constraints.

Do not put workflow topology, approval rules, QA rubrics, hash lifecycle,
reviewer instructions, attempt history, or duplicated upstream JSON into the
generator prompt. Those belong in deterministic validators and package state.

## Proof-First Generation

Always prove the slide with the highest combined semantic and rendering risk.
The repo prepares the selected compiled prompt and reference bindings. Codex
reads that prompt, attaches the four identity files and one style board, and generates
only that slide first for each requested native canvas. The repo immediately
ingests every returned file into quarantine; it is not creator-ready.

Codex then opens the decoded normalized candidate with `view_image` (or the
unchanged candidate when the source was already exact) and submits structured QA
bound to its package-relative path, SHA-256, and dimensions. If image generation
or `view_image` is unavailable, retain `handoff_ready` and report
`BLOCKED/NOT_RUN`; never report generated, inspected, or PASS. The repo does not
contain an API renderer, API-key path, OCR fallback, or environment capability
probe.

Inspect decoded current pixels in this order:

1. **Story meaning:** hide the copy and name the event actually visible before
   comparing it with the visual sentence. For an exchange, identify the actor,
   recipient, directed action and consequence. A phone and parcel in the frame
   do not establish a delivery; presenting a prop to the viewer does not supply
   a missing in-scene recipient. Prompt compliance alone cannot pass story
   meaning when the planned event is itself weak or wrong.
2. **Cinematic story frame:** the image reads as a caught event, with motivated
   light, distinct depth layers, mapped story evidence, before/after
   implication, continuation or final payoff, and no posed/decorative/generic-
   AI substitute.
3. **Entity/anatomy/spatial integrity:** expected people count matches; no
   unintended person, reflection, silhouette, duplicate, or second story;
   every full silhouette has coherent front/behind/contact relations to walls,
   doors, furniture and floor; every visible hand traces from owner through arm
   and wrist to a plausible contacted object.
   Record each visible hand separately with owner, side, attachment, contact,
   finger integrity, and solid-object intersection evidence. Summary prose
   cannot pass this layer.
   Trace feet, shoes, rugs/mats and thresholds too: which surface supports each
   object, which edge occludes which, and whether contact/shadow/depth agree.
   Do not infer correct shoe contact merely because the floor is level. Put a
   visible contradiction or unresolved contact in the existing failed check;
   do not invent a physical explanation to preserve PASS.
4. **Identity:** compare both people to the attached reference IDs with concrete
   face, hair, height, proportion, posture, expression, and wardrobe notes.
5. **Finish:** exact integrated text, brandmark, house style, deterministic
   palette check, focal readability, and exact native dimensions.

Bind `proof-qa.json` to current file bytes. Prompts, filenames, model claims, or
reviewer names do not count as inspection. Creator approval comes only after all
checks pass.

When an accepted larger post source was normalized, retain its source hash and
dimensions in the candidate binding and bind QA/approval to the normalized
1080x1440 bytes. Reuse those exact approved normalized bytes in finalization;
do not regenerate or downsample the proof again.

For a semantic failure, change the event, evidence, staging, or sequence before
changing style adjectives. Allow at most two total semantic attempts for one
visual premise. A second failure produces `proof_failed` with next action
`repair_visual_premise`; it must never produce `handoff_ready`.

A passed, hash-bound, creator-approved proof is reused as the final candidate
for that slide and format. It is excluded from remaining-slide generation.

## Final QA

After Gate 3, generate only the remaining slides and repeat the same pixel
checks for each exact file. Review stops at the first failed layer: do not score
identity, typography, or finish after the action or spatial read has failed.

`final-images.json` owns the file inventory, input fingerprints, current paths,
hashes, and dimensions. `visual-qa.json` owns observed checks and binds them to
the final-manifest fingerprint plus per-asset binding hashes; it does not copy
the inventory. `final-audit.json` owns only manifest/QA fingerprints, status,
and issues.

Atomic promotion happens only after the hidden complete candidate set passes.
`final-audit.json` is PASS only when:

- every requested slide/format exists, with no unrequested derivative;
- all files have the required native dimensions;
- exact slide text and top-right brandmark are visible;
- story, entity/anatomy/spatial, identity, and style checks pass;
- the manifest hashes equal current file bytes.

Use `PASS`, `NEEDS_FIXES`, or `BLOCKED`. There is no `PASS_WITH_NOTES` for a
semantic, identity, anatomy/spatial, text, brandmark, or dimension failure.

## Slide-Local Repair Contract

Each slide fingerprint covers semantic slide content, that slide's compiled
prompt, applicable story references, and shared identity/style/format/brand
contracts. Formatting or JSON key order is irrelevant.

- A non-proof slide edit invalidates only that slide's prompt, attempts,
  candidate, and QA.
- A proof-slide edit also revokes creator approval.
- Identity/style references, compiler, brand, format, slide order, or other
  shared-style changes invalidate the full deck.
- Any input change removes public final claims immediately while preserving
  unaffected hidden candidates.
- Final-image byte tampering revokes `publish_ready`.

New packages use generation-state v3. Archived v2 packages are read-only and
auditable; they are never migrated during an ordinary run.

## Public States

The only public states are `draft`, `blocked`, `handoff_ready`,
`proof_qa_required`, `proof_failed`,
`awaiting_creator_proof_approval`, `batch_ready`, `final_qa_required`,
`final_qa_failed`, and `publish_ready`.

A passing final `review` immediately uses the existing final audit and atomic
promotion boundary and returns `publish_ready`; there is no extra ready-to-
finalize state or creator gate. Standalone `finalize` remains a recovery/
diagnostic command.
