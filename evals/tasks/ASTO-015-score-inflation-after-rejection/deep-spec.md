# ASTO-015 Deep Spec - Score Inflation After Rejection

## Why This Task Exists

The repo has repeated evidence that agents can satisfy checklists while still
producing weak concepts. `Own Plate Theory` and `Seeti Count Marriage` show the
same pattern: concept artifacts score the route 28-29/30, the creator rejects
it as not sendable or far below the winning carousel bar, and the prior score
becomes dangerous if preserved as positive calibration. This eval ensures the
system learns from rejection rather than defending the rubric.

## Starting Fixture

Fixture direction: **solution**. A single-pass `evals/runner.py review` must
observe the materialized starter as `unresolved`. The task becomes resolved
only after the agent repairs the fixture-backed repository state and the named
checker passes.

The visible fixture at
`fixtures/output/concepts/fixtures/score-inflation-after-rejection/` contains
`concept-selection.json` with `Seeti Count Marriage` marked
`REJECTED_BY_CREATOR` while still scoring 29 and 28.5 with `PASS_NO_CAP` and
positive calibration use. The companion rejection note preserves the creator
correction instead of hiding it. The fail-to-pass state is that the workflow
still treats the route as a winner or future calibration example. The
pass-to-pass state is that a truly fresh, ownable, staged, creator-specific
route can still score above 28.

## Failure Modes

- Agent keeps the numeric score and adds only a note saying "creator disliked."
- Agent lowers all thresholds instead of applying rejection overrides.
- Agent deletes rejection notes or concept artifacts.
- Agent re-presents the rejected lane with polished wording.
- Agent turns taste gates into generic "looks good" prose.

## Checker Design

The named deterministic checker is `score_rejection_fixture`. It inspects
concept-selection records and flags the contradiction of creator-rejected
status plus a 28+ score without STOP, cap, invalidation, or rebuild routing.
The rubric checker should score whether the repair requires observable novelty,
creator-world specificity, dense physical receipts, and a send/save reason.
The hidden variant should use a different rejected lane and different rejection
wording so the checker does not overfit to `Seeti Count Marriage`.
Fail-to-pass flips when creator rejection becomes a hard override.
Pass-to-pass coverage confirms approved high-score artifacts still pass.

## Anti-Gaming

Do not accept changing every rejected route to a low number without explaining
the failure. Require preserved evidence, a state change, and future routing
impact. Forbid hiding creator corrections in archive files the workflow never
reads. The checker should fail if the route can still be selected by title,
slug, or lane keyword after the rejection.

## Severity Model

Critical: rejected route remains selectable, creator correction is deleted, or
inflated scores remain active calibration. Major: score is capped but no
future routing block exists. Minor: rejection summary is imprecise while the
block itself is enforceable.
