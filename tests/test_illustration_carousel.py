from __future__ import annotations

import json
from datetime import date
from pathlib import Path

from PIL import Image
import pytest

from pipeline.agentic.workflow_doctor import inspect_carousel_package
from pipeline.stages.codex_builtin_image_generation import (
    approve_proof,
    current_proof_binding_sha256,
    finalize_codex_builtin_outputs,
    ingest_generated_outputs,
    prepare_codex_builtin_image_generation,
    read_generation_state,
    reconcile_package_state,
    review_quarantined_outputs,
)
from pipeline.stages.codex_native_carousel import create_codex_native_carousel
from pipeline.stages.carousel_pixel_qa import manifest_fingerprint


def _png(path: Path, size: tuple[int, int] = (1080, 1440), color: str = "ivory") -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    Image.new("RGB", size, color=color).save(path)
    return path


def _brief(path: Path) -> Path:
    path.write_text(
        json.dumps(
            {
                "slides": [
                    {
                        "copy": copy,
                        "physical_action": action,
                        "relationship_state": relationship,
                    }
                    for copy, action, relationship in (
                        ("I was never unsure of you.", "Aachu places one house key in Zuv's open palm.", "certain"),
                        ("Then life asked harder questions.", "They point toward different doorways over one box.", "uncertain"),
                        ("Love did not tell us what to do.", "They pull one paper map toward opposite sides of the table.", "conflict"),
                        ("We are still learning how.", "They turn the map and trace one route together.", "committed"),
                    )
                ]
            }
        ),
        encoding="utf-8",
    )
    return path


def _package(tmp_path: Path) -> Path:
    identity_paths = [
        _png(tmp_path / "identity/aachu/a.png", (50, 50), "salmon"),
        _png(tmp_path / "identity/zuv/z.png", (50, 50), "skyblue"),
        _png(tmp_path / "identity/together/face.png", (50, 50), "tan"),
        _png(tmp_path / "identity/together/body.png", (50, 50), "plum"),
    ]
    return create_codex_native_carousel(
        story="Certain of you, lost in us",
        image_paths=[_png(tmp_path / "story.png", (50, 50), "skyblue")],
        identity_image_paths=identity_paths,
        style_reference_paths=[_png(tmp_path / "style.png", (50, 50), "ivory")],
        title="Certain of You",
        creative_baseline_path=_brief(tmp_path / "brief.json"),
        output_root=tmp_path / "output/carousels",
        today=date(2026, 8, 24),
    )


def _authored_qa(package: Path, slides: list[int], *, scope: str) -> dict[str, object]:
    prompt_pack = json.loads((package / "prompt-pack.json").read_text(encoding="utf-8"))
    style = prompt_pack["style_reference_images"][0]
    context = json.loads((package / "creative-context.json").read_text(encoding="utf-8"))
    role_paths = {
        record["role"]: record["path"]
        for record in context["identity_reference_selection"]["selected_references"]
    }
    slide_records = json.loads((package / "slides.json").read_text(encoding="utf-8"))
    copy_by_slide = {int(item["slide"]): item["copy"] for item in slide_records}
    return {
        "status": "PASS",
        "inspection": {
            "method": "codex_view_image",
            "decoded_pixels_observed": True,
        },
        "selected_slides": slides,
        "slides": [
            {
                "slide": number,
                "reviews": {
                    "instagram_post": {
                        "checks": {
                            "physical_action": {"status": "PASS", "evidence": "The intended physical action is visibly clear."},
                            "relationship_state": {"status": "PASS", "evidence": "Their posture visibly proves the relationship beat."},
                            "entity_spatial_integrity": {"status": "PASS", "evidence": "Two complete people and attached hands occupy coherent space."},
                            "identity_wardrobe_accessories": {
                                "status": "PASS",
                                "evidence": "Aachu and Zuv match the attached whole-person reference.",
                                "references": {
                                    "aachu": [role_paths["Aachu identity anchor"]],
                                    "zuv": [role_paths["Zuv identity anchor"]],
                                    "together": [
                                        role_paths["together face/scale anchor"],
                                        role_paths["together body/posture anchor"],
                                    ],
                                },
                            },
                            "text_brandmark_style_dimensions": {
                                "status": "PASS",
                                "evidence": "Exact text, tiny top-right brandmark, style, and native canvas are visible.",
                                "expected_text": copy_by_slide[number],
                                "observed_text": copy_by_slide[number],
                                "observed_brandmark": "@a.storyof.two",
                                "style_references": [style],
                            },
                        }
                    }
                },
            }
            for number in slides
        ],
        "scope": scope,
    }


