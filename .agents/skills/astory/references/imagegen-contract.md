# ImageGen Contract

Codex directly calls the built-in ImageGen tool. Preparing a prompt or handoff
without generating and inspecting the returned pixels is incomplete. Repository
code owns deterministic preparation, ingestion, binding, QA validation, and
atomic promotion; it does not substitute a renderer or external image API.

## Required generation inputs

- Use the exact compiled prompt returned by `scripts/carousel.py prepare`.
- Attach exactly four actual identity images in the named Aachu, Zuv,
  together-face/scale, and together-body/posture roles.
- Attach exactly one hash-bound canonical style board.
- Keep story images as authoring context; they are not extra generation
  attachments at the locked boundary.
- The prompt must include the slide purpose, emotional beat, observable action,
  relationship proof, setting, camera distance, watercolor-and-ink finish,
  palette, lighting, exact quoted copy, native `1080x1440` canvas, and the tiny
  `@a.storyof.two` top-right brandmark.
- A correction edit must include the event's explicit `must_change` and
  `must_preserve` clauses.

## Proof-to-final execution

1. Run `python scripts/carousel.py prepare PACKAGE --proof-slide NUMBER`.
2. Read the returned compiled prompt and attach the five returned reference
   bindings to the ImageGen call.
3. Invoke ImageGen for the selected proof. Record its tool-reported model when
   exposed; do not hardcode a permanent model name.
4. Ingest the fresh return with `python scripts/carousel.py ingest PACKAGE
   --instagram-post PATH [--model MODEL] [--feedback-id ID]`.
5. Open every path returned in `review_targets` and inspect the decoded pixels.
   Write evidence-based QA against those exact hashes, then run `carousel review`.
6. Do not approve a proof unless exact text, identity, brandmark, dimensions,
   scene/action, and relationship proof pass.
7. After creator proof approval, repeat the same direct ImageGen, ingest, and
   pixel-review loop for every remaining selected slide.
8. Finalize only when each selected slide has a returned-source receipt,
   hash-bound passing QA, approval state, and promotion state.

## Failure and repair

- A semantic premise gets at most two generated attempts. After that, rewrite
  the scene/action before asking ImageGen again.
- Wrong text, identity drift, missing brandmark, wrong dimensions, stale
  references, or unbound QA are hard failures even when the image is attractive.
- Never recycle an existing package asset as a fresh ImageGen return.
- Creator corrections must first be captured with `carousel feedback`; apply
  them to the same package with `carousel revise` and link the resulting eval.
