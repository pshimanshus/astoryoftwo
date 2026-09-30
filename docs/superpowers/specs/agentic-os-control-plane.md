# Agentic OS Control Plane

last_updated: 2026-09-12
confidence: 0.96
sources:
- AGENTS.md
- config/rules/
- config/skill-systems.json
- pipeline/agentic/
- pipeline/stages/carousel_visual_storytelling.py
- pipeline/stages/codex_builtin_image_generation.py
- evals/feedback_cases.py
- evals/deepeval_adapter.py

## Product Contract

Every creator correction must improve the current package and the future agent
system without creating another creative gate. The closed loop is:

```text
captured -> diagnosed -> applied -> evaluated -> learning_proposed
                                      |                 |
                                      |                 -> approved -> promoted
                                      |                 -> rejected
                                      -> retained as package evidence
```

The four creator/production locks remain concept, copy plus format, proof pixels
plus creator approval, and final package QA. Feedback capture, evaluation,
retrieval, tracing, and learning proposals run around those locks; they do not
add a fifth approval stop or delay ImageGen.

“Self-improving” means better retrieved examples, tested repairs, and explicitly
approved durable guidance in this repository. It does not retrain model weights
or silently convert every package preference into a global rule. Failed or
unverified lessons remain evidence/debt, not active instructions.

## Authority Map

| Concern | Authority | Enforcement |
| --- | --- | --- |
| Creative rules | `config/rules/` | Highest durable authority after the creator |
| Workflow route | `config/skill-systems.json` | `carousel_jam` owns final production |
| Exact correction | package `creator-correction.json` | v3 append-only `events` |
| Repair target | current package JSON | revise in place by default |
| Eval evidence | `evals/feedback-cases/` | deterministic, fail-closed |
| Retrieval source | correction and learning events | derived SQLite index is rebuildable |
| Durable change | learning proposal | creator approval before apply |
| Generation truth | `generation-state.json` | per-attempt receipt history |
| Pixel truth | candidate bytes plus bound QA | hashes, dimensions, decoded-pixel review |
| Optional telemetry | Langfuse mirror | redacted, disabled, nonblocking |

## Creator-Correction Schema

New writes use `creator-correction/v3`. Legacy shapes remain readable and are
normalized by the compatibility reader. An event contains its stable
`feedback_id`, timestamp, exact creator bytes and their SHA-256, kind, scope,
slide/asset binding where applicable, primary and secondary diagnoses, root
cause, desired behavior, change/preserve clauses, affected artifacts, repair
operations, action evidence, linked learning event, eval IDs or waiver,
lifecycle status, generation effect, and optional superseded event.

The stable ID is derived from package path, exact text, kind, scope, slides, and
asset binding. Retrying identical capture returns the same event. Changed
wording or scope appends another event. Supersession points backward and never
deletes history. Retrieval hides superseded guidance by default and prefers the
newer correction in the same scope.

Supported scopes are workflow, package, slide, asset, copy, and global.
Supported diagnosis families are concept/recognition, voice/copy, scene/action,
identity/reference, exact text/layout, dimensions/brandmark, instruction drift,
runtime/tool failure, and provenance/QA.

## Command and Repair Contract

Capture exact feedback before claiming it was implemented:

```bash
python scripts/carousel.py feedback PACKAGE --text 'EXACT TEXT' \
  --scope slide --slide 3 --kind correction \
  --primary-diagnosis scene_action \
  --must-change 'observable action' --must-preserve 'approved copy' \
  --affected-artifact slides.json \
  --repair-json '{"artifact":"slides.json","json_pointer":"/2/physical_action","value":"Aachu passes the mug; Zuv catches it and smiles."}'

python scripts/carousel.py revise PACKAGE --feedback-id fb-...
python scripts/carousel.py feedback-status PACKAGE
```

`revise` applies declared JSON-pointer replacements to the same package,
captures before/after hashes, reconciles generation fingerprints, and evaluates
the linked case. A manual repair is also accepted when the affected artifact's
current hash differs from the baseline captured with the event. With no repair
evidence, revise fails. A waiver is explicit, stored, and still preserves exact
feedback; it is not a false eval pass.

A concept rejection may justify a new package. Execution corrections stay in
their writable v3 package. Archived v2 packages use `create --successor-of`:
fresh feedback/event/eval identities point to immutable source provenance, and
no source receipt, QA, final, or approval is inherited.
Generated images are never edited in place by the feedback engine.

When an explicitly named successor replaces another successor that carries the
same live corrections, retire only the duplicate feedback lineage:

