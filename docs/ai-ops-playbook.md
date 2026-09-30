# AI Ops Playbook

last_updated: 2026-09-04
confidence: 0.95
sources:
- AGENTS.md
- memory/semantic/engineering-workflow-preferences.md
- memory/semantic/carousel-idea-preferences.md
- scripts/carousel.py
- scripts/analyze_prepost.py
- scripts/create_substack_article_package.py
- scripts/wiki_health.py
- scripts/autopublish.py

## Purpose

Use the terminal as an English-operated command surface for @a.storyof.two.
The goal is to reduce repeated manual work: Codex can inspect repo state,
choose the right existing workflow, run it, verify the result, and leave a
reviewable package state.

## Daily Loop

1. Run `make brief`.
2. Pick one lane: Reel pre-post, carousel jam, article package, or infra health.
3. Run the matching Make target.
4. Check current package state and actual generated pixels before treating the
   work as done.

`make health` is a repository-maintenance/closeout command. An ordinary
carousel run never invokes it and never writes wiki, memory, rules, tests, or
diagnostics.

## Context selection

`venv/bin/python scripts/agentic_os.py context --render` loads the compact
`ideation` profile for idea discussion and recall. Before illustration work,
select `--profile a-story-of-two` for the complete production rules, runtime,
and identity guidance. For article work, select `--profile article`.

Budgets are deterministic character-based estimates (characters / 4), not
model tokenizer counts, and cover section content rather than rendering
metadata. All required sections must fit in full; otherwise assembly fails
with the required size and source paths. Optional excerpts use only the space
left after reserving every required section. Large preference history is
retrieved as needed through the working-memory pointers, not loaded wholesale
into the article or ideation profile.

## Command Surface

`make brief`

Leads with saved own-channel evidence: collection date, publication coverage,
metric availability, three descriptive observations, and one proposed content
experiment when there are at least three comparable posts. Snapshots older than
14 days are labeled historical. The brief uses raw source counts so unavailable
metrics remain unavailable; it never treats a new report date as fresh data.

The comparison window is posts aged 7–60 days at collection, grouped by format.
These remain cumulative counts, not matched-age results or proof of a winning
hook. A sparse, missing, invalid, or future-dated latest snapshot reports the
data gap instead of inventing an experiment. The brief performs no scraping,
scheduling, publishing, or maintenance writes.

Use `venv/bin/python scripts/daily_creator_brief.py --maintenance` to also show
recent packages, workflow commands, hypotheses, and learning debt. The default
brief includes only a compact pointer to the latest saved health report.

`make analyze`

`make analyze` defaults to carousels. `--all-formats` on the A3 CLI is an
explicit opt-in for Reel and single-image comparisons. `make brief` also
defaults to carousels and surfaces validated local visual observations first.

Before a new content decision, `make analyze` writes both a human-readable
performance report and a JSON evidence file in `output/reports/`. It selects
the newest dated own-channel snapshot and prefers raw data over normalized
data from the same date. Raw counts are normalized in memory; corpus files
are not changed. A corrupt newest snapshot fails instead of falling back.

Comparisons stay within the same format and publication-age band (7–13,
14–29, or 30–60 days at collection). A metric needs five observed posts and
80% cohort coverage. The report shows higher and lower tails, including ties,
with post links and exact caption excerpts. Its metric priority is declared
in the companion JSON; tied primary metrics are not replaced to seek a more
dramatic contrast. Missing values remain unavailable, including ambiguous
zeros from legacy normalized files. Reach-based rates require paired counts
and positive reach; shares/sends and views/plays stay separate.

Evidence quality is shown through sample size, coverage, collection date,
and source hash rather than a fixed confidence score. Caption metadata is
descriptive; captions do not substitute for the carousel artwork. Inspect
`corpus/media/<shortcode>/slide-*` and its ordered on-image text with
`view_image` before concluding that visual evidence is unavailable. Review
the cover, new evidence per swipe, text/image agreement, scene variety, turn,
payoff and plausible send reason. The supplied local archive requires no
download. Generated drafts may inform a separate craft review, but must not
be assumed to be the published slides.

