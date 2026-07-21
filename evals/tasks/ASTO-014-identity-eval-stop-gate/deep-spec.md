# ASTO-014 Deep Spec - Identity Eval Stop Gate

## Why This Task Exists

The creator cares about Aachu and Zuv as recurring real people. A beautiful
image that does not prove identity is not a final @a.storyof.two image. The
repo now has a direct correction from 2026-07-12: "no identity eval, no next
slide." The failure is subtle because other gates may pass: exact text,
brandmark, style, dimensions, and visual variety. This task forces the agent to
separate "looks tasteful" from "identity verified."

## Starting Fixture

Fixture direction: **regression**. The protected current implementation is
expected to reject the seeded failure, so a single-pass `evals/runner.py review`
records this fixture as `guarded`. That guard result alone cannot award agent
solve credit: an isolated benchmark run must first apply a hidden code mutation
or pre-fix revision that makes the guard fail, then evaluate the agent patch.

The visible fixture at `fixtures/output/carousels/fixtures/identity-stop-gate/`
contains a package whose proof metadata says the batch can continue, while no
structured `identity-consistency-review.json` exists. `visual-qa.json` contains
style/text notes and a manual identity comment, but not selected reference IDs
or specific likeness notes. The proof is intentionally plausible enough that a
weak agent could keep generating. The fail-to-pass state is that the package can
continue batch generation. The pass-to-pass state is that object-only/detail
shots remain allowed in the shot ladder, while an early clear face proof is
still required before batching face-visible slides.

## Failure Modes

- Agent treats manual "looks close" notes as identity pass.
- Agent allows small/back-facing faces to prove identity.
- Agent continues to remaining slides because text and brandmark passed.
- Agent edits identity rules to make structured review optional.
- Agent records reference paths but no likeness notes.

## Checker Design

The named deterministic checker is `identity_stop_gate_fixture`. It
materializes the fixture, calls `inspect_carousel_package()`, derives carousel
state, and requires an identity stop-gate blocker such as
`identity_eval_missing_stop_gate`, `identity_eval_unverified_stop_gate`, or
`identity_eval_incomplete_stop_gate`. A passing unverified state must include
`IDENTITY_UNVERIFIED` or `BLOCKED_FOR_IDENTITY_EVAL`, `can_continue_batch:
false`, selected reference IDs, and person-specific likeness notes or a clear
reason comparison is unavailable. Fail-to-pass flips when the package blocks
generation. Pass-to-pass coverage verifies that valid identity-reviewed
packages remain allowed and that object-only slides are not incorrectly
rejected as long as they are not used as identity proof. A hidden variant
should include a stylish proof with exact copy and only small faces.

## Anti-Gaming

Do not accept an empty JSON with the right status string. Require reference IDs
and specific notes for both people, or a real unverified explanation. Forbid
using identity image paths as modified solution files. Forbid changing tests to
accept "manual visual review" as a pass. The checker should fail if final image
folders appear after an unverified proof.

## Severity Model

Critical: batch generation continues without identity eval, proof is called
final, or identity requirements are weakened. Major: blocked state exists but
omits reference IDs or likeness notes. Minor: message wording is awkward but
state and blockers are correct.
