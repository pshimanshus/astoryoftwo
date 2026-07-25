# Project Failure Taxonomy

last_updated: 2026-07-25
confidence: 0.93
sources:
- AGENTS.md
- evals/research/sources.json
- memory/semantic/carousel-idea-preferences.md
- memory/semantic/engineering-workflow-preferences.md
- memory/semantic/visual-director-intelligence.md
- memory/agentic/learning-events/
- output/concepts/
- output/carousels/
- pipeline/agentic/workflow_doctor.py
- scripts/autopublish.py
- scripts/wiki_health.py

## Purpose

This taxonomy maps recurring @a.storyof.two agent failures to eval task
families. The embedded Evidence Ledger names the actual memory, audit,
rejection, blocker, and package artifacts that caused each task to exist. It
separates mechanical contract failures from creative contract failures so a
subjective taste score never hides a broken production gate.

## Evidence Ledger

This ledger keeps the eval suite grounded in the repo's actual repeated
mistakes. It is not a generic benchmark wishlist. New eval tasks should trace
back to one or more rows here, then reduce the failure into a realistic
starting state, fail-to-pass condition, pass-to-pass regression surface, and
checker strategy.

Search labels covered here: stale artifact carryover, home-like visuals,
copy-visual logic, score inflation after rejection, identity eval stop gate.

### E01 Instruction Authority Drift

Pattern: downstream prompts, audits, or rules drift from `AGENTS.md` and
agents are tempted to patch the root contract instead of the dependent surface.

Evidence:
- `AGENTS.md` says not to edit it to resolve downstream mismatches.
- `docs/audits/2026-05-16-carousel-pipeline-structure-audit.md` records older
  prompt/style surfaces mixing generic C-layer language with stricter gates.
- Older package audits contain stale brandmark placement such as bottom-right
  while current rules require top-right.

Eval coverage:
- `ASTO-001-brandmark-drift`
- `ASTO-007-context-rule-truncation`

### E02 Format Snapback And Native Output Confusion

Pattern: workflow defaults override the latest creator correction, or package
metadata claims finality while native size requirements fail.

Evidence:
- `memory/semantic/engineering-workflow-preferences.md` records the 2026-07-02
  correction: lock the exact canvas and do not snap back to repo defaults.
- `output/carousels/2026-06-30/tum-meri-baat-sun-rahe-ho/image-generation-blocker.md`
  blocks generation because proof attempts did not preserve `1440x1920` source
  and `1080x1440` final export requirements.
- `output/carousels/2026-07-12/after-one-hour-with-you-zuv-pov/visual-qa.md`
  records proof images at `1086x1448` and `941x1672`, not publishable native
  outputs.

Eval coverage:
- `ASTO-002-format-snapback`
- `ASTO-004-fake-publishable-package`

### E03 Textless Or Deferred Typography Shortcuts

Pattern: an agent tries to generate blank source art and add narrative text
later, even though the project requires exact on-image text and brandmark
inside the image from the first proof onward.

Evidence:
- `memory/semantic/carousel-idea-preferences.md` records repeated creator
  corrections on 2026-06-14, 2026-06-30, and 2026-07-03: never generate
  textless @a.storyof.two proof/concept/final images.
- `memory/semantic/visual-director-intelligence.md` says deferred lettering is
  blocked, not a valid intermediate.
- `output/carousels/2026-06-30/tum-meri-baat-sun-rahe-ho/image-generation-blocker.md`
  says the blank edit-target experiment was invalid.

Eval coverage:
- `ASTO-003-textless-prompt`

### E04 False Finality And Publishable Package Theater

Pattern: the repo produces a strong-looking package, review, or proof set and
then calls it done despite missing native finals for the current-request format
lock, structured QA, final audit, source provenance, or an explicitly requested
Story/Reel or square output.

Evidence:
- `docs/audits/2026-05-16-carousel-pipeline-structure-audit.md` records stale
  `PASS_WITH_NOTES` packages that predated final-image and identity gates.
- Multiple `output/carousels/*/final-audit.json` files report missing
  `final/slide-XX.png`, requested `final-reels-stories/` assets, and missing
  structured `visual-qa.json`.
- `output/carousels/2026-07-11/the-almosts-were-practicing/visual-qa.md`
  explicitly says the folder is a post-format draft illustration set, not a
  full publish closeout package.

