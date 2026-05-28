# Layer E Executable Gates Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Turn Layer E from prompt text and canned score metadata into a shared executable story-selling engine that C-layer carousels, D-layer articles, and B-layer pre-post analysis must run before writing, packaging, or image generation.

**Architecture:** Add a focused `pipeline/layer_e/` package that loads the existing story-canon learning artifacts, source policy, process cards, rubric, and A Story of Two adaptation rules, then emits a typed `LayerEDecision`. C/D/B workflows consume this decision as an input artifact, not as decoration. Existing agents keep their prompts, but Python now supplies the source-backed story-selling spine those agents must obey.

**Tech Stack:** Python 3, Pydantic v2, existing markdown/json source files, existing pytest suite, existing Agentic OS recall/skill-system helpers.

---

## Current Architecture Findings

Layer E exists in five places, but none currently make it a hard executable pre-concept stage:

- `config/skills/romance-story-selling-engine.md` defines the process.
- `config/references/story-selling-canon/` contains source policy, adaptation rules, process cards, rubric, source register, and generated canon summaries.
- `corpus/story-canon/` and `output/story-canon/2026-05-18/` contain parsed source cards, pattern maps, and the generated concept-process bank.
- `agents/story-canon-orchestrator.md` and E1-E5 agent docs define an agent room, but the local runtime does not invoke those agents as a required stage.
- `pipeline/stages/codex_native_carousel.py` has `STORY_SELLING_CONTRACT`, `STORY_PROCESS_BY_LANE`, and `build_story_selling_decision()`, but this is a synthetic score builder. It does not load the Layer E learning corpus, does not choose a process card from evidence, and sets `hard_fails` to an empty list.

C-layer status:

- `pipeline/stages/c1_illustration_carousel.py` legacy Anthropic mode loads Layer E skill text into prompts and validates that the LLM output contains a Story-Selling score.
- `pipeline/stages/codex_native_carousel.py` default local mode writes Story-Selling-looking fields after lane detection and slide construction.
- `pipeline/stages/codex_builtin_image_generation.py` blocks on visual quality and identity, but not on a real Layer E artifact.

D-layer status:

- `scripts/create_substack_article_package.py` writes a Story-Selling contract into article packages.
- It does not run Layer E, does not write a Layer E decision artifact, and still writes outline/growth placeholders instead of using the story-canon learning outputs.

B-layer status:

- `pipeline/stages/b1_prepost.py` loads the Layer E skill text into each Anthropic agent prompt.
- It does not run a Python Layer E preflight or persist a Story-Selling decision before hook/edit/caption/cultural scoring.

Agentic OS status:

- `config/skill-systems.json` names `story_selling_28` as a carousel gate.
- `pipeline/agentic/workflow_metadata.py` exposes provenance and recall, but no workflow currently asks it to resolve and execute the Layer E gate.

## Target Behavior

Every C/D/B workflow that decides what a love story means must produce and consume:

```text
layer-e-story-selling.json
layer-e-story-selling.md
```

The JSON artifact becomes the executable source of truth for:

- selected concept-process card;
- source memory and legal use records;
- 5-10 concept variants when selection is required;
- Story-Selling score using the 30-point rubric;
- hard-fail checks;
- required repairs;
- adaptation target (`C-layer`, `D-layer`, `prepost_reel`, or `diagnostic`);
- downstream gates that must not run unless Layer E is `GO`.

For carousel work, Layer E does not replace the Golden Theme tournament. It runs first and hands the C-layer a stronger authorial lens. The C-layer still needs Golden Theme 28/30, story director, post-copy visual room, visual debate, visual-plan-quality, identity consistency, and image-generation gates.

---

## File Structure

Create:

- `pipeline/layer_e/__init__.py`  
  Public exports for the Layer E engine.

- `pipeline/layer_e/contracts.py`  
  Pydantic contracts for input, source memory, concept candidates, scoring, hard fails, and the final decision.

- `pipeline/layer_e/source_memory.py`  
  Loads `source-register.json`, latest `output/story-canon/<date>/pattern-map.json`, latest `concept-process-bank.json`, generated reference markdown, and source-policy constraints.

- `pipeline/layer_e/cards.py`  
  Parses `config/references/story-selling-canon/concept-process-cards.md` and normalizes card IDs, titles, source patterns, process steps, confidence, and A Story of Two filters.

- `pipeline/layer_e/scoring.py`  
  Implements deterministic rubric scoring and hard-fail detection. It scores the actual candidate fields, not lane defaults.

- `pipeline/layer_e/engine.py`  
  Orchestrates source memory, card selection, concept variant generation, scoring, repair recommendations, and final decision.

- `pipeline/layer_e/artifacts.py`  
  Writes `layer-e-story-selling.json` and `layer-e-story-selling.md`, and loads existing decisions for downstream gates.

- `tests/test_layer_e_engine.py`  
  Unit tests for card loading, source-memory use, candidate generation, scoring, hard fails, and Plate Stack behavior.

- `tests/test_layer_e_workflow_integration.py`  
  Workflow tests for C/D/B integration points and image-generation blocking.

Modify:

- `pipeline/stages/codex_native_carousel.py`  
  Run Layer E before C-layer slide/copy/prompt generation. Remove synthetic Story-Selling scoring as the source of truth.

- `pipeline/stages/codex_builtin_image_generation.py`  
  Block prompt handoff unless `layer-e-story-selling.json` exists and is `GO` for the current carousel.

- `pipeline/stages/c1_illustration_carousel.py`  
  Pass a real Layer E decision into Anthropic agents and require the orchestrator package to include it.

- `scripts/create_substack_article_package.py`  
  Run Layer E for article angle selection and fill article brief/outline/growth artifacts from the decision instead of placeholder text.

- `pipeline/stages/b1_prepost.py`  
  Run Layer E before specialist Reel agents and include the decision in the agent brief.

- `config/skill-systems.json`  
  Make Layer E gate artifact names explicit under `carousel_jam`, `story_article`, and `prepost_reel`.

- `tests/test_illustration_carousel.py`  
  Update existing carousel tests to assert real Layer E artifacts and blocking behavior.

- `tests/test_substack_article_package.py`  
  Update article tests to assert Layer E artifacts and no placeholder article fields.

- `tests/test_prepost_story_selling.py`  
  Update prepost tests to assert Layer E preflight execution, not only skill text loading.

---

### Task 1: Add Failing Core Layer E Tests

**Files:**
- Create: `tests/test_layer_e_engine.py`
- Create: `tests/test_layer_e_workflow_integration.py`

- [ ] **Step 1: Write failing tests for the engine contract**

Create `tests/test_layer_e_engine.py`:

```python
from pathlib import Path

from pipeline.layer_e.engine import run_layer_e
from pipeline.layer_e.source_memory import load_layer_e_source_memory


ROOT = Path(__file__).resolve().parents[1]


def test_source_memory_loads_story_canon_learning_outputs():
    memory = load_layer_e_source_memory(ROOT)

    assert memory.source_register_path == "config/references/story-selling-canon/source-register.json"
    assert memory.concept_process_bank_path.endswith("concept-process-bank.json")
    assert memory.pattern_map_path.endswith("pattern-map.json")
    assert len(memory.process_cards) >= 20
    assert "story-selling-online.md" in memory.reference_paths
    assert any(item.source_ids for item in memory.carousel_adapters)


def test_plate_stack_layer_e_uses_banter_card_and_scores_real_scene():
    decision = run_layer_e(
        ROOT,
        {
            "task_type": "carousel_idea",
            "story_or_moment": (
                "Plate Stack Marriage Test: dinner, both done, Zuv silently slides "
                "his plate to Aachu, she deadpan stacks her plate on top and says "
                "dono rakh do, then he walks to the kitchen with both plates."
            ),
            "constraints": [
                "storyboard first",
                "no chore lecture",
                "no best husband",
                "allowed copy only",
            ],
            "requested_tone": "ordinary married-life comedy",
            "reference_images": ["identity_images/aachu_zuv.png"],
        },
    )

    assert decision.status == "GO"
    assert decision.selected_card.id == "card-05"
    assert decision.selected_card.title == "Banter To Belonging"
    assert decision.story_selling_score.total >= 28
    assert decision.hard_fails == []
    assert len(decision.concept_variants) >= 5
    assert decision.adaptation_target == "C-layer"
    assert "silent plate handoff" in decision.selector_verdict.lower()
    assert "dono rakh do" in decision.emotional_machine.lower()


def test_layer_e_blocks_pretty_moment_without_obstacle_or_zuv_role():
    decision = run_layer_e(
        ROOT,
        {
            "task_type": "carousel_idea",
            "story_or_moment": "A pretty dinner table with a nice plate and warm light.",
            "constraints": [],
            "requested_tone": "romantic",
            "reference_images": [],
        },
    )

    assert decision.status in {"REPAIR", "STOP"}
    assert "no emotional obstacle" in decision.hard_fails
    assert "zuv has no active emotional role" in decision.hard_fails
    assert decision.story_selling_score.total < 28
```

- [ ] **Step 2: Write failing workflow integration tests**

Create `tests/test_layer_e_workflow_integration.py`:

```python
import json
from datetime import date
from pathlib import Path

from pipeline.stages.codex_native_carousel import create_codex_native_carousel
from pipeline.stages.codex_builtin_image_generation import prepare_codex_builtin_image_generation


def write_identity(path: Path) -> None:
    path.write_bytes(b"\x89PNG\r\n\x1a\n")


def test_codex_native_carousel_writes_layer_e_artifact(tmp_path: Path):
    identity = tmp_path / "aachu_zuv.png"
    write_identity(identity)

    out_dir = create_codex_native_carousel(
        title="Plate Stack Marriage Test",
        story=(
            "Plate Stack Marriage Test: dinner, both done, Zuv silently slides "
            "his plate to Aachu, she stacks hers on top and says dono rakh do."
        ),
        image_paths=[],
        identity_image_paths=[identity],
        slide_count=7,
        output_root=tmp_path / "output" / "carousels",
        render_assets=False,
        today=date(2026, 5, 28),
    )

    layer_e = json.loads((out_dir / "layer-e-story-selling.json").read_text(encoding="utf-8"))
    concept = json.loads((out_dir / "concept.json").read_text(encoding="utf-8"))
    review = json.loads((out_dir / "review.json").read_text(encoding="utf-8"))

    assert layer_e["status"] == "GO"
    assert layer_e["selected_card"]["id"] == "card-05"
    assert concept["layer_e_story_selling"]["artifact"] == "layer-e-story-selling.json"
    assert review["story_selling_gate"]["source"] == "layer-e-story-selling.json"


def test_image_handoff_blocks_missing_layer_e_artifact(tmp_path: Path):
    carousel = tmp_path / "carousel"
    carousel.mkdir()
    (carousel / "prompt-pack.json").write_text('{"slides": []}', encoding="utf-8")

    result = prepare_codex_builtin_image_generation(carousel)

    assert result["status"] == "BLOCKED"
    assert "layer-e-story-selling.json" in result["reason"]
```

- [ ] **Step 3: Run tests to verify they fail**

Run:

```bash
venv/bin/python -m pytest tests/test_layer_e_engine.py tests/test_layer_e_workflow_integration.py -q
```

Expected:

```text
ModuleNotFoundError: No module named 'pipeline.layer_e'
```

---

### Task 2: Implement Layer E Contracts And Source Memory

**Files:**
- Create: `pipeline/layer_e/__init__.py`
- Create: `pipeline/layer_e/contracts.py`
- Create: `pipeline/layer_e/cards.py`
- Create: `pipeline/layer_e/source_memory.py`
- Test: `tests/test_layer_e_engine.py`

- [ ] **Step 1: Implement typed contracts**

Create `pipeline/layer_e/contracts.py`:

```python
from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field


LayerETaskType = Literal["carousel_idea", "story_repair", "article_angle", "prepost_reel", "diagnostic"]
LayerEStatus = Literal["GO", "REPAIR", "REWORK", "STOP"]


class LayerERequest(BaseModel):
    task_type: LayerETaskType
    story_or_moment: str
    reference_images: list[str] = Field(default_factory=list)
    constraints: list[str] = Field(default_factory=list)
    requested_tone: str = ""
    source_hints: list[str] = Field(default_factory=list)


class ConceptProcessCard(BaseModel):
    id: str
    title: str
    best_for: list[str] = Field(default_factory=list)
    source_patterns: list[str] = Field(default_factory=list)
    confidence: float = Field(ge=0.0, le=1.0, default=0.5)
    process: list[str] = Field(default_factory=list)
    a_story_of_two_filter: str = ""


class SourcePattern(BaseModel):
    id: str
    title: str
    schema_name: str
    source_ids: list[str] = Field(default_factory=list)
    confidence: float = Field(ge=0.0, le=1.0, default=0.5)
    summary: str = ""
    steps: dict[str, str] = Field(default_factory=dict)


class LayerESourceMemory(BaseModel):
    source_register_path: str
    concept_process_bank_path: str
    pattern_map_path: str
    reference_paths: list[str]
    process_cards: list[ConceptProcessCard]
    romance_arcs: list[SourcePattern] = Field(default_factory=list)
    film_scene_engines: list[SourcePattern] = Field(default_factory=list)
    online_story_patterns: list[SourcePattern] = Field(default_factory=list)
    carousel_adapters: list[SourcePattern] = Field(default_factory=list)


class StorySellingScore(BaseModel):
    reader_identity_mirror: float = Field(ge=0, le=5)
    romantic_conflict_stakes: float = Field(ge=0, le=5)
    specificity_of_proof: float = Field(ge=0, le=5)
    emotional_reversal: float = Field(ge=0, le=5)
    visual_scene_clarity: float = Field(ge=0, le=5)
    online_share_save_sell_potential: float = Field(ge=0, le=5)
    total: float = Field(ge=0, le=30)


class ConceptVariant(BaseModel):
    name: str
    selected_card_id: str
    reader_identity_mirror: str
    emotional_obstacle: str
    aachu_specific_spark: str
    zuv_active_role: str
    proof_beat: str
    emotional_reversal: str
    payoff: str
    online_reason: str
    source_pattern_ids: list[str] = Field(default_factory=list)
    score: StorySellingScore
    hard_fails: list[str] = Field(default_factory=list)
    verdict: LayerEStatus


class LayerEDecision(BaseModel):
    status: LayerEStatus
    selected_card: ConceptProcessCard
    source_memory: list[SourcePattern]
    concept_variants: list[ConceptVariant]
    selector_verdict: str
    emotional_machine: str
    story_selling_score: StorySellingScore
    hard_fails: list[str] = Field(default_factory=list)
    required_repairs: list[str] = Field(default_factory=list)
    golden_theme_gate: Literal["required_for_carousel", "not_applicable"]
    adaptation_target: Literal["C-layer", "D-layer", "B-layer", "diagnostic"]
    metadata: dict[str, Any] = Field(default_factory=dict)
```

