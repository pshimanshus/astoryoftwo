# Agentic OS Spine Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a repo-native agentic operating spine for @a.storyof.two that keeps the current carousel/article/pre-post systems, but adds explicit identity context, semantic recall, skill systems, guarded learning, audit logs, and technical learning checkpoints.

**Architecture:** Add a new `pipeline/agentic/` control plane beside the existing stage scripts. The control plane does not replace Layer E, C, D, B, or the wiki; it assembles context packs, indexes memory, composes reusable skill systems, records learning proposals, evaluates changes with external gates, and exposes one CLI for daily use.

**Tech Stack:** Python 3.13, pydantic v2, sqlite3 FTS5 from the standard library, pathlib/json/argparse, existing Markdown skills and agents, existing pytest suite, existing `scripts/wiki_health.py`.

---

## Transcript Read

The video transcript is arguing for a custom agentic setup over blindly installing an off-the-shelf agent OS.

The core claims are:

- Off-the-shelf systems are fast to start, but they smuggle in identity, memory, security, and learning-loop assumptions.
- A single `user.md` plus `memory.md` style identity layer works for one person or one business, but becomes awkward for multiple brands, clients, or content systems.
- Short-term memory injection is valuable, especially when capped and summarized, but keyword-only long-term recall becomes weak when the user cannot remember exact phrases.
- Automatic self-learning loops are risky when the same model writes a new skill and also grades the skill without external validation, versioning, or audit.
- Skills should become modular systems, not one-off task prompts that duplicate voice, audience, format, and client context.
- The better long-term setup is slower at first, but easier to debug, evolve, share across projects, and secure.

Treat the transcript as architecture input, not as verified market research. The exact GitHub star counts, vulnerability counts, and marketplace claims should not become repo facts unless separately verified from primary sources.

## Engineering Debate

### Position A: Install an external system

This gets a fast memory file, skill marketplace, and self-learning loop. It is attractive if the repo had no existing architecture. This project already has a strong local ontology: `AGENTS.md`, `config/skills/`, `agents/`, `memory/`, `wiki/`, `output/`, and deterministic quality gates. Installing an external system would duplicate this structure and hide important decisions behind someone else's runtime.

### Position B: Keep everything manual

This keeps maximum control and avoids automatic corruption. The downside is visible in the current repo: many hard gates live in Markdown, `pipeline/stages/codex_native_carousel.py` has grown to 5972 lines, and memory recall depends on a human or assistant reading the right files. Manual-only works until the number of skills, artifacts, and creator preferences grows beyond what a session can reliably load.

### Position C: Build a repo-native control plane

This is the best path. Keep the existing content architecture as the product, then add a thin executable spine that makes identity, memory, skills, learning, and audits queryable. The control plane should be boring, inspectable, and deterministic by default. It can propose changes, but it cannot approve or silently overwrite skills.

### Final Verdict

Build the custom repo-native spine. Do not auto-install Hermes-like systems. Do not add auto-writing skills without external validation. Add a modular skill-system registry, context assembler, memory search index, learning inbox, evaluator, and audit trail. Then integrate them into the C-layer, D-layer, B-layer, and wiki-health loop.

## Current Repo Assessment

### Existing strengths

- `AGENTS.md` is already a schema-level product file. It documents layers E, D, C, B, 1, 2, and 3.
- `config/skills/` contains operational skills for carousel, story-selling, pre-post, algorithm, and Substack work.
- `agents/` contains named specialist roles for C-layer, B-layer, and E-layer workflows.
- `memory/working.md`, `memory/semantic/`, `memory/episodic/`, and `memory/graph.json` already implement a Rohit v2 style memory lifecycle.
- `scripts/wiki_health.py` and `pipeline/stages/wiki_health.py` already write diagnostics, HEAL proposals, episodic records, and logs.
- The carousel system already has serious gates: golden-theme tournament, story-selling score, post-copy visual room, visual debate, visual-plan quality, identity review, final audit, and visual QA.

### Main gaps

- Identity is scattered across `AGENTS.md`, `CLAUDE.md`, `config/voice.md`, `config/channel.py`, `config/carousel_style_contract.json`, and identity images. There is no explicit context pack manifest or context budget.
- Memory exists as files, but recall is not a first-class executable service. There is no semantic or FTS index and no ranked retrieval with citations.
- Skills exist as Markdown, but there is no registry with stable IDs, owners, dependency graph, versions, evaluation status, or duplicate detection.
- Skill composition is hard-coded in places like `pipeline/stages/c1_illustration_carousel.py` and `pipeline/stages/codex_native_carousel.py`.
- The learning loop is human-managed. That is safer than blind self-learning, but it misses structured proposals, snapshots, and eval gates.
- There is no general audit log for agentic decisions outside carousel/package-specific artifacts and wiki health.
- The workspace is not currently a git repository, so versioning must work through snapshots and JSONL logs even before git is introduced.

## Target Architecture

Add a new control plane:

```text
pipeline/
  agentic/
    __init__.py
    contracts.py
    context_loader.py
    skill_registry.py
    memory_index.py
    recall.py
    audit_log.py
    learning_loop.py
    skill_eval.py
    workflow_state.py

config/
  agentic_context_manifest.json
  skill-systems.json

memory/
  agentic/
    audit/
    index/
    learning-events/
    learning-proposals/
    snapshots/

scripts/
  agentic_os.py

tests/
  test_agentic_contracts.py
  test_agentic_context_loader.py
  test_agentic_skill_registry.py
  test_agentic_memory_index.py
  test_agentic_recall.py
  test_agentic_learning_loop.py
  test_agentic_skill_eval.py
  test_agentic_cli.py
```

The spine has five explicit loops:

1. Context loop: assemble the right identity, brand, workflow, and memory files within a token budget.
2. Recall loop: search working memory first, semantic/wiki memory second, graph/artifact metadata third.
3. Skill-system loop: compose small reusable skills into workflow systems without duplicating brand voice or audience.
4. Learning loop: capture events, propose changes, snapshot originals, evaluate externally, then require approval.
5. Audit loop: record who/what changed, why it changed, what evidence supported it, and how to roll it back.

## File Structure

- Create: `pipeline/agentic/__init__.py`
  - Marks the new control plane package.
- Create: `pipeline/agentic/contracts.py`
  - Pydantic models for context packs, memory records, skill records, learning proposals, audits, and workflow gates.
- Create: `config/agentic_context_manifest.json`
  - Source of truth for user, brand, project, workflow, and memory context packs.
- Create: `pipeline/agentic/context_loader.py`
  - Loads manifest paths, estimates token budget, summarizes oversized files safely, and emits a provenance-rich context pack.
- Create: `config/skill-systems.json`
  - Declares reusable skill systems such as `carousel_jam`, `story_article`, `prepost_reel`, and `wiki_health`.
- Create: `pipeline/agentic/skill_registry.py`
  - Discovers skills/agents, parses metadata and skill refs, detects duplicates, and resolves skill systems.
- Create: `pipeline/agentic/memory_index.py`
  - Builds a sqlite FTS index over memory, wiki, skills, docs, reports, and selected output metadata.
- Create: `pipeline/agentic/recall.py`
  - Combines injected context plus indexed recall into ranked, cited memory bundles.
- Create: `pipeline/agentic/audit_log.py`
  - Writes append-only JSONL decisions and before/after snapshots for changed Markdown/JSON files.
- Create: `pipeline/agentic/learning_loop.py`
  - Captures learning events and creates proposal files instead of auto-editing skills.
- Create: `pipeline/agentic/skill_eval.py`
  - Evaluates proposed skill/context/memory changes with deterministic gates.
- Create: `pipeline/agentic/workflow_state.py`
  - Shared GO / REPAIR / STOP and PASS / FAIL state helpers for future orchestration.
- Create: `scripts/agentic_os.py`
  - CLI for context, registry, index, search, propose-learning, evaluate-learning, and health commands.
- Modify: `pipeline/stages/c1_illustration_carousel.py`
  - Replace ad hoc context loading with `pipeline.agentic.context_loader`.
- Modify: `pipeline/stages/codex_native_carousel.py`
  - Load skill systems and recall bundles through the control plane before deterministic packaging.
- Modify: `scripts/analyze_prepost.py`
  - Use `prepost_reel` skill system and recall pack for B-layer analysis.
- Modify: `scripts/create_substack_article_package.py`
  - Use `story_article` skill system and recall pack for D-layer articles.
- Modify: `AGENTS.md`
  - Document the Agentic OS control plane after implementation.
- Modify: `CLAUDE.md`
  - Add a short reading-order pointer to the context manifest and CLI.
- Test: add the new `tests/test_agentic_*.py` files listed above.

Current workspace note: `/Users/himanshusharma/astoryoftwo-analysis` is not a git repository. If implementation happens without git, each task must create audit snapshots and the final answer must report changed files instead of commits. If git is initialized later, commit after each task.

---

### Task 1: Add Core Agentic Contracts

**Files:**
- Create: `pipeline/agentic/__init__.py`
- Create: `pipeline/agentic/contracts.py`
- Test: `tests/test_agentic_contracts.py`

- [ ] **Step 1: Write failing contract tests**

Create `tests/test_agentic_contracts.py`:

```python
import pytest
from pydantic import ValidationError

from pipeline.agentic.contracts import (
    AuditEvent,
    ContextPack,
    LearningProposal,
    MemoryRecord,
    SkillRecord,
)


def test_context_pack_requires_budget_and_provenance():
    pack = ContextPack(
        profile="a-story-of-two",
        budget_tokens=1300,
        estimated_tokens=84,
        sections=[
            {
                "id": "voice",
                "path": "config/voice.md",
                "kind": "brand_voice",
                "estimated_tokens": 84,
                "content": "Warm intimate voice.",
            }
        ],
    )

    assert pack.profile == "a-story-of-two"
    assert pack.sections[0].path == "config/voice.md"
    assert pack.estimated_tokens <= pack.budget_tokens


def test_skill_record_requires_stable_id_and_path():
    record = SkillRecord(
        skill_id="carousel.story-director-persona",
        name="carousel-story-director-persona",
        kind="skill",
        path="config/skills/carousel-story-director-persona.md",
        description="Hook, story, bridge, ending, and send/save persona.",
        dependencies=["golden-viral-carousel-theme"],
        confidence=0.96,
    )

    assert record.skill_id == "carousel.story-director-persona"
    assert record.dependencies == ["golden-viral-carousel-theme"]


def test_memory_record_rejects_missing_confidence():
    with pytest.raises(ValidationError):
        MemoryRecord(
            record_id="semantic.carousel-preferences",
            path="memory/semantic/carousel-idea-preferences.md",
            title="Carousel Idea Preferences",
            kind="semantic",
            text="fact: avoid repeating cooled down ideas",
            tags=["carousel", "preferences"],
        )


def test_learning_proposal_defaults_to_proposal_only():
    proposal = LearningProposal(
        proposal_id="learn-2026-05-25-context-pack",
        source_event_id="event-1",
        target_path="config/skills/golden-viral-carousel-theme.md",
        proposed_action="modify",
        rationale="Persist the new context-pack gate.",
        before_hash="abc",
        after_hash="def",
        required_validators=["skill_eval", "pytest"],
    )

    assert proposal.status == "draft"
    assert proposal.auto_apply is False
    assert "skill_eval" in proposal.required_validators


def test_audit_event_has_append_only_shape():
    event = AuditEvent(
        event_id="audit-1",
        event_type="learning_proposal_created",
        actor="codex",
        target_path="memory/agentic/learning-proposals/p1.json",
        summary="Created a proposal.",
        evidence_paths=["memory/agentic/learning-events/e1.json"],
    )

    assert event.event_type == "learning_proposal_created"
    assert event.evidence_paths == ["memory/agentic/learning-events/e1.json"]
```

- [ ] **Step 2: Run tests and confirm they fail**

Run:

```bash
venv/bin/python -m pytest tests/test_agentic_contracts.py -v
```

Expected: FAIL with `ModuleNotFoundError: No module named 'pipeline.agentic'`.

- [ ] **Step 3: Implement contracts**

Create `pipeline/agentic/__init__.py`:

```python
"""Repo-native agentic operating spine for @a.storyof.two."""
```

Create `pipeline/agentic/contracts.py`:

```python
from __future__ import annotations

from datetime import datetime, timezone
from typing import Literal

from pydantic import BaseModel, Field, field_validator


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


class ContextSection(BaseModel):
    id: str
    path: str
    kind: str
    estimated_tokens: int = Field(ge=0)
    content: str
    truncated: bool = False
    summary: str | None = None


class ContextPack(BaseModel):
    schema_version: str = "1.0"
    profile: str
    budget_tokens: int = Field(ge=1)
    estimated_tokens: int = Field(ge=0)
    sections: list[ContextSection]
    created_at: str = Field(default_factory=utc_now)

    @field_validator("sections")
    @classmethod
    def require_sections(cls, value: list[ContextSection]) -> list[ContextSection]:
        if not value:
            raise ValueError("ContextPack must include at least one section.")
        return value


class SkillRecord(BaseModel):
    schema_version: str = "1.0"
    skill_id: str
    name: str
    kind: Literal["skill", "agent", "system"]
    path: str
    description: str
    dependencies: list[str] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)
    confidence: float = Field(ge=0, le=1)
    content_hash: str | None = None


class MemoryRecord(BaseModel):
    schema_version: str = "1.0"
    record_id: str
    path: str
    title: str
    kind: Literal["working", "semantic", "episodic", "wiki", "graph", "report", "skill", "doc"]
    text: str
    tags: list[str] = Field(default_factory=list)
    confidence: float = Field(ge=0, le=1)
    sources: list[str] = Field(default_factory=list)
    last_updated: str | None = None


class RecallHit(BaseModel):
    record_id: str
    path: str
    title: str
    score: float
    snippet: str
    kind: str
    confidence: float = Field(ge=0, le=1)


class LearningProposal(BaseModel):
    schema_version: str = "1.0"
    proposal_id: str
    source_event_id: str
    target_path: str
    proposed_action: Literal["create", "modify", "supersede", "archive"]
    rationale: str
    before_hash: str
    after_hash: str
    required_validators: list[str]
    status: Literal["draft", "evaluated", "approved", "rejected", "applied"] = "draft"
    auto_apply: bool = False
    created_at: str = Field(default_factory=utc_now)


class AuditEvent(BaseModel):
    schema_version: str = "1.0"
    event_id: str
    event_type: str
    actor: str
    target_path: str
    summary: str
    evidence_paths: list[str] = Field(default_factory=list)
    created_at: str = Field(default_factory=utc_now)
```

- [ ] **Step 4: Run tests and confirm they pass**

Run:

```bash
venv/bin/python -m pytest tests/test_agentic_contracts.py -v
```

Expected: PASS, 5 tests.

---

### Task 2: Add Context Manifest And Context Loader

**Files:**
- Create: `config/agentic_context_manifest.json`
- Create: `pipeline/agentic/context_loader.py`
- Test: `tests/test_agentic_context_loader.py`

- [ ] **Step 1: Write failing context loader tests**

Create `tests/test_agentic_context_loader.py`:

```python
import json
from pathlib import Path

from pipeline.agentic.context_loader import assemble_context_pack, estimate_tokens


def test_estimate_tokens_is_deterministic():
    assert estimate_tokens("one two three four") == 1
    assert estimate_tokens("x" * 400) == 100


def test_assemble_context_pack_loads_profile_with_provenance(tmp_path: Path):
    root = tmp_path
    (root / "config").mkdir()
    (root / "memory").mkdir()
    (root / "config" / "voice.md").write_text("Warm voice " * 20, encoding="utf-8")
    (root / "memory" / "working.md").write_text("Working memory " * 20, encoding="utf-8")
    manifest = {
        "schema_version": "1.0",
        "default_profile": "a-story-of-two",
        "profiles": {
            "a-story-of-two": {
                "budget_tokens": 80,
                "sections": [
                    {"id": "voice", "path": "config/voice.md", "kind": "brand_voice", "required": True},
                    {"id": "working", "path": "memory/working.md", "kind": "working_memory", "required": True}
                ]
            }
        }
    }
    (root / "config" / "agentic_context_manifest.json").write_text(
        json.dumps(manifest),
        encoding="utf-8",
    )

    pack = assemble_context_pack(root, profile="a-story-of-two")

    assert pack.profile == "a-story-of-two"
    assert [section.id for section in pack.sections] == ["voice", "working"]
    assert pack.estimated_tokens <= pack.budget_tokens
    assert pack.sections[0].path == "config/voice.md"


def test_assemble_context_pack_rejects_missing_required_file(tmp_path: Path):
    root = tmp_path
    (root / "config").mkdir()
    manifest = {
        "schema_version": "1.0",
        "default_profile": "a-story-of-two",
        "profiles": {
            "a-story-of-two": {
                "budget_tokens": 80,
                "sections": [
                    {"id": "voice", "path": "config/voice.md", "kind": "brand_voice", "required": True}
                ]
            }
        }
    }
    (root / "config" / "agentic_context_manifest.json").write_text(
        json.dumps(manifest),
        encoding="utf-8",
    )

    try:
        assemble_context_pack(root, profile="a-story-of-two")
    except FileNotFoundError as exc:
        assert "config/voice.md" in str(exc)
    else:
        raise AssertionError("missing required file must raise")
```

- [ ] **Step 2: Run tests and confirm they fail**

Run:

```bash
venv/bin/python -m pytest tests/test_agentic_context_loader.py -v
```

Expected: FAIL with `ModuleNotFoundError` or missing `assemble_context_pack`.

- [ ] **Step 3: Add the manifest**

Create `config/agentic_context_manifest.json`:

```json
{
  "schema_version": "1.0",
  "default_profile": "a-story-of-two",
  "profiles": {
    "a-story-of-two": {
      "budget_tokens": 1800,
      "sections": [
        {
          "id": "channel_voice",
          "path": "config/voice.md",
          "kind": "brand_voice",
          "required": true
        },
        {
          "id": "working_memory",
          "path": "memory/working.md",
          "kind": "working_memory",
          "required": true
        },
        {
          "id": "carousel_preferences",
          "path": "memory/semantic/carousel-idea-preferences.md",
          "kind": "semantic_memory",
          "required": true
        },
        {
          "id": "gold_theme",
          "path": "wiki/themes/calm-enough-for-chaos.md",
          "kind": "wiki_theme",
          "required": true
        },
        {
          "id": "style_contract",
          "path": "config/carousel_style_contract.json",
          "kind": "visual_identity",
          "required": true
        }
      ]
    },
    "article": {
      "budget_tokens": 1800,
      "sections": [
        {
          "id": "channel_voice",
          "path": "config/voice.md",
          "kind": "brand_voice",
          "required": true
        },
        {
          "id": "substack_framework",
          "path": "config/skills/couple-substack-article-framework.md",
          "kind": "workflow_skill",
          "required": true
        },
        {
          "id": "growth_reference",
          "path": "config/references/couple-substack-growth-reference.md",
          "kind": "growth_reference",
          "required": true
        }
      ]
    }
  }
}
```

