"""Three-call pre-post analysis pipeline for @a.storyof.two."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Literal, TypeVar

import anthropic
from pydantic import BaseModel, Field, model_validator

from pipeline.agentic.context_loader import estimate_tokens, render_context_pack
from pipeline.agentic.contracts import WorkflowContextBundle
from pipeline.agentic.recall import render_recall_bundle, render_recall_hits
from pipeline.agentic.workflow_metadata import (
    build_workflow_context,
    workflow_context_metadata,
)
from pipeline.layer_e.engine import run_layer_e


BASE_DIR = Path(__file__).parent.parent.parent
SKILLS_DIR = BASE_DIR / "config" / "skills"
AGENTS_DIR = BASE_DIR / "agents"
OUTPUT_DIR = BASE_DIR / "output" / "prepost"
VOICE_FILE = BASE_DIR / "config" / "rules" / "voice.md"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

RELATED_SKILL_REFERENCES = {
    "romance-story-selling-engine": [
        BASE_DIR / "config" / "references" / "story-selling-canon" / "source-policy.md",
        BASE_DIR / "config" / "references" / "story-selling-canon" / "a-story-of-two-adaptation.md",
        BASE_DIR / "config" / "references" / "story-selling-canon" / "concept-process-cards.md",
        BASE_DIR / "config" / "references" / "story-selling-canon" / "rubric.md",
        BASE_DIR / "config" / "references" / "story-selling-canon" / "story-selling-online.md",
    ],
}

# These remain the five public scoring facets. One combined analyst now
# evaluates them instead of dispatching five overlapping prompts.
PREPOST_AGENT_CONFIGS = [
    ("hook-analyzer", ["romance-story-selling-engine", "hook-and-edit-framework", "instagram-algorithm-2026", "indian-creator-intelligence"]),
    ("edit-auditor", ["romance-story-selling-engine", "hook-and-edit-framework", "instagram-algorithm-2026"]),
    ("algorithm-scorer", ["romance-story-selling-engine", "instagram-algorithm-2026", "hook-and-edit-framework"]),
    ("caption-advisor", ["romance-story-selling-engine", "indian-creator-intelligence", "instagram-algorithm-2026"]),
    ("cultural-resonance", ["romance-story-selling-engine", "indian-creator-intelligence"]),
]

ORCHESTRATOR_SKILLS = [
    "romance-story-selling-engine",
    "instagram-algorithm-2026",
    "hook-and-edit-framework",
    "indian-creator-intelligence",
]

Verdict = Literal["POST", "REVISE", "REWORK", "KILL"]
ModelT = TypeVar("ModelT", bound=BaseModel)


class FacetReport(BaseModel):
    score: float = Field(ge=0)
    max_score: int = Field(gt=0)
    report: str = Field(min_length=1)


class CombinedPrepostAnalysis(BaseModel):
    hook: FacetReport
    edit: FacetReport
    algorithm: FacetReport
    caption: FacetReport
    culture: FacetReport
    dm_send_score: float = Field(ge=0, le=25)
    cultural_authenticity_score: float = Field(ge=0, le=10)
    audio_missing: bool
    missing_inputs: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def facet_contract(self) -> "CombinedPrepostAnalysis":
        expected = {
            "hook": 10,
            "edit": 35,
            "algorithm": 70,
            "caption": 35,
            "culture": 50,
        }
        for name, maximum in expected.items():
            facet = getattr(self, name)
            if facet.max_score != maximum or facet.score > maximum:
                raise ValueError(f"{name} must score within 0-{maximum}")
        return self

    @property
    def raw_total(self) -> float:
        return sum(
            facet.score
            for facet in (self.hook, self.edit, self.algorithm, self.caption, self.culture)
        )


class PrepostChallenge(BaseModel):
    score_arithmetic_valid: bool
    unsupported_claims: list[str] = Field(default_factory=list)
    missing_inputs: list[str] = Field(default_factory=list)
    hard_gate_conflicts: list[str] = Field(default_factory=list)
    recommended_verdict_cap: Verdict | None = None
    priority_corrections: list[str] = Field(default_factory=list)


class PrepostSynthesis(BaseModel):
    concept_summary: str
    verdict_reason: str
    must_fix: list[str] = Field(default_factory=list)
    should_fix: list[str] = Field(default_factory=list)
    nice_to_have: list[str] = Field(default_factory=list)
    ready_to_post_summary: str = ""


class PromptUsageRecord(BaseModel):
    stage: Literal["combined_analysis", "independent_challenge", "synthesis"]
    model: str
    system_sha256: str
    user_sha256: str
    system_chars: int
    user_chars: int
    estimated_input_tokens: int
    actual_input_tokens: int | None = None
    actual_output_tokens: int | None = None
    cache_creation_input_tokens: int | None = None
    cache_read_input_tokens: int | None = None
    context_ids: list[str] = Field(default_factory=list)


class PrepostUsageReport(BaseModel):
    schema_version: Literal["prepost-prompt-usage/v1"] = "prepost-prompt-usage/v1"
    calls: list[PromptUsageRecord]
    estimated_input_tokens_total: int
    actual_input_tokens_total: int | None = None
    actual_output_tokens_total: int | None = None


class PrepostRunContext(BaseModel):
    workflow: WorkflowContextBundle
    layer_e: dict[str, Any]


def load_skill(name: str) -> str:
    """Compatibility reader for diagnostics; live prompts use compact context."""

    path = SKILLS_DIR / f"{name}.md"
    if not path.exists():
        return f"[Skill file not found: {name}]"
    body = path.read_text(encoding="utf-8")
    references = []
    for reference_path in RELATED_SKILL_REFERENCES.get(name, []):
        if reference_path.exists():
            references.append(
                f"# Required Reference: {reference_path.relative_to(BASE_DIR)}\n"
                f"{reference_path.read_text(encoding='utf-8')}"
            )
    return body if not references else body + "\n\n---\n\n" + "\n\n---\n\n".join(references)


def load_agent(name: str) -> str:
    path = AGENTS_DIR / f"{name}.md"
    return path.read_text(encoding="utf-8") if path.exists() else f"[Agent file not found: {name}]"


def load_context() -> str:
    from pipeline.agentic.context_loader import assemble_context_pack

    return render_context_pack(assemble_context_pack(BASE_DIR, profile="prepost"))


def _brief_query(brief: dict[str, Any]) -> str:
    query = str(brief.get("concept") or " ".join(str(value) for value in brief.values() if value))
    return query.strip() or "planned Reel pre-post analysis"


def build_layer_e_prepost_decision(brief: dict[str, Any]):
    return run_layer_e(
        BASE_DIR,
        {
            "task_type": "prepost_reel",
            "story_or_moment": _brief_query(brief),
            "constraints": [
                "prepost reel analysis",
                "hook/edit/algo/caption/culture facets must consume Layer E first",
            ],
            "requested_tone": "Instagram Reel pre-post analysis",
            "reference_images": [],
        },
    )


def _layer_e_payload(decision: Any) -> dict[str, Any]:
    payload = decision.model_dump(mode="json") if hasattr(decision, "model_dump") else dict(decision)
    return {
        "status": payload["status"],
        "selected_story_lens": payload["selected_story_lens"],
        "emotional_machine": payload["emotional_machine"],
        "reader_mirror": payload["reader_mirror"],
        "distribution_reason": payload["distribution_reason"],
        "rooms": list(payload["rooms"].keys()),
        "process_influences": payload["process_influences"],
    }


def _render_layer_e_payload(payload: dict[str, Any]) -> str:
    return "\n".join(
        [
            "## Layer E Story-Selling",
            "",
            "Artifact: `layer-e-story-selling.json`",
            "",
            "```json",
            json.dumps(payload, indent=2, ensure_ascii=False),
            "```",
        ]
    )


def render_layer_e_prepost_brief(brief: dict[str, Any]) -> str:
    try:
        return _render_layer_e_payload(_layer_e_payload(build_layer_e_prepost_decision(brief)))
    except Exception as exc:  # noqa: BLE001 - compatibility surface reports unavailable gates.
        return f"## Layer E Story-Selling\n\nStatus: unavailable\nReason: {exc}"


def build_prepost_run_context(brief: dict[str, Any]) -> PrepostRunContext:
    workflow = build_workflow_context(
        BASE_DIR,
        skill_system_name="prepost_reel",
        recall_query=_brief_query(brief),
        profile="prepost",
        limit=4,
    )
    layer_e = _layer_e_payload(build_layer_e_prepost_decision(brief))
    return PrepostRunContext(workflow=workflow, layer_e=layer_e)


def _workflow_source_paths(context: PrepostRunContext) -> list[str]:
    paths: list[str] = []
    for field in ("components", "source_references"):
        values = context.workflow.skill_system.get(field, [])
        if isinstance(values, list):
            paths.extend(value for value in values if isinstance(value, str))
    return list(dict.fromkeys(paths))


def render_prepost_provenance(context: PrepostRunContext) -> str:
    return "\n".join(
        [
            "# Agentic OS Pre-Post Brief",
            "",
            "## Skill System",
            "",
            "```json",
            json.dumps(workflow_context_metadata(context.workflow), indent=2, ensure_ascii=False),
            "```",
            "",
            render_recall_bundle(context.workflow.recall).rstrip(),
            "",
            _render_layer_e_payload(context.layer_e),
        ]
    )


def build_agentic_os_brief(brief: dict[str, Any]) -> str:
    try:
        return render_prepost_provenance(build_prepost_run_context(brief))
    except Exception as exc:  # noqa: BLE001 - preserve diagnostic compatibility.
        return "\n".join(
            [
                "# Agentic OS Pre-Post Brief",
                "",
                "## Skill System",
                "",
                "```json",
                json.dumps(
                    {
                        "context_manifest": "config/agentic_context_manifest.json",
                        "skill_systems": "config/skill-systems.json",
                        "skill_system": "prepost_reel",
                        "status": "recall_unavailable",
                        "reason": str(exc),
                    },
                    indent=2,
                ),
                "```",
                "",
                "# Recall Bundle",
                "",
                "Status: recall_unavailable",
                "",
                "## Layer E Story-Selling",
                "",
                "Status: unavailable",
            ]
        )


def _schema_instruction(model: type[BaseModel]) -> str:
    return json.dumps(model.model_json_schema(), ensure_ascii=False, separators=(",", ":"))


def build_stage_system_prompts(context_text: str | None = None) -> dict[str, str]:
    compact = context_text or load_context()
    return {
        "combined_analysis": (
            "Evaluate one planned @a.storyof.two Reel across all five B1-B5 facets. "
            "Use only supplied evidence, keep unknowns explicit, and return JSON matching this schema.\n\n"
            f"{compact}\n\nSCHEMA\n{_schema_instruction(CombinedPrepostAnalysis)}"
        ),
        "independent_challenge": (
            "Independently audit the supplied pre-post analysis. Check score arithmetic, unsupported claims, "
            "missing inputs, and Layer E conflicts. Do not rewrite the five reports. Return JSON only.\n\n"
            f"SCHEMA\n{_schema_instruction(PrepostChallenge)}"
        ),
        "synthesis": (
            "Turn the locked scores, verdict, and challenge into concise creator-facing narrative fields. "
            "Do not change scores or verdict. Return JSON only.\n\n"
            f"SCHEMA\n{_schema_instruction(PrepostSynthesis)}"
        ),
    }


def build_system_prompt(agent_name: str, skill_names: list[str]) -> str:
    """Compatibility helper returning the compact combined-analysis prompt."""

    facets = ", ".join(name for name, _ in PREPOST_AGENT_CONFIGS)
    return build_stage_system_prompts()["combined_analysis"] + f"\n\nFacets: {facets}. Requested: {agent_name}."


def _json_text(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, indent=2, default=str)


def _extract_response_text(response: Any) -> str:
    content = getattr(response, "content", None)
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts = [getattr(block, "text", "") for block in content]
        return "\n".join(part for part in parts if part)
    raise ValueError("Model response did not contain text content")


def _parse_model_json(text: str, model: type[ModelT]) -> ModelT:
    stripped = text.strip()
    if stripped.startswith("```"):
        stripped = stripped.split("\n", 1)[1]
        stripped = stripped.rsplit("```", 1)[0]
    start, end = stripped.find("{"), stripped.rfind("}")
    if start < 0 or end < start:
        raise ValueError(f"{model.__name__} response was not a JSON object")
    return model.model_validate_json(stripped[start : end + 1])


def _usage_value(usage: Any, name: str) -> int | None:
    value = getattr(usage, name, None)
    return int(value) if value is not None else None


def _call_model(
    client: Any,
    *,
    stage: Literal["combined_analysis", "independent_challenge", "synthesis"],
    model_name: str,
    max_tokens: int,
    system: str,
    user: str,
    result_model: type[ModelT],
    context_ids: list[str],
) -> tuple[ModelT, PromptUsageRecord]:
    response = client.messages.create(
        model=model_name,
        max_tokens=max_tokens,
        system=system,
        messages=[{"role": "user", "content": user}],
    )
    result = _parse_model_json(_extract_response_text(response), result_model)
    usage = getattr(response, "usage", None)
    record = PromptUsageRecord(
        stage=stage,
        model=model_name,
        system_sha256=hashlib.sha256(system.encode()).hexdigest(),
        user_sha256=hashlib.sha256(user.encode()).hexdigest(),
        system_chars=len(system),
        user_chars=len(user),
        estimated_input_tokens=estimate_tokens(system) + estimate_tokens(user),
        actual_input_tokens=_usage_value(usage, "input_tokens"),
        actual_output_tokens=_usage_value(usage, "output_tokens"),
        cache_creation_input_tokens=_usage_value(usage, "cache_creation_input_tokens"),
        cache_read_input_tokens=_usage_value(usage, "cache_read_input_tokens"),
        context_ids=context_ids,
    )
    return result, record


VERDICT_RANK: dict[Verdict, int] = {"KILL": 0, "REWORK": 1, "REVISE": 2, "POST": 3}


def _cap_verdict(verdict: Verdict, cap: Verdict) -> Verdict:
    return verdict if VERDICT_RANK[verdict] <= VERDICT_RANK[cap] else cap


def compute_prepost_verdict(
    analysis: CombinedPrepostAnalysis,
    *,
    layer_e_status: str,
    challenger_cap: Verdict | None = None,
) -> tuple[Verdict, float]:
    adjusted = max(0.0, analysis.raw_total - (10 if analysis.audio_missing else 0))
    if adjusted >= 160:
        verdict: Verdict = "POST"
    elif adjusted >= 120:
        verdict = "REVISE"
    elif adjusted >= 80:
        verdict = "REWORK"
    else:
        verdict = "KILL"
    if analysis.hook.score < 5:
        verdict = _cap_verdict(verdict, "REWORK")
    if analysis.dm_send_score < 10 or analysis.cultural_authenticity_score < 5:
        verdict = _cap_verdict(verdict, "REVISE")
    layer_caps: dict[str, Verdict] = {"REPAIR": "REVISE", "REWORK": "REWORK", "STOP": "KILL"}
    if layer_e_status in layer_caps:
        verdict = _cap_verdict(verdict, layer_caps[layer_e_status])
    if challenger_cap:
        verdict = _cap_verdict(verdict, challenger_cap)
    return verdict, adjusted


def _bullet_block(items: list[str], fallback: str) -> str:
    values = items or [fallback]
    return "\n".join(f"- {item}" for item in values)


def render_prepost_report(
    brief: dict[str, Any],
    analysis: CombinedPrepostAnalysis,
    challenge: PrepostChallenge,
    synthesis: PrepostSynthesis,
    verdict: Verdict,
    adjusted_total: float,
) -> str:
    concept = str(brief.get("concept") or "Planned Reel")
    rows = [
        ("Hook", "B1 — Hook Analysis", analysis.hook),
        ("Edit & Loop", "B2 — Edit & Loop Audit", analysis.edit),
        ("Algorithm Fit", "B3 — Algorithm Fit Score", analysis.algorithm),
        ("Caption & Voice", "B4 — Caption & Voice", analysis.caption),
        ("Cultural Resonance", "B5 — Cultural Resonance", analysis.culture),
    ]
    score_table = "\n".join(
        ["| Agent | Score | Max |", "|---|---:|---:|"]
        + [f"| {label} | {facet.score:g} | {facet.max_score} |" for label, _, facet in rows]
        + [f"| **TOTAL** | **{adjusted_total:g}** | **200** |"]
    )
    specialist_reports = "\n\n".join(
        f"### {heading}\n\n{facet.report}" for _, heading, facet in rows
    )
    ready = ""
    if verdict in {"POST", "REVISE"}:
        ready = (
            "\n\n## Ready-to-Post Summary (if REVISE or POST verdict)\n\n"
            + (synthesis.ready_to_post_summary or "Complete the must-fix items, then recheck the locked verdict inputs.")
        )
    return f"""# Pre-Post Analysis — {concept}
