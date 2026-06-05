# AGENTS.md Instruction Surface Repair Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Turn `AGENTS.md` from a stale, overlapping workflow dump into a concise Codex instruction surface that points to canonical plans, rules, memory, skills, and executable gates.

**Architecture:** `AGENTS.md` should be an index and operating contract, not the place where every carousel agent, artifact, and rule is copied. Canonical detail remains in `config/rules/`, `config/skill-systems.json`, `config/skills/`, `docs/superpowers/plans/creative-os-master-plan.md`, and executable gates. `wiki_health.py` and docs tests must fail when `AGENTS.md` or `CLAUDE.md` drift from that contract.

**Tech Stack:** Markdown, Python 3 via `venv/bin/python`, pytest, existing `pipeline/stages/wiki_health.py`, existing Agentic OS learning proposal flow.

---

## Source Hierarchy

Use this order when resolving conflicts:

1. `docs/superpowers/plans/creative-os-master-plan.md` - canonical creative OS plan.
2. `docs/superpowers/plans/THE-PLAN.md` - ordered execution sequence.
3. `docs/superpowers/plans/2026-05-31-agentic-os-activation-sprint.md` - runner activation target.
4. `config/rules/*.md` - canonical generation rules.
5. `config/skill-systems.json` - workflow system registry.
6. `config/skills/*.md` and `agents/*.md` - behavior modules.
7. `AGENTS.md` and `CLAUDE.md` - instruction surfaces only.

The earlier `docs/superpowers/plans/2026-05-31-carousel-autopilot-sprint.md` is superseded. Its P0 work still matters only where the master plan absorbed it.

---

## Section Review Matrix

| Current `AGENTS.md` Section | Verdict | Required Change |
|---|---|---|
| Canonical Rules | Keep, compress | Preserve `config/rules/` authority and migration gap. Remove prose duplication beyond the rule table. |
| Deterministic Gates | Keep, update | Keep runtime checks, require evidence paths/reasons, and point to `pipeline/agentic/checks/`. |
| Architecture Seven Layers | Keep, shorten | Keep high-level layer map but remove stale `Entry: scripts/create_illustration_carousel.py` as the primary C-layer entry. Mark current CLI vs activation target honestly. |
| Romance Story Selling Canon | Dedup | Keep trigger, source legality, 28/30 threshold, and hard fails. Point to `config/skills/romance-story-selling-engine.md` for the process. |
| Pipeline Stages A0-A5 | Keep, compress | Keep analysis pipeline only. Do not mix carousel runner rules here. |
| Running the Pipeline | Keep | Use `venv/bin/python` examples where repo commands require venv. |
| Agentic OS Control Plane | Major rewrite | Add live commands: `context`, `skill-system`, `recall`, `carousel-doctor`, `health`. Add activation target: `run-system`, `resume`, `status`, `runs`, `audit-packages` once runner lands. |
| Autopublish Closeout Gate | Keep, sync | Preserve mandatory closeout. Ensure `CLAUDE.md` has the same closeout commands. |
| Illustrated Carousel Pipeline | Major rewrite | Replace the giant C-layer block with a short `carousel_jam` contract, hard gates, human pauses, state honesty, and links to canonical files. |
| `/story` Command | Rewrite | Treat as a creator command routed through current carousel jam flow. Do not make `scripts/create_illustration_carousel.py` the authoritative process. |
| Stage-Scene Gate | Keep, compress | Keep as a hard gate. Point detailed behavior to skills and contracts. |
| Visual Debate Gate | Keep, compress | Keep as hard gate. Tests should not require all detailed visual-agent text in `AGENTS.md`. |
| Creator Jam Response Contract | Keep, compress | Keep the creator-facing override and no generic visual companion rule. Move detailed step order to `config/skills/carousel-jam-autopilot.md`. |
| C-Layer Agents Table | Remove | Replace with `config/skill-systems.json:carousel_jam` as source of components, agents, gates, and artifacts. |
| C-Layer Output | Replace | Remove old 20-plus artifact list. Use current honest state contract and note reduced artifact target from activation sprint. |
| D-Layer Article Pipeline | Compress | Keep entry behavior and final publish gate. Point details to D-layer skill files. |
| Memory Model | Major rewrite | Add atomic learning propagation: semantic memory plus skill/contract plus episodic record; `working.md` pointer only. |
| Wiki Health And Session Close | Keep, strengthen | Add instruction surface sync and banned stale workflow checks. |
| Wiki Structure | Keep | No change beyond wording. |
| Apify Integration | Fix | Remove "Claude Code sessions" wording from `AGENTS.md`; use platform-neutral wording. |
| Pre-Post Pipeline | Compress | Keep B-layer summary and verdict tiers. Point process to `config/skill-systems.json:prepost_reel`. |
| Lint Rules | Expand | Add no stale instruction surface, no working-only learning, and no docs-only PASS rules. |

