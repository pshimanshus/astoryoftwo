# Hand–Box Intersection — Repair and Root-Cause Eval

Date: 2026-07-20

Verdict: the visible hand–box defect is repaired; identity remains unverified.

## Corrected Asset

- Rejected source: `source/original-rejected-1086x1448.png`
- Corrected edit source: `source/still-choosing-hand-box-fixed-source.png`
- Exact feed export: `final/still-choosing-hand-box-fixed-1080x1440.png`
- Structured review: `visual-qa.json`

The man's right hand now sits outside the moving box and supports its lower
exterior edge. His forearm remains continuous from sleeve to wrist; neither the
hand nor forearm penetrates the box wall. The foreground couple, exact copy,
brandmark, watercolor-and-ink language, and 3:4 composition remain intact.

## What Actually Failed

The primary failure was not the background couple. The man's hand/forearm
entered the box through a solid boundary, producing an impossible load-bearing
pose. My first review fixated on a secondary background detail and missed the
high-salience anatomy/physics defect.

That exposes two workflow failures:

1. **Attention failure:** review followed scene semantics before tracing every
   visible limb and every limb–object contact.
2. **Contract failure:** hand count and finger plausibility were treated as
   enough; the QA did not require ownership, narrative purpose, contact
   geometry, overlap order, and load direction.

## New Hard Gate

For every visible hand, QA must now record and verify:

- owner and left/right side;
- whether the locked scene actually requires the hand;
- continuous arm → wrist → hand attachment;
- contacted object, including `null` when there is none;
- believable contact geometry and occlusion order;
- no solid-object intersection;
- no unexplained entry from a frame, door, wall, clothing, or object edge.

`ASTO-020-hand-object-integrity` contains both rejected patterns from this
session: the forearm-through-box error and the anonymous door-edge hand. A
single beauty score, correct people count, or correct finger count cannot pass
either fixture.

## Remaining Limitation

The repair is visually usable as a corrected scene asset, but it is not labeled
a fully identity-verified A Story final because the edit was not compared with
the selected Aachu/Zuv identity bundle.
