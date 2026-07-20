# Carousel Jam Autopilot

last_updated: 2026-06-27
confidence: 0.99
sources:
- direct creator instruction on 2026-05-24
- config/skills/creator-skill-stack.md
- config/skills/continuous-carousel-agent-room.md
- config/skills/carousel-story-director-persona.md
- config/skills/illustration-carousel-framework.md
- AGENTS.md

## Purpose

Use this whenever the creator wants to jam on one carousel idea, develop a
concept, choose a theme, approve copy, make visuals, generate images, or turn a
single idea into a finished @a.storyof.two carousel.

The goal is not a plan, prompt pack, or handoff. The goal is final packaged
images:

- `final/slide-XX.png` for native `3:4` Instagram carousel;
- `final-reels-stories/slide-XX.png` for separate native `9:16` companion
  slides;
- `final-images.json`, `visual-qa.md`, and `final-audit.json` updated after
  packaging.

## Trigger Phrases

Treat these as autopilot triggers, even if the creator does not write `/story`:

- "jam on this"
- "let's jam"
- "one idea"
- "make this a carousel"
- "turn this into a post"
- "make prompts"
- "generate"
- "final images"
- "go ahead"
- "approved"
- "this is the direction"
- "copy is final"
- "now visuals"

## Operating Rule

Do not ask whether to run agents. Run the agent room automatically.

Do not stop at `READY_FOR_CODEX_BUILTIN_GENERATION` if final-image generation
is available in the session. Continue into image generation, proof review,
packaging, and QA.

If final-image generation is not available or a required reference is missing,
write a concrete blocker file inside the carousel package and ask the creator
for only the missing item.

## Jam Debate First

When the creator starts with "jam", the first creator-facing checkpoint is
story/theme lock, not slide copy. Internally, run a free creative pass first:
let the model generate concept, copy, and visual setup together so the alive
route can reveal itself. Then use engineering guardrails to check repetition,
identity, visual quality, exact text, brandmark, dimensions, stale artifacts,
and house guidance.

Before showing any concept suggestion, invoke
`config/skills/creator-skill-stack.md`: define scroll stop, recognition,
emotional contradiction, scene proof, retention ladder, payoff, format remix,
audience mirror, volume path, taste gate, and DM Send Test. This is the jam
hook, not public copy.

Do not answer an opening jam with a 5-line slide copy, hook bank, or slide
architecture. Before concept lock, creator-facing output may include the
emotional machine, reader mirror, obstacle, proof engine, Stage-Scene beats,
rejected lanes, scores, and GO / REPAIR / STOP verdict. Public slide copy
waits until the creator approves the concept direction.

## Creator Raw Scene Lock

If the creator supplies a real moment, lock the literal scene row before any
concept tournament, Layer E framing, hook, copy, visual style, prompt pack, or
generation. The row must preserve:

- actual sequence of events;
- exact locations;
- exact objects;
- who acted;
- who noticed;
- what changed on screen;
- what consequence creates the next beat.

Do not convert a supplied story into a more convenient relationship concept.
Do not add symmetry, extra objects, moral endings, or quote-card structure
unless the creator asked for them. If the creator says the direction is not
working, immediately mark the previous route rejected/superseded, clear stale
prompt-pack language, and rebuild from the raw scene row.

## Creator Checkpoints

The creator stays in the loop at four points:

1. Idea lock: the parallel room presents the selected GO / REPAIR / STOP
   direction and the top rejected alternatives.
2. Copy lock: the creator approves or edits slide copy.
3. Visual proof lock: generate one proof slide first when identity, safety,
   money, body, or style risk is high. The default proof slide is the slide
   that proves the riskiest story beat, not necessarily slide 1. If identity
   is in scope, no identity eval means no next slide: stop until a structured
   `identity-consistency-review.json` or `visual-qa.json` records the selected
   Aachu/Zuv reference IDs and specific likeness notes.
4. Final approval: after all images are packaged and visual QA is written, the
   creator gets the final folder and any failed checks.

Do not make the creator approve every internal artifact. Keep internal gates
moving unless they change public copy, visual meaning, identity, or safety.

## Required Parallel Agents

Use actual parallel/sub-agent tools when available. If tools are unavailable,
simulate the room as separate named reviewers and record the limitation.