---

## File Map

### Modify

- `AGENTS.md` - rewrite as concise Codex instruction surface.
- `CLAUDE.md` - keep synced with `AGENTS.md` on source hierarchy, Agentic OS surface, learning, and closeout.
- `pipeline/stages/wiki_health.py` - strengthen instruction surface sync checks.
- `tests/test_agentic_docs_contract.py` - enforce Agentic OS and instruction surface contract.
- `tests/test_creator_workflow_contract.py` - move detailed carousel gate expectations away from `AGENTS.md` and toward canonical skills/systems.
- `tests/test_wiki_health.py` - add tests for stale instruction surface and banned phrases.

### Create

- `config/instruction_surface_contract.json` - structured required and banned instruction-surface rules.
- `tests/test_instruction_surface_contract.py` - validates the contract file itself.

### Do Not Modify In This Plan

- Do not rewrite carousel generation code.
- Do not delete skill files.
- Do not delete existing carousel packages.
- Do not auto-apply learning proposals without approval.

---

### Task 1: Add An Instruction Surface Contract

**Files:**
- Create: `config/instruction_surface_contract.json`
- Create: `tests/test_instruction_surface_contract.py`

- [ ] **Step 1: Write the failing contract test**

Create `tests/test_instruction_surface_contract.py`:

```python
from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_instruction_surface_contract_declares_required_and_banned_phrases() -> None:
    path = ROOT / "config" / "instruction_surface_contract.json"
    data = json.loads(path.read_text(encoding="utf-8"))

    assert data["schema_version"] == "1.0"
    assert data["max_agents_md_lines"] <= 420
    assert "AGENTS.md" in data["surfaces"]
    assert "CLAUDE.md" in data["surfaces"]

    required = set(data["required_phrases"])
    assert "config/rules/" in required
    assert "config/skill-systems.json" in required
    assert "scripts/agentic_os.py carousel-doctor" in required
    assert "memory/semantic/" in required
    assert "scripts/wiki_health.py --write --fix-index" in required
    assert "scripts/autopublish.py" in required

    banned = set(data["banned_phrases"]["AGENTS.md"])
    assert "Entry: scripts/create_illustration_carousel.py" in banned
    assert "and can be called directly from Claude Code sessions" in banned
```

- [ ] **Step 2: Run the test and verify failure**

Run:

```bash
venv/bin/python -m pytest tests/test_instruction_surface_contract.py -q
```

Expected:

```text
FAILED ... FileNotFoundError: ... config/instruction_surface_contract.json
```

- [ ] **Step 3: Create the contract**

Create `config/instruction_surface_contract.json`:

