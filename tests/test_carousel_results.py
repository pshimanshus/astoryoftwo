"""Results plumbing tests; synthetic records are not observed channel performance."""
import copy
import hashlib
import json
from pathlib import Path

import pytest
from PIL import Image

from pipeline.stages import carousel_results as results
from pipeline.stages.carousel_pixel_qa import manifest_fingerprint


def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value))


def package(root, monkeypatch, *, approve=True):
    folder = root / "output/carousels/2026-01-01/test"
    folder.mkdir(parents=True)
    image = folder / "instagram-post/slide-01.png"
    image.parent.mkdir()
    Image.new("RGB", (1080, 1440), "ivory").save(image)
    manifest = {"schema_version": "carousel-final-images/v3", "selected_formats": ["instagram_post"],
                "slides": [{"slide": 1, "native_outputs": {"instagram_post": {
                    "path": str(image.relative_to(folder)), "sha256": "sha256:" + hashlib.sha256(image.read_bytes()).hexdigest(),
                    "width": 1080, "height": 1440}}}]}
    write(folder / "final-images.json", manifest)
    write(folder / "generation-state.json", {"schema_version": "carousel-generation-state/v3", "status": "publish_ready"})
    write(folder / "final-audit.json", {"status": "PASS", "issues": [], "manifest_sha256": manifest_fingerprint(manifest)})
    write(folder / "creative-context.json", {"story_plan": {"theme": "Shared room, different habits"}})
    write(folder / "visual-qa.json", {"sequence_review": {"closure": "Reviewer described an ending"}})
    write(folder / "slides.json", [{"slide": 1, "copy": "A test line", "beat_delta": "One bounded unit-test fixture"}])
    # Audit internals have their own integration suite. The fixture never writes
    # a generated-pixel certification or calls a generation/publish tool.
    if approve:
        monkeypatch.setattr(results, "build_final_audit", lambda *_args, **_kwargs: {"status": "PASS", "issues": []})
    return folder


def publication(code="TEST"):
    return {"shortcode": code, "url": f"https://www.instagram.com/p/{code}/", "published_at": "2026-01-01T10:00:00Z",
            "confirmed": True, "slide_order": [1], "correspondence": {"status": "unverified"},
            "creative_hypothesis": "The shared room creates recognition", "next_hypothesis": "Test a closer cover framing"}


def snapshot(at="2026-01-08T10:00:00Z", **metrics):
    return {"observed_at": at, "source": {"kind": "native_insights", "reference": "Synthetic test fixture"},
            "metrics": {"Views": 100, "Viewers": 80, "Shares": 4, "Saves": 0, "Follows": 1, **metrics}}


def link(root, monkeypatch):
    folder = package(root, monkeypatch)
    result = results.record_publication(root, folder, publication())
    return folder, result


def test_publication_is_idempotent_bound_to_final_manifest_and_does_not_copy_art(tmp_path, monkeypatch):
    folder, record = link(tmp_path, monkeypatch)
    assert record == results.record_publication(tmp_path, folder, publication())
    assert record["final_manifest_sha256"] == manifest_fingerprint(json.loads((folder / "final-images.json").read_text()))
    assert record["correspondence"]["status"] == "unverified"
    assert record["story_plan"]["theme"] == "Shared room, different habits"
    assert not (tmp_path / "corpus/media").exists()
    changed = publication()
    changed["published_at"] = "2026-01-01T11:00:00Z"
    with pytest.raises(ValueError, match="immutable"):
        results.record_publication(tmp_path, folder, changed)


def test_forged_stored_pass_does_not_bypass_current_audit(tmp_path, monkeypatch):
    folder = package(tmp_path, monkeypatch, approve=False)
    with pytest.raises(ValueError, match="final audit"):
        results.record_publication(tmp_path, folder, publication())
    assert not (tmp_path / "corpus/publications/TEST.json").exists()


@pytest.mark.parametrize("patch", [{"confirmed": False}, {"shortcode": "../other"}, {"url": "https://www.instagram.com/p/OTHER/"},
                                    {"published_at": "2026-01-01"}, {"published_at": "2099-01-01T00:00:00Z"}, {"slide_order": [2]},
                                    {"slide_order": [True]}, {"correspondence": {"status": "reviewed"}}])
