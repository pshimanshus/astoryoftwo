# Visual QA

Status: PROMPTS_REPAIRED, GENERATION STILL BLOCKED FOR NATIVE SIZE.

Creator correction applied:

- Same clothes across all slides.
- One continuous home dinner-table setup: Aachu and Zuv sit facing each other at a small 4-seater table.
- Visual storytelling now depends on posture, eye-line, hands, phone movement, table silence, and a folded napkin gesture.
- Removed bedroom/sofa/bed/cushion staging.
- Removed wardrobe changes between slides.
- Strengthened typography lock to the standard Observational Intimacy Premium @a.storyof.two handwritten lettering.
- Added explicit eye-line lock after creator screenshot feedback: when Zuv is visible, his face angle and pupils must land on Aachu, not on the phone, table, camera, window, or empty space.

Repaired shot ladder:

1. Wide establishing dinner-table shot.
2. Aachu-led over-Zuv-shoulder/table-level suspicion shot.
3. Zuv-led phone/autopilot confidence shot.
4. Across-table trap shot.
5. Reaction freeze across the table.
6. Soft aftermath with phone face-down.
7. Folded napkin affection gesture.

Rejected generated candidates remain rejected:

- `rejected/native-size-fail/slide-05-proof-v1-1122x1402.png`
- `rejected/native-size-fail/slide-05-proof-v2-1122x1402.png`
- `rejected/native-size-fail/slide-05-proof-v3-edit-target-1122x1402.png`
- `rejected/native-size-fail/slide-05-proof-v4-real-refs-1003x1568.png`
- `rejected/native-size-fail/slide-05-proof-v5-dinner-table-1122x1402.png`
- `generated-candidates/non-native/slide-01-candidate-971x1619.png`
- `generated-candidates/non-native/slide-02-candidate-986x1595.png`
- `generated-candidates/non-native/slide-03-candidate-999x1575.png`
- `generated-candidates/non-native/slide-04-candidate-992x1586.png`
- `generated-candidates/non-native/slide-06-candidate-eyeline-v1-971x1619.png`
- `generated-candidates/non-native/slide-07-candidate-eyeline-v1-1122x1402.png`

Latest candidate note:

- Slide 6 and slide 7 were regenerated with the eye-line lock. Visually, the core correction is improved: Zuv is directed toward Aachu instead of the phone/table. They still fail native dimensions and cannot be final assets.

Full-carousel candidate pass, 2026-07-02:

- `generated-candidates/non-native/slide-01-full-carousel-v1-979x1606.png`
- `generated-candidates/non-native/slide-02-full-carousel-v1-1092x1440.png`
- `generated-candidates/non-native/slide-03-full-carousel-v1-978x1608.png`
- `generated-candidates/non-native/slide-04-full-carousel-v1-983x1600.png`
- `generated-candidates/non-native/slide-05-full-carousel-v1-999x1575.png`
- `generated-candidates/non-native/slide-06-full-carousel-v1-1000x1573.png`
- `generated-candidates/non-native/slide-07-full-carousel-v1-999x1574.png`

Full-pass result: all seven slides were generated from the repaired dinner-table prompts with same wardrobe, single setting, and explicit Zuv-to-Aachu eye-line lock. All seven remain non-native dimension candidates, so they are not publishable finals.

Accepted final folders remain empty:

- `final/`
- `final-reels-stories/`

Next valid action: generate one new proof from the repaired slide 5 dinner-table prompt through a backend/export worker that hard-enforces `1440x1920` source with exact `1080x1440` final export; only then continue the remaining slides. Do not crop, pad, stretch, resize, or package non-native outputs as finals.
