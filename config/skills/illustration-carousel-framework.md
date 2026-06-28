# Illustration Carousel Framework

## Purpose

Turn user-supplied photos plus a short story into a complete illustrated
Instagram carousel package for @a.storyof.two.

The output is not a generic quote carousel. It is a tiny visual love story:
specific to Anchal and Himanshu, rooted in the supplied pictures, and formatted
for image generation plus human review.

Before any concept, slide copy, caption, or prompt work, apply the golden viral
theme skill:

- `config/skills/golden-viral-carousel-theme.md`
- `config/references/golden-viral-carousel-theme-reference.md`

When the creator asks for a stronger romance story, cinematic feeling,
novelistic arc, or online-selling concept process, also apply Layer E:

- `config/skills/romance-story-selling-engine.md`
- `config/references/story-selling-canon/concept-process-cards.md`
- `config/references/story-selling-canon/rubric.md`

After the existing memory, Layer E, and golden-theme gates have loaded, apply
the carousel story director persona before writing or designing:

- `config/skills/carousel-story-director-persona.md`
- `config/skills/continuous-carousel-agent-room.md`
- `config/skills/carousel-jam-autopilot.md`

This persona persists through concept, arc, visual plan, copy, prompt pack,
image-generation handoff, visual QA, and final image sets. It must reject any
deck that lacks a hook, setup, proof, bridge, relationship motion or a relevant
partner role, earned ending, or send/save reason.

For serious carousel concepts, the continuous agent room is mandatory before
final copy or generation: generate multiple routes, cross-debate story risks,
repair the top candidates, and select one GO / REPAIR / STOP winner. Do not
proceed from a single assistant idea.

When the creator is jamming on one idea, use Carousel Jam Autopilot. Run the
parallel room automatically, keep the creator in the loop for idea lock, copy
lock, proof image approval when needed, and final approval, then continue
through final image generation instead of stopping at a prompt handoff.

After Layer E and before final hooks, slide copy, visual prompts, or image
handoff, run the Stage-Scene Gate. This is a storyboard-first gate: the carousel
must play like staged scenes before it reads like a text carousel. The visual
sequence must carry action, reaction, eye-line, hands, body distance, object
movement, silence, consequence, reversal, and payoff. text completes the scene;
text must not carry the scene. Any route that is only a candidate table, poster
copy spine, quote-card sequence, or generic couple pose must return REPAIR even
if Story-Selling and Golden Theme scores are high.

This is mandatory. The supplied photo, place, outfit, or object is evidence for
a universal relationship truth. It is not enough by itself. Any carousel that
starts and stays object-first, travel-first, or outfit-first must be rewritten
before image generation.

## Required Artifact Contract

Every run must create:

- `manifest.json`: run metadata, source images, status, artifact map
- `agent-room.json`: continuous agent room status, active agents, unresolved objections, and stage verdict
- `source-memory-brief.json`: source facts, image evidence, creator memory exclusions, and unknowns
- `concept-routes.json`: 5-10 distinct route candidates before selection
- `concept-debate.json`: cross-agent debate of universality, safety, generativity, and distribution risk
- `concept-repairs.json`: repaired top candidates and objections solved
- `concept-selection.json`: selector verdict, scores, and GO / REPAIR / STOP decision
- `story-director-lock.json`: locked hook, obstacle, proof, bridge, relationship motion / relevant partner role, payoff, and send/save reason
- `concept.json`: title, human truth, emotional arc, slide summaries
- `post-copy-visual-room.json`: mandatory visual creative-room record after creator-approved copy, before final visual debate, prompt pack, or image generation
- `visual-debate.json`: Visual Debate Gate record from three visual agents before visual plan finalization, carousel packaging, or image generation
- `visual-plan-quality.json`: per-slide GO / REPAIR / STOP screen before image generation, covering golden-theme proof, stage-scene storytelling, copy-visual alignment, scene logic, pose/anatomy, visual evidence, identity continuity, composition, typography, aspect-ratio safety, and doubt flags
- `slides.json`: ordered slide copy, role, visual description, emotion, CTA intent
- `prompt-pack.json`: shared style prompt, negative prompt, slide prompts
- `identity-consistency-review.json`: C3.5 pre-generation review that verifies face structure, facial expression, clothing/body-language cues, and cross-slide identity continuity are locked from selected actual identity image inputs
- `copy.json`: caption options, alt text, hashtags, posting notes
- `review.json`: scorecard and required fixes
- `storyboard.md`: readable slide-by-slide brief
- `final-approval.md`: checklist before posting or generating final assets
- `run-ledger.json`: Jarvis observer requirements, stage status, final gate
- `stage-reviews.json`: expected vs actual reviews for every stage
- `final-audit.json`: package-level contract audit
- `wiki-update.md`: learning summary for wiki and memory carry-forward
- `final-images.json`: final generated image manifest and source mapping
- `visual-qa.md`: human/agent checklist for storyboard, identity, style, and typography

