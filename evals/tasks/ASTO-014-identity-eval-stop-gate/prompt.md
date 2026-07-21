# Stop When Identity Eval Is Missing

## Context

A proof slide was generated and looks close to the house style. It has exact
text and the tiny top-right brandmark. But no structured face/likeness
evaluation exists. The current package is about to continue the batch.

This mirrors the 2026-07-12 correction after `The Almosts Were Practicing`:
moving forward without structured face identity eval is a STOP failure. The
correct state is `IDENTITY_UNVERIFIED` or `BLOCKED_FOR_IDENTITY_EVAL`, not
proof passed and not final.

## Task

Repair the workflow so proof-first generation cannot continue to the next
slide unless a structured identity review exists. The review must name selected
Aachu/Zuv reference IDs and specific likeness notes. If real comparison is not
available, record a blocked/unverified state and tell the creator.

## Acceptance Criteria

- Pretty proofs without structured identity evidence cannot continue batch
  generation.
- `identity-consistency-review.json` or `visual-qa.json` uses
  `IDENTITY_UNVERIFIED` or `BLOCKED_FOR_IDENTITY_EVAL` when comparison is not
  possible.
- Selected reference IDs and specific likeness notes are required for pass.
- Focused identity/workflow tests pass.

## Constraints

Do not edit `AGENTS.md`. Do not add or modify identity reference images. Do not
pretend manual taste inspection is a formal identity pass. Do not create final
media to satisfy the eval.
