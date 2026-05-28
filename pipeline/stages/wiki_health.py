"""
Repo-wide wiki and memory health checks.

Carousel runs already have a quality spine. This module provides the missing
session/repo spine: deterministic linting, diagnostics, HEAL proposals, and an
episodic record that future sessions can read.
"""

from __future__ import annotations

import argparse
import json
import re
from datetime import date
from pathlib import Path
from typing import Any


ADVERTISED_PIPELINE_FILES = [
    "pipeline/runner.py",
    "pipeline/stages/a1_ingest.py",
    "pipeline/stages/a2_parser.py",
    "pipeline/stages/a3_analyzer.py",
    "pipeline/stages/a4_wiki.py",
    "pipeline/stages/a5_report.py",
]

INSTRUCTION_SURFACE_FILES = [
    "AGENTS.md",
    "CLAUDE.md",
]

REQUIRED_CLOSEOUT_PHRASES = [
    "scripts/autopublish.py",
    "scripts/wiki_health.py --write --fix-index",
]

REQUIRED_AGENTIC_OS_FILES = [
    "pipeline/agentic/__init__.py",
    "pipeline/agentic/contracts.py",
    "pipeline/agentic/context_loader.py",
    "pipeline/agentic/skill_registry.py",
    "pipeline/agentic/memory_index.py",
    "pipeline/agentic/recall.py",
    "pipeline/agentic/audit_log.py",
    "pipeline/agentic/learning_loop.py",
    "pipeline/agentic/skill_eval.py",
    "pipeline/agentic/workflow_metadata.py",
    "pipeline/agentic/workflow_state.py",
    "scripts/agentic_os.py",
    "config/agentic_context_manifest.json",
    "config/skill-systems.json",
    "docs/superpowers/specs/agentic-os-control-plane.md",
]

REQUIRED_MEMORY_SURFACE = {
    "wiki_index": "wiki/index.md",
    "wiki_themes": "wiki/themes",
    "wiki_insights": "wiki/insights",
    "wiki_posts": "wiki/posts",
    "wiki_people": "wiki/people",
    "working_memory": "memory/working.md",
    "semantic_memory": "memory/semantic",
    "episodic_memory": "memory/episodic",
    "graph_memory": "memory/graph.json",
    "logs": "logs",
}

WIKI_REQUIRED_METADATA = ["last_updated", "confidence", "sources"]


def normalize_instruction_text(text: str) -> str:
    return re.sub(r"\s+", " ", text)


def instruction_has_phrase(text: str, phrase: str) -> bool:
    normalized_text = normalize_instruction_text(text)
    normalized_phrase = normalize_instruction_text(phrase)
    return normalized_phrase in normalized_text


def instruction_surface_evidence(root: Path) -> dict[str, Any]:
    missing_files: list[str] = []
    missing_phrases: dict[str, list[str]] = {}
    for relative in INSTRUCTION_SURFACE_FILES:
        path = root / relative
        if not path.exists():
            missing_files.append(relative)
            missing_phrases[relative] = list(REQUIRED_CLOSEOUT_PHRASES)
            continue
        text = path.read_text(encoding="utf-8")
        absent = [
            phrase
            for phrase in REQUIRED_CLOSEOUT_PHRASES
            if not instruction_has_phrase(text, phrase)
        ]
        if absent:
            missing_phrases[relative] = absent
    return {
        "required_files": INSTRUCTION_SURFACE_FILES,
        "required_phrases": REQUIRED_CLOSEOUT_PHRASES,
        "missing_files": missing_files,
        "missing_phrases": missing_phrases,
    }


def relative_path(path: Path, root: Path) -> str:
    try:
        return path.relative_to(root).as_posix()
    except ValueError:
        return path.as_posix()


def wiki_pages(root: Path) -> list[Path]:
    wiki_root = root / "wiki"
    if not wiki_root.exists():
        return []
    return sorted(
        path
        for path in wiki_root.rglob("*.md")
        if path.name != "index.md"
    )


def md_files(root: Path, directory: str) -> list[Path]:
    base = root / directory
    if not base.exists():
        return []
    return sorted(path for path in base.rglob("*.md") if path.is_file())


def metadata_missing(path: Path) -> list[str]:
    text = path.read_text(encoding="utf-8")
    missing = []
    for key in WIKI_REQUIRED_METADATA:
        if key == "sources":
            if "sources:" not in text or not re.search(r"(?m)^sources:\s*\n(?:-\s+.+\n?)+", text):
                missing.append(key)
        elif not re.search(rf"(?m)^{re.escape(key)}:\s*.+$", text):
            missing.append(key)
    return missing


