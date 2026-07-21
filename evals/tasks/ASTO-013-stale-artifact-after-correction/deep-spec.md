# ASTO-013 Deep Spec - Stale Artifact After Correction

## Why This Task Exists

This project repeatedly fails when a creator correction lands after package
artifacts already exist. The top-level copy or conversation may be repaired,
but stale text remains in `prompt-pack.json`, `visual-debate.json`,
`visual-plan-quality.json`, `review.json`, `manifest.json`, or
`image-generation.json`. Image generation then follows the old route. The
durable memory explicitly calls this a production bug and requires every
generation-facing artifact to be rebuilt from the corrected source of truth.
The eval exists because this is not a copywriting preference; it is a state
integrity problem that should block generation.

## Starting Fixture

Fixture direction: **regression**. The protected current implementation is
expected to reject the seeded failure, so a single-pass `evals/runner.py review`
records this fixture as `guarded`. That guard result alone cannot award agent
solve credit: an isolated benchmark run must first apply a hidden code mutation
or pre-fix revision that makes the guard fail, then evaluate the agent patch.

The visible fixture at
`fixtures/output/carousels/fixtures/stale-artifact-carryover/` seeds a
carousel package with `creator-correction.json`, archived rejection evidence,
new locked copy, and stale rejected phrases in active generation-facing files.
The package looks partially valid: `slides.json` and `copy.json` point toward
the corrected house-object route, while `prompt-pack.json`,
`visual-plan-quality.json`, `visual-debate.json`, `review.json`, and
`image-generation.json` still carry phrases like "pressure-cooker route",
"seeti count", and "home runs on maybe." The fail-to-pass behavior is that the
workflow doctor reports stale-artifact blockers and generation cannot continue.
The pass-to-pass behavior is that a package whose active artifacts all agree
with the current copy remains allowed even if archival rejection notes preserve
the old phrases as evidence.

## Failure Modes

- Agent repairs only `copy.json` but leaves stale prompt text.
- Agent deletes old evidence instead of recording what changed.
- Agent allows image generation because `visual-plan-quality.json` still says
  `PASS`.
- Agent treats stale prompt language as harmless notes.
- Agent edits `AGENTS.md` or rules to make creator corrections less binding.

## Checker Design

The named deterministic checker is `stale_artifact_fixture`. It materializes
the fixture, calls `inspect_carousel_package()`, derives carousel state, and
requires the `stale_artifact_carryover` blocker. The underlying doctor compares
declared rejected phrases from `creator-correction.json` against active
generation-facing artifacts while ignoring archival evidence. The hidden variant
should hide old phrases in a less obvious field such as a prompt negative
example, `image-generation.json.expected_file` note, or `review.json.next_action`.
Fail-to-pass flips only when stale phrases block generation. Pass-to-pass
coverage ensures valid corrected packages are not blocked merely because they
preserve rejection notes in a clearly archival file.

## Anti-Gaming

Do not accept a checker that scans only `slides.json`. Do not allow agents to
delete rejection notes, concept-selection history, or creator correction
evidence. The checker should distinguish archival evidence from active
generation instructions by file role and field name. It should also fail if
the package moves straight to final images while stale phrases are unresolved.

## Severity Model

Critical: stale active prompt/copy/visual text can reach generation, package is
marked publishable, or creator correction evidence is deleted. Major: stale
audit exists but misses one generation-facing artifact type. Minor: audit
wording is unclear but the package is blocked correctly.
