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
- The canonical reference list stays five. For an edit, attach the separately
  bound target as image 1, then those same five references in their prepared
  order. The target supplies editable pixels, never identity/style authority.
- Keep story images as authoring context; they are not extra generation
  attachments at the locked boundary.
- The prompt must include the slide purpose, emotional beat, observable action,
  relationship proof, setting, camera distance, watercolor-and-ink finish,
  palette, lighting, exact quoted copy, native `1080x1440` canvas, and the tiny
  `@a.storyof.two` top-right brandmark.
- Existing slide fields and feedback supply a correction edit's `must_change`
  and `must_preserve` clauses. Do not create a second scene or copy payload.

## Edit preparation and invocation records

For edits, add `--operation-json PATH` to `prepare`. Its JSON array contains
`{slide, intent, targets}` records; `intent` is `edit` and `targets` maps each
selected format to one source file path. For example:

```json
[{"slide": 2, "intent": "edit", "targets": {"instagram_post": "/absolute/source.png"}}]
```

Preparation validates the full array before mutation and copies targets into
`.internal/references/edit-targets/`. The canonical `slides.json`
`image_operation` holds package-relative path, SHA-256, width, and height for
each format. Missing operation or targetless `generate` keeps generation
behavior. Inspect a local target with `view_image` before editing.

The handoff's `files[]` has `intent`, optional `edit_target_binding`, and ordered
`input_images`. Read the exact per-file compiled prompt and send it unchanged.
Use all five references for generation or target then five references for edit;
this is not a platform-wide attachment limit claim. Use local paths when all
inputs have them. Do not rely on implicit conversation images or omit references.

Preparation does not prove that the current tool accepts every attachment.
The September 30 maintenance smoke rejected six local paths before generation
with `referenced_image_paths must contain at most 5 paths`. Keep the edit target
and all five references, leave `handoff_ready`, and report `BLOCKED/NOT_RUN` if
that limit remains. Do not drop a reference or use a CLI fallback. Current
evidence is in `config/evals/carousel-live-smoke-report.json`; this is an observed
runtime constraint, not a permanent platform limit.

Every fresh return requires `ingest --invocation-json PATH`, with one record
per returned slide/format, including ordinary generation:

```json
[{"slide": 2, "format": "instagram_post", "intent": "edit", "tool": "image_gen.imagegen", "sent_prompt_sha256": "sha256:...", "input_images": [], "returned_source_sha256": "sha256:..."}]
```

Replace `input_images` with the exact ordered bindings used from that handoff:
role, path, SHA-256, and available width/height. The empty array above is only a
schema placeholder and cannot pass ingest. Hash the prompt actually sent for
that file, not the aggregate prompt fingerprint; hash untouched returned bytes
before normalization. Include `tool_call_id` and model only when exposed.
Coverage, prompt hash, order, current input bytes, and raw return hash must all
match before reconciliation or ingestion. No flag exempts a new return.

Receipts store `operator_recorded` invocation evidence. This is not independent
server attestation and does not prove visual correctness or creator approval.
Legacy receipts remain readable and byte-stable without invented evidence.

## Proof-to-final execution

1. Run `python scripts/carousel.py prepare PACKAGE --proof-slide NUMBER`.
2. Send the exact returned compiled prompt and ordered `input_images` to the
   ImageGen call, including the separate target first when editing.
3. Invoke ImageGen for the selected proof. Record its tool-reported model when
   exposed; do not hardcode a permanent model name.
4. Ingest the fresh return with `python scripts/carousel.py ingest PACKAGE
   --instagram-post PATH --invocation-json RECORDS.json [--model MODEL]
   [--feedback-id ID]`.
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
- Changing an operation or target does not reset that budget. Editing a proof
  revokes its approval; unrelated hidden candidates are retained.
- Wrong text, identity drift, missing brandmark, wrong dimensions, stale
  references, or unbound QA are hard failures even when the image is attractive.
- Never recycle an existing package asset as a fresh ImageGen return.
- Creator corrections must first be captured with `carousel feedback`; apply
  them to the same package with `carousel revise` and link the resulting eval.