Final generated images must be copied into:

- `final/slide-XX.png`: native 4:5 Instagram post artwork in the creator-approved illustration style, with exact ON-IMAGE TEXT integrated into the final image raster
- `final-reels-stories/slide-XX.png`: native 9:16 Reels/Stories artwork generated separately for the taller frame, with exact ON-IMAGE TEXT integrated into the final image raster
- `final-with-text/slide-XX.png`: optional compatibility duplicate/intermediate only; the publishable text-bearing asset belongs in `final/`

## Default Format

- Per `config/rules/image-dimensions.md`, the creator hard rule for proof
  illustrations, concept illustrations, single-slide outputs, and default
  Instagram post/carousel slides is native `1080x1350 px` (4:5). Generate
  `1080x1920 px` (9:16) only when the creator explicitly asks for Story/Reel,
  and `1080x1080 px` square only when the creator explicitly asks for square.
  Instruct the image model with the exact pixel size, not the aspect ratio
  alone. Reject any image whose dimensions do not exactly match the requested
  format; do not crop, pad, stretch, or resize a wrong-dimension output into
  compliance; regenerate natively.
- Platform: Instagram
- Type: Carousel
- Aspect ratio: 4:5
- Upload size: 1080x1350 px (exact, mandatory)
- Reels/Stories aspect ratio: 9:16
- Reels/Stories size: 1080x1920 px (exact, mandatory)
- Slide count: default 5, range 4-5

Never stretch artwork to fit a target format. Never create the Reels/Stories output by resizing, cropping, padding, or extending the Instagram post output. The final illustration flow uses three output workers: one native 4:5 Instagram Post Output worker, one native 9:16 Reels/Stories Output worker, and one Identity/Visual QA worker that checks both outputs before packaging.

## Visual Direction

Use `config/carousel_style_contract.json` as the canonical source for visual
style, negative prompt, typography, brandmark, content lanes, and the Aachu/Zuv
character bible.

Before any final prompt or generation handoff, also load:

- `config/references/a-story-illustration-master-prompt.md`
- `config/references/a-story-premium-illustration-style-lock.md`
- `config/references/style-lock/observational-intimacy-premium/`

North Star:

> A soft illustrated archive of Aachu and Zuv's love, chaos, culture, and tiny rituals.

Use the @a.storyof.two romantic watercolor-and-ink master style:

- creator-approved Observational Intimacy Premium look as the default house
  style: warm ivory paper, visible paper grain, fine ink/pencil linework,
  transparent watercolor blooms, delicate sketch texture, muted vintage
  palette, tactile clothing detail, soft faded edges, couple and story props in
  the lower or middle-lower frame, clean upper-middle negative space for exact
  integrated handwritten ON-IMAGE TEXT, and strong A Story of Two house style
  even when outside references supply the message, emotion, story, or pose
- premium hand-drawn romantic editorial illustration
- soft watercolor wash with fine ink and pencil linework
- warm ivory paper background with visible paper grain
- delicate sketch lines, gentle crosshatching, and imperfect organic edges
- clean expressive faces with warm skin shading, carefully drawn eyes, and soft blush
- premium muted vintage palette: warm ivory, soft off-white, denim blue, soft navy, terracotta red, camel, gentle brown, faded sage, peach blush, dusty coral
- tactile clothing and prop details such as denim grain, fabric folds, scarf patterns, leather straps, ceramic cups, small jewelry, and shoe stitching
- generous warm upper-middle negative space for exact final slide text
- one clear Aachu/Zuv behavior scene per slide
- a non-repeating shot ladder across the carousel: vary camera angle, shot
  distance, setting lane, primary action, and who is visible; do not solve
  variety by wardrobe changes alone
