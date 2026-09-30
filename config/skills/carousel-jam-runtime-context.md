# Carousel Jam Runtime Context

last_updated: 2026-09-30
status: minimal default runtime

## Purpose

This is the compact context for ordinary @a.storyof.two carousel work. It keeps
the default run fast and readable. Canonical `config/rules/` files win on
palette, identity, text, brandmark, dimensions, variety, relationship motion,
and scene/entity integrity.

Do not load the long theme, scoring, memory, agent-room, or review-loop sources
at startup. Search the relevant section only when a creator correction, rejected
lane, or failed check needs it. Use `$a-story-instagram-idea-loop` only on an
explicit request for the deep idea loop.

## Default Flow

```text
small brief
-> Gate 1: concept lock
-> Gate 2: exact copy + requested format lock
-> one physical event per slide
-> compact prompt compile
-> riskiest proof
-> Gate 3: actual-pixel QA + creator approval
-> remaining native slides
-> Gate 4: final package QA
```

These are the only gates. A deterministic check may support a gate but must not
create another approval state or duplicate artifact.

The active illustration look is resolved fail-closed from the single
`style_profile` in `config/carousel_style_contract.json`. Human-readable finish
and cinematic rules live in `config/rules/palette.md` and
`config/rules/visual-variety.md`; this runtime context does not restate them.

Creator feedback is input to this same flow. Preserve its exact words in
`creator-correction.json`, emit the existing idempotent `LearningEvent`, and
repair only the affected authoritative fields. Pass only concise `must_change`
and `must_preserve` constraints into ImageGen; raw feedback stays out of the
prompt. Capture, indexing, evaluation, and health create no additional gate.
Use `carousel feedback`, repair existing inputs, and `carousel revise` for this
exception path; `feedback-status` reports actual resolution. Durable policy
changes remain inactive proposals until the creator approves the diff.

## Creative Context

- Preserve the creator's literal sequence, objects, corrections, approved
  language, and rejected scope.
- Keep creator constraints and the selected architecture active while writing
  the alive draft. Apply voice and editorial checks to that draft; rules alone
  do not invent the idea or establish its quality.
- Make the relationship legible to a cold viewer through action and consequence,
  not explanation alone.
- Use `config/skills/creator-skill-stack.md` as the six-question taste pass.
- For retrieved-carousel analysis or a specific sequence repair, consult
  `memory/semantic/carousel-sequence-learnings.md`; its linked archive preserves
  the visual evidence and limits. Do not load the full archive for every jam.
- Before any multi-slide copy delivery, apply the storytelling hook's
  `Copy Delivery Review`; instruction compliance and editorial quality are
  separate checks. Use its taste calibration only when the copy problem needs it.
- Keep public copy free of internal framework and score language.
- The last beat must reframe or answer the opening, not soften into a generic
  moral.
- Preserve a creator-supplied architecture, including
  `Cover -> Cold Open -> Deepening -> Conflict -> Turn -> Payoff`.
- Treat that reflective structure as first-class. Deepening, Conflict, and Turn
  may each span multiple slides when each new scene changes the story.

## Format Lock

Resolve format from the current request and corrections before prompts:

- `instagram_post`: default only when no canvas is specified; 1080x1440.
- `reels_stories`: 1080x1920; explicit request only.
- `square`: 1080x1080; explicit request only.

Persist only the requested set in `format-contract.json` and prompt each exact
target. Never infer intent from old folders. A current creator correction
overrides defaults and stale assets.

The prompt still requests the exact target and must not mention a fallback.
Observed built-in-runtime accommodation applies only at `instagram_post`
ingest: quarantine and bind an untouched exact-3:4 source whose size lies from
1080x1440 through 1440x1920 inclusive, then proportionally downsample once to
the exact 1080x1440 proof/final asset. No crop, pad, stretch, upscale, wrong
ratio, or second resample is allowed. Story/Reel and square sources remain
exact-size only. Preserve source hash/dimensions and reuse approved normalized
proof bytes as the final candidate.

## Scene Lock

For every slide, `slides.json` must contain exact on-image text (or an explicit
`copy_mode: wordless` lock for an intentional silent beat) and one concise
physical event:

```text
subject + observable action + target/object + visible reaction or changed state
```

Also capture the few generation-critical facts in their canonical fields:
camera and focal hierarchy; specific setting, time, motivated light, and depth
layers; hands, gaze, body distance, object ownership, expected people, wardrobe
reference, and text-safe space; plus `visual_richness` for point of view,
before/after implication, continuation/payoff, and two to four story-evidence
records. Vary story job, action, shot, or setting between adjacent slides. Text
completes the scene; it must not be the only story carrier.

