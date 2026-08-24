from __future__ import annotations

import hashlib
import json
from pathlib import Path

from PIL import Image

from pipeline.agentic.carousel_state import derive_carousel_state
from pipeline.stages.carousel_format_contract import write_format_contract


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def write_png(path: Path, size: tuple[int, int] = (1080, 1440)) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    Image.new("RGB", size, "ivory").save(path)


def base_package(package: Path, *, status: str) -> Path:
    package.mkdir()
    write_format_contract(package, ["instagram_post"], source="test")
    identity = package / "refs" / "couple.png"
    write_png(identity, (64, 64))
    write_json(package / "slides.json", {"slides": [{"slide": 1, "copy": "Exact copy."}]})
    write_json(
        package / "prompt-pack.json",
        {
            "identity_reference_images": ["refs/couple.png"],
            "slides": [{"slide": 1, "text": "Exact copy."}],
        },
    )
    write_json(
        package / "generation-state.json",
        {"status": status, "requested_formats": ["instagram_post"]},
    )
    return package


def pixel_qa(package: Path, *, passed: bool, semantic: bool = True) -> dict:
    asset = package / ".internal" / "visual-quarantine" / "slide-01" / "attempt-01" / "instagram-post.png"
    write_png(asset)
    digest = hashlib.sha256(asset.read_bytes()).hexdigest()
    return {
        "status": "PASS" if passed else "FAIL",
        "pass": passed,
        "image_set_sha256": "sha256:test-proof",
        "checks": {
            "semantic_action": {"pass": semantic},
            "relationship_state": {"pass": True},
            "entity_anatomy_spatial": {"pass": True},
            "identity": {"pass": True},
            "text_style_dimensions": {"pass": True},
        },
        "slides": [
            {
                "slide": 1,
                "native_outputs": {
                    "instagram_post": {
                        "path": str(asset.relative_to(package)),
                        "sha256": digest,
                    }
                },
            }
        ],
    }


def test_copy_lock_is_ready_for_one_risky_proof(tmp_path: Path) -> None:
    package = tmp_path / "copy-lock"
    package.mkdir()
    write_json(package / "prompt-pack.json", {"slides": [{"slide": 1}]})

    state = derive_carousel_state(package)

    assert state.name == "copy_locked"
    assert state.next_action == "generate_risky_proof"


def test_handoff_state_does_not_require_event_a_storyboard(tmp_path: Path) -> None:
    package = base_package(tmp_path / "handoff", status="HANDOFF_READY")

    state = derive_carousel_state(package)

    assert state.name == "handoff_ready"
    assert state.blocked is False
    assert state.next_action == "generate_risky_proof"


def test_unreviewed_quarantined_proof_is_proof_ready(tmp_path: Path) -> None:
    package = base_package(tmp_path / "proof", status="GENERATED_QUARANTINED")

    state = derive_carousel_state(package)

    assert state.name == "proof_ready"
    assert state.next_action == "review_proof_pixels"


def test_failed_quarantined_proof_is_never_handoff_ready(tmp_path: Path) -> None:
    package = base_package(tmp_path / "failed", status="GENERATED_QUARANTINED")
    write_json(package / "proof-qa.json", pixel_qa(package, passed=False, semantic=False))

    state = derive_carousel_state(package)

    assert state.name == "proof_failed"
    assert state.blocked is True
    assert state.next_action == "repair_visual_premise"
    assert "proof_semantic_action_failed" in state.issue_codes


def test_batch_allowed_maps_to_generate_remaining_slides(tmp_path: Path) -> None:
    package = base_package(tmp_path / "approved", status="BATCH_ALLOWED")
    qa = pixel_qa(package, passed=True)
    write_json(package / "proof-qa.json", qa)
    state_payload = json.loads((package / "generation-state.json").read_text(encoding="utf-8"))
    state_payload["creator_approved"] = True
    write_json(package / "generation-state.json", state_payload)

    state = derive_carousel_state(package)

    assert state.name == "proof_approved"
    assert state.next_action == "generate_remaining_slides"


def test_partial_final_requires_final_qa(tmp_path: Path) -> None:
    package = tmp_path / "partial"
    package.mkdir()
    write_json(package / "final-images.json", {"status": "generated", "publishable": False})

    state = derive_carousel_state(package)

    assert state.name == "final_qa_required"
    assert state.next_action == "run_visual_qa_and_final_audit"


def test_complete_current_pixel_package_is_publishable(tmp_path: Path) -> None:
    package = base_package(tmp_path / "publishable", status="PUBLISH_READY")
    final = package / "final" / "slide-01.png"
    write_png(final)
    digest = hashlib.sha256(final.read_bytes()).hexdigest()
    write_json(
        package / "final-images.json",
        {
            "status": "PUBLISH_READY",
            "slide_count": 1,
            "slides": [
                {
                    "slide": 1,
                    "native_outputs": {
                        "instagram_post": {
                            "path": "final/slide-01.png",
                            "sha256": digest,
                            "width": 1080,
                            "height": 1440,
                        }
                    },
                }
            ],
        },
    )
    qa = pixel_qa(package, passed=True)
    qa["slides"][0]["native_outputs"]["instagram_post"] = {
        "path": "final/slide-01.png",
        "sha256": digest,
        "width": 1080,
        "height": 1440,
    }
    write_json(package / "visual-qa.json", qa)
    write_json(package / "final-audit.json", {"status": "PASS", "pass": True})

    state = derive_carousel_state(package)

    assert state.name == "publishable"
    assert state.publishable is True
    assert state.next_action == "ready_for_closeout"
