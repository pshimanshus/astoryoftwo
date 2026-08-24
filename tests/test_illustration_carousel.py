from __future__ import annotations

import json
from datetime import date
from pathlib import Path

from PIL import Image
import pytest

from pipeline.stages.carousel_quality import build_final_audit
from pipeline.stages.codex_builtin_image_generation import (
    package_codex_builtin_outputs,
    prepare_codex_builtin_image_generation,
    promote_quarantined_codex_builtin_outputs,
    run_fail_closed_visual_worker,
)
from pipeline.stages.carousel_format_contract import write_format_contract
from pipeline.stages.codex_native_carousel import create_codex_native_carousel


def _write_png(path: Path, size: tuple[int, int] = (1080, 1440), color: str = "ivory") -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    Image.new("RGB", size, color=color).save(path)
    return path


def _brief(path: Path) -> Path:
    slides = [
        {
            "copy": copy,
            "physical_action": action,
            "relationship_state": state,
        }
        for copy, action, state in (
            ("I was never unsure of you.", "Aachu places one house key in Zuv's open palm.", "certain of each other"),
            ("Then life asked harder questions.", "They stand over the same moving box, pointing toward different doorways.", "uncertain about direction"),
            ("Some days, love did not tell us what to do.", "They sit at opposite ends of a dining table, each pulling the same paper map toward themselves.", "love present inside conflict"),
            ("We are still learning how.", "They turn the map around and trace one route together.", "committed and learning"),
        )
    ]
    path.write_text(json.dumps({"slides": slides}), encoding="utf-8")
    return path


def _package(tmp_path: Path) -> Path:
    identity = _write_png(tmp_path / "identity.png", (400, 400), "tan")
    story_reference = _write_png(tmp_path / "story-reference.png", (400, 400), "skyblue")
    return create_codex_native_carousel(
        story="Certain of you, lost in us",
        image_paths=[story_reference],
        identity_image_paths=[identity],
        title="Certain of You",
        output_root=tmp_path / "output" / "carousels",
        creative_baseline_path=_brief(tmp_path / "brief.json"),
        today=date(2026, 8, 24),
    )


def _qa_from_state(state: dict[str, object], *, creator_approved: bool = False) -> dict[str, object]:
    records = []
    for candidate in state["quarantine_candidates"]:  # type: ignore[index]
        candidate = dict(candidate)
        copy = str(candidate["copy"])
        records.append(
            {
                "slide": candidate["slide"],
                "native_outputs": candidate["native_outputs"],
                "checks": {
                    "semantic_action": {"status": "PASS", "evidence": "The intended physical action is plainly visible."},
                    "relationship_state": {"status": "PASS", "evidence": "Their body language clearly carries the intended relationship state."},
                    "anatomy_spatial": {"status": "PASS", "evidence": "Two people, natural limbs, attached hands, and believable contact are visible."},
                    "identity": {"status": "PASS", "evidence": "Aachu and Zuv match the attached identity reference."},
                    "exact_text": {"status": "PASS", "expected": copy, "observed": copy, "evidence": "Every character matches the locked slide copy."},
                    "brandmark": {"status": "PASS", "observed": "@a.storyof.two", "evidence": "The tiny brandmark is visible at top-right."},
                    "style": {"status": "PASS", "evidence": "Warm ivory watercolor-and-ink style is consistent."},
                },
            }
        )
    payload: dict[str, object] = {
        "schema_version": "carousel-pixel-qa/v1",
        "scope": "proof" if state["stage"] == "proof" else "final_deck",
        "status": "PASS",
        "image_set_sha256": state["image_set_sha256"],
        "slides": records,
    }
    if creator_approved:
        payload["creator_approval"] = {
            "status": "APPROVED",
            "approved": True,
            "approved_by": "creator",
            "image_set_sha256": state["image_set_sha256"],
        }
    return payload


def _generated_set(tmp_path: Path, selected: list[int]) -> dict[str, list[Path]]:
    return {
        "instagram_post": [
            _write_png(tmp_path / "generated" / f"slide-{number:02d}.png", color="linen")
            for number in selected
        ]
    }


