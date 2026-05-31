# A Story of Two — Creative OS Master Plan
# The Final, Definitive Architecture + Implementation Reference

> **This is the canonical plan.** Prior plans (`2026-05-31-carousel-autopilot-sprint.md`,
> architecture discussions in chat) are superseded by this document.
> Do not create new structural plans without updating this file first.

---

## The One Sentence

**Every creative decision must produce a locked artifact, every creator correction must
propagate atomically to the skill layer, and every gate must be enforced by checking
the artifact — not by trusting the prompt.**

---

## What This System Is

A self-enforcing, self-correcting, ever-learning creative operating system for
**@a.storyof.two** — Anchal and Himanshu's Instagram. Its job is to turn one creative
idea (a jam, a real moment, a reference image) into a publishable illustrated carousel
package with native 4:5 and 9:16 outputs, without requiring the creator to re-explain
the same rule twice.

**The system fails when:**
- Gates are documentation-only (instructions instead of artifacts)
- Corrections land in `memory/working.md` but don't propagate to skill files
- The image generation path doesn't attach actual identity references
- "PASS" artifacts exist for packages that are actually blocked/partial

**The system succeeds when:**
- A blocked artifact stops the pipeline before anyone generates anything
- A correction in chat immediately updates the relevant semantic memory + skill file
- The doctor CLI returns honest state before any session trusts a package
- Every session closes with `wiki_health.py` + `autopublish.py` and the system is
  provably smarter than the session before it

---

## Part I: Architecture — The Three Zones

### Zone Model

```
┌─────────────────────────────────────────────────────────────────┐
│  ZONE 1: CREATIVE INTELLIGENCE                                   │
│  What story are we telling? What does it mean?                  │
│  Layer E → Golden Theme Tournament → Stage-Scene Gate           │
│  Hard output: concept.json with story_row + success_definition  │
└───────────────────────────┬─────────────────────────────────────┘
                            │ ARTIFACT GATE
                            │ concept.json must exist with:
                            │   - human_story_setup.emotional_obstacle (non-empty)
                            │   - success_definition (4 fields filled)
                            │   - story_selling_score >= 28
                            │   - hard_fails_present == false
                            │   - raw_scene_row locked (if creator-supplied moment)
┌───────────────────────────▼─────────────────────────────────────┐
│  ZONE 2: PRODUCTION INTELLIGENCE                                 │
│  How does the story look? How does each slide prove it?         │
│  Post-Copy Visual Room → Visual Debate → Per-Slide QA           │
│  Hard output: visual-plan-quality.json all slides GO            │
└───────────────────────────┬─────────────────────────────────────┘
                            │ ARTIFACT GATE
                            │ visual-plan-quality.json: every slide GO
                            │ identity-consistency-review.json: PASS
                            │ post-copy-visual-room.json: GO
                            │ visual-debate.json: GO
┌───────────────────────────▼─────────────────────────────────────┐
│  ZONE 3: GENERATION INTELLIGENCE                                 │
│  What can we actually generate? What is honest handoff state?   │
│  Capability check → Proof → Approval → Batch 4:5 → Batch 9:16  │
│  Hard output: publishable == true in final-images.json          │
│               OR HANDOFF_READY_FOR_CODEX_WITH_IDENTITY          │
└─────────────────────────────────────────────────────────────────┘
```

**The zones have one-way artifact gates.** You cannot enter Zone 2 without a valid
`concept.json`. You cannot enter Zone 3 without every slide in
`visual-plan-quality.json` returning GO and identity review passing.

---

### Zone 1 Detail: Creative Intelligence

#### Layer E — The Actual Thinking Council

Layer E is not a score or a card. It must produce `layer-e-story-selling.json` with:

```json
{
  "human_story_setup": {
    "raw_moment": "the exact creator-supplied event (if any)",
    "emotional_obstacle": "what is in the way — REQUIRED, non-empty",
    "proof_behavior": "what Aachu/Zuv actually do",
    "reversal": "what changes",
    "payoff": "the earned ending"
  },
  "success_definition": {
    "audience_success": "why strangers send/save/tag",
    "creative_success": "the staged story sequence with receipts",
    "brand_success": "ownable warm desi relationship IP",
    "production_success": "native outputs + QA"
  },
  "concept_process_card": "selected card name",
  "story_selling_score": 28,
  "hard_fails_present": false,
  "room_debate_record": []
}
```

