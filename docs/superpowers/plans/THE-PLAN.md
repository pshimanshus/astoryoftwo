# The Plan

Updated: 2026-08-24
Status: v3 hot path implemented; validate and use

## Now

1. Run `make carousel` from a creator seed plus a locked creative brief. A
   story-only request stays `draft` and spends no generation call.
2. Lock only the concept, exact copy, and requested canvas.
3. Describe one observable physical action per slide.
4. Compile prompts under the enforced budgets.
5. Codex attaches four identity files plus one style board, generates the risky
   proof, and ingests it. Five is an observed runtime boundary, not an official
   limit. Prompt exact 1080x1440; post ingest may bind exact-3:4 through
   1440x1920 and downsample once—never crop/pad/stretch/upscale/change ratio.
6. Inspect the actual pixels in this order: story action, relationship state,
   entity/anatomy/spatial integrity, identity, then text/style/dimensions.
7. If the story read fails, repair that slide's visual premise. Stop after two
   semantic attempts and return to concept/visual direction.
8. After hash-bound QA and approval, reuse normalized proof bytes and generate
   only remaining slides.
9. Audit hidden candidates and atomically promote only a complete native deck.

If a story-only command has exact copy but no observable scene, package it but
block proof with `define_physical_actions`; never send a “Draft needed” scene to
image generation.

## When to Expand

Use the explicit Instagram idea loop for a deep independent concept search.
Use a bounded specialist only when one concrete risk needs independent review.
Parallel engineering work must have separate file ownership. No continuous
creative room belongs in the default path.

## Never Reintroduce

- mandatory agent councils or debate transcripts;
- numeric taste/story thresholds as production blockers;
- prose Event A as evidence that generated pixels communicate;
- duplicated approval, run, stage, or provenance ledgers;
- lifecycle/state essays inside image prompts;
- production commands that run the whole test suite before doing work;
- final manifests for incomplete or quarantined images;
- automatic Story/Reel or square companions.
- API renderers, API-key ceremony, OCR fallback, or environment capability
  claims for the Codex-owned generation and visual-inspection boundary.

## Public States
`draft`, `blocked`, `handoff_ready`, `proof_qa_required`, `proof_failed`,
`awaiting_creator_proof_approval`, `batch_ready`, `final_qa_required`,
`final_qa_failed`, `publish_ready`.

## Verification
The change is complete when focused tests, package fixture, Agentic OS health,
wiki health, and the safe closeout gate pass on the isolated branch.
