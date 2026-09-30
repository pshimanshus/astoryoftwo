#!/usr/bin/env python3
"""Print a creator decision brief from saved evidence; maintenance is opt-in."""

from __future__ import annotations

import argparse
import json
import math
import re
import sys
from collections import defaultdict
from datetime import date, datetime
from pathlib import Path
from statistics import median


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.start_agentic_session import load_research_partner_lens  # noqa: E402
from pipeline.agentic.learning_loop import (  # noqa: E402
    compact,
    learning_debt_records,
    list_hypotheses,
    recent_learning_records,
    relative_to,
)


def newest(paths: list[Path]) -> Path | None:
    existing = [path for path in paths if path.exists()]
    if not existing:
        return None
    return max(existing, key=lambda path: (path.stat().st_mtime, str(path)))


def newest_glob(pattern: str) -> Path | None:
    return newest(list(ROOT.glob(pattern)))


def recent_dirs(path: Path, limit: int = 5) -> list[Path]:
    if not path.exists():
        return []
    dirs = [item for item in path.iterdir() if item.is_dir()]
    return sorted(dirs, key=lambda item: (item.stat().st_mtime, item.name), reverse=True)[:limit]


def read_text(path: Path, limit: int = 1200) -> str:
    if not path.exists():
        return ""
    text = path.read_text(encoding="utf-8", errors="replace").strip()
    return text[:limit]


def status_from_diagnostics(path: Path | None) -> str:
    if not path:
        return "missing"
    text = read_text(path, limit=2000)
    match = re.search(r"^Status:\s*(\S+)", text, flags=re.MULTILINE)
    return match.group(1) if match else "unknown"


def first_matching_lines(path: Path, patterns: tuple[str, ...], limit: int = 6) -> list[str]:
    if not path.exists():
        return []
    matches: list[str] = []
    for raw_line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        line = raw_line.strip()
        if not line:
            continue
        lowered = line.lower()
        if any(pattern in lowered for pattern in patterns):
            matches.append(line)
        if len(matches) >= limit:
            break
    return matches


def fact_summaries(path: Path, limit: int = 6) -> list[str]:
    if not path.exists():
        return []
    facts: list[str] = []
    current: list[str] = []
    for raw_line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        line = raw_line.strip()
        if line.startswith("fact: "):
            if current:
                facts.append(" ".join(current))
            current = [line.removeprefix("fact: ").strip()]
            continue
        if current and line and not line.startswith("confidence:") and not line.startswith("- "):
            current.append(line)
        elif current:
            facts.append(" ".join(current))
            current = []
    if current:
        facts.append(" ".join(current))

    filtered = []
    for fact in facts:
        lowered = fact.lower()
        if any(pattern in lowered for pattern in ("avoid", "do not", "must", "blocking", "required", "risk")):
            filtered.append(fact)
        if len(filtered) >= limit:
            break
    return filtered


def relative(path: Path | None) -> str:
    return relative_to(ROOT, path)


def hypothesis_brief_records(root: Path, limit: int = 5) -> list[dict[str, str]]:
    open_records = list_hypotheses(root, status="open", limit=limit)
    resolved_records = list_hypotheses(root, status="resolved", limit=limit)
    records: list[dict[str, str]] = []

    for payload in open_records:
        records.append(
            {
                "kind": "open",
                "path": str(payload.get("hypothesis_path", "missing")),
                "line": (
                    f"open {payload.get('hypothesis_id', 'unknown')} from "
                    f"{payload.get('source', 'unknown source')}: "
                    f"{compact(payload.get('hypothesis', ''))}"
                ),
            }
        )
    for payload in resolved_records:
        outcome = payload.get("outcome", "inconclusive")
        records.append(
            {
                "kind": "resolved",
                "path": str(payload.get("hypothesis_path", "missing")),
                "line": (
                    f"resolved {outcome} {payload.get('hypothesis_id', 'unknown')}: "
                    f"{compact(payload.get('result_summary', ''))}"
                ),
            }
        )
    return records[:limit]