Eval coverage:
- `ASTO-004-fake-publishable-package`
- `ASTO-014-identity-eval-stop-gate`

### E05 Working Memory And Durable Learning Misplacement

Pattern: agents dump durable policy into `memory/working.md`, skip semantic
confidence/sources, or let memory/wiki surfaces drift after session close.

Evidence:
- `AGENTS.md` says `memory/working.md` is pointer-only.
- `memory/semantic/carousel-idea-preferences.md` has a "How This Ledger
  Learns" method that says to update, merge, downgrade, delete, or append
  crisp durable learning.
- `memory/agentic/learning-events/` and `memory/agentic/learning-proposals/`
  show the desired proposal-first path for applying durable learning.
- `output/diagnostics/wiki-health-*.md` defines the wiki/memory health checks
  expected at closeout.

Eval coverage:
- `ASTO-005-working-memory-pointer`

### E06 Skill Routing And Context Loading Drift

Pattern: carousel jams skip the creator skill stack, compact runtime context,
or required rules because a routing surface falls out of sync.

Evidence:
- `AGENTS.md` requires `config/skills/creator-skill-stack.md` at creative
  session start and jam start.
- `config/skill-systems.json`, `config/agentic_context_manifest.json`,
  `.agents/skills/a-story-carousel-jam/SKILL.md`, and `scripts/jam_today.py`
  all participate in routing.
- `tests/test_creator_workflow_contract.py` protects these surfaces.

Eval coverage:
- `ASTO-006-creator-skill-routing`
- `ASTO-007-context-rule-truncation`

### E07 Score Inflation After Creator Rejection

Pattern: the room assigns 28-29/30 scores to concepts the creator later rejects
as unsendable, low-average, or far below the winning-carousel bar.

Evidence:
- `memory/agentic/learning-events/event-2026-06-06-1.json` records repeated
  low-average concepts despite fresh research and multiple repair attempts.
- `output/concepts/2026-06-06/ideation-quality-failure-diagnosis.md` diagnoses
  checklist completeness and score inflation.
- `output/concepts/2026-06-23/seeti-count-marriage-jam/concept-selection.json`
  gives `Seeti Count Marriage` 29 and 28.5 while marking it
  `REJECTED_BY_CREATOR`.
- `output/concepts/2026-06-23/seeti-count-marriage-jam/rejection-note.md`
  says prior scores were inflated and should not be used as calibration.

Eval coverage:
- `ASTO-015-score-inflation-after-rejection`

### E08 Framework-First Or Generic Creative Output

Pattern: agents answer small creative prompts with rubric names, score tables,
or generic relationship theories before preserving a human seed and a live
scene.

Evidence:
- `AGENTS.md` says not to answer a small creative brief with a framework
  report.
- `memory/semantic/carousel-idea-preferences.md` says not to start a jam with
  5-line copy, hook banks, or visible architecture.
- `output/concepts/2026-06-27/bids-for-connection-jam/copy-repair-v2.json`
  records a draft that stated a thesis instead of telling a story.
- `output/concepts/2026-06-06/ideation-quality-failure-diagnosis.md` says
  recognizable tropes are not enough without freshness and ownability.

Eval coverage:
- `ASTO-011-small-brief-no-framework-dump`
- `ASTO-015-score-inflation-after-rejection`

### E09 Stale Artifact Carryover After Corrections

Pattern: the creator corrects a story, proof, format, or route, but downstream
artifacts still contain the old text, old route, old prompt language, or old
package status.

Evidence:
- `memory/semantic/engineering-workflow-preferences.md` says stale downstream
  artifacts after creator correction are a production bug and lists the files
  that must be rebuilt.
- The same memory requires `rg` for old phrases before generation.
- `memory/semantic/carousel-idea-preferences.md` says a creator rejection means
  stop and rebuild from the raw row, not polish the same concept.

Eval coverage:
- `ASTO-013-stale-artifact-after-correction`

### E10 Identity Eval Stop-Gate Failure

Pattern: a proof looks pretty, so agents continue generating or presenting
slides even though no structured face/likeness eval exists.

Evidence:
- `memory/semantic/engineering-workflow-preferences.md` records the 2026-07-12
  correction after `The Almosts Were Practicing`: no identity eval means no
  next slide.
