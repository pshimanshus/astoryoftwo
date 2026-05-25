# Her Mood Changed His Hand Didnt - Carousel Quality Update

last_updated: 2026-05-17
confidence: 0.7
sources:
- output/carousels/2026-05-17/her-mood-changed-his-hand-didnt/manifest.json
- output/carousels/2026-05-17/her-mood-changed-his-hand-didnt/prompt-pack.json
- output/carousels/2026-05-17/her-mood-changed-his-hand-didnt/final-audit.json

## Status

Final audit: NEEDS_FIXES

## Issues

- REQ-IDENTITY-CONSISTENCY-001: Face structure, expressions, clothing, and cross-slide identity continuity are reviewed before image generation
- REQ-VISUAL-QA-001: Structured face and storyboard visual QA gate passes with evidence
- identity_consistency_reviewer: This package was generated before the C3.5 identity gate existed.; Slide prompts do not include the required Identity continuity lock.; Existing final images were visually inspected and should not be treated as identity-approved final art.; Slide 1 missing identity continuity fields: face_structure, facial_expression, clothing, cross_slide_consistency.; Slide 2 missing identity continuity fields: face_structure, facial_expression, clothing, cross_slide_consistency.; Slide 3 missing identity continuity fields: face_structure, facial_expression, clothing, cross_slide_consistency.; Slide 4 missing identity continuity fields: face_structure, facial_expression, clothing, cross_slide_consistency.; Slide 5 missing identity continuity fields: face_structure, facial_expression, clothing, cross_slide_consistency.
- prompt_reviewer: Slide 1 prompt missing Identity continuity lock.; Slide 2 prompt missing Identity continuity lock.; Slide 3 prompt missing Identity continuity lock.; Slide 4 prompt missing Identity continuity lock.; Slide 5 prompt missing Identity continuity lock.
- Visual QA failed: - [x] FAIL: Aachu face is not sufficiently proven from the identity reference bundle.; - [x] FAIL: Zuv face is not sufficiently proven from the identity reference bundle.; - [x] FAIL: Clothing and dress details are not sufficiently proven from the selected identity references.

## Notes

- Wiki and memory files are updated after final audit generation.

## Human Truth

Some feelings change in the middle of an ordinary moment, and steady love is not the person who rushes the mood away; it is the hand that stays easy to reach.

## Learning

- Keep the desi storybook / photo-rooted style as the default for memory-led carousels.
- Preserve source-photo objects before adding decorative story elements.
- Preserve Aachu/Zuv identity references across every generated slide.
- Generate model-native publishable slides when typography, face quality, outfit continuity, and composition must match the reference examples.

## Caption

some moods change mid-walk.

one minute soft.
one minute quiet.
one hand still reaching.

love is not fixing the weather.
sometimes it is slowing down enough to keep pace.

love keeps pace.
