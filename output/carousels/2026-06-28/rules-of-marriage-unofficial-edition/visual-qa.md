# Visual QA

Status: TEXT_BEARING_CANDIDATES_CREATED__NOT_FINAL

## Creator Correction

No @a.storyof.two carousel image may be generated without on-image text. For
this corrected pass, the slide copy and the tiny top-right `@a.storyof.two`
brandmark were requested as part of each generated illustration. No separate
post-generation text overlay or textless source pass was used.

## Corrected Candidate Set

- Text-bearing generated slides: `source/text-bearing/slide-01-text-generated.png` through `source/text-bearing/slide-09-text-generated.png`
- Contact sheet: `contact-sheets/text-generated-contact-sheet.png`
- QA manifest: `text-generated-candidates.json`
- Rejected textless sources: `rejected-images/textless-hard-fail-2026-06-28/`

## Dimension Gate

All nine corrected candidates fail the native `1080x1350` gate. The built-in
image generator returned mixed sizes:

- Slide 01: `997x1577`
- Slide 02: `1122x1402`
- Slide 03: `1122x1402`
- Slide 04: `1003x1568`
- Slide 05: `1122x1402`
- Slide 06: `1122x1402`
- Slide 07: `1003x1568`
- Slide 08: `1023x1537`
- Slide 09: `997x1577`

No candidate was cropped, padded, stretched, or resized into a fake final.

## Text QA

Every corrected candidate has visible on-image text generated into the
illustration itself. Manual review from the contact sheet flags remaining exact
copy risks:

- Slides 02, 05, and 06 reflow long lines compared with `slides.json`.
- Slides 03 and 08 may use straight quote glyphs instead of the exact curly
  quote glyphs in `slides.json`.
- Slides 04 and 09 have small prop-detail risks that could read as accidental
  extra text.

OCR validation could not run because `tesseract` and `pytesseract` are not
available in this environment.

## Verdict

This is the corrected text-bearing illustration pass, not a publish-pass final
carousel. To publish cleanly, regenerate through an image path that can guarantee
native `1080x1350` while baking the exact `slides.json` text and top-right
brandmark into each illustration from the start.
