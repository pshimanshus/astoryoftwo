"""Skill and agent discovery plus reusable skill-system resolution."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from pipeline.agentic.contracts import SkillRecord


SKILL_SYSTEMS_PATH = Path("config/skill-systems.json")


def slug(path: Path) -> str:
    return path.stem.replace("_", "-")


def first_heading(text: str, fallback: str) -> str:
    match = re.search(r"(?m)^#\s+(.+?)\s*$", text)
    return match.group(1).strip() if match else fallback


def parse_confidence(text: str) -> float:
    match = re.search(r"(?m)^confidence:\s*(0(?:\.\d+)?|1(?:\.0+)?)\s*$", text)
    return float(match.group(1)) if match else 0.5


def parse_dependencies(text: str) -> list[str]:
    refs = re.findall(r"(?m)config/skills/[A-Za-z0-9_.-]+\.md", text)
    names = [Path(ref).stem for ref in refs]
    return sorted(set(names))


def make_record(root: Path, path: Path, kind: str) -> SkillRecord:
    text = path.read_text(encoding="utf-8", errors="ignore")
    relative = path.relative_to(root).as_posix()
    name = slug(path)
    return SkillRecord(
        skill_id=f"{kind}.{name}",
        name=name,
        kind=kind,
        path=relative,
        description=first_heading(text, name),
        dependencies=parse_dependencies(text),
        confidence=parse_confidence(text),
    )


def discover_skill_records(root: Path) -> list[SkillRecord]:
    root = root.resolve()
    records: list[SkillRecord] = []
    for path in sorted((root / "config" / "skills").glob("*.md")):
        records.append(make_record(root, path, "skill"))
    for path in sorted((root / "agents").glob("*.md")):
        records.append(make_record(root, path, "agent"))
    return records


def load_skill_systems(root: Path) -> dict[str, Any]:
    path = root / SKILL_SYSTEMS_PATH
    if not path.exists():
        raise FileNotFoundError(f"Missing skill-system manifest: {SKILL_SYSTEMS_PATH}")
    return json.loads(path.read_text(encoding="utf-8"))


def resolve_skill_system(systems: dict[str, Any], name: str) -> dict[str, Any]:
    system = systems["systems"][name]
    return {
        "name": name,
        "description": system.get("description", ""),
        "components": list(system.get("components", [])),
        "agents": list(system.get("agents", [])),
        "gates": list(system.get("gates", [])),
    }
