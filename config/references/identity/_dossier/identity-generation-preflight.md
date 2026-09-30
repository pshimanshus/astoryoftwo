# Identity Generation Preflight
# @a.storyof.two — read this before every image generation run

last_updated: 2026-08-24

---

## Hard Rule

Do not generate or accept a slide if Aachu or Zuv look like generic illustrated
people. Face structure is the first requirement — before style, text, props,
or background. **No generation from text descriptions alone. Photos must be attached.**

---

## Attach These 4 Files To Every Generation Call

| File | Subject | Why |
|------|---------|-----|
| `config/references/identity/aachu/reel-jaldi.jpg` | Aachu solo | Current clean Aachu close-face anchor in natural daylight |
| `config/references/identity/zuv/portrait-07.jpg` | Zuv solo | Current clear Zuv face-and-body anchor with curls and beard visible |
| `config/references/identity/together/together-18.jpg` | Both | Best close-face couple anchor for smiles, curls, beard, and facial scale |
| `config/references/identity/together/together-16.jpg` | Both | Standing full-body anchor for relative scale, body build, and wardrobe |

Label them in the prompt as "identity reference for the woman (Aachu)" and
"identity reference for the man (Zuv)".

For an Aachu-only visible-face call, use the stronger current packet in
`config/references/identity/aachu/curated-v3/manifest.json`. Select 2–4 actual
photos according to the requested view: master front, shallow three-quarter,
deeper three-quarter, and close smile. These supersede `reel-jaldi.jpg` as the
default Aachu face packet for solo identity work.

**Sheet-specific exception:** the four-file bundle above is the operational
baseline. A character sheet or story may replace one or more bundle members
with verified detail references, but every generation call must still attach
2-4 actual photos that cover every visible person, face, body, scale, wardrobe,
and accessory decision. Contact sheets and generated charts never replace the
actual photos as identity authority.

**Generated-chart prohibition:** never use a generated character chart alone
as the face input for Aachu or Zuv. Even a creator-approved chart is only a
supplemental continuity aid; every visible-face generation call still requires
selected actual photos. A photo master board may organize the evidence, but it
also does not replace the original photographs.

## Character Model-Sheet Preflight

A production character chart is a technical face-and-body reference, not a
decorative montage. Before generating a solo face turnaround, first search
every verified private identity library already supplied by the creator, not
only the small copied repository bundle. The current Aachu source library is
`/Users/himanshusharma/Desktop/Identity Images /Aachu Images/` (the directory
name contains a trailing space). Copy a role-specific set of 2–4 strongest real
photos into the repository before generation: neutral front, expression/front,
three-quarter, and true 90-degree side profile. Add a rear or over-shoulder
view when locking the hair silhouette. Do not treat a low-resolution contact
sheet or generated chart as profile evidence.

If no true side-profile photograph exists after searching the verified source
libraries, normally stop with `BLOCKED_FOR_PROFILE_REFERENCE_PHOTOS`. When the
creator explicitly requests a constructed all-angle turnaround, a profile may
be generated only as a provisional rotation of one unified head built from the
strongest front and three-quarter actual photos. It must be recorded as
unverified, cannot be promoted, and requires explicit creator approval per
profile. Never claim mirrored ear, piercing, mole, or hairline details as
verified. The sheet must
carry readable written construction notes and a
dedicated signature-accessory detail: Aachu's evil-eye bracelet on the right
wrist, and Zuv's evil-eye locket on its slim silver chain. Approve each solo
face turnaround before generating the couple scale/interaction sheet.

Creator correction, 2026-08-23: the first Aachu technical face sheet was
rejected because it looked like a different woman and the larger dedicated
Aachu photo library had not been searched. A creator-rejected generated face
must never be repaired from itself or reused as an identity input.

Creator correction, 2026-08-24: in the second Aachu technical face sheet, only
the large `FRONT (NEUTRAL)` view was recognized as correct. The left and right
three-quarter views, both profiles, and the expression row were rejected. This
is a partial component approval, not approval of the sheet. The complete v2
image must not be used as an identity input. Preserve the approved front only
as a supplemental comparison view and rebuild every other angle from matching
real photographs.

The full dedicated Aachu library and the repository Aachu/couple bundle were
searched on 2026-08-24. The bridal image previously labeled `TRUE PROFILE` is
an oblique, downward, smiling candid—not a clean neutral 90-degree profile—and
must not control profile projection. No clean neutral side photograph is
currently available. The creator rejected the complete V4 all-angle sheet as
incorrect. V4 and its profile repair are non-reusable and cannot be used as
identity authority.

**Current Aachu repair protocol:** do not generate another multi-angle or
multi-expression composite. Generate one large neutral-front portrait from
actual photos, stop for creator approval, and then proceed one view at a time.
Reject and retire any failed portrait immediately. Assemble the final technical
sheet from approved portrait pixels without generative redrawing. A constructed
profile is always provisional and requires explicit per-profile approval.

Contact sheet (to pick alternate options):
`config/references/identity/_dossier/identity-face-contact-sheet.jpg`
Note: contact sheet IDs (ID01-ID45) map to pre-rename filenames — use as visual reference
only, not for path lookup. Update `identity-dossier.json` → `selected_generation_bundle` directly.

Full character descriptions: `../README.md`.

---

## Face Non-Negotiables (hard reject if any fail)

**Aachu must have:**
- Large expressive dark eyes — her primary anchor
- Dense very dark mostly-straight hair — thick, with soft bends and the correct silhouette
- Soft oval face, warm medium-brown skin
- Playful expressiveness — not placid or model-generic

**Zuv must have:**
- Thick dark curly hair — curls visible, not straightened
- Short natural stubble beard — always present
- Warm dark almond-shaped eyes with kind, patient gaze
- Warm medium-brown skin, relaxed masculine structure

## Signature Accessories (hard identity gate)

- Aachu always wears her evil-eye bracelet on her right wrist, grounded in
  `aachu/face-04.png`. If the right wrist or forearm is visible, the bracelet
  must be visible in the same position and must not be moved or redesigned.
- Zuv always wears his small round evil-eye locket on a slim silver chain,
  grounded most clearly in `zuv/portrait-07.jpg`. If his neck, open collar, or
  upper chest is visible, the locket and chain must be visible and unchanged.
- When framing or clothing physically hides either accessory, record that
  occlusion in the prompt and visual QA. Never silently omit the accessory.

---

## Generation Procedure

1. Attach the sheet-specific 2-4 verified identity photos, starting from the operational bundle above
2. Load `identity-face-contact-sheet.jpg` only when it helps select or compare alternate face anchors
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
