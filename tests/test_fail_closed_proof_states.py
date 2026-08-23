from __future__ import annotations

import json
import hashlib
from pathlib import Path
from unittest.mock import patch

import pytest
from PIL import Image

from pipeline.agentic.workflow_doctor import inspect_carousel_package
from pipeline.stages.codex_builtin_image_generation import (
    accept_failed_proof_by_creator,
    build_compiled_prompt_handoff,
    image_set_sha256,
    load_attempt_ledger,
    next_retry_count,
    package_codex_builtin_outputs,
    prepare_codex_builtin_image_generation,
    promote_quarantined_codex_builtin_outputs,
    recompile_failed_proof_handoff,
    retry_prompt_handoff_attestation_issues,
    run_fail_closed_visual_worker,
    validate_exact_image_visual_qa,
    validate_quarantine_integrity,
    visual_qa_issues_fingerprint,
)
from pipeline.stages.carousel_format_contract import write_format_contract
from pipeline.stages.carousel_generation_state import GenerationStatus, write_generation_state


def _png(path: Path, size: tuple[int, int]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    Image.new("RGB", size, "ivory").save(path)


def _package(tmp_path: Path) -> tuple[Path, dict[str, list[Path]]]:
    package = tmp_path / "package"
    package.mkdir()
    write_format_contract(package, ["instagram_post", "reels_stories"], source="test")
    (package / "prompt-pack.json").write_text(
        json.dumps(
            {
                "slides": [
                    {
                        "slide": 1,
                        "text": "Proof",
                        "prompt": "Object-only repair receipt with layered environment.",
                    }
                ]
            }
        ),
        encoding="utf-8",
    )
    (package / "slides.json").write_text(
        json.dumps([{"slide": 1, "copy": "Proof", "visual": "Object-only repair receipt."}]),
        encoding="utf-8",
    )
    (package / "visual-plan-quality.json").write_text("{}", encoding="utf-8")
    (package / "manifest.json").write_text(
        json.dumps(
            {
                "source_story": "story",
                "title": "title",
                "slug": "slug",
                "date": "2026-07-20",
                "reference_images": [],
            }
        ),
        encoding="utf-8",
    )
    (package / "concept.json").write_text("{}", encoding="utf-8")
    (package / "copy.json").write_text("{}", encoding="utf-8")
    for prompt_folder in ("instagram-post", "reels-stories"):
        prompt_dir = package / "codex-image-prompts" / prompt_folder
        prompt_dir.mkdir(parents=True, exist_ok=True)
        (prompt_dir / "slide-01.prompt.txt").write_text(
            f"compiled {prompt_folder} prompt",
            encoding="utf-8",
        )
        (prompt_dir / "slide-01.md").write_text(
            f"handoff for {prompt_folder}",
            encoding="utf-8",
        )
    formats = ["instagram_post", "reels_stories"]
    compiled_handoff = build_compiled_prompt_handoff(
        package,
        slide_numbers=[1],
        output_formats=formats,
    )
    write_generation_state(
        package,
        status=GenerationStatus.HANDOFF_READY,
        backend="codex_builtin",
        generation_mode="model_native_publishable",
        slide_count=1,
        slides=[{"slide": 1, "status": "awaiting_codex_builtin_image"}],
        extra={
            "requested_formats": formats,
            "compiled_prompt_handoff": compiled_handoff,
        },
    )
    instagram = tmp_path / "generated" / "instagram.png"
    story = tmp_path / "generated" / "story.png"
    _png(instagram, (1080, 1440))
    _png(story, (1080, 1920))
    return package, {"instagram_post": [instagram], "reels_stories": [story]}


def _proof_package(tmp_path: Path) -> tuple[Path, Path]:
    package = tmp_path / "proof-package"
    package.mkdir()
    write_format_contract(package, ["instagram_post"], source="test")
    prompt_slides = [
        {
            "slide": number,
            "text": f"Slide {number}",
            "prompt": f"Prompt for slide {number}",
        }
        for number in range(1, 12)
    ]
    (package / "prompt-pack.json").write_text(
        json.dumps({"slides": prompt_slides}),
        encoding="utf-8",
    )
    (package / "slides.json").write_text(
        json.dumps(
            [
                {
                    "slide": number,
                    "copy": f"Slide {number}",
                    "visual": f"Visual for slide {number}",
                }
                for number in range(1, 12)
            ]
        ),
        encoding="utf-8",
    )
    (package / "visual-plan-quality.json").write_text("{}", encoding="utf-8")
    prompt_dir = package / "codex-image-prompts" / "instagram-post"
    prompt_dir.mkdir(parents=True)
    (prompt_dir / "slide-09.prompt.txt").write_text(
        "compiled proof prompt",
        encoding="utf-8",
    )
    (prompt_dir / "slide-09.md").write_text(
        "proof handoff",
        encoding="utf-8",
    )
    compiled_handoff = build_compiled_prompt_handoff(
        package,
        slide_numbers=[9],
        output_formats=["instagram_post"],
    )
    write_generation_state(
        package,
        status=GenerationStatus.HANDOFF_READY,
        backend="codex_builtin",
        generation_mode="model_native_publishable",
        # Legacy proof handoffs recorded the full deck count despite exposing
        # one compiled slide. Packaging must migrate this to truthful scope.
        slide_count=11,
        slides=[{"slide": 9, "status": "awaiting_codex_builtin_image"}],
        extra={
            "requested_formats": ["instagram_post"],
            "compiled_prompt_handoff": compiled_handoff,
            "requested_proof_slide": 9,
        },
    )
    generated = tmp_path / "generated" / "proof-slide-09.png"
    _png(generated, (1086, 1448))
    return package, generated


def _failed_retry_package(tmp_path: Path) -> tuple[Path, Path, dict]:
    package, generated = _proof_package(tmp_path)
    contact_sheet = tmp_path / "identity-face-contact-sheet.jpg"
    identity = tmp_path / "identity.jpg"
    _png(contact_sheet, (64, 64))
    _png(identity, (64, 64))
    prompt_pack = json.loads((package / "prompt-pack.json").read_text(encoding="utf-8"))
    prompt_pack["identity_dossier_reference_images"] = [str(contact_sheet)]
    prompt_pack["identity_reference_images"] = [str(identity)]
    prompt_pack["style_reference_images"] = []
    (package / "prompt-pack.json").write_text(json.dumps(prompt_pack), encoding="utf-8")
    state = json.loads((package / "image-generation.json").read_text(encoding="utf-8"))
    state["compiled_prompt_handoff"] = build_compiled_prompt_handoff(
        package,
        slide_numbers=[9],
        output_formats=["instagram_post"],
    )
    for filename in ("image-generation.json", "final-images.json"):
        (package / filename).write_text(json.dumps(state), encoding="utf-8")
    for filename in (
        "identity-consistency-review.json",
        "review.json",
        "layer-e-story-selling.json",
        "stage-reviews.json",
    ):
        (package / filename).write_text("{}", encoding="utf-8")

    with (
        patch(
            "pipeline.stages.codex_builtin_image_generation.visual_plan_quality_gate_reason",
            return_value=None,
        ),
        patch(
            "pipeline.stages.codex_builtin_image_generation.identity_consistency_gate_reason",
            return_value=None,
        ),
    ):
        quarantined = package_codex_builtin_outputs(
            package,
            generated_paths_by_format={"instagram_post": [generated]},
            proof_slide=9,
        )
    qa = _passing_qa(quarantined)
    qa["reviews"]["storytelling_richness_text_style"]["pass"] = False
    (package / "visual-qa.json").write_text(json.dumps(qa), encoding="utf-8")
    with (
        patch(
            "pipeline.stages.codex_builtin_image_generation.visual_plan_quality_gate_reason",
            return_value=None,
        ),
        patch(
            "pipeline.stages.codex_builtin_image_generation.identity_consistency_gate_reason",
            return_value=None,
        ),
        patch(
            "pipeline.stages.codex_builtin_image_generation.validate_frame_readability",
            return_value=[],
        ),
    ):
        failed = promote_quarantined_codex_builtin_outputs(package)
    assert failed["status"] == "GENERATED_QUARANTINED"
    assert failed["visual_qa_issues"]
    return package, generated, failed


def _replace_failed_issue_evidence(
    package: Path,
    failed: dict,
    issues: list[str],
) -> dict:
    updated = json.loads(json.dumps(failed))
    updated["visual_qa_issues"] = list(issues)
    for filename in ("image-generation.json", "final-images.json"):
        (package / filename).write_text(json.dumps(updated), encoding="utf-8")
    ledger_path = package / ".internal" / "visual-qa-attempts.json"
    ledger = json.loads(ledger_path.read_text(encoding="utf-8"))
    ledger["attempts"][-1]["qa_issues"] = list(issues)
    ledger["attempts"][-1]["targeted_repair_instructions"] = [
        f"Repair legacy failure: {issue}" for issue in issues
    ]
    ledger_path.write_text(json.dumps(ledger), encoding="utf-8")
    return updated


def _blocked_failed_proof(tmp_path: Path) -> tuple[Path, dict]:
    """Promote the one-attempt fixture to a truthful attempt-03 blocked state."""

    package, _, failed = _failed_retry_package(tmp_path)
    old_quarantine = (
        package / ".internal" / "visual-quarantine" / "attempt-01"
    )
    new_quarantine = (
        package / ".internal" / "visual-quarantine" / "attempt-03"
    )
    old_quarantine.replace(new_quarantine)

    blocked = json.loads(json.dumps(failed))
    encoded = json.dumps(blocked).replace("attempt-01", "attempt-03")
    blocked = json.loads(encoded)
    blocked.update(
        {
            "status": "BLOCKED_VISUAL_QA",
            "proof_state": "BLOCKED_VISUAL_QA",
            "retry_count": 2,
            "retries_remaining": 0,
            "quarantine_dir": (
                ".internal/visual-quarantine/attempt-03"
            ),
            "reason": "Visual QA failed after all allowed proof attempts.",
        }
    )
    for filename in ("image-generation.json", "final-images.json"):
        (package / filename).write_text(
            json.dumps(blocked),
            encoding="utf-8",
        )

    ledger_path = package / ".internal" / "visual-qa-attempts.json"
    ledger = json.loads(ledger_path.read_text(encoding="utf-8"))
    current = ledger["attempts"][-1]
    attempts = []
    for retry_count in range(3):
        attempt = json.loads(json.dumps(current))
        attempt.update(
            {
                "attempt": retry_count + 1,
                "retry_count": retry_count,
                "status": "QA_FAILED",
            }
        )
        attempts.append(attempt)
    ledger["attempts"] = attempts
    ledger_path.write_text(json.dumps(ledger), encoding="utf-8")

    visual_qa_path = package / blocked["visual_qa_path"]
    visual_qa = json.loads(visual_qa_path.read_text(encoding="utf-8"))
    visual_qa["status"] = "FAIL"
    visual_qa["proof_state"] = "BLOCKED_VISUAL_QA"
    visual_qa_path.write_text(json.dumps(visual_qa), encoding="utf-8")
    return package, blocked


def _write_failed_proof_creator_approval(
    package: Path,
    state: dict,
    **overrides: object,
) -> Path:
    issues = state["visual_qa_issues"]
    approval: dict[str, object] = {
        "status": "APPROVED",
        "approved": True,
        "image_set_sha256": state["image_set_sha256"],
        "approved_by": "creator",
        "evidence": "Creator reviewed attempt 03 and accepts these exact exceptions.",
        "accepts_known_qa_exceptions": True,
        "acknowledged_visual_qa_issues": list(issues),
        "acknowledged_visual_qa_issues_fingerprint": (
            visual_qa_issues_fingerprint(issues)
        ),
    }
    approval.update(overrides)
    approval_path = package / ".internal" / "creator-failed-proof-approval.json"
    approval_path.write_text(json.dumps(approval), encoding="utf-8")
    return approval_path


def _prepared_creator_override_handoff(tmp_path: Path) -> tuple[Path, dict]:
    package, failed = _blocked_failed_proof(tmp_path)
    approval_path = _write_failed_proof_creator_approval(package, failed)
    accept_failed_proof_by_creator(package, approval_path)
    passing_constraint = type(
        "Constraint",
        (),
        {"status": "PASS", "reason": ""},
    )()
    with (
        patch(
            "pipeline.stages.codex_builtin_image_generation.visual_plan_quality_gate_reason",
            return_value=None,
        ),
        patch(
            "pipeline.stages.codex_builtin_image_generation.identity_consistency_gate_reason",
            return_value=None,
        ),
        patch(
            "pipeline.stages.codex_builtin_image_generation.house_style_consistency_gate_reason",
            return_value=None,
        ),
        patch(
            "pipeline.stages.codex_builtin_image_generation.layer_e_gate_reason",
            return_value=None,
        ),
        patch(
            "pipeline.stages.codex_builtin_image_generation.pre_generation_review_gate_reason",
            return_value=None,
        ),
        patch(
            "pipeline.stages.codex_builtin_image_generation.check_prompt_constraints",
            return_value=passing_constraint,
        ),
    ):
        handoff = prepare_codex_builtin_image_generation(package)
    (package / "identity-consistency-review.json").write_text(
        json.dumps({"status": "PASS"}),
        encoding="utf-8",
    )
    return package, handoff


def _inspect_creator_override_fixture(package: Path):
    """Ignore fixture-only legacy gaps outside the override branch under test."""

    with (
        patch(
            "pipeline.agentic.workflow_doctor._qa_asset_hash_issues",
            return_value=[],
        ),
        patch(
            "pipeline.agentic.workflow_doctor.validate_director_storyboard",
            return_value=[],
        ),
    ):
        return inspect_carousel_package(package)


def _full_deck_generated_sources(
    tmp_path: Path,
    *,
    slide_count: int = 11,
    size: tuple[int, int] = (1080, 1440),
) -> dict[str, list[Path]]:
    generated_dir = tmp_path / "generated-full-deck"
    paths: list[Path] = []
    for slide_number in range(1, slide_count + 1):
        path = generated_dir / f"slide-{slide_number:02d}.png"
        _png(path, size)
        paths.append(path)
    return {"instagram_post": paths}


def _package_creator_override_full_deck(
    package: Path,
    generated: dict[str, list[Path]],
) -> dict:
    with (
        patch(
            "pipeline.stages.codex_builtin_image_generation.visual_plan_quality_gate_reason",
            return_value=None,
        ),
        patch(
            "pipeline.stages.codex_builtin_image_generation.identity_consistency_gate_reason",
            return_value=None,
        ),
    ):
        return package_codex_builtin_outputs(
            package,
            generated_paths_by_format=generated,
        )


def test_creator_can_accept_exact_failed_proof_for_batch_only(
    tmp_path: Path,
) -> None:
    package, failed = _blocked_failed_proof(tmp_path)
    approval_path = _write_failed_proof_creator_approval(package, failed)
    visual_qa_path = package / failed["visual_qa_path"]
    visual_qa_before = visual_qa_path.read_bytes()
    original_issues = list(failed["visual_qa_issues"])

    accepted = accept_failed_proof_by_creator(package, approval_path)

    persisted = json.loads(
        (package / "image-generation.json").read_text(encoding="utf-8")
    )
    final_state = json.loads(
        (package / "final-images.json").read_text(encoding="utf-8")
    )
    latest_attempt = load_attempt_ledger(package)["attempts"][-1]
    assert accepted == persisted == final_state
    assert accepted["status"] == "BATCH_ALLOWED"
    assert accepted["proof_state"] == "BATCH_ALLOWED"
    assert accepted["creator_override"] is True
    assert accepted["batch_generation_allowed"] is True
    assert accepted["publishable"] is False
    assert accepted["proof_qa_passed"] is False
    assert accepted["visual_qa_status"] == "QA_FAILED"
    assert accepted["visual_qa_issues"] == original_issues
    assert accepted["known_qa_exceptions"]["visual_qa_issues"] == original_issues
    assert accepted["creator_approval_binding"]["sha256"].startswith("sha256:")
    assert latest_attempt["status"] == (
        "CREATOR_ACCEPTED_WITH_KNOWN_EXCEPTIONS"
    )
    assert latest_attempt["qa_status"] == "QA_FAILED"
    assert latest_attempt["qa_issues"] == original_issues
    assert latest_attempt["status_history"][0]["status"] == "QA_FAILED"
    assert visual_qa_path.read_bytes() == visual_qa_before
    assert json.loads(visual_qa_before)["status"] == "FAIL"
    assert not (package / "final" / "slide-09.png").exists()


def test_creator_failed_proof_acceptance_rejects_stale_image_hash(
    tmp_path: Path,
) -> None:
    package, failed = _blocked_failed_proof(tmp_path)
    approval_path = _write_failed_proof_creator_approval(
        package,
        failed,
        image_set_sha256="0" * 64,
    )

    with pytest.raises(ValueError, match="image_set_sha256 is stale"):
        accept_failed_proof_by_creator(package, approval_path)

    assert json.loads(
        (package / "image-generation.json").read_text(encoding="utf-8")
    )["status"] == "BLOCKED_VISUAL_QA"


def test_creator_failed_proof_acceptance_requires_exact_issue_acknowledgement(
    tmp_path: Path,
) -> None:
    package, failed = _blocked_failed_proof(tmp_path)
    approval_path = _write_failed_proof_creator_approval(
        package,
        failed,
        acknowledged_visual_qa_issues=[],
    )

    with pytest.raises(
        ValueError,
        match="acknowledged_visual_qa_issues must exactly match",
    ):
        accept_failed_proof_by_creator(package, approval_path)


def test_creator_failed_proof_acceptance_rejects_changed_quarantine(
    tmp_path: Path,
) -> None:
    package, failed = _blocked_failed_proof(tmp_path)
    approval_path = _write_failed_proof_creator_approval(package, failed)
    proof_path = (
        package
        / failed["slides"][0]["native_outputs"]["instagram_post"]["path"]
    )
    proof_path.write_bytes(proof_path.read_bytes() + b"changed")

    with pytest.raises(ValueError, match="quarantine integrity failed"):
        accept_failed_proof_by_creator(package, approval_path)


def test_creator_failed_proof_acceptance_rejects_state_manifest_mismatch(
    tmp_path: Path,
) -> None:
    package, failed = _blocked_failed_proof(tmp_path)
    approval_path = _write_failed_proof_creator_approval(package, failed)
    final_state_path = package / "final-images.json"
    final_state = json.loads(final_state_path.read_text(encoding="utf-8"))
    final_state["reason"] = "Diverged final state."
    final_state_path.write_text(json.dumps(final_state), encoding="utf-8")

    with pytest.raises(ValueError, match="contain the same current state"):
        accept_failed_proof_by_creator(package, approval_path)


def test_creator_failed_proof_acceptance_never_fakes_a_qa_pass(
    tmp_path: Path,
) -> None:
    package, failed = _blocked_failed_proof(tmp_path)
    approval_path = _write_failed_proof_creator_approval(package, failed)
    visual_qa_path = package / failed["visual_qa_path"]
    failed_qa_before = visual_qa_path.read_bytes()

    accepted = accept_failed_proof_by_creator(package, approval_path)

    assert accepted["publishable"] is False
    assert accepted["visual_qa_status"] == "QA_FAILED"
    assert accepted["proof_qa_passed"] is False
    assert accepted["visual_qa_issues"]
    assert visual_qa_path.read_bytes() == failed_qa_before
    ledger_attempt = load_attempt_ledger(package)["attempts"][-1]
    assert ledger_attempt["qa_status"] == "QA_FAILED"
    assert any(
        event["status"] == "QA_FAILED"
        for event in ledger_attempt["status_history"]
    )


def test_creator_override_batch_allowed_compiles_full_deck_with_bound_evidence(
    tmp_path: Path,
) -> None:
    package, failed = _blocked_failed_proof(tmp_path)
    approval_path = _write_failed_proof_creator_approval(package, failed)
    accepted = accept_failed_proof_by_creator(package, approval_path)
    visual_qa_path = package / accepted["visual_qa_path"]
    failed_qa_before = visual_qa_path.read_bytes()
    ledger_path = package / ".internal" / "visual-qa-attempts.json"
    ledger_before = ledger_path.read_bytes()
    passing_constraint = type(
        "Constraint",
        (),
        {"status": "PASS", "reason": ""},
    )()

    with (
        patch(
            "pipeline.stages.codex_builtin_image_generation.visual_plan_quality_gate_reason",
            return_value=None,
        ),
        patch(
            "pipeline.stages.codex_builtin_image_generation.identity_consistency_gate_reason",
            return_value=None,
        ),
        patch(
            "pipeline.stages.codex_builtin_image_generation.house_style_consistency_gate_reason",
            return_value=None,
        ),
        patch(
            "pipeline.stages.codex_builtin_image_generation.layer_e_gate_reason",
            return_value=None,
        ),
        patch(
            "pipeline.stages.codex_builtin_image_generation.pre_generation_review_gate_reason",
            return_value=None,
        ),
        patch(
            "pipeline.stages.codex_builtin_image_generation.check_prompt_constraints",
            return_value=passing_constraint,
        ),
    ):
        handoff = prepare_codex_builtin_image_generation(package)

    persisted = json.loads(
        (package / "image-generation.json").read_text(encoding="utf-8")
    )
    final_state = json.loads(
        (package / "final-images.json").read_text(encoding="utf-8")
    )
    proof_binding = handoff["creator_override_proof_binding"]
    assert handoff == persisted == final_state
    assert handoff["status"] == "handoff_ready"
    assert handoff["proof_state"] == "BATCH_ALLOWED"
    assert handoff["proof_only"] is False
    assert handoff["requested_proof_slide"] is None
    assert handoff["slide_count"] == handoff["total_slide_count"] == 11
    assert handoff["compiled_prompt_handoff"]["slide_numbers"] == list(
        range(1, 12)
    )
    assert handoff["publishable"] is False
    assert handoff["creator_override"] is True
    assert handoff["batch_generation_allowed"] is True
    assert handoff["proof_qa_passed"] is False
    assert handoff["visual_qa_status"] == "QA_FAILED"
    assert handoff["visual_qa_issues"] == accepted["visual_qa_issues"]
    assert handoff["known_qa_exceptions"] == accepted["known_qa_exceptions"]
    assert handoff["creator_approval_binding"] == accepted[
        "creator_approval_binding"
    ]
    assert handoff["creator_override_record"] == accepted[
        "creator_override_record"
    ]
    assert proof_binding["proof_slide"] == 9
    assert proof_binding["proof_slide_record"] == accepted["slides"][0]
    assert proof_binding["image_set_sha256"] == accepted["image_set_sha256"]
    assert proof_binding["binding_fingerprint"].startswith("sha256:")
    assert visual_qa_path.read_bytes() == failed_qa_before
    assert ledger_path.read_bytes() == ledger_before
    assert len(
        list(
            (
                package / "codex-image-prompts" / "instagram-post"
            ).glob("slide-*.prompt.txt")
        )
    ) == 11
    (package / "identity-consistency-review.json").write_text(
        json.dumps({"status": "PASS"}),
        encoding="utf-8",
    )
    with (
        patch(
            "pipeline.agentic.workflow_doctor._qa_asset_hash_issues",
            return_value=[],
        ),
        patch(
            "pipeline.agentic.workflow_doctor.validate_director_storyboard",
            return_value=[],
        ),
    ):
        doctor_report = inspect_carousel_package(package)
    assert not doctor_report.blocked, [
        issue.code for issue in doctor_report.issues
    ]
    assert any(
        issue.code == "handoff_ready_not_publishable"
        for issue in doctor_report.issues
    )


def test_batch_allowed_without_creator_override_cannot_compile_full_deck(
    tmp_path: Path,
) -> None:
    package, failed = _blocked_failed_proof(tmp_path)
    approval_path = _write_failed_proof_creator_approval(package, failed)
    accepted = accept_failed_proof_by_creator(package, approval_path)
    tampered = json.loads(json.dumps(accepted))
    tampered["creator_override"] = False
    for filename in ("image-generation.json", "final-images.json"):
        (package / filename).write_text(json.dumps(tampered), encoding="utf-8")
    state_before = (package / "image-generation.json").read_bytes()
    proof_prompt = (
        package
        / "codex-image-prompts"
        / "instagram-post"
        / "slide-09.prompt.txt"
    )
    proof_prompt_before = proof_prompt.read_bytes()

    with pytest.raises(ValueError, match="recorded creator override"):
        prepare_codex_builtin_image_generation(package)

    assert (package / "image-generation.json").read_bytes() == state_before
    assert proof_prompt.read_bytes() == proof_prompt_before
    assert not (
        package
        / "codex-image-prompts"
        / "instagram-post"
        / "slide-01.prompt.txt"
    ).exists()


def test_creator_override_full_deck_rejects_changed_approval_binding(
    tmp_path: Path,
) -> None:
    package, failed = _blocked_failed_proof(tmp_path)
    approval_path = _write_failed_proof_creator_approval(package, failed)
    accept_failed_proof_by_creator(package, approval_path)
    state_before = (package / "image-generation.json").read_bytes()
    approval_path.write_bytes(approval_path.read_bytes() + b"\n")

    with pytest.raises(ValueError, match="approval changed after acceptance"):
        prepare_codex_builtin_image_generation(package)

    assert (package / "image-generation.json").read_bytes() == state_before
    assert not (
        package
        / "codex-image-prompts"
        / "instagram-post"
        / "slide-01.prompt.txt"
    ).exists()


def test_doctor_blocks_tampered_creator_override_proof_binding(
    tmp_path: Path,
) -> None:
    package, handoff = _prepared_creator_override_handoff(tmp_path)
    tampered = json.loads(json.dumps(handoff))
    tampered["creator_override_proof_binding"]["image_set_sha256"] = (
        "sha256:" + ("0" * 64)
    )
    for filename in ("image-generation.json", "final-images.json"):
        (package / filename).write_text(json.dumps(tampered), encoding="utf-8")

    report = _inspect_creator_override_fixture(package)
    codes = {issue.code for issue in report.issues}
    assert report.blocked
    assert "creator_override_handoff_integrity_invalid" in codes
    assert "generated_proof_without_structured_qa_v2" in codes
    assert "batch_state_without_required_gates" in codes


def test_doctor_keeps_ordinary_blockers_when_override_evidence_is_missing(
    tmp_path: Path,
) -> None:
    package, handoff = _prepared_creator_override_handoff(tmp_path)
    missing = json.loads(json.dumps(handoff))
    missing.pop("creator_override")
    missing.pop("creator_override_proof_binding")
    for filename in ("image-generation.json", "final-images.json"):
        (package / filename).write_text(json.dumps(missing), encoding="utf-8")

    codes = {
        issue.code
        for issue in _inspect_creator_override_fixture(package).issues
    }
    assert "generated_proof_without_structured_qa_v2" in codes
    assert "batch_state_without_required_gates" in codes
    assert "blocked_visual_qa_terminal" in codes
    assert "identity_eval_incomplete_stop_gate" in codes


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("publishable", True),
        ("done", True),
        ("proof_qa_passed", True),
    ],
)
def test_doctor_rejects_publish_or_qa_pass_claims_on_creator_override_handoff(
    tmp_path: Path,
    field: str,
    value: bool,
) -> None:
    package, handoff = _prepared_creator_override_handoff(tmp_path)
    claimed = json.loads(json.dumps(handoff))
    claimed[field] = value
    for filename in ("image-generation.json", "final-images.json"):
        (package / filename).write_text(json.dumps(claimed), encoding="utf-8")

    report = _inspect_creator_override_fixture(package)
    codes = {issue.code for issue in report.issues}
    assert report.blocked
    assert "creator_override_handoff_integrity_invalid" in codes
    if field in {"publishable", "done"}:
        assert "blocked_visual_qa_claims_publishable" in codes


