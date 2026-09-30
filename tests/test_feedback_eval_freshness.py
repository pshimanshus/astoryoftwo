from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from evals.feedback_cases import (
    EVALUATOR_CONTRACT_VERSION,
    ensure_feedback_case,
    evaluate_feedback_case,
    evaluator_contract_sha256,
    feedback_case_is_current,
    revise_feedback_case_assertions,
    verification_contract_sha256,
)


def _write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def _event() -> dict[str, object]:
    exact = "Keep this from Zuv's point of view."
    return {
        "feedback_id": "fb-freshness",
        "user_instruction_exact": exact,
        "user_instruction_sha256": "sha256:"
        + hashlib.sha256(exact.encode("utf-8")).hexdigest(),
        "primary_diagnosis": "scene_action",
        "must_change": ["Zuv owns the scene."],
        "must_preserve": ["Exact copy."],
        "affected_artifacts": ["slides.json"],
        "repair_operations": [],
        "verification_assertions": [],
        "action_taken": {"type": "existing_package_repair"},
        "resolution_evidence": ["slides.json"],
        "eval_waiver_reason": None,
    }


def test_old_hash_only_pass_is_not_current(tmp_path: Path) -> None:
    package = tmp_path / "output/carousels/2026-09-05/example"
    _write_json(package / "slides.json", {"slides": [{"physical_action": "Zuv waits."}]})
    current_hash = "sha256:" + hashlib.sha256(
        (package / "slides.json").read_bytes()
    ).hexdigest()
    old_case = {
        "schema_version": "creator-feedback-eval/v1",
        "task_id": "FEEDBACK-OLD",
        "feedback_id": "fb-old",
        "package_path": "output/carousels/2026-09-05/example",
        "user_instruction_sha256": "sha256:" + "1" * 64,
        "diagnosis": "scene_action",
        "must_change": ["Repair the scene."],
        "must_preserve": ["Exact copy."],
        "status": "passed",
        "source_affected_artifacts": ["slides.json"],
        "affected_artifacts": ["slides.json"],
        "baseline_artifact_hashes": {"slides.json": "sha256:" + "0" * 64},
        "preserved_projection_hashes": {},
        "repair_operations": [],
        "verification_assertions": [],
        "verification_contract_revision": 1,
        "evaluator_contract_version": EVALUATOR_CONTRACT_VERSION,
        "evaluator_contract_sha256": evaluator_contract_sha256(),
        "checks": [
            {"code": "exact_feedback_preserved", "status": "PASS"},
            {"code": "repair_evidence_linked", "status": "PASS"},
            {
                "code": "declared_artifacts_repaired",
                "status": "PASS",
                "current_hashes": {"slides.json": current_hash},
            },
        ],
    }
    old_case["verification_contract_sha256"] = verification_contract_sha256(
        old_case
    )

    assert feedback_case_is_current(package, old_case) is False


def test_explicit_assertion_revision_preserves_identity_baseline_and_history(
    tmp_path: Path,
) -> None:
    package = tmp_path / "output/carousels/2026-09-05/example"
    _write_json(
        package / "slides.json",
        {"slides": [{"physical_action": "Zuv boards a commercial flight."}]},
    )
    event = _event()
    initial = ensure_feedback_case(tmp_path, package, event)
    original_baseline = dict(initial["baseline_artifact_hashes"])
    unverified = evaluate_feedback_case(tmp_path, package, event)
    assert unverified["status"] == "unverified"
    assert feedback_case_is_current(package, unverified) is False

    revised_event = {
        **event,
        "verification_assertions": [
            {
                "artifact": "slides.json",
                "json_pointer": "/slides/0/physical_action",
                "operator": "contains",
                "value": "commercial flight",
            }
        ],
    }
    revised = revise_feedback_case_assertions(
        tmp_path,
        package,
        revised_event,
        revised_event["verification_assertions"],
        revised_by="acceptance-auditor",
        reason="Replace a legacy hash-only result with an executable assertion.",
    )

    assert revised["feedback_id"] == initial["feedback_id"]
    assert revised["user_instruction_sha256"] == initial["user_instruction_sha256"]
    assert revised["baseline_artifact_hashes"] == original_baseline
    assert revised["verification_contract_revision"] == 2
    assert revised["verification_contract_history"][0]["revision"] == 1
    assert revised["evaluation_history"][0]["status"] == "unverified"
    assert revised["status"] == "pending"

    result = evaluate_feedback_case(tmp_path, package, revised_event)
    assert result["status"] == "passed"
    assert result["evaluator_contract_version"] == EVALUATOR_CONTRACT_VERSION
    assert feedback_case_is_current(package, result) is True

    tampered = {**result, "verification_contract_sha256": "sha256:" + "0" * 64}
    assert feedback_case_is_current(package, tampered) is False
    stale_evaluator = {**result, "evaluator_contract_sha256": "sha256:" + "0" * 64}
    assert feedback_case_is_current(package, stale_evaluator) is False

    _write_json(
        package / "slides.json",
        {"slides": [{"physical_action": "Aachu boards a train."}]},
    )
    assert feedback_case_is_current(package, result) is False