```bash
venv/bin/python scripts/agentic_os.py retire-successor-feedback \
  output/carousels/YYYY-MM-DD/duplicate-successor \
  --superseded-by output/carousels/YYYY-MM-DD/named-successor \
  --retired-by creator \
  --reason 'Exact reason this duplicate route is superseded.'
```

The command never guesses the active package. It validates that the named
target carries every live origin with the same exact-feedback hash, appends a
fingerprinted `successor-retirement/v1` audit record, and leaves event statuses,
generation state, receipts, media, and package history untouched. Health and
recall exclude a retired duplicate only while that lineage remains valid; a
missing target, changed hash, incomplete carry, or tampered retirement fails
closed and restores the package's feedback debt.

Repair pointers replace existing JSON slots only: no whole-document replacement,
negative array indices, missing paths, traversal, or symlinks. Declared values
are checked after repair and the untouched JSON projection must match the
captured baseline. A passing case records whether the original failure was
actually reproduced; only such a deterministic case is regression-promotable.
Stored results become stale if affected bytes, evaluator code/version, or the
verification contract change after evaluation. Hash-only legacy passes are
unverified. Assertion or derived-diagnosis revisions use the audited `revise`
API: immutable creator wording and original artifact baselines remain intact,
and previous contracts/results remain in history. Capture
and successful revise retries are idempotent; a partial failure remains visible
as unresolved debt rather than a success receipt.

## Learning Promotion Policy

Learning is proposal-only until the creator explicitly approves promotion.

An explicit creator instruction containing “always” or “never” can produce an
inactive learning proposal after its package eval passes. Other feedback needs
matching transferable behavior in two independent packages, with current passing
evaluation evidence for every supporting event. Matching diagnosis labels alone
are insufficient. Package facts and local preserve clauses cannot become global
rules. The proposal contains
the complete proposed content for the existing authoritative rule/skill/memory
file; it is not a placeholder and is not active.

Feedback-derived proposals cannot be applied autonomously from draft. The
creator can use `agentic_os.py approve-learning ... --approved-by creator...`
or explicitly approve and apply with `apply-learning --approved-by creator`.
Both record creator identity and time. `apply-learning` validates hashes,
snapshot the target, apply atomically, and move the feedback event to promoted.
Health fails any applied feedback-derived proposal lacking this approval.
Approval and application re-check evidence freshness. Declining a proposal sets
`learning_disposition: declined` while leaving the correction `evaluated` and
revisable; legacy `learning_declined` records are supported without making the
correction terminal.

## Codex-Native ImageGen Boundary

Codex directly invokes ImageGen. Repository code compiles prompts and returns
five attachment bindings: four actual identity references in named roles and
one canonical style board. Codex attaches those files, sends the exact compiled
prompt, ingests the fresh return, opens the decoded candidate pixels, writes QA
against those bytes, and completes approval/promotion. Prompt preparation alone
is incomplete.

For posts/carousels, the prompt contains the beat, physical action, relationship
proof, composition, setting, camera, watercolor-and-ink style, palette,
lighting, exact text in its `ON-IMAGE TEXT` block, native `1080x1440`, and tiny top-right
`@a.storyof.two`. Revisions include the active feedback event's `must_change`
and `must_preserve`. Story/Reel and square formats remain explicit-request-only.

Each slide's `attempt_history` stores boundary, exposed model, prompt hash,
reference manifest and hashes, slide/attempt, fresh returned source path/hash/
dimensions/time, all applicable per-slide feedback IDs, pixel-review status and QA hash,
approval, and promotion. State cannot advance from handoff without a return,
from ingest without hashes/dimensions, from review without hash-bound decoded
pixel QA, or to publish-ready without every selected slide promoted. Exact text,
identity, brandmark, or dimension failure blocks approval. A semantic premise
gets two attempts before scene/action rewrite.

New receipts bind a sorted `feedback_ids` array to both the candidate and state
history; a correction for another slide is excluded. The legacy scalar
`feedback_id` remains populated for a unique applicable correction, or an
explicitly selected applicable correction. Multiple corrections no longer lose
their provenance by collapsing to a null scalar. Ingest rejects an explicit ID
that applies to none of the selected slides. Existing receipts without the
array remain readable; they are never rewritten to invent historical evidence.
Receipt validation rejects a changed array just as it rejects changed source
or prompt hashes. No new creator step or generation gate is introduced.

## Eval and Observability Contract

Deterministic checks own correctness. Each new correction creates an executable
feedback case containing exact-text hash, artifact baselines, required changes,
preserved constraints, and later repair checks. `evals/runner.py feedback-case`
runs it directly.

