# Layer E Multi-Room Thinking Engine Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Turn Layer E into the executable thinking brain for @a.storyof.two: a multi-room story-selling engine that explores deeply, debates, repairs, and hands C/D/B workflows a source-backed story lens before writing, packaging, or generation.

**Architecture:** Build a focused `pipeline/layer_e/` package that loads Agentic OS context, successful-carousel memory, story-canon sources, process cards, golden-theme references, and creator preferences. The engine runs named expert rooms, records their debate, synthesizes a `selected_story_lens`, and only treats concept-process cards as traceable influences, not as the answer. C/D/B workflows consume `layer-e-story-selling.json` and block downstream work unless Layer E returns `GO` or an explicit repair path.

**Tech Stack:** Python 3, Pydantic v2, existing markdown/json source files, existing Agentic OS helpers, existing pytest suite, optional future subagent execution with deterministic local fallback.

---

## Current Repo State And Priority Order

The original repo recovery list remains the spine of this work.

Completed or protected before this plan:

- `codex/agentic-os-spine` is already merged into `main`.
- `main` is clean after stashing generated May 28 carousel outputs as `stash@{0}: protect-may-28-carousel-output-artifacts`.
- The carousel module split is already merged into `main`.
- The focused baseline command passed in the Layer E worktree:

```bash
/Users/himanshusharma/astoryoftwo-analysis/venv/bin/python -m pytest -q -k successful_carousel_standard
```

Remaining priority order:

1. Hard new-session takeover protocol.
2. Closeout enforcement with episodic handoff.
3. Layer E executable multi-room thinking engine.
4. C/D/B workflow integration and image-handoff blocking.
5. Backfill current May 28 carousel packages.
6. Creative pipeline recovery and final image QA.

Do not build another parallel creative path while `main`, Agentic OS, and Layer E disagree. Layer E must plug into Agentic OS and existing carousel rooms.

---

## Layer E Philosophy

Layer E is not a card picker.

Wrong model:

```text
story -> classify lane -> select Card 05 -> assign score
```

Correct model:

```text
story + memory + canon + success standard
-> expert rooms explore possible meanings
-> rooms debate universality, romance, retention, algorithm, safety, visual proof
-> top routes are repaired
-> final selector creates a story lens
-> process cards are recorded as influences
-> C/D/B workflows receive the emotional machine
```

The concept-process card is a cited influence. It is not the brain. If no existing card fits, Layer E may create a temporary synthesized lens as long as it records the source/canon/process influences and passes rubric gates.

---

## Required Layer E Rooms

Every non-trivial `run_layer_e()` call creates a room record even when the local runtime simulates the agents deterministically.

### Room 1: Context And Source Memory

Agents:

- Source Curator
- Agentic OS Recall Loader
- Successful Carousel Standard Reader
- Creator Preference Ledger Reader

Responsibilities:

- Load `wiki/insights/successful-carousel-standard.md`.
- Load `wiki/themes/calm-enough-for-chaos.md`.
- Load `output/reports/2026-05-17-he-didnt-marry-peace-viral-theme-analysis.md`.
- Load `memory/semantic/carousel-idea-preferences.md`.
- Load `config/references/story-selling-canon/`.
- Load latest `output/story-canon/<date>/pattern-map.json` and `concept-process-bank.json`.
- Enforce `source-policy.md`.

Output section: `source_memory_room`.

### Room 2: Story Meaning Room

Agents:

- Romance Novelist
- Film Scene Director
- Aachu/Zuv Dynamics Writer
- Emotional Obstacle Miner

Responsibilities:

- Generate 5-10 distinct story routes, not wording variants.
- Find relationship truth, obstacle, proof, reversal, and payoff.
- Make Aachu expressive without making her the problem.
- Make Zuv active through behavior, not passive perfection.
- Translate the moment into drawable scene grammar.

Output section: `story_meaning_room`.

### Room 3: Audience And Algorithm Room

Agents:

