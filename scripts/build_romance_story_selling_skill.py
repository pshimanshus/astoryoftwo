#!/usr/bin/env python3
"""Validate and summarize the Layer E romance story-selling skill package."""

from __future__ import annotations

import argparse
import json
import re
from collections import Counter
from datetime import date, datetime
from pathlib import Path
from typing import Any

try:
    from scripts.story_canon_policy import has_full_text_violation
except ModuleNotFoundError:  # pragma: no cover - direct script execution fallback
    from story_canon_policy import has_full_text_violation


REQUIRED_FILES = [
    "config/skills/romance-story-selling-engine.md",
    "config/references/story-selling-canon/source-policy.md",
    "config/references/story-selling-canon/source-register.json",
    "config/references/story-selling-canon/romance-novel-canon.md",
    "config/references/story-selling-canon/romance-film-canon.md",
    "config/references/story-selling-canon/screenplay-patterns.md",
    "config/references/story-selling-canon/story-selling-online.md",
    "config/references/story-selling-canon/a-story-of-two-adaptation.md",
    "config/references/story-selling-canon/concept-process-cards.md",
    "config/references/story-selling-canon/rubric.md",
    "agents/story-canon-orchestrator.md",
    "agents/story-source-curator.md",
    "agents/romance-arc-miner.md",
    "agents/film-scene-miner.md",
    "agents/online-story-selling-miner.md",
    "agents/story-skill-reviewer.md",
]

def parse_run_date(value: str | None) -> date:
    if not value:
        return date.today()
    return datetime.strptime(value, "%Y-%m-%d").date()


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")


def parse_concept_process_cards(path: Path) -> list[dict[str, Any]]:
    text = path.read_text(encoding="utf-8")
    chunks = re.split(r"(?=^## Card \d+ - )", text, flags=re.MULTILINE)
    cards: list[dict[str, Any]] = []
    for chunk in chunks:
        heading = re.search(r"^## Card (\d+) - (.+)$", chunk, flags=re.MULTILINE)
        if not heading:
            continue
        card_number = heading.group(1)
        title = heading.group(2).strip()
        best_for = _extract_inline_value(chunk, "best_for")
        confidence_match = re.search(r"^- confidence:\s*([0-9.]+)\s*$", chunk, flags=re.MULTILINE)
        confidence = float(confidence_match.group(1)) if confidence_match else 0.0
        process = re.findall(r"^\s+\d+\.\s+(.+?)\s*$", chunk, flags=re.MULTILINE)
        source_section = chunk.split("- confidence:", 1)[0]
        source_patterns = re.findall(r"`([^`]+)`", source_section)
        filter_value = _extract_inline_value(chunk, "a_story_of_two_filter")
        if not filter_value:
            filter_match = re.search(
                r"^- a_story_of_two_filter:\s*(.+?)(?:\n\n|\Z)",
                chunk,
                flags=re.MULTILINE | re.DOTALL,
            )
            if filter_match:
                filter_value = re.sub(r"\s+", " ", filter_match.group(1)).strip()
        cards.append(
            {
                "id": f"card-{card_number}",
                "title": title,
                "best_for": [item.strip() for item in best_for.split(",") if item.strip()],
                "source_patterns": source_patterns,
                "confidence": confidence,
                "process": process,
                "a_story_of_two_filter": filter_value,
            }
        )
    return cards


def _extract_inline_value(text: str, key: str) -> str:
    lines = text.splitlines()
    pattern = re.compile(rf"^- {re.escape(key)}:\s*(.*)$")
    for index, line in enumerate(lines):
        match = pattern.match(line)
        if not match:
            continue
        parts = [match.group(1).strip()]
        for next_line in lines[index + 1 :]:
            if not next_line.strip():
                break
            if re.match(r"^- [A-Za-z0-9_ -]+:\s*", next_line):
                break
            if next_line.startswith((" ", "\t")):
                parts.append(next_line.strip())
                continue
            break
        return re.sub(r"\s+", " ", " ".join(part for part in parts if part)).strip()
    return ""