DeepEval is an optional shadow adapter for prompt adherence, completion,
trajectory, image alignment/coherence, reference awareness, creator recognition,
and relationship proof. The runner sets `DEEPEVAL_DISABLE_DOTENV=1` and disables
SDK telemetry. `ASOT_DEEPEVAL_ENABLED=1` enables provider scoring;
`ASOT_DEEPEVAL_ALLOW_MEDIA=1` explicitly permits attached media in that optional
external evaluation. These settings never affect native ImageGen. Missing
package or evaluator credentials produce `not_run`, never pass. Model metrics
cannot gate until calibration contains at least 20 creator-reviewed outputs
from five packages and hard-fail disagreement is strictly below ten percent; even then
threshold promotion requires creator approval. Mechanical hashes, dimensions,
text, references, state, and brandmark always remain deterministic.
Calibration evidence must also bind `output_path` to an existing regular file
inside the declared `package_id`; the recorded SHA-256 must match its current
bytes. Missing, moved, or changed outputs are invalid rather than silently
contributing to the 20-output threshold.

Langfuse is disabled unless `ASOT_LANGFUSE_ENABLED=1`. Its allow-list includes
stable IDs, hashes, diagnoses, lifecycle states, and scalar eval scores. It
never includes identity images, raw stories, credentials, or unrestricted
prompts. Import produces only a captured candidate event. Network and SDK
errors are reported as nonblocking and do not change local results.

## Retrieval and Health

Article packages keep their existing `source-memory-brief.md` integration;
this correction lifecycle does not create another article memory authority.

The memory index expands correction documents into event-level records with
scope, time, diagnosis, supersession, and exact searchable evidence. FTS/BM25
is combined with scope and recency preference. Semantic similarity is optional
only when an existing embedder is available. The index is rebuilt by normal
search/recall commands and is never source truth. `config/rules/` remains above
all recalled memory.

Wiki health fails recent unsupported correction schemas, unresolved feedback
debt, resolved events without action/eval evidence, stale active generation
guidance, non-pointer working memory, advanced generation without receipts or
pixel QA, unapproved durable promotion, and disagreement about the Codex-owned
ImageGen boundary.

Maintenance commands remain outside the illustration hot path:

```bash
venv/bin/python scripts/agentic_os.py index-memory
venv/bin/python scripts/agentic_os.py search 'scope:slide identity correction'
venv/bin/python scripts/agentic_os.py health
venv/bin/python scripts/wiki_health.py --write --fix-index
```

## Implemented Acceptance Map

| Accepted ask | Existing integration and executable evidence |
| --- | --- |
| Exact feedback, diagnosis, in-place repair, lifecycle | `carousel_visual_storytelling.py`; `test_creator_feedback_loop.py` exercises capture, failed baseline, repair, preserved copy, repeat calls, illegal transitions, and real proposal promotion |
| Creator-operated commands unnecessary | `scripts/carousel.py` feedback/revise/status and both active carousel skills invoke the exception path for the creator |
| Actual ImageGen ownership and provenance | `codex_builtin_image_generation.py` and `carousel_generation_state.py`; public CLI lifecycle tests cover five bindings, returned source dimensions, pixel QA, final promotion, and receipt tampering |
| Future recall without a new memory service | `memory_index.py`; correction and linked learning-event supersession are both tested, including queries that match only obsolete words |
| Optional evaluators and observability | `evals/deepeval_adapter.py` and `pipeline/agentic/langfuse_mirror.py`; credential-free, SDK-interface, redaction, calibration, and nonblocking-failure tests |
| Historical corrections preserved | `scripts/backfill_creator_feedback.py`; metadata-only migration tests retain raw legacy JSON, exact feedback, media hashes, and live v3 debt |
| No extra illustration delay | Four locks unchanged; repeated palette measurements are cached by pixel-content hash and measurement parameters, never by filename or prior PASS |
| Real docs rather than scaffolds | Existing master plan, ordered plan, hot-path history, this specification, playbook, active skills, and semantic engineering/eval memory are reconciled |

Validation evidence is scoped. Synthetic assets certify orchestration, not actual
likeness or story quality. DeepEval SDK-interface tests use doubles and are not
live model scores; credentials are neither loaded implicitly nor requested for
ordinary production. Langfuse remains off. Previously committed working-memory
history is preserved in the existing September 4 session-health episode while
the active working file contains pointers only.

## Sprint Execution Backlog

The sprint boundaries below are delivery sequencing, not approval gates. The
illustration hot path keeps exactly these four existing locks:

1. concept lock;
2. copy plus format lock;
3. proof pixels plus creator approval;
4. final package QA.