def test_assertion_drift_requires_explicit_revision_api(tmp_path: Path) -> None:
    package = tmp_path / "output/carousels/2026-09-05/example"
    _write_json(package / "slides.json", {"slides": [{"physical_action": "Zuv waits."}]})
    event = {
        **_event(),
        "verification_assertions": [
            {
                "artifact": "slides.json",
                "json_pointer": "/slides/0/physical_action",
                "operator": "contains",
                "value": "Zuv",
            }
        ],
    }
    ensure_feedback_case(tmp_path, package, event)
    drifted = {
        **event,
        "verification_assertions": [
            {**event["verification_assertions"][0], "value": "Aachu"}
        ],
    }

    with pytest.raises(ValueError, match="different identity"):
        evaluate_feedback_case(tmp_path, package, drifted)


def test_derived_contract_revision_replaces_stale_direction_but_keeps_exact_feedback(
    tmp_path: Path,
) -> None:
    package = tmp_path / "output/carousels/2026-09-05/example"
    _write_json(
        package / "slides.json",
        {"slides": [{"physical_action": "Zuv invites Aachu to travel."}]},
    )
    assertion = {
        "artifact": "slides.json",
        "json_pointer": "/slides/0/physical_action",
        "operator": "contains",
        "value": "Zuv",
    }
    event = {
        **_event(),
        "must_change": ["Zuv initiates the train invitation."],
        "verification_assertions": [assertion],
    }
    original = evaluate_feedback_case(tmp_path, package, event)
    assert original["status"] == "passed"

    revised = revise_feedback_case_assertions(
        tmp_path,
        package,
        event,
        must_change=["Zuv initiates the travel invitation."],
        revised_by="acceptance-auditor",
        reason="A later flight correction changes transport, not narrator ownership.",
    )
    assert revised["user_instruction_sha256"] == event["user_instruction_sha256"]
    assert revised["must_change"] == ["Zuv initiates the travel invitation."]
    assert revised["verification_contract_history"][0]["must_change"] == [
        "Zuv initiates the train invitation."
    ]
    assert revised["verification_contract_history"][0]["repair_operations"] == []
    assert revised["verification_contract_history"][0][
        "verification_assertions"
    ] == [assertion]
    assert revised["evaluation_history"][0]["status"] == "passed"

    with pytest.raises(ValueError, match="identity-derived contract"):
        evaluate_feedback_case(tmp_path, package, event)

    updated_event = {
        **event,
        "must_change": ["Zuv initiates the travel invitation."],
    }
    current = evaluate_feedback_case(tmp_path, package, updated_event)
    assert current["status"] == "passed"
    assert feedback_case_is_current(package, current) is True


def test_event_contract_drift_invalidates_stored_pass(tmp_path: Path) -> None:
    package = tmp_path / "output/carousels/2026-09-05/example"
    _write_json(
        package / "slides.json",
        {"slides": [{"physical_action": "Zuv waits."}]},
    )
    event = {
        **_event(),
        "repair_operations": [
            {
                "artifact": "slides.json",
                "json_pointer": "/slides/0/physical_action",
                "value": "Zuv flies with Aachu.",
            }
        ],
    }
    ensure_feedback_case(tmp_path, package, event)
    _write_json(
        package / "slides.json",
        {"slides": [{"physical_action": "Zuv flies with Aachu."}]},
    )
    result = evaluate_feedback_case(tmp_path, package, event)
    assert result["status"] == "passed"
    assert feedback_case_is_current(package, result, event) is True

    operation_drift = {
        **event,
        "repair_operations": [
            {**event["repair_operations"][0], "value": "Zuv takes a train."}
        ],
    }
    assert feedback_case_is_current(package, result, operation_drift) is False
    with pytest.raises(ValueError, match="identity-derived contract"):
        ensure_feedback_case(tmp_path, package, operation_drift)

    artifact_drift = {
        **event,
        "affected_artifacts": ["slides.json", "prompt-pack.json"],
    }
    assert feedback_case_is_current(package, result, artifact_drift) is False

    waiver_drift = {**event, "eval_waiver_reason": "Do not evaluate this repair."}
    assert feedback_case_is_current(package, result, waiver_drift) is False

    exact_text_drift = {**event, "user_instruction_exact": "Changed words."}
    assert feedback_case_is_current(package, result, exact_text_drift) is False
    with pytest.raises(ValueError, match="exact text"):
        evaluate_feedback_case(tmp_path, package, exact_text_drift)


def test_removed_repair_evidence_invalidates_stored_pass(tmp_path: Path) -> None:
    package = tmp_path / "output/carousels/2026-09-05/example"
    _write_json(
        package / "slides.json",
        {"slides": [{"physical_action": "Zuv waits."}]},
    )
    event = {
        **_event(),
        "verification_assertions": [
            {
                "artifact": "slides.json",
                "json_pointer": "/slides/0/physical_action",
                "operator": "contains",
                "value": "Zuv",
            }
        ],
    }
    result = evaluate_feedback_case(tmp_path, package, event)
    assert result["status"] == "passed"
    assert feedback_case_is_current(package, result, event) is True

    assert feedback_case_is_current(
        package,
        result,
        {**event, "action_taken": None},
    ) is False
    assert feedback_case_is_current(
        package,
        result,
        {**event, "resolution_evidence": []},
    ) is False
