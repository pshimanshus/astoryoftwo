ON-IMAGE TEXT — the exact text written in `slides.md` (or `slides.json`) for the current slide must appear in the illustration, baked into the artwork as readable hand-drawn typography. Text completes the scene; text must not carry the scene.

SOURCE OF TRUTH
- `slides.md` (or `slides.json`) is the canonical text source.
- Preserve spelling, line breaks, punctuation, capitalization, and wording exactly. No paraphrasing, no expansion, no abbreviation.
- If `slides.md` is empty for a slide, the slide has no on-image text. Do not invent any.

PLACEMENT
- Clean warm upper-middle negative space. Generous breathing room around the text.
- Text must not cover faces, hands, important props, or core emotional gestures.
- For 4:5 (Instagram post) and 9:16 (Reels/Stories), the upper-middle zone scales differently — verify text remains legible at phone-screen size in both native formats.

TYPOGRAPHY
- Handwritten lettering style locked to the Observational Intimacy Premium reference bundle: `config/references/style-lock/observational-intimacy-premium/`.
- Warm black or charcoal ink. Slightly imperfect, airy, human.
- Integrated into the paper — reads as part of the illustration, not as a digital overlay, poster title, or separate graphic layer.
- No flat digital font. No platform UI typography.

HARD FAIL — regenerate, do not accept
- Any visible text in the image that is not in `slides.md` for that slide.
- Model-invented words, extra labels, random letters, decorative quote fragments, mottos, taglines.
- Typos, dropped letters, doubled letters, mis-spaced characters.
- Speech bubbles, caption overlays, watermarks (other than the bottom-right `@a.storyof.two` brandmark), platform UI, social handles, view counters.
- Text covering a face, hand, or core gesture.
- Text rendered as flat digital font rather than handwritten ink.
- Text bleeding into the lower frame where the couple sits.
- Same-text rendering across two slides that have different `slides.md` content (paste-and-tweak failure).

DETERMINISTIC ACCEPTANCE (used by pipeline/agentic/checks/ocr_text.py)
- OCR pass on the rendered image returns the expected text from `slides.md` after whitespace normalization, with at least 85% similarity (fuzzy partial match) to account for normal handwritten rendering variation.
- Empty expected text always passes (the slide has no on-image text).
- A failure means the slide cannot proceed to proof approval or final packaging until regenerated or human-overridden with a recorded reason.

ANTI-DRIFT NOTES (lessons from real rejections)
- 2026-05-30 phone-prank Slide 03: text said "YOUR SOCKS ON BEFORE YOUR PANTS" but Zuv was already wearing pants in the illustration. The hard fail wasn't typography — it was scene/text contradiction. The visible action must prove the line.
- Models often invent decorative micro-text in scarves, scarves, signs, mug rims, and notebook covers. Default the prompt to "no text anywhere in the image except the exact ON-IMAGE TEXT for this slide and the bottom-right brandmark."
