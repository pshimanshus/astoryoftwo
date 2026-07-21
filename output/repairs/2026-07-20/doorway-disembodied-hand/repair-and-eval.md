# Anonymous Door Hand — Repair and Root-Cause Eval

Date: 2026-07-20

Verdict: the unowned door-edge hand is removed.

## Corrected Asset

- Screenshot source: `source/screenshot-original.png`
- Cropped edit target: `source/slide-08-cropped-edit-target.png`
- Corrected source: `source/slide-08-hand-removed-source-1085x1449.png`
- Exact feed export: `final/slide-08-hand-removed-1080x1440.png`
- Structured review: `visual-qa.json`

The rejected hand had no visible owner, no required narrative function, and no
continuous wrist/forearm connection. It entered from the door/frame edge and
was therefore a hard anatomy and scene-integrity failure even though its local
finger rendering looked plausible.

The source visual direction also invited the error by asking Zuv to brace the
door while the focal action already required him to present his injured thumb.
That secondary door action has been removed from the storyboard, slide JSON,
copy, debate artifacts, prompt pack, and compiled image prompt. The corrected
direction keeps his other arm outside the frame and explicitly forbids any hand
touching the door.

This failure is covered by `ASTO-020-hand-object-integrity` and the production
hand inventory now requires story purpose, ownership, attachment, contact
geometry, occlusion evidence, and absence of unexplained edge entry.
