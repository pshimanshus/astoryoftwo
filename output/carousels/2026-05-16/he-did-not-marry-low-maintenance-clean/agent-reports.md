# C-Layer Rebuild Notes

Runtime: codex_native_manual_rebuild

## Root Cause From Prior Run

The previous package was contract-complete but creatively weak. It used the
identity image as if it were a story image, then filled missing story context
with a hardcoded carousel lane. That made the prompts generic and misaligned.

## Rebuild Decision

This package is identity-only and concept-led. The creative brief is the source
of truth. JSON files export the brief; they do not invent the story.

## Reviewer Note

Ready for image generation, but not ready to post. Final audit must remain open
until model-native final slides and visual QA exist.