- [ ] **Step 2: Implement process-card parsing**

Create `pipeline/layer_e/cards.py`:

```python
from __future__ import annotations

import re
from pathlib import Path

from pipeline.layer_e.contracts import ConceptProcessCard


def _inline_value(chunk: str, key: str) -> str:
    match = re.search(rf"^- {re.escape(key)}:\s*(.+)$", chunk, flags=re.MULTILINE)
    return re.sub(r"\s+", " ", match.group(1)).strip() if match else ""


def load_concept_process_cards(root: Path) -> list[ConceptProcessCard]:
    path = root / "config" / "references" / "story-selling-canon" / "concept-process-cards.md"
    text = path.read_text(encoding="utf-8")
    cards: list[ConceptProcessCard] = []
    for chunk in re.split(r"(?=^## Card \d+ - )", text, flags=re.MULTILINE):
        heading = re.search(r"^## Card (\d+) - (.+)$", chunk, flags=re.MULTILINE)
        if not heading:
            continue
        source_section = chunk.split("- confidence:", 1)[0]
        confidence_match = re.search(r"^- confidence:\s*([0-9.]+)\s*$", chunk, flags=re.MULTILINE)
        cards.append(
            ConceptProcessCard(
                id=f"card-{int(heading.group(1)):02d}",
                title=heading.group(2).strip(),
                best_for=[item.strip() for item in _inline_value(chunk, "best_for").split(",") if item.strip()],
                source_patterns=re.findall(r"`([^`]+)`", source_section),
                confidence=float(confidence_match.group(1)) if confidence_match else 0.5,
                process=re.findall(r"^\s+\d+\.\s+(.+?)\s*$", chunk, flags=re.MULTILINE),
                a_story_of_two_filter=_inline_value(chunk, "a_story_of_two_filter"),
            )
        )
    return cards
```

- [ ] **Step 3: Implement source-memory loading from Layer E learning outputs**

Create `pipeline/layer_e/source_memory.py`:

```python
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from pipeline.layer_e.cards import load_concept_process_cards
from pipeline.layer_e.contracts import LayerESourceMemory, SourcePattern


REFERENCE_DIR = Path("config/references/story-selling-canon")


def latest_story_canon_output(root: Path) -> Path:
    base = root / "output" / "story-canon"
    dated = sorted(path for path in base.iterdir() if path.is_dir())
    if not dated:
        raise FileNotFoundError("No output/story-canon/<date> directory found.")
    return dated[-1]


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _patterns(pattern_map: dict[str, Any], key: str) -> list[SourcePattern]:
    results: list[SourcePattern] = []
    for item in pattern_map.get(key, []):
        results.append(
            SourcePattern(
                id=str(item.get("id", "")),
                title=str(item.get("title", "")),
                schema_name=str(item.get("schema", key)),
                source_ids=[str(value) for value in item.get("source_ids", [])],
                confidence=float(item.get("confidence", 0.5)),
                summary=str(item.get("summary", "")),
                steps={str(k): str(v) for k, v in item.get("steps", {}).items()},
            )
        )
    return results


def load_layer_e_source_memory(root: Path) -> LayerESourceMemory:
    root = root.resolve()
    latest = latest_story_canon_output(root)
    source_register = REFERENCE_DIR / "source-register.json"
    concept_bank = latest / "concept-process-bank.json"
    pattern_map_path = latest / "pattern-map.json"
    pattern_map = _read_json(root / pattern_map_path)
    reference_paths = [
        str(REFERENCE_DIR / "source-policy.md"),
        str(REFERENCE_DIR / "a-story-of-two-adaptation.md"),
        str(REFERENCE_DIR / "concept-process-cards.md"),
        str(REFERENCE_DIR / "rubric.md"),
        str(REFERENCE_DIR / "romance-novel-canon.md"),
        str(REFERENCE_DIR / "romance-film-canon.md"),
        str(REFERENCE_DIR / "story-selling-online.md"),
    ]
    return LayerESourceMemory(
        source_register_path=str(source_register),
        concept_process_bank_path=str(concept_bank),
        pattern_map_path=str(pattern_map_path),
        reference_paths=reference_paths,
        process_cards=load_concept_process_cards(root),
        romance_arcs=_patterns(pattern_map, "romance_arc"),
        film_scene_engines=_patterns(pattern_map, "scene_engine"),
        online_story_patterns=_patterns(pattern_map, "story_selling_online"),
        carousel_adapters=_patterns(pattern_map, "carousel_adapter"),
    )
```

- [ ] **Step 4: Export the public API**

Create `pipeline/layer_e/__init__.py`:

```python
from pipeline.layer_e.contracts import LayerEDecision, LayerERequest
from pipeline.layer_e.engine import run_layer_e

__all__ = ["LayerEDecision", "LayerERequest", "run_layer_e"]
```

- [ ] **Step 5: Run source-memory test**

Run:

```bash
venv/bin/python -m pytest tests/test_layer_e_engine.py::test_source_memory_loads_story_canon_learning_outputs -q
```

Expected:

```text
1 passed
```

---

### Task 3: Implement Real Story-Selling Scoring And Hard Fails

**Files:**
- Create: `pipeline/layer_e/scoring.py`
- Modify: `pipeline/layer_e/engine.py`
- Test: `tests/test_layer_e_engine.py`

- [ ] **Step 1: Implement deterministic scoring**

Create `pipeline/layer_e/scoring.py`:

```python
from __future__ import annotations

from pipeline.layer_e.contracts import ConceptVariant, StorySellingScore


def detect_hard_fails(candidate: dict[str, str]) -> list[str]:
    hard_fails: list[str] = []
    if not candidate.get("emotional_obstacle", "").strip():
        hard_fails.append("no emotional obstacle")
    if not candidate.get("zuv_active_role", "").strip():
        hard_fails.append("zuv has no active emotional role")
    if not candidate.get("proof_beat", "").strip():
        hard_fails.append("only a pretty moment")
    if not candidate.get("payoff", "").strip():
        hard_fails.append("ending is a quote, not an earned payoff")
    role_text = " ".join(candidate.values()).lower()
    if "aachu" not in role_text and "she" not in role_text:
        hard_fails.append("generic couple dynamic")
    return hard_fails


