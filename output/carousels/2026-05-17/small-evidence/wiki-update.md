# Small Evidence - Carousel Quality Update

last_updated: 2026-05-17
confidence: 0.7
sources:
- output/carousels/2026-05-17/small-evidence/manifest.json
- output/carousels/2026-05-17/small-evidence/prompt-pack.json
- output/carousels/2026-05-17/small-evidence/final-audit.json

## Status

Final audit: NEEDS_FIXES

## Issues

- REQ-FINAL-IMAGES-001: Final generated carousel images are packaged from approved generated art, not local placeholders
- REQ-MODEL-NATIVE-TEXT-001: Default final slides include model-rendered copy and brandmark inside final/slide-XX.png
- REQ-VISUAL-QA-001: Structured face and storyboard visual QA gate passes with evidence
- asset_reviewer: Missing final generated images: output/carousels/2026-05-17/small-evidence/final/slide-01.png, output/carousels/2026-05-17/small-evidence/final/slide-02.png, output/carousels/2026-05-17/small-evidence/final/slide-03.png, output/carousels/2026-05-17/small-evidence/final/slide-04.png, output/carousels/2026-05-17/small-evidence/final/slide-05.png

## Notes

- Wiki and memory files are updated after final audit generation.
- render_assets=False

## Human Truth

The story begins with one ordinary moment, then grows into shared comfort, travel, and the realization that even in the trip, the real subject is still the two of them.

## Learning

- Keep the desi storybook / photo-rooted style as the default for memory-led carousels.
- Preserve source-photo objects before adding decorative story elements.
- Preserve Aachu/Zuv identity references across every generated slide.
- Generate model-native publishable slides when typography, face quality, outfit continuity, and composition must match the reference examples.

## Caption

it started with one ordinary moment.

then somehow the story got bigger - the places, the views, the silence.

but the best part stayed the same:
it was still us.
