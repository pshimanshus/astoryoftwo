# Carousel learnings: end-to-end workflow integration

Date: 2026-09-20
Status: implemented on the isolated `codex/carousel-learning-integration` branch and copied into the shared workspace; publication loop remains data-dependent
Scope: connect retrieved carousel evidence to ideation, copy, visual direction,
generation, sequence review and subsequent learning through the existing workflow.

## Outcome

A learning is integrated when it changes a specific creative decision, that
decision survives packaging and image generation, the final pixels are reviewed
against it, and the published result can be traced back to it. Finding a research
page in search is only the first part.

The creator should experience one coherent creative conversation. Codex handles
selective reference recall, structured files, checks and repairs. Keep the existing
four gates: concept; copy + format; proof pixels + creator approval; final package
QA. Post-publication research is a separate maintenance activity, not a fifth
production gate or a prerequisite for the next draft.

```text
Creator seed / fresh idea
  -> alive first draft
  -> selective evidence and counterexample
  -> concept lock: one story intention
  -> copy + format lock: ordered copy and visible beats
  -> compiled slide prompts
  -> riskiest proof: actual pixels + creator approval
  -> remaining slides
  -> final package QA: frames AND whole sequence
  -> confirmed publication + dated observations
  -> descriptive comparison + next hypothesis
  -> evidence recall / approved durable correction
  -> next draft
```

## 1. Current position and concrete gaps

The saved research covers 27 mapped sequences, 158 slide positions and 153
distinct image hashes. It includes local source counterparts and earlier
Instagram reviews; it is not 27 controlled experiments or proof of exact
published bytes for every mapped image. The archive, compact semantic memory,
wiki page and targeted skill pointers already exist.

Repository inspection on September 20 found these integration gaps:

| Area | Existing support | Remaining gap |
| --- | --- | --- |
| Recall | Compact semantic memory and pointers from the storytelling/runtime skills | No common structured lookup connects a mechanism, its exact slide evidence and its counterexample to a package decision. |
| Analysis inputs | `carousel_intelligence.py` loads the September 19 seed, visual decisions and path map | The September 20 close readings are not its seed input. Three older prose mappings are known to be wrong. |
| Story handoff | `creative-context.json` and a creative brief exist | The context builder does not currently preserve a typed sequence intention from the brief; adding prose to a skill will not make it survive this boundary. |
| Slide handoff | `role`, physical action, relationship state, camera, continuity and `visual_richness` already travel through production | New beat fields must survive both `slides_from_creative_baseline()` and `_minimal_slide()`; otherwise the writer silently drops them. |
| Editorial checks | Existing concept analysis examines hooks, progression, payoff and alignment | “Alignment” currently means copy and scene fields are populated. Scene diversity is largely string comparison; relationship/progression/payoff use text markers. These cannot certify meaning or pixels. |
| Wordless beats | Research contains useful wordless closure | Brief ingestion and package readiness currently require nonempty copy. The analyzer also treats missing copy as incomplete. Intentional wordlessness needs an explicit representation. |
| Pixel review | Per-frame checks already include observed continuation, payoff, physical action and story evidence | A dedicated ordered sequence assessment must establish whether adjacent frames develop the story and whether the final beat fulfils the opening promise. |
| Results | `make analyze`, the A2/A3 pipeline and hash-bound published-image review exist | Generation packages, confirmed publication, dated native Insights and the chosen mechanism need a reliable join. Local production sources must remain distinct from published evidence. |

There is also active instruction drift: the current hash-bound intelligence
policy is enabled with a 70-point floor, while the compact production skills say
concept lock is a human decision and prohibit numeric taste gates. The plan must
resolve this explicitly. It must not quietly change thresholds or treat a
27/27 historical calibration pass as proof of editorial discrimination.

## 2. Evidence: make the research usable without loading the archive every time

Keep three layers with distinct jobs:

1. **Archive:** the full close readings, annotated slides, contact sheets and
   source bindings remain the research record.
2. **Compact recall:** `memory/semantic/carousel-sequence-learnings.md` remains
   the short explanation of mechanisms, counterexamples and limitations.
3. **Reference index:** `config/references/carousel-patterns.json`
   supplies stable, searchable mechanism records. It is derived from reviewed
   evidence, not a second rulebook or a new per-package ledger.

