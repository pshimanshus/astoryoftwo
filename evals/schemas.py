from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path, PurePosixPath
from typing import Any


REGISTRY_PATH = Path("evals/registry.json")
TASKS_PATH = Path("evals/tasks")
DEEP_SPEC_REQUIRED_HEADINGS = (
    "## Why This Task Exists",
    "## Starting Fixture",
    "## Failure Modes",
    "## Checker Design",
    "## Anti-Gaming",
    "## Severity Model",
)
KNOWN_DETERMINISTIC_CHECKERS = {
    "diff_guard",
    "brandmark_top_right_rule",
    "carousel_doctor_fixture",
    "autopublish_safety_fixture",
    "creator_visible_copy",
}


def _fixture_path_issue(raw_path: str, *, label: str) -> str | None:
    normalized = raw_path.replace("\\", "/")
    pure = PurePosixPath(normalized)
    if normalized in {"", "."}:
        return f"{label} fixture path is empty"
    if pure.is_absolute():
        return f"{label} fixture path must be relative: {raw_path}"
    if any(part == ".." for part in pure.parts):
        return f"{label} fixture path may not contain '..': {raw_path}"
    return None


@dataclass(frozen=True)
class FixtureOverlay:
    source: str
    target: str
    mode: str = "text"

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "FixtureOverlay":
        return cls(
            source=str(data["source"]),
            target=str(data["target"]),
            mode=str(data.get("mode", "text")),
        )


@dataclass(frozen=True)
class PassCriteria:
    critical_failures_allowed: int = 0
    major_failures_allowed: int = 0
    minor_failures_allowed: int = 999
    minimum_score: float = 1.0

    @classmethod
    def from_dict(cls, data: dict[str, Any] | None) -> "PassCriteria":
        data = data or {}
        return cls(
            critical_failures_allowed=int(data.get("critical_failures_allowed", 0)),
            major_failures_allowed=int(data.get("major_failures_allowed", 0)),
            minor_failures_allowed=int(data.get("minor_failures_allowed", 999)),
            minimum_score=float(data.get("minimum_score", 1.0)),
        )


@dataclass(frozen=True)
class EvalTask:
    schema_version: str
    id: str
    title: str
    category: str
    difficulty: str
    suites: list[str]
    prompt: str
    starting_state: list[str]
    done_when: list[str]
    allowed_paths: list[str]
    forbidden_paths: list[str]
    expected_files_changed: list[str]
    forbidden_changes: list[str]
    required_commands: list[list[str]]
    deterministic_checkers: list[str]
    rubric_checkers: list[str]
    pass_criteria: PassCriteria
    fail_to_pass: list[str] = field(default_factory=list)
    pass_to_pass: list[str] = field(default_factory=list)
    fixture_overlay: list[FixtureOverlay] = field(default_factory=list)
    anti_gaming_notes: list[str] = field(default_factory=list)
    task_dir: Path = Path(".")

    @classmethod
    def from_file(cls, path: Path) -> "EvalTask":
        data = json.loads(path.read_text(encoding="utf-8"))
        return cls(
            schema_version=str(data["schema_version"]),
            id=str(data["id"]),
            title=str(data["title"]),
            category=str(data["category"]),
            difficulty=str(data["difficulty"]),
            suites=list(data.get("suites", [])),
            prompt=str(data.get("prompt", "prompt.md")),
            starting_state=list(data.get("starting_state", [])),
            done_when=list(data.get("done_when", [])),
            allowed_paths=list(data.get("allowed_paths", [])),
            forbidden_paths=list(data.get("forbidden_paths", [])),
            expected_files_changed=list(data.get("expected_files_changed", [])),
            forbidden_changes=list(data.get("forbidden_changes", [])),
            required_commands=[list(command) for command in data.get("required_commands", [])],
            deterministic_checkers=list(data.get("deterministic_checkers", [])),
            rubric_checkers=list(data.get("rubric_checkers", [])),
            fail_to_pass=list(data.get("fail_to_pass", [])),
            pass_to_pass=list(data.get("pass_to_pass", [])),
            pass_criteria=PassCriteria.from_dict(data.get("pass_criteria")),
            fixture_overlay=[
                FixtureOverlay.from_dict(item)
                for item in data.get("fixture_overlay", [])
            ],
            anti_gaming_notes=list(data.get("anti_gaming_notes", [])),
            task_dir=path.parent,
        )


@dataclass(frozen=True)
class EvalRegistry:
    schema_version: str
    suites: dict[str, dict[str, Any]]
    tasks: list[str]

    @classmethod
    def from_file(cls, path: Path) -> "EvalRegistry":
        data = json.loads(path.read_text(encoding="utf-8"))
        return cls(
            schema_version=str(data["schema_version"]),
            suites=dict(data.get("suites", {})),
            tasks=list(data.get("tasks", [])),
        )


