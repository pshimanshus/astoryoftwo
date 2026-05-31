# Visual Director Intelligence — @a.storyof.two
# This file loads every session. It is the visual brain.
# When you make any illustration decision, check here first.

last_updated: 2026-05-31
confidence: 1.0
sources:
- direct creator instruction 2026-05-31
- memory/semantic/premium-illustration-style-lock.md
- config/references/a-story-illustration-master-prompt.md
- config/references/identity/README.md
- output/carousels/2026-05-30/before-us-timing-found-us-2 (approved package)

---

## RULE ZERO — Identity References Are Mandatory

**Before any illustrated slide showing faces: check `config/references/identity/`.**

Aachu and Zuv's faces are the product. They are the reason the viewer tags their
partner. Generic South Asian couple faces destroy the carousel — the viewer feels
nothing because the people aren't specific. The 2026-05-30 proof confirmed this:
when the faces didn't match, the art failed even though the style was correct.

**Identity reference bundle location:**
```
config/references/identity/aachu/   ← Anchal's (Aachu's) face photos
config/references/identity/zuv/     ← Himanshu's (Zuv's) face photos
```

**The generation protocol is non-negotiable:**
1. Attach minimum 2 face photos per person from the identity bundle to every image
   generation call where faces will appear
2. Label them explicitly in the prompt: "identity reference for the woman (Aachu)"
   and "identity reference for the man (Zuv)"
3. If the identity bundle is empty or photos cannot be attached: the carousel is
   `HANDOFF_READY_FOR_GENERATION_WITH_IDENTITY_REFS` — NOT NEEDS_FIXES
4. Post-generation: check faces against photos. If faces have drifted, regenerate.
   Never pass output where faces are generic.

**Slides that do NOT need identity references:** object-only slides, detail shots
(hands, anklet, locket), over-shoulder shots where faces aren't visible. Only
mark as blocked when recognizable faces are required by the scene.

**Text descriptions are FALLBACK ONLY.** They inform writing and briefing.
They cannot produce consistent final Aachu/Zuv faces in generated art. The full
text descriptions live in `config/references/identity/README.md`.

---

## The Core Principle

**The concept decides the visual. The visual does not decorate the concept.**

Every shot angle, framing choice, zoom level, and composition is derived from what
the story needs to prove at that exact slide. Ask: "what is the one thing this slide
must make the viewer feel without reading the text?" That answer determines everything
below. Never pick a visual because it looks nice. Pick it because it proves the beat.

---

## Brand Identity Objects — Always Present, Always Recognizable

These are Aachu and Zuv's recurring personal objects. They are identity markers and
emotional proof tools. Use them when the story beat calls for hands, accessories,
or personal details. Do not add them decoratively — add them when the story needs them.

| Object | Who | When to Use |
|--------|-----|-------------|
| Evil eye locket | Shared / his | Close-up when protection, love, or a keepsake is the beat |
| Her bracelet | Aachu | Hand shots, gesture slides, care moments |
| Her anklet | Aachu | Foot/ground shots, travel, movement, arrival/departure |
| Evil eye motif | Both / scene | Appears on objects, clothing, background details — visual continuity |
| Heart motif | Both | As a drawn graphic element in the illustration, not a literal sticker |
| Reaction annotation | In-scene | Handwritten word/feeling floating near a character, like a living caption |

**Rule:** In every carousel, at least one slide should feature one brand object as
a meaningful scene element. This is what makes illustrations feel like @a.storyof.two
and not generic couple art.

---

## Shot Types — When to Use Which

### 1. Close-Up: Emotion / Reaction / Object
Use when: the emotion IS the story, a reaction is the proof, or an object is the evidence.
- Close face (one person): deadpan, realization, soft smile, crying, that look
- Close hands: making something, holding something, touching something quietly
- Close object: the locket, the bracelet, the food, the phone, the item that carries meaning
- When NOT to use: do not use close-up face when the relationship dynamic is what needs to show

### 2. Medium: Relationship Dynamic
Use when: the story is about how they are together — distance, proximity, the space between.
- Both in frame: proximity, touch, side-by-side, one reaching toward the other
- Asymmetric framing: one active, one watching; one moving, one still
- When NOT to use: do not default to medium shot for every slide — it becomes wallpaper

### 3. Over-Shoulder / Watching Shot
Use when: one person is doing something and the other is noticing quietly.
- The watcher perspective: we see what he/she sees
- Creates tenderness without showing both faces
- Great for slides where the "proof" is that someone notices without being asked

### 4. Single Person — One in Frame
Use when: the story beat belongs to one person's experience.
- Her expression in the doorway
- His hands making something
- Her sitting alone, then the next slide he arrives
- Forces the viewer to read the emotion on one face clearly
- Do NOT put both people in every slide — sometimes one is more powerful

### 5. Object / Scene Only — No People
Use when: the object or setting carries the meaning more than any face could.
- The cup of tea already made
- The suitcase at the door
- The note on the counter
- The evil eye locket on a surface
- Best for the "silent proof" beat — show the consequence, not the character

### 6. Detail Shot — Body Part or Fragment
Use when: specificity is the emotion.
- Her anklet as she walks
- His hand finding hers without looking
- Her bracelet against his sleeve
- The object moving between hands
- This is the "movie close-up" equivalent — holds the moment

