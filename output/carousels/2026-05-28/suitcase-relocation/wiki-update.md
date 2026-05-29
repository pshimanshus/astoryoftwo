# Suitcase Relocation - Carousel Quality Update

last_updated: 2026-05-28
confidence: 0.7
sources:
- output/carousels/2026-05-28/suitcase-relocation/manifest.json
- output/carousels/2026-05-28/suitcase-relocation/prompt-pack.json
- output/carousels/2026-05-28/suitcase-relocation/final-audit.json

## Status

Final audit: NEEDS_FIXES

## Issues

- REQ-FINAL-IMAGES-001: Final generated carousel images are packaged as separate native 4:5 and 9:16 outputs, not local placeholders
- REQ-MODEL-NATIVE-TEXT-001: Default final slides include rendered copy and brandmark inside both final/ and final-reels-stories/
- REQ-VISUAL-QA-001: Structured face and storyboard visual QA gate passes with evidence
- asset_reviewer: Missing final generated images: output/carousels/2026-05-28/suitcase-relocation/final/slide-01.png, output/carousels/2026-05-28/suitcase-relocation/final/slide-02.png, output/carousels/2026-05-28/suitcase-relocation/final/slide-03.png, output/carousels/2026-05-28/suitcase-relocation/final/slide-04.png, output/carousels/2026-05-28/suitcase-relocation/final/slide-05.png, output/carousels/2026-05-28/suitcase-relocation/final/slide-06.png, output/carousels/2026-05-28/suitcase-relocation/final/slide-07.png

## Notes

- No story photos supplied; identity references and the creative brief are the source of truth.
- Wiki and memory files are updated after final audit generation.
- render_assets=False

## Human Truth

Some couples do not pack light; they overprepare together, create the suitcase mess together, and choose a harmless villain instead of blaming each other.

## Learning

- Keep the romantic watercolor-and-ink / identity-rooted style as the default for memory-led carousels.
- Preserve source-photo objects before adding decorative story elements.
- Preserve Aachu/Zuv identity references across every generated slide.
- Carry the successful-carousel standard as open agent alignment, not a keyword checklist.
- Generate model-native publishable slides when typography, face quality, outfit continuity, and composition must match the reference examples.

## Caption

some couples pack for a trip.
some couples pack for every possible version of the trip.

the outfit options.
the charger pile.
the suitcase negotiation.
the toothbrushes, obviously forgotten.

and after all that,
nobody blamed each other.
only the zip.

send this to the person who says pack light and still sits on the suitcase with you.
