"""A3: source-bound performance comparisons with explicit evidence limits."""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
from collections import Counter, defaultdict
from datetime import date, datetime, timezone
from pathlib import Path
from statistics import median
from typing import Any

from pipeline.stages.a2_parser import FORMAT_ALIASES, METRIC_ALIASES, normalize_post
from pipeline.stages.source_integrity import atomic_write_text, verify_source_receipt
from pipeline.stages.carousel_analysis import carousel_visual_evidence, carousel_report_lines, carousel_results_evidence, carousel_results_lines

BASE_METRICS = tuple(METRIC_ALIASES)
RATE_METRICS = tuple(f"{name}_per_reach" for name in ("sends", "shares", "saves", "likes"))
METRICS = BASE_METRICS + RATE_METRICS
PRIMARY_ORDER = RATE_METRICS + ("retention_rate", "sends", "shares", "saves", "likes", "comments", "views", "viewers", "follows", "plays")
AGE_BANDS = ((7, 13), (14, 29), (30, 60))
MIN_SAMPLE = 5
MIN_COVERAGE = 0.8


def number(value: Any, *, fraction: bool = False) -> float | None:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    try:
        value = float(value)
    except OverflowError:
        return None
    if not math.isfinite(value) or value < 0 or (fraction and value > 1):
        return None
    return value


def day(value: Any) -> date | None:
    if not isinstance(value, str):
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00")).date()
    except ValueError:
        return None


def collection_date(path: Path) -> date | None:
    match = re.fullmatch(r"(\d{4}-\d{2}-\d{2})-(?:raw|posts)(?:-\d+)?\.json", path.name)
    if not match:
        return None
    try:
        return date.fromisoformat(match[1])
    except ValueError:
        return None


def load_posts(posts_path: Path) -> list[Any]:
    posts = json.loads(posts_path.read_text(encoding="utf-8"))
    if not isinstance(posts, list):
        raise ValueError(f"Expected a list in {posts_path}")
    return posts


def canonical_post(item: dict) -> dict:
    post = dict(item) if "engagement" in item else normalize_post(item)
    engagement = post.get("engagement")
    engagement = engagement if isinstance(engagement, dict) else {}
    status = post.get("metric_status")
    status = status if isinstance(status, dict) else {}
    legacy = post.get("schema_version") != "2.0"
    values, statuses = {}, {}
    for metric in BASE_METRICS:
        value = number(engagement.get(metric), fraction=metric == "retention_rate")
        # Earlier A2 versions zero-filled absent counts. Never reconstruct
        # 'observed zero' without its original raw record or observation status.
        ambiguous = legacy and value == 0
        if ambiguous or status.get(metric) == "unavailable":
            value = None
        values[metric] = value
        statuses[metric] = "ambiguous_legacy_zero" if ambiguous else ("observed" if value is not None else "unavailable")
    for metric in RATE_METRICS:
        numerator = values[metric.removesuffix("_per_reach")]
        reach = values["reach"]
        values[metric] = number(numerator / reach) if numerator is not None and reach is not None and reach > 0 else None
        statuses[metric] = "observed" if values[metric] is not None else "unavailable"
    raw_type = str(post.get("post_type") or "").lower()
    post["post_type"] = FORMAT_ALIASES.get(raw_type, "unknown")
    post["engagement"], post["metric_status"] = values, statuses
    post["rate_provenance"] = {
        metric: {"numerator": metric.removesuffix("_per_reach"), "denominator": "reach",
                 "denominator_value": values["reach"], "source": post.get("source"),
                 "observed_at": post.get("observed_at"), "collected_on": post.get("collected_on"),
                 "availability": statuses[metric]}
        for metric in RATE_METRICS
    }
    post["caption"] = post.get("caption") if isinstance(post.get("caption"), str) else ""
    post["hashtags"] = sorted(set(tag.lower() for tag in re.findall(r"(?<!\w)#([\w]+)", post["caption"])))
    return post


def coverage(posts: list[dict], metric: str) -> dict:
    values = [p["engagement"][metric] for p in posts if p["engagement"][metric] is not None]
    return {"observed": len(values), "unavailable": len(posts) - len(values),
            "median": median(values) if values else None}