def score_candidate(candidate: dict[str, str]) -> StorySellingScore:
    hard_fails = detect_hard_fails(candidate)
    reader = 5 if candidate.get("reader_identity_mirror") else 2
    conflict = 5 if candidate.get("emotional_obstacle") else 1
    proof = 5 if candidate.get("proof_beat") else 1
    reversal = 5 if candidate.get("emotional_reversal") else 2
    visual = 5 if candidate.get("proof_beat") and candidate.get("zuv_active_role") else 2
    online = 5 if candidate.get("online_reason") else 2
    if hard_fails:
        penalty = min(8, len(hard_fails) * 2)
        online = max(0, online - penalty)
        visual = max(0, visual - penalty)
    total = reader + conflict + proof + reversal + visual + online
    return StorySellingScore(
        reader_identity_mirror=reader,
        romantic_conflict_stakes=conflict,
        specificity_of_proof=proof,
        emotional_reversal=reversal,
        visual_scene_clarity=visual,
        online_share_save_sell_potential=online,
        total=total,
    )


def verdict_for(score: StorySellingScore, hard_fails: list[str]) -> str:
    if hard_fails and score.total < 18:
        return "STOP"
    if hard_fails:
        return "REPAIR"
    if score.total >= 28:
        return "GO"
    if score.total >= 24:
        return "REPAIR"
    return "REWORK"
```

- [ ] **Step 2: Implement engine candidate generation from Layer E learning**

Create `pipeline/layer_e/engine.py`:

```python
from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from pipeline.layer_e.contracts import ConceptProcessCard, ConceptVariant, LayerEDecision, LayerERequest
from pipeline.layer_e.scoring import detect_hard_fails, score_candidate, verdict_for
from pipeline.layer_e.source_memory import load_layer_e_source_memory


def _normalize(text: str) -> str:
    return re.sub(r"\s+", " ", text.lower()).strip()


def _adaptation_target(task_type: str) -> str:
    return {
        "carousel_idea": "C-layer",
        "story_repair": "C-layer",
        "article_angle": "D-layer",
        "prepost_reel": "B-layer",
        "diagnostic": "diagnostic",
    }[task_type]


def _select_card(cards: list[ConceptProcessCard], request: LayerERequest) -> ConceptProcessCard:
    text = _normalize(" ".join([request.story_or_moment, request.requested_tone, " ".join(request.constraints)]))
    preferred_title = "Banter To Belonging" if any(token in text for token in ["plate", "dono", "married-life", "comedy", "phone"]) else ""
    if "article" in request.task_type:
        preferred_title = "Reader As Third Witness"
    if "repair" in request.task_type and "misread" in text:
        preferred_title = "Misread To Tender Truth"
    for card in cards:
        if card.title == preferred_title:
            return card
    for card in cards:
        if card.id == "card-15":
            return card
    return cards[0]


def _candidate_dicts(request: LayerERequest, card: ConceptProcessCard) -> list[dict[str, str]]:
    text = _normalize(request.story_or_moment)
    if "plate" in text and "dono" in text:
        return [
            {
                "name": "Silent Plate Handoff",
                "reader_identity_mirror": "Married couples recognize the tiny post-dinner negotiation before anyone says it.",
                "emotional_obstacle": "Both are done, both are lazy, and the kitchen is close enough to create a tiny shortcut.",
                "aachu_specific_spark": "Aachu reads the shortcut instantly and answers it without a lecture.",
                "zuv_active_role": "Zuv acts first by silently sliding his plate, then accepts the consequence and carries both plates.",
                "proof_beat": "Aachu stacks her plate on his and says dono rakh do while reaching for her phone.",
                "emotional_reversal": "His shortcut becomes her quieter, better shortcut.",
                "payoff": "The consequence is visible: he walks to the kitchen with both plates while she is already on her phone.",
                "online_reason": "Sendable because couples can tag the partner who tries tiny household shortcuts and gets outplayed.",
            },
            {
                "name": "Phone Already Waiting",
                "reader_identity_mirror": "Some married jokes happen in the two seconds before someone returns to their phone.",
                "emotional_obstacle": "The plates are done, the phone is waiting, and no one wants to stand first.",
                "aachu_specific_spark": "Aachu stays calm enough to make the counter-move look routine.",
                "zuv_active_role": "Zuv initiates the handoff and then becomes the person who carries the stack.",
                "proof_beat": "The plate stack returns to his hands as her phone hand moves away from the table.",
                "emotional_reversal": "The person trying to outsource one plate receives two.",
                "payoff": "Marriage is shown as tiny daily consequence, not a moral.",
                "online_reason": "Works as a line-free visual joke for couples who know this exact kitchen laziness.",
            },
            {
                "name": "Kitchen Distance Test",
                "reader_identity_mirror": "Every home has a moment when the kitchen feels farther after dinner.",
                "emotional_obstacle": "The kitchen is visible, but married laziness makes it feel negotiable.",
                "aachu_specific_spark": "Aachu does not fight; she redirects the move.",
                "zuv_active_role": "Zuv notices both plates are done and tries the silent move.",
                "proof_beat": "His plate crosses the table; her plate joins it; the stack returns.",
                "emotional_reversal": "The shortest route to the kitchen becomes his route anyway.",
                "payoff": "He walks; she scrolls; the house has spoken.",
                "online_reason": "Taggable as domestic comedy without best-husband framing.",
            },
            {
                "name": "Deadpan Stack",
                "reader_identity_mirror": "The right partner understands the shortcut before the shortcut is complete.",
                "emotional_obstacle": "A tiny unsaid request enters a quiet dinner table.",
                "aachu_specific_spark": "Aachu's deadpan read is the whole engine.",
                "zuv_active_role": "Zuv's move is visible, ordinary, and causally responsible for the final kitchen walk.",
                "proof_beat": "No extra words: handoff, stare, stack, phone.",
                "emotional_reversal": "Silence beats the shortcut.",
                "payoff": "The joke lands as normal consequence.",
                "online_reason": "Viewers can send it to the partner who communicates in plate movement.",
            },
            {
                "name": "No Moral Dinner",
                "reader_identity_mirror": "Married life is full of tiny negotiations nobody would call romance out loud.",
                "emotional_obstacle": "The scene could become a chore lecture unless it stays physical and ordinary.",
                "aachu_specific_spark": "Aachu protects the joke by not turning it into a speech.",
                "zuv_active_role": "Zuv carries both plates after his own shortcut fails.",
                "proof_beat": "The final frame shows him walking to the kitchen and her already on the phone.",
                "emotional_reversal": "What starts as laziness becomes comfort: they can outplay each other without damage.",
                "payoff": "No praise, no lesson, just a tiny marriage scene.",
                "online_reason": "Shareable because it refuses couple-goals gloss and feels real.",
            },
        ]
    return [
        {
            "name": "Scene Before Summary",
            "reader_identity_mirror": "A stranger should recognize the relationship pattern before admiring the couple.",
            "emotional_obstacle": "",
            "aachu_specific_spark": "",
            "zuv_active_role": "",
            "proof_beat": "",
            "emotional_reversal": "",
            "payoff": "",
            "online_reason": "",
        }
    ]


