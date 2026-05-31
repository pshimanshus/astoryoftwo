# Prompt Route V2 Repair

status: GENERATION_PAUSED_AFTER_FAILED_PROOF
reason: first four generated proofs failed identity, paper tone, scene blocking, and text integration gates.

## Non-Negotiable Repair Rules

- Generate one proof slide first, not a batch.
- Attach actual identity references and style-lock references before generation.
- Use the master prompt verbatim as the base.
- Use neutral warm ivory/off-white paper only; reject yellow, parchment, sepia, beige/tan, or heavy cream.
- Zuv appears only when he has a story job. No repeated doorway/watching posture.
- Aachu can carry search slides alone. The relationship still exists through the household evidence.
- Text must be part of the illustration: hand-drawn charcoal lettering in clean upper-middle negative space, exact spelling/punctuation, no extra words, no altered line breaks unless explicitly supplied.
- If generated text is wrong, the slide is failed, not “almost.”
- If product text is wrong, use the brand label workflow for product microtext only.

## Reference Attachments For Every Character Slide

- `output/carousels/2026-05-31/he-didn-t-marry-organized/identity-face-contact-sheet.jpg`
- `config/references/identity/aachu/portrait-02.jpg`
- `config/references/identity/together/together-18.jpg`
- `config/references/identity/together/together-19.jpg`
- `config/references/identity/together/together-21.jpg`
- `config/references/style-lock/observational-intimacy-premium/contact-sheet.png`
- `config/references/style-lock/observational-intimacy-premium/slide-01.png`
- `config/references/style-lock/observational-intimacy-premium/slide-03.png`
- `config/references/style-lock/observational-intimacy-premium/slide-08.png`

## Slide Blocking V2

1. `He didn't marry organized.`
   - Aachu solo.
   - Cropped lower-room vanity scene: her hand in hair, open drawer, tiny missing tube gap.
   - Zuv absent. The joke is her search-chaos, not him watching.

2. `He married "maine yahin rakha tha."`
   - Aachu solo or Zuv only as an off-frame hand/blurred shoulder.
   - Aachu points confidently at the exact wrong spot.
   - No full standing Zuv.

3. `He married drawer-searching.`
   - Hands-first drawer scene.
   - Aachu face visible in partial three-quarter angle, searching.
   - Zuv absent.

4. `Pouch-searching. Bathroom-searching.`
   - Aachu with pouch in foreground and bathroom shelf/mirror behind.
   - Zuv absent.
   - Text must stay exactly one line or two lines only if the exact punctuation remains.

5. `And wardrobe-searching also.`
   - Aachu half-hidden behind wardrobe door, searching through folded clothes.
   - Zuv absent.
   - The absurdity should carry the slide.

6. `Then he opened his stock drawer.`
   - Zuv enters actively for the first time.
   - Show his hand opening a neat stock drawer. Aachu only as a partial surprised profile or not visible.
   - His role is action, not observation.

7. `Her Dot & Key was already there.`
   - Product-reveal slide.
   - Zuv hand holds drawer open; Aachu reaction can be a small side profile.
   - Blue Dot & Key Barrier Repair tube front-facing and legible.
   - Product is secondary to the reveal, but readable.

8. `Maybe love is knowing what she'll need before she does.`
   - Both appear, but naturally close: seated at vanity/bed edge, not standing.
   - Aachu softens; Zuv hands her the tube or places it quietly near her routine.
   - Earned payoff, no packshot feel.

## Proof Prompt To Use First

Use slide 6 as the first proof because it tests the repaired Zuv role: he must act, not watch.

```text
USE CASE:
illustration-story

ASSET TYPE:
Premium hand-drawn romantic watercolor-and-ink @a.storyof.two Instagram post illustration in native 4:5 portrait composition. Render exact readable text baked naturally into the image and add only the tiny low-contrast bottom-right handwritten brandmark.

REFERENCE IMAGE ROLES:
Use the attached Aachu/Zuv identity references as face, hair, skin tone, expression, posture, and wardrobe anchors. Use the attached Observational Intimacy Premium references only for style: neutral warm ivory/off-white paper, visible paper grain, fine pencil/ink linework, transparent watercolor blooms, muted vintage palette, soft faded edges, airy upper-middle handwritten text, and tiny bottom-right brandmark.

ON-IMAGE TEXT:
Then he opened his stock drawer.

SCENE:
A quiet domestic bedroom/vanity corner. Zuv is not standing and watching; he is actively opening a neat household stock drawer with one hand. The drawer has small organized sections for skincare, chargers, clips, and tiny household backups. Aachu is only partially visible as a surprised side profile or soft shoulder at the edge of frame. The missing-product search has paused because Zuv knows exactly where the backup is. The blue Dot & Key tube may be hinted inside the skincare section, but do not make it the hero yet.

TEXT PLACEMENT / TYPOGRAPHY:
Place the exact text in clean upper-middle negative space as warm dark-charcoal hand-drawn lettering integrated into the paper. Do not change the wording, punctuation, capitalization, or spacing. Do not add extra words. Do not put text on a poster/card/panel.

COMPOSITION:
Native 4:5 vertical. Neutral warm ivory/off-white paper, not yellow or parchment. Drawer/action in the lower-middle. Generous breathing room above. Zuv's hand and drawer-opening action must prove the line even if text is hidden.

CHARACTER IDENTITY:
Zuv must preserve his real curly dark hair, strong brows, warm eyes, short stubble beard, medium-brown South Asian skin, and calm amused expression from the identity references. Aachu, if visible, must preserve expressive dark eyes, long dark hair, warm medium-brown South Asian skin, soft oval face, and playful strawberry-cheek warmth. Do not darken either face beyond the references. No generic faces.

STYLE:
Creator-approved Observational Intimacy Premium A Story of Two watercolor-and-ink look. Fine ink and pencil texture, soft transparent watercolor, tactile drawer/wood/skincare details, gentle muted palette, no photorealism, no flat vector, no anime, no generic AI watercolor.

BRANDMARK:
Include only the tiny low-contrast handwritten `@a.storyof.two` in the bottom-right corner.

FAIL IF:
Zuv is merely standing and watching; paper is yellow/parchment; faces are too dark or generic; the text changes; the text looks like a digital overlay; the product becomes an ad packshot; anatomy is cramped or awkward.
```
