# Carousel Review Loop

last_updated: 2026-07-21
confidence: 0.98
source: creator request plus LangChain's "The Art of Loop Engineering"

## Purpose

Run review, repair, and fresh verification repeatedly until an A Story of Two
carousel package is genuinely publishable or reaches an honest stop condition.
This is the executable verification loop around the existing carousel agent
workflow. It does not replace the workflow doctor, visual-story checks,
identity gate, creator approval, or final audit.

## Four Nested Loops

The implementation adapts the four-loop stack described by LangChain:

1. Execution loop: a scoped repair agent edits only what the current feedback
   requires.
2. Verification loop: the workflow doctor, derived carousel state, and optional
   deterministic commands grade the new result from scratch.
3. Event loop: `make review-loop` is the one-command trigger; CI, cron, or a
   webhook may invoke the same command later without changing its contract.
4. Improvement loop: repeated failure signatures produce a draft
   `improvement-proposal.json`. Harness changes remain human-reviewed and must
   never weaken a gate merely to obtain green output.

Reference: https://www.langchain.com/blog/the-art-of-loop-engineering

## Completion Contract

The loop returns `COMPLETE` only when all are true:

- canonical derived carousel state is `publishable`;
- the workflow doctor reports no blocker or warning;
- every optional `--verify-command` exits successfully;
- required visual QA, identity evidence, native formats, exact text,
  brandmark, Event A/Event B provenance, creator approval, and final audit are
  real and current.

An agent saying "fixed" is not completion evidence. Every repair is followed
by a new independent programmatic review.

## Stop Conditions

The loop stops without pretending success when:

- creator approval is required;
- identity/likeness evidence is unavailable or unverified;
- visual QA has exhausted its allowed image retries;
- image generation or another required external capability is unavailable;
- the same verification signature repeats to the stagnation limit;
- the bounded iteration budget is exhausted;
- review-only mode finds a failure.

Never solve these stops by writing fake PASS JSON, made-up reviewer IDs,
synthetic hashes, invented creator approval, or placeholder images.

## Command

Default constrained Codex repair loop:

```bash
make review-loop CAROUSEL=output/carousels/YYYY-MM-DD/slug
```

Custom repair worker and deterministic verifier:

```bash
make review-loop \
  CAROUSEL=output/carousels/YYYY-MM-DD/slug \
  REPAIR_COMMAND='my-repair-worker --package {package} --feedback {feedback}' \
  VERIFY='venv/bin/python -m pytest tests/test_fail_closed_visual_qa.py -q'
```

Direct review-only diagnosis:

```bash
venv/bin/python scripts/carousel_review_loop.py \
  output/carousels/YYYY-MM-DD/slug --review-only
```

The command parser does not invoke a shell. `{package}` and `{feedback}` are
expanded as individual command arguments.

## Trace Contract

Package-local traces live under `.internal/review-loop/`:

- `trace.jsonl`: append-only verification and repair events;
- `feedback.json`: exact latest grader feedback given to the repair worker;
- `summary.json`: terminal status, state, issues, and iteration count;
- `improvement-proposal.json`: draft harness-improvement proposal on
  stagnation or budget exhaustion.

Failed candidate images and public final folders remain governed by the
existing quarantine and promotion rules. This loop cannot promote pixels by
itself.
