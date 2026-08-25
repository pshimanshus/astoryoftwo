# A Story of Two Creative OS

Status: active architecture
Updated: 2026-08-24

## Purpose

Help the creator find a recognizable couple truth, turn it into an image-led
story, and publish a technically valid @a.storyof.two carousel. The system
should increase creative clarity without making the creator supervise internal
agents or read framework reports.

## One Default Route

```text
seed or fresh jam
  -> human concept and format
  -> exact copy plus one physical action per slide
  -> compact generation prompts
  -> riskiest-slide proof
  -> actual-pixel story and integrity QA
  -> creator proof approval
  -> remaining slides
  -> final package QA
```

There are four locks:

1. Concept lock.
2. Copy and format lock.
3. Actual-pixel proof QA plus creator approval.
4. Final package QA.

## Dynamic Depth

The normal route uses no default agent room. Add depth only for a named need:

- Use the Instagram idea loop only when the creator explicitly asks for a deep,
  autonomous, independently challenged idea search.
- Use a bounded critic for one risky visual, identity, anatomy, or final audit.
- Use parallel workers for independent engineering changes with distinct file
  ownership.
- Do not introduce a council, debate, tournament, or scoring ledger merely
  because the task is a carousel.

## Creative Contract

- The model owns the first alive concept, copy, and visual route.
- Context and memory are seasoning, not a visible framework.
- Every slide needs one observable physical event or state change.
- The scene must communicate with copy hidden; copy deepens it.
- Creator-supplied structure and exact copy are preserved.
- A failed visual premise is repaired before polishing likeness or typography.

## Production Contract

Keep these hard gates:

- four selected identity images plus one canonical style board, copied locally
  and shared by prompt handoff and doctor;
- wardrobe and whole-person identity anchored to those images;
- exact integrated on-image text;
- tiny top-right `@a.storyof.two`;
- exact `1080x1440` final post/carousel output by default;
- `1080x1920` Story/Reel and `1080x1080` square only when requested;
- correct people/entities/physics plus actual-pixel story, integrity, identity,
  text, style, and dimension inspection;
- one risky proof and at most two semantic attempts per premise;
- final hashes and manifests only after the complete deck passes.

The prompt still asks for exact 1080x1440. As an observed built-in-runtime
accommodation, only post ingest may bind an untouched exact-3:4 source from
1080x1440 through 1440x1920 and proportionally downsample once. Final remains
exact 1080x1440; crop/pad/stretch/upscale/wrong ratio are blocked. Story/Reel
and square remain exact-only, and approved normalized proof bytes are reused.

Codex owns image-generation calls and actual decoded-pixel inspection. The repo
owns prompt preparation, exact-output ingestion, QA/approval binding, state,
and atomic promotion. There is no repo API renderer, API-key flow, OCR fallback,
or environment capability artifact.

New calls attach those four identity files plus one style board. Five is the
observed built-in-runtime boundary, not an official limit; never drop identity.

## Small Package

Before proof: `creative-context.json`, `format-contract.json`, `slides.json`,
`prompt-pack.json`, and `.internal/compiled-prompts/`. After proof: one
quarantined proof image and `proof-qa.json`. After the full deck passes: final
native PNGs, `final-images.json`, `visual-qa.json`, and `final-audit.json`.

Deliberation transcripts, agent-room records, approval ledgers, provenance
graphs, raw model responses, and prose-only storyboard certifications are not
package artifacts.

## Prompt Contract

One compiled prompt is at most 8,000 characters and 900 words. Its scene is at
most 180 words and its combined essential negatives are at most 80 words. It
contains only the physical scene, camera/focal hierarchy, actual reference
roles, wardrobe, compact house style, exact text, brandmark, dimensions, and
essential entity/anatomy/spatial constraints. Workflow lifecycle and hashes
belong in validators.

## Honest State

A quarantined proof that fails the cold pixel read is `proof_failed` and its
next action is `repair_visual_premise`. It is never `handoff_ready`. Public final
folders and `final-images.json` are written only after all requested slides and
formats pass actual-pixel QA.

New packages use compact v3 state with slide-semantic fingerprints. A local
slide edit invalidates only that slide; a proof edit also revokes approval;
shared identity/style/compiler/brand/format/order changes invalidate the deck.
An approved proof is reused, not regenerated. Archived v2 packages remain
read-only and are never migrated during an ordinary run.

The public state vocabulary is: `draft`, `blocked`, `handoff_ready`,
`proof_qa_required`, `proof_failed`,
`awaiting_creator_proof_approval`, `batch_ready`, `final_qa_required`,
`final_qa_failed`, and `publish_ready`.

## Source of Truth

Canonical rules stay in `config/rules/`; routing stays in
`config/skill-systems.json`; compact execution lives in the carousel runtime
and autopilot skill docs. Generated output and old plans are not rule authority.
