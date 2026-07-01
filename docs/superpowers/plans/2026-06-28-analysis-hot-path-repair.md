# Analysis Hot Path Repair Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Repair `astoryoftwo-analysis` into the production spine for A Story of Two: small brief first, human draft first, compact context as seasoning, final image/story handoff with the right information present.

**Architecture:** Keep the one-command production path in `astoryoftwo-analysis`. Replace heavy always-on gates with a small hot path: raw brief -> human baseline -> taste/context seasoning -> compact visual proof -> imagegen/package QA. Mine V2 only into compact reference assets; do not import its 33-state runtime.

**Tech Stack:** Markdown instruction surfaces, existing Python pipeline, pytest contract tests, Make targets, no new external runtime dependency.

---

## Scope

This plan deliberately fixes the hot path first. It does not clean every generated markdown file in `output/`, every episodic memory file, or every old carousel wiki page. Those are archives. The work starts with the documents and code that change future behavior.

## Rewrite Method

For instruction surfaces and creative docs, do not patch around the old process.
Treat each target document as if it is being written fresh for the new system,
then carry forward only the parts that still help the hot path.

The snippets in this plan are intent anchors, not a command to do tiny
paragraph swaps. For each doc task:

1. Read the current file.
2. Name what the file is responsible for in the new system.
3. Draft the clean target version in one pass.
4. Re-import only durable commands, paths, and safety constraints that still
   matter.
5. Remove visible framework language, duplicated rule authority, and artifact
   ceremony.
6. Apply the rewrite with `apply_patch`.
7. Run the focused tests that prove the file now teaches the new behavior.

For Python code and tests, use small TDD patches. Those files should change
surgically because behavior and regressions need tight diffs.

## File Map

Modify:
- `/Users/himanshusharma/astoryoftwo-analysis/AGENTS.md`
- `/Users/himanshusharma/astoryoftwo-analysis/.agents/skills/a-story-carousel-jam/SKILL.md`
- `/Users/himanshusharma/astoryoftwo-analysis/config/skills/carousel-jam-runtime-context.md`
- `/Users/himanshusharma/astoryoftwo-analysis/config/skills/carousel-jam-autopilot.md`
- `/Users/himanshusharma/astoryoftwo-analysis/config/skills/illustration-carousel-framework.md`
- `/Users/himanshusharma/astoryoftwo-analysis/config/skills/carousel-story-director-persona.md`
- `/Users/himanshusharma/astoryoftwo-analysis/config/skill-systems.json`
- `/Users/himanshusharma/astoryoftwo-analysis/config/agentic_context_manifest.json`
- `/Users/himanshusharma/astoryoftwo-analysis/memory/semantic/copywriter-intelligence.md`
- `/Users/himanshusharma/astoryoftwo-analysis/memory/semantic/visual-director-intelligence.md`
- `/Users/himanshusharma/astoryoftwo-analysis/pipeline/stages/carousel_prompt_compiler.py`
- `/Users/himanshusharma/astoryoftwo-analysis/pipeline/agentic/checks/image_size.py`
- `/Users/himanshusharma/astoryoftwo-analysis/tests/test_creator_workflow_contract.py`
- `/Users/himanshusharma/astoryoftwo-analysis/tests/test_carousel_prompt_compiler.py`
- `/Users/himanshusharma/astoryoftwo-analysis/tests/test_checks_image_size.py`

Create:
- `/Users/himanshusharma/astoryoftwo-analysis/config/references/winner-board.md`
- `/Users/himanshusharma/astoryoftwo-analysis/config/skills/taste-card.md`
- `/Users/himanshusharma/astoryoftwo-analysis/config/skills/imagegen-preflight.md`
- `/Users/himanshusharma/astoryoftwo-analysis/pipeline/stages/creative_context.py`
- `/Users/himanshusharma/astoryoftwo-analysis/tests/test_creative_context.py`

Do not modify in this pass:
- `/Users/himanshusharma/astoryoftwo-analysis/output/**`
- `/Users/himanshusharma/astoryoftwo-analysis/memory/episodic/**`
- `/Users/himanshusharma/astoryoftwo-analysis/wiki/carousels/**`
- `/Users/himanshusharma/A Story of Two V2/**`

---

### Task 1: Freeze The New Behavioral Contract

**Files:**
- Modify: `/Users/himanshusharma/astoryoftwo-analysis/tests/test_creator_workflow_contract.py`

- [ ] **Step 1: Replace old heavy-process expectations with human-first contract tests**

Replace the existing carousel-jam contract assertions that require `golden-theme variant tournament`, nested rooms, and mandatory visual debate before writing with tests for the new hot path.

Use this test structure:

```python
def test_creator_jam_contract_starts_with_human_baseline():
    agents = (WORKSPACE / "AGENTS.md").read_text(encoding="utf-8")
    runtime = (WORKSPACE / "config/skills/carousel-jam-runtime-context.md").read_text(
        encoding="utf-8"
    )
    jam = (WORKSPACE / "config/skills/carousel-jam-autopilot.md").read_text(
        encoding="utf-8"
    )

    for text in (agents, runtime, jam):
        assert "Small Brief First" in text
        assert "Human Draft First" in text
        assert "Context As Seasoning" in text
        assert "No Visible Framework Language" in text

    assert "Do not answer a small creative brief with a framework report" in agents
    assert "write the plain emotionally alive baseline before scoring" in runtime
    assert "copy lock comes after the human baseline" in jam


def test_creator_jam_uses_four_creator_locks_not_artifact_ceremony():
    jam = (WORKSPACE / "config/skills/carousel-jam-autopilot.md").read_text(
        encoding="utf-8"
    )
    skill = (WORKSPACE / ".agents/skills/a-story-carousel-jam/SKILL.md").read_text(
        encoding="utf-8"
    )
    systems = json.loads((WORKSPACE / "config/skill-systems.json").read_text(encoding="utf-8"))
    carousel_jam = systems["systems"]["carousel_jam"]

    for text in (jam, skill):
        assert "concept lock" in text
        assert "copy lock" in text
        assert "imagegen proof lock" in text
        assert "final package lock" in text

    assert "nested story/theme debate room" not in jam
    assert "at least two creative-editor voices and two writer voices" not in jam
    assert carousel_jam["gates"] == [
        "human_baseline_present",
        "creative_context_complete",
        "copy_lock",
        "imagegen_preflight_pass",
        "final_package_qa",
    ]


def test_runtime_context_points_to_compact_v2_assets():
    runtime = (WORKSPACE / "config/skills/carousel-jam-runtime-context.md").read_text(
        encoding="utf-8"
    )
    systems = json.loads((WORKSPACE / "config/skill-systems.json").read_text(encoding="utf-8"))
    carousel_jam = systems["systems"]["carousel_jam"]

    for path in (
        "config/references/winner-board.md",
        "config/skills/taste-card.md",
        "config/skills/imagegen-preflight.md",
    ):
        assert path in runtime
        assert path in carousel_jam["source_references"]


def test_visual_process_is_surgical_not_default_agent_room():
    framework = (WORKSPACE / "config/skills/illustration-carousel-framework.md").read_text(
        encoding="utf-8"
    )
    visual = (WORKSPACE / "memory/semantic/visual-director-intelligence.md").read_text(
        encoding="utf-8"
    )

    assert "Taste-first visual QA" in framework
    assert "Use visual agents only when the risk is concrete" in framework
    assert "The image must prove the beat before it passes dimensions" in visual
    assert "continuous agent room is mandatory" not in framework
```

- [ ] **Step 2: Run the focused contract tests and confirm they fail**

Run:

```bash
cd /Users/himanshusharma/astoryoftwo-analysis
venv/bin/python -m pytest tests/test_creator_workflow_contract.py -q
```

Expected: FAIL because the documents still encode the old process-heavy behavior.

- [ ] **Step 3: Commit after the tests are intentionally failing**

```bash
cd /Users/himanshusharma/astoryoftwo-analysis
git add tests/test_creator_workflow_contract.py
git commit -m "test: capture human-first carousel workflow contract"
```

---

### Task 2: Rewrite The Root Instruction Surfaces

**Files:**
- Modify: `/Users/himanshusharma/astoryoftwo-analysis/AGENTS.md`

- [ ] **Step 1: Replace the heavy creative gate section in `AGENTS.md`**

Replace `## Hard Creative Rules` through the end of `Creator Jam Response Contract` with this shorter contract:

```markdown
## Carousel Hot Path

For normal A Story carousel work, use the small production loop:

1. Small Brief First - preserve the creator's feeling, situation, or exact line.
2. Human Draft First - write the plain emotionally alive baseline before scoring.
3. Context As Seasoning - use winner data, rules, and references to improve the draft quietly.
4. CreativeContext - ensure the final handoff carries source, audience, voice, receipts, exact text, visual references, identity references, forbidden failures, and send/save reason.
5. Imagegen Proof - generate or inspect the riskiest proof before producing the full set.
6. Small QA - check taste first, then text, identity, dimensions, brandmark, exports.

Do not answer a small creative brief with a framework report. Do not expose internal terms such as "public contradiction", "sendable thesis", "Layer E", "Stage-Scene Gate", "28/30", or "emotional receipt" in creator-facing copy unless the creator asks for analysis.

The four creator-visible locks are:

- concept lock
- copy lock
- imagegen proof lock
- final package lock

Use agents surgically. Subagents are useful for bounded audits, output forensics, reference extraction, visual risk review, or final skepticism. They are not the default creative runtime.
```

- [ ] **Step 2: Update `AGENTS.md` source-of-truth table**

Add these rows under `Source Of Truth`:

```markdown
| winner-board | `config/references/winner-board.md` | proven posts, share/save/follow metrics, what traveled |
| taste-card | `config/skills/taste-card.md` | compact A Story voice, human-first copy taste, invisible framework rules |
| imagegen-preflight | `config/skills/imagegen-preflight.md` | exact text, native formats, identity refs, visual proof blockers |
```

- [ ] **Step 3: Remove outdated dimension language in `AGENTS.md`**

Replace the current `image-dimensions` table description:

```markdown
1080x1080 proof/concept/single-slide generation gate and rejection rule
```

with:

```markdown
native 1080x1350 post and 1080x1920 story/reel outputs, with square only for explicit concept experiments
```

