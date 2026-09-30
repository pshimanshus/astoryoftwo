from __future__ import annotations

import hashlib
import json
import sys
import types
from pathlib import Path

import pytest

from evals.deepeval_adapter import (
    DEEPEVAL_TESTED_VERSION,
    calibration_status,
    run_deepeval_shadow,
)
from evals.runner import main as eval_main
from pipeline.agentic.langfuse_mirror import (
    LANGFUSE_TESTED_VERSION,
    candidate_event_from_annotation,
    import_annotation_candidates,
    mirror_feedback_event,
    redacted_feedback_payload,
)


ROOT = Path(__file__).resolve().parents[1]


def _write_review(
    root: Path,
    index: int,
    *,
    creator_hard_fail: bool = False,
    judge_hard_fail: bool = False,
    output_sha256: str | None = None,
) -> Path:
    package_id = f"output/carousels/package-{index % 5}"
    output_path = f"{package_id}/output-{index}.png"
    artifact = root / output_path
    artifact.parent.mkdir(parents=True, exist_ok=True)
    artifact.write_bytes(f"output-{index}".encode())
    path = root / "evals" / "calibration" / f"review-{index:02d}.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(
            {
                "creator_reviewed": True,
                "output_sha256": output_sha256
                or hashlib.sha256(artifact.read_bytes()).hexdigest(),
                "package_id": package_id,
                "output_path": output_path,
                "creator_hard_fail": creator_hard_fail,
                "judge_hard_fail": judge_hard_fail,
            }
        ),
        encoding="utf-8",
    )
    return path


def test_calibration_requires_strictly_less_than_ten_percent_disagreement(tmp_path: Path):
    for index in range(20):
        _write_review(tmp_path, index, judge_hard_fail=index < 2)

    status = calibration_status(tmp_path)

    assert status["reviewed_outputs"] == 20
    assert status["package_count"] == 5
    assert status["hard_fail_disagreement_rate"] == pytest.approx(0.10)
    assert status["calibrated"] is False

    _write_review(tmp_path, 0, judge_hard_fail=False)
    assert calibration_status(tmp_path)["calibrated"] is True


def test_calibration_rejects_malformed_and_conflicting_duplicate_evidence(tmp_path: Path):
    first = _write_review(tmp_path, 1)
    duplicate = _write_review(
        tmp_path,
        2,
        judge_hard_fail=True,
        output_sha256=json.loads(first.read_text())["output_sha256"],
    )
    first_payload = json.loads(first.read_text())
    duplicate_payload = json.loads(duplicate.read_text())
    (tmp_path / duplicate_payload["output_path"]).write_bytes(
        (tmp_path / first_payload["output_path"]).read_bytes()
    )
    malformed = tmp_path / "evals" / "calibration" / "malformed.json"
    malformed.write_text('{"creator_reviewed": true}', encoding="utf-8")

    status = calibration_status(tmp_path)

    assert duplicate.is_file()
    assert status["reviewed_outputs"] == 0
    assert status["conflicting_output_count"] == 1
    assert status["invalid_record_count"] == 1
    assert "invalid_output_sha256" in status["invalid_records"][0]["reasons"]


def test_calibration_rejects_unbound_or_changed_output_bytes(tmp_path: Path):
    review = _write_review(tmp_path, 1)
    payload = json.loads(review.read_text())
    (tmp_path / payload["output_path"]).write_bytes(b"changed-after-review")

    status = calibration_status(tmp_path)

    assert status["reviewed_outputs"] == 0
    assert status["invalid_record_count"] == 1
    assert status["invalid_records"][0]["reasons"] == ["output_sha256_mismatch"]
    assert status["artifact_policy"] == "existing_workspace_output_bound_by_sha256"


