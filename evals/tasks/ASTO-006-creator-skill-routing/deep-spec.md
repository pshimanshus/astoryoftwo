# ASTO-006 Deep Spec - Creator Skill Routing

## Why This Task Exists

The creator skill stack is the session-start hook for scroll stop,
recognition, emotional contradiction, scene proof, payoff, format remix, taste,
and DM-send thinking. If one routing surface omits it, future carousel jams can
look efficient while skipping the creative muscles the repo is trying to
preserve. This task evaluates workflow routing across the skill registry,
runtime context, manifest, and command path.

## Starting Fixture

The fixture should remove `config/skills/creator-skill-stack.md` from one or
more surfaces, such as `config/skill-systems.json`,
`config/agentic_context_manifest.json`, `config/skills/carousel-jam-runtime-context.md`,
or `scripts/jam_today.py`. The fail-to-pass case is that creator workflow tests
or an explicit route scan fails. The pass-to-pass case is that existing repo
skills still resolve, closeout/wiki-health skills remain explicit-only, and the
compact runtime policy still avoids loading every long source by default.

## Failure Modes

- Agent adds the hook only to documentation, not machine-readable routing.
- Agent makes all skills implicit, including closeout or wiki-health.
- Agent loads long source files by default and violates token policy.
- Agent removes the free creative pass or human draft language while editing.
- Agent updates only one route and leaves `jam_today.py` stale.

## Checker Design

Run creator workflow and skill registry tests, then inspect every carousel_jam
component surface for the hook path. The fail-to-pass check flips when the
missing route is restored. Pass-to-pass coverage confirms skill records,
implicit invocation policy, and Agentic OS health remain stable. A hidden variant
should remove the hook from a less obvious surface, such as the context
manifest, to prevent single-file repairs.

## Anti-Gaming

Forbid changing test expectations to make the hook optional. Forbid broadening
implicit invocation policies. Require that the route keeps the hook private to
the creative process unless the creator asks for operating analysis.

## Severity Model

Critical: creator hook missing from an active route, closeout/wiki-health made
implicit, or runtime context bypassed. Major: hook restored in docs but not
machine-readable registry. Minor: wording drift that does not affect routing.
