# Discarded Built-In Generation Attempt

date: 2026-05-18
status: DISCARDED

The built-in image-generation fallback was started after the project legacy API
route failed with `legacy_api_disabled`.

This attempt is not accepted as final carousel art because the creator clarified
that identity images must always be passed as actual reference image inputs, not
only described in text prompts. Face consistency is the hard gate.

Generated files left in the Codex default image folder, not packaged:

- /Users/himanshusharma/.codex/generated_images/019e3bb6-7055-7160-a2a1-5d34e749e528/ig_0f78dcd0ac701998016a0b378932288191b6e19f1df00ff40a.png
- /Users/himanshusharma/.codex/generated_images/019e3bb6-7055-7160-a2a1-5d34e749e528/ig_0f78dcd0ac701998016a0b374b7b3081919a154f22af9fc7c5.png

Final image generation for this package should resume only through a path that
attaches the selected identity images as real image references for every slide.