```json
{
  "schema_version": "1.0",
  "max_agents_md_lines": 420,
  "surfaces": [
    "AGENTS.md",
    "CLAUDE.md"
  ],
  "source_hierarchy": [
    "docs/superpowers/plans/creative-os-master-plan.md",
    "docs/superpowers/plans/THE-PLAN.md",
    "docs/superpowers/plans/2026-05-31-agentic-os-activation-sprint.md",
    "config/rules/",
    "config/skill-systems.json",
    "config/skills/",
    "agents/"
  ],
  "required_phrases": [
    "config/rules/",
    "config/skill-systems.json",
    "scripts/agentic_os.py context --render",
    "scripts/agentic_os.py skill-system carousel_jam",
    "scripts/agentic_os.py carousel-doctor",
    "memory/semantic/",
    "memory/working.md is pointer-only",
    "Learning proposals are draft-only",
    "scripts/wiki_health.py --write --fix-index",
    "scripts/autopublish.py"
  ],
  "banned_phrases": {
    "AGENTS.md": [
      "Entry: scripts/create_illustration_carousel.py",
      "Each package contains:",
      "C1-C6 runner",
      "and can be called directly from Claude Code sessions"
    ],
    "CLAUDE.md": []
  }
}
```

- [ ] **Step 4: Run the test and verify pass**

Run:

```bash
venv/bin/python -m pytest tests/test_instruction_surface_contract.py -q
```

Expected:

```text
1 passed
```

---

### Task 2: Strengthen Wiki Health Instruction Checks

**Files:**
- Modify: `pipeline/stages/wiki_health.py`
- Modify: `tests/test_wiki_health.py`
- Test: `tests/test_instruction_surface_contract.py`

- [ ] **Step 1: Add failing tests for stale instruction drift**

Append these tests to `tests/test_wiki_health.py`:

```python
def test_health_flags_stale_agents_instruction_surface(tmp_path):
    minimal_workspace(tmp_path)
    contract_dir = tmp_path / "config"
    contract_dir.mkdir(exist_ok=True)
    write_text(
        contract_dir / "instruction_surface_contract.json",
        json.dumps(
            {
                "schema_version": "1.0",
                "max_agents_md_lines": 20,
                "surfaces": ["AGENTS.md", "CLAUDE.md"],
                "required_phrases": [
                    "config/rules/",
                    "scripts/agentic_os.py carousel-doctor",
                    "scripts/autopublish.py"
                ],
                "banned_phrases": {
                    "AGENTS.md": ["Entry: scripts/create_illustration_carousel.py"],
                    "CLAUDE.md": []
                },
            }
        ),
    )
    write_text(
        tmp_path / "AGENTS.md",
        "\n".join(
            [
                "# AGENTS",
                "config/rules/",
                "scripts/agentic_os.py carousel-doctor",
                "scripts/autopublish.py",
                "Entry: scripts/create_illustration_carousel.py"
            ]
        ),
    )
    write_text(
        tmp_path / "CLAUDE.md",
        "# CLAUDE\n\nconfig/rules/\nscripts/agentic_os.py carousel-doctor\nscripts/autopublish.py\n",
    )

    health = collect_wiki_health(tmp_path, today=date(2026, 6, 6))
    checks = checks_by_id(health)

    assert checks["instruction_surface_contract"]["status"] == "FAIL"
    assert "Entry: scripts/create_illustration_carousel.py" in checks["instruction_surface_contract"]["evidence"]["banned_hits"]["AGENTS.md"]


def test_health_passes_clean_instruction_surface_contract(tmp_path):
    minimal_workspace(tmp_path)
    contract_dir = tmp_path / "config"
    contract_dir.mkdir(exist_ok=True)
    write_text(
        contract_dir / "instruction_surface_contract.json",
        json.dumps(
            {
                "schema_version": "1.0",
                "max_agents_md_lines": 20,
                "surfaces": ["AGENTS.md", "CLAUDE.md"],
                "required_phrases": [
                    "config/rules/",
                    "scripts/agentic_os.py carousel-doctor",
                    "scripts/autopublish.py"
                ],
                "banned_phrases": {
                    "AGENTS.md": ["Entry: scripts/create_illustration_carousel.py"],
                    "CLAUDE.md": []
                },
            }
        ),
    )
    clean = "# SURFACE\n\nconfig/rules/\nscripts/agentic_os.py carousel-doctor\nscripts/autopublish.py\n"
    write_text(tmp_path / "AGENTS.md", clean)
    write_text(tmp_path / "CLAUDE.md", clean)

    health = collect_wiki_health(tmp_path, today=date(2026, 6, 6))
    checks = checks_by_id(health)

    assert checks["instruction_surface_contract"]["status"] == "PASS"
```

