from __future__ import annotations

import json
from types import SimpleNamespace

import pytest

import pipeline.stages.b1_prepost as prepost
from pipeline.agentic.contracts import (
    ContextPack,
    ContextSection,
    RecallBundle,
    RecallHit,
    WorkflowContextBundle,
)
from pipeline.stages.b1_prepost import (
    ORCHESTRATOR_SKILLS,
    PREPOST_AGENT_CONFIGS,
    CombinedPrepostAnalysis,
    FacetReport,
    build_agentic_os_brief,
    compute_prepost_verdict,
    load_skill,
)


def test_prepost_flow_loads_story_selling_authorial_spine_for_every_agent():
    for _, skill_names in PREPOST_AGENT_CONFIGS:
        assert "romance-story-selling-engine" in skill_names
    assert "romance-story-selling-engine" in ORCHESTRATOR_SKILLS

    loaded = load_skill("romance-story-selling-engine")

    assert "Story-Selling" in loaded
    assert "Concept Process Cards" in loaded
    assert "Story-Selling Rubric" in loaded
    assert "Story Selling Canon Source Policy" in loaded


def test_prepost_agentic_brief_includes_layer_e_room_decision():
    brief = build_agentic_os_brief({"concept": "Aachu stacks the plates and says dono rakh do."})

    assert "## Layer E Story-Selling" in brief
    assert "layer-e-story-selling.json" in brief
    assert "selected_story_lens" in brief
    assert "rooms" in brief


def _analysis(**overrides: object) -> CombinedPrepostAnalysis:
    payload: dict[str, object] = {
        "hook": {"score": 8, "max_score": 10, "report": "Hook report"},
        "edit": {"score": 28, "max_score": 35, "report": "Edit report"},
        "algorithm": {"score": 58, "max_score": 70, "report": "Algorithm report"},
        "caption": {"score": 28, "max_score": 35, "report": "Caption report"},
        "culture": {"score": 42, "max_score": 50, "report": "Culture report"},
        "dm_send_score": 20,
        "cultural_authenticity_score": 8,
        "audio_missing": False,
        "missing_inputs": [],
    }
    payload.update(overrides)
    return CombinedPrepostAnalysis.model_validate(payload)


@pytest.mark.parametrize(
    ("layer_status", "expected"),
    [("GO", "POST"), ("REPAIR", "REVISE"), ("REWORK", "REWORK"), ("STOP", "KILL")],
)
def test_prepost_verdict_applies_layer_e_caps(layer_status: str, expected: str) -> None:
    verdict, adjusted = compute_prepost_verdict(_analysis(), layer_e_status=layer_status)

    assert adjusted == 164
    assert verdict == expected


def test_prepost_verdict_applies_missing_audio_and_signal_caps() -> None:
    analysis = _analysis(
        hook=FacetReport(score=4, max_score=10, report="Weak hook"),
        dm_send_score=8,
        audio_missing=True,
    )

    verdict, adjusted = compute_prepost_verdict(analysis, layer_e_status="GO")

    assert adjusted == 150
    assert verdict == "REWORK"


@pytest.mark.parametrize(
    ("total", "expected"),
    [(160, "POST"), (159, "REVISE"), (120, "REVISE"), (119, "REWORK"), (80, "REWORK"), (79, "KILL")],
)
def test_prepost_verdict_tier_boundaries(total: int, expected: str) -> None:
    maxima = {"hook": 10, "edit": 35, "algorithm": 70, "caption": 35, "culture": 50}
    remaining = total
    facets: dict[str, FacetReport] = {}
    for name, maximum in maxima.items():
        score = min(maximum, remaining)
        facets[name] = FacetReport(score=score, max_score=maximum, report=f"{name} report")
        remaining -= score
    analysis = CombinedPrepostAnalysis(
        **facets,
        dm_send_score=20,
        cultural_authenticity_score=8,
        audio_missing=False,
    )

    verdict, adjusted = compute_prepost_verdict(analysis, layer_e_status="GO")

    assert adjusted == total
    assert verdict == expected


def test_missing_audio_subtracts_ten_before_tiering() -> None:
    verdict, adjusted = compute_prepost_verdict(
        _analysis(audio_missing=True),
        layer_e_status="GO",
    )

    assert adjusted == 154
    assert verdict == "REVISE"


def test_structured_analysis_rejects_wrong_facet_contract() -> None:
    with pytest.raises(ValueError, match="hook must score within 0-10"):
        _analysis(hook=FacetReport(score=8, max_score=11, report="Wrong scale"))


def _run_context() -> prepost.PrepostRunContext:
    pack = ContextPack(
        profile="prepost",
        budget_tokens=3000,
        estimated_tokens=4,
        sections=[
            ContextSection(
                id="prepost_context_compact",
                path="config/skills/a-story-prepost-context-compact.md",
                kind="workflow_context",
                estimated_tokens=4,
                content="Compact prepost context.",
            )
        ],
    )
    workflow = WorkflowContextBundle(
        skill_system_name="prepost_reel",
        skill_system={
            "name": "prepost_reel",
            "components": ["config/skills/a-story-prepost-context-compact.md"],
            "source_references": ["config/skills/romance-story-selling-engine.md"],
        },
        recall=RecallBundle(query="exact", context=pack, hits=[]),
    )
    return prepost.PrepostRunContext(
        workflow=workflow,
        layer_e={
            "status": "GO",
            "selected_story_lens": ["proof"],
            "emotional_machine": "before -> proof -> after",
            "reader_mirror": "couples",
            "distribution_reason": "recognition",
            "rooms": ["story"],
            "process_influences": [],
        },
    )