- `config/rules/identity.md` makes this a canonical rule with
  `BLOCKED_FOR_IDENTITY_EVAL` / `IDENTITY_UNVERIFIED`.
- `output/carousels/2026-07-11/the-almosts-were-practicing/visual-qa.md`
  says face identity was not passed.
- `output/carousels/2026-07-11/the-almosts-were-practicing/identity-consistency-review.json`
  correctly records `IDENTITY_UNVERIFIED`, `STOP`, and `can_continue_batch:
  false`.

Eval coverage:
- `ASTO-014-identity-eval-stop-gate`

### E11 Visual Repetition And Weak Shot Grammar

Pattern: slide copy is warm, but all images become the same medium couple shot,
same room, same objects, or same listening/comfort posture.

Evidence:
- `memory/semantic/carousel-idea-preferences.md` records creator correction on
  2026-06-15: always break the visual pattern across carousel images.
- `config/rules/visual-variety.md` requires a shot ladder and repeated
  prop/setting audit.
- `output/carousels/2026-07-12/after-one-hour-with-you-zuv-pov/visual-qa.md`
  notes slides 3, 4, and 6 were regenerated to repair repeated couch/table
  shots.

Eval coverage:
- `ASTO-012-visual-variety-shot-ladder`

### E12 Home-Cinematic Visual Evidence Gap

Pattern: agents say "cozy home" or "warm domestic scene" without designing
interiors as lived-in relationship evidence: motivated light, camera position,
blocking, object continuity, tactile surfaces, and home-specific story proof.

Evidence:
- Creator correction on 2026-07-20: the project lacked a visual theme pushing
  agents toward vibrant, real, home-like visuals like
  `output/carousels/2026-07-03/the-house-learned-us/proofs/contact-sheet.png`.
- `memory/semantic/visual-director-intelligence.md` already has shot grammar,
  but not a dedicated home-cinematic pass.
- `output/carousels/2026-07-03/the-house-learned-us/proofs/` demonstrates the
  target: object constellations, doorway views, mirrors, table-level closeups,
  pooja corner, morning/night light, plants, fabrics, mugs, laptop, watch,
  hair clip, charger, bag, and final room payoff.

Eval coverage:
- `ASTO-016-home-cinematic-visual-evidence`

### E13 Public / Private Name Boundary Leakage

Pattern: internal names are correct for identity prompts and QA, but they leak
into public-facing slide copy when the creator has not asked for names.

Evidence:
- `memory/semantic/carousel-idea-preferences.md` says do not mention "Aachu" or
  "Zuv" in public-facing carousel copy unless explicitly requested.
- `AGENTS.md` allows names internally through identity/reference workflows but
  emphasizes voice, actual couple, and public copy taste.

Eval coverage:
- `ASTO-017-public-name-leakage`

### E14 Copy-Visual Logic Contradictions

Pattern: image style or identity passes, but the visible scene contradicts the
approved copy, making the story impossible.

Evidence:
- `config/rules/identity.md` records the 2026-05-30 phone-prank slide where
  Zuv was already wearing pants while the copy said "YOUR SOCKS ON BEFORE YOUR
  PANTS."
- `memory/semantic/carousel-idea-preferences.md` says future visual QA must
  block copy-visual logic failures and awkward poses.
- `output/concepts/2026-06-14/roti-bite-rights-jam/scratch-storyboard.md`
  locks exact scene logic: Zuv looks at his father, does not hold a bite, and
  Aachu is already eating.

Eval coverage:
- `ASTO-018-copy-visual-logic-contradiction`

### E15 Unsafe Closeout And Mixed Worktree Publishing

Pattern: agents stage secrets, identity images, generated media, logs, or
unrelated mixed-worktree changes because the code path treats "publish" as a
blind git operation.

Evidence:
- `AGENTS.md` warns not to stage a mixed worktree silently.
- `scripts/autopublish.py` and `tests/test_autopublish.py` encode risky-path
  and secret scanning.
- `memory/semantic/engineering-workflow-preferences.md` rejects blind
  auto-pushing and timer daemons.

Eval coverage:
- `ASTO-008-autopublish-risky-paths`

### E16 Duplicate Background Characters

