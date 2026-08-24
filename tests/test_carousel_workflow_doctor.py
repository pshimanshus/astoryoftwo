from __future__ import annotations

import hashlib
import json
from pathlib import Path

from PIL import Image

from pipeline.agentic.workflow_doctor import inspect_carousel_package
from pipeline.stages.carousel_format_contract import write_format_contract


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def write_png(path: Path, size: tuple[int, int] = (1080, 1440)) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    Image.new("RGB", size, "ivory").save(path)


def codes(package: Path) -> set[str]:
    return {issue.code for issue in inspect_carousel_package(package).issues}


def base_package(package: Path, *, status: str) -> Path:
    package.mkdir()
    write_format_contract(package, ["instagram_post"], source="test")
    write_png(package / "refs" / "couple.png", (64, 64))
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


def qa_for_asset(package: Path, asset: Path, *, semantic: bool = True, passed: bool = True) -> dict:
    digest = hashlib.sha256(asset.read_bytes()).hexdigest()
    return {
        "status": "PASS" if passed else "FAIL",
        "pass": passed,
        "image_set_sha256": "sha256:test-image-set",
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


def final_manifest(package: Path, asset: Path) -> dict:
    digest = hashlib.sha256(asset.read_bytes()).hexdigest()
    with Image.open(asset) as image:
        width, height = image.size
    return {
        "status": "PUBLISH_READY",
        "publishable": True,
        "slide_count": 1,
        "slides": [
            {
                "slide": 1,
                "native_outputs": {
                    "instagram_post": {
                        "path": str(asset.relative_to(package)),
                        "sha256": digest,
                        "width": width,
                        "height": height,
                    }
                },
            }
        ],
    }


def test_handoff_does_not_require_event_a_or_agent_room_artifacts(tmp_path: Path) -> None:
    package = base_package(tmp_path / "handoff", status="HANDOFF_READY")

    report = inspect_carousel_package(package)

    assert report.blocked is False
    assert "director_storyboard_failed" not in codes(package)
    assert "missing_visual_debate" not in codes(package)
    assert "missing_post_copy_visual_room" not in codes(package)


def test_handoff_requires_real_identity_reference_files(tmp_path: Path) -> None:
    package = base_package(tmp_path / "identity", status="HANDOFF_READY")
    (package / "refs" / "couple.png").unlink()

    assert "identity_references_missing" in codes(package)


def test_failed_semantic_action_is_the_proof_blocker(tmp_path: Path) -> None:
    package = base_package(tmp_path / "semantic", status="GENERATED_QUARANTINED")
    asset = package / ".internal" / "visual-quarantine" / "proof.png"
    write_png(asset)
    write_json(package / "proof-qa.json", qa_for_asset(package, asset, semantic=False, passed=False))

    report = inspect_carousel_package(package)

    assert "proof_semantic_action_failed" in codes(package)
    issue = next(issue for issue in report.issues if issue.code == "proof_semantic_action_failed")
    assert issue.next_action == "repair_visual_premise"


def test_stale_pixel_hash_invalidates_proof_pass(tmp_path: Path) -> None:
    package = base_package(tmp_path / "stale", status="QA_PASS_CANDIDATE")
    asset = package / ".internal" / "visual-quarantine" / "proof.png"
    write_png(asset)
    write_json(package / "proof-qa.json", qa_for_asset(package, asset))
    asset.write_bytes(b"changed after review")

    assert "proof_pixel_qa_incomplete" in codes(package)


def test_batch_requires_current_pixel_pass_and_creator_approval(tmp_path: Path) -> None:
    package = base_package(tmp_path / "batch", status="BATCH_ALLOWED")
    asset = package / ".internal" / "visual-quarantine" / "proof.png"
    write_png(asset)
    write_json(package / "proof-qa.json", qa_for_asset(package, asset))

    assert "batch_without_approved_proof" in codes(package)


def test_batch_accepts_creator_approval_embedded_in_current_proof_qa(tmp_path: Path) -> None:
    package = base_package(tmp_path / "approved-batch", status="BATCH_ALLOWED")
    asset = package / ".internal" / "visual-quarantine" / "proof.png"
    write_png(asset)
    qa = qa_for_asset(package, asset)
    qa["creator_approval"] = {
        "status": "APPROVED",
        "approved": True,
        "approved_by": "creator",
        "image_set_sha256": qa["image_set_sha256"],
    }
    write_json(package / "proof-qa.json", qa)

    assert "batch_without_approved_proof" not in codes(package)


def test_publishable_claim_requires_actual_final_pixel_gates(tmp_path: Path) -> None:
    package = base_package(tmp_path / "final", status="PUBLISH_READY")
    final = package / "final" / "slide-01.png"
    write_png(final)
    write_json(package / "final-images.json", final_manifest(package, final))
    qa = qa_for_asset(package, final)
    write_json(package / "visual-qa.json", qa)
    write_json(package / "final-audit.json", {"status": "PASS", "pass": True})

    assert inspect_carousel_package(package).blocked is False


def test_wrong_final_dimensions_cannot_publish(tmp_path: Path) -> None:
    package = base_package(tmp_path / "wrong-size", status="PUBLISH_READY")
    final = package / "final" / "slide-01.png"
    write_png(final, (1080, 1080))
    write_json(package / "final-images.json", final_manifest(package, final))
    write_json(package / "visual-qa.json", qa_for_asset(package, final))
    write_json(package / "final-audit.json", {"status": "PASS", "pass": True})

    assert "wrong_final_image_dimensions" in codes(package)


def test_rejected_phrase_only_blocks_active_generation_artifacts(tmp_path: Path) -> None:
    package = tmp_path / "correction"
    package.mkdir()
    write_json(
        package / "creator-correction.json",
        {"rejected_route_phrases": ["old raft metaphor"], "active_artifact_paths": ["prompt-pack.json"]},
    )
    write_json(package / "prompt-pack.json", {"slides": [{"slide": 1, "prompt": "old raft metaphor"}]})
    (package / "archive.md").write_text("old raft metaphor", encoding="utf-8")

    assert "stale_artifact_carryover" in codes(package)

    write_json(package / "prompt-pack.json", {"slides": [{"slide": 1, "prompt": "clear dining-table action"}]})
    assert "stale_artifact_carryover" not in codes(package)