def test_creator_override_full_deck_packages_into_separate_batch_quarantine(
    tmp_path: Path,
) -> None:
    package, _ = _prepared_creator_override_handoff(tmp_path)
    proof_ledger_path = package / ".internal" / "visual-qa-attempts.json"
    proof_ledger_before = proof_ledger_path.read_bytes()
    proof_quarantine = package / ".internal" / "visual-quarantine"
    proof_files_before = {
        path.relative_to(proof_quarantine).as_posix(): path.read_bytes()
        for path in proof_quarantine.rglob("*")
        if path.is_file()
    }

    state = _package_creator_override_full_deck(
        package,
        _full_deck_generated_sources(tmp_path),
    )
    assert validate_quarantine_integrity(
        state["slides"],
        ("instagram_post",),
        carousel_dir=package,
    ) == []
    with (
        patch(
            "pipeline.stages.codex_builtin_image_generation.validate_spatial_topology_check",
            return_value=[],
        ),
        patch(
            "pipeline.stages.codex_builtin_image_generation.validate_frame_readability",
            return_value=[],
        ) as readability,
    ):
        validation_issues = validate_exact_image_visual_qa(
            {
                "checks": {
                    "spatial_topology": {
                        "slides": [
                            {"slide": record["slide"]}
                            for record in state["slides"]
                        ]
                    },
                    "visual_story_readability": {
                        "frames": [
                            {
                                "slide": record["slide"],
                                "format": "instagram_post",
                            }
                            for record in state["slides"]
                        ]
                    },
                }
            },
            state["slides"],
            visual_plan={},
            carousel_dir=package,
        )

    full_deck_ledger = json.loads(
        (
            package / ".internal" / "full-deck-visual-qa-attempts.json"
        ).read_text(encoding="utf-8")
    )
    assert state["status"] == "GENERATED_QUARANTINED"
    assert state["generation_scope"] == "creator_override_full_deck"
    assert state["full_deck_qa_state"] == "FULL_DECK_GENERATED_QUARANTINED"
    assert state["proof_only"] is False
    assert state["slide_count"] == state["total_slide_count"] == 11
    assert state["quarantine_dir"] == (
        ".internal/full-deck-visual-quarantine/attempt-01"
    )
    assert all(
        record["native_outputs"]["instagram_post"]["path"].startswith(
            ".internal/full-deck-visual-quarantine/attempt-01/"
        )
        for record in state["slides"]
    )
    assert full_deck_ledger["scope"] == "creator_override_full_deck"
    assert full_deck_ledger["attempts"][0]["status"] == "QUARANTINED"
    assert not any(
        "canonical package-contained quarantine asset" in issue
        or "file-backed validation requires package_dir" in issue
        for issue in validation_issues
    )
    assert readability.call_args.kwargs["package_dir"] == (
        package
        / ".internal"
        / "full-deck-visual-quarantine"
        / "attempt-01"
    ).resolve()
    assert proof_ledger_path.read_bytes() == proof_ledger_before
    assert {
        path.relative_to(proof_quarantine).as_posix(): path.read_bytes()
        for path in proof_quarantine.rglob("*")
        if path.is_file()
    } == proof_files_before


