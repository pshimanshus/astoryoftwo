# Softness Under Fire - Carousel Quality Update

last_updated: 2026-05-19
confidence: 0.7
sources:
- output/carousels/2026-05-19/softness-under-fire-4/manifest.json
- output/carousels/2026-05-19/softness-under-fire-4/prompt-pack.json
- output/carousels/2026-05-19/softness-under-fire-4/final-audit.json

## Status

Final audit: NEEDS_FIXES

## Issues

- REQ-FINAL-IMAGES-001: Final generated carousel images are packaged as separate native 4:5 and 9:16 outputs, not local placeholders
- REQ-MODEL-NATIVE-TEXT-001: Default final slides include model-rendered copy and brandmark inside both final/ and final-reels-stories/
- REQ-VISUAL-QA-001: Structured face and storyboard visual QA gate passes with evidence
- asset_reviewer: Missing final generated images: output/carousels/2026-05-19/softness-under-fire-4/final/slide-01.png, output/carousels/2026-05-19/softness-under-fire-4/final/slide-02.png, output/carousels/2026-05-19/softness-under-fire-4/final/slide-03.png, output/carousels/2026-05-19/softness-under-fire-4/final/slide-04.png, output/carousels/2026-05-19/softness-under-fire-4/final/slide-05.png

## Notes

- Wiki and memory files are updated after final audit generation.
- render_assets=False

## Human Truth

Aachu's spicy tone is not the opposite of softness; it is often hurt, worry, and affection trying to protect itself, and Zuv's active love is hearing the feeling underneath before the moment becomes a fight.

## Learning

- Keep the desi storybook / photo-rooted style as the default for memory-led carousels.
- Preserve source-photo objects before adding decorative story elements.
- Preserve Aachu/Zuv identity references across every generated slide.
- Generate model-native publishable slides when typography, face quality, outfit continuity, and composition must match the reference examples.

## Caption

some people do not say love gently when they are hurt.

they say don't touch me,
but still hold your sleeve.

they say be safe like a warning,
because worry came out wearing attitude.

and the right person does not fight the fire first.
he hears the softness underneath.

maybe love is softness under fire.