def _generated(tmp_path: Path, selected: list[int]) -> dict[str, list[Path]]:
    return {
        "instagram_post": [
            _png(tmp_path / f"slide-{number:02d}.png", color="linen")
            for number in selected
        ]
    }


def _approve_proof(package: Path, tmp_path: Path, proof_slide: int = 3) -> None:
    prepare_codex_builtin_image_generation(package, proof_slide=proof_slide)
    ingest_generated_outputs(package, _generated(tmp_path / "proof", [proof_slide]), proof_slide=proof_slide)
    (package / "proof-qa.json").write_text(
        json.dumps(_authored_qa(package, [proof_slide], scope="proof")), encoding="utf-8"
    )
    reviewed = review_quarantined_outputs(package)
    assert reviewed["status"] == "awaiting_creator_proof_approval"
    approve_proof(
        package,
        approved_by="creator",
        proof_sha256=current_proof_binding_sha256(package),
    )


def _publish(package: Path, tmp_path: Path) -> dict[str, object]:
    _approve_proof(package, tmp_path)
    handoff = prepare_codex_builtin_image_generation(package)
    assert 3 not in handoff["selected_slides"]
    ingest_generated_outputs(package, _generated(tmp_path / "batch", handoff["selected_slides"]))
    (package / "visual-qa.json").write_text(
        json.dumps(_authored_qa(package, [1, 2, 3, 4], scope="final")), encoding="utf-8"
    )
    reviewed = review_quarantined_outputs(package)
    assert reviewed["status"] == "final_qa_required"
    assert reviewed["next_action"] == "finalize_deck"
    return finalize_codex_builtin_outputs(package)


def test_creation_writes_only_small_v3_preproof_contract(tmp_path: Path) -> None:
    package = _package(tmp_path)
    root_files = {path.name for path in package.iterdir() if path.is_file()}
    assert root_files == {
        "creative-context.json",
        "format-contract.json",
        "slides.json",
        "prompt-pack.json",
        "generation-state.json",
    }
    assert read_generation_state(package)["schema_version"] == "carousel-generation-state/v3"


def test_story_only_fallback_stays_truthful_draft_then_blocks_prepare(tmp_path: Path) -> None:
    package = create_codex_native_carousel(
        story="Certain of you. Still learning how.",
        image_paths=[],
        identity_image_paths=[_png(tmp_path / "identity.png", (40, 40))],
        title="Needs Scenes",
        slide_count=4,
        output_root=tmp_path / "output/carousels",
        today=date(2026, 8, 24),
    )
    assert read_generation_state(package)["status"] == "draft"
    assert read_generation_state(package)["next_action"] == "lock_visible_actions"
    blocked = prepare_codex_builtin_image_generation(package)
    assert blocked["status"] == "blocked"
    assert blocked["next_action"] == "lock_visible_actions"


def test_pre_generation_gate_rejects_three_identity_references_and_no_style(
    tmp_path: Path,
) -> None:
    identities = [
        _png(tmp_path / "short/aachu/a.png", (40, 40), "salmon"),
        _png(tmp_path / "short/zuv/z.png", (40, 40), "skyblue"),
        _png(tmp_path / "short/together/face.png", (40, 40), "tan"),
    ]
    brief = _brief(tmp_path / "short-brief.json")
    with pytest.raises(ValueError, match="exactly 1 explicit style board"):
        create_codex_native_carousel(
            story="Certain of you, lost in us",
            image_paths=[],
            identity_image_paths=identities,
            style_reference_paths=[],
            creative_baseline_path=brief,
            output_root=tmp_path / "short-output/carousels",
            today=date(2026, 8, 24),
        )
    package = create_codex_native_carousel(
        story="Certain of you, lost in us",
        image_paths=[],
        identity_image_paths=identities,
        style_reference_paths=[_png(tmp_path / "short/style.png", (40, 40), "ivory")],
        creative_baseline_path=brief,
        output_root=tmp_path / "short-output/carousels",
        today=date(2026, 8, 24),
    )

    blocked = prepare_codex_builtin_image_generation(package, proof_slide=1)

    assert blocked["status"] == "blocked"
    assert blocked["next_action"] == (
        "attach_four_curated_identity_references_and_one_style_board"
    )
    assert "Exactly four" in blocked["reason"]


