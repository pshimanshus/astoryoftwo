# ASTO-010 Deep Spec - Prepost Layer E

## Why This Task Exists

Planned Reel analysis can become a shallow optimization pass: hook score,
caption, audio, algorithm notes. The repo contract requires story-selling
diagnosis first so the analysis judges whether the Reel sells an actual
relationship story. This task checks that Layer E remains in the pre-post
workflow and every B1-B5 facet sees the authorial spine.

## Starting Fixture

Fixture direction: **solution**. A single-pass `evals/runner.py review` must
observe the materialized starter as `unresolved`. The task becomes resolved
only after the agent repairs the fixture-backed repository state and the named
checker passes.

The visible fixture at `fixtures/output/evals/ASTO-010/prepost-config.json`
lists hook, caption, and edit agents without Layer E or
`romance-story-selling-engine` grounding. The fail-to-pass check fails on
missing story-spine references and missing brief sections. The pass-to-pass
check keeps hook, edit, algorithm, caption, and cultural-resonance agents
available.

## Failure Modes

- Agent adds Layer E only to synthesis, not the combined B1-B5 analysis.
- Agent makes hook score override story-selling hard fails.
- Agent deletes hook, edit, algorithm, caption, or culture facets to simplify the config.
- Agent changes public output to expose internal terms unnecessarily.
- Agent fixes tests by checking only one hard-coded config entry.

## Checker Design

Run `tests/test_prepost_story_selling.py` and inspect
`PREPOST_AGENT_CONFIGS`, `ORCHESTRATOR_SKILLS`, the combined-analysis prompt,
and `build_agentic_os_brief`. The fail-to-pass case flips when all five facets
remain represented, the combined analysis consumes Layer E, and the brief names
the Layer E artifact.

A hidden variant should remove Layer E from a different B1-B5 facet or omit one
facet record so the checker cannot pass through a single hard-coded assertion.

## Anti-Gaming

Forbid removing prepost facets. A three-call analyst/challenger/synthesizer
topology is valid when the combined analyst returns distinct B1-B5 records and
the final report preserves those sections. The checker should assert facet
breadth and generated brief evidence, not five separate model calls.

## Severity Model

Critical: any prepost facet can run without Layer E, or hook score becomes the
only gate. Major: brief omits artifact names. Minor: internal section naming is
awkward but machine-readable evidence is present.
