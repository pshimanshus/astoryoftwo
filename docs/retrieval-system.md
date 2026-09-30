# Retrieval System

All retrieval backends consume the same generated
`memory/agentic/index/retrieval-manifest.json`. Each eligible chunk carries an
exact source pointer, source hash, authority, lifecycle, scope, package,
feedback IDs, and role eligibility. The generated manifest and indexes are
ignored by Git and can be rebuilt from repository evidence.

FTS5 is the production default and updates incrementally by manifest record ID,
including removal of deleted or retired records:

```bash
venv/bin/python scripts/agentic_os.py index --backend fts5
venv/bin/python scripts/agentic_os.py search "visible emotional change"
```

QMD and multilingual E5 are opt-in evaluation candidates. QMD uses an isolated
generated collection and disables update hooks. E5 persists normalized vectors
and fuses dense and FTS ranks with reciprocal-rank fusion. Neither dependency is
imported during normal FTS startup.

```bash
ASOT_RETRIEVAL_QMD_ENABLED=1 venv/bin/python scripts/agentic_os.py index --backend qmd
venv/bin/pip install -r requirements-retrieval.txt
ASOT_RETRIEVAL_LOCAL_DENSE_ENABLED=1 venv/bin/python scripts/agentic_os.py index --backend sentence_transformers
```

Run the versioned held-out comparison with:

```bash
venv/bin/python scripts/benchmark_retrieval.py --backend qmd --backend sentence_transformers
```

The report records candidates as `not_evaluated` when their real executable,
model, or fresh derived index is unavailable. FTS fallback is never scored as a
semantic result. A candidate can be selected only after every critical query is
in the top three, citations and role boundaries pass, and mean nDCG@5 improves
by at least 0.10 over FTS5; ties use warm p95 latency and then disk footprint.