Save those observed readings in
`output/reports/carousel-visual-evidence.json`, bound to each actual image
path, SHA-256, dimensions and slide number. Explicitly identify a contact-sheet
panel when it is the only local evidence for a slide. `make analyze` checks
these bindings and renders the observations beside the carousel metrics; it
does not claim to run new vision inspection. New or changed slides need a new
Codex pixel review. Missing slides and stale reviews remain visible, and
partial sequences must not be presented as fully reviewed.
The default 14-day freshness label is a workflow threshold, not a claim about
the platform. No scrape, publication, memory update, or rule change occurs.

For a custom source, use `venv/bin/python -m pipeline.stages.a3_analyzer
--posts-path PATH --collected-on YYYY-MM-DD`. Supply the actual collection
date, not today's report date. The existing A-layer runner still supports
`venv/bin/python -m pipeline.runner --stage a3`.

`make jam MOMENT="one specific couple moment"`

Prepares a small carousel jam from the supplied moment. Deep research and the
multi-agent Instagram idea loop are explicit opt-ins, never default preflight.

`make prepost CONCEPT="planned Reel concept"`

Runs the three-call, five-facet pre-post analysis and returns POST / REVISE /
REWORK / KILL.
Optional variables: `HOOK`, `CAPTION`, `EDIT`, `AUDIO`, `COVER`.

The runtime makes one combined five-facet analysis call, one independent
challenge call, and one synthesis call. The old five-specialist dispatch is
retired; the five facet names remain scoring labels rather than agent roles.

`venv/bin/python scripts/agentic_os.py knowledge-workflow EVENT.json --execute-compile`

Routes a bounded evidence event to the read-only evidence reviewer, adds the
contradiction reviewer only when the packet needs it, and invokes A4 as the
single wiki writer. A retrieval invalidation receipt is emitted only after the
compiler receipt and current output hashes verify.

`make carousel STORY="source story" CREATIVE_BRIEF="locked-brief.json" TITLE="optional title"`

Creates the minimal v3 package and, when the creative brief contains locked
physical actions, prepares the selected risky proof. Story-only input remains
`draft` and makes no generation call. Optional variables include `STORY_FILE`,
`STORY_IMAGES`, `IDENTITY_IMAGES`, `FORMATS`, `OUTPUT_ROOT`, and `PROOF_SLIDE`.
The style prompt and style board are not CLI inputs: the pipeline resolves and
hash-verifies the one active profile in `config/carousel_style_contract.json`.

The canonical image-production lifecycle is exactly six commands:

```bash
python scripts/carousel.py create ... --prepare-proof --proof-slide 3
python scripts/carousel.py ingest PACKAGE --instagram-post returned-proof.png --proof-slide 3
python scripts/carousel.py review PACKAGE --qa authored-proof-qa.json
python scripts/carousel.py approve PACKAGE --proof-sha256 sha256:<bound-proof-hash>
python scripts/carousel.py ingest PACKAGE --instagram-post slide-01.png --instagram-post slide-02.png  # repeat in selected-slide order
python scripts/carousel.py review PACKAGE --qa authored-final-qa.json
```

Approval automatically prepares the remaining-slide batch. A passing final
review automatically audits and finalizes the complete deck. `status PACKAGE`
is a diagnostic read, not a seventh production command.

Every command returns versioned JSON with `package_dir`, `state`,
`next_action`, selected slides, and selected formats. Invalid/blocked input is
nonzero; `awaiting_creator_proof_approval` is a successful pause.

When the creator gives a correction, Codex must capture it before claiming the
change is implemented:

```bash
python scripts/carousel.py feedback PACKAGE --text 'EXACT TEXT' --scope slide \
  --slide 3 --kind correction --primary-diagnosis scene_action \
  --must-change 'the corrected visible behavior' \
  --must-preserve 'the approved copy and unaffected slides' \
  --affected-artifact slides.json \
  --repair-json '{"artifact":"slides.json","json_pointer":"/2/physical_action","value":"the corrected physical action"}'
python scripts/carousel.py revise PACKAGE --feedback-id fb-...
python scripts/carousel.py feedback-status PACKAGE
```

