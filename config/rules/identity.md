IDENTITY — Aachu (Anchal, the woman) and Zuv (Himanshu, the man) are the same recurring people across the carousel. Individual slides may show Aachu, Zuv, both, partial presence, object-only evidence, or no faces when the shot ladder requires it. Identity preservation is the highest creative priority, above decorative style.

HIERARCHY
- Selected actual Aachu/Zuv identity images control faces, expressions,
  posture, body proportions, and wardrobe anchors — always.
- The active style profile and its Cinematic Observational Watercolor v1 board
  control illustration finish, paper, palette, line quality, and cinematic
  composition — never the faces. Resolve them through
  `config/carousel_style_contract.json`; do not select a board ad hoc.
- Shared brief images control mood, composition, story essence, text, hand gesture, and objects — unless the creator explicitly says otherwise.
- If these three sources conflict, identity wins.

GENERATED CHARTS NEVER REPLACE PHOTOGRAPHS
- Never use a generated character chart alone as the face or identity input for
  Aachu or Zuv. A generated sheet may be a supplemental style, proportion, or
  accessory-continuity aid only after the creator explicitly approves the
  relevant views.
- Every image-generation call with a visible Aachu or Zuv face must attach
  selected actual photographs of that person. A photo contact sheet, photo
  master board, written character bible, prior carousel, or approved generated
  chart does not remove this requirement.
- A creator-approved component does not approve the rest of its sheet. Record
  approval per view. Rejected or unreviewed views remain non-reusable.
- Creator correction, 2026-08-24: in Aachu face turnaround v2, only the large
  neutral front view was recognized as correct. Both three-quarter views, both
  profiles, and the expression row were rejected. The correct front may remain
  a supplemental approved-view aid, but the complete v2 sheet is not an
  approved character model and must never be used as a sole identity source.
- Creator correction, 2026-08-24: the complete Aachu V4 sheet was rejected.
  Its expression row repeated one internally consistent but incorrect synthetic
  face. Internal consistency is not likeness. V4, its profile repair, and its
  prompt are retired and must not be reused or repaired from themselves.

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
- Large expressive dark round-almond eyes; full mostly straight brows with a low soft arch; natural medium-width nose with a rounded tip; compact lips with a fuller lower lip.
- Soft rounded-to-oval face; full cheek structure; softly squared jaw corners; rounded chin.
- Long, dense, very dark hair: mostly straight and smooth with soft natural bends and layered face-framing strands. It may be loose, half-tied, or in a casual ponytail; thickness, dark color, hairline, and soft-bend silhouette stay consistent across slides.
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

CHARACTER MODEL-SHEET GATE
- A "character sheet", "character chart", or "character bible sheet" means a
  technical identity reference, not a decorative couple montage or a set of
  narrative poses.
- The face turnaround must show a large neutral front, left three-quarter,
  right three-quarter, left profile, and right profile. Add a rear or
  over-shoulder hair-silhouette view when hair construction matters.
- Before claiming an angle is unavailable, search every verified private
  identity library already supplied by the creator, not only the small copied
  repository bundle. Copy a role-specific 2–4-photo selection into the repo so
  later generation cannot silently fall back to weak or distant references.
- Front, three-quarter, and true side-profile projection must each be supported
  by an attached actual photograph. Never extrapolate a profile from frontal
  photographs and label the invented geometry accurate. If no true side
  profile exists after searching the verified libraries, stop with
  `BLOCKED_FOR_PROFILE_REFERENCE_PHOTOS`.
- One clear side profile can support forehead/nose/lips/chin projection for the
  opposing turnaround side, but unobserved bilateral asymmetry remains
  provisional. Never claim mirrored ear, piercing, mole, or hairline detail as
  verified.
- A production sheet must include readable written construction notes for face
  envelope, hairline, brows, eyes, nose, lips, jaw/chin, ears, skin tone,
  distinguishing asymmetries, hair, facial hair, body proportions, wardrobe,
  and signature accessories. Technical callouts are explicitly allowed on a
  private character reference sheet when the creator asks for them.
- Build and approve Aachu's and Zuv's solo face turnarounds before the couple
  scale/interaction sheet. A repeated face that is internally consistent but
  does not resemble the real person is still a hard fail.
- Generate and approve one large face view at a time, beginning with neutral
  front. Stop for creator approval after every angle and expression. Do not ask
  one image-generation call to solve a multi-angle or multi-expression sheet.
- Preserve every approved portrait as fixed pixels and assemble the final
  sheet deterministically. Do not use image generation to redraw, harmonize,
  or reinterpret the approved portraits during assembly.
- A creator-rejected generated face must never be used as an identity input or
  as the starting point for a repair. Return to the real photographs and reset.
- A generated sheet with one approved view and other rejected views must be
  treated as partially approved, never promoted as a complete model sheet, and
  never supplied whole as an identity reference.

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
- Aachu and Zuv must look natural, flattering, and physically believable. No
  deep crouched, cramped, squatting, awkwardly folded, broken, or
  unflattering poses. Legs and feet must be proportional and comfortably
  placed.
- A motivated kneeling pose is permitted only when the locked physical action
  requires floor-level work and the scene contract records the knee, foot, and
  floor support, readable adult-scale body proportions, and the actor's exact
  task. It does not permit a deep crouch, compacted limbs, hidden support, or a
  dwarf-like reading. A kneeling exception does not relax any anatomy, entity,
  contact, spatial-topology, or identity failure.

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
- deep crouched, cramped, squatting, awkwardly folded, broken, or unflattering poses
- a kneeling pose without a locked floor action, readable support, and adult-scale body proportions
- distorted hands, extra fingers, broken wrists, warped facial features
- Zuv's visible neck/open collar is missing or changes the evil-eye locket and silver chain
- Aachu's visible right wrist/forearm is missing, relocates, or changes her evil-eye bracelet
- a decorative montage is presented as a character model sheet
- profile projection is invented from frontal photos without a true side-profile photograph
- a creator-rejected generated face is reused as an identity reference
- a generated character chart is used alone without attached actual identity photographs
- a partially approved sheet is treated as fully approved or supplied whole as identity authority
- the creator says either face is wrong, even when mechanical QA passed

ANTI-DRIFT NOTES (lessons from real rejections)
- 2026-05-31 Private Captions early proofs rejected for face drift and wrong heights. The creator's note: Aachu looks tiny, Zuv looks oversized/generic — reject and regenerate one corrected proof from actual identity references before batching the rest.
- 2026-05-30 phone-prank Slide 03 rejected because Zuv was already wearing pants while copy said "YOUR SOCKS ON BEFORE YOUR PANTS." Scene logic and ON-IMAGE TEXT must match the visible action — identity preservation does not excuse copy-visual contradictions.
- 2026-05-30 phone-prank Slide 08 rejected for crouched/cramped pose. Identity match was acceptable but pose anatomy failed.
- 2026-07-12 The Almosts Were Practicing correction: draft images were allowed
  to continue after no structured face identity eval existed. This is a STOP
  failure. The correct behavior is to stop, mark identity unverified or
  blocked, and repair the identity/eval gate before generating or presenting
  more "final" images.
