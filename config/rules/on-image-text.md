ON-IMAGE TEXT: the exact text written in `slides.md` (or `slides.json`) for the current slide must appear in the illustration, baked into the artwork as readable hand-drawn typography.

Placement: clean warm upper-middle negative space. Must not cover faces, hands, important props, or emotional gestures.

Typography: slightly imperfect, warm black or charcoal, airy, human, integrated into the paper. Matches the observational-intimacy-premium handwritten lettering style. Reads as part of the illustration, not as a digital overlay, poster title, or separate graphic layer.

Preserve spelling, line breaks, punctuation, capitalization, and wording exactly as written in `slides.md`.

HARD FAIL:
- any visible text in the image that is not in `slides.md` for that slide (no model-invented words, no extra labels, no random letters, no decorative quote fragments)
- typos, dropped letters, doubled letters, mis-spaced characters
- speech bubbles, captions overlay, watermarks, platform UI, social handles, view counters
- text covering a face, hand, or core gesture
- text rendered as flat digital font rather than handwritten ink

Acceptance: OCR pass on the rendered image returns the expected text from `slides.md` verbatim (after whitespace normalization). Failure to OCR-match blocks the slide from proof or final approval.
