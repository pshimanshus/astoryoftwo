# THE PLAN
# A Story of Two — Creative OS: One Final Step-by-Step Plan
# Written: 2026-05-31. Do not rewrite. Amend only.

---

## Why This Plan Exists

Two previous plans existed. Codex wrote a technical sprint. Claude wrote an architecture
document. Both were correct. Neither was the right sequence. The user needs one ordered
list of steps that makes carousels actually ship — not more documentation about why
carousels aren't shipping.

The honest problem:
- 51 carousels created. Most stuck at NEEDS_FIXES. Very few publishable.
- The system can't complete final art because identity references can't be attached.
- Working memory (working.md) is stale noise from May 9 — the system is lying to itself.
- The same corrections repeat session after session because learning doesn't propagate.
- Every session produces structure updates instead of finished carousels.

---

## The Plan

---

### STEP 1 — Know What You Have (Today, 1 hour)

**What:** Run the workflow doctor to get an honest triage of every recent carousel.
Build it if it doesn't exist. Run it on the last 10 packages.

**Why:** You cannot fix what you don't accurately see. Right now some packages claim
PASS that are broken, and some are stuck but salvageable. The triage separates them.

**How:**
- Implement `pipeline/agentic/workflow_doctor.py` and `scripts/carousel_doctor.py`
  (Task A from the sprint plan — use Session A prompt)
- Run on all carousels from May 28 to today
- Produce `output/reports/2026-05-31-carousel-package-triage.md` with one honest
  board: publishable / proof-ready / handoff-ready / blocked / abandon

**Done when:** You have a list of ≤5 carousels worth finishing and know exactly
what is blocking each one.

---

### STEP 2 — Reset Working Memory (Today, 30 min)

**What:** Reset `memory/working.md` from its current 886-line stale state to a
clean current-session file.

**Why:** working.md says `session_date: 2026-05-09`. It's been appended continuously
for 3 weeks without a reset. Every session loads this noise as "current context."
The system is making decisions on 3-week-old state.

**How:**
- Extract every correction and preference that only lives in working.md → move to
  the relevant `memory/semantic/` file with a confidence score
- Keep carousel status entries → move to `memory/episodic/`
- Reset working.md to current state: today's date, active carousel slug, what's
  in progress now
- Run `venv/bin/python scripts/wiki_health.py --write --fix-index`

**Done when:** working.md is under 50 lines and accurate to today.

---

### STEP 3 — Fix the Identity Generation Path (Today or Tomorrow, 2–3 hours)

**What:** Make a permanent architectural decision about how Aachu/Zuv identity
references get attached to image generation. Enforce it.

**Why:** This is the #1 blocker. Every carousel ends at NEEDS_FIXES because final
art uses text-only identity descriptions and produces generic faces. This is not a
prompt problem. It is a tooling problem. Until it's solved, no carousel will be
truly done — it will only be a handoff document.

**How:**
- At session start, write `generation-capability.json` declaring whether the current
  environment can attach actual identity reference images
- If YES: proof-first flow (proof slide → creator approval → batch 4:5 → batch 9:16)
- If NO: package routes to `HANDOFF_READY_FOR_CODEX_WITH_IDENTITY` — honest state,
  not NEEDS_FIXES. The creative work is complete. The final art is pending.
- Wire this check into `scripts/create_illustration_carousel.py` so it prints the
  right next action at the end of every run
- Hard fail rule: if `can_attach_identity_refs: false`, the pipeline must not attempt
  final image generation and must not mark the package as anything other than handoff

**Done when:** A carousel package's final state is either `publishable` (real final
art generated with identity refs) or `HANDOFF_READY_FOR_CODEX_WITH_IDENTITY` (complete
creative package, pending generation environment). NEEDS_FIXES is no longer the
default end state.

---

### STEP 4 — Make the Pipeline State Honest (This Week, 3–4 hours)

**What:** Implement the canonical package state contract and wire it into the
final audit. One source of truth for whether a package is done.

**Why:** Right now packages can claim PASS or GO while being broken, partial, or
incomplete. The final audit doesn't check this. So sessions end trusting packages
that aren't trustworthy.

