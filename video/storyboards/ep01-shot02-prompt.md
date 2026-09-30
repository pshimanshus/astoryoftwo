# EP01 · Shot 2 — Generation Prompt Pack

status: READY TO RUN — run in Codex, which owns the ImageGen call
shot: 2 of 6 · 0:05–0:10 · "Him, in the doorway"
role in lane grammar: cold open
canvas: 1080×1920 (reels_stories)
why first: highest identity load in the episode; every later shot inherits this face

Built by hand rather than through `scripts/carousel.py prepare`. That compiler
requires on-image copy for every beat and this film is silent in four of six
frames. Deviation is deliberate and scoped to the video line — the carousel
lifecycle contract is unchanged.

---

## Attachments — exactly five, no more

Reference minimalism is a standing rule: **do not add photographs to improve
likeness.** More references make the model average across faces instead of
locking to one.

| Role | File |
|---|---|
| Identity — the man (Zuv) | `config/references/identity/zuv/portrait-07.jpg` |
| Identity — the woman (Aachu) | `config/references/identity/aachu/curated-v3/aachu-master-front.jpg` |
| Identity — together, face & scale | `config/references/identity/together/together-18.jpg` |
| Identity — together, body & posture | `config/references/identity/together/together-16.jpg` |
| Style board (hash-bound, style only) | `config/references/style-lock/cinematic-observational-watercolor-v1/contact-sheet.png` |

Style board SHA-256 must match:
`sha256:850634480a635e296cbbb352bcbf461ade1bc4e1c3b419881a614e4ded13ee18`

Aachu's references stay attached even though she is out of frame — they hold the
couple's proportion and wardrobe world. The style board is never face authority.

---

## Compiled Prompt