There is no fifth feedback, eval, learning, style-rollout, or sprint approval
gate. Health checks and learning proposals run beside the hot path. The only
creator decision still required during production is the already-existing proof
approval and, separately, any explicit decision to promote a proposed durable
learning.

### Role distribution

| Role | Responsibility |
| --- | --- |
| Primary integrator | Owns lifecycle code, safe state changes, package generation, and final integration |
| Acceptance auditor | Independently proves feedback debt, eval freshness, learning safety, and pixel evidence |
| Integration verifier | Runs focused and full test/eval/benchmark suites and records exact results |
| Package readiness auditor | Reconciles package history, creator approvals/rejections, references, and the next legal state transition |

### Sprint 1A — Foundation truth and safe learning

Goal: make the implemented loop report reality before producing more images.

| Task | Owner | Dependencies | Required artifacts | Acceptance test | Status |
| --- | --- | --- | --- | --- | --- |
| S1.1 Preserve exact creator feedback as append-only v3 events, apply declared in-package JSON repairs, bind evals, and expose feedback/revise/status commands | Primary integrator | None | `creator-correction.json`, linked LearningEvent, feedback case/result, action hashes | Feedback lifecycle and CLI contract tests pass; retry remains idempotent | Implemented |
| S1.2 Version evaluator/verification contracts; expose audited assertion revision; unify health and learning-debt; carry source debt through verified successor provenance | Acceptance auditor | S1.1 | Fingerprinted eval cases, preserved contract/result history, common unresolved records | Old hash-only passes are stale; live orphan debt is visible; unrelated or cyclic provenance cannot hide it | Implemented; final integration verification below |
| S1.3 Restrict proposals to transferable behavior with current passing evidence across independent packages; revalidate at approval and apply | Primary integrator | S1.1 | Proposal eligibility and freshness checks | Stale support and package-specific preserve text cannot enter durable rules | Implemented; final integration verification below |
| S1.4 Separate proposal decline from correction resolution and retain legacy revision compatibility | Primary integrator | S1.3 | `learning_disposition`, decline receipt, CLI | Decline retains enforceable/revisable correction; retry converges after partial failure | Implemented; final integration verification below |
| S1.5 Decline the two unsafe Zuv-POV/flight drafts and retrofit their real storyboard evaluations | Primary integrator | S1.4 | Rejected proposals; two real versioned cases with exact-copy, narrator and flight assertions | Original creator text and baselines preserved; storyboard verification is distinguished from pending pixel QA | Implemented; final integration verification below |
| S1.7 Give adopted feedback fresh successor/event/eval IDs and preserve source provenance | Successor implementer | S1.1 | Fresh LearningEvents/cases; exact source text; source byte-integrity tests | Successor create → revise → eval passes; two successors cannot collide; approval-with-work and declined learning remain actionable | 43 successor CLI tests passed |
| S1.8 Project slide-specific change/preserve clauses independently | Primary integrator | S1.1 | Updated prompt constraint projection | Slide 5 instructions do not reach slide 6; global preservation remains active; approval-with-work stays visible | Implemented; final integration verification below |
| S1.6 Re-run focused feedback, health, learning, CLI, memory-index, and migration tests | Integration verifier | S1.2–S1.5 | Test results and current health/debt records | All focused suites pass and health reports every remaining live item explicitly | Passed: full suite 774 passed / 2 skipped / 1 subtest; final focused suite 127 passed; 728 baseline media files unchanged |

Sprint 1A exits only when health is truthful. It does not require a green health
result while the three known carousel packages still contain legitimate,
unresolved creator work.

### Sprint 1B — Researched integration acceptance

These tasks were missing from the earlier sprint table. They are explicit
acceptance work, with configured live service evidence distinguished from local
SDK tests. They add no illustration lock.