If `emotional_obstacle` is empty: `BLOCKED: Layer E did not identify emotional obstacle`.
If `story_selling_score < 28`: `BLOCKED: story-selling score below threshold`.
If `hard_fails_present == true`: `BLOCKED: hard fail present`.

**E-Layer Hard Fails (automatically block):**
- No emotional obstacle
- Only a pretty moment (no tension)
- Generic couple dynamic
- Zuv has no active emotional role
- Ending is a quote, not an earned payoff
- Copyrighted source text copied into artifacts

#### Raw Scene Row Lock

When the creator supplies a real daily-life moment, the pipeline's **first act** is
`raw-scene-row.json`:

```json
{
  "source": "creator_supplied",
  "sequence": ["exact step 1", "exact step 2", ...],
  "actor": "who initiates",
  "watcher": "who observes/reacts",
  "location_progression": ["location per step"],
  "object": "the key prop",
  "visible_proof": "what is physically visible",
  "consequence": "what happens as result",
  "lock": true
}
```

`"lock": true` means: **no downstream agent can change the sequence, symmetrize it,
add a second object, abstract it into a thesis, or convert it to something safer.**
If any downstream artifact contradicts the raw scene row, it is a hard fail.

#### Golden Theme Tournament — Parallel Blind Scoring

Tournament produces `concept-selection.json`:

```
4-6 concept agents (parallel, each gets its own lens):
  Agent A: Ad-copy / shareability lens
  Agent B: Film / screenplay director lens
  Agent C: Retention / algorithm lens
  Agent D: Desi couple mirror lens
  [+ optional Agent E/F: reader mirror, obstacle-first lens]

Each agent writes 2-3 distinct concept routes independently.
Selector agent receives all routes without attribution (blind scoring).
Selector scores each 0-30 against the Golden Theme rubric.
Winner requires >= 28/30 or repair + rescore.
```

**Selector must penalize:** photo/aesthetic-first concepts, beauty/glow premises,
passive Zuv role, concepts that only work if names are mentioned, "he held everything
else" waiting-type frames, generic acceptance thesis.

#### Stage-Scene Gate

Must produce `stage-scene-gate.json` before any copy is written:

```json
{
  "slide_storyboard": [
    {
      "slide": 1,
      "action": "...",
      "reaction": "...",
      "eye_line": "...",
      "hands": "...",
      "body_distance": "...",
      "object_movement": "...",
      "silence_beat": "...",
      "consequence": "...",
      "text_needed_to_understand": false
    }
  ],
  "text_carries_scene": false,
  "visual_proves_truth": true,
  "verdict": "GO"
}
```

`"text_carries_scene": true` = hard block. A stranger who sees only the visuals with
text covered must still understand what happened between these two people.

---

### Zone 2 Detail: Production Intelligence

#### Post-Copy Visual Room — 6 Parallel Agents

Runs after creator confirms copy. Produces `post-copy-visual-room.json`.

| Agent | Job |
|-------|-----|
| Visual Format Anthropologist | What formats have proven this theme? |
| Scene Evidence Director | What real scenes/props prove each beat? |
| Romance Blocking Director | How do bodies/space/eye-line prove emotion? |
| Typography + Aspect Director | Where does text live in 4:5 vs 9:16? |
| Generation Prompt Director | Draft briefest precise prompt per slide |
| Harsh Visual Selector | Which system wins? What has rejected-option leakage? |

Harsh Selector verdict = GO/REPAIR/STOP. REPAIR blocks image generation.
STOP blocks the whole carousel until concept is revisited.

Rejected motifs go into `rejected_motifs` array and are banned from the storyboard
unless the story literally requires them AND the creator explicitly unlocks them.

#### Visual Plan Quality — Per-Slide GO/REPAIR/STOP

Every slide in `visual-plan-quality.json` must pass all of:

```
visual_evidence:       does the scene show what it claims?
golden_theme_proof:    does this slide advance the emotional machine?
identity_continuity:   Aachu/Zuv identifiable from style lock?
text_placement:        clean upper-middle space for handwritten copy?
copy_visual_alignment: image proves the line, not contradicts?
scene_logic:           socks before pants? props match the moment?
pose_anatomy:          both characters in natural, non-awkward positions?
paper_tone_check:      warm ivory/off-white, NOT yellow/parchment/sepia?
identity_match:        faces match selected Aachu/Zuv identity bundle?
doubt_flag:            any "maybe okay" feeling? → REPAIR immediately
```

**One REPAIR = full carousel blocked.** Not one slide regenerated. Full carousel repair.

---

### Zone 3 Detail: Generation Intelligence