def test_bad_publication_metadata_fails_closed(tmp_path, monkeypatch, patch):
    folder = package(tmp_path, monkeypatch)
    record = publication()
    record.update(patch)
    with pytest.raises(ValueError):
        results.record_publication(tmp_path, folder, record)


def test_stale_manifest_hash_and_nonfinal_state_rejected(tmp_path, monkeypatch):
    folder = package(tmp_path, monkeypatch)
    write(folder / "generation-state.json", {"schema_version": "carousel-generation-state/v3", "status": "final_qa_required"})
    with pytest.raises(ValueError, match="publish_ready"):
        results.record_publication(tmp_path, folder, publication())
    write(folder / "generation-state.json", {"schema_version": "carousel-generation-state/v3", "status": "publish_ready"})
    data = json.loads((folder / "final-audit.json").read_text())
    data["manifest_sha256"] = "stale"
    write(folder / "final-audit.json", data)
    with pytest.raises(ValueError, match="manifest"):
        results.record_publication(tmp_path, folder, publication())


def test_reviewed_correspondence_can_have_different_bytes(tmp_path, monkeypatch):
    folder = package(tmp_path, monkeypatch)
    image = tmp_path / "corpus/media/TEST/slide-01.jpg"
    image.parent.mkdir(parents=True)
    Image.new("RGB", (1080, 1440), "white").save(image)
    record = publication()
    record["correspondence"] = {"status": "reviewed", "reviewer": "Test reviewer", "reviewed_at": "2026-01-02T10:00:00Z",
                                "slides": [{"published_position": 1, "package_slide": 1, "published_image_path": str(image.relative_to(tmp_path)),
                                            "evidence": "Synthetic correspondence assertion, not a real inspection"}]}
    saved = results.record_publication(tmp_path, folder, record)
    assert saved["correspondence"]["slides"][0]["byte_identity"] is False
    assert saved["correspondence"]["status"] == "reviewed"
    record["correspondence"]["slides"][0]["published_image_path"] = str((folder / "instagram-post/slide-01.png").relative_to(tmp_path))
    with pytest.raises(ValueError, match="published archive"):
        results.record_publication(tmp_path, folder, record)


def test_snapshots_preserve_native_labels_and_zero_without_inventing_sends(tmp_path, monkeypatch):
    link(tmp_path, monkeypatch)
    saved = results.record_snapshot(tmp_path, "TEST", snapshot())
    assert saved["metrics"]["Views"]["value"] == 100
    assert saved["metrics"]["Viewers"]["value"] == 80
    assert saved["metrics"]["Saves"] == {"value": 0, "availability": "observed", "native_label": "Saves"}
    assert saved["metrics"]["sends"]["value"] is None
    assert saved["metrics"]["reach"]["availability"] == "unavailable"
    assert saved["post_age_days"] == 7
    assert saved == results.record_snapshot(tmp_path, "TEST", snapshot())
    with pytest.raises(ValueError, match="immutable"):
        results.record_snapshot(tmp_path, "TEST", snapshot(Views=99))
    assert len(list((tmp_path / "corpus/insights/TEST").glob("*.json"))) == 1


@pytest.mark.parametrize("bad", [True, "100", -1, float("nan"), float("inf"), [], {}])
def test_snapshot_rejects_non_numeric_native_counts(tmp_path, monkeypatch, bad):
    link(tmp_path, monkeypatch)
    with pytest.raises(ValueError, match="numeric"):
        results.record_snapshot(tmp_path, "TEST", snapshot(Views=bad))


@pytest.mark.parametrize("at", ["2026-01-01T09:59:59Z", "2099-01-08T10:00:00Z", "2026-01-08", "2026-01-08T10:00:00"])
def test_snapshot_requires_valid_aware_chronology(tmp_path, monkeypatch, at):
    link(tmp_path, monkeypatch)
    with pytest.raises(ValueError):
        results.record_snapshot(tmp_path, "TEST", snapshot(at))


