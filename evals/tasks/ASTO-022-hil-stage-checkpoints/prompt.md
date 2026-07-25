# Enforce Hash-Bound Human Checkpoints

## Context

The carousel workflow needs four separate maker-verifier loops: concept, copy,
images, and publish readiness. Each loop may repair its own artifacts until its
verifier is clean, but a clean verifier is not creator approval. The verified
candidate must be shown to the creator for an explicit APPROVE, REVISE, or
REJECT decision before the next stage can start. A prior approval must become
invalid whenever any governed artifact changes.

## Task

Implement and preserve a fail-closed HIL checkpoint ledger that binds each
creator decision to the exact fingerprint of the verified stage artifacts.
Route every run to the earliest stage without a current approval. Re-run the
stage verifier when the decision is recorded so a candidate cannot change
between verification and approval.

## Acceptance Criteria

- A stale concept approval cannot unlock copy.
- A current explicit approval is accepted before mutation and rejected after
  any governed artifact changes.
- Agent-authored or provenance-free approvals are invalid.
- Revising an upstream stage invalidates every downstream approval.
- Every stage stops and presents only a clean candidate to the creator.
- Final publish approval records permission but does not call a publisher.
- Focused loop and eval-runner tests pass.

## Constraints

Do not edit `AGENTS.md`. Do not fabricate creator decisions or audit evidence.
Do not publish, push, or generate final media. Preserve existing visual,
identity, copy, dimension, and closeout gates instead of weakening them.
