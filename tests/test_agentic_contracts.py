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


def test_audit_event_records_actor_action_and_evidence():
    event = AuditEvent(
        event_id="audit-1",
        actor="codex",
        action="context_pack_loaded",
        target_path="config/agentic_context_manifest.json",
        rationale="Loaded profile before carousel work.",
        evidence_paths=["config/voice.md", "memory/working.md"],
    )

    assert event.actor == "codex"
    assert event.evidence_paths == ["config/voice.md", "memory/working.md"]