Every person slide must store a complete hand-ownership map and whole-person/
object topology in `slides.json`. Prompt compilation must fail closed unless it
can embed those slide-specific plans in the actual ImageGen prompt. Generic
anatomy negatives do not satisfy this lock.

For locked production, apply `$non-ai-image-skill` and persist the applicable
risk-specific `scene_contract` per slide. Keep it bound to the exact scene and
copy through compilation; canonical rules own its detailed requirements.

## Generation Lock

- The repo prepares prompts and reference bindings; Codex performs the image
  generation call and actual-pixel inspection. There is no API renderer,
  credential flow, OCR dependency, or environment capability artifact.
- Read `identity-dossier.json.selected_generation_bundle` and attach its exact
  four Aachu/Zuv/together identity files plus one style-board file copied from
  the active profile resolved through `config/carousel_style_contract.json`.
  Its current evidence path is
  `config/references/style-lock/cinematic-observational-watercolor-v1/contact-sheet.png`;
  runtime code must also verify the declared SHA-256 rather than trusting this
  prose pointer.
  These are exactly five canonical references. Generate attaches five files;
  edit attaches its separate target first, then these same five references.
  This is not a published-platform limit claim. Follow the prepared ordered
  `input_images`; never drop an identity role or append individual style frames.
  Text-only identity descriptions are blocked.
- An edit uses `prepare --operation-json PATH`; the canonical `image_operation`
  selects a bound canvas, while existing slide fields and feedback remain the
  sole scene/copy/change authority. Inspect its local target before calling
  `image_gen.imagegen`. Send the exact compiled prompt without rewriting it.
- Every new return, including generation, requires `ingest --invocation-json
  PATH`. Record the per-file sent prompt hash, ordered input bindings, and raw
  returned-source hash. This is `operator_recorded` evidence, never server
  attestation. Preserve legacy receipts without inventing invocation evidence.
  See `.agents/skills/astory/references/imagegen-contract.md` for the schema.
- Wardrobe comes from the attached identity/current-request images first.
- Preserve both whole people: face, hair, height, proportions, expression,
  posture, and clothing.
- Integrate exact approved text and tiny `@a.storyof.two` at top-right.
- Generate one risky proof first. Do not batch until its current pixels pass and
  the creator approves.
- Ingest each returned image into quarantine immediately, then inspect the
  decoded file with `view_image` and submit QA bound to its path, SHA-256, and
  dimensions. If either image generation or pixel viewing is unavailable,
  remain `handoff_ready` and report `BLOCKED/NOT_RUN`; never infer PASS.
- No identity eval means no next slide.
- Allow two total semantic attempts for one visual premise. Replace the premise
  after the second miss.

## Pixel QA

Begin with the non-AI-image skill's blind scene read, with copy hidden and
before revealing the intended answer: actor, recipient or response, and visible
consequence. Add only applicable specialist reviews, then compare against the
locked scene contract. Inspect the decoded file, in order:

1. visible physical action and relationship state;
2. cinematic caught-event read, before/after implication, motivated light,
   depth layers, focal action, story evidence, and continuation/payoff;
3. expected people/entities, continuous silhouettes, body/solid-object depth,
   and per-hand owner -> arm -> wrist -> hand -> contacted-object evidence;
4. Aachu/Zuv likeness and wardrobe against attached reference IDs;
5. exact text, brandmark, house style, palette, and native dimensions.

Bind QA to the current package-relative path, SHA-256, dimensions, and derived
scene-contract hash. A prompt,
filename, agent label, or generation report cannot pass pixel QA. Failed
candidates stay quarantined and set the next action to a concrete repair.
One generic sentence about "coherent hands" cannot pass: the review must name
every visible hand's owner and side, contact, attachment, finger integrity, and
solid-object intersection result. Foreground support and overlap require the
same scrutiny; unresolved critical evidence stays failed or `data_gap`.

## Minimal Artifacts

Before proof: `creative-context.json`, `format-contract.json`, `slides.json`,
`prompt-pack.json`, `generation-state.json`, and compiled prompt files. After
proof: quarantined PNG and `proof-qa.json`. After final: requested native PNGs,
`final-images.json`, `visual-qa.json`, and `final-audit.json`.

The ordinary run does not create debate rooms, numeric scorecards, provenance
graphs, ledgers, stage reviews, or wiki-update artifacts.

## Public State Vocabulary

Use exactly: `draft`, `blocked`, `handoff_ready`, `proof_qa_required`,
`proof_failed`, `awaiting_creator_proof_approval`, `batch_ready`,
`final_qa_required`, `final_qa_failed`, and `publish_ready`.

An ordinary carousel command never runs tests or health checks and never writes
wiki, memory, rules, tests, or diagnostics. Those are maintenance and closeout
operations, not production side effects.