Pattern: a polished image invents extra background people, reflected figures,
silhouettes, or a duplicate couple while broad visual QA still claims PASS.

Evidence:
- `config/rules/scene-entity-integrity.md` now treats expected/observed people
  counts and unexpected entities as a hard visual QA gate.
- `pipeline/stages/carousel_quality.py` has
  `validate_scene_entity_integrity_check` for per-slide scene inventories.
- This remains a secondary general safeguard, not the creator-identified
  failure in the moving-box image.

Eval coverage:
- `ASTO-019-duplicate-background-characters`

### E17 Hand Ownership And Object-Contact AI Slop

Pattern: an illustration is text-correct and attractive, but a hand has no
owner or story purpose, enters anonymously from an edge, or passes through a
solid object. Finger count and people count may still look correct.

Evidence:
- Creator correction on 2026-07-20 identified the primary moving-box failure:
  Zuv's right hand/forearm penetrated the solid box wall.
- A second rejected doorway slide contained an unnecessary hand entering from
  the door edge with no traceable wrist, forearm, or required action.
- The source direction asked Zuv to brace the door while already using a hand
  for the focal tissue exchange, inviting an unnecessary secondary limb. That
  instruction was removed from every generation-facing artifact.
- `validate_anatomy_inventory_check` now requires narrative necessity,
  ownership, attachment, contact geometry, occlusion evidence, absence of
  solid-object intersection, and absence of unexplained edge entry.

Eval coverage:
- `ASTO-020-hand-object-integrity`

### E18 Whole-Person Spatial Topology Failure

Pattern: an illustration passes broad visual checks while a full body merges
into a wall, door, frame, chair, sofa, bed, table, or other solid object. The
person count and hand count may be correct, but the figure cannot be traced as
a believable body occupying the room.

Evidence:
- The 2026-07-20 spatial-integrity repair plan records the motivating doorway
  failure: Zuv's shoulder/back/torso visually merged into the door and frame.
- `validate_spatial_topology_check` now requires environment planes, body-region
  depth relationships, continuous silhouettes, occlusion-order evidence, and
  unresolved-intersection lists.
- `ASTO-021-whole-person-spatial-integrity` materializes this as a deterministic
  fixture so future agents cannot rely on hand-count or style QA alone.

Eval coverage:
- `ASTO-021-whole-person-spatial-integrity`

### E19 Eval Direction And No-Op Credit

Pattern: a seeded bad artifact is correctly blocked by the current production
gate, but the task is presented as though an agent still needs to repair it. A
no-op agent can then receive solve credit because fixture detection and agent
task resolution are conflated.

Evidence:
- The 2026-07-21 all-task audit found both solution fixtures that start
  `unresolved` and regression fixtures that start `guarded`.
- Regression fixtures for package, visual, identity, and closeout gates already
  pass their named checker on the protected implementation.
- OpenAI's 2026 coding-eval audit identifies misleading prompts,
  underspecification, overly strict tests, and low coverage as separate task
  quality failures; no-op credit is a local low-coverage/misalignment form.

Eval-system coverage:
- every task declares `fixture_contract`;
- `evals/runner.py review` checks each starting direction once in registry
  order;
- regression fixtures require a hidden code mutation or pre-fix revision
  before they can award agent solve credit;
- `evals/runner.py baseline` refuses already-resolved starters and writes its
  hash snapshot outside the solver workspace;
- `evals/runner.py grade` requires a real changed path, a declared solution
  file update, and every baseline failure to flip to `PASS`;
- `evals/**` is protected from solver changes.

### E20 Stale Or Agent-Inferred Human Approval

Pattern: an automated verifier result, old creator decision, or agent-authored
ledger entry is treated as permission to enter copy, image, or publish work
after the approved artifact changed. The creator saw one candidate, while
downstream production acts on another.

Evidence:
- `memory/episodic/2026-07-25-session-health.md` records the implementation of
  hash-bound concept, copy, image, and publish checkpoints.
- `config/skills/carousel-review-loop.md` states that verifier `PASS` is not
  creator approval and that every candidate must stop at a hash-bound human
  decision.
- `tests/test_carousel_review_loop.py` covers stale artifact hashes,
  downstream-lock invalidation, and explicit
  `creator_concept_approval_required` blockers.
