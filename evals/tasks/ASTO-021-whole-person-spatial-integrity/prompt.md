# Block Whole-Person Spatial Integrity Failures

## Context

A proof can now pass text, identity, people count, hand count, and general
style while still containing obvious AI image slop: a person's body merges into
a door, wall, chair, sofa, bed, table, or frame. The specific seeded failure is
Zuv in a doorway scene where his shoulder, back, and torso are not fully
separate from the door plane.

This is different from finger-count or anonymous-hand QA. The whole person must
occupy a believable volume in the room.

## Task

Strengthen visual QA so each person has a traceable silhouette, declared depth
relationship to nearby solid objects, continuous body-region boundaries, clear
occlusion order, and no unresolved body/object intersection or morph.

## Acceptance Criteria

- A person merging into a door, wall, furniture edge, or frame blocks proof and
  final approval.
- Correct people/hand/finger counts cannot override broken body/environment
  topology.
- Valid leaning contact or partial occlusion still passes when the body
  continues visibly and front/back order is explicit.
- Focused fail-closed visual QA and eval-runner tests pass.

## Constraints

Do not edit `AGENTS.md`. Do not generate final media. Do not weaken identity,
text, brandmark, dimension, or hand-object gates. This task adds a spatial
topology layer; it does not replace existing anatomy or scene-entity checks.
