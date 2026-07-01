ON-IMAGE TEXT — the exact text written in `slides.md` (or `slides.json`) for the current slide must appear in the final illustration image, baked into the final raster as readable hand-drawn typography. Text completes the scene; text must not carry the scene.

CREATOR HARD RULE
- Never generate a textless @a.storyof.two proof, concept illustration, carousel slide, or final illustration.
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
- For @a.storyof.two proof/final illustrations, an empty text source blocks generation until exact proof/slide text is supplied or locked.

PLACEMENT
- Clean warm upper-middle negative space. Generous breathing room around the text.
- Text must not cover faces, hands, important props, or core emotional gestures.
- For 4:5 (Instagram post) and 9:16 (Reels/Stories), the upper-middle zone scales differently — verify text remains legible at phone-screen size in both native formats.

TYPOGRAPHY
- Handwritten lettering style locked to the Observational Intimacy Premium reference bundle: `config/references/style-lock/observational-intimacy-premium/`.
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
- If the output looks like a screenshot redraw, quote-card, meme template, or UI-inspired composition instead of an Observational Intimacy Premium illustration, regenerate.

DETERMINISTIC ACCEPTANCE (used by pipeline/agentic/checks/ocr_text.py)
- OCR pass on the rendered image returns the expected text from `slides.md` after whitespace normalization, with at least 85% similarity (fuzzy partial match) to account for normal handwritten rendering variation.
- Empty expected text always passes (the slide has no on-image text).
- A failure means the slide cannot proceed to proof approval or final packaging until regenerated or human-overridden with a recorded reason.

ANTI-DRIFT NOTES (lessons from real rejections)
- 2026-05-30 phone-prank Slide 03: text said "YOUR SOCKS ON BEFORE YOUR PANTS" but Zuv was already wearing pants in the illustration. The hard fail wasn't typography — it was scene/text contradiction. The visible action must prove the line.
- Models often invent decorative micro-text in scarves, scarves, signs, mug rims, and notebook covers. Default the prompt to "no text anywhere in the image except the exact ON-IMAGE TEXT for this slide and the top-right brandmark."
- 2026-06-15 intimacy-carousel correction updated by 2026-06-30 marriage run RCA: exact text and the top-right brandmark must be present in every generated @a.storyof.two proof, concept, carousel slide, or final. If exact text cannot be rendered, block or retry; never generate a textless workaround image.
