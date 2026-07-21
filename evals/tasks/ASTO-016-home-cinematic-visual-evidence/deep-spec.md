# ASTO-016 Deep Spec - Home-Cinematic Visual Evidence

## Why This Task Exists

The existing visual-variety rule prevents repeated medium shots, but it does
not fully solve home-like visual quality. The creator's 2026-07-20 correction
is about a more precise visual intelligence: the home must feel vibrant, real,
and lived-in like `the-house-learned-us`, where tables, mugs, laptop, watch,
hair clip, pooja corner, doorway, mirror, bag, charger, plants, fabrics, light,
and room continuity prove the couple's life. "Cozy home" is too vague and easy
to game.

## Starting Fixture

Fixture direction: **regression**. The protected current implementation is
expected to reject the seeded failure, so a single-pass `evals/runner.py review`
records this fixture as `guarded`. That guard result alone cannot award agent
solve credit: an isolated benchmark run must first apply a hidden code mutation
or pre-fix revision that makes the guard fail, then evaluate the agent patch.

The visible fixture at `fixtures/output/evals/ASTO-016/home-visual-plan.json`
contains a domestic carousel visual plan where every slide says warm home,
cozy plants, soft light, or couple in room, but omits camera position,
motivated light, blocking, object constellation, active movement, texture,
negative-space plan, and continuity callbacks. The fail-to-pass behavior is
that such a plan cannot reach visual GO. The pass-to-pass behavior is that
non-home carousels still use the normal shot ladder and are not forced to add
pooja corners, mugs, or apartment objects.

## Failure Modes

- Agent adds a list of aesthetic adjectives but no scene mechanics.
- Agent uses random plants/chai/books as filler.
- Agent makes every slide the same pretty interior.
- Agent creates a new reference file but does not wire it into skills/rules.
- Agent treats style as taste only, with no deterministic field requirements.

## Checker Design

The named deterministic checker is `home_cinematic_fixture`. It requires
home/interior plans to expose concrete evidence for room or sub-location, time
of day, motivated light source, camera position/shot size, blocking/body
distance, object constellation, active movement, texture/material notes,
text/negative-space placement, and continuity callback. The rubric should
judge whether those fields create home-as-story evidence rather than
decoration. A hidden variant should use "apartment", "kitchen", "vanity", or
"doorway" without the word "home." Fail-to-pass flips when generic cozy plans
block. Pass-to-pass confirms non-domestic routes are not over-constrained.

## Anti-Gaming

Do not accept keyword stuffing. The checker should inspect per-slide structure
and reject empty values such as "nice lighting" or "some props." It should
also fail if the added rule weakens existing visual-variety gates or makes
domestic props mandatory for travel, street, cafe, or family-function scenes.

## Severity Model

Critical: generic cozy-home plan can generate, visual-variety gate is weakened,
or the new reference competes with `config/rules/`. Major: fields exist but no
workflow surface loads them. Minor: wording is repetitive while the gate is
enforceable.
