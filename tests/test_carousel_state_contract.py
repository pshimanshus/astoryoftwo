from __future__ import annotations

import json
from pathlib import Path

from PIL import Image

from pipeline.agentic.checks.ocr_text import check_ocr_text
from pipeline.agentic.checks.palette import check_palette
from pipeline.agentic.checks.prompt_constraints import check_prompt_constraints
from pipeline.agentic.carousel_state import derive_carousel_state
from pipeline.agentic.workflow_doctor import inspect_carousel_package


def write_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")


def write_png(path: Path, size: tuple[int, int]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    Image.new("RGB", size, color=(248, 243, 232)).save(path)


def valid_prompt_text(slide_text: str) -> str:
    return "\n".join(
        [
            "Generate an illustration.",
            "PALETTE: warm ivory paper.",
            "HARD FAIL: yellow, sepia, parchment.",
            "Style lock: Observational Intimacy Premium.",
            f"ON-IMAGE TEXT: {slide_text}",
            "Each identity reference image must be attached to the call.",
            "Preserve Aachu and Zuv face identity.",
            "PAPER TONE LOCK: neutral off-white paper only.",
            "STAGE-SCENE / VISUAL RECEIPT: text completes the scene.",
            "SHOT LADDER / VISUAL VARIETY: vary camera, action, and who is visible.",
            "RELATIONSHIP MOTION: do not make Zuv the default caretaker.",
            "Aachu is 5'6\" and Zuv is 5'8\".",
            "Brandmark: tiny handwritten @a.storyof.two in top-right.",
            "No split-screen divider may appear in final art.",
            slide_text,
        ]
    )


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


def test_blocked_generation_manifest_derives_blocked_state(tmp_path: Path) -> None:
    package = tmp_path / "blocked-generation"
    package.mkdir()
    write_json(package / "prompt-pack.json", {"slides": [{"slide": 1}]})
    write_json(package / "image-generation.json", {"status": "blocked", "reason": "dimension gate failed"})
    write_json(package / "final-images.json", {"status": "blocked", "publishable": False})
    (package / "image-generation-blocker.md").write_text("status: BLOCKED\n", encoding="utf-8")

    state = derive_carousel_state(package)

    assert state.name == "blocked"
    assert state.publishable is False
    assert state.blocked is True


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
    write_png(package / "final" / "slide-01.png", (1080, 1440))
    write_png(package / "final-reels-stories" / "slide-01.png", (1080, 1920))

    state = derive_carousel_state(package)

    assert state.name == "publishable"
    assert state.publishable is True
    assert state.blocked is False


def test_publishable_claim_with_fake_pngs_derives_blocked_state(tmp_path: Path) -> None:
    package = tmp_path / "fake-pngs"
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

    assert state.name == "blocked"
    assert state.publishable is False
    assert state.blocked is True
    assert "invalid_final_image_asset" in state.issue_codes


def test_compact_publish_ready_package_passes_combined_gates(
    tmp_path: Path,
    monkeypatch,
) -> None:
    import pipeline.agentic.checks.ocr_text as ocr_mod

    package = tmp_path / "publish-ready"
    package.mkdir()
    slide_text = "dumber"
    identity_ref = tmp_path / "identity.jpg"
    write_png(identity_ref, (1080, 1440))
    write_json(
        package / "manifest.json",
        {
            "identity_references": [
                {"path": str(identity_ref), "role": "Aachu/Zuv face consistency reference"}
            ],
        },
    )
    write_json(
        package / "prompt-pack.json",
        {
            "slides": [{"slide": 1, "text": slide_text}],
            "identity_reference_images": [str(identity_ref)],
            "identity_dossier_reference_images": [str(identity_ref)],
        },
    )
    write_json(
        package / "final-images.json",
        {
            "status": "publish_ready",
            "done": True,
            "publishable": True,
            "slide_count": 1,
            "slides": [{"slide": 1}],
        },
    )
    write_json(package / "final-audit.json", {"status": "PASS", "pass": True})
    (package / "visual-qa.md").write_text("- [x] PASS final files\n", encoding="utf-8")
    post = package / "final" / "slide-01.png"
    story = package / "final-reels-stories" / "slide-01.png"
    write_png(post, (1080, 1440))
    write_png(story, (1080, 1920))
    prompt = package / "codex-image-prompts" / "instagram-post" / "slide-01.prompt.txt"
    prompt.parent.mkdir(parents=True)
    prompt.write_text(valid_prompt_text(slide_text), encoding="utf-8")

    monkeypatch.setattr(ocr_mod, "_easyocr_available", lambda: True)

    class _StubReader:
        def readtext(self, _path, detail=0):
            return [slide_text]

    monkeypatch.setattr(ocr_mod, "_reader", lambda: _StubReader())

    report = inspect_carousel_package(package)
    state = derive_carousel_state(package)

    assert report.blocked is False
    assert state.name == "publishable"
    assert check_prompt_constraints(prompt, expected_text=slide_text).status == "PASS"
    assert check_palette(post).status == "PASS"
    assert check_ocr_text(post, slide_text, publish_mode=True).status == "PASS"


def test_generated_files_without_publishable_audit_derives_partial_final(tmp_path: Path) -> None:
    package = tmp_path / "partial"
    package.mkdir()
    write_json(package / "final-images.json", {"status": "generated", "done": False, "publishable": False})

    state = derive_carousel_state(package)

    assert state.name == "partial_final"
    assert state.publishable is False
    assert state.next_action == "run_visual_qa_and_final_audit"


def test_empty_final_directories_do_not_count_as_generated_output(tmp_path: Path) -> None:
    package = tmp_path / "empty-final-dirs"
    package.mkdir()
    write_json(package / "final-images.json", {"status": "handoff_ready", "done": False, "publishable": False})
    (package / "final").mkdir()
    (package / "final-reels-stories").mkdir()

    state = derive_carousel_state(package)

    assert state.name != "partial_final"
    assert state.name == "handoff_ready"
    assert state.publishable is False
