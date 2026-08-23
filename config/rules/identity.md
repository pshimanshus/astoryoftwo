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

IDENTITY EVAL STOP GATE
- No identity eval, no next slide. After any proof slide or creator identity
  correction, stop before generating the rest of the batch until identity is
  explicitly reviewed.
- A pass requires a structured `identity-consistency-review.json` or
  `visual-qa.json` with Aachu/Zuv reference IDs and specific likeness notes.
  Casual visual taste notes, dimensions checks, or "looks good" commentary do
  not count as identity pass.
- If the current tools cannot run a real face/likeness comparison, record
  `BLOCKED_FOR_IDENTITY_EVAL` or `IDENTITY_UNVERIFIED` and tell the creator.
  Do not keep moving forward, do not call the images final, and do not batch
  remaining slides from a pretty-but-unverified proof.
- Back-facing, tiny, hidden, or partial faces can support a shot ladder, but
  they cannot prove identity. At least one early proof must show clear enough
  Aachu/Zuv face, hair, body proportion, wardrobe, and posture evidence for a
  meaningful identity review.

AACHU (woman)
- Aachu is 5'6".
- Warm medium-brown South Asian skin.
- Large expressive dark eyes; softly arched brows; delicate nose; natural lips.
- Youthful oval face; soft cheek structure.
- Long dark wavy hair: may be loose, half-tied, or in a casual ponytail. Thickness, dark color, natural waves, and face-framing strands stay consistent across slides.
- Playful warmth, softness, real-person charm. Expressive face; dramatic body language; the spark in the carousel.
- Height: 5'6".
- Signature accessory: her slim evil-eye bracelet belongs on her right wrist,
  grounded in the visible right-wrist bracelet in `aachu/face-04.png`. It is a
  recurring identity feature, not optional decoration. Whenever her right
  wrist or forearm is visible, render the same bracelet in the same position;
  never move it to the left wrist, replace it with a generic bangle, or omit it.

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
- Signature accessory: his small round evil-eye locket on a slim silver chain,
  grounded most clearly in `zuv/portrait-07.jpg`. It is a recurring identity
  feature, not optional decoration. Whenever his neck, open collar, or upper
  chest is visible, render the same centered locket and chain; never replace it
  with a generic pendant, change its design, or omit it.

SIGNATURE ACCESSORY VISIBILITY GATE
- These two signature accessories are always worn in illustrated carousel
  scenes: Zuv's evil-eye locket and Aachu's right-wrist evil-eye bracelet.
- A visible neck/open collar without Zuv's locket is a hard fail. A visible
  Aachu right wrist/forearm without her bracelet is a hard fail.
- Clothing, framing, pose, or physically credible occlusion may hide an
  accessory, but the prompt and QA must record that it is hidden rather than
  redesigning, relocating, or silently dropping it.
- These two worn identity anchors are mandatory. Optional evil-eye symbols in
  backgrounds, props, or decorative motifs remain story-dependent and must not
  be added merely to satisfy this gate.

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
- Zuv's visible neck/open collar is missing or changes the evil-eye locket and silver chain
- Aachu's visible right wrist/forearm is missing, relocates, or changes her evil-eye bracelet

ANTI-DRIFT NOTES (lessons from real rejections)
- 2026-05-31 Private Captions early proofs rejected for face drift and wrong heights. The creator's note: Aachu looks tiny, Zuv looks oversized/generic — reject and regenerate one corrected proof from actual identity references before batching the rest.
- 2026-05-30 phone-prank Slide 03 rejected because Zuv was already wearing pants while copy said "YOUR SOCKS ON BEFORE YOUR PANTS." Scene logic and ON-IMAGE TEXT must match the visible action — identity preservation does not excuse copy-visual contradictions.
- 2026-05-30 phone-prank Slide 08 rejected for crouched/cramped pose. Identity match was acceptable but pose anatomy failed.
- 2026-07-12 The Almosts Were Practicing correction: draft images were allowed
  to continue after no structured face identity eval existed. This is a STOP
  failure. The correct behavior is to stop, mark identity unverified or
  blocked, and repair the identity/eval gate before generating or presenting
  more "final" images.
