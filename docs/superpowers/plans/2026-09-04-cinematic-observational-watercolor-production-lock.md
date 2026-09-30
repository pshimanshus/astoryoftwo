# Cinematic Observational Watercolor Production Lock

Status: implementation landed locally; live acceptance certification blocked
Date: 2026-09-04
Scope: all new repo-managed illustrated posts, carousels, and explicitly requested Reel/Story frames

## Implementation and Verification Record

The code and instruction changes below are implemented in the existing pipeline,
not a parallel workflow. The active profile is the creator-requested default;
that selection is separate from certification of any generated output.

- One active profile and exact reference board; no free-form style overrides or
  fallback style prose. Canonical slides feed shared-only prompt-pack v3 and
  one compiler. Cinematic direction and distinct evidence are checked before
  generation and in actual-pixel QA.
- Historical state-v2 and prompt-pack-v2 packages are read-only, including the
  old combination of state-v3 plus prompt-pack-v2. Status, prepare, ingest,
  review, approve, revise, and finalize regressions cover this boundary.
- Negative prompt remains within the existing 80-word budget with room for
  slide-specific constraints; slash-delimited wording is avoided because it
  collides with filesystem-path sanitization.
- Repeated palette analysis is deduped by freshly computed image-content hash.
  Only numeric measurements are cached in-process; thresholds and evidence
  paths remain current, and changed/corrupt bytes cannot reuse approval.
- Full repository suite: 594 passed, 2 skipped. Subsequent live-report and
  palette checks: 24 passed. Synthetic lifecycle benchmark: PASS, 3.77 seconds
  against the unchanged 10-second budget. All three edited creative skills
  pass the skill validator.
- Four real ImageGen calls were made through production handoffs: two post
  close-ups and two explicitly requested Reel wide frames. Both post attempts
  failed the locked hand/contact plan. Both Reel sources were 941x1672 and
  failed the required 1080x1920 ingest contract. All remain quarantined; no
  creator approval, final promotion, or publishable art is claimed.
- `config/evals/carousel-live-smoke-report.json` preserves the old calibration
  separately from the blocked active-profile rollout, including exact hashes.
  The two-actual-call limit per smoke premise is exhausted. Do not retry these
  premises by resetting their state or silently relaxing dimensions.
- Latest Agentic OS/wiki health still reports unrelated unresolved creator
  feedback in `forever-was-many-small-choices-15`. That record and the mixed
  worktree are preserved. Scoped closeout must not stage unrelated changes.
- The explicit-path safe-publish dry run was attempted but rejected by the
  environment as requiring approval while approvals are disabled. No staging,
  commit, push, or alternate publishing route was attempted.

The remaining live limitation is generator compliance, not missing pipeline
wiring. Completion of all original rollout acceptance criteria still requires
fresh, conforming post and native Reel proofs with actual-pixel review and the
normal creator approval gate. The plan below is retained as implementation
history; canonical rules and executable validators remain the authorities.

## Decision

Make **Cinematic Observational Watercolor v1** the only active illustration
profile in the normal production path.

The pipeline cannot guarantee that an image model's first response will be
correct. It can guarantee that:

1. every generation request uses the same approved style profile and exact
   style-board bytes;
2. every slide carries enough physical and cinematic direction to produce a
   story frame rather than a decorated quote card;
3. every proof and final is inspected against that same plan; and
4. an output that does not pass is quarantined and cannot be approved,
   promoted, or published.

This is an acceptance guarantee, not a promise that every raw generation will
pass on attempt one.

## What We Are Trying to Achieve

The target is not merely “watercolor.” It is an image that feels like a frame
from a lived story:

- the viewer immediately understands one physical event with the copy hidden;
- the couple looks caught inside a moment, not arranged for a portrait;
- the frame implies what happened just before and what may happen next;
- light comes from a believable source and helps organize emotion;
- foreground, midground, and background create spatial and narrative depth;
- two to four visible details carry story evidence rather than decorative
  clutter;
- faces, hands, clothing, objects, and posture remain human, tactile, and
  specific;
- the warm-ivory watercolor-and-ink finish stays consistent without becoming
  glossy, synthetic, photorealistic, vector-like, yellow, or sepia;
- the upper copy space feels integrated into the scene, not pasted onto a
  poster; and
- adjacent slides vary shot, action, setting, and story job enough to create a
  sequence that invites the next swipe.

“Less AI-looking” will not be implemented as an unreliable AI-detector score.
It will be implemented through observable causes: non-posed blocking,
motivated light, coherent depth, tactile irregularity, specific story evidence,
plausible anatomy and contact, restrained symmetry, and the absence of generic
stock-scene artifacts.

## Scope and Non-Goals

In scope:

- replace the current default style reference with the newly approved visual
  family;
- strengthen the existing canonical palette and visual-variety rules;
- make cinematic direction structured production data;
- remove duplicated style strings and stale per-slide prompt copies;
- remove public free-form style overrides from the normal CLI;
- bind the exact style profile, prompt, reference bytes, and compiler version
  into generation fingerprints;