#### Capability Check (run at session start)

Write `generation-capability.json`:

```json
{
  "can_attach_identity_refs": true,
  "can_attach_style_refs": true,
  "identity_refs_available": ["ID36", "ID37", "ID39", "ID44"],
  "style_refs_path": "config/references/style-lock/observational-intimacy-premium/"
}
```

If `can_attach_identity_refs: false` → pipeline routes to
`HANDOFF_READY_FOR_CODEX_WITH_IDENTITY`. This is not failure. The creative work is
complete; the final art is pending an environment with reference inputs.

#### Proof-First Generation Flow

```
1. Generate proof slide (always slide 4 — highest identity complexity)
2. QA proof: identity_match, paper_tone, pose_anatomy, text_readability
   Hard fails: yellow/parchment tone, wrong faces, unreadable text, awkward pose
   These are STOP → repair prompt → regenerate proof → repeat
3. Creator approves proof
4. Generate full 4:5 batch (native, not resized)
5. Generate separate 9:16 batch (native, not derived from 4:5)
6. visual-qa.md written
7. final-images.json updated: publishable: true
```

---

## Part II: Package State Contract

### The Seven States

Every carousel package has exactly one canonical state at any time:

| State | Meaning | Publishable |
|-------|---------|-------------|
| `draft` | Missing core C-layer artifacts | No |
| `blocked` | Workflow doctor has active blockers | No |
| `copy_locked` | Prompt pack exists, no generation yet | No |
| `handoff_ready` | All prompts ready, generation pending | No |
| `partial_final` | Some final images exist, both formats not complete | No |
| `proof_ready` | Proof slide generated, awaiting creator approval | No |
| `publishable` | Both native formats + visual QA + final audit PASS | Yes |

State is **derived** from artifacts, never manually set. Use
`pipeline/agentic/carousel_state.py` → `derive_carousel_state(package_dir)`.

### Blocker Rules (Doctor)

The workflow doctor (`pipeline/agentic/workflow_doctor.py`) flags these as blockers:

1. `raw_scene_rejected_but_generation_allowed` — raw scene row is rejected but
   visual-plan-quality still allows generation
2. `stale_blocker_with_generated_finals` — blocker file says no PNGs exist but
   final-images claims generated/publishable
3. `missing_prompt_pack` — package in generation-facing state but prompt-pack.json absent
4. `missing_visual_debate` — required C-layer artifact missing
5. `missing_post_copy_visual_room` — required C-layer artifact missing
6. `missing_final_audit` — package claims publishable without final-audit.json
7. `missing_reels_stories_final_folder` — Instagram final folder exists but no 9:16 folder
8. `publishable_without_visual_qa` — publishable flag without visual QA evidence

**Final audit cannot pass when `derive_carousel_state(package).name == "blocked"`.**

---

## Part III: The Learning System

### How Corrections Propagate (Atomic)

```
Creator correction in chat
          │
          ▼
   Identify type:
   Style / Story / Process / Identity / Gate
          │
          ▼
   ATOMIC PROPAGATION (all 4 or rollback):
   1. memory/semantic/<relevant-file>.md  — durable fact with confidence score
   2. config/skills/<relevant-skill>.md   — behavioral rule update
   3. config/<relevant-contract>.json     — hard constraint update (if visual/style)
   4. memory/episodic/<date>-learning.md  — permanent audit entry
   5. memory/working.md                   — pointer only ("see semantic/X.md")
```

**working.md is never the primary learning destination.** It holds pointers only.
If a correction exists only in working.md, it will be lost at next session reset.

### Session Close Protocol (Mandatory)

```bash
# 1. Capture session learnings
venv/bin/python scripts/wiki_health.py --write --fix-index \
  --session-note "what got better about the system today"

# 2. Autopublish verified state
venv/bin/python scripts/autopublish.py \
  --session-note "what got better about the system today"
```

Session note answers: **what got better about the system today?** Not "created three
carousels." That's output. "Added raw-scene-row lock to pipeline; yellow/parchment
now enforced as hard fail in style contract" — that's a learning.

### Pattern Extraction (Proactive — every 10 carousels)

```bash
venv/bin/python scripts/extract_carousel_patterns.py --last 10
```

Reads all `concept.json`, `story_selling_score`, creator approval vs NEEDS_FIXES
signals. Extracts: what emotional machines scored highest? What visual motifs keep
being rejected? Writes `wiki/insights/carousel-pattern-YYYY-MM-DD.md`.
Updates `memory/semantic/carousel-idea-preferences.md` with extracted patterns.