class _FakeMessages:
    def __init__(self, payloads: list[dict[str, object]]) -> None:
        self.payloads = payloads
        self.calls: list[dict[str, object]] = []

    def create(self, **kwargs: object) -> object:
        self.calls.append(kwargs)
        payload = self.payloads.pop(0)
        return SimpleNamespace(
            content=[SimpleNamespace(text=json.dumps(payload))],
            usage=SimpleNamespace(
                input_tokens=100,
                output_tokens=25,
                cache_creation_input_tokens=7,
                cache_read_input_tokens=11,
            ),
        )


class _FakeClient:
    def __init__(self, payloads: list[dict[str, object]]) -> None:
        self.messages = _FakeMessages(payloads)


def _fake_payloads() -> list[dict[str, object]]:
    return [
        _analysis().model_dump(),
        {
            "score_arithmetic_valid": True,
            "unsupported_claims": [],
            "missing_inputs": [],
            "hard_gate_conflicts": [],
            "recommended_verdict_cap": None,
            "priority_corrections": ["Keep the hook visual."],
        },
        {
            "concept_summary": "A concrete couple moment.",
            "verdict_reason": "The proof and distribution signals are strong.",
            "must_fix": [],
            "should_fix": ["Tighten the cover."],
            "nice_to_have": ["Test one alternate opening."],
            "ready_to_post_summary": "Ready after the cover pass.",
        },
    ]


def test_prepost_executes_exactly_three_calls_and_preserves_exact_input(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fake = _FakeClient(_fake_payloads())
    monkeypatch.setattr(prepost.anthropic, "Anthropic", lambda **_: fake)
    monkeypatch.setattr(prepost, "build_prepost_run_context", lambda _: _run_context())
    exact = "Aachu says: `dono rakh do` -- exactly."

    report = prepost.analyze_prepost({"concept": exact, "audio": "original"}, save=False)

    assert len(fake.messages.calls) == 3
    assert [call["model"] for call in fake.messages.calls] == [
        "claude-sonnet-4-6",
        "claude-sonnet-4-6",
        "claude-opus-4-6",
    ]
    assert all(exact in call["messages"][0]["content"] for call in fake.messages.calls)
    assert "config/skills/a-story-prepost-context-compact.md" in fake.messages.calls[0]["messages"][0]["content"]
    assert "Story Selling Canon Source Policy" not in fake.messages.calls[0]["messages"][0]["content"]
    assert "## VERDICT: POST" in report
    assert "| Hook | 8 | 10 |" in report
    assert "| **TOTAL** | **164** | **200** |" in report
    assert "## Ready-to-Post Summary (if REVISE or POST verdict)" in report
    for heading in ("B1 — Hook Analysis", "B2 — Edit & Loop Audit", "B3 — Algorithm Fit Score", "B4 — Caption & Voice", "B5 — Cultural Resonance"):
        assert heading in report


def test_prepost_usage_sidecar_has_no_raw_prompt_text(
    tmp_path, monkeypatch: pytest.MonkeyPatch
) -> None:
    fake = _FakeClient(_fake_payloads())
    monkeypatch.setattr(prepost.anthropic, "Anthropic", lambda **_: fake)
    monkeypatch.setattr(prepost, "build_prepost_run_context", lambda _: _run_context())
    monkeypatch.setattr(prepost, "OUTPUT_DIR", tmp_path)
    exact = "PRIVATE-EXACT-CREATOR-TEXT"

    prepost.analyze_prepost({"concept": exact, "audio": "original"}, save=True)

    usage_path = next(tmp_path.glob("*.usage.json"))
    usage_text = usage_path.read_text(encoding="utf-8")
    usage = json.loads(usage_text)
    assert usage["schema_version"] == "prepost-prompt-usage/v1"
    assert len(usage["calls"]) == 3
    assert usage["estimated_input_tokens_total"] < 20_000
    assert exact not in usage_text
    assert all(len(call["system_sha256"]) == 64 for call in usage["calls"])
    assert usage["actual_input_tokens_total"] == 300
    assert usage["actual_output_tokens_total"] == 75
    assert all(call["cache_creation_input_tokens"] == 7 for call in usage["calls"])
    assert all(call["cache_read_input_tokens"] == 11 for call in usage["calls"])


def test_prepost_run_context_builds_recall_and_layer_e_once(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    counts = {"workflow": 0, "layer_e": 0}
    context = _run_context()

    def fake_workflow(*args: object, **kwargs: object) -> WorkflowContextBundle:
        counts["workflow"] += 1
        return context.workflow

    class FakeDecision:
        def model_dump(self, **_: object) -> dict[str, object]:
            counts["layer_e"] += 1
            return context.layer_e | {"rooms": {"story": {}}}

    monkeypatch.setattr(prepost, "build_workflow_context", fake_workflow)
    monkeypatch.setattr(prepost, "build_layer_e_prepost_decision", lambda _: FakeDecision())

    prepost.build_prepost_run_context({"concept": "One exact moment"})

    assert counts == {"workflow": 1, "layer_e": 1}


def test_prepost_recall_snippets_are_bounded(monkeypatch: pytest.MonkeyPatch) -> None:
    context = _run_context()
    context.workflow.recall.hits = [
        RecallHit(
            path=f"memory/semantic/hit-{index}.md",
            title=f"Hit {index}",
            kind="research",
            snippet="x" * 2000,
        )
        for index in range(4)
    ]
    fake = _FakeClient(_fake_payloads())
    monkeypatch.setattr(prepost.anthropic, "Anthropic", lambda **_: fake)
    monkeypatch.setattr(prepost, "build_prepost_run_context", lambda _: context)

    prepost.analyze_prepost({"concept": "Bound the recall", "audio": "original"}, save=False)

    combined_prompt = fake.messages.calls[0]["messages"][0]["content"]
    assert combined_prompt.count("[TRUNCATED]") == 4
    assert "x" * 601 not in combined_prompt