- extend the existing pre-generation review and actual-pixel QA;
- update tests, evals, runtime context, skills, memory pointers, and docs to the
  same authority chain; and
- preserve the existing four production gates and native-format rules.

Not in scope:

- no fifth approval gate;
- no new default agent council, reviewer room, scorecard, or taste ledger;
- no new public package artifact;
- no automatic square or 9:16 derivatives;
- no silent rewrite of historical published packages;
- no new identity system; the existing four-photo identity bundle remains;
- no claim that watercolor should become photorealism; the target is cinematic
  narrative realism within the watercolor-and-ink house style; and
- no unrestricted future style picker. If alternate profiles are introduced
  later, they must be allowlisted, versioned, and explicitly creator-selected.

## Current-State Diagnosis

| Layer | Current behavior | Failure mode |
| --- | --- | --- |
| Canonical rules | `palette.md` defines the finish and `visual-variety.md` defines layering and scene variety. | The finish is strong, but cinematic time, point of view, motivated light, and narrative continuation are not required as one complete contract. |
| Runtime style contract | `carousel_style_contract.json` contains both `shared_style_prompt` and `compact_style_prompt`. | The two values are currently identical, creating immediate drift risk. |
| Master prompt | The master prompt hard-codes a HOUSE STYLE paragraph. | The compiler later adds `Additional style note`, so style is expressed twice. |
| Runtime fallbacks | `carousel_lanes.py`, `carousel_style_consistency.py`, `codex_native_carousel.py`, `carousel_generation_inputs.py`, and `codex_builtin_image_generation.py` contain fallback style prose. | A missing or malformed contract can silently degrade into a different, weaker style instead of failing closed. |
| Slide direction | Slides store overlapping aliases such as `visual`, `scene`, `physical_action`, `composition`, `pose`, `camera`, `background`, and `setting`. | Corrections can update one field while generation or fingerprints read another. |
| Visual-richness contract | `build_visual_richness_contract()` and `visual_richness_prompt()` already exist. | `compile_image_prompt()` explicitly discards `visual_richness`, so the contract never reaches the generator. |
| Prompt package | `prompt-pack.json` stores a second per-slide copy of text, scene, and prompt prose. | `slides.json` and `prompt-pack.json` can disagree; stale prompt text remains package state. |
| CLI | `--style-brief`, `--style-reference`, `STYLE_REFERENCE(S)`, and `jam_today.py` can inject arbitrary style instructions or files. | The production path can bypass the approved house style. |
| Reference validation | Generation requires one style attachment by count. | Any image can satisfy the slot; the path and bytes do not have to match the approved board. |
| Preflight | `visual_plan_quality_gate_reason()` checks copy and physical action. | Generic camera, empty depth, unmotivated light, staged poses, and prop filler can still reach generation. |
| Pixel QA | The fixed order checks action, relationship, spatial integrity, identity, text/style/dimensions. | It does not require concrete evidence that the frame is cinematic, observed, layered, or temporally alive. |
| Palette check | A deterministic palette checker exists and is calibrated. | It is not part of the proof/final promotion path. |
| Evals | The home-cinematic eval already rejects generic lighting and props. | Its stronger semantics are not the normal production validator for every scene type. |
| Skills, docs, memory | Several surfaces repeat the old style name, prose, and reference path. | These surfaces behave like competing contracts instead of thin pointers. |

## Single-Source Ownership Model

Every fact gets one owner. Other surfaces may point to or snapshot that fact,
but may not restate it as an independent instruction.

| Concern | Sole authority | Consumers |
| --- | --- | --- |
| Human-readable finish and palette rules | `config/rules/palette.md` | Context loader, reviewers, tests, style-profile authoring |
| Human-readable cinematic composition and sequence rules | `config/rules/visual-variety.md` | Creative brief, slide validator, pixel QA, evals |
| Active machine-readable generation style | `config/carousel_style_contract.json` → one `style_profile` object | Package writer, prompt compiler, reference binder, fingerprints |
| Approved visual evidence | `config/references/style-lock/cinematic-observational-watercolor-v1/` | The one attached style board and provenance tests |
| Prompt skeleton | `config/references/a-story-illustration-master-prompt.md` | `carousel_master_prompt.py` only |
| Per-slide meaning and direction | `slides.json` | Compiler, fingerprints, preflight, proof selector, QA |
| Per-run immutable style/reference snapshot | `prompt-pack.json` v3 | Reproducibility, stale-profile detection, handoff |
| Compiled generator prompt | Derived at handoff from the sources above | Image generation only; never edited as source truth |
| Exact rendered-pixel observations | `proof-qa.json` and `visual-qa.json` | Promotion state and final audit |
| Creator preference/history | `memory/semantic/premium-illustration-style-lock.md` | Recall only; points to rules/profile rather than copying them |
| Workflow instructions | Repo skills and runtime-context docs | Thin pointers to the authorities above |

An immutable package snapshot is intentional duplication for reproducibility,
not a second authority. It must contain the source profile hash and be rejected
as stale when it no longer matches the active production profile.

## Target Production Flow

