IDENTITY — Aachu (Anchal, the woman) and Zuv (Himanshu, the man) are the same recurring people across the carousel. Individual slides may show Aachu, Zuv, both, partial presence, object-only evidence, or no faces when the shot ladder requires it. Identity preservation is the highest creative priority, above decorative style.

HIERARCHY
- Selected actual Aachu/Zuv identity images control faces, expressions,
  posture, body proportions, and wardrobe anchors — always.
- Style references (Observational Intimacy Premium) control illustration style, paper, palette, line quality, composition — never the faces.
- Shared brief images control mood, composition, story essence, text, hand gesture, and objects — unless the creator explicitly says otherwise.
- If these three sources conflict, identity wins.

IDENTITY REFERENCES — `config/references/identity/`
- Select a small story-relevant identity bundle from
  `config/references/identity/` or current-request identity photos before
  generation. Legacy `identity_images/` references are candidate-library
  aliases only when that folder exists.
- These selected images must be attached to the image-generation call. Text
  descriptions alone are not sufficient for final Aachu/Zuv artwork.
- If the current generation path cannot accept actual identity reference images, the correct status is `BLOCKED_FOR_IDENTITY_STYLE_REFERENCES`, not "final" and not "proof passed."
- The 2026-05-30 phone-prank rejection proved this: with only text identity, the model produced generic illustrated characters that the creator rejected on first proof.

AACHU (woman)
- Aachu is 5'6".
- Warm medium-brown South Asian skin.
- Large expressive dark eyes; softly arched brows; delicate nose; natural lips.
- Youthful oval face; soft cheek structure.
- Long dark wavy hair: may be loose, half-tied, or in a casual ponytail. Thickness, dark color, natural waves, and face-framing strands stay consistent across slides.
- Playful warmth, softness, real-person charm. Expressive face; dramatic body language; the spark in the carousel.
- Height: 5'6".

ZUV (man)
- Zuv is 5'8".
- Warm medium-brown South Asian skin.
- Thick dark curly hair (consistent silhouette across slides).
- Strong eyebrows; dark almond-shaped eyes; defined nose.
- Short natural stubble beard (consistent density and shape).
- Kind smile; relaxed masculine facial structure; gentle gaze.
- Steadiness, patience, grounded humor, and care when the story is genuinely
  his beat. Do not make him the default handler, rescuer, admirer, or caretaker
  for every Aachu-led story; relationship motion may come from Aachu, Zuv,
  both, a shared rhythm, or a generic couple situation.
- Height: 5'8".

HEIGHT RULE (hard body-scale gate)
- The two-inch height difference (Zuv 5'8", Aachu 5'6") is non-negotiable in every two-shot.
- Reject any frame where Aachu reads tiny / pixie-sized, or Zuv reads oversized, lanky, chiseled, or generic.
- Eye-line, shoulder, and head positions in a standing two-shot must reflect the real height difference. Sitting or asymmetric poses can hide this — verify against identity refs first.

FACE PRESERVATION
- Preserve identity over decorative style. The characters may be stylized as watercolor illustrations, but they must still be recognizably the same two people.
- Avoid face drift between slides: keep eye shape, eyebrow shape, nose, lips, jawline, cheek structure, hairline, skin tone, beard shape, and hairstyle identity consistent.
- Do not change ethnicity, age, facial proportions, skin tone, hairstyle identity, or body type.
- Do not merge their features with each other.
- Do not create new faces. Do not over-beautify them into different people.

WARDROBE CONTINUITY — casual modern Indo-western
- Wardrobe must be selected from the attached identity images or
  current-request identity photos first. Do not use a fixed wardrobe menu as
  the source of truth.
- For each carousel or slide, identify visible clothing/accessory anchors in
  the selected identity images, then choose story-appropriate outfits, colors,
  fabrics, jewelry, shoes, bags, and small personal details from those anchors.
- Vary wardrobe across slides unless the same scene/time continues, the creator
  asks for continuity, or a signature anchor supports recognition.
- If a scene needs clothing not visible in the selected identity images, extend
  conservatively from the same casual modern Indo-western language and state
  the extension in the slide-specific WARDROBE field. Do not invent random
  model styling or a new fashion palette.

RECURRING PROPS
- cream tote bag, blue-red patterned scarf, denim pouch, coffee cup, sneakers, phone with small heart sticker, travel bag, plants, warm lanterns, balcony lights, wooden bench, cafe table, tiny hand-drawn hearts.
- Props should feel intentional and story-driven, not random decoration.

ANATOMY AND POSE RULES
- Natural hands and fingers; correct count; clean facial anatomy.
- No distorted eyes, warped smiles, broken wrists, extra limbs, duplicated body parts, melted accessories.
- Aachu and Zuv must look natural, flattering, and physically believable. No crouched, cramped, squatting, awkwardly folded, broken, or unflattering poses. Legs and feet must be proportional and comfortably placed.

HARD FAIL — regenerate, do not accept
- faces drift between slides
- ethnicity, age, facial proportions, skin tone, hairstyle identity, or body type changes between slides
- features merge between Aachu and Zuv
- new faces invented; either face does not clearly match the selected identity references
- characters over-beautified into different people (model-prettified, lankier, chiseled, more European, anime-fied)
- identity built from text-only description without using actual identity reference images
- wardrobe chosen from a static menu instead of attached identity/current
  identity photos
- height proportions wrong (Aachu reads tiny or Zuv reads oversized)
- crouched / cramped / unflattering poses
- distorted hands, extra fingers, broken wrists, warped facial features

ANTI-DRIFT NOTES (lessons from real rejections)
- 2026-05-31 Private Captions early proofs rejected for face drift and wrong heights. The creator's note: Aachu looks tiny, Zuv looks oversized/generic — reject and regenerate one corrected proof from actual identity references before batching the rest.
- 2026-05-30 phone-prank Slide 03 rejected because Zuv was already wearing pants while copy said "YOUR SOCKS ON BEFORE YOUR PANTS." Scene logic and ON-IMAGE TEXT must match the visible action — identity preservation does not excuse copy-visual contradictions.
- 2026-05-30 phone-prank Slide 08 rejected for crouched/cramped pose. Identity match was acceptable but pose anatomy failed.
