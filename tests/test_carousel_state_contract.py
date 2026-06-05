from __future__ import annotations

import json
from pathlib import Path

from pipeline.agentic.carousel_state import derive_carousel_state


def write_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")


def test_handoff_package_derives_handoff_ready_state(tmp_path: Path) -> None:
    package = tmp_path / "handoff"
    package.mkdir()
    write_json(package / "prompt-pack.json", {"slides": [{"slide": 1}]})
    write_json(package / "image-generation.json", {"status": "handoff_ready"})
    write_json(package / "final-images.json", {"status": "handoff_ready", "publishable": False})

    state = derive_carousel_state(package)

    assert state.name == "handoff_ready"
    assert state.publishable is False
    assert state.blocked is False
    assert state.next_action == "generate_with_identity_refs"


def test_blocker_issue_derives_blocked_state(tmp_path: Path) -> None:
    package = tmp_path / "blocked"
    package.mkdir()
    (package / "raw-scene-row.md").write_text("STATUS: REJECTED\n", encoding="utf-8")
    write_json(package / "visual-plan-quality.json", {"status": "PASS", "can_generate": True})

    state = derive_carousel_state(package)

    assert state.name == "blocked"
    assert state.publishable is False
    assert state.blocked is True
    assert "raw_scene_rejected_but_generation_allowed" in state.issue_codes


def test_publishable_requires_final_audit_and_no_doctor_blockers(tmp_path: Path) -> None:
    package = tmp_path / "publishable"
    package.mkdir()
    write_json(
        package / "final-images.json",
        {
            "status": "generated",
            "done": True,
            "publishable": True,
            "slide_count": 1,
            "slides": [{"slide": 1}],
        },
    )
    write_json(package / "final-audit.json", {"status": "PASS", "pass": True})
    (package / "visual-qa.md").write_text("- [x] PASS final files\n", encoding="utf-8")
    (package / "final").mkdir()
    (package / "final" / "slide-01.png").write_bytes(b"not a real png")
    (package / "final-reels-stories").mkdir()
    (package / "final-reels-stories" / "slide-01.png").write_bytes(b"not a real png")

    state = derive_carousel_state(package)

    assert state.name == "publishable"
    assert state.publishable is True
    assert state.blocked is False


def test_generated_files_without_publishable_audit_derives_partial_final(tmp_path: Path) -> None:
    package = tmp_path / "partial"
    package.mkdir()
    write_json(package / "final-images.json", {"status": "generated", "done": False, "publishable": False})

    state = derive_carousel_state(package)

    assert state.name == "partial_final"
    assert state.publishable is False
    assert state.next_action == "run_visual_qa_and_final_audit"