def declared_total_pages(index_text: str) -> int | None:
    match = re.search(r"(?m)^total_pages:\s*(\d+)\s*$", index_text)
    if not match:
        return None
    return int(match.group(1))


def make_check(
    check_id: str,
    status: str,
    severity: str,
    message: str,
    evidence: Any,
) -> dict[str, Any]:
    return {
        "id": check_id,
        "status": status,
        "severity": severity,
        "message": message,
        "evidence": evidence,
    }


def collect_wiki_health(root: Path, today: date | None = None) -> dict[str, Any]:
    root = root.resolve()
    today = today or date.today()
    checks: list[dict[str, Any]] = []

    missing_surface = [
        path
        for path in REQUIRED_MEMORY_SURFACE.values()
        if not (root / path).exists()
    ]
    checks.append(
        make_check(
            "memory_surface",
            "FAIL" if missing_surface else "PASS",
            "critical" if missing_surface else "info",
            "Required wiki, memory, graph, and log surfaces exist.",
            {"missing": missing_surface},
        )
    )

    missing_pipeline = [
        path
        for path in ADVERTISED_PIPELINE_FILES
        if not (root / path).exists()
    ]
    checks.append(
        make_check(
            "advertised_pipeline_files",
            "FAIL" if missing_pipeline else "PASS",
            "critical" if missing_pipeline else "info",
            "AGENTS/CLAUDE advertised pipeline entry points exist.",
            {"missing": missing_pipeline},
        )
    )

    instruction_evidence = instruction_surface_evidence(root)
    instruction_drift = bool(
        instruction_evidence["missing_files"]
        or instruction_evidence["missing_phrases"]
    )
    checks.append(
        make_check(
            "instruction_surface_sync",
            "FAIL" if instruction_drift else "PASS",
            "critical" if instruction_drift else "info",
            "AGENTS.md and CLAUDE.md share the required health and autopublish closeout commands.",
            instruction_evidence,
        )
    )

    missing_agentic = [
        path
        for path in REQUIRED_AGENTIC_OS_FILES
        if not (root / path).exists()
    ]
    checks.append(
        make_check(
            "agentic_os_surface",
            "FAIL" if missing_agentic else "PASS",
            "critical" if missing_agentic else "info",
            "Agentic OS control-plane files exist and are available to future sessions.",
            {"required": REQUIRED_AGENTIC_OS_FILES, "missing": missing_agentic},
        )
    )

    index_path = root / "wiki" / "index.md"
    pages = wiki_pages(root)
    if index_path.exists():
        index_text = index_path.read_text(encoding="utf-8")
        declared = declared_total_pages(index_text)
        checks.append(
            make_check(
                "wiki_index_total_pages",
                "FAIL" if declared != len(pages) else "PASS",
                "major" if declared != len(pages) else "info",
                "wiki/index.md total_pages matches actual wiki page count.",
                {"declared": declared, "actual": len(pages)},
            )
        )
    else:
        checks.append(
            make_check(
                "wiki_index_total_pages",
                "FAIL",
                "critical",
                "wiki/index.md exists and declares total_pages.",
                {"declared": None, "actual": len(pages)},
            )
        )

    missing_metadata = {
        relative_path(path, root): missing
        for path in pages
        if (missing := metadata_missing(path))
    }
    checks.append(
        make_check(
            "wiki_markdown_metadata",
            "FAIL" if missing_metadata else "PASS",
            "major" if missing_metadata else "info",
            "Every wiki page has last_updated, confidence, and sources metadata.",
            missing_metadata,
        )
    )

    semantic_missing_confidence = {
        relative_path(path, root): ["confidence"]
        for path in md_files(root, "memory/semantic")
        if not re.search(r"(?m)^confidence:\s*(0(?:\.\d+)?|1(?:\.0+)?)\s*$", path.read_text(encoding="utf-8"))
    }
    checks.append(
        make_check(
            "semantic_memory_confidence",
            "FAIL" if semantic_missing_confidence else "PASS",
            "major" if semantic_missing_confidence else "info",
            "Semantic memory markdown files carry confidence scores.",
            semantic_missing_confidence,
        )
    )

    episodic_records = md_files(root, "memory/episodic")
    checks.append(
        make_check(
            "episodic_records",
            "WARN" if not episodic_records else "PASS",
            "major" if not episodic_records else "info",
            "Episodic memory has at least one permanent session record.",
            {"count": len(episodic_records)},
        )
    )

    logs = sorted((root / "logs").glob("*")) if (root / "logs").exists() else []
    checks.append(
        make_check(
            "session_logs",
            "WARN" if not logs else "PASS",
            "minor" if not logs else "info",
            "Session/log directory has written diagnostics.",
            {"count": len(logs)},
        )
    )

    status = "PASS"
    if any(check["status"] == "FAIL" for check in checks):
        status = "NEEDS_HEAL"
    elif any(check["status"] == "WARN" for check in checks):
        status = "PASS_WITH_WARNINGS"

    return {
        "schema_version": "1.0",
        "date": str(today),
        "workspace": str(root),
        "status": status,
        "summary": {
            "checks": len(checks),
            "failures": sum(check["status"] == "FAIL" for check in checks),
            "warnings": sum(check["status"] == "WARN" for check in checks),
            "wiki_pages": len(pages),
        },
        "checks": checks,
    }