## @a.storyof.two | {datetime.now().strftime('%Y-%m-%d')}

## Concept Summary

{synthesis.concept_summary}

## Agent Scores

{score_table}

## VERDICT: {verdict}

{synthesis.verdict_reason}

## Priority Actions (in order of algorithm impact)

### 🔴 Must Fix Before Posting

{_bullet_block(synthesis.must_fix, 'No blocking repair identified.')}

### 🟡 Should Fix If Time Allows

{_bullet_block(synthesis.should_fix, 'No secondary repair identified.')}

### 🟢 Nice to Have

{_bullet_block(synthesis.nice_to_have, 'No optional refinement identified.')}

## Independent Challenge

{_bullet_block(challenge.priority_corrections, 'No additional correction identified.')}

## Specialist Agent Reports

{specialist_reports}{ready}
"""


def _usage_report(records: list[PromptUsageRecord]) -> PrepostUsageReport:
    actual_inputs = [record.actual_input_tokens for record in records]
    actual_outputs = [record.actual_output_tokens for record in records]
    return PrepostUsageReport(
        calls=records,
        estimated_input_tokens_total=sum(record.estimated_input_tokens for record in records),
        actual_input_tokens_total=(sum(value for value in actual_inputs if value is not None) if all(value is not None for value in actual_inputs) else None),
        actual_output_tokens_total=(sum(value for value in actual_outputs if value is not None) if all(value is not None for value in actual_outputs) else None),
    )


def analyze_prepost(brief: dict, save: bool = True) -> str:
    """Analyze a planned Reel with one analyst, one challenger, and one synthesizer."""

    client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))
    context = build_prepost_run_context(brief)
    context_text = render_context_pack(context.workflow.recall.context)
    systems = build_stage_system_prompts(context_text)
    brief_json = _json_text(brief)
    layer_json = _json_text(context.layer_e)
    recall_text = render_recall_hits(
        context.workflow.recall,
        max_snippet_chars=600,
    )
    source_paths = _workflow_source_paths(context)
    context_ids = [section.id for section in context.workflow.recall.context.sections]
    context_ids.extend(hit.path for hit in context.workflow.recall.hits)
    context_ids.extend(source_paths)

    print("Running combined B1-B5 analyst...")
    analysis_user = (
        f"# Exact planned Reel inputs\n{brief_json}\n\n# Source paths (contents not embedded)\n"
        f"{_json_text(source_paths)}\n\n# Layer E\n{layer_json}\n\n# Bounded recall\n{recall_text}"
    )
    analysis, usage_analysis = _call_model(
        client,
        stage="combined_analysis",
        model_name="claude-sonnet-4-6",
        max_tokens=4000,
        system=systems["combined_analysis"],
        user=analysis_user,
        result_model=CombinedPrepostAnalysis,
        context_ids=context_ids + ["layer-e-story-selling.json"],
    )
    if not brief.get("audio") and not analysis.audio_missing:
        analysis = analysis.model_copy(update={"audio_missing": True})

    print("Running independent challenge...")
    challenge_user = f"# Exact planned Reel inputs\n{brief_json}\n\n# Layer E\n{layer_json}\n\n# Combined analysis\n{_json_text(analysis.model_dump())}"
    challenge, usage_challenge = _call_model(
        client,
        stage="independent_challenge",
        model_name="claude-sonnet-4-6",
        max_tokens=2000,
        system=systems["independent_challenge"],
        user=challenge_user,
        result_model=PrepostChallenge,
        context_ids=["combined_analysis", "layer-e-story-selling.json"],
    )
    verdict, adjusted_total = compute_prepost_verdict(
        analysis,
        layer_e_status=str(context.layer_e["status"]),
        challenger_cap=challenge.recommended_verdict_cap,
    )

    print("Running pre-post synthesis...")
    synthesis_user = (
        f"# Exact planned Reel inputs\n{brief_json}\n\n# Locked verdict\n{verdict}\n"
        f"Adjusted composite: {adjusted_total:g}/200\n\n# Combined analysis\n{_json_text(analysis.model_dump())}"
        f"\n\n# Independent challenge\n{_json_text(challenge.model_dump())}"
    )
    synthesis, usage_synthesis = _call_model(
        client,
        stage="synthesis",
        model_name="claude-opus-4-6",
        max_tokens=4000,
        system=systems["synthesis"],
        user=synthesis_user,
        result_model=PrepostSynthesis,
        context_ids=["combined_analysis", "independent_challenge", "locked_verdict"],
    )

    final_report = render_prepost_report(
        brief,
        analysis,
        challenge,
        synthesis,
        verdict,
        adjusted_total,
    )
    report_with_provenance = final_report + "\n---\n\n" + render_prepost_provenance(context)
    usage_report = _usage_report([usage_analysis, usage_challenge, usage_synthesis])

    if save:
        date_str = datetime.now().strftime("%Y-%m-%d")
        concept_slug = str(brief.get("concept", "reel"))[:40].replace(" ", "-").lower()
        concept_slug = "".join(char for char in concept_slug if char.isalnum() or char == "-") or "reel"
        filename = OUTPUT_DIR / f"{date_str}-{concept_slug}.md"
        filename.write_text(report_with_provenance, encoding="utf-8")
        usage_path = filename.with_suffix(".usage.json")
        usage_path.write_text(
            json.dumps(usage_report.model_dump(mode="json"), indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
        print(f"\nReport saved → {filename}")
        print(f"Usage saved → {usage_path}")

    return report_with_provenance


def interactive_mode() -> dict:
    """Prompt user for Reel brief interactively."""

    print("\n=== Pre-Post Analysis — @a.storyof.two ===\n")
    print("Describe the planned Reel. Press Enter to skip optional fields.\n")
    brief = {"concept": input("Concept (required): ").strip()}
    if not brief["concept"]:
        print("Concept is required.")
        sys.exit(1)
    brief["hook_plan"] = input("Hook plan (first 3 seconds): ").strip() or None
    brief["caption_draft"] = input("Caption draft: ").strip() or None
    brief["edit_plan"] = input("Edit plan / scene structure: ").strip() or None
    brief["audio"] = input("Planned audio: ").strip() or None
    brief["cover_frame"] = input("Cover frame description: ").strip() or None
    return {key: value for key, value in brief.items() if value}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Pre-post Reel analysis for @a.storyof.two")
    parser.add_argument("--concept", help="Video concept description")
    parser.add_argument("--hook", help="Hook plan (first 3 seconds)")
    parser.add_argument("--caption", help="Caption draft")
    parser.add_argument("--edit", help="Edit plan / scene structure")
    parser.add_argument("--audio", help="Planned audio")
    parser.add_argument("--cover", help="Cover frame description")
    parser.add_argument("--no-save", action="store_true", help="Don't save report to file")
    args = parser.parse_args()
    if args.concept:
        brief = {
            "concept": args.concept,
            "hook_plan": args.hook,
            "caption_draft": args.caption,
            "edit_plan": args.edit,
            "audio": args.audio,
            "cover_frame": args.cover,
        }
        brief = {key: value for key, value in brief.items() if value}
    else:
        brief = interactive_mode()
    report = analyze_prepost(brief, save=not args.no_save)
    print("\n" + "=" * 60)
    print(report)