- [ ] **Step 4: Keep `CLAUDE.md` retired**

Do not recreate `CLAUDE.md`. `AGENTS.md` is the required project instruction
surface; `config/instruction_surface_contract.json` should list `CLAUDE.md` as
a retired path so wiki health fails if it reappears.

- [ ] **Step 5: Run the contract tests**

Run:

```bash
cd /Users/himanshusharma/astoryoftwo-analysis
venv/bin/python -m pytest tests/test_creator_workflow_contract.py -q
```

Expected: still failing until the referenced compact assets and downstream docs are updated.

- [ ] **Step 6: Commit**

```bash
cd /Users/himanshusharma/astoryoftwo-analysis
git add AGENTS.md config/instruction_surface_contract.json
git commit -m "docs: make carousel workflow human-first"
```

---

### Task 3: Create The Three Compact Runtime Assets

**Files:**
- Create: `/Users/himanshusharma/astoryoftwo-analysis/config/references/winner-board.md`
- Create: `/Users/himanshusharma/astoryoftwo-analysis/config/skills/taste-card.md`
- Create: `/Users/himanshusharma/astoryoftwo-analysis/config/skills/imagegen-preflight.md`
- Modify: `/Users/himanshusharma/astoryoftwo-analysis/config/agentic_context_manifest.json`
- Modify: `/Users/himanshusharma/astoryoftwo-analysis/config/skill-systems.json`

- [ ] **Step 1: Create `winner-board.md`**

Use this initial content:

```markdown
# Winner Board

last_updated: 2026-06-28
status: compact reference

## Purpose

Use this to remember what has already worked before inventing new A Story ideas.
Do not copy the framework language into public copy.

## Ranking Rule

Rank A Story carousels by shares per 1k reach first, then saves per 1k reach,
then follows per 1k reach. Likes are secondary.

## Owned Winners

| Post | Why It Matters |
|---|---|
| DYJpjt9CQYY | strongest send-behavior winner; 40.15 shares/1k reach, 13.14 saves/1k |
| DY9SfANiXWc | strong send-behavior winner; 27.9 shares/1k reach, 10.0 saves/1k |
| DY4tGrQCXRA | large-reach send winner; 27.04 shares/1k reach, 10.0 saves/1k |
| DY_t4Dek0pq | strong save/follow winner; 24.87 shares/1k reach, 16.99 saves/1k |

## What Travels

- a public relationship mirror
- a tiny behavior that feels spied-on
- a real couple receipt instead of a romantic claim
- one active partner response
- an ending someone would send privately

## Use In Creative Work

Start from the feeling or line. Then quietly ask:

- Which winner does this resemble?
- What made that winner travel?
- What must stay specific?
- What should be removed because it sounds like a framework?
```

- [ ] **Step 2: Create `taste-card.md`**

Use this initial content:

```markdown
# Taste Card

last_updated: 2026-06-28
status: compact creative taste contract

## Human First Rule

Small Brief First. Human Draft First. Context As Seasoning. No Visible Framework Language.

When the creator gives a feeling, line, or situation, write the simplest alive
version before analysis. The first draft should sound like a sharp human wrote
it, not like a workflow completed it.

## A Story Voice

- short, spoken, emotionally direct
- slightly funny before tender when the moment allows
- Hinglish only when it is the natural voice of the moment
- no moral at the end
- no therapy-page polish
- no visible rubric words

## Copy Test

If the line sounds like "Sometimes love is..." or "A healthy relationship means...",
repair it.

If it sounds like someone could mutter it, text it, confess it, or send it to
their person, keep going.

## Invisible Intelligence

Use winner metrics, story logic, visual logic, and source references to improve
the draft. Do not let those terms appear in the copy.
```

- [ ] **Step 3: Create `imagegen-preflight.md`**

Use this initial content:

```markdown
# Imagegen Preflight

last_updated: 2026-06-28
status: compact imagegen handoff contract

## Pass Order

Taste first, then mechanics.

1. Does the image prove the emotional beat?
2. Does it preserve the exact on-image text?
3. Does it use actual Aachu/Zuv identity references when faces are visible?
4. Does it avoid copying a style reference as pose, camera, or theme?
5. Is the post output native 1080x1350?
6. Is the story/reel output native 1080x1920?
7. Is the tiny `@a.storyof.two` brandmark present?

## Blockers

- beautiful but emotionally wrong
- exact text missing, changed, or unreadable
- generic couple faces when identity matters
- style reference copied as scene logic
- wrong native canvas
- quote-card or poster instead of lived Aachu/Zuv scene

## Proof Rule

For high-risk runs, prove the riskiest slide first. The riskiest slide is the
one most likely to fail identity, text, emotional logic, or canvas format.
```

- [ ] **Step 4: Update `config/skill-systems.json`**

Set `systems.carousel_jam.components` to:

```json
[
  "config/skills/carousel-jam-runtime-context.md",
  "config/skills/taste-card.md",
  "config/skills/imagegen-preflight.md",
  "config/skills/carousel-jam-autopilot.md",
  "config/skills/illustration-carousel-framework.md"
]
```

Set `systems.carousel_jam.source_references` to:

```json
[
  "config/references/winner-board.md",
  "wiki/insights/successful-carousel-standard.md",
  "memory/semantic/carousel-idea-preferences.md",
  "config/skills/romance-story-selling-engine.md",
  "config/skills/golden-viral-carousel-theme.md"
]
```

Set `systems.carousel_jam.gates` to:

```json
[
  "human_baseline_present",
  "creative_context_complete",
  "copy_lock",
  "imagegen_preflight_pass",
  "final_package_qa"
]
```

Set `systems.carousel_jam.artifacts` to:

```json
[
  "creative-context.json",
  "human-baseline.md",
  "slides.json",
  "codex-image-prompts/",
  "visual-qa.md",
  "final-audit.json"
]
```

- [ ] **Step 5: Update `config/agentic_context_manifest.json`**

Add optional compact sections after `carousel_runtime_context`:

```json
{
  "id": "winner_board",
  "path": "config/references/winner-board.md",
  "kind": "compact_reference",
  "required": false
},
{
  "id": "taste_card",
  "path": "config/skills/taste-card.md",
  "kind": "workflow_runtime_context",
  "required": true
},
{
  "id": "imagegen_preflight",
  "path": "config/skills/imagegen-preflight.md",
  "kind": "workflow_runtime_context",
  "required": true
}
```

- [ ] **Step 6: Run JSON and contract tests**

Run:

```bash
cd /Users/himanshusharma/astoryoftwo-analysis
venv/bin/python -m json.tool config/skill-systems.json >/tmp/skill-systems.json.check
venv/bin/python -m json.tool config/agentic_context_manifest.json >/tmp/agentic-context.json.check
venv/bin/python -m pytest tests/test_creator_workflow_contract.py -q
```

Expected: JSON checks pass. Contract tests still fail until runtime/autopilot/framework text is updated.

- [ ] **Step 7: Commit**

```bash
cd /Users/himanshusharma/astoryoftwo-analysis
git add config/references/winner-board.md config/skills/taste-card.md config/skills/imagegen-preflight.md config/skill-systems.json config/agentic_context_manifest.json
git commit -m "docs: add compact carousel runtime assets"
```

---

### Task 4: Repair The Runtime And Copy Brain

**Files:**
- Modify: `/Users/himanshusharma/astoryoftwo-analysis/config/skills/carousel-jam-runtime-context.md`
- Modify: `/Users/himanshusharma/astoryoftwo-analysis/memory/semantic/copywriter-intelligence.md`

- [ ] **Step 1: Add the human-first block near the top of runtime context**

Insert after `## Purpose`:

```markdown
## Human-First Opening

Small Brief First.
Human Draft First.
Context As Seasoning.
No Visible Framework Language.

For creative work, do not begin with a rubric, score, debate, table, or
framework explanation. Preserve the creator's raw feeling, situation, or exact
line and write the plain emotionally alive baseline before scoring.

After the baseline exists, quietly use the source files and compact assets to
repair weak specificity, weak sendability, passive partner response, visual
drift, or generic romance language.
```

- [ ] **Step 2: Replace the current low-scoring route language**

Replace the paragraph beginning `Creator-facing carousel suggestions must be 28/30` with:

```markdown
Creator-facing output should show the best alive direction, not a pile of
internal scoring. Use scoring privately. If no route feels alive, say the
direction needs repair and return with one sharper rewrite or one concrete
question. Do not show weak routes as options.
```

- [ ] **Step 3: Replace "When the creator starts a jam" runtime language**

Replace:

```markdown
When the creator starts a jam, do not answer with 5-line slide copy, a hook
bank, or slide architecture. First lock the concept: story/theme diagnosis,
multi-voice debate summary, Stage-Scene proof, scores, rejected lanes, selector
verdict, and GO / REPAIR / STOP.
```

with:

```markdown
When the creator starts with a small creative brief, first return the human
baseline: the clean line, the emotional read, or one simple post direction.
Only move into concept lock, visual planning, or scoring after the baseline
feels alive.
```

- [ ] **Step 4: Add a top-level correction to copywriter intelligence**

Insert after the opening metadata in `memory/semantic/copywriter-intelligence.md`:

```markdown
## Active Correction - 2026-06-28

The creator gets better copy when the first answer is not overfed with context.
Do not turn every brief into a visible framework. Write the human baseline first.

The proven formula is a private diagnostic, not a public template. Use it to
repair the draft after the first alive version exists.
```

- [ ] **Step 5: Soften mandatory formula wording**

Replace:

```markdown
**This machine is mandatory.**
```

with:

```markdown
Use this machine as a private diagnostic. If the public copy starts sounding
like the machine, simplify it back into human speech.
```

- [ ] **Step 6: Run tests**

Run:

```bash
cd /Users/himanshusharma/astoryoftwo-analysis
venv/bin/python -m pytest tests/test_creator_workflow_contract.py -q
```

Expected: runtime/copy tests pass where these files are involved; remaining failures point to autopilot/framework/skill docs.

- [ ] **Step 7: Commit**

```bash
cd /Users/himanshusharma/astoryoftwo-analysis
git add config/skills/carousel-jam-runtime-context.md memory/semantic/copywriter-intelligence.md
git commit -m "docs: make carousel runtime human-first"
```

---

