---
name: a-story-direct-visual-story
description: Turn a locked @a.storyof.two concept into image-led physical scenes and audit the generated pixels for story readability. Use after concept lock for storyboards, shot planning, proof generation, visual repair, or final image QA; do not use for open-ended ideation.
---

# Direct Visual Story

Direct scenes, not decorated copy. The picture should communicate a specific
relationship event when the slide text is hidden.

## Load

Read `config/skills/carousel-jam-runtime-context.md` and
`config/skills/illustration-carousel-framework.md`. Canonical rules in
`config/rules/` still govern palette, identity, text, brandmark, dimensions,
visual variety, relationship motion, and scene/entity integrity.

Load `references/craft-canon.md` or `references/a-story-calibration.md` only to
repair a specific craft problem. The default path does not require checker
provenance, independent-review fingerprints, blind-response artifacts, or
legacy migration ceremony.

## Visual Sentence

For every slide write one sentence containing:

- a specific person or subject;
- an observable action;
- the person, object, or space acted upon;
- a visible reaction, consequence, or changed state.

“Warm couple in a cozy room” is mood. “They pull the same dining table in
opposite directions while dinner goes cold between them” is an event.

Also define only what generation needs: point of view, shot size and camera
reason, hands/contact, gaze, body distance, object ownership/state, lived setting
trace, focal hierarchy, and text-safe negative space. Adjacent slides must change
action, story job, camera, setting, or consequence; wardrobe changes alone do not
create variety.

## Direction Pass

1. Confirm the concept, exact facts, copy status, identity/style references,
   current creator corrections, and locked canvases.
2. Describe the before-state, pressure/choice, and after-state of the sequence.
3. Give each slide one physical event. Track recurring objects only when their
   state changes or pays off; decorative motifs are removable.
4. Stage the relationship before adding style language. Specify feet/posture,
   hands, gaze, distance, front/behind/contact order, and expected people.
5. Treat the swipe as an edit: each frame reveals new evidence and earns the
   next one.
6. Compare the scene with the exact copy. Subject, verb, chronology, direction,
   spatial side, and shared-versus-solo action must agree.
7. Compile one compact prompt per slide. The prompt contains the physical event,
   camera/focal hierarchy, attached reference roles, wardrobe from those
   references, compact house style, exact text, brandmark, dimensions, and only
   essential negatives.

If the copy or canvas is still open, the scene direction is provisional and
cannot unlock generation.

## Proof Pass

Choose the frame most likely to fail in story clarity, identity, hands, object
state, composition, or exact text. Generate only that proof first in each
explicitly locked native format:

- default post/carousel: 1080x1440;
- Story/Reel: 1080x1920, explicit request only;
- square: 1080x1080, explicit request only.

Attach the selected actual Aachu/Zuv references and chosen style references to
the generation call. The references guide face, hair, body proportions, height,
expression, posture, and wardrobe.

Put the candidate in package quarantine, then inspect its decoded current
pixels in this order:

1. **Story:** what action and relationship state are visibly communicated;
   compare them with the intended physical event and exact copy.
2. **Integrity:** expected versus observed people/entities; trace each whole
   silhouette against doors, walls, furniture and floor; trace every visible
   owner -> arm -> wrist -> hand -> contacted object.
3. **Identity:** compare both people with the attached reference IDs and record
   concrete face, hair, proportion, posture, and wardrobe evidence.
4. **Finish:** exact text, tiny top-right `@a.storyof.two`, house style, and
   exact native dimensions.

Record the result in `proof-qa.json`, bound to the proof file path, SHA-256, and
dimensions. A prompt, filename, reviewer label, or generator report is never
pixel evidence. Do not show or batch from a failed proof.

The creator approves the proof only after pixel QA passes. That single decision
is Gate 3; do not create extra approval ledgers.

## Repair

Classify the failure before editing:

1. wrong or unreadable event -> replace the physical premise;
2. weak evidence -> change action, reaction, object state, or consequence;
3. weak staging -> change blocking, eye-line, camera, scale, or focal hierarchy;
4. generation drift -> repair reference attachment or prompt wording.

Never regenerate an unchanged semantic premise. Permit at most two total
semantic attempts for one premise. After the second miss, set `proof_failed`,
name `repair_visual_premise` as the next action, and replace the idea instead of
polishing it.

## Final Pass

After proof approval, generate the remaining slides with the same locks. Inspect
every exact final asset with the proof-pass order and record the results in
`visual-qa.json`. Bind each check to the current package-relative path, format,
dimensions, and hash.

Finish only when:

- every slide exists in every requested native format and no unrequested format
  exists;
- the exact text and brandmark are present;
- story, entity/anatomy/spatial, identity, style, and dimension checks pass;
- `final-images.json` matches the bytes on disk;
- `final-audit.json` records PASS.

Use `make visual-check CAROUSEL=... PHASE=pre` for the copy/format/action
preflight and `PHASE=post` for actual-pixel package QA. These checks support the
four gates; they do not add new gates.
