"""Build cited recall bundles from context packs and indexed memory."""

from __future__ import annotations

from pathlib import Path

from pipeline.agentic.context_loader import assemble_context_pack, render_context_pack
from pipeline.agentic.contracts import RecallBundle, RecallHit
from pipeline.agentic.retrieval import search as search_retrieval


def build_recall_bundle(
    root: Path,
    query: str,
    profile: str | None = None,
    limit: int = 8,
    backend: str | None = None,
) -> RecallBundle:
    context = assemble_context_pack(root, profile=profile)
    hits = search_retrieval(root, query, limit=limit, backend=backend)
    return RecallBundle(query=query, context=context, hits=hits)


def render_hit(hit: RecallHit, rank: int, *, max_snippet_chars: int | None = None) -> str:
    snippet = hit.snippet
    if max_snippet_chars is not None and len(snippet) > max_snippet_chars:
        snippet = snippet[:max_snippet_chars].rstrip() + " [TRUNCATED]"
    return "\n".join(
        [
            f"### {rank}. {hit.title}",
            "",
            f"- Path: `{hit.path}`",
            f"- Source: `{hit.source_path or hit.path}` ({hit.source_pointer or 'whole document'})",
            f"- Backend: {hit.backend}",
            f"- Requested backend: {hit.requested_backend}",
            f"- Kind: {hit.kind}",
            f"- Authority: {hit.authority}",
            f"- Lifecycle: {hit.lifecycle}",
            f"- Source hash: `{hit.content_sha256}`",
            f"- Record ID: `{hit.record_id}`",
            f"- Scope: {hit.scope or 'unspecified'}",
            f"- Package: `{hit.package}`" if hit.package else "- Package: none",
            f"- Feedback IDs: {', '.join(hit.feedback_ids) if hit.feedback_ids else 'none'}",
            f"- Fallback: {hit.fallback_reason}" if hit.fallback_reason else "- Fallback: none",
            f"- Confidence: {hit.confidence:.2f}",
            f"- Score: {hit.score:.4f}",
            "",
            snippet,
        ]
    )


def render_recall_hits(
    bundle: RecallBundle,
    *,
    max_snippet_chars: int | None = None,
) -> str:
    lines = ["## Ranked Long-Term Recall", ""]
    if bundle.hits:
        for index, hit in enumerate(bundle.hits, start=1):
            lines.extend(
                [render_hit(hit, index, max_snippet_chars=max_snippet_chars), ""]
            )
    else:
        lines.extend(["No ranked long-term recall hits found.", ""])
    return "\n".join(lines).rstrip() + "\n"


def render_recall_bundle(bundle: RecallBundle) -> str:
    lines = [
        "# Recall Bundle",
        "",
        f"Query: {bundle.query}",
        "",
        render_context_pack(bundle.context).rstrip(),
        "",
        render_recall_hits(bundle).rstrip(),
        "",
    ]
    return "\n".join(lines).rstrip() + "\n"