```text
creator seed or approved creative brief
                |
                v
Gate 1: concept lock
                |
                v
Gate 2: exact copy + requested native format lock
                |
                v
slides.json
  - one physical action
  - relationship state
  - camera + setting
  - cinematic visual_richness
  - identity/wardrobe + topology
                |
                +------------------------------+
                |                              |
                v                              v
active style profile                  4 exact identity photos
  - prompt text                       + 1 exact style board
  - negative text                              |
  - board path + SHA-256                        |
                +---------------+--------------+
                                v
                    deterministic prompt compiler
                    - style injected once
                    - slide direction injected once
                    - exact copy and format retained
                                |
                                v
                    Gate 3: riskiest-slide proof
                                |
                                v
                    actual-pixel ordered QA
                    - event and relationship
                    - cinematic story frame
                    - anatomy/spatial/identity
                    - exact text/style/palette/size
                                |
                   FAIL --------+-------- PASS
                    |                         |
                    v                         v
               quarantine +             creator approval
               targeted repair                 |
                                                v
                                    generate remaining slides
                                                |
                                                v
                                    Gate 4: final package QA
```

The flow applies to 1080x1440 posts/carousels by default. The same style profile
applies to native 1080x1920 Reel/Story frames or native 1080x1080 square frames
only when those formats were explicitly requested at Gate 2.

## Target Data Contracts

### 1. Active style profile

Refactor `config/carousel_style_contract.json` from duplicated loose fields to
one versioned profile:

```json
{
  "schema_version": "3.0",
  "style_profile": {
    "id": "cinematic-observational-watercolor",
    "version": "1.0.0",
    "status": "active",
    "generation_prompt": "One compact generator-facing style instruction.",
    "negative_prompt": "One compact shared negative instruction.",
    "reference": {
      "path": "config/references/style-lock/cinematic-observational-watercolor-v1/contact-sheet.png",
      "sha256": "sha256:<exact-board-digest>",
      "attachment_count": 1
    }
  }
}
```

Keep the existing typography, characters, identity policy, visual-story policy,
content lanes, and production gates in this contract. Delete
`shared_style_prompt`, `compact_style_prompt`, `shared_negative_prompt`, and the
plural `style_references` field after all consumers move to the profile object.

The profile prompt must describe only generation behavior. Long validation
rubrics, workflow state, hashes, provenance, filenames, and approval language
remain outside the image prompt.

### 2. Canonical slide direction

For new packages, `slides.json` remains the only per-slide semantic authority.
Reuse and strengthen the existing `visual_richness` concept rather than adding
a second `cinematic_direction` object.

```json
{
  "slide": 3,
  "role": "recognition",
  "copy": "Exact creator-approved text",
  "physical_action": "One observable action with subject, object, and visible consequence.",
  "relationship_state": "The emotional turn visible in that action.",
  "camera": {
    "shot_size": "medium-wide",
    "position": "doorway-height, three-quarter view",
    "negative_space": "clean upper-left paper space for copy"
  },
  "setting": {
    "place": "specific sub-location",
    "time": "specific time or weather state",
    "motivated_light": "source, direction, and emotional job",
    "depth_layers": {
      "foreground": "one story-supporting layer",
      "midground": "the focal event",
      "background": "one context or consequence layer"
    }
  },
  "focal_hierarchy": "First read, second read, protected copy space.",
  "visual_richness": {
    "point_of_view": "Whose feeling organizes the frame and why.",
    "before_frame": "The visible state or incident immediately before this instant.",
    "after_frame": "The likely next beat left open by the frame.",
    "continuation_pull": "The unanswered visual question that earns the next swipe.",
    "story_evidence": [
      {
        "carrier": "specific person, object, mark, or spatial relation",
        "observable_state": "what is visibly true about it",
        "narrative_job": "what it proves about this beat"
      }
    ],
    "posed_portrait_allowed": false,
    "decorative_clutter_allowed": false
  },
  "wardrobe": "Anchors taken from the attached current identity photos.",
  "props": "Only objects with a named story job.",
  "emotion": "Microexpression and body-language direction.",
  "continuity_lock": "Only facts that must persist into adjacent slides.",
  "hand_map": {},
  "spatial_topology": {}
}
```

Rules for this object:

- `physical_action` owns the event. Do not repeat it in `visual` or `scene`.
- `camera` owns shot size, viewpoint, and copy negative space. Do not also store
  `shot`, `composition`, or `pose` aliases.
- `setting` owns location, time, motivated light, and depth. Do not also store a
  prose `background` alias.
- `visual_richness` owns point of view, before/after implication, continuation,
  and two to four story-evidence records. It does not repeat action, camera, or
  setting.
- `props` may name only objects used by `physical_action` or `story_evidence`.
- `posed_portrait_allowed` and `decorative_clutter_allowed` must be literal
  `false` in the default profile.
- the last slide may resolve rather than open the continuation question, but it
  must still have a visible after-state/payoff.

For compatibility, readers may understand old aliases, but new writers must
emit only the canonical fields above. Compatibility aliases must never be
written back into new packages.

### 3. Prompt pack v3

