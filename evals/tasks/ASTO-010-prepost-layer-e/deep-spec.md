# ASTO-010 Deep Spec - Prepost Layer E

## Why This Task Exists

Planned Reel analysis can become a shallow optimization pass: hook score,
caption, audio, algorithm notes. The repo contract requires story-selling
diagnosis first so the analysis judges whether the Reel sells an actual
relationship story. This task checks that Layer E remains in the pre-post
workflow and every agent sees the authorial spine.

## Starting Fixture

The fixture should remove `romance-story-selling-engine` from one prepost agent
config or from orchestrator skills. The generated Agentic OS brief then lacks
`layer-e-story-selling.json`, selected story lens, or room decision fields. The
fail-to-pass check should fail on missing skill references and missing brief
sections. The pass-to-pass check keeps hook, edit, algorithm, caption, and
cultural-resonance agents available.

## Failure Modes

- Agent adds Layer E only to the top-level orchestrator, not every agent.
- Agent makes hook score override story-selling hard fails.
- Agent deletes other prepost agent skills to simplify the config.
- Agent changes public output to expose internal terms unnecessarily.
- Agent fixes tests by checking only one hard-coded config entry.

## Checker Design

Run `tests/test_prepost_story_selling.py` and inspect
`PREPOST_AGENT_CONFIGS`, `ORCHESTRATOR_SKILLS`, and
`build_agentic_os_brief`. The fail-to-pass case flips when all agents include
the story-selling spine and the brief names the Layer E artifact. The
pass-to-pass case confirms non-Layer-E prepost agents remain present. A hidden variant
should remove the skill from a different agent index.

## Anti-Gaming

Forbid removing prepost agents or replacing the config with a single catch-all
agent. The checker should assert both breadth of config coverage and generated
brief evidence. It should not require creator-facing output to show rubric
language unless this is an internal analysis artifact.

## Severity Model

Critical: any prepost agent can run without Layer E, or hook score becomes the
only gate. Major: brief omits artifact names. Minor: internal section naming is
awkward but machine-readable evidence is present.
