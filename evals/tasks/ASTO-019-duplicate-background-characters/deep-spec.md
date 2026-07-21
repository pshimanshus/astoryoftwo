# ASTO-019 Deep Spec - Duplicate Background Characters

## Why This Task Exists

The creator rejected a polished 3:4 illustration on 2026-07-20 because the
model invented a second couple walking away behind the intended foreground
couple. The extra pair was neither harmless decoration nor a small style flaw:
it created a competing timeline and made the scene look unmistakably
machine-generated. Existing gates were strong on exact text, brandmark,
dimensions, identity, pose, and copy-visual logic, but none required an
instance-level inventory of every visible person. A holistic “looks right”
judgment therefore missed an obvious semantic error.

## Starting Fixture

Fixture direction: **regression**. The protected current implementation is
expected to reject the seeded failure, so a single-pass `evals/runner.py review`
records this fixture as `guarded`. That guard result alone cannot award agent
solve credit: an isolated benchmark run must first apply a hidden code mutation
or pre-fix revision that makes the guard fail, then evaluate the agent patch.

The fixture is a one-slide `visual-qa.json` that claims `PASS`. Its scene
contract expects two people, while the inspection record observes four and
names an unintended background couple beneath the corridor arch. This is
deliberately self-inconsistent so the checker does not need the private source
image. The fail-to-pass condition is that structured QA rejects the mismatch
with a concrete reason. The pass-to-pass control is a record with two expected
and two observed people, no unexpected entities, and real inspection evidence.
An additional valid control may authorize a crowd when the storyboard makes it
part of the scene.

## Failure Modes

- The agent adds “no extra people” to a prompt but leaves QA unchanged.
- The checker trusts `pass: true` without inspecting counts and unexpected
  entities.
- Distant figures, mirrors, silhouettes, portraits, or ghost figures are
  excluded from the count.
- The gate blindly requires two people on every slide and breaks object-only,
  single-person, family-function, or crowd scenes.
- A beauty, CLIP, or VLM alignment score averages away the count error.
- The fixture is recognized only by the literal phrase “background couple.”

## Checker Design

The deterministic checker loads the fixture and passes the embedded
`scene_entity_integrity` structure to the same validator used by final visual
QA. The validator requires one record for every slide, unique slide numbers,
non-negative integer `expected_people` and `observed_people`, an explicit
`unexpected_entities` list, and concrete evidence. Any count mismatch or
non-empty unexpected list is blocking. The checker confirms that the seeded
two-versus-four mismatch and background couple are both present in the failure
reasons. Focused unit tests should exercise missing records, duplicate slide
numbers, thin evidence, extra entities with equal counts, and clean controls.

## Anti-Gaming

A hidden variant must replace the walking pair with a mirror duplicate, a tiny
doorway silhouette, a reflected third person, or a portrait that reads as a
live actor. Another hidden variant should use `expected_people=0` for an
object-only slide. A pass-to-pass crowd case should authorize background roles
instead of forcing a universal two-person rule. String matching alone is not
enough: the validator must compare structured counts and reject every non-empty
unexpected-entity list regardless of wording.

## Severity Model

Critical: final audit can pass with an unauthorized extra person, duplicate
couple, reflection, or silhouette. Major: the gate exists only in docs or
prompt text, inventory is not per-slide, or valid authorized crowds are
blocked. Minor: failure evidence is correct but could name the offending
entity or slide more clearly.
