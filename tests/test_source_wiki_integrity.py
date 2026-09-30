import json
from datetime import date, timedelta
from pathlib import Path

import pytest

from pipeline.stages.a1_ingest import save_raw_items
from pipeline.stages.a2_parser import parse_raw_posts
from pipeline.stages.a3_analyzer import run as analyze
from pipeline.stages.a4_wiki import apply_compile_plan, check_compile, plan_compile
from pipeline.stages.source_integrity import load_raw_snapshot_registry, validate_raw_snapshot_registry
from pipeline.stages.wiki_health import collect_wiki_health


TODAY = date(2026, 9, 30)


def sample_items(label: str = "one") -> list[dict]:
    return [
        {
            "id": label,
            "shortCode": f"short-{label}",
            "caption": "a tiny caption #marriedlife",
            "type": "Video",
            "likesCount": 12,
            "commentsCount": 3,
        }
    ]


def source_chain(root: Path) -> tuple[Path, Path, Path]:
    raw = save_raw_items(sample_items(), root, today=TODAY)
    posts = parse_raw_posts(raw, root / "corpus" / "posts")
    analysis = analyze(root, posts_path=posts, today=TODAY)
    return raw, posts, analysis


def checks_by_id(health: dict) -> dict:
    return {check["id"]: check for check in health["checks"]}


def test_a1_is_idempotent_and_uses_collision_suffix_without_overwrite(tmp_path):
    first = save_raw_items(sample_items(), tmp_path, today=TODAY)
    original = first.read_bytes()

    assert save_raw_items(sample_items(), tmp_path, today=TODAY) == first
    second = save_raw_items(sample_items("two"), tmp_path, today=TODAY)

    registry = json.loads((tmp_path / "corpus" / "integrity" / "raw-snapshots.json").read_text())
    assert first.read_bytes() == original
    assert second.name == "2026-09-30-raw-2.json"
    assert [snapshot["raw_path"] for snapshot in registry["snapshots"]] == [
        "corpus/raw/2026-09-30-raw.json",
        "corpus/raw/2026-09-30-raw-2.json",
    ]
    assert registry["schema_version"] == 2
    assert registry["snapshots"][0]["schema_version"] == "raw-snapshot/v2"
    assert registry["snapshots"][0]["source_id"].startswith("a1-instagram:2026-09-30:")
    assert registry["snapshots"][0]["record_count"] == 1
    assert registry["snapshots"][0]["prior_version"] is None
    assert registry["snapshots"][1]["prior_version"] == registry["snapshots"][0]["snapshot_id"]

    first_posts = parse_raw_posts(first, tmp_path / "corpus" / "posts")
    second_posts = parse_raw_posts(second, tmp_path / "corpus" / "posts")
    assert first_posts.name == "2026-09-30-posts.json"
    assert second_posts.name == "2026-09-30-posts-2.json"


def test_identical_payload_on_different_days_has_distinct_capture_identity(tmp_path):
    first = save_raw_items(sample_items(), tmp_path, today=TODAY - timedelta(days=1))
    second = save_raw_items(sample_items(), tmp_path, today=TODAY)

    registry = load_raw_snapshot_registry(tmp_path)["snapshots"]
    assert first != second
    assert registry[0]["sha256"] == registry[1]["sha256"]
    assert registry[0]["snapshot_id"] != registry[1]["snapshot_id"]
    assert registry[1]["prior_version"] == registry[0]["snapshot_id"]
    assert validate_raw_snapshot_registry(tmp_path) == []


def test_a1_to_a4_preserves_verified_provenance_and_plan_is_non_mutating(tmp_path):
    raw, posts_path, analysis = source_chain(tmp_path)
    posts = json.loads(posts_path.read_text())
    provenance = posts[0]["source_provenance"]

    assert provenance["status"] == "verified"
    assert provenance["raw_path"] == raw.relative_to(tmp_path).as_posix()
    assert "a-story-source-provenance" in analysis.read_text()

    plan = plan_compile(tmp_path, analysis_path=analysis, today=TODAY)
    assert not plan.insight_path.exists()
    assert not plan.receipt_path.exists()
    assert plan.receipt["source_provenance"] == provenance

    assert apply_compile_plan(plan) == plan.insight_path
    assert plan.insight_path.exists()
    assert plan.receipt_path.exists()
    assert "snapshot_id" in plan.insight_path.read_text()
    assert "Compiled Analysis" in (tmp_path / "wiki" / "index.md").read_text()
    assert check_compile(tmp_path, analysis_path=analysis, today=TODAY) == []


def test_a3_rejects_a_changed_normalized_artifact_after_a2_receipt(tmp_path):
    raw = save_raw_items(sample_items(), tmp_path, today=TODAY)
    posts = parse_raw_posts(raw, tmp_path / "corpus" / "posts")
    posts.write_text("[]\n", encoding="utf-8")

    with pytest.raises(ValueError, match="normalized artifact hash mismatch"):
        analyze(tmp_path, posts_path=posts, today=TODAY)