Each indexed mechanism should name what it does, when it helps, exact supporting
sequence/slide references, at least one relevant limit or contrast, and the
quality of the evidence. Keep separate fields for:

- what was visibly observed;
- the editorial interpretation;
- any associated performance snapshot and its observation date;
- the proposed creative test.

Useful retrieval dimensions: theme, sequence mode, hook mechanism, kind of
mismatch, swipe development, copy–image relationship, visual carrier, ending
mechanism and failure mode. A mismatch may concern motive, ownership, expectation,
capacity, belonging or timing; it need not be an argument.

Resolve the three superseded mappings in the derived index before using it:
`Dc5eniKic95` = public-pressure/husband-alliance; `DcRQEEjCSNo` = chores;
`DcG9gVzCfO7` = continuing commitment. Preserve old records as historical evidence,
with explicit supersession, rather than editing raw corpus to hide discrepancies.
Record the shared weather images so duplicate positions are not independent
visual observations.

Extend the existing memory index/recall surface to find these records. After an
alive draft exists, retrieve only the best one or two mechanisms plus a relevant
counterexample. If there is no useful match, continue with an honest hypothesis.
Do not force a historical analogue, copy a winning post, or load the full archive
at every jam. Historical metrics and the complete corpus stay out of ImageGen.

## 3. One story intention, then one authoritative slide sequence

### Concept lock: preserve the whole idea

Add a compact `story_plan` section to the existing `creative-context.json`, carried
from the approved brief. Suggested fields:

| Field | Question it answers |
| --- | --- |
| `theme` | What specific truth about these two people is this story expressing? |
| `recognition` | Who recognises themselves or their partner, and in what behaviour? |
| `sequence_mode` | How does this particular sequence develop? |
| `opening_promise` | What curiosity, recognition or emotional expectation does the cover create? |
| `mismatch` | What difference in motive, words, behaviour, need or expectation gives it energy? |
| `turn_or_accumulation` | What changes the reader's understanding, or what distinct evidence accumulates? |
| `payoff` | What ending action or interpretation fulfils the opening promise? |
| `send_reason` | What would one partner be communicating by sending it? |

Preserve raw facts, creator wording and approved architecture alongside this
section. An optional small `research_refs` list can identify which examples
informed a decision and why; it is not another mandatory provenance artifact.

Support four observed modes as useful descriptions, not an exhaustive taxonomy:

| Mode | What earns each swipe | What completeness means |
| --- | --- | --- |
| One unfolding question | Changed pressure, information, timing or expectation | The question receives an earned response or reversal. |
| Independent recognition rewards | Another distinct, complete miniature observation or joke | The series fulfils its premise; a callback or final joke can close it. |
| Accumulating evidence | A new dimension of the relationship | The details establish the larger meaning without repeating the same proof. |
| Changing relationship state | A changed choice, position, capacity or bond | The later state is understandable because of what preceded it. |

Allow hybrids and creator-supplied structures. “Change” can be a change in the
viewer's interpretation, not a correction to either partner's personality.
Do not manufacture dramatic conflict, an unresolved question on every card, or a
single recurring prop for a catalogue of separate moments.

### Copy + format lock: make each swipe accountable

Use `slides.json` as the single source for the sequence. Reuse current fields
before adding new ones:

| Needed information | Existing home or proposed addition |
| --- | --- |
| Exact on-image text | Existing `copy`; proposed `copy_mode: text / wordless` |
| Slide's job | Existing `role` |
| What this card newly gives the reader | Proposed short `beat_delta` |
| Observable proof | Existing `physical_action`, `relationship_state`, `visual_richness.story_evidence` |
| How image and words work together | Proposed `copy_image_relation` with a brief explanation: contradiction, completion, reinterpretation, direct depiction or intentionally wordless |
| Before/after, next reward or question | Existing `visual_richness.before_frame`, `after_frame`, `continuation_pull` |
| Relevant recurring object/person state | Existing `props`, `continuity_lock`, hand map and spatial topology |
| Visual emphasis and pacing | Existing camera, focal hierarchy, setting, light and depth fields |

Codex fills these from the draft; the creator does not complete a questionnaire.
Show a simple ordered storyboard when useful: copy, visible action, what changes,
and next-swipe reason. This lets the creator assess the whole story at Gate 2.

