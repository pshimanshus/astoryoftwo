VISUAL VARIETY — every @a.storyof.two carousel must break the visual pattern.

CREATOR HARD RULE
- Do not make every slide the same medium two-shot of both people doing the
  same emotional action from the same front/three-quarter angle.
- If the carousel is a montage across time, feeling, or family rhythm rather
  than one continuous real-time scene, every slide must be written and prompted
  as a different setup with different clothes. Identity references anchor the
  people; they do not lock one outfit, one room, or one pose across the deck.
- Do not let a carousel collapse into repeated bed, table, chai, books,
  garden, balcony, or generic listening scenes unless the creator's real story
  specifically requires that repeated place.
- Scene variety is not just changing clothes. The camera, blocking, action,
  setting, prop grammar, and who is visible must change.

SHOT LADDER / VISUAL VARIETY
Before image generation, `slides.json` is the single per-slide authority. Each
slide needs:
- `physical_action`: one observable event with subject, acted-on person/object/
  space, and a visible consequence;
- `camera`: shot size, specific position/viewpoint, and protected copy negative
  space;
- `setting`: a specific sub-location, time or weather state, motivated light,
  and distinct foreground/midground/background jobs;
- who is visible: Aachu, Zuv, both, partial hand/back/shoulder, or no faces;
- `focal_hierarchy`, story-serving props, and continuity facts; and
- `visual_richness`: the point of view, before/after implication, continuation
  pull or final payoff, and two to four observable story-evidence records.

Do not write parallel `visual`, `scene`, `composition`, `pose`, `shot`, or
`background` aliases for new packages. The canonical fields above must feed the
compiler, fingerprints, preflight, and pixel QA directly.

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
- sparse posed portraits where two people stand beside the copy without
  foreground, midground, background, or a visible cause-and-effect receipt;
- decorative clutter that creates detail without advancing the same scene.

VISUAL RICHNESS GATE
- Every planned slide must state whose feeling organizes the frame, what
  visibly happened just before, what likely happens just after, and the visual
  question or payoff that earns its place in the sequence.
- Motivated light must name a believable source, direction, and emotional or
  focal job. “Warm light,” “cinematic lighting,” and “nice lighting” are not
  direction.
- Foreground, midground, and background must each have a distinct spatial or
  narrative job. Empty depth and three restatements of the same subject fail.
- `story_evidence` contains two to four distinct records. Each names a concrete carrier,
  its observable state, and the narrative fact it proves. “Some props,” “lived
  details,” and unrelated decoration fail. Repeated carriers, including case,
  punctuation, or whitespace variations, do not count as additional evidence.
- The focal action must read first with text hidden. Microexpression, gaze,
  distance, contact, displaced objects, wear, condensation, an open door, or an
  aftermath trace may carry the quieter second read.
- Default flags are `posed_portrait_allowed: false` and
  `decorative_clutter_allowed: false`.
- Every generated proof/final must record structured actual-pixel evidence for
  the same plan: foreground/midground/background, focal action, two to four
  story details, before/after implication, motivated light, caught-event read,
  continuation/payoff, `posed_portrait: false`, `decorative_clutter: false`,
  and no unexplained generic-AI tells.
- Richness means layered evidence, not more objects. A clean composition can
  pass when its few details all advance the beat; an ornate static portrait
  fails.

GENERIC / AI-LOOKING PROXIES — repair before generation or reject in pixels
- staged portrait blocking, centered stock symmetry, or both people presenting
  the same camera-ready expression;
- over-soft identityless faces, plastic skin, glossy digital surfaces, or
  uniformly airbrushed textures;
- lighting with no visible source/direction or an ambient golden glow that
  flattens the paper and scene;
- shallow subject cutouts with no coherent foreground, midground, background,
  contact, or spatial consequence;
- decorative prop spam, repeated furniture/plant/mug filler, or pristine rooms
  whose objects prove nothing;
- copied reference text, screenshot residue, layout chrome, or a literal
  collage of reference examples; and
- a frame whose only meaning comes from reading its on-image copy.

EXCEPTIONS
- A single continuous-scene story may intentionally keep the same wardrobe and
  location, but must still vary camera angle, distance, action, and whose
  perspective we see.
- Same wardrobe across slides is allowed only when the creator explicitly locks
  a continuous sequence. Otherwise, repeated clothing makes the carousel read
  as one setup and fails the visual plan.
- A quiet emotional carousel may stay subtle, but subtle does not mean static:
  use hands, doors, backs, objects, distance, partial presence, or negative
  space to change the visual sentence.

QA QUESTION
If all on-image text were hidden, would the carousel still feel like six
different visual beats in one story, or like the same scene with different
captions? If it feels like the same scene, it fails.