- [ ] **Step 4: Implement context loader**

Create `pipeline/agentic/context_loader.py`:

```python
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from pipeline.agentic.contracts import ContextPack, ContextSection


MANIFEST_PATH = Path("config") / "agentic_context_manifest.json"


def estimate_tokens(text: str) -> int:
    return max(1, len(text) // 4) if text else 0


def load_manifest(root: Path) -> dict[str, Any]:
    path = root / MANIFEST_PATH
    if not path.exists():
        raise FileNotFoundError(f"Missing context manifest: {MANIFEST_PATH}")
    return json.loads(path.read_text(encoding="utf-8"))


def compact_content(content: str, token_limit: int) -> tuple[str, bool, str | None]:
    if estimate_tokens(content) <= token_limit:
        return content, False, None
    keep_chars = max(200, token_limit * 4)
    head = content[: keep_chars // 2].strip()
    tail = content[-keep_chars // 2 :].strip()
    summary = (
        "Content compacted by deterministic head/tail extraction. "
        "Use full file from provenance path when exact wording matters."
    )
    return f"{head}\n\n[...compacted...]\n\n{tail}", True, summary


def assemble_context_pack(root: Path, profile: str | None = None) -> ContextPack:
    root = root.resolve()
    manifest = load_manifest(root)
    profile_name = profile or manifest["default_profile"]
    profiles = manifest.get("profiles", {})
    if profile_name not in profiles:
        raise ValueError(f"Unknown context profile: {profile_name}")

    profile_config = profiles[profile_name]
    budget = int(profile_config["budget_tokens"])
    section_configs = list(profile_config.get("sections", []))
    per_section_limit = max(80, budget // max(1, len(section_configs)))
    sections: list[ContextSection] = []

    for section_config in section_configs:
        rel_path = Path(section_config["path"])
        abs_path = root / rel_path
        required = bool(section_config.get("required", False))
        if not abs_path.exists():
            if required:
                raise FileNotFoundError(f"Missing required context file: {rel_path.as_posix()}")
            continue
        raw = abs_path.read_text(encoding="utf-8")
        content, truncated, summary = compact_content(raw, per_section_limit)
        sections.append(
            ContextSection(
                id=section_config["id"],
                path=rel_path.as_posix(),
                kind=section_config["kind"],
                estimated_tokens=estimate_tokens(content),
                content=content,
                truncated=truncated,
                summary=summary,
            )
        )

    estimated = sum(section.estimated_tokens for section in sections)
    if estimated > budget and sections:
        scale_limit = max(80, budget // len(sections))
        repaired: list[ContextSection] = []
        for section in sections:
            content, truncated, summary = compact_content(section.content, scale_limit)
            repaired.append(
                section.model_copy(
                    update={
                        "content": content,
                        "estimated_tokens": estimate_tokens(content),
                        "truncated": section.truncated or truncated,
                        "summary": section.summary or summary,
                    }
                )
            )
        sections = repaired
        estimated = sum(section.estimated_tokens for section in sections)

    return ContextPack(
        profile=profile_name,
        budget_tokens=budget,
        estimated_tokens=estimated,
        sections=sections,
    )


def render_context_pack(pack: ContextPack) -> str:
    lines = [
        f"# Context Pack: {pack.profile}",
        f"budget_tokens: {pack.budget_tokens}",
        f"estimated_tokens: {pack.estimated_tokens}",
        "",
    ]
    for section in pack.sections:
        lines.extend(
            [
                f"## {section.id}",
                f"path: {section.path}",
                f"kind: {section.kind}",
                f"truncated: {str(section.truncated).lower()}",
                "",
                section.content,
                "",
            ]
        )
    return "\n".join(lines).strip() + "\n"
```

- [ ] **Step 5: Run context tests**

Run:

```bash
venv/bin/python -m pytest tests/test_agentic_context_loader.py -v
```

Expected: PASS, 3 tests.

---

### Task 3: Add Skill Registry And Skill Systems

**Files:**
- Create: `config/skill-systems.json`
- Create: `pipeline/agentic/skill_registry.py`
- Test: `tests/test_agentic_skill_registry.py`

- [ ] **Step 1: Write failing registry tests**

Create `tests/test_agentic_skill_registry.py`:

```python
import json
from pathlib import Path

from pipeline.agentic.skill_registry import (
    discover_skill_records,
    load_skill_systems,
    resolve_skill_system,
)


def test_discover_skill_records_reads_markdown_skills(tmp_path: Path):
    root = tmp_path
    (root / "config" / "skills").mkdir(parents=True)
    (root / "agents").mkdir()
    (root / "config" / "skills" / "alpha-skill.md").write_text(
        "# Alpha Skill\n\nconfidence: 0.8\n\n## Purpose\n\nDoes alpha work.\n",
        encoding="utf-8",
    )
    (root / "agents" / "beta-agent.md").write_text(
        "# beta-agent\n# skill_refs:\n#   - config/skills/alpha-skill.md\n",
        encoding="utf-8",
    )

    records = discover_skill_records(root)

    ids = {record.skill_id for record in records}
    assert "skill.alpha-skill" in ids
    assert "agent.beta-agent" in ids


def test_resolve_skill_system_expands_ordered_components(tmp_path: Path):
    root = tmp_path
    (root / "config").mkdir()
    (root / "config" / "skill-systems.json").write_text(
        json.dumps(
            {
                "schema_version": "1.0",
                "systems": {
                    "carousel_jam": {
                        "description": "Carousel jam workflow.",
                        "components": [
                            "config/skills/romance-story-selling-engine.md",
                            "config/skills/golden-viral-carousel-theme.md"
                        ]
                    }
                }
            }
        ),
        encoding="utf-8",
    )

    systems = load_skill_systems(root)
    resolved = resolve_skill_system(systems, "carousel_jam")

    assert resolved["name"] == "carousel_jam"
    assert resolved["components"][0] == "config/skills/romance-story-selling-engine.md"
```

- [ ] **Step 2: Run tests and confirm they fail**

Run:

```bash
venv/bin/python -m pytest tests/test_agentic_skill_registry.py -v
```

Expected: FAIL with missing module or functions.

- [ ] **Step 3: Add skill-system manifest**

Create `config/skill-systems.json`:

```json
{
  "schema_version": "1.0",
  "systems": {
    "carousel_jam": {
      "description": "Creator jam to final carousel workflow.",
      "components": [
        "config/skills/carousel-jam-autopilot.md",
        "config/skills/continuous-carousel-agent-room.md",
        "config/skills/romance-story-selling-engine.md",
        "config/skills/golden-viral-carousel-theme.md",
        "config/skills/carousel-story-director-persona.md",
        "config/skills/illustration-carousel-framework.md",
        "config/skills/indian-creator-intelligence.md"
      ],
      "agents": [
        "agents/carousel-story-director.md",
        "agents/carousel-post-copy-visual-room-orchestrator.md",
        "agents/carousel-visual-evidence-planner.md",
        "agents/carousel-romance-scene-planner.md",
        "agents/carousel-visual-continuity-judge.md"
      ],
      "gates": [
        "story_selling_28",
        "golden_theme_28",
        "story_director_8_each",
        "post_copy_visual_room_go",
        "visual_debate_go",
        "visual_plan_quality_go",
        "identity_consistency_pass"
      ]
    },
    "story_article": {
      "description": "Carousel or love story to Substack article workflow.",
      "components": [
        "config/skills/romance-story-selling-engine.md",
        "config/skills/couple-substack-article-framework.md",
        "config/references/couple-substack-growth-reference.md"
      ],
      "agents": [
        "agents/story-canon-orchestrator.md",
        "agents/story-skill-reviewer.md"
      ],
      "gates": [
        "source_integrity",
        "love_theme_fit",
        "image_reference_fit",
        "article_structure",
        "voice_and_taste",
        "growth_package",
        "final_publish_approval"
      ]
    },
    "prepost_reel": {
      "description": "Planned Reel analysis and reach-recovery workflow.",
      "components": [
        "config/skills/romance-story-selling-engine.md",
        "config/skills/instagram-algorithm-2026.md",
        "config/skills/hook-and-edit-framework.md",
        "config/skills/indian-creator-intelligence.md"
      ],
      "agents": [
        "agents/prepost-orchestrator.md",
        "agents/hook-analyzer.md",
        "agents/edit-auditor.md",
        "agents/algorithm-scorer.md",
        "agents/caption-advisor.md",
        "agents/cultural-resonance.md"
      ],
      "gates": [
        "hook_score_min_5",
        "dm_send_potential_min_10",
        "cultural_authenticity_min_5",
        "audio_plan_penalty"
      ]
    },
    "wiki_health": {
      "description": "Session close memory and wiki health workflow.",
      "components": [
        "AGENTS.md",
        "CLAUDE.md"
      ],
      "agents": [],
      "gates": [
        "memory_surface",
        "advertised_pipeline_files",
        "wiki_index_total_pages",
        "wiki_markdown_metadata",
        "semantic_memory_confidence",
        "episodic_records",
        "session_logs"
      ]
    }
  }
}
```