def test_pre_generation_gate_rejects_missing_style_and_identity_role(
    tmp_path: Path,
) -> None:
    missing_style = _package(tmp_path / "missing-style")
    prompt_path = missing_style / "prompt-pack.json"
    prompt = json.loads(prompt_path.read_text(encoding="utf-8"))
    prompt["style_reference_images"] = []
    prompt_path.write_text(json.dumps(prompt), encoding="utf-8")
    blocked_style = prepare_codex_builtin_image_generation(missing_style, proof_slide=1)
    assert blocked_style["status"] == "blocked"
    assert "Exactly one style board" in blocked_style["reason"]

    missing_role = _package(tmp_path / "missing-role")
    context_path = missing_role / "creative-context.json"
    context = json.loads(context_path.read_text(encoding="utf-8"))
    selected = context["identity_reference_selection"]["selected_references"]
    selected[-1]["role"] = selected[-2]["role"]
    context_path.write_text(json.dumps(context), encoding="utf-8")
    blocked_role = prepare_codex_builtin_image_generation(missing_role, proof_slide=1)
    assert blocked_role["status"] == "blocked"
    assert "Exactly the Aachu, Zuv" in blocked_role["reason"]


def test_pre_generation_gate_rejects_attachment_overflow(tmp_path: Path) -> None:
    package = _package(tmp_path)
    extra = _png(package / ".internal/references/identity/extra.png", (40, 40), "black")
    prompt_path = package / "prompt-pack.json"
    prompt = json.loads(prompt_path.read_text(encoding="utf-8"))
    prompt["identity_reference_images"].append(extra.relative_to(package).as_posix())
    prompt_path.write_text(json.dumps(prompt), encoding="utf-8")

    blocked = prepare_codex_builtin_image_generation(package, proof_slide=1)

    assert blocked["status"] == "blocked"
    assert "Exactly four" in blocked["reason"]


def test_approved_proof_is_reused_and_excluded_from_batch(tmp_path: Path) -> None:
    package = _package(tmp_path)
    _approve_proof(package, tmp_path)
    state = read_generation_state(package)
    assert state["status"] == "batch_ready"
    assert (package / ".internal/approved-final-candidates/slide-03/candidate.json").is_file()
    handoff = prepare_codex_builtin_image_generation(package)
    assert handoff["selected_slides"] == [1, 2, 4]
    assert not list((package / ".internal/compiled-prompts").rglob("*.md"))


@pytest.mark.parametrize("tamper", ["observation", "status", "asset_binding"])
def test_post_approval_qa_tampering_revokes_batch(
    tmp_path: Path,
    tamper: str,
) -> None:
    package = _package(tmp_path)
    _approve_proof(package, tmp_path)
    qa_path = package / "proof-qa.json"
    qa = json.loads(qa_path.read_text(encoding="utf-8"))
    if tamper == "observation":
        qa["slides"][0]["reviews"]["instagram_post"]["checks"]["physical_action"][
            "evidence"
        ] = "Altered after the creator approved this exact review."
    elif tamper == "status":
        qa["status"] = "FAIL"
    else:
        qa["slides"][0]["asset_bindings"]["instagram_post"]["sha256"] = "sha256:" + (
            "0" * 64
        )
    qa_path.write_text(json.dumps(qa), encoding="utf-8")

    state = reconcile_package_state(package)

    assert state["status"] == "proof_qa_required"
    assert state["selected_slides"] == [3]
    assert state["next_action"] == "review_proof_pixels"
    assert not (package / ".internal/approved-final-candidates/slide-03").exists()
    rebound = json.loads(qa_path.read_text(encoding="utf-8"))
    assert "creator_approval" not in rebound


