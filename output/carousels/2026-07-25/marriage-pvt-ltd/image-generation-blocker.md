# Image Generation Blocker

status: BLOCKED_VISUAL_QA
date: 2026-07-25
locked_format: instagram_post
required_final_dimensions: 1080x1440
proof_slide: 5

The built-in image generator returned `1086x1448` for the initial proof and
both targeted retries. The current image-dimensions rule rejects every attempt
and forbids cropping, padding, stretching, or arbitrary resizing into
compliance.

Quarantined attempts:

- `.internal/quarantine/slide-05/attempt-01/candidate.png`
- `.internal/quarantine/slide-05/attempt-02/candidate.png`
- `.internal/quarantine/slide-05/attempt-03/candidate.png`

No image was promoted into `final/`, and the remaining eight slides were not
generated. Continuing the batch would violate the proof-first and bounded-retry
contracts.

Next authorized path:

- Creator explicitly opts into the CLI/API fallback, which requires a locally
  configured `OPENAI_API_KEY`, so the image request can enforce an exact native
  canvas.
