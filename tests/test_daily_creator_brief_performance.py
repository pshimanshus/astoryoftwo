"""Evidence and failure-boundary tests for the creator-facing daily brief."""

import json
import os
import re
from datetime import date, timedelta
from pathlib import Path

import pytest


TODAY = date(2026, 9, 5)
COLLECTED = date(2026, 9, 1)


def post(
    identity: str,
    likes: object,
    *,
    collected: date = COLLECTED,
    age: int = 20,
    kind: str = "Sidecar",
    **overrides: object,
) -> dict:
    value = {
        "id": identity,
        "shortCode": identity,
        "url": f"https://www.instagram.com/p/{identity}/",
        "ownerUsername": "a.storyof.two",
        "timestamp": f"{collected - timedelta(days=age)}T12:00:00.000Z",
        "type": kind,
        "likesCount": likes,
        "commentsCount": 2,
    }
    value.update(overrides)
    return value


def cohort(*, collected: date = COLLECTED, prefix: str = "post") -> list[dict]:
    return [
        post(f"{prefix}-low", 10, collected=collected, age=10),
        post(f"{prefix}-middle", 20, collected=collected, age=20),
        post(f"{prefix}-top", 90, collected=collected, age=30),
    ]


def snapshot(root: Path, collected: date, posts: object) -> Path:
    folder = root / "corpus" / "raw"
    folder.mkdir(parents=True, exist_ok=True)
    path = folder / f"{collected}-raw.json"
    path.write_text(json.dumps(posts), encoding="utf-8")
    return path


def brief(root: Path, today: date = TODAY) -> str:
    from scripts.daily_creator_brief import performance_brief

    lines = performance_brief(root, today=today, all_formats=True)
    assert isinstance(lines, list)
    assert all(isinstance(line, str) for line in lines)
    return "\n".join(lines)


def test_missing_snapshot_is_explicitly_unavailable(tmp_path: Path):
    text = brief(tmp_path).lower()

    assert "unavailable" in text
    assert "snapshot" in text
    assert "instagram.com/p/" not in text
    assert "experiment" in text
    assert any(word in text for word in ("collect", "refresh", "capture"))


def test_adequate_cohort_uses_same_format_median_and_links_the_post(tmp_path: Path):
    snapshot(tmp_path, COLLECTED, cohort())

    text = brief(tmp_path)

    assert "https://www.instagram.com/p/post-top/" in text
    assert re.search(r"\b90\b", text)
    assert re.search(r"median[^\n]*\b20\b|\b20\b[^\n]*median", text, re.I)
    assert "4.5" in text
    assert "2026-09-01" in text
    assert "2026-09-05" in text
    assert "collection" in text.lower() or "collected" in text.lower()
    assert "experiment" in text.lower()
    assert any(term in text.lower() for term in ("hypothesis", "test", "unproven"))
    assert len(re.findall(r"^[123]\. ", text, re.M)) == 3


def test_source_selection_uses_filename_date_not_file_mtime(tmp_path: Path):
    old = snapshot(tmp_path, date(2026, 8, 20), cohort(collected=date(2026, 8, 20), prefix="old"))
    latest = snapshot(tmp_path, COLLECTED, cohort(prefix="latest"))
    os.utime(old, (2_000_000_000, 2_000_000_000))
    os.utime(latest, (1_000_000_000, 1_000_000_000))
    (latest.parent / "2099-01-01-raw-copy.json").write_text(json.dumps(cohort(prefix="copy")))

    text = brief(tmp_path)

    assert "https://www.instagram.com/p/latest-top/" in text
    assert "https://www.instagram.com/p/old-top/" not in text
    assert "https://www.instagram.com/p/copy-top/" not in text


