#!/usr/bin/env python3
"""Evaluate real retrieval backends on a versioned, held-out corpus."""
from __future__ import annotations

import argparse
import json
import math
import statistics
import sys
import tempfile
import time
import tracemalloc
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from pipeline.agentic.retrieval import backend_name, get_backend  # noqa: E402
from pipeline.agentic.retrieval_errors import BackendStale, BackendUnavailable  # noqa: E402

REPORT_VERSION = "retrieval-benchmark-report/v2"

def _percentile(values: list[float], percentile: float) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    position = max(0, min(len(ordered) - 1, math.ceil(percentile * len(ordered)) - 1))
    return ordered[position]

def _ndcg_at_five(retrieved: list[str], relevance: dict[str, int]) -> float:
    unique_retrieved = list(dict.fromkeys(retrieved))
    gains = [int(relevance.get(path, 0)) for path in unique_retrieved[:5]]
    dcg = sum((2**gain - 1) / math.log2(rank + 1) for rank, gain in enumerate(gains, 1))
    ideal = sorted(relevance.values(), reverse=True)[:5]
    idcg = sum((2**gain - 1) / math.log2(rank + 1) for rank, gain in enumerate(ideal, 1))
    return dcg / idcg if idcg else 1.0

def _directory_bytes(path: Path) -> int:
    return sum(item.stat().st_size for item in path.rglob("*") if item.is_file()) if path.exists() else 0

