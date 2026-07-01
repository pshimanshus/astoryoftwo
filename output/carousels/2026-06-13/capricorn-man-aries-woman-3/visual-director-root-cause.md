# Visual Director Root Cause

status: PREVIOUS_VISUAL_SYSTEM_REJECTED

## What Failed

The previous visual room approved the idea but did not enforce a designed frame.
It passed broad scene concepts such as balcony, keys, notebook, and movement,
but it did not turn those concepts into hard camera, crop, blocking, and logic
requirements.

## Concrete Failure Seen

The rejected proof crop showed Zuv clearly but cropped Aachu's face and upper
body out of the frame. The wrist contact read ambiguous/restraint-like instead
of playful invitation. The frame looked like a zoomed fragment, not a premium
Instagram carousel slide.

## Root Cause

- Visual direction was vibe-led instead of shot-led.
- `visual-plan-quality.json` used generic GO checks and did not require
  face visibility, crop safety, balanced couple blocking, or logic readability.
- The generation prompt contained vague slide-specific fields such as
  "Natural couple action", "Use identity photos", and "Scene props only".
- The prompt prioritized watercolor style over DOP composition and carousel
  design.

## New Rule

No image can pass because it has nice watercolor texture. Every proof and final
must pass the frame first:

- both faces visible unless the slide explicitly uses an over-shoulder POV;
- no partner cropped into a torso-only or limb-only fragment;
- hand contact must read as affection, invitation, or care, never restraint;
- the viewer must understand the relationship action before reading text;
- exact 4:5 Instagram composition with safe negative space;
- text must not rescue a confusing image.

