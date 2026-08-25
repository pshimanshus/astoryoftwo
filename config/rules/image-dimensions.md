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

- Every @a.storyof.two proof illustration, concept illustration, single-slide
  output, and default Instagram post/carousel slide must finish exactly as:
  `1080x1440 px`

- Keep the generation prompt requesting exact `1080x1440`; do not advertise a
  fallback canvas or claim that a returned source is already the final.

- Observed built-in-runtime accommodation, `instagram_post` only: the repo may
  quarantine an untouched returned source at any exact 3:4 integer size from
  `1080x1440` through `1440x1920`, inclusive. Width must be from 1080 through
  1440, height from 1440 through 1920, and `width * 4 == height * 3`.
  This is an observed current-runtime accommodation, not a published model or
  platform guarantee.

- Bind the untouched source path, SHA-256, width, and height before processing.
  If it is larger than `1080x1440`, proportionally downsample exactly once to
  `1080x1440`. Never crop, pad, stretch, upscale, change ratio, or resample more
  than once. If already exact target size, preserve the bytes.

- Proof QA and creator approval bind the normalized `1080x1440` proof bytes
  while retaining the source binding. Reuse those approved normalized proof
  bytes as the final candidate; never regenerate or downsample the proof again.

- If the creator explicitly asks for Instagram Story, Stories, Reel, or Reels format, generate natively as:
  `1080x1920 px`

- If the creator explicitly asks for square format, generate natively as:
  `1080x1080 px`

- Reject any generated proof, concept, single-slide, post, story, or reel source
  whose ratio or dimensions fall outside the applicable contract.

- Do not accept, present, or continue from a wrong-dimension image as a proof, even if the identity, style, story, or text looks good.

- Do not repair a failed generation by cropping, padding, stretching, upscaling,
  or arbitrary resizing. The only allowed transform is one proportional
  downsample from an accepted larger 3:4 `instagram_post` source to exact
  `1080x1440`.

- Check dimensions immediately after generation with `file`, PIL, or the matching size check:
  - Post / carousel source: exact 3:4, from `1080x1440` through `1440x1920`
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
- Any proof/concept/single-slide/post source below `1080x1440`, above
  `1440x1920`, or not exact 3:4 is rejected.
- Any transform other than the single allowed proportional downsample is
  rejected, including crop, pad, stretch, upscale, ratio change, or a second
  resample.
- Any proof/concept/single-slide/post final export that is not exactly
  `1080x1440` is rejected.
- Any Story/Reel output that is not exactly `1080x1920` is rejected.
- Any Square output that is not exactly `1080x1080` is rejected.