def test_creator_override_full_deck_refuses_quarantine_collision(
    tmp_path: Path,
) -> None:
    package, _ = _prepared_creator_override_handoff(tmp_path)
    proof_ledger_path = package / ".internal" / "visual-qa-attempts.json"
    proof_ledger_before = proof_ledger_path.read_bytes()
    collision = (
        package
        / ".internal"
        / "full-deck-visual-quarantine"
        / "attempt-01"
        / "sentinel.txt"
    )
    collision.parent.mkdir(parents=True)
    collision.write_bytes(b"must-not-overwrite")

    with pytest.raises(ValueError, match="refusing to overwrite"):
        _package_creator_override_full_deck(
            package,
            _full_deck_generated_sources(tmp_path),
        )

    assert collision.read_bytes() == b"must-not-overwrite"
    assert proof_ledger_path.read_bytes() == proof_ledger_before
    assert not (
        package / ".internal" / "full-deck-visual-qa-attempts.json"
    ).exists()


def test_quarantine_integrity_rejects_mixed_proof_and_full_deck_scopes(
    tmp_path: Path,
) -> None:
    package, _ = _prepared_creator_override_handoff(tmp_path)
    state = _package_creator_override_full_deck(
        package,
        _full_deck_generated_sources(tmp_path),
    )
    accepted_proof = state["creator_override_origin_handoff"][
        "creator_override_proof_binding"
    ]["proof_slide_record"]

    issues = validate_quarantine_integrity(
        [state["slides"][0], accepted_proof],
        ("instagram_post",),
        carousel_dir=package,
    )

    assert (
        "quarantined slides must belong to one canonical quarantine attempt scope"
        in issues
    )


