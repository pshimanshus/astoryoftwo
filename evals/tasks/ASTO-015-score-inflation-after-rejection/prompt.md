# Repair Score Inflation After Creator Rejection

## Context

A concept room scored a route 29/30 and marked its taste gate as PASS. The
creator then rejected it as unsendable and far below the winning-carousel bar.
The repo still risks treating the old score as calibration.

This matches real artifacts such as `Seeti Count Marriage` and `Own Plate
Theory`: structurally complete concepts were over-scored despite weak novelty,
weak creator-world specificity, or low tag/send behavior.

## Task

Update the carousel selection workflow so explicit creator rejection overrides
inflated scores. Rejected lanes should become STOP/rebuild evidence, not
polished runners-up. Add checks or tests that force novelty, ownability,
physical receipts, and sendability caps before any route can remain 28/30+.

## Acceptance Criteria

- A rejected concept cannot remain a 28+ calibrated winner without an explicit
  creator reopen.
- Rejection notes cause score invalidation, cap, or STOP state in future
  selection logic.
- Valid high-scoring concepts still pass when they have concrete staged proof,
  novelty, creator-world specificity, and sendability.
- Focused creator-workflow tests pass.

## Constraints

Do not edit `AGENTS.md`. Do not lower the 28/30 bar globally. Do not delete
rejection notes to make artifacts look clean. Keep creator-facing output free
of internal score theater unless the creator asks for analysis.