@pytest.mark.parametrize("payload", [[], {}, "corrupt"])
def test_unusable_latest_snapshot_does_not_silently_use_older_data(tmp_path: Path, payload: object):
    snapshot(tmp_path, date(2026, 8, 20), cohort(collected=date(2026, 8, 20), prefix="older"))
    latest = snapshot(tmp_path, COLLECTED, payload)
    if payload == "corrupt":
        latest.write_text("{ invalid json", encoding="utf-8")

    text = brief(tmp_path).lower()

    assert "unavailable" in text
    assert "2026-09-01" in text
    assert "https://www.instagram.com/p/older-top/" not in text


def test_future_snapshot_is_rejected_instead_of_falling_back(tmp_path: Path):
    snapshot(tmp_path, COLLECTED, cohort(prefix="older"))
    snapshot(tmp_path, date(2026, 9, 6), cohort(collected=date(2026, 9, 6), prefix="future"))

    text = brief(tmp_path).lower()

    assert "future" in text
    assert "unavailable" in text
    assert "https://www.instagram.com/p/older-top/" not in text
    assert "https://www.instagram.com/p/future-top/" not in text


@pytest.mark.parametrize("age, stale", [(14, False), (15, True)])
def test_collection_freshness_boundary(tmp_path: Path, age: int, stale: bool):
    collected = TODAY - timedelta(days=age)
    snapshot(tmp_path, collected, cohort(collected=collected))

    text = brief(tmp_path).lower()

    assert str(collected) in text
    assert "https://www.instagram.com/p/post-top/" in text
    if stale:
        assert "stale" in text
        assert any(term in text for term in ("historical", "refresh", "collect"))
    else:
        assert "stale snapshot" not in text
        assert "stale (" not in text


def test_formats_and_post_ages_are_not_pooled(tmp_path: Path):
    posts = cohort() + [
        post("single-video", 900001, kind="Video", videoViewCount=900002),
        post("single-image", 800001, kind="Image"),
        post("too-young", 700001, age=6),
        post("too-old", 600001, age=61),
    ]
    snapshot(tmp_path, COLLECTED, posts)

    text = brief(tmp_path)

    assert "https://www.instagram.com/p/post-top/" in text
    assert "4.5" in text
    for excluded in ("single-video", "single-image", "too-young", "too-old"):
        assert f"https://www.instagram.com/p/{excluded}/" not in text


def test_post_age_boundaries_are_inclusive_at_collection_date(tmp_path: Path):
    snapshot(tmp_path, COLLECTED, [post("age-seven", 10, age=7), post("age-middle", 20), post("age-sixty", 90, age=60)])

    text = brief(tmp_path, today=date(2026, 10, 1))

    assert "https://www.instagram.com/p/age-sixty/" in text
    assert "4.5" in text


@pytest.mark.parametrize("bad_value", [None, -1, True, False, "90", float("nan"), float("inf"), -float("inf")])
def test_unobserved_likes_do_not_manufacture_an_adequate_cohort(tmp_path: Path, bad_value: object):
    snapshot(tmp_path, COLLECTED, [post("first", 10), post("second", 20), post("invalid", bad_value)])

    text = brief(tmp_path).lower()

    assert "unavailable" in text
    assert "https://www.instagram.com/p/invalid/" not in text
    assert any(term in text for term in ("three", "3", "insufficient", "too few"))


def test_zero_is_an_observed_metric_without_division_by_zero(tmp_path: Path):
    snapshot(tmp_path, COLLECTED, [post("zero-one", 0), post("zero-two", 0), post("positive", 90)])

    text = brief(tmp_path)

    assert "https://www.instagram.com/p/positive/" in text
    assert re.search(r"median[^\n]*\b0\b|\b0\b[^\n]*median", text, re.I)
    assert not re.search(r"\b(?:nan|inf|infinity)\b", text, re.I)