def replace_or_insert_metadata(text: str, key: str, value: str) -> str:
    pattern = rf"(?m)^{re.escape(key)}:\s*.*$"
    replacement = f"{key}: {value}"
    if re.search(pattern, text):
        return re.sub(pattern, replacement, text, count=1)
    lines = text.splitlines()
    insert_at = 1 if lines and lines[0].startswith("#") else 0
    lines.insert(insert_at, replacement)
    return "\n".join(lines) + "\n"


def repair_wiki_index_metadata(root: Path, today: date | None = None) -> None:
    root = root.resolve()
    today = today or date.today()
    index_path = root / "wiki" / "index.md"
    index_path.parent.mkdir(parents=True, exist_ok=True)
    if index_path.exists():
        text = index_path.read_text(encoding="utf-8")
    else:
        text = "# Wiki Index\n\n"
    text = replace_or_insert_metadata(text, "last_updated", str(today))
    text = replace_or_insert_metadata(text, "total_pages", str(len(wiki_pages(root))))
    index_path.write_text(text, encoding="utf-8")


def markdown_table_row(values: list[str]) -> str:
    return "| " + " | ".join(value.replace("\n", " ") for value in values) + " |"


def health_markdown(health: dict[str, Any]) -> str:
    lines = [
        "# Wiki Health Diagnostics",
        "",
        f"last_updated: {health['date']}",
        "confidence: 0.82",
        "sources:",
        "- AGENTS.md",
        "- CLAUDE.md",
        "- wiki/index.md",
        "- memory/working.md",
        "- memory/graph.json",
        "",
        "## Status",
        "",
        f"Status: {health['status']}",
        f"Failures: {health['summary']['failures']}",
        f"Warnings: {health['summary']['warnings']}",
        f"Wiki pages: {health['summary']['wiki_pages']}",
        "",
        "## Checks",
        "",
        markdown_table_row(["Check", "Status", "Severity", "Message"]),
        markdown_table_row(["---", "---", "---", "---"]),
    ]
    for check in health["checks"]:
        lines.append(
            markdown_table_row(
                [
                    check["id"],
                    check["status"],
                    check["severity"],
                    check["message"],
                ]
            )
        )
    lines.extend(["", "## Evidence", ""])
    for check in health["checks"]:
        lines.extend(
            [
                f"### {check['id']}",
                "",
                "```json",
                json.dumps(check["evidence"], indent=2, ensure_ascii=False),
                "```",
                "",
            ]
        )
    return "\n".join(lines)


def heal_proposal_markdown(health: dict[str, Any]) -> str:
    actionable = [
        check for check in health["checks"] if check["status"] in {"FAIL", "WARN"}
    ]
    lines = [
        "# HEAL Proposal - Wiki Health",
        "",
        f"last_updated: {health['date']}",
        "confidence: 0.78",
        "sources:",
        "- output/diagnostics/wiki-health report",
        "- AGENTS.md architecture contract",
        "- repository filesystem scan",
        "",
        "## Hypothesis",
        "",
        "Repeated project setup failures are happening because the repo has C-layer carousel quality checks but no repo-wide session-close gate for wiki health, episodic memory, stale index metadata, advertised pipeline drift, or repair proposals.",
        "",
        "## Evidence",
        "",
    ]
    if actionable:
        for check in actionable:
            lines.append(f"- {check['id']}: {check['status']} - {check['message']}")
    else:
        lines.append("- No failing checks in the latest run.")
    lines.extend(["", "## Action", ""])
    if actionable:
        for check in actionable:
            lines.append(f"- Repair `{check['id']}` and rerun `venv/bin/python scripts/wiki_health.py --write --fix-index`.")
    else:
        lines.append("- Keep running the health check at session close.")
    lines.extend(
        [
            "",
            "## Learning",
            "",
            "A session should not be considered closed until diagnostics, a HEAL proposal when needed, an episodic record, and a log entry exist.",
            "",
        ]
    )
    return "\n".join(lines)