- Retention Analyst
- Algorithm / Share-Save Strategist
- Copy Chief
- Culture And Taste Reader

Responsibilities:

- Score public doorway strength.
- Score swipe ladder and middle-slide re-engagement.
- Name why a stranger would tag, send, save, comment, or subscribe.
- Check caption/search/distribution risk.
- Keep the channel warm, desi, specific, and non-generic.

Output section: `audience_algorithm_room`.

### Room 4: Contrarian Repair Room

Agents:

- Harsh Critic
- Genericness Detector
- Safety/Taste Guard
- Visual Generativity Skeptic

Responsibilities:

- Attack the raw winner before repair.
- Block aesthetic-first, object-first, private-context-first, copied, unsafe, generic, or ungenerative routes.
- Repair the top 2-3 candidates, not only the favorite.
- Record what was cut and why.

Output section: `contrarian_repair_room`.

### Room 5: Final Synthesis Room

Agents:

- Story Lens Selector
- Story-Selling Rubric Judge
- Golden Theme Bridge Judge for carousel work
- Downstream Contract Writer

Responsibilities:

- Choose one `selected_story_lens`.
- Write the `emotional_machine`.
- Record `proof_engine`, `reader_mirror`, `distribution_reason`, and `process_influences`.
- Score the chosen route with the 30-point Story-Selling rubric.
- Return `GO`, `REPAIR`, `REWORK`, or `STOP`.
- For carousel work, mark Golden Theme as required, not replaced.

Output section: `final_synthesis_room`.

---

## Artifact Contract

Every C/D/B workflow that decides what a love story means must produce:

```text
layer-e-story-selling.json
layer-e-story-selling.md
```

JSON shape:

```json
{
  "schema_version": "1.0",
  "status": "GO",
  "task_type": "carousel_idea",
  "adaptation_target": "C-layer",
  "source_memory_room": {},
  "story_meaning_room": {},
  "audience_algorithm_room": {},
  "contrarian_repair_room": {},
  "final_synthesis_room": {},
  "exploration_routes": [],
  "repaired_routes": [],
  "rejected_routes": [],
  "selected_story_lens": "",
  "emotional_machine": "",
  "proof_engine": "",
  "reader_mirror": "",
  "distribution_reason": "",
  "process_influences": [],
  "story_selling_score": {
    "reader_identity_mirror": 0,
    "romantic_conflict_stakes": 0,
    "specificity_of_proof": 0,
    "emotional_reversal": 0,
    "visual_scene_clarity": 0,
    "online_share_save_sell_potential": 0,
    "total": 0
  },
  "hard_fails": [],
  "required_repairs": [],
  "golden_theme_gate": "required_for_carousel",
  "downstream_contract": {
    "c_layer": {},
    "d_layer": {},
    "b_layer": {}
  }
}
```

Hard fails remain deterministic:

- no emotional obstacle;
- only a pretty moment;
- generic couple dynamic;
- Zuv has no active emotional role;
- ending is a quote, not an earned payoff;
- copyrighted source text copied into artifacts;
- no reader send/save/comment reason for online work;
- concept cannot become simple scenes for carousel work.

---

## File Structure

Create:

- `pipeline/layer_e/__init__.py`  
  Public exports for the Layer E engine.

- `pipeline/layer_e/contracts.py`  
  Pydantic contracts for requests, source memory, room outputs, routes, scoring, influences, and decisions.

- `pipeline/layer_e/source_memory.py`  
  Loads Agentic OS context, success standard, gold theme references, creator preference memory, source register, pattern map, concept-process bank, and reference markdown.

- `pipeline/layer_e/cards.py`  
  Parses concept-process cards as influence records, not as final decisions.

- `pipeline/layer_e/rooms.py`  
  Local deterministic room runner. Produces named expert outputs and debate records. Later this can dispatch real subagents without changing artifact shape.

- `pipeline/layer_e/scoring.py`  
  Implements rubric scoring and hard-fail detection against route fields.

