# Risk-specific visual controls

Use this reference after the current creator correction and locked scene are
known. Every condition below is a visual observation to be made on the rendered
asset; a written prompt or a JSON field cannot establish it.

| Risk | Direct before generation | Reject rendered pixels when | Repair boundary |
| --- | --- | --- | --- |
| Phone or other asymmetric prop | State the visible face, orientation, parts, function, owner, and viewer. | A display/UI and rear camera cluster share one physical face, a prop lacks a plausible use face, or fingers/eyes contradict the stated orientation. | Regenerate or repair the prop face only, then re-check its use geometry. The September 30 phone correction has no broader style scope. |
| Hands, touch, handoff, or load | Name owner, anatomical side, action, target, target region, and depth order. | A visible hand lacks a continuous owner/arm/wrist chain; is unneeded; touches the wrong target/region; penetrates a solid object; or enters unexplained from an edge. | Restage the contact and load path. Correct count alone is insufficient. |
| Body/object topology | State allowed contacts and which body regions are in front of, behind, touching, or occluded by nearby architecture/furniture. | A body merges into, crosses, replaces, or has an untraceable continuation through a door, wall, box, floor, seat, or other solid object. | Repair the blocked silhouette or solid boundary. Check the whole person before a focal hand crop. |
| Adult scale and pose | Specify crop, camera height, floor/door/furniture scale anchors, posture, and two-shot height relation. | A person reads tiny/oversized, unsupported, cramped, or implausibly folded without the scene establishing a motivated pose. | Change blocking/camera/scale anchors. Do not convert the rule into a ban on all sitting, kneeling, or natural occlusion. |
| Room geometry and props | Specify threshold side, door state, floor support, needed props, and no-addition constraints. | An item has no support, changes the locked threshold/room geography, or invents a prop that alters the event. | Correct the localized scene plane or remove the unsupported addition. |
| Identity | Use the selected actual identity photos and current package attachment contract. | A visible view does not retain recognizable face, hair, adult proportion, posture, or wardrobe evidence from the named references. | Restore the reference bundle and re-render the visible view. A generated chart cannot replace actual photos. |
| Visible accessories | State item, wearer, anatomical side/location, and whether framing or clothing credibly hides it. | A visible Zuv neck/open collar lacks the locket, or a visible Aachu right wrist/forearm lacks the bracelet, moves it, or replaces it. | Restore the item at the correct location. Do not draw an item through clothing merely to satisfy a checklist. |
| Sequence continuity | List only the facts that persist or change: time, wardrobe, accessory, location, prop owner/state, and transition. | Adjacent images change one of those facts without a visible transition or established time change. | Repair the discontinuous frame or make the time/state transition visible. |
| Gaze and gesture | State actor -> action -> target -> consequence and eye-lines. | The gaze, hand, or posture tells a different action, target, emotional beat, or relationship role than the locked event. | Restage the gesture/eye-line; decorative detail cannot repair a wrong event. |
| Copy and chronology | State temporal phase, inside/outside side, movement direction, shared/solo action, and object state. | Pixels contradict the exact line, including before/after state, direction, threshold side, or who acts. | Change the scene premise or copy only through the existing copy gate. |
| Visual event | Write what a reader should infer without text and the observable pressure/change that proves it. | The image is attractive but reads as generic affection or cannot show the pressure, joke, conflict, turn, or payoff. | Strengthen the physical event, reaction, state, or consequence. Route a rejected concept to the creative workflow. |
| Sequence variety | Give each slide a reason for its shot, action, setting, or changed state. | Repeated framing/action/setting adds no new story information. | Vary the visual sentence or make the changed state legible. A purposeful repeated frame may pass. |
| House finish | Name the current style-board reference; preserve existing palette thresholds. | Paper reads yellow/parchment, the image is a photo-plus-filter hybrid, or line/pigment/facial treatment resolves as generic glossy AI stock rather than the approved illustrated finish. | Re-render the whole affected treatment. Do not add arbitrary grain or wobble as proof of human authorship. |
| Text, signature, and canvas | Lock exact copy, line breaks, tiny top-right signature, requested native format, and no other text. | Copy, line breaks, signature, dimensions, or on-image treatment is wrong, or incidental lettering/UI/watermarks appear. | Correct the final text-bearing raster and re-check the exact requested format. |

## Scope rules

- A single review checks only the stated family and asset; it does not certify the
  rest of the frame or another format.
- Strong pixel evidence identifies what is visible and where. Avoid claiming a
  cause that cannot be observed.
- Current canonical rules decide conflicts. If they conflict with a correction
  or allow ambiguous cases, stop at `data_gap` and request a scoped creator
  decision rather than broadening a prior lesson.
