"""Repo Codex skill usage telemetry."""

from __future__ import annotations

import json
from pathlib import Path

from pipeline.agentic.contracts import utc_now_iso
from pipeline.agentic.skill_registry import discover_skill_records


USAGE_PATH = Path("memory/agentic/skill-usage.json")
OUTCOMES = {"pass", "fail", "blocked"}


def load_skill_usage(root: Path) -> dict:
    path = root / USAGE_PATH
    if not path.exists():
        return {"schema_version": "1.0", "skills": {}}
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        return {"schema_version": "1.0", "skills": {}}
    data.setdefault("schema_version", "1.0")
    data.setdefault("skills", {})
    return data


def write_skill_usage(root: Path, data: dict) -> Path:
    path = root / USAGE_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return path


def repo_skill_names(root: Path) -> set[str]:
    return {
        record.name
        for record in discover_skill_records(root)
        if record.kind == "repo_skill"
    }


def record_skill_run(
    root: Path,
    *,
    skill_name: str,
    outcome: str,
    note: str = "",
) -> dict:
    if outcome not in OUTCOMES:
        allowed = ", ".join(sorted(OUTCOMES))
        raise ValueError(f"outcome must be one of: {allowed}")
    if skill_name not in repo_skill_names(root):
        raise ValueError(f"unknown repo skill: {skill_name}")

    data = load_skill_usage(root)
    skills = data.setdefault("skills", {})
    entry = skills.setdefault(
        skill_name,
        {
            "invocations": 0,
            "passes": 0,
            "failures": 0,
            "blocked": 0,
            "history": [],
        },
    )

    now = utc_now_iso()
    entry["invocations"] = int(entry.get("invocations", 0)) + 1
    if outcome == "pass":
        entry["passes"] = int(entry.get("passes", 0)) + 1
    elif outcome == "fail":
        entry["failures"] = int(entry.get("failures", 0)) + 1
    elif outcome == "blocked":
        entry["blocked"] = int(entry.get("blocked", 0)) + 1
    entry["last_invoked"] = now
    entry["last_outcome"] = outcome
    entry["last_note"] = note
    history = list(entry.get("history", []))
    history.append({"at": now, "outcome": outcome, "note": note})
    entry["history"] = history[-50:]

    write_skill_usage(root, data)
    return entry


def summarize_skill_usage(root: Path) -> list[dict]:
    data = load_skill_usage(root)
    skills = data.get("skills", {})
    summary = []
    for record in discover_skill_records(root):
        if record.kind != "repo_skill":
            continue
        usage = skills.get(record.name, {})
        summary.append(
            {
                "skill": record.name,
                "path": record.path,
                "implicit_invocation": record.implicit_invocation,
                "invocations": int(usage.get("invocations", 0)),
                "passes": int(usage.get("passes", 0)),
                "failures": int(usage.get("failures", 0)),
                "blocked": int(usage.get("blocked", 0)),
                "last_outcome": usage.get("last_outcome"),
                "last_invoked": usage.get("last_invoked"),
                "last_note": usage.get("last_note", ""),
            }
        )
    return summary