def _publish_complete_deck(package: Path, tmp_path: Path) -> dict[str, object]:
    prepare_codex_builtin_image_generation(package, proof_slide=3)
    proof = package_codex_builtin_outputs(package, _generated_set(tmp_path, [3]), proof_slide=3)
    (package / "proof-qa.json").write_text(
        json.dumps(_qa_from_state(proof, creator_approved=True)),
        encoding="utf-8",
    )
    promote_quarantined_codex_builtin_outputs(package)
    batch_handoff = prepare_codex_builtin_image_generation(package)
    batch = package_codex_builtin_outputs(
        package,
        _generated_set(tmp_path / "batch", batch_handoff["selected_slides"]),
    )
    (package / "visual-qa.json").write_text(
        json.dumps(_qa_from_state(batch)),
        encoding="utf-8",
    )
    return promote_quarantined_codex_builtin_outputs(package)


def test_creation_writes_only_small_preproof_contract(tmp_path: Path) -> None:
    package = _package(tmp_path)
    root_files = {path.name for path in package.iterdir() if path.is_file()}
    assert root_files == {
        "creative-context.json",
        "format-contract.json",
        "slides.json",
        "prompt-pack.json",
        "generation-state.json",
    }
    assert not (package / "manifest.json").exists()
    assert not (package / "run-ledger.json").exists()
    assert not (package / "final-images.json").exists()
    assert not (package / "final-audit.json").exists()

    prompt_pack = json.loads((package / "prompt-pack.json").read_text(encoding="utf-8"))
    assert set(prompt_pack) == {
        "schema_version",
        "generation_mode",
        "brandmark",
        "style_prompt",
        "negative_prompt",
        "style_reference_images",
        "identity_reference_images",
        "identity_dossier_reference_images",
        "slides",
    }
    assert len((package / "prompt-pack.json").read_bytes()) < 30_000
    identity_path = prompt_pack["identity_reference_images"][0]
    assert identity_path.startswith(".internal/references/identity/")
    assert (package / identity_path).is_file()
    context = json.loads((package / "creative-context.json").read_text(encoding="utf-8"))
    assert context["identity_references"][0]["path"] == identity_path


def test_story_only_fallback_cannot_enter_proof_with_placeholder_actions(tmp_path: Path) -> None:
    identity = _write_png(tmp_path / "identity.png", (400, 400), "tan")
    package = create_codex_native_carousel(
        story="Certain of you. Still learning how.",
        image_paths=[],
        identity_image_paths=[identity],
        title="Needs Scenes",
        slide_count=4,
        output_root=tmp_path / "output" / "carousels",
        today=date(2026, 8, 24),
    )

    result = prepare_codex_builtin_image_generation(package)

    assert result["status"] == "blocked"
    assert result["next_action"] == "define_physical_actions"
    assert "physical action" in result["reason"]


@pytest.mark.parametrize(
    "bad_action",
    ["TBD", "Locked copy 1"],
)
def test_placeholder_or_copy_repeated_action_cannot_create_package(
    tmp_path: Path,
    bad_action: str,
) -> None:
    identity = _write_png(tmp_path / "identity.png", (400, 400), "tan")
    brief = tmp_path / "bad-brief.json"
    brief.write_text(
        json.dumps(
            {
                "slides": [
                    {
                        "copy": f"Locked copy {number}",
                        "physical_action": bad_action if number == 1 else f"They complete visible action {number} together.",
                    }
                    for number in range(1, 5)
                ]
            }
        ),
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="physical action"):
            create_codex_native_carousel(
                story="A shared decision",
                image_paths=[],
                identity_image_paths=[identity],
            creative_baseline_path=brief,
            output_root=tmp_path / "output/carousels",
            today=date(2026, 8, 24),
        )


