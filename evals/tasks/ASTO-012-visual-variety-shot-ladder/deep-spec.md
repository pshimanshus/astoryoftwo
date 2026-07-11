# ASTO-012 Deep Spec - Visual Variety Shot Ladder

## Why This Task Exists

Carousel packages can pass copy review while failing visually: same medium
two-shot, same room, same posture, same feeling, with different text pasted on
top. The repo contract says text completes the scene; text must not carry the
scene. This task evaluates whether the visual planning path blocks repeated
poster scenes and requires a shot ladder before generation.

## Starting Fixture

The fixture should include a seven-slide storyboard where every visual field is
a warm couple medium shot in the same room. Copy may be emotionally good so the
agent cannot reject it on writing alone. The fail-to-pass check should make
`visual-plan-quality.json` return REPAIR or BLOCK_GENERATION until the shot
ladder varies camera distance, angle, action, setting lane, props, and who is
visible. The pass-to-pass case should allow a continuous same-location scene
when camera and action materially change.

## Failure Modes

- Agent lowers the visual-variety threshold.
- Agent changes copy instead of repairing visual plan.
- Agent adds a superficial shot ladder while slide visuals remain identical.
- Agent approves quote-card visuals with characters added later.
- Agent generates final images before visual-plan-quality is GO/PASS.

## Checker Design

Use `build_visual_plan_quality`, story-scene tests, and a hidden comparison of
visual fields. The fail-to-pass case flips when repeated scene plans block
generation. The pass-to-pass case proves legitimate two-act or continuous scene
plans still pass when action, camera, and props change. A hidden variant should
repeat a different setting, such as a bed/table/chai sequence, to avoid
overfitting to one room.

## Anti-Gaming

Require structured evidence, not only the phrase "shot ladder." The checker
should compare per-slide fields for camera, action, prop grammar, setting, and
visibility. It should fail if final image directories appear before the visual
gate passes.

## Severity Model

Critical: repeated visual plan can generate, final images appear before GO, or
quote-card visuals pass. Major: shot ladder exists but does not materially vary
slides. Minor: repeated setting is acceptable but needs clearer continuity note.
