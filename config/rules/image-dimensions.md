IMAGE DIMENSIONS — hard gates for @a.storyof.two illustration generation.

CREATOR HARD RULE

- Every @a.storyof.two proof illustration, concept illustration, single-slide output, and default Instagram post/carousel slide must be generated natively as an Instagram Feed Portrait Post:
  `1080x1350 px`

- If the creator explicitly asks for Instagram Story, Stories, Reel, or Reels format, generate natively as:
  `1080x1920 px`

- If the creator explicitly asks for square format, generate natively as:
  `1080x1080 px`

- Reject any generated proof, concept, single-slide, post, story, or reel image whose pixel dimensions do not exactly match the requested format.

- Do not accept, present, or continue from a wrong-dimension image as a proof, even if the identity, style, story, or text looks good.

- Do not repair a failed generation by cropping, padding, stretching, or resizing. Regenerate natively at the correct requested dimensions.

- Check dimensions immediately after generation with `file`, PIL, or the matching size check:
  - Post / carousel slide: `1080x1350`
  - Story / Reel: `1080x1920`
  - Square: `1080x1080`

DEFAULT FORMAT RULE

- If the creator says “post,” “Instagram post,” “carousel slide,” “single-slide,” “proof,” or “concept” without naming Story/Reel/Square, use `1080x1350`.

STORY / REEL EXCEPTION

- If the creator explicitly asks for Story, Stories, Reel, or Reels, use `1080x1920`.
- Do not generate Story/Reel outputs at post size.
- Do not generate post/carousel outputs at Story/Reel size unless explicitly requested.

HARD FAIL

- Any proof/concept/single-slide/post output that is not exactly `1080x1350` is rejected.
- Any Story/Reel output that is not exactly `1080x1920` is rejected.
- Any Square output that is not exactly `1080x1080` is rejected.