def episode_markdown(health: dict[str, Any], session_note: str) -> str:
    note = session_note or "Wiki health check run."
    lines = [
        "# Session Health Episode",
        "",
        f"last_updated: {health['date']}",
        "confidence: 0.8",
        "sources:",
        "- scripts/wiki_health.py",
        "- output/diagnostics/wiki-health report",
        "",
        "## Session Note",
        "",
        note,
        "",
        "## Outcome",
        "",
        f"- status: {health['status']}",
        f"- failures: {health['summary']['failures']}",
        f"- warnings: {health['summary']['warnings']}",
        "",
    ]
    return "\n".join(lines)


def log_text(health: dict[str, Any]) -> str:
    return "\n".join(
        [
            f"date={health['date']}",
            f"status={health['status']}",
            f"failures={health['summary']['failures']}",
            f"warnings={health['summary']['warnings']}",
            f"wiki_pages={health['summary']['wiki_pages']}",
            "",
        ]
    )


def write_health_artifacts(
    root: Path,
    health: dict[str, Any],
    today: date | None = None,
    session_note: str = "",
) -> dict[str, Path]:
    root = root.resolve()
    today = today or date.fromisoformat(health["date"])
    stamp = str(today)
    paths = {
        "diagnostics": root / "output" / "diagnostics" / f"wiki-health-{stamp}.md",
        "heal_proposal": root / "memory" / "heal" / "proposals" / f"{stamp}-wiki-health.md",
        "episode": unique_path(root / "memory" / "episodic" / f"{stamp}-session-health.md"),
        "log": unique_path(root / "logs" / f"{stamp}-wiki-health.log"),
    }
    for path in paths.values():
        path.parent.mkdir(parents=True, exist_ok=True)

    paths["diagnostics"].write_text(health_markdown(health), encoding="utf-8")
    paths["heal_proposal"].write_text(heal_proposal_markdown(health), encoding="utf-8")
    paths["episode"].write_text(episode_markdown(health, session_note), encoding="utf-8")
    paths["log"].write_text(log_text(health), encoding="utf-8")

    refreshed_health = collect_wiki_health(root, today=today)
    paths["diagnostics"].write_text(health_markdown(refreshed_health), encoding="utf-8")
    paths["heal_proposal"].write_text(heal_proposal_markdown(refreshed_health), encoding="utf-8")
    paths["episode"].write_text(episode_markdown(refreshed_health, session_note), encoding="utf-8")
    paths["log"].write_text(log_text(refreshed_health), encoding="utf-8")
    return paths


def unique_path(path: Path) -> Path:
    if not path.exists():
        return path
    for index in range(2, 1000):
        candidate = path.with_name(f"{path.stem}-{index}{path.suffix}")
        if not candidate.exists():
            return candidate
    raise RuntimeError(f"Could not find a unique path for {path}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Lint wiki/memory health and write session diagnostics.")
    parser.add_argument("--workspace-root", type=Path, default=Path.cwd())
    parser.add_argument("--write", action="store_true", help="Write diagnostics, HEAL proposal, episode, and log files.")
    parser.add_argument("--fix-index", action="store_true", help="Repair wiki/index.md last_updated and total_pages metadata before checking.")
    parser.add_argument("--session-note", default="", help="Short note to include in memory/episodic.")
    args = parser.parse_args(argv)

    today = date.today()
    if args.fix_index:
        repair_wiki_index_metadata(args.workspace_root, today=today)
    health = collect_wiki_health(args.workspace_root, today=today)
    if args.write:
        paths = write_health_artifacts(
            args.workspace_root,
            health,
            today=today,
            session_note=args.session_note,
        )
        for name, path in paths.items():
            print(f"{name}: {path}")
    print(f"wiki health: {health['status']} ({health['summary']['failures']} failures, {health['summary']['warnings']} warnings)")
    return 1 if health["status"] == "NEEDS_HEAL" else 0


if __name__ == "__main__":
    raise SystemExit(main())
