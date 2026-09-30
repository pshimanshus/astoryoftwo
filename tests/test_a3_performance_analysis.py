"""Evidence integrity and end-to-end regressions for the A3 analyzer."""
import hashlib
import json
from datetime import date, timedelta
from pathlib import Path

import pytest

from pipeline.stages.a2_parser import normalize_post
from pipeline.stages.a3_analyzer import analyze_posts, report_markdown, run

TODAY = date(2026, 9, 5)
COLLECTED = date(2026, 9, 1)


def post(identifier, likes, *, age=20, kind="Video", **fields):
    return {"id": str(identifier), "shortCode": f"post_{identifier}",
            "ownerUsername": "a.storyof.two", "type": kind,
            "timestamp": (COLLECTED - timedelta(days=age)).isoformat(),
            "caption": f"A moment with you {identifier}", "likesCount": likes, **fields}


def cohort(**fields):
    return [post(i, likes, **fields) for i, likes in enumerate([0, 10, 20, 30, 40, 50, 60, 100])]


def analyze(rows):
    return analyze_posts(rows, COLLECTED, TODAY)


def snapshot(root, rows, name="2026-09-01-raw.json", directory="raw"):
    path = root / "corpus" / directory / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(rows))
    return path


def comparison(summary, metric="likes"):
    return next(c for group in summary["cohorts"] for c in group["comparisons"] if c["metric"] == metric)


def test_stronger_and_weaker_are_linked_to_posts_with_exact_median():
    summary = analyze(cohort())
    result = comparison(summary)
    assert result["median"] == 35
    assert result["higher"] == ["6", "7"]
    assert result["lower"] == ["0", "1"]
    assert summary["metric_coverage"]["likes"] == {"observed": 8, "unavailable": 0, "median": 35}
    text = report_markdown(summary, Path("snapshot.json"), TODAY)
    assert "https://www.instagram.com/p/post_7/" in text
    assert "https://www.instagram.com/p/post_0/" in text
    assert "confidence: 0.72" not in text
    assert "not causal" in text


def test_comparisons_do_not_mix_formats_or_age_bands():
    rows = cohort() + [post("image", 9999999, kind="Image"), post("old", 9999999, age=50), post("new", 9999999, age=2)]
    summary = analyze(rows)
    result = comparison(summary)
    assert result["median"] == 35
    assert "image" not in result["higher"]
    assert "old" not in result["higher"]
    assert "new" not in result["higher"]
    assert summary["cohort_exclusions"]["outside_7_to_60_day_window"] == 1


@pytest.mark.parametrize("age,expected", [(6, None), (7, "7-13"), (13, "7-13"), (14, "14-29"), (29, "14-29"), (30, "30-60"), (60, "30-60"), (61, None), (-1, None)])
def test_age_boundaries(age, expected):
    summary = analyze([post(1, 10, age=age)])
    assert [c["age_band"] for c in summary["cohorts"]] == ([expected] if expected else [])


@pytest.mark.parametrize("value", [None, -1, True, False, "0", float("nan"), float("inf"), [], {}, 10**400])
def test_invalid_metrics_remain_unavailable(value):
    summary = analyze([post("invalid", value)])
    assert summary["metric_coverage"]["likes"]["observed"] == 0
    assert summary["metric_coverage"]["likes"]["median"] is None


def test_missing_metrics_are_not_padded_with_zeros():
    summary = analyze(cohort())
    for metric in ["comments", "reach", "sends", "shares", "saves", "retention_rate"]:
        assert summary["metric_coverage"][metric]["observed"] == 0
        assert summary["metric_coverage"][metric]["median"] is None


def test_legacy_zero_is_ambiguous_but_new_parser_zero_is_observed():
    legacy = {"id": "legacy", "timestamp": "2026-08-10", "post_type": "video", "engagement": {"likes": 0, "comments": 3}}
    summary = analyze([legacy, normalize_post(post("new", 0))])
    assert summary["metric_coverage"]["likes"]["observed"] == 1
    assert summary["metric_coverage"]["comments"]["observed"] == 1
    by_id = {p["id"]: p for p in summary["posts"]}
    assert by_id["legacy"]["metric_status"]["likes"] == "ambiguous_legacy_zero"
    assert by_id["new"]["engagement"]["likes"] == 0


