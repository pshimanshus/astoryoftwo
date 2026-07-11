# Issue: Creator Skill Stack Missing From A Jam Route

## Context

Fresh carousel jams must load `config/skills/creator-skill-stack.md` before
creator-facing concepts. One routing surface stopped loading it, so a future
agent can skip scroll-stop, recognition, scene-proof, payoff, and DM-send
thinking.

## Task

Repair the routing so the creator skill stack is present in the carousel jam
skill system, context manifest, runtime context, autopilot path, and command
flow where appropriate.

## Acceptance Criteria

- Every active carousel jam route references the creator skill stack.
- Closeout and wiki-health skills remain explicit-only.
- Compact runtime loading remains intact.
- Creator workflow and skill registry tests pass.

## Constraints

Do not edit `AGENTS.md`. Do not make risky skills implicit. Do not replace the
runtime context with broad long-source loading.