Keep the existing filename; change its responsibility. It becomes shared,
immutable generation input rather than a second store of slide prose:

```json
{
  "schema_version": "carousel-prompt-pack/v3",
  "brandmark": "@a.storyof.two",
  "style_profile": {
    "id": "cinematic-observational-watercolor",
    "version": "1.0.0",
    "contract_sha256": "sha256:<profile-json-digest>",
    "generation_prompt": "Snapshot of the active prompt",
    "negative_prompt": "Snapshot of the active negatives",
    "reference": {
      "path": ".internal/references/style/<localized-file>.png",
      "sha256": "sha256:<localized-file-digest>"
    }
  },
  "identity_reference_images": [
    ".internal/references/identity/<file-1>",
    ".internal/references/identity/<file-2>",
    ".internal/references/identity/<file-3>",
    ".internal/references/identity/<file-4>"
  ]
}
```

Remove the `slides` array, per-slide `prompt`, per-slide `scene`, duplicated
`text`, top-level `style_prompt`, top-level `negative_prompt`, and plural
`style_reference_images`. Compiled `.prompt.txt` files remain disposable
handoff artifacts and are always regenerated from `slides.json` plus this
shared snapshot.

## Approved Reference Bundle

Create:

`config/references/style-lock/cinematic-observational-watercolor-v1/`

Contents:

- `source-01-wedding-action.png`
- `source-02-mountain-wide.png`
- `source-03-kitchen-support.png`
- `source-04-sofa-close-up.png`
- `contact-sheet.png`
- `manifest.json`
- `README.md`

Use the clean exported frames, not the supplied screenshot with browser/app UI.
The four candidate source frames are:

| Story job | Current clean candidate |
| --- | --- |
| Wedding action | `output/carousels/2026-09-04/i-call-it-remembering-brand-reset/final/slide-01.png` |
| Mountain wide | `output/carousels/2026-09-04/i-call-it-remembering-brand-reset/final/slide-03.png` |
| Kitchen support | `output/carousels/2026-09-04/i-call-it-remembering-brand-reset/final/slide-05.png` |
| Sofa close-up | `output/carousels/2026-09-04/i-call-it-remembering-brand-reset/final/slide-06.png` |

Record each source's dimensions, source SHA-256, tracked destination SHA-256,
story job, and the deterministic board layout in `manifest.json`. Record the
final contact-sheet SHA-256 in both the manifest and the active style profile.
Only `contact-sheet.png` is attached at generation time; the four source files
are provenance and maintenance evidence.

The four current candidates already pass the existing deterministic palette
check. Re-run that checker after copying and after composing the board; never
trust the source path alone.

Current source-byte fingerprints to verify before the files are promoted into
the tracked bundle:

| Source | SHA-256 |
| --- | --- |
| Wedding action / slide 01 | `cdd8d2028def22c8dd4cf72d5d8e9539e875ead806e264e49928217bda9fe051` |
| Mountain wide / slide 03 | `be4aa4972322f9598d8908e9da4bc2fd37b4aaa079c89edfe8dadb2ee610d4a1` |
| Kitchen support / slide 05 | `54d408c727f09040d95eeac9da2867f00323c610aa7ba237969c53036ad36b0f` |
| Sofa close-up / slide 06 | `e16a85d9429a8acf7a6cd654e16d6ba6b9d8b12b4ea2e1f0c228f0f6d704024f` |

## Implementation Sequence

### Phase 0 — Baseline and worktree isolation

1. Capture `git status --short` and preserve all unrelated current changes.
2. Work only on the files enumerated by this plan; do not normalize or rewrite
   unrelated modified docs, memory, media, or output packages.
3. Run the current focused carousel tests to create a before-state report.
4. Mark all existing `carousel-prompt-pack/v2` packages as historical/read-only
   for generation. Do not edit their JSON or images in place.

Exit condition: the current failures, passing baseline, and dirty-worktree
boundaries are recorded before implementation changes.

### Phase 1 — Lock the visual evidence and canonical rules

Files:

- `config/references/style-lock/cinematic-observational-watercolor-v1/*`
- `config/rules/palette.md`
- `config/rules/visual-variety.md`
- `config/rules/on-image-text.md`
- `config/carousel_style_contract.json`
- `pipeline/stages/carousel_contract.py`

Changes:

1. Build the clean four-frame reference bundle and deterministic contact sheet.
2. Update `palette.md` so the named default is Cinematic Observational
   Watercolor v1. Preserve the warm-ivory, watercolor-and-ink, muted-palette,
   tactile-detail, and anti-yellow hard fails.
3. State explicitly that “cinematic” means observed story depth inside the
   illustration style, not full photorealism.
4. Extend `visual-variety.md` with point of view, before/after implication,
   motivated light, depth-layer jobs, continuation pull, natural asymmetry, and
   concrete non-AI proxies.
5. Update `on-image-text.md` only where it points to the old style bundle; keep
   exact-copy authority there.
6. Refactor the JSON contract to the single `style_profile` schema above.
7. Make `carousel_contract.py` validate profile id/version, one active profile,
   one reference, SHA-256 syntax, actual file existence, actual-byte hash, and
   attachment count one.