**How:**
- Implement `pipeline/agentic/carousel_state.py` with 7 states:
  draft / blocked / copy_locked / handoff_ready / partial_final / proof_ready / publishable
- Wire into `pipeline/stages/carousel_quality.py`: final audit cannot PASS when
  state is blocked
- Add two hard checks to the doctor:
  - `missing_reels_stories_final_folder` — if 4:5 final exists but 9:16 doesn't, blocker
  - `publishable_without_visual_qa` — publishable flag without visual QA, blocker
- Fix canonical prompt source: `carousel_master_prompt.py` must load from
  `config/references/a-story-illustration-master-prompt.md` on disk, not a
  hardcoded Python string. The yellow/parchment hard-fail language must come from
  the canonical file.
- Fix handoff markdown: `.md` handoff files must not embed a second prompt body.
  They point to `.prompt.txt` only.

**Done when:** `derive_carousel_state(package_dir).publishable` is the only signal
that matters. Triage report shows honest states. Tests pass.

---

### STEP 5 — Ship One Carousel End-to-End (This Week)

**What:** Take the carousel closest to done from the triage board and complete it
all the way to publishable + autopublish.

**Why:** The system has never shipped a carousel from idea to published package in
one clean session. Until it does that once, all the architecture is theoretical.
One proven end-to-end run validates everything and produces real content.

**How:**
- From the Step 1 triage board, pick the one carousel that is closest to publishable
  (based on doctor report — fewest blockers, identity refs available, copy confirmed)
- Resolve every doctor blocker for that carousel
- If generation environment supports identity refs: generate proof → approval → batch
- If not: complete the handoff package to publishable creative state, document clearly
  what generation step remains
- Run visual QA, final audit, session close

**Done when:** One carousel has `publishable: true` or `HANDOFF_READY_FOR_CODEX_WITH_IDENTITY`
with full prompt pack, visual QA, final audit, AND is committed via autopublish.

---

### STEP 6 — Fix the Learning Loop (This Week, alongside Step 5)

**What:** Make corrections propagate atomically. Stop losing learning.

**Why:** The same corrections have been given 2–4 times each: Stage-Scene Gate,
Layer E council, yellow paper tone, raw scene preservation. They land in working.md
and get lost. The system resets to its mistakes every session.

**How:**
- Rule: every creator correction in chat triggers two file writes before continuing:
  1. `memory/semantic/<relevant-file>.md` — durable fact with confidence score
  2. `config/skills/<relevant-skill>.md` OR `config/<relevant-contract>.json` — behavior
- Rule: working.md gets only a pointer ("see semantic/X.md") — never the correction itself
- Add `memory/semantic/raw-scene-row-rules.md` for the raw scene preservation rules
  (they currently only exist in working.md entries)
- Verify `memory/semantic/premium-illustration-style-lock.md` contains the yellow/
  parchment hard fail (it does — verify `config/carousel_style_contract.json` also has it)

**Done when:** You can delete working.md entirely and the system still knows every
rule, preference, and style constraint because they live in semantic memory and skill files.

---

### STEP 7 — Establish Session Rhythm (Permanent, starting now)

**What:** Every creative session follows the same opening and closing sequence.
No exceptions.

**Why:** The system is only as good as its state at session start and end. Right now
sessions start with stale context and end without committing learnings. The flywheel
never spins.

**Session Opening (5 min):**
```bash
venv/bin/python scripts/agentic_os.py context --render
venv/bin/python scripts/carousel_doctor.py output/carousels/<active-package> --json
```
Know what's real before doing anything.

**Session Work:**
- Every correction → semantic memory + skill file, immediately
- No carousel proceeds to generation without doctor returning no blockers
- No final art without identity refs attached (or honest HANDOFF state)

**Session Closing (5 min, mandatory):**
```bash
venv/bin/python scripts/wiki_health.py --write --fix-index \
  --session-note "what got better today"
venv/bin/python scripts/autopublish.py \
  --session-note "what got better today"
```

**Done when:** Two consecutive sessions open with zero stale corrections being
repeated and close with autopublish confirmed.

---

### STEP 8 — Build One Real Carousel Per Session (Ongoing)

