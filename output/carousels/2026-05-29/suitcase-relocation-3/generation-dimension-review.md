# Generation Dimension Review

status: BLOCKED_DIMENSION_NONCOMPLIANCE

The current generated image batch cannot be packaged as final.

Required source contract:

- Instagram post: native 4:5 source, final upload normalization to 1080x1350.
- Reels/Stories: separate native 9:16 source, final upload normalization to 1080x1920.
- No crop, pad, contain-on-paper, or one-format-derived-from-another workaround.

Accepted only for source aspect:

- 1122x1402 files are eligible as 4:5 Instagram-post source candidates, but still need story/text/face/slide-order QA before use.

Rejected:

- 977x1610, 992x1586, 1003x1568, and 1024x1535 outputs are wrong-ratio sources. They are neither native 4:5 nor native 9:16.

Packaging gate:

- `package_codex_builtin_outputs` now rejects wrong native source aspect before copying or writing finals.
- This carousel remains blocked until all 7 Instagram-post sources and all 7 separate Reels/Stories sources are native aspect.