### 7. Reaction Annotation Slide
Use when: a feeling needs to exist as a visible floating element, not as copy below.
- A word, a sound, a reaction (like "AB AAYE HO?" floating near her)
- Drawn in the handwritten annotation style, integrated into the scene
- Should look like the character's thought or reaction is leaking into the image

---

## Composition Rules

### Face Presence
**You do not need to show both faces every slide.** In fact, showing faces in
every slide weakens the carousel. Vary face presence across slides:
- Slide 1 (hook): one face OR a scene detail that creates curiosity
- Middle slides: mix of medium shots, object shots, detail shots, single person
- Penultimate slide: the emotional peak — close emotion or over-shoulder
- Final slide: can be both faces (the earned reunion/resolution) OR a single
  quiet object that carries the payoff

### Couple Placement
- Lower to middle-lower frame: couple placement keeps upper space for text
- Never centered and symmetrical by default — asymmetry creates visual energy
- The one who acts is more forward/dominant in frame; the one who reacts is slightly behind

### Upper Space
- Always preserve clean upper-middle negative space for on-image text
- Text sits above or around the figures, never on their faces or bodies
- Warm ivory/off-white paper fills this space naturally

### When To Show Less of Both
Resist the urge to always show the full couple. Show:
- Just hands when hands are the story
- Just a back when someone is leaving
- Just an object when the object IS the relationship proof
- Just the space between two people when distance is the emotion
A single well-framed detail often hits harder than a full-figure scene.

---

## Visual Storytelling Sequence Across Slides

Think of the carousel as a short film. Apply shot variety like a director:
```
Slide 1: WIDE or DETAIL (hook — create curiosity, don't give everything)
Slide 2: MEDIUM (establish the dynamic)
Slide 3: CLOSE or DETAIL (the specific proof — the behavior, the object)
Slide 4: REACTION or SINGLE (the emotional turn — one person's face or moment)
Slide 5: CLOSE OBJECT or ANNOTATION (the quiet evidence before payoff)
Slide 6+: MEDIUM or CLOSE (the earned ending — together or apart, both work)
```
Never repeat the same shot type twice in a row. Never use full-couple medium
shots for 4 of 5 slides.

---

## Font + Typography

- One consistent handwritten storybook font across all slides in a carousel
- Dark charcoal, slightly imperfect, naturally integrated into the paper
- Readable at phone screen size — never smaller than a comfortable phone read
- Upper-middle placement: the text sits in the clean space, not overlaid on faces
- On-image text is BAKED into the illustration, not overlaid in post
- Reaction annotations use the same font family but with a slightly rougher/faster
  feel, as if written in the moment

---

## Aesthetic Non-Negotiables

- Paper: warm ivory / off-white. NOT yellow. NOT parchment. NOT sepia. NOT beige.
  If it reads warm yellow under a phone screen, it fails.
- Style: premium hand-drawn watercolor-and-ink. NOT flat vector. NOT digital brush.
  NOT generic AI watercolor. Visible paper grain, layered blooms, fine ink linework.
- Palette: navy, muted denim, camel, terracotta, sage, dusty coral, soft rust.
  Muted and vintage, never saturated or neon.
- Texture: fabric texture on clothes, ceramic warmth on cups, wood grain on surfaces,
  shoe leather, bag material. The tactile detail is what makes it premium.

---

## Face Consistency Across A Carousel

Identity references must be re-attached in every new generation batch — models
do not retain identity from a previous call. Face drift accumulates in long
carousels (7+ slides) and across sessions.

**Fastest identity consistency checks:**
- Aachu: her long dark wavy hair silhouette — thickness and wave pattern must match
- Zuv: his thick dark curly hair silhouette — the curls must be present, not straightened
- Both: skin tone must stay consistent across every slide in the carousel

If you cannot guarantee face consistency for a specific slide, fall back to
hands, backs, objects, or single-character shots rather than risk a generic face.

**Full identity description and generation protocol:** `config/references/identity/README.md`

---

## What Makes a Visual Choice @a.storyof.two

The visual feels like @a.storyof.two when:
- The brand objects appear naturally as part of the scene
- The shot type is serving the story, not filling space
- The couple feels specific — not like any two people, but like THESE two people
- The warmth is in the details (her anklet, his hand, the evil eye locket, the
  worn-in texture of familiar objects)
- The text and image are integrated — you couldn't remove the text without the
  image feeling incomplete, but the image could almost tell the story alone
- It does not look like any other couple carousel on Instagram
- It has @a.storyof.two brandmark on every slide to ensure copywriting.


---

## What Makes a Visual Choice NOT @a.storyof.two

- Both people shown symmetrically centered in every slide
- No brand objects anywhere
- Generic poses: standing together looking at camera, sitting at a table, walking hand-in-hand
- Face forward, smiling, clearly posed — feels like a stock photo not a moment
- Dense cinematic landscape takes over the frame (the couple becomes tiny)
- Yellow/parchment paper that reads warm in a bad way
- No shot variation — same framing slide after slide
- Text placed on faces or clothing instead of clean upper space
