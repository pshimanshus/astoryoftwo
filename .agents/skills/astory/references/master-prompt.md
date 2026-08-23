# A Story Of Two Illustration Master Prompt

last_updated: 2026-06-16
status: creator_locked_v4_gold_standard_identity_route
confidence: 1.0

Use this as the canonical compact prompt contract for `@a.storyof.two`
illustration-story generation. The active prompt must be a priority stack, not a
catalog of every possible rule. Keep it short enough that the image model can
follow the real priorities: raw face match first, house style second, exact scene
and text third.

Do not restore the old long exact-template prompt. Any prompt with too many
major sections or too many non-empty instruction lines must fail
`PROMPT_OVERLOAD`.

Pair every current illustration/image/carousel generation with the V2-local
role-based reference set:

- raw Aachu face anchors: `references/identity/aachu/`
- raw Zuv face anchors: `references/identity/zuv/`
- together/body-language support: `references/identity/together/`
- place support: `references/places/`
- style lock: `references/style/best-illustration/`
- failure examples to avoid: `references/failures/visual-inconsistencies/`
- text style: `references/text-style/`
- brand rules: `references/brand/`

Creator lock, 2026-06-13: the `references/style/best-illustration/` set is the
canonical approved style + finish + text-style lock (it replaces the retired
`observational-intimacy-premium` set). Shared images from a new brief control
only mood, composition, story essence, text, gesture, visuals, and objects
unless the creator explicitly says otherwise. Aachu/Zuv face anchors control
face identity. Together and place references are support roles only and must
never replace face anchors. Before accepting any slide, check it against
`references/failures/visual-inconsistencies/`: each filename names a failure
mode (inconsistent/rubber hands, merged seats, cup holder behind car seat,
forced/wrong locket, wrong gaze direction, missing on-image text, wrong text
font) that must not recur.

Creator correction, 2026-05-30: yellow/parchment paper and generic non-matching
faces are hard failures. Do not generate or accept final Aachu/Zuv artwork from
text-only identity descriptions; actual identity references and style references
must be usable by the image-generation path.

Creator correction, 2026-06-06: prompt assembly is autopilot by default. If the
creator gives a rough concept, prompt, photo, screenshot, or reference image,
infer the scene, on-image text, and image roles from that material instead of
asking for perfect fields. Treat user-shared photos that clearly depict the
requested people/couple as a current-request role bundle unless the creator or
context marks them as inspiration only.

Creator correction, 2026-06-13: the creator should not need to reattach
repo-local identity/style references when starting or resuming a flow. Before
final imagegen, generate the run's local reference manifest with
`scripts/prepare_imagegen_reference_context.py`, load every queued raw
face-anchor and style image in `view_image_queue` with `view_image`, and block
instead of generating if the image path cannot be read, the visibility proof is
stale against the current `load_plan_sha256`, the active queue is binder-only,
or the active generation path cannot use the loaded image context. Reference
Binder packets are audit/review artifacts only; they do not satisfy the final
face-identity input gate.

Creator correction, 2026-06-13: prompts must not fight the no-yellow rule with
positive color cues. Use neutral white/off-white paper language. Any lamp or
phone glow must stay local to faces/props and must never tint the paper or
background.

Creator correction, 2026-06-15: every final imagegen prompt must explicitly
request native `1080x1350 px` portrait output. Do not use square, 1:1, 9:16,
or 1080x1080 prompt language for final A Story illustrations unless the creator
explicitly changes this lock later. Wrong-size output is a hard reject, not a
resize/crop/pad task.

Creator correction, 2026-06-16: the face-match route from
`runs/2026-06-15_19-09_plate-nervous/` is now a hard gate, not a loose lesson.
Before imagegen or final package, `gold_standard_identity_route_gate` must pass:
selected references, 4 raw Aachu face anchors, 4 raw Zuv face anchors, 3 style
refs, 11 loaded references, multi-angle face-anchor diversity, current visibility
proof, pre-generation eval, agent assignment matrix, prompt-room review, scene
landing preview, scene options, selected idea, slide beat map, slide-count
decision, trace states, and prompt language that makes raw face anchors the
highest-priority visual input while forbidding single-anchor pose/expression
copying.
If any part fails, stop and mark `GOLD_STANDARD_IDENTITY_ROUTE_MISSING`.