def test_post_approval_proof_asset_tampering_revokes_batch(tmp_path: Path) -> None:
    package = _package(tmp_path)
    _approve_proof(package, tmp_path)
    state = read_generation_state(package)
    candidate_path = (
        package
        / ".internal/visual-quarantine/slide-03"
        / f"attempt-{state['slides']['3']['attempts']:02d}"
        / "candidate.json"
    )
    candidate = json.loads(candidate_path.read_text(encoding="utf-8"))
    binding = candidate["native_outputs"]["instagram_post"]
    _png(package / binding["path"], color="red")

    revoked = reconcile_package_state(package)

    assert revoked["status"] == "proof_failed"
    assert revoked["selected_slides"] == [3]
    assert revoked["next_action"] == "retry_selected_slides"
    assert not (package / ".internal/approved-final-candidates/slide-03").exists()


def test_approve_proof_requires_nonempty_exact_binding(tmp_path: Path) -> None:
    package = _package(tmp_path)
    prepare_codex_builtin_image_generation(package, proof_slide=3)
    ingest_generated_outputs(
        package, _generated(tmp_path / "proof", [3]), proof_slide=3
    )
    (package / "proof-qa.json").write_text(
        json.dumps(_authored_qa(package, [3], scope="proof")), encoding="utf-8"
    )
    review_quarantined_outputs(package)

    with pytest.raises(ValueError, match="proof_sha256 is required"):
        approve_proof(package, proof_sha256="")
    with pytest.raises(ValueError, match="does not match"):
        approve_proof(package, proof_sha256="sha256:" + "0" * 64)


def test_candidate_record_swap_after_qa_is_rejected_by_approval(tmp_path: Path) -> None:
    package = _package(tmp_path)
    prepare_codex_builtin_image_generation(package, proof_slide=3)
    ingest_generated_outputs(
        package, _generated(tmp_path / "proof", [3]), proof_slide=3
    )
    (package / "proof-qa.json").write_text(
        json.dumps(_authored_qa(package, [3], scope="proof")), encoding="utf-8"
    )
    review_quarantined_outputs(package)
    exact_binding = current_proof_binding_sha256(package)
    candidate_path = package / ".internal/visual-quarantine/slide-03/attempt-01/candidate.json"
    candidate = json.loads(candidate_path.read_text(encoding="utf-8"))
    candidate["slide"] = 2
    candidate_path.write_text(json.dumps(candidate), encoding="utf-8")

    report = inspect_carousel_package(package)
    assert any(issue.code == "proof_pixel_qa_incomplete" for issue in report.issues)
    with pytest.raises(ValueError, match="passing current proof QA is required"):
        approve_proof(package, proof_sha256=exact_binding)

    reconciled = reconcile_package_state(package)
    assert reconciled["status"] == "proof_qa_required"
    assert reconciled["next_action"] == "repair_proof_qa"
    assert reconciled["selected_slides"] == [3]
    assert reconciled["slides"]["3"]["attempts"] == 1


def test_candidate_record_swap_after_approval_revokes_batch(tmp_path: Path) -> None:
    package = _package(tmp_path)
    _approve_proof(package, tmp_path)
    candidate_path = package / ".internal/visual-quarantine/slide-03/attempt-01/candidate.json"
    candidate = json.loads(candidate_path.read_text(encoding="utf-8"))
    candidate["slide"] = 2
    candidate_path.write_text(json.dumps(candidate), encoding="utf-8")

    revoked = reconcile_package_state(package)

    assert revoked["status"] == "proof_failed"
    assert revoked["selected_slides"] == [3]
    assert not (package / ".internal/approved-final-candidates/slide-03").exists()