| Task | Owner | Acceptance evidence | Status |
| --- | --- | --- | --- |
| S1B.1 DeepEval SDK adapter and runner | Integration implementer | Installed SDK smoke, missing-key/import/provider failure paths, actual image/reference/trajectory inputs, dotenv and telemetry disabled | Local acceptance passed, including actual offline metric construction and multimodal input conversion; authenticated scoring pending evaluator credentials |
| S1B.2 Calibration evidence validation | Integration implementer | At least 20 distinct creator-reviewed outputs from five packages; strictly below 10% hard-fail disagreement; reject malformed/conflicting evidence | Validator implemented; real corpus has 0 reviews and 0 packages, so calibration remains open |
| S1B.3 Langfuse metadata mirror | Integration implementer | Redacted allowlist, real SDK interface smoke, disabled/missing/outage paths; no raw creator text or identity references exported | Local acceptance passed; configured live round trip pending credentials |
| S1B.4 Annotation import | Primary integrator | `import-feedback-annotations` persists deduplicated local candidates from annotation exports; retry/dry-run tested; exact comment retained | Implemented; candidates require local diagnosis before creator-feedback capture |
| S1B.5 Internal Mem0-inspired retrieval | Retrieval implementer | BM25/lexical search, recency/scope ordering, strict `package:` isolation, supersession before limit, canonical/event deduplication | 13 memory tests and real-repo package query passed; imported candidates excluded from active guidance; Mem0 dependency intentionally absent |
| S1B.6 Codex ImageGen boundary | Integration verifier | Existing prompt/reference → ingest → pixel QA → promotion lifecycle tests; no SDK mirror can certify an image | Passed in full suite and 215-test focused boundary/workflow run; these tests use synthetic images and do not certify production art |
| S1B.7 Rejected alternatives | Primary integrator | Keep Promptfoo and Phoenix recorded as non-goals; no second runtime or observability deployment | Intentional non-adoption retained |

`agentic_os.py feedback-integrations` reports installation, credential presence,
enablement, and calibration counts without printing secrets. On this workspace
both optional SDKs remain absent from the base project interpreter. The isolated
`.venv-evals` runtime now contains the tested SDKs and passes their real offline
smoke checks (September 12). Credentials and enablement remain absent; live
provider acceptance is `not_run`. An installed SDK runtime is not a configured
production service and must never be reported as one.
`make feedback-integrations-setup` is the explicit local opt-in: it installs the
tested `deepeval==4.2.1` and `langfuse==4.15.1` pins under `.venv-evals`, never
into the project interpreter. It then runs
only offline SDK contract smoke; provider scoring and tracing remain disabled
until their separate enable flags and process credentials are present.
When Langfuse is explicitly enabled, the project interpreter passes only the
allow-listed payload over stdin to a `.venv-evals` worker. The worker validates
the payload again, performs the flush, and is bounded by a ten-second parent
timeout. It does not use the former daemon-thread delivery path, so a quick CLI
exit cannot silently abandon an in-process export.

### September 5 Sprint 1 acceptance receipt

Sprint 1A code acceptance is complete. Sprint 1B local adapter acceptance is
complete; live provider and real calibration acceptance remain open. The full
Sprint 1 is therefore not represented as fully closed.

- Full repo test run: `venv/bin/python -m pytest --import-mode=importlib tests -q`
  returned 774 passed, 2 skipped and 1 subtest passed in 113.20 seconds.
- Final focused run after the last event-contract/CLI fixes: 127 passed in
  15.13 seconds. It covered feedback freshness/lifecycle, successor CLI,
  annotation imports, optional integrations, learning promotion, and recall.
- The existing 21-task eval registry validates with zero issues. Diff whitespace
  checks pass. All 728 original migration media paths retain their SHA-256.
- Lived's two real storyboard cases pass 17 and 14 explicit assertions and are
  current against the final evaluator. Their old evaluations/baselines remain
  preserved; `regression_promotable` is false and pixel/final acceptance remains
  pending. The old proof is historical after changed inputs.
- The pre-closeout Agentic OS health and learning-debt snapshot agreed on seven
  current repair events. Six source events were carried into the concurrently created
  `output/carousels/2026-09-05/forever-was-many-small-choices-theme-rebuild`;
  Conversation's repair remained on its archived source. Further successor work
  continued concurrently during final checks, so the current diagnostic rather
  than this snapshot is authoritative for the open count. This records live state,
  not a claim that this sprint generated or approved the successor's art.
- Wiki health reports `NEEDS_HEAL` for open creator repairs. Six existing
  taxonomy-only diagnoses across the two concurrently created Forever successors
  were replaced with concrete explanations from their source feedback; exact
  wording and generation constraints stayed unchanged. Future adoptions now
  derive an explicit cause summary rather than copying the taxonomy label. There are no
  receipt-integrity or missing-learning-approval failures. One separate analysis
  learning event remains proposal debt and was preserved.
- The scoped autopublish dry run was rejected by the session's automatic
  approval policy (`AskForApproval=Never`). No commit or push was made.

To finish Sprint 1B, provide process credentials for the installed optional SDKs, verify
one redacted Langfuse round trip, run real DeepEval scoring, and collect 20 actual
creator-reviewed outputs spanning five packages with strictly below 10%
disagreement. These are external integration acceptance tasks and do not delay
the native illustration hot path or introduce another approval lock.

