# Carousel Jam Autopilot

last_updated: 2026-05-24
confidence: 0.99
sources:
- direct creator instruction on 2026-05-24
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

- `final/slide-XX.png` for native `4:5` Instagram carousel;
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

## Creator Checkpoints

The creator stays in the loop at four points:

1. Idea lock: the parallel room presents the selected GO / REPAIR / STOP
   direction and the top rejected alternatives.
2. Copy lock: the creator approves or edits slide copy.
3. Visual proof lock: generate one proof slide first when identity, safety,
   money, body, or style risk is high. The default proof slide is the slide
   that proves the riskiest story beat, not necessarily slide 1.
4. Final approval: after all images are packaged and visual QA is written, the
   creator gets the final folder and any failed checks.

Do not make the creator approve every internal artifact. Keep internal gates
moving unless they change public copy, visual meaning, identity, or safety.

## Required Parallel Agents

Use actual parallel/sub-agent tools when available. If tools are unavailable,
simulate the room as separate named reviewers and record the limitation.

Minimum room:

- Storyline Architect: obstacle, proof, reversal, payoff, 5-10 routes.
- Contrarian Critic: why it fails, safety/taste risks, private-context risk.
- Retention Analyst: hook, swipe ladder, middle re-engagement, send/save.
- Visual Director: scenes, identity, typography, 4:5 and 9:16 feasibility.
- Copy Chief: slide copy, caption, no-name public wording, exact text.
- Algorithm / Brand Strategist: shareability, comment/tag behavior, brand IP.
- Harsh Final Selector: one winner, repairs, GO / REPAIR / STOP.

Write or update:

- `agent-room.json`
- `concept-routes.json`
- `concept-debate.json`
- `concept-repairs.json`
- `concept-selection.json`

## Autopilot Sequence

1. Load memory and exclusions:
   - `memory/semantic/carousel-idea-preferences.md`
   - `wiki/themes/calm-enough-for-chaos.md`
   - `output/reports/2026-05-17-he-didnt-marry-peace-viral-theme-analysis.md`
2. Run Layer E:
   - `config/skills/romance-story-selling-engine.md`
3. Run Golden Theme tournament:
   - 5-10 routes;
   - 30-point score each;
   - top route must score 28/30+.
4. Run the Stage-Scene Gate:
   - storyboard-first stage scenes before slide copy;
   - each route must play as action -> reaction -> consequence -> reversal;
   - every scene must define eye-line, hands, body distance, object movement,
     silence, and the partner's active response;
   - text completes the scene; text must not carry the scene.
5. Load Story Director:
   - `config/skills/carousel-story-director-persona.md`
6. Run parallel agent room and present the creator one selected direction.
7. After creator approval, lock copy.
8. Run Post-Copy Visual Creative Room:
   - `post-copy-visual-room.json`
9. Run Visual Debate Gate:
   - `visual-debate.json`
   - `visual-plan-quality.json`
10. Build package:
    - `slides.json`
    - `copy.json`
    - `prompt-pack.json`
    - `identity-consistency-review.json`
    - `review.json`
11. Prepare image handoff:
    - `codex-image-prompts/instagram-post/`
    - `codex-image-prompts/reels-stories/`
12. Generate one proof slide when risk is high.
13. If proof passes, generate all remaining native `4:5` and native `9:16`
    slides.
14. Package generated sources:
    - `scripts/package_generated_carousel.py`
15. Run final QA:
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
- visible Aachu role and visible Zuv role;
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
- the creator has rejected a prior generated batch;
- text rendering or aspect framing is likely to fail.

The proof slide must be the riskiest slide. For Wallet Audit Love, use slide 4:

> He saw. He pretended to sleep.

Full-batch generation is blocked until the proof slide passes identity, style,
story, text, aspect, and safety QA.

## Done Means

Do not say the carousel is done until all are true:

- `final/slide-XX.png` exists for every slide;
- `final-reels-stories/slide-XX.png` exists for every slide;
- both formats came from separate native generated sources;
- exact copy and brandmark are inside the images;
- identity, style, text, and safety QA pass;
- `final-images.json` status is `generated` or `packaged`;
- `final-audit.json` is `PASS` or `PASS_WITH_NOTES`.

If any item is missing, say "handoff ready" or "blocked", not "final images
ready."
