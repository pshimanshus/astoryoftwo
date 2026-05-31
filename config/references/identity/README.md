# Character Identity Reference Bundle — Aachu & Zuv
# @a.storyof.two

last_updated: 2026-05-31
status: POPULATED — 47 photos, ready for generation
confidence: 1.0

---

## Why This Folder Is The Most Important Folder In This Project

Faces are the #1 asset and differentiator of @a.storyof.two.

Every carousel viewer sees the couple and thinks: "that's them." That recognition
creates the tag reflex — "send this to my partner." Generic South Asian couple
faces destroy the product. The 2026-05-30 proof confirmed this: when the faces
didn't match, the art failed even though the style was correct.

**No final illustrated art without actual photos from this folder attached to the
image generation call. If photos cannot be attached: HANDOFF_READY, not NEEDS_FIXES.**

**For the generation procedure: read `_dossier/identity-generation-preflight.md` before every generation run.**

---

## Folder Structure

```
config/references/identity/
  aachu/       face-01..06.png, portrait-01..06.jpg   (12 photos of Aachu solo)
  zuv/         face-01..07.png, portrait-01..07.jpg   (14 photos of Zuv solo)
  together/    together-01..21 (.jpg/.png)            (21 photos of both together)
  _dossier/    identity-dossier.json                  machine catalog: 45 images, face detection, option IDs
               identity-face-contact-sheet.jpg        all faces labeled — use to pick stronger refs
               identity-generation-preflight.md       the operational document for generation
  README.md    ← this file: what + who
```

**Total: 47 photos. All filenames clean, no spaces.**

---

## Character Identity Descriptions

These prose descriptions are for writing generation prompts and briefing agents.
They are NOT sufficient for generating consistent faces — photos are always required.
The machine version lives in `_dossier/identity-dossier.json` → `face_identity_contract`.

### Aachu (Anchal) — The Woman

Warm medium-brown South Asian skin. Large expressive dark eyes — they are her
most recognizable feature; they widen with exasperation, soften with love, and
spark with humor. Softly arched brows. Delicate nose. Natural lips. Youthful
oval face with soft cheek structure. Long dark wavy hair — thick, dark brown,
natural waves, falls past shoulders, face-framing strands. Hair can be loose,
half-tied, or casual ponytail depending on the scene but the thickness, color,
wave texture, and silhouette must stay consistent.

Her presence is warm, playful, and alive. Real-person charm — not model-perfect.
Do not turn her into a generic model, anime character, or doll-like figure.

**Signature features (fastest identity checks):**
- Large expressive dark eyes — the primary anchor
- Long dark wavy hair silhouette — thickness and wave pattern
- Soft cheek structure and oval face shape
- Natural medium-brown skin tone — never lightened or darkened

### Zuv (Himanshu) — The Man

Warm medium-brown South Asian skin. Thick dark curly hair — the curls are
distinctive; must be preserved, not straightened, not reduced to a slight wave.
Strong eyebrows. Dark almond-shaped eyes — warm, observant, kind. Defined nose.
Short natural stubble beard — present, not heavy, not clean-shaven, not full beard.
Relaxed masculine facial structure. Kind smile. Gentle gaze that communicates
patience and quiet love.

His presence is calm, grounded, warm. Do not make him older, younger, overly
muscular, overly chiseled, generic, or photorealistic.

**Signature features (fastest identity checks):**
- Thick dark curly hair silhouette — the primary anchor
- Short natural stubble — always present
- Dark almond-shaped eyes with warm gaze
- Natural medium-brown skin tone — consistent with Aachu's

---

## Adding More Photos

Continue the existing sequence:
```
aachu/face-07.png, aachu/portrait-07.jpg   (continue from 06)
zuv/face-08.png, zuv/portrait-08.jpg       (continue from 07)
together/together-22.jpg                   (continue from 21)
```

After adding, update `_dossier/identity-dossier.json` → `selected_generation_bundle` if
the new photos are stronger identity anchors than the current 4.

---

## What This Folder Is NOT

- Not a style reference — style lives in `style-lock/observational-intimacy-premium/`
- Not a mood board — mood comes from the concept and scene direction
- Not optional — it is the foundation of every final illustration

Style-lock controls how the illustration looks.
This folder controls WHO is in the illustration.
Both are required. Neither replaces the other.