def test_snapshot_requires_publication_and_does_not_accept_invented_retention(tmp_path, monkeypatch):
    with pytest.raises(ValueError, match="publication"):
        results.record_snapshot(tmp_path, "TEST", snapshot())
    link(tmp_path, monkeypatch)
    with pytest.raises(ValueError, match="Unsupported"):
        results.record_snapshot(tmp_path, "TEST", snapshot(retention=0.9))


def test_review_without_snapshot_is_honest_and_preserves_next_test(tmp_path, monkeypatch):
    link(tmp_path, monkeypatch)
    review = results.review_results(tmp_path, "TEST")
    assert review["outcome_status"] == "unavailable"
    assert review["mechanism_assessment"]["status"] == "ambiguous"
    assert review["next_hypothesis"] == "Test a closer cover framing"
    assert review["comparisons"] == []
    assert (tmp_path / "output/reports/carousel-results/TEST.md").is_file()


def test_review_does_not_equate_shares_to_dm_or_infer_retention(tmp_path, monkeypatch):
    link(tmp_path, monkeypatch)
    results.record_snapshot(tmp_path, "TEST", snapshot(reach=50, sends=2))
    review = results.review_results(tmp_path, "TEST")
    assert review["latest_observation"]["rates"]["shares_per_reach"]["value"] == .08
    assert review["latest_observation"]["rates"]["shares_per_reach"]["denominator"] == {"label": "reach", "value": 50.0}
    assert review["latest_observation"]["rates"]["shares_per_reach"]["source"]
    assert review["unmeasured"] == ["private_dm_count", "per_slide_abandonment", "dwell", "completion"]
    assert "not establish private DM" in " ".join(review["limits"])
    assert review["mechanism_assessment"]["status"] == "ambiguous"


def test_adapter_deduplicates_raw_and_normalized_exports_and_keeps_times(tmp_path, monkeypatch):
    from pipeline.stages.a2_parser import normalize_post
    link(tmp_path, monkeypatch)
    results.record_snapshot(tmp_path, "TEST", snapshot())
    raw = [{"id": "raw-id", "shortCode": "OTHER", "type": "Sidecar", "timestamp": "2026-01-01T10:00:00Z", "sharesCount": 2}]
    write(tmp_path / "corpus/raw/2026-01-08-raw.json", raw)
    write(tmp_path / "corpus/posts/2026-01-08-posts.json", [normalize_post(row) for row in raw])
    rows = results.load_metric_observations(tmp_path)
    assert len(rows) == 2
    by_code = {r["shortcode"]: r for r in rows}
    assert by_code["TEST"]["observed_at"] == "2026-01-08T10:00:00Z"
    assert by_code["OTHER"]["observed_at"] is None
    assert by_code["OTHER"]["collected_on"] == "2026-01-08"
    assert by_code["OTHER"]["observation_precision"] == "day"


def test_cohorts_use_actual_per_post_age_and_one_observation_per_post(tmp_path, monkeypatch):
    link(tmp_path, monkeypatch)
    results.record_snapshot(tmp_path, "TEST", snapshot(reach=100))
    for n in range(5):
        code = f"PEER{n}"
        row = {"id": code, "shortCode": code, "type": "Sidecar", "timestamp": "2026-01-01T10:00:00Z",
               "observed_at": "2026-01-08T10:00:00Z", "sharesCount": n, "reach": 100}
        # Different historical file date must not override embedded observation.
        write(tmp_path / f"corpus/raw/2026-02-{n+1:02}-raw.json", [row])
    # Repeated peer snapshot stays one post in a cohort; a Reel is excluded.
    write(tmp_path / "corpus/raw/2026-02-10-raw.json", [row, {**row, "id": "REEL", "shortCode": "REEL", "type": "Video"}])
    review = results.review_results(tmp_path, "TEST")
    assert len(review["comparisons"]) == 1
    assert review["comparisons"][0]["n"] == 6
    assert review["comparisons"][0]["age_band"] == "7-13"
    assert len(review["comparisons"][0]["post_ids"]) == len(set(review["comparisons"][0]["post_ids"]))


