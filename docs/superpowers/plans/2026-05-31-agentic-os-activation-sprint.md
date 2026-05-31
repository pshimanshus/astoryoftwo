# Agentic OS Activation Sprint Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Activate the existing Agentic OS so it executes the carousel workflow end-to-end as a typed state machine — replacing the ad-hoc orchestration in `scripts/create_illustration_carousel.py`, collapsing 15-place rule duplication to a single canonical source, swapping LLM-judged-gates for deterministic checks where physics allows, and inserting five explicit human pauses at the moments the creator's taste must enter the loop.

**Architecture:** The repo already has solid typed primitives (`ContextPack`, `SkillRecord`, `WorkflowGate`, `AuditEvent`, `LearningEvent` → `LearningProposal` → `SkillEvalResult`) and a read-only inspector CLI in `scripts/agentic_os.py`. The missing piece is a **runner** that consumes `config/skill-systems.json:carousel_jam` and drives a workflow state machine with pause-resume semantics, per-state agent invocations with typed I/O, deterministic gates (palette/OCR/size), and reduced per-package artifacts (8 first-class files derived from `state.json` + `audit.log.jsonl` + `gates.json`).

**Tech Stack:** Python 3.11+, pydantic v2 (already in use via `contracts.py`), pytest, Pillow (palette), easyocr (text), existing `pipeline/agentic/` package, existing `pipeline/stages/` modules where relevant, JSON/JSONL artifacts. No new third-party orchestration framework. No additional API providers — Codex itself is the image-generation runtime.

---

## Sprint North Star

The current failure modes — yellow tone returning despite the rule, identity drift, hours per carousel, 25 artifacts written per package, 7 sequential LLM-judged gates that all return PASS while the image is wrong — share **one** root cause: the well-designed Agentic OS primitives in `pipeline/agentic/` are not invoked at the moment a carousel is generated. The carousel script runs its own ad-hoc flow; the typed contracts, gates, audit log, and learning loop are parallel infrastructure with no caller.

The fastest 10× sprint is therefore:

1. **Consolidate rules to one canonical source** so every prompt, agent, and check reads the same constraint text (kills the 15-copies-of-yellow problem).
2. **Make `agentic_os.py` an executor**, not just an inspector — add `run-system`, `resume`, `status`, `runs` subcommands that drive a state machine.
3. **Define the carousel state machine** as a typed Pydantic model with discrete states, gates, and pause-for-human transitions.
4. **Build deterministic gates** (palette histogram, OCR text match, image size, prompt constraint regex) and wire them next to LLM gates so PASS means something physical.
5. **Reduce per-package artifacts to 8 first-class files + 3 derived files** (state.json, audit.log.jsonl, gates.json) computed from runner state. No more 14 personas each writing free-form JSON.
6. **Five explicit human pauses** (concept-lock, copy-lock, visual-plan-lock, proof-approval, final-approval) as first-class states in the machine, resumable via `agentic_os.py resume <run-id>`.

If a future sprint adds Remotion motion or D-layer article runs, they reuse the runner. This sprint is the spine.

---

## Pareto Scope

### Must Finish This Sprint

These eight items are the activation spine. They produce ~10× the reliability gain over the current ad-hoc flow.

1. **Rule consolidation** to `config/rules/` with `{{rule:NAME}}` include syntax.
2. **`WorkflowState` + `WorkflowRun` typed contracts** added to `pipeline/agentic/contracts.py`.
3. **Workflow runner** in `pipeline/agentic/workflow_runner.py` with the carousel_jam state machine.
4. **Per-state agent invocation** with typed I/O Pydantic schemas in `pipeline/agentic/workflows/carousel_jam/`.
5. **Deterministic gates** package in `pipeline/agentic/checks/` (palette, OCR, size, prompt-constraints).
6. **`agentic_os.py run-system / resume / status / runs`** subcommands.
7. **Reduced artifact set** — package writer emits only the 8 first-class files; runner state lives under `memory/agentic/workflow-runs/<run-id>/`.
8. **One real carousel** taken end-to-end through the runner with all five pauses honored, compared against a recent old-flow carousel for latency + reliability.

### Should Finish After Must Finish

9. **`create_illustration_carousel.py` becomes a thin wrapper** that forwards to `agentic_os.py run-system carousel_jam` with the existing CLI surface.
10. **Skill files in `config/skills/` deduplicated** to use rule includes; no inline rule duplication remains.
11. **Triage of existing 67 packages** via a one-shot `agentic_os.py audit-packages` that reports state per package using the new gates.
12. **Wire `LearningEvent` capture** into the runner so repair notes from human pauses become draft proposals.

### Deeper Hardening (Next Sprint)

13. Replay support: `agentic_os.py replay <run-id>` re-executes a state with current rules to catch regressions when rules change.
14. Same runner pattern applied to `story_article` and `prepost_reel` skill-systems (already declared, never executed).
15. Remotion motion as an optional post-CLOSEOUT state.
16. Brand integration as a first-class input flag with brand-zone rule + brand-label OCR check.
17. Index past carousels into `memory/graph.json` via `build_memory_index` so future runs benefit from recall.

---

## Sprint Board

| Lane | Owner Session | Priority | Status | Outcome |
|---|---:|---:|---|---|
| A. Rule Consolidation | Session A | P0 | Ready | One canonical rule source per concept; skill files use includes |
| B. Typed Contracts Extension | Session B | P0 | Ready | `WorkflowState` / `WorkflowRun` / `RunArtifact` / `RepairBudget` types added |
| C. Deterministic Gates | Session C | P0 | Ready | Palette / OCR / size / prompt-constraint checks return typed `WorkflowGate` |
| D. Workflow Runner Core | Session D | P0 | Ready | State machine executes carousel_jam with pause-resume |
| E. Per-State Handlers | Session E | P0 | Ready | One handler per state with typed I/O; agents invoked discretely |
| F. CLI Activation | Session F | P0 | Ready | `agentic_os.py run-system / resume / status / runs` work end-to-end |
| G. Package Writer Reduction | Session G | P1 | Ready | Package contains 8 first-class artifacts; runner state lives in memory/ |
| H. Real Carousel Dry Run | Session H | P0 | Ready | One end-to-end run; compared to old-flow latency + reliability |
| I. Legacy Wrapper + Skill Dedup | Session I | P1 | Ready | `create_illustration_carousel.py` is thin wrapper; skills use includes |
| J. Existing Package Audit | Session J | P1 | Ready | One-shot triage report over all 67 packages using new gates |
| K. Learning Capture Wiring | Session K | P2 | Ready | Human pause repair notes become draft `LearningProposal` |

---

## File Map

### Create

