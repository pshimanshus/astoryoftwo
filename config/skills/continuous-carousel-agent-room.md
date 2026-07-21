# Continuous Carousel Agent Room

last_updated: 2026-06-27
confidence: 0.97
sources:
- direct creator feedback in chat on 2026-05-23
- config/skills/carousel-story-director-persona.md
- config/skills/golden-viral-carousel-theme.md
- config/skills/romance-story-selling-engine.md
- memory/semantic/carousel-idea-preferences.md

## Purpose

Use this before finalizing any serious @a.storyof.two carousel concept,
storyline, slide copy, visual plan, prompt pack, or final image set.

When the creator says they want to jam on one idea, this room runs by default.
Do not ask whether to spawn agents. Run the room automatically and follow
`config/skills/carousel-jam-autopilot.md` until the idea is either packaged
with final images or explicitly blocked.

The room prevents one assistant from prematurely settling on a single idea.
It generates multiple story routes, attacks them, repairs the strongest
candidates, and keeps re-checking the chosen route through packaging and image
generation.

This skill does not replace Layer E, the Golden Theme gate, the Story Director
persona, or the Visual Debate Gate. It is the debate mechanism that keeps those
gates honest.

## Required Agents

Run the smallest useful room for low-risk edits, but for any new concept,
story repair, hook/copy direction, or image-generation handoff, use these
ownership lanes:

- Storyline Architect: generates 5-10 distinct story routes and owns emotional
  obstacle, proof, reversal, and payoff.
- Contrarian Critic: finds why each story will not work, why it is too private,
  unsafe, ungenerative, generic, body-shame adjacent, or confusing.
- Retention Analyst: owns hook strength, swipe ladder, comedy-to-tenderness
  movement, middle re-engagement, and DM-send logic.
- Visual Director: owns drawable scenes, visual variety, photo evidence,
  typography safety, aspect-ratio safety, and generative feasibility.
- Copy Chief: owns public wording, caption, low-text slide copy, no-name rule,
  and send/save line.
- Algorithm / Ad Strategist: owns reader mirror, partner-tag behavior, saves,
  shareability, caption keywords, and distribution risk.
- Final Selector: compares all routes, repairs top candidates, and returns one
  GO / REPAIR / STOP verdict.

## Nested Debate Requirement

For opening jam sessions, the room must think from the story, viral theme, or
golden-theme machine first. The first checkpoint is concept/story lock; it is
not slide copy, a hook bank, or a 5-line carousel draft.

Do not treat one isolated agent per role as enough for serious ideation. For
each top route, run a nested discussion with at least two creative-editor
voices and two writer voices. They must debate the same route in detail: what
story it is really proving, what viral recognition it protects, where the
emotional obstacle lives, what the proof engine is, why the ending is earned,
and why it could fail if written too soon.

Only after this nested debate and creator concept lock should the Copy Chief
draft public slide copy. Before concept lock, any creator-facing text should be
a story/theme decision record, not final slide copy.

## Required Exchange

1. Blind route generation: create at least 5 distinct topics or routes, not one
   route with wording variants.
2. Cross-debate: every agent reviews the shared route table and names what
   works, what breaks, whether it is universal or too private, whether it is
   safe or risky, whether it can be drawn/generated, and whether it can travel
   through sends, saves, comments, or tags.
3. Nested story/theme debate: the top routes get the multi-voice
   creative-editor and writer discussion described above. Record the debate,
   protected story spine, rejected interpretation, and repair notes before
   selector approval.
4. Loophole pass: the Contrarian Critic must score the raw winner before
   repair. If the raw score is below 24/30, the winner cannot proceed without a
   visible repair.
5. Repair pass: repair the top 2-3 routes, not only the favorite. Record what
   changed.
6. World-Class Taste Gate: before selector approval, record why the finalist
   is fresh, ownable, physically staged, and not a generic couple-account
   trope. Apply score caps for weak novelty, weak creator-world specificity,
   known-trope-plus-tender-ending, or generic replaceable couple content.
7. Stage-Scene Gate: before selector approval, convert finalists into
   storyboard-first stage scenes. Each finalist must show action, reaction,
   eye-line, hands, body distance, object movement, silence, consequence,
   reversal, and payoff. Text completes the scene; text must not carry the
   scene.
8. Selector pass: choose the route that best combines story truth,
   universality, visual proof, retention, safety, and distribution. Highest
   numeric score wins only if no hard gate is open.
9. Continuous re-entry: after C1 story, C2 arc, C3 visual plan, C4 prompt pack,
   C5 copy, and final images, the relevant agents re-check their ownership.
   Any blocking issue reopens the owning stage and downstream artifacts touched
   by that change.
10. Final-image closeout: after creator-approved copy and visuals, continue from
   prompt handoff into proof generation, full batch generation, packaging,
   visual QA, and final audit whenever image generation is available.

## Copy Confirmation Listener

The agent must actively listen for creator language that confirms copy is
closed. Treat these as hard triggers:

- "copy is final"
- "copies are closed"
- "copy locked"
- "perfect"
- "I like it"
- "go ahead"
- "proceed"
- "this is it"
- "approved"
- "now visuals"
- "make prompts"
- "generate"

When the creator confirms copy, do not continue directly to visual planning,
prompt writing, or image generation. First enter the mandatory Post-Copy Visual
Creative Room and keep the approved copy locked unless the visual room proves
that a line cannot be visualized safely.

## Post-Copy Visual Creative Room

After copy is confirmed and before `visual-debate.json`,
`visual-plan-quality.json`, `prompt-pack.json`, or image generation can pass,
run a separate visual room and write `post-copy-visual-room.json`.

Required visual lanes:

- Visual Format Anthropologist: extracts the visual mechanic from references
  without copying frames, likenesses, exact text, or copyrighted expression.
- Scene Evidence Director: proposes concrete per-slide scenes that prove the
  locked copy through visible behavior.
- Romance Blocking Director: defines wants, hidden needs, eye-lines, hands,
  posture, distance, expressions, and the joke-to-tenderness movement.
- Typography And Aspect Director: designs text/label placement for native 3:4
  and native 9:16 outputs, including face-safe zones and brandmark placement.
- Generation Prompt Director: converts the winning visual system into
  final-generation prompt instructions with identity, style, copy, reserved text space,
  integrated text-placement, and negative prompt locks.
- Harsh Visual Selector: attacks all options, repairs the winner, and returns
  GO / REPAIR / STOP.

The room must compare at least three visual systems. It must record what got
rejected, what got repaired, why the winner preserves the approved copy, and
what downstream `visual-debate.json`, `visual-plan-quality.json`, and
`prompt-pack.json` must preserve.

The canonical prompt source for this room is:

- `agents/carousel-post-copy-visual-room-orchestrator.md`

## Public Copy Rules

- Do not use Aachu, Zuv, Anchal, Himanshu, or private names in public-facing
  slide copy or captions unless the creator explicitly asks.
- Internal artifacts, prompts, identity QA, and visual direction may use names
  for clarity.
- Public copy should default to she/he/we/us, relationship roles, or universal
  phrasing.

## Food Bridge Rule

For "life got tastier," appetite, food-love, weight-number, or fuller-life
payoff concepts, a visible food/appetite/life-taste bridge is mandatory before
the ending.

Food must act as emotional evidence: comfort, ease, appetite for life, home
warmth, being unguarded. It must not become body comparison, weight comedy,
restaurant content, or the whole premise.

If the ending mentions numbers, taste, fullness, bites, appetite, or "tasty
life" without a food/appetite bridge by the middle of the deck, return REPAIR.

## Score Gates

Use these gates separately, not as one blended vibe score:

- Story-Selling: 28/30 minimum, no hard fail.
- Golden Theme: 28/30 minimum.
- Story Director: every dimension 8/10+ for hook, story, bridge, active partner
  role, ending, and send/save reason.
- Distribution: 26/30 minimum across hook, swipe ladder, DM-send, save payoff,
  caption/search, and skip risk.
- Visual Generativity: 27/30 minimum across photo evidence, simple scenes,
  non-repetition, identity, aspect/text safety, and non-generic prompts.
- Shot Ladder: PASS required. The visual plan must vary shot type, camera
  angle, setting lane, primary action, and who is visible. Repeated
  front-facing full-couple medium shots, bed/table/chai/books/garden defaults,
  or "both sitting together processing feelings" scenes return REPAIR even if
  style and identity are good.
- World-Class Taste: PASS with no score cap for novelty, creator-world
  specificity, non-obvious staged turn, and anti-generic replaceability.
- Safety/Taste: all PASS for respect, privacy, copyright, cultural
  authenticity, and non-shaming framing.

## STOP / REPAIR / GO

Return STOP if:

- no route reaches 28/30 after repair;
- the concept is primarily body-shame, object-first, or private-context-first;
- there is no relationship motion or relevant partner role;
- the visual plan cannot be generated as simple scenes;
- safety, taste, copyright, or privacy fails.
- the route is a generic couple trope with golden-theme parts attached and no
  ownable @a.storyof.two turn.

Return REPAIR if:

- agents disagree on the winner;
- raw winner scored below 24 before repair;
- the food bridge is missing for a payoff concept;
- the hook is universal but the visuals are generic;
- the copy is strong but the story proof is weak.
- the route is a text spine, quote-card deck, or candidate table without
  staged scene action.
- the taste gate caps novelty, creator-world specificity, known-trope, or
  generic replaceability below the 28/30 threshold.

Return GO only when:

- Story-Selling score is 28/30+;
- Golden Theme score is 28/30+;
- World-Class Taste Gate passes with no cap;
- Contrarian repair is resolved;
- retention, visual, copy, safety, and algorithm checks pass;
- required artifacts exist before final copy or generation.

## Required Artifacts

Before final copy:

- `agent-room.json`
- `source-memory-brief.json`
- `concept-routes.json`
- `concept-debate.json`
- `concept-repairs.json`
- `taste-gate.json`
- `concept-selection.json`
- `story-director-lock.json`
- nested story/theme debate notes with multiple creative-editor and writer
  voices for each top route

Before image generation:

- `slides.json`
- `copy.json`
- `post-copy-visual-room.json`
- `visual-debate.json`
- `visual-plan-quality.json`
- `prompt-pack.json`
- `identity-consistency-review.json`
- `review.json`

Final generation remains blocked until `concept-selection.json`,
`story-director-lock.json`, `post-copy-visual-room.json`,
`visual-debate.json`, `visual-plan-quality.json`, and
`identity-consistency-review.json` all say `GO` or `PASS`.

## Final Image Autopilot

`READY_FOR_CODEX_BUILTIN_GENERATION` means the package is ready for image
generation; it is not the finish line.

If the session has image-generation capability, continue automatically:

1. Generate the riskiest proof slide first when identity, taste, or safety risk
   is high.
2. Ask the creator to approve or reject the proof image.
3. If approved, generate every remaining slide independently in each format
   locked by `format-contract.json`.
4. Package only those locked outputs: `final/` for `instagram_post`,
   `final-reels-stories/` for explicit `reels_stories`, and `final-square/` for
   explicit `square`.
5. Run visual QA and final audit.

If generation cannot run, write the exact blocker in the carousel package and
surface that blocker to the creator. Do not present prompt files as final
images.
