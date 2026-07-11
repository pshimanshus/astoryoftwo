"""Skill and agent discovery plus reusable skill-system resolution."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from pipeline.agentic.contracts import SkillRecord


SKILL_SYSTEMS_PATH = Path("config/skill-systems.json")
FRONTMATTER_RE = re.compile(r"^---\n(.*?)\n---", re.DOTALL)


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


def parse_frontmatter(text: str) -> dict[str, Any]:
    match = FRONTMATTER_RE.match(text)
    if not match:
        return {}
    return parse_simple_yaml(match.group(1))


def parse_scalar(value: str) -> Any:
    value = value.strip()
    if value in {"true", "True"}:
        return True
    if value in {"false", "False"}:
        return False
    if (value.startswith('"') and value.endswith('"')) or (
        value.startswith("'") and value.endswith("'")
    ):
        return value[1:-1]
    return value


def parse_simple_yaml(text: str) -> dict[str, Any]:
    data: dict[str, Any] = {}
    current_section: str | None = None
    for raw_line in text.splitlines():
        if not raw_line.strip() or raw_line.lstrip().startswith("#"):
            continue
        if raw_line.startswith((" ", "\t")):
            if current_section is None or ":" not in raw_line:
                continue
            key, value = raw_line.strip().split(":", 1)
            section = data.setdefault(current_section, {})
            if isinstance(section, dict):
                section[key.strip()] = parse_scalar(value)
            continue
        if ":" not in raw_line:
            continue
        key, value = raw_line.split(":", 1)
        key = key.strip()
        if value.strip():
            data[key] = parse_scalar(value)
            current_section = None
        else:
            data[key] = {}
            current_section = key
    return data


def parse_implicit_invocation(skill_md: Path) -> bool:
    metadata_path = skill_md.parent / "agents" / "openai.yaml"
    if not metadata_path.exists():
        return True
    data = parse_simple_yaml(metadata_path.read_text(encoding="utf-8"))
    policy = data.get("policy", {})
    if not isinstance(policy, dict):
        return True
    return bool(policy.get("allow_implicit_invocation", True))


def make_record(
    root: Path,
    path: Path,
    kind: str,
    *,
    skill_id_prefix: str | None = None,
    name: str | None = None,
    description: str | None = None,
    implicit_invocation: bool | None = None,
) -> SkillRecord:
    text = path.read_text(encoding="utf-8", errors="ignore")
    relative = path.relative_to(root).as_posix()
    record_name = name or slug(path)
    prefix = skill_id_prefix or kind
    return SkillRecord(
        skill_id=f"{prefix}.{record_name}",
        name=record_name,
        kind=kind,
        path=relative,
        description=description or first_heading(text, record_name),
        dependencies=parse_dependencies(text),
        implicit_invocation=implicit_invocation,
        confidence=parse_confidence(text),
    )


def make_repo_skill_record(root: Path, path: Path) -> SkillRecord:
    text = path.read_text(encoding="utf-8", errors="ignore")
    frontmatter = parse_frontmatter(text)
    name = str(frontmatter.get("name") or path.parent.name).strip()
    description = str(frontmatter.get("description") or first_heading(text, name)).strip()
    return make_record(
        root,
        path,
        "repo_skill",
        skill_id_prefix="repo_skill",
        name=name,
        description=description,
        implicit_invocation=parse_implicit_invocation(path),
    )


def discover_skill_records(root: Path) -> list[SkillRecord]:
    root = root.resolve()
    records: list[SkillRecord] = []
    for path in sorted((root / ".agents" / "skills").glob("*/SKILL.md")):
        records.append(make_repo_skill_record(root, path))
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
        "source_references": list(system.get("source_references", [])),
        "agents": list(system.get("agents", [])),
        "gates": list(system.get("gates", [])),
    }