def _materialize_fixture(payload: dict[str, Any], destination: Path) -> None:
    for source in payload.get("corpus") or []:
        path = destination / str(source["path"])
        path.parent.mkdir(parents=True, exist_ok=True)
        if "json" in source:
            path.write_text(json.dumps(source["json"], ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        else:
            path.write_text(str(source.get("text") or ""), encoding="utf-8")

def _query_rows(backend: Any, root: Path, queries: list[dict[str, Any]],
                *, limit: int, repetitions: int) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for query in queries:
        samples: list[float] = []
        final_hits = []
        for _ in range(repetitions):
            started = time.perf_counter()
            final_hits = backend.search(root, str(query["query"]), limit)
            samples.append((time.perf_counter() - started) * 1000)
        paths = [hit.source_path for hit in final_hits]
        scored_paths = list(dict.fromkeys(paths))
        relevance = {str(path): int(gain) for path, gain in (query.get("relevance") or {}).items()}
        expected = set(relevance)
        forbidden_paths = tuple(str(value) for value in query.get("forbidden_source_paths") or [])
        forbidden_text = [str(value).casefold() for value in query.get("forbidden_text") or []]
        combined = " ".join(hit.snippet for hit in final_hits).casefold()
        actual_names = {hit.backend for hit in final_hits}
        rows.append({
            "id": query["id"], "class": query["class"], "critical": bool(query["critical"]),
            "cold_latency_ms": round(samples[0], 3),
            "warm_latency_ms": [round(value, 3) for value in samples[1:]],
            "retrieved_record_ids": [hit.record_id for hit in final_hits],
            "retrieved_source_paths": paths,
            "scored_source_paths": scored_paths,
            "recall_at_3": (len(expected.intersection(scored_paths[:3])) / len(expected)) if expected else 1.0,
            "expected_top3": bool(expected.intersection(scored_paths[:3])) if expected else True,
            "ndcg_at_5": round(_ndcg_at_five(scored_paths, relevance), 6),
            "role_boundary_failure": any(path.startswith(forbidden_paths) for path in paths) if forbidden_paths else False,
            "forbidden_text_failure": any(value in combined for value in forbidden_text),
            "citation_valid": all(hit.record_id and hit.source_path and hit.source_pointer
                                  and hit.content_sha256 for hit in final_hits),
            "actual_backend_names": sorted(actual_names),
        })
    return rows

def _summary(rows: list[dict[str, Any]], *, baseline_ndcg: float | None,
             build_ms: float, peak_memory_bytes: int, footprint_bytes: int) -> dict[str, Any]:
    ndcgs = [float(row["ndcg_at_5"]) for row in rows]
    critical = [row for row in rows if row["critical"]]
    warm = [value for row in rows for value in row["warm_latency_ms"]]
    mean_ndcg = statistics.fmean(ndcgs) if ndcgs else 0.0
    critical_pass = all(row["expected_top3"] and row["citation_valid"]
                        and not row["role_boundary_failure"] and not row["forbidden_text_failure"]
                        for row in critical)
    improvement = None if baseline_ndcg is None else mean_ndcg - baseline_ndcg
    return {
        "status": "evaluated", "mean_ndcg_at_5": round(mean_ndcg, 4),
        "mean_recall_at_3": round(statistics.fmean(float(row["recall_at_3"]) for row in rows), 4) if rows else 0.0,
        "critical_queries_pass": critical_pass,
        "role_boundary_failures": sum(bool(row["role_boundary_failure"]) for row in rows),
        "forbidden_text_failures": sum(bool(row["forbidden_text_failure"]) for row in rows),
        "p95_cold_latency_ms": round(_percentile([float(row["cold_latency_ms"]) for row in rows], .95), 3),
        "p95_warm_latency_ms": round(_percentile(warm, .95), 3),
        "build_ms": round(build_ms, 3), "peak_build_memory_bytes": peak_memory_bytes,
        "footprint_bytes": footprint_bytes,
        "improvement_over_fts5": None if improvement is None else round(improvement, 4),
        "qualified": critical_pass and baseline_ndcg is not None and improvement is not None and improvement >= .10,
    }

def _evaluate(backend: Any, root: Path, payload: dict[str, Any], *, limit: int,
              repetitions: int, baseline_ndcg: float | None) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    available, reason = backend.availability()
    if not available:
        return [], {"status": "not_evaluated", "reason": reason, "qualified": False}
    try:
        tracemalloc.start()
        started = time.perf_counter()
        index_path = backend.build(root)
        build_ms = (time.perf_counter() - started) * 1000
        _current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        rows = _query_rows(backend, root, payload["queries"], limit=limit, repetitions=repetitions)
    except (BackendUnavailable, BackendStale, OSError, ValueError) as exc:
        if tracemalloc.is_tracing():
            tracemalloc.stop()
        return [], {"status": "not_evaluated", "reason": f"{type(exc).__name__}: {exc}", "qualified": False}
    summary = _summary(rows, baseline_ndcg=baseline_ndcg, build_ms=build_ms,
                       peak_memory_bytes=peak, footprint_bytes=_directory_bytes(index_path if index_path.is_dir() else index_path.parent))
    return rows, summary

def run(root: Path, fixture: Path, backends: list[str], limit: int = 5,
        repetitions: int = 3) -> dict[str, Any]:
    payload = json.loads(fixture.read_text(encoding="utf-8"))
    if int(payload.get("fixture_version") or 0) != 2:
        raise ValueError("benchmark fixture must declare fixture_version 2")
    requested = []
    for name in ["fts5", *backends]:
        canonical = backend_name(name)
        if canonical not in requested:
            requested.append(canonical)
    report: dict[str, Any] = {"schema_version": REPORT_VERSION,
                              "fixture_schema_version": payload["schema_version"],
                              "fixture": str(fixture), "repetitions": repetitions,
                              "backends": {}, "selection": {}}
    with tempfile.TemporaryDirectory(prefix="asot-retrieval-benchmark-") as raw:
        benchmark_root = Path(raw) if payload.get("corpus") else root.resolve()
        if payload.get("corpus"):
            _materialize_fixture(payload, benchmark_root)
        baseline_ndcg: float | None = None
        for name in requested:
            rows, summary = _evaluate(get_backend(name), benchmark_root, payload, limit=limit,
                                      repetitions=max(2, repetitions), baseline_ndcg=baseline_ndcg)
            if name == "fts5" and summary.get("status") == "evaluated":
                baseline_ndcg = float(summary["mean_ndcg_at_5"])
                summary["qualified"] = bool(summary["critical_queries_pass"])
            report["backends"][name] = {"summary": summary, "queries": rows}
        candidates = [(name, value["summary"]) for name, value in report["backends"].items()
                      if name != "fts5" and value["summary"].get("qualified")]
        if candidates:
            selected, summary = min(candidates, key=lambda item: (item[1]["p95_warm_latency_ms"],
                                                                   item[1]["footprint_bytes"], item[0]))
            report["selection"] = {"selected_backend": selected,
                                   "reason": "candidate passed critical, boundary, citation, and +0.10 nDCG gates",
                                   "p95_warm_latency_ms": summary["p95_warm_latency_ms"],
                                   "footprint_bytes": summary["footprint_bytes"]}
        else:
            report["selection"] = {"selected_backend": "fts5",
                                   "reason": "no evaluated semantic candidate passed every release gate"}
    return report

def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workspace-root", type=Path, default=ROOT)
    parser.add_argument("--fixture", type=Path, default=ROOT / "tests/fixtures/retrieval/held-out-v1.json")
    parser.add_argument("--backend", action="append", default=[])
    parser.add_argument("--limit", type=int, default=5)
    parser.add_argument("--repetitions", type=int, default=3)
    parser.add_argument("--report", type=Path, default=ROOT / "output/reports/retrieval/benchmark-v2.json")
    args = parser.parse_args(argv)
    report = run(args.workspace_root.resolve(), args.fixture, args.backend, args.limit, args.repetitions)
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