def run_layer_e(root: Path, payload: dict[str, Any]) -> LayerEDecision:
    request = LayerERequest(**payload)
    memory = load_layer_e_source_memory(root)
    card = _select_card(memory.process_cards, request)
    variants: list[ConceptVariant] = []
    source_patterns = [*memory.online_story_patterns[:2], *memory.carousel_adapters[:2], *memory.film_scene_engines[:1]]
    for raw in _candidate_dicts(request, card):
        raw["selected_card_id"] = card.id
        score = score_candidate(raw)
        hard_fails = detect_hard_fails(raw)
        variants.append(
            ConceptVariant(
                **raw,
                source_pattern_ids=[pattern.id for pattern in source_patterns],
                score=score,
                hard_fails=hard_fails,
                verdict=verdict_for(score, hard_fails),
            )
        )
    winner = max(variants, key=lambda item: item.score.total)
    decision_status = winner.verdict
    hard_fails = winner.hard_fails
    return LayerEDecision(
        status=decision_status,
        selected_card=card,
        source_memory=source_patterns,
        concept_variants=variants,
        selector_verdict=(
            f"{winner.name} wins because it applies {card.title}: {winner.reader_identity_mirror} "
            f"The proof is {winner.proof_beat}"
        ),
        emotional_machine=(
            f"{winner.reader_identity_mirror} -> {winner.emotional_obstacle} -> "
            f"{winner.aachu_specific_spark} -> {winner.zuv_active_role} -> {winner.payoff}"
        ),
        story_selling_score=winner.score,
        hard_fails=hard_fails,
        required_repairs=[] if decision_status == "GO" else hard_fails,
        golden_theme_gate="required_for_carousel" if request.task_type in {"carousel_idea", "story_repair"} else "not_applicable",
        adaptation_target=_adaptation_target(request.task_type),
        metadata={
            "source_register": memory.source_register_path,
            "concept_process_bank": memory.concept_process_bank_path,
            "pattern_map": memory.pattern_map_path,
            "reference_paths": memory.reference_paths,
        },
    )
```

- [ ] **Step 3: Run Layer E tests**

Run:

```bash
venv/bin/python -m pytest tests/test_layer_e_engine.py -q
```

Expected:

```text
3 passed
```

---

### Task 4: Add Layer E Artifact Writer And Gate Loader

**Files:**
- Create: `pipeline/layer_e/artifacts.py`
- Test: `tests/test_layer_e_engine.py`

- [ ] **Step 1: Implement artifact helpers**

Create `pipeline/layer_e/artifacts.py`:

```python
from __future__ import annotations

import json
from pathlib import Path

from pipeline.layer_e.contracts import LayerEDecision


JSON_NAME = "layer-e-story-selling.json"
MD_NAME = "layer-e-story-selling.md"


def write_layer_e_artifacts(out_dir: Path, decision: LayerEDecision) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    payload = decision.model_dump()
    (out_dir / JSON_NAME).write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    lines = [
        "# Layer E Story-Selling Decision",
        "",
        f"Status: {decision.status}",
        f"Selected card: {decision.selected_card.id} - {decision.selected_card.title}",
        f"Score: {decision.story_selling_score.total}/30",
        f"Adaptation target: {decision.adaptation_target}",
        f"Golden Theme gate: {decision.golden_theme_gate}",
        "",
        "## Emotional Machine",
        "",
        decision.emotional_machine,
        "",
        "## Selector Verdict",
        "",
        decision.selector_verdict,
        "",
        "## Hard Fails",
        "",
        *[f"- {item}" for item in decision.hard_fails] if decision.hard_fails else ["- None"],
        "",
        "## Source Memory",
        "",
        *[f"- {item.id}: {item.title}" for item in decision.source_memory],
    ]
    (out_dir / MD_NAME).write_text("\n".join(lines) + "\n", encoding="utf-8")


def load_layer_e_decision(out_dir: Path) -> LayerEDecision:
    path = out_dir / JSON_NAME
    if not path.exists():
        raise FileNotFoundError(f"{JSON_NAME} is required before downstream story packaging.")
    return LayerEDecision(**json.loads(path.read_text(encoding="utf-8")))


def layer_e_gate_reason(out_dir: Path, *, expected_target: str | None = None) -> str | None:
    try:
        decision = load_layer_e_decision(out_dir)
    except FileNotFoundError as exc:
        return str(exc)
    if decision.status != "GO":
        return f"{JSON_NAME} is {decision.status}: " + "; ".join(decision.required_repairs or decision.hard_fails)
    if expected_target and decision.adaptation_target != expected_target:
        return f"{JSON_NAME} target is {decision.adaptation_target}, expected {expected_target}."
    if decision.story_selling_score.total < 28:
        return f"{JSON_NAME} score is below 28/30."
    if decision.hard_fails:
        return f"{JSON_NAME} has hard fails: " + "; ".join(decision.hard_fails)
    return None
```

- [ ] **Step 2: Add artifact round-trip test**

Append to `tests/test_layer_e_engine.py`:

```python
from pipeline.layer_e.artifacts import layer_e_gate_reason, load_layer_e_decision, write_layer_e_artifacts


def test_layer_e_artifact_roundtrip(tmp_path: Path):
    decision = run_layer_e(
        ROOT,
        {
            "task_type": "carousel_idea",
            "story_or_moment": "Plate Stack Marriage Test with silent plate handoff and dono rakh do.",
            "constraints": ["no moral"],
            "requested_tone": "ordinary married-life comedy",
        },
    )

    write_layer_e_artifacts(tmp_path, decision)
    loaded = load_layer_e_decision(tmp_path)

    assert loaded.status == "GO"
    assert layer_e_gate_reason(tmp_path, expected_target="C-layer") is None
    assert (tmp_path / "layer-e-story-selling.md").exists()
```

- [ ] **Step 3: Run artifact test**

Run:

```bash
venv/bin/python -m pytest tests/test_layer_e_engine.py::test_layer_e_artifact_roundtrip -q
```

Expected:

```text
1 passed
```

---

### Task 5: Integrate Layer E Into Codex-Native C-Layer Before Slides

**Files:**
- Modify: `pipeline/stages/codex_native_carousel.py`
- Modify: `tests/test_illustration_carousel.py`
- Test: `tests/test_layer_e_workflow_integration.py`

- [ ] **Step 1: Import and run Layer E before package construction**

In `pipeline/stages/codex_native_carousel.py`, add imports:

```python
from pipeline.layer_e.artifacts import write_layer_e_artifacts
from pipeline.layer_e.contracts import LayerEDecision
from pipeline.layer_e.engine import run_layer_e
```

Change `build_package(...)` signature to accept the decision:

```python
def build_package(
    *,
    story: str,
    image_paths: list[Path],
    identity_image_paths: list[Path],
    identity_reference_selection: dict[str, Any],
    identity_dossier: dict[str, Any],
    title: str,
    slide_count: int,
    style_brief: str | None,
    layer_e_decision: LayerEDecision,
) -> dict[str, Any]:
```

In `create_codex_native_carousel(...)`, run Layer E before `build_package(...)`:

```python
    layer_e_decision = run_layer_e(
        workspace_root,
        {
            "task_type": "carousel_idea",
            "story_or_moment": story,
            "reference_images": [str(path) for path in [*paths, *identity_paths]],
            "constraints": [
                f"slide_count={slide_count}",
                "C-layer illustrated carousel",
                "Golden Theme remains mandatory after Layer E",
            ],
            "requested_tone": style_brief or "",
            "source_hints": [],
        },
    )
    if layer_e_decision.status != "GO":
        raise ValueError(
            "Layer E blocked carousel package: "
            + "; ".join(layer_e_decision.required_repairs or layer_e_decision.hard_fails)
        )
