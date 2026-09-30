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
    kind: Literal["skill", "repo_skill", "agent", "reference", "system", "unknown"] = "unknown"
    path: str
    description: str = ""
    dependencies: list[str] = Field(default_factory=list)
    implicit_invocation: bool | None = None
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
    # `path` is retained for callers written before the retrieval manifest.
    # The fields below let a later workflow reproduce the exact evidence used.
    backend: str = "fts5"
    requested_backend: str = "fts5"
    record_id: str = ""
    source_path: str = ""
    source_pointer: str = ""
    content_sha256: str = ""
    authority: str = "reviewed_observation"
    lifecycle: str = "active"
    scope: str = ""
    package: str = ""
    feedback_ids: list[str] = Field(default_factory=list)
    fallback_reason: str = ""


class RecallBundle(BaseModel):
    query: str
    context: ContextPack
    hits: list[RecallHit]


class WorkflowContextBundle(BaseModel):
    skill_system_name: str
    skill_system: dict[str, object]
    recall: RecallBundle


class AuditEvent(BaseModel):
    event_id: str
    actor: str
    action: str
    target_path: str
    rationale: str
    evidence_paths: list[str] = Field(default_factory=list)
    created_at: str = Field(default_factory=utc_now_iso)


class LearningEvent(BaseModel):
    schema_version: str = "learning-event/v1"
    event_id: str
    source: str
    summary: str
    evidence_paths: list[str] = Field(default_factory=list)
    user_instruction_exact: str | None = None
    diagnosis: str | None = None
    scope: str | None = None
    package_path: str | None = None
    feedback_status: str | None = None
    resolution_evidence: list[str] = Field(default_factory=list)
    eval_disposition: str | None = None
    supersedes_event_id: str | None = None
    feedback_metadata: dict[str, object] | None = None
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
    kind: Literal[
        "input",
        "intermediate",
        "output",
        "blocker",
        "report",
        "log",
    ]
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


class RepairAttempt(BaseModel):
    attempted_at: str = Field(default_factory=utc_now_iso)
    reason: str
    gate_failures: list[WorkflowGate] = Field(default_factory=list)


class WorkflowStateRecord(BaseModel):
    state: str
    entered_at: str = Field(default_factory=utc_now_iso)
    exited_at: str | None = None
    gates: list[WorkflowGate] = Field(default_factory=list)
    repair_budget: RepairBudget = Field(default_factory=RepairBudget)
    repair_history: list[RepairAttempt] = Field(default_factory=list)
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
