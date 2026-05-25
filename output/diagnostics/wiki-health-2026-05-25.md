# Wiki Health Diagnostics

last_updated: 2026-05-25
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
Wiki pages: 62

## Checks

| Check | Status | Severity | Message |
| --- | --- | --- | --- |
| memory_surface | PASS | info | Required wiki, memory, graph, and log surfaces exist. |
| advertised_pipeline_files | PASS | info | AGENTS/CLAUDE advertised pipeline entry points exist. |
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

### wiki_index_total_pages

```json
{
  "declared": 62,
  "actual": 62
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
  "count": 52
}
```

### session_logs

```json
{
  "count": 52
}
```