def post_link(post: dict) -> str | None:
    shortcode = post.get("shortcode")
    if isinstance(shortcode, str) and re.fullmatch(r"[A-Za-z0-9_-]+", shortcode):
        return f"https://www.instagram.com/p/{shortcode}/"
    url = post.get("url")
    if isinstance(url, str) and re.fullmatch(r"https://www\.instagram\.com/(?:p|reel)/[A-Za-z0-9_-]+/?", url):
        return url
    return None


def caption_features(post: dict) -> set[str]:
    caption = post["caption"]
    features = {f"caption hashtag #{tag}" for tag in post["hashtags"]}
    if caption.strip():
        features.add("caption contains a question mark" if "?" in caption else "caption has no question mark")
        features.add("caption has 20 words or fewer" if len(caption.split()) <= 20 else "caption has more than 20 words")
    return features


def analyze_posts(posts: list[Any], collected_on: date | None = None, today: date | None = None) -> dict[str, Any]:
    today = today or date.today()
    if collected_on and collected_on > today:
        raise ValueError("Collection date is in the future; correct source provenance")
    unique, conflicts = {}, set()
    exclusions = Counter()
    unknown_owner = 0
    for item in posts:
        if not isinstance(item, dict):
            exclusions["invalid_row"] += 1
            continue
        post = canonical_post(item)
        owner = post.get("ownerUsername")
        coauthors = post.get("coauthorProducers")
        collab = isinstance(coauthors, list) and any(isinstance(p, dict) and p.get("username") == "a.storyof.two" for p in coauthors)
        if owner and owner != "a.storyof.two" and not collab:
            exclusions["foreign_owner"] += 1
            continue
        identifier = post.get("id") or post.get("shortcode") or post.get("url")
        if isinstance(identifier, bool) or not isinstance(identifier, (str, int)) or not str(identifier):
            exclusions["missing_identity"] += 1
            continue
        identifier = str(identifier)
        post["id"] = identifier
        post["url"] = post_link(post)
        if identifier in conflicts:
            exclusions["conflicting_duplicate"] += 1
            continue
        if identifier in unique:
            if post == unique[identifier]:
                exclusions["identical_duplicate"] += 1
            else:
                unique.pop(identifier)
                conflicts.add(identifier)
                exclusions["conflicting_duplicate"] += 2
            continue
        unique[identifier] = post
    clean = sorted(unique.values(), key=lambda p: p["id"])
    groups = defaultdict(list)
    ineligible = Counter()
    for post in clean:
        if not post.get("ownerUsername"):
            unknown_owner += 1
        published = day(post.get("timestamp"))
        post["published_on"] = published.isoformat() if published else None
        # Per-row observation timestamps override batch filenames. Never treat
        # heterogeneous native Insights as if every row was collected today.
        row_collected = day(post.get("observed_at")) or day(post.get("collected_on")) or collected_on
        age = (row_collected - published).days if row_collected and published else None
        if post.get("observed_at"):
            try:
                observed_at = datetime.fromisoformat(post["observed_at"].replace("Z", "+00:00"))
                published_at = datetime.fromisoformat(post["timestamp"].replace("Z", "+00:00"))
                if observed_at.tzinfo is not None and published_at.tzinfo is not None:
                    age = (observed_at - published_at).total_seconds() / 86400
            except (KeyError, TypeError, ValueError):
                age = None
        post["age_days"] = age
        post["collected_on"] = row_collected.isoformat() if row_collected else None
        if row_collected and row_collected > today:
            ineligible["future_collection"] += 1
            continue
        band = next((f"{lo}-{hi}" for lo, hi in AGE_BANDS if age is not None and lo <= age < hi + 1), None)
        if post["post_type"] == "unknown":
            ineligible["unknown_format"] += 1
        elif age is None:
            ineligible["unknown_publication_or_collection_date"] += 1
        elif age < 0:
            ineligible["published_after_collection"] += 1
        elif band is None:
            ineligible["outside_7_to_60_day_window"] += 1
        else:
            groups[(post["post_type"], band)].append(post)

    cohorts = []
    for (kind, band), members in sorted(groups.items()):
        metrics = {metric: coverage(members, metric) for metric in METRICS}
        comparisons = []
        for metric in PRIMARY_ORDER:
            available = [p for p in members if p["engagement"][metric] is not None]
            if len(available) < MIN_SAMPLE or len(available) / len(members) < MIN_COVERAGE:
                continue
            available.sort(key=lambda p: (p["engagement"][metric], p["id"]))
            quartile = max(1, len(available) // 4)
            low_cut = available[quartile - 1]["engagement"][metric]
            high_cut = available[-quartile]["engagement"][metric]
            # Include boundary ties; if the tails overlap, no contrast exists.
            lower = [p["id"] for p in available if p["engagement"][metric] <= low_cut]
            higher = [p["id"] for p in available if p["engagement"][metric] >= high_cut]
            if low_cut >= high_cut:
                lower, higher = [], []
            comparisons.append({"metric": metric, "n": len(available), "median": metrics[metric]["median"],
                                "higher": higher, "lower": lower, "has_contrast": low_cut < high_cut})
        primary = comparisons[0] if comparisons else None
        patterns = []
        if primary:
            high = [unique[i] for i in primary["higher"]]
            low = [unique[i] for i in primary["lower"]]
            # Caption metadata only. Missing caption is unobserved, never an
            # absent feature. Require at least two observed captions per tail.
            high_captions = [p for p in high if p["caption"].strip()]
            low_captions = [p for p in low if p["caption"].strip()]
            if len(high_captions) >= 2 and len(low_captions) >= 2:
                features = set().union(*(caption_features(p) for p in high_captions + low_captions))
                for feature in sorted(features):
                    h = [p["id"] for p in high_captions if feature in caption_features(p)]
                    l = [p["id"] for p in low_captions if feature in caption_features(p)]
                    difference = len(h) / len(high_captions) - len(l) / len(low_captions)
                    if difference != 0 and len(h) + len(l) >= 2:
                        patterns.append({"feature": feature, "higher_with_feature": h, "higher_observed": len(high_captions),
                                         "lower_with_feature": l, "lower_observed": len(low_captions),
                                         "difference": difference})
                patterns.sort(key=lambda p: (-abs(p["difference"]), p["feature"]))
        cohorts.append({"format": kind, "age_band": band, "n": len(members), "post_ids": [p["id"] for p in members],
                        "metrics": metrics, "comparisons": comparisons, "primary_metric": primary["metric"] if primary else None,
                        "caption_patterns": patterns[:5]})

    available_dates = [p["published_on"] for p in clean if p["published_on"]]
    observation_dates = sorted({p["collected_on"] for p in clean if p.get("collected_on")})
    common_collection = date.fromisoformat(observation_dates[0]) if len(observation_dates) == 1 else collected_on if not clean else None
    observation_freshness = {"stale" if (today - date.fromisoformat(stamp)).days > 14 else "recent" for stamp in observation_dates}
    freshness = (next(iter(observation_freshness)) if len(observation_freshness) == 1 else "mixed" if observation_freshness else
                 "stale" if common_collection and (today - common_collection).days > 14 else "recent" if common_collection else "unknown")
    if any(not p.get("collected_on") for p in clean):
        freshness = "mixed" if observation_dates else "unknown"
    return {
        "schema_version": "2.0", "generated_on": today.isoformat(),
        "collected_on": common_collection.isoformat() if common_collection else None,
        "batch_collected_on": collected_on.isoformat() if collected_on else None,
        "observation_range": [observation_dates[0], observation_dates[-1]] if observation_dates else [],
        "freshness": freshness,
        "source_age_days": (today - common_collection).days if common_collection else None,
        "input_count": len(posts), "post_count": len(clean), "exclusions": dict(exclusions),
        "cohort_exclusions": dict(ineligible), "ownership_unverified_count": unknown_owner,
        "publication_range": [min(available_dates), max(available_dates)] if available_dates else [],
        "metric_coverage": {metric: coverage(clean, metric) for metric in METRICS},
        "cohorts": cohorts, "posts": clean,
        "content_evidence": {"caption_observed": sum(bool(p["caption"].strip()) for p in clean),
                             "video_hooks": "unavailable", "scenes": "unavailable", "relationship_dynamics": "unavailable"},
        "method": {"minimum_observed": MIN_SAMPLE, "minimum_coverage": MIN_COVERAGE,
                   "age_bands_days": [list(band) for band in AGE_BANDS], "counts": "cumulative_at_collection",
                   "primary_metric_priority": list(PRIMARY_ORDER)},
    }


def display(value: float | None, metric: str = "") -> str:
    if value is None:
        return "unavailable"
    if metric.endswith("_per_reach") or metric == "retention_rate":
        return f"{value:.2%}"
    return f"{value:,.1f}".removesuffix(".0")


def cell(text: Any) -> str:
    return str(text).replace("\\", "\\\\").replace("|", "\\|").replace("\n", " ").replace("\r", " ").replace("<", "&lt;").replace(">", "&gt;")


def reference(post: dict) -> str:
    return f"[{cell(post['id'])}]({post['url']})" if post.get("url") else f"ID {cell(post['id'])} (URL unavailable)"


def report_markdown(summary: dict[str, Any], source: Path, today: date) -> str:
    title = "Carousel Visual and Performance Analysis" if summary.get("analysis_focus") == "carousel" else "Corpus Performance Analysis"
    lines = [f"# @a.storyof.two — {title}", "", f"Generated: {today}",
             f"Source: [{source.name}]({source.resolve()})", ""]
    provenance = summary.get("source", {})
    lines += [f"Recorded collection date: {summary['collected_on'] or 'unknown'} ({provenance.get('date_basis', 'caller supplied')}).",
              f"Source age: {summary['source_age_days'] if summary['source_age_days'] is not None else 'unknown'} days; evidence is **{summary['freshness']}**."]
    if summary.get("observation_range"):
        lines.append(f"Actual observation-date range: {' to '.join(summary['observation_range'])}; per-post timestamps take precedence over a batch filename.")
    if provenance.get("sha256"):
        lines.append(f"Source SHA-256: `{provenance['sha256']}`")
    if isinstance(provenance.get("provenance"), dict):
        lines.append(
            "<!-- a-story-source-provenance: "
            + json.dumps(provenance["provenance"], sort_keys=True)
            + " -->"
        )
    if isinstance(provenance.get("receipt"), dict):
        lines.append(
            "<!-- a-story-source-receipt: "
            + json.dumps(provenance["receipt"], sort_keys=True)
            + " -->"
        )
    if summary.get("carousel_visual_evidence"):
        lines += [""] + carousel_report_lines(summary["carousel_visual_evidence"], Path(summary["workspace_root"]))
    lines += ["", "## What this evidence supports", "",
              f"{summary['post_count']} unique posts from {summary['input_count']} input rows; publication range: {' to '.join(summary['publication_range']) or 'unknown'}.",
              f"Excluded rows: {summary['exclusions'] or 'none'}. Ownership unverified: {summary['ownership_unverified_count']} posts.",
              "Comparisons use the same format and a 7–13, 14–29, or 30–60 day publication-age band at collection. Each metric needs at least five observed posts and 80% cohort coverage.",
              "Counts remain cumulative and exposure is unequal even within a band. These are descriptive associations, not causal effects or a forecast. The primary metric follows a declared priority, not whichever produces the biggest difference.",
              "Missing and hidden values are unavailable. Zero-filled values in legacy normalized files are ambiguous unless backed by raw evidence. Shares and sends, and views and plays, remain distinct."]
    if summary["freshness"] != "recent":
        lines.append("**Refresh or establish collection provenance before using this as current strategy. A new report date does not refresh the evidence.**")
    lines += ["", "## Metric coverage", "", "| Metric | Observed | Unavailable | Median of observed |", "| --- | ---: | ---: | ---: |"]
    for metric, info in summary["metric_coverage"].items():
        lines.append(f"| {metric} | {info['observed']} | {info['unavailable']} | {display(info['median'], metric)} |")
    lines += ["", "Rates use paired observed numerator and positive reach from the same record. Retention rate is accepted only as an explicitly supplied fraction from 0 to 1. Global medians are coverage summaries, not cross-format rankings.",
              "", "## Stronger and weaker posts within comparable groups", "",
              f"Posts outside comparison groups: {summary['cohort_exclusions'] or 'none'}."]
    lookup = {p["id"]: p for p in summary["posts"]}
    for cohort in summary["cohorts"]:
        lines += ["", f"### {cohort['format']} · {cohort['age_band']} days · n={cohort['n']}", ""]
        if not cohort["comparisons"]:
            lines.append("Insufficient observed coverage or no distinct higher/lower tails. No winner is selected.")
            continue
        comparison = cohort["comparisons"][0]
        metric = comparison["metric"]
        if not comparison["has_contrast"]:
            lines.append(f"Primary metric: **{metric}**; observed {comparison['n']}/{cohort['n']}; median {display(comparison['median'], metric)}. The tails overlap, so no stronger/weaker contrast is claimed. The metric is not changed to seek a more dramatic result.")
            continue
        lines += [f"Primary metric: **{metric}**; observed {comparison['n']}/{cohort['n']}; median {display(comparison['median'], metric)}. Higher/lower tails use quartile boundaries including ties.",
                  "", "| Tail | Post | Published | Value | Caption excerpt (not video hook) |", "| --- | --- | --- | ---: | --- |"]
        for tail in ("higher", "lower"):
            for identifier in comparison[tail]:
                post = lookup[identifier]
                caption = post["caption"]
                excerpt = caption[:180] + ("…" if len(caption) > 180 else "")
                lines.append(f"| {tail} | {reference(post)} | {post['published_on']} | {display(post['engagement'][metric], metric)} | {cell(excerpt) or 'unavailable'} |")
        lines += ["", "Caption metadata differences (exploratory; many features inspected, no significance claim):", ""]
        if not cohort["caption_patterns"]:
            lines.append("No eligible caption contrast: a repeated differing feature needs at least two supporting posts overall and at least two observed captions in each tail.")
        for pattern in cohort["caption_patterns"]:
            high_links = ", ".join(reference(lookup[i]) for i in pattern["higher_with_feature"]) or "none"
            low_links = ", ".join(reference(lookup[i]) for i in pattern["lower_with_feature"]) or "none"
            lines.append(f"- {cell(pattern['feature'])}: higher {len(pattern['higher_with_feature'])}/{pattern['higher_observed']}, lower {len(pattern['lower_with_feature'])}/{pattern['lower_observed']}. Higher examples: {high_links}; lower examples: {low_links}.")
    if not summary["cohorts"]:
        lines.append("No comparable groups available; supply valid collection/publication dates and sufficient same-format observations.")
    if summary.get("carousel_results"):
        lines += [""] + carousel_results_lines(summary["carousel_results"], Path(summary["workspace_root"]))
    lines += ["", "## What remains unmeasured", "",
              "Pixel observations of available local carousels are documented above when attached. Unreviewed slides remain pending. Video hooks and measured swipe retention are unavailable; captions are not substitutes for visual inspection.",
              "No fixed confidence score is assigned: judge each observation by its sample, coverage, age, and source evidence above.",
              "", "## Next decision", "",
              "Review both tails of one eligible group before proposing a content change. Record what is actually visible in those posts; treat any explanation as a hypothesis. Test one change prospectively and collect the same metric at the same post age. Do not change strategy from a hashtag contrast alone.",
              "The companion JSON includes every retained post, per-metric comparison, missing-value status, exclusions, and source hash. This command does not publish or update rules or memory.", ""]
    return "\n".join(lines)


def select_source(root: Path) -> Path:
    candidates = []
    for directory, suffix, priority in (("posts", "posts", 0), ("raw", "raw", 1)):
        for path in (root / "corpus" / directory).glob(f"*-{suffix}*.json"):
            collected = collection_date(path)
            if collected:
                candidates.append((collected, priority, path))
    for path in (root / "corpus/insights").glob("*/*.json"):
        payload = json.loads(path.read_text(encoding="utf-8"))
        observed = day(payload.get("observed_at")) if isinstance(payload, dict) else None
        if observed:
            candidates.append((observed, 2, path))
    if not candidates:
        undated = sorted((root / "corpus").glob("*.json"))
        if len(undated) == 1:
            return undated[0]
        raise FileNotFoundError("No dated own-channel snapshot is available; supply --posts-path for an undated export (no age comparisons)")
    return max(candidates)[2]


def run(root: Path | None = None, posts_path: Path | None = None, today: date | None = None,
        collected_on: date | None = None, *, all_formats: bool = False) -> Path:
    root = (root or Path.cwd()).resolve()
    today = today or date.today()
    source = posts_path or select_source(root)
    source = source if source.is_absolute() else root / source
    source = source.resolve()
    # Parse the exact bytes whose hash is reported, avoiding a second-read race.
    content = source.read_bytes()
    rows = json.loads(content)
    native_observed = None
    if isinstance(rows, dict) and rows.get("schema_version") == "carousel-insights/v1":
        from pipeline.stages.carousel_results import load_metric_observations
        native_observed = day(rows.get("observed_at"))
        source_relative = str(source.relative_to(root))
        rows = [row for row in load_metric_observations(root) if row["source"]["path"] == source_relative]
    elif isinstance(rows, dict) and isinstance(rows.get("posts"), list):
        rows = rows["posts"]
    if not isinstance(rows, list):
        raise ValueError(f"Expected a post list or a native Insights snapshot in {source}")
    collected = collected_on or native_observed or collection_date(source)
    selected = rows if all_formats else [p for p in rows if isinstance(p, dict) and canonical_post(p)["post_type"] == "sidecar"]
    summary = analyze_posts(selected, collected, today)
    summary["analysis_focus"] = "all_formats" if all_formats else "carousel"
    summary["source_post_count"] = len(rows)
    summary["other_format_rows"] = len(rows) - len(selected)
    summary["workspace_root"] = str(root)
    summary["carousel_visual_evidence"] = carousel_visual_evidence(root, summary["posts"])
    summary["carousel_results"] = carousel_results_evidence(root)
    summary["content_evidence"]["carousel_pixel_reviews"] = summary["carousel_visual_evidence"]["counts"]
    summary["content_evidence"]["scenes"] = "reviewed_local_carousel_slides" if summary["carousel_visual_evidence"]["counts"]["reviewed_slides"] else "pending_local_image_review"
    summary["content_evidence"]["relationship_dynamics"] = "editorial_carousel_observations" if summary["carousel_visual_evidence"]["counts"]["reviewed_slides"] else "pending_local_image_review"
    summary["source"] = {"path": str(source), "sha256": hashlib.sha256(content).hexdigest(),
                         "collected_on": collected.isoformat() if collected else None,
                         "date_basis": "explicit --collected-on" if collected_on else ("native observed_at timestamp" if native_observed else "recorded snapshot filename; individual observed_at timestamps take precedence" if collected else "unknown")}
    provenance = [row.get("source_provenance") for row in rows if isinstance(row, dict) and isinstance(row.get("source_provenance"), dict)]
    if source.parent.name == "posts":
        source_receipt, receipt_errors = verify_source_receipt(root, source)
        if receipt_errors:
            raise ValueError("A3 refuses normalized input with invalid source receipt: " + "; ".join(receipt_errors))
        identities = {(item.get("snapshot_id"), item.get("raw_sha256"), item.get("status")) for item in provenance}
        if provenance and len(identities) != 1:
            raise ValueError("A3 requires one verified A1 provenance receipt per normalized source")
        if provenance and source_receipt.get("source_provenance") != provenance[0]:
            raise ValueError("A3 source receipt does not match normalized row provenance")
        summary["source"]["provenance"] = source_receipt["source_provenance"]
        summary["source"]["receipt"] = source_receipt
    else:
        summary["source"]["provenance"] = {"status": "unverified_legacy"}
        summary["source"]["receipt"] = {
            "status": "unverified_legacy",
            "reason": "explicit or legacy source has no verified A1-A2 receipt chain",
        }
    out_dir = root / "output" / "reports"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"{today}-analysis.md"
    json_path = out_path.with_suffix(".json")
    atomic_write_text(json_path, json.dumps(summary, indent=2, ensure_ascii=False, allow_nan=False) + "\n")
    atomic_write_text(out_path, report_markdown(summary, source, today))
    return out_path


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="A3: compare post performance with source evidence and missing-metric coverage.")
    parser.add_argument("--posts-path", type=Path, help="Raw or normalized JSON; default chooses newest dated snapshot, preferring raw on ties.")
    parser.add_argument("--workspace-root", type=Path, default=Path.cwd())
    parser.add_argument("--all-formats", action="store_true", help="Also analyze Reels and single images; default focuses on carousels.")
    parser.add_argument("--collected-on", type=date.fromisoformat, help="Explicit collection date for a source without a dated filename (YYYY-MM-DD).")
    args = parser.parse_args(argv)
    try:
        out_path = run(root=args.workspace_root, posts_path=args.posts_path, collected_on=args.collected_on, all_formats=args.all_formats)
    except (OSError, ValueError) as exc:
        parser.exit(2, f"Analysis unavailable: {exc}\n")
    print(out_path)
    print(out_path.with_suffix(".json"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