- tiny low-contrast brandmark: `@a.storyof.two` at bottom-right for every final asset
- rooted in supplied photos and selected actual identity images before adding decorative interpretation

Every final image-generation handoff must include the project master prompt
structure from `pipeline/stages/carousel_master_prompt.py`. The prompt must
cover use case, asset type, reference image roles, primary request, scene,
character identity lock, face preservation, illustration style, color palette,
composition, emotional direction, wardrobe continuity, recurring props,
background style, line/texture details, anatomy/quality rules, text rule, final
identity/style reinforcement, and the final rendering layer.

Adapt the style to the supplied images:

- preserve recognizable outfit, pose, setting, and relationship cues
- break visual patterning across slides. Do not repeat the same front-facing
  full-couple medium shot, bed/table/chai/books/garden prop cluster, or
  quiet-listening scene unless the creator has locked a continuous sequence.
  Use wide, medium, close, over-shoulder, single-person, object-only, detail,
  doorway, reflection, and transition shots as story evidence.
- treat shared images only as mood/composition/story references unless the
  creator explicitly says otherwise or the images clearly depict the requested
  people/couple for this prompt; in that case, use them as current-request
  identity references
- if the creator gives only a rough concept, prompt, screenshot, or photo,
  infer a first-pass scene, on-image text, and visual direction from that
  material instead of asking for perfect fields
- do not import screenshot or app-layout devices into final art. If a
  reference uses split-screen, phone UI, carousel dots, social handles,
  engagement icons, black app chrome, or a vertical divider, translate the
  relationship idea into a premium lived Aachu/Zuv scene using architecture,
  eye-line, distance, furniture, or natural staging instead. No split-screen
  divider may appear unless the creator explicitly asks for that graphic device
  as story content.
- keep Anchal expressive and emotionally alive
- keep Himanshu calm, warm, and grounded
- use selected actual Aachu/Zuv identity images as attached face, expression,
  posture, body-proportion, and wardrobe anchors
- choose wardrobe from those selected identity/current-request photos first;
  do not use a fixed wardrobe menu as the source of truth
- treat previous successful illustrations as style references only, never as
  face identity references
- treat `config/references/identity/` and any legacy `identity_images/` folder
  as candidate libraries, then choose a small story-specific identity bundle
  instead of attaching the whole folder
- use desi details only when the photos or story support them
- add Kashmiri or wedding cues only when authentic to the story

## Visual Debate Gate

After the creator confirms final slide copy, run the mandatory Post-Copy Visual
Creative Room before final visual planning, prompt finalization, packaging, or
image generation. Write `post-copy-visual-room.json` using:

- `agents/carousel-post-copy-visual-room-orchestrator.md`

The trigger is creator confirmation language such as "copy is final",
"copies are closed", "perfect", "I like it", "go ahead", "proceed", "approved",
"now visuals", "make prompts", or "generate." Once this trigger appears, keep
the approved copy locked and enter the visual room. The room must compare at
least three visual systems and include a Visual Format Anthropologist, Scene
Evidence Director, Romance Blocking Director, Typography And Aspect Director,
Generation Prompt Director, and Harsh Visual Selector. A `REPAIR` or `STOP`
blocks visual-debate, prompt-pack, and image-generation handoff.

After the Post-Copy Visual Creative Room returns GO, run the three visual
agents as a council and write `visual-debate.json`:

- `agents/carousel-visual-evidence-planner.md`: proposes photo-rooted,
  non-repetitive scenes where objects, outfits, and places act as evidence.
- `agents/carousel-romance-scene-planner.md`: turns the emotional machine into
  drawable scene beats with obstacle, reversal, and payoff.
- `agents/carousel-visual-continuity-judge.md`: debates the options, blocks
  repeated props or one-setting defaults, and selects GO / REPAIR / STOP.

The council must preserve the `post-copy-visual-room.json` winner unless it
records an explicit repair. It must produce three or more visual options,
rejected visual patterns, a selector verdict, the winning visual system, and the
final slide-by-slide visual plan. No carousel packaging or image generation
should start until both gates pass. If the creator rejects a visual motif, do
not repeat that motif across every illustration; use it only as occasional
evidence when it is truly needed.