def test_creator_override_full_deck_rejects_tampered_handoff_before_copy(
    tmp_path: Path,
) -> None:
    package, handoff = _prepared_creator_override_handoff(tmp_path)
    tampered = json.loads(json.dumps(handoff))
    tampered["creator_override_proof_binding"]["image_set_sha256"] = (
        "sha256:" + ("0" * 64)
    )
    for filename in ("image-generation.json", "final-images.json"):
        (package / filename).write_text(json.dumps(tampered), encoding="utf-8")

    with pytest.raises(
        ValueError,
        match="Creator-override full-deck handoff integrity failed",
    ):
        _package_creator_override_full_deck(
            package,
            _full_deck_generated_sources(tmp_path),
        )

    assert not (
        package / ".internal" / "full-deck-visual-quarantine"
    ).exists()
    assert not (
        package / ".internal" / "full-deck-visual-qa-attempts.json"
    ).exists()


def test_creator_override_full_deck_candidate_remains_nonpublishable(
    tmp_path: Path,
) -> None:
    package, _ = _prepared_creator_override_handoff(tmp_path)

    state = _package_creator_override_full_deck(
        package,
        _full_deck_generated_sources(tmp_path),
    )

    assert state["publishable"] is False
    assert state["done"] is False
    assert state["proof_qa_passed"] is not True
    assert not (package / ".internal" / "full-deck-visual-qa.json").exists()
    assert not (package / "final" / "slide-01.png").exists()