def test_early_observation_is_descriptive_even_with_many_peers(tmp_path, monkeypatch):
    link(tmp_path, monkeypatch)
    results.record_snapshot(tmp_path, "TEST", snapshot("2026-01-02T10:00:00Z"))
    assert results.review_results(tmp_path, "TEST")["comparisons"] == []


def test_matching_export_does_not_hide_linked_native_snapshot(tmp_path, monkeypatch):
    link(tmp_path, monkeypatch)
    results.record_snapshot(tmp_path, "TEST", snapshot())
    write(tmp_path / "corpus/raw/2026-01-08-raw.json", [{
        "id": "platform-id", "shortCode": "TEST", "type": "Sidecar", "timestamp": "2026-01-01T10:00:00Z",
        "observed_at": "2026-01-08T10:00:00Z", "Views": 100, "Viewers": 80, "Shares": 4, "Saves": 0, "Follows": 1,
    }])
    assert len(results.load_metric_observations(tmp_path)) == 1
    assert results.review_results(tmp_path, "TEST")["outcome_status"] == "observed"


def test_partial_exports_at_same_instant_merge_only_nonconflicting_observations(tmp_path, monkeypatch):
    link(tmp_path, monkeypatch)
    results.record_snapshot(tmp_path, "TEST", snapshot())
    write(tmp_path / "corpus/raw/2026-01-08-raw.json", [{
        "shortCode": "TEST", "type": "Sidecar", "timestamp": "2026-01-01T10:00:00Z",
        "observed_at": "2026-01-08T10:00:00Z", "Shares": 4, "reach": 50,
    }])
    rows = results.load_metric_observations(tmp_path)
    assert len(rows) == 1
    assert rows[0]["engagement"]["shares"] == 4
    assert rows[0]["engagement"]["reach"] == 50
    assert rows[0]["metric_provenance"]["reach"]["path"].startswith("corpus/raw/")
    assert rows[0]["metric_provenance"]["views"]["path"].startswith("corpus/insights/")


def test_conflicting_same_instant_metrics_are_not_silently_chosen(tmp_path, monkeypatch):
    link(tmp_path, monkeypatch)
    results.record_snapshot(tmp_path, "TEST", snapshot())
    write(tmp_path / "corpus/raw/2026-01-08-raw.json", [{
        "shortCode": "TEST", "type": "Sidecar", "timestamp": "2026-01-01T10:00:00Z",
        "observed_at": "2026-01-08T10:00:00Z", "Shares": 999,
    }])
    assert results.load_metric_observations(tmp_path) == []
    assert results.review_results(tmp_path, "TEST")["outcome_status"] == "unavailable"


def test_unstamped_legacy_native_row_retains_counts_and_reported_age_without_inventing_dates(tmp_path):
    write(tmp_path / "corpus/rows.json", [{"shortcode": "LEGACY", "post_type": "carousel", "age_days": 10,
                                          "Views": 100, "Profile visits": 2}])
    row = results.load_metric_observations(tmp_path)[0]
    assert row["metrics"]["Profile visits"] == 2
    assert row["collected_on"] is None and row["observed_at"] is None
    assert row["reported_age_days"] == 10
    assert row["age_days"] is None and row["age_band"] is None
    assert row["observation_precision"] == "unknown"


def test_reviewed_correspondence_becomes_stale_when_archive_changes(tmp_path, monkeypatch):
    folder = package(tmp_path, monkeypatch)
    image = tmp_path / "corpus/media/TEST/slide-01.jpg"
    image.parent.mkdir(parents=True)
    Image.new("RGB", (1080, 1440), "white").save(image)
    record = publication()
    record["correspondence"] = {"status": "reviewed", "reviewer": "Test reviewer", "reviewed_at": "2026-01-02T10:00:00Z",
                                "slides": [{"published_position": 1, "package_slide": 1, "published_image_path": str(image.relative_to(tmp_path)), "evidence": "Synthetic test only"}]}
    results.record_publication(tmp_path, folder, record)
    Image.new("RGB", (1080, 1440), "blue").save(image)
    report = results.review_results(tmp_path, "TEST")
    assert report["final_work_evidence"]["published_correspondence"]["status"] == "stale"
    assert "not certified" in " ".join(report["limits"])