Creator correction, 2026-06-18: contact sheets and a single best reference photo
are not the identity mechanism. The mechanism is individual raw face anchors
loaded in context, with multiple angles/expressions per person. Use them to
synthesize stable likeness only. Do not copy one anchor's posture, head angle,
eye state, expression, wardrobe, lighting, background, camera position, or scene
composition into every illustration.

Creator correction, 2026-06-18: source/current-request illustrations with
visible non-Aachu/Zuv faces must be analysis-only for final identity-sensitive
imagegen. Do not load them as active imagegen inputs, because the image model can
blend their faces, hair, pose, and wardrobe into Aachu/Zuv despite role labels.
Keep them in the manifest and binder trail for audit, then translate only their
story premise, text, body logic, and broad composition into the prompt.

```text
GENERATION PRIORITY:
Create a native 1080x1350 px @a.storyof.two illustration for slide [N] of [TOTAL]. Use raw Aachu/Zuv face anchors as the highest-priority visual input. Use the best-illustration style references only for watercolor-and-ink finish, neutral paper, text style, and composition. Do not let style images, binders, contact sheets, current-request source images, or text descriptions replace raw face anchors. Use multiple face anchors for identity structure only; do not copy any single anchor's pose, head angle, eye state, expression, wardrobe, lighting, background, camera position, or scene composition.

ON-IMAGE TEXT:
[INSERT EXACT TEXT]

SCENE:
[INSERT THE LOCKED SLIDE SCENE IN ONE FOCUSED PARAGRAPH]

IDENTITY ANCHORS:
Aachu: preserve her real face from the Aachu face-anchor inputs: large expressive dark eyes, natural brows, soft oval/round face, fuller lips, long dark hair with natural volume, playful real-person charm.
Zuv: preserve his real face from the Zuv face-anchor inputs: thick dark wavy hair, thick brows, recognizable eyes and nose, trimmed beard and mustache, rounded/oval face, gentle gaze.
The same two people must appear in every slide. Do not reverse the roles. Do not create new faces, merge their features, change ethnicity/age/skin tone, or over-beautify them into different people.

STYLE AND COLOR:
Premium hand-drawn romantic watercolor-and-ink, fine ink/pencil linework, visible paper grain, transparent muted washes, tactile clothing/prop detail, soft faded edges, clean expressive faces. Neutral white/off-white paper only: no yellow, mustard, sepia, beige/tan, parchment, coffee-stained, or heavy cream cast. Keep lamp/phone glow localized to faces/props; never tint the paper or background.

COMPOSITION AND TEXT:
Place exact hand-drawn charcoal text in clean upper-middle negative space, preserving spelling, punctuation, capitalization, and line breaks. Use the slide-specific camera distance and emotional proof. Keep both faces readable in a medium-wide, front three-quarter or equally clear composition unless the creator explicitly approved a face-hidden beat. Add tiny low-contrast handwritten @a.storyof.two at top-right.

HARD NO:
No anime, cartoon, doll/model face, photorealism, flat vector, quote-card/poster design, generic AI watercolor, rendered phone UI unless explicitly required, extra text, wrong text, missing brandmark, distorted eyes, bad hands/fingers, extra limbs, face merge, face drift, role reversal, yellow/parchment cast.

GENERATION HARD GATE:
Do not generate final Aachu/Zuv artwork from text descriptions or file paths alone. If actual raw Aachu/Zuv face anchors and style references are not loaded as usable image inputs in this conversation, stop and mark IDENTITY_REFERENCE_INPUT_UNPROVEN. If `gold_standard_identity_route_gate` fails, stop and mark GOLD_STANDARD_IDENTITY_ROUTE_MISSING. The prompt must include `1080x1350 px`; if it does not, stop and mark PROMPT_CANVAS_SIZE_MISSING. Generate one slide at a time; if a slide fails hard gates, stop before the next slide.
```