def test_observation_status_overrides_a_numeric_placeholder():
    row = normalize_post(post("x", 50))
    row["metric_status"]["likes"] = "unavailable"
    assert analyze([row])["metric_coverage"]["likes"]["observed"] == 0


def test_rates_require_paired_positive_reach_and_keep_shares_sends_separate():
    rows = [post("both", 50, reach=100, sends=10, shares=20),
            post("zero", 50, reach=0, sends=10), post("missing", 50, sends=10),
            post("no_numerator", 50, reach=100)]
    summary = analyze(rows)
    assert summary["metric_coverage"]["sends_per_reach"]["median"] == .1
    assert summary["metric_coverage"]["shares_per_reach"]["median"] == .2
    assert summary["metric_coverage"]["sends_per_reach"]["observed"] == 1


def test_nonfinite_derived_rate_is_unavailable():
    summary = analyze([post("huge", 1, sends=1e308, reach=1e-308)])
    assert summary["metric_coverage"]["sends_per_reach"]["observed"] == 0


def test_incomplete_metric_coverage_cannot_drive_primary_metric():
    rows = cohort()
    for i, row in enumerate(rows[:5]):
        row.update(reach=100, sends=i)
    summary = analyze(rows)
    assert summary["cohorts"][0]["primary_metric"] == "likes"
    assert all(c["metric"] != "sends_per_reach" for c in summary["cohorts"][0]["comparisons"])


def test_primary_metric_is_not_changed_just_because_another_has_a_contrast():
    rows = cohort()
    for row in rows:
        row.update(reach=100, sends=10)
    summary = analyze(rows)
    group = summary["cohorts"][0]
    assert group["primary_metric"] == "sends_per_reach"
    result = group["comparisons"][0]
    assert result["higher"] == result["lower"] == []
    assert "tails overlap" in report_markdown(summary, Path("source.json"), TODAY)


def test_quartile_boundary_ties_are_included_without_arbitrary_id_selection():
    rows = [post(i, v) for i, v in enumerate([0, 0, 0, 10, 20, 100, 100, 100])]
    result = comparison(analyze(rows))
    assert set(result["lower"]) == {"0", "1", "2"}
    assert set(result["higher"]) == {"5", "6", "7"}


def test_foreign_owners_removed_collaborators_retained_and_missing_owner_disclosed():
    summary = analyze([post("foreign", 10, ownerUsername="other"),
                       post("collab", 20, ownerUsername="other", coauthorProducers=[{"username": "a.storyof.two"}]),
                       post("unknown", 30, ownerUsername=None)])
    assert summary["post_count"] == 2
    assert summary["ownership_unverified_count"] == 1
    assert summary["exclusions"]["foreign_owner"] == 1


def test_duplicate_conflicts_cannot_select_a_winner_by_file_order():
    rows = cohort() + [post("duplicate", 999999), post("duplicate", 1)]
    summary = analyze(rows)
    assert summary["post_count"] == 8
    assert summary["exclusions"]["conflicting_duplicate"] == 2
    assert comparison(summary)["higher"] == ["6", "7"]


def test_identical_duplicate_is_counted_once():
    rows = cohort()
    assert analyze(rows + [dict(rows[0])])["post_count"] == 8


def test_missing_dates_do_not_create_comparisons():
    assert analyze_posts(cohort(), today=TODAY)["cohorts"] == []
    rows = cohort()
    for row in rows:
        row["timestamp"] = "unknown"
    assert analyze(rows)["cohorts"] == []
    with pytest.raises(ValueError, match="future"):
        analyze_posts(cohort(), date(2027, 1, 1), TODAY)


def test_caption_features_are_cited_and_never_claimed_as_video_hooks():
    rows = cohort()
    for i in [6, 7]:
        rows[i]["caption"] = "A question? #together"
    for i in [0, 1]:
        rows[i]["caption"] = "A quiet moment."
    summary = analyze(rows)
    patterns = summary["cohorts"][0]["caption_patterns"]
    tag = next(p for p in patterns if p["feature"] == "caption hashtag #together")
    assert tag["higher_with_feature"] == ["6", "7"]
    assert tag["lower_with_feature"] == []
    assert summary["content_evidence"]["video_hooks"] == "unavailable"
    text = report_markdown(summary, Path("source.json"), TODAY)
    assert "Caption excerpt (not video hook)" in text
    assert "no significance claim" in text