def test_deepeval_is_disabled_before_sdk_or_credentials_are_considered(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    monkeypatch.delenv("ASOT_DEEPEVAL_ENABLED", raising=False)
    monkeypatch.setenv("OPENAI_API_KEY", "must-not-be-used")

    report = run_deepeval_shadow(
        tmp_path,
        prompt="api_key=must-not-leak",
        actual_output="private@example.com",
    )

    assert report["status"] == "not_run"
    assert report["reason"] == "DeepEval shadow evaluation is disabled"
    assert report["can_gate"] is False


def test_deepeval_sdk_contract_scores_redacted_text_without_cloud_logging(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    seen_cases: list[object] = []

    class FakeCase:
        def __init__(self, **kwargs):
            self.__dict__.update(kwargs)
            seen_cases.append(self)

    class FakeParams:
        INPUT = "input"
        ACTUAL_OUTPUT = "actual_output"

    class FakeImage:
        def __init__(self, *, url, local):
            self.url = url
            self.local = local

        def __str__(self):
            return "[DEEPEVAL:IMAGE:test]"

    class FakeMetric:
        def __init__(self, *args, **kwargs):
            assert kwargs["threshold"] is None
            assert kwargs["async_mode"] is False
            self.score = 0.8
            self.reason = "scored"

        def measure(self, case):
            assert "must-not-leak" not in case.input
            assert "private@example.com" not in case.actual_output

    package = types.ModuleType("deepeval")
    metrics = types.ModuleType("deepeval.metrics")
    test_case = types.ModuleType("deepeval.test_case")
    metrics.GEval = metrics.ImageCoherenceMetric = metrics.TextToImageMetric = FakeMetric
    test_case.LLMTestCase = FakeCase
    test_case.MLLMImage = FakeImage
    test_case.SingleTurnParams = FakeParams
    monkeypatch.setitem(sys.modules, "deepeval", package)
    monkeypatch.setitem(sys.modules, "deepeval.metrics", metrics)
    monkeypatch.setitem(sys.modules, "deepeval.test_case", test_case)
    monkeypatch.setenv("ASOT_DEEPEVAL_ENABLED", "1")
    monkeypatch.setenv("OPENAI_API_KEY", "process-only-key")
    monkeypatch.delenv("ASOT_DEEPEVAL_ALLOW_MEDIA", raising=False)

    report = run_deepeval_shadow(
        tmp_path,
        prompt="api_key=must-not-leak",
        actual_output="private@example.com",
    )

    assert report["status"] == "scored"
    assert [item["name"] for item in report["metrics"] if item["status"] == "scored"] == [
        "prompt_adherence",
        "task_completion",
    ]
    assert seen_cases
    assert report["can_gate"] is False


def test_deepeval_refuses_media_outside_workspace(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    outside = tmp_path.parent / "outside.png"
    outside.write_bytes(b"not-sent")
    monkeypatch.setenv("ASOT_DEEPEVAL_ENABLED", "1")
    monkeypatch.setenv("OPENAI_API_KEY", "process-only-key")

    report = run_deepeval_shadow(
        tmp_path,
        prompt="safe",
        actual_output="safe",
        image_paths=[str(outside)],
    )

    assert report["status"] == "not_run"
    assert report["reason"] == "image or reference input unavailable"


def test_langfuse_payload_is_strictly_allowlisted_and_redacted():
    event = {
        "feedback_id": "fb-safe",
        "learning_event_id": "event-safe",
        "user_instruction_exact": "private creator words",
        "root_cause": "private@example.com sk-secretsecretsecret",
        "primary_diagnosis": "scene_action",
        "scope": "slide",
        "status": "learning_declined",
        "generation_effect": "shared",
    }

    payload = redacted_feedback_payload(
        event,
        eval_scores={"deterministic": "passed", "unsafe-name!": "private", "nan": float("nan")},
    )

    encoded = json.dumps(payload)
    assert "private creator words" not in encoded
    assert "private@example.com" not in encoded
    assert "sk-secret" not in encoded
    assert payload["status"] == "learning_declined"
    assert payload["eval_scores"] == {"deterministic": "passed"}
    assert payload["mirror_idempotency_sha256"].startswith("sha256:")


def test_langfuse_disabled_missing_auth_and_exporter_outage_are_nonblocking(
    monkeypatch: pytest.MonkeyPatch,
):
    event = {"feedback_id": "fb-safe", "status": "captured"}
    monkeypatch.delenv("ASOT_LANGFUSE_ENABLED", raising=False)
    assert mirror_feedback_event(event)["status"] == "disabled"

    monkeypatch.setenv("ASOT_LANGFUSE_ENABLED", "1")
    monkeypatch.delenv("LANGFUSE_PUBLIC_KEY", raising=False)
    monkeypatch.delenv("LANGFUSE_SECRET_KEY", raising=False)
    assert mirror_feedback_event(event)["status"] == "not_run"

    monkeypatch.setenv("LANGFUSE_PUBLIC_KEY", "present")
    monkeypatch.setenv("LANGFUSE_SECRET_KEY", "present")

    def outage(_payload):
        raise ConnectionError("private outage detail")

    failed = mirror_feedback_event(event, exporter=outage)
    assert failed["status"] == "failed_nonblocking"
    assert failed["reason"] == "ConnectionError"
    assert "private outage detail" not in json.dumps(failed)


def test_annotation_import_is_validated_idempotent_and_candidate_only():
    annotation = {
        "id": "score-123",
        "source": "ANNOTATION",
        "data_type": "TEXT",
        "string_value": "\nThe umbrella hand is still visually wrong.\n",
        "metadata": {"scope": "slide"},
    }

    candidate = candidate_event_from_annotation(annotation)
    result = import_annotation_candidates(
        [
            annotation,
            annotation,
            {**annotation, "string_value": "Conflicting retry."},
            {**annotation, "id": "api-score", "source": "API"},
        ]
    )

    assert candidate["candidate_status"] == "pending_local_review"
    assert candidate["source"] == "langfuse_annotation_candidate"
    assert candidate["user_instruction_exact"].startswith("\n")
    assert candidate["user_instruction_exact"].endswith("\n")
    assert "status" not in candidate
    assert result["candidate_count"] == 1
    assert result["duplicate_count"] == 1
    assert len(result["invalid"]) == 2
    assert any("conflicting content" in item["reason"] for item in result["invalid"])
    assert result["persistence"] == "none"

    replay = import_annotation_candidates(
        [annotation],
        existing_annotation_ids=[candidate["external_annotation_id_sha256"]],
    )
    assert replay["status"] == "no_new_candidates"
    assert replay["duplicate_count"] == 1


def test_calibration_status_cli_reports_presence_only(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
):
    monkeypatch.setenv("OPENAI_API_KEY", "secret-evaluator-value")
    monkeypatch.setenv("LANGFUSE_PUBLIC_KEY", "secret-public-value")
    monkeypatch.setenv("LANGFUSE_SECRET_KEY", "secret-private-value")
    monkeypatch.delenv("ASOT_DEEPEVAL_ENABLED", raising=False)
    monkeypatch.delenv("ASOT_LANGFUSE_ENABLED", raising=False)

    assert eval_main(["--workspace-root", str(tmp_path), "calibration-status"]) == 0
    output = capsys.readouterr().out
    report = json.loads(output)

    assert report["external_calls"] == "not_run"
    assert report["deepeval"]["environment"]["evaluator_credentials_present"] is True
    assert report["langfuse"]["environment"]["credentials_present"] is True
    assert report["deepeval"]["environment"]["isolated_setup_command"] == (
        "make feedback-integrations-setup"
    )
    assert report["langfuse"]["environment"]["isolated_setup_command"] == (
        "make feedback-integrations-setup"
    )
    assert "secret-evaluator-value" not in output
    assert "secret-public-value" not in output
    assert "secret-private-value" not in output


def test_isolated_setup_target_stays_pinned_to_adapter_contracts():
    makefile = (ROOT / "Makefile").read_text(encoding="utf-8")

    assert "FEEDBACK_INTEGRATIONS_VENV ?= .venv-evals" in makefile
    assert f"'deepeval=={DEEPEVAL_TESTED_VERSION}'" in makefile
    assert f"'langfuse=={LANGFUSE_TESTED_VERSION}'" in makefile