Exit condition: there is one named active profile and one exact approved board;
removing or changing either fails contract tests.

### Phase 2 — Make cinematic direction first-class slide data

Files:

- `pipeline/stages/carousel_visual_integrity.py`
- `pipeline/stages/carousel_visual_storytelling.py`
- `pipeline/stages/codex_native_carousel.py`
- `pipeline/stages/carousel_package_writer.py`
- creative-brief fixtures and schema tests

Changes:

1. Extend the existing `build_visual_richness_contract()` rather than creating
   another cinematic contract module.
2. Replace synthetic generic defaults with fail-closed validation. A slide with
   missing point of view, motivated light, depth layers, before/after state, or
   story evidence stays draft and cannot prepare a proof.
3. Generalize `validate_director_storyboard()` so the production slide
   validator and eval fixtures call the same validation functions.
4. Require two to four `story_evidence` records; every record must name a
   carrier, observable state, and narrative job.
5. Require a specific sub-location, time/weather state, camera position,
   motivated light source/direction/job, and distinct foreground/midground/
   background responsibilities.
6. Reject generic values such as “cozy home,” “nice lighting,” “some props,” or
   “appropriate composition.”
7. Reject repeated shot size/story job across a sequence unless a deliberate
   repetition reason is present.
8. Update `slides_from_creative_baseline()` and `build_package()` to accept and
   preserve the canonical fields only.
9. Update `_minimal_slide()` to retain `visual_richness` and stop writing the
   `visual`, `scene`, `composition`, `pose`, and `background` aliases for new
   packages.

Exit condition: a locked creative brief produces one non-duplicated slide
record per beat, and incomplete cinematic direction blocks before ImageGen.

### Phase 3 — Remove production style bypasses

Files:

- `scripts/carousel.py`
- `scripts/jam_today.py`
- `Makefile`
- `pipeline/stages/codex_native_carousel.py`
- `pipeline/stages/carousel_lanes.py`
- every active non-legacy standalone illustration entry point found by the
  implementation inventory

Changes:

1. Remove public `--style-brief` and `--style-reference` arguments from
   `carousel create`.
2. Remove `STYLE_REFERENCE`, `STYLE_REFERENCES`, and the equivalent forwarding
   from `make carousel` and `jam_today.py`.
3. Remove `style_brief` and `style_reference_paths` from production package
   creation signatures.
4. Remove `creative-context.json.style_brief`.
5. Load the active style only through `load_style_contract()`.
6. Keep test injection at a Python dependency/fixture boundary using a temporary
   contract root; do not keep a user-facing backdoor merely for tests.
7. Remove all prose style fallbacks. A missing profile is a configuration error,
   not permission to generate a weaker default.
8. Expose one shared `load_active_illustration_style_profile()` resolver from
   the existing contract layer. The carousel post path, explicitly requested
   Reel/Story formats, and any active standalone illustration path must call
   this same resolver and reference binder. Legacy render scripts remain
   explicitly legacy and are not silently revived.

If alternate styles are needed later, introduce a closed `--style-profile ID`
selector only after a versioned profile registry exists. Do not reintroduce
free-form prompt or arbitrary-file overrides.

Exit condition: no normal CLI, Make target, or jam command can substitute
another style sentence or board.

### Phase 4 — Compile the style and story exactly once

Files:

- `config/references/a-story-illustration-master-prompt.md`
- `pipeline/stages/carousel_master_prompt.py`
- `pipeline/stages/carousel_prompt_compiler.py`
- `pipeline/stages/carousel_generation_inputs.py`
- `pipeline/stages/carousel_style_consistency.py`
- `pipeline/agentic/checks/prompt_constraints.py`

Changes:

1. Replace the hard-coded HOUSE STYLE paragraph in the master template with
   `[INSERT CANONICAL HOUSE STYLE HERE]`.
2. Add one `CINEMATIC STORY FRAME` placeholder for the compact, structured slide
   direction.
3. Update `_fill_slide_placeholders()` to require and replace both placeholders.
4. Delete `Additional style note` from the slide-direction suffix.
5. Bump the master prompt version to a v7 cinematic-profile identifier.
6. Stop discarding `visual_richness` in `compile_image_prompt()`.
7. Compile canonical slide fields in a fixed order: exact text, physical event,
   camera, setting/light/depth, point of view and temporal implication, story
   evidence, topology, identity/wardrobe, style, brand, negatives, and active
   creator feedback.
8. Keep the current prompt budgets. Compact typed fields; never truncate locked
   copy, physical action, identity, topology, or feedback constraints.
9. Fail on unresolved placeholders and assert that the style-profile text occurs
   exactly once.
10. Bump `PROMPT_COMPILER_VERSION`; the new version becomes part of every
    generation fingerprint.
11. Replace embedded old-style names and fallback phrases in
    `carousel_style_consistency.py` and `prompt_constraints.py` with checks
    against the resolved profile id and required semantic fragments.

Exit condition: one deterministic compiled prompt is reproducible from
`slides.json`, `prompt-pack.json`, the format lock, and active feedback—with no
second style paragraph and no stale per-slide prompt source.