Copy review checks the premise, rhythm, character voices and ending together.
Language and word count serve the specific scene: spoken Hinglish, reflective
English, longer explanation and silence are available choices, not performance
rules. Consult Humanizer when drafting public copy. Ask whether the words explain
something the picture could prove and whether the picture contributes anything
the words do not already supply.

Intentional wordlessness must be locked, compiled and reviewed explicitly:
`copy_mode=wordless` with empty `copy` is allowed; accidental empty copy still
fails. The brandmark remains required. Update all relevant ingestion, readiness,
compiler and pixel-text checks together so a later stage cannot reintroduce the
old failure or invent a line.

### Example: how a finding becomes a usable decision

Use the existing husband-summons sequence as a retrospective demonstration,
not a proposed new post:

| Position | New information | Visual responsibility | Swipe/closure job |
| --- | --- | --- | --- |
| 1 | One partner calls from a distance | Establish separation and direction of attention | What does she need? |
| 2 | The call continues | Preserve separation while the split word performs duration | Sustain the question through timing. |
| 3 | His arrival reveals the affectionate motive | Make arrival and the response legible | Reinterpret the apparent summons. |
| 4 | He reciprocates | The wordless hug completes the response | Resolve distance into mutual closeness. |

The usable learning is the connection between distance, duration, arrival and
reciprocity. “Four slides perform well” would discard the mechanism.

## 4. Carry the intention through generation and repair

Update the brief normalizer, package writer and fingerprints together. Test that
the approved `story_plan`, `beat_delta`, copy mode and copy–image relationship
survive creation and resume. A field in a planning JSON that disappears before
generation is not an implemented handoff.

Compile only the slide's actionable visual consequence: who acts, what object
state or response matters, what must be readable first, relevant continuity and
exact locked text. A contradiction such as spoken denial versus visible tears
must survive in the physical staging. Research explanations, metric tables and
scoring instructions must not enter the image prompt. Preserve current prompt
budgets, reference attachments, style resolution and requested native dimensions.

Choose the proof by the story's greatest uncertainty: for example, whether a
small act of care, change of ownership or comic contradiction will read in pixels.
The default remains one riskiest slide. Review cross-slide effects when the deck
exists; do not introduce a compulsory second proof or new approval gate.

Repair the failed layer:

- unclear theme/opening promise: revise the concept;
- redundant middle or unsupported payoff: revise the sequence;
- copy–image mismatch: repair wording or staging while respecting locked copy;
- good planned event, unreadable pixels: repair action, framing or object state;
- rendering drift: repair generation inputs and inspect the replacement pixels.

Reuse existing `feedback`, `revise` and `feedback-status`; retain exact creator
words and change/preserve constraints. If a proposed repair changes approved copy
or concept, return to that existing lock. Do not silently rewrite an approved
line while fixing a hand.

Use existing invalidation mechanics: changed slide semantics revoke affected
render/QA bindings; shared generation inputs or order follow the existing deck
invalidation policy. A changed sequence judgment invalidates sequence review.
A research annotation change alone should not regenerate unchanged art. Separate
generation dependencies from review-only research metadata and test both.

## 5. Final review must establish completeness

Add a compact `sequence_review` to the existing `visual-qa.json`, bound to the
ordered final manifest and the current story/beat inputs. Keep inventory in
`final-images.json` and the resulting status/issues in `final-audit.json`.
No second manifest or review ledger is needed.

Codex inspects the full ordered strip and individual slides where detail matters.
Record specific evidence for:

1. **Hook:** what the cover lets a cold viewer recognise and what it promises.
2. **Every transition:** what new information, pressure, reward or interpretation
   appears; note accidental repetition and misplaced peaks.
3. **Copy with image:** whether the intended contradiction/completion/reframe is
   visible in the actual output. Populated fields are not sufficient.
4. **Whole-deck coherence:** character agency, chronology and any meaningful
   object states; visual emphasis should follow the story.
5. **Closure:** which earlier details the ending answers, gathers or reinterprets;
   whether a further card repeats an already-complete emotional result.

Use a text-hidden read to identify the image's contribution, then restore the
words to assess the combined meaning. Do not demand that the image alone tell a
copy-dependent verbal joke. Use slide-removal/reordering questions as editorial
diagnostics, not universal automated failures: timing and rhythmic repetition can
be intentional, and independent catalogue entries may legitimately be reorderable.

