# Failure Taxonomy

Use these exact codes in evals, trace logs, reports, and blocked states.

- `IDENTITY_REFERENCE_MISSING`
- `IDENTITY_REFERENCE_INPUT_UNPROVEN`
- `GOLD_STANDARD_IDENTITY_ROUTE_MISSING`
- `IDENTITY_DRIFT`
- `FACE_MERGE`
- `STYLE_DRIFT`
- `QUOTE_CARD_NOT_ILLUSTRATION`
- `YELLOW_PAPER_CAST`
- `TEXT_MISSING_IN_IMAGEGEN`
- `TEXT_UNREADABLE`
- `TEXT_NOT_EXACT`
- `BRANDMARK_MISSING`
- `PROMPT_BRANDMARK_MISSING`
- `PROMPT_CANVAS_SIZE_MISSING`
- `WRONG_CANVAS_SIZE`
- `SCENE_LOGIC_CONTRADICTION`
- `VISUAL_SETTING_CONTRADICTION`
- `ANATOMY_FAILURE`
- `WARDROBE_CONTINUITY_FAILURE`
- `AI_SLOP_COPY_DRIFT`
- `VIRAL_RESEARCH_LAYER_SKIPPED`
- `PLATFORM_MECHANIC_MISSING`
- `VISUAL_ONLY_MOOD_WORDS`
- `EVIDENCE_GAP_UNDISCLOSED`
- `GENERIC_IDEA`
- `SCENE_LANDING_MISSING`
- `WEAK_PAYOFF`
- `TOO_MANY_SLIDES`
- `TOO_FEW_SLIDES`
- `PROMPT_OVERLOAD`
- `PROMPT_PALETTE_CONFLICT`
- `GENERATION_CONTINUED_AFTER_HARD_REJECT`
- `HITL_NOT_APPROVED`
- `AGENT_ASSIGNMENT_MISSING`
- `IMAGEGEN_TOOL_FAILURE`
- `ARTIFACT_MISSING`
- `DEBATE_COLLAPSE`
- `LOW_SCORE_NO_SELECTION`

Each failure record includes:
- stage
- severity
- failed gate
- likely cause
- attempted repair
- retry count
- final status
- prevention note

## Visual Failure Examples

`references/failures/visual-inconsistencies/` holds creator-rejected renders as a
negative reference. Every filename names the failure in plain language. Image QA
must check each candidate slide against this folder and cite the matching code
below when rejecting:

- inconsistent / rubber hands, impossible hand poses → `ANATOMY_FAILURE`
- two seats merged into one; cup holder behind a car seat; bench-with-shawl that
  makes no physical sense; wrong gaze direction → `SCENE_LOGIC_CONTRADICTION`
- on-image text missing entirely → `TEXT_UNREADABLE`
- imagegen prompt asks for blank space, later overlay, or omits the exact
  locked on-image text from generation → `TEXT_MISSING_IN_IMAGEGEN`
- text not in the A Story Of Two handwritten font when baked into the
  illustration → `TEXT_NOT_EXACT`
- locket forced onto Zuv / worn in a way no one wears it → `SCENE_LOGIC_CONTRADICTION`
- prompt omits native `1080x1350 px` → `PROMPT_CANVAS_SIZE_MISSING`
- prompt omits tiny top-right `@a.storyof.two` → `PROMPT_BRANDMARK_MISSING`
- generated candidate is not native 1080x1350 px → `WRONG_CANVAS_SIZE`
- exact-copy slide is rendered as a designed quote card, poster, typography
  layout, deterministic text card, or decorative background instead of a lived
  Aachu/Zuv watercolor-and-ink illustration → `QUOTE_CARD_NOT_ILLUSTRATION`
- visual setting, prop placement, eyeline, or physical environment makes no
  concrete sense for the locked beat → `VISUAL_SETTING_CONTRADICTION`

These are illustrative, not exhaustive: any new creator-rejected render should be
added here with a self-describing filename and mapped to its code.
