# A Story of Two Creative OS

Status: active architecture
Updated: 2026-09-04

## Product Outcome

Help the creator turn a recognizable couple truth into a technically valid,
image-led @a.storyof.two carousel without supervising internal machinery. A
correction should improve the current deck now and remain useful to later work.

## Default Route

```text
seed or fresh jam -> concept and format -> exact copy + physical actions
-> risky-slide proof -> pixel QA + creator approval -> remaining slides
-> final package QA
```

There are four locks:

1. Concept lock.
2. Copy and requested-format lock.
3. Actual-pixel proof QA plus creator approval.
4. Final package QA.

No internal check, feedback capture, learning event, evaluation, or health run
creates a fifth creator-facing lock.

## Creative Contract

- Codex owns the first alive concept, copy, and visual route.
- Context and memory are quiet seasoning, not a visible framework.
- Every slide has one observable physical event or changed state.
- The scene communicates with copy hidden; exact copy deepens it.
- A failed premise is repaired before likeness or typography polish.
- Use a specialist or parallel worker only for a bounded, non-overlapping job.

## Feedback Becomes Better Work

When the creator corrects a concept, slide, image, or package:

1. preserve the exact correction in the existing creator-correction record;
2. emit one idempotent `LearningEvent` through the existing learning surface;
3. diagnose the affected authoritative slide or prompt fields;
4. repair those fields and let v3 fingerprint reconciliation invalidate only
   affected candidates, QA, or approval;
5. resume the same four-lock production route; and
6. index the evidence during maintenance so future recall can retrieve it.

Every explicit correction is captured; the creator does not operate a feedback
form. The existing correction file carries an internal lifecycle:
captured → diagnosed → applied → evaluated → learning_proposed → approved →
promoted, or rejected. It is not another carousel approval gate. `feedback`,
`revise`, and `feedback-status` connect real repair evidence and regression cases.
Durable rule, skill, or semantic-memory changes remain creator-reviewed proposals.
Optional DeepEval and Langfuse adapters have no authority over deterministic
production gates; local work remains usable without either dependency.

## Production Contract

- Bind exactly four selected identity files plus one canonical style board.
- Anchor face, hair, height, proportions, posture, expression, and wardrobe.
- Integrate exact text and tiny top-right `@a.storyof.two`.
- Default only to 1080x1440; 1080x1920 and 1080x1080 are explicit-request-only.
- Inspect actual pixels for story, entities, anatomy/spatial integrity, identity,
  text, style, brandmark, and dimensions.
- Prove one risky slide; allow at most two semantic attempts per premise.
- Promote finals atomically only after every requested native asset passes.

The prompt requests the exact locked size. Only post ingest may bind an untouched
exact-3:4 source from 1080x1440 through 1440x1920 and proportionally downsample
once. Crop, pad, stretch, upscale, wrong ratio, and a second resample are blocked.

## Codex-Owned ImageGen Boundary

The repo prepares prompts, binds references, ingests outputs, reconciles state,
and promotes files. Codex reads each selected compiled prompt, attaches the four
identity files and one style board, calls ImageGen, then inspects the decoded
candidate with `view_image`. If either capability is unavailable, remain
`handoff_ready` and report `BLOCKED/NOT_RUN`; never infer a visual PASS.

The internal illustration loop is exactly six commands: create with
`--prepare-proof`; ingest proof; review proof; approve (which prepares the
batch); ingest batch; review final (which finalizes a passing deck). `status` is
diagnostic. Automatic correction capture and targeted repair are exception
handling around these six commands, not additional steps on an ordinary run.

## Package and State

Before proof: `creative-context.json`, `format-contract.json`, `slides.json`,
`prompt-pack.json`, `generation-state.json`, and compiled prompts. After proof:
one quarantined image and `proof-qa.json`. After final QA: native PNGs,
`final-images.json`, `visual-qa.json`, and `final-audit.json`.

The public states are `draft`, `blocked`, `handoff_ready`, `proof_qa_required`,
`proof_failed`, `awaiting_creator_proof_approval`, `batch_ready`,
`final_qa_required`, `final_qa_failed`, and `publish_ready`.

Learning proposals, shadow evals, tests, and health stay outside the ordinary
illustration hot path. The lightweight feedback regression runs when repairing
a correction; retrieval rebuilds its derived index when needed. Archived v2
packages remain read-only during normal work. The explicit metadata migration
preserves full historical sources and media hashes without inventing pixel QA.

## Acceptance and Non-Goals

The technical contract is `docs/superpowers/specs/agentic-os-control-plane.md`.
Acceptance requires exact feedback retention, idempotent capture, a reproduced
failure that passes after same-package repair, preservation of untouched JSON,
scoped invalidation, receipt-bound QA, supersession-aware recall, guarded durable
promotion, and a hash-proven historical migration. Synthetic lifecycle tests do
not certify illustration taste or likeness. Optional judges remain uncalibrated
until 20 distinct creator-reviewed outputs across five packages have at most
10% hard-fail disagreement; calibration alone does not authorize production use.

This system improves repository context, examples, retrieval, and tested behavior.
It does not continuously train OpenAI model weights, silently publish content,
invent creator approvals, or regenerate historical art during a migration.

## Source of Truth

Canonical rules stay in `config/rules/`; routing stays in
`config/skill-systems.json`; the compact runtime and autopilot define execution.
Generated outputs, old packages, and historical plans are not rule authority.
