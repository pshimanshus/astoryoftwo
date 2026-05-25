# Pipeline Repair Smoke Test - Carousel Quality Update

last_updated: 2026-05-25
confidence: 0.7
sources:
- output/carousels/2026-05-25/pipeline-repair-smoke-test/manifest.json
- output/carousels/2026-05-25/pipeline-repair-smoke-test/prompt-pack.json
- output/carousels/2026-05-25/pipeline-repair-smoke-test/final-audit.json

## Status

Final audit: NEEDS_FIXES

## Issues

- REQ-VISUAL-PLAN-QUALITY-001: Per-slide visual screen passes before image generation
- REQ-FINAL-IMAGES-001: Final generated carousel images are packaged as separate native 4:5 and 9:16 outputs, not local placeholders
- REQ-MODEL-NATIVE-TEXT-001: Default final slides include rendered copy and brandmark inside both final/ and final-reels-stories/
- REQ-VISUAL-QA-001: Structured face and storyboard visual QA gate passes with evidence
- visual_reviewer: Slide 4 must prove Zuv/Himanshu knowingly participates in the bit.; Slide 5 must turn the wallet joke into quiet care by showing extra cash prepared.
- asset_reviewer: Missing final generated images: output/carousels/2026-05-25/pipeline-repair-smoke-test/final/slide-01.png, output/carousels/2026-05-25/pipeline-repair-smoke-test/final/slide-02.png, output/carousels/2026-05-25/pipeline-repair-smoke-test/final/slide-03.png, output/carousels/2026-05-25/pipeline-repair-smoke-test/final/slide-04.png, output/carousels/2026-05-25/pipeline-repair-smoke-test/final/slide-05.png

## Notes

- No story photos supplied; identity references and the creative brief are the source of truth.
- Wiki and memory files are updated after final audit generation.
- render_assets=False

## Human Truth

The best couples do not only tolerate each other's tiny nonsense; they quietly make room for it, budget for it, and turn the bit into a shared language.

## Learning

- Keep the desi storybook / photo-rooted style as the default for memory-led carousels.
- Preserve source-photo objects before adding decorative story elements.
- Preserve Aachu/Zuv identity references across every generated slide.
- Generate model-native publishable slides when typography, face quality, outfit continuity, and composition must match the reference examples.

## Caption

Every couple has one finance minister.
And one person pretending not to notice.

She said bas 500.
Then checked the backup pocket.

He saw everything.
He still pretended to sleep.

By morning, he kept extra there.

Maybe love is not always grand gestures.
Sometimes it is quietly budgeting for each other's nonsense.

Send this to the person who became your alibi, not your audience.