### Memory Architecture

```
memory/working.md          Current session only. Max 100 lines. Resets each full run.
memory/semantic/           Permanent. Durable facts with confidence scores.
  carousel-idea-preferences.md     — idea ledger (required reading before ideation)
  premium-illustration-style-lock.md  — visual law (confidence: 1.0)
  engineering-workflow-preferences.md — process rules
memory/episodic/           Permanent. Append-only. One file per session close.
memory/graph.json          Entity relationships.
```

### Confidence Lifecycle

```
new correction     → 0.4
confirmed ×2       → 0.7
confirmed ×3       → 0.9
contradicted       → -0.2
stale (30 days)    → -0.1/week
< 0.3              → wiki_health flags as STALE_CANDIDATE
```

---

## Part IV: Parallel Agent Architecture

### How to Run a Parallel Room

```python
# Orchestrator spawns parallel agents via Agent tool
# Each agent has its own context window, its own output

concept_a = Agent("Contradiction hook lens: ...", background=True)
concept_b = Agent("Film scene director lens: ...", background=True)
concept_c = Agent("Retention architecture lens: ...", background=True)
concept_d = Agent("Desi couple mirror lens: ...", background=True)

# Wait for all 4
# Feed outputs to selector — blind, no attribution labels
selector  = Agent("Score all 4 concepts. You do not know who wrote them. ...")
```

**The selector must not know which concept came from which lens.** Blind scoring
prevents anchoring. The tournament produces genuine debate, not self-selection.

### Skill Load Order (Every Session)

```
Layer 0 (always active — loaded from agentic_context_manifest.json):
  config/voice.md
  memory/semantic/premium-illustration-style-lock.md
  memory/semantic/carousel-idea-preferences.md
  wiki/themes/calm-enough-for-chaos.md

Layer 1 (on /story or creator jam):
  config/skills/romance-story-selling-engine.md
  config/skills/golden-viral-carousel-theme.md

Layer 2 (after Layer E passes):
  config/skills/carousel-story-director-persona.md
  config/skills/carousel-jam-autopilot.md

Layer 3 (after copy confirmed):
  config/skills/illustration-carousel-framework.md
  config/skills/continuous-carousel-agent-room.md

Layer 4 (before generation):
  config/references/a-story-illustration-master-prompt.md
  config/references/a-story-premium-illustration-style-lock.md
  config/references/style-lock/observational-intimacy-premium/README.md
```

---

## Part V: Sprint Implementation (P0 Today)

This is Codex's plan from `2026-05-31-carousel-autopilot-sprint.md`,
integrated with the architecture above. These five tasks are the 80/20.

### Sprint North Star

The failure mode is **orchestration honesty**. The code produces `GO`, `PASS`, or
`handoff_ready` while the carousel is stale, partial, rejected, or unpublishable.
The sprint fixes that without touching creative taste.

### P0 Tasks

| Task | Files | Purpose |
|------|-------|---------|
| A. Workflow Doctor | `pipeline/agentic/workflow_doctor.py`, `scripts/carousel_doctor.py` | Detect contradictions before anyone trusts a package |
| B. Canonical Prompt Source | `pipeline/stages/carousel_master_prompt.py`, `carousel_prompt_compiler.py` | One prompt source — the disk file, not a Python duplicate |
| C. Handoff Prompt Cleanup | `pipeline/stages/codex_builtin_image_generation.py` | `.md` and `.prompt.txt` cannot disagree |
| D. State Contract | `pipeline/agentic/carousel_state.py`, `carousel_quality.py` | One derived state replaces scattered statuses |
| E. Final QA Gate | extend `workflow_doctor.py` | Wrong aspect, missing 9:16, stale blockers fail loudly |

### P1 Tasks (after P0 lands)

| Task | Purpose |
|------|---------|
| F. CLI Wiring | Wire doctor/state into `create_illustration_carousel.py` and `agentic_os.py` |
| G. Package Triage | Honest board for recent packages via `carousel_doctor.py` |
| H. Runner v2 Spec | Design doc for turning `skill-systems.json` into executable state machine |

### Parallel Session Execution

Run Sessions A and B immediately in parallel. C and E wait for A. D waits for A+C.