Machine checks validate required observations, slide coverage, current inputs,
order and asset bindings. They cannot decide whether a hug feels earned. A
syntactically valid review or high heuristic score is not a visual PASS.
Gate 4 reports concrete unresolved sequence issues and blocks final completion
when the intended story is missing, even if every isolated frame is polished.

## 6. Close the loop after publication

Reuse `make analyze`, `pipeline/stages/a2_parser.py`, `a3_analyzer.py` and
`carousel_analysis.py`. Add the missing join as post-publication research metadata
in the existing corpus/analysis surfaces, outside the minimal production package:

- package ID and final-manifest fingerprint;
- confirmed published shortcode/URL, publication time and slide order;
- verified published-image correspondence, or an explicit unverified status;
- caption/context changes, distribution conditions and chosen creative hypothesis;
- observation time, post age, native metric label, value, source and availability.

Platform image recompression means published bytes can differ from final PNGs.
Record a reviewed correspondence when established; do not claim byte identity
without equal hashes. Do not move a local draft into the published archive simply
to make the existing review validator accept it.

Preserve Views, Viewers, Shares, Saves, Follows, reach and sends separately where
actually available. The current normalized metric aliases do not cover all of
these private Insights labels, and the intelligence scanner expects a different
shape from the normalized engagement object. Reconcile the adapters instead of
letting each analyzer calculate from its own partially compatible rows. Missing
values remain unavailable, not zero; denominator choice and source accompany
every rate. Deduplicate by post and observation snapshot.

Proposed collection checkpoints are 24 hours, 7 days and 30 days, recorded at the
actual observation time. These are project measurement choices, not algorithm
windows or an automation created by this plan. Existing age-band and coverage
limits continue to govern cohort comparisons; early readings stay descriptive.

For each reviewed result, report:

1. what we intended and what the final work actually did;
2. observed distribution and response, with post age and denominator;
3. useful same-format, similar-age contrasts and important differences;
4. whether the mechanism remains promising, ambiguous or contradicted;
5. one focused change worth testing next.

No available snapshot establishes per-slide abandonment, dwell or completion.
Call swipe-strength assessments editorial hypotheses unless those measurements
exist. Shares do not establish private DM counts. Separate apparent reach from
response rates; do not turn a low-distribution post into a settled creative failure.

Feed supported observations back into the reference index/semantic recall with
their limits. Preserve creator corrections in the existing LearningEvent path.
Changes to reusable rules or skills remain explicit, reviewable proposals;
ordinary production does not silently write global policy. Unsuccessful and
contradictory examples must remain searchable alongside successes.

## 7. Ordered implementation slices

| Slice | Main surfaces | Acceptance evidence |
| --- | --- | --- |
| 1. Trustworthy retrieval | Proposed reference index; `carousel_intelligence.py`; existing memory index; semantic pointers | Corrected mappings win; slide references resolve; duplicate imagery is disclosed; local-source and published evidence remain distinct; a mechanism search returns a relevant limit as well as a positive example. |
| 2. Preserve creative decisions | `codex_native_carousel.py`, `carousel_package_writer.py`, `carousel_generation_inputs.py`; existing context/slides schemas | Story intention and beat fields round-trip; explicit wordless slides survive; accidental empty copy fails; archived packages remain readable without forced migration. |
| 3. Compile and review the sequence | `carousel_prompt_compiler.py`, `carousel_visual_storytelling.py`, `carousel_pixel_qa.py`, `carousel_generation_state.py` | Prompt contains the physical meaning; QA covers each transition and closure; stale order/input/asset bindings revoke review; research metadata alone does not unnecessarily regenerate art. |
| 4. Reconcile the editorial check | `carousel_intelligence.py`, gate policy, runtime/intelligence skills and focused tests | Resolve numeric-gate instruction drift with an explicit reviewed diff; structural checks are distinguished from actual editorial/pixel judgment; all four sequence modes and known counterexamples are exercised. |
| 5. Connect results and learning | A2/A3, `carousel_analysis.py`, existing corpus/Insights adapters and learning loop | Confirmed package-to-post link; native metrics/date/age retained; missing data handled honestly; a result updates recall without automatically changing production policy. |
| 6. Pilot and consolidate guidance | Runtime context, autopilot, storytelling/direct-visual skills, workflow registry and docs contracts | One new package completes all four gates using the same source fields; final sequence review and a later results review can explain what was learned and where the evidence stops. |

