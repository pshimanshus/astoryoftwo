"""Allow-listed, receipt-bound validators for learning proposals.

Validators are deliberately selected by a repository manifest and an in-code
executor map.  A proposal therefore cannot turn a validator name into an
arbitrary import or shell command.  Every successful execution writes a
receipt tied to the proposal's target and proposed-content hashes; applying a
proposal requires those current receipts.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import tempfile
import tomllib
from pathlib import Path
from typing import Any, Callable

from pipeline.agentic.contracts import LearningEvent, SkillEvalResult, utc_now_iso
from pipeline.agentic.skill_eval import evaluate_learning_proposal


VALIDATOR_REGISTRY_PATH = Path("config/agentic_validator_registry.json")
RECEIPTS_DIR = Path("memory/agentic/validator-receipts")
VALIDATOR_ID = re.compile(r"^[a-z][a-z0-9_]*$")
EVENT_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$")


def _sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _read_json(path: Path) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"invalid JSON at {path}: {exc}") from exc
    if not isinstance(data, dict):
        raise ValueError(f"expected a JSON object at {path}")
    return data


def _skill_eval_executor(root: Path, proposal_path: Path) -> SkillEvalResult:
    return evaluate_learning_proposal(root, proposal_path)


def _creator_workflow_executor(root: Path, proposal_path: Path) -> SkillEvalResult:
    """Validate the source event, its evidence paths, and feedback identity."""
    result = evaluate_learning_proposal(root, proposal_path)
    payload = _read_json(proposal_path)
    event_id = str(payload.get("source_event_id") or "")
    event_path = root / "memory" / "agentic" / "learning-events" / f"{event_id}.json"
    issues = list(result.issues)
    event: LearningEvent | None = None
    if not EVENT_ID.fullmatch(event_id):
        issues.append("creator workflow validator requires a safe source event id")
    elif not event_path.is_file() or event_path.is_symlink():
        issues.append("creator workflow validator requires an existing source learning event")
    else:
        try:
            event = LearningEvent.model_validate(_read_json(event_path))
        except ValueError as exc:
            issues.append(f"source learning event is invalid: {exc}")
    if event is not None:
        for evidence_path in event.evidence_paths:
            dependency = _artifact_dependency(root, evidence_path)
            if dependency["state"] == "unsafe":
                issues.append(f"source evidence path is unsafe: {evidence_path}")
            elif dependency["state"] == "symlink":
                issues.append(f"source evidence must not traverse a symlink: {evidence_path}")
            elif dependency["state"] == "missing":
                issues.append(f"source evidence is missing: {evidence_path}")
        if event.source == "creator_feedback":
            metadata = event.feedback_metadata or {}
            if not str(metadata.get("feedback_id") or "").strip():
                issues.append("creator feedback event is missing feedback_id")
            if not event.package_path:
                issues.append("creator feedback event is missing package_path")
    return SkillEvalResult(
        proposal_id=result.proposal_id,
        status="FAIL" if issues else "PASS",
        issues=issues,
        warnings=result.warnings,
    )


def _agentic_docs_executor(root: Path, proposal_path: Path) -> SkillEvalResult:
    """Validate the proposed instruction/workflow artifact by its file type."""
    result = evaluate_learning_proposal(root, proposal_path)
    payload = _read_json(proposal_path)
    issues = list(result.issues)
    warnings = list(result.warnings)
    content_path = _proposal_content_path(root, payload)
    target = str(payload.get("target_path") or "")
    content = content_path.read_text(encoding="utf-8") if content_path.is_file() else ""
    if not content.strip():
        issues.append("instruction/workflow proposal content must not be empty")
    if target.endswith(".json") and content.strip():
        try:
            document = json.loads(content)
        except json.JSONDecodeError as exc:
            issues.append(f"proposed JSON is invalid: {exc}")
            document = None
        if target == "config/skill-systems.json" and isinstance(document, dict):
            systems = document.get("systems")
            if not isinstance(systems, dict):
                issues.append("skill-systems workflow definition requires a systems object")
            else:
                prepost = systems.get("prepost_reel")
                if isinstance(prepost, dict):
                    if "specialist_agent_count" in prepost:
                        issues.append("prepost_reel must not restore the retired specialist-agent contract")
                    if prepost.get("runtime_call_count") != 3:
                        issues.append("prepost_reel must declare the current three-call runtime")
    if target.endswith(".toml") and content.strip():
        try:
            document = tomllib.loads(content)
        except tomllib.TOMLDecodeError as exc:
            issues.append(f"proposed TOML is invalid: {exc}")
            document = None
        if target.startswith(".codex/agents/") and isinstance(document, dict):
            if document.get("sandbox_mode") != "read-only":
                issues.append("knowledge reviewer agent records must remain read-only")
            if not str(document.get("developer_instructions") or "").strip():
                issues.append("agent record requires bounded developer_instructions")
    if target.endswith(".md") and content.strip() and not re.search(r"(?m)^#", content):
        warnings.append("proposed Markdown has no heading")
    return SkillEvalResult(
        proposal_id=result.proposal_id,
        status="FAIL" if issues else "PASS",
        issues=issues,
        warnings=warnings,
    )


# This map is the executable allow-list.  Manifest entries only enable one of
# these fixed functions; they never provide an import path or command string.
EXECUTORS: dict[str, Callable[[Path, Path], SkillEvalResult]] = {
    "skill_eval": _skill_eval_executor,
    "creator_workflow_contract": _creator_workflow_executor,
    "agentic_docs_contract": _agentic_docs_executor,
}


def default_validator_registry() -> dict[str, Any]:
    """Safe fallback used by isolated test workspaces and older repositories."""
    return {
        "schema_version": "1.0",
        "validators": {
            "skill_eval": {
                "executor": "skill_eval",
                "contract_version": "skill-eval/v1",
                "description": "Checks proposal-only invariants and target existence.",
            },
            "creator_workflow_contract": {
                "executor": "creator_workflow_contract",
                "contract_version": "creator-workflow/v3",
                "description": "Requires the source learning event for creator-feedback proposals.",
            },
            "agentic_docs_contract": {
                "executor": "agentic_docs_contract",
                "contract_version": "agentic-docs/v2",
                "description": "Rechecks the proposal-only learning contract.",
            },
        },
    }


def load_validator_registry(root: Path) -> dict[str, Any]:
    path = root.resolve() / VALIDATOR_REGISTRY_PATH
    registry = _read_json(path) if path.exists() else default_validator_registry()
    validators = registry.get("validators")
    if not isinstance(validators, dict) or not validators:
        raise ValueError("validator registry must contain a non-empty validators object")
    for validator_id, definition in validators.items():
        if not isinstance(validator_id, str) or not VALIDATOR_ID.fullmatch(validator_id):
            raise ValueError(f"invalid validator id: {validator_id!r}")
        if not isinstance(definition, dict):
            raise ValueError(f"validator '{validator_id}' must be an object")
        executor = definition.get("executor")
        if executor not in EXECUTORS:
            raise ValueError(
                f"validator '{validator_id}' names unsupported executor {executor!r}"
            )
        if not isinstance(definition.get("contract_version"), str):
            # Older project-local registries remain usable, but their receipt
            # identity is explicitly versioned as legacy rather than implicit.
            definition["contract_version"] = "legacy/v1"
    return registry


def allowed_validator_ids(root: Path) -> set[str]:
    return set(load_validator_registry(root)["validators"])


def _proposal_content_path(root: Path, payload: dict[str, Any]) -> Path:
    raw = payload.get("proposed_content_path")
    if not isinstance(raw, str) or not raw:
        raise ValueError("proposal missing proposed_content_path")
    path = (root / raw).resolve()
    try:
        path.relative_to(root)
    except ValueError as exc:
        raise ValueError("proposed_content_path must stay inside workspace root") from exc
    return path


def proposal_binding(root: Path, proposal_path: Path) -> dict[str, Any]:
    """Return the immutable proposal facts each validator receipt attests."""
    root = root.resolve()
    path = proposal_path if proposal_path.is_absolute() else root / proposal_path
    payload = _read_json(path)
    content_path = _proposal_content_path(root, payload)
    if not content_path.is_file():
        raise ValueError(f"proposal content is missing: {content_path}")
    content_hash = _sha256_bytes(content_path.read_bytes())
    after_hash = str(payload.get("after_hash", ""))
    if content_hash != after_hash:
        raise ValueError("proposal content hash does not match after_hash")
    target_path = str(payload.get("target_path", ""))
    if not target_path:
        raise ValueError("proposal missing target_path")
    validators = payload.get("required_validators")
    if not isinstance(validators, list) or not validators:
        raise ValueError("proposal must require at least one validator")
    if any(not isinstance(item, str) for item in validators):
        raise ValueError("proposal required_validators must contain only strings")
    binding = {
        "proposal_id": str(payload.get("proposal_id", path.stem)),
        "target_path": target_path,
        "proposed_action": str(payload.get("proposed_action", "")),
        "before_hash": str(payload.get("before_hash", "")),
        "after_hash": after_hash,
        "content_sha256": content_hash,
        "required_validators": sorted(set(validators)),
    }
    binding_json = json.dumps(binding, sort_keys=True, separators=(",", ":"))
    binding["binding_sha256"] = _sha256_bytes(binding_json.encode("utf-8"))
    return binding


def receipt_path(root: Path, proposal_id: str, validator_id: str) -> Path:
    return root.resolve() / RECEIPTS_DIR / proposal_id / f"{validator_id}.json"


def _definition_binding(definition: dict[str, Any]) -> tuple[str, str]:
    canonical = json.dumps(definition, sort_keys=True, separators=(",", ":"))
    return str(definition["contract_version"]), _sha256_bytes(canonical.encode("utf-8"))


def _atomic_write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            json.dump(payload, handle, indent=2, ensure_ascii=False)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


def _artifact_dependency(root: Path, relative_path: str) -> dict[str, Any]:
    """Describe current bytes for one workspace artifact without following links."""

    raw = Path(relative_path)
    dependency: dict[str, Any] = {"path": relative_path}
    if not relative_path.strip() or raw.is_absolute() or ".." in raw.parts:
        dependency["state"] = "unsafe"
        return dependency

    candidate = root / raw
    cursor = root
    for part in raw.parts:
        cursor /= part
        if cursor.is_symlink():
            dependency["state"] = "symlink"
            return dependency
    if candidate.is_file():
        dependency.update(
            {
                "state": "file",
                "bytes": candidate.stat().st_size,
                "sha256": _sha256_bytes(candidate.read_bytes()),
            }
        )
        return dependency
    if candidate.is_dir():
        entries: list[dict[str, Any]] = []
        for child in sorted(candidate.rglob("*")):
            child_relative = child.relative_to(candidate).as_posix()
            if child.is_symlink():
                entries.append({"path": child_relative, "state": "symlink"})
            elif child.is_file():
                entries.append(
                    {
                        "path": child_relative,
                        "state": "file",
                        "bytes": child.stat().st_size,
                        "sha256": _sha256_bytes(child.read_bytes()),
                    }
                )
        tree_sha256 = _sha256_bytes(
            json.dumps(entries, sort_keys=True, separators=(",", ":")).encode("utf-8")
        )
        dependency.update(
            {"state": "directory", "tree_sha256": tree_sha256, "entries": entries}
        )
        return dependency
    dependency["state"] = "missing"
    return dependency


def _validator_dependency_binding(
    root: Path,
    proposal_path: Path,
    executor_name: str,
) -> dict[str, Any]:
    """Bind every mutable artifact read by a validator outside the proposal."""

    artifacts: list[dict[str, Any]] = []
    if executor_name == "creator_workflow_contract":
        payload = _read_json(proposal_path)
        event_id = str(payload.get("source_event_id") or "")
        event_relative = f"memory/agentic/learning-events/{event_id}.json"
        event_dependency = _artifact_dependency(root, event_relative)
        artifacts.append(event_dependency)
        if EVENT_ID.fullmatch(event_id) and event_dependency.get("state") == "file":
            try:
                event = LearningEvent.model_validate(_read_json(root / event_relative))
            except ValueError:
                event = None
            if event is not None:
                artifacts.extend(
                    _artifact_dependency(root, evidence_path)
                    for evidence_path in event.evidence_paths
                )

    binding: dict[str, Any] = {
        "executor": executor_name,
        "artifacts": artifacts,
    }
    canonical = json.dumps(binding, sort_keys=True, separators=(",", ":"))
    binding["binding_sha256"] = _sha256_bytes(canonical.encode("utf-8"))
    return binding


def run_validator(root: Path, proposal_path: Path, validator_id: str) -> dict[str, Any]:
    root = root.resolve()
    resolved_proposal_path = (
        proposal_path.resolve()
        if proposal_path.is_absolute()
        else (root / proposal_path).resolve()
    )
    registry = load_validator_registry(root)
    definitions = registry["validators"]
    if validator_id not in definitions:
        raise ValueError(f"validator is not allow-listed: {validator_id}")
    binding = proposal_binding(root, resolved_proposal_path)
    definition = definitions[validator_id]
    executor_name = definition["executor"]
    contract_version, definition_sha256 = _definition_binding(definition)
    dependencies_before = _validator_dependency_binding(
        root, resolved_proposal_path, executor_name
    )
    result = EXECUTORS[executor_name](root, resolved_proposal_path)
    dependencies = _validator_dependency_binding(root, resolved_proposal_path, executor_name)
    if dependencies["binding_sha256"] != dependencies_before["binding_sha256"]:
        result = SkillEvalResult(
            proposal_id=result.proposal_id,
            status="FAIL",
            issues=[*result.issues, "validator dependencies changed during execution"],
            warnings=result.warnings,
        )
    receipt = {
        "schema_version": "1.0",
        "validator_id": validator_id,
        "executor": executor_name,
        "contract_version": contract_version,
        "definition_sha256": definition_sha256,
        "status": result.status,
        "issues": result.issues,
        "warnings": result.warnings,
        "binding": binding,
        "dependencies": dependencies,
        "created_at": utc_now_iso(),
    }
    path = receipt_path(root, binding["proposal_id"], validator_id)
    _atomic_write_json(path, receipt)
    receipt["receipt_path"] = path.relative_to(root).as_posix()
    return receipt


def run_required_validators(root: Path, proposal_path: Path) -> list[dict[str, Any]]:
    binding = proposal_binding(root, proposal_path)
    allowed = allowed_validator_ids(root)
    unknown = sorted(set(binding["required_validators"]) - allowed)
    if unknown:
        raise ValueError(f"proposal requires non-allow-listed validators: {', '.join(unknown)}")
    return [
        run_validator(root, proposal_path, validator_id)
        for validator_id in binding["required_validators"]
    ]


def require_current_validator_receipts(root: Path, proposal_path: Path) -> list[str]:
    """Return receipt paths or raise when application lacks passing, current proof."""
    root = root.resolve()
    binding = proposal_binding(root, proposal_path)
    allowed = allowed_validator_ids(root)
    unknown = sorted(set(binding["required_validators"]) - allowed)
    if unknown:
        raise ValueError(f"proposal requires non-allow-listed validators: {', '.join(unknown)}")

    current_target = root / binding["target_path"]
    action = binding["proposed_action"]
    if action == "modify":
        if not current_target.is_file():
            raise ValueError(f"target_path missing for modify proposal: {binding['target_path']}")
        if _sha256_bytes(current_target.read_bytes()) != binding["before_hash"]:
            raise ValueError("target changed since proposal creation; validator receipts are stale")
    elif action == "create":
        if current_target.exists():
            raise ValueError("target now exists; create proposal must be regenerated")
    elif action == "deprecate":
        if not current_target.is_file():
            raise ValueError(f"target_path missing for deprecate proposal: {binding['target_path']}")
        if _sha256_bytes(current_target.read_bytes()) != binding["before_hash"]:
            raise ValueError("target changed since proposal creation; validator receipts are stale")
    else:
        raise ValueError(f"unsupported proposed_action: {action}")

    receipt_paths: list[str] = []
    for validator_id in binding["required_validators"]:
        path = receipt_path(root, binding["proposal_id"], validator_id)
        receipt = _read_json(path) if path.exists() else {}
        if receipt.get("status") != "PASS":
            raise ValueError(f"missing passing validator receipt: {validator_id}")
        definition = load_validator_registry(root)["validators"][validator_id]
        contract_version, definition_sha256 = _definition_binding(definition)
        if (
            receipt.get("validator_id") != validator_id
            or receipt.get("executor") != definition.get("executor")
            or receipt.get("contract_version") != contract_version
            or receipt.get("definition_sha256") != definition_sha256
        ):
            raise ValueError(f"stale validator contract receipt: {validator_id}")
        recorded_binding = receipt.get("binding")
        if not isinstance(recorded_binding, dict) or recorded_binding.get("binding_sha256") != binding["binding_sha256"]:
            raise ValueError(f"stale validator receipt: {validator_id}")
        recorded_dependencies = receipt.get("dependencies")
        current_dependencies = _validator_dependency_binding(
            root,
            proposal_path if proposal_path.is_absolute() else root / proposal_path,
            str(definition.get("executor") or ""),
        )
        if (
            not isinstance(recorded_dependencies, dict)
            or recorded_dependencies.get("binding_sha256")
            != current_dependencies["binding_sha256"]
        ):
            raise ValueError(f"stale validator dependency receipt: {validator_id}")
        receipt_paths.append(path.relative_to(root).as_posix())
    return receipt_paths
