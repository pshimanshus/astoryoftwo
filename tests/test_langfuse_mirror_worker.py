from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

from pipeline.agentic import langfuse_mirror


def _enable(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("ASOT_LANGFUSE_ENABLED", "1")
    monkeypatch.setenv("LANGFUSE_PUBLIC_KEY", "present")
    monkeypatch.setenv("LANGFUSE_SECRET_KEY", "present")


def test_standard_runtime_dispatches_only_redacted_data_to_isolated_worker(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _enable(monkeypatch)
    worker = Path("/tmp/asot-test-evals-python")
    calls: list[dict[str, object]] = []
    monkeypatch.setattr(langfuse_mirror, "_worker_python", lambda: worker)

    def fake_run(command, **kwargs):
        calls.append({"command": command, **kwargs})
        return SimpleNamespace(returncode=0, stdout='{"status":"mirrored"}\n', stderr="")

    monkeypatch.setattr(langfuse_mirror.subprocess, "run", fake_run)

    result = langfuse_mirror.mirror_feedback_event(
        {
            "feedback_id": "fb-worker",
            "status": "captured",
            "user_instruction_exact": "private creator wording",
        }
    )

    assert result["status"] == "mirrored"
    assert calls[0]["command"] == [
        str(worker),
        "-m",
        "pipeline.agentic.langfuse_worker",
    ]
    assert calls[0]["timeout"] == langfuse_mirror.LANGFUSE_WORKER_TIMEOUT_SECONDS
    encoded = str(calls[0]["input"])
    assert "private creator wording" not in encoded
    assert json.loads(encoded)["feedback_id"] == "fb-worker"


def test_worker_timeout_is_nonblocking_and_does_not_expose_payload(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _enable(monkeypatch)
    monkeypatch.setattr(langfuse_mirror, "_worker_python", lambda: Path(sys.executable))

    def timeout(*_args, **_kwargs):
        raise subprocess.TimeoutExpired("private-command", 10, output="private-output")

    monkeypatch.setattr(langfuse_mirror.subprocess, "run", timeout)

    result = langfuse_mirror.mirror_feedback_event(
        {"feedback_id": "fb-timeout", "status": "captured"}
    )

    assert result["status"] == "failed_nonblocking"
    assert result["reason"] == "TimeoutExpired"
    assert "private" not in json.dumps(result)


def test_worker_revalidates_payload_integrity() -> None:
    payload = langfuse_mirror.redacted_feedback_payload(
        {"feedback_id": "fb-integrity", "status": "captured"}
    )
    payload["mirror_idempotency_sha256"] = "sha256:" + "0" * 64

    with pytest.raises(ValueError, match="integrity"):
        langfuse_mirror.validate_redacted_feedback_payload(payload)


def test_worker_rejects_new_payload_fields() -> None:
    payload = langfuse_mirror.redacted_feedback_payload(
        {"feedback_id": "fb-fields", "status": "captured"}
    )
    payload["raw_story"] = "must never leave the workspace"

    with pytest.raises(ValueError, match="unsupported fields"):
        langfuse_mirror.validate_redacted_feedback_payload(payload)