Slices 1–4 must be integrated before the live pilot. Slice 5 needs at least one
confirmed publication and dated observation to demonstrate the complete learning
loop; until then it is tested plumbing, not verified end-to-end operation.
Update dependent instructions after behavior is verified. Keep `AGENTS.md` as
the existing router; do not expand it into the research report.

Implemented treatment of the current score conflict: preserve concrete structural
and production failures as blocking checks, use heuristic scores as advisory
diagnostics, and require actual evidence for editorial judgments. The active gate
policy records this as `structural_with_advisory_heuristics` and binds the
`carousel-sequence/v1` contract and reviewed pattern registry. It does not lower
the production floors or certify editorial taste from historical calibration alone.

## 8. Verification and definition of done

Use a small, varied retrospective set before one fresh live carousel:

- husband summons: one setting, meaningful timing, reciprocal wordless closure;
- original and later rulebooks: same count, different details and historical results;
- shared objects: accumulation and the distinction between reach and response;
- commute: a turn delivered early and then repeated;
- versions of us: copy names a change that the boxes alone do not establish;
- food catalogue: repeated form with separate rewards rather than forced plot;
- deliberately broken copies: swapped ending, redundant beat, unsupported copy,
  stale mapping, changed asset and missing metric.

Deterministic tests cover field preservation, intentional silence, bindings,
mode-aware validation, provenance and metric integrity. Human/model pixel reads
cover semantic contrast and completeness. Do not make tests pass by inserting
“payoff”, “relationship” or “new event” into every fixture. Historical acceptance
does not mean every historical slide is strong.

Extend the existing focused suites for intelligence, source normalization,
generation inputs, compiler, pixel QA, state and carousel analysis. Run the
public CLI lifecycle test after integration. Run instruction contracts when
skills/docs change; Agentic OS and wiki health remain maintenance/closeout checks,
not generation preflights.

Completion requires all of the following:

- a recalled finding has an exact evidence source and a stated limit;
- its chosen application persists from brief to slide plan to prompt;
- each swipe has a clear contribution appropriate to the sequence mode;
- final pixels, paired copy and the whole ending are actually inspected;
- feedback repairs the correct layer and preserves unrelated approved work;
- the published version and dated results can be linked honestly;
- the next draft can recall both the result and its uncertainty;
- the creator still sees four gates, with no extra form, agent room or research chore.

At plan creation, prior save validation recorded two existing health failures:
creator-feedback lifecycle debt and a missing historical ImageGen attempt receipt.
They are separate maintenance issues, not evidence that this integration works or
fails. Recheck at implementation closeout; never fabricate historical receipts or
mark feedback resolved to obtain a green report. Scope any commit to owned files
because the current worktree contains unrelated edits and staged changes.

## Plan-delivery validation

This document was checked on 2026-09-20. All local Markdown links resolve.
The implementation suites for sequence contracts, production handoffs, pattern
evidence, native metrics, source normalization, pixel QA, CLI lifecycle and
benchmark passed 396 tests in the isolated workspace. This validates workflow
plumbing and authored contracts; it does not certify generated pixels or claim a
live publication performance result.

Current Agentic OS health remains FAIL and wiki health remains NEEDS_HEAL with
the same two failure categories named above. The scoped autopublish dry run was
rejected by automatic approval review: approval is required while the session's
approval mode is Never. This plan is saved locally; no commit or push was made.

## Source pointers

- [Saved research](../../../wiki/insights/retrieved-carousel-pattern-analysis.md)
- [Compact learnings](../../../memory/semantic/carousel-sequence-learnings.md)
- [Per-slide observations](../../../output/reports/2026-09-20-carousel-pattern-analysis/beat-notes.json)
- [Archive and validation](../../../output/reports/2026-09-20-carousel-pattern-analysis/save-validation.json)
- [Current workflow](../../../config/skills/carousel-jam-runtime-context.md)
- [Current autopilot](../../../config/skills/carousel-jam-autopilot.md)
- [Existing operational plan](THE-PLAN.md)