def test_a4_rechecks_normalized_source_and_cites_a3_json_for_claim_pointers(tmp_path):
    _raw, posts, analysis = source_chain(tmp_path)
    analysis_json = analysis.with_suffix(".json")
    summary = json.loads(analysis_json.read_text())
    summary["cohorts"] = [{
        "format": "carousel",
        "age_band": "mature",
        "caption_patterns": [{"feature": "question", "difference": 1.0}],
    }]
    analysis_json.write_text(json.dumps(summary), encoding="utf-8")
    plan = plan_compile(tmp_path, analysis_path=analysis, today=TODAY)
    assert f"{analysis_json.relative_to(tmp_path).as_posix()}#/cohorts/" in plan.insight_text

    posts.write_text("[]\n", encoding="utf-8")
    with pytest.raises(ValueError, match="normalized artifact hash mismatch"):
        plan_compile(tmp_path, analysis_path=analysis, today=TODAY)


def test_a4_check_uses_recorded_compile_date_and_health_allows_historical_receipts(tmp_path):
    _raw, _posts, first_analysis = source_chain(tmp_path)
    apply_compile_plan(plan_compile(tmp_path, analysis_path=first_analysis, today=TODAY))
    assert check_compile(tmp_path, analysis_path=first_analysis) == []

    next_day = TODAY + timedelta(days=1)
    second_raw = save_raw_items(sample_items("two"), tmp_path, today=next_day)
    second_posts = parse_raw_posts(second_raw, tmp_path / "corpus" / "posts")
    second_analysis = analyze(tmp_path, posts_path=second_posts, today=next_day)
    apply_compile_plan(plan_compile(tmp_path, analysis_path=second_analysis, today=next_day))

    check = checks_by_id(collect_wiki_health(tmp_path, today=next_day))["a4_compile_receipts"]
    assert check["status"] == "PASS"
    assert check["evidence"]["active_receipt"].endswith(f"{second_analysis.stem}.json")
    assert len(check["evidence"]["historical_receipts"]) == 1

    apply_compile_plan(plan_compile(tmp_path, analysis_path=first_analysis, today=next_day))
    recompiled = checks_by_id(collect_wiki_health(tmp_path, today=next_day))["a4_compile_receipts"]
    assert recompiled["status"] == "PASS"
    assert recompiled["evidence"]["active_receipt"].endswith(f"{first_analysis.stem}.json")
    assert check_compile(tmp_path) == []


def test_a4_interrupted_compile_is_detectable_and_repeatable(tmp_path, monkeypatch):
    _raw, _posts, analysis = source_chain(tmp_path)
    plan = plan_compile(tmp_path, analysis_path=analysis, today=TODAY)
    from pipeline.stages import a4_wiki

    original = a4_wiki.atomic_write_text

    def fail_on_index(path, content):
        if Path(path) == plan.index_path:
            raise OSError("simulated interruption")
        original(path, content)

    monkeypatch.setattr(a4_wiki, "atomic_write_text", fail_on_index)
    with pytest.raises(OSError, match="simulated interruption"):
        apply_compile_plan(plan)
    assert plan.journal_path.exists()
    assert any("interrupted compile journal" in error for error in check_compile(tmp_path, analysis, TODAY))

    monkeypatch.setattr(a4_wiki, "atomic_write_text", original)
    apply_compile_plan(plan)
    assert not plan.journal_path.exists()
    assert check_compile(tmp_path, analysis, TODAY) == []


def test_a4_refuses_a_raw_snapshot_that_changed_after_a3(tmp_path):
    raw, _posts, analysis = source_chain(tmp_path)
    raw.write_text("[]\n", encoding="utf-8")

    with pytest.raises(ValueError, match="invalid source provenance"):
        plan_compile(tmp_path, analysis_path=analysis, today=TODAY)


def test_wiki_health_reports_tampered_registry_and_broken_index_link(tmp_path):
    raw, _posts, analysis = source_chain(tmp_path)
    apply_compile_plan(plan_compile(tmp_path, analysis_path=analysis, today=TODAY))
    index = tmp_path / "wiki" / "index.md"
    index.write_text(index.read_text() + "\n[broken](insights/nope.md)\n", encoding="utf-8")
    raw.write_text("[]\n", encoding="utf-8")

    checks = checks_by_id(collect_wiki_health(tmp_path, today=TODAY))
    assert checks["raw_snapshot_registry"]["status"] == "FAIL"
    assert checks["wiki_index_links"]["status"] == "FAIL"
    assert checks["a4_compile_receipts"]["status"] == "FAIL"