### Phase 5 — Collapse package duplication and bind exact bytes

Files:

- `pipeline/stages/carousel_package_writer.py`
- `pipeline/stages/carousel_generation_inputs.py`
- `pipeline/stages/codex_builtin_image_generation.py`
- package-state compatibility tests

Changes:

1. Write `carousel-prompt-pack/v3` without a `slides` array.
2. Refactor `_slide_source()` and `effective_slide_prompt_fields()` to consume
   `slides.json` directly and remove the prompt-record argument.
3. Store one immutable style-profile snapshot in the prompt pack.
4. At read time, compare the snapshot id, version, contract hash, prompt hash,
   negative hash, reference path, and actual reference SHA-256 with the active
   profile.
5. Return a fail-closed `style_profile_stale` reason when any shared style input
   changes. A profile change invalidates the entire deck.
6. Include canonical `visual_richness`, camera, and setting data in the
   slide-local source fingerprint. A correction to one slide invalidates only
   that slide.
7. Keep identity, format, brand, compiler, order, and creator-feedback
   fingerprints exactly as shared or slide-local inputs according to their
   existing scope.
8. Update `build_shared_reference_bindings()` to return exactly four identity
   files plus the one profile reference and verify all five actual byte hashes.

Exit condition: changing JSON whitespace changes nothing; changing one slide's
cinematic direction invalidates that slide; changing the style profile or board
invalidates every slide.

### Phase 6 — Strengthen the existing pre-generation gate

Files:

- `pipeline/stages/codex_builtin_image_generation.py`
- `pipeline/stages/carousel_visual_storytelling.py`
- `pipeline/stages/carousel_style_consistency.py`

Changes:

1. Expand `visual_plan_quality_gate_reason()` to call the shared cinematic
   validator after the existing exact-copy and physical-action checks.
2. Validate canonical camera, motivated light, depth layers, story evidence,
   before/after implication, continuation/payoff, non-posed mode, and sequence
   variety.
3. Expand `identity_consistency_gate_reason()` into reference-integrity review:
   preserve the four-photo identity roles, require the exact active style-board
   bytes, and reject identity/style overlap.
4. Extend the existing style-consistency check to require one active profile
   id/version and one style insertion. Do not create a second style validator.
5. Keep `pre_generation_review_gate_reason()` as the one preflight entry point.

Exit condition: an under-directed or stale-profile package cannot prepare the
risky proof handoff.

### Phase 7 — Add cinematic evidence to actual-pixel QA

Files:

- `pipeline/stages/carousel_pixel_qa.py`
- `pipeline/stages/carousel_visual_storytelling.py`
- `pipeline/agentic/checks/palette.py`
- QA fixtures and helpers

Changes:

1. Add `cinematic_story_frame` immediately after `relationship_state` in the
   existing fixed pixel-QA order. This is an internal ordered check inside Gates
   3 and 4, not a new public workflow gate.
2. Require per-frame observations:
   - `frame_reads_as_caught_event: true`;
   - `before_after_implied: true`;
   - `motivated_light_observed` with source and direction;
   - foreground, midground, and background evidence;
   - `focal_action_clear: true`;
   - two to four visible story-evidence items mapped to the plan;
   - `posed_portrait: false`;
   - `decorative_clutter: false`;
   - `generic_ai_tells: []`;
   - a non-empty continuation pull, or an explicit final-payoff observation on
     the last slide; and
   - concrete image-first evidence rather than a bare verdict.
3. Reuse `validate_frame_readability()` for file/hash binding and the ordered
   fail-fast result.
4. Run the existing deterministic `check_palette()` on the exact inspected
   proof/final asset. Do not duplicate its thresholds in carousel code.
5. Compare observed story evidence with planned evidence; a beautifully painted
   but generic replacement scene fails.
6. On failure, quarantine the bytes and feed only the concrete failed
   observations into the existing slide-local repair path.

Exit condition: “looks pretty” cannot pass. A promoted frame must prove the
event, cinematic depth, house finish, identity, exact text, brandmark, anatomy,
and native dimensions on the exact approved bytes.

### Phase 8 — Update evals and live smoke coverage

Files:

- `evals/tasks/ASTO-016-home-cinematic-visual-evidence/*`
- `evals/checkers/task_specific.py`
- `config/evals/carousel-live-smoke-scenarios.json`
- relevant tests under `tests/`

Changes:

1. Preserve ASTO-016's home-specific cases but make it call the same production
   cinematic validator used by package preflight.
2. Add fixtures for four scene types represented by the approved board:
   wedding action, wide landscape, domestic support, and intimate close-up.
3. Add negative controls for staged portrait, generic warm light, empty
   background, prop spam, repeated medium two-shot, copied reference text, and
   glossy/photorealistic finish.
4. Update live-smoke configuration to the new style-board path and hash.
5. Run at least one real proof smoke with a complex physical action and one
   wide/deep scene before enabling the profile as the default.

Exit condition: the same defect fails unit tests, eval fixtures, live proof QA,
and final QA; there is no eval-only rule that production ignores.

