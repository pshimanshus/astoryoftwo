# Issue: Pre-Post Reel Analysis Skips Layer E

## Context

The planned Reel pre-post workflow is producing hook, edit, algorithm, caption,
and cultural notes without the romance story-selling spine. That makes the
analysis tactical but not authorial.

## Task

Repair the prepost workflow so every relevant agent and the orchestrator load
the Layer E Story-Selling engine and produce artifact-aware story diagnosis.
Update the seeded prepost config artifact to reflect the repaired route.

## Acceptance Criteria

- Every prepost agent config includes the story-selling engine.
- The orchestrator brief names Layer E and `layer-e-story-selling.json`.
- Existing hook/edit/caption/cultural agent roles remain intact.
- Prepost story-selling tests pass.

## Constraints

Do not edit `AGENTS.md`. Do not make hook score the only gate. Do not delete
other prepost agent skills to simplify the fix.