### Task 5: Slim The Carousel Skill And Autopilot

**Files:**
- Modify: `/Users/himanshusharma/astoryoftwo-analysis/.agents/skills/a-story-carousel-jam/SKILL.md`
- Modify: `/Users/himanshusharma/astoryoftwo-analysis/config/skills/carousel-jam-autopilot.md`
- Modify: `/Users/himanshusharma/astoryoftwo-analysis/config/skills/illustration-carousel-framework.md`

- [ ] **Step 1: Replace the skill operating contract**

In `.agents/skills/a-story-carousel-jam/SKILL.md`, replace `## Operating Contract` with:

```markdown
## Operating Contract

- Small Brief First: preserve the creator's exact feeling, situation, line, or image premise.
- Human Draft First: write the plain emotionally alive baseline before private scoring.
- Context As Seasoning: use winner-board, taste-card, runtime context, and imagegen-preflight quietly.
- No Visible Framework Language: do not expose internal rubric terms in public copy.
- Four creator-visible locks: concept lock, copy lock, imagegen proof lock, final package lock.
- Use subagents only for bounded reviews, output forensics, visual risk, reference extraction, or final skepticism.
- Do not call the carousel final unless native 1080x1350 post finals, native 1080x1920 story/reel finals, visual QA, and final audit exist.
```

- [ ] **Step 2: Replace the autopilot "Required Parallel Agents" section**

In `config/skills/carousel-jam-autopilot.md`, replace `## Required Parallel Agents` through its artifact list with:

```markdown
## Surgical Agents

Do not ask whether to run agents for every small creative move. Use agents only
when the risk is concrete:

- Story/source strategist: when the idea depends on a winner, source reference, or trend pattern.
- Visual director: when image logic, identity, canvas, or style can fail.
- Final skeptic: before expensive image generation or final packaging.

For normal production, keep the creator-facing path simple:

1. concept lock
2. copy lock
3. imagegen proof lock
4. final package lock

copy lock comes after the human baseline, not after a debate transcript.
```

- [ ] **Step 3: Replace the autopilot sequence**

In `config/skills/carousel-jam-autopilot.md`, replace `## Autopilot Sequence` with:

```markdown
## Autopilot Sequence

1. Preserve the raw brief.
2. Write `human-baseline.md` or a human baseline section before scoring.
3. Build `creative-context.json` with source, audience, voice, receipts, exact text, visual references, identity references, forbidden failures, and send/save reason.
4. Use `config/references/winner-board.md`, `config/skills/taste-card.md`, and `config/skills/imagegen-preflight.md` as compact seasoning.
5. Ask for concept lock only after the idea feels alive.
6. Write final slide copy after concept lock.
7. Ask for copy lock.
8. Build image prompts with exact text and selected identity/style references.
9. Run imagegen proof lock on the riskiest slide when identity, text, style, or emotional logic can fail.
10. Generate native 1080x1350 post outputs and native 1080x1920 story/reel outputs.
11. Run taste-first QA, then text, identity, dimensions, brandmark, and export checks.
12. Ask for final package lock.
```

- [ ] **Step 4: Slim the illustration framework artifact contract**

In `config/skills/illustration-carousel-framework.md`, replace `## Required Artifact Contract` with:

```markdown
## Required Artifact Contract

The default hot path creates only the artifacts needed to produce and verify
final images:

- `creative-context.json`
- `human-baseline.md`
- `slides.json`
- `storyboard.md`
- `codex-image-prompts/instagram-post/`
- `codex-image-prompts/reels-stories/`
- `final/slide-XX.png`
- `final-reels-stories/slide-XX.png`
- `final-images.json`
- `visual-qa.md`
- `final-audit.json`

Create debate, repair, agent-room, or extended ledger artifacts only when a
specific failure or user request requires them.
```

- [ ] **Step 5: Add taste-first visual QA language**

In `config/skills/illustration-carousel-framework.md`, add under `## Visual Direction`:

```markdown
## Taste-first visual QA

Use visual agents only when the risk is concrete. The first visual question is:
does the image prove the beat? A beautiful image fails if it is emotionally
wrong, copies a reference pose, loses Aachu/Zuv identity, or turns the slide
into a quote card. After that, check exact text, native dimensions, brandmark,
and exports.
```

- [ ] **Step 6: Run contract tests**

Run:

```bash
cd /Users/himanshusharma/astoryoftwo-analysis
venv/bin/python -m pytest tests/test_creator_workflow_contract.py -q
```

Expected: PASS for the workflow contract tests.

- [ ] **Step 7: Commit**

```bash
cd /Users/himanshusharma/astoryoftwo-analysis
git add .agents/skills/a-story-carousel-jam/SKILL.md config/skills/carousel-jam-autopilot.md config/skills/illustration-carousel-framework.md
git commit -m "docs: slim carousel autopilot hot path"
```

---

### Task 6: Add `CreativeContext`

**Files:**
- Create: `/Users/himanshusharma/astoryoftwo-analysis/pipeline/stages/creative_context.py`
- Create: `/Users/himanshusharma/astoryoftwo-analysis/tests/test_creative_context.py`

- [ ] **Step 1: Write tests first**

Create `tests/test_creative_context.py`:

