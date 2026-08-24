# Visual Director Intelligence — @a.storyof.two
# This file loads every session. It is the visual brain.
# When you make any illustration decision, check here first.

last_updated: 2026-07-20
confidence: 1.0
sources:
- direct creator instruction 2026-05-31
- direct creator correction 2026-06-15: break the pattern across carousel
  images; do not repeat the same angle, same couple action, same books/bed/chai
  garden scene grammar
- direct creator correction 2026-06-30: on-image text must be present from the
  first proof onward; blank-scene/deferred-lettering workflows are blocked,
  not valid intermediates
- direct creator instruction 2026-07-20: illustrations must communicate as
  richly as a writer, filmmaker, comics author, or storyboard director; the
  "I'm leaving" / juttis frame is the calibration because visible action,
  object ownership, blocking, and reaction carry more story than copy alone
- .agents/skills/a-story-direct-visual-story/SKILL.md
- Bruce Block, The Visual Story (Routledge)
- Scott McCloud, Making Comics (author source)
- Pixar in a Box, The Art of Storytelling (Pixar / Khan Academy)
- Neil Cohn, Visual Narrative Structure (Cognitive Science)
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

Richness means causal evidence, not decorative density. A directed frame has a
specific subject, visible action, target/object, and reaction, consequence, or
changed state. The location, light, wardrobe, props, hands, gaze, feet, body
distance, and camera should reveal character or event history rather than fill
the scene.

---

## Recurring Identity Objects — Worn Anchors Mandatory, Scene Motifs Optional

These are Aachu and Zuv's recurring personal objects. The creator correction on
2026-08-23 makes two worn accessories permanent identity anchors: Zuv's
evil-eye locket and Aachu's right-wrist evil-eye bracelet. They are always worn
and must be rendered whenever the corresponding neckline/chest or right wrist
is visible. Other objects and scene motifs remain optional proof tools.

| Object | Who | When to Use |
|--------|-----|-------------|
| Evil-eye locket on slim silver chain | Zuv | Always worn; visible whenever neck, open collar, or upper chest is visible |
| Evil-eye bracelet on right wrist | Aachu | Always worn; visible whenever her right wrist or forearm is visible |
| Her anklet | Aachu | Foot/ground shots, travel, movement, arrival/departure |
| Evil eye motif | Both / scene | Appears on objects, clothing, background details — visual continuity |
| Heart motif | Both | As a drawn graphic element in the illustration, not a literal sticker |
| Reaction annotation | In-scene | Handwritten word/feeling floating near a character, like a living caption |

**Rule:** There is no per-carousel quota for optional props or decorative
motifs. Do not force a background evil eye, heart, shoes, chai, or another motif
into an unrelated scene. This optionality does not apply to the two signature
worn accessories: keep Zuv's locket and Aachu's right-wrist bracelet on their
bodies, showing them whenever the framing makes their placement visible.

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

Think of the carousel as a short film. This is an example ladder, not a fixed
recipe:
```
Slide 1: WIDE or DETAIL (hook — create curiosity, don't give everything)
Slide 2: MEDIUM (establish the dynamic)
Slide 3: CLOSE or DETAIL (the specific proof — the behavior, the object)
Slide 4: REACTION or SINGLE (the emotional turn — one person's face or moment)
Slide 5: CLOSE OBJECT or ANNOTATION (the quiet evidence before payoff)
Slide 6+: MEDIUM or CLOSE (the earned ending — together or apart, both work)
```
Avoid unmotivated repetition. Consecutive shot sizes may repeat when the
continuous action or designed comparison needs them, but camera position,
blocking, focal evidence, or story information must change and the repetition
must have an explicit reason. Do not use full-couple medium shots for 4 of 5
slides unless the repetition itself is the authored device and a fresh reader
can identify the changing story.

## Pattern-Breaking Rule

Changing outfits is not enough. Every carousel visual plan must change the
visual sentence across slides:
- shot type: wide, medium, close-up, over-shoulder, single-person, object-only,
  detail, reaction, or transition;
- camera angle: front, profile, overhead, table-level, doorway, reflection,
  behind/over-shoulder, or distant establishing view;
- setting lane: bedroom, kitchen, street, cafe, balcony, travel, doorway,
  car/ride, bathroom/vanity, terrace, shop, hotel, family-function, or
  object-only paper space;
- primary action and who is visible.

Hard fail: every slide shows both of them from the same three-quarter/front
angle doing the same emotional listening/comforting action. Hard fail: the deck
keeps returning to the same bed, books, chai, mugs, garden table, balcony
plants, or generic soft-couple setup without story need. If the story needs one
continuous location, vary distance, angle, hand/object focus, and perspective
so the carousel still feels like a sequence rather than repeated captions.

## Proof-First Pixel Readability Loop

After concept lock, use `.agents/skills/a-story-direct-visual-story/SKILL.md`.

1. After exact copy and requested native formats are locked, write one concrete
   physical event per slide: visible people, action, hands/contact, gaze,
   blocking, object state, camera reason, and visible consequence. A compact
   copy-hidden read is useful when the visual premise is ambiguous, but it does
   not create another lifecycle or approval artifact.
2. Generate only the riskiest slide. Inspect the decoded current pixels
   image-first, then compare observed action and relationship state to the
   physical event and exact copy. Bind `proof-qa.json` to the package-relative
   path, SHA-256, and native dimensions. Check story, entity/anatomy/spatial
   integrity, identity, exact text, brandmark, style, and dimensions in order.
3. Only passed proof pixels plus explicit creator approval unlock the remaining
   deck. Repeat the same file-bound checks for every final asset in
   `visual-qa.json` and `final-audit.json`.

Prompts, filenames, reviewer names, and generator claims are not pixel evidence.
The format set is exactly the request lock: post by default only when
unspecified, Story/Reel or square only when explicit. Never infer intent from
old folders or create 9:16 by default. Old reports may inform diagnosis but
cannot promote current files; rerun pixel QA against current locks and bytes.

---

## Font + Typography

- One consistent handwritten storybook font across all slides in a carousel
- Dark charcoal, slightly imperfect, naturally integrated into the paper
- Readable at phone screen size — never smaller than a comfortable phone read
- Upper-middle placement: the text sits in the clean space, not overlaid on faces
- On-image text is generated into the illustration from the first proof onward.
  If exact copy fails, block or retry with a stronger text-bearing prompt. A
  local typography repair may only correct an already text-bearing raster; it
  is not permission to create a blank illustration for deferred lettering. The
  final must read as one integrated A Story paper illustration, not a separate
  quote-card, platform overlay, or flat digital layer.
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
- Any object that appears has a natural story job; an object motif is optional
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
- Objects are decorative shorthand rather than causal relationship evidence
- Generic poses: standing together looking at camera, sitting at a table, walking hand-in-hand
- Face forward, smiling, clearly posed — feels like a stock photo not a moment
- Dense cinematic landscape takes over the frame (the couple becomes tiny)
- Yellow/parchment paper that reads warm in a bad way
- No shot variation — same framing slide after slide
- Same bed/table/chai/books/garden prop cluster repeated across the deck
- Wardrobe changes but camera, action, and blocking stay the same
- Text placed on faces or clothing instead of clean upper space