- [ ] **Step 4: Implement registry**

Create `pipeline/agentic/skill_registry.py`:

```python
from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Any

from pipeline.agentic.contracts import SkillRecord


SYSTEMS_PATH = Path("config") / "skill-systems.json"


def content_hash(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def extract_confidence(text: str, default: float = 0.5) -> float:
    match = re.search(r"(?m)^confidence:\s*([0-9.]+)\s*$", text)
    if not match:
        return default
    value = float(match.group(1))
    return max(0.0, min(1.0, value))


def extract_title(text: str, fallback: str) -> str:
    match = re.search(r"(?m)^#\s+(.+?)\s*$", text)
    return match.group(1).strip() if match else fallback


def extract_agent_skill_refs(text: str) -> list[str]:
    refs: list[str] = []
    for match in re.finditer(r"(?m)^#\s+-\s+(config/skills/[A-Za-z0-9_.-]+\.md)\s*$", text):
        refs.append(match.group(1))
    return refs


def discover_skill_records(root: Path) -> list[SkillRecord]:
    root = root.resolve()
    records: list[SkillRecord] = []

    for path in sorted((root / "config" / "skills").glob("*.md")):
        text = path.read_text(encoding="utf-8")
        rel = path.relative_to(root).as_posix()
        name = path.stem
        records.append(
            SkillRecord(
                skill_id=f"skill.{name}",
                name=name,
                kind="skill",
                path=rel,
                description=extract_title(text, name),
                dependencies=[],
                tags=["skill"],
                confidence=extract_confidence(text),
                content_hash=content_hash(text),
            )
        )

    for path in sorted((root / "agents").glob("*.md")):
        text = path.read_text(encoding="utf-8")
        rel = path.relative_to(root).as_posix()
        name = path.stem
        records.append(
            SkillRecord(
                skill_id=f"agent.{name}",
                name=name,
                kind="agent",
                path=rel,
                description=extract_title(text, name),
                dependencies=extract_agent_skill_refs(text),
                tags=["agent"],
                confidence=extract_confidence(text, default=0.6),
                content_hash=content_hash(text),
            )
        )

    return records


def load_skill_systems(root: Path) -> dict[str, Any]:
    path = root / SYSTEMS_PATH
    if not path.exists():
        raise FileNotFoundError(f"Missing skill system manifest: {SYSTEMS_PATH}")
    return json.loads(path.read_text(encoding="utf-8"))


def resolve_skill_system(systems: dict[str, Any], name: str) -> dict[str, Any]:
    system = systems.get("systems", {}).get(name)
    if not system:
        raise ValueError(f"Unknown skill system: {name}")
    return {
        "name": name,
        "description": system.get("description", ""),
        "components": list(system.get("components", [])),
        "agents": list(system.get("agents", [])),
        "gates": list(system.get("gates", [])),
    }
```

- [ ] **Step 5: Run registry tests**

Run:

```bash
venv/bin/python -m pytest tests/test_agentic_skill_registry.py -v
```

Expected: PASS, 2 tests.

---

### Task 4: Add Memory Index With Meaning-Oriented Metadata

**Files:**
- Create: `pipeline/agentic/memory_index.py`
- Test: `tests/test_agentic_memory_index.py`

- [ ] **Step 1: Write failing memory index tests**

Create `tests/test_agentic_memory_index.py`:

```python
from pathlib import Path

from pipeline.agentic.memory_index import build_memory_index, search_memory


def test_build_memory_index_finds_semantic_memory(tmp_path: Path):
    root = tmp_path
    (root / "memory" / "semantic").mkdir(parents=True)
    (root / "wiki" / "themes").mkdir(parents=True)
    (root / "memory" / "semantic" / "carousel-idea-preferences.md").write_text(
        "# Carousel Idea Preferences\n\n"
        "last_updated: 2026-05-24\n"
        "confidence: 0.99\n"
        "sources:\n"
        "- creator chat\n\n"
        "fact: Avoid repeating wallet audit money jokes unless the creator asks.\n",
        encoding="utf-8",
    )

    index_path = build_memory_index(root)
    hits = search_memory(index_path, "money wallet joke", limit=3)

    assert hits
    assert hits[0].path == "memory/semantic/carousel-idea-preferences.md"
    assert hits[0].confidence == 0.99


def test_search_memory_returns_empty_for_no_index(tmp_path: Path):
    hits = search_memory(tmp_path / "missing.sqlite", "anything", limit=3)
    assert hits == []
```

- [ ] **Step 2: Run tests and confirm they fail**

Run:

```bash
venv/bin/python -m pytest tests/test_agentic_memory_index.py -v
```

Expected: FAIL with missing module or functions.

- [ ] **Step 3: Implement memory index**

Create `pipeline/agentic/memory_index.py`:

```python
from __future__ import annotations

import re
import sqlite3
from pathlib import Path

from pipeline.agentic.contracts import MemoryRecord, RecallHit


INDEX_PATH = Path("memory") / "agentic" / "index" / "memory.sqlite"
INDEXED_GLOBS = [
    ("memory/working.md", "working"),
    ("memory/semantic/*.md", "semantic"),
    ("memory/episodic/*.md", "episodic"),
    ("wiki/**/*.md", "wiki"),
    ("config/skills/*.md", "skill"),
    ("docs/**/*.md", "doc"),
    ("output/reports/*.md", "report"),
]


def extract_confidence(text: str, default: float = 0.5) -> float:
    match = re.search(r"(?m)^confidence:\s*([0-9.]+)\s*$", text)
    if not match:
        return default
    return max(0.0, min(1.0, float(match.group(1))))


def extract_sources(text: str) -> list[str]:
    match = re.search(r"(?ms)^sources:\s*\n((?:-\s+.+\n?)+)", text)
    if not match:
        return []
    return [line[2:].strip() for line in match.group(1).splitlines() if line.startswith("- ")]


def extract_title(path: Path, text: str) -> str:
    match = re.search(r"(?m)^#\s+(.+?)\s*$", text)
    return match.group(1).strip() if match else path.stem.replace("-", " ").title()


def extract_tags(path: Path, text: str) -> list[str]:
    tags = set(path.parts)
    for match in re.finditer(r"(?i)\b(carousel|article|prepost|golden|wallet|visual|identity|story|memory|skill|agent)\b", text):
        tags.add(match.group(1).lower())
    return sorted(tags)


def iter_memory_records(root: Path) -> list[MemoryRecord]:
    root = root.resolve()
    records: list[MemoryRecord] = []
    for pattern, kind in INDEXED_GLOBS:
        for path in sorted(root.glob(pattern)):
            if not path.is_file():
                continue
            text = path.read_text(encoding="utf-8")
            rel = path.relative_to(root).as_posix()
            records.append(
                MemoryRecord(
                    record_id=rel.replace("/", "."),
                    path=rel,
                    title=extract_title(path, text),
                    kind=kind if kind != "wiki" else "wiki",
                    text=text,
                    tags=extract_tags(path, text),
                    confidence=extract_confidence(text),
                    sources=extract_sources(text),
                )
            )
    return records


def open_index(path: Path) -> sqlite3.Connection:
    path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(path)
    connection.execute(
        "CREATE TABLE IF NOT EXISTS memory_records ("
        "record_id TEXT PRIMARY KEY, path TEXT, title TEXT, kind TEXT, "
        "confidence REAL, tags TEXT, sources TEXT, text TEXT)"
    )
    connection.execute(
        "CREATE VIRTUAL TABLE IF NOT EXISTS memory_fts USING fts5("
        "record_id UNINDEXED, title, body, tags)"
    )
    return connection


def build_memory_index(root: Path, index_path: Path | None = None) -> Path:
    root = root.resolve()
    path = index_path or (root / INDEX_PATH)
    records = iter_memory_records(root)
    connection = open_index(path)
    with connection:
        connection.execute("DELETE FROM memory_records")
        connection.execute("DELETE FROM memory_fts")
        for record in records:
            connection.execute(
                "INSERT INTO memory_records VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    record.record_id,
                    record.path,
                    record.title,
                    record.kind,
                    record.confidence,
                    " ".join(record.tags),
                    "\n".join(record.sources),
                    record.text,
                ),
            )
            connection.execute(
                "INSERT INTO memory_fts(record_id, title, body, tags) VALUES (?, ?, ?, ?)",
                (record.record_id, record.title, record.text, " ".join(record.tags)),
            )
    connection.close()
    return path


def make_snippet(text: str, query: str, length: int = 260) -> str:
    lowered = text.lower()
    tokens = [token.lower() for token in re.findall(r"[a-z0-9]+", query)]
    positions = [lowered.find(token) for token in tokens if lowered.find(token) >= 0]
    start = max(0, min(positions) - 80) if positions else 0
    snippet = text[start : start + length].replace("\n", " ").strip()
    return snippet


def search_memory(index_path: Path, query: str, limit: int = 8) -> list[RecallHit]:
    if not index_path.exists():
        return []
    connection = sqlite3.connect(index_path)
    connection.row_factory = sqlite3.Row
    try:
        rows = connection.execute(
            "SELECT r.record_id, r.path, r.title, r.kind, r.confidence, r.text, "
            "bm25(memory_fts) AS rank "
            "FROM memory_fts JOIN memory_records r ON memory_fts.record_id = r.record_id "
            "WHERE memory_fts MATCH ? "
            "ORDER BY rank LIMIT ?",
            (query, limit),
        ).fetchall()
    except sqlite3.OperationalError:
        rows = []
    finally:
        connection.close()

    hits: list[RecallHit] = []
    for row in rows:
        score = 1.0 / (1.0 + abs(float(row["rank"])))
        hits.append(
            RecallHit(
                record_id=row["record_id"],
                path=row["path"],
                title=row["title"],
                kind=row["kind"],
                confidence=float(row["confidence"]),
                score=score,
                snippet=make_snippet(row["text"], query),
            )
        )
    return hits
```