def test_proof_qa_schema_error_repairs_qa_without_spending_image_attempt(
    tmp_path: Path,
) -> None:
    package = _package(tmp_path)
    prepare_codex_builtin_image_generation(package, proof_slide=3)
    ingest_generated_outputs(
        package, _generated(tmp_path / "proof", [3]), proof_slide=3
    )
    qa = _authored_qa(package, [3], scope="proof")
    qa.pop("inspection")
    (package / "proof-qa.json").write_text(json.dumps(qa), encoding="utf-8")

    repaired = review_quarantined_outputs(package)

    assert repaired["status"] == "proof_qa_required"
    assert repaired["next_action"] == "repair_proof_qa"
    assert repaired["slides"]["3"]["attempts"] == 1


def test_mixed_batch_semantic_failure_retries_only_first_failed_slide(
    tmp_path: Path,
) -> None:
    package = _package(tmp_path)
    _approve_proof(package, tmp_path)
    handoff = prepare_codex_builtin_image_generation(package)
    ingest_generated_outputs(
        package, _generated(tmp_path / "batch", handoff["selected_slides"])
    )
    state_before = read_generation_state(package)
    candidate_bytes = {
        number: (
            package
            / ".internal/visual-quarantine"
            / f"slide-{number:02d}"
            / f"attempt-{state_before['slides'][str(number)]['attempts']:02d}"
            / "candidate.json"
        ).read_bytes()
        for number in handoff["selected_slides"]
    }
    qa = _authored_qa(package, [1, 2, 3, 4], scope="final")
    qa["status"] = "FAIL"
    slide_one = next(record for record in qa["slides"] if record["slide"] == 1)
    slide_one["reviews"]["instagram_post"]["checks"]["physical_action"] = {
        "status": "FAIL",
        "evidence": "The intended physical action is not visible.",
    }
    (package / "visual-qa.json").write_text(json.dumps(qa), encoding="utf-8")

    failed = review_quarantined_outputs(package)

    assert failed["status"] == "final_qa_failed"
    assert failed["next_action"] == "retry_selected_slides"
    assert failed["selected_slides"] == [1]
    retry = prepare_codex_builtin_image_generation(package)
    assert retry["selected_slides"] == [1]
    for number in (2, 4):
        assert retry["slides"][str(number)]["attempts"] == 1
        candidate_path = (
            package
            / ".internal/visual-quarantine"
            / f"slide-{number:02d}/attempt-01/candidate.json"
        )
        assert candidate_path.read_bytes() == candidate_bytes[number]


def test_final_qa_binding_error_repairs_qa_without_spending_attempts(
    tmp_path: Path,
) -> None:
    package = _package(tmp_path)
    _approve_proof(package, tmp_path)
    handoff = prepare_codex_builtin_image_generation(package)
    ingest_generated_outputs(
        package, _generated(tmp_path / "batch", handoff["selected_slides"])
    )
    before = read_generation_state(package)
    qa = _authored_qa(package, [1, 2, 3, 4], scope="final")
    qa["manifest_sha256"] = "sha256:" + "0" * 64
    (package / "visual-qa.json").write_text(json.dumps(qa), encoding="utf-8")

    repaired = review_quarantined_outputs(package)

    assert repaired["status"] == "final_qa_required"
    assert repaired["next_action"] == "repair_final_qa"
    assert {
        number: record["attempts"] for number, record in repaired["slides"].items()
    } == {
        number: record["attempts"] for number, record in before["slides"].items()
    }


def test_identity_role_tamper_after_handoff_invalidates_all_and_doctor_blocks(
    tmp_path: Path,
) -> None:
    package = _package(tmp_path)
    prepared = prepare_codex_builtin_image_generation(package, proof_slide=3)
    assert prepared["status"] == "handoff_ready"
    context_path = package / "creative-context.json"
    context = json.loads(context_path.read_text(encoding="utf-8"))
    selected = context["identity_reference_selection"]["selected_references"]
    selected[-1]["role"] = selected[-2]["role"]
    context_path.write_text(json.dumps(context), encoding="utf-8")

    report = inspect_carousel_package(package)
    codes = {issue.code for issue in report.issues}
    assert "identity_references_missing" in codes
    assert "stale_slide_input_fingerprint" in codes

    invalidated = reconcile_package_state(package)
    assert invalidated["status"] == "draft"
    assert invalidated["selected_slides"] == []
    assert all(record["attempts"] == 0 for record in invalidated["slides"].values())
    assert not (package / ".internal/compiled-prompts").exists()