def test_missing_captions_are_not_counted_as_absent_features():
    rows = cohort()
    for i in [0, 1]:
        rows[i]["caption"] = None
    assert analyze(rows)["cohorts"][0]["caption_patterns"] == []


def test_run_prefers_raw_on_date_ties_and_preserves_source_bytes(tmp_path):
    raw = snapshot(tmp_path, cohort())
    snapshot(tmp_path, [], "2026-09-01-posts.json", "posts")
    before = raw.read_bytes()
    output = run(tmp_path, today=TODAY, all_formats=True)
    report = json.loads(output.with_suffix(".json").read_text())
    assert report["post_count"] == 8
    assert report["source"]["sha256"] == hashlib.sha256(before).hexdigest()
    assert report["source"]["path"] == str(raw)
    assert report["collected_on"] == "2026-09-01"
    assert raw.read_bytes() == before
    assert output.exists()


def test_latest_source_uses_collection_date_not_mtime(tmp_path):
    older = snapshot(tmp_path, [post("older", 99999)], "2026-08-01-raw.json")
    snapshot(tmp_path, cohort())
    older.touch()
    report = json.loads(run(tmp_path, today=TODAY, all_formats=True).with_suffix(".json").read_text())
    assert report["post_count"] == 8


@pytest.mark.parametrize("bad", ["not json", "{}"])
def test_corrupt_latest_source_does_not_fall_back(tmp_path, bad):
    snapshot(tmp_path, cohort(), "2026-08-01-raw.json")
    latest = snapshot(tmp_path, cohort())
    latest.write_text(bad)
    with pytest.raises(ValueError):
        run(tmp_path, today=TODAY, all_formats=True)
    assert not (tmp_path / "output").exists()


def test_empty_latest_source_reports_no_evidence_not_old_results(tmp_path):
    snapshot(tmp_path, cohort(), "2026-08-01-raw.json")
    snapshot(tmp_path, [])
    report = json.loads(run(tmp_path, today=TODAY, all_formats=True).with_suffix(".json").read_text())
    assert report["post_count"] == 0
    assert report["cohorts"] == []


def test_explicit_custom_source_requires_known_collection_date_for_comparisons(tmp_path):
    source = tmp_path / "custom.json"
    source.write_text(json.dumps(cohort()))
    output = run(tmp_path, source, TODAY, all_formats=True)
    assert json.loads(output.with_suffix(".json").read_text())["cohorts"] == []
    output = run(tmp_path, source, TODAY, COLLECTED, all_formats=True)
    assert json.loads(output.with_suffix(".json").read_text())["cohorts"]


def test_stale_source_is_not_made_fresh_by_generating_a_report(tmp_path):
    snapshot(tmp_path, cohort(), "2026-06-06-raw.json")
    output = run(tmp_path, today=TODAY, all_formats=True)
    report = json.loads(output.with_suffix(".json").read_text())
    assert report["freshness"] == "stale"
    assert report["source_age_days"] == 91
    assert "**stale**" in output.read_text()


def test_embedded_heterogeneous_dates_do_not_inherit_one_fresh_file_date():
    rows = [post("old_observation", 10, timestamp="2026-06-24T10:00:00Z", observed_at="2026-07-01T10:00:00Z"),
            post("recent_observation", 20, timestamp="2026-08-24T10:00:00Z", observed_at="2026-08-31T10:00:00Z")]
    summary = analyze(rows)
    assert summary["observation_range"] == ["2026-07-01", "2026-08-31"]
    assert summary["freshness"] == "mixed"
    assert summary["collected_on"] is None
    assert summary["source_age_days"] is None
    assert [p["age_days"] for p in summary["posts"]] == [7, 7]


def test_explicit_stale_observation_cannot_be_refreshed_by_export_filename():
    summary = analyze([post("old", 10, timestamp="2026-06-24T10:00:00Z", observed_at="2026-07-01T10:00:00Z")])
    assert summary["freshness"] == "stale"
    assert summary["collected_on"] == "2026-07-01"
    assert summary["source_age_days"] == 66
