"""JSON-safe workflow provenance helpers for Agentic OS integrations."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from pipeline.agentic.contracts import WorkflowContextBundle
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


def build_workflow_context(
    root: Path,
    *,
    skill_system_name: str,
    recall_query: str,
    profile: str = "a-story-of-two",
    limit: int = 6,
) -> WorkflowContextBundle:
    root = root.resolve()
    skill_system = resolve_skill_system(load_skill_systems(root), skill_system_name)
    recall = build_recall_bundle(root, query=recall_query, profile=profile, limit=limit)
    return WorkflowContextBundle(
        skill_system_name=skill_system_name,
        skill_system=skill_system,
        recall=recall,
    )


def workflow_context_metadata(bundle: WorkflowContextBundle) -> dict[str, Any]:
    return {
        "context_manifest": CONTEXT_MANIFEST,
        "skill_systems": SKILL_SYSTEMS_MANIFEST,
        "skill_system": bundle.skill_system,
        "recall_query": bundle.recall.query,
        "recall_hit_paths": [hit.path for hit in bundle.recall.hits],
        "recall_hits": [
            {
                "path": hit.path,
                "title": hit.title,
                "kind": hit.kind,
                "confidence": hit.confidence,
                "score": hit.score,
                "backend": hit.backend,
                "record_id": hit.record_id,
                "source_path": hit.source_path or hit.path,
                "source_pointer": hit.source_pointer,
                "content_sha256": hit.content_sha256,
                "authority": hit.authority,
                "lifecycle": hit.lifecycle,
            }
            for hit in bundle.recall.hits
        ],
    }


def build_workflow_metadata(
    root: Path,
    *,
    skill_system_name: str,
    recall_query: str,
    profile: str = "a-story-of-two",
    limit: int = 6,
) -> dict[str, Any]:
    bundle = build_workflow_context(
        root,
        skill_system_name=skill_system_name,
        recall_query=recall_query,
        profile=profile,
        limit=limit,
    )
    return workflow_context_metadata(bundle)


def build_workflow_recall_markdown(
    root: Path,
    *,
    query: str,
    profile: str = "a-story-of-two",
    limit: int = 6,
) -> str:
    return render_recall_bundle(build_recall_bundle(root, query=query, profile=profile, limit=limit))