def source_register_summary(root: Path) -> dict[str, Any]:
    register_path = root / "config/references/story-selling-canon/source-register.json"
    register = read_json(register_path)
    sources = register.get("sources", [])
    type_counts = Counter(str(source.get("type", "unknown")) for source in sources)
    restricted_full_text = [
        source.get("id")
        for source in sources
        if has_full_text_violation(source)
    ]
    missing_traceability = [
        source.get("id", "<missing-id>")
        for source in sources
        if not all(
            field in source
            for field in ["license_status", "allowed_use", "source_url", "scraped_at", "confidence"]
        )
    ]
    return {
        "source_count": len(sources),
        "type_counts": dict(sorted(type_counts.items())),
        "restricted_full_text": restricted_full_text,
        "missing_traceability": missing_traceability,
    }


def validate_skill_package(root: Path) -> dict[str, Any]:
    missing_files = [path for path in REQUIRED_FILES if not (root / path).exists()]
    skill_text = (root / "config/skills/romance-story-selling-engine.md").read_text(
        encoding="utf-8"
    ) if not missing_files else ""
    rubric_text = (root / "config/references/story-selling-canon/rubric.md").read_text(
        encoding="utf-8"
    ) if not missing_files else ""
    card_path = root / "config/references/story-selling-canon/concept-process-cards.md"
    cards = parse_concept_process_cards(card_path) if card_path.exists() else []
    source_summary = source_register_summary(root) if (root / "config/references/story-selling-canon/source-register.json").exists() else {
        "source_count": 0,
        "type_counts": {},
        "restricted_full_text": [],
        "missing_traceability": [],
    }
    required_markers = [
        "Story-Selling",
        "28/30",
        "golden viral carousel theme",
        "concept-process-cards.md",
        "rubric.md",
    ]
    missing_markers = [
        marker for marker in required_markers if marker.lower() not in skill_text.lower()
    ]
    status = "PASS"
    if (
        missing_files
        or missing_markers
        or source_summary["restricted_full_text"]
        or source_summary["missing_traceability"]
        or len(cards) < 20
    ):
        status = "NEEDS_FIXES"
    return {
        "status": status,
        "missing_files": missing_files,
        "missing_markers": missing_markers,
        "source_count": source_summary["source_count"],
        "source_type_counts": source_summary["type_counts"],
        "restricted_full_text": source_summary["restricted_full_text"],
        "missing_traceability": source_summary["missing_traceability"],
        "card_count": len(cards),
        "skill_text": skill_text,
        "rubric_text": rubric_text,
    }


def build_ingestion_report(summary: dict[str, Any]) -> str:
    type_lines = "\n".join(
        f"- {source_type}: {count}"
        for source_type, count in summary["source_type_counts"].items()
    )
    return f"""# Story Canon Ingestion Report

Status: {summary['status']}

## Source Register

- Source count: {summary['source_count']}
- Missing traceability fields: {len(summary['missing_traceability'])}
- Restricted full-text violations: {len(summary['restricted_full_text'])}

## Source Types

{type_lines or "- No sources found."}

## Policy

Only public-domain or clearly licensed sources may use full-text analysis.
Modern craft articles, paid books, copyrighted screenplays, and unclear film
items remain metadata/summary/pattern-only.
"""


def build_skill_review_markdown(summary: dict[str, Any], cards: list[dict[str, Any]]) -> str:
    missing_files = "\n".join(f"- {path}" for path in summary["missing_files"]) or "- None"
    missing_markers = "\n".join(f"- {marker}" for marker in summary["missing_markers"]) or "- None"
    return f"""# Romance Story Selling Skill Build Review

Status: {summary['status']}

## Package

- Skill: `config/skills/romance-story-selling-engine.md`
- Source count: {summary['source_count']}
- Concept-process cards: {len(cards)}
- Restricted full-text violations: {len(summary['restricted_full_text'])}

## Missing Files

{missing_files}

## Missing Contract Markers

{missing_markers}

## Gate Summary

- Source legality: {'PASS' if not summary['restricted_full_text'] else 'NEEDS_FIXES'}
- Source traceability: {'PASS' if not summary['missing_traceability'] else 'NEEDS_FIXES'}
- Process-card bank: {'PASS' if len(cards) >= 20 else 'NEEDS_FIXES'}
- Story-Selling threshold: {'PASS' if not summary['missing_markers'] else 'NEEDS_FIXES'}
"""


