# Fail-Closed Visual QA

last_updated: 2026-07-20
confidence: 1.0
source: direct creator correction after slide-08 doorway proof

An anatomy instruction inside an image prompt is not an anatomy check. A
pre-generation visual-plan PASS cannot approve generated pixels.

Generated carousel proofs remain internal and quarantined until structured
post-generation QA inspects the exact file. The review inventories hands and
limbs, binds evidence to the file hash and dimensions, checks entity integrity
and identity, and separately checks storytelling, visual richness, text, and
style. Creator approval happens after those passes. Failed proofs are retried
at most twice and are never shown as approved/final or used to continue the
batch.

The enforcement is per requested native format, not per conceptual slide. A
clean 3:4 review cannot approve a separate 9:16 render. Retry count is derived
from an immutable attempt ledger and cannot be supplied by a caller. Promotion
uses an internal staging tree, and public final folders remain empty until the
staged assets pass final audit.

The creator identified three non-negotiable AI-slop failures on 2026-07-20: a
forearm passing through a moving box, an unnecessary hand entering from a door
edge, and—most importantly—Zuv's shoulder, back, shirt, and torso visually
morphing into the door and doorframe. The body-door merge was the primary miss.
Review must not stop at people count, hand count, finger shape, or the local
focal gesture.
For every visible hand it must verify story necessity, owner and side,
continuous arm/wrist attachment, contacted object, overlap/occlusion order,
load direction, absence of solid-object intersection, and absence of
unexplained entry from a frame, door, wall, clothing, or object edge. Any one
of these failures blocks the image.

Before local anatomy review, trace each person's whole silhouette and the
nearby solid-object boundaries at full-frame and cropped views. Record every
body-region relation as in front of, behind, touching, separately adjacent, or
occluded by the object. The observed relation must match the planned relation;
occlusion must have a clear continuation; architecture must never cross,
replace, absorb, or hide an untraceable portion of the body. Any ambiguous
region, unresolved intersection, or painterly body/object merge is a hard
`REJECTED_SPATIAL_INTEGRITY`, never PASS_WITH_NOTES.

Visual richness means layered story evidence: foreground, midground,
background, one focal action, two to four relevant details, and visible cause
and effect. It does not mean decorative clutter.
