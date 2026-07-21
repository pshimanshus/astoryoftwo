# ASTO-021 Deep Spec - Whole-Person Spatial Integrity

## Why This Task Exists

The visual QA system can correctly count people, arms, hands, and fingers while
still missing a whole-body environment failure. The motivating failure is a
doorway proof where Zuv's shoulder, back, and torso appear absorbed into the
door and frame. It is attractive watercolor work, but the body cannot be traced
as a continuous person occupying a believable volume. This task protects against
the AI-image failure where a figure and background object share one impossible
silhouette.

## Starting Fixture

Fixture direction: **regression**. The protected current implementation is
expected to reject the seeded failure, so a single-pass `evals/runner.py review`
records this fixture as `guarded`. That guard result alone cannot award agent
solve credit: an isolated benchmark run must first apply a hidden code mutation
or pre-fix revision that makes the guard fail, then evaluate the agent patch.

The visible fixture at `fixtures/visual-qa.json` contains a `spatial_topology`
check that claims PASS-like package context while its structured records expose
the problem: Zuv's silhouette is not fully traceable, his body region is
observed as touching when it should be in front of the door, the boundary is not
continuous, occlusion order is unclear, the body may intersect a solid object,
and the door edge enters his torso. The fail-to-pass state is that this proof
is rejected by production spatial QA. The pass-to-pass state is a valid shoulder
lean or door-edge occlusion with one declared contact point, clear front/back
order, and visible continuation above and below the occluder.

## Failure Modes

- A body region merges into a wall, door, frame, bed, sofa, table, or chair.
- A silhouette is not traceable from head through torso and limbs.
- A solid object appears to cut into a person without declared occlusion order.
- A valid soft watercolor edge is confused with structural ambiguity.
- The checker accepts correct hand anatomy as sufficient whole-person QA.

## Checker Design

The deterministic checker is `whole_person_spatial_integrity_fixture`. It
materializes the visible fixture and invokes `validate_spatial_topology_check`,
the same production validator used by fail-closed visual QA. Fail-to-pass flips
when the seeded Zuv-door morph emits concrete spatial blockers. Pass-to-pass
coverage comes from production tests for valid single-point shoulder contact and
valid explicit occlusion. A hidden variant should change the body region,
person, object type, and camera angle so the task cannot be gamed by matching
the words `Zuv` or `door`.

## Anti-Gaming

Do not accept a generic "spatial pass" checkbox. The checker requires per-slide
records, people inventories, environment planes, body-region contracts,
expected and observed relations, continuous-boundary evidence, clear occlusion
order, and explicit unresolved-intersection lists. Blocking every occlusion is
also wrong: valid controls must pass when the person remains reconstructable and
the contact or occlusion is explained.

## Severity Model

Critical: a whole person merges into a solid object, proof/final approval
continues after unresolved topology, or the validator is replaced with a broad
beauty/style score. Major: the failure is blocked but evidence does not name the
person, body region, object, and expected relationship. Minor: wording is
awkward while the structured blocker is enforceable.
