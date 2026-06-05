# Wiki Health Diagnostics

last_updated: 2026-06-05
confidence: 0.82
sources:
- AGENTS.md
- CLAUDE.md
- wiki/index.md
- memory/working.md
- memory/graph.json

## Status

Status: PASS
Failures: 0
Warnings: 0
Wiki pages: 78

## Checks

| Check | Status | Severity | Message |
| --- | --- | --- | --- |
| memory_surface | PASS | info | Required wiki, memory, graph, and log surfaces exist. |
| advertised_pipeline_files | PASS | info | AGENTS/CLAUDE advertised pipeline entry points exist. |
| instruction_surface_sync | PASS | info | AGENTS.md and CLAUDE.md share the required health and autopublish closeout commands. |
| agentic_os_surface | PASS | info | Agentic OS control-plane files exist and are available to future sessions. |
| wiki_index_total_pages | PASS | info | wiki/index.md total_pages matches actual wiki page count. |
| wiki_markdown_metadata | PASS | info | Every wiki page has last_updated, confidence, and sources metadata. |
| semantic_memory_confidence | PASS | info | Semantic memory markdown files carry confidence scores. |
| episodic_records | PASS | info | Episodic memory has at least one permanent session record. |
| session_logs | PASS | info | Session/log directory has written diagnostics. |

## Evidence

### memory_surface

```json
{
  "missing": []
}
```

### advertised_pipeline_files

```json
{
  "missing": []
}
```

### instruction_surface_sync

```json
{
  "required_files": [
    "AGENTS.md",
    "CLAUDE.md"
  ],
  "required_phrases": [
    "scripts/autopublish.py",
    "scripts/wiki_health.py --write --fix-index"
  ],
  "missing_files": [],
  "missing_phrases": {}
}
```

### agentic_os_surface

```json
{
  "required": [
    "pipeline/agentic/__init__.py",
    "pipeline/agentic/contracts.py",
    "pipeline/agentic/context_loader.py",
    "pipeline/agentic/skill_registry.py",
    "pipeline/agentic/memory_index.py",
    "pipeline/agentic/recall.py",
    "pipeline/agentic/audit_log.py",
    "pipeline/agentic/learning_loop.py",
    "pipeline/agentic/skill_eval.py",
    "pipeline/agentic/workflow_metadata.py",
    "pipeline/agentic/workflow_state.py",
    "scripts/agentic_os.py",
    "config/agentic_context_manifest.json",
    "config/skill-systems.json",
    "docs/superpowers/specs/agentic-os-control-plane.md"
  ],
  "missing": []
}
```

### wiki_index_total_pages

```json
{
  "declared": 78,
  "actual": 78
}
```

### wiki_markdown_metadata

```json
{}
```

### semantic_memory_confidence

```json
{}
```

### episodic_records

```json
{
  "count": 138
}
```

### session_logs

```json
{
  "count": 189
}
```