```python
from __future__ import annotations

import pytest

from pipeline.stages.creative_context import CreativeContext


def _valid_context() -> CreativeContext:
    return CreativeContext(
        brief="She says main kar lungi but waits near the door.",
        human_baseline="main kar lungi. bas gate ke paas ruk jaana.",
        source_winner="DYJpjt9CQYY",
        audience="people who send tiny relationship recognitions to their partner",
        voice="short, spoken, emotionally direct, no visible framework language",
        receipts=["gate ke paas rukna", "main kar lungi", "he waits without making it a lesson"],
        exact_text=["main kar lungi.", "bas gate ke paas ruk jaana."],
        visual_references=["config/references/style-lock/observational-intimacy-premium"],
        identity_references=["config/references/identity/aachu", "config/references/identity/zuv"],
        format_targets=["instagram_post", "reels_stories"],
        forbidden_failures=["therapy-page copy", "generic couple faces", "quote-card scene"],
        send_save_reason="It feels like a private joke a partner would receive softly.",
    )


def test_creative_context_accepts_complete_context():
    context = _valid_context()
    assert context.is_complete()
    assert context.missing_fields() == []


def test_creative_context_reports_missing_generation_fields():
    context = _valid_context()
    context.identity_references = []
    context.send_save_reason = ""

    assert not context.is_complete()
    assert context.missing_fields() == ["identity_references", "send_save_reason"]


def test_creative_context_serializes_to_generation_packet():
    packet = _valid_context().to_generation_packet()

    assert packet["human_baseline"].startswith("main kar lungi")
    assert "DYJpjt9CQYY" in packet["source_winner"]
    assert packet["format_targets"] == ["instagram_post", "reels_stories"]
    assert "No visible framework language" in packet["rules"]


def test_creative_context_rejects_empty_brief():
    with pytest.raises(ValueError, match="brief"):
        CreativeContext(
            brief="",
            human_baseline="alive line",
            source_winner=None,
            audience="audience",
            voice="voice",
            receipts=["receipt"],
            exact_text=["text"],
            visual_references=["style"],
            identity_references=["identity"],
            format_targets=["instagram_post"],
            forbidden_failures=["failure"],
            send_save_reason="reason",
        )
```

- [ ] **Step 2: Run the tests and confirm they fail**

Run:

```bash
cd /Users/himanshusharma/astoryoftwo-analysis
venv/bin/python -m pytest tests/test_creative_context.py -q
```

Expected: FAIL with `ModuleNotFoundError` for `pipeline.stages.creative_context`.

- [ ] **Step 3: Implement `creative_context.py`**

Create `pipeline/stages/creative_context.py`:

```python
from __future__ import annotations

from dataclasses import asdict, dataclass


@dataclass
class CreativeContext:
    brief: str
    human_baseline: str
    source_winner: str | None
    audience: str
    voice: str
    receipts: list[str]
    exact_text: list[str]
    visual_references: list[str]
    identity_references: list[str]
    format_targets: list[str]
    forbidden_failures: list[str]
    send_save_reason: str

    def __post_init__(self) -> None:
        if not self.brief.strip():
            raise ValueError("brief is required")

    def missing_fields(self) -> list[str]:
        missing: list[str] = []
        for field_name, value in asdict(self).items():
            if field_name == "source_winner":
                continue
            if isinstance(value, str) and not value.strip():
                missing.append(field_name)
            elif isinstance(value, list) and not value:
                missing.append(field_name)
        return missing

    def is_complete(self) -> bool:
        return not self.missing_fields()

    def to_generation_packet(self) -> dict[str, object]:
        packet = asdict(self)
        packet["rules"] = [
            "Small Brief First",
            "Human Draft First",
            "Context As Seasoning",
            "No visible framework language",
            "Taste-first visual QA before mechanical checks",
        ]
        return packet
```

- [ ] **Step 4: Run tests**

Run:

```bash
cd /Users/himanshusharma/astoryoftwo-analysis
venv/bin/python -m pytest tests/test_creative_context.py -q
```

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
cd /Users/himanshusharma/astoryoftwo-analysis
git add pipeline/stages/creative_context.py tests/test_creative_context.py
git commit -m "feat: add creative context packet"
```

---

### Task 7: Fix Prompt Budget Without Losing The Human Baseline

**Files:**
- Modify: `/Users/himanshusharma/astoryoftwo-analysis/pipeline/stages/carousel_prompt_compiler.py`
- Modify: `/Users/himanshusharma/astoryoftwo-analysis/tests/test_carousel_prompt_compiler.py`

- [ ] **Step 1: Add a budget compaction test**

Add this test to `tests/test_carousel_prompt_compiler.py`:

```python
def test_compile_image_prompt_compacts_verbose_scene_before_failing_budget():
    prompt = compile_image_prompt(
        slide_number=1,
        slide_count=5,
        slide_copy="main kar lungi.",
        visual=(
            "Scene: Aachu stands near the door while Zuv waits quietly. "
            + ("discardable production commentary " * 900)
        ),
        format_key="instagram_post",
        style="premium romantic watercolor-and-ink illustration " * 200,
        negative="No photorealism. " * 200,
    )

    assert len(prompt) <= MAX_PROMPT_CHARS
    assert "main kar lungi." in prompt
    assert "Aachu stands near the door" in prompt
    assert "exact 4:5 canvas" in prompt
