# Identity Generation Preflight

This file must be read before every carousel image-generation run.

## Hard Rule

Do not generate or accept a slide if Aachu or Zuv look like generic illustrated people. Face structure is the first requirement, before style, text, props, or background.

## Required Visual Inputs

- output/carousels/2026-08-14/a-bad-day-was-never-the-whole-truth/identity-face-contact-sheet.jpg
- config/references/identity/aachu/reel-jaldi.jpg
- config/references/identity/together/together-16.jpg
- config/references/identity/together/together-18.jpg
- config/references/identity/zuv/portrait-07.jpg

## Face Identity Contract

### Himanshu/Zuv
- dark wavy hair with visible volume
- thick dark brows
- warm brown skin tone
- rounded/oval smiling face structure
- trimmed full beard and mustache
- calm grounded expression, not a generic model face
- medium-tall broader build relative to Aachu

### Aachu/Anchal
- long dark hair
- expressive eyes and brows
- warm fair-medium skin tone
- soft oval/round face structure
- fuller lips and expressive smile
- playful dramatic energy under the softness
- slightly smaller/petite presence relative to Himanshu

## Generation Procedure

1. Load the identity contact sheet into the image context.
2. Use the visible ID labels on the contact sheet to choose 2-4 strongest current anchors for the story.
3. Load the selected face/posture/clothing references into the image context as actual images.
4. Start the prompt with the face identity contract.
5. Generate one slide at a time.
6. Reject the image if either face, hair, brows, beard, skin tone, body proportions, or clothing anchors drift from the references.
7. If Aachu/Anchal is wrong, do not continue the set; pick stronger Anchal option IDs from the contact sheet and regenerate from slide 1.
8. Only then check typography, brandmark, and storyboard match.

## Acceptance Standard

A stranger who knows Aachu and Zuv from the identity folder should recognize both people before reading the text.
