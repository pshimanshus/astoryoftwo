"""Build cited recall bundles from context packs and indexed memory."""

from __future__ import annotations

from pathlib import Path

from pipeline.agentic.context_loader import assemble_context_pack, render_context_pack
from pipeline.agentic.contracts import RecallBundle, RecallHit
from pipeline.agentic.memory_index import build_memory_index, search_memory


def build_recall_bundle(
    root: Path,
    query: str,
    profile: str | None = None,
    limit: int = 8,
) -> RecallBundle:
    context = assemble_context_pack(root, profile=profile)
    index_path = build_memory_index(root)
    hits = search_memory(index_path, query, limit=limit)
    return RecallBundle(query=query, context=context, hits=hits)


def render_hit(hit: RecallHit, rank: int) -> str:
    return "\n".join(
        [
            f"### {rank}. {hit.title}",
            "",
            f"- Path: `{hit.path}`",
            f"- Kind: {hit.kind}",
            f"- Confidence: {hit.confidence:.2f}",
            f"- Score: {hit.score:.4f}",
            "",
            hit.snippet,
        ]
    )


def render_recall_bundle(bundle: RecallBundle) -> str:
    lines = [
        "# Recall Bundle",
        "",
        f"Query: {bundle.query}",
        "",
        render_context_pack(bundle.context).rstrip(),
        "",
        "## Ranked Long-Term Recall",
        "",
    ]
    if bundle.hits:
        for index, hit in enumerate(bundle.hits, start=1):
            lines.extend([render_hit(hit, index), ""])
    else:
        lines.extend(["No ranked long-term recall hits found.", ""])
    return "\n".join(lines).rstrip() + "\n"