### Sprint 2 — Production proof recovery

Goal: turn every live correction into an honest v3 production route, then use
the normal riskiest-slide proof lock. No v2 final is relabelled as a v3 receipt.

| Task | Owner | Dependencies | Required artifacts | Acceptance test | Status |
| --- | --- | --- | --- | --- | --- |
| S2.1 Reconcile the three package histories, exact feedback, prior pixel decisions, identity/style bindings, and the next legal commands | Package readiness auditor | S1 truthful health | Readiness findings in the existing package/diagnostic surfaces | Every preserved approval and rejection is traceable to exact evidence; no invented provenance | Audited: Lived recovered; Forever remains owned by its active creative task; Conversation has an explicit old-pixels/current-style choice pending |
| S2.2 Repair `i-have-lived-so-many-years-without-you` as the current v3 package: retain Zuv's point of view, replace the train bookends with commercial-flight travel, preserve the exact ten-slide copy and other approved scenes | Primary integrator | S2.1 | Updated slides/prompts/state plus fresh riskiest-slide ImageGen receipt | Current feedback cases are fresh and pass; proof is native `1080x1440`, uses four identity references plus one style board, and passes decoded-pixel QA | Flight proof passed; current production changes require flight-feedback evaluation refresh before final acceptance |
| S2.3 Present that flight-bookend proof for the existing creator proof decision | Primary integrator | S2.2 | One hash-bound proof candidate and QA record | Creator approval/rejection is recorded against the exact candidate bytes; no additional approval request is inserted | Explicit creator approval recorded September 12; active task continues the batch |
| S2.4 Create an honest v3 successor for `forever-was-many-small-choices-15`, preserving the corrected slide 5 requirement and the creator-approved slide 6 umbrella-after-an-argument premise | Create forever carousel task | S2.1 | Successor package, lineage, fresh prompts/state, riskiest-slide receipt | Extra hand/furniture-box anatomy is absent; slide 6 reads as the approved umbrella action with simple visible hands; all evidence is bound to returned pixels | Active successor is theme-rebuild-10; seven replacement slides are being generated while retaining approved umbrella slide 6; not final |
| S2.5 Create an honest v3 successor for `the-conversation-follows-us`, preserving only the creator-approved slide 3 visual facts and rejecting the misleading doorway-body/hand construction | Primary integrator | S2.1 | Successor package, lineage, fresh prompts/state, riskiest-slide receipt | Slide 4 has spatially traceable bodies and limbs; no unapproved legacy candidate is promoted | Pending |
| S2.6 Re-evaluate every linked correction after package changes | Acceptance auditor | S2.2, S2.4, S2.5 | Fresh feedback-case results with current artifact hashes | No stale eval, hidden orphan, false pass, or waived visual failure remains | Pending |

The first real production proof that passes deterministic and decoded-pixel
review may also supply the existing style-smoke acceptance evidence. This reuses
work already needed for the carousel; it does not add a style gate or another
ImageGen attempt.

#### September 5 production continuation receipt

- Actual native ImageGen was invoked three times for Lived slide 6, each with
  the same four verified photographs and one package-bound active style board.
  The first two returns failed hand-role/accessory integrity; neither was
  approved. Their source bytes, normalized pixels, prompts and QA remain in
  the existing superseded archive. No rejected image became a reference.
- The replacement premise removes overlapping forearm-touch/paper-grip
  choreography: Zuv points with one hand while his other rests on his thigh;
  Aachu has set the itinerary down and looks out with both hands resting.
  All ten copy lines, Zuv POV, flight bookend and remaining scenes are retained.
- The current normalized proof is
  `output/carousels/2026-09-04/i-have-lived-so-many-years-without-you/.internal/visual-quarantine/slide-06/attempt-01/instagram_post.png`,
  SHA-256 `8dbed82a9cfa4e709d8f1f61979442c43d810e486e13c9f80b87604392a4bda1`.
  Its `proof-qa.json` records full-frame, person/seat and individual-hand crop
  observations, exact text, identity/accessories and palette evidence. One
  harmless resting fingertip overlap with the itinerary is documented rather
  than concealed. Source `1086x1448` was proportionally downsampled once to
  `1080x1440`; no crop, padding, upscale or extra format was delivered.
- State is `awaiting_creator_proof_approval`, with proof-set binding
  `sha256:fd97f9df1511889b4f5442be3a3ee65e730e3dd65ceb2aa7752416eea628f25a`.
  There is no creator approval, final deck, batch generation or publishing claim.