```text
PRIMARY REQUEST:
Create one image-led @a.storyof.two relationship-story frame. The physical event must remain understandable with the copy hidden. Use the attached actual Aachu and Zuv identity images—each one an actual photograph—for faces, hair, skin tone, age, body proportions, height relationship, expressions, posture, and wardrobe anchors. Generated character charts, contact sheets, prior illustrations, and written descriptions may be supplemental comparison aids but can never replace the actual photographs or become the sole face source. Use the attached approved A Story references for illustration style only. If actual identity and style references are not attached, stop; identity references must be photographs, and prose such as "same couple" is not a substitute.

ON-IMAGE TEXT:
None. This frame carries no words at all. Render the tiny brandmark only. Do not add a caption, quote, subtitle, title card, or any lettering anywhere in the image.

SCENE:
Evening, inside a small lived-in Indian flat. Zuv has just come home and stopped in the open front doorway, not yet stepped inside. His work bag is still on his shoulder and he is in the middle of letting it down. He is alone in the frame — Aachu is not visible. He is tired in a specific, undramatic way: shoulders dropped, jaw slack, gaze unfocused toward the middle of the room. Not sad, not crying, not performing anything. Just a man at the end of a bad day who has not yet started being at home. Behind him the stairwell is a warm dim rectangle; in front of him the flat is larger than he is.

CINEMATIC STORY FRAME:
Medium-wide, camera at standing eye level, straight on. Zuv occupies roughly the lower-middle third of a vertical frame and is deliberately small against the room — the emptiness above and around him is the point and must not be cropped away. Doorway backlight rims his shoulder and hair; a soft cool ambient fill from the flat keeps his face readable at mid-distance. No close-up, no push-in, no shallow-focus blur on his face. Foreground: a stretch of floor. Midground: Zuv and the doorframe. Background: the dim room and one warm lamp well behind him.

LIMB AND HAND PLAN:
Right hand raised to the bag strap at the point of his shoulder, fingers hooked under it, the strap already sliding. Left arm hanging loose and slightly behind the line of his hip, fingers relaxed and slightly curled, not clenched, not splayed. Both arms connect through visible shoulders to a single body. Five fingers per hand, natural knuckle spacing, no merged or missing digits. The bag hangs from the strap under its own weight with a believable diagonal.

WHOLE-PERSON AND OBJECT TOPOLOGY:
One complete standing human figure, head to shoes, feet flat on the floor just inside the threshold, weight settled slightly on one leg. One doorframe, one open door, one shoulder bag, one floor plane, one back wall. The threshold line clearly separates stairwell from room; the door swings into the room and does not intersect his body. Nothing overlaps ambiguously. No second person, no reflection, no silhouette in the stairwell behind him.

IDENTITY AND WARDROBE:
Keep Aachu and Zuv recognizably the same real people shown in the attached identity images, not generic models. Preserve their whole-person likeness, not only their faces. When both stand visibly, keep Zuv only slightly taller: Aachu is 5'6" and Zuv is 5'8". Select clothing, jewelry, accessories, and relationship styling from the attached identity or current-request photos first. Do not invent a disconnected fashion look.
Zuv specifically: dark wavy hair, thick brows, beard and mustache, his real face structure and build. His collar is open and his evil-eye locket on the slim silver chain is visible at his neck — this is mandatory whenever his neck or upper chest shows. Everyday work clothes, worn-in, not styled.

HOUSE STYLE:
Cinematic Observational Watercolor-and-ink story frame on neutral warm-ivory paper grain: a candid, physically specific lived moment rather than a posed portrait; believable motivated light; clear foreground, midground, and background; natural asymmetry; precise microexpressions and body language; two to four narrative details that imply the beat before and after; fine graphite and ink contours, transparent layered pigment blooms, tactile fabric, hair, wood, and ceramic detail, a restrained muted denim, navy, terracotta, sage, and skin-tone palette, and soft organic edges fading into paper.

TEXT AND BRAND:
This frame has no on-image text. Add no words except the tiny, low-contrast handwritten brandmark `@a.storyof.two` at the top-right.

SCENE INTEGRITY:
Show only the people and story entities required by the SCENE. No extra person, duplicate couple, unexplained reflection, silhouette, or limb. Every visible hand belongs to a visible body through a plausible arm and wrist, with natural fingers and believable contact. Keep bodies, clothing, furniture, walls, doors, and props spatially separate and physically coherent. Preserve the stated action, object ownership, gaze, movement direction, chronology, and inside/outside relationship.

ESSENTIAL NEGATIVES:
No photorealism, 3D, glossy AI-stock, generic-watercolor, vector, anime, doll faces, generic couples, staged symmetry, clutter, empty depth, unmotivated glow, yellow, mustard, sepia, parchment, beige, heavy-cream paper, posters, quote-cards, UI, split-screens, extra people or limbs, duplicate couples, malformed hands, broken contact, invented or misspelled copy, missing brandmark, unrequested logos. No on-image words or lettering of any kind. No second figure in the doorway or stairwell. No crying, no theatrical grief, no hand-to-face despair pose. No close-up crop.
```

---

## Acceptance Checks For This Frame

Inspect the returned pixels, not the prompt. Reject on any of these:

- [ ] Zuv reads as the real man in `portrait-07.jpg` — hair, brows, beard, face structure, build
- [ ] Evil-eye locket and slim silver chain present at the open collar
- [ ] Medium-wide holds — he is small in the frame, headroom intact, no close-up crop
- [ ] Face readable at mid-distance without shallow-focus blur
- [ ] Tired reads as *depleted*, not sad, theatrical, or crying
- [ ] Exactly one person, one bag, one doorframe; no reflection or second silhouette
- [ ] Both hands correct — five fingers, right hand on the strap, left loose
- [ ] Zero words in the image except the top-right brandmark
- [ ] Paper ground is warm ivory, not yellow, parchment, sepia, or beige
- [ ] Canvas is 1080×1920

Two generated attempts maximum on this premise. If it fails twice, rewrite the
scene rather than re-rolling — per the imagegen contract's repair rule.

## After This Frame Passes

Shot 2 becomes the face authority for the rest of the episode. Next is **shot 3**
(Aachu hero frame), then the two-shots 4/5/6, then shot 1 last so it can be
composed to rhyme with the finished shot 6.
