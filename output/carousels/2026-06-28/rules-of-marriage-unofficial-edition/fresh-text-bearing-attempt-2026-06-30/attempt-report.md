# Fresh Text-Bearing Attempt Report

status: BLOCKED_NOT_FINAL
date: 2026-06-30

## Scope

Proof-first retry for Slide 02 after repairing the active prompt to fix:

- hand/blanket anatomy;
- exact on-image text;
- top-right `@a.storyof.two` brandmark;
- neutral warm ivory/off-white premium paper tone.

## Candidate Files

- `instagram-post/slide-02.png`
- `instagram-post/slide-02-retry-native-size.png`

## Result

Both generated candidates include the slide text and top-right brandmark, and
the hand/blanket anatomy is no longer the original under-bed failure.

However, both saved PNGs are `1122x1402`, not native `1080x1350`. Per
`config/rules/image-dimensions.md`, these are candidates/rejections, not
finals. They must not be copied into `final/` or used to clear the existing
package blockers.

## Next Action

Use an image-generation path that can produce exact native `1080x1350` and
`1080x1920` files, or keep the package blocked. Do not resize, crop, pad, or
stretch these candidates into compliance.
