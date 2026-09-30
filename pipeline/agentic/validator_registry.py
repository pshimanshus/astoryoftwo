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
import re
from pathlib import Path
from typing import Any, Callable

from pipeline.agentic.contracts import SkillEvalResult, utc_now_iso
from pipeline.agentic.skill_eval import evaluate_learning_proposal


VALIDATOR_REGISTRY_PATH = Path("config/agentic_validator_registry.json")
RECEIPTS_DIR = Path("memory/agentic/validator-receipts")
VALIDATOR_ID = re.compile(r"^[a-z][a-z0-9_]*$")


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
    """Check that feedback-led learning still has a local source event."""
    result = evaluate_learning_proposal(root, proposal_path)
    payload = _read_json(proposal_path)
    event_id = str(payload.get("source_event_id") or "")
    event_path = root / "memory" / "agentic" / "learning-events" / f"{event_id}.json"
    issues = list(result.issues)
    if not event_id or not event_path.is_file():
        issues.append("creator workflow validator requires an existing source learning event")
    return SkillEvalResult(
        proposal_id=result.proposal_id,
        status="FAIL" if issues else "PASS",
        issues=issues,
        warnings=result.warnings,
    )


def _agentic_docs_executor(root: Path, proposal_path: Path) -> SkillEvalResult:
    """Keep a proposal in the guarded learning contract without shelling out."""
    return evaluate_learning_proposal(root, proposal_path)


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
                "description": "Checks proposal-only invariants and target existence.",
            },
            "creator_workflow_contract": {
                "executor": "creator_workflow_contract",
                "description": "Requires the source learning event for creator-feedback proposals.",
            },
            "agentic_docs_contract": {
                "executor": "agentic_docs_contract",
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
    executor_name = definitions[validator_id]["executor"]
    result = EXECUTORS[executor_name](root, resolved_proposal_path)
    receipt = {
        "schema_version": "1.0",
        "validator_id": validator_id,
        "executor": executor_name,
        "status": result.status,
        "issues": result.issues,
        "warnings": result.warnings,
        "binding": binding,
        "created_at": utc_now_iso(),
    }
    path = receipt_path(root, binding["proposal_id"], validator_id)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(receipt, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
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
        recorded_binding = receipt.get("binding")
        if not isinstance(recorded_binding, dict) or recorded_binding.get("binding_sha256") != binding["binding_sha256"]:
            raise ValueError(f"stale validator receipt: {validator_id}")
        receipt_paths.append(path.relative_to(root).as_posix())
    return receipt_paths
