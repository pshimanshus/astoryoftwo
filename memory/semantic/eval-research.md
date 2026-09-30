# Eval Research Memory

last_updated: 2026-09-05
confidence: 0.95
sources:
- docs/evals/a-story-swebench-style-evals.md
- evals/README.md
- evals/research/failure-taxonomy.md
- evals/research/sources.json
- AGENTS.md
- https://github.com/mem0ai/mem0
- https://github.com/confident-ai/deepeval
- https://github.com/langfuse/langfuse

## Durable Learning

This repo should evaluate agent behavior with local SWE-bench-style tasks:
issue-like prompts, fixed starting-state descriptions, allowed and forbidden
changes, deterministic checkers, and explicit pass criteria.

Mechanical contract gates must remain separate from creative-quality judging.
Creative rubrics can review recognition, scene proof, voice, sendability, and
format fit, but they must not override hard failures such as edited `AGENTS.md`,
secret leaks, missing identity references, wrong native dimensions, textless
source-art prompts, missing visual QA, or fake final audit claims.

The eval suite should evolve from real failures: creator corrections, failed
carousel packages, wiki-health diagnostics, review comments, closeout blocks,
and instruction drift. Each recurring failure should become a minimized fixture
and then a deterministic checker before it becomes a subjective rubric.

## Feedback-Loop Reuse Decision

Creator feedback must improve the current carousel first and future work
second. Reuse the existing `creator-correction.json`, `LearningEvent`, learning
proposal, FTS recall, carousel state, and QA surfaces. The existing correction
event now has an internal captured → diagnosed → applied → evaluated →
learning_proposed → approved/promoted or rejected lifecycle. This is evidence
management, not another creator-facing production gate or documentation tree.
Package repair stays on the existing four-lock carousel route; indexing,
learning debt, and eval maintenance run outside illustration generation.

The researched stack is integrated through optional adapters:

- Mem0's append-only, temporal, and supersession patterns are useful, but this
  repo already has learning events, proposals, snapshots, and local recall.
- DeepEval is a shadow-judge adapter inside the existing Python eval runner.
  `DEEPEVAL_DISABLE_DOTENV=1` prevents implicit dotenv loading. Missing package
  support or evaluator credentials returns `not_run`, never pass. It must never
  become an ImageGen preflight.
- Langfuse is a disabled-by-default redacted observability mirror. Only stable
  IDs, hashes, diagnoses, lifecycle states, and scalar scores can leave the
  repo. Local audit, prompt, candidate, and QA bindings remain source truth;
  network failure cannot block them.
- Promptfoo or Phoenix would duplicate the current evaluator/runtime surface
  for this problem and are not adopted.

One creator correction does not automatically deserve a new canonical rule.
Capture it exactly, repair its package, and make it searchable. Explicit
“always” or “never” instructions may produce an inactive proposal; other
patterns require matching transferable behavior in two independent packages,
with passing current evaluations for every supporting correction. Approval and
application re-check that evidence; declining promotion retains a separate
learning disposition and leaves the package correction revisable.
Generalized rules, skills, and semantic memory require recorded creator
approval before promotion.

Model judges remain advisory until at least 20 creator-reviewed outputs from
five packages show strictly below ten percent hard-fail disagreement. Threshold
promotion also needs creator approval. A deterministic feedback regression may
become a hard gate only after reproducing the failure and passing on the repair.

Sprint 1 now fingerprints evaluator code and verification contracts, preserves
past assertions/results during explicit revisions, and rejects legacy hash-only
passes. Successors receive fresh feedback/event/eval identities and immutable
source provenance. `package:` recall isolates one package and hides superseded
guidance before result limiting. Langfuse annotation exports become deduplicated
local-review candidates; they cannot automatically become creator instructions.

SDK smoke evidence covers DeepEval 4.2.1 and Langfuse 4.15.1 in an isolated test
environment without provider calls. The project interpreter has neither SDK
installed or configured and the real calibration corpus contains zero reviewed
outputs. These integration paths remain optional; live acceptance is pending.
Current API references: [DeepEval standalone metrics](https://deepeval.com/docs/metrics-introduction),
[multimodal cases](https://deepeval.com/docs/evaluation-test-cases),
[Langfuse Python API](https://python.reference.langfuse.com/), and
[annotation score model](https://langfuse.com/docs/evaluation/scores/data-model).

Every stable task should include a deep evaluator spec with fail-to-pass,
pass-to-pass, hidden variant, anti-gaming, and severity notes. A task prompt
alone is not enough; shallow task labels encourage benchmark gaming and do not
teach future checkers what behavior matters.

Smoke and high-risk tasks should also include fixture overlays. The first
fixture layer materializes broken files with `evals/runner.py prepare`, so a
checker can prove the starting state actually triggers package, prompt,
autopublish, or instruction-surface gates before any agent attempts a fix.

Fixture direction must be explicit. A solution fixture starts unresolved and
is repaired by the agent. A regression fixture starts guarded because the
current production validator catches the seeded failure. The latter is useful
as a contract regression, but it cannot award agent solve credit until an
isolated hidden code mutation or pre-fix revision makes the guard fail. This
distinction prevents no-op agents from inflating results.

Creative rubric prechecks are not creative-quality judgments. A rubric-bearing
task stays pending until a named reviewer supplies per-dimension scores and
concrete artifact evidence. Hard mechanical failures remain blocking regardless
of rubric score.

Use `venv/bin/python evals/runner.py review` for a bounded alignment pass. It
freezes registry order, inspects each selected fixture once, reports direction
mismatches, and stops; it does not retry or recursively review its own report.

Do not count `review` or the diagnostic `check` command as an agent solve.
Certified repair requires an evaluator-owned `baseline` record followed by
`grade`. The baseline must contain a real failing task checker. The final
workspace must change at least one declared solution file, every baseline
failure must flip to `PASS`, all pass-to-pass commands must stay green, and the
eval harness must remain unchanged. Regression fixtures are `NOT_READY`
without a verified external hidden mutation manifest.

Before adding or expanding eval tasks, inspect the repo's actual failure trail:
semantic memory, episodic/session health, Agentic OS learning events,
concept-rejection notes, package blockers, final audits, visual QA, wiki-health
diagnostics, and closeout safety tests. Each task should name the repetitive
mistake it covers and cite concrete evidence in
the Evidence Ledger in `evals/research/failure-taxonomy.md`; otherwise it is
likely to become generic one-line eval slop instead of a useful future-agent
contract.

## Current Starter Suites

- `smoke`: fastest dangerous failures.
- `contract`: instruction, rule, memory, Agentic OS, and closeout behavior.
- `carousel`: package and image-production gates.
- `creative`: creator-facing behavior with rubric hooks.
- `full`: all starter tasks.