@pytest.mark.parametrize(
    "overrides",
    [
        {"ownerUsername": "another.account"},
        {"ownerUsername": "another.account", "inputUrl": "https://www.instagram.com/a.storyof.two/"},
        {"ownerUsername": None},
        {"ownerUsername": None, "inputUrl": "https://www.instagram.com/a.storyof.two.fan/"},
        {"ownerUsername": None, "inputUrl": "https://example.com/a.storyof.two/"},
        {"ownerUsername": None, "inputUrl": "https://www.instagram.com/another.account/?q=a.storyof.two"},
    ],
)
def test_ambiguous_or_foreign_ownership_is_excluded(tmp_path: Path, overrides: dict):
    snapshot(tmp_path, COLLECTED, [post("own-one", 10), post("own-two", 20), post("outsider", 90, **overrides)])

    text = brief(tmp_path).lower()

    assert "unavailable" in text
    assert "https://www.instagram.com/p/outsider/" not in text


def test_missing_owner_can_be_supported_by_exact_own_profile_input_url(tmp_path: Path):
    own = post("supported-owner", 90, inputUrl="https://www.instagram.com/a.storyof.two/")
    del own["ownerUsername"]
    snapshot(tmp_path, COLLECTED, [post("own-one", 10), post("own-two", 20), own])

    text = brief(tmp_path)

    assert "https://www.instagram.com/p/supported-owner/" in text
    assert "4.5" in text


def test_explicit_channel_coauthor_counts_as_own_channel_evidence(tmp_path: Path):
    collaboration = post(
        "own-collaboration", 90,
        ownerUsername="another.account",
        coauthorProducers=[{"username": "another.account"}, {"username": "a.storyof.two"}],
    )
    snapshot(tmp_path, COLLECTED, [post("own-one", 10), post("own-two", 20), collaboration])

    text = brief(tmp_path)

    assert "https://www.instagram.com/p/own-collaboration/" in text
    assert "4.5" in text


def test_duplicate_ids_cannot_inflate_evidence_or_select_a_winner(tmp_path: Path):
    duplicate = post("duplicate", 900)
    conflicting_duplicate = dict(duplicate, likesCount=9)
    snapshot(tmp_path, COLLECTED, [post("first", 10), post("second", 20), duplicate, conflicting_duplicate])

    text = brief(tmp_path).lower()

    assert "duplicate" in text
    assert "unavailable" in text
    assert "https://www.instagram.com/p/duplicate/" not in text


@pytest.mark.parametrize("timestamp", [None, "not a date", "2026-09-20T12:00:00Z"])
def test_invalid_or_future_post_dates_cannot_fill_a_cohort(tmp_path: Path, timestamp: object):
    snapshot(tmp_path, COLLECTED, [post("first", 10), post("second", 20), post("bad-date", 90, timestamp=timestamp)])

    text = brief(tmp_path).lower()

    assert "unavailable" in text
    assert "https://www.instagram.com/p/bad-date/" not in text


def test_change_observation_uses_matched_posts_from_previous_snapshot(tmp_path: Path):
    previous = [post("same-one", 10, age=20), post("same-two", 20, age=30), post("same-three", 30, age=40)]
    current = [dict(item, likesCount=item["likesCount"] * 2) for item in previous]
    current.append(post("new-unmatched-image", 999999, kind="Image"))
    snapshot(tmp_path, date(2026, 8, 25), previous)
    snapshot(tmp_path, COLLECTED, current)

    text = brief(tmp_path)

    assert "2026-08-25" in text
    assert "2026-09-01" in text
    assert "matched" in text.lower()
    assert re.search(r"\+20(?:\.0)?\b", text)
    assert "999999" not in text


def test_no_matched_previous_posts_means_no_invented_growth(tmp_path: Path):
    snapshot(tmp_path, date(2026, 8, 25), cohort(collected=date(2026, 8, 25), prefix="old"))
    snapshot(tmp_path, COLLECTED, cohort(prefix="new"))

    text = brief(tmp_path).lower()

    assert "unavailable" in text
    assert "matched" in text