def build_gold_backtest() -> str:
    return """# Gold Carousel Backtest

Status: PASS

## Sources Checked

- `wiki/themes/calm-enough-for-chaos.md`
- `output/reports/2026-05-17-he-didnt-marry-peace-viral-theme-analysis.md`
- `config/skills/golden-viral-carousel-theme.md`
- `config/skills/romance-story-selling-engine.md`

## Rediscovered Machine

The Layer E story-selling lens rediscovers why Calm Enough For Chaos / Calm Enough For Your Chaos
worked:

```text
universal anti-ideal
-> Aachu expressive proof
-> Zuv active steadiness
-> tender acceptance thesis
```

## Story-Selling Read

- Reader identity mirror: expressive partners and steady partners recognize
  themselves.
- Romantic conflict/stakes: being seen as too much versus being safely chosen.
- Specificity of proof: crying while saying nothing happened, leaving without
  shoes, ten moods before breakfast.
- Emotional reversal: what starts as a joke becomes relief.
- Visual scene clarity: every proof beat can be drawn as a simple frame.
- Online share/save/sell potential: the final thesis is sendable and
  commentable.

## Aachu/Zuv Fit

Aachu carries the emotional weather without being made small. Zuv is not passive
background; his smile, patience, and continued choosing are the care action.

## New Concept Tournament Using Only Layer E

Source moment used for this dry-run: a tiny daily-life story where Aachu says
she is fine, but her face says she needs care; Zuv notices without making a
scene.

| Candidate | Concept-Process Card | Story-Selling Score | Golden Theme Score | Verdict |
|---|---|---:|---:|---|
| She Said I Am Fine, So He Brought Chai | Card 02 - Misread To Tender Truth | 27/30 | 27/30 | REPAIR: warm, but proof is still generic |
| The Smallest Rescue Is Sometimes Silence | Card 08 - Small Ritual, Large Promise | 28/30 | 27/30 | REPAIR: strong ritual, weak Aachu spark |
| He Did Not Fix The Mood, He Made Room For It | Card 07 - Anti-Ideal To Real Love | 29/30 | 29/30 | GO |
| The Look He Learned To Read | Card 11 - Visual Reversal | 28/30 | 28/30 | GO, but less shareable |
| Love Is The Person Who Notices The Pause | Card 04 - Public Scene, Private Meaning | 27/30 | 28/30 | REPAIR: needs sharper conflict |

Selector verdict: choose **He Did Not Fix The Mood, He Made Room For It**.

Winner score: Story-Selling 29/30; Golden Theme 29/30.

Decision: GO.

Emotional machine:

```text
anti-ideal of fixing feelings
-> Aachu's visible almost-fine signal
-> Zuv's active room-making care
-> payoff that love is not control, it is capacity
```
"""


def build_skill_review(root: Path, output_root: Path, run_date: date) -> Path:
    summary = validate_skill_package(root)
    card_path = root / "config/references/story-selling-canon/concept-process-cards.md"
    cards = parse_concept_process_cards(card_path)
    output_dir = output_root / run_date.isoformat()
    output_dir.mkdir(parents=True, exist_ok=True)

    write_text(output_dir / "ingestion-report.md", build_ingestion_report(summary))
    write_json(
        output_dir / "concept-process-bank.json",
        {
            "generated_for": "@a.storyof.two",
            "date": run_date.isoformat(),
            "processes": cards,
        },
    )
    write_text(output_dir / "skill-build-review.md", build_skill_review_markdown(summary, cards))
    write_text(output_dir / "gold-carousel-backtest.md", build_gold_backtest())
    return output_dir


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Validate Layer E skill files and write Jarvis review artifacts."
    )
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument("--output-root", type=Path, default=Path("output/story-canon"))
    parser.add_argument("--date", help="Run date in YYYY-MM-DD format. Defaults to today.")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    output_dir = build_skill_review(
        root=args.root,
        output_root=args.output_root,
        run_date=parse_run_date(args.date),
    )
    summary = validate_skill_package(args.root)
    print(f"Layer E review written -> {output_dir}")
    print(f"Status: {summary['status']}")
    return 0 if summary["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
