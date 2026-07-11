#!/usr/bin/env python3
"""Print a local creator/engineering command brief for @a.storyof.two."""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


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


def build_brief() -> int:
    latest_diagnostics = newest_glob("output/diagnostics/wiki-health-*.md")
    latest_post_sprint = newest_glob("output/post-sprints/*/README.md")
    latest_report = newest_glob("output/reports/*.md")
    latest_prepost = newest_glob("output/prepost/*.md")
    ledger = ROOT / "memory" / "semantic" / "carousel-idea-preferences.md"
    engineering_prefs = ROOT / "memory" / "semantic" / "engineering-workflow-preferences.md"
    research_partner = load_research_partner_lens(ROOT)

    print("# AI Command Center Brief")
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
    print("make jam MOMENT=\"specific couple moment\"")
    print("make prepost CONCEPT=\"planned Reel concept\"")
    print("make carousel STORY=\"source story\" TITLE=\"working title\"")
    print("make article CAROUSEL=output/carousels/YYYY-MM-DD/slug TITLE=\"working title\"")
    print("make publish-dry-run NOTE=\"scope check\" INCLUDE=\"path1 path2\"")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Show today's local AI command-center brief.")
    parser.parse_args()
    return build_brief()


if __name__ == "__main__":
    raise SystemExit(main())
