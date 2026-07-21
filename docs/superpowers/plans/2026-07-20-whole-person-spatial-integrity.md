# Whole-Person Spatial Integrity Plan

Date: 2026-07-20

Status: proposed implementation plan

Trigger: creator rejection of slide 08 because Zuv's shoulder, back, and torso
are morphed into the door/doorframe.

## Correction To The Diagnosis

The main defect is not only hand anatomy. Zuv does not occupy a coherent human
volume in front of the doorway. The dark door plane, frame edge, shoulder,
upper back, side of the torso, and shirt merge into one unresolved mass. The
architecture appears to enter or absorb his body. His silhouette cannot be
traced cleanly, and the image never establishes whether he is in front of the
door, behind it, leaning on its frame, or embedded inside it.

This is a **whole-person spatial-topology failure**. The earlier hand-focused
gate was necessary but insufficient.

The image model cannot be guaranteed never to generate this mistake. The
production system can and must guarantee that an image with this mistake never
passes quarantine, reaches creator proof, continues a batch, or is called
fixed/final.

## Goal

Make every generated person occupy a coherent, inspectable volume relative to
doors, walls, furniture, boxes, floors, clothing and other solid objects.
Reject any frame in which a body region is absorbed by, penetrates, or has an
unresolved depth relationship with the environment.

## Done When

- Every person–object relationship is declared before generation.
- Every rendered body silhouette and environmental boundary is inspected
  after generation.
- Ambiguous depth or occlusion fails closed; reviewers cannot use “probably
  behind the door” as a pass.
- The rejected Zuv-inside-door fixture fails deterministically.
- Valid partial occlusion and a valid shoulder leaning against a doorframe
  continue to pass.
- Failed candidates remain quarantined and invisible to the creator-facing
  proof flow.

## Phase 1 — Canonical Rule: Person–Environment Topology

Extend `config/rules/scene-entity-integrity.md` from limb ownership to complete
body/environment integrity.

For each visible person, require:

- a traceable silhouette for head, neck, shoulders, torso and every visible
  limb;
- a declared depth position relative to each nearby solid object;
- explicit permitted contact points, such as `left shoulder touches doorframe`;
- explicit forbidden intersections;
- a coherent floor/support relationship when feet or seated weight are shown;
- continuous clothing/body boundaries that do not dissolve into architecture;
- an explainable occlusion order wherever an object hides part of the body.

Hard failures must include:

- door, wall, furniture or object boundary running through a torso or head;
- body mass sharing the same unresolved painted region as a solid object;
- shoulder/back disappearing into a door without a single clear contact plane;
- architecture changing direction or thickness to accommodate the body;
- missing body volume hidden by an object when the occlusion cannot be
  anatomically reconstructed;
- ambiguous `in front of` versus `behind` versus `inside` relationships;
- person/object colors or linework merging so completely that the silhouette
  cannot be traced.

## Phase 2 — Pre-Generation Spatial Topology Contract

Add a `spatial_topology` contract to
`pipeline/stages/carousel_visual_integrity.py` and inject it through
`pipeline/stages/carousel_prompt_compiler.py`.

Each contract must declare:

```json
{
  "person": "Zuv",
  "body_regions_visible": ["head", "neck", "shoulders", "torso", "left forearm", "left hand"],
  "environment_planes": [
    {"object": "door leaf", "depth": "behind Zuv"},
    {"object": "doorframe", "depth": "behind and to Zuv's right"},
    {"object": "doorway opening", "depth": "behind both people"}
  ],
  "allowed_contacts": [],
  "forbidden_intersections": [
    "door edge through shoulder or torso",
    "shirt or back merged into door surface",
    "doorframe replacing any part of Zuv's silhouette"
  ],
  "required_visible_separation": "A readable contour or value boundary separates Zuv's entire shoulder/back/torso from the door."
}
```

For this exact slide, the locked blocking must say:

- Zuv stands fully in front of the door and frame.
- The door leaf is a separate plane behind him.
- No door or frame line touches, crosses, replaces or absorbs his head,
  shoulder, back or torso.
- His non-focal arm stays completely outside the frame.
- Only Aachu's tissue-offering hand and Zuv's injured-thumb hand are visible.

The prompt compiler must render this as a hard spatial instruction, not bury it
inside a generic negative-prompt paragraph.

## Phase 3 — Post-Generation Full-Frame Geometry Audit

Add a required `spatial_topology` check to schema-v2 visual QA in
`pipeline/stages/carousel_quality.py` and mirror it in
`pipeline/stages/codex_builtin_image_generation.py`.

The audit order is mandatory:

1. **Whole-frame silhouette pass:** trace every person's exterior boundary
   before inspecting faces, hands, typography or style.
2. **Environment-plane pass:** trace doors, walls, furniture, containers,
   floor and other solid boundaries.
3. **Pairwise topology pass:** for every nearby person/object pair, record
   `in_front_of`, `behind`, `touching`, `inside`, or `ambiguous`.
4. **Contact pass:** inspect every intended touch point and confirm that only
   the declared body region contacts the declared surface.
5. **Occlusion pass:** name the front surface, hidden body region and visible
   continuation. If any one cannot be named, fail.
6. **Local anatomy pass:** inspect hands, fingers, wrists and object contact.
7. **Identity/text/style pass:** run only after spatial integrity succeeds.

Each per-person QA record must include:

