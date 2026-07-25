# Failure audit — The Date That Missed Its Reservation

Status: **BLOCKED. Do not generate from or publish this package.**

## What failed

### 1. The creator correction never reached the active generation artifacts

The creator corrected the vehicle from scooter to car, but the active
`slides.json` and `prompt-pack.json` still contained:

- parked scooter;
- scooter key;
- two helmets / both helmets.

The generation-facing files therefore described a different story from the
creator-approved direction.

### 2. The final door scene was wrong before image generation

The slide copy says:

> Then she went back / and checked it with him.

The active storyboard instead placed the camera inside the entryway, after the
date, and made Aachu check the interior handle while Zuv watched. That loses all
three required pieces of story proof:

- **when:** before leaving, not after returning home;
- **where:** outside the closed apartment door, not inside the house;
- **who does what:** Aachu visibly returns and checks with Zuv, not alone while
  he watches.

The image model rendered the incorrect storyboard faithfully. The primary
failure was scene direction and action topology, not merely image-model taste.

### 3. The formal review state already said REPAIR

Generation should have stopped because:

- `review.json` marked Story-Selling **REPAIR** below the 28/30 threshold;
- `review.json` marked Story Director **REPAIR**;
- `review.json` marked Stage Scene **REPAIR**;
- `review.json` marked the Successful Carousel Standard **REPAIR**;
- `stage-reviews.json` marked the visual reviewer **NEEDS_FIXES**;
- `stage-reviews.json` marked the success-standard reviewer **NEEDS_FIXES**;
- `final-audit.json` marked the package **NEEDS_FIXES**.

`layer-e-story-selling.json` had been changed to `GO`, contradicting the other
review artifacts. That one inconsistent artifact was treated as permission to
continue instead of forcing a stop.

### 4. Prompt provenance was bypassed

The images were generated from ad-hoc chat prompts rather than the active,
compiled, fingerprint-bound `.prompt.txt` handoff. After the creator correction,
the previous pre-generation review was stale and could not approve the changed
story. No fresh director review was bound to the corrected prompt payload.

### 5. Required post-generation QA did not run

No schema-v2 `visual-qa.json` exists. Consequently, the following failures were
not checked before the images were shown:

- exact dimensions;
- scene chronology and camera side;
- action ownership and shared action;
- identity continuity;
- anatomy and scene entities;
- copy-image agreement;
- copy-hidden image-first story readability.

### 6. The generated pixels failed the native format

The requested carousel size is exactly `1080x1440`.

- Slides 1–4 and 6 were `1086x1448`.
- Slides 5 and 7 were `941x1672`.

Slides 5 and 7 were effectively portrait/story-shaped images, not carousel
slides.

### 7. Additional visible scene failures

- Slide 6 was intended to show Aachu stealing a sip from Zuv's chai, but reads
  more like Aachu offering the glass to him.
- Slide 7 showed an inside-house, solo lock check. It did not show Aachu going
  back, a fully closed exterior door, or both partners checking together.

## Why the evaluator appeared to pass

No valid end-to-end evaluator passed the generated set.

An older blind storyboard review passed a coherent but incorrect "back home"
callback. It did not reconcile the exact verbs in the copy against visible
chronology, camera side, door state, return movement, and shared action. Later
review artifacts recorded REPAIR/NEEDS_FIXES, but execution ignored those
failures. The post-generation evaluator never ran at all.

This was therefore both:

1. a review-spec gap for action chronology/topology; and
2. an execution/reporting failure that bypassed recorded blockers and surfaced
   unchecked images.

## Repairs now in place

- The corrected creative baseline specifies **car, not scooter**.
- The final lock scene is explicitly before departure, outside the fully closed
  apartment door, with a visible Aachu turn-back and a shared handle check.
- Stale scooter/helmet/inside-house phrases are recorded as rejected phrases in
  `creator-correction.json`.
- The mistaken identity-proof approval has been invalidated.
- Failed images have been moved to `quarantine/failed-2026-07-21/`.
- Active generated finals and prompt handoff files have been removed.
- Prompt compilation now blocks unresolved door/lock chronology, camera side,
  door state, return path, and shared-vs-solo action.
- Image handoff now blocks contradictory review artifacts and every
  REPAIR/NEEDS_FIXES pre-generation state.
- The workflow now requires a fresh precheck immediately before generation,
  generation only from the active compiled prompt, and structured post-image QA
  before any output can be shown as creator-ready.

## Current gate result

The package doctor correctly returns **BLOCKED** for:

- stale rejected phrases in generation-facing artifacts;
- stale creator-correction and generation-payload fingerprints;
- stale review provenance;
- missing structured post-generation QA.

This package must be rebuilt from the corrected baseline and reviewed as a new
generation payload. It must not be repaired by manually changing a score or
copying the quarantined images back into `final/`.
