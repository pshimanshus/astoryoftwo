IMAGE DIMENSIONS — hard gates for @a.storyof.two illustration generation.

CREATOR HARD RULE

- FORMAT INFERENCE PREFLIGHT: before any image generation or export, identify
  the requested canvas from the current creator instruction, current attached
  references, and any immediate correction in the chat. If the creator removes,
  rejects, or corrects a format/aspect/size decision, that correction overrides
  every repo default below for the current task.

- Do not silently snap back to `3:4`, `9:16`, feed, Story, Reel, square, or
  multi-format output from repo defaults after the creator has corrected the
  format. If the current canvas is not explicit after a correction, stop and ask
  for the exact canvas instead of generating.

- Every @a.storyof.two proof illustration, concept illustration,
  single-slide output, and default Instagram post/carousel slide must finish
  as an Instagram Feed Portrait Post export:
  `1080x1440 px`

- For image models that cannot hard-enforce `1080x1440` directly, generate the
  Instagram post/carousel source as native `1440x1920 px` (same 3:4 ratio), then
  export proportionally to exact `1080x1440 px`. This deterministic export is
  allowed only when the source and final share the exact same aspect ratio. It
  is not a crop, pad, stretch, or format conversion.

- If the creator explicitly asks for Instagram Story, Stories, Reel, or Reels format, generate natively as:
  `1080x1920 px`

- If the creator explicitly asks for square format, generate natively as:
  `1080x1080 px`

- Reject any generated proof, concept, single-slide, post, story, or reel image
  whose pixel dimensions do not match an approved source size or the requested
  final format.

- Do not accept, present, or continue from a wrong-dimension image as a proof, even if the identity, style, story, or text looks good.

- Do not repair a failed generation by cropping, padding, stretching, or
  arbitrary resizing. Regenerate at the approved source dimensions. The only
  allowed post-processing for carousel/post outputs is proportional export from
  `1440x1920` source to exact `1080x1440` final.

- Check dimensions immediately after generation with `file`, PIL, or the matching size check:
  - Post / carousel source: `1440x1920`
  - Post / carousel final export: `1080x1440`
  - Story / Reel: `1080x1920`
  - Square: `1080x1080`

DEFAULT FORMAT RULE

- If the creator says “post,” “Instagram post,” “carousel slide,” “single-slide,” “proof,” or “concept” without naming Story/Reel/Square, use `1080x1440`.
- This default applies only when the creator has not supplied a current
  correction, reference screenshot, or prior accepted screen that implies a
  different canvas. Never use this default to override the creator's latest
  correction.

STORY / REEL EXCEPTION

- If the creator explicitly asks for Story, Stories, Reel, or Reels, use `1080x1920`.
- Do not generate Story/Reel outputs at post size.
- Do not generate post/carousel outputs at Story/Reel size unless explicitly requested.

HARD FAIL

- Generating an unrequested Story/Reel/long variant, feed/post variant, square
  variant, or "all formats" batch because a repo workflow mentions it.
- Continuing generation after the creator says the format decision was wrong
  without first locking the exact requested canvas.
- Any proof/concept/single-slide/post source that is not `1440x1920` or
  already-exact `1080x1440` is rejected.
- Any proof/concept/single-slide/post final export that is not exactly
  `1080x1440` is rejected.
- Any Story/Reel output that is not exactly `1080x1920` is rejected.
- Any Square output that is not exactly `1080x1080` is rejected.