After the council selects a visual system, run a per-slide visual screen and
write `visual-plan-quality.json` before C4 prompt finalization or any image
handoff. Each slide must be reviewed by multiple visual reviewers: a
visual/story reviewer, a romance-scene reviewer, a continuity judge, and a
screen-quality judge. A slide passes only when it proves the exact copy through
visible Aachu/Zuv behavior, preserves the golden-theme machine, keeps identity
and outfit continuity plausible, avoids rejected/losing visual options, and is
safe for both 4:5 and 9:16 composition. Any doubt about likeness, story proof,
visual repetition, shot-ladder variety, text placement, aspect-specific framing, or place/metaphor
drift must return REPAIR or STOP. Do not generate that slide, or the carousel,
until the doubt is repaired and re-reviewed.

## Identity Reference Flow

Do not use one permanent Aachu/Zuv image for every carousel, and do not feed
the whole identity library into one generation prompt. The flow is:

1. Browse or discover available identity candidates.
2. Select a curated bundle of 2-4 images for the current story.
3. Attach the bundle as visual input evidence for likeness, posture, outfit,
   context, or expression.
4. Keep the relationship truth as the premise; outfits and objects stay proof.

Hard face-consistency rule:

- The selected identity bundle must be passed to the image-generation model as
  actual image inputs for every final slide.
- Text-only descriptions of the identity images do not satisfy the final-image
  gate, even if the prompt names the files.
- If the available generation path cannot attach identity reference files,
  stop and mark the package blocked instead of producing final art.
- Any generated slide that does not clearly preserve Aachu/Zuv face structure
  from the identity bundle must be treated as a failed image, not as a final.
- Wardrobe must be chosen from the selected identity bundle or current-request
  identity photos first. Repeat outfits only for same-time continuity,
  creator-requested continuity, or a deliberate signature anchor.

Default bundle roles:

- face anchor
- body/posture anchor
- story-relevant outfit or context anchor
- emotion/detail anchor

If the run auto-discovers more than four candidate images under
`config/references/identity/` or legacy `identity_images/`, it must record the
larger candidate count but attach only the selected bundle to `prompt-pack.json`.
If the user explicitly supplies more than four identity references for one run,
ask them to narrow the set before image generation.

Avoid:

- photorealism
- 3D rendering
- glossy AI look
- generic Indian couple stock characters
- Canva quote-card layouts
- crowded backgrounds
- too many props
- moralizing self-help language
- jokes that make either person look cruel or small

Typography rule:

- Default final slide copy must appear inside the final illustration image, not in a separate caption, mockup, or quote-card layer.
- When the image model can render the exact text cleanly, image-model text is acceptable. When exact text is long or fragile, generate the illustrated scene with clean reserved paper space, then place the approved text into the same final raster as an integrated lettering/typesetting pass.
- Image-generation prompts must reserve generous clean paper space and ask for no random text beyond the approved slide copy and tiny brandmark. Final export workers must then produce two complete native publishable outputs per slide when required: 4:5 Instagram post and 9:16 Reels/Stories, each with exact ON-IMAGE TEXT inside the final image.
- Brand-integration prompts may include product labels, but brand/product name legibility is a hard QA gate at phone-screen size. If tiny packaging text is misspelled or blurred by generation, render the product body in the illustration first, then use `scripts/render_brand_product_labels.swift` for exact readable label text.
- Local text placement is valid only when it is treated as part of the final illustration composition: same warm paper, same visual rhythm, no flat platform typography, no poster/quote-card feel, no separate text-only deliverable. A visible digital overlay fails.
- Do not claim final images are ready until `final/`, `final-reels-stories/`, and visual QA exist.
- Do not stop at `READY_FOR_CODEX_BUILTIN_GENERATION` when an image-generation
  path is available. Generate, package, and QA the native `4:5` and separate
  native `9:16` outputs. If generation is unavailable, write the concrete
  blocker inside the package and call the state `handoff ready` or `blocked`,
  not `final images ready`.

## Story Arc Pattern

Every story arc must first pass the golden-theme filter:

1. Universal relationship truth.
2. Aachu/Zuv-specific interpretation.
3. Concrete photo, object, behavior, or ritual proof.
4. Relationship motion or relevant partner role; do not default to
   Zuv-as-handler or Aachu-as-problem.
5. Tender save/share thesis.

Then pass the story-director structure:

