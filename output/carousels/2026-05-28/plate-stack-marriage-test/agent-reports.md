# Agent Reports

## Storyline / Retention Agent

Verdict: REPAIR, then proof-first generation.

Corrected spine:

`dinner -> both done -> Zuv first thinks he'll keep his plate -> lazy married shortcut arrives -> silent/casual plate handoff -> Aachu reads it -> she stacks hers on his -> "dono rakh do." -> she starts using phone -> he carries both to kitchen`

Scores: Story-Selling 29/30, Golden Theme 28.5/30. Both hold only for the
corrected silent-handoff version.

## Visual / Identity Agent

Verdict: GO for one repaired proof first, STOP for full final generation.

Use `identity_images/aachu_zuv.png` as actual visual reference every time. Match
the `main-kar-lungi` hand-drawn house style. Use proof v4 as aspect/style anchor
and proof v5 as story/action anchor. Current v5 is story-correct but too tall.

## Prompt / Packaging QA Agent

Verdict: not ready before repair; downstream artifacts needed rebuild.

Applied repairs:

- rebuilt `prompt-pack.json` with all 7 corrected slides;
- changed identity review to PASS with identity-first requirements;
- repaired post-copy visual room, visual debate, visual-plan-quality, review,
  copy, manifest, and prompt draft status;
- added package-local identity dossier, preflight, and contact sheet path.

Remaining gate: generate and approve repaired slide 6 proof before full batch.
