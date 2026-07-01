# Visual Failure Audit - Road / Flyover Carousel

Status: NEEDS_FIXES

The batch was incorrectly passed. It should have been rejected as soon as the contact sheet showed that the images were only mechanically compliant, not story-ready.

## Why The False Pass Happened

I checked the wrong things first:
- dimensions were exact 1080x1350;
- text was present inside the images;
- the style broadly resembled watercolor A Story references;
- the top-right brandmark existed.

Those checks are necessary but not sufficient. I did not run a strict enough scroller POV visual read: "would a cold viewer instantly understand the road beat, feel the turn, laugh at the +17, and want to tag someone?"

## Actual Failure

The carousel does not yet create a strong public relationship mirror through visual receipts. It has the idea, but the generated images do not consistently turn that idea into crisp moments.

Slide-level failures:
- Slide 1: `seedha?` is too small/edge-adjacent, and the split does not feel like an instantly confusing decision.
- Slide 2: the missed-left-cut receipt is present but not sharp enough; it feels like another road beauty shot instead of "oh no, we missed it."
- Slide 3: the car-interior beat is close, but the couple identity and acting are not strong enough to be final Aachu/Zuv.
- Slide 4: `seedha.` is too small/edge-adjacent, and the right-cut decision is not clear enough at swipe speed.
- Slide 5: the "not you / not me / this" idea is visible, but it needs cleaner road blame and stronger togetherness.
- Slide 6: the `+17 minutes` idea is the strongest visual beat, but it still needs to be treated as the psychological stop, not just a pretty map-like loop.
- Slide 7: the emotional payoff is weak; it does not clearly show one annoyed, one laughing, both now sharing the story.
- Slide 8: the CTA is readable, but the image lacks final-slide punch and reads too calm/postcard-like.

## Corrected Gate

A future pass cannot be approved by "text exists + dimensions correct." It must pass:
- exact 1080x1350;
- text inside the image and readable at phone size;
- top-right brandmark, per creator override;
- instant road geometry read;
- no repeated pretty-road filler;
- clear car position and consequence per slide;
- Aachu/Zuv relationship acting where characters appear;
- slide 6 as the psychological stop;
- slide 7 as the earned team payoff;
- slide 8 as a taggable CTA, not a postcard.

## Next Move

Do not regenerate all 8 blindly. Rebuild the visual system from one proof slide first, preferably slide 6 or slide 7, then use that approved proof to drive the batch.