1. Hook.
2. Setup.
3. Proof.
4. Escalation.
5. Bridge.
6. Relationship motion.
7. Earned ending.

Never move the strongest hook to the end. The ending can deepen the opening
truth, but slide 1 must stop the scroll and open the loop.

## Concept Selection Gate

Before naming a "final" carousel idea or starting a C-layer package, run the
golden-theme variant tournament from `config/skills/golden-viral-carousel-theme.md`.
This is required for next-idea, theme, carousel, and `/story` planning work.

The minimum accepted decision record is:

- 5-10 distinct concept variants from different creative lenses;
- a 30-point Golden Theme score for each variant;
- a World-Class Taste Gate record that checks novelty, creator-world
  specificity, non-obvious staged turn, anti-generic replaceability, and score
  caps;
- a selector verdict that chooses the highest-rated option that passes every
  hard gate;
- a GO / REPAIR / STOP decision;
- no image generation or carousel packaging unless the winner scores 28/30 or
  higher and the World-Class Taste Gate applies no cap.

Use one of these structures:

1. **Moment to Meaning**
   Hook on the visible moment, reveal why it mattered, end with a save-worthy
   emotional line.

2. **Banter to Softness**
   Open with a funny relationship truth, escalate with specific details, soften
   into love by the final slides.

3. **Place to Memory**
   Let the location carry the first half, then make the relationship the point.

4. **Then to Now**
   Use photos as proof of a journey, ending with what changed or stayed true.

## Copy Rules

- Slide copy should be short enough to read in one glance.
- Prefer specificity over grand romance language.
- Start from a universal relationship truth, then prove it with Aachu/Zuv
  specifics. Do not let the object, outfit, place, or photo aesthetic become
  the whole concept.
- Aachu/Zuv specifics are allowed to remain internal: visible slide and caption
  copy should not force private names into every post. Prefer "she", "he",
  "we", "us", or relationship-role language unless names naturally serve the
  emotional truth.
- Hinglish is welcome when the story is playful or culturally specific.
- Use Voice 1 for banter and couple chaos.
- Use Voice 2 for proposals, anniversaries, grief, distance, or reflective love.
- Default to 5 slides unless the user explicitly asks for 4.
- Final slide should be worth saving or sending.

## Review Rules

Score 0-5 on:

- golden-theme alignment
- story specificity
- photo-to-illustration faithfulness
- character likeness prompting
- visual simplicity
- slide-to-slide flow
- emotional payoff
- channel voice fit
- absence of generic couple content

Pass threshold: 36/45 when golden-theme alignment is included, or 32/40 for
legacy scorecards that have not added the field yet. No zero is allowed in
golden-theme alignment, story specificity, photo-to-illustration faithfulness,
or absence of generic couple content.

## Quality Spine

Every Codex-native run must include the review spine:

1. C0.5-Jarvis creates `run-ledger.json` and tracks requirements.
2. Stage reviewers compare expected vs actual output after each stage.
3. Before C4 prompt finalization or image generation, write `visual-plan-quality.json` with per-slide GO / REPAIR / STOP checks from multiple reviewers.
4. Any slide with REPAIR, STOP, or unresolved doubt blocks generation for the whole carousel until repaired and re-reviewed.
5. C7-Final Contract Auditor writes `final-audit.json`.
6. C3.5-IdentityConsistency writes `identity-consistency-review.json` after slide descriptions are generated and before image generation. It must pass before generating final art.
7. Final generated images are packaged into `final/slide-XX.png` and `final-reels-stories/slide-XX.png` from separate native generated sources.
8. If `final-with-text/slide-XX.png` exists, it is only a compatibility copy or intermediate; `final/slide-XX.png` is the publishable text-bearing image.
9. `visual-qa.md` and `visual-qa.json` check storyboard match, face
   consistency, dress continuity, style, scene logic, pose/anatomy, exact
   integrated final text, brand/product label visibility when relevant, and final
   output existence.
10. The run writes a carousel wiki page, updates `wiki/index.md`, appends
   `memory/working.md`, and updates `memory/graph.json`.

Allowed final statuses:

- `PASS`: complete with no notes.
- `PASS_WITH_NOTES`: complete with explicit limitations.
- `NEEDS_FIXES`: one or more critical requirements failed.
- `BLOCKED`: required input or output is unavailable.