def test_proof_first_then_complete_deck_promotes_only_after_pixel_qa(tmp_path: Path) -> None:
    package = _package(tmp_path)
    handoff = prepare_codex_builtin_image_generation(package, proof_slide=3)
    assert handoff["status"] == "handoff_ready"
    assert handoff["stage"] == "proof"
    assert handoff["selected_slides"] == [3]
    assert not (package / "final-images.json").exists()
    handoff_text = (
        package / ".internal/compiled-prompts/instagram-post/slide-03.md"
    ).read_text(encoding="utf-8")
    assert "/references/identity/" in handoff_text
    assert "/references/story/" in handoff_text
    assert "/references/style/" in handoff_text
    assert str(tmp_path) not in handoff_text
    assert all(
        not Path(binding["path"]).is_absolute()
        and binding["path"].startswith(".internal/references/identity/")
        for binding in handoff["identity_reference_bindings"]
    )

    proof = package_codex_builtin_outputs(
        package,
        _generated_set(tmp_path, [3]),
        proof_slide=3,
    )
    assert proof["status"] == "generated_quarantined"
    assert (package / ".internal/visual-quarantine/slide-03/attempt-01/instagram_post.png").is_file()
    assert not (package / "final/slide-03.png").exists()

    (package / "proof-qa.json").write_text(
        json.dumps(_qa_from_state(proof, creator_approved=True)),
        encoding="utf-8",
    )
    approved = promote_quarantined_codex_builtin_outputs(package)
    assert approved["status"] == "BATCH_ALLOWED"
    assert approved["next_action"] == "prepare_remaining_slides"
    assert not (package / "final-images.json").exists()

    batch_handoff = prepare_codex_builtin_image_generation(package)
    assert batch_handoff["stage"] == "batch"
    assert batch_handoff["selected_slides"] == [1, 2, 3, 4]
    batch = package_codex_builtin_outputs(
        package,
        _generated_set(tmp_path / "batch", [1, 2, 3, 4]),
    )
    assert batch["status"] == "generated_quarantined"
    assert not (package / "final-images.json").exists()

    (package / "visual-qa.json").write_text(
        json.dumps(_qa_from_state(batch)),
        encoding="utf-8",
    )
    final_state = promote_quarantined_codex_builtin_outputs(package)
    assert final_state["status"] == "publish_ready"
    assert sorted((package / "final").glob("*.png")) == [
        package / "final" / f"slide-{number:02d}.png" for number in range(1, 5)
    ]
    final = json.loads((package / "final-images.json").read_text(encoding="utf-8"))
    assert final["slide_count"] == 4
    assert final["requested_formats"] == ["instagram_post"]
    assert final["identity_reference_bindings"] == handoff["identity_reference_bindings"]
    assert final["reference_bindings"] == handoff["reference_bindings"]
    assert all(output["width"] == 1080 and output["height"] == 1440 for record in final["slides"] for output in record["native_outputs"].values())
    audit = json.loads((package / "final-audit.json").read_text(encoding="utf-8"))
    assert audit["pass"] is True


@pytest.mark.parametrize("mutation", ["slides", "prompt_pack", "reference"])
def test_compiled_handoff_binds_source_json_and_reference_bytes(
    tmp_path: Path,
    mutation: str,
) -> None:
    package = _package(tmp_path)
    handoff = prepare_codex_builtin_image_generation(package, proof_slide=3)
    if mutation == "slides":
        slides = json.loads((package / "slides.json").read_text(encoding="utf-8"))
        slides[2]["copy"] = "Changed after compilation."
        (package / "slides.json").write_text(json.dumps(slides), encoding="utf-8")
    elif mutation == "prompt_pack":
        prompt_pack = json.loads((package / "prompt-pack.json").read_text(encoding="utf-8"))
        prompt_pack["style_prompt"] = "Changed after compilation."
        (package / "prompt-pack.json").write_text(json.dumps(prompt_pack), encoding="utf-8")
    else:
        identity = next(
            binding for binding in handoff["reference_bindings"] if "identity" in binding["roles"]
        )
        _write_png(package / identity["path"], (400, 400), "red")

    blocked = package_codex_builtin_outputs(
        package,
        _generated_set(tmp_path / "stale", [3]),
        proof_slide=3,
    )

    assert blocked["status"] == "blocked"
    assert blocked["next_action"] == "recompile_prompt_handoff"


def test_explicit_format_lock_never_generates_unrequested_derivatives(tmp_path: Path) -> None:
    package = _package(tmp_path)
    contract = json.loads((package / "format-contract.json").read_text(encoding="utf-8"))
    assert contract["requested_formats"] == ["instagram_post"]
    prepare_codex_builtin_image_generation(package, proof_slide=1)
    assert not (package / "final-reels-stories").exists()
    assert not (package / "final-square").exists()


def test_explicit_format_change_after_approval_requires_a_new_proof(tmp_path: Path) -> None:
    package = _package(tmp_path)
    prepare_codex_builtin_image_generation(package, proof_slide=3)
    proof = package_codex_builtin_outputs(package, _generated_set(tmp_path, [3]), proof_slide=3)
    (package / "proof-qa.json").write_text(
        json.dumps(_qa_from_state(proof, creator_approved=True)),
        encoding="utf-8",
    )
    approved = promote_quarantined_codex_builtin_outputs(package)
    assert approved["proof_approved"] is True

    changed = prepare_codex_builtin_image_generation(package, formats=["square"])

    assert changed["status"] == "handoff_ready"
    assert changed["stage"] == "proof"
    assert changed["requested_formats"] == ["square"]
    assert changed["proof_approved"] is False
    assert all(value == 0 for value in changed["attempts_by_slide"].values())


