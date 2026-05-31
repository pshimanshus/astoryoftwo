STORY-SELLING (Layer E) — every carousel concept must pass the 30-point Story-Selling rubric before copy, visual plan, or prompt compilation. This is additive to the Golden Theme score; a concept must pass both thresholds before C-layer packaging or image generation.

Source: `config/references/story-selling-canon/rubric.md`.
Adaptation: `config/references/story-selling-canon/a-story-of-two-adaptation.md`.
Process cards: `config/references/story-selling-canon/concept-process-cards.md`.
Source policy: `config/references/story-selling-canon/source-policy.md`.

PASS THRESHOLD — 28/30

30-POINT SCORECARD

1. READER IDENTITY MIRROR (0–5)
- 5: A stranger immediately recognizes a relationship truth and can imagine sending it to their partner.
- 4: Broadly relatable but slightly more tied to the couple than the reader.
- 3: Understandable, not strongly self-recognizing.
- 2: Mostly private context.
- 1: Aesthetic or event-first with almost no reader doorway.
- 0: No clear reader identity.

2. ROMANTIC CONFLICT AND STAKES (0–5)
- 5: A real emotional obstacle, tension, fear, misread, or cost drives the story.
- 4: Clear tension but stakes could be sharper.
- 3: Mild friction, mostly charming.
- 2: Implied tension only.
- 1: Pretty moment with almost no emotional obstacle.
- 0: No conflict, stakes, or obstacle.

3. SPECIFICITY OF PROOF (0–5)
- 5: Concrete behavior, object, place, phrase, or gesture proves the thesis.
- 4: Specific proof exists but could be more visual.
- 3: Some details but they feel interchangeable.
- 2: Mostly abstract couple language.
- 1: Generic romance proof.
- 0: No proof trail.

4. EMOTIONAL REVERSAL (0–5)
- 5: The idea turns from joke to tenderness, fear to safety, surface to truth, or misread to meaning.
- 4: Reversal is present but not fully earned.
- 3: Emotional movement exists but it is predictable.
- 2: Slight tonal softening only.
- 1: Same feeling from start to finish.
- 0: No turn.

5. VISUAL SCENE CLARITY (0–5)
- 5: The core idea can be drawn or filmed in simple frames with clear roles.
- 4: Mostly visual; one abstract beat needs repair.
- 3: Usable but copy-dependent.
- 2: Requires explanation to understand.
- 1: Looks like a generic quote card.
- 0: No scene.

6. ONLINE SHARE/SAVE/SELL POTENTIAL (0–5)
- 5: Clear send/save/comment reason; strong caption, article title, or carousel hook.
- 4: Shareable but the close or hook needs sharpening.
- 3: Warm but not especially memorable.
- 2: Pleasant, low urgency.
- 1: Too private or generic to travel.
- 0: No online distribution reason.

DECISION RULES
- 28–30: GO. Proceed to the next C-layer or D-layer gate.
- 24–27: REPAIR. Fix the weakest dimensions and rescore.
- 18–23: REWORK. Return to the concept-process cards.
- 0–17: STOP. The premise is not ready.

A hard fail caps the decision at REPAIR regardless of numeric score.

HARD FAIL — reject or repair before proceeding
- No emotional obstacle (only a pretty moment).
- Generic couple dynamic (could be any two people).
- Zuv has no active emotional role.
- Ending is a quote, advice, or generic relationship maxim, not an earned payoff.
- Copyrighted source text copied verbatim into the artifact.
- Premise relies on private context the reader cannot infer.
- Thesis is a teach-claim ("relationships need X") rather than a lived truth.

REQUIRED RECORD (when scoring, write into `layer-e-story-selling.json`)
- concept title
- selected concept-process card (from `concept-process-cards.md`)
- six dimension scores
- total score
- hard-fail check
- decision: GO / REPAIR / REWORK / STOP
- one repair note for any dimension under 5

SOURCE POLICY (when drawing from external story craft)
- Use only allowed-use sources per `config/references/story-selling-canon/source-policy.md`.
- Do not copy copyrighted source text into artifacts; extract emotional patterns only.
- Record the source in `source-register.json` when a craft pattern is adapted.