Capture writes one idempotent `creator-correction/v3` event, its diagnosis,
eval case, and linked `LearningEvent`. `revise` updates the same package,
records before/after artifact hashes, runs the deterministic regression, and
reconciles only stale generation evidence. This lifecycle is internal evidence,
not another creator-facing production gate. A new package is reserved for a
rejected concept, not an execution correction.

At `handoff_ready`, Codex directly invokes ImageGen: it reads the selected compiled prompt, attaches the
identity dossier's exact four-file Aachu/Zuv/together bundle plus the single
package-bound canonical style contact sheet,
calls ImageGen only for selected slides, ingests each returned file with the
tool-reported model and triggering feedback ID when available,
opens the decoded pixels with `view_image`, and submits hash/dimension-bound
QA. Each attempt is persisted inside `generation-state.json` with the prompt,
five reference hashes, returned source path/hash/dimensions/time, review QA
hash, approval, and promotion state. If generation or pixel viewing is unavailable, report
`handoff_ready: BLOCKED/NOT_RUN`; never claim a PASS.

Ingest automatically records every applicable correction in per-slide
`feedback_ids`; the optional scalar trigger must belong to the selected slide
set. A correction for another slide never becomes generation provenance.
`status` and `feedback-status` are read-only even when inputs drift. Use the
existing `prepare` command when you actually intend to reconcile/recompile;
checking progress must not archive a candidate or revoke an approval.

Inside the existing pixel QA finish check, transcribe actual visible copy after
opening the decoded image, not from the expected prompt. New reviews also
record `unexpected_visible_text: []` after inspecting the whole frame; reported
extra lettering fails that same check. Legacy hash-bound reviews remain
readable. Exact comparison validates the transcription; it is not a claim that
an independent OCR backend inspected the raster.

Relative package paths are accepted by ingest and resolved once before any
quarantine write. Presentation-only edits (camera wording, wardrobe, copy or
hand-detail prose) invalidate stale pixels but do not reset the existing
two-attempt allowance. Reset requires a changed structured scene-action
binding. Earlier images, source returns, prompts and QA stay in the existing
superseded archive. Old v3 packages infer their previous scene from the compiled
handoff when available; uncertainty preserves the allowance already used.
No additional creator gate or command is needed.

That five-file attachment set is the boundary observed in the current built-in
Codex runtime smoke, not a claim about a documented platform limit. Do not add
the three individual style slides on top of the style board or silently omit an
identity file.

Prompts still request exact `1080x1440; native 3:4` for posts. As an observed
built-in-runtime accommodation, repo ingest may quarantine an untouched exact
3:4 post source from 1080x1440 through 1440x1920 inclusive, retain its source
hash/dimensions, and downsample once proportionally to exact 1080x1440. Crop,
pad, stretch, upscale, wrong-ratio input, and a second resample are blocked;
Story/Reel and square remain exact-source only. Approved normalized proof bytes
are reused as the final candidate.

For repository validation—not an ordinary carousel run—use
`python scripts/benchmark_carousel.py --runs 3 --json`. It exercises the public
CLI with temporary synthetic images and reports timing, RSS, and package
overhead; it explicitly does not claim the images passed real vision review.

Learning proposals, evaluation, memory indexing, search/recall refresh, wiki
health, and Agentic OS health remain maintenance operations outside the
illustration hot path. Search automatically rebuilds the derived event-level
index and prefers current, scope-matched, non-superseded corrections. DeepEval
may run only as an optional shadow judge and reports `not_run` without explicit
credentials. The optional Langfuse mirror is disabled by default, redacts raw
prompts/stories/images, and cannot block local work. Durable changes to rules,
skills, or semantic memory require explicit creator approval: either
`approve-learning --approved-by creator` followed by `apply-learning`, or one
`apply-learning --approved-by creator` action after the creator approves the
proposed diff. An agent must never invent that approval.

Sprint 1 adds executable maintenance commands to the same workflow:

```bash
make feedback-integrations
# Explicit opt-in; installs pinned SDKs only in .venv-evals.
make feedback-integrations-setup
venv/bin/python scripts/agentic_os.py feedback-integrations
venv/bin/python scripts/agentic_os.py search 'package:output/carousels/2026-09-04/i-have-lived-so-many-years-without-you flight'
venv/bin/python scripts/agentic_os.py import-feedback-annotations /absolute/path/to/langfuse-annotations.json --dry-run
venv/bin/python scripts/agentic_os.py import-feedback-annotations /absolute/path/to/langfuse-annotations.json
```