- `pipeline/layer_e/engine.py`  
  Orchestrates memory load, rooms, cross-debate, repair, synthesis, scoring, and final decision.

- `pipeline/layer_e/artifacts.py`  
  Writes/loads `layer-e-story-selling.json` and `layer-e-story-selling.md` and validates gate status for downstream workflows.

- `scripts/start_agentic_session.py`  
  Hard new-session takeover command: loads context, skill system, recall, git state, wiki health, and writes session intent.

- `tests/test_layer_e_engine.py`  
  Unit tests for source memory, rooms, free exploration, Plate Stack story lens, hard fails, and influence traceability.

- `tests/test_layer_e_workflow_integration.py`  
  C-layer/image-handoff integration tests.

- `tests/test_session_takeover.py`  
  Tests the new session start protocol.

Modify:

- `scripts/agentic_os.py`  
  Add or expose a session-start command if the existing CLI is the better entry point than a standalone script.

- `scripts/autopublish.py`  
  Require episodic session handoff and preserve closeout gate behavior.

- `config/skill-systems.json`  
  Make Layer E room artifacts explicit under `carousel_jam`, `story_article`, and `prepost_reel`.

- `pipeline/stages/codex_native_carousel.py`  
  Run Layer E before slide/copy/prompt generation and consume `selected_story_lens`.

- `pipeline/stages/codex_builtin_image_generation.py`  
  Block prompt handoff unless Layer E artifact exists and is `GO`.

- `pipeline/stages/c1_illustration_carousel.py`  
  Pass Layer E room output into legacy Anthropic agents and require the artifact.

- `scripts/create_substack_article_package.py`  
  Run Layer E for article angle selection and fill brief/outline from the story lens.

- `pipeline/stages/b1_prepost.py`  
  Run Layer E before specialist Reel agents and include room outputs in the brief.

---

### Task 1: Replace Narrow Card-Lock Tests With Multi-Room Red Tests

**Files:**
- Modify: `tests/test_layer_e_engine.py`
- Modify: `tests/test_layer_e_workflow_integration.py`

- [ ] **Step 1: Update engine tests so cards are influences**

Expected test behaviors:

- source memory loads success standard, process cards, and story-canon outputs;
- Plate Stack returns at least four named rooms;
- Plate Stack creates at least five exploration routes;
- selected output is `selected_story_lens`, not `selected_card`;
- `process_influences` includes Card 05 but does not require it as the sole answer;
- emotional machine includes `dono rakh do`;
- weak pretty-moment input returns `REPAIR` or `STOP`.

- [ ] **Step 2: Run red tests**

```bash
/Users/himanshusharma/astoryoftwo-analysis/venv/bin/python -m pytest tests/test_layer_e_engine.py tests/test_layer_e_workflow_integration.py -q
```

Expected: `ModuleNotFoundError: No module named 'pipeline.layer_e'`.

---

### Task 2: Implement Contracts And Source Memory

**Files:**
- Create: `pipeline/layer_e/__init__.py`
- Create: `pipeline/layer_e/contracts.py`
- Create: `pipeline/layer_e/cards.py`
- Create: `pipeline/layer_e/source_memory.py`

- [ ] **Step 1: Add Pydantic models**

Include:

- `LayerERequest`
- `LayerESourceMemory`
- `ProcessInfluence`
- `ExpertAgentOutput`
- `LayerERoomOutput`
- `StoryRoute`
- `StorySellingScore`
- `LayerEDecision`

- [ ] **Step 2: Load source memory**

Load:

- `wiki/insights/successful-carousel-standard.md`
- `wiki/themes/calm-enough-for-chaos.md`
- `output/reports/2026-05-17-he-didnt-marry-peace-viral-theme-analysis.md`
- `memory/semantic/carousel-idea-preferences.md`
- `config/references/story-selling-canon/source-register.json`
- latest `output/story-canon/<date>/pattern-map.json`
- latest `output/story-canon/<date>/concept-process-bank.json`
- `config/references/story-selling-canon/*.md`

