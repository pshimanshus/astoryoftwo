from __future__ import annotations

import json

from pipeline.agentic.generation_capability import detect_generation_capability, write_generation_capability


def test_default_generation_capability_is_handoff_only(tmp_path, monkeypatch) -> None:
    monkeypatch.delenv("CODEX_CAN_ATTACH_IDENTITY_REFS", raising=False)

    capability = detect_generation_capability(tmp_path)

    assert capability["can_attach_identity_refs"] is False
    assert capability["package_terminal_state"] == "HANDOFF_READY_FOR_CODEX_WITH_IDENTITY"


def test_generation_capability_accepts_env_override(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("CODEX_CAN_ATTACH_IDENTITY_REFS", "1")

    capability = detect_generation_capability(tmp_path)

    assert capability["can_attach_identity_refs"] is True
    assert capability["package_terminal_state"] == "publishable_after_visual_qa"


def test_write_generation_capability_json(tmp_path, monkeypatch) -> None:
    monkeypatch.delenv("CODEX_CAN_ATTACH_IDENTITY_REFS", raising=False)

    payload = write_generation_capability(tmp_path)

    written = json.loads((tmp_path / "generation-capability.json").read_text(encoding="utf-8"))
    assert written == payload
    assert written["capability_source"] == "environment"
