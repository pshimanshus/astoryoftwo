# SCENE ENTITY INTEGRITY

Every @a.storyof.two proof and final illustration must contain only the people,
animals, reflections, silhouettes, and narrative objects authorized by the
locked scene. Attractive style, correct text, and plausible anatomy do not
override an entity-count or role error.

A hand is an owned story entity with physics, not decorative texture. Every
visible hand must be required by the locked scene, attributable to one person
and side, connected through wrist/forearm anatomy, and physically believable
where it touches or passes behind an object.

A person is a coherent volume, not a texture layer. Head, neck, shoulders,
back, torso, clothing and visible limbs must remain spatially separate from
doors, walls, furniture, containers, floors and other solid objects except at
explicitly declared contact points. If front/behind/contact order is ambiguous,
the image fails.

## Required Pre-Generation Contract

For each slide, record:

- intended people count and roles;
- whether background people are allowed;
- allowed reflections, portraits, silhouettes, or memory figures;
- forbidden duplicate characters or extra narrative actors;
- exact visible hands required by the focal action and which hands stay out of
  frame;
- each person's visible body regions, nearby solid-object planes, expected
  front/behind/contact relationships, and permitted contact points;
- the visible evidence a reviewer must check after generation.

Every person scene must also carry a hand-ownership map. It names the owner,
left/right side, action, visibility, and continuous anatomical attachment for
each potentially visible hand. Secondary prose such as "brace the door" is not
enough: the plan must say whose hand, which side, where the wrist/forearm comes
from, and what the other hand is doing or whether it is fully out of frame.

Scenes involving doors, locks, thresholds, departure, arrival, or returning
must also carry an action-chronology topology contract. It states:

- the exact temporal phase, such as before departure or after return;
- the camera side and each person's side of the threshold;
- whether the door is open, closing, fully closed, or already locked;
- each person's prior position, direction of travel, and return path;
- whether the focal action is shared or solo.

The contract must reconcile the verbs in the exact copy. "Went back" requires a
visible prior direction and return. "Checked it with him" requires both people
to participate in the same check; one person acting while the other watches is
not equivalent. A creator correction that specifies outside versus inside
overrides any earlier scene description.

If the scene is an intimate two-person moment, default to exactly two visible
people and no background figures unless the storyboard explicitly requires
them.

## Required Visual QA

`visual-qa.json` must include a `scene_entity_integrity` check with one record
per slide. Each record must state `expected_people`, `observed_people`,
`unexpected_entities`, and concrete visual evidence. A count mismatch or any
unexpected entity blocks proof approval, batch continuation, final audit, and
publishable status.

`pose_anatomy: true` is never sufficient. Structured post-generation QA must
record expected and observed arms/hands, every visible hand's owner and side,
wrist/forearm attachment, action, held object, malformed fingers, duplicated
limbs, and unexpected limbs. QA must be bound to the inspected file's SHA-256
and native dimensions; a changed image invalidates the previous review.
When more than one native format is locked, anatomy, entity, and richness
evidence is required independently for every slide-format pair. Passing the
3:4 frame cannot approve separately generated 9:16 or 1:1 pixels.

Generated proofs enter quarantine. They may move to creator-visible proof only
after separate anatomy/entity/identity and storytelling/richness/text/style
reviews both pass. Creator approval is a separate gate after QA. Failed proofs
stay internal, may be retried twice, and then become `BLOCKED_VISUAL_QA`.
Attempt numbers come only from the persisted internal ledger: initial attempt,
repair one, repair two. Callers may not supply, reset, repeat, or skip them.
Every repair receives the prior attempt's exact QA failures.

Creator approval moves a proof only into internal promotion staging. Final
folders are created only after the final audit passes against staged pixels.
An audit failure leaves no publishable image in `final/`,
`final-reels-stories/`, or `final-square/`.

Count all visually represented people, including small background figures,
mirrors, windows, shadows, silhouettes, ghosted memories, framed portraits
that read as live scene actors, and accidental duplicates. Do not ignore an
extra figure because it is faint, distant, aesthetically pleasing, or seems
symbolic.

For each visible hand, trace `owner -> arm -> wrist -> hand -> contacted object`.
Record contact geometry and occlusion order. A solid object may hide part of a
limb, but the limb may not enter through the object's rim, wall, door plane,
clothing, or surface. A load-bearing hand must meet the object's exterior at a
believable support point and direction.

Before local hand review, trace every person's whole silhouette and every
nearby solid boundary. Record per-body-region expected and observed spatial
relationships. A painterly edge is allowed; an untraceable shoulder, back,
torso, head or limb is not. A body and door/wall/furniture surface may never
collapse into one unresolved mass.

## Hard Fails

- an unintended second Aachu/Zuv pair;
- any extra background person in a locked two-person scene;
- duplicate limbs, bodies, reflections, silhouettes, or ghost figures that
  read as another character;
- a generated background action that creates a second story not present in
  the approved visual plan;
- `scene_entity_integrity.pass: true` without a complete per-slide inventory;
- a visual-QA or final-audit PASS when expected and observed counts differ.
- a boolean-only anatomy claim with no per-slide limb/hand evidence;
- an unowned hand, unattached hand, duplicated limb, malformed fingers, or one
  hand performing spatially incompatible actions;
- a hand with no narrative purpose in the locked scene;
- a hand entering from a door, wall, body, object, or frame edge without a
  traceable owner and wrist/forearm connection;
- a hand, wrist, or forearm penetrating a box, door, table, clothing, or other
  solid object;
- an impossible grip, support pose, overlap order, or load direction;
- a door, wall, furniture, container or floor boundary crossing a person's
  head, neck, shoulder, back, torso, clothing or visible limb;
- a person morphed into, absorbed by or sharing an unresolved painted mass with
  architecture or another solid object;
- an ambiguous `in_front_of`, `behind`, `touching`, `occluded_by`, or
  `separate_from` relationship;
- `spatial_topology.pass: true` without per-person, per-body-region evidence
  from full-frame, person-object-crop and focal-detail inspection;
- QA whose recorded file hash or dimensions do not match the inspected asset;
- a quarantined or creator-unapproved proof used for batch continuation.
- a door/lock scene on the wrong side of the threshold or at the wrong temporal
  phase;
- copy says a person returned, but the frame contains no readable movement path
  or prior direction;
- copy describes a shared action, but only one person performs it while the
  other watches;
- an unresolved action-chronology topology contract passed into prompt
  compilation.

## Repair Rule

Use a precise object-removal edit when the rest of the image is worth
preserving. State the edit target, the exact entity to remove, the background
to reconstruct, and all invariants. Re-run entity inventory, text, brandmark,
dimensions, identity, and scene-logic checks after the edit.

Spatial integrity has no `PASS_WITH_NOTES`. One ambiguous or merged body region
means reject and regenerate.