- `ASTO-022-hil-stage-checkpoints` proves a current explicit approval is valid
  before mutation and invalid immediately after its governed concept changes.

Eval coverage:
- `ASTO-022-hil-stage-checkpoints`

## Mechanical Contract Failures

- Root-contract damage: editing `AGENTS.md` to resolve downstream drift.
- Rule-authority drift: copying stale rule fragments instead of using
  `config/rules/` as canonical source.
- Unsafe closeout: staging `.env`, identity media, generated finals, logs,
  caches, or unrelated mixed-worktree files.
- False finality: claiming publishable images without native assets, visual QA,
  final audit, exact text, identity references, or brandmark evidence.
- Context mutilation: truncating required rule text or dropping hard-fail
  fragments from assembled context or prompts.
- Memory corruption: turning `memory/working.md` into durable memory, omitting
  semantic confidence scores, or deleting episodic records.
- Stale artifact carryover: after a creator correction, old route/copy/prompt
  strings remain in generation-facing files and still drive the next proof.
- Identity stop-gate bypass: continuing from a pretty proof without structured
  reference IDs, likeness notes, and `identity-consistency-review.json` or
  `visual-qa.json`.

## Creative Contract Failures

- Framework-first response: showing rubric terms, score tables, or process
  language before an alive human route.
- Seed erasure: replacing the creator's actual feeling, line, photo, or moment
  with a generic couple trope.
- Text-driven poster spine: visuals become interchangeable if slide copy is
  hidden.
- Relationship-motion collapse: every route becomes "Aachu is chaos, Zuv is
  caretaker" even when the moment needs mutuality, Aachu agency, or no heroic
  actor.
- Visual repetition: same medium two-shot, same room, same posture, same action
  across slides.
- Identity/style drift: text says "same couple" but no actual identity/style
  references guide the whole illustrated person.
- Score inflation after rejection: concept rooms keep 28-29/30 scores after
  the creator says the idea is unsendable or far below the winning carousel
  bar.
- Home-cinematic underdirection: prompts say "cozy home" but omit camera
  position, motivated light, blocking, object continuity, tactile surfaces, and
  home-as-story evidence.
- Public/private boundary leakage: internal Aachu/Zuv names leak into
  public-facing slide copy when the creator did not ask for names.
- Copy-visual contradiction: the art is attractive but visible clothing,
  object, gaze, or action contradicts the exact slide text.
- Scene-entity drift: an extra person, duplicate couple, reflection,
  silhouette, or background actor creates a second unauthorized story.

## Eval Mapping

Mechanical failures should have deterministic fail-to-pass checkers and
pass-to-pass regression coverage.

Creative failures may need rubric review, but every rubric must name observable
evidence: scene behavior, concrete props, exact seed preservation, format
choice, relationship motion, visible absence of internal framework language,
shot grammar, object continuity, or copy-visual causality.

## Coverage Matrix

| Evidence cluster | Eval task |
| --- | --- |
| E01 instruction authority drift | `ASTO-001`, `ASTO-007` |
| E02 format snapback/native output confusion | `ASTO-002`, `ASTO-004` |
| E03 textless/deferred typography | `ASTO-003` |
| E04 false finality | `ASTO-004`, `ASTO-014` |
| E05 working memory misuse | `ASTO-005` |
| E06 skill/context routing drift | `ASTO-006`, `ASTO-007` |
| E07 score inflation after rejection | `ASTO-015` |
| E08 framework-first/generic output | `ASTO-011`, `ASTO-015` |
| E09 stale artifact carryover | `ASTO-013` |
| E10 identity eval stop gate | `ASTO-014` |
| E11 repeated visual grammar | `ASTO-012` |
| E12 home-cinematic visual evidence | `ASTO-016` |
| E13 public/private name boundary | `ASTO-017` |
| E14 copy-visual contradiction | `ASTO-018` |
| E15 unsafe closeout | `ASTO-008` |
| E16 duplicate background characters | `ASTO-019` |
| E17 hand ownership and object-contact AI slop | `ASTO-020` |
| E18 whole-person spatial topology failure | `ASTO-021` |
| E19 eval direction/no-op credit | finite suite review + fixture contracts |
| E20 stale or agent-inferred human approval | `ASTO-022` |