- [ ] **Step 2: Run the tests and verify failure**

Run:

```bash
venv/bin/python -m pytest tests/test_wiki_health.py::test_health_flags_stale_agents_instruction_surface tests/test_wiki_health.py::test_health_passes_clean_instruction_surface_contract -q
```

Expected:

```text
FAILED ... KeyError: 'instruction_surface_contract'
```

- [ ] **Step 3: Implement contract loading and checking**

In `pipeline/stages/wiki_health.py`, add a helper after `instruction_surface_evidence`:

```python
def instruction_surface_contract_evidence(root: Path) -> dict[str, Any]:
    path = root / "config" / "instruction_surface_contract.json"
    if not path.exists():
        return {
            "contract_path": "config/instruction_surface_contract.json",
            "missing_contract": True,
            "missing_phrases": {},
            "banned_hits": {},
            "line_count_violations": {},
        }
    contract = json.loads(path.read_text(encoding="utf-8"))
    required = contract.get("required_phrases", [])
    banned_by_surface = contract.get("banned_phrases", {})
    surfaces = contract.get("surfaces", INSTRUCTION_SURFACE_FILES)
    max_agents_lines = int(contract.get("max_agents_md_lines", 10_000))

    missing_phrases: dict[str, list[str]] = {}
    banned_hits: dict[str, list[str]] = {}
    line_count_violations: dict[str, int] = {}

    for relative in surfaces:
        surface_path = root / relative
        text = surface_path.read_text(encoding="utf-8") if surface_path.exists() else ""
        absent = [phrase for phrase in required if not instruction_has_phrase(text, phrase)]
        if absent:
            missing_phrases[relative] = absent

        hits = [
            phrase
            for phrase in banned_by_surface.get(relative, [])
            if instruction_has_phrase(text, phrase)
        ]
        if hits:
            banned_hits[relative] = hits

        if relative == "AGENTS.md":
            line_count = len(text.splitlines())
            if line_count > max_agents_lines:
                line_count_violations[relative] = line_count

    return {
        "contract_path": "config/instruction_surface_contract.json",
        "missing_contract": False,
        "missing_phrases": missing_phrases,
        "banned_hits": banned_hits,
        "line_count_violations": line_count_violations,
    }
```

Then in `collect_wiki_health`, after the existing `instruction_surface_sync` check, add:

```python
    contract_evidence = instruction_surface_contract_evidence(root)
    contract_drift = bool(
        contract_evidence["missing_contract"]
        or contract_evidence["missing_phrases"]
        or contract_evidence["banned_hits"]
        or contract_evidence["line_count_violations"]
    )
    checks.append(
        make_check(
            "instruction_surface_contract",
            "FAIL" if contract_drift else "PASS",
            "critical" if contract_drift else "info",
            "Instruction surfaces match the current source hierarchy and avoid stale workflow claims.",
            contract_evidence,
        )
    )
```

- [ ] **Step 4: Run focused tests**

Run:

```bash
venv/bin/python -m pytest tests/test_instruction_surface_contract.py tests/test_wiki_health.py::test_health_flags_stale_agents_instruction_surface tests/test_wiki_health.py::test_health_passes_clean_instruction_surface_contract -q
```

Expected:

```text
3 passed
```

---

### Task 3: Rewrite `AGENTS.md` As A Codex Instruction Surface

**Files:**
- Modify: `AGENTS.md`
- Test: `tests/test_agentic_docs_contract.py`
- Test: `tests/test_creator_workflow_contract.py`

- [ ] **Step 1: Add failing docs contract tests**

Extend `tests/test_agentic_docs_contract.py`:

```python
def test_agents_md_is_codex_instruction_index_not_stale_workflow_dump():
    agents = (ROOT / "AGENTS.md").read_text(encoding="utf-8")

    assert len(agents.splitlines()) <= 420
    assert "docs/superpowers/plans/creative-os-master-plan.md" in agents
    assert "docs/superpowers/plans/THE-PLAN.md" in agents
    assert "config/skill-systems.json" in agents
    assert "scripts/agentic_os.py carousel-doctor" in agents
    assert "memory/working.md is pointer-only" in agents
    assert "Learning proposals are draft-only" in agents

    assert "Entry: scripts/create_illustration_carousel.py" not in agents
    assert "and can be called directly from Claude Code sessions" not in agents
    assert "Each package contains:" not in agents
```

- [ ] **Step 2: Run docs tests and verify failure**

Run:

```bash
venv/bin/python -m pytest tests/test_agentic_docs_contract.py -q
```

Expected before the rewrite:

```text
FAILED ... assert len(agents.splitlines()) <= 420
```

- [ ] **Step 3: Replace the `AGENTS.md` structure**

Rewrite `AGENTS.md` to this section order:

```markdown
# AGENTS.md - A Story of Two Creative OS

## Read First
- `AGENTS.md` is the Codex instruction surface. It is not the canonical source for every detailed rule.
- Canonical creative architecture: `docs/superpowers/plans/creative-os-master-plan.md`.
- Ordered execution plan: `docs/superpowers/plans/THE-PLAN.md`.
- Runner activation target: `docs/superpowers/plans/2026-05-31-agentic-os-activation-sprint.md`.
- Superseded context only: `docs/superpowers/plans/2026-05-31-carousel-autopilot-sprint.md`.

## Source Of Truth
- Generation rules live in `config/rules/`.
- Workflow systems live in `config/skill-systems.json`.
- Skill behavior lives in `config/skills/`.
- Agent prompts live in `agents/`.
- Durable memory lives in `memory/semantic/` and `memory/episodic/`.
- `memory/working.md is pointer-only`: current-session notes and links, not durable learning.

## Canonical Rules
Keep the existing compact table for:
- palette
- identity
- on-image-text
- brandmark
- brand-zone
- voice
- golden-theme
- story-selling

Also keep:
- `{{rule:NAME}}` include syntax.
- Known skill-dedup migration gap.
- `config/rules/` wins on disagreement.

## Agentic OS Control Plane
Current live commands:
```bash
venv/bin/python scripts/agentic_os.py context --render
venv/bin/python scripts/agentic_os.py skill-system carousel_jam
venv/bin/python scripts/agentic_os.py recall "kitchen comedy carousel"
venv/bin/python scripts/agentic_os.py carousel-doctor output/carousels/<date>/<slug>
venv/bin/python scripts/agentic_os.py health
```

Activation target once runner tasks land:
```bash
venv/bin/python scripts/agentic_os.py run-system carousel_jam --story "..."
venv/bin/python scripts/agentic_os.py status <run-id>
venv/bin/python scripts/agentic_os.py resume <run-id> --input-file decision.json
venv/bin/python scripts/agentic_os.py runs
venv/bin/python scripts/agentic_os.py audit-packages
```

Do not claim target commands are live until `scripts/agentic_os.py --help` lists them.

## Creative Workflow Systems
- Carousel jam: `config/skill-systems.json:carousel_jam`.
- Story article: `config/skill-systems.json:story_article`.
- Pre-post Reel: `config/skill-systems.json:prepost_reel`.
- Wiki health: `config/skill-systems.json:wiki_health`.

## Carousel Hard Gates
For carousel work, these are non-negotiable:
- Load `wiki/insights/successful-carousel-standard.md` before carousel writing.
- Define audience success, creative success, brand success, and production success.
- Run Layer E before deciding what the love story means.
- Require Story-Selling score >= 28/30 or repair.
- Run the golden-theme variant tournament and require >= 28/30 or repair.
- Run Stage-Scene Gate before hooks, slide copy, captions, prompts, or generation.
- Text completes the scene; text must not carry the scene.
- Run Post-Copy Visual Room after creator-confirmed copy.
- Run Visual Debate Gate before image generation.
- Run `visual-plan-quality` per slide and block on any REPAIR/STOP.
- Use actual Aachu/Zuv identity references for final generation.
- Handoff is not final. Partial final is not publishable.
- A carousel is publishable only when both native 4:5 and native 9:16 outputs, visual QA, and final audit pass.

## Creator Jam Contract
- For "jam", "brainstorm", "pick today's carousel", or similar, treat it as C-layer creator ideation.
- Do not offer generic visual companion, browser mockup, design-doc, or spec approval flow.
- Read `memory/semantic/carousel-idea-preferences.md` before pitching ideas.
- Do not pitch rejected, packaged, or cooled-down lanes as fresh ideas unless explicitly asked.
- Ask at most one practical context question if no moment, photo, or constraint exists.
- Record recommendation, rejection, acceptance, or cooldown in `memory/semantic/carousel-idea-preferences.md`.

## State Honesty
- Use `pipeline/agentic/carousel_state.py` and `pipeline/agentic/workflow_doctor.py`.
- No PASS/GO/publishable without artifact proof.
- No docs-only gates.
- No image-generation blocker may coexist with publishable final state unless explicitly superseded.
- No raw-scene rejection may coexist with generation allowed.

## Learning And Memory
- No correction that only lands in `memory/working.md`.
- Creator corrections propagate to durable memory and behavior:
  1. `memory/semantic/<relevant-file>.md` with confidence.
  2. Relevant `config/skills/*.md`, `config/rules/*.md`, or contract JSON when behavior changes.
  3. `memory/episodic/<date>-learning.md` or Agentic OS learning event.
  4. `memory/working.md` pointer only.
- Learning proposals are draft-only until evaluation passes and a human or explicit repo instruction approves the change.
- If a learning changes how agents should operate, update `AGENTS.md` and `CLAUDE.md` in the same session or leave a HEAL proposal that names the missing instruction update.

## Pipelines
Keep only compact summaries for:
- A0-A5 analysis pipeline.
- B-layer pre-post Reel analysis.
- D-layer Substack article packaging.
- Apify scraping.

## Session Closeout
At the end of every substantial session that changes repo files:
```bash
venv/bin/python scripts/wiki_health.py --write --fix-index \
  --session-note "what got better about the system today"
venv/bin/python scripts/autopublish.py \
  --session-note "what got better about the system today"
```

If the worktree contains unrelated changes, use repeated `--include PATH` flags for owned files only.

## Lint Rules
- Never commit `.env`.
- `corpus/raw/` is ephemeral.
- `config/rules/` is authoritative over duplicated rule text.
- `memory/working.md` is not durable memory.
- `AGENTS.md` must remain a concise instruction surface, not a copied workflow manual.
```

- [ ] **Step 4: Run docs tests**

Run:

```bash
venv/bin/python -m pytest tests/test_agentic_docs_contract.py -q
```

Expected:

```text
all tests passed
```

---

### Task 4: Move Detailed Carousel Assertions Out Of `AGENTS.md`

**Files:**
- Modify: `tests/test_creator_workflow_contract.py`
- Modify: `AGENTS.md` if needed after tests

- [ ] **Step 1: Update brittle tests**

Change `tests/test_creator_workflow_contract.py` so it no longer requires full detailed artifact names in `AGENTS.md`. The detailed checks should target canonical files:

```python
def test_visual_debate_gate_is_persistent_for_carousel_work():
    agents = (WORKSPACE / "AGENTS.md").read_text(encoding="utf-8")
    framework = (WORKSPACE / "config/skills/illustration-carousel-framework.md").read_text(
        encoding="utf-8"
    )
    systems = (WORKSPACE / "config/skill-systems.json").read_text(encoding="utf-8")
    contract = (WORKSPACE / "config/carousel_style_contract.json").read_text(encoding="utf-8")

    assert "Visual Debate Gate" in agents
    assert "before image generation" in agents
    assert "visual-debate.json" in framework
    assert "three visual agents" in framework
    assert "carousel-visual-evidence-planner.md" in systems
    assert "carousel-romance-scene-planner.md" in systems
    assert "carousel-visual-continuity-judge.md" in systems

    assert '"visual_debate_policy"' in contract
    assert '"required": true' in contract
```

Keep the existing tests that require:
- Creator Jam Response Contract.
- Layer E.
- Stage-Scene Gate.
- `text completes the scene`.
- Successful carousel standard.

But allow `AGENTS.md` to mention these as compact hard gates, not full process copies.

- [ ] **Step 2: Run focused creator workflow tests**

Run:

```bash
venv/bin/python -m pytest tests/test_creator_workflow_contract.py -q
```

Expected:

```text
all tests passed
```

---

### Task 5: Sync `CLAUDE.md` With The Repaired Surface

**Files:**
- Modify: `CLAUDE.md`
- Test: `tests/test_agentic_docs_contract.py`
- Test: `tests/test_wiki_health.py`

- [ ] **Step 1: Add or confirm shared phrases**

Ensure `CLAUDE.md` contains:

```markdown
## Agentic OS Control Plane

Live commands:
```bash
venv/bin/python scripts/agentic_os.py context --render
venv/bin/python scripts/agentic_os.py skill-system carousel_jam
venv/bin/python scripts/agentic_os.py carousel-doctor output/carousels/<date>/<slug>
venv/bin/python scripts/agentic_os.py health
```

Learning proposals are draft-only. Durable learning belongs in `memory/semantic/` and `memory/episodic/`; `memory/working.md is pointer-only`.
```

Also ensure closeout still includes:

```bash
venv/bin/python scripts/wiki_health.py --write --fix-index \
  --session-note "what got better about the system today"
venv/bin/python scripts/autopublish.py \
  --session-note "what got better about the system today"
```

- [ ] **Step 2: Run sync checks**

Run:

```bash
venv/bin/python -m pytest tests/test_agentic_docs_contract.py tests/test_wiki_health.py -q
```

Expected:

```text
all tests passed
```

---

### Task 6: Add Learning-To-Instruction Update Rules

**Files:**
- Modify: `AGENTS.md`
- Modify: `pipeline/agentic/learning_loop.py`
- Modify: `tests/test_agentic_learning_eval_cli.py` or create `tests/test_instruction_learning_proposals.py`

- [ ] **Step 1: Add failing test for instruction-surface learning proposal**

Create `tests/test_instruction_learning_proposals.py`:

```python
from __future__ import annotations

import json
from pathlib import Path

from pipeline.agentic.learning_loop import capture_learning_event, create_instruction_surface_proposal


def test_learning_event_can_propose_agents_md_update(tmp_path: Path) -> None:
    (tmp_path / "AGENTS.md").write_text(
        "# AGENTS\n\n## Learning And Memory\n\nLearning proposals are draft-only.\n",
        encoding="utf-8",
    )
    event = capture_learning_event(
        tmp_path,
        source="creator_correction",
        summary="Instruction update needed: AGENTS.md must say raw-scene rows are locked before Layer E.",
        evidence_paths=["docs/superpowers/plans/creative-os-master-plan.md"],
    )

    proposal_path = create_instruction_surface_proposal(
        tmp_path,
        source_event_id=event.event_id,
        target_path="AGENTS.md",
        insertion_heading="Learning And Memory",
        instruction_line="- Raw-scene rows are locked before Layer E for creator-supplied moments.",
        rationale="Creator correction changed the operating contract for carousel sessions.",
    )

    proposal = json.loads(proposal_path.read_text(encoding="utf-8"))
    assert proposal["target_path"] == "AGENTS.md"
    assert proposal["status"] == "draft"
    content = (tmp_path / proposal["proposed_content_path"]).read_text(encoding="utf-8")
    assert "Raw-scene rows are locked before Layer E" in content
```

- [ ] **Step 2: Run test and verify failure**

Run:

```bash
venv/bin/python -m pytest tests/test_instruction_learning_proposals.py -q
```

Expected:

```text
ImportError: cannot import name 'create_instruction_surface_proposal'
```

- [ ] **Step 3: Implement proposal helper**

Add to `pipeline/agentic/learning_loop.py`:

```python
def create_instruction_surface_proposal(
    root: Path,
    *,
    source_event_id: str,
    target_path: str,
    insertion_heading: str,
    instruction_line: str,
    rationale: str,
) -> Path:
    root = root.resolve()
    target = root / target_path
    current = target.read_text(encoding="utf-8") if target.exists() else ""
    heading = f"## {insertion_heading}"
    if instruction_line in current:
        proposed = current
    elif heading in current:
        proposed = current.replace(heading, f"{heading}\n{instruction_line}", 1)
    else:
        proposed = current.rstrip() + f"\n\n{heading}\n{instruction_line}\n"
    return create_learning_proposal(
        root,
        source_event_id=source_event_id,
        target_path=target_path,
        proposed_action="modify",
        rationale=rationale,
        proposed_content=proposed,
        required_validators=[
            "venv/bin/python -m pytest tests/test_agentic_docs_contract.py tests/test_wiki_health.py -q"
        ],
    )
```

This helper creates a draft proposal. It does not auto-apply it.

- [ ] **Step 4: Run learning proposal tests**

Run:

```bash
venv/bin/python -m pytest tests/test_instruction_learning_proposals.py tests/test_agentic_learning_eval_cli.py -q
```

Expected:

```text
all tests passed
```

---

### Task 7: Verify The Whole Repair

**Files:**
- All modified files from Tasks 1-6

- [ ] **Step 1: Run focused tests**

Run:

```bash
venv/bin/python -m pytest \
  tests/test_instruction_surface_contract.py \
  tests/test_agentic_docs_contract.py \
  tests/test_creator_workflow_contract.py \
  tests/test_wiki_health.py \
  tests/test_instruction_learning_proposals.py \
  -q
```

Expected:

```text
all tests passed
```

- [ ] **Step 2: Run full tests**

Run:

```bash
venv/bin/python -m pytest -q
```

Expected:

```text
all tests passed
```

- [ ] **Step 3: Run wiki health**

Run:

```bash
venv/bin/python scripts/wiki_health.py --write --fix-index \
  --session-note "Repair AGENTS.md instruction surface, sync CLAUDE.md, and add instruction drift checks"
```

Expected:

```text
status is PASS or NEEDS_HEAL only for unrelated pre-existing wiki metadata issues.
No instruction_surface_contract failure.
```

- [ ] **Step 4: Run autopublish**

Run:

```bash
venv/bin/python scripts/autopublish.py \
  --session-note "Repair AGENTS.md instruction surface, sync CLAUDE.md, and add instruction drift checks"
```

Expected:

```text
Autopublish either commits and pushes owned changes, or blocks with a named mixed-worktree/risky-path reason.
```

---

## Definition Of Done

- `AGENTS.md` is under 420 lines.
- `AGENTS.md` no longer presents `scripts/create_illustration_carousel.py` as the primary C-layer entry.
- `AGENTS.md` contains current live Agentic OS commands and clearly labels future runner commands as activation targets.
- `AGENTS.md` points to `config/skill-systems.json` instead of duplicating every C-layer agent and artifact.
- `AGENTS.md` preserves hard creative gates: Layer E, golden-theme tournament, Stage-Scene Gate, Visual Debate Gate, visual-plan-quality, identity references, native 4:5 and 9:16, visual QA, final audit.
- `AGENTS.md` states that `memory/working.md is pointer-only`.
- Durable learning requires `memory/semantic/` plus skill/rule/contract updates when behavior changes.
- Learning proposals remain draft-only.
- `CLAUDE.md` and `AGENTS.md` share required closeout and Agentic OS surface phrases.
- `wiki_health.py` fails on stale/banned instruction surface phrases.
- Focused and full tests pass, or blockers are explicitly named.