def test_make_analyze_path_accepts_native_insights_and_refreshes_linked_review(tmp_path, monkeypatch):
    from datetime import date
    from pipeline.stages.a3_analyzer import run
    link(tmp_path, monkeypatch)
    results.record_snapshot(tmp_path, "TEST", snapshot())
    output = run(tmp_path, today=date(2026, 1, 9))
    report = json.loads(output.with_suffix(".json").read_text())
    assert report["posts"][0]["engagement"]["views"] == 100
    assert report["posts"][0]["age_days"] == 7
    assert report["carousel_results"]["reviews"][0]["outcome_status"] == "observed"
    assert "Dated publication results" in output.read_text()


def test_make_analyze_undated_export_reports_counts_without_age_comparisons(tmp_path):
    from datetime import date
    from pipeline.stages.a3_analyzer import run
    write(tmp_path / "corpus/rows.json", [{"shortcode": "LEGACY", "post_type": "carousel", "age_days": 10,
                                          "Views": 100, "Profile visits": 2}])
    output = run(tmp_path, today=date(2026, 1, 9))
    report = json.loads(output.with_suffix(".json").read_text())
    assert report["posts"][0]["engagement"]["views"] == 100
    assert report["posts"][0]["age_days"] is None
    assert report["cohorts"] == []
    assert report["freshness"] == "unknown"


def test_analyzer_does_not_accept_stale_saved_results_without_revalidating_sources(tmp_path, monkeypatch):
    from pipeline.stages.carousel_analysis import carousel_results_evidence
    link(tmp_path, monkeypatch)
    results.record_snapshot(tmp_path, "TEST", snapshot())
    results.review_results(tmp_path, "TEST")
    path = tmp_path / "corpus/publications/TEST.json"
    record = json.loads(path.read_text())
    record["story_plan"]["theme"] = "changed outside immutable writer"
    write(path, record)
    evidence = carousel_results_evidence(tmp_path)
    assert evidence["reviews"] == []
    assert evidence["issues"]


@pytest.mark.parametrize("timestamp_key", ["takenAt", "createdAt"])
def test_metric_adapter_uses_normalized_publication_timestamp_aliases(tmp_path, timestamp_key):
    write(tmp_path / "corpus/raw/2026-01-08-raw.json", [{"shortCode": "TEST", "type": "Sidecar",
          timestamp_key: "2026-01-01T10:00:00Z", "observed_at": "2026-01-08T10:00:00Z", "Shares": 5, "reach": 100}])
    row = results.load_metric_observations(tmp_path)[0]
    assert row["age_days"] == 7
    assert row["age_band"] == "7-13"


def test_native_results_preserve_slide_count_for_complete_archived_review(tmp_path, monkeypatch):
    from datetime import date
    from pipeline.stages.a3_analyzer import run
    from tests.test_carousel_analysis import evidence
    folder = package(tmp_path, monkeypatch)
    results.record_publication(tmp_path, folder, publication("ABC"))
    results.record_snapshot(tmp_path, "ABC", snapshot())
    evidence(tmp_path, expected=1, reviewed=(1,))
    output = run(tmp_path, today=date(2026, 1, 9))
    report = json.loads(output.with_suffix(".json").read_text())
    assert report["posts"][0]["slide_count"] == 1
    assert report["carousel_visual_evidence"]["counts"]["complete_reviews"] == 1


def test_snapshot_payload_tampering_is_rejected_on_review(tmp_path, monkeypatch):
    link(tmp_path, monkeypatch)
    results.record_snapshot(tmp_path, "TEST", snapshot())
    path = next((tmp_path / "corpus/insights/TEST").glob("*.json"))
    raw = json.loads(path.read_text())
    raw["metrics"]["Views"]["value"] = 999
    write(path, raw)
    with pytest.raises(ValueError, match="snapshot"):
        results.review_results(tmp_path, "TEST")