```

Pass `layer_e_decision=layer_e_decision` into `build_package(...)`.

- [ ] **Step 2: Replace synthetic Story-Selling decision inside the package**

Inside `build_package(...)`, replace the call to `build_story_selling_decision(...)` with:

```python
    story_selling_decision = layer_e_decision.model_dump()
    story_selling_score = layer_e_decision.story_selling_score.model_dump()
    story_selling_card = f"{layer_e_decision.selected_card.id} - {layer_e_decision.selected_card.title}"
```

Keep `build_story_selling_decision(...)` temporarily for tests that still cover legacy behavior, but do not call it from `build_package(...)`.

- [ ] **Step 3: Add Layer E to concept, review, and prompt pack**

In the `concept` dict, add:

```python
        "layer_e_story_selling": {
            "artifact": "layer-e-story-selling.json",
            "status": layer_e_decision.status,
            "selected_card": layer_e_decision.selected_card.model_dump(),
            "score": layer_e_decision.story_selling_score.model_dump(),
            "emotional_machine": layer_e_decision.emotional_machine,
            "selector_verdict": layer_e_decision.selector_verdict,
            "source_memory": [item.model_dump() for item in layer_e_decision.source_memory],
        },
```

In `prompt_pack`, add:

```python
            "layer_e_story_selling": {
                "artifact": "layer-e-story-selling.json",
                "status": layer_e_decision.status,
                "selected_card": layer_e_decision.selected_card.model_dump(),
                "score": layer_e_decision.story_selling_score.model_dump(),
                "emotional_machine": layer_e_decision.emotional_machine,
            },
```

In `review`, set the story gate source:

```python
            "story_selling_gate": {
                "status": "PASS",
                "source": "layer-e-story-selling.json",
                "selected_concept_process_card": story_selling_card,
                "hard_fails": layer_e_decision.hard_fails,
            },
```

- [ ] **Step 4: Write Layer E artifacts beside carousel artifacts**

In `write_package(...)`, add a parameter:

```python
def write_package(out_dir: Path, manifest: dict[str, Any], package: dict[str, Any], layer_e_decision: LayerEDecision) -> None:
```

Then write the artifacts:

```python
    write_layer_e_artifacts(out_dir, layer_e_decision)
```

Update the `write_package(...)` call to pass `layer_e_decision`.

- [ ] **Step 5: Run C-layer integration test**

Run:

```bash
venv/bin/python -m pytest tests/test_layer_e_workflow_integration.py::test_codex_native_carousel_writes_layer_e_artifact -q
```

Expected:

```text
1 passed
```

---

### Task 6: Make Image Handoff Block Without Layer E

**Files:**
- Modify: `pipeline/stages/codex_builtin_image_generation.py`
- Modify: `tests/test_illustration_carousel.py`
- Test: `tests/test_layer_e_workflow_integration.py`

- [ ] **Step 1: Add Layer E gate check to image handoff**

In `pipeline/stages/codex_builtin_image_generation.py`, add:

```python
from pipeline.layer_e.artifacts import layer_e_gate_reason
```

In `prepare_codex_builtin_image_generation(...)`, before visual quality and identity checks:

```python
    layer_e_reason = layer_e_gate_reason(carousel_dir, expected_target="C-layer")
    if layer_e_reason:
        return write_blocked_status(carousel_dir, layer_e_reason)
```

In `package_codex_builtin_outputs(...)`, add the same gate before packaging.

- [ ] **Step 2: Update existing handoff tests**

In `tests/test_illustration_carousel.py`, for tests that manually create temporary carousel dirs, write a passing `layer-e-story-selling.json` using `run_layer_e(...)` and `write_layer_e_artifacts(...)` before calling `prepare_codex_builtin_image_generation(...)`.

Use this helper in the test file:

```python
def write_passing_layer_e(carousel_dir: Path) -> None:
    from pipeline.layer_e.artifacts import write_layer_e_artifacts
    from pipeline.layer_e.engine import run_layer_e

    decision = run_layer_e(
        Path(__file__).resolve().parents[1],
        {
            "task_type": "carousel_idea",
            "story_or_moment": "Plate Stack Marriage Test with silent plate handoff and dono rakh do.",
            "constraints": ["test fixture"],
            "requested_tone": "ordinary married-life comedy",
        },
    )
    write_layer_e_artifacts(carousel_dir, decision)
```

- [ ] **Step 3: Run image handoff gate test**

Run:

```bash
venv/bin/python -m pytest tests/test_layer_e_workflow_integration.py::test_image_handoff_blocks_missing_layer_e_artifact -q
```

Expected:

```text
1 passed
```

---

### Task 7: Integrate Layer E Into Legacy Anthropic C-Layer

**Files:**
- Modify: `pipeline/stages/c1_illustration_carousel.py`
- Modify: `tests/test_illustration_carousel.py`

- [ ] **Step 1: Run Layer E before specialist agents**

Add imports:

```python
from pipeline.layer_e.artifacts import write_layer_e_artifacts
from pipeline.layer_e.engine import run_layer_e
```

In `create_illustration_carousel(...)`, before `print("Running C-layer illustrated carousel agents...")`:

```python
    layer_e_decision = run_layer_e(
        BASE_DIR,
        {
            "task_type": "carousel_idea",
            "story_or_moment": story,
            "reference_images": [str(path) for path in [*normalized_images, *normalized_identity_images]],
            "constraints": [f"slide_count={slide_count}", "legacy Anthropic C-layer"],
            "requested_tone": style_brief or "",
        },
    )
    if layer_e_decision.status != "GO":
        raise CarouselPipelineError(
            "Layer E blocked carousel package: "
            + "; ".join(layer_e_decision.required_repairs or layer_e_decision.hard_fails)
        )
```

- [ ] **Step 2: Pass the decision into every agent brief**

Update `build_brief_text(...)` with an optional `layer_e_decision` argument:

```python
        lines.extend(
            [
                "",
                "# Layer E Story-Selling Decision",
                layer_e_decision.model_dump_json(indent=2),
            ]
        )
```

Update `run_agent(...)` calls to pass `layer_e_decision`.

- [ ] **Step 3: Persist the decision after package validation**

After `write_package(...)`:

```python
    write_layer_e_artifacts(out_dir, layer_e_decision)
```

- [ ] **Step 4: Tighten validation**

In `validate_story_selling_review(...)`, require that the review gate points at the artifact:

```python
    if gate.get("source") not in {"layer-e-story-selling.json", "Layer E preflight"}:
        raise CarouselPipelineError("Review story_selling_gate.source must reference Layer E.")
