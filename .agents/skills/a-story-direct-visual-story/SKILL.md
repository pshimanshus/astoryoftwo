---
name: a-story-direct-visual-story
description: Turn a locked @a.storyof.two concept into image-led physical scenes and audit the generated pixels for story readability. Use after concept lock for storyboards, shot planning, proof generation, visual repair, or final image QA; do not use for open-ended ideation.
---

# Direct Visual Story

Compact router after concept/copy lock. Read
`config/skills/illustration-carousel-framework.md` and
`config/skills/carousel-jam-runtime-context.md` only when exact detail is
needed. Apply [`$non-ai-image-skill`](../non-ai-image-skill/SKILL.md) for the
activated scene risks; it adds no creator-approval gate.

## Direction

Direct scenes, not decorated copy. Each slide needs one physical event: subject,
observable action, acted-on person/object/space, and visible consequence. Keep
camera, hands/contact, gaze, body distance, object state, text-safe space,
native dimensions, exact copy, and tiny top-right brandmark aligned.

Use actual identity refs for the whole person. Stage relationship, then style.
Check entity/anatomy/spatial integrity before beauty language.
Bind the locked scene/copy and activated contact, object, chronology, scale, and
depth risks in each slide's `scene_contract` before generation.

## Proof And QA

Codex directly invokes ImageGen for requested proof and final-slide generation.
Generate the riskiest proof first. Inspect actual-pixel evidence with
`view_image`; prompt text, filenames, generator reports, or reviewer labels are
not evidence.
For edits and invocation receipts, follow
`.agents/skills/astory/references/imagegen-contract.md`. Start review with a
blind pixel-only scene read; unresolved contact or overlap is failure/data gap.

Record proof results in `proof-qa.json` with path, SHA-256, dimensions, story
read, identity, exact text, brandmark, style, and native canvas. Creator approval
comes only after proof QA passes.

On failure, classify the visible miss. Wrong event means replace the premise;
weak evidence means change action/reaction/object state/consequence; weak
staging means change blocking, eye-line, camera, scale, or focal hierarchy. Do
not polish an unchanged semantic premise. After two misses, set
`proof_failed`, name `repair_visual_premise`, and replace the idea.

After proof approval, generate remaining requested native slides and bind final
actual-pixel QA in `visual-qa.json`. Finish only when story,
entity/anatomy/spatial, identity, style, dimensions, exact text, brandmark,
`final-images.json`, and `final-audit.json` pass.
