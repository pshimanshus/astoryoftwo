"""Small workflow gate helpers shared by future orchestrators."""

from __future__ import annotations

from pipeline.agentic.contracts import WorkflowGate


def gate(name: str, status: str, reason: str = "", evidence_paths: list[str] | None = None) -> WorkflowGate:
    return WorkflowGate(
        name=name,
        status=status,  # type: ignore[arg-type]
        reason=reason,
        evidence_paths=evidence_paths or [],
    )


def has_blocking_gate(gates: list[WorkflowGate]) -> bool:
    return any(item.status in {"REPAIR", "STOP", "FAIL"} for item in gates)