def test_complete_deck_promotes_only_after_bound_final_qa_and_hidden_audit(tmp_path: Path) -> None:
    package = _package(tmp_path)
    final_state = _publish(package, tmp_path)
    assert final_state["status"] == "publish_ready"
    final = json.loads((package / "final-images.json").read_text(encoding="utf-8"))
    assert set(final) == {"schema_version", "selected_formats", "format_sha256", "slides"}
    assert [item["slide"] for item in final["slides"]] == [1, 2, 3, 4]
    audit = json.loads((package / "final-audit.json").read_text(encoding="utf-8"))
    assert set(audit) == {"schema_version", "status", "issues", "manifest_sha256", "visual_qa_sha256"}
    assert audit["status"] == "PASS"


def test_format_change_after_approval_invalidates_every_candidate(tmp_path: Path) -> None:
    package = _package(tmp_path)
    _approve_proof(package, tmp_path)
    changed = prepare_codex_builtin_image_generation(package, formats=["square"])
    assert changed["status"] == "handoff_ready"
    assert changed["selected_formats"] == ["square"]
    assert all(record["attempts"] == 0 for record in changed["slides"].values())
    assert not (package / "proof-qa.json").exists()


def test_stale_handoff_is_rejected_nonzero_by_core(tmp_path: Path) -> None:
    package = _package(tmp_path)
    prepare_codex_builtin_image_generation(package, proof_slide=3)
    slides = json.loads((package / "slides.json").read_text(encoding="utf-8"))
    slides[2]["copy"] = "Changed after compilation."
    (package / "slides.json").write_text(json.dumps(slides), encoding="utf-8")
    with pytest.raises(ValueError, match="Prepare the compiled prompt"):
        ingest_generated_outputs(package, _generated(tmp_path / "stale", [3]), proof_slide=3)


def test_wrong_size_candidate_is_quarantined_and_counted_not_resized(tmp_path: Path) -> None:
    package = _package(tmp_path)
    prepare_codex_builtin_image_generation(package, proof_slide=1)
    state = ingest_generated_outputs(
        package,
        {"instagram_post": [_png(tmp_path / "wrong.png", (1440, 1800))]},
        proof_slide=1,
    )
    assert state["status"] == "proof_failed"
    assert state["slides"]["1"]["attempts"] == 1
    assert state["next_action"] == "retry_selected_slides"
    assert not (package / "final").exists()


def test_final_pixel_tampering_revokes_publish_ready(tmp_path: Path) -> None:
    package = _package(tmp_path)
    _publish(package, tmp_path)
    _png(package / "final/slide-02.png", color="red")
    state = reconcile_package_state(package)
    assert state["status"] == "final_qa_failed"
    assert not (package / "final").exists()
    assert not (package / "final-images.json").exists()
    assert not (package / "final-audit.json").exists()


def test_malformed_inputs_retract_every_public_final_claim(tmp_path: Path) -> None:
    package = _package(tmp_path)
    _publish(package, tmp_path)
    slides_path = package / "slides.json"
    slides = json.loads(slides_path.read_text(encoding="utf-8"))
    slides.reverse()
    slides_path.write_text(json.dumps(slides), encoding="utf-8")

    state = reconcile_package_state(package)

    assert state["status"] == "blocked"
    assert state["next_action"] == "repair_inputs"
    assert not (package / "final").exists()
    assert not (package / "final-images.json").exists()
    assert not (package / "visual-qa.json").exists()
    assert not (package / "final-audit.json").exists()


