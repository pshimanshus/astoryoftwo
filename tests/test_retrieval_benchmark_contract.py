import json
from pathlib import Path

from scripts.benchmark_retrieval import _ndcg_at_five, run


def test_held_out_retrieval_fixture_has_required_query_classes():
    fixture = Path(__file__).parent / "fixtures" / "retrieval" / "held-out-v1.json"
    payload = json.loads(fixture.read_text(encoding="utf-8"))
    assert payload["schema_version"] == "retrieval-benchmark/v2"
    assert payload["fixture_version"] == 2
    corpus_paths = {row["path"] for row in payload["corpus"]}
    classes = {row["class"] for row in payload["queries"]}
    assert {
        "exact", "paraphrase", "hindi", "hinglish", "negation", "conflict",
        "latest_correction", "rejected_route", "package_isolation",
        "forbidden_role_leakage",
    } <= classes
    assert all("critical" in row and row.get("relevance") for row in payload["queries"])
    assert all(set(row["relevance"]) <= corpus_paths for row in payload["queries"])


def test_benchmark_does_not_score_an_unavailable_candidate_as_fts_fallback(tmp_path, monkeypatch):
    monkeypatch.delenv("ASOT_RETRIEVAL_QMD_ENABLED", raising=False)
    fixture = Path(__file__).parent / "fixtures" / "retrieval" / "held-out-v1.json"
    report = run(tmp_path, fixture, ["qmd"], repetitions=2)
    assert report["schema_version"] == "retrieval-benchmark-report/v2"
    assert report["backends"]["fts5"]["summary"]["critical_queries_pass"] is True
    assert report["backends"]["qmd"]["summary"]["status"] == "not_evaluated"
    assert report["backends"]["qmd"]["queries"] == []
    assert report["selection"]["selected_backend"] == "fts5"


def test_source_level_ndcg_deduplicates_multiple_chunks_from_one_source():
    score = _ndcg_at_five(
        ["memory/semantic/sequence.md", "memory/semantic/sequence.md"],
        {"memory/semantic/sequence.md": 3},
    )
    assert score == 1.0
