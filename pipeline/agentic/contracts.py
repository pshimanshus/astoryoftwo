"""Typed contracts for the Agentic OS control plane."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Literal

from pydantic import BaseModel, Field, field_validator, model_validator


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


class ContextSection(BaseModel):
    id: str
    path: str
    kind: str
    estimated_tokens: int = Field(ge=0)
    content: str
    required: bool = True
    truncated: bool = False


class ContextPack(BaseModel):
    profile: str
    budget_tokens: int = Field(gt=0)
    estimated_tokens: int = Field(ge=0)
    sections: list[ContextSection]

    @model_validator(mode="after")
    def estimated_tokens_fit_budget(self) -> "ContextPack":
        if self.estimated_tokens > self.budget_tokens:
            raise ValueError("estimated_tokens must not exceed budget_tokens")
        return self


class SkillRecord(BaseModel):
    skill_id: str
    name: str
    kind: Literal["skill", "agent", "reference", "system", "unknown"] = "unknown"
    path: str
    description: str = ""
    dependencies: list[str] = Field(default_factory=list)
    confidence: float = Field(ge=0.0, le=1.0, default=0.5)

    @field_validator("skill_id")
    @classmethod
    def stable_skill_id(cls, value: str) -> str:
        if "." not in value:
            raise ValueError("skill_id must be namespaced with a stable prefix")
        return value


class MemoryRecord(BaseModel):
    record_id: str
    path: str
    title: str
    kind: str
    text: str
    tags: list[str] = Field(default_factory=list)
    confidence: float = Field(ge=0.0, le=1.0)


class RecallHit(BaseModel):
    path: str
    title: str
    kind: str
    snippet: str
    score: float = 0.0
    confidence: float = Field(ge=0.0, le=1.0, default=0.5)


class RecallBundle(BaseModel):
    query: str
    context: ContextPack
    hits: list[RecallHit]


class AuditEvent(BaseModel):
    event_id: str
    actor: str
    action: str
    target_path: str
    rationale: str
    evidence_paths: list[str] = Field(default_factory=list)
    created_at: str = Field(default_factory=utc_now_iso)


class LearningEvent(BaseModel):
    event_id: str
    source: str
    summary: str
    evidence_paths: list[str] = Field(default_factory=list)
    created_at: str = Field(default_factory=utc_now_iso)


class LearningProposal(BaseModel):
    proposal_id: str
    source_event_id: str
    target_path: str
    proposed_action: Literal["create", "modify", "deprecate"]
    rationale: str
    before_hash: str
    after_hash: str
    required_validators: list[str]
    status: Literal["draft", "approved", "rejected", "applied"] = "draft"
    auto_apply: bool = False
    proposed_content_path: str | None = None
    created_at: str = Field(default_factory=utc_now_iso)


class SkillEvalResult(BaseModel):
    proposal_id: str
    status: Literal["PASS", "FAIL"]
    issues: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)


class WorkflowGate(BaseModel):
    name: str
    status: Literal["GO", "REPAIR", "STOP", "PASS", "FAIL"]
    reason: str = ""
    evidence_paths: list[str] = Field(default_factory=list)
