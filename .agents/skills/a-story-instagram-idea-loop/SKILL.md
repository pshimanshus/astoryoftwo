---
name: a-story-instagram-idea-loop
description: Run an opt-in, evidence-heavy, multi-agent loop to discover, challenge, repair, and select one fresh Instagram concept for @a.storyof.two. Use only when the creator explicitly requests the idea-agent loop, autonomous repeated ideation, deep independent verification, or the strongest evidence-backed bet; ordinary ideas stay with a-story-carousel-jam.
---

# A Story Instagram Idea Loop

Return one evidence-backed concept for creator lock or an honest stop. Do not
write public copy, generate images, publish, auto-approve, promise performance,
or edit durable memory.

## Start

1. Read `config/skill-systems.json` -> `instagram_idea_loop`.
2. Read the run's `.internal/loop-state.json`, `evidence-manifest.json`,
   `preference-index.json`, and `context-budget.json`.
3. Run `venv/bin/python scripts/instagram_idea_loop.py schema`; use those exact
   artifact fields.

The context budget is a role boundary:

- `asot_idea_scout` reads the preference index and manifest-selected evidence.
  It may read the full `memory/semantic/carousel-idea-preferences.md` once only
  when the compact index is insufficient, after recording the reason and use.
- `asot_idea_maker` receives only `source-memory-brief.json` and its assigned
  lane. Run two independent makers with different lanes.
- `asot_idea_verifier` receives blind candidate cards and cited excerpts. Run
  two independent lenses, then a fresh selector over passing cards and reviews.
- Makers, critics, and selector must not reopen the ledger, corpus, wiki,
  unrelated output, or each other's hidden context.

All subagents are read-only. Only the controller writes inside the exact run
directory. A subagent must not spawn another subagent.

## Loop

Scout -> two makers -> exclude collisions -> two blind critics -> repair the
best two or three -> fresh critics -> fresh selector. Preserve parent and
repair lineage, exact fingerprints, hidden-author critic cards, task IDs, and
iteration history. Stop as `STAGNATED` when the normalized failure signature
repeats twice. Respect the state's `max_iterations` and `candidate_budget`;
never lower a gate to force convergence.

Every route must identify its concrete moment, universal truth, audience
mirror, scroll stop, visible proof, relationship motion, retention ladder,
payoff, DM-send reason, format, @a.storyof.two turn, evidence, risks, and moment
provenance. Never present a generic hypothesis as Aachu/Zuv canon. Use
`CREATOR_CONFIRMATION_REQUIRED` when a lived detail needs confirmation.

## Pass Contract

Return `READY_FOR_CONCEPT_LOCK` only when one exact route has two distinct blind
passes and a fresh selector pass with Story-Selling >=28/30, Golden Theme
>=28/30, distribution >=26/30, visual generativity >=27/30, every Story
Director dimension >=8/10, Stage-Scene `PASS`, World-Class Taste `PASS_NO_CAP`,
safety `PASS`, no repeat/rejection/copy hit, and creator approval `PENDING`.

Otherwise use `NO_GO`, `BUDGET_EXHAUSTED`, `STAGNATED`, `STALE_EVIDENCE`, or
`HUMAN_REQUIRED` according to the schema. Show no failed alternatives in the
creator brief.

Before finishing, run:

```bash
venv/bin/python scripts/instagram_idea_loop.py validate \
  output/idea-loops/YYYY-MM-DD/<run-id>
```

Keep every JSON artifact at `schema_version: "1.0"` with one `run_id`. The
validator proves artifact and declared task separation, not cryptographic
subagent identity. The creator brief must stay concise and end with the single
decision needed for concept lock.