```json
{
  "person": "Zuv",
  "silhouette_traceable": true,
  "body_regions": [
    {
      "region": "right shoulder/back/torso",
      "near_object": "door and doorframe",
      "expected_relation": "in_front_of",
      "observed_relation": "in_front_of",
      "boundary_continuous": true,
      "occlusion_order_clear": true,
      "solid_object_intersection": false,
      "morph_or_merge": false,
      "evidence": "Zuv's shirt contour stays continuous and separate from the door edge from shoulder to waist."
    }
  ],
  "ambiguous_regions": []
}
```

Any `ambiguous`, `solid_object_intersection: true`, `morph_or_merge: true`,
missing region, or untraceable silhouette blocks the image. A prose assertion
without region-level evidence also blocks.

## Phase 4 — Reviewer Separation And Evidence

The anatomy/entity reviewer must become the
`anatomy_entity_spatial_identity` reviewer and inspect the exact hash-bound
image at both full-frame and detail scale.

Require three evidence views:

- full frame for overall depth and body volume;
- person–object crop for boundary and occlusion;
- focal-hand crop for local anatomy/contact.

The same agent that generated or edited the image may not certify spatial
integrity. A second independent visual reviewer must confirm all ambiguous
regions are empty. Disagreement means `REPAIR`, never `PASS_WITH_NOTES`.

## Phase 5 — Quarantine And Retry Behaviour

Update the proof state machine so:

- generated image starts as `GENERATED_QUARANTINED`;
- any spatial-topology failure becomes `REJECTED_SPATIAL_INTEGRITY`;
- a rejected image cannot be copied into proof/final folders;
- it cannot seed the next slide or be described as “fixed”;
- retry prompts carry the exact failed person, body region, object and
  expected relationship;
- after two failed retries, stop as `BLOCKED_VISUAL_QA` and report the
  unresolved geometry plainly.

## Phase 6 — Regression Eval ASTO-021

Create `ASTO-021-whole-person-spatial-integrity` with materialized fixtures.

Fail-to-pass cases:

1. Zuv's shoulder/back/torso morphed into a door and frame.
2. A wall edge crossing through a person's head or hair mass.
3. A chair back passing through a seated torso.
4. Legs disappearing into a bed or sofa with no reconstructable occlusion.
5. A body and background object sharing an unresolved silhouette.
6. Correct hand anatomy but incorrect whole-body/environment topology.

Pass-to-pass controls:

1. Zuv fully in front of the door with a continuous separate silhouette.
2. One shoulder intentionally leaning on the frame at a single declared
   contact point.
3. A torso validly hidden behind a door edge with clear front/back order and
   visible continuation above and below.
4. Watercolor edges remaining soft while structural boundaries stay readable.

The deterministic checker must invoke the same production validator used by
final QA. Hidden variants must change the person, body region, object, camera
angle and type of valid occlusion so the eval cannot be gamed with the words
`Zuv` or `door`.

## Phase 7 — Focused Tests

Add tests covering:

- missing `spatial_topology` fails closed;
- a boolean-only spatial PASS is rejected;
- expected `in_front_of` but observed `ambiguous` fails;
- torso/door intersection fails even when people, arm and hand counts match;
- morph/merge fails even without a literal line crossing the body;
- unexplained occlusion fails;
- a declared single-point shoulder lean passes;
- a valid door-edge occlusion passes;
- stale SHA-256 evidence fails after an image changes;
- generator/QA reviewer identity collision fails independence checks;
- proof promotion is blocked after spatial failure.

Focused command:

```bash
venv/bin/python -m pytest \
  tests/test_fail_closed_visual_qa.py \
  tests/test_fail_closed_proof_states.py \
  tests/test_carousel_prompt_compiler.py \
  tests/test_eval_runner.py -q
```

Then run creator-workflow contracts, Agentic OS health and wiki health.

## Implementation Order

1. Add the canonical whole-person rule and structured schema.
2. Add validator and failing unit tests.
3. Add prompt-level topology contract.
4. Add quarantine/state-machine enforcement.
5. Add ASTO-021 fixture and deterministic checker.
6. Update the slide-08 visual direction and every generation-facing derivative.
7. Regenerate one quarantined slide-08 proof from actual identity references.
8. Run full-frame, boundary-crop and hand-crop independent reviews.
9. Show the creator only if all spatial, anatomy, identity, text and style gates
   pass.

## Required File Surfaces

- `config/rules/scene-entity-integrity.md`
- `.agents/skills/a-story-carousel-jam/SKILL.md`
- `config/skills/carousel-jam-runtime-context.md`
- `config/skills/illustration-carousel-framework.md`
- `pipeline/stages/carousel_visual_integrity.py`
- `pipeline/stages/carousel_prompt_compiler.py`
- `pipeline/stages/carousel_quality.py`
- `pipeline/stages/codex_builtin_image_generation.py`
- proof-state and packaging modules
- focused QA, prompt, state and eval tests
- `evals/tasks/ASTO-021-whole-person-spatial-integrity/`
- durable failure taxonomy and visual-QA memory

## Acceptance Gate For The Replacement Slide

The replacement slide cannot be shown as a proof until all answers are yes:

- Can Zuv's entire head–neck–shoulder–back–torso silhouette be traced?
- Is the door a separate, continuous plane behind him?
- Is every door/frame boundary visible or logically occluded without entering
  his body?
- Are all intended contact points declared and physically believable?
- Are there zero ambiguous, merged or intersecting body regions?
- Are both focal hands anatomically clean and spatially separate from the
  tissue and door?
- Do Aachu and Zuv match the selected identity references and two-inch scale?
- Does the scene still read as anger plus instinctive care with the text hidden?
- Are exact copy, brandmark and locked dimensions correct?

One “no” means reject and regenerate. There is no `PASS_WITH_NOTES` for spatial
integrity.