**What:** After Steps 1–7 are solid, every session produces one new carousel that
reaches handoff-ready or publishable — not NEEDS_FIXES.

**Why:** The platform exists to create content. All the infrastructure is in service
of this. If it's not producing publishable carousels, the infrastructure failed.

**The session carousel flow (non-negotiable order):**

1. Load context pack (voice + style lock + idea preferences + golden theme)
2. Creator supplies moment, reference, or jam request
3. If real moment: lock raw-scene-row.json immediately
4. Layer E parallel room → layer-e-story-selling.json (requires emotional_obstacle,
   success_definition, score ≥28, no hard fails)
5. Golden theme tournament (4+ parallel agents, blind selector, ≥28/30)
6. Stage-scene gate → stage-scene-gate.json (text must not carry the scene)
7. Director persona loaded → hooks + slide copy written
8. Creator confirms copy → post-copy visual room (6 parallel agents)
9. Visual debate → visual-plan-quality.json (all slides GO)
10. Identity consistency review → PASS
11. Check generation-capability.json
12. If can attach identity refs: proof slide → creator approval → batch 4:5 → 9:16
13. If cannot: HANDOFF_READY package with complete prompt-pack
14. visual-qa.md → final-audit.json → carousel-idea-preferences.md updated
15. Session close: wiki_health + autopublish

**Done when:** A new carousel is in publishable or HANDOFF_READY state every session
that was meant to produce creative output.

---

### STEP 9 — Pattern Extraction (After Every 10 Carousels)

**What:** Run an automated pattern extraction to update what the system knows
about what works.

**Why:** The system must get smarter from its own output, not just from corrections.
After 10 carousels, patterns emerge: what emotional machines score highest, what
visual motifs keep getting rejected, what hooks generate sends/saves. These should
be permanent knowledge, not rediscovered each time.

**How:**
```bash
venv/bin/python scripts/extract_carousel_patterns.py --last 10
```
Writes `wiki/insights/carousel-pattern-YYYY-MM-DD.md` and updates
`memory/semantic/carousel-idea-preferences.md` with extracted signals.

Build this script when Step 8 has produced 10+ carousels.

**Done when:** `memory/semantic/carousel-idea-preferences.md` is being updated not
just from corrections but from pattern signals after every 10-carousel batch.

---

## Priority Order

```
TODAY:
  Step 1  — Triage (know what you have)
  Step 2  — Reset working.md (stop lying to yourself)
  Step 3  — Fix identity generation path (unblock final art)

THIS WEEK:
  Step 4  — Honest state contract (infrastructure)
  Step 5  — Ship one carousel end-to-end (prove it works)
  Step 6  — Fix learning loop (stop repeating corrections)

PERMANENT:
  Step 7  — Session rhythm (every session)
  Step 8  — One carousel per session (ongoing)
  Step 9  — Pattern extraction (every 10 carousels)
```

---

## The Rules That Do Not Change

1. No PASS/publishable without artifact proof. State is derived, not declared.
2. No final art without actual identity reference images attached. Text descriptions
   are not identity references. If refs can't be attached: HANDOFF state, not NEEDS_FIXES.
3. No Layer E without `emotional_obstacle` field filled. A story without tension is
   a moment. Moments don't produce viral carousels.
4. No carousel copy without Stage-Scene Gate. If the visuals can't prove the truth
   without text, the story isn't staged.
5. No correction that only lands in working.md. Semantic memory + skill file or it
   doesn't exist after the session resets.
6. No session end without wiki_health + autopublish.
7. No more plan rewrites. Amend this file. Don't replace it.

---

## Definition of Success

Six months from now, the system is working if:
- Every session produces one carousel that reaches publishable or honest HANDOFF state
- No correction is ever given more than once (it's in semantic memory after the first time)
- The wiki reflects what actually works, extracted from real carousel performance
- Anchal can look at the content calendar and see a backlog of ready carousels
- The system is visibly smarter than it was three months ago

---

last_updated: 2026-05-31
status: final
replaces: all prior plan documents in this repo
amend_by: adding numbered steps at the end or noting changes inline
do_not: rewrite from scratch, create a new plan document, or contradict these rules