- [ ] **Step 3: Verify source-memory test passes**

```bash
/Users/himanshusharma/astoryoftwo-analysis/venv/bin/python -m pytest tests/test_layer_e_engine.py::test_source_memory_loads_story_canon_learning_outputs -q
```

Expected: `1 passed`.

---

### Task 3: Implement Local Multi-Room Engine

**Files:**
- Create: `pipeline/layer_e/rooms.py`
- Create: `pipeline/layer_e/scoring.py`
- Create: `pipeline/layer_e/engine.py`

- [ ] **Step 1: Generate exploration routes**

The local deterministic engine must produce 5-10 routes using story text, memory, source patterns, and process-card influences.

- [ ] **Step 2: Run expert room passes**

Each room writes:

- agents;
- inputs used;
- claims;
- objections;
- scores where relevant;
- selected or repaired output.

- [ ] **Step 3: Repair top routes**

Repair top 2-3 routes after Contrarian Repair Room review. Record raw and repaired scores.

- [ ] **Step 4: Synthesize final decision**

Return:

- `selected_story_lens`;
- `emotional_machine`;
- `proof_engine`;
- `reader_mirror`;
- `distribution_reason`;
- `process_influences`;
- `story_selling_score`;
- `hard_fails`;
- `status`.

- [ ] **Step 5: Run engine tests**

```bash
/Users/himanshusharma/astoryoftwo-analysis/venv/bin/python -m pytest tests/test_layer_e_engine.py -q
```

Expected: all Layer E engine tests pass.

---

### Task 4: Write Artifacts And Gate Loader

**Files:**
- Create: `pipeline/layer_e/artifacts.py`
- Modify: `tests/test_layer_e_engine.py`

- [ ] **Step 1: Add artifact writer**

Write `layer-e-story-selling.json` and `layer-e-story-selling.md`.

- [ ] **Step 2: Add gate loader**

`load_layer_e_decision(carousel_dir)` validates:

- file exists;
- schema loads;
- status is `GO`;
- no hard fails;
- Story-Selling total is 28+ when required.

- [ ] **Step 3: Run artifact tests**

```bash
/Users/himanshusharma/astoryoftwo-analysis/venv/bin/python -m pytest tests/test_layer_e_engine.py -q
```

---

### Task 5: Hard New-Session Takeover Protocol

**Files:**
- Create: `tests/test_session_takeover.py`
- Create or modify: `scripts/start_agentic_session.py`
- Modify if needed: `scripts/agentic_os.py`

- [ ] **Step 1: Add failing takeover test**

The command must:

- load Agentic OS context;
- load requested skill system;
- run recall;
- show dirty git state;
- show wiki health status;
- write a session intent file in `memory/episodic/`;
- block creative work when repo health is bad.

- [ ] **Step 2: Implement command**

Preferred invocation:

```bash
/Users/himanshusharma/astoryoftwo-analysis/venv/bin/python scripts/start_agentic_session.py \
  --skill-system carousel_jam \
  --intent "Layer E multi-room thinking engine"
```

- [ ] **Step 3: Verify**

```bash
/Users/himanshusharma/astoryoftwo-analysis/venv/bin/python -m pytest tests/test_session_takeover.py -q
```

---

### Task 6: Closeout Enforcement

**Files:**
- Modify: `scripts/autopublish.py`
- Add or modify tests around autopublish behavior.

- [ ] **Step 1: Add tests for episodic handoff requirement**

Autopublish must fail if a substantial session has no fresh readable handoff in `memory/episodic/`.

- [ ] **Step 2: Preserve existing gates**

Autopublish still blocks on:

- unsafe paths;
- live-looking secrets;
- full pytest failure;
- wiki health failure;
- git commit/push failure.

- [ ] **Step 3: Verify focused tests**

```bash
/Users/himanshusharma/astoryoftwo-analysis/venv/bin/python -m pytest tests -q -k "autopublish or session_takeover"
```

---