- [ ] **Step 4: Run memory index tests**

Run:

```bash
venv/bin/python -m pytest tests/test_agentic_memory_index.py -v
```

Expected: PASS, 2 tests.

---

### Task 5: Add Recall Bundles

**Files:**
- Create: `pipeline/agentic/recall.py`
- Test: `tests/test_agentic_recall.py`

- [ ] **Step 1: Write failing recall tests**

Create `tests/test_agentic_recall.py`:

```python
from pathlib import Path

from pipeline.agentic.memory_index import build_memory_index
from pipeline.agentic.recall import build_recall_bundle, render_recall_bundle


def test_recall_bundle_combines_context_and_search(tmp_path: Path):
    root = tmp_path
    (root / "config").mkdir()
    (root / "memory" / "semantic").mkdir(parents=True)
    (root / "config" / "voice.md").write_text("Warm voice.", encoding="utf-8")
    (root / "memory" / "semantic" / "prefs.md").write_text(
        "# Preferences\n\nconfidence: 0.9\nsources:\n- chat\n\n"
        "fact: Wallet audit is a cooled-down lane after reach recovery.\n",
        encoding="utf-8",
    )
    (root / "config" / "agentic_context_manifest.json").write_text(
        '{"schema_version":"1.0","default_profile":"a-story-of-two","profiles":{"a-story-of-two":{"budget_tokens":400,"sections":[{"id":"voice","path":"config/voice.md","kind":"voice","required":true}]}}}',
        encoding="utf-8",
    )
    index_path = build_memory_index(root)

    bundle = build_recall_bundle(root, query="wallet audit", profile="a-story-of-two", index_path=index_path)
    rendered = render_recall_bundle(bundle)

    assert bundle["context"].profile == "a-story-of-two"
    assert bundle["hits"][0].path == "memory/semantic/prefs.md"
    assert "wallet audit" in rendered.lower()
```

- [ ] **Step 2: Run tests and confirm they fail**

Run:

```bash
venv/bin/python -m pytest tests/test_agentic_recall.py -v
```

Expected: FAIL with missing module.

- [ ] **Step 3: Implement recall**

Create `pipeline/agentic/recall.py`:

```python
from __future__ import annotations

from pathlib import Path
from typing import Any

from pipeline.agentic.context_loader import assemble_context_pack, render_context_pack
from pipeline.agentic.memory_index import INDEX_PATH, search_memory


def build_recall_bundle(
    root: Path,
    *,
    query: str,
    profile: str = "a-story-of-two",
    index_path: Path | None = None,
    limit: int = 8,
) -> dict[str, Any]:
    root = root.resolve()
    pack = assemble_context_pack(root, profile=profile)
    path = index_path or (root / INDEX_PATH)
    hits = search_memory(path, query, limit=limit)
    return {
        "schema_version": "1.0",
        "query": query,
        "profile": profile,
        "context": pack,
        "hits": hits,
    }


def render_recall_bundle(bundle: dict[str, Any]) -> str:
    lines = [
        "# Recall Bundle",
        "",
        f"query: {bundle['query']}",
        f"profile: {bundle['profile']}",
        "",
        "## Injected Context",
        "",
        render_context_pack(bundle["context"]).strip(),
        "",
        "## Retrieved Memory",
        "",
    ]
    hits = bundle.get("hits", [])
    if not hits:
        lines.append("- No indexed memory hits.")
    for index, hit in enumerate(hits, start=1):
        lines.extend(
            [
                f"### Hit {index}: {hit.title}",
                f"path: {hit.path}",
                f"kind: {hit.kind}",
                f"confidence: {hit.confidence}",
                f"score: {hit.score:.4f}",
                "",
                hit.snippet,
                "",
            ]
        )
    return "\n".join(lines).strip() + "\n"
```

- [ ] **Step 4: Run recall tests**

Run:

```bash
venv/bin/python -m pytest tests/test_agentic_recall.py -v
```

Expected: PASS, 1 test.

---

### Task 6: Add Append-Only Audit Log And Snapshots

**Files:**
- Create: `pipeline/agentic/audit_log.py`
- Test: `tests/test_agentic_audit_log.py`

- [ ] **Step 1: Write failing audit tests**

Create `tests/test_agentic_audit_log.py`:

```python
import json
from pathlib import Path

from pipeline.agentic.audit_log import snapshot_file, write_audit_event


def test_write_audit_event_appends_jsonl(tmp_path: Path):
    path = write_audit_event(
        tmp_path,
        event_type="context_pack_created",
        actor="codex",
        target_path="memory/agentic/index/memory.sqlite",
        summary="Indexed memory.",
        evidence_paths=["memory/working.md"],
    )

    lines = path.read_text(encoding="utf-8").splitlines()
    assert len(lines) == 1
    event = json.loads(lines[0])
    assert event["event_type"] == "context_pack_created"


def test_snapshot_file_records_hash_and_copy(tmp_path: Path):
    source = tmp_path / "config" / "voice.md"
    source.parent.mkdir()
    source.write_text("voice v1", encoding="utf-8")

    result = snapshot_file(tmp_path, source)

    assert result["sha256"]
    assert Path(result["snapshot_path"]).exists()
```

- [ ] **Step 2: Run tests and confirm they fail**

Run:

```bash
venv/bin/python -m pytest tests/test_agentic_audit_log.py -v
```

Expected: FAIL with missing module.

- [ ] **Step 3: Implement audit log**

Create `pipeline/agentic/audit_log.py`:

```python
from __future__ import annotations

import hashlib
import json
import shutil
from datetime import date
from pathlib import Path
from uuid import uuid4

from pipeline.agentic.contracts import AuditEvent


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def audit_log_path(root: Path) -> Path:
    today = date.today().isoformat()
    return root / "memory" / "agentic" / "audit" / f"{today}.jsonl"


def write_audit_event(
    root: Path,
    *,
    event_type: str,
    actor: str,
    target_path: str,
    summary: str,
    evidence_paths: list[str] | None = None,
) -> Path:
    root = root.resolve()
    path = audit_log_path(root)
    path.parent.mkdir(parents=True, exist_ok=True)
    event = AuditEvent(
        event_id=f"audit-{uuid4().hex}",
        event_type=event_type,
        actor=actor,
        target_path=target_path,
        summary=summary,
        evidence_paths=evidence_paths or [],
    )
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(event.model_dump(), ensure_ascii=False) + "\n")
    return path


def snapshot_file(root: Path, source: Path) -> dict[str, str]:
    root = root.resolve()
    source = source.resolve()
    digest = sha256_file(source)
    rel = source.relative_to(root).as_posix()
    safe_name = rel.replace("/", "__")
    snapshot_dir = root / "memory" / "agentic" / "snapshots" / date.today().isoformat()
    snapshot_dir.mkdir(parents=True, exist_ok=True)
    target = snapshot_dir / f"{safe_name}.{digest[:12]}"
    shutil.copy2(source, target)
    return {
        "source_path": rel,
        "snapshot_path": target.as_posix(),
        "sha256": digest,
    }
```

- [ ] **Step 4: Run audit tests**

Run:

```bash
venv/bin/python -m pytest tests/test_agentic_audit_log.py -v
```

Expected: PASS, 2 tests.

---

### Task 7: Add Guarded Learning Loop

**Files:**
- Create: `pipeline/agentic/learning_loop.py`
- Test: `tests/test_agentic_learning_loop.py`

- [ ] **Step 1: Write failing learning tests**

Create `tests/test_agentic_learning_loop.py`:

```python
import json
from pathlib import Path

from pipeline.agentic.learning_loop import create_learning_event, create_learning_proposal


def test_create_learning_event_writes_event_file(tmp_path: Path):
    path = create_learning_event(
        tmp_path,
        workflow="carousel_jam",
        summary="Creator rejected repeated wallet audit lane.",
        evidence_paths=["memory/semantic/carousel-idea-preferences.md"],
        tags=["carousel", "preference"],
    )

    payload = json.loads(path.read_text(encoding="utf-8"))
    assert payload["workflow"] == "carousel_jam"
    assert payload["tags"] == ["carousel", "preference"]


def test_learning_proposal_is_not_auto_applied(tmp_path: Path):
    target = tmp_path / "config" / "skills" / "golden.md"
    target.parent.mkdir(parents=True)
    target.write_text("old skill", encoding="utf-8")
    event = create_learning_event(
        tmp_path,
        workflow="carousel_jam",
        summary="Need stronger duplicate-lane block.",
        evidence_paths=["memory/semantic/carousel-idea-preferences.md"],
        tags=["skill"],
    )
    proposal = create_learning_proposal(
        tmp_path,
        source_event_path=event,
        target_path=target,
        proposed_content="new skill",
        rationale="Preserve creator rejection as a gate.",
        required_validators=["skill_eval", "pytest"],
    )

    payload = json.loads(proposal.read_text(encoding="utf-8"))
    assert payload["auto_apply"] is False
    assert payload["status"] == "draft"
    assert payload["before_hash"] != payload["after_hash"]
```