def test_manual_format_drift_after_approval_blocks_batch(tmp_path: Path) -> None:
    package = _package(tmp_path)
    prepare_codex_builtin_image_generation(package, proof_slide=3)
    proof = package_codex_builtin_outputs(package, _generated_set(tmp_path, [3]), proof_slide=3)
    (package / "proof-qa.json").write_text(
        json.dumps(_qa_from_state(proof, creator_approved=True)),
        encoding="utf-8",
    )
    promote_quarantined_codex_builtin_outputs(package)
    write_format_contract(package, ["square"], source="manual_test", replace=True)

    blocked = prepare_codex_builtin_image_generation(package)

    assert blocked["status"] == "blocked"
    assert blocked["next_action"] == "regenerate_proof_for_format_change"


def test_format_correction_after_publish_removes_stale_public_evidence(tmp_path: Path) -> None:
    package = _package(tmp_path)
    published = _publish_complete_deck(package, tmp_path)
    assert published["status"] == "publish_ready"
    assert (package / "final-images.json").is_file()
    assert (package / "final").is_dir()

    changed = prepare_codex_builtin_image_generation(package, formats=["square"])

    assert changed["status"] == "handoff_ready"
    assert changed["stage"] == "proof"
    assert not (package / "final-images.json").exists()
    assert not (package / "final-audit.json").exists()
    assert not (package / "final").exists()


def test_final_audit_rehashes_every_package_reference(tmp_path: Path) -> None:
    package = _package(tmp_path)
    published = _publish_complete_deck(package, tmp_path)
    assert published["status"] == "publish_ready"
    final = json.loads((package / "final-images.json").read_text(encoding="utf-8"))
    identity = next(
        binding for binding in final["reference_bindings"] if "identity" in binding["roles"]
    )
    _write_png(package / identity["path"], (400, 400), "red")

    audit = build_final_audit(package, write=False)

    assert audit["pass"] is False
    assert f"final reference hash is stale: {identity['path']}" in audit["issues"]


def test_proof_repair_uses_only_proof_qa_and_can_unlock_batch(tmp_path: Path) -> None:
    package = _package(tmp_path)
    reviews = 0

    def generate(attempt: int, _issues: list[str]) -> dict[str, list[Path]]:
        state = json.loads((package / "generation-state.json").read_text(encoding="utf-8"))
        return _generated_set(tmp_path / f"worker-{attempt}", state["selected_slides"])

    def review(state: dict[str, object]) -> dict[str, object]:
        nonlocal reviews
        reviews += 1
        qa = _qa_from_state(state, creator_approved=reviews == 2)
        if reviews == 1:
            qa["status"] = "FAIL"
            qa["slides"][0]["checks"]["semantic_action"] = {  # type: ignore[index]
                "status": "FAIL",
                "evidence": "The intended shared physical action is not visible.",
            }
        return qa

    result = run_fail_closed_visual_worker(
        package,
        generate_attempt=generate,
        review_attempt=review,
    )

    assert result["status"] == "BATCH_ALLOWED"
    assert result["proof_approved"] is True
    assert (package / "proof-qa.json").is_file()
    assert not (package / "visual-qa.json").exists()


def test_failed_final_audit_never_promotes_requested_public_finals(tmp_path: Path) -> None:
    package = _package(tmp_path)
    prepare_codex_builtin_image_generation(package, proof_slide=3)
    proof = package_codex_builtin_outputs(package, _generated_set(tmp_path, [3]), proof_slide=3)
    (package / "proof-qa.json").write_text(
        json.dumps(_qa_from_state(proof, creator_approved=True)),
        encoding="utf-8",
    )
    promote_quarantined_codex_builtin_outputs(package)
    batch_handoff = prepare_codex_builtin_image_generation(package)
    batch = package_codex_builtin_outputs(
        package,
        _generated_set(tmp_path / "batch", batch_handoff["selected_slides"]),
    )
    (package / "visual-qa.json").write_text(
        json.dumps(_qa_from_state(batch)),
        encoding="utf-8",
    )
    _write_png(package / "final-square/stale.png", (1080, 1080))

    result = promote_quarantined_codex_builtin_outputs(package)

    assert result["status"] == "generated_audit_failed"
    assert not (package / "final").exists()
    assert not (package / "final-images.json").exists()
    audit = json.loads((package / "final-audit.json").read_text(encoding="utf-8"))
    assert audit["pass"] is False
    assert "unrequested format contains PNGs: square" in audit["issues"]