@dataclass(frozen=True)
class CheckResult:
    code: str
    status: str
    severity: str
    message: str
    evidence: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "code": self.code,
            "status": self.status,
            "severity": self.severity,
            "message": self.message,
            "evidence": self.evidence,
        }


def load_registry(root: Path) -> EvalRegistry:
    return EvalRegistry.from_file(root / REGISTRY_PATH)


def discover_tasks(root: Path) -> list[EvalTask]:
    registry = load_registry(root)
    tasks: list[EvalTask] = []
    for task_id in registry.tasks:
        tasks.append(EvalTask.from_file(root / TASKS_PATH / task_id / "task.json"))
    return tasks


def validate_task_suite(root: Path) -> dict[str, Any]:
    issues: list[str] = []
    try:
        registry = load_registry(root)
    except (FileNotFoundError, json.JSONDecodeError, KeyError) as exc:
        return {"status": "FAIL", "task_count": 0, "issues": [str(exc)]}

    seen: set[str] = set()
    tasks: list[EvalTask] = []
    for task_id in registry.tasks:
        task_path = root / TASKS_PATH / task_id / "task.json"
        prompt_path = root / TASKS_PATH / task_id / "prompt.md"
        if task_id in seen:
            issues.append(f"duplicate task id in registry: {task_id}")
        seen.add(task_id)
        if not task_path.exists():
            issues.append(f"missing task metadata: {task_path.relative_to(root)}")
            continue
        if not prompt_path.exists():
            issues.append(f"missing task prompt: {prompt_path.relative_to(root)}")
            continue
        deep_spec_path = root / TASKS_PATH / task_id / "deep-spec.md"
        if not deep_spec_path.exists():
            issues.append(f"{task_id}: missing deep-spec.md")
        else:
            deep_text = deep_spec_path.read_text(encoding="utf-8")
            if len(deep_text.split()) < 220:
                issues.append(f"{task_id}: deep-spec.md is below the 220-word floor")
            for heading in DEEP_SPEC_REQUIRED_HEADINGS:
                if heading not in deep_text:
                    issues.append(f"{task_id}: deep-spec.md missing heading {heading}")
            lowered = deep_text.lower()
            for phrase in ("hidden variant", "pass-to-pass", "fail-to-pass"):
                if phrase not in lowered:
                    issues.append(f"{task_id}: deep-spec.md missing phrase {phrase}")
        try:
            task = EvalTask.from_file(task_path)
        except (json.JSONDecodeError, KeyError, TypeError, ValueError) as exc:
            issues.append(f"{task_id}: invalid metadata: {exc}")
            continue
        tasks.append(task)
        if task.id != task_id:
            issues.append(f"{task_id}: id does not match registry entry")
        if task.schema_version != "1.0":
            issues.append(f"{task.id}: unsupported schema_version")
        if not task.suites:
            issues.append(f"{task.id}: suites must not be empty")
        if not task.starting_state:
            issues.append(f"{task.id}: starting_state must not be empty")
        if not task.done_when:
            issues.append(f"{task.id}: done_when must not be empty")
        if not task.fail_to_pass:
            issues.append(f"{task.id}: fail_to_pass must not be empty")
        if not task.pass_to_pass:
            issues.append(f"{task.id}: pass_to_pass must not be empty")
        unknown_checkers = sorted(set(task.deterministic_checkers) - KNOWN_DETERMINISTIC_CHECKERS)
        if unknown_checkers:
            issues.append(f"{task.id}: unknown deterministic checkers: {unknown_checkers}")
        if "AGENTS.md" not in task.forbidden_paths and task.category != "instruction_surface":
            issues.append(f"{task.id}: AGENTS.md should be forbidden")
        for overlay in task.fixture_overlay:
            source_issue = _fixture_path_issue(overlay.source, label="source")
            target_issue = _fixture_path_issue(overlay.target, label="target")
            if source_issue:
                issues.append(f"{task.id}: {source_issue}")
            if target_issue:
                issues.append(f"{task.id}: {target_issue}")
            if source_issue is None and not (task.task_dir / overlay.source).exists():
                issues.append(f"{task.id}: fixture source missing: {overlay.source}")
            if overlay.mode not in {"text", "binary"}:
                issues.append(f"{task.id}: unsupported fixture mode: {overlay.mode}")

    registered_suites = set(registry.suites)
    for task in tasks:
        unknown = sorted(set(task.suites) - registered_suites)
        if unknown:
            issues.append(f"{task.id}: unknown suites: {unknown}")

    return {
        "status": "FAIL" if issues else "PASS",
        "task_count": len(tasks),
        "issues": issues,
    }