def test_slide_local_batch_correction_reuses_unaffected_current_candidates(
    tmp_path: Path,
) -> None:
    package = _package(tmp_path)
    _approve_proof(package, tmp_path)
    prepared = prepare_codex_builtin_image_generation(package)
    assert prepared["selected_slides"] == [1, 2, 4]
    ingest_generated_outputs(
        package,
        _generated(tmp_path / "batch-before-correction", [1, 2, 4]),
    )
    before = read_generation_state(package)
    preserved = {
        number: (
            package
            / f".internal/visual-quarantine/slide-{number:02d}/attempt-01/candidate.json"
        ).read_bytes()
        for number in (1, 4)
    }
    slides_path = package / "slides.json"
    slides = json.loads(slides_path.read_text(encoding="utf-8"))
    slides[1]["physical_action"] = (
        "Aachu rotates one moving box while Zuv braces its opposite corner."
    )
    slides[1]["visual"] = slides[1]["physical_action"]
    slides_path.write_text(json.dumps(slides), encoding="utf-8")

    reconciled = reconcile_package_state(package)
    next_handoff = prepare_codex_builtin_image_generation(package)

    assert reconciled["slides"]["1"]["attempts"] == before["slides"]["1"]["attempts"]
    assert reconciled["slides"]["2"]["attempts"] == 0
    assert reconciled["slides"]["4"]["attempts"] == before["slides"]["4"]["attempts"]
    assert next_handoff["selected_slides"] == [2]
    for number, expected in preserved.items():
        path = (
            package
            / f".internal/visual-quarantine/slide-{number:02d}/attempt-01/candidate.json"
        )
        assert path.read_bytes() == expected


def test_post_publish_visual_qa_prose_tamper_revokes_bound_audit(
    tmp_path: Path,
) -> None:
    package = _package(tmp_path)
    _publish(package, tmp_path)
    before = read_generation_state(package)
    approved_candidate_bytes = {
        number: (
            package
            / f".internal/approved-final-candidates/slide-{number:02d}/candidate.json"
        ).read_bytes()
        for number in (1, 2, 3, 4)
    }
    qa_path = package / "visual-qa.json"
    qa = json.loads(qa_path.read_text(encoding="utf-8"))
    qa["slides"][0]["reviews"]["instagram_post"]["checks"]["physical_action"][
        "evidence"
    ] = "Different prose written after the final audit passed."
    qa_path.write_text(json.dumps(qa), encoding="utf-8")

    report = inspect_carousel_package(package)
    stale = [issue for issue in report.issues if issue.code == "publish_evidence_stale"]
    assert stale
    assert "visual_qa_sha256" in stale[0].message

    revoked = reconcile_package_state(package)
    assert revoked["status"] == "final_qa_required"
    assert revoked["next_action"] == "repair_final_qa"
    assert revoked["selected_slides"] == [1, 2, 3, 4]
    assert {
        number: record["attempts"] for number, record in revoked["slides"].items()
    } == {
        number: record["attempts"] for number, record in before["slides"].items()
    }
    for number, expected in approved_candidate_bytes.items():
        path = (
            package
            / f".internal/approved-final-candidates/slide-{number:02d}/candidate.json"
        )
        assert path.read_bytes() == expected
    assert (package / ".internal/final-manifest-candidate.json").is_file()
    assert not (package / ".internal/final-audit-candidate/final-images.json").exists()
    assert not (package / "final").exists()
    assert not (package / "final-images.json").exists()
    assert not (package / "visual-qa.json").exists()
    assert not (package / "final-audit.json").exists()


def test_post_publish_coherent_manifest_and_qa_replacement_revokes_bound_audit(
    tmp_path: Path,
) -> None:
    package = _package(tmp_path)
    _publish(package, tmp_path)
    manifest_path = package / "final-images.json"
    qa_path = package / "visual-qa.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    # Reordering leaves complete valid inventory and exact asset bindings, but
    # changes the audited manifest semantics.
    manifest["slides"].reverse()
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
    qa = json.loads(qa_path.read_text(encoding="utf-8"))
    qa["manifest_sha256"] = manifest_fingerprint(manifest)
    qa_path.write_text(json.dumps(qa), encoding="utf-8")

    report = inspect_carousel_package(package)
    stale = [issue for issue in report.issues if issue.code == "publish_evidence_stale"]
    assert stale
    assert "manifest_sha256" in stale[0].message

    revoked = reconcile_package_state(package)
    assert revoked["status"] == "final_qa_failed"
    assert not (package / "final").exists()
    assert not (package / "final-images.json").exists()
    assert not (package / "visual-qa.json").exists()
    assert not (package / "final-audit.json").exists()