```

- [ ] **Step 2: Run and confirm failure**

Run:

```bash
cd /Users/himanshusharma/astoryoftwo-analysis
venv/bin/python -m pytest tests/test_carousel_prompt_compiler.py::test_compile_image_prompt_compacts_verbose_scene_before_failing_budget -q
```

Expected: FAIL because the compiler raises after building an over-budget prompt.

- [ ] **Step 3: Add compacting helpers**

In `pipeline/stages/carousel_prompt_compiler.py`, add:

```python
def limit_words(value: str, max_words: int) -> str:
    words = clean_text(value).split()
    if len(words) <= max_words:
        return " ".join(words)
    return " ".join(words[:max_words]).rstrip(" .,;:") + "."


def compact_prompt_inputs(
    *,
    scene: str,
    style: str,
    negative: str,
    pose: str,
    wardrobe: str,
    props: str,
    background: str,
    emotion: str,
) -> dict[str, str]:
    return {
        "scene": limit_words(scene, 90),
        "style": limit_words(style, 80),
        "negative": limit_words(negative, 50),
        "pose": limit_words(pose, 45),
        "wardrobe": limit_words(wardrobe, 45),
        "props": limit_words(props, 45),
        "background": limit_words(background, 45),
        "emotion": limit_words(emotion, 35),
    }
```

- [ ] **Step 4: Use compacting before raising**

Refactor `compile_image_prompt` so it first builds from full cleaned inputs. If the prompt is too long, rebuild once using `compact_prompt_inputs`. Only raise if the compact rebuild is still over `MAX_PROMPT_CHARS`.

The key implementation shape:

```python
    values = {
        "scene": clean_text(visual),
        "pose": clean_text(pose or default_pose),
        "wardrobe": clean_text(wardrobe or default_wardrobe),
        "props": clean_text(props or default_props),
        "background": clean_text(background or default_background),
        "emotion": clean_text(emotion or default_emotion),
        "style": clean_text(style),
        "negative": clean_text(negative),
    }
    prompt = build_prompt_from_values(values)
    if len(prompt) > MAX_PROMPT_CHARS:
        prompt = build_prompt_from_values(compact_prompt_inputs(**values))
    if len(prompt) > MAX_PROMPT_CHARS:
        raise ValueError(f"Compiled image prompt is too long: {len(prompt)} characters.")
```

Do this with a private nested helper or a small module-level helper. Keep exact slide copy untouched.

- [ ] **Step 5: Run prompt compiler tests**

Run:

```bash
cd /Users/himanshusharma/astoryoftwo-analysis
venv/bin/python -m pytest tests/test_carousel_prompt_compiler.py -q
```

Expected: PASS.

- [ ] **Step 6: Commit**

```bash
cd /Users/himanshusharma/astoryoftwo-analysis
git add pipeline/stages/carousel_prompt_compiler.py tests/test_carousel_prompt_compiler.py
git commit -m "fix: compact verbose image prompts before budget failure"
```

---

### Task 8: Align Native Image Dimension Rules

**Files:**
- Modify: `/Users/himanshusharma/astoryoftwo-analysis/pipeline/agentic/checks/image_size.py`
- Modify: `/Users/himanshusharma/astoryoftwo-analysis/tests/test_checks_image_size.py`
- Modify: `/Users/himanshusharma/astoryoftwo-analysis/config/rules/image-dimensions.md`
- Modify: `/Users/himanshusharma/astoryoftwo-analysis/config/skills/illustration-carousel-framework.md`

- [ ] **Step 1: Add exact native format tests**

Add:

```python
def test_passes_for_exact_instagram_post_1080x1350(tmp_path: Path) -> None:
    path = _save_blank(tmp_path / "post.png", (1080, 1350))
    gate = check_image_size(path, "instagram_post")
    assert gate.status == "PASS"
    assert "exact" in gate.reason.lower()


def test_fails_instagram_post_when_upscaled_ratio_only(tmp_path: Path) -> None:
    path = _save_blank(tmp_path / "post-big.png", (1440, 1800))
    gate = check_image_size(path, "instagram_post")
    assert gate.status == "FAIL"
    assert "1080x1350" in gate.reason


def test_passes_for_exact_reels_stories_1080x1920(tmp_path: Path) -> None:
    path = _save_blank(tmp_path / "story.png", (1080, 1920))
    gate = check_image_size(path, "reels_stories")
    assert gate.status == "PASS"
    assert "exact" in gate.reason.lower()
