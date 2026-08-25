# Carousel Hot-Path Repair

Status: v3 repair implemented on `codex/carousel-hot-path-v2`
Updated: 2026-08-24

## Failure That Triggered the Rewrite

The previous workflow spent roughly thirty minutes producing and reviewing a
single proof. Several prose reviewers accepted the planned duvet-cover story,
but the rendered image still did not clearly show the missing corner or failed
insertion. The system optimized written intention, agent agreement, and
artifact completeness before checking whether a cold viewer could understand
the pixels.

The same default path also carried long generator prompts, five mandatory
creative agents, numeric taste gates, Event A provenance, approval ledgers,
stage reviews, duplicated generation/final state, and package artifacts that
the doctor did not consistently require. This increased latency and created
false confidence without preventing the actual failure.

## Repair Implemented

- Replaced the default carousel council with a zero-agent small brief path.
- Reduced the active workflow to four locks.
- Made deep multi-agent idea search explicit-only.
- Replaced prose-first certification with actual-pixel story-first QA.
- Made failed quarantined proofs derive `proof_failed` and
  `repair_visual_premise`.
- Capped compiled prompts at 8,000 characters / 900 words, scenes at 180 words,
  and essential negatives at 80 words.
- Removed repository lifecycle, hashes, provenance, and QA schema prose from
  image prompts.
- Reduced the public package to creative context, format, slides, prompts,
  proof QA, final images, visual QA, and final audit.
- Kept identity attachments, wardrobe anchors, exact text, top-right brandmark,
  native dimensions, quarantine, anatomy/entity/spatial inspection, creator
  approval, slide-local retries, and final hashes.
- Removed production-time test/health preflights from `make carousel`; those
  remain verification and closeout commands.
- Blocked story-only placeholder scenes from entering proof generation; the
  next action is now `define_physical_actions`.
- Consolidated creation, preparation, ingestion, review, approval, status, and
  finalization under `scripts/carousel.py` with versioned JSON responses.
- Made the production boundary explicit: Codex generates and opens decoded
  pixels; repo commands prepare, quarantine, bind QA, approve, and atomically
  promote. Unavailable visual tools remain `handoff_ready`, never PASS.
- Added slide-semantic v3 fingerprints and slide-local invalidation. Shared
  identity/style/compiler/brand/format/order changes invalidate the full deck;
  harmless JSON formatting does not.
- Reused a passed, hash-bound, creator-approved proof as its final candidate
  and removed duplicate inventory from visual QA and final audit.
- New calls bind four curated identity files plus one style contact sheet—five
  is an observed built-in-runtime boundary, not an official limit claim.
- Post ingest may bind an untouched exact-3:4 source through 1440x1920 and
  downsample once to the exact 1080x1440 final; other formats stay exact-only.
- Kept archived v2 packages read-only. No existing carousel was migrated,
  regenerated, inspected, or edited by this repair.

## Acceptance Tests

Acceptance covers four gates/zero default agents, prompt budgets, truthful
failed-proof state, no incomplete final claim, requested formats only, exact
text/identity/brandmark/dimensions/pixel integrity, a minimal fixture, and the
synthetic public lifecycle/benchmark without claiming vision quality.

## Deliberately Removed

The default route writes no agent-room, debate, taste-score, Event A director,
run/stage/approval ledger, raw-response, or wiki-update files.
Historical generated packages are not source truth and are not migrated in
place.

The durable architecture now lives in
`docs/superpowers/plans/creative-os-master-plan.md`; the operational sequence is
in `docs/superpowers/plans/THE-PLAN.md`.
