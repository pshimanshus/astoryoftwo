VISUAL VARIETY — every @a.storyof.two carousel must break the visual pattern.

CREATOR HARD RULE
- Do not make every slide the same medium two-shot of both people doing the
  same emotional action from the same front/three-quarter angle.
- Do not let a carousel collapse into repeated bed, table, chai, books,
  garden, balcony, or generic listening scenes unless the creator's real story
  specifically requires that repeated place.
- Scene variety is not just changing clothes. The camera, blocking, action,
  setting, prop grammar, and who is visible must change.

SHOT LADDER / VISUAL VARIETY
Before image generation, every carousel must include a shot ladder in
`visual-plan-quality.json`, `visual-debate.json`, or the prompt pack. Each
slide needs:
- shot type: wide, medium, close-up, over-shoulder, single-person, object-only,
  detail, reaction, or transition;
- camera angle: front, profile, overhead, low table-level, doorway view,
  reflection, behind/over-shoulder, or distant establishing view;
- setting lane: bedroom, kitchen, street, cafe, balcony, travel, doorway,
  car/ride, bathroom/vanity, terrace, shop, hotel, family-function, or
  object-only paper space;
- primary visible action;
- who is visible: Aachu, Zuv, both, partial hand/back/shoulder, or no faces;
- repeated prop/setting check.

MINIMUM VARIETY GATES
- No same shot type twice in a row unless the sequence is a deliberate
  before/after or action/reaction pair.
- No more than two full-couple medium shots in a 5-6 slide carousel.
- At least one slide should use single-person, over-shoulder, object-only, or
  detail-shot grammar when the story allows it.
- At least three distinct scene/setting lanes are required in a 5-6 slide
  carousel unless the creator has locked a single continuous sequence.
- If the same setting repeats, the camera angle and action must change
  materially.
- Repeated props such as chai, books, notebooks, beds, mugs, plants, phones,
  or garden tables cannot appear as default filler. Use them only when they
  prove the slide's specific story beat.

HARD FAIL — regenerate or repair before generation
- four or more slides use the same front-facing/full-couple medium shot;
- consecutive slides repeat the same angle, same distance, and same emotional
  action;
- every slide shows both partners sitting together and processing feelings;
- the scene set defaults to bed/table/chai/books/garden without story need;
- wardrobe changes but shot grammar and staging remain the same;
- the visual plan says "different scenes" but the generated images still feel
  like the same room/table/pose re-skinned.

EXCEPTIONS
- A single continuous-scene story may intentionally keep the same wardrobe and
  location, but must still vary camera angle, distance, action, and whose
  perspective we see.
- A quiet emotional carousel may stay subtle, but subtle does not mean static:
  use hands, doors, backs, objects, distance, partial presence, or negative
  space to change the visual sentence.

QA QUESTION
If all on-image text were hidden, would the carousel still feel like six
different visual beats in one story, or like the same scene with different
captions? If it feels like the same scene, it fails.