The import accepts Langfuse `source: ANNOTATION` score exports in an array or
`data` array, retains exact comments, and deduplicates annotation IDs. It saves
`langfuse_annotation_candidate` LearningEvents for local review. It does not
turn an external comment into creator approval or a rule change. Credentials
and SDK availability are reported as booleans/version strings; secrets are not
printed. DeepEval and Langfuse remain optional and disabled by default.
The setup target does not enable either adapter, use credentials, or call a
provider. It only prepares the isolated SDK runtime and runs its offline
constructor/signature smoke. `make feedback-integrations` automatically uses
that isolated runtime when present. The normal carousel interpreter keeps the
SDK isolated: enabled feedback mirroring launches a stdin-only worker under
`.venv-evals`, revalidates the redacted allow-list in the worker, flushes there,
and waits for at most ten seconds. Timeout, SDK, authentication, and provider
failures remain nonblocking and never expose worker output or raw creator text.

Use `carousel.py revise --assertion-json` with a `--reason` to replace an old
hash-only evaluation contract. Each JSON object specifies `artifact`,
`json_pointer`, `operator` (`equals` or `contains`), and `value`. The same command
accepts revised `--must-change`, `--must-preserve`, or `--primary-diagnosis` when
later feedback changes derived guidance. Original creator wording, artifact
baselines, and prior verification results remain in history. A storyboard
assertion pass does not certify generated pixels. `feedback-status` rejects
stale evaluator or artifact evidence; health and learning-debt share the same
unresolved feedback list.

Declining global promotion keeps the package correction revisable with
`learning_disposition: declined`. Successful successor creation carries live
feedback into fresh event/eval identities while retaining source provenance.
Slide-specific change clauses are projected separately from global preservation
clauses, keeping correction text from contaminating unrelated prompts.

`make article CAROUSEL=output/carousels/YYYY-MM-DD/slug TITLE="optional title"`

Creates a gated Substack article package from a carousel package.

`make health NOTE="what changed"`

Runs wiki/memory health with write and index repair enabled. This is the
session-close gate for substantial work.

`make publish NOTE="what changed" INCLUDE="path1 path2"`

Runs the safe closeout gate: inspect changed paths, block risky media/secrets,
run tests, run wiki health, commit, and push. Use `INCLUDE` when the worktree
contains changes outside the current session. Use `make publish-dry-run` first
when scope is unclear.

## Good English Prompts For Codex

Use these when you want the agent, not your memory, to drive the terminal.

```text
Run make brief, inspect the suggested next commands, and tell me what is most
important today.
```

```text
Take this Reel idea through pre-post analysis. If it is REVISE or worse, tell
me the smallest fix that would make it postable.
```

```text
Prepare a carousel jam from this moment. Read the idea-preference ledger first
and do not repeat cooled-down lanes.
```

```text
Create the article package for this carousel, then inspect editorial gates and
tell me what is still not publish-ready.
```

```text
Run health. If the wiki reports NEEDS_HEAL, treat that as a blocker and fix or
name the exact next-session repair.
```

## Operating Rules

- Prefer the Make target over remembering long script invocations.
- Do not bypass health when work touches memory, wiki, core scripts, or
  pipeline contracts.
- Do not publish a mixed worktree without either inspecting every changed path
  or passing explicit `INCLUDE` paths to the safe publish gate.
- Do not call a carousel done unless state is `publish_ready`, the requested
  native files have passed actual-pixel QA, and final manifest/audit bindings
  match. Default output is only 1080x1440; Story/Reel and square exist only when
  explicitly requested.
- Do not use this layer to weaken the existing C-layer or D-layer gates. It is
  a command surface, not a replacement for the creative rules.
- Keep new automation boring and inspectable: small scripts, visible commands,
  no hidden network dependency.
- Use only `draft`, `blocked`, `handoff_ready`, `proof_qa_required`,
  `proof_failed`, `awaiting_creator_proof_approval`, `batch_ready`,
  `final_qa_required`, `final_qa_failed`, and `publish_ready` for public
  carousel state.
