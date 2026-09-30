# A Story of Two — Video Generation Master Prompt

last_updated: 2026-09-05
status: active
scope: every `generate_video` call on the video line
companion to: `config/references/a-story-illustration-master-prompt.md`

The image master prompt fills slots to describe **a frame**. This one fills slots
to describe **what changes inside that frame** — and, just as importantly, what
must not.

## The One Rule

**A video prompt is a subtraction, not an addition.** The still already carries
composition, identity, wardrobe, light and style. The video's only job is to move
one thing. Every extra instruction is another chance for the model to redraw a
face, morph a hand, or slide the painting toward photorealism.

If a prompt lists more than one moving element, it is wrong.

## Model Routing

| Shot type | Model | Credits (5s, 1080p) |
|---|---|---|
| Silent motion | `seedance_2_5` · `mode: omni_reference` | 45 |
| Character speaks | `wan2_7` + `audio_references` | 12.5 |
| Facial emotion, no speech | `minimax_hailuo` | preflight it |
| No real motion needed | **none** — edit-motion in post | 0 |

Talking is cheaper than silence. Decide by story need, never by price.

## Slot Template

Fill in order. Unbracketed text is the reusable scaffold — do not reword it.

```text
SUBJECT AND CONTINUITY LOCK:
The people, faces, hair, clothing, jewellery, props, furniture, room and lighting in this video are exactly as they appear in the source image and must not change, redraw, morph or drift at any point. [INSERT THE SPECIFIC ACCESSORY LOCKS FOR THIS SHOT]

MOTION — THE ONE THING THAT MOVES:
[INSERT THE SINGLE MOVING ELEMENT, described as one plain physical action]

SECONDARY MOTION:
[INSERT AT MOST ONE ambient element — light shifting, fabric settling, a breath — or the word: None]

WHAT MUST NOT MOVE:
Everything else in the frame stays completely still. [INSERT THE SPECIFIC OBJECTS THAT MUST HOLD]

PERFORMANCE:
Restrained and undramatic. No theatrical expression, no exaggerated emotion, no performed sadness or joy. [INSERT THE EMOTIONAL REGISTER FOR THIS SHOT]

CAMERA:
[INSERT: "The camera is completely locked. No pan, tilt, zoom, push-in, drift or handheld movement." OR the single deliberate move]

STYLE PRESERVATION:
The watercolour-and-gouache painted finish, the warm ivory paper grain, the soft dry-brush edges and the pigment granulation must survive every frame. The image must never become photographic, three-dimensional, glossy or video-realistic as it moves. It stays a painting in motion.

DIALOGUE:
[INSERT the exact spoken line, the speaker, and the language — or the word: None. The line must match the supplied audio word for word.]

ESSENTIAL NEGATIVES:
No morphing, warping or melting of faces, hands or bodies. No identity drift — the person must remain the same person in the last frame as in the first. No extra fingers, extra limbs, extra people entering frame, reflections or silhouettes. No style shift toward photorealism, 3D render or glossy video. No camera drift or unrequested camera movement. No text, words, lettering, subtitles or watermark appearing at any point. No background figures. No object appearing, disappearing or changing shape. No lip movement when DIALOGUE is None.
```

## Slot Notes

**MOTION.** One action, stated physically, not emotionally. *"She slowly turns her
head to look back over her shoulder"* — not *"she notices him with dawning
recognition."* The model animates verbs, not feelings.

**WHAT MUST NOT MOVE.** Name the specific things that would ruin the shot if they
drifted — the plate, the bag strap, the laptop. Generic "everything else" is
weaker than a list.

**PERFORMANCE.** This register is the brand. Every model's default is to overact.
Say restrained, then say it again in the negatives.

**DIALOGUE.** Only for `wan2_7`, and only with matching `audio_references`. When
audio is not supplied the model **invents a voice and a language** — confirmed on
2026-09-05, when a random English voice was generated for a Hindi scene. Never
let a talking shot run without supplied audio.

**STYLE PRESERVATION.** Non-negotiable and never trimmed. Motion models are
trained on photographic video; every one of them pulls a painted source toward
photorealism unless actively held back.

## Audio Pipeline for Talking Shots

1. `generate_audio` · model `seed_audio` · `voice_type: "element"` · the cloned
   `voice_id` · the exact line — **0.1 credits**
2. Pass the returned job id into `generate_video` as `audio_references`, with the
   approved still as `start_image`
3. The DIALOGUE slot must quote the same line word for word

Cloned voices live as workspace elements and are permanent.

| Voice | ID | Type |
|---|---|---|
| `Zuv-1` (Himanshu) | `f7609a73-ee15-4ffd-82c9-59fa666e8164` | element |

## Standing Rules

1. One moving element per shot. Two is a bug.
2. Never run a talking shot without supplied audio.
3. Style preservation and the negatives block are never trimmed to save tokens.
4. Decline Higgsfield preset recommendations — a preset overrides the locked
   look. Pass `declined_preset_id` and generate literally.
5. Preflight any cost not already measured in `video/PRODUCTION.md`.
