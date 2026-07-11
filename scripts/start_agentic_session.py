#!/usr/bin/env python3
"""Hard session takeover command for Agentic OS-backed work."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from pipeline.agentic.context_loader import assemble_context_pack  # noqa: E402
from pipeline.agentic.recall import build_recall_bundle  # noqa: E402
from pipeline.agentic.skill_registry import load_skill_systems, resolve_skill_system  # noqa: E402
from pipeline.stages.wiki_health import collect_wiki_health  # noqa: E402


RESEARCH_PARTNER_MEMORY = Path("memory/semantic/engineering-workflow-preferences.md")
RESEARCH_PARTNER_QUESTIONS = [
    "What does memory say has worked?",
    "What recently failed or drifted?",
    "What hypothesis are we testing next?",
    "What weak idea or stale default should be challenged?",
    "What learning would become durable if this works?",
]


def run_git_status(root: Path) -> dict[str, Any]:
    result = subprocess.run(
        ["git", "status", "--short", "--branch"],
        cwd=root,
        text=True,
        capture_output=True,
        check=False,
    )
    if result.returncode != 0:
        return {
            "status": "git_unavailable",
            "returncode": result.returncode,
            "stderr": result.stderr.strip(),
        }
    lines = [line for line in result.stdout.splitlines() if line.strip()]
    dirty = [line for line in lines if not line.startswith("## ")]
    return {
        "status": "dirty" if dirty else "clean",
        "lines": lines,
        "dirty_count": len(dirty),
    }


def unique_intent_path(root: Path) -> Path:
    base = root / "memory" / "episodic"
    base.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y-%m-%d-session-intent")
    path = base / f"{stamp}.json"
    if not path.exists():
        return path
    for index in range(2, 1000):
        candidate = base / f"{stamp}-{index}.json"
        if not candidate.exists():
            return candidate
    raise RuntimeError("Could not allocate unique session intent path.")


def load_research_partner_lens(root: Path) -> dict[str, Any]:
    relative = RESEARCH_PARTNER_MEMORY.as_posix()
    path = root / RESEARCH_PARTNER_MEMORY
    if not path.exists():
        return {
            "status": "missing",
            "path": relative,
            "session_questions": RESEARCH_PARTNER_QUESTIONS,
            "operating_rules": [],
        }

    rules: list[str] = []
    fallback_rules: list[str] = []
    in_partner_behavior = False
    for raw_line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        line = raw_line.strip()
        if line.lower().startswith("the partner behavior is"):
            in_partner_behavior = True
            continue
        if in_partner_behavior and line.startswith("## "):
            break
        if line.startswith("- "):
            rule = line.removeprefix("- ").rstrip(";.")
            if in_partner_behavior:
                rules.append(rule)
            else:
                fallback_rules.append(rule)
        if len(rules) >= 6:
            break
    if not rules:
        rules = fallback_rules[:6]

    return {
        "status": "loaded",
        "path": relative,
        "session_questions": RESEARCH_PARTNER_QUESTIONS,
        "operating_rules": rules,
    }


def build_session_takeover(
    root: Path,
    *,
    skill_system_name: str,
    intent: str,
    profile: str | None = None,
    recall_query: str | None = None,
) -> dict[str, Any]:
    root = root.resolve()
    context_status: dict[str, Any]
    try:
        context = assemble_context_pack(root, profile=profile)
        context_status = {
            "status": "loaded",
            "profile": context.profile,
            "estimated_tokens": context.estimated_tokens,
            "sections": [section.path for section in context.sections],
        }
    except Exception as exc:  # noqa: BLE001 - startup should report every surface.
        context_status = {"status": "unavailable", "reason": str(exc)}

    try:
        skill_system = resolve_skill_system(load_skill_systems(root), skill_system_name)
    except Exception as exc:  # noqa: BLE001
        skill_system = {"name": skill_system_name, "status": "unavailable", "reason": str(exc)}

    query = recall_query or intent or skill_system_name
    try:
        recall = build_recall_bundle(root, query, profile=profile)
        recall_status = {
            "status": "loaded",
            "query": recall.query,
            "hit_count": len(recall.hits),
            "hits": [hit.path for hit in recall.hits[:8]],
        }
    except Exception as exc:  # noqa: BLE001
        recall_status = {"status": "unavailable", "query": query, "reason": str(exc)}

    dirty_git_state = run_git_status(root)
    wiki_health = collect_wiki_health(root)
    creative_work_blocked = wiki_health["status"] == "NEEDS_HEAL"
    research_partner = load_research_partner_lens(root)
    payload = {
        "schema_version": "1.0",
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "intent": intent,
        "skill_system": skill_system,
        "context": context_status,
        "recall": recall_status,
        "research_partner": research_partner,
        "dirty_git_state": dirty_git_state,
        "wiki_health": {
            "status": wiki_health["status"],
            "failures": wiki_health["summary"]["failures"],
            "warnings": wiki_health["summary"]["warnings"],
        },
        "creative_work_blocked": creative_work_blocked,
        "block_reason": "wiki_health_needs_heal" if creative_work_blocked else "",
    }
    intent_path = unique_intent_path(root)
    intent_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    payload["session_intent_path"] = intent_path.relative_to(root).as_posix()
    intent_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return payload


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workspace-root", type=Path, default=ROOT)
    parser.add_argument("--skill-system", required=True)
    parser.add_argument("--intent", required=True)
    parser.add_argument("--profile")
    parser.add_argument("--recall-query")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    payload = build_session_takeover(
        args.workspace_root,
        skill_system_name=args.skill_system,
        intent=args.intent,
        profile=args.profile,
        recall_query=args.recall_query,
    )
    print(json.dumps(payload, indent=2, ensure_ascii=False))
    return 2 if payload["creative_work_blocked"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