- Real execution exposed and fixed relative package-root duplication at ingest.
  It also exposed retry-budget reset on cosmetic prompt edits. Existing state
  now retains the two-attempt allowance across presentation-only edits and
  resets it for a changed structured physical action. Old v3 state uses the
  previous compiled scene when available and otherwise preserves the budget
  conservatively. This changes no creator gate and adds no CLI parameter.
- Conversation slide 4 still needs compacting (1,106 words before repair).
  Its imported preserve instruction names approved slide-3 **bytes**, bound to
  an older style board. A current-style regeneration cannot also be byte-identical.
  The creator has been asked to retain those original pixels or regenerate the
  same copy/scene in the current style; no exception or approval is invented.
- The optional integrations remain disabled/unconfigured, with zero real
  calibration reviews. They do not block native generation. The latest health
  diagnostic remains authoritative as the separate Forever task creates or
  revises its successors; this task has not silently resolved their feedback.

### Sprint 3 — Batch generation and final QA

Goal: complete the approved routes as real carousel packages, not prompt packs
or empty document shells.

| Task | Owner | Dependencies | Required artifacts | Acceptance test | Status |
| --- | --- | --- | --- | --- | --- |
| S3.1 Generate the remaining selected slides after each package's existing proof approval | Primary integrator | S2 proof approval for that package | Fresh source returns, ingested candidates, per-attempt receipts | Each selected slide records prompt/reference/source hashes and native dimensions; no generated image is silently reused | Pending |
| S3.2 Review actual pixels slide by slide in story, cinematic, spatial/anatomy, identity, exact-text/brand/style/dimension order | Acceptance auditor | S3.1 | Hash-bound visual-QA records | Hard failures cannot be approved; a repeated semantic premise is rewritten after two failed attempts | Pending |
| S3.3 Promote approved candidates and build final packages | Primary integrator | S3.2 | `final/` media, manifest, visual QA, final audit | Every selected slide is promoted from a reviewed receipt; exact copy, tiny top-right brandmark, identity/style references, and `1080x1440` all pass | Pending |
| S3.4 Run package doctor and feedback-status across all repaired/successor packages | Package readiness auditor | S3.3 | Doctor/status output in existing diagnostics | No selected slide, live correction, receipt, QA hash, or final audit is missing | Pending |
| S3.5 Run regression and public lifecycle benchmark | Integration verifier | S3.3 | Existing eval/benchmark outputs | Feedback regressions, generation lifecycle, 21-task eval registry, and unchanged performance budget pass | Pending |

Story/Reel `1080x1920` and square `1080x1080` derivatives are out of scope unless
the creator explicitly requests them. Their absence is not a Sprint 3 failure.

### Sprint 4 — Repository closeout

Goal: prove the repo is coherent and publish only scoped implementation work.

| Task | Owner | Dependencies | Required artifacts | Acceptance test | Status |
| --- | --- | --- | --- | --- | --- |
| S4.1 Re-run media migration integrity against the preserved baseline | Acceptance auditor | S3 complete | Updated existing migration diagnostic | Every pre-existing media hash is unchanged; additions are enumerated, never mistaken for mutations | Pending |
| S4.2 Run full tests, 21-task eval validation/review, lifecycle benchmark, `git diff --check`, Agentic OS health, and wiki health | Integration verifier | S4.1 | Existing test/eval/health outputs | All executable checks pass, or any external-only limitation is named without claiming completion | Pending |
| S4.3 Reconcile this specification and existing playbook/memory surfaces with final evidence | Primary integrator | S4.2 | Updated existing documents only | Status, counts, package paths, and remaining human decisions match the executable state | Pending |
| S4.4 Perform a scoped closeout that excludes unrelated human and generated worktree changes | Primary integrator | S4.3 | Scoped dry-run/publish evidence | Included paths are explicit; no unrelated path is staged, committed, or pushed | Pending; an earlier dry-run was denied while approvals were unavailable |

## Current Evidence and Open Work

The September 4 baseline is real but does not certify the open production work:
`python -m pytest --import-mode=importlib tests -q` passed 594 tests, skipped two,
and passed one subtest; the 21-task registry validation/review passed; the
synthetic public lifecycle benchmark completed in 7.66 seconds against the
10-second budget; and `git diff --check` passed. These checks certify the tested
orchestration surface, not current illustration quality or repair completion.

The migration's own 728-file before/after hash maps still match in
`output/diagnostics/creator-feedback-backfill.json`. The earlier 723-file
snapshot also remained unchanged while five concurrently created files were
added. These are integrity facts, not a claim that package recovery is done.

Current live work is broader than the single event previously reported:

- `forever-was-many-small-choices-15` has unresolved slide 5 anatomy and slide 6
  story/readability evidence, including a later creator-approved umbrella route.
- `the-conversation-follows-us` has a rejected slide 4 doorway-body/hand
  construction; only slide 3 carries prior creator-approved visual evidence.
- `i-have-lived-so-many-years-without-you` has a real native slide-6 flight proof
  with current pixel QA and an explicitly applied September 12 creator approval.
  It is `batch_ready`, not final; its active production task owns the remaining
  slides. A subsequent flight-feedback evaluation/source-input drift remains
  visible in health and must be repaired by that owner before final acceptance.
- the two unsafe story-specific learning proposals are rejected with decline
  receipts; their corrections remain revisable and their real storyboard
  evaluations now use explicit assertions. This does not certify generated art.
- the style smoke report is blocked because its prior sofa proof contained an
  extra hand and its explicit Reel-wide sources were undersized. It can be
  resolved from successful production evidence without adding a gate.

Until Sprints 1–4 meet their acceptance tests, this implementation is not
complete. The generated flight proof and its explicitly recorded approval are
real; no complete final package, green health result, scoped commit, or push is
claimed here.

### September 12 implementation and acceptance continuation

This continuation fixes executable behavior in existing modules rather than
adding a parallel plan or template. Its verification must be read separately
from the historical September 4/5 results above.

- Feedback assertion revision recovers a case-first partial commit: an identical
  retry resynchronizes the correction without duplicating version history.
  Removing repair action or resolution evidence invalidates an old eval PASS.
- `carousel.py status` and `feedback-status` are observational. They report
  input drift without writing state, archiving evidence, or retracting an
  approval. `prepare` remains the explicit existing reconciliation path.
- Per-slide generation receipts retain every applicable correction ID in both
  candidate and attempt history. Cross-slide IDs are rejected; old receipts
  remain readable without invented backfilled provenance.
- Real legacy feedback schema families (`1.0`, unversioned corrections, and
  `creator-correction/v1`) have exact-wording, raw-payload preservation, and
  byte-idempotence regression tests.
- Generic creator-feedback captures default to package-local pending linkage
  until attached to a canonical package correction. Existing unlinked records
  remain unchanged and visible as `feedback_linkage` debt, rather than being
  misrepresented as obligations to create global policy proposals. Explicit
  durable learning still uses the existing approval path.
- Text QA now rejects a reported extra-lettering inventory as well as wrong,
  missing, reordered, or extra copy words. The canonical rule accurately names
  decoded-image transcription as the perception boundary and exact comparison
  as the deterministic check; it does not pretend an absent OCR backend ran.
  This stays inside the existing proof/final check and changes no compiled
  prompts or approved image bytes.
- `make feedback-integrations-setup` actually completed in `.venv-evals`:
  DeepEval `4.2.1` real offline metric construction/multimodal token smoke PASS;
  Langfuse `4.15.1` installed import/signature smoke PASS. The first real setup
  exposed eager production-image imports in the evaluator CLI; lazy imports
  now let the isolated SDK runtime execute without base imaging dependencies.
  Evaluator workspace baselines exclude this installed runtime.
- The service boundary is still explicit: enable flags false, evaluator and
  Langfuse credentials absent, external media disabled, dotenv/telemetry
  disabled, external calls `not_run`. Calibration has 0 valid reviewed outputs
  across 0 packages, versus required 20/5 and strictly less than 10% hard-fail
  disagreement. Calibration now binds each review to existing package output
  bytes with matching SHA-256; synthetic records cannot satisfy acceptance.
- All 728 original migration media files were rehashed on September 12 against
  both saved before/after maps: zero missing or changed files.
- The Forever production owner explicitly identified `theme-rebuild-10` as
  active and `theme-rebuild` through `theme-rebuild-9` as abandoned setup
  attempts. All nine now have validated retirement lineage to the active
  target, without marking their corrections repaired. Health/recall use the
  carried active corrections instead of counting nine duplicate sets. The
  September 12 post-retirement snapshot is 11 repair items plus 5 linkage
  items; receipt-integrity and missing-learning-approval failures are empty.
  Health remains `FAIL`, correctly, rather than hiding those 16 open items.

Production acceptance remains separate. Lived and Forever are actively owned
by their respective creative tasks, so this engineering continuation does not
generate competing images or overwrite their state. Conversation still needs a
v3 successor and an explicit decision about retaining historically approved
slide-3 bytes versus regenerating under the current style. Optional live
scoring/tracing needs credentials and genuine human calibration, not fabricated
reviews. These are open acceptance items, not completed implementations.