- `config/rules/palette.md` — single canonical palette rule (warm ivory; hard fails: yellow, mustard, sepia, parchment, tan, beige, cream-heavy).
- `config/rules/identity.md` — single canonical identity rule (Aachu/Zuv face refs, heights 5'8"/5'6", wardrobe continuity).
- `config/rules/on-image-text.md` — single canonical text rule (exact match `slides.md`, placement, typography).
- `config/rules/brandmark.md` — single canonical brandmark rule (bottom-right tiny low-contrast handwritten `@a.storyof.two`).
- `config/rules/brand-zone.md` — single canonical brand-integration rule (legibility, disclosure, brand-zone placement).
- `config/rules/voice.md` — single canonical voice rule (warm, intimate, visual-first, no advice tone).
- `config/rules/golden-theme.md` — single canonical golden-theme rule (universal relationship truth → Aachu/Zuv proof → Zuv active care → tender thesis).
- `config/rules/story-selling.md` — single canonical story-selling rubric (28/30 threshold + hard fails).
- `pipeline/agentic/workflow_runner.py` — state-machine driver with pause-resume.
- `pipeline/agentic/workflow_state.py` — typed `WorkflowRun` + `WorkflowState` + helpers (extends the existing stub).
- `pipeline/agentic/rule_includes.py` — `{{rule:NAME}}` expander used by context loader, prompt compiler, and skill renderer.
- `pipeline/agentic/checks/__init__.py`
- `pipeline/agentic/checks/palette.py` — Pillow histogram check.
- `pipeline/agentic/checks/ocr_text.py` — easyocr-backed on-image text match.
- `pipeline/agentic/checks/image_size.py` — PIL dimensions + aspect check.
- `pipeline/agentic/checks/prompt_constraints.py` — regex check that compiled prompt contains canonical hard-fail fragments.
- `pipeline/agentic/checks/face_continuity.py` — LLM-backed gate that compares slide image with identity refs; returns typed `WorkflowGate`.
- `pipeline/agentic/workflows/__init__.py`
- `pipeline/agentic/workflows/carousel_jam/__init__.py`
- `pipeline/agentic/workflows/carousel_jam/states.py` — `enum CarouselJamState` + transitions.
- `pipeline/agentic/workflows/carousel_jam/handlers/__init__.py`
- `pipeline/agentic/workflows/carousel_jam/handlers/session_start.py`
- `pipeline/agentic/workflows/carousel_jam/handlers/raw_scene_lock.py`
- `pipeline/agentic/workflows/carousel_jam/handlers/concept_generation.py`
- `pipeline/agentic/workflows/carousel_jam/handlers/copy_generation.py`
- `pipeline/agentic/workflows/carousel_jam/handlers/visual_plan.py`
- `pipeline/agentic/workflows/carousel_jam/handlers/prompt_compile.py`
- `pipeline/agentic/workflows/carousel_jam/handlers/proof_generation.py`
- `pipeline/agentic/workflows/carousel_jam/handlers/full_generation.py`
- `pipeline/agentic/workflows/carousel_jam/handlers/closeout.py`
- `pipeline/agentic/workflows/carousel_jam/io_schemas.py` — Pydantic input/output types per state.
- `pipeline/agentic/package_writer.py` — emits the reduced 8-file package; reads from runner state.
- `scripts/audit_packages.py` — one-shot triage over `output/carousels/**` using new gates.
- `tests/test_rule_includes.py`
- `tests/test_workflow_state.py`
- `tests/test_checks_palette.py`
- `tests/test_checks_ocr_text.py`
- `tests/test_checks_image_size.py`
- `tests/test_checks_prompt_constraints.py`
- `tests/test_workflow_runner_carousel_jam.py`
- `tests/test_agentic_os_run_system_cli.py`
- `tests/test_package_writer_reduced.py`
- `docs/superpowers/specs/agentic-os-workflow-runner.md` — durable contract for the runner; updated as the runner stabilizes.

### Modify

- `pipeline/agentic/contracts.py` — add `WorkflowRun`, `WorkflowStateRecord`, `RepairBudget`, `RunArtifact`, `PauseRequest` types; extend `WorkflowGate` if needed.
- `pipeline/agentic/context_loader.py` — expand `{{rule:NAME}}` includes in section content before token estimation.
- `pipeline/agentic/skill_registry.py` — when resolving a system, include the rule files referenced by its skills.
- `pipeline/agentic/audit_log.py` — append per-run JSONL writer; one file per `run-id`.
- `pipeline/agentic/learning_loop.py` — surface a `record_pause_repair(run_id, state, note)` helper used by handlers.
- `scripts/agentic_os.py` — add `run-system`, `resume`, `status`, `runs`, `audit-packages` subcommands.
- `scripts/create_illustration_carousel.py` — becomes a thin wrapper around `agentic_os.py run-system carousel_jam` (Session I).
- `config/skills/*.md` — replace inline rule duplication with `{{rule:NAME}}` includes (Session I).
- `CLAUDE.md` — point the "Agentic OS Control Plane" section at the new runner commands.
- `AGENTS.md` — replace the giant per-agent paragraph blocks with a short reference to `config/skill-systems.json` + the runner; preserve only the architectural diagram and the hard creative gates.
- `requirements.txt` — add `Pillow>=10`, `easyocr>=1.7`.

### Read Before Editing

- `pipeline/agentic/contracts.py` — current typed contracts (do not break).
- `pipeline/agentic/context_loader.py` — current ContextPack assembly.
- `pipeline/agentic/skill_registry.py` — current registry resolution.
- `pipeline/agentic/recall.py` — current recall bundle assembly.
- `pipeline/agentic/audit_log.py` — current audit log API.
- `pipeline/agentic/learning_loop.py` — current learning-event flow.
- `config/skill-systems.json` — carousel_jam definition.
- `config/agentic_context_manifest.json` — context pack source.
- `scripts/agentic_os.py` — current CLI shape.
- `scripts/create_illustration_carousel.py` — existing ad-hoc flow being replaced.
- `pipeline/stages/carousel_master_prompt.py` — existing prompt builder; lift its canonical fragments into rule files.
- `pipeline/stages/carousel_prompt_compiler.py` — existing compiler; will be called by the prompt_compile handler.
- `pipeline/stages/codex_builtin_image_generation.py` — existing handoff writer; will be called by proof/full_generation handlers.
- `pipeline/stages/carousel_quality.py` — existing quality stage; many of its checks migrate into `pipeline/agentic/checks/`.
- `output/carousels/2026-05-31/private-captions-fresh-a-story/` — most recent BLOCKED package; reference case.
- `output/carousels/2026-05-30/one-brain-cell-at-home/` — most recent rejected-raw-scene case; reference case.
- `output/carousels/2026-05-30/the-hand-that-stays/` — most recent PASS_WITH_NOTES case; reference case for the "what good looks like" target.

---

## Task 1 — Rule Consolidation

**Purpose:** Make every prompt, agent, skill, and check read the same constraint text. Kill the 15-place duplication of "no yellow" and similar rules.

**Files:**

- Create: `config/rules/palette.md`, `identity.md`, `on-image-text.md`, `brandmark.md`, `brand-zone.md`, `voice.md`, `golden-theme.md`, `story-selling.md`
- Create: `pipeline/agentic/rule_includes.py`
- Modify: `pipeline/agentic/context_loader.py`
- Create: `tests/test_rule_includes.py`

- [ ] **Step 1.1 — Extract canonical text into rule files**

For each concept below, read the existing duplicates and synthesize one canonical, short, hard-fails-first rule file. Each file is ~10-30 lines, no prose padding.

- `palette.md` — source duplicates: `config/references/a-story-illustration-master-prompt.md`, `config/references/a-story-premium-illustration-style-lock.md`, `config/skills/illustration-carousel-framework.md`, `memory/semantic/premium-illustration-style-lock.md`, `memory/working.md`, `pipeline/stages/carousel_master_prompt.py`, `pipeline/stages/carousel_quality.py`. Canonical text must contain: warm ivory / off-white paper, visible paper grain, allowed accent palette, **hard fails: yellow, mustard, sepia, parchment, tan, beige, cream-heavy, coffee-stained.**
- `identity.md` — Aachu (Anchal) 5'6", Zuv (Himanshu) 5'8". Identity-first faces from `identity_images/`. Wardrobe continuity per slide. Hard fails: Aachu reads tiny, Zuv reads oversized/lanky/chiseled/generic; faces drift across slides; identity-text-only without image refs.
- `on-image-text.md` — exact text from `slides.md`, placement in upper-middle negative space, handwritten typography, no typos, no model-invented text. Hard fail: any text in the image that is not in `slides.md` for that slide.
- `brandmark.md` — tiny low-contrast handwritten `@a.storyof.two` in bottom-right corner, always present, never absent, never centered.
- `brand-zone.md` — when `brief.md` has `brand:` field: product/brand name must be legible at phone-screen size, placed in a designated brand zone, must not occlude faces, disclosure language per Indian regulations.
- `voice.md` — warm, intimate, visual-first, conversational; no advice tone, no listicle vibe, no "5 things every couple should know."
- `golden-theme.md` — universal relationship truth → Aachu/Zuv specific proof → Zuv active care → tender thesis. 28/30 minimum on the rubric or the concept is repaired/rescored before proceeding.
- `story-selling.md` — Layer E 30-point rubric, 28/30 threshold, hard fails (no emotional obstacle, only a pretty moment, generic dynamic, Zuv passive, ending is a quote, copyrighted text).

- [ ] **Step 1.2 — Implement `{{rule:NAME}}` expander**

Create `pipeline/agentic/rule_includes.py`:

```python
from __future__ import annotations

import re
from functools import lru_cache
from pathlib import Path

RULE_INCLUDE_PATTERN = re.compile(r"\{\{rule:([a-z0-9_\-]+)\}\}")
RULES_DIR_NAME = "config/rules"


@lru_cache(maxsize=64)
def _load_rule(workspace_root: Path, name: str) -> str:
    path = workspace_root / RULES_DIR_NAME / f"{name}.md"
    if not path.exists():
        raise FileNotFoundError(f"Unknown rule include: {name} (looked at {path})")
    return path.read_text(encoding="utf-8").strip()


def expand_rule_includes(text: str, workspace_root: Path) -> str:
    def _sub(match: re.Match[str]) -> str:
        name = match.group(1)
        return _load_rule(workspace_root, name)
    return RULE_INCLUDE_PATTERN.sub(_sub, text)


def rule_names_referenced(text: str) -> list[str]:
    return sorted({match.group(1) for match in RULE_INCLUDE_PATTERN.finditer(text)})
```

- [ ] **Step 1.3 — Wire expander into `context_loader.py`**

In `pipeline/agentic/context_loader.py`, after reading a section's content and before token estimation, call `expand_rule_includes(content, workspace_root)`. This means every `ContextSection` delivered to a session has rule includes resolved.

- [ ] **Step 1.4 — Add tests**

Create `tests/test_rule_includes.py`:

```python
from __future__ import annotations

from pathlib import Path

from pipeline.agentic.rule_includes import (
    expand_rule_includes,
    rule_names_referenced,
)


def test_expander_replaces_known_rule(tmp_path: Path) -> None:
    (tmp_path / "config" / "rules").mkdir(parents=True)
    (tmp_path / "config" / "rules" / "palette.md").write_text(
        "PALETTE: warm ivory only.\nHARD FAIL: yellow, sepia, parchment.\n",
        encoding="utf-8",
    )
    text = "Before. {{rule:palette}} After."
    out = expand_rule_includes(text, tmp_path)
    assert "warm ivory only" in out
    assert "HARD FAIL: yellow" in out
    assert "{{rule:" not in out


def test_expander_raises_on_unknown_rule(tmp_path: Path) -> None:
    (tmp_path / "config" / "rules").mkdir(parents=True)
    text = "{{rule:does_not_exist}}"
    try:
        expand_rule_includes(text, tmp_path)
    except FileNotFoundError as exc:
        assert "does_not_exist" in str(exc)
    else:
        raise AssertionError("expected FileNotFoundError")


def test_rule_names_referenced_returns_sorted_unique() -> None:
    text = "{{rule:palette}} and {{rule:identity}} and {{rule:palette}}"
    assert rule_names_referenced(text) == ["identity", "palette"]
```

- [ ] **Step 1.5 — Verify**

```bash
venv/bin/python -m pytest tests/test_rule_includes.py -q
```

Expected: 3 passed.

---

## Task 2 — Typed Contracts Extension

**Purpose:** Give the runner a strongly-typed state model so every transition is auditable and every gate result has a schema.

**Files:**

- Modify: `pipeline/agentic/contracts.py`
- Create: `tests/test_workflow_state.py`

- [ ] **Step 2.1 — Add the new contracts**

Append to `pipeline/agentic/contracts.py`:

```python
class RepairBudget(BaseModel):
    max_retries: int = Field(ge=0, default=2)
    retries_used: int = Field(ge=0, default=0)

    def increment(self) -> "RepairBudget":
        return self.model_copy(update={"retries_used": self.retries_used + 1})

    @property
    def exhausted(self) -> bool:
        return self.retries_used >= self.max_retries


class RunArtifact(BaseModel):
    name: str
    path: str
    kind: Literal["input", "intermediate", "output"]
    written_at: str = Field(default_factory=utc_now_iso)


class PauseRequest(BaseModel):
    state: str
    reason: str
    awaiting: Literal[
        "concept_lock",
        "copy_lock",
        "visual_plan_lock",
        "proof_approval",
        "final_approval",
        "proof_repair_human",
    ]
    summary_path: str
    resume_hint: str


class WorkflowStateRecord(BaseModel):
    state: str
    entered_at: str = Field(default_factory=utc_now_iso)
    exited_at: str | None = None
    gates: list[WorkflowGate] = Field(default_factory=list)
    repair_budget: RepairBudget = Field(default_factory=RepairBudget)
    pause: PauseRequest | None = None


class WorkflowRun(BaseModel):
    run_id: str
    system: str
    package_dir: str
    current_state: str
    history: list[WorkflowStateRecord] = Field(default_factory=list)
    artifacts: list[RunArtifact] = Field(default_factory=list)
    started_at: str = Field(default_factory=utc_now_iso)
    completed_at: str | None = None

    def is_paused(self) -> bool:
        return bool(self.history and self.history[-1].pause is not None)

    def latest_pause(self) -> PauseRequest | None:
        return self.history[-1].pause if self.history else None
```

- [ ] **Step 2.2 — Add tests**

Create `tests/test_workflow_state.py`:

```python
from __future__ import annotations

from pipeline.agentic.contracts import (
    PauseRequest,
    RepairBudget,
    RunArtifact,
    WorkflowGate,
    WorkflowRun,
    WorkflowStateRecord,
)


def test_repair_budget_increments_and_exhausts() -> None:
    budget = RepairBudget(max_retries=2)
    assert budget.exhausted is False
    budget = budget.increment().increment()
    assert budget.exhausted is True


def test_workflow_run_detects_paused_state() -> None:
    run = WorkflowRun(
        run_id="r1",
        system="carousel_jam",
        package_dir="/tmp/pkg",
        current_state="awaiting_concept_lock",
        history=[
            WorkflowStateRecord(
                state="awaiting_concept_lock",
                pause=PauseRequest(
                    state="awaiting_concept_lock",
                    reason="three concept routes ready",
                    awaiting="concept_lock",
                    summary_path="/tmp/pkg/concept.md",
                    resume_hint="reply 'lock route N'",
                ),
            )
        ],
    )
    assert run.is_paused() is True
    pause = run.latest_pause()
    assert pause is not None and pause.awaiting == "concept_lock"


def test_workflow_state_record_collects_gates() -> None:
    record = WorkflowStateRecord(state="proof_generation")
    record.gates.append(WorkflowGate(name="palette", status="PASS"))
    record.gates.append(WorkflowGate(name="ocr_text", status="FAIL", reason="text drift"))
    assert [g.status for g in record.gates] == ["PASS", "FAIL"]


def test_run_artifact_records_path_and_kind() -> None:
    artifact = RunArtifact(name="slides.md", path="/tmp/pkg/slides.md", kind="output")
    assert artifact.kind == "output"
```

- [ ] **Step 2.3 — Verify**

```bash
venv/bin/python -m pytest tests/test_workflow_state.py -q
```

Expected: 4 passed.

---

## Task 3 — Deterministic Gates

**Purpose:** Replace LLM opinions about palette, on-image text, and image dimensions with measurements. A `WorkflowGate(name="palette", status="PASS")` should mean "we sampled pixels and they're within tolerance," not "an LLM judged the image."

**Files:**

- Create: `pipeline/agentic/checks/__init__.py`
- Create: `pipeline/agentic/checks/palette.py`
- Create: `pipeline/agentic/checks/ocr_text.py`
- Create: `pipeline/agentic/checks/image_size.py`
- Create: `pipeline/agentic/checks/prompt_constraints.py`
- Create: `tests/test_checks_palette.py`
- Create: `tests/test_checks_ocr_text.py`
- Create: `tests/test_checks_image_size.py`
- Create: `tests/test_checks_prompt_constraints.py`
- Modify: `requirements.txt`

- [ ] **Step 3.1 — Add dependencies**

Append to `requirements.txt`:

```
Pillow>=10
easyocr>=1.7
numpy>=1.26
```

Then:

```bash
venv/bin/pip install -r requirements.txt
```

- [ ] **Step 3.2 — Palette check**

Create `pipeline/agentic/checks/palette.py`:

```python
from __future__ import annotations

from pathlib import Path

from PIL import Image
import numpy as np

from pipeline.agentic.contracts import WorkflowGate

IVORY_TARGET_RGB = (245, 240, 228)
TOLERANCE = 18
SAMPLE_FRACTION = 0.04
YELLOW_BAND_HUE_RANGE = (35, 65)
YELLOW_BAND_SAT_MIN = 0.35
YELLOW_BAND_PIXEL_LIMIT = 0.06


def _hsv_yellow_fraction(arr: np.ndarray) -> float:
    rgb = arr[..., :3].astype(np.float32) / 255.0
    r, g, b = rgb[..., 0], rgb[..., 1], rgb[..., 2]
    mx = np.max(rgb, axis=-1)
    mn = np.min(rgb, axis=-1)
    diff = mx - mn
    hue = np.zeros_like(mx)
    mask = diff > 0
    hue[mask & (mx == r)] = ((g - b) / np.where(diff == 0, 1, diff))[mask & (mx == r)] % 6
    hue[mask & (mx == g)] = ((b - r) / np.where(diff == 0, 1, diff) + 2)[mask & (mx == g)]
    hue[mask & (mx == b)] = ((r - g) / np.where(diff == 0, 1, diff) + 4)[mask & (mx == b)]
    hue = (hue * 60.0) % 360.0
    sat = np.where(mx > 0, diff / np.where(mx == 0, 1, mx), 0)
    yellow_mask = (
        (hue >= YELLOW_BAND_HUE_RANGE[0])
        & (hue <= YELLOW_BAND_HUE_RANGE[1])
        & (sat >= YELLOW_BAND_SAT_MIN)
    )
    return float(yellow_mask.mean())


def check_palette(image_path: Path) -> WorkflowGate:
    if not image_path.exists():
        return WorkflowGate(
            name="palette", status="FAIL", reason=f"image missing: {image_path}"
        )
    img = Image.open(image_path).convert("RGB")
    arr = np.array(img)
    sample = arr.reshape(-1, 3)
    if sample.shape[0] > 200_000:
        idx = np.random.default_rng(0).choice(
            sample.shape[0], size=int(sample.shape[0] * SAMPLE_FRACTION), replace=False
        )
        sample = sample[idx]
    median = np.median(sample, axis=0)
    deltas = np.abs(median - np.array(IVORY_TARGET_RGB))
    median_ok = bool((deltas <= TOLERANCE).all())
    yellow_fraction = _hsv_yellow_fraction(arr)
    yellow_ok = yellow_fraction <= YELLOW_BAND_PIXEL_LIMIT
    if median_ok and yellow_ok:
        return WorkflowGate(
            name="palette",
            status="PASS",
            reason=(
                f"median RGB={median.tolist()} within tolerance; "
                f"yellow_fraction={yellow_fraction:.3f}"
            ),
            evidence_paths=[str(image_path)],
        )
    reasons = []
    if not median_ok:
        reasons.append(f"median RGB={median.tolist()} exceeds ±{TOLERANCE} from ivory")
    if not yellow_ok:
        reasons.append(
            f"yellow_fraction={yellow_fraction:.3f} above limit {YELLOW_BAND_PIXEL_LIMIT}"
        )
    return WorkflowGate(
        name="palette", status="FAIL", reason="; ".join(reasons),
        evidence_paths=[str(image_path)],
    )
```

- [ ] **Step 3.3 — OCR text match**

Create `pipeline/agentic/checks/ocr_text.py`:

```python
from __future__ import annotations

import re
from functools import lru_cache
from pathlib import Path

from pipeline.agentic.contracts import WorkflowGate


@lru_cache(maxsize=1)
def _reader():
    import easyocr
    return easyocr.Reader(["en"], gpu=False, verbose=False)


def _normalize(text: str) -> str:
    return re.sub(r"\s+", " ", text.lower().strip())


def check_ocr_text(image_path: Path, expected_text: str) -> WorkflowGate:
    if not image_path.exists():
        return WorkflowGate(
            name="ocr_text", status="FAIL", reason=f"image missing: {image_path}"
        )
    reader = _reader()
    detections = reader.readtext(str(image_path), detail=0)
    detected = _normalize(" ".join(detections))
    expected = _normalize(expected_text)
    if not expected:
        return WorkflowGate(name="ocr_text", status="PASS", reason="no expected text")
    if expected in detected:
        return WorkflowGate(
            name="ocr_text",
            status="PASS",
            reason=f"expected text found verbatim",
            evidence_paths=[str(image_path)],
        )
    return WorkflowGate(
        name="ocr_text",
        status="FAIL",
        reason=f"expected '{expected_text}' not found; detected: '{detected[:120]}'",
        evidence_paths=[str(image_path)],
    )
```

- [ ] **Step 3.4 — Image size check**

Create `pipeline/agentic/checks/image_size.py`:

```python
from __future__ import annotations

from pathlib import Path

from PIL import Image

from pipeline.agentic.contracts import WorkflowGate

ASPECT_TARGETS = {
    "4:5": (4 / 5, 0.01),
    "9:16": (9 / 16, 0.01),
}
MIN_DIMENSIONS = {
    "4:5": (1080, 1350),
    "9:16": (1080, 1920),
}


def check_image_size(image_path: Path, aspect: str) -> WorkflowGate:
    if aspect not in ASPECT_TARGETS:
        return WorkflowGate(
            name="image_size", status="FAIL", reason=f"unknown aspect: {aspect}"
        )
    if not image_path.exists():
        return WorkflowGate(
            name="image_size", status="FAIL", reason=f"image missing: {image_path}"
        )
    target_ratio, tol = ASPECT_TARGETS[aspect]
    min_w, min_h = MIN_DIMENSIONS[aspect]
    with Image.open(image_path) as img:
        w, h = img.size
    actual_ratio = w / h
    if abs(actual_ratio - target_ratio) > tol:
        return WorkflowGate(
            name="image_size",
            status="FAIL",
            reason=f"{w}x{h} ratio {actual_ratio:.3f} != target {target_ratio:.3f} ±{tol}",
            evidence_paths=[str(image_path)],
        )
    if w < min_w or h < min_h:
        return WorkflowGate(
            name="image_size",
            status="FAIL",
            reason=f"{w}x{h} below minimum {min_w}x{min_h}",
            evidence_paths=[str(image_path)],
        )
    return WorkflowGate(
        name="image_size",
        status="PASS",
        reason=f"{w}x{h} matches {aspect}",
        evidence_paths=[str(image_path)],
    )
```

- [ ] **Step 3.5 — Prompt constraints check**

Create `pipeline/agentic/checks/prompt_constraints.py`:

```python
from __future__ import annotations

from pathlib import Path

from pipeline.agentic.contracts import WorkflowGate

REQUIRED_FRAGMENTS = (
    "warm ivory",
    "HARD FAIL: yellow",
    "ON-IMAGE TEXT",
    "@a.storyof.two",
)


def check_prompt_constraints(prompt_path: Path) -> WorkflowGate:
    if not prompt_path.exists():
        return WorkflowGate(
            name="prompt_constraints", status="FAIL",
            reason=f"prompt missing: {prompt_path}",
        )
    text = prompt_path.read_text(encoding="utf-8")
    missing = [fragment for fragment in REQUIRED_FRAGMENTS if fragment not in text]
    if missing:
        return WorkflowGate(
            name="prompt_constraints",
            status="FAIL",
            reason=f"missing required fragments: {missing}",
            evidence_paths=[str(prompt_path)],
        )
    return WorkflowGate(
        name="prompt_constraints",
        status="PASS",
        reason="all required fragments present",
        evidence_paths=[str(prompt_path)],
    )
```

- [ ] **Step 3.6 — Add tests for each check**

Create `tests/test_checks_palette.py`, `tests/test_checks_ocr_text.py`, `tests/test_checks_image_size.py`, `tests/test_checks_prompt_constraints.py`. Each uses Pillow to synthesize fixture images in tmp_path so tests don't depend on real carousel files.

Example shape for palette:

```python
def test_palette_passes_for_ivory_image(tmp_path):
    img = Image.new("RGB", (256, 256), color=(245, 240, 228))
    path = tmp_path / "ivory.png"
    img.save(path)
    gate = check_palette(path)
    assert gate.status == "PASS"


def test_palette_fails_for_yellow_image(tmp_path):
    img = Image.new("RGB", (256, 256), color=(240, 220, 90))
    path = tmp_path / "yellow.png"
    img.save(path)
    gate = check_palette(path)
    assert gate.status == "FAIL"
    assert "yellow" in gate.reason.lower()
```

Same shape for OCR (use Pillow + ImageDraw + a system font to render expected text), image_size (create PIL.Image at exact 1080×1350 and 1080×1920), prompt_constraints (write text files with and without required fragments).

- [ ] **Step 3.7 — Verify**

```bash
venv/bin/python -m pytest tests/test_checks_palette.py tests/test_checks_ocr_text.py tests/test_checks_image_size.py tests/test_checks_prompt_constraints.py -q
```

Expected: all passed.

---

## Task 4 — Workflow Runner Core

**Purpose:** Drive the carousel state machine with typed transitions, pause-resume support, and audit-logged transitions. This is the executor the existing read-only `agentic_os.py` is missing.

**Files:**

- Create: `pipeline/agentic/workflow_runner.py`
- Create: `pipeline/agentic/workflows/carousel_jam/states.py`
- Modify: `pipeline/agentic/audit_log.py`
- Create: `tests/test_workflow_runner_carousel_jam.py` (initial fixture-driven tests; expanded after Task 5)

- [ ] **Step 4.1 — Define state enum and transition table**

Create `pipeline/agentic/workflows/carousel_jam/states.py`:

```python
from __future__ import annotations

from enum import Enum


class CarouselJamState(str, Enum):
    SESSION_START = "session_start"
    RAW_SCENE_LOCK = "raw_scene_lock"
    CONCEPT_GENERATION = "concept_generation"
    AWAITING_CONCEPT_LOCK = "awaiting_concept_lock"
    COPY_GENERATION = "copy_generation"
    AWAITING_COPY_LOCK = "awaiting_copy_lock"
    VISUAL_PLAN = "visual_plan"
    AWAITING_VISUAL_PLAN_LOCK = "awaiting_visual_plan_lock"
    PROMPT_COMPILE = "prompt_compile"
    PROOF_GENERATION = "proof_generation"
    AWAITING_PROOF_APPROVAL = "awaiting_proof_approval"
    AWAITING_PROOF_REPAIR_HUMAN = "awaiting_proof_repair_human"
    FULL_GENERATION = "full_generation"
    AWAITING_FINAL_APPROVAL = "awaiting_final_approval"
    CLOSEOUT = "closeout"
    DONE = "done"


# Forward edges only; repair edges are handled imperatively in handlers.
DEFAULT_TRANSITIONS: dict[CarouselJamState, CarouselJamState] = {
    CarouselJamState.SESSION_START: CarouselJamState.RAW_SCENE_LOCK,
    CarouselJamState.RAW_SCENE_LOCK: CarouselJamState.CONCEPT_GENERATION,
    CarouselJamState.CONCEPT_GENERATION: CarouselJamState.AWAITING_CONCEPT_LOCK,
    CarouselJamState.AWAITING_CONCEPT_LOCK: CarouselJamState.COPY_GENERATION,
    CarouselJamState.COPY_GENERATION: CarouselJamState.AWAITING_COPY_LOCK,
    CarouselJamState.AWAITING_COPY_LOCK: CarouselJamState.VISUAL_PLAN,
    CarouselJamState.VISUAL_PLAN: CarouselJamState.AWAITING_VISUAL_PLAN_LOCK,
    CarouselJamState.AWAITING_VISUAL_PLAN_LOCK: CarouselJamState.PROMPT_COMPILE,
    CarouselJamState.PROMPT_COMPILE: CarouselJamState.PROOF_GENERATION,
    CarouselJamState.PROOF_GENERATION: CarouselJamState.AWAITING_PROOF_APPROVAL,
    CarouselJamState.AWAITING_PROOF_APPROVAL: CarouselJamState.FULL_GENERATION,
    CarouselJamState.FULL_GENERATION: CarouselJamState.AWAITING_FINAL_APPROVAL,
    CarouselJamState.AWAITING_FINAL_APPROVAL: CarouselJamState.CLOSEOUT,
    CarouselJamState.CLOSEOUT: CarouselJamState.DONE,
}
```

- [ ] **Step 4.2 — Implement the runner**

Create `pipeline/agentic/workflow_runner.py`:

```python
from __future__ import annotations

import json
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Protocol

from pipeline.agentic.audit_log import append_audit_event
from pipeline.agentic.contracts import (
    AuditEvent,
    PauseRequest,
    RunArtifact,
    WorkflowGate,
    WorkflowRun,
    WorkflowStateRecord,
)


@dataclass
class HandlerResult:
    gates: list[WorkflowGate]
    artifacts: list[RunArtifact]
    pause: PauseRequest | None = None
    repair_back_to: str | None = None  # state name to retry; None = advance


class StateHandler(Protocol):
    def __call__(self, run: WorkflowRun, workspace_root: Path) -> HandlerResult: ...


class WorkflowRunner:
    def __init__(
        self,
        workspace_root: Path,
        runs_root: Path,
        handlers: dict[str, StateHandler],
        transitions: dict[str, str],
        terminal_state: str = "done",
    ) -> None:
        self.workspace_root = workspace_root
        self.runs_root = runs_root
        self.handlers = handlers
        self.transitions = transitions
        self.terminal_state = terminal_state

    def start(self, system: str, package_dir: Path, initial_state: str) -> WorkflowRun:
        run_id = uuid.uuid4().hex[:12]
        run = WorkflowRun(
            run_id=run_id,
            system=system,
            package_dir=str(package_dir),
            current_state=initial_state,
        )
        self._persist(run)
        return self.advance(run)

    def resume(self, run_id: str, human_input: dict | None = None) -> WorkflowRun:
        run = self._load(run_id)
        if not run.is_paused():
            raise RuntimeError(f"run {run_id} is not paused (current_state={run.current_state})")
        last = run.history[-1]
        last.exited_at = self._now()
        last.pause = None
        next_state = self.transitions[run.current_state]
        run.current_state = next_state
        if human_input is not None:
            self._record_human_input(run, human_input)
        self._persist(run)
        return self.advance(run)

    def advance(self, run: WorkflowRun) -> WorkflowRun:
        while True:
            if run.current_state == self.terminal_state:
                run.completed_at = self._now()
                self._persist(run)
                return run
            handler = self.handlers.get(run.current_state)
            if handler is None:
                raise KeyError(f"no handler for state {run.current_state}")
            record = WorkflowStateRecord(state=run.current_state)
            run.history.append(record)
            self._persist(run)
            result = handler(run, self.workspace_root)
            record.gates = result.gates
            for artifact in result.artifacts:
                run.artifacts.append(artifact)
            if result.pause is not None:
                record.pause = result.pause
                self._audit(run, "pause", record.pause.reason, [record.pause.summary_path])
                self._persist(run)
                return run
            if any(gate.status in {"FAIL", "STOP"} for gate in result.gates):
                if record.repair_budget.exhausted:
                    self._audit(run, "halt", "repair budget exhausted", [])
                    record.pause = PauseRequest(
                        state=run.current_state,
                        reason="repair budget exhausted",
                        awaiting="proof_repair_human",
                        summary_path=str(Path(run.package_dir) / "gates.json"),
                        resume_hint="inspect gates.json and provide repair direction",
                    )
                    self._persist(run)
                    return run
                record.repair_budget = record.repair_budget.increment()
                self._audit(run, "repair", "gate failure; retrying", [])
                record.exited_at = self._now()
                self._persist(run)
                continue  # re-run the same handler
            if result.repair_back_to is not None:
                run.current_state = result.repair_back_to
            else:
                run.current_state = self.transitions[run.current_state]
            record.exited_at = self._now()
            self._persist(run)

    def _persist(self, run: WorkflowRun) -> None:
        run_dir = self.runs_root / run.run_id
        run_dir.mkdir(parents=True, exist_ok=True)
        (run_dir / "state.json").write_text(
            json.dumps(run.model_dump(), indent=2, ensure_ascii=False),
            encoding="utf-8",
        )

    def _load(self, run_id: str) -> WorkflowRun:
        path = self.runs_root / run_id / "state.json"
        return WorkflowRun.model_validate_json(path.read_text(encoding="utf-8"))

    def _audit(self, run: WorkflowRun, action: str, rationale: str, evidence: list[str]) -> None:
        event = AuditEvent(
            event_id=uuid.uuid4().hex[:12],
            actor="workflow_runner",
            action=action,
            target_path=run.package_dir,
            rationale=rationale,
            evidence_paths=evidence,
        )
        append_audit_event(self.runs_root / run.run_id, event)

    def _record_human_input(self, run: WorkflowRun, payload: dict) -> None:
        path = self.runs_root / run.run_id / "human-input.jsonl"
        with path.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(payload, ensure_ascii=False) + "\n")

    @staticmethod
    def _now() -> str:
        from datetime import datetime, timezone
        return datetime.now(timezone.utc).replace(microsecond=0).isoformat()
```

- [ ] **Step 4.3 — Extend `audit_log.py` for per-run JSONL**

In `pipeline/agentic/audit_log.py`, add:

```python
def append_audit_event(run_dir: Path, event: AuditEvent) -> None:
    run_dir.mkdir(parents=True, exist_ok=True)
    path = run_dir / "audit.log.jsonl"
    with path.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(event.model_dump(), ensure_ascii=False) + "\n")
```

- [ ] **Step 4.4 — Runner unit tests with stub handlers**

Create `tests/test_workflow_runner_carousel_jam.py` with stub handlers so the runner can be exercised without LLM calls or image generation:

```python
def test_runner_pauses_then_resumes(tmp_path):
    handlers = {
        "s_start": lambda run, root: HandlerResult(
            gates=[WorkflowGate(name="ok", status="PASS")],
            artifacts=[],
        ),
        "s_pause": lambda run, root: HandlerResult(
            gates=[],
            artifacts=[],
            pause=PauseRequest(
                state="s_pause",
                reason="awaiting input",
                awaiting="concept_lock",
                summary_path=str(tmp_path / "summary.md"),
                resume_hint="reply lock",
            ),
        ),
        "s_done": lambda run, root: HandlerResult(
            gates=[WorkflowGate(name="ok", status="PASS")],
            artifacts=[],
        ),
    }
    transitions = {"s_start": "s_pause", "s_pause": "s_done", "s_done": "done"}
    runner = WorkflowRunner(
        workspace_root=tmp_path,
        runs_root=tmp_path / "runs",
        handlers=handlers,
        transitions=transitions,
    )
    run = runner.start(system="test", package_dir=tmp_path / "pkg", initial_state="s_start")
    assert run.is_paused()
    assert run.latest_pause().awaiting == "concept_lock"
    resumed = runner.resume(run.run_id, human_input={"choice": "lock"})
    assert resumed.current_state == "done"
    assert resumed.completed_at is not None
```

Add tests for: repair-budget exhaustion path, retry-on-gate-FAIL path, audit log JSONL contents after a paused-then-resumed run.

- [ ] **Step 4.5 — Verify**

```bash
venv/bin/python -m pytest tests/test_workflow_runner_carousel_jam.py -q
```

Expected: all passed.

---

## Task 5 — Per-State Handlers (carousel_jam)

**Purpose:** Implement each state's handler with typed input/output. Each handler reads run state + workspace artifacts, invokes agents or deterministic checks, writes its artifact, and returns a `HandlerResult`.

**Files:**

- Create: `pipeline/agentic/workflows/carousel_jam/io_schemas.py`
- Create: `pipeline/agentic/workflows/carousel_jam/handlers/*.py` (9 files)

**Architecture rule (do not break):** A handler is a pure function over `(WorkflowRun, workspace_root) → HandlerResult`. Side effects to the package directory are allowed (writing concept.md, slides.md, etc.). Side effects to runner state are not — those are managed by the runner.

- [ ] **Step 5.1 — Define I/O schemas**

Create `pipeline/agentic/workflows/carousel_jam/io_schemas.py`:

```python
from __future__ import annotations

from pydantic import BaseModel, Field


class CarouselBrief(BaseModel):
    story: str
    title: str | None = None
    slide_count: int = Field(ge=4, le=8, default=5)
    image_paths: list[str] = Field(default_factory=list)
    identity_image_paths: list[str] = Field(default_factory=list)
    brand: str | None = None


class ConceptRoute(BaseModel):
    id: str
    title: str
    universal_truth: str
    aachu_zuv_proof: str
    zuv_active_care: str
    tender_thesis: str
    golden_theme_score: int = Field(ge=0, le=30)
    story_selling_score: int = Field(ge=0, le=30)


class ConceptPackage(BaseModel):
    routes: list[ConceptRoute]
    chosen_route_id: str | None = None


class SlideCopy(BaseModel):
    slide_number: int = Field(ge=1, le=8)
    on_image_text: str
    caption_fragment: str | None = None


class CopyPackage(BaseModel):
    slides: list[SlideCopy]


class SlideVisualPlan(BaseModel):
    slide_number: int = Field(ge=1, le=8)
    scene_summary: str
    composition: str
    wardrobe: str
    text_placement: str
    photo_evidence_paths: list[str] = Field(default_factory=list)


class VisualPlanPackage(BaseModel):
    slides: list[SlideVisualPlan]
```

- [ ] **Step 5.2 — Implement handlers**

For each state, write the handler. Shape (illustrative; abridged):

```python
# pipeline/agentic/workflows/carousel_jam/handlers/concept_generation.py
from __future__ import annotations

from pathlib import Path

from pipeline.agentic.contracts import RunArtifact, WorkflowGate
from pipeline.agentic.workflow_runner import HandlerResult
from pipeline.agentic.workflows.carousel_jam.io_schemas import (
    CarouselBrief, ConceptPackage, ConceptRoute,
)


def handle_concept_generation(run, workspace_root: Path) -> HandlerResult:
    package = Path(run.package_dir)
    brief = CarouselBrief.model_validate_json((package / "brief.json").read_text(encoding="utf-8"))
    routes = _generate_routes(brief, workspace_root)  # invokes agents with rule includes
    package_obj = ConceptPackage(routes=routes)
    (package / "concept.json").write_text(package_obj.model_dump_json(indent=2), encoding="utf-8")
    (package / "concept.md").write_text(_render_concept_md(package_obj), encoding="utf-8")
    gate = WorkflowGate(
        name="at_least_one_concept_score_28",
        status="PASS" if any(r.golden_theme_score >= 28 for r in routes) else "FAIL",
        reason=f"max score = {max(r.golden_theme_score for r in routes)}",
    )
    return HandlerResult(
        gates=[gate],
        artifacts=[
            RunArtifact(name="concept.json", path=str(package / "concept.json"), kind="output"),
            RunArtifact(name="concept.md", path=str(package / "concept.md"), kind="output"),
        ],
    )
```

The `_generate_routes` helper invokes the persona-prompted LLM with: brief, rule includes from `config/rules/voice.md` + `golden-theme.md` + `story-selling.md`, and the relevant recall bundle. Returns 3 `ConceptRoute` objects.

Similar shape for each state. Notably:

- `awaiting_*` handlers ONLY write the summary file and return a `PauseRequest`. No agent invocation.
- `prompt_compile` is deterministic — reads `slides.json`, `visual-plan.json`, rule includes, identity refs, calls `pipeline/stages/carousel_prompt_compiler.compile_image_prompt`, writes `prompts/slide-NN.txt`, then runs `check_prompt_constraints` per file.
- `proof_generation` calls the existing `codex_builtin_image_generation` to prepare the handoff for slide 1, then on next session entry (or via in-session image gen) checks the produced PNG with palette + OCR + size + face-continuity. If any FAIL and budget remains, the runner retries.
- `full_generation` mirrors proof_generation but for slides 2..N and both aspects.
- `closeout` runs existing `scripts/wiki_health.py --write --fix-index` and `scripts/autopublish.py`.

- [ ] **Step 5.3 — Register handlers**

Create `pipeline/agentic/workflows/carousel_jam/__init__.py`:

```python
from pipeline.agentic.workflows.carousel_jam.states import (
    CarouselJamState, DEFAULT_TRANSITIONS,
)
from pipeline.agentic.workflows.carousel_jam.handlers.session_start import handle_session_start
from pipeline.agentic.workflows.carousel_jam.handlers.raw_scene_lock import handle_raw_scene_lock
# ... etc

HANDLERS = {
    CarouselJamState.SESSION_START.value: handle_session_start,
    CarouselJamState.RAW_SCENE_LOCK.value: handle_raw_scene_lock,
    # ... etc
}

TRANSITIONS = {state.value: target.value for state, target in DEFAULT_TRANSITIONS.items()}
```

- [ ] **Step 5.4 — Integration test with fixtures**

Extend `tests/test_workflow_runner_carousel_jam.py` with a fixture-driven end-to-end test that pre-creates `brief.json`, stubs LLM calls (monkeypatched to return canned `ConceptRoute`/`SlideCopy` lists), and asserts the runner reaches `AWAITING_PROOF_APPROVAL` with all expected artifacts written.

- [ ] **Step 5.5 — Verify**

```bash
venv/bin/python -m pytest tests/test_workflow_runner_carousel_jam.py -q
```

Expected: all passed.

---

## Task 6 — CLI Activation

**Purpose:** Expose the runner via the existing `agentic_os.py` CLI so the user (and any session) drives carousels through one entry point.

**Files:**

- Modify: `scripts/agentic_os.py`
- Create: `tests/test_agentic_os_run_system_cli.py`

- [ ] **Step 6.1 — Add subcommands**

Extend the parser in `scripts/agentic_os.py`:

```python
run_system = sub.add_parser("run-system")
run_system.add_argument("name", choices=["carousel_jam"])
run_system.add_argument("--story", required=True)
run_system.add_argument("--title")
run_system.add_argument("--image", action="append", default=[])
run_system.add_argument("--identity-image", action="append", default=[])
run_system.add_argument("--slide-count", type=int, default=5)
run_system.add_argument("--brand")

resume = sub.add_parser("resume")
resume.add_argument("run_id")
resume.add_argument("--input-file", type=Path,
                    help="JSON file with human input payload for the paused state")

status = sub.add_parser("status")
status.add_argument("run_id")

runs = sub.add_parser("runs")
runs.add_argument("--limit", type=int, default=20)

audit = sub.add_parser("audit-packages")
audit.add_argument("--root", type=Path, default=Path("output/carousels"))
```

- [ ] **Step 6.2 — Wire commands to the runner**

In `main()`:

```python
if args.command == "run-system":
    package_dir = _allocate_package_dir(root, args.story, args.title)
    _write_brief(package_dir, args)
    runner = _build_runner(root)
    run = runner.start(
        system=args.name,
        package_dir=package_dir,
        initial_state="session_start",
    )
    print_json(_summarize_run(run))
elif args.command == "resume":
    runner = _build_runner(root)
    payload = json.loads(args.input_file.read_text(encoding="utf-8")) if args.input_file else None
    run = runner.resume(args.run_id, human_input=payload)
    print_json(_summarize_run(run))
elif args.command == "status":
    run = _load_run(root, args.run_id)
    print_json(_summarize_run(run))
elif args.command == "runs":
    print_json(_recent_runs(root, args.limit))
elif args.command == "audit-packages":
    from scripts.audit_packages import audit_packages
    print_json(audit_packages(args.root))
```

- [ ] **Step 6.3 — CLI tests**

Create `tests/test_agentic_os_run_system_cli.py`. Use `subprocess.run([sys.executable, "scripts/agentic_os.py", "run-system", "carousel_jam", "--story", "..."])` with monkeypatched handlers so the test runs offline.

Verify:
- `run-system` returns JSON with `run_id`, `current_state`, `is_paused` after the first pause.
- `resume` advances past the pause.
- `status` returns the same shape without mutating state.
- `runs` lists run summaries.

- [ ] **Step 6.4 — Verify**

```bash
venv/bin/python -m pytest tests/test_agentic_os_run_system_cli.py -q
```

Expected: all passed.

---

## Task 7 — Package Writer Reduction

**Purpose:** Reduce the per-carousel package from 25 free-form LLM-written JSON files to 8 first-class artifacts + 3 derived files computed from runner state.

**Files:**

- Create: `pipeline/agentic/package_writer.py`
- Create: `tests/test_package_writer_reduced.py`

- [ ] **Step 7.1 — Define the first-class artifact set**

A carousel package after this task contains exactly:

```
output/carousels/YYYY-MM-DD/<slug>/
├── brief.json              # input (slug, story, images, brand)
├── brief.md                # human-editable rendered view of brief.json
├── concept.json + .md      # ConceptPackage typed
├── slides.json + .md       # CopyPackage typed
├── visual-plan.json + .md  # VisualPlanPackage typed
├── prompts/slide-NN.txt    # compiled prompts
├── proof/slide-01.png      # one-slide proof
├── final/4x5/slide-NN.png  # native 4:5
├── final/9x16/slide-NN.png # native 9:16
└── checks.json             # CheckResults — all WorkflowGate outputs for image checks

# Derived from runner state (NOT written by LLM agents):
output/carousels/YYYY-MM-DD/<slug>/.derived/
├── state.md                # human-readable view of memory/agentic/.../state.json
├── audit.md                # human-readable view of audit.log.jsonl
└── gates.md                # human-readable view of all gates
```

The `.derived/` views are regenerated by `package_writer.refresh_derived(run)` on every state transition.

- [ ] **Step 7.2 — Implement writer**

Create `pipeline/agentic/package_writer.py` with `refresh_derived(run, package_dir)` that renders Markdown views from `WorkflowRun`. Each derived file has a stable, scannable format so the creator can read package state quickly.

- [ ] **Step 7.3 — Migrate handlers to use writer**

Each handler that writes a package artifact uses helpers from `package_writer.py` (`write_concept`, `write_copy`, etc.). No handler writes free-form JSON.

- [ ] **Step 7.4 — Tests**

Create `tests/test_package_writer_reduced.py`. Assert that a finished `WorkflowRun` rendered to a package directory produces exactly the artifacts listed above and nothing else. Assert derived views regenerate idempotently.

- [ ] **Step 7.5 — Verify**

```bash
venv/bin/python -m pytest tests/test_package_writer_reduced.py -q
```

Expected: all passed.

---

## Task 8 — Real Carousel Dry Run

**Purpose:** Take one real carousel end-to-end through the runner. Compare against a recent old-flow carousel for latency, artifact count, and gate fidelity.

**Files:**

- Create: `output/reports/2026-05-31-agentic-runner-dry-run.md`

- [ ] **Step 8.1 — Choose a real story**

Pick a story the creator wants next. Document the brief.

- [ ] **Step 8.2 — Run**

```bash
venv/bin/python scripts/agentic_os.py run-system carousel_jam \
  --story "<...>" \
  --image <path> --identity-image <path>
```

Hit all five human pauses. Resume at each:

```bash
venv/bin/python scripts/agentic_os.py resume <run-id> --input-file decision.json
```

- [ ] **Step 8.3 — Compare to a recent old-flow run**

Pick `output/carousels/2026-05-31/he-didn-t-marry-organized` (most recent old-flow). Build a comparison table in the report:

| Metric | Old flow | New runner |
|---|---:|---:|
| Wall-clock time, brief → publishable | | |
| Number of artifacts in package | | |
| Number of LLM agent calls | | |
| Number of deterministic gate calls | | |
| Number of explicit human pauses | | |
| Palette gate result | n/a | |
| OCR text-match gate result | n/a | |
| Final size gate result (4:5 + 9:16) | n/a | |
| Repair iterations on slide 1 | | |

- [ ] **Step 8.4 — Capture learning**

If the runner surfaced anything surprising (a missing rule, an awkward pause hint, a gate that mis-fired), capture it:

```bash
venv/bin/python scripts/agentic_os.py capture-learning \
  --source dry-run --summary "..." --evidence output/reports/2026-05-31-agentic-runner-dry-run.md
```

- [ ] **Step 8.5 — Decide go/no-go**

The dry run is a go if **all five** of these are true:
- The runner reached `done` without manual intervention beyond the five expected pauses.
- Wall-clock time is < 50% of the old-flow comparison run.
- Palette gate FAILED at least once during proof generation if the model produced any yellow drift (proving the gate works), or PASSED first try (proving the prompt encoded the rule).
- OCR gate matched expected text without manual approval.
- The creator approves the final 4:5 + 9:16 set without "this looks like the old failures" critique.

If any of the five fails, file repair tasks and rerun the dry run before proceeding.

---

## Task 9 — Legacy Wrapper & Skill Dedup

**Purpose:** Make the existing CLI entry point use the runner; remove rule duplication from skill files.

**Files:**

- Modify: `scripts/create_illustration_carousel.py`
- Modify: every file in `config/skills/`

- [ ] **Step 9.1 — Replace `create_illustration_carousel.py` with thin wrapper**

```python
#!/usr/bin/env python3
"""Thin compatibility wrapper. Forwards to agentic_os.py run-system carousel_jam."""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main(argv: list[str]) -> int:
    forwarded = ["venv/bin/python", str(ROOT / "scripts" / "agentic_os.py"),
                 "run-system", "carousel_jam"] + argv
    return subprocess.call(forwarded, cwd=ROOT)


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
```

- [ ] **Step 9.2 — Skill dedup**

For each file in `config/skills/`, find inline duplications of palette/identity/on-image-text/brandmark/voice/golden-theme/story-selling rules and replace them with `{{rule:NAME}}` includes. The skill file keeps its composition recipe, loses its rule duplication.

- [ ] **Step 9.3 — Verify**

```bash
venv/bin/python -m pytest -q
grep -rn "yellow\|sepia\|parchment" config/skills/ memory/semantic/  # should return 0 or very few results
```

Any remaining mention should be either an include marker or commentary about the rule.

---

## Task 10 — Existing Package Audit

**Purpose:** Produce an honest triage report for all 67 existing carousels using the new deterministic gates.

**Files:**

- Create: `scripts/audit_packages.py`
- Create: `output/reports/2026-05-31-package-audit-via-new-gates.md`

- [ ] **Step 10.1 — Implement audit script**

`scripts/audit_packages.py`:

```python
from __future__ import annotations

from pathlib import Path

from pipeline.agentic.checks.image_size import check_image_size
from pipeline.agentic.checks.palette import check_palette


def audit_packages(root: Path) -> list[dict]:
    results = []
    for package in sorted(root.glob("*/*/")):
        report = {"package": str(package), "gates": []}
        for slide in sorted(package.glob("final/slide-*.png")):
            report["gates"].append(
                {"slide": slide.name, **check_palette(slide).model_dump()}
            )
            report["gates"].append(
                {"slide": slide.name, **check_image_size(slide, "4:5").model_dump()}
            )
        for slide in sorted(package.glob("final-reels-stories/slide-*.png")):
            report["gates"].append(
                {"slide": slide.name, **check_image_size(slide, "9:16").model_dump()}
            )
        report["palette_pass_rate"] = _pass_rate(report["gates"], "palette")
        report["size_pass_rate"] = _pass_rate(report["gates"], "image_size")
        results.append(report)
    return results
```

- [ ] **Step 10.2 — Run and write report**

```bash
venv/bin/python scripts/agentic_os.py audit-packages > tmp/audit.json
```

Then write `output/reports/2026-05-31-package-audit-via-new-gates.md` summarizing:

- Total packages audited
- Packages where every slide passes palette + size
- Packages where palette FAILS on ≥1 slide
- Packages where size FAILS on ≥1 slide
- Packages with no final images at all
- A board with the top 10 most-failed packages

- [ ] **Step 10.3 — Decide retention**

For each package not currently linked from `wiki/index.md`:
- If audit gives a pass rate ≥ 80% → keep.
- Otherwise → move to `archive/2026-05-pre-restructure-carousels/` in a single commit.

---

## Task 11 — Learning Capture Wiring

**Purpose:** Make the runner produce draft `LearningProposal` entries when human pause repair notes recur, so rules tighten over time without manual edits.

**Files:**

- Modify: `pipeline/agentic/learning_loop.py`
- Modify: handlers in `pipeline/agentic/workflows/carousel_jam/handlers/` that accept human input

- [ ] **Step 11.1 — Record repair notes**

When `WorkflowRunner.resume` receives `human_input` and the input contains a `repair_note` field, write a `LearningEvent` via `learning_loop.capture_learning_event`. The event's `summary` is the repair note; `evidence_paths` includes the run's `state.json`.

- [ ] **Step 11.2 — Detect recurring patterns**

Add to `learning_loop.py`:

```python
def recurring_repair_summaries(workspace_root: Path, min_occurrences: int = 3) -> list[str]:
    """Return repair summaries that have occurred ≥min_occurrences across runs."""
    # scans memory/agentic/workflow-runs/*/audit.log.jsonl
    ...
```

When a summary is recurring, the runner emits a draft `LearningProposal` targeting the relevant rule file (e.g. `config/rules/palette.md`) and writes the proposal under `memory/heal/proposals/`. Proposals stay draft until `evaluate_learning_proposal` returns PASS and a human reviewer approves.

- [ ] **Step 11.3 — Test**

Add a test that simulates three runs each emitting the same repair note ("yellow on slide 3 again") and asserts a proposal is created targeting `config/rules/palette.md` with the note in its rationale.

---

## Recommended Execution Order

### Fastest path to a working end-to-end run

1. **Sessions A, B, C in parallel** (P0, no deps): rule consolidation, typed contracts, deterministic gates.
2. **Session D** after B lands (P0): workflow runner core needs the new contracts.
3. **Session E** after A + B + D land (P0): per-state handlers need rule includes, contracts, and the runner protocol.
4. **Session F** after D + E land (P0): CLI activation wires it all.
5. **Session H** after F lands (P0): real carousel dry run. This is the decision point — go/no-go on the rest.
6. **Session G** after H lands (P1): package writer reduction, once the runner has proven the artifact shape works.
7. **Session I** after G lands (P1): legacy wrapper + skill dedup.
8. **Session J, K** after I lands (P1, P2): audit + learning capture.

### Merge order

Same as execution order. Each lane merges to `main` before the next dependent lane begins so the runner doesn't fork.

---

## Parallel Session Prompts

Use one prompt per fresh Codex session. Each session should create its own worktree before editing. Sessions are narrow; merge after tests pass.

### Session A Prompt — Rule Consolidation

```text
You are in /Users/himanshusharma/astoryoftwo-analysis.

Use superpowers:using-git-worktrees and superpowers:executing-plans.

Work only on Task 1 from
docs/superpowers/plans/2026-05-31-agentic-os-activation-sprint.md.

Goal: collapse duplicated rule text across 15+ files into one canonical
source per concept, and add a {{rule:NAME}} include expander used by
the context loader.

Scope:
- Create config/rules/*.md (8 files).
- Create pipeline/agentic/rule_includes.py.
- Modify pipeline/agentic/context_loader.py to call the expander.
- Create tests/test_rule_includes.py.

Do not modify carousel outputs, agent personas, skill files, or any
state contract code. Skill dedup happens in Session I, not here.

Run:
venv/bin/python -m pytest tests/test_rule_includes.py -q

Return:
- list of rule files created with line counts
- proof the expander resolves an include
- proof the context loader applies the expander before token estimation
```

### Session B Prompt — Typed Contracts

```text
You are in /Users/himanshusharma/astoryoftwo-analysis.

Use superpowers:using-git-worktrees and superpowers:executing-plans.

Work only on Task 2 from
docs/superpowers/plans/2026-05-31-agentic-os-activation-sprint.md.

Goal: extend pipeline/agentic/contracts.py with WorkflowRun,
WorkflowStateRecord, RepairBudget, RunArtifact, PauseRequest.

Scope:
- Modify pipeline/agentic/contracts.py.
- Create tests/test_workflow_state.py.

Do not change any existing contract field; only add new types.
Do not touch the runner, handlers, or CLI.

Run:
venv/bin/python -m pytest tests/test_workflow_state.py -q

Return:
- diff of contracts.py
- test output
```

### Session C Prompt — Deterministic Gates

```text
You are in /Users/himanshusharma/astoryoftwo-analysis.

Use superpowers:using-git-worktrees and superpowers:executing-plans.

Work only on Task 3 from
docs/superpowers/plans/2026-05-31-agentic-os-activation-sprint.md.

Goal: build pipeline/agentic/checks/{palette,ocr_text,image_size,prompt_constraints}.py
that return typed WorkflowGate values.

Scope:
- Add Pillow, easyocr, numpy to requirements.txt and install.
- Create pipeline/agentic/checks/*.py.
- Create tests/test_checks_*.py with Pillow-synthesized fixtures.

Do not call any external API. All tests must run offline (easyocr
downloads its model on first run; cache via tests/__init__.py if
needed).

Do not modify contracts, runner, handlers, or CLI.

Run:
venv/bin/python -m pytest tests/test_checks_palette.py \
  tests/test_checks_ocr_text.py tests/test_checks_image_size.py \
  tests/test_checks_prompt_constraints.py -q

Return:
- list of new check modules
- proof each gate's PASS and FAIL paths are exercised
- test output
```

### Session D Prompt — Workflow Runner Core

```text
You are in /Users/himanshusharma/astoryoftwo-analysis.

Use superpowers:using-git-worktrees and superpowers:executing-plans.

Work only on Task 4 from
docs/superpowers/plans/2026-05-31-agentic-os-activation-sprint.md.

Wait until Session B has merged (contracts must exist).

Goal: implement the state-machine driver with pause-resume support
and per-run JSONL audit log.

Scope:
- Create pipeline/agentic/workflow_runner.py.
- Create pipeline/agentic/workflows/carousel_jam/states.py.
- Modify pipeline/agentic/audit_log.py to add per-run JSONL writer.
- Create tests/test_workflow_runner_carousel_jam.py with stub
  handlers (no LLM calls, no image generation).

Do not implement real handlers; that is Session E.

Run:
venv/bin/python -m pytest tests/test_workflow_runner_carousel_jam.py -q

Return:
- runner module diff summary
- proof pause-then-resume cycle works
- proof repair-budget exhaustion produces a halt pause
- audit log content after one paused-resumed run
```

### Session E Prompt — Per-State Handlers

```text
You are in /Users/himanshusharma/astoryoftwo-analysis.

Use superpowers:using-git-worktrees and superpowers:executing-plans.

Work only on Task 5 from
docs/superpowers/plans/2026-05-31-agentic-os-activation-sprint.md.

Wait until Sessions A + B + D have merged.

Goal: implement one handler per carousel_jam state with typed I/O.

Scope:
- Create pipeline/agentic/workflows/carousel_jam/io_schemas.py.
- Create pipeline/agentic/workflows/carousel_jam/handlers/*.py
  (one per state).
- Wire handlers into pipeline/agentic/workflows/carousel_jam/__init__.py.
- Extend tests/test_workflow_runner_carousel_jam.py with a fixture-
  driven end-to-end test (monkeypatch any LLM calls).

For prompt_compile, proof_generation, full_generation handlers:
reuse pipeline/stages/carousel_prompt_compiler and
pipeline/stages/codex_builtin_image_generation where appropriate.

Do not modify the runner, contracts, gates, CLI, or skill files.

Run:
venv/bin/python -m pytest tests/test_workflow_runner_carousel_jam.py -q

Return:
- list of handler files with line counts
- proof a fixture-driven end-to-end run reaches AWAITING_PROOF_APPROVAL
  with all expected artifacts present
- test output
```

### Session F Prompt — CLI Activation

```text
You are in /Users/himanshusharma/astoryoftwo-analysis.

Use superpowers:using-git-worktrees and superpowers:executing-plans.

Work only on Task 6 from
docs/superpowers/plans/2026-05-31-agentic-os-activation-sprint.md.

Wait until Sessions D + E have merged.

Goal: add run-system, resume, status, runs, audit-packages
subcommands to scripts/agentic_os.py.

Scope:
- Modify scripts/agentic_os.py.
- Create tests/test_agentic_os_run_system_cli.py.

Do not modify the runner, handlers, or contracts.
Do not call any external API in tests.

Run:
venv/bin/python -m pytest tests/test_agentic_os_run_system_cli.py -q

Return:
- CLI usage output for each new subcommand
- proof a fixture-driven run-system + resume + status cycle works
- test output
```

### Session G Prompt — Package Writer Reduction

```text
You are in /Users/himanshusharma/astoryoftwo-analysis.

Use superpowers:using-git-worktrees and superpowers:executing-plans.

Work only on Task 7 from
docs/superpowers/plans/2026-05-31-agentic-os-activation-sprint.md.

Wait until Session H has produced a green dry run.

Goal: collapse the per-package artifact set to 8 first-class files
+ 3 derived Markdown views computed from runner state.

Scope:
- Create pipeline/agentic/package_writer.py.
- Migrate handlers (Session E lane) to use writer helpers.
- Create tests/test_package_writer_reduced.py.

Do not change runner state semantics.
Do not delete files from existing packages on disk.

Run:
venv/bin/python -m pytest tests/test_package_writer_reduced.py -q

Return:
- before/after artifact listing for one fixture package
- proof derived views are idempotent
- test output
```

### Session H Prompt — Real Carousel Dry Run

```text
You are in /Users/himanshusharma/astoryoftwo-analysis.

Use superpowers:executing-plans.

Wait until Session F has merged (CLI must work).

Work only on Task 8 from
docs/superpowers/plans/2026-05-31-agentic-os-activation-sprint.md.

Goal: take one real carousel end-to-end through the runner. Compare
to the most recent old-flow carousel
(output/carousels/2026-05-31/he-didn-t-marry-organized).

This is a CREATIVE session. Coordinate with the creator at each pause.
Do not skip pauses. Do not auto-approve.

Run:
venv/bin/python scripts/agentic_os.py run-system carousel_jam \
  --story "<from creator>" --image <path> --identity-image <path>

Then at each pause:
venv/bin/python scripts/agentic_os.py status <run-id>
# discuss with creator, write decision.json, then:
venv/bin/python scripts/agentic_os.py resume <run-id> --input-file decision.json

After done:
- Create output/reports/2026-05-31-agentic-runner-dry-run.md with
  the comparison table from Task 8.
- Run agentic_os.py capture-learning for anything surprising.

Return:
- run_id
- final state
- the comparison table
- one-paragraph go/no-go recommendation
```

### Session I Prompt — Legacy Wrapper + Skill Dedup

```text
You are in /Users/himanshusharma/astoryoftwo-analysis.

Use superpowers:using-git-worktrees and superpowers:executing-plans.

Wait until Session G has merged.

Work only on Task 9 from
docs/superpowers/plans/2026-05-31-agentic-os-activation-sprint.md.

Goal: make scripts/create_illustration_carousel.py a thin wrapper
around scripts/agentic_os.py run-system carousel_jam, and replace
inline rule duplication in config/skills/*.md with {{rule:NAME}}
includes.

Scope:
- Rewrite scripts/create_illustration_carousel.py.
- Edit every file in config/skills/.

Do not change the agentic OS runner or handlers.
Do not delete skill files.

After editing skills, run:
grep -rn "yellow\|sepia\|parchment\|mustard" config/skills/

Confirm the only remaining hits are within include markers or
commentary about a rule.

Run:
venv/bin/python -m pytest -q

Return:
- list of skill files modified with before/after line counts
- grep proof of dedup
- test output
```

### Session J Prompt — Existing Package Audit

```text
You are in /Users/himanshusharma/astoryoftwo-analysis.

Use superpowers:using-git-worktrees and superpowers:executing-plans.

Wait until Session C has merged (gates must exist).

Work only on Task 10 from
docs/superpowers/plans/2026-05-31-agentic-os-activation-sprint.md.

Goal: build scripts/audit_packages.py and produce
output/reports/2026-05-31-package-audit-via-new-gates.md covering
all 67 existing carousels.

Scope:
- Create scripts/audit_packages.py.
- Run agentic_os.py audit-packages.
- Write the report.

Do not modify any carousel package on disk.
Do not delete anything.

Return:
- report path
- one-paragraph summary of pass rates
- list of recommended archive candidates (do not move them yet)
```

### Session K Prompt — Learning Capture Wiring

```text
You are in /Users/himanshusharma/astoryoftwo-analysis.

Use superpowers:using-git-worktrees and superpowers:executing-plans.

Wait until Session I has merged.

Work only on Task 11 from
docs/superpowers/plans/2026-05-31-agentic-os-activation-sprint.md.

Goal: turn recurring human-pause repair notes into draft
LearningProposal entries targeting the relevant rule files.

Scope:
- Modify pipeline/agentic/learning_loop.py.
- Modify handlers that accept human input.
- Add test for the recurring-repair detection.

Proposals must remain draft until evaluate_learning_proposal returns
PASS and a human approves. Do not auto-apply.

Run:
venv/bin/python -m pytest -q

Return:
- proof a simulated three-occurrence repair note produces a
  draft proposal targeting config/rules/palette.md
- test output
```

---

## Definition of Done

This sprint is done when **all** of the following are true:

- `venv/bin/python -m pytest -q` passes for the new test suite:
  `tests/test_rule_includes.py`, `tests/test_workflow_state.py`,
  `tests/test_checks_*.py`, `tests/test_workflow_runner_carousel_jam.py`,
  `tests/test_agentic_os_run_system_cli.py`,
  `tests/test_package_writer_reduced.py`.
- `scripts/agentic_os.py run-system carousel_jam --story "..."` starts a run, pauses at the first human gate, persists `state.json` under `memory/agentic/workflow-runs/<run-id>/`, and `scripts/agentic_os.py resume <run-id>` advances past the pause.
- One real carousel has been taken end-to-end through the runner with all five pauses honored and approved by the creator.
- The dry-run report shows wall-clock time < 50% of the most recent old-flow run, palette + OCR + size gates exercised on the proof slide, and the creator's approval of the final 4:5 + 9:16 set.
- `grep -rn "yellow\|sepia\|parchment\|mustard" config/skills/ memory/semantic/` returns zero hits outside of include markers and commentary.
- `scripts/create_illustration_carousel.py` is a thin wrapper around `agentic_os.py run-system carousel_jam`.
- All 67 existing carousels are audited via the new gates and the audit report exists at `output/reports/2026-05-31-package-audit-via-new-gates.md`.

---

## Anti-Scope-Creep Rules

- Do not add a new image-generation backend in this sprint. Codex remains the runtime.
- Do not implement Remotion motion in this sprint. It is a post-CLOSEOUT state added in a later sprint.
- Do not implement D-layer (`story_article`) or B-layer (`prepost_reel`) runners in this sprint. The runner pattern transfers; that is the next sprint.
- Do not delete skill files in `config/skills/`. Dedup them by inserting rule includes; deletion comes only after proven redundancy across two sprints.
- Do not delete existing carousel packages in `output/carousels/`. Archive at most; deletion only after the audit has produced an explicit candidate list and the creator has approved.
- Do not auto-apply `LearningProposal` entries. The guardrail is explicit in `pipeline/agentic/learning_loop.py`; preserve it.
- Do not write any handler that auto-advances through a human pause state. The runner contract is: pause states return control; only `resume` advances them.
- Do not allow any gate to return PASS without producing evidence (`evidence_paths` populated or a measured `reason`).
- Do not introduce a new third-party orchestration framework (Prefect, Temporal, Airflow). The Pydantic state machine is the orchestration layer.

---

## Closeout

At the end of implementation, run:

```bash
venv/bin/python -m pytest -q
venv/bin/python scripts/wiki_health.py --write --fix-index \
  --session-note "Activate Agentic OS as carousel workflow runner; consolidate rules; add deterministic gates; reduce per-package artifacts; insert five human pauses"
venv/bin/python scripts/autopublish.py \
  --session-note "Activate Agentic OS as carousel workflow runner; consolidate rules; add deterministic gates; reduce per-package artifacts; insert five human pauses"
```

If the worktree contains unrelated carousel outputs, use repeated `--include` flags with `scripts/autopublish.py` for only the files changed by the sprint.

---

## Appendix A — State Machine Diagram

```
                  SESSION_START
                        ↓
                  RAW_SCENE_LOCK
                        ↓
                  CONCEPT_GENERATION
                        ↓
            ▼ AWAITING_CONCEPT_LOCK ▼   ← human pause 1
                        ↓
                  COPY_GENERATION
                        ↓
              ▼ AWAITING_COPY_LOCK ▼    ← human pause 2
                        ↓
                  VISUAL_PLAN
                        ↓
         ▼ AWAITING_VISUAL_PLAN_LOCK ▼  ← human pause 3
                        ↓
                  PROMPT_COMPILE  ──→ deterministic gates
                        ↓
                  PROOF_GENERATION  ──→ palette / ocr / size / face-continuity
                   ↓             ↓
                  PASS          FAIL (retry ≤2)
                   ↓             ↓
         ▼ AWAITING_PROOF_APPROVAL ▼   ← human pause 4
                        ↓
                  FULL_GENERATION  ──→ palette / ocr / size per slide
                        ↓
         ▼ AWAITING_FINAL_APPROVAL ▼   ← human pause 5
                        ↓
                  CLOSEOUT  (wiki_health + autopublish)
                        ↓
                       DONE
```

## Appendix B — Why the Existing Codex Plan Becomes a Sub-Plan

The earlier Codex sprint plan (`2026-05-31-carousel-autopilot-sprint.md`) is not discarded. Its five P0 items map cleanly into this sprint:

- Workflow Doctor → subsumed by Task 4 (Runner) + Task 10 (Audit). Doctor checks become gate checks.
- Canonical Prompt Source → subsumed by Task 1 (Rule Consolidation) — the master prompt becomes `{{rule:palette}} {{rule:identity}} {{rule:on-image-text}} {{rule:brandmark}}` composed from canonical sources.
- Handoff Prompt Cleanup → automatic once `prompt_compile` handler is the single prompt source.
- Final State Contract → Task 2 (WorkflowRun + WorkflowStateRecord) IS the state contract.
- 80/20 Final QA → Task 3 (Deterministic Gates) + Task 7 (Package Writer) replace the old final-audit JSON.

This plan supersedes the Codex plan only because it builds the executable runner those checks attach to.
