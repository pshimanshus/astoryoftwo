# Visual QA

Status: PASS_WITH_NOTES.

Final carousel images exist in `final/slide-01.png` through `final/slide-05.png` at 1080x1350.
Final Reels/Stories images exist in `final-reels-stories/slide-01.png` through `final-reels-stories/slide-05.png` at 1080x1920.
HD carousel master images exist in `final-hd/slide-01.png` through `final-hd/slide-05.png` at 2160x2700.

## Dimension And Export

- [x] Carousel exports use vertical 4:5 at 1080x1350.
- [x] Reels/Stories exports use vertical 9:16 at 1080x1920.
- [x] Artwork was not stretched or non-uniformly scaled.
- [x] 9:16 exports use warm-paper background extension where needed.
- [x] Contact sheets exist for both carousel and Reels/Stories exports.

## Storyboard Match

- [x] Slide 1 matches: He didn't marry low maintenance.
- [x] Slide 2 matches: He married "mujhe kuch nahi hua."
- [x] Slide 3 matches: One plan. Twelve backup plans.
- [x] Slide 4 matches: Drama. Snack. Silence. Smile.
- [x] Slide 5 matches: Maybe the chaos was home.

## Notes

- Slide 1 source was replaced with the cleaner regenerated composition that is less cropped and has more breathing room.
- The current workspace does not contain an `external API key`, so slides 2-5 were exported from existing model-native sources rather than regenerated.
- Future legacy API generations now default to native 4:5 and produce both 4:5 carousel and 9:16 Reels/Stories outputs.
