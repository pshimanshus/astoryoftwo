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
    success_standard_excerpt: str = ""
    creator_preference_excerpt: str = ""


class ProcessInfluence(BaseModel):
    id: str
    title: str
    influence_type: str
    source_patterns: list[str] = Field(default_factory=list)
    confidence: float = Field(ge=0.0, le=1.0, default=0.5)
    reason: str = ""


class ExpertAgentOutput(BaseModel):
    agent: str
    role: str
    claim: str
    objection: str = ""
    recommendation: str = ""
    score: float | None = None


class LayerERoomOutput(BaseModel):
    name: str
    status: LayerEStatus
    agents: list[ExpertAgentOutput]
    summary: str
    selected_outputs: dict[str, str] = Field(default_factory=dict)
    objections: list[str] = Field(default_factory=list)
    repairs: list[str] = Field(default_factory=list)


class StoryRoute(BaseModel):
    name: str
    story_lens: str
    reader_mirror: str
    emotional_obstacle: str
    aachu_specific_spark: str
    zuv_active_role: str
    proof_engine: str
    emotional_reversal: str
    payoff: str
    distribution_reason: str
    process_influence_ids: list[str] = Field(default_factory=list)
    score_total: float = Field(ge=0, le=30, default=0)
    hard_fails: list[str] = Field(default_factory=list)
    verdict: LayerEStatus = "REPAIR"


class StorySellingScore(BaseModel):
    reader_identity_mirror: float = Field(ge=0, le=5)
    romantic_conflict_stakes: float = Field(ge=0, le=5)
    specificity_of_proof: float = Field(ge=0, le=5)
    emotional_reversal: float = Field(ge=0, le=5)
    visual_scene_clarity: float = Field(ge=0, le=5)
    online_share_save_sell_potential: float = Field(ge=0, le=5)
    total: float = Field(ge=0, le=30)


class LayerEDecision(BaseModel):
    schema_version: str = "1.0"
    status: LayerEStatus
    task_type: LayerETaskType
    adaptation_target: Literal["C-layer", "D-layer", "B-layer", "diagnostic"]
    rooms: dict[str, LayerERoomOutput]
    exploration_routes: list[StoryRoute]
    repaired_routes: list[StoryRoute] = Field(default_factory=list)
    rejected_routes: list[StoryRoute] = Field(default_factory=list)
    selected_story_lens: str
    emotional_machine: str
    proof_engine: str
    reader_mirror: str
    distribution_reason: str
    process_influences: list[ProcessInfluence]
    story_selling_score: StorySellingScore
    hard_fails: list[str] = Field(default_factory=list)
    required_repairs: list[str] = Field(default_factory=list)
    golden_theme_gate: Literal["required_for_carousel", "not_applicable"]
    downstream_contract: dict[str, Any] = Field(default_factory=dict)
    metadata: dict[str, Any] = Field(default_factory=dict)
