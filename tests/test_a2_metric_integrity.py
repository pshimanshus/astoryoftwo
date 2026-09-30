import json
import subprocess
import sys
from pathlib import Path

import pytest

from pipeline.stages.a2_parser import normalize_post, parse_raw_posts


ROOT = Path(__file__).resolve().parents[1]


def test_missing_metrics_are_unavailable_instead_of_zero():
    post = normalize_post({"id": "missing"})

    assert post["schema_version"] == "2.0"
    assert post["engagement"] == {
        "likes": None,
        "comments": None,
        "views": None,
        "viewers": None,
        "follows": None,
        "profile_visits": None,
        "plays": None,
        "reach": None,
        "saves": None,
        "shares": None,
        "sends": None,
        "retention_rate": None,
    }
    assert set(post["metric_status"].values()) == {"unavailable"}


@pytest.mark.parametrize("value", [None, -1, True, False, float("nan"), float("inf"), -float("inf"), "0", "invalid", [], {}])
def test_invalid_metrics_do_not_claim_observations(value):
    post = normalize_post({"likesCount": value, "retention_rate": value})

    assert post["engagement"]["likes"] is None
    assert post["metric_status"]["likes"] == "unavailable"
    assert post["engagement"]["retention_rate"] is None
    assert post["metric_status"]["retention_rate"] == "unavailable"


def test_zero_primary_metric_wins_over_nonzero_alias():
    post = normalize_post({
        "likesCount": 0, "likes": 12,
        "commentsCount": 0, "comments": 8,
        "videoViewCount": 0, "viewCount": 200,
        "Viewers": 0, "Follows": 0, "Profile visits": 0,
        "videoPlayCount": 0, "playCount": 300,
        "reach": 0, "reachCount": 250,
        "saves": 0, "saved": 5,
        "shares": 0, "sharesCount": 7,
        "sends": 0, "sendsCount": 6,
        "retention_rate": 0,
    })

    assert set(post["engagement"].values()) == {0}
    assert set(post["metric_status"].values()) == {"observed"}


def test_aliases_recover_valid_observations_without_merging_shares_and_sends():
    post = normalize_post({
        "likesCount": None, "likes": 120,
        "commentsCount": -1, "comments": 12,
        "videoViewCount": float("nan"), "viewCount": 1000,
        "videoPlayCount": True, "playCount": 1500,
        "reach": "unknown", "reachCount": 900,
        "saves": None, "saved": 40, "savesCount": 90,
        "shares": None, "sharesCount": 30,
        "sends": None, "sendsCount": 20,
        "retention_rate": 0.625,
    })

    assert post["engagement"] == {
        "likes": 120, "comments": 12, "views": 1000, "plays": 1500,
        "viewers": None, "follows": None,
        "profile_visits": None,
        "reach": 900, "saves": 40, "shares": 30, "sends": 20,
        "retention_rate": 0.625,
    }
    assert post["metric_status"]["shares"] == "observed"
    assert post["metric_status"]["viewers"] == "unavailable"
    assert normalize_post({"sharesCount": 9})["engagement"]["sends"] is None
    assert normalize_post({"sendsCount": 7})["engagement"]["shares"] is None
    assert normalize_post({"savesCount": 0})["engagement"]["saves"] == 0


def test_retention_requires_an_explicit_fraction():
    assert normalize_post({"retention_rate": 1})["engagement"]["retention_rate"] == 1
    assert normalize_post({"retention_rate": 62.5})["engagement"]["retention_rate"] is None
    assert normalize_post({"watchTime": 50, "duration": 100})["engagement"]["retention_rate"] is None


@pytest.mark.parametrize("raw_type, product_type, expected", [
    ("Video", None, "video"),
    ("Sidecar", None, "sidecar"),
    ("Image", None, "image"),
    (None, "clips", "video"),
    ("clips", None, "video"),
    ("reel", None, "video"),
    ("unknown", "clips", "video"),
    ("carousel", None, "sidecar"),
    ("photo", None, "image"),
])
def test_format_is_normalized_without_discarding_raw_type(raw_type, product_type, expected):
    post = normalize_post({"type": raw_type, "productType": product_type})
    assert post["post_type"] == expected
    assert post["raw_type"] == raw_type


