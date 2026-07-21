---
name: a-story-instagram-idea-loop
description: Discover, generate, independently verify, repair, and select one fresh evidence-backed Instagram idea for @a.storyof.two. Use for "find today's idea", "come up with an Instagram idea", autonomous or repeated idea discovery, idea-agent loops, daily ideation, or requests based on loop engineering; stop at creator concept lock and hand accepted routes to a-story-carousel-jam.
---

# A Story Instagram Idea Loop

## Purpose

Run a bounded maker/checker loop upstream of carousel production. Return one
strongest current Instagram bet for creator concept lock, or stop honestly when
no route clears the bar. Never promise performance, auto-approve the concept,
write public copy, generate images, publish, or silently change durable memory.

This workflow adapts Addy Osmani's Loop Engineering pattern:
https://addyosmani.com/blog/loop-engineering/

## Load First

1. Read `config/skill-systems.json` -> `instagram_idea_loop`.
2. Read the run's `.internal/evidence-manifest.json` and
   `.internal/loop-state.json`.
3. Run `venv/bin/python scripts/instagram_idea_loop.py schema` and preserve the
   exact artifact field names.
4. Read `config/skills/creator-skill-stack.md`.
5. Read `config/skills/carousel-jam-runtime-context.md`.
6. Inspect the exact evidence paths selected by the manifest. Do not full-read
   unrelated corpus or output folders.

Use the live `memory/semantic/carousel-idea-preferences.md` ledger directly for
rejected and cooled lanes; do not rely on a truncated summary.

## Roles

Use project-scoped custom agents from `.codex/agents/`:

- `asot_idea_scout`: read evidence and return opportunity signals, recent
  collisions, and freshness limits. It must not invent or select concepts.
- `asot_idea_maker`: run two independent tasks with different creative lanes.
  Each task creates distinct unscored routes and does not grade itself.
- `asot_idea_verifier`: run two blind critic tasks with different lenses, then
  a fresh third task as selector. The selector must not be a maker or either
  critic task.

Keep all subagents read-only. The controller alone writes to the exact run
directory. Close completed tasks before opening a new wave when thread capacity
is tight. Do not let a subagent spawn another subagent.

## Loop

1. Discover:
   - ask the scout for a source-grounded brief;
   - record missing or stale evidence as uncertainty;
   - separate transferable mechanics from copied wording or scenes.
2. Generate:
   - spawn two maker tasks in parallel;
   - assign different lanes such as lived private recognition, desi/cultural
     specificity, visual comedy-to-tenderness, chosen family, witness,
     dignity, shared adulthood, repair language, or private mythology;
   - keep the free creative pass alive before scoring;
   - cap the combined pool at the run's `candidate_budget`.
3. Exclude:
   - remove exact or semantic repeats, recent packages, rejected/cooled lanes,
     private-context-only ideas, generic quote-card romance, and copied source
     expression;
   - preserve rejected evidence internally.
4. Blind verify:
   - remove maker identity, self-scores, and persuasive commentary from critic
     cards;
   - bind each review to the exact candidate SHA-256 produced by
     `scripts/instagram_idea_loop.py fingerprint`;
   - run two independent verifier tasks: audience/retention/distribution and
     stage-scene/taste/brand/safety.
5. Repair:
   - repair only the best two or three routes using concrete verifier feedback;
   - preserve parent/repair lineage and assign a new fingerprint;
   - rerun fresh blind verification after every material repair.
6. Select:
   - use a fresh verifier task as selector;
   - choose exactly one fully passing route or return `NO_GO`;
   - show no below-threshold alternatives in the creator brief.
7. Remember:
   - append iteration, failure signature, task provenance, decision, and next
     action to run-local state;
   - do not edit semantic memory until the creator accepts or rejects the idea;
   - later outcome learning must remain a draft proposal until human review.

## Candidate Contract

Every candidate must contain:

- stable candidate ID, iteration, and maker task ID;
- `maker_agent: "asot_idea_maker"`;
- concrete couple moment and universal relationship truth;
- audience mirror, scroll stop, and emotional contradiction;
- visible scene proof and relationship motion;
- retention ladder and earned payoff;
- natural DM-send reason;
- strongest format recommendation;
- ownable @a.storyof.two turn;
- repo-relative evidence paths, risks, and novelty fingerprint.

Keep this at concept-lock level. Do not produce slide copy, captions, prompts,
or images.

## Completion Predicate

Return `READY_FOR_CONCEPT_LOCK` only when the exact selected candidate receives
two distinct blind verifier passes and a fresh selector pass with:

- Story-Selling >= 28/30;
- Golden Theme >= 28/30;
- distribution >= 26/30;
- visual generativity >= 27/30;
- Story Director hook, story, bridge, relationship motion, ending, and DM-send
  dimensions each >= 8/10;
- Stage-Scene `PASS`;
- World-Class Taste `PASS_NO_CAP`;
- safety `PASS`;
- no rejected/cooldown/repeat/copy exclusion;
- no hard failure;
- creator approval still `PENDING`.

Use at most the state's `max_iterations`. Stop earlier as `STAGNATED` when the
same normalized failure signature repeats twice. Other honest terminal states
are `NO_GO`, `BUDGET_EXHAUSTED`, `STALE_EVIDENCE`, and `HUMAN_REQUIRED`.
Never lower a gate to force convergence.

## Durable Artifacts

Write only inside `output/idea-loops/YYYY-MM-DD/<run-id>/`:

- `.internal/loop-state.json`
- `.internal/evidence-manifest.json`
- `.internal/iterations/<NN>/...` for attempt history
- `source-memory-brief.json`
- `concept-routes.json`
- `concept-debate.json`
- `concept-repairs.json`
- `taste-gate.json`
- `verification.json`
- `concept-selection.json`
- `creator-brief.md`

Include `schema_version: "1.0"` and the same `run_id` in every JSON artifact.
Bind critic reviews to candidate fingerprints and record distinct maker,
verifier, and selector task IDs. Bind each blind critic to the author-hidden
input fingerprint as well as the full candidate fingerprint. Run the
deterministic validator before finishing:

```bash
venv/bin/python scripts/instagram_idea_loop.py validate \
  output/idea-loops/YYYY-MM-DD/<run-id>
```

## Creator Handoff

Make `creator-brief.md` concise and human:

1. selected candidate ID and working title;
2. the concrete moment;
3. why a cold viewer recognizes it;
4. strongest format and visible proof;
5. why someone sends it to one person;
6. evidence and uncertainties;
7. one request: approve, reject, or repair the concept.

After explicit concept approval, hand the accepted moment and route to
`$a-story-carousel-jam`. That workflow owns copy lock, visual direction,
identity references, generation, QA, and final packaging.

## Commands

```bash
make idea-loop
make idea-loop SEED="optional real couple moment"
venv/bin/python scripts/instagram_idea_loop.py resume \
  output/idea-loops/YYYY-MM-DD/<run-id>
venv/bin/python scripts/instagram_idea_loop.py status \
  output/idea-loops/YYYY-MM-DD/<run-id>
```