### Phase 9 — Turn skills, docs, and memory into pointers

Files:

- `config/skills/carousel-jam-runtime-context.md`
- `config/skills/illustration-carousel-framework.md`
- `config/skills/carousel-jam-autopilot.md`
- `.agents/skills/a-story-carousel-jam/SKILL.md`
- `.agents/skills/a-story-direct-visual-story/SKILL.md`
- `config/references/a-story-premium-illustration-style-lock.md`
- `memory/semantic/premium-illustration-style-lock.md`
- `memory/semantic/carousel-idea-preferences.md`
- `memory/working.md`
- `wiki/insights/successful-carousel-standard.md`
- `config/references/identity/README.md`

Changes:

1. Replace old reference paths with the new profile pointer.
2. Remove copied style paragraphs from skills and reference notes. Each surface
   should say where the canonical rule and active profile live and what stage
   consumes them.
3. Convert the premium-style semantic-memory page into creator preference,
   approval date, provenance, and links—not another normative style contract.
4. Replace old style prose in `memory/working.md` with one pointer to semantic
   memory, preserving its pointer-only contract.
5. Update wiki material as derived documentation only; it must not become an
   authority over `config/rules/`.
6. Do not change `AGENTS.md`; update downstream surfaces to match it.

Exit condition: repository search finds the old bundle only in historical
provenance or migration tests, and finds the full machine style prompt only in
the active style contract plus immutable package snapshots.

### Phase 10 — Verification, rollout, and closeout

Focused automated coverage:

- `tests/test_creator_workflow_contract.py`
- `tests/test_carousel_prompt_compiler.py`
- `tests/test_carousel_generation_inputs.py`
- `tests/test_carousel_cli.py`
- `tests/test_carousel_source_normalization.py`
- `tests/test_carousel_pixel_qa.py`
- `tests/test_carousel_visual_storytelling.py`
- `tests/test_carousel_hot_path_cli_e2e.py`
- `tests/test_illustration_carousel.py`
- `tests/test_fail_closed_visual_qa.py`
- `tests/test_checks_palette.py`
- `tests/test_carousel_live_smoke_contract.py`
- `tests/test_visual_story_checker_cli.py`

Required assertions:

1. the style contract exposes one profile, one prompt, one negative, and one
   exact board;
2. public CLI help has no arbitrary style override;
3. every active non-legacy illustration generation entry point resolves the
   same active style profile and contains no fallback style literal;
4. new prompt packs contain no slide prose;
5. compiled prompts contain the profile instruction and cinematic direction
   exactly once;
6. unresolved template placeholders fail;
7. generic or missing cinematic fields fail before generation;
8. four identity photos plus the exact one style board are required;
9. a style-profile or board-byte change invalidates all slides;
10. a one-slide cinematic correction invalidates only that slide;
11. pixel QA cannot pass without concrete cinematic observations;
12. palette drift blocks promotion;
13. all current identity, topology, copy, brandmark, dimension, quarantine,
    proof-approval, and format tests remain intact; and
14. 9:16 and square outputs remain explicit-request-only.

Recommended command order during implementation:

```bash
venv/bin/python -m pytest tests/test_creator_workflow_contract.py -q
venv/bin/python -m pytest tests/test_carousel_prompt_compiler.py tests/test_carousel_generation_inputs.py -q
venv/bin/python -m pytest tests/test_carousel_visual_storytelling.py tests/test_carousel_pixel_qa.py -q
venv/bin/python -m pytest tests/test_carousel_cli.py tests/test_carousel_hot_path_cli_e2e.py -q
venv/bin/python -m pytest tests/test_checks_palette.py tests/test_carousel_live_smoke_contract.py -q
venv/bin/python -m pytest tests/test_agentic_docs_contract.py tests/test_codex_project_surfaces.py -q
venv/bin/python scripts/agentic_os.py health
venv/bin/python scripts/wiki_health.py --write --fix-index --session-note "Lock Cinematic Observational Watercolor v1 across the illustration pipeline"
make publish-dry-run NOTE="Lock Cinematic Observational Watercolor v1" INCLUDE="<explicit changed paths>"
```

After automated checks, run one normal 1080x1440 carousel proof and one
explicitly requested 1080x1920 illustrated Reel/Story proof. Inspect their
actual exported pixels, not only prompt text or metadata. Enable the profile as
the default only after both prove the same finish across close, action, and
wide/depth scenes.

## Migration and Compatibility

- Historical output packages and published images remain untouched.
- `carousel-prompt-pack/v2` remains readable for audit/status only and cannot
  start or resume generation under the new runtime.
- An in-progress v2 package must be intentionally rebuilt from its approved
  creative brief or current `slides.json`; it is never silently upgraded.
- The rebuild creates a new package directory, preserves exact locked copy and
  requested formats, and uses the active v3 prompt pack/profile.
- Existing old-style reference assets remain in place as provenance until a
  separate cleanup is approved. They are no longer selected by production.
- Compatibility readers may map old fields in memory, but new writers never
  emit the old aliases.