def print_section(title: str) -> None:
    print(f"\n## {title}")


def observed_count(value: object) -> float | None:
    """Missing, hidden and invalid counts are not zero."""
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    try:
        return float(value) if math.isfinite(value) and value >= 0 else None
    except OverflowError:
        return None


def post_date(value: object) -> date | None:
    if not isinstance(value, str):
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00")).date()
    except ValueError:
        return None


def read_snapshot(path: Path) -> tuple[list[dict], int]:
    """Read own-channel rows without the parser's missing-to-zero coercion."""
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, list):
        raise ValueError("expected a list of posts")
    rows: dict[str, dict] = {}
    conflicts: set[str] = set()
    excluded = 0
    for row in payload:
        if not isinstance(row, dict):
            excluded += 1
            continue
        owner = row.get("ownerUsername")
        coauthors = row.get("coauthorProducers")
        collaboration = isinstance(coauthors, list) and any(
            isinstance(person, dict) and person.get("username") == "a.storyof.two" for person in coauthors
        )
        input_url = row.get("inputUrl")
        own = owner == "a.storyof.two" or collaboration or (
            not owner and isinstance(input_url, str) and input_url in {
                "https://www.instagram.com/a.storyof.two/",
                "https://www.instagram.com/a.storyof.two",
            }
        )
        identifier = row.get("id") or row.get("shortCode") or row.get("url")
        if not own or isinstance(identifier, bool) or not isinstance(identifier, (str, int)) or not str(identifier):
            excluded += 1
            continue
        key = str(identifier)
        if key in conflicts:
            excluded += 1
            continue
        if key in rows:
            excluded += 1
            if rows[key] != row:
                # Conflicting counts for one post cannot be resolved by order.
                rows.pop(key)
                conflicts.add(key)
                excluded += 1
            continue
        rows[key] = row
    return list(rows.values()), excluded


def post_reference(row: dict) -> str:
    shortcode = row.get("shortCode")
    url = row.get("url")
    if isinstance(shortcode, str) and re.fullmatch(r"[A-Za-z0-9_-]+", shortcode):
        url = f"https://www.instagram.com/p/{shortcode}/"
    if isinstance(url, str) and re.fullmatch(r"https://www\.instagram\.com/(?:p|reel)/[A-Za-z0-9_-]+/?", url):
        return f"[post]({url})"
    return f"post ID {row.get('id', 'unavailable')}"


