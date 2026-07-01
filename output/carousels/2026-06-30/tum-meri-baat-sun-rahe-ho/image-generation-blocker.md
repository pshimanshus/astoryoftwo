# Image Generation Blocker

status: BLOCKED_FOR_NATIVE_SIZE

The all-slide final generation step is blocked because the available built-in image generation route is not preserving the repo-required native Instagram post size.

Root cause:

- The repo documents, prompt files, and package contracts request `1080x1350`.
- The current built-in `image_gen` call does not expose/enforce a native pixel-size parameter.
- Because of that, prompt text like "Generate native 1080x1350 px" is advisory to the model, not a hard renderer/export constraint.
- The generator is selecting its own raster sizes: earlier proof attempts returned `1122x1402`, and the latest real-reference attempt returned `1003x1568`.

Evidence:

- Required native size: `1080x1350`
- Attempt 1 output: `1122x1402`
- Attempt 2 output: `1122x1402`
- Attempt 3 output, generated from a diagnostic-only blank edit target: `1122x1402`
- Attempt 4 output, generated from the real selected identity/style references: `1003x1568`

Rejected proof files:

- `rejected/native-size-fail/slide-05-proof-v1-1122x1402.png`
- `rejected/native-size-fail/slide-05-proof-v2-1122x1402.png`
- `rejected/native-size-fail/slide-05-proof-v3-edit-target-1122x1402.png`
- `rejected/native-size-fail/slide-05-proof-v4-real-refs-1003x1568.png`

The full batch must not be generated through this route because every resulting slide is expected to fail the same hard size gate. The rejected proofs must not be cropped, padded, stretched, resized, or repackaged as finals.

The blank edit-target experiment was not a valid repo plan. It has been removed from the package because blank-page editing violates the required identity/style/story generation setup.

API fallback check:

- Current OpenAI `gpt-image-2` custom sizes require both edges to be multiples of 16, so exact `1080x1350` is not a valid request size.
- Earlier GPT Image model sizes are standard portrait/landscape/square sizes, not exact `1080x1350`.

The seven Instagram post prompts and the wardrobe plan remain ready. Continue only when a generation path can hard-enforce true native `1080x1350` images with the selected identity/style references and exact on-image text.
