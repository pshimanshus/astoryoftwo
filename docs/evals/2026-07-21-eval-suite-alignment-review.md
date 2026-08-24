# Eval Suite Alignment Review

review_date: 2026-07-25
scope: registry snapshot of 22 tasks plus all shared eval documentation and harness surfaces
protocol: single pass, registry order, no retries, no recursive review of this report

## Stop Rule

This review freezes the registry at 22 tasks, reviews every task's `task.json`,
`prompt.md`, `deep-spec.md`, and fixture direction once, applies confirmed
cross-cutting repairs once, runs one final validation pass, and stops. A new
review is justified only by a changed task inventory, changed checker contract,
or new failure evidence.

Alignment means:

- prompt requirements and checker behavior point in the same direction;
- the visible fixture's initial outcome is declared and observed;
- regression guards cannot be reported as agent solves without a hidden broken
  code baseline;
- certified repair requires an evaluator-owned failing baseline, a real patch
  to a declared solution file, and a final fail-to-pass transition;
- solver changes cannot touch `evals/**`;
- deterministic gates and subjective rubric judgment remain separate;
- rubric tasks cannot resolve while subjective review is missing;
- evidence, failure taxonomy, task metadata, and docs use one vocabulary.

## Shared Surfaces

| Surface | Review result |
| --- | --- |
| [Suite guide](../../evals/README.md) | Aligned to solution versus regression fixture direction, finite review, protected harness, and pending rubric semantics. |
| [System spec](a-story-swebench-style-evals.md) | Aligned to current task-quality risks: misleading prompt, strict tests, underspecification, low coverage, contamination, and no-op credit. |
| [Failure taxonomy](../../evals/research/failure-taxonomy.md) | Canonical Evidence Ledger retained; E19 records fixture-direction/no-op failure. |
| [Research sources](../../evals/research/sources.json) | Current official OpenAI eval guidance and 2026 coding-eval audit recorded with repo implications. |
| [Creative rubric](../../evals/rubrics/creative-contract.md) | Anchored 12-point scoring; missing review remains pending. |
| [Visual rubric](../../evals/rubrics/visual-storytelling.md) | Anchored image-first, shot, continuity, blocking, spatial, and composition scoring. |
| [Semantic eval memory](../../memory/semantic/eval-research.md) | Durable direction, no-op, rubric, and bounded-review learning recorded. |

## Task Ledger

Every row below represents a completed review of the task prompt, metadata,
deep spec, fixture mapping, named deterministic checker, and rubric declaration.