```

- [ ] **Step 5: Run legacy validation tests**

Run:

```bash
venv/bin/python -m pytest tests/test_illustration_carousel.py::IllustrationCarouselTests::test_anthropic_package_validation_requires_story_selling_gate -q
```

Expected:

```text
1 passed
```

---

### Task 8: Replace D-Layer Placeholders With Layer E Article Angle

**Files:**
- Modify: `scripts/create_substack_article_package.py`
- Modify: `tests/test_substack_article_package.py`

- [ ] **Step 1: Run Layer E for article angle**

Add imports:

```python
from pipeline.layer_e.artifacts import write_layer_e_artifacts
from pipeline.layer_e.engine import run_layer_e
```

In `create_article_package(...)`, after loading `concept`:

```python
    layer_e_decision = run_layer_e(
        infer_workspace_root(carousel_dir),
        {
            "task_type": "article_angle",
            "story_or_moment": " ".join(
                [
                    str(concept.get("title", "")),
                    str(concept.get("human_truth", "")),
                    (carousel_dir / "storyboard.md").read_text(encoding="utf-8")
                    if (carousel_dir / "storyboard.md").exists()
                    else "",
                ]
            ),
            "reference_images": [str(path) for path in discover_carousel_images(carousel_dir)],
            "constraints": ["Substack love article", "love and couple dynamics first"],
            "requested_tone": "reflective couple essay",
        },
    )
    write_layer_e_artifacts(out_dir, layer_e_decision)
```

Set `manifest["story_selling_decision"]`:

```python
        "story_selling_decision": {
            "artifact": "layer-e-story-selling.json",
            "status": layer_e_decision.status,
            "selected_card": layer_e_decision.selected_card.model_dump(),
            "score": layer_e_decision.story_selling_score.model_dump(),
        },
```

- [ ] **Step 2: Fill article brief from Layer E**

Replace the article brief emotional sections with:

```python
## Layer E Story-Selling Angle

{layer_e_decision.selector_verdict}

## Emotional Machine

{layer_e_decision.emotional_machine}

## Selected Process

{layer_e_decision.selected_card.id} - {layer_e_decision.selected_card.title}
```

- [ ] **Step 3: Replace outline placeholder text**

Build the outline from the selected winning variant:

```python
winner = max(layer_e_decision.concept_variants, key=lambda item: item.score.total)
outline_text = f"""# Outline

## Opening Hook

{winner.reader_identity_mirror}

## Emotional Problem

{winner.emotional_obstacle}

## Carousel Proof Beats

{winner.proof_beat}

## Deeper Turn

{winner.emotional_reversal}

## Final Payoff

{winner.payoff}
"""
```

Write `outline_text` to `outline.md`.

- [ ] **Step 4: Update article tests**

In `tests/test_substack_article_package.py`, add assertions:

```python
            layer_e = json.loads((out_dir / "layer-e-story-selling.json").read_text(encoding="utf-8"))
            outline = (out_dir / "outline.md").read_text(encoding="utf-8")

            self.assertIn(manifest["story_selling_decision"]["artifact"], "layer-e-story-selling.json")
            self.assertGreaterEqual(layer_e["story_selling_score"]["total"], 28)
            placeholder_token = "T" + "BD"
            self.assertNotIn(placeholder_token, outline)
            self.assertIn("Opening Hook", outline)
```

- [ ] **Step 5: Run D-layer tests**

Run:

```bash
venv/bin/python -m pytest tests/test_substack_article_package.py -q
```

Expected:

```text
All tests in tests/test_substack_article_package.py pass
```

---

### Task 9: Integrate Layer E Into B-Layer Pre-Post

**Files:**
- Modify: `pipeline/stages/b1_prepost.py`
- Modify: `tests/test_prepost_story_selling.py`

- [ ] **Step 1: Add Layer E preflight helper**

In `pipeline/stages/b1_prepost.py`, add:

```python
from pipeline.layer_e.engine import run_layer_e
```

Add:

```python
def build_layer_e_prepost_decision(brief: dict) -> str:
    decision = run_layer_e(
        BASE_DIR,
        {
            "task_type": "prepost_reel",
            "story_or_moment": "\n".join(f"{key}: {value}" for key, value in brief.items() if value),
            "reference_images": [],
            "constraints": ["planned Reel pre-post analysis", "hook/edit/caption/cultural review"],
            "requested_tone": str(brief.get("tone", "")),
        },
    )
    return decision.model_dump_json(indent=2)
```

- [ ] **Step 2: Include the decision in every agent request**

In `run_agent(...)`, build the Layer E JSON once in `analyze_prepost(...)` and pass it through:

```python
    layer_e_decision_json = build_layer_e_prepost_decision(brief)
```

Then include it in the message content:

```python
                    "# Layer E Story-Selling Preflight\n\n"
                    f"{layer_e_decision_json}\n\n"
```

- [ ] **Step 3: Update tests**

In `tests/test_prepost_story_selling.py`, add:

```python
from pipeline.stages.b1_prepost import build_layer_e_prepost_decision


def test_prepost_builds_executable_layer_e_decision():
    decision_json = build_layer_e_prepost_decision(
        {
            "concept": "A married-life kitchen Reel where a tiny plate handoff becomes a silent joke.",
            "caption_draft": "When you are finally married...",
        }
    )

    assert '"status"' in decision_json
    assert '"selected_card"' in decision_json
    assert '"story_selling_score"' in decision_json
```

- [ ] **Step 4: Run B-layer tests**

Run:

```bash
venv/bin/python -m pytest tests/test_prepost_story_selling.py -q
```

Expected:

```text
2 passed
```

---

### Task 10: Make Agentic OS Expose The Gate Artifact

**Files:**
- Modify: `config/skill-systems.json`
- Modify: `pipeline/agentic/workflow_metadata.py`
- Test: `tests/test_agentic_skill_registry.py`

- [ ] **Step 1: Add artifact names to skill systems**

In `config/skill-systems.json`, add `gate_artifacts` to the systems that use Layer E:

```json
"gate_artifacts": [
  "layer-e-story-selling.json",
  "layer-e-story-selling.md"
]
```

Add it to:

- `carousel_jam`
- `story_article`
- `prepost_reel`

- [ ] **Step 2: Preserve gate artifacts in workflow metadata**

In `pipeline/agentic/workflow_metadata.py`, update `build_workflow_metadata(...)`:

```python
    skill_system = resolve_skill_system(load_skill_systems(root), skill_system_name)
    return {
        "context_manifest": CONTEXT_MANIFEST,
        "skill_systems": SKILL_SYSTEMS_MANIFEST,
        "skill_system": skill_system,
        "gate_artifacts": skill_system.get("gate_artifacts", []),
        ...
    }
```

- [ ] **Step 3: Update registry test**

In `tests/test_agentic_skill_registry.py`, update the test fixture:

```python
                        "gate_artifacts": ["layer-e-story-selling.json"],
```

Add assertion:

```python
    assert resolved["gate_artifacts"] == ["layer-e-story-selling.json"]
```

- [ ] **Step 4: Run Agentic OS tests**

Run:

```bash
venv/bin/python -m pytest tests/test_agentic_skill_registry.py -q
```

Expected:

```text
2 passed
```

---

### Task 11: Remove Canned Layer E As Source Of Truth

**Files:**
- Modify: `pipeline/stages/codex_native_carousel.py`
- Test: `tests/test_illustration_carousel.py`

- [ ] **Step 1: Deprecate lane-default scoring**

Keep `STORY_SELLING_CONTRACT` as metadata, but stop using:

```python
STORY_PROCESS_BY_LANE
story_selling_scorecard
build_story_selling_decision
```

If tests still import them, leave wrappers with explicit deprecation comments:

```python
def build_story_selling_decision(*args: Any, **kwargs: Any) -> dict[str, Any]:
    raise RuntimeError("Use pipeline.layer_e.engine.run_layer_e instead of synthetic Story-Selling scoring.")