def test_invalid_previous_counts_do_not_manufacture_growth(tmp_path: Path):
    previous = [post("same-one", 10), post("same-two", 20), post("same-three", None)]
    current = [post("same-one", 20), post("same-two", 40), post("same-three", 90)]
    snapshot(tmp_path, date(2026, 8, 25), previous)
    snapshot(tmp_path, COLLECTED, current)

    text = brief(tmp_path).lower()
    change_lines = [line for line in text.splitlines() if line.startswith("3.")]

    assert len(change_lines) == 1
    assert "unavailable" in change_lines[0]
    assert "matched" in change_lines[0]
    assert "+" not in change_lines[0]


def test_metric_coverage_keeps_views_plays_and_missing_values_separate(tmp_path: Path):
    posts = [
        post("first", 10, kind="Video", commentsCount=0, videoViewCount=0, videoPlayCount=100),
        post("second", 20, kind="Video", commentsCount=None, videoViewCount=-1, videoPlayCount=200),
        post("third", 90, kind="Video", commentsCount="99", videoViewCount=True, videoPlayCount=float("nan")),
    ]
    snapshot(tmp_path, COLLECTED, posts)

    text = brief(tmp_path).lower()

    assert re.search(r"comments\s+1/3", text)
    assert re.search(r"views\s+1/3", text)
    assert re.search(r"plays\s+2/3", text)
    assert re.search(r"\b0\b[^\n]*median comments|median comments[^\n]*\b0\b", text)
    assert "retention" in text
    assert "reach" in text
    assert "saves" in text


def test_malformed_row_shapes_do_not_crash_or_replace_valid_evidence(tmp_path: Path):
    malformed = [
        None,
        "not a post",
        post("bad-kind", 900, type=["Sidecar"]),
        post("bad-owner", 900, ownerUsername=None, inputUrl=["https://www.instagram.com/a.storyof.two/"]),
        post("bad-id", 900, id=["not-an-id"]),
        post("enormous", 10**400),
    ]
    snapshot(tmp_path, COLLECTED, cohort() + malformed)

    text = brief(tmp_path)

    assert "https://www.instagram.com/p/post-top/" in text
    assert "4.5" in text
    for excluded in ("bad-kind", "bad-owner", "bad-id", "enormous"):
        assert f"https://www.instagram.com/p/{excluded}/" not in text


def test_previous_counts_on_posts_published_after_previous_collection_are_unavailable(tmp_path: Path):
    previous = [post("same-one", 10, age=20), post("same-two", 20, age=30), post("same-three", 30, age=40)]
    current = [dict(item, likesCount=item["likesCount"] * 2) for item in previous]
    previous[-1]["timestamp"] = "2026-08-29T12:00:00Z"
    snapshot(tmp_path, date(2026, 8, 25), previous)
    snapshot(tmp_path, COLLECTED, current)

    text = brief(tmp_path).lower()
    change_lines = [line for line in text.splitlines() if line.startswith("3.")]

    assert len(change_lines) == 1
    assert "unavailable" in change_lines[0]
    assert "matched" in change_lines[0]


def test_brief_does_not_write_or_modify_repository_files(tmp_path: Path):
    snapshot(tmp_path, COLLECTED, cohort())
    before = {str(path.relative_to(tmp_path)): (path.read_bytes(), path.stat().st_mtime_ns) for path in tmp_path.rglob("*") if path.is_file()}

    brief(tmp_path)

    after = {str(path.relative_to(tmp_path)): (path.read_bytes(), path.stat().st_mtime_ns) for path in tmp_path.rglob("*") if path.is_file()}
    assert after == before


def test_default_brief_leads_with_decisions_and_keeps_maintenance_opt_in(tmp_path: Path, monkeypatch, capsys):
    from scripts import daily_creator_brief

    snapshot(tmp_path, COLLECTED, cohort())
    monkeypatch.setattr(daily_creator_brief, "ROOT", tmp_path)
    assert daily_creator_brief.build_brief() == 0
    text = capsys.readouterr().out
    assert text.index("## Three observations") < text.index("## Repository status")
    assert "## One proposed experiment" in text
    assert "--maintenance" in text
    assert "## Research Partner Lens" not in text
    assert "## Learning Debt" not in text
    assert "## Next Commands" not in text
