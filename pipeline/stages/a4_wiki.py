"""A4 wiki builder: promote the latest analysis into wiki and memory."""

from __future__ import annotations

import argparse
from datetime import date
from pathlib import Path

from pipeline.stages.a2_parser import latest_file
from pipeline.stages.wiki_health import repair_wiki_index_metadata


def replace_section(text: str, header: str, replacement: str) -> str:
    start = text.find(header)
    if start == -1:
        return text.rstrip() + "\n\n" + replacement.rstrip() + "\n"
    next_start = text.find("\n## ", start + len(header))
    if next_start == -1:
        return text[:start].rstrip() + "\n\n" + replacement.rstrip() + "\n"
    return text[:start].rstrip() + "\n\n" + replacement.rstrip() + "\n" + text[next_start:].lstrip()


def build_latest_analysis_page(analysis_path: Path, today: date) -> str:
    return "\n".join(
        [
            "# Latest Corpus Analysis",
            "",
            f"last_updated: {today}",
            "confidence: 0.72",
            "sources:",
            f"- {analysis_path}",
            "",
            "## Summary",
            "",
            "The latest A3 report has been promoted into the wiki index cycle.",
            "",
            "## Artifact",
            "",
            f"- {analysis_path}",
            "",
        ]
    )


def update_working_memory(root: Path, analysis_path: Path, today: date) -> None:
    memory_path = root / "memory" / "working.md"
    memory_path.parent.mkdir(parents=True, exist_ok=True)
    text = memory_path.read_text(encoding="utf-8") if memory_path.exists() else "# Working Memory\n"
    section = "\n".join(
        [
            "## A-layer wiki compile",
            f"- date: {today}",
            f"- report: {analysis_path}",
            "- status: latest analysis promoted to wiki/insights/latest-analysis.md",
            "",
        ]
    )
    memory_path.write_text(replace_section(text, "## A-layer wiki compile", section), encoding="utf-8")


def run(root: Path | None = None, analysis_path: Path | None = None, today: date | None = None) -> Path:
    root = (root or Path.cwd()).resolve()
    today = today or date.today()
    analysis_path = analysis_path or latest_file(root / "output" / "reports", "*-analysis.md")
    insight_path = root / "wiki" / "insights" / "latest-analysis.md"
    insight_path.parent.mkdir(parents=True, exist_ok=True)
    insight_path.write_text(build_latest_analysis_page(analysis_path, today), encoding="utf-8")
    update_working_memory(root, analysis_path, today)
    repair_wiki_index_metadata(root, today=today)
    return insight_path


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="A4 compile latest analysis into wiki and memory.")
    parser.add_argument("--analysis-path", type=Path)
    parser.add_argument("--workspace-root", type=Path, default=Path.cwd())
    args = parser.parse_args(argv)

    out_path = run(root=args.workspace_root, analysis_path=args.analysis_path)
    print(out_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