- [ ] **Step 2: Run tests and confirm they fail**

Run:

```bash
venv/bin/python -m pytest tests/test_agentic_learning_loop.py -v
```

Expected: FAIL with missing module.

- [ ] **Step 3: Implement learning loop**

Create `pipeline/agentic/learning_loop.py`:

```python
from __future__ import annotations

import hashlib
import json
from datetime import date
from pathlib import Path
from uuid import uuid4

from pipeline.agentic.audit_log import snapshot_file, write_audit_event
from pipeline.agentic.contracts import LearningProposal


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def create_learning_event(
    root: Path,
    *,
    workflow: str,
    summary: str,
    evidence_paths: list[str],
    tags: list[str],
) -> Path:
    root = root.resolve()
    event_id = f"event-{uuid4().hex}"
    directory = root / "memory" / "agentic" / "learning-events" / date.today().isoformat()
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / f"{event_id}.json"
    payload = {
        "schema_version": "1.0",
        "event_id": event_id,
        "workflow": workflow,
        "summary": summary,
        "evidence_paths": evidence_paths,
        "tags": tags,
        "status": "captured",
    }
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    write_audit_event(
        root,
        event_type="learning_event_created",
        actor="codex",
        target_path=path.relative_to(root).as_posix(),
        summary=summary,
        evidence_paths=evidence_paths,
    )
    return path


def create_learning_proposal(
    root: Path,
    *,
    source_event_path: Path,
    target_path: Path,
    proposed_content: str,
    rationale: str,
    required_validators: list[str],
) -> Path:
    root = root.resolve()
    target_path = target_path.resolve()
    source_event_path = source_event_path.resolve()
    before_text = target_path.read_text(encoding="utf-8") if target_path.exists() else ""
    if target_path.exists():
        snapshot_file(root, target_path)
    proposal_id = f"proposal-{uuid4().hex}"
    event_payload = json.loads(source_event_path.read_text(encoding="utf-8"))
    proposal = LearningProposal(
        proposal_id=proposal_id,
        source_event_id=event_payload["event_id"],
        target_path=target_path.relative_to(root).as_posix(),
        proposed_action="modify" if target_path.exists() else "create",
        rationale=rationale,
        before_hash=sha256_text(before_text),
        after_hash=sha256_text(proposed_content),
        required_validators=required_validators,
    )
    directory = root / "memory" / "agentic" / "learning-proposals" / date.today().isoformat()
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / f"{proposal_id}.json"
    payload = proposal.model_dump()
    payload["proposed_content"] = proposed_content
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    write_audit_event(
        root,
        event_type="learning_proposal_created",
        actor="codex",
        target_path=path.relative_to(root).as_posix(),
        summary=rationale,
        evidence_paths=[source_event_path.relative_to(root).as_posix()],
    )
    return path
```

- [ ] **Step 4: Run learning tests**

Run:

```bash
venv/bin/python -m pytest tests/test_agentic_learning_loop.py -v
```

Expected: PASS, 2 tests.

---

### Task 8: Add External Skill Evaluation Gates

**Files:**
- Create: `pipeline/agentic/skill_eval.py`
- Test: `tests/test_agentic_skill_eval.py`

- [ ] **Step 1: Write failing skill evaluation tests**

Create `tests/test_agentic_skill_eval.py`:

```python
import json
from pathlib import Path

from pipeline.agentic.skill_eval import evaluate_learning_proposal


def test_evaluate_learning_proposal_blocks_auto_apply(tmp_path: Path):
    proposal = tmp_path / "proposal.json"
    proposal.write_text(
        json.dumps(
            {
                "proposal_id": "p1",
                "target_path": "config/skills/a.md",
                "proposed_action": "modify",
                "rationale": "Improve skill.",
                "before_hash": "a",
                "after_hash": "b",
                "required_validators": ["skill_eval"],
                "status": "draft",
                "auto_apply": True,
                "proposed_content": "# Skill\n\nconfidence: 0.9\n"
            }
        ),
        encoding="utf-8",
    )

    result = evaluate_learning_proposal(tmp_path, proposal)

    assert result["status"] == "FAIL"
    assert "auto_apply must be false" in result["failures"][0]


def test_evaluate_learning_proposal_requires_confidence_for_markdown(tmp_path: Path):
    proposal = tmp_path / "proposal.json"
    proposal.write_text(
        json.dumps(
            {
                "proposal_id": "p1",
                "target_path": "config/skills/a.md",
                "proposed_action": "modify",
                "rationale": "Improve skill.",
                "before_hash": "a",
                "after_hash": "b",
                "required_validators": ["skill_eval"],
                "status": "draft",
                "auto_apply": False,
                "proposed_content": "# Skill\n\nNo metadata.\n"
            }
        ),
        encoding="utf-8",
    )

    result = evaluate_learning_proposal(tmp_path, proposal)

    assert result["status"] == "FAIL"
    assert any("confidence" in failure for failure in result["failures"])
```

- [ ] **Step 2: Run tests and confirm they fail**

Run:

```bash
venv/bin/python -m pytest tests/test_agentic_skill_eval.py -v
```

Expected: FAIL with missing module.

- [ ] **Step 3: Implement skill evaluation**

Create `pipeline/agentic/skill_eval.py`:

```python
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from pipeline.agentic.audit_log import write_audit_event


def evaluate_learning_proposal(root: Path, proposal_path: Path) -> dict[str, Any]:
    root = root.resolve()
    proposal_path = proposal_path.resolve()
    payload = json.loads(proposal_path.read_text(encoding="utf-8"))
    proposed_content = payload.get("proposed_content", "")
    failures: list[str] = []
    warnings: list[str] = []

    if payload.get("auto_apply") is not False:
        failures.append("auto_apply must be false for all learning proposals.")
    if not payload.get("required_validators"):
        failures.append("required_validators must name at least one external gate.")
    if payload.get("target_path", "").endswith(".md"):
        if not re.search(r"(?m)^confidence:\s*(0(?:\.\d+)?|1(?:\.0+)?)\s*$", proposed_content):
            failures.append("Markdown proposals must include confidence metadata.")
        if "sources:" not in proposed_content:
            warnings.append("Markdown proposal has no sources block.")
    if "do not ask" in proposed_content.lower() and "source" not in proposed_content.lower():
        warnings.append("Instructional hard gates should cite the source of the preference.")
    if len(proposed_content.strip()) < 20:
        failures.append("proposed_content is too small to evaluate safely.")

    status = "FAIL" if failures else ("PASS_WITH_WARNINGS" if warnings else "PASS")
    result = {
        "schema_version": "1.0",
        "proposal_id": payload.get("proposal_id"),
        "status": status,
        "failures": failures,
        "warnings": warnings,
    }
    result_path = proposal_path.with_suffix(".evaluation.json")
    result_path.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
    write_audit_event(
        root,
        event_type="learning_proposal_evaluated",
        actor="codex",
        target_path=proposal_path.relative_to(root).as_posix(),
        summary=f"Evaluation status: {status}",
        evidence_paths=[result_path.relative_to(root).as_posix()],
    )
    return result
```

- [ ] **Step 4: Run skill evaluation tests**

Run:

```bash
venv/bin/python -m pytest tests/test_agentic_skill_eval.py -v
```

Expected: PASS, 2 tests.

---

### Task 9: Add Agentic OS CLI

**Files:**
- Create: `scripts/agentic_os.py`
- Test: `tests/test_agentic_cli.py`

- [ ] **Step 1: Write failing CLI tests**

Create `tests/test_agentic_cli.py`:

```python
import subprocess
from pathlib import Path


def test_agentic_os_help_runs():
    result = subprocess.run(
        ["venv/bin/python", "scripts/agentic_os.py", "--help"],
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0
    assert "context" in result.stdout
    assert "index-memory" in result.stdout


def test_agentic_os_registry_runs():
    result = subprocess.run(
        ["venv/bin/python", "scripts/agentic_os.py", "registry"],
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0
    assert "skill." in result.stdout
```

- [ ] **Step 2: Run tests and confirm they fail**

Run:

```bash
venv/bin/python -m pytest tests/test_agentic_cli.py -v
```

Expected: FAIL because `scripts/agentic_os.py` does not exist.

- [ ] **Step 3: Implement CLI**

Create `scripts/agentic_os.py`:

```python
#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from pipeline.agentic.context_loader import assemble_context_pack, render_context_pack
from pipeline.agentic.memory_index import build_memory_index, search_memory
from pipeline.agentic.recall import build_recall_bundle, render_recall_bundle
from pipeline.agentic.skill_eval import evaluate_learning_proposal
from pipeline.agentic.skill_registry import discover_skill_records, load_skill_systems, resolve_skill_system


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="A Story Of Two agentic OS control plane.")
    parser.add_argument("--workspace-root", type=Path, default=ROOT)
    sub = parser.add_subparsers(dest="command", required=True)

    context_parser = sub.add_parser("context", help="Render a context pack.")
    context_parser.add_argument("--profile", default="a-story-of-two")
    context_parser.add_argument("--json", action="store_true")

    sub.add_parser("registry", help="List discovered skills and agents.")

    system_parser = sub.add_parser("skill-system", help="Resolve a named skill system.")
    system_parser.add_argument("name")

    sub.add_parser("index-memory", help="Build the memory search index.")

    search_parser = sub.add_parser("search", help="Search indexed memory.")
    search_parser.add_argument("query")
    search_parser.add_argument("--limit", type=int, default=8)

    recall_parser = sub.add_parser("recall", help="Render context plus memory recall.")
    recall_parser.add_argument("query")
    recall_parser.add_argument("--profile", default="a-story-of-two")

    eval_parser = sub.add_parser("evaluate-learning", help="Evaluate a learning proposal.")
    eval_parser.add_argument("proposal_path", type=Path)

    args = parser.parse_args(argv)
    root = args.workspace_root.resolve()

    if args.command == "context":
        pack = assemble_context_pack(root, profile=args.profile)
        print(json.dumps(pack.model_dump(), indent=2, ensure_ascii=False) if args.json else render_context_pack(pack))
        return 0

    if args.command == "registry":
        for record in discover_skill_records(root):
            print(f"{record.skill_id}\t{record.path}\t{record.confidence}")
        return 0

    if args.command == "skill-system":
        systems = load_skill_systems(root)
        print(json.dumps(resolve_skill_system(systems, args.name), indent=2, ensure_ascii=False))
        return 0

    if args.command == "index-memory":
        print(build_memory_index(root))
        return 0

    if args.command == "search":
        index_path = build_memory_index(root)
        for hit in search_memory(index_path, args.query, limit=args.limit):
            print(f"{hit.score:.4f}\t{hit.path}\t{hit.title}")
        return 0

    if args.command == "recall":
        index_path = build_memory_index(root)
        bundle = build_recall_bundle(root, query=args.query, profile=args.profile, index_path=index_path)
        print(render_recall_bundle(bundle))
        return 0

    if args.command == "evaluate-learning":
        result = evaluate_learning_proposal(root, args.proposal_path)
        print(json.dumps(result, indent=2, ensure_ascii=False))
        return 1 if result["status"] == "FAIL" else 0

    raise ValueError(f"Unhandled command: {args.command}")


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 4: Run CLI tests**

Run:

```bash
venv/bin/python -m pytest tests/test_agentic_cli.py -v
```

Expected: PASS, 2 tests.

- [ ] **Step 5: Smoke-test real commands**

Run:

```bash
venv/bin/python scripts/agentic_os.py context --profile a-story-of-two
venv/bin/python scripts/agentic_os.py registry
venv/bin/python scripts/agentic_os.py index-memory
venv/bin/python scripts/agentic_os.py search "wallet audit cooled down"
```

Expected:

- `context` prints context sections from the manifest.
- `registry` lists `skill.carousel-jam-autopilot` and multiple agents.
- `index-memory` prints `memory/agentic/index/memory.sqlite`.
- `search` returns `memory/semantic/carousel-idea-preferences.md` near the top for wallet/audit queries.

---

### Task 10: Integrate Context And Recall Into Existing Workflows

**Files:**
- Modify: `pipeline/stages/c1_illustration_carousel.py`
- Modify: `pipeline/stages/codex_native_carousel.py`
- Modify: `scripts/analyze_prepost.py`
- Modify: `scripts/create_substack_article_package.py`
- Test: `tests/test_illustration_carousel.py`
- Test: `tests/test_prepost_story_selling.py`
- Test: `tests/test_substack_article_package.py`

- [ ] **Step 1: Add tests that assert workflows mention the control plane**

Add this test to `tests/test_creator_workflow_contract.py`:

```python
def test_agentic_os_control_plane_is_documented_for_workflows():
    agents = (WORKSPACE / "AGENTS.md").read_text(encoding="utf-8")
    assert "Agentic OS Control Plane" in agents
    assert "config/agentic_context_manifest.json" in agents
    assert "scripts/agentic_os.py" in agents
```

Expected first run: FAIL until Task 12 updates docs.

- [ ] **Step 2: Change C1 Anthropic context loading**

In `pipeline/stages/c1_illustration_carousel.py`, replace the body of `load_context()` with:

```python
def load_context() -> str:
    from pipeline.agentic.context_loader import assemble_context_pack, render_context_pack

    pack = assemble_context_pack(BASE_DIR, profile="a-story-of-two")
    return render_context_pack(pack)
```

This preserves the existing call site in `build_system_prompt()` while making the context source explicit and budgeted.

- [ ] **Step 3: Add deterministic recall metadata to Codex-native packages**

In `pipeline/stages/codex_native_carousel.py`, import:

```python
from pipeline.agentic.memory_index import build_memory_index
from pipeline.agentic.recall import build_recall_bundle, render_recall_bundle
from pipeline.agentic.skill_registry import load_skill_systems, resolve_skill_system
```

Inside `build_package(...)`, before returning the package, build:

```python
workspace_root = infer_workspace_root(output_root)
index_path = build_memory_index(workspace_root)
recall_bundle = build_recall_bundle(
    workspace_root,
    query=story,
    profile="a-story-of-two",
    index_path=index_path,
    limit=8,
)
skill_system = resolve_skill_system(load_skill_systems(workspace_root), "carousel_jam")
```

Then include the following keys in `concept` or package-level metadata:

```python
"agentic_os": {
    "skill_system": skill_system,
    "recall_query": story,
    "recall_hit_paths": [hit.path for hit in recall_bundle["hits"]],
}
```

Also write `source-memory-brief.md` in `write_package(...)`:

```python
(out_dir / "source-memory-brief.md").write_text(
    render_recall_bundle(package["agentic_os"]["recall_bundle"]),
    encoding="utf-8",
)
```

When implementing this step, keep `recall_bundle` out of JSON artifacts if pydantic objects are not JSON-serializable. Store only paths/scores in JSON and write the full rendered Markdown separately.

- [ ] **Step 4: Integrate pre-post script**

In `scripts/analyze_prepost.py`, before building the analysis prompt, load:

```python
from pipeline.agentic.memory_index import build_memory_index
from pipeline.agentic.recall import build_recall_bundle, render_recall_bundle
from pipeline.agentic.skill_registry import load_skill_systems, resolve_skill_system

index_path = build_memory_index(ROOT)
skill_system = resolve_skill_system(load_skill_systems(ROOT), "prepost_reel")
recall_text = render_recall_bundle(
    build_recall_bundle(ROOT, query=concept, profile="a-story-of-two", index_path=index_path)
)
```

Inject `skill_system` and `recall_text` into the pre-post system prompt or package artifact.

- [ ] **Step 5: Integrate article package script**

In `scripts/create_substack_article_package.py`, before article brief generation, load `story_article`:

```python
from pipeline.agentic.memory_index import build_memory_index
from pipeline.agentic.recall import build_recall_bundle, render_recall_bundle
from pipeline.agentic.skill_registry import load_skill_systems, resolve_skill_system

index_path = build_memory_index(ROOT)
skill_system = resolve_skill_system(load_skill_systems(ROOT), "story_article")
recall_text = render_recall_bundle(
    build_recall_bundle(ROOT, query=title or carousel_dir.name, profile="article", index_path=index_path)
)
```

Write `source-memory-brief.md` inside the article package with `recall_text`.

- [ ] **Step 6: Run integration tests**

Run:

```bash
venv/bin/python -m pytest tests/test_illustration_carousel.py tests/test_prepost_story_selling.py tests/test_substack_article_package.py -v
```

Expected: existing tests still pass after context/recall integration.

---

### Task 11: Split The Large Codex-Native Carousel Module

**Files:**
- Create: `pipeline/stages/carousel_lanes.py`
- Create: `pipeline/stages/carousel_visual_rooms.py`
- Create: `pipeline/stages/carousel_package_writer.py`
- Modify: `pipeline/stages/codex_native_carousel.py`
- Test: `tests/test_illustration_carousel.py`

- [ ] **Step 1: Establish current baseline**

Run:

```bash
venv/bin/python -m pytest tests/test_illustration_carousel.py -v
```

Expected: record the current pass/fail state before refactoring. If tests fail before changes, stop and repair the baseline or split this task into a debugging plan.

- [ ] **Step 2: Extract lane classification and slide builders**

Move token constants, `classify_content_lane`, all `is_*_story` helpers, and all `build_*_slides` helpers from `pipeline/stages/codex_native_carousel.py` into `pipeline/stages/carousel_lanes.py`.

Keep the public import surface:

```python
from pipeline.stages.carousel_lanes import classify_content_lane, build_slides
```

Do not change function signatures in this task.

- [ ] **Step 3: Extract visual rooms**

Move `build_visual_debate`, `build_post_copy_visual_room`, and `build_visual_plan_quality` into `pipeline/stages/carousel_visual_rooms.py`.

Keep the public import surface:

```python
from pipeline.stages.carousel_visual_rooms import (
    build_post_copy_visual_room,
    build_visual_debate,
    build_visual_plan_quality,
)
```

Do not change artifact JSON shape in this task.

- [ ] **Step 4: Extract package writers**

Move `write_json`, `write_storyboard`, `write_approval`, `write_agent_reports`, `build_manifest`, `write_package`, and `try_render_assets` into `pipeline/stages/carousel_package_writer.py`.

Keep the public import surface:

```python
from pipeline.stages.carousel_package_writer import build_manifest, try_render_assets, write_package
```

Do not change output file names in this task.

- [ ] **Step 5: Run carousel tests after each extraction**

Run after each extraction:

```bash
venv/bin/python -m pytest tests/test_illustration_carousel.py -v
```

Expected: any failure must point to import movement only, not behavior changes.

- [ ] **Step 6: Run broad regression slice**

Run:

```bash
venv/bin/python -m pytest tests/test_illustration_carousel.py tests/test_carousel_generation_state.py tests/test_carousel_prompt_compiler.py tests/test_creator_workflow_contract.py -v
```

Expected: PASS or same pre-existing failures documented from Step 1.

---

### Task 12: Document The Agentic OS Control Plane

**Files:**
- Modify: `AGENTS.md`
- Modify: `CLAUDE.md`
- Create: `docs/superpowers/specs/2026-05-25-agentic-os-spine-design.md`
- Test: `tests/test_creator_workflow_contract.py`

- [ ] **Step 1: Add AGENTS control plane section**

Add this section after the Architecture diagram in `AGENTS.md`:

```markdown
## Agentic OS Control Plane

