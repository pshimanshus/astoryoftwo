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

The regression fixture contains only a bootstrap approval ledger; it does not
hard-code a bogus hash. The checker programmatically builds the complete
governed concept artifact set, verifies that the concept itself is clean, and
records an explicit creator approval using the current production fingerprint.
It first proves this approval is valid and routes the workflow to copy. It then
changes one governed concept artifact without changing its semantic validity.
The checker asks the production HIL router whether the once-current approval is
now stale, whether routing returns to concept, and whether copy is locked behind
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
than duplicating their logic. It materializes the bootstrap fixture, writes
semantically valid concept artifacts, and obtains the approval hash from
`stage_fingerprint`. Passing first requires a clean concept report,
`approval_valid(concept)=True`, and copy as the next unapproved stage. The
checker then mutates `concept-selection.json`, a real member of the governed
artifact set. Passing after mutation requires `approval_valid(concept)=False`,
concept as the earliest unapproved stage, and the copy verifier to contain the
explicit prior-approval blocker. Unit tests separately cover a clean stage
stopping for HIL, REVISE reopening the stage, hash mutation invalidating
approval, and upstream reapproval deleting downstream locks.

## Anti-Gaming

The checker must not search for one literal fingerprint, accept a prewritten
bogus hash as sufficient evidence, or special-case ASTO-022. Hidden variants
alter which stage is stale, which required artifact changes, whether the
provenance field is missing, and whether mutation happens before or after
candidate presentation. Other hidden variants use valid current approvals as
pass-to-pass controls. A robust implementation computes hashes from the
governed artifact set, validates explicit creator provenance, rechecks at
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
