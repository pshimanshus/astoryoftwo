---
name: a-story-direct-visual-story
description: Turn a locked @a.storyof.two concept into image-led physical scenes and audit the generated pixels for story readability. Use after concept lock for storyboards, shot planning, proof generation, visual repair, or final image QA; do not use for open-ended ideation.
---

# Direct Visual Story

Compact router after concept/copy lock. Read
`config/skills/illustration-carousel-framework.md` and
`config/skills/carousel-jam-runtime-context.md` only when exact detail is
needed. For every locked image-production task, also apply
[`$non-ai-image-skill`](../non-ai-image-skill/SKILL.md) for applicable scene-risk
contracts, review routing, and regression controls. Canonical rules remain
authoritative; this adds no creator-approval gate.

## Direction

Direct scenes, not decorated copy. Each slide needs one physical event: subject,
observable action, acted-on person/object/space, and visible consequence. Keep
camera, hands/contact, gaze, body distance, object state, text-safe space,
native dimensions, exact copy, and tiny top-right brandmark aligned.

Use actual identity refs for the whole person. Stage relationship, then style.
Check entity/anatomy/spatial integrity before beauty language.

Store the resulting `scene_contract` with every slide before
generation. Include only activated risks: contact target, story-critical object
face/orientation/use, chronology, adult-scale support, accessory visibility,
and body/solid-object depth order. Its scene and copy bindings must match the
locked slide and reach the compiled prompt; do not infer missing geometry
from prose. If copy or canvas remains open, direction is provisional.

Start with the non-AI-image skill's blind scene read: before judging prompt
compliance or revealing the intended answer, hide the copy and describe the
event visible in the pixels. For an exchange, name who acts, who receives or
responds, and what changes. A prop displayed toward the camera does not prove an interaction.
Let the camera observe the participants' task; do not turn them toward the
viewer merely to expose a screen or label. A hidden screen can tell the story
through its recipient, grip, gaze and the resulting action.

## Proof And QA

Generate the riskiest proof first. For a requested edit, bind its target with
`prepare --operation-json PATH`, inspect it, then attach it first followed by
the five canonical identity/style references. Send the exact compiled prompt;
scene/copy fields and feedback remain authoritative. Every new call requires
`ingest --invocation-json PATH`; see
`.agents/skills/astory/references/imagegen-contract.md` for the record format.
Inspect actual-pixel evidence with `view_image`; prompt text, filenames,
operator-recorded invocations, generator reports, or reviewer labels are not
pixel evidence.

Trace shoe–rug–floor, foot–threshold and other foreground overlaps as carefully
as hands. A level floor does not prove coherent contact: identify what is above,
behind and supported by what. Unresolved overlap is a failure or data gap, never
an assumed PASS. Read `references/checker-contract.md` for the six-check order
and record observation before interpretation; a flawed prompt can be obeyed
accurately and still produce the wrong event.

Route only the specialist reviews the scene needs: object geometry,
anatomy/contact, spatial topology, sequence continuity, and finish/text/format.
Synthesize against the locked scene contract; unresolved critical evidence is
`data_gap` or failure, never PASS.

Record proof results in `proof-qa.json` with path, SHA-256, dimensions, derived
scene-contract hash, story read, identity, exact text, brandmark, style, and
native canvas. Creator approval comes only after proof QA passes.

On failure, classify the visible miss. Wrong event means replace the premise;
weak evidence means change action/reaction/object state/consequence; weak
staging means change blocking, eye-line, camera, scale, or focal hierarchy. Do
not polish an unchanged semantic premise. After two misses, set
`proof_failed`, name `repair_visual_premise`, and replace the idea.

After proof approval, generate remaining requested native slides and bind final
actual-pixel QA in `visual-qa.json`. Finish only when story,
entity/anatomy/spatial, identity, style, dimensions, exact text, brandmark,
`final-images.json`, and `final-audit.json` pass.
