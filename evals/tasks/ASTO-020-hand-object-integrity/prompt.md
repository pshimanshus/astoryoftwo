# Task: Stop hand-object AI slop

## Context

Two rejected illustrations passed superficial review. In one, an anonymous
hand entered from the door edge beside Zuv even though the locked scene needed
only Aachu offering a tissue and Zuv showing his injured thumb. In the other,
the number of hands looked plausible, but Zuv's forearm passed through the
solid wall of a moving box. Correct text, style, people count, and finger count
did not prevent either visible failure.

## Task

Repair the image-production contract and structured visual-QA validator so a
carousel cannot pass when a hand has no owner or story purpose, enters from a
door/frame/object edge without an attached limb, or intersects a solid object.
Add deterministic production tests for both rejected patterns and a valid
partial-occlusion control.

## Acceptance Criteria

Every visible hand records owner, side, narrative necessity, wrist/forearm
attachment, contacted object, contact geometry, occlusion evidence, solid-object
intersection status, and unexplained-edge-entry status. Both seeded failures
must be rejected. A valid owned hand with believable partial occlusion and
object contact must continue to pass.

## Constraints

Do not solve this with negative prompt wording alone, a holistic beauty score,
or finger counting. Do not reject valid hands merely because part of the limb
is naturally occluded. Do not weaken existing identity, text, dimensions,
scene-entity, or independent-review gates. Do not edit `AGENTS.md`.