**Session A — Workflow Doctor:**
```
You are in /Users/himanshusharma/astoryoftwo-analysis.
Use superpowers:using-git-worktrees and superpowers:executing-plans.
Work only on Task A (workflow doctor) and Task F (CLI doctor).
Create:
  pipeline/agentic/workflow_doctor.py
  scripts/carousel_doctor.py
  tests/test_carousel_workflow_doctor.py
  tests/test_carousel_doctor_cli.py
Do not touch prompt compiler, image generation, memory, wiki, or package artifacts.
Run: venv/bin/python -m pytest tests/test_carousel_workflow_doctor.py tests/test_carousel_doctor_cli.py -q
Return: files changed, test output, example issues for private-captions-fresh-a-story
and one-brain-cell-at-home.
```

**Session B — Canonical Prompt Source:**
```
You are in /Users/himanshusharma/astoryoftwo-analysis.
Use superpowers:using-git-worktrees and superpowers:executing-plans.
Work only on Tasks B and C (prompt source + handoff cleanup).
Modify:
  pipeline/stages/carousel_master_prompt.py
  pipeline/stages/carousel_prompt_compiler.py
  pipeline/stages/codex_builtin_image_generation.py
  tests/test_carousel_prompt_compiler.py
Read config/references/a-story-illustration-master-prompt.md first.
The canonical prompt must load from disk. The path scrubber must not corrupt
slash-separated prose like "muted denim/red scarf". Handoff markdown must not
duplicate the prompt body — it must point to the .prompt.txt file only.
Run: venv/bin/python -m pytest tests/test_carousel_prompt_compiler.py -q
Return: proof compiled prompt contains canonical yellow/parchment language,
proof slash-separated wardrobe is preserved, proof handoff has no second prompt body.
```

**Session C — State Contract (starts after A):**
```
You are in /Users/himanshusharma/astoryoftwo-analysis.
Use superpowers:using-git-worktrees and superpowers:executing-plans.
Work only on Task D (state contract) and Task E (final QA gate).
Create:
  pipeline/agentic/carousel_state.py
  tests/test_carousel_state_contract.py
Modify:
  pipeline/agentic/workflow_doctor.py (add missing_reels_stories and publishable_without_qa checks)
  pipeline/stages/carousel_quality.py (fail final audit when state is blocked)
Run: venv/bin/python -m pytest tests/test_carousel_state_contract.py tests/test_carousel_workflow_doctor.py -q
Return: state names for draft/blocked/handoff_ready/partial_final/publishable,
exact final-audit change, test output.
```

**Session D — CLI Wiring (starts after A+C):**
```
You are in /Users/himanshusharma/astoryoftwo-analysis.
Use superpowers:using-git-worktrees and superpowers:executing-plans.
Work only on Task F (CLI wiring into create_illustration_carousel.py and agentic_os.py).
Modify scripts/create_illustration_carousel.py to print derived package state after
package creation and after handoff prep. Wire agentic_os.py doctor subcommand if clean.
Do not implement image generation. Do not call external APIs.
Run: venv/bin/python -m pytest tests/ -q
Return: sample output for handoff_ready package, sample output for blocked package.
```

**Session E — Package Triage (starts after A):**
```
You are in /Users/himanshusharma/astoryoftwo-analysis.
Use superpowers:using-git-worktrees and superpowers:executing-plans.
Work only on Task G (triage report).
Run carousel_doctor.py on:
  output/carousels/2026-05-31/private-captions-fresh-a-story
  output/carousels/2026-05-30/one-brain-cell-at-home
  output/carousels/2026-05-30/i-have-no-car-i-ll-walk
  output/carousels/2026-05-30/the-hand-that-stays
  output/carousels/2026-05-30/before-us-timing-found-us-2
Create output/reports/2026-05-31-carousel-package-triage.md with package board,
exact blockers per package, next action per package.
Do not modify any carousel package files. Report only.
```

**Session F — Runner v2 Spec (spare capacity):**
```
You are in /Users/himanshusharma/astoryoftwo-analysis.
Use superpowers:using-git-worktrees and superpowers:writing-plans.
Work only on Task H (runner v2 spec).
Read config/skill-systems.json, scripts/agentic_os.py, pipeline/agentic/.
Write docs/superpowers/specs/carousel-agentic-runner-v2.md as a crisp state-machine
spec for turning skill-systems.json into an executable carousel workflow runner.
Do not implement runner code. Spec only.
Return: spec path, required states, gate invariants, smallest next implementation slice.
```

### Merge Order

1. Session A first — other tasks depend on doctor interface
2. Session B second — isolated, high value
3. Session C third — consumes doctor state
4. Session D fourth — wires user-facing CLI
5. Session E fifth — report only
6. Session F — design artifact for next sprint

