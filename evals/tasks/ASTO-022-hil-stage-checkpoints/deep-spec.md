# ASTO-022 Deep Spec - Hash-Bound Human Checkpoints

## Why This Task Exists

A maker-verifier loop can improve artifacts, but it cannot replace the creator.
The dangerous failure is a workflow that treats a passing automated review as
permission to advance, or keeps using an approval after the approved concept,
copy, or image has changed. That creates invisible drift: the creator sees one
candidate while downstream production uses another. The final boundary is even
more sensitive because approval to show a publish-ready package must never be
confused with an instruction to execute publishing.

## Starting Fixture

Fixture direction: **regression**

The regression fixture contains an approval ledger claiming that the creator
approved the concept. Its artifact fingerprint is deliberately stale. The
package can therefore resemble a previously approved workflow while the current
concept files, including missing or changed files, produce a different
fingerprint. The checker asks the production HIL router whether concept approval
is valid, which stage should run next, and whether copy remains locked behind
`creator_concept_approval_required`.

## Failure Modes

The critical fail-to-pass cases are accepting a stale hash, accepting a record
without explicit-creator provenance, skipping directly to copy, or treating a
verifier PASS as creator approval. Other failures include failing to invalidate
copy, image, and publish approvals after concept revision; recording a decision
against a candidate that changed after verification; letting a maker edit
already approved upstream material; and automatically publishing after the
final checkpoint. A loop that merely reaches its iteration cap also fails if it
presents unresolved work as clean.

## Checker Design

The deterministic checker imports the production checkpoint functions rather
than duplicating their logic. It materializes the fixture, evaluates
`approval_valid` for concept, evaluates `next_unapproved_stage`, and runs the
copy-stage verifier. Passing requires all three observations: the stale approval
is false, the earliest stage is concept, and copy contains the explicit prior
approval blocker. Unit tests separately cover a clean stage stopping for HIL,
REVISE reopening the stage, hash mutation invalidating approval, and upstream
reapproval deleting downstream locks.

## Anti-Gaming

The checker must not search for one literal fingerprint or special-case
ASTO-022. Hidden variants alter which stage is stale, which required artifact
changes, whether the provenance field is missing, and whether mutation happens
before or after candidate presentation. Other hidden variants use valid current
approvals as pass-to-pass controls. A robust implementation computes hashes from
the governed artifact set, validates explicit creator provenance, rechecks at
decision time, and walks stages in order.

## Severity Model

Accepting a stale, fabricated, or verifier-inferred approval is critical because
it breaks the human control boundary. Starting a downstream maker before its
prior creator lock is also critical. Failing to invalidate downstream approvals
after upstream change is critical. Weak diagnostics or unclear repair guidance
are major when the gate still blocks safely. Cosmetic differences in trace
wording are minor. Pass-to-pass behavior requires a current explicit creator
approval to remain valid while—and only while—the exact stage artifacts remain
unchanged. The final publish decision may produce `APPROVED_TO_PUBLISH`, but no
publication side effect is permitted.
