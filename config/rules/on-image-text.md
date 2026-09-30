ON-IMAGE TEXT — the exact text written in `slides.md` (or `slides.json`) for the current slide must appear in the final illustration image, baked into the final raster as readable hand-drawn typography. Text completes the scene; text must not carry the scene.

CREATOR HARD RULE
- Never generate an accidentally textless @a.storyof.two proof, concept illustration, carousel slide, or final illustration. An intentional wordless story beat is allowed only when `copy_mode: wordless` is locked in `slides.json`, the physical scene and brandmark remain present, and pixel QA records that no story text was expected.
- If slide copy is not yet locked, first lock an explicit proof line or slide line, then generate with that exact text baked into the artwork.
- Identity-only proofs without on-image text are blocked. Test identity, style, scene, and typography together from the first proof.
- If the image model cannot reliably render exact long text, the package must block or retry with a text-bearing generation prompt. A local typography repair may only correct an already text-bearing raster; it must never create, keep, or rely on a textless generated image.
- The only text besides the approved on-image text is the tiny top-right `@a.storyof.two` brandmark.
- Proof text must be scene-native, conversational, and approved against the
  raw moment before generation. Reject preachy thesis lines, moral summaries,
  generic romantic captions, or title-card copy when the scene needs deadpan
  lived behavior.

STAGE-SCENE / VISUAL RECEIPT
- The illustration must visually prove the exact line through behavior, object
  movement, body position, expression, contradiction, ritual, or aftermath.
- Text completes the scene; text must not carry the scene. If the slide becomes
  a quote card when the text is hidden, repair the scene before generation.
- Clothing state, props, hands, eye-line, and body position must not contradict
  the approved ON-IMAGE TEXT.

SOURCE OF TRUTH
- `slides.md` (or `slides.json`) is the canonical text source.
- Preserve spelling, line breaks, punctuation, capitalization, and wording exactly. No paraphrasing, no expansion, no abbreviation.
- If `slides.md` is empty for a non-@a.storyof.two utility asset, the slide has no on-image text. Do not invent any.
- For @a.storyof.two proof/final illustrations, an empty text source blocks generation until exact proof/slide text is supplied or an intentional `copy_mode: wordless` beat is locked.

PLACEMENT
- Clean warm upper-middle negative space. Generous breathing room around the text.
- Text must not cover faces, hands, important props, or core emotional gestures.
- The upper-middle zone scales differently by canvas. Verify text at
  phone-screen size in every current-request format: 3:4 by default, 9:16 and/or
  1:1 only when explicitly locked.

TYPOGRAPHY
- Handwritten lettering style is evidenced by the active Cinematic
  Observational Watercolor v1 bundle:
  `config/references/style-lock/cinematic-observational-watercolor-v1/`.
- Warm black or charcoal ink. Slightly imperfect, airy, human.
- Integrated into the paper — reads as part of the final illustration image, not as a separate quote-card layer, poster title, or platform overlay.
- Controlled typography repair is allowed only on an already text-bearing raster, and only when the final raster still looks like one A Story illustration with native paper, spacing, and hand-drawn/storybook typography.
- No flat digital font. No platform UI typography.

HARD FAIL — regenerate, do not accept
- Any visible text in the image that is not in `slides.md` for that slide.
- Model-invented words, extra labels, random letters, decorative quote fragments, mottos, taglines.
- Preachy or thesis-like text used as a proof line when the creator has supplied
  a literal daily-life moment that needs scene-native copy.
- Typos, dropped letters, doubled letters, mis-spaced characters.
- Speech bubbles, caption overlays, watermarks (other than the top-right `@a.storyof.two` brandmark), platform UI, social handles, view counters.
- Text covering a face, hand, or core gesture.
- Text rendered as flat digital font rather than handwritten ink.
- Text bleeding into the lower frame where the couple sits.
- Same-text rendering across two slides that have different `slides.md` content (paste-and-tweak failure).
- A package marking textless source art as final, or presenting source art separately from the text-bearing final image.

REFERENCE ADAPTATION HARD FAIL
- Inspiration screenshots provide dialogue, emotion, blocking, gesture, and scene evidence only.
- No split-screen divider, vertical center line, phone UI, carousel dots, social handle, engagement icon, black app chrome, or screenshot layout device may appear in final art unless the creator explicitly asks for that graphic device as story content.
- When a reference uses split-screen or app-layout grammar, translate the relationship idea into one premium lived Aachu/Zuv scene with clean negative space. Use architecture, eye-line, bed placement, doorway, furniture, or distance to separate beats naturally instead of drawing a hard graphic divider.
- If the output looks like a screenshot redraw, quote-card, meme template, or
  UI-inspired composition instead of a Cinematic Observational Watercolor
  story frame, regenerate.

EXACT-TEXT ACCEPTANCE (inside the existing proof/final pixel QA)
- Codex must open the actual decoded candidate image, inspect the complete frame for lettering, and transcribe the visible slide copy word by word into `observed_text`. Never populate that field by copying the expected prompt text without reading the pixels.
- `pipeline/stages/carousel_pixel_qa.py` deterministically compares that transcription with the locked copy, including punctuation and capitalization. Wrong, missing, reordered, or extra words fail. The transcription and review must bind to the inspected asset SHA-256; a text assertion alone does not prove that the image was inspected.
- New reviews record `unexpected_visible_text: []` only after checking the whole frame for invented lettering outside the locked copy and permitted brandmark. Record any extra lettering in that array; a nonempty or malformed array fails the same existing finish check. Older hash-bound QA remains readable and is not silently rewritten.
- The exact `@a.storyof.two` brandmark is inspected separately. Empty story copy blocks generation unless the current slide explicitly locks `copy_mode: wordless`; wordless slides still require a physical action, no invented story lettering, and the brandmark.
- `pipeline/agentic/checks/ocr_text.py` is a legacy optional diagnostic, not the native lifecycle's pixel-perception authority. Its fuzzy score cannot certify exact copy, and an unavailable OCR backend must never be represented as a successful text check. Do not add its heavyweight dependency or a separate approval stop to the carousel hot path.
- Perception remains an accountable Codex pixel-review step; deterministic comparison validates the authored transcription, not independent OCR of the raster. A failed text review blocks proof approval/final packaging until repaired or explicitly excepted by the creator with a recorded reason.

ANTI-DRIFT NOTES (lessons from real rejections)
- 2026-05-30 phone-prank Slide 03: text said "YOUR SOCKS ON BEFORE YOUR PANTS" but Zuv was already wearing pants in the illustration. The hard fail wasn't typography — it was scene/text contradiction. The visible action must prove the line.
- Models often invent decorative micro-text in scarves, scarves, signs, mug rims, and notebook covers. Default the prompt to "no text anywhere in the image except the exact ON-IMAGE TEXT for this slide and the top-right brandmark."
- 2026-06-15 intimacy-carousel correction updated by 2026-06-30 marriage run RCA: exact text and the top-right brandmark must be present in every generated @a.storyof.two proof, concept, carousel slide, or final. If exact text cannot be rendered, block or retry; never generate a textless workaround image.
