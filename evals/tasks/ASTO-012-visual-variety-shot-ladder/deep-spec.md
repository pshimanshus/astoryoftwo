# ASTO-012 Deep Spec - Visual Variety Shot Ladder

## Why This Task Exists

Carousel packages can pass copy review while failing visually: same medium
two-shot, same room, same posture, same feeling, with different text pasted on
top. The repo contract says text completes the scene; text must not carry the
scene. This task evaluates whether the visual planning path blocks repeated
poster scenes and requires a shot ladder before generation.

## Starting Fixture

Fixture direction: **regression**. The protected current implementation is
expected to reject the seeded failure, so a single-pass `evals/runner.py review`
records this fixture as `guarded`. That guard result alone cannot award agent
solve credit: an isolated benchmark run must first apply a hidden code mutation
or pre-fix revision that makes the guard fail, then evaluate the agent patch.

The visible fixture at `fixtures/output/evals/ASTO-012/visual-plan-quality.json`
uses emotionally plausible copy while every visual field stays a medium
two-shot at the same table in the same room. The fail-to-pass check makes
`visual-plan-quality.json` return REPAIR or BLOCK_GENERATION until the shot
ladder varies camera distance, angle, action, setting lane, props, and who is
visible. The pass-to-pass case allows a continuous same-location scene when
camera and action materially change.

## Failure Modes

- Agent lowers the visual-variety threshold.
- Agent changes copy instead of repairing visual plan.
- Agent adds a superficial shot ladder while slide visuals remain identical.
- Agent approves quote-card visuals with characters added later.
- Agent generates final images before visual-plan-quality is GO/PASS.

## Checker Design

Use the compact visual preflight and pixel-story tests plus a hidden comparison
of physical-action fields. The fail-to-pass case flips when repeated scenes
block proof generation. The pass-to-pass case proves a continuous scene still
passes when action, camera, and object state materially change. A hidden variant
should repeat a different setting to avoid overfitting to one room.

## Anti-Gaming

Require structured evidence, not only the phrase "shot ladder." The checker
should compare per-slide fields for camera, action, prop grammar, setting, and
visibility. It should fail if final image directories appear before the visual
gate passes.

## Severity Model

Critical: repeated visual plan can generate, final images appear before GO, or
quote-card visuals pass. Major: shot ladder exists but does not materially vary
slides. Minor: repeated setting is acceptable but needs clearer continuity note.