def test_creator_override_full_deck_promotion_reenters_bound_preaudit_state(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    package, _ = _prepared_creator_override_handoff(tmp_path)
    quarantined = _package_creator_override_full_deck(
        package,
        _full_deck_generated_sources(tmp_path, size=(1086, 1448)),
    )
    qa_path = package / ".internal" / "full-deck-visual-qa.json"
    qa_path.write_text("{}", encoding="utf-8")
    approval_path = package / ".internal" / "full-deck-creator-approval.json"
    approval_path.write_text(
        json.dumps(
            {
                "status": "APPROVED",
                "approved": True,
                "approved_by": "creator",
                "image_set_sha256": quarantined["image_set_sha256"],
                "evidence": "Creator approved this exact full-deck image set.",
            }
        ),
        encoding="utf-8",
    )
    relative_package = package.relative_to(tmp_path)
    monkeypatch.chdir(tmp_path)

    common_patches = (
        patch(
            "pipeline.stages.codex_builtin_image_generation.visual_plan_quality_gate_reason",
            return_value=None,
        ),
        patch(
            "pipeline.stages.codex_builtin_image_generation.identity_consistency_gate_reason",
            return_value=None,
        ),
        patch(
            "pipeline.stages.codex_builtin_image_generation.validate_exact_image_visual_qa",
            return_value=[],
        ),
    )
    with (
        common_patches[0],
        common_patches[1],
        common_patches[2],
        pytest.raises(FileNotFoundError),
    ):
        promote_quarantined_codex_builtin_outputs(
            relative_package,
            refresh_quality=True,
            visual_qa_path=qa_path,
            creator_approval_path=approval_path,
        )

    interrupted = json.loads(
        (package / "image-generation.json").read_text(encoding="utf-8")
    )
    interrupted_ledger = json.loads(
        (
            package / ".internal" / "full-deck-visual-qa-attempts.json"
        ).read_text(encoding="utf-8")
    )
    assert interrupted["status"] == "BATCH_ALLOWED"
    assert interrupted["publishable"] is False
    assert interrupted["slide_count"] == interrupted["total_slide_count"] == 11
    assert interrupted["creator_approval_path"] == (
        ".internal/full-deck-creator-approval.json"
    )
    assert interrupted["creator_approval_sha256"].startswith("sha256:")
    assert interrupted_ledger["attempts"][-1]["status"] == "CREATOR_APPROVED"

    legacy_interrupted = json.loads(json.dumps(interrupted))
    legacy_interrupted["creator_approval_path"] = (
        relative_package / ".internal" / "full-deck-creator-approval.json"
    ).as_posix()
    legacy_interrupted.pop("creator_approval_sha256")
    for filename in ("image-generation.json", "final-images.json"):
        (package / filename).write_text(
            json.dumps(legacy_interrupted),
            encoding="utf-8",
        )

    (package / "manifest.json").write_text(
        json.dumps(
            {
                "source_story": "story",
                "title": "title",
                "slug": "slug",
                "date": "2026-07-30",
                "reference_images": [],
            }
        ),
        encoding="utf-8",
    )
    (package / "concept.json").write_text("{}", encoding="utf-8")
    (package / "copy.json").write_text("{}", encoding="utf-8")

    with (
        patch(
            "pipeline.stages.codex_builtin_image_generation.visual_plan_quality_gate_reason",
            return_value=None,
        ),
        patch(
            "pipeline.stages.codex_builtin_image_generation.identity_consistency_gate_reason",
            return_value=None,
        ),
        patch(
            "pipeline.stages.codex_builtin_image_generation.validate_exact_image_visual_qa",
            return_value=[],
        ),
        patch(
            "pipeline.stages.carousel_quality.write_quality_artifacts",
            return_value={"status": "NEEDS_FIXES", "pass": False},
        ),
    ):
        retried = promote_quarantined_codex_builtin_outputs(
            relative_package,
            refresh_quality=True,
            visual_qa_path=qa_path,
            creator_approval_path=approval_path,
        )

    assert retried["status"] == "generated_audit_failed"
    assert retried["publishable"] is False
    assert json.loads(
        (
            package / ".internal" / "full-deck-visual-qa-attempts.json"
        ).read_text(encoding="utf-8")
    )["attempts"][-1]["status"] == "FINAL_AUDIT_FAILED"


def test_proof_only_packaging_quarantines_canonical_frame_and_preserves_source(
    tmp_path: Path,
) -> None:
    from scripts.package_generated_carousel import package_generated_images

    package, generated = _proof_package(tmp_path)
    sentinel = package / "final" / "slide-01.png"
    sentinel.parent.mkdir(parents=True)
    sentinel.write_bytes(b"existing-final-must-not-be-touched")

    with (
        patch(
            "scripts.package_generated_carousel.inspect_carousel_package",
            return_value=type("Report", (), {"issues": []})(),
        ),
        patch(
            "pipeline.stages.codex_builtin_image_generation.visual_plan_quality_gate_reason",
            return_value=None,
        ),
        patch(
            "pipeline.stages.codex_builtin_image_generation.identity_consistency_gate_reason",
            return_value=None,
        ),
    ):
        state = package_generated_images(
            package,
            instagram_post_paths=[generated],
            proof_slide=9,
        )

    output = state["slides"][0]["native_outputs"]["instagram_post"]
    canonical_frame = package / output["path"]
    source_binding = output["model_native_source"]
    preserved_source = package / source_binding["path"]
    ledger = load_attempt_ledger(package)

    assert state["status"] == "GENERATED_QUARANTINED"
    assert state["proof_only"] is True
    assert state["requested_proof_slide"] == 9
    assert state["slide_count"] == 1
    assert state["total_slide_count"] == 11
    assert [record["slide"] for record in state["slides"]] == [9]
    assert (output["width"], output["height"]) == (1080, 1440)
    assert canonical_frame.parent.name == "final"
    assert canonical_frame.name == "slide-09.png"
    assert output["path"].startswith(".internal/visual-quarantine/")
    assert source_binding["path"].startswith(
        ".internal/visual-quarantine/"
    )
    assert hashlib.sha256(canonical_frame.read_bytes()).hexdigest() == output["sha256"]
    assert (source_binding["width"], source_binding["height"]) == (1086, 1448)
    assert output["normalization"] == (
        "proportional export from 1086x1448 to exact 1080x1440"
    )
    assert preserved_source.read_bytes() == generated.read_bytes()
    assert (
        hashlib.sha256(preserved_source.read_bytes()).hexdigest()
        == source_binding["sha256"]
    )
    assert state["image_set_sha256"] == image_set_sha256(state["slides"])
    assert ledger["attempts"][0]["image_set_sha256"] == state["image_set_sha256"]
    assert ledger["attempts"][0]["status"] == "QUARANTINED"
    assert not state.get("creator_approval_path")
    assert sentinel.read_bytes() == b"existing-final-must-not-be-touched"


def test_failed_proof_handoff_recompile_is_atomic_and_preserves_failed_evidence(
    tmp_path: Path,
) -> None:
    package, generated, failed = _failed_retry_package(tmp_path)
    legacy_issues = [
        f"Human-readable failed QA observation {number}"
        for number in range(1, 8)
    ]
    failed = _replace_failed_issue_evidence(package, failed, legacy_issues)
    old_prompt = (
        package
        / "codex-image-prompts"
        / "instagram-post"
        / "slide-09.prompt.txt"
    ).read_bytes()
    prompt_pack = json.loads((package / "prompt-pack.json").read_text(encoding="utf-8"))
    prompt_pack["slides"][8]["prompt"] = "Targeted repair prompt with corrected spatial topology."
    (package / "prompt-pack.json").write_text(json.dumps(prompt_pack), encoding="utf-8")

    passing_constraint = type("Constraint", (), {"status": "PASS", "reason": ""})()
    with (
        patch(
            "pipeline.stages.codex_builtin_image_generation.visual_plan_quality_gate_reason",
            return_value=None,
        ),
        patch(
            "pipeline.stages.codex_builtin_image_generation.identity_consistency_gate_reason",
            return_value=None,
        ),
        patch(
            "pipeline.stages.codex_builtin_image_generation.house_style_consistency_gate_reason",
            return_value=None,
        ),
        patch(
            "pipeline.stages.codex_builtin_image_generation.layer_e_gate_reason",
            return_value=None,
        ),
        patch(
            "pipeline.stages.codex_builtin_image_generation.pre_generation_review_gate_reason",
            return_value=None,
        ),
        patch(
            "pipeline.stages.codex_builtin_image_generation.check_prompt_constraints",
            return_value=passing_constraint,
        ),
        patch(
            "pipeline.stages.codex_builtin_image_generation.validate_exact_image_visual_qa",
            return_value=[
                f"structured validator failure {number}"
                for number in range(1, 21)
            ],
        ),
    ):
        recompiled = recompile_failed_proof_handoff(package)

    backup_prompt = (
        package
        / ".internal"
        / "codex-image-prompts-previous"
        / "attempt-01"
        / "instagram-post"
        / "slide-09.prompt.txt"
    )
    active_prompt = (
        package
        / "codex-image-prompts"
        / "instagram-post"
        / "slide-09.prompt.txt"
    )
    preserved_keys = set(failed) - {
        "compiled_prompt_handoff",
        "retry_prompt_handoff_attestation",
    }
    assert {key: recompiled[key] for key in preserved_keys} == {
        key: failed[key] for key in preserved_keys
    }
    assert recompiled["status"] == failed["status"]
    assert recompiled["slides"] == failed["slides"]
    assert backup_prompt.read_bytes() == old_prompt
    assert active_prompt.read_bytes() != old_prompt
    assert retry_prompt_handoff_attestation_issues(package, state=recompiled) == []
    assert json.loads((package / "final-images.json").read_text(encoding="utf-8")) == recompiled

    retry_image = tmp_path / "generated" / "proof-slide-09-retry.png"
    _png(retry_image, (1080, 1440))
    with (
        patch(
            "pipeline.stages.codex_builtin_image_generation.visual_plan_quality_gate_reason",
            return_value=None,
        ),
        patch(
            "pipeline.stages.codex_builtin_image_generation.identity_consistency_gate_reason",
            return_value=None,
        ),
    ):
        next_state = package_codex_builtin_outputs(
            package,
            generated_paths_by_format={"instagram_post": [retry_image]},
            proof_slide=9,
            visual_qa_path=".internal/pending-retry-qa.json",
        )
    assert next_state["status"] == "GENERATED_QUARANTINED"
    assert (
        next_state["retry_prompt_handoff_attestation"]
        == recompiled["retry_prompt_handoff_attestation"]
    )
    assert load_attempt_ledger(package)["attempts"][-1]["status"] == "QUARANTINED"


def test_failed_proof_handoff_recompile_rejects_empty_qa_recomputation(
    tmp_path: Path,
) -> None:
    package, _, failed = _failed_retry_package(tmp_path)
    failed = _replace_failed_issue_evidence(
        package,
        failed,
        ["Legacy human reviewer rejected the proof."],
    )
    state_before = (package / "image-generation.json").read_bytes()
    prompt_before = (
        package
        / "codex-image-prompts"
        / "instagram-post"
        / "slide-09.prompt.txt"
    ).read_bytes()

    with (
        patch(
            "pipeline.stages.codex_builtin_image_generation.validate_exact_image_visual_qa",
            return_value=[],
        ),
        pytest.raises(ValueError, match="no longer reproduces any validator failure"),
    ):
        recompile_failed_proof_handoff(package)

    assert json.loads(state_before)["visual_qa_issues"] == failed["visual_qa_issues"]
    assert (package / "image-generation.json").read_bytes() == state_before
    assert (
        package
        / "codex-image-prompts"
        / "instagram-post"
        / "slide-09.prompt.txt"
    ).read_bytes() == prompt_before
    assert not (
        package / ".internal" / "codex-image-prompts-previous"
    ).exists()


def test_failed_proof_handoff_recompile_gate_failure_keeps_active_state_unchanged(
    tmp_path: Path,
) -> None:
    package, _, _ = _failed_retry_package(tmp_path)
    state_before = (package / "image-generation.json").read_bytes()
    prompt_before = (
        package
        / "codex-image-prompts"
        / "instagram-post"
        / "slide-09.prompt.txt"
    ).read_bytes()

    with (
        patch(
            "pipeline.stages.codex_builtin_image_generation.visual_plan_quality_gate_reason",
            return_value="director evidence is stale",
        ),
        patch(
            "pipeline.stages.codex_builtin_image_generation.validate_frame_readability",
            return_value=[],
        ),
        pytest.raises(ValueError, match="visual-plan gate"),
    ):
        recompile_failed_proof_handoff(package)

    assert (package / "image-generation.json").read_bytes() == state_before
    assert (
        package
        / "codex-image-prompts"
        / "instagram-post"
        / "slide-09.prompt.txt"
    ).read_bytes() == prompt_before
    assert not (
        package / ".internal" / "codex-image-prompts-previous"
    ).exists()


def test_relative_package_input_records_package_relative_quarantine_paths(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    package, generated = _proof_package(tmp_path)
    monkeypatch.chdir(tmp_path)
    relative_package = package.relative_to(tmp_path)

    with (
        patch(
            "pipeline.stages.codex_builtin_image_generation.visual_plan_quality_gate_reason",
            return_value=None,
        ),
        patch(
            "pipeline.stages.codex_builtin_image_generation.identity_consistency_gate_reason",
            return_value=None,
        ),
    ):
        state = package_codex_builtin_outputs(
            relative_package,
            generated_paths_by_format={"instagram_post": [generated]},
            proof_slide=9,
        )

    output = state["slides"][0]["native_outputs"]["instagram_post"]
    source = output["model_native_source"]

    assert output["path"] == (
        ".internal/visual-quarantine/attempt-01/final/slide-09.png"
    )
    assert source["path"] == (
        ".internal/visual-quarantine/attempt-01/model-native-source/"
        "instagram-post-slide-09.png"
    )
    assert state["quarantine_dir"] == (
        ".internal/visual-quarantine/attempt-01"
    )
    assert (package / output["path"]).is_file()
    assert (package / source["path"]).is_file()
    assert (
        validate_quarantine_integrity(
            state["slides"],
            ("instagram_post",),
            carousel_dir=relative_package,
        )
        == []
    )


@pytest.mark.parametrize("source_size", [(1086, 1447), (810, 1080)])
def test_proof_only_packaging_rejects_off_ratio_or_undersized_source(
    tmp_path: Path,
    source_size: tuple[int, int],
) -> None:
    package, generated = _proof_package(tmp_path)
    _png(generated, source_size)

    with (
        patch(
            "pipeline.stages.codex_builtin_image_generation.visual_plan_quality_gate_reason",
            return_value=None,
        ),
        patch(
            "pipeline.stages.codex_builtin_image_generation.identity_consistency_gate_reason",
            return_value=None,
        ),
        pytest.raises(ValueError, match="native source dimensions"),
    ):
        package_codex_builtin_outputs(
            package,
            generated_paths_by_format={"instagram_post": [generated]},
            proof_slide=9,
        )

    assert not (package / ".internal" / "visual-qa-attempts.json").exists()
    assert not list(
        (package / ".internal" / "visual-quarantine").glob("**/*.png")
    )


def test_proof_only_handoff_requires_explicit_proof_packaging_mode(
    tmp_path: Path,
) -> None:
    package, generated = _proof_package(tmp_path)

    with pytest.raises(ValueError, match="--proof-slide"):
        package_codex_builtin_outputs(
            package,
            generated_paths_by_format={"instagram_post": [generated]},
        )


def test_proof_event_b_binds_canonical_sparse_slide_frame(tmp_path: Path) -> None:
    package, generated = _proof_package(tmp_path)
    with (
        patch(
            "pipeline.stages.codex_builtin_image_generation.visual_plan_quality_gate_reason",
            return_value=None,
        ),
        patch(
            "pipeline.stages.codex_builtin_image_generation.identity_consistency_gate_reason",
            return_value=None,
        ),
    ):
        state = package_codex_builtin_outputs(
            package,
            generated_paths_by_format={"instagram_post": [generated]},
            proof_slide=9,
        )

    proof_qa = {
        "schema_version": "2.1",
        "checks": {
            "spatial_topology": {"slides": [{"slide": 9}]},
            "visual_story_readability": {
                "frames": [{"slide": 9, "format": "instagram_post"}]
            },
        },
    }
    with (
        patch(
            "pipeline.stages.codex_builtin_image_generation.validate_spatial_topology_check",
            return_value=[],
        ),
        patch(
            "pipeline.stages.codex_builtin_image_generation.validate_frame_readability",
            return_value=[],
        ) as readability,
    ):
        validate_exact_image_visual_qa(
            proof_qa,
            state["slides"],
            visual_plan={},
            carousel_dir=package,
        )

    adapted_check = readability.call_args.args[0]
    call_kwargs = readability.call_args.kwargs
    binding = call_kwargs["expected_frame_bindings"][(1, "instagram_post")]

    assert adapted_check["frames"][0]["slide"] == 1
    assert binding["relative_path"] == "final/slide-09.png"
    assert binding["dimensions"] == (1080, 1440)
    assert call_kwargs["package_dir"] == (package / state["quarantine_dir"]).resolve()


def test_quarantine_integrity_rejects_external_absolute_asset_root(
    tmp_path: Path,
) -> None:
    package = tmp_path / "quarantine-package"
    package.mkdir()
    external = tmp_path / "external" / "slide-01.png"
    _png(external, (1080, 1440))
    image_bytes = external.read_bytes()
    records = [
        {
            "slide": 1,
            "native_outputs": {
                "instagram_post": {
                    "path": str(external.resolve()),
                    "sha256": hashlib.sha256(image_bytes).hexdigest(),
                    "width": 1080,
                    "height": 1440,
                }
            },
        }
    ]

    issues = validate_quarantine_integrity(
        records,
        ("instagram_post",),
        carousel_dir=package,
    )

    assert any(
        "canonical package-contained quarantine asset" in issue for issue in issues
    )


def _passing_qa(state: dict) -> dict:
    slide = state["slides"][0]
    native_outputs = slide["native_outputs"]
    anatomy_formats = {}
    entity_formats = {}
    richness_formats = {}
    for output_format, source_asset in native_outputs.items():
        anatomy_formats[output_format] = {
            "source_asset": source_asset,
            "expected_arms": 0,
            "observed_arms": 0,
            "expected_hands": 0,
            "observed_hands": 0,
            "visible_hands": [],
            "unexpected_limbs": [],
            "duplicated_limbs": [],
            "malformed_fingers": False,
        }
        entity_formats[output_format] = {
            "source_asset": source_asset,
            "expected_people": 0,
            "observed_people": 0,
            "expected_arms": 0,
            "observed_arms": 0,
            "expected_hands": 0,
            "observed_hands": 0,
            "unexpected_entities": [],
            "unexpected_limbs": [],
            "duplicated_limbs": [],
            "evidence": "Only the authorized repair receipt and environmental objects are visible.",
        }
        richness_formats[output_format] = {
            "source_asset": source_asset,
            "foreground": "The repaired key and receipt establish the immediate evidence.",
            "midground": "The open repair kit shows the action that just finished.",
            "background": "The apartment landing preserves the incident location.",
            "focal_action": "The repaired key replaces the snapped key from the prior beat.",
            "story_details": ["snapped key half", "open repair kit"],
            "cause_effect": "The earlier break caused the repair now visible in the frame.",
            "posed_portrait": False,
            "decorative_clutter": False,
        }
    return {
        "schema_version": "2.1",
        "status": "PASS",
        "proof_state": "QA_PASS_CANDIDATE",
        "image_set_sha256": state["image_set_sha256"],
        "reviews": {
            "anatomy_entity_spatial_identity": {
                "reviewer_id": "anatomy-reviewer",
                "pass": True,
                "evidence": "Confirmed the object-only frame contains no unexpected bodies, limbs, hands, or identity actors.",
            },
            "storytelling_richness_text_style": {
                "reviewer_id": "story-reviewer",
                "pass": True,
                "evidence": "Confirmed layered story evidence, exact text, causal repair detail, and house style.",
            },
        },
        "slides": [
            {
                "slide": 1,
                "native_outputs": native_outputs,
            }
        ],
        "checks": {
            "anatomy_inventory": {
                "pass": True,
                "slides": [
                    {
                        "slide": 1,
                        "formats": anatomy_formats,
                    }
                ],
            },
            "scene_entity_integrity": {
                "pass": True,
                "slides": [
                    {
                        "slide": 1,
                        "formats": entity_formats,
                    }
                ],
            },
            "spatial_topology": {
                "pass": True,
                "slides": [
                    {
                        "slide": 1,
                        "observed_people": 0,
                        "evidence_views": {
                            "full_frame": "Object-only frame contains no human silhouette.",
                            "person_object_crop": "No person-object boundary exists in this frame.",
                            "focal_detail": "Repair objects remain separate with clear overlap order."
                        },
                        "environment_planes": [],
                        "people": [],
                        "ambiguous_regions": [],
                        "unresolved_intersections": []
                    }
                ]
            },
            "visual_richness": {
                "pass": True,
                "slides": [
                    {
                        "slide": 1,
                        "formats": richness_formats,
                    }
                ],
            },
        },
    }


@pytest.mark.parametrize(
    "tamper",
    ["missing", "absolute", "traversal", "symlink", "extra", "stale_slides", "stale_formats"],
)
def test_initial_packaging_rejects_unsafe_or_stale_compiled_handoff_before_quarantine(
    tmp_path: Path,
    tamper: str,
) -> None:
    package, paths = _package(tmp_path)
    state_path = package / "image-generation.json"
    state = json.loads(state_path.read_text(encoding="utf-8"))
    prompt_path = package / "codex-image-prompts" / "instagram-post" / "slide-01.prompt.txt"

    if tamper == "missing":
        prompt_path.unlink()
    elif tamper == "absolute":
        state["compiled_prompt_handoff"]["files"][0]["relative_path"] = str(
            (tmp_path / "external.prompt.txt").resolve()
        )
    elif tamper == "traversal":
        state["compiled_prompt_handoff"]["files"][0]["relative_path"] = "../external.prompt.txt"
    elif tamper == "symlink":
        external = tmp_path / "external.prompt.txt"
        external.write_text("external", encoding="utf-8")
        prompt_path.unlink()
        prompt_path.symlink_to(external)
    elif tamper == "extra":
        (prompt_path.parent / "stale.prompt.txt").write_text("stale", encoding="utf-8")
    elif tamper == "stale_slides":
        prompt_pack = json.loads((package / "prompt-pack.json").read_text(encoding="utf-8"))
        prompt_pack["slides"][0]["text"] = "Changed after handoff"
        (package / "prompt-pack.json").write_text(json.dumps(prompt_pack), encoding="utf-8")
    elif tamper == "stale_formats":
        write_format_contract(package, ["instagram_post"], source="creator_correction", replace=True)
        paths = {"instagram_post": paths["instagram_post"]}
    if tamper in {"absolute", "traversal"}:
        state_path.write_text(json.dumps(state), encoding="utf-8")
        (package / "final-images.json").write_text(json.dumps(state), encoding="utf-8")

    result = package_codex_builtin_outputs(package, generated_paths_by_format=paths)

    assert result["status"] == "blocked"
    assert "Compiled prompt handoff integrity failed" in result["reason"]
    assert not (package / ".internal" / "visual-qa-attempts.json").exists()
    assert not list((package / ".internal" / "visual-quarantine").glob("**/*.png"))
    assert not (package / "codex-image-prompts").exists()


def test_generated_pixels_remain_quarantined_until_qa_and_creator_approval(tmp_path: Path) -> None:
    package, paths = _package(tmp_path)
    with (
        patch("pipeline.stages.codex_builtin_image_generation.visual_plan_quality_gate_reason", return_value=None),
        patch("pipeline.stages.codex_builtin_image_generation.identity_consistency_gate_reason", return_value=None),
        patch("pipeline.stages.codex_builtin_image_generation.validate_frame_readability", return_value=[]),
    ):
        state = package_codex_builtin_outputs(package, generated_paths_by_format=paths)

    assert state["status"] == "GENERATED_QUARANTINED"
    assert not (package / "final" / "slide-01.png").exists()
    qa = _passing_qa(state)
    (package / "visual-qa.json").write_text(json.dumps(qa), encoding="utf-8")
    approval = {
        "status": "APPROVED",
        "approved": True,
        "image_set_sha256": state["image_set_sha256"],
        "approved_by": "creator",
        "evidence": "Approved QA-passed proof.",
    }
    (package / "creator-proof-approval.json").write_text(json.dumps(approval), encoding="utf-8")

    with (
        patch("pipeline.stages.codex_builtin_image_generation.visual_plan_quality_gate_reason", return_value=None),
        patch("pipeline.stages.codex_builtin_image_generation.identity_consistency_gate_reason", return_value=None),
        patch("pipeline.stages.codex_builtin_image_generation.validate_frame_readability", return_value=[]),
    ):
        with patch(
            "pipeline.stages.carousel_quality.write_quality_artifacts",
            return_value={"status": "PASS", "pass": True},
        ):
            promoted = promote_quarantined_codex_builtin_outputs(
                package, refresh_quality=True
            )

    assert promoted["status"] == "publish_ready", promoted.get("visual_qa_issues")
    assert (package / "final" / "slide-01.png").exists()
    assert (package / "final-reels-stories" / "slide-01.png").exists()


def test_changed_quarantined_pixels_invalidate_qa_and_block_promotion(tmp_path: Path) -> None:
    package, paths = _package(tmp_path)
    with (
        patch("pipeline.stages.codex_builtin_image_generation.visual_plan_quality_gate_reason", return_value=None),
        patch("pipeline.stages.codex_builtin_image_generation.identity_consistency_gate_reason", return_value=None),
        patch("pipeline.stages.codex_builtin_image_generation.validate_frame_readability", return_value=[]),
    ):
        state = package_codex_builtin_outputs(package, generated_paths_by_format=paths)
    qa = _passing_qa(state)
    (package / "visual-qa.json").write_text(json.dumps(qa), encoding="utf-8")
    quarantined = (
        package
        / state["slides"][0]["native_outputs"]["instagram_post"]["path"]
    )
    _png(quarantined, (1080, 1440))
    quarantined.write_bytes(quarantined.read_bytes() + b"changed")

    with (
        patch("pipeline.stages.codex_builtin_image_generation.visual_plan_quality_gate_reason", return_value=None),
        patch("pipeline.stages.codex_builtin_image_generation.identity_consistency_gate_reason", return_value=None),
        patch("pipeline.stages.codex_builtin_image_generation.validate_frame_readability", return_value=[]),
    ):
        result = promote_quarantined_codex_builtin_outputs(package)

    assert result["status"] == "BLOCKED_VISUAL_QA"
    assert not (package / "final" / "slide-01.png").exists()


def test_reels_anatomy_must_pass_independently_from_instagram(tmp_path: Path) -> None:
    package, paths = _package(tmp_path)
    with (
        patch("pipeline.stages.codex_builtin_image_generation.visual_plan_quality_gate_reason", return_value=None),
        patch("pipeline.stages.codex_builtin_image_generation.identity_consistency_gate_reason", return_value=None),
        patch("pipeline.stages.codex_builtin_image_generation.validate_frame_readability", return_value=[]),
    ):
        state = package_codex_builtin_outputs(package, generated_paths_by_format=paths)
    qa = _passing_qa(state)
    anatomy = qa["checks"]["anatomy_inventory"]["slides"][0]["formats"]["reels_stories"]
    anatomy["expected_hands"] = 0
    anatomy["observed_hands"] = 1
    anatomy["visible_hands"] = [
        {
            "owner": "",
            "side": "right",
            "action": "enters from the door edge",
            "story_required": False,
            "attachment_visible": False,
            "attachment_evidence": "",
            "contact_object": "door",
            "contact_geometry_pass": False,
            "occlusion_evidence": "",
            "solid_object_intersection": True,
            "edge_entry_unexplained": True,
        }
    ]
    (package / "visual-qa.json").write_text(json.dumps(qa), encoding="utf-8")

    with (
        patch("pipeline.stages.codex_builtin_image_generation.visual_plan_quality_gate_reason", return_value=None),
        patch("pipeline.stages.codex_builtin_image_generation.identity_consistency_gate_reason", return_value=None),
        patch("pipeline.stages.codex_builtin_image_generation.validate_frame_readability", return_value=[]),
    ):
        result = promote_quarantined_codex_builtin_outputs(package)

    assert result["status"] == "GENERATED_QUARANTINED"
    assert any("reels_stories" in issue for issue in result["visual_qa_issues"])
    assert not (package / "final" / "slide-01.png").exists()


def test_failed_final_audit_keeps_assets_internal(tmp_path: Path) -> None:
    package, paths = _package(tmp_path)
    with (
        patch("pipeline.stages.codex_builtin_image_generation.visual_plan_quality_gate_reason", return_value=None),
        patch("pipeline.stages.codex_builtin_image_generation.identity_consistency_gate_reason", return_value=None),
        patch("pipeline.stages.codex_builtin_image_generation.validate_frame_readability", return_value=[]),
    ):
        state = package_codex_builtin_outputs(package, generated_paths_by_format=paths)
    (package / "visual-qa.json").write_text(json.dumps(_passing_qa(state)), encoding="utf-8")
    (package / "creator-proof-approval.json").write_text(
        json.dumps(
            {
                "status": "APPROVED",
                "approved": True,
                "image_set_sha256": state["image_set_sha256"],
                "approved_by": "creator",
                "evidence": "Approved QA-passed proof.",
            }
        ),
        encoding="utf-8",
    )

    with (
        patch("pipeline.stages.codex_builtin_image_generation.visual_plan_quality_gate_reason", return_value=None),
        patch("pipeline.stages.codex_builtin_image_generation.identity_consistency_gate_reason", return_value=None),
        patch("pipeline.stages.codex_builtin_image_generation.validate_frame_readability", return_value=[]),
        patch(
            "pipeline.stages.carousel_quality.write_quality_artifacts",
            return_value={"status": "NEEDS_FIXES", "pass": False},
        ),
    ):
        result = promote_quarantined_codex_builtin_outputs(package, refresh_quality=True)

    assert result["status"] == "generated_audit_failed"
    assert not (package / "final" / "slide-01.png").exists()
    assert not (package / "final-reels-stories" / "slide-01.png").exists()
    staging = Path(result["promotion_staging_dir"])
    assert (staging / "final" / "slide-01.png").exists()


def test_promotion_without_final_audit_never_writes_public_assets(tmp_path: Path) -> None:
    package, paths = _package(tmp_path)
    with (
        patch("pipeline.stages.codex_builtin_image_generation.visual_plan_quality_gate_reason", return_value=None),
        patch("pipeline.stages.codex_builtin_image_generation.identity_consistency_gate_reason", return_value=None),
        patch("pipeline.stages.codex_builtin_image_generation.validate_frame_readability", return_value=[]),
    ):
        state = package_codex_builtin_outputs(package, generated_paths_by_format=paths)
    (package / "visual-qa.json").write_text(json.dumps(_passing_qa(state)), encoding="utf-8")
    (package / "creator-proof-approval.json").write_text(
        json.dumps(
            {
                "status": "APPROVED",
                "approved": True,
                "image_set_sha256": state["image_set_sha256"],
                "approved_by": "creator",
                "evidence": "Approved QA-passed proof.",
            }
        ),
        encoding="utf-8",
    )

    with (
        patch("pipeline.stages.codex_builtin_image_generation.visual_plan_quality_gate_reason", return_value=None),
        patch("pipeline.stages.codex_builtin_image_generation.identity_consistency_gate_reason", return_value=None),
        patch("pipeline.stages.codex_builtin_image_generation.validate_frame_readability", return_value=[]),
    ):
        result = promote_quarantined_codex_builtin_outputs(package)

    assert result["status"] == "CREATOR_APPROVED_PROOF"
    assert result["promotion_blocker"] == "final_audit_required"
    assert not (package / "final" / "slide-01.png").exists()
    assert not (package / "final-reels-stories" / "slide-01.png").exists()


def test_internal_worker_runs_initial_attempt_plus_two_targeted_repairs(tmp_path: Path) -> None:
    package, paths = _package(tmp_path)
    generator_calls: list[tuple[int, list[str]]] = []

    def generate_attempt(retry_count: int, repair_issues: list[str]):
        generator_calls.append((retry_count, repair_issues))
        return paths

    def review_attempt(state: dict):
        qa = _passing_qa(state)
        qa["status"] = "FAIL"
        qa["reviews"]["anatomy_entity_spatial_identity"]["pass"] = False
        return qa

    with (
        patch("pipeline.stages.codex_builtin_image_generation.visual_plan_quality_gate_reason", return_value=None),
        patch("pipeline.stages.codex_builtin_image_generation.identity_consistency_gate_reason", return_value=None),
        patch("pipeline.stages.codex_builtin_image_generation.validate_frame_readability", return_value=[]),
    ):
        result = run_fail_closed_visual_worker(
            package,
            generate_attempt=generate_attempt,
            review_attempt=review_attempt,
        )

    assert result["status"] == "BLOCKED_VISUAL_QA"
    assert [retry for retry, _ in generator_calls] == [0, 1, 2]
    assert generator_calls[0][1] == []
    assert generator_calls[1][1]
    assert generator_calls[2][1]
    ledger = load_attempt_ledger(package)
    assert [attempt["status"] for attempt in ledger["attempts"]] == [
        "QA_FAILED",
        "QA_FAILED",
        "QA_FAILED",
    ]
    assert not (package / "final" / "slide-01.png").exists()


def test_approved_proof_batch_does_not_consume_a_full_deck_repair(tmp_path: Path) -> None:
    package = tmp_path / "approved-proof-batch-retries"
    package.mkdir()
    ledger_path = package / ".internal" / "visual-qa-attempts.json"
    ledger_path.parent.mkdir(parents=True)
    ledger_path.write_text(
        json.dumps(
            {
                "schema_version": "1.0",
                "max_retries": 2,
                "attempts": [
                    {
                        "attempt": 1,
                        "retry_count": 0,
                        "image_set_sha256": "proof",
                        "status": "BATCH_ALLOWED",
                    },
                    {
                        "attempt": 2,
                        "retry_count": 1,
                        "image_set_sha256": "deck-1",
                        "status": "QA_FAILED",
                    },
                    {
                        "attempt": 3,
                        "retry_count": 2,
                        "image_set_sha256": "deck-2",
                        "status": "QA_FAILED",
                    },
                ],
            }
        ),
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="retry limit"):
        next_retry_count(package)

    assert next_retry_count(package, allow_approved_proof_batch=True) == 3


def test_spatial_topology_failure_uses_distinct_rejected_state(tmp_path: Path) -> None:
    package, paths = _package(tmp_path)
    with (
        patch("pipeline.stages.codex_builtin_image_generation.visual_plan_quality_gate_reason", return_value=None),
        patch("pipeline.stages.codex_builtin_image_generation.identity_consistency_gate_reason", return_value=None),
        patch("pipeline.stages.codex_builtin_image_generation.validate_frame_readability", return_value=[]),
    ):
        state = package_codex_builtin_outputs(package, generated_paths_by_format=paths)
    qa = _passing_qa(state)
    topology = qa["checks"]["spatial_topology"]
    assert isinstance(topology, dict)
    record = topology["slides"][0]
    record["observed_people"] = 1
    record["people"] = [
        {
            "person": "Zuv",
            "silhouette_traceable": False,
            "ambiguous_regions": ["shoulder/back/torso against door"],
            "body_regions": [
                {
                    "region": "right shoulder back and torso",
                    "near_object": "door and doorframe",
                    "expected_relation": "in_front_of",
                    "observed_relation": "touching",
                    "boundary_continuous": False,
                    "occlusion_order_clear": False,
                    "solid_object_intersection": True,
                    "morph_or_merge": True,
                    "evidence": "The door absorbs the shoulder, back, torso, and shirt boundary."
                }
            ]
        }
    ]
    record["ambiguous_regions"] = ["Zuv shares one unresolved mass with the door"]
    record["unresolved_intersections"] = ["door edge enters Zuv's torso"]
    (package / "visual-qa.json").write_text(json.dumps(qa), encoding="utf-8")

    with (
        patch("pipeline.stages.codex_builtin_image_generation.visual_plan_quality_gate_reason", return_value=None),
        patch("pipeline.stages.codex_builtin_image_generation.identity_consistency_gate_reason", return_value=None),
        patch("pipeline.stages.codex_builtin_image_generation.validate_frame_readability", return_value=[]),
    ):
        result = promote_quarantined_codex_builtin_outputs(package)

    assert result["status"] == "REJECTED_SPATIAL_INTEGRITY"
    assert result["proof_state"] == "REJECTED_SPATIAL_INTEGRITY"
    assert not (package / "final" / "slide-01.png").exists()