def performance_brief(root: Path, today: date | None = None, *, all_formats: bool = False) -> list[str]:
    """Describe observed counts, then propose a test; never infer hook causality.

    This is a read-only brief over existing A1 snapshots, not a replacement for
    the channel analyzer. File modification times and generated reports cannot
    refresh source evidence. The date in the A1 filename is the only collection
    provenance currently persisted by that pipeline.
    """
    today = today or date.today()
    lines = ["# Daily Creator Brief", "", f"Prepared: {today}", "", "## Evidence available"]
    candidates = []
    for path in (root / "corpus" / "raw").glob("*-raw.json"):
        if not re.fullmatch(r"\d{4}-\d{2}-\d{2}-raw\.json", path.name):
            continue
        try:
            collected = date.fromisoformat(path.name.removesuffix("-raw.json"))
        except ValueError:
            continue
        candidates.append((collected, path))
    if not candidates:
        return lines + ["Own-channel performance data unavailable: no dated raw snapshot.",
                        "Next action: collect an own-channel snapshot before recommending a performance-based experiment."]

    candidates.sort()
    collected, source = candidates[-1]
    lines.append(f"Source: [{source.name}]({source}); recorded collection date: {collected} (filename; no embedded collection timestamp).")
    age = (today - collected).days
    if age < 0:
        return lines + ["Unavailable: newest snapshot has a future collection date. Correct its provenance before using it."]
    lines.append(f"Freshness: {'STALE — historical evidence only' if age > 14 else 'within the 14-day brief freshness window'}; {age} days old.")
    try:
        rows, excluded = read_snapshot(source)
    except (OSError, ValueError) as exc:
        return lines + [f"Unavailable: newest snapshot cannot be read ({type(exc).__name__}). Repair it; older data was not substituted."]
    if not rows:
        return lines + ["Unavailable: newest snapshot contains no usable own-channel posts. Collect a valid snapshot before choosing an experiment."]
    source_count = len(rows)
    if not all_formats:
        rows = [row for row in rows if str(row.get("type")).lower() in ("sidecar", "carousel")]
        lines.append(f"Focus: carousels ({len(rows)} of {source_count} source posts). Other formats require --all-formats.")
        if not rows:
            return lines + ["No carousels in this snapshot. No Reel-based recommendation is substituted."]

    from pipeline.stages.a3_analyzer import canonical_post
    from pipeline.stages.carousel_analysis import carousel_visual_evidence
    visual = carousel_visual_evidence(root, [canonical_post(row) for row in rows])
    counts = visual["counts"]
    lines += ["", "## Carousel visual evidence", "",
              f"Local pixel review: {counts['reviewed_slides']} slides; {counts['complete_reviews']} complete carousels and {counts['partial_reviews']} partial carousels. Saved observations are checked against current file hashes."]
    for review in visual["carousels"]:
        if review["assessment"]:
            code = review["shortcode"]
            lines.append(f"- [{review['title']}](https://www.instagram.com/p/{code}/): {review['assessment']['hook']} Sequence: {review['assessment']['sequence']}")
    if not counts["reviewed_slides"]:
        lines.append("Open available local slides and review image, on-image text and sequence before drawing creative conclusions. This command does not claim to perform new pixel inspection.")
    lines += [f"[Full visual evidence]({root / 'output/reports/carousel-visual-evidence.json'}). No image downloads are needed for the available archive.", ""]

    dated = [(row, post_date(row.get("timestamp"))) for row in rows]
    valid_dates = [day for _, day in dated if day and day <= collected]
    period = f"{min(valid_dates)} to {max(valid_dates)}" if valid_dates else "unavailable"
    lines.append(f"Coverage: {len(rows)} unique own-channel posts; publication dates {period}; {excluded} duplicate, foreign, or invalid rows excluded.")
    fields = {"likes": "likesCount", "comments": "commentsCount", "views": "videoViewCount", "plays": "videoPlayCount"}
    coverage = "; ".join(f"{label} {sum(observed_count(row.get(key)) is not None for row in rows)}/{len(rows)}" for label, key in fields.items())
    lines.append(f"Observed metrics: {coverage}. Missing/hidden counts stay unavailable; views and plays are separate.")
    lines.append("Reach, saves, sends and retention are not supplied by this brief's source contract; no engagement rates or hook-quality claims are inferred.")
    if age > 14:
        lines.append("Refresh the own-channel snapshot before treating these observations as current strategy.")

    # A bounded publication window and minimum age reduce obvious comparisons
    # between old viral posts and brand-new posts. These remain lifetime counts.
    groups: dict[str, list[dict]] = defaultdict(list)
    for row, day in dated:
        kind = {"Video": "video", "Sidecar": "carousel", "Image": "image"}.get(str(row.get("type")))
        if kind and day and 7 <= (collected - day).days <= 60 and observed_count(row.get("likesCount")) is not None:
            groups[kind].append(row)
    eligible = {kind: posts for kind, posts in groups.items() if len(posts) >= 3}
    lines += ["", "## Three observations", "Counts below are cumulative at collection, for posts aged 7–60 days; unequal post ages still limit comparison.", ""]
    if not eligible:
        lines += ["1. Standout: unavailable — fewer than three posts with observed likes in any comparable format.",
                  "2. Typical performance: unavailable — insufficient same-format evidence.",
                  "3. Change: unavailable — no adequate current cohort to compare.", "", "## Next action",
                  "Collect at least three comparable own-channel posts with publication dates and observed metrics before proposing a performance-based test."]
        return lines

    kind, cohort = max(eligible.items(), key=lambda pair: (len(pair[1]), pair[0]))
    top = max(cohort, key=lambda row: row["likesCount"])
    typical = median(row["likesCount"] for row in cohort)
    ratio = f" ({top['likesCount'] / typical:.1f}× median)" if typical > 0 else " (median is zero; ratio unavailable)"
    lines.append(f"1. Standout in the largest comparable cohort ({kind}, n={len(cohort)}): {post_reference(top)}, published {post_date(top.get('timestamp'))}, has {top['likesCount']:,.0f} likes versus a {typical:,.0f} median{ratio}. Inspect its opening and scene; the counts do not explain why it performed this way.")
    summaries = []
    for format_name, posts in sorted(eligible.items()):
        comments = [value for row in posts if (value := observed_count(row.get("commentsCount"))) is not None]
        comment_text = f"{median(comments):,.0f} median comments (observed {len(comments)}/{len(posts)})" if comments else "comments unavailable"
        summaries.append(f"{format_name}: n={len(posts)}, {median(row['likesCount'] for row in posts):,.0f} median likes, {comment_text}")
    lines.append("2. Typical performance within each format: " + "; ".join(summaries) + ". These are descriptive baselines, not a format ranking.")

    change = "unavailable — no earlier snapshot."
    if len(candidates) > 1:
        previous_date, previous_path = candidates[-2]
        try:
            previous, _ = read_snapshot(previous_path)
            def key(row: dict) -> str:
                return str(row.get("id") or row.get("shortCode") or row.get("url"))
            lookup = {key(row): row for row in previous}
            changes = []
            for row in cohort:
                before = lookup.get(key(row))
                before_date = post_date(before.get("timestamp")) if before else None
                if before and before_date and before_date <= previous_date and before.get("type") == row.get("type"):
                    old = observed_count(before.get("likesCount"))
                    if old is not None:
                        changes.append(row["likesCount"] - old)
            if len(changes) >= 3:
                change = (f"{len(changes)} matched {kind} posts have a median net change of {median(changes):+,.0f} likes "
                          f"between {previous_date} and {collected} ([earlier snapshot]({previous_path})). "
                          "This measures count changes on the same posts, not improvement in new content.")
            else:
                change = f"unavailable — only {len(changes)} matched posts with observed likes in the earlier snapshot ({previous_date}); need at least three."
        except (OSError, ValueError):
            change = f"unavailable — earlier snapshot {previous_path.name} is unreadable."
    lines.append("3. What changed: " + change)
    lines += ["", "## One proposed experiment",
              f"Use the {kind} cohort above to choose a familiar format. Test whether showing a concrete couple action in the opening gets more response than opening with a reflective line. This is an untested creative hypothesis, not a pattern established by the counts.",
              f"Across four new {kind} posts, alternate action-first and line-first openings. Keep theme, length and posting conditions as similar as practical; use fresh moments. Treat the linked standout as a reference to inspect, not copy.",
              "Record each post's likes at seven days and compare the two pairs. Add sends/reach only if Insights supplies both for every post; otherwise leave that rate unavailable. Review after all four observations; mixed results are inconclusive, and this small comparison cannot establish causality.",
              "First step: refresh stale evidence if needed, then draft the two opening approaches for one fresh couple moment. This brief neither schedules nor publishes posts."]
    return lines