### Definition of Done (Sprint)

```bash
# All tests pass
venv/bin/python -m pytest tests/test_carousel_workflow_doctor.py \
  tests/test_carousel_doctor_cli.py \
  tests/test_carousel_state_contract.py \
  tests/test_carousel_prompt_compiler.py -q

# Doctor correctly flags packages
venv/bin/python scripts/carousel_doctor.py \
  output/carousels/2026-05-31/private-captions-fresh-a-story
# → blocked, not publishable

venv/bin/python scripts/carousel_doctor.py \
  output/carousels/2026-05-30/one-brain-cell-at-home
# → blocked if raw_scene_rejected coexists with generation_allowed

# Canonical prompt integrity
# Compiled prompt contains yellow/parchment hard-fail language from disk
# Handoff markdown has no second prompt body

# Final audit blocks on doctor blockers
# Triage report separates publishable/handoff/partial/draft/blocked
```

---

## Part VI: The Creative OS Flywheel (Ongoing)

This is what "ever-evolving" means in practice:

```
Session runs
     │
     ▼
Creator corrections happen in chat
     │
     ▼
Corrections propagate ATOMICALLY to semantic + skill + contract
     │
     ▼
Session closes: wiki_health + autopublish
     │
     ▼
Every 10 carousels: extract_carousel_patterns.py
     │
     ▼
Patterns update semantic memory + wiki/insights
     │
     ▼
Next session loads improved context pack
     │
     └──► System is measurably smarter than the session before it
```

**The system gets smarter in two directions:**
1. **Correction learning** (reactive) — what you correct today never gets repeated
2. **Pattern extraction** (proactive) — what worked across 10 carousels becomes
   a permanent preference signal

**The wiki gets smarter too:**
- Smoke test carousels get `content_type: smoke_test` and are excluded from context
- Superseded carousels get confidence decayed to 0.2
- `successful-carousel-standard.md` updated after every `publishable` carousel
  based on what the visual QA actually confirmed

---

## Part VII: Anti-Drift Rules

These rules do not change. They are architectural invariants.

1. **No PASS/GO/publishable without artifact proof.** State is derived, not declared.
2. **No image generation without actual identity reference images attached.**
   Text-only identity descriptions are not enough. If refs can't be attached,
   the state is HANDOFF_READY, not final.
3. **No Layer E without human_story_setup.emotional_obstacle.**
   A story without tension is a moment. Moments don't have 28/30 scores.
4. **No carousel copy without Stage-Scene Gate passing.**
   If the visuals can't prove the truth without text, the story isn't staged.
5. **No raw creator moment abstracted, symmetrized, or made "safer."**
   The raw-scene-row.json is the locked source of truth for creator-supplied moments.
6. **No correction that only lands in working.md.**
   If it's not in semantic memory, it doesn't exist after the session resets.
7. **No session end without wiki_health + autopublish.**
   The repo is not the output. The system growing smarter is the output.

---

## Appendix: Quick Reference Commands

```bash
# Check package state before trusting it
venv/bin/python scripts/carousel_doctor.py output/carousels/<date>/<slug> --json

# Run all tests
venv/bin/python -m pytest tests/ -q

# Session close
venv/bin/python scripts/wiki_health.py --write --fix-index \
  --session-note "what changed"
venv/bin/python scripts/autopublish.py \
  --session-note "what changed"

# Extract patterns after 10+ carousels
venv/bin/python scripts/extract_carousel_patterns.py --last 10

# Agentic OS context render
venv/bin/python scripts/agentic_os.py context --render

# Agentic OS health
venv/bin/python scripts/agentic_os.py health
```

---

## Appendix: Current Package Status (2026-05-31)

| Package | State | Next Action |
|---------|-------|-------------|
| `private-captions-fresh-a-story` | blocked/draft | Run through full C-layer or promote to manual draft |
| `one-brain-cell-at-home` | blocked | Repair storyboard; raw scene rejected coexists with generation-allowed |
| `i-have-no-car-i-ll-walk` | handoff_ready | Generate native 4:5 + 9:16 with identity refs |
| `the-hand-that-stays` | publishable | Closeout-ready |
| `before-us-timing-found-us-2` | PASS_WITH_NOTES | Review final QA and close |

---

last_updated: 2026-05-31
status: canonical
supersedes:
  - docs/superpowers/plans/2026-05-31-carousel-autopilot-sprint.md
  - architecture discussion in chat 2026-05-31