def test_source_identity_and_exact_caption_are_preserved():
    caption = "  Us.\n#Love @A.StoryOf.Two 🫶  "
    item = {
        "id": "post-id", "shortCode": "abc123", "url": "https://www.instagram.com/p/abc123/",
        "timestamp": "2026-06-06T12:30:00Z", "caption": caption,
        "ownerUsername": "a.storyof.two", "coauthorProducers": [{"username": "collaborator"}],
        "inputUrl": "https://www.instagram.com/a.storyof.two/",
    }
    post = normalize_post(item)

    for key in ("id", "url", "timestamp", "caption", "ownerUsername", "coauthorProducers", "inputUrl"):
        assert post[key] == item[key]
    assert post["shortcode"] == "abc123"
    assert post["hashtags"] == ["love"]
    assert post["mentions"] == ["a.storyof.two"]
    assert normalize_post({"caption": "", "text": "fallback"})["caption"] == ""
    assert normalize_post({"text": "fallback"})["caption"] == "fallback"


def test_identifier_timestamp_fallbacks_remain_compatible():
    post = normalize_post({"shortcode": "fallback", "takenAt": "2026-06-01", "createdAt": "2026-05-01"})
    assert post["id"] == "fallback"
    assert post["shortcode"] == "fallback"
    assert post["timestamp"] == "2026-06-01"
    assert normalize_post({"url": "url-only", "createdAt": "2026-05-01"})["id"] == "url-only"
    assert normalize_post({"createdAt": "2026-05-01"})["timestamp"] == "2026-05-01"


def test_parse_keeps_list_contract_and_serializes_missing_metrics_as_null(tmp_path):
    raw = tmp_path / "corpus" / "raw" / "2026-06-06-raw.json"
    raw.parent.mkdir(parents=True)
    raw.write_text(json.dumps([{"id": "missing", "likesCount": None}, {"id": "zero", "likesCount": 0}, "skip"]), encoding="utf-8")

    output = parse_raw_posts(raw)
    records = json.loads(output.read_text(encoding="utf-8"))

    assert output == tmp_path / "corpus" / "posts" / "2026-06-06-posts.json"
    assert len(records) == 2
    assert records[0]["engagement"]["likes"] is None
    assert records[0]["metric_status"]["likes"] == "unavailable"
    assert records[1]["engagement"]["likes"] == 0
    assert records[1]["metric_status"]["likes"] == "observed"


def test_parse_cli_uses_workspace_root_and_versioned_metrics(tmp_path):
    raw = tmp_path / "corpus" / "raw" / "2026-06-06-raw.json"
    raw.parent.mkdir(parents=True)
    raw.write_text('[{"id": "example", "sharesCount": 3}]', encoding="utf-8")

    result = subprocess.run(
        [sys.executable, "-m", "pipeline.stages.a2_parser", "--workspace-root", str(tmp_path)],
        cwd=ROOT, capture_output=True, text=True, check=False, timeout=30,
    )

    assert result.returncode == 0, result.stderr
    output = Path(result.stdout.strip())
    assert output == tmp_path / "corpus" / "posts" / "2026-06-06-posts.json"
    post = json.loads(output.read_text(encoding="utf-8"))[0]
    assert post["schema_version"] == "2.0"
    assert post["engagement"]["shares"] == 3
    assert post["engagement"]["sends"] is None


def test_native_insights_labels_and_provenance_remain_distinct():
    row = normalize_post({"Views": 50, "Viewers": 40, "Follows": 0, "Shares": 3, "Saves": 2, "observed_at": "2026-01-08T10:00:00Z"})
    assert row["engagement"]["views"] == 50
    assert row["engagement"]["viewers"] == 40
    assert row["engagement"]["follows"] == 0
    assert row["engagement"]["sends"] is None
    assert row["engagement"]["reach"] is None
    assert row["metric_sources"]["views"] == "Views"
    assert row["observed_at"] == "2026-01-08T10:00:00Z"