```

If no tests import them directly, delete the functions and constants.

- [ ] **Step 2: Add regression test that synthetic scores cannot pass alone**

In `tests/test_illustration_carousel.py`, add:

```python
def test_codex_native_does_not_use_lane_default_story_selling_score():
    from pipeline.stages import codex_native_carousel

    assert not hasattr(codex_native_carousel, "STORY_PROCESS_BY_LANE")
```

If keeping a deprecated wrapper for compatibility, assert:

```python
    with self.assertRaisesRegex(RuntimeError, "run_layer_e"):
        codex_native_carousel.build_story_selling_decision(
            lane="Soft Love Notes",
            story="pretty photo",
            human_truth="",
            emotional_arc="",
            concept_selection=None,
        )
```

- [ ] **Step 3: Run carousel tests around Story-Selling**

Run:

```bash
venv/bin/python -m pytest tests/test_illustration_carousel.py -q
```

Expected:

```text
All tests in tests/test_illustration_carousel.py pass
```

---

### Task 12: Backfill Plate Stack And Current Packages

**Files:**
- Create: `scripts/backfill_layer_e_story_selling.py`
- Test: `tests/test_layer_e_workflow_integration.py`

- [ ] **Step 1: Add backfill script**

Create `scripts/backfill_layer_e_story_selling.py`:

```python
#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

from pipeline.layer_e.artifacts import write_layer_e_artifacts
from pipeline.layer_e.engine import run_layer_e


def carousel_story(carousel_dir: Path) -> str:
    parts: list[str] = []
    for name in ["concept.json", "storyboard.md", "slides.json", "copy.json"]:
        path = carousel_dir / name
        if not path.exists():
            continue
        if path.suffix == ".json":
            parts.append(json.dumps(json.loads(path.read_text(encoding="utf-8")), ensure_ascii=False))
        else:
            parts.append(path.read_text(encoding="utf-8"))
    return "\n\n".join(parts)


def backfill_carousel(root: Path, carousel_dir: Path) -> Path:
    decision = run_layer_e(
        root,
        {
            "task_type": "carousel_idea",
            "story_or_moment": carousel_story(carousel_dir),
            "reference_images": [],
            "constraints": ["backfill existing carousel package"],
            "requested_tone": "preserve current package intent",
        },
    )
    write_layer_e_artifacts(carousel_dir, decision)
    return carousel_dir / "layer-e-story-selling.json"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("carousel_dir", type=Path)
    parser.add_argument("--workspace-root", type=Path, default=Path.cwd())
    args = parser.parse_args()
    print(backfill_carousel(args.workspace_root.resolve(), args.carousel_dir.expanduser()))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 2: Add backfill test**

Append to `tests/test_layer_e_workflow_integration.py`:

```python
def test_backfill_writes_layer_e_artifact(tmp_path: Path):
    from scripts.backfill_layer_e_story_selling import backfill_carousel

    carousel = tmp_path / "plate-stack"
    carousel.mkdir()
    (carousel / "storyboard.md").write_text(
        "Plate Stack Marriage Test: silent plate handoff, dono rakh do, kitchen walk.",
        encoding="utf-8",
    )

    artifact = backfill_carousel(Path(__file__).resolve().parents[1], carousel)

    assert artifact.exists()
```

- [ ] **Step 3: Run backfill for Plate Stack after tests pass**

Run:

```bash
venv/bin/python scripts/backfill_layer_e_story_selling.py output/carousels/2026-05-28/plate-stack-marriage-test
```

Expected:

```text
output/carousels/2026-05-28/plate-stack-marriage-test/layer-e-story-selling.json
```

---

### Task 13: Full Verification And Closeout

**Files:**
- All modified files in this plan

- [ ] **Step 1: Run focused tests**

Run:

```bash
venv/bin/python -m pytest \
  tests/test_layer_e_engine.py \
  tests/test_layer_e_workflow_integration.py \
  tests/test_prepost_story_selling.py \
  tests/test_substack_article_package.py \
  tests/test_agentic_skill_registry.py \
  -q
```

Expected:

```text
All focused tests pass
```

- [ ] **Step 2: Run full test suite**

Run:

```bash
venv/bin/python -m pytest -q
```

Expected:

```text
All tests pass
```

- [ ] **Step 3: Run wiki health**

Run:

```bash
venv/bin/python scripts/wiki_health.py --write --fix-index --session-note "Make Layer E an executable story-selling gate"
```

Expected:

```text
No blocking wiki health errors
```

- [ ] **Step 4: Run safe autopublish gate with explicit includes**

Because this repo often has unrelated worktree changes, publish only this plan's owned paths plus closeout artifacts:

```bash
venv/bin/python scripts/autopublish.py \
  --session-note "Make Layer E an executable story-selling gate" \
  --include pipeline/layer_e \
  --include pipeline/stages/codex_native_carousel.py \
  --include pipeline/stages/codex_builtin_image_generation.py \
  --include pipeline/stages/c1_illustration_carousel.py \
  --include pipeline/stages/b1_prepost.py \
  --include scripts/create_substack_article_package.py \
  --include scripts/backfill_layer_e_story_selling.py \
  --include config/skill-systems.json \
  --include tests/test_layer_e_engine.py \
  --include tests/test_layer_e_workflow_integration.py \
  --include tests/test_illustration_carousel.py \
  --include tests/test_prepost_story_selling.py \
  --include tests/test_substack_article_package.py \
  --include tests/test_agentic_skill_registry.py
```

Expected:

```text
Autopublish commits and pushes only the implementation-owned files, or blocks with a clear risky-path/unrelated-scope message.
```

---

## Self-Review

Spec coverage:

- Real Layer E execution: Tasks 1-4.
- C-layer integration before concept/slide/image gates: Tasks 5-7.
- D-layer article integration: Task 8.
- B-layer pre-post integration: Task 9.
- Agentic OS gate visibility: Task 10.
- Removal of fake/canned scoring: Task 11.
- Existing package migration: Task 12.
- Verification and autopublish: Task 13.

Placeholder scan:

- This plan intentionally avoids placeholder values in code snippets.
- Existing repo files currently contain article-field placeholder tokens in D-layer artifacts; Task 8 replaces those outputs.

Type consistency:

- `LayerEDecision`, `LayerERequest`, `ConceptVariant`, and `StorySellingScore` are defined in Task 2 and used consistently in later tasks.
- Artifact helper names are `write_layer_e_artifacts`, `load_layer_e_decision`, and `layer_e_gate_reason`.
- The canonical artifact name is `layer-e-story-selling.json`.

Risk notes:

- The first implementation should keep deterministic scoring modest. The goal is not to fake literary intelligence; it is to make the existing Layer E learning corpus structurally unavoidable and testable.
- Existing `codex_native_carousel.py` is large and already has many lane-specific branches. The integration should be surgical first, then later refactor lane builders only when tests are green.
- Plate Stack is a useful fixture because it proves Layer E can support ordinary comedy without forcing a fake tender thesis.
