# Identity Generation Preflight
# @a.storyof.two — read this before every image generation run

last_updated: 2026-05-31

---

## Hard Rule

Do not generate or accept a slide if Aachu or Zuv look like generic illustrated
people. Face structure is the first requirement — before style, text, props,
or background. **No generation from text descriptions alone. Photos must be attached.**

---

## Attach These 4 Files To Every Generation Call

| File | Subject | Why |
|------|---------|-----|
| `config/references/identity/aachu/portrait-02.jpg` | Aachu solo | Best solo — natural daylight, face large and clear, full warm smile |
| `config/references/identity/together/together-18.jpg` | Both | Best overall — couch selfie, both faces close, Zuv curls + beard clear |
| `config/references/identity/together/together-19.jpg` | Both | Beach hut selfie, both close, different lighting context |
| `config/references/identity/together/together-21.jpg` | Both | Domestic hug, Aachu very clear, intimate natural moment |

Label them in the prompt as "identity reference for the woman (Aachu)" and
"identity reference for the man (Zuv)".

**Note on Zuv:** There is currently no close-up solo portrait of Zuv in this library.
The together shots above are the best Zuv identity anchors. The couch selfie
(together-18.jpg) is the single most important file to attach for Zuv's face.

Contact sheet (to pick alternate options):
`config/references/identity/_dossier/identity-face-contact-sheet.jpg`
Note: contact sheet IDs (ID01-ID45) map to pre-rename filenames — use as visual reference
only, not for path lookup. Update `identity-dossier.json` → `selected_generation_bundle` directly.

Full character descriptions: `../README.md`.

---

## Face Non-Negotiables (hard reject if any fail)

**Aachu must have:**
- Large expressive dark eyes — her primary anchor
- Long dark wavy hair — thick, dark, correct silhouette
- Soft oval face, warm medium-brown skin
- Playful expressiveness — not placid or model-generic

**Zuv must have:**
- Thick dark curly hair — curls visible, not straightened
- Short natural stubble beard — always present
- Warm dark almond-shaped eyes with kind, patient gaze
- Warm medium-brown skin, relaxed masculine structure

---

## Generation Procedure

1. Load `identity-face-contact-sheet.jpg` into image context
2. Attach the 4 identity references above
3. Start the prompt with the face non-negotiables
4. Generate one slide at a time — never batch all slides in one call
5. Check each output against photos before proceeding to the next slide
6. **If Aachu wrong:** pick 2-4 stronger Aachu options from contact sheet → rebuild bundle → regenerate from slide 1
7. **If Zuv wrong:** pick 1-2 stronger Zuv options → rebuild → regenerate from slide 1
8. Only after faces pass: check typography, brandmark, storyboard match

---

## Slides With Hidden Faces

Do not drop the selected identity bundle from final carousel generation just
because a slide hides faces. The package and handoff must still carry the
selected identity image inputs so wardrobe, hands, jewelry, body scale, and
relationship continuity stay anchored.

For object-only, detail, over-shoulder, or scene-only slides, QA should not
claim face preservation from the image itself. Instead verify that the slide
does not invent new faces or bodies, and that any visible clothing, hands,
jewelry, or recurring personal details match the selected identity bundle or
current-request identity photos.

---

## Acceptance Standard

**A stranger who knows Aachu and Zuv should recognize both people before reading the text.**
A beautiful scene with wrong faces = fail. Regenerate.
