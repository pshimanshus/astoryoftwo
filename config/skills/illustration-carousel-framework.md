# Illustration Carousel Framework

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
- `slides.json`: ordered exact copy plus one physical-event sentence per slide;
- `prompt-pack.json`: compact shared generation facts and slide prompts;
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

| Format | Final size | Rule | Final folder |
| --- | ---: | --- | --- |
| `instagram_post` | 1080x1440 | default when no canvas is named | `final/` |
| `reels_stories` | 1080x1920 | explicit request only | `final-reels-stories/` |
| `square` | 1080x1080 | explicit request only | `final-square/` |

Generate every requested format natively. Never crop, pad, stretch, or derive one
requested canvas from another. Never add an unrequested format.

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

Vary action, story job, setting, angle, or shot distance across adjacent slides.
Repeated medium couple poses with new text or wardrobe are a hard repair. Text
may complete the meaning; it may not be the sole story carrier.

Preserve the creator's approved architecture. In particular,
`Cover -> Cold Open -> Deepening -> Conflict -> Turn -> Payoff` is a first-class
structure and must not be padded or relabelled.

## Identity And Reference Contract

Before generation, select a small story-specific bundle of actual Aachu/Zuv
images plus the chosen style references. Attach the actual files to every image
generation call. Filenames or text descriptions alone do not satisfy identity.

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

Use `config/carousel_style_contract.json`, the canonical palette rule, and the
selected style-lock references. Keep the prompt version compact:

- warm ivory paper with visible grain;
- fine ink/pencil linework and transparent watercolor blooms;
- muted vintage palette and tactile clothing details;
- one clear behavior scene with selected lived-in evidence;
- generous clean upper-middle space for exact integrated text;
- tiny low-contrast `@a.storyof.two` at top-right;
- no photorealism, glossy 3D/AI-stock finish, quote-card layout, random text,
  extra people, duplicate couple, split-screen UI, or decorative clutter.

Outside references may contribute message, emotion, pose, or composition, but
must not import app chrome, engagement icons, carousel dots, or another
creator's distinctive style.

## Prompt Contract

Compile one prompt per slide only after Gate 2. It contains:

1. physical event and relationship state;
2. camera and focal hierarchy;
3. attached identity/style reference roles and wardrobe choice;
4. compact house style and palette;
5. exact on-image text and tiny top-right brandmark;
6. exact native dimensions;
7. essential negative constraints.

Do not put workflow topology, approval rules, QA rubrics, hash lifecycle,
reviewer instructions, attempt history, or duplicated upstream JSON into the
generator prompt. Those belong in deterministic validators and package state.

## Proof-First Generation

Always prove the slide with the highest combined semantic and rendering risk.
Generate only that slide first for each requested native canvas. A returned file
is quarantined, not creator-ready.

Inspect decoded current pixels in this order:

1. **Story meaning:** observed action and relationship state match the visual
   sentence and exact copy.
2. **Entity/anatomy/spatial integrity:** expected people count matches; no
   unintended person, reflection, silhouette, duplicate, or second story;
   every full silhouette has coherent front/behind/contact relations to walls,
   doors, furniture and floor; every visible hand traces from owner through arm
   and wrist to a plausible contacted object.
3. **Identity:** compare both people to the attached reference IDs with concrete
   face, hair, height, proportion, posture, expression, and wardrobe notes.
4. **Finish:** exact integrated text, brandmark, house style, focal readability,
   and exact native dimensions.

Bind `proof-qa.json` to current file bytes. Prompts, filenames, model claims, or
reviewer names do not count as inspection. Creator approval comes only after all
checks pass.

For a semantic failure, change the event, evidence, staging, or sequence before
changing style adjectives. Allow at most two total semantic attempts for one
visual premise. A second failure produces `proof_failed` with next action
`repair_visual_premise`; it must never produce `handoff_ready`.

## Final QA

After Gate 3, generate remaining slides and repeat the same pixel checks for
each exact file. `visual-qa.json` must record observed evidence and current
path/hash/dimensions for every requested slide/format pair.

`final-images.json` lists only files that passed and were promoted to the final
folders. `final-audit.json` is PASS only when:

- every requested slide/format exists, with no unrequested derivative;
- all files have the required native dimensions;
- exact slide text and top-right brandmark are visible;
- story, entity/anatomy/spatial, identity, and style checks pass;
- the manifest hashes equal current file bytes.

Use `PASS`, `NEEDS_FIXES`, or `BLOCKED`. There is no `PASS_WITH_NOTES` for a
semantic, identity, anatomy/spatial, text, brandmark, or dimension failure.
