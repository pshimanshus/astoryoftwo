# Image Generation Repair Plan

status: PROOF_REQUIRED_BEFORE_BATCH
date: 2026-05-24

## What Failed

The previous generated images were rejected because they were generic
photoreal contact sheets. They did not preserve Aachu/Zuv identity, the
accepted illustrated carousel style, native single-slide output, or the
package's visual QA contract.

## Correct Fix

Do not regenerate the whole carousel blindly.

Generate one proof slide first:

- slide: 4
- copy: `He saw. He pretended to sleep.`
- reason: this slide proves the story is shared couple mischief, not theft.

Only after slide 4 passes identity, style, story, text, and safety QA should
the remaining 4:5 slides and separate 9:16 slides be generated.

## Non-Negotiables

- Use `identity-face-contact-sheet.jpg` and `identity_images/aachu_zuv.png` as
  actual visual references.
- Use the accepted illustrated style references, not photoreal phone shots.
- Generate native individual slides, not contact sheets.
- Keep the visual natural and ordinary: no glossy romance, no luxury bedroom,
  no perfect-boyfriend framing.
- The man must look sleepy, aware, and lightly complicit; the woman must look
  mischievous and mock-official, not guilty or greedy.
- Cash must be a tiny domestic proof object, not a money-flex prop.

## PASS Criteria For Proof Slide

- same recurring Aachu/Zuv illustrated identity;
- 4:5 publishable carousel slide;
- exact text is readable;
- warm hand-drawn desi storybook style;
- one clear wallet/bedroom action;
- joke reads as shared system;
- no generic stock couple or photoreal AI look.

## STOP Criteria

Stop and repair prompts if the proof slide:

- changes the faces;
- becomes photoreal;
- creates a contact sheet;
- uses foreign-looking cash;
- makes the wife look like she is stealing;
- makes the husband look helpless, angry, or like a saint.
