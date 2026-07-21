# ASTO-020 Deep Spec - Hand-Object Integrity

## Why This Task Exists

Correct text, style, identity, people count, and finger count can all coexist
with obvious AI slop. The rejected examples are an ownerless hand on a door and
a forearm passing through a moving box.

## Starting Fixture

Fixture direction: **regression**. The protected current implementation is
expected to reject the seeded failure, so a single-pass `evals/runner.py review`
records this fixture as `guarded`. That guard result alone cannot award agent
solve credit: an isolated benchmark run must first apply a hidden code mutation
or pre-fix revision that makes the guard fail, then evaluate the agent patch.

The fixture contains two slide records: one unauthorized edge-entry hand and
one correctly counted but physically impossible hand-box intersection.

## Failure Modes

- a visible hand has no owner or story purpose;
- a hand enters from an object or frame edge without an attached limb;
- a wrist or forearm penetrates a solid object;
- overlap order or load-bearing contact is not believable.

## Checker Design

The deterministic checker invokes the production anatomy validator. It passes
only when the validator reports both narrative/ownership failure and physical
contact/intersection failure.

The **fail-to-pass** case deliberately claims overall PASS while its structured
records disclose both defects. The corrected validator must surface the
unnecessary/unowned door hand, its unexplained edge entry, the failed contact
geometry, and the solid-object intersection. Missing fields also fail closed;
an evaluator cannot evade the gate by omitting contact evidence.

The **pass-to-pass** control keeps a legitimate hand visible: it belongs to a
named partner and side, performs the locked focal action, continues through a
credible wrist and forearm, and meets the exterior of its object with sensible
overlap and load direction. Natural partial occlusion remains valid when the
reviewer can explain which surface is in front and where the limb continues.

## Anti-Gaming

The check does not key only on hand count, finger count, the word `door`, or the
word `box`. Hidden cases vary edge, object, occlusion, grip, and load direction.
Each **hidden variant** should change both language and geometry: a hand may
emerge from a sleeve with no arm, a forearm may cross a table plane, fingers may
sit behind an object they supposedly grip, or a load may hang opposite the
support direction. At least one hidden control must include a valid wrist
hidden behind an object edge so the implementation cannot ban all occlusion.

## Severity Model

Any anonymous limb or solid-object intersection is a critical visual failure
that blocks proof approval, final audit, and publishability.

A missing narrative-purpose or contact-evidence field is also critical because
the gate is designed to fail closed. A vague but present evidence sentence is a
major failure when it does not name the relevant limb and surface. Cosmetic
style differences are out of scope and must not influence this task's score.