| Task | Fixture direction | Primary proof | Alignment |
| --- | --- | --- | --- |
| [ASTO-001](../../evals/tasks/ASTO-001-brandmark-drift/) | solution / unresolved | Active brandmark authority is top-right and root contract is untouched. | PASS |
| [ASTO-002](../../evals/tasks/ASTO-002-format-snapback/) | solution / unresolved | Latest creator format correction removes unrequested planned outputs. | PASS |
| [ASTO-003](../../evals/tasks/ASTO-003-textless-prompt/) | regression / guarded | Carousel doctor blocks active textless source-art prompts. | PASS; hidden code mutation required for agent solve credit |
| [ASTO-004](../../evals/tasks/ASTO-004-fake-publishable-package/) | regression / guarded | Corrupt or incomplete finals cannot derive publishable state. | PASS; hidden code mutation required for agent solve credit |
| [ASTO-005](../../evals/tasks/ASTO-005-working-memory-pointer/) | solution / unresolved | Durable learning moves to sourced semantic memory and working memory stays pointer-only. | PASS |
| [ASTO-006](../../evals/tasks/ASTO-006-creator-skill-routing/) | solution / unresolved | Every active carousel route loads the creator skill stack without broad implicit skills. | PASS |
| [ASTO-007](../../evals/tasks/ASTO-007-context-rule-truncation/) | regression / guarded | Required rule includes fail loudly at the token boundary. | PASS; hidden code mutation required for agent solve credit |
| [ASTO-008](../../evals/tasks/ASTO-008-autopublish-risky-paths/) | regression / guarded | Risky paths and synthetic secrets are blocked while placeholders remain allowed. | PASS; hidden code mutation required for agent solve credit |
| [ASTO-009](../../evals/tasks/ASTO-009-article-story-selling-gate/) | solution / unresolved | Generated article artifacts carry Layer E, Story-Selling, and final gate evidence. | PASS |
| [ASTO-010](../../evals/tasks/ASTO-010-prepost-layer-e/) | solution / unresolved | Every prepost agent and the orchestrator carry Layer E grounding. | PASS |
| [ASTO-011](../../evals/tasks/ASTO-011-small-brief-no-framework-dump/) | solution / unresolved | Creator brief preserves the seed, format, scene object, reaction, and payoff without framework leakage. | PASS; anchored creative review required after repair |
| [ASTO-012](../../evals/tasks/ASTO-012-visual-variety-shot-ladder/) | regression / guarded | Physical-scene preflight isolates repeated narrative job and shot-size failure. | PASS; hidden code mutation and anchored visual review required |
| [ASTO-013](../../evals/tasks/ASTO-013-stale-artifact-after-correction/) | regression / guarded | Active stale phrases block generation while archival correction evidence remains. | PASS; hidden code mutation required for agent solve credit |
| [ASTO-014](../../evals/tasks/ASTO-014-identity-eval-stop-gate/) | regression / guarded | Missing or incomplete structured identity evidence stops batch continuation. | PASS; hidden code mutation required for agent solve credit |
| [ASTO-015](../../evals/tasks/ASTO-015-score-inflation-after-rejection/) | solution / unresolved | Rejected 28+ concepts require stop, cap, invalidation, or rebuild routing. | PASS; anchored creative review required after repair |
| [ASTO-016](../../evals/tasks/ASTO-016-home-cinematic-visual-evidence/) | regression / guarded | Generic home language fails concrete camera, light, and story-evidence fields. | PASS; hidden code mutation and anchored visual review required |
| [ASTO-017](../../evals/tasks/ASTO-017-public-name-leakage/) | solution / unresolved | Public names are removed while internal identity names remain available. | PASS; anchored creative review required after repair |
| [ASTO-018](../../evals/tasks/ASTO-018-copy-visual-logic-contradiction/) | regression / guarded | Rendered-frame QA isolates explicit copy-visual contradictions. | PASS; hidden code mutation and anchored visual review required |
| [ASTO-019](../../evals/tasks/ASTO-019-duplicate-background-characters/) | regression / guarded | Structured entity QA blocks unexpected background people. | PASS; hidden code mutation required for agent solve credit |
| [ASTO-020](../../evals/tasks/ASTO-020-hand-object-integrity/) | regression / guarded | Anatomy QA blocks ownerless limbs, unexplained edge entry, and solid-object intersection. | PASS; hidden code mutation required for agent solve credit |
| [ASTO-021](../../evals/tasks/ASTO-021-whole-person-spatial-integrity/) | regression / guarded | Spatial QA blocks body/environment morphs while valid occlusion remains possible. | PASS; hidden code mutation required for agent solve credit |

## Resolved Findings

1. Checker direction was implicit and inconsistent. Every task now declares a
   machine-readable `fixture_contract`, and every deep spec explains it.
2. Regression guards could be mistaken for solved agent tasks. They now require
   `hidden_code_mutation_required` before solve credit.
3. Solvers could edit visible eval files on tasks allowing `evals/**`. The
   allowlists were removed and the diff guard now protects the entire harness.
4. Rubric hooks could look like completed creative judgment. They are now
   prechecks plus a mandatory evidence-bearing review; missing review is
   `PENDING`.
5. Three visual tasks expected the solver to modify their own eval package.
   Self-referential expected paths and prompt language were removed.
6. Format, article, and prepost solution fixtures were not named as repair
   artifacts in their task surface. Their prompts and expected paths now match
   their checker inputs.
7. Research guidance missed the latest official coding-eval data-quality
   taxonomy. The source ledger and system principles now include it.
8. Final-state checking did not prove that an agent changed or repaired
   anything. Certified attempts now require an external failing baseline,
   changed declared solution files, checker fail-to-pass transitions, complete
   pass-to-pass checks, and an unchanged eval harness.
9. Dimension wording still implied automatic post plus Story/Reel output.
   ASTO-002, ASTO-004, the system spec, and the failure taxonomy now follow the
   current-request lock: post-only by default, other canvases only when
   explicitly requested.

## Deliberate Boundary

This repository now has a coherent contract-regression suite and a finite
alignment review. It does not yet claim that all 22 tasks are benchmark-ready
agent challenges. The 13 regression fixtures intentionally require hidden code
mutations or pinned pre-fix revisions before an agent run; counting their
already-guarded state as a solve would be invalid.
