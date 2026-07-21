# Issue: Duplicate Background Characters Escape Visual QA

## Context

An @a.storyof.two feed illustration is meant to show exactly one couple packing
and standing together in a room. The generated image looks polished and carries
the exact text and brandmark, but it also invents a second couple walking away
through the background corridor. The current QA can still approve the image by
checking style, text, anatomy, identity, and broad scene logic without counting
every visible person. This creates a second unintended story and makes the art
read like obvious generative AI output.

## Task

Add a hard, instance-level scene-entity integrity gate to visual planning,
structured visual QA, and final approval. Every slide must declare the intended
people count and roles, whether background people are allowed, the observed
people count, and any unexpected figures such as duplicates, reflections,
silhouettes, ghosted memories, or distant background actors. Repair the nearest
existing rule and quality surfaces; do not solve this only with prompt wording.

## Acceptance Criteria

- The supplied broken fixture cannot pass when two people are expected but four
  are observed and the extras are an unintended background couple.
- `visual-qa.json` requires one complete scene-entity record per slide.
- Missing inventory evidence, count mismatch, or non-empty unexpected entities
  blocks proof approval and final audit.
- An explicitly authorized crowd or background role remains possible when the
  storyboard and inventory agree.
- Focused tests cover duplicate people, missing evidence, and a valid control.

## Constraints

Do not edit `AGENTS.md`. Do not weaken identity, typography, dimensions,
brandmark, anatomy, or copy-visual logic checks. Do not rely on one holistic
VLM score: preserve a deterministic structured gate with concrete reasons that
can be exercised by a hidden variant.
