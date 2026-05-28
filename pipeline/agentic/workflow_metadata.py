"""JSON-safe workflow provenance helpers for Agentic OS integrations."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from pipeline.agentic.recall import build_recall_bundle, render_recall_bundle
from pipeline.agentic.skill_registry import load_skill_systems, resolve_skill_system


CONTEXT_MANIFEST = "config/agentic_context_manifest.json"
SKILL_SYSTEMS_MANIFEST = "config/skill-systems.json"


def build_workflow_contract(skill_system_name: str) -> dict[str, str]:
    return {
        "context_manifest": CONTEXT_MANIFEST,
        "skill_systems": SKILL_SYSTEMS_MANIFEST,
        "skill_system": skill_system_name,
    }


def build_workflow_metadata(
    root: Path,
    *,
    skill_system_name: str,
    recall_query: str,
    profile: str = "a-story-of-two",
    limit: int = 6,
) -> dict[str, Any]:
    root = root.resolve()
    skill_system = resolve_skill_system(load_skill_systems(root), skill_system_name)
    recall_bundle = build_recall_bundle(root, query=recall_query, profile=profile, limit=limit)
    return {
        "context_manifest": CONTEXT_MANIFEST,
        "skill_systems": SKILL_SYSTEMS_MANIFEST,
        "skill_system": skill_system,
        "recall_query": recall_query,
        "recall_hit_paths": [hit.path for hit in recall_bundle.hits],
        "recall_hits": [
            {
                "path": hit.path,
                "title": hit.title,
                "kind": hit.kind,
                "confidence": hit.confidence,
                "score": hit.score,
            }
            for hit in recall_bundle.hits
        ],
    }


def build_workflow_recall_markdown(
    root: Path,
    *,
    query: str,
    profile: str = "a-story-of-two",
    limit: int = 6,
) -> str:
    return render_recall_bundle(build_recall_bundle(root, query=query, profile=profile, limit=limit))
