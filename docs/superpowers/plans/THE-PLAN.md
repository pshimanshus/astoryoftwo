# The Plan

Updated: 2026-09-04
Status: feedback-aware v3 hot path; implement, validate, and use

## Outcome

One creator correction repairs the current carousel through existing v3 state,
is captured once as learning evidence, and becomes recallable later without a
parallel ledger, mandatory dependency stack, or creator gate. Completion means
working commands and tested transitions, not an empty document or prompt handoff.

## Ordered Work

1. Reuse `creator-correction.json` for exact creator corrections and the
   existing `LearningEvent` contract for idempotent evidence capture.
2. Capture each explicit correction automatically with `carousel feedback`.
   Preserve exact words, scope, diagnosis, desired behavior, must-change and
   must-preserve constraints, affected artifacts, and its executable eval ID.
3. Repair authoritative `slides.json` and prompt inputs in place. Reconcile
   existing semantic fingerprints so only affected candidates, QA, or approval
   are invalidated. `carousel revise --feedback-id` executes declared JSON
   replacements or validates already-applied edits, records before/after hashes,
   and evaluates the repair. `feedback-status` exposes unresolved work.
4. Preserve exactly four locks: concept; copy + format; proof pixels + creator
   approval; final package QA.
5. Use the existing six-command illustration loop:

```text
create --prepare-proof -> ingest proof -> review proof
-> approve (prepare batch) -> ingest batch -> review final (finalize)
```

6. At each handoff, Codex reads the compiled prompt, attaches exactly four
   identity files and one style board, calls ImageGen, ingests the result, and
   inspects decoded pixels with `view_image`.
7. Persist attempt receipts inside existing `generation-state.json`: boundary,
   available model identity, compiled prompt hash, five reference hashes, raw
   returned source hashes/dimensions/time, feedback ID, QA binding, approval,
   and final promotion. Missing proof is never synthesized from filenames.
8. Rebuild the event-level lexical index automatically during search/recall;
   scope and recency improve ranking and superseded corrections are excluded.
9. Turn an explicit always/never correction or a repeated independent-package
   failure into a complete inactive diff against the existing canonical file.
   Creator approval is required before applying that diff; package repair does
   not wait for durable-policy approval.
10. Keep DeepEval optional, score-only, and `not_run` without credentials. Keep
    Langfuse disabled by default, strictly redacted, and nonblocking. No Mem0
    service or parallel memory authority is introduced.
11. Backfill August 7–September 4 legacy corrections only, preserving exact raw
    source payloads and every media hash. Never waive a live v3 correction.
12. Run regression, receipt-tampering, adapter, migration, docs, CLI, and full
    repository tests; then evaluate health and scoped publishing safety.

## Reuse Map

- Current intent and accepted locks: `creative-context.json`.
- Exact creator correction: `creator-correction.json`.
- Slide truth and repair: `slides.json` plus `prompt-pack.json`.
- Invalidation/resume: v3 fingerprints and `generation-state.json`.
- Proof/final evidence: existing QA files and asset hashes.
- Durable evidence: existing `LearningEvent`, memory index, search, and recall.
- Durable policy: reviewed proposals into current rule/skill/memory surfaces.

The feedback lifecycle is metadata inside the existing correction file, not a
carousel state machine or fifth lock. Do not add duplicate ledgers, automatic
format derivatives, an API renderer, or required external services.

## Verification and Closeout

The illustration style rollout is implemented through the existing path:
one active profile in `config/carousel_style_contract.json`, canonical
`slides.json` direction, immutable `prompt-pack.json` v3 snapshots, and the
existing proof/final QA. Historical prompt-pack/v2 packages remain read-only,
including when their generation state already uses v3. The detailed rollout
record is `2026-09-04-cinematic-observational-watercolor-production-lock.md`;
it is implementation history, not another rule authority.

Focused workflow, CLI, docs-contract, state-reconciliation, learning-idempotency,
and recall tests must pass. Then run Agentic OS health, wiki health, and the safe
scoped closeout gate without staging unrelated worktree changes.

Public states remain `draft`, `blocked`, `handoff_ready`, `proof_qa_required`,
`proof_failed`, `awaiting_creator_proof_approval`, `batch_ready`,
`final_qa_required`, `final_qa_failed`, and `publish_ready`.
