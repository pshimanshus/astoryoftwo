# Image Generation Blocker

status: BLOCKED_EXACT_NATIVE_DIMENSIONS

The corrected slide 06 proofs fixed the earlier visual mistakes, but both returned `1122x1402` instead of exact `1080x1350`.

Rejected proof evidence:

- `proofs/slide-06-proof-4x5-rejected-1122x1402-v1.png`
- `proofs/slide-06-proof-4x5-rejected-1122x1402-v2.png`

Why blocked:

- `config/rules/image-dimensions.md` requires default carousel slides to be generated natively at exactly `1080x1350`.
- It also forbids fixing wrong-dimension outputs by resizing, cropping, padding, or stretching.
- The built-in image tool does not expose an exact pixel-size parameter.
- CLI `gpt-image-2` is not a clean exact-size fallback because its dimensions must be multiples of 16, and `1080x1350` is not.

Brandmark correction:

- Source prompt/rule surfaces have been updated to top-right `@a.storyof.two` per creator instruction.

No final PNGs were accepted.
