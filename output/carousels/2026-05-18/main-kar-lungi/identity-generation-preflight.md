# Identity Generation Preflight

This file must be read before every carousel image-generation run.

## Hard Rule

Do not generate or accept a slide if Aachu or Zuv look like generic illustrated people. Face structure is the first requirement, before style, text, props, or background.

## Required Visual Inputs

- output/carousels/2026-05-18/main-kar-lungi/identity-face-contact-sheet.jpg
- identity_images/WhatsApp Image 2026-05-16 at 18.29.46.jpeg
- identity_images/WhatsApp Image 2026-05-16 at 18.29.47.jpeg
- identity_images/WhatsApp Image 2026-05-16 at 18.31.34.jpeg
- identity_images/aachu_zuv.png

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
2. Load the selected face/posture/clothing references into the image context.
3. Start the prompt with the face identity contract.
4. Generate one slide at a time.
5. Reject the image if either face, hair, brows, beard, skin tone, body proportions, or clothing anchors drift from the references.
6. Only then check typography, brandmark, and storyboard match.

## Acceptance Standard

A stranger who knows Aachu and Zuv from the identity folder should recognize both people before reading the text.