## Failure Handling

| Failure | Required behavior |
| --- | --- |
| Active style profile missing or malformed | Stop package creation. |
| Board path exists but bytes do not match the profile hash | Stop before handoff. |
| Package snapshot differs from active profile | Mark shared inputs stale and require rebuild. |
| Cinematic direction is missing or generic | Keep package at copy/format lock; next action is to complete visual direction. |
| Proof is pretty but staged, shallow, or generic | Fail `cinematic_story_frame`, quarantine, and repair that slide. |
| Palette/finish drifts | Fail style/palette review and quarantine. |
| Identity or topology fails | Preserve existing fail-fast ordering and quarantine. |
| Exact copy or brandmark fails | Quarantine; do not repair through metadata. |
| Image model remains unable to satisfy the frame within retry budget | Stop honestly with the failed evidence; do not promote the closest-looking attempt. |

## Risks and Controls

| Risk | Control |
| --- | --- |
| “Cinematic” becomes vague aesthetic prose | Require typed, observable camera/light/depth/time/story-evidence fields. |
| Style board overfits content from one scene | Use four frames spanning action, landscape, support, and close intimacy. |
| Example text leaks into generated copy | Exact-text QA plus random/copied-text hard fail; only approved slide copy and brandmark may appear. |
| More direction bloats prompts | Compile compact typed fields once and retain the current hard prompt budget. |
| New schema breaks historical packages | Read-only compatibility and intentional rebuild; no in-place migration. |
| Multiple validators drift | One shared production validator called by preflight, CLI checker, and evals. |
| Rules and skills drift again | Long rules live only in `config/rules/`; skills and memory store pointers. |
| Free-form overrides reappear for convenience | Contract tests inspect public CLI/Make surfaces and reject those flags. |
| Subjective QA becomes a numeric taste score | Use ordered pass/fail observations with concrete visual evidence; no aggregate score. |

## Definition of Done

The implementation is complete only when all of the following are true:

- every new repo-managed illustration, carousel, and explicitly requested Reel/
  Story frame resolves to `cinematic-observational-watercolor@1.0.0` by default;
- the runtime has one style prompt, one negative prompt, and one exact style
  board;
- no production command accepts an arbitrary style sentence or reference file;
- new `slides.json` files contain complete structured cinematic direction and
  none of the retired scene/composition aliases;
- new prompt packs contain shared immutable inputs only, not duplicated slide
  copy or scene prose;
- generated prompts include the active style and slide cinematic direction
  exactly once and stay within budget;
- all five required attachments are exact, hash-bound files: four actual
  identity photographs plus one approved style board;
- generic visual plans fail before ImageGen;
- proof and final promotion require actual-pixel evidence for cinematic story,
  palette, identity, anatomy/spatial integrity, exact text, brandmark, and native
  dimensions;
- failed outputs remain quarantined and cannot become final;
- old packages remain unchanged and read-only;
- all focused tests, live smoke checks, Agentic OS health, and wiki health pass;
  and
- repository search confirms that old style prose and paths are not active in
  CLI, runtime, skills, or production tests.

## File-Level Change Inventory

| File or area | Planned responsibility |
| --- | --- |
| `config/rules/palette.md` | Canonical finish/palette semantics |
| `config/rules/visual-variety.md` | Canonical cinematic story-frame and sequence semantics |
| `config/carousel_style_contract.json` | One active machine style profile |
| `config/references/style-lock/cinematic-observational-watercolor-v1/` | Approved visual evidence and hashes |
| `carousel_contract.py` | Style-profile schema/path/hash validation |
| `carousel_visual_integrity.py` | Build and validate the one visual-richness contract |
| `carousel_visual_storytelling.py` | Shared plan and frame-readability validation |
| `carousel_lanes.py` | Identity helpers only; no style fallback |
| `carousel_style_consistency.py`, `prompt_constraints.py` | Validate the resolved profile, not duplicated style prose |
| `codex_native_carousel.py` | Canonical slide/profile package creation, no overrides |
| `carousel_package_writer.py` | Non-duplicated slides and prompt-pack v3 |
| `carousel_master_prompt.py` | Structural template injection and version |
| `carousel_prompt_compiler.py` | One deterministic prompt compilation path |
| `carousel_generation_inputs.py` | Canonical shared/slide fingerprints and stale detection |
| `codex_builtin_image_generation.py` | Preflight, exact reference binding, proof lifecycle |
| `carousel_pixel_qa.py` | Ordered actual-pixel cinematic acceptance |
| `pipeline/agentic/checks/palette.py` | Reused deterministic palette evidence |
| `scripts/carousel.py`, `scripts/jam_today.py`, `Makefile` | One production path without arbitrary style bypasses |
| skills, runtime context, references, memory, wiki | Thin pointers and provenance only |
| tests/evals/live smoke | Regression proof across the full path |

This plan deliberately strengthens the existing pipeline. It does not introduce
a parallel illustration workflow: the existing rules, style contract, slide
package, prompt compiler, four gates, reference binder, pixel QA, and closeout
remain the path—each with one clearer responsibility and no competing style
source.