Each serious route needs a discussion room, not one isolated agent per role.
For the top routes, run at least two creative-editor voices and two writer
voices debating the same story spine before the selector sees it. The room must
argue what story/viral/golden theme is being protected, what the idea loses if
written too soon, and why the rejected routes are weaker.

Minimum room:

- Storyline Architect: obstacle, proof, reversal, payoff, 5-10 routes.
- Contrarian Critic: why it fails, safety/taste risks, private-context risk.
- Retention Analyst: hook, swipe ladder, middle re-engagement, send/save.
- Visual Director: scenes, identity, typography, 3:4 and 9:16 feasibility.
- Copy Chief: slide copy, caption, no-name public wording, exact text.
- Algorithm / Brand Strategist: shareability, comment/tag behavior, brand IP.
- World-Class Taste Judge: novelty, creator-world specificity, non-obvious
  staged turn, anti-generic score caps, and whether only @a.storyof.two can
  post this route this way.
- Harsh Final Selector: one winner, repairs, GO / REPAIR / STOP.

Write or update:

- `agent-room.json`
- `concept-routes.json`
- `concept-debate.json`
- `concept-repairs.json`
- `taste-gate.json`
- `concept-selection.json`

## Autopilot Sequence

0. If a real moment is supplied, run Creator Raw Scene Lock:
   - write the action row first;
   - block hooks, copy, Layer E scoring, prompt packs, and generation until the
     row preserves the creator's literal facts;
   - if any beat invents, removes, abstracts, or rearranges the event, return
     STOP and repair the row before continuing.
1. Load compact runtime context:
   - `config/skills/carousel-jam-runtime-context.md`
   - do not full-read the four long source files below as a routine opening
     move; open only the needed section when scoring, repairing, resolving a
     conflict, updating durable memory, or gathering final audit evidence.
   - deep source references:
     - `wiki/insights/successful-carousel-standard.md`
     - `memory/semantic/carousel-idea-preferences.md`
     - `config/skills/romance-story-selling-engine.md`
     - `config/skills/golden-viral-carousel-theme.md`
     - `wiki/themes/calm-enough-for-chaos.md`
     - `output/reports/2026-05-17-he-didnt-marry-peace-viral-theme-analysis.md`
2. Run or preserve the free creative pass before scoring:
   - model owns concept, copy, and visual invention;
   - if the creator or model has already produced a strong route, save it as
     `creative-baseline.json`;
   - engineering is the guardrail layer and should block hard failures rather
     than replace the alive route with a safer template.
3. Define what success looks like before writing:
   - audience success: send/save/tag behavior and "this is us" recognition;
   - creative success: staged story sequence, behavior receipts, active partner
     response, emotional turn, and earned thesis;
   - brand success: ownable warm desi relationship IP;
   - production success: native 3:4 and separate native 9:16 finals with QA.
   - story/theme success: the specific story, viral theme, or golden-theme
     machine the carousel must prove before any copy is drafted.
4. Run Layer E:
   - `config/skills/romance-story-selling-engine.md`
5. Run Golden Theme tournament:
   - 5-10 routes;
   - 30-point score each;
   - top route must score 28/30+ before taste caps.
6. Run the nested story/theme debate room:
   - at least two creative-editor voices and two writer voices debate the top
     routes against the desired story/viral/golden-theme spine;
   - record what each voice would protect, cut, repair, and refuse;
   - do not write public slide copy yet.
7. Run the World-Class Taste Gate:
   - write `taste-gate.json` or an equivalent section in `concept-selection.json`;
   - require novelty, creator-world specificity, a non-obvious staged turn,
     anti-generic reasoning, and a cold-viewer send reason;
   - cap weak novelty or weak creator-world specificity at 24/30;
   - cap a known trope plus tender ending at 23/30;
   - cap a generic couple-account route at 22/30;
   - if the creator says the idea is low-average or unimpressive, stop
     polishing the lane and rebuild from a raw incident, recurring phrase,
     object movement, one-second contradiction, or creator-supplied reference
     mechanic.
8. Run the Stage-Scene Gate:
   - storyboard-first stage scenes before slide copy;
   - each route must play as action -> reaction -> consequence -> reversal;
   - every scene must define eye-line, hands, body distance, object movement,
     silence, and the partner's active response;
   - text completes the scene; text must not carry the scene.
9. Load Story Director:
   - `config/skills/carousel-story-director-persona.md`
10. Present the creator one selected concept direction for concept lock, with
   debate summary and staged beats but without a finished slide-copy list.
