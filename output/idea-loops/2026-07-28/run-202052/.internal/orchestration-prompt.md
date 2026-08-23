Use $a-story-instagram-idea-loop to run one bounded Instagram idea loop.

Exact run directory (the only path you may write):
/Users/himanshusharma/astoryoftwo-analysis/output/idea-loops/2026-07-28/run-202052

Repository evidence root (read-only; never edit it):
/Users/himanshusharma/astoryoftwo-analysis

Seed:
No seed supplied. Discover a fresh opportunity from repo evidence.

Budgets:
- maximum iterations: 3
- maximum candidates per iteration: 6

Read `.internal/loop-state.json` and `.internal/evidence-manifest.json` inside
the run directory first. Load the exact artifact field contract with:
/Users/himanshusharma/astoryoftwo-analysis/venv/bin/python /Users/himanshusharma/astoryoftwo-analysis/scripts/instagram_idea_loop.py schema

Follow the skill exactly. Use project custom agents
`asot_idea_scout`, `asot_idea_maker`, and `asot_idea_verifier`; the controller
must not impersonate their independent outputs. Spawn two maker tasks with
different creative lanes, two blind verifier tasks with different lenses, and
a fresh selector task. The first line of every spawn prompt must be exactly
`ASOT_IDEA_LOOP_ROLE=<custom-agent-name>`, using one of the three names above.
Store the exact returned receiver thread ID as each artifact's task ID; live
validation matches those IDs exactly against completed Codex spawn events.
Give critics only the author-hidden card produced by the schema contract and
bind their reviews to both the exact candidate and blind input fingerprints.
The controller alone writes artifacts.

Iterate generate -> blind verify -> scoped repair -> fresh verify until one
route satisfies every stop condition or an honest terminal state is reached.
Never lower thresholds, expose below-threshold routes in `creator-brief.md`,
invent creator approval, package a carousel, generate images, publish, edit
durable memory, or claim guaranteed virality. On success stop at
READY_FOR_CONCEPT_LOCK with creator approval PENDING.

Before finishing, run:
/Users/himanshusharma/astoryoftwo-analysis/venv/bin/python /Users/himanshusharma/astoryoftwo-analysis/scripts/instagram_idea_loop.py validate /Users/himanshusharma/astoryoftwo-analysis/output/idea-loops/2026-07-28/run-202052
Repair contract errors within the remaining budget. If they cannot be repaired,
write an honest stop reason rather than fabricating a pass.
