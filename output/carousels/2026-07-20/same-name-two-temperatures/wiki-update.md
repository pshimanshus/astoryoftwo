# The First “Suno” Never Counts - Carousel Quality Update

last_updated: 2026-07-20
confidence: 0.7
sources:
- output/carousels/2026-07-20/same-name-two-temperatures/manifest.json
- output/carousels/2026-07-20/same-name-two-temperatures/prompt-pack.json
- output/carousels/2026-07-20/same-name-two-temperatures/final-audit.json

## Status

Final audit: NEEDS_FIXES

## Issues

- REQ-STYLE-001: Use romantic watercolor-and-ink / identity-rooted illustration style
- REQ-PHOTO-001: Preserve supplied photo cues, outfits, settings, poses, and relationship energy
- REQ-IDENTITY-001: Aachu/Zuv identity reference is present in manifest and prompt pack
- REQ-IDENTITY-CONSISTENCY-001: Face structure, expressions, clothing, and cross-slide identity continuity are reviewed before image generation
- REQ-POST-COPY-VISUAL-ROOM-001: Run the post-copy visual creative room after approved copy and before prompt/image handoff
- REQ-VISUAL-PLAN-QUALITY-001: Per-slide visual screen passes before image generation
- REQ-SUCCESS-STANDARD-001: Successful carousel standard is carried as open agent alignment and passes before final approval
- REQ-VISUAL-QA-001: Structured face and storyboard visual QA gate passes with evidence
- REQ-BRAND-001: Keep @a.storyof.two as a tiny, low-contrast top-right brandmark
- REQ-NEGATIVE-001: Block photorealism, 3D rendering, generic stock couple art, and quote-card layout
- intake_reviewer: No reference images were supplied.
- visual_reviewer: Slide 1 missing: cta_intent.; Slide 2 missing: cta_intent.; Slide 3 missing: cta_intent.; Slide 4 missing: cta_intent.; Slide 5 missing: cta_intent.; Slide 6 missing: cta_intent.; Slide 7 missing: cta_intent.; visual-plan-quality.json has 0 slide records, expected 7.
- identity_consistency_reviewer: identity-consistency-review.json has 0 slide records, expected 7.; Slide 1 missing identity continuity fields: face_structure, facial_expression, clothing, cross_slide_consistency.; Slide 2 missing identity continuity fields: face_structure, facial_expression, clothing, cross_slide_consistency.; Slide 3 missing identity continuity fields: face_structure, facial_expression, clothing, cross_slide_consistency.; Slide 4 missing identity continuity fields: face_structure, facial_expression, clothing, cross_slide_consistency.; Slide 5 missing identity continuity fields: face_structure, facial_expression, clothing, cross_slide_consistency.; Slide 6 missing identity continuity fields: face_structure, facial_expression, clothing, cross_slide_consistency.; Slide 7 missing identity continuity fields: face_structure, facial_expression, clothing, cross_slide_consistency.
- prompt_reviewer: Shared style prompt does not specify watercolor-and-ink illustration.; Shared style prompt does not specify hand-drawn illustration.; Shared style prompt does not explicitly preserve photo/reference details.; Negative prompt missing 'photorealism'.; Negative prompt missing '3d'.; Negative prompt missing 'stock'.; Negative prompt missing 'quote-card'.; Slide 1 prompt missing Identity continuity lock.; Slide 2 prompt missing Identity continuity lock.; Slide 3 prompt missing Identity continuity lock.; Slide 4 prompt missing Identity continuity lock.; Slide 5 prompt missing Identity continuity lock.; Slide 6 prompt missing Identity continuity lock.; Slide 7 prompt missing Identity continuity lock.
- copy_reviewer: Recommended caption is missing.; Alt text list is missing.
- success_standard_reviewer: Missing recorded agent alignment to the successful-carousel goals.; Prompts do not carry the successful-carousel standard into generation handoff.
- asset_reviewer: Unexpected render status: BATCH_ALLOWED.

## Notes

- Wiki and memory files are updated after final audit generation.

## Human Truth

In many couples, the first polite call is information; the second tone is the actual notification.

## Learning

- Keep the romantic watercolor-and-ink / identity-rooted style as the default for memory-led carousels.
- Preserve source-photo objects before adding decorative story elements.
- Preserve Aachu/Zuv identity references across every generated slide.
- Carry the successful-carousel standard as open agent alignment, not a keyword checklist.
- Generate model-native publishable slides when typography, face quality, outfit continuity, and composition must match the reference examples.

## Caption