### Task 7: Integrate Layer E Into C-Layer And Image Handoff

**Files:**
- Modify: `pipeline/stages/codex_native_carousel.py`
- Modify: `pipeline/stages/codex_builtin_image_generation.py`
- Modify: `tests/test_layer_e_workflow_integration.py`

- [ ] **Step 1: Run Layer E before package construction**

`create_codex_native_carousel()` runs `run_layer_e()` with the story, constraints, title, and identity/reference image context.

- [ ] **Step 2: Consume story lens**

`concept.json`, `prompt-pack.json`, `review.json`, and `storyboard.md` reference:

- `layer-e-story-selling.json`;
- `selected_story_lens`;
- `emotional_machine`;
- `process_influences`;
- room verdicts.

- [ ] **Step 3: Block image handoff without Layer E**

`prepare_codex_builtin_image_generation()` returns `BLOCKED` when `layer-e-story-selling.json` is missing or not `GO`.

- [ ] **Step 4: Verify**

```bash
/Users/himanshusharma/astoryoftwo-analysis/venv/bin/python -m pytest tests/test_layer_e_workflow_integration.py tests/test_illustration_carousel.py -q
```

---

### Task 8: Integrate D-Layer And B-Layer

**Files:**
- Modify: `scripts/create_substack_article_package.py`
- Modify: `pipeline/stages/b1_prepost.py`
- Modify: `tests/test_substack_article_package.py`
- Modify: `tests/test_prepost_story_selling.py`

- [ ] **Step 1: Article package consumes Layer E**

Article brief and outline use the selected story lens, proof engine, and reader mirror.

- [ ] **Step 2: Prepost consumes Layer E**

Hook/edit/algo/caption/culture agents receive Layer E room outputs before scoring.

- [ ] **Step 3: Verify**

```bash
/Users/himanshusharma/astoryoftwo-analysis/venv/bin/python -m pytest tests/test_substack_article_package.py tests/test_prepost_story_selling.py -q
```

---

### Task 9: Backfill Current May 28 Packages

**Files:**
- Create: `scripts/backfill_layer_e_artifacts.py`
- Add: `tests/test_layer_e_backfill.py`

- [ ] **Step 1: Backfill script**

For an existing carousel package, infer story/title/images, run Layer E, and write artifacts without overwriting final creative files.

- [ ] **Step 2: Run for Plate Stack and Kitchen Forgiveness after tests pass**

Generated output paths are restored from the protected stash only when needed.

---

### Task 10: Full Verification And Safe Closeout

- [ ] **Step 1: Focused tests**

```bash
/Users/himanshusharma/astoryoftwo-analysis/venv/bin/python -m pytest \
  tests/test_layer_e_engine.py \
  tests/test_layer_e_workflow_integration.py \
  tests/test_session_takeover.py \
  tests/test_illustration_carousel.py \
  tests/test_substack_article_package.py \
  tests/test_prepost_story_selling.py \
  -q
```

- [ ] **Step 2: Full tests**

```bash
/Users/himanshusharma/astoryoftwo-analysis/venv/bin/python -m pytest -q
```

- [ ] **Step 3: Wiki health**

```bash
/Users/himanshusharma/astoryoftwo-analysis/venv/bin/python scripts/wiki_health.py --write --fix-index
```

- [ ] **Step 4: Autopublish**

Use explicit includes if the worktree is mixed. Do not include generated carousel image/video outputs.

```bash
/Users/himanshusharma/astoryoftwo-analysis/venv/bin/python scripts/autopublish.py \
  --session-note "Layer E multi-room thinking engine setup and integration"
```

---

## Self-Review

- The plan treats Layer E as the main story brain, not a selected-card wrapper.
- Existing cards remain useful as `process_influences`.
- Rooms match the creator’s desired skilled writers, content strategists, algorithm readers, critics, and selectors.
- The original repo recovery priorities remain in order.
- Downstream generation stays blocked until Layer E, golden theme, visual, identity, and QA gates agree.