def build_brief(*, maintenance: bool = False, all_formats: bool = False) -> int:
    print("\n".join(performance_brief(ROOT, all_formats=all_formats)))
    latest_diagnostics = newest_glob("output/diagnostics/wiki-health-*.md")
    print_section("Repository status")
    print(f"Latest saved health: {status_from_diagnostics(latest_diagnostics)} ({relative(latest_diagnostics)}; not rerun by this brief).")
    if not maintenance:
        print("For workflow commands, active work and learning debt: python scripts/daily_creator_brief.py --maintenance")
        return 0

    latest_post_sprint = newest_glob("output/post-sprints/*/README.md")
    latest_report = newest_glob("output/reports/*.md")
    latest_prepost = newest_glob("output/prepost/*.md")
    ledger = ROOT / "memory" / "semantic" / "carousel-idea-preferences.md"
    engineering_prefs = ROOT / "memory" / "semantic" / "engineering-workflow-preferences.md"
    research_partner = load_research_partner_lens(ROOT)

    print("\n# Maintenance details")
    print(f"workspace: {ROOT}")

    print_section("Health")
    print(f"latest diagnostics: {relative(latest_diagnostics)}")
    print(f"status: {status_from_diagnostics(latest_diagnostics)}")
    print("run: make health NOTE=\"short summary of what changed\"")

    print_section("Latest Creative Surfaces")
    print(f"post sprint: {relative(latest_post_sprint)}")
    print(f"latest report: {relative(latest_report)}")
    print(f"latest prepost: {relative(latest_prepost)}")
    print("recent carousels:")
    carousel_days = recent_dirs(ROOT / "output" / "carousels", limit=3)
    carousel_packages: list[Path] = []
    for day in carousel_days:
        carousel_packages.extend(recent_dirs(day, limit=3))
    for package in sorted(carousel_packages, key=lambda item: item.stat().st_mtime, reverse=True)[:6]:
        print(f"- {relative(package)}")
    if not carousel_packages:
        print("- none found")

    print_section("Memory Flags")
    print(f"idea ledger: {relative(ledger)}")
    for line in fact_summaries(ledger, limit=7):
        print(f"- {line}")
    print(f"engineering prefs: {relative(engineering_prefs)}")
    for line in fact_summaries(engineering_prefs, limit=4):
        print(f"- {line}")

    print_section("Research Partner Lens")
    print(f"memory: {research_partner['path']} ({research_partner['status']})")
    rules = " ".join(research_partner["operating_rules"])
    print("- hypothesis: name the working bet before building")
    if "challenge" in rules.lower():
        print("- challenge: push back on weak or stale directions with repo evidence")
    else:
        print("- challenge: ask what weak idea or stale default should be challenged")
    if "durable" in rules.lower():
        print("- durable learning: write repeated learnings into memory, rules, skills, wiki, or tests")
    else:
        print("- durable learning: identify what should become memory if this works")

    print_section("Hypothesis Tracker")
    hypotheses = hypothesis_brief_records(ROOT, limit=5)
    for record in hypotheses:
        print(f"- {record['line']} [{record['path']}]")
    if not hypotheses:
        print("- no hypotheses captured yet")

    print_section("Recent Learning Loop")
    print("policy: proposal-only until approved/applied; no silent self-editing")
    records = recent_learning_records(ROOT, limit=5)
    for record in records:
        print(f"- {record['line']} [{record['path']}]")
    if not records:
        print("- no learning events or proposals yet")

    print_section("Learning Debt")
    debt = learning_debt_records(ROOT, limit=5)
    for record in debt:
        print(f"- {record['line']} [{record['path']}]")
    if not debt:
        print("- no unresolved learning debt")

    print_section("Next Commands")
    print("make idea-loop  # discover and verify one fresh Instagram concept")
    print("make jam MOMENT=\"specific couple moment\"")
    print("make prepost CONCEPT=\"planned Reel concept\"")
    print("make carousel STORY=\"source story\" TITLE=\"working title\"")
    print("make article CAROUSEL=output/carousels/YYYY-MM-DD/slug TITLE=\"working title\"")
    print("make publish-dry-run NOTE=\"scope check\" INCLUDE=\"path1 path2\"")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Show today's creator decisions from saved performance evidence.")
    parser.add_argument("--maintenance", action="store_true", help="Also show workflow commands, recent packages and learning debt.")
    parser.add_argument("--all-formats", action="store_true", help="Include Reel and single-image metrics; default focuses on carousels.")
    args = parser.parse_args()
    return build_brief(maintenance=args.maintenance, all_formats=args.all_formats)


if __name__ == "__main__":
    raise SystemExit(main())
