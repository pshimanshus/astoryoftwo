"""Deterministic external gates for learning proposals."""

from __future__ import annotations

import json
from pathlib import Path

from pipeline.agentic.contracts import SkillEvalResult


def evaluate_learning_proposal(root: Path, proposal_path: Path) -> SkillEvalResult:
    root = root.resolve()
    data = json.loads(proposal_path.read_text(encoding="utf-8"))
    issues: list[str] = []
    warnings: list[str] = []

    if data.get("auto_apply") is not False:
        issues.append("auto_apply must be false; proposals require external approval")
    if data.get("status") != "draft":
        warnings.append("proposal is not draft")
    target = root / data.get("target_path", "")
    if data.get("proposed_action") == "modify" and not target.exists():
        issues.append(f"target_path missing for modify proposal: {data.get('target_path')}")
    if "skill_eval" not in data.get("required_validators", []):
        issues.append("required_validators must include skill_eval")
    if data.get("before_hash") == data.get("after_hash"):
        issues.append("before_hash and after_hash are identical")

    return SkillEvalResult(
        proposal_id=data.get("proposal_id", "unknown"),
        status="FAIL" if issues else "PASS",
        issues=issues,
        warnings=warnings,
    )