```

- [ ] **Step 2: Run and confirm failure**

Run:

```bash
cd /Users/himanshusharma/astoryoftwo-analysis
venv/bin/python -m pytest tests/test_checks_image_size.py -q
```

Expected: FAIL because `instagram_post` and `reels_stories` are unknown.

- [ ] **Step 3: Update image size targets**

In `pipeline/agentic/checks/image_size.py`, update constants:

```python
EXACT_DIMENSIONS = {
    "4:5": (1080, 1350),
    "9:16": (1080, 1920),
    "instagram_post": (1080, 1350),
    "reels_stories": (1080, 1920),
    "1:1": (1080, 1080),
    "square": (1080, 1080),
    "square_1080": (1080, 1080),
}
EXACT_DIMENSIONS = {
    "instagram_post": (1080, 1350),
    "reels_stories": (1080, 1920),
    "square_1080": (1080, 1080),
}
```

- [ ] **Step 4: Rewrite docs to make square explicit-only**

In `config/rules/image-dimensions.md` and `config/skills/illustration-carousel-framework.md`, replace any default square proof language with:

```markdown
Default final outputs are native 1080x1350 for Instagram posts and native
1080x1920 for Reels/Stories. Square 1080x1080 is allowed only when the creator
explicitly asks for square. Do not resize, crop, pad, or extend a wrong-size
image into final compliance.
```

- [ ] **Step 5: Run dimension tests**

Run:

```bash
cd /Users/himanshusharma/astoryoftwo-analysis
venv/bin/python -m pytest tests/test_checks_image_size.py -q
```

Expected: PASS.

- [ ] **Step 6: Commit**

```bash
cd /Users/himanshusharma/astoryoftwo-analysis
git add pipeline/agentic/checks/image_size.py tests/test_checks_image_size.py config/rules/image-dimensions.md config/skills/illustration-carousel-framework.md
git commit -m "fix: require exact native carousel output sizes"
```

---

### Task 9: Run The Focused Verification Set

**Files:**
- No source edits unless a focused test exposes a missed reference.

- [ ] **Step 1: Run focused tests**

Run:

```bash
cd /Users/himanshusharma/astoryoftwo-analysis
venv/bin/python -m pytest \
  tests/test_creator_workflow_contract.py \
  tests/test_creative_context.py \
  tests/test_carousel_prompt_compiler.py \
  tests/test_checks_image_size.py \
  -q
```

Expected: PASS.

- [ ] **Step 2: Run Agentic OS health because docs/context changed**

Run:

```bash
cd /Users/himanshusharma/astoryoftwo-analysis
venv/bin/python scripts/agentic_os.py health
```

Expected: PASS or a concrete existing repo-health warning unrelated to these edits. If it fails on changed files, repair before continuing.

- [ ] **Step 3: Run wiki health without committing unrelated output churn**

Run:

```bash
cd /Users/himanshusharma/astoryoftwo-analysis
venv/bin/python scripts/wiki_health.py --write --fix-index \
  --session-note "human-first carousel hot path repair"
```

Expected: command completes. Inspect generated changes and keep only relevant index/memory updates.

- [ ] **Step 4: Inspect git status**

Run:

```bash
cd /Users/himanshusharma/astoryoftwo-analysis
git status --short
```

Expected: only files intentionally changed by this plan are staged or unstaged. Do not revert unrelated human changes.

---

### Task 10: Prove The New Loop With One Dry Run

**Files:**
- Generated output under `/Users/himanshusharma/astoryoftwo-analysis/output/carousels/<date>/<slug>/`
- No manual edits expected unless the dry run exposes a real bug.

- [ ] **Step 1: Run a tiny carousel dry path**

Run:

```bash
cd /Users/himanshusharma/astoryoftwo-analysis
make carousel STORY="main kar lungi, but she still waits near the door"
```

Expected: package is created with a human baseline, creative context, prompts, and native-format handoff expectations.

- [ ] **Step 2: Inspect generated package**

Run:

```bash
cd /Users/himanshusharma/astoryoftwo-analysis
find output/carousels -maxdepth 3 -type f \( -name 'human-baseline.md' -o -name 'creative-context.json' -o -name 'storyboard.md' -o -name 'visual-qa.md' -o -name 'final-audit.json' \) | tail -20
```

Expected: new package contains the compact hot-path artifacts or the command reveals which pipeline file still writes only the older artifact set.

- [ ] **Step 3: Decide next implementation plan**

If the dry run still writes the older artifact set, create the next plan for wiring `CreativeContext` into:

- `/Users/himanshusharma/astoryoftwo-analysis/scripts/create_illustration_carousel.py`
- `/Users/himanshusharma/astoryoftwo-analysis/pipeline/stages/codex_native_carousel.py`
- `/Users/himanshusharma/astoryoftwo-analysis/pipeline/stages/carousel_package_writer.py`

Do not expand this plan until the docs, tests, prompt compiler, and dimensions are green.

---

## Self-Review

Spec coverage:
- Uses `astoryoftwo-analysis` as the production repo.
- Treats V2 as a reference mine only through compact assets.
- Implements "small brief first, human draft first, context as seasoning".
- Removes default multi-agent/process-heavy behavior from the hot path.
- Adds a canonical `CreativeContext` packet.
- Fixes known prompt budget and native dimension problems.
- Keeps verification focused.

Placeholder scan:
- No task uses placeholder tokens or open-ended implementation language.

Type consistency:
- `CreativeContext`, `creative-context.json`, `human-baseline.md`, `instagram_post`, and `reels_stories` are named consistently across tasks and tests.

## Execution Choice

Plan complete. Recommended execution is task-by-task, with a review checkpoint after each task.

1. Subagent-Driven: one fresh worker per task, with main-agent review after each patch.
2. Inline Execution: execute in this session, one task at a time, with focused tests after each task.