11. After creator approval, write and lock copy.
12. Run Post-Copy Visual Creative Room:
   - `post-copy-visual-room.json`
13. Run Visual Debate Gate:
   - `visual-debate.json`
   - `visual-plan-quality.json`
14. Build package:
    - `slides.json`
    - `copy.json`
    - `prompt-pack.json`
    - `identity-consistency-review.json`
    - `review.json`
15. Prepare image handoff:
    - `codex-image-prompts/instagram-post/`
    - `codex-image-prompts/reels-stories/`
    - load `config/references/style-lock/observational-intimacy-premium/` as
      the default style reference bundle, with selected actual Aachu/Zuv
      identity images attached as face, body, and wardrobe anchors. Wardrobe
      comes from selected identity/current-request photos first, not a static
      menu.
16. Generate one proof slide when risk is high. If the proof includes Aachu or
    Zuv, immediately run the identity eval stop gate before any next slide:
    write or update `identity-consistency-review.json` or `visual-qa.json` with
    Aachu/Zuv reference IDs, face/hair/body/wardrobe notes, and PASS/REPAIR/
    STOP. If tools cannot perform real likeness comparison, record
    `BLOCKED_FOR_IDENTITY_EVAL` or `IDENTITY_UNVERIFIED`, tell the creator, and
    stop instead of batching.
17. If proof passes structured identity, style, story, text, aspect, and safety
    QA, generate all remaining native `3:4` and native `9:16` slides.
18. Package generated sources:
    - `scripts/package_generated_carousel.py`
19. Run final QA:
    - `visual-qa.md`
    - `final-audit.json`
    - wiki health if the session is substantial.

## Stage-Scene Gate

Do not present an idea as the next carousel just because its hook and slide
copy score well. After Layer E and before copy lock, stage the route as a tiny
story first. The creator should be able to understand the relationship beat if
all poster text is hidden.

A passing staged route has:

- one clear action per slide;
- a reaction or consequence that earns the next swipe;
- visible relationship motion: Aachu, Zuv, both partners, or the shared
  situation must create behavior/reaction that earns the next swipe;
- eye-line, hands, body distance, posture, object movement, and silence;
- a joke-to-tenderness or friction-to-belonging turn;
- scene-native text only after the visual beat works.

Return REPAIR if the route is a text spine, quote-card deck, generic couple
pose, "Aachu/Zuv standing beside the line," or a candidate table without staged
behavior. text completes the scene; text must not carry the scene.

## Proof-First Rule

Use proof-first generation when any of these are true:

- identity consistency is critical;
- the concept can be misread as theft, control, cruelty, body shame, or a fight;
- the style has recently drifted into photorealism, contact sheets, or generic
  AI stock art;
- the generated image might drift away from the Observational Intimacy Premium
  lock: warm ivory paper, visible grain, fine ink/pencil linework, transparent
  watercolor blooms, upper-middle handwritten text, and tiny top-right
  `@a.storyof.two` brandmark;
- the creator has rejected a prior generated batch;
- text rendering or aspect framing is likely to fail.

The proof slide must be the riskiest slide. For Wallet Audit Love, use slide 4:

> He saw. He pretended to sleep.

Full-batch generation is blocked until the proof slide passes identity, style,
story, text, aspect, and safety QA.

Identity is a stop gate, not a taste note. "Looks good", dimension checks, or a
manual visual impression do not pass the gate unless a structured
`identity-consistency-review.json` or `visual-qa.json` records selected
reference IDs and specific likeness notes. If that structured review cannot be
performed, mark `BLOCKED_FOR_IDENTITY_EVAL` or `IDENTITY_UNVERIFIED`, tell the
creator, and do not call the proof final or generate the remaining slides.

## Done Means

Do not say the carousel is done until all are true:

- `final/slide-XX.png` exists for every slide;
- `final-reels-stories/slide-XX.png` exists for every slide;
- both formats came from separate native generated sources;
- exact copy and brandmark are inside the images;
- identity, style, text, and safety QA pass;
- `identity-consistency-review.json` or `visual-qa.json` contains selected
  Aachu/Zuv reference IDs and specific likeness notes, or the work is marked
  blocked/unverified instead of final;
- `final-images.json` status is `generated` or `packaged`;
- `final-audit.json` is `PASS` or `PASS_WITH_NOTES`.

If any item is missing, say "handoff ready" or "blocked", not "final images
ready."
