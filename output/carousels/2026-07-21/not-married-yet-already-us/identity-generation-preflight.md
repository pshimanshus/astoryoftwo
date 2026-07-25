# Identity Generation Preflight

This file must be read before every carousel image-generation run.

## Hard Rule

Do not generate or accept a slide if Aachu or Zuv look like generic illustrated people. Face structure is the first requirement, before style, text, props, or background.

## Required Visual Inputs

- output/carousels/2026-07-21/not-married-yet-already-us/identity-face-contact-sheet.jpg
- config/references/identity/aachu/face-04.png
- config/references/identity/aachu/reel-jaldi.jpg
- config/references/identity/together/together-18.jpg
- config/references/identity/zuv/portrait-07.jpg

## Face Identity Contract

### Himanshu/Zuv
- warm medium-brown South Asian skin
- thick dark curly hair with a visible curl silhouette
- strong dark brows, dark almond eyes, and a defined nose
- relaxed masculine face structure
- short natural stubble, never clean-shaven and never a full beard
- natural body proportions
- exactly about two inches taller than Aachu

### Aachu/Anchal
- warm medium-brown South Asian skin
- large expressive dark eyes and softly arched brows
- delicate nose, natural lips, youthful oval face, and soft cheeks
- long thick dark wavy hair
- playful real-person expression, never a generic model face
- natural body proportions
- exactly about two inches shorter than Zuv

## Reference Exclusions

- Do not copy wedding or engagement cues from any reference: no rings, bangles, ceremonial clothing, kiss pose, or staged couple-portrait pose.
- Do not copy carousel dots, UI, background vehicles, old reference text, or old reference brandmarks.
- Treat the contact sheet as an identity catalog only; never copy its grid, labels, layout, poses, or background.

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