Entry point for identity context, memory recall, skill-system composition,
guarded learning, and audit logs:

- Manifest: `config/agentic_context_manifest.json`
- Skill systems: `config/skill-systems.json`
- CLI: `scripts/agentic_os.py`
- Package: `pipeline/agentic/`
- Durable audit: `memory/agentic/audit/`
- Learning events: `memory/agentic/learning-events/`
- Learning proposals: `memory/agentic/learning-proposals/`
- Snapshots: `memory/agentic/snapshots/`

Rules:

1. Context must be assembled from explicit profiles, not ad hoc file loading.
2. Long-term memory recall must return ranked paths and citations.
3. Skills must be composed through skill systems when a workflow reuses more
   than one skill or agent.
4. Learning loops are proposal-only. No model may silently overwrite skills,
   memory, or agent files.
5. Every proposal needs external validation through `pipeline/agentic/skill_eval.py`
   and relevant pytest gates before approval.
6. If git is unavailable, snapshots and JSONL audit logs are the minimum
   rollback trail.
```

- [ ] **Step 2: Add CLAUDE reading-order pointer**

In `CLAUDE.md`, add `config/agentic_context_manifest.json` and `config/skill-systems.json` to the reading order after `memory/working.md`.

- [ ] **Step 3: Create design spec**

Create `docs/superpowers/specs/2026-05-25-agentic-os-spine-design.md` with the transcript read, debate, target architecture, and failure model from this plan. Keep the spec shorter than this implementation plan and focused on design decisions.

- [ ] **Step 4: Run workflow contract tests**

Run:

```bash
venv/bin/python -m pytest tests/test_creator_workflow_contract.py -v
```

Expected: PASS after docs mention the control plane.

---

### Task 13: Add Wiki Health Coverage For Agentic OS

**Files:**
- Modify: `pipeline/stages/wiki_health.py`
- Test: `tests/test_wiki_health.py`

- [ ] **Step 1: Add failing health expectations**

Add checks to `tests/test_wiki_health.py` asserting that `collect_wiki_health` checks these paths:

```python
def test_wiki_health_checks_agentic_os_surface(tmp_path):
    from pipeline.stages.wiki_health import collect_wiki_health

    required = [
        "config/agentic_context_manifest.json",
        "config/skill-systems.json",
        "pipeline/agentic",
        "scripts/agentic_os.py",
        "memory/agentic",
    ]
    for rel in required:
        path = tmp_path / rel
        if rel.endswith(".json") or rel.endswith(".py"):
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text("{}", encoding="utf-8")
        else:
            path.mkdir(parents=True, exist_ok=True)
    (tmp_path / "wiki").mkdir()
    (tmp_path / "wiki" / "index.md").write_text("# Wiki\n\ntotal_pages: 0\n", encoding="utf-8")
    (tmp_path / "memory" / "working.md").write_text("# Working\n", encoding="utf-8")
    (tmp_path / "memory" / "semantic").mkdir(exist_ok=True)
    (tmp_path / "memory" / "episodic").mkdir(exist_ok=True)
    (tmp_path / "memory" / "graph.json").write_text("{}", encoding="utf-8")
    (tmp_path / "logs").mkdir()

    health = collect_wiki_health(tmp_path)

    assert any(check["id"] == "agentic_os_surface" for check in health["checks"])
```

- [ ] **Step 2: Run health tests and confirm they fail**

Run:

```bash
venv/bin/python -m pytest tests/test_wiki_health.py -v
```

Expected: FAIL because `agentic_os_surface` is missing.

- [ ] **Step 3: Add health check**

In `pipeline/stages/wiki_health.py`, add:

```python
AGENTIC_OS_SURFACE = [
    "config/agentic_context_manifest.json",
    "config/skill-systems.json",
    "pipeline/agentic",
    "scripts/agentic_os.py",
    "memory/agentic",
]
```

Inside `collect_wiki_health`, after `memory_surface`, add:

```python
missing_agentic = [
    path
    for path in AGENTIC_OS_SURFACE
    if not (root / path).exists()
]
checks.append(
    make_check(
        "agentic_os_surface",
        "FAIL" if missing_agentic else "PASS",
        "major" if missing_agentic else "info",
        "Agentic OS context, skill-system, CLI, package, and memory surfaces exist.",
        {"missing": missing_agentic},
    )
)
```

- [ ] **Step 4: Run health tests**

Run:

```bash
venv/bin/python -m pytest tests/test_wiki_health.py -v
```

Expected: PASS.

---

### Task 14: End-To-End Verification

**Files:**
- No new files.
- Verify: all relevant tests and wiki health.

- [ ] **Step 1: Run agentic test suite**

Run:

```bash
venv/bin/python -m pytest tests/test_agentic_contracts.py tests/test_agentic_context_loader.py tests/test_agentic_skill_registry.py tests/test_agentic_memory_index.py tests/test_agentic_recall.py tests/test_agentic_audit_log.py tests/test_agentic_learning_loop.py tests/test_agentic_skill_eval.py tests/test_agentic_cli.py -v
```

Expected: PASS.

- [ ] **Step 2: Run workflow regression suite**

Run:

```bash
venv/bin/python -m pytest tests/test_creator_workflow_contract.py tests/test_illustration_carousel.py tests/test_prepost_story_selling.py tests/test_substack_article_package.py tests/test_wiki_health.py -v
```

Expected: PASS or documented pre-existing failures from the baseline.

- [ ] **Step 3: Run control plane smoke commands**

Run:

```bash
venv/bin/python scripts/agentic_os.py context --profile a-story-of-two
venv/bin/python scripts/agentic_os.py skill-system carousel_jam
venv/bin/python scripts/agentic_os.py index-memory
venv/bin/python scripts/agentic_os.py search "golden theme wallet audit reach recovery"
venv/bin/python scripts/agentic_os.py recall "make this carousel more cinematic"
```

Expected:

- Context command prints the configured profile.
- Skill-system command prints ordered carousel components and gates.
- Index command writes `memory/agentic/index/memory.sqlite`.
- Search command returns at least one memory/wiki path.
- Recall command prints both context and retrieved memory.

- [ ] **Step 4: Run wiki health closeout**

Run:

```bash
venv/bin/python scripts/wiki_health.py --write --fix-index --session-note "Implemented Agentic OS spine: context packs, memory index, skill systems, guarded learning, audit logs, and workflow integration."
```

Expected: `wiki health: PASS` or `PASS_WITH_WARNINGS`. If it returns `NEEDS_HEAL`, repair the failing checks or leave the generated HEAL proposal as the next-session starting point.

## Learning Track

Use the implementation as a learning lab. Each phase teaches one agentic engineering idea.

1. Identity injection: implement Tasks 1-2, then explain why context packs beat one giant memory file.
2. Skill systems: implement Task 3, then map which current workflows share components and which skills are truly atomic.
3. Long-term recall: implement Tasks 4-5, then test queries where the exact wording differs from the memory wording.
4. Guarded self-learning: implement Tasks 6-8, then create a fake bad proposal and prove the evaluator blocks it.
5. CLI ergonomics: implement Task 9, then run every command without reading source code.
6. Workflow integration: implement Task 10, then inspect a generated package and verify recall/provenance artifacts.
7. Maintainability: implement Task 11, then compare the line count and import surface of `codex_native_carousel.py` before and after.
8. Operating discipline: implement Tasks 12-14, then run wiki health and read the HEAL proposal if any gate fails.

## Security And Safety Rules

- No automatic skill overwrite.
- No marketplace package execution.
- No skill proposal applies without snapshot, audit event, deterministic evaluation, and human approval.
- No copyrighted source text is copied into skills or memory artifacts.
- No `.env` or secret files are indexed.
- No context pack may include raw identity images; it may include paths and identity dossier summaries only.
- No workflow can claim final generation unless `final-images.json`, visual QA, and final audit support that status.

## Definition Of Done

- `scripts/agentic_os.py` can render context, list registry, resolve skill systems, build the memory index, search memory, render recall, and evaluate learning proposals.
- `memory/agentic/` contains audit, index, learning-event, learning-proposal, and snapshot subdirectories when used.
- C-layer, D-layer, and B-layer workflows can reference a skill system and recall bundle.
- `AGENTS.md` and `CLAUDE.md` document the control plane.
- Wiki health checks the Agentic OS surface.
- New tests pass or failures are documented as pre-existing baseline failures.
- The learning loop can propose a skill update, but cannot auto-apply it.

## Execution Recommendation

Execute in this order:

1. Tasks 1-3 as the foundation.
2. Tasks 4-6 for memory and audit.
3. Tasks 7-9 for learning and CLI.
4. Task 10 for workflow integration.
5. Task 11 only after the test baseline is stable.
6. Tasks 12-14 for docs, health, and closeout.

This order gives value early without forcing a risky refactor before the spine is proven.
