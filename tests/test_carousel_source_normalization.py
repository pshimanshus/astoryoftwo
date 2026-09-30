from __future__ import annotations

from tests.helpers.imagegen_invocations import ingest_synthetic_outputs

import hashlib
import json
from datetime import date
from pathlib import Path

from PIL import Image
import pytest

from pipeline.stages.carousel_format_contract import source_dimensions_are_acceptable
from pipeline.stages.codex_builtin_image_generation import (
    _assert_current_receipt,
    approve_proof,
    current_proof_binding_sha256,
    finalize_codex_builtin_outputs,
    prepare_codex_builtin_image_generation,
    read_generation_state,
    reconcile_package_state,
    review_quarantined_outputs,
)
from pipeline.stages.codex_native_carousel import create_codex_native_carousel
from pipeline.stages.carousel_visual_storytelling import record_creator_feedback
from tests.helpers.carousel_qa import (
    passing_cinematic_story_frame,
    passing_entity_spatial_integrity,
)


def _png(path: Path, size: tuple[int, int], color: str = "linen") -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    Image.new("RGB", size, color).save(path)
    return path


def _cinematic_slide(number: int) -> dict[str, object]:
    is_final = number == 4
    return {
        "role": "payoff" if is_final else f"story_beat_{number}",
        "copy": f"Locked copy {number}",
        "physical_action": f"Aachu and Zuv move shared object {number} toward the window together.",
        "relationship_state": f"Their coordinated effort makes trust visible during beat {number}.",
        "camera": {
            "shot_size": "close payoff detail" if is_final else f"medium-wide action frame {number}",
            "position": f"table-height three-quarter view beside active object {number}",
            "negative_space": f"quiet upper-left wall above action beat {number}",
        },
        "focal_hierarchy": f"Their active hands read first, object {number} second, and upper copy stays clear.",
        "setting": {
            "place": f"their narrow apartment room beside window {number}",
            "time": "late rainy afternoon",
            "motivated_light": f"cool window light crosses frame-left over active object {number}",
            "depth_layers": {
                "foreground": f"chair edge leads toward action beat {number}",
                "midground": f"both partners move shared object {number} together",
                "background": f"rain-streaked window holds the destination for beat {number}",
            },
        },
        "visual_richness": {
            "point_of_view": f"Their shared hesitation organizes action beat {number}.",
            "before_frame": f"They had chosen separate directions before beat {number}.",
            "after_frame": f"They will settle the object together after beat {number}.",
            "continuation_pull": "" if is_final else f"Will their movement align after beat {number}?",
            "story_evidence": [
                {
                    "carrier": f"the marked shared object {number}",
                    "observable_state": "its position changes beneath both active grips",
                    "narrative_job": "proves their coordination through a visible consequence",
                },
                {
                    "carrier": f"their synchronized feet at beat {number}",
                    "observable_state": "both bodies step toward the same destination",
                    "narrative_job": "proves the relationship turn without relying on copy",
                },
            ],
            "posed_portrait_allowed": False,
            "decorative_clutter_allowed": False,
        },
    }


def _package(tmp_path: Path) -> Path:
    brief = tmp_path / "brief.json"
    brief.write_text(
        json.dumps(
            {
                "slides": [_cinematic_slide(number) for number in range(1, 5)]
            }
        ),
        encoding="utf-8",
    )
    identity_paths = [
        _png(tmp_path / "identity/aachu/a.png", (40, 40), "salmon"),
        _png(tmp_path / "identity/zuv/z.png", (40, 40), "skyblue"),
        _png(tmp_path / "identity/together/face.png", (40, 40), "tan"),
        _png(tmp_path / "identity/together/body.png", (40, 40), "plum"),
    ]
    return create_codex_native_carousel(
        story="One shared direction.",
        image_paths=[],
        identity_image_paths=identity_paths,
        creative_baseline_path=brief,
        output_root=tmp_path / "output/carousels",
        today=date(2026, 8, 24),
    )


def _candidate(package: Path, slide: int, attempt: int) -> dict[str, object]:
    path = (
        package
        / ".internal/visual-quarantine"
        / f"slide-{slide:02d}"
        / f"attempt-{attempt:02d}"
        / "candidate.json"
    )
    return json.loads(path.read_text(encoding="utf-8"))


def _authored_qa(package: Path, slides: list[int]) -> dict[str, object]:
    prompt_pack = json.loads((package / "prompt-pack.json").read_text(encoding="utf-8"))
    style = prompt_pack["style_profile"]["reference"]["path"]
    context = json.loads((package / "creative-context.json").read_text(encoding="utf-8"))
    role_paths = {
        record["role"]: record["path"]
        for record in context["identity_reference_selection"]["selected_references"]
    }
    copy_by_slide = {
        int(record["slide"]): record["copy"]
        for record in json.loads((package / "slides.json").read_text(encoding="utf-8"))
    }
    return {
        "status": "PASS",
        "inspection": {"method": "codex_view_image", "decoded_pixels_observed": True},
        "selected_slides": slides,
        "slides": [
            {
                "slide": number,
                "reviews": {
                    "instagram_post": {
                        "checks": {
                            "physical_action": {"status": "PASS", "evidence": "The locked physical action is visibly clear."},
                            "relationship_state": {"status": "PASS", "evidence": "Their visible posture proves the relationship beat."},
                            "cinematic_story_frame": passing_cinematic_story_frame(
                                package, number
                            ),
                            "entity_spatial_integrity": passing_entity_spatial_integrity(package, number),
                            "identity_wardrobe_accessories": {
                                "status": "PASS",
                                "evidence": (
                                    "Aachu retains long dense very dark mostly-straight hair with soft bends, "
                                    "large expressive dark round-almond eyes and full mostly-straight brows with a low soft arch, "
                                    "and warm medium-brown skin tone. Zuv retains thick dark curly hair with visible top and side volume, "
                                    "thick dark brows, and warm brown skin tone; their referenced proportions, clothing, and accessories match."
                                ),
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
                                "evidence": "Exact text, brandmark, watercolor style, and native dimensions are visible.",
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
    }


def test_1086x1448_is_raw_preserved_then_lanczos_normalized(tmp_path: Path) -> None:
    package = _package(tmp_path)
    source = _png(tmp_path / "source.png", (1086, 1448), "skyblue")
    source_bytes = source.read_bytes()
    prepare_codex_builtin_image_generation(package, proof_slide=2)

    state = ingest_synthetic_outputs(
        package,
        {"instagram_post": [source]},
        proof_slide=2,
    )

    assert state["status"] == "proof_qa_required"
    assert state["slides"]["2"]["attempts"] == 1
    candidate = _candidate(package, 2, 1)
    raw = candidate["source_evidence"]["instagram_post"]
    normalized = candidate["native_outputs"]["instagram_post"]
    assert raw["width"] == 1086 and raw["height"] == 1448
    assert raw["normalization"] == "lanczos_downsample"
    assert (package / raw["path"]).read_bytes() == source_bytes
    assert normalized["width"] == 1080 and normalized["height"] == 1440
    with Image.open(package / normalized["path"]) as image:
        assert image.size == (1080, 1440)


@pytest.mark.parametrize("select_trigger", [False, True])
def test_receipt_binds_every_applicable_correction_without_other_slide_feedback(tmp_path, select_trigger):
    package = _package(tmp_path)
    events = []
    for slide, wording in [(2, "Keep both hands visible."), (2, "Keep the window visible."),
                           (3, "Keep slide three unchanged.")]:
        events.append(record_creator_feedback(
            package, workspace_root=tmp_path, user_instruction_exact=wording,
            kind="correction", scope="slide", slide_numbers=[slide],
            primary_diagnosis="scene_action", must_preserve=[wording],
        ))
    source = _png(tmp_path / "source.png", (1080, 1440), "skyblue")
    prepare_codex_builtin_image_generation(package, proof_slide=2)
    before = (package / "generation-state.json").read_bytes()
    with pytest.raises(ValueError, match="active feedback"):
        ingest_synthetic_outputs(package, {"instagram_post": [source]},
                                 proof_slide=2, feedback_id=events[2]["feedback_id"])
    assert (package / "generation-state.json").read_bytes() == before
    trigger = events[0]["feedback_id"] if select_trigger else None
    state = ingest_synthetic_outputs(package, {"instagram_post": [source]}, proof_slide=2,
                                     feedback_id=trigger)
    receipt = _candidate(package, 2, 1)["generation_receipt"]
    assert receipt["feedback_ids"] == sorted(event["feedback_id"] for event in events[:2])
    assert receipt["feedback_id"] == trigger
    assert state["slides"]["2"]["attempt_history"][-1]["feedback_ids"] == receipt["feedback_ids"]
    assert "Keep both hands visible." not in json.dumps(receipt)
    candidate = _candidate(package, 2, 1)
    candidate["generation_receipt"]["feedback_ids"] = [events[0]["feedback_id"]]
    with pytest.raises(ValueError, match="receipt does not match"):
        _assert_current_receipt(package, state, candidate)


def test_receipt_preserves_scalar_compatibility_for_one_correction(tmp_path):
    package = _package(tmp_path)
    event = record_creator_feedback(
        package, workspace_root=tmp_path, user_instruction_exact="Keep the shared action.",
        kind="correction", scope="slide", slide_numbers=[2],
        primary_diagnosis="scene_action", must_preserve=["Keep the shared action."],
    )
    prepare_codex_builtin_image_generation(package, proof_slide=2)
    state = ingest_synthetic_outputs(
        package, {"instagram_post": [_png(tmp_path / "source.png", (1080, 1440))]},
        proof_slide=2, feedback_id=event["feedback_id"],
    )
    receipt = state["slides"]["2"]["attempt_history"][-1]
    assert receipt["feedback_id"] == event["feedback_id"]
    assert receipt["feedback_ids"] == [event["feedback_id"]]


def test_ingest_accepts_relative_package_path_without_nesting_root(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    package = _package(tmp_path)
    source = _png(tmp_path / "source.png", (1080, 1440), "skyblue")
    prepare_codex_builtin_image_generation(package, proof_slide=2)
    relative_package = package.relative_to(tmp_path)
    monkeypatch.chdir(tmp_path)

    state = ingest_synthetic_outputs(
        relative_package,
        {"instagram_post": [source]},
        proof_slide=2,
    )

    assert state["status"] == "proof_qa_required"
    assert _candidate(package, 2, 1)["source_evidence"]["instagram_post"][
        "path"
    ].startswith(".internal/visual-quarantine/")
    assert not (package / relative_package.parts[0]).exists()


def test_exact_native_source_is_byte_preserved(tmp_path: Path) -> None:
    package = _package(tmp_path)
    source = _png(tmp_path / "exact.png", (1080, 1440), "skyblue")
    prepare_codex_builtin_image_generation(package, proof_slide=1)
    ingest_synthetic_outputs(package, {"instagram_post": [source]}, proof_slide=1)
    candidate = _candidate(package, 1, 1)
    raw = candidate["source_evidence"]["instagram_post"]
    normalized = candidate["native_outputs"]["instagram_post"]
    assert raw["normalization"] == "native_exact"
    assert (package / normalized["path"]).read_bytes() == source.read_bytes()
    assert normalized["sha256"] == "sha256:" + hashlib.sha256(source.read_bytes()).hexdigest()


def test_wrong_ratio_is_quarantined_counts_attempt_and_caps_at_two(tmp_path: Path) -> None:
    package = _package(tmp_path)
    prepare_codex_builtin_image_generation(package, proof_slide=2)
    first_source = _png(tmp_path / "wrong-1.png", (1086, 1447), "red")
    first = ingest_synthetic_outputs(
        package,
        {"instagram_post": [first_source]},
        proof_slide=2,
    )
    assert first["status"] == "proof_failed"
    assert first["slides"]["2"]["attempts"] == 1
    assert first["next_action"] == "retry_selected_slides"
    failed = _candidate(package, 2, 1)
    raw_path = failed["source_evidence"]["instagram_post"]["path"]
    assert (package / raw_path).read_bytes() == first_source.read_bytes()
    assert failed["native_outputs"] == {}

    prepare_codex_builtin_image_generation(package)
    second = ingest_synthetic_outputs(
        package,
        {"instagram_post": [_png(tmp_path / "wrong-2.png", (1090, 1440), "red")]},
    )
    assert second["status"] == "proof_failed"
    assert second["slides"]["2"]["attempts"] == 2
    assert second["next_action"] == "repair_visual_premise"
    still_blocked = prepare_codex_builtin_image_generation(package)
    assert still_blocked["status"] == "proof_failed"
    assert still_blocked["slides"]["2"]["attempts"] == 2


def test_cosmetic_prompt_edit_keeps_premise_budget_and_archives_first_attempt(
    tmp_path: Path,
) -> None:
    package = _package(tmp_path)
    first_source = _png(tmp_path / "first.png", (1086, 1447), "red")
    prepare_codex_builtin_image_generation(package, proof_slide=2)
    ingest_synthetic_outputs(
        package,
        {"instagram_post": [first_source]},
        proof_slide=2,
    )
    slides_path = package / "slides.json"
    slides = json.loads(slides_path.read_text(encoding="utf-8"))
    first_action = slides[1]["physical_action"]
    slides[1]["camera"]["negative_space"] = "a slightly wider upper-left copy margin"
    slides[1]["wardrobe"] = "Preserve the same clothes with cleaner sleeve edges."
    slides_path.write_text(json.dumps(slides), encoding="utf-8")

    revised = reconcile_package_state(package)

    assert slides[1]["physical_action"] == first_action
    assert revised["slides"]["2"]["attempts"] == 1
    archived_sources = list(
        (package / ".internal/visual-quarantine/superseded").glob(
            "*/.internal/visual-quarantine/slide-02/attempt-01/source/instagram_post.png"
        )
    )
    assert len(archived_sources) == 1
    assert archived_sources[0].read_bytes() == first_source.read_bytes()

    prepare_codex_builtin_image_generation(package)
    second = ingest_synthetic_outputs(
        package,
        {"instagram_post": [_png(tmp_path / "second.png", (1090, 1440), "blue")]},
    )

    assert second["slides"]["2"]["attempts"] == 2
    assert second["next_action"] == "repair_visual_premise"
    assert _candidate(package, 2, 2)["attempt"] == 2
    assert archived_sources[0].read_bytes() == first_source.read_bytes()


def test_physical_premise_change_resets_budget_and_preserves_archive(
    tmp_path: Path,
) -> None:
    package = _package(tmp_path)
    first_source = _png(tmp_path / "first.png", (1086, 1447), "red")
    prepare_codex_builtin_image_generation(package, proof_slide=2)
    ingest_synthetic_outputs(
        package,
        {"instagram_post": [first_source]},
        proof_slide=2,
    )
    slides_path = package / "slides.json"
    slides = json.loads(slides_path.read_text(encoding="utf-8"))
    changed_action = (
        "Aachu closes the shared suitcase while Zuv steadies its opposite edge."
    )
    slides[1]["physical_action"] = changed_action
    slides[1]["hand_map"]["scene_action_binding"] = changed_action
    slides[1]["spatial_topology"]["scene_action_binding"] = changed_action
    slides_path.write_text(json.dumps(slides), encoding="utf-8")

    revised = reconcile_package_state(package)

    assert revised["slides"]["2"]["attempts"] == 0
    archived_sources = list(
        (package / ".internal/visual-quarantine/superseded").glob(
            "*/.internal/visual-quarantine/slide-02/attempt-01/source/instagram_post.png"
        )
    )
    assert len(archived_sources) == 1
    assert archived_sources[0].read_bytes() == first_source.read_bytes()

    prepare_codex_builtin_image_generation(package)
    second_source = _png(tmp_path / "second.png", (1090, 1440), "blue")
    second = ingest_synthetic_outputs(
        package,
        {"instagram_post": [second_source]},
    )

    assert second["slides"]["2"]["attempts"] == 1
    assert _candidate(package, 2, 1)["source_evidence"]["instagram_post"][
        "sha256"
    ] == "sha256:" + hashlib.sha256(second_source.read_bytes()).hexdigest()
    assert archived_sources[0].read_bytes() == first_source.read_bytes()


def test_legacy_v3_without_premise_hash_preserves_budget_once(tmp_path: Path) -> None:
    package = _package(tmp_path)
    state_path = package / "generation-state.json"
    state = read_generation_state(package)
    state["slides"]["2"]["attempts"] = 1
    for record in state["slides"].values():
        record.pop("premise_sha256", None)
    state_path.write_text(json.dumps(state), encoding="utf-8")
    slides_path = package / "slides.json"
    slides = json.loads(slides_path.read_text(encoding="utf-8"))
    slides[1]["physical_action"] = "A genuinely different shared action."
    slides_path.write_text(json.dumps(slides), encoding="utf-8")

    revised = reconcile_package_state(package)

    assert revised["slides"]["2"]["attempts"] == 1
    assert revised["slides"]["2"]["premise_sha256"].startswith("sha256:")


def test_legacy_v3_uses_compiled_scene_to_recognize_real_premise_change(
    tmp_path: Path,
) -> None:
    package = _package(tmp_path)
    prepare_codex_builtin_image_generation(package, proof_slide=2)
    ingest_synthetic_outputs(
        package,
        {"instagram_post": [_png(tmp_path / "first.png", (1086, 1447), "red")]},
        proof_slide=2,
    )
    state_path = package / "generation-state.json"
    state = read_generation_state(package)
    for record in state["slides"].values():
        record.pop("premise_sha256", None)
    state_path.write_text(json.dumps(state), encoding="utf-8")
    slides_path = package / "slides.json"
    slides = json.loads(slides_path.read_text(encoding="utf-8"))
    changed_action = (
        "Aachu closes the shared suitcase while Zuv steadies its opposite edge."
    )
    slides[1]["physical_action"] = changed_action
    slides[1]["hand_map"]["scene_action_binding"] = changed_action
    slides[1]["spatial_topology"]["scene_action_binding"] = changed_action
    slides_path.write_text(json.dumps(slides), encoding="utf-8")

    revised = reconcile_package_state(package)

    assert revised["slides"]["2"]["attempts"] == 0
    assert revised["slides"]["2"]["premise_sha256"].startswith("sha256:")


def test_story_and_square_sources_remain_exact_only() -> None:
    assert source_dimensions_are_acceptable("instagram_post", 1086, 1448) is True
    assert source_dimensions_are_acceptable("instagram_post", 1086, 1447) is False
    assert source_dimensions_are_acceptable("reels_stories", 1080, 1920) is True
    assert source_dimensions_are_acceptable("reels_stories", 1086, 1930) is False
    assert source_dimensions_are_acceptable("square", 1080, 1080) is True
    assert source_dimensions_are_acceptable("square", 1200, 1200) is False


def test_normalized_proof_is_reused_and_all_finals_are_exact_native(tmp_path: Path) -> None:
    package = _package(tmp_path)
    prepare_codex_builtin_image_generation(package, proof_slide=3)
    ingest_synthetic_outputs(
        package,
        {"instagram_post": [_png(tmp_path / "proof-large.png", (1086, 1448), "linen")]},
        proof_slide=3,
    )
    candidate = _candidate(package, 3, 1)
    normalized_hash = candidate["native_outputs"]["instagram_post"]["sha256"]
    (package / "proof-qa.json").write_text(
        json.dumps(_authored_qa(package, [3])), encoding="utf-8"
    )
    review_quarantined_outputs(package)
    approve_proof(
        package,
        approved_by="creator",
        proof_sha256=current_proof_binding_sha256(package),
    )
    handoff = prepare_codex_builtin_image_generation(package)
    assert handoff["selected_slides"] == [1, 2, 4]
    ingest_synthetic_outputs(
        package,
        {
            "instagram_post": [
                _png(tmp_path / "batch" / f"slide-{number}.png", (1080, 1440))
                for number in handoff["selected_slides"]
            ]
        },
    )
    (package / "visual-qa.json").write_text(
        json.dumps(_authored_qa(package, [1, 2, 3, 4])), encoding="utf-8"
    )
    review_quarantined_outputs(package)
    final_state = finalize_codex_builtin_outputs(package)
    assert final_state["status"] == "publish_ready"
    manifest = json.loads((package / "final-images.json").read_text(encoding="utf-8"))
    proof = next(record for record in manifest["slides"] if record["slide"] == 3)
    assert proof["native_outputs"]["instagram_post"]["sha256"] == normalized_hash
    for record in manifest["slides"]:
        binding = record["native_outputs"]["instagram_post"]
        assert (binding["width"], binding["height"]) == (1080, 1440)
        with Image.open(package / binding["path"]) as image:
            assert image.size == (1080, 1440)


def test_raw_source_tamper_revokes_approved_proof(tmp_path: Path) -> None:
    package = _package(tmp_path)
    prepare_codex_builtin_image_generation(package, proof_slide=3)
    ingest_synthetic_outputs(
        package,
        {"instagram_post": [_png(tmp_path / "proof-large.png", (1086, 1448), "linen")]},
        proof_slide=3,
    )
    (package / "proof-qa.json").write_text(
        json.dumps(_authored_qa(package, [3])), encoding="utf-8"
    )
    review_quarantined_outputs(package)
    approve_proof(
        package,
        proof_sha256=current_proof_binding_sha256(package),
    )
    candidate = _candidate(package, 3, 1)
    raw_path = package / candidate["source_evidence"]["instagram_post"]["path"]
    _png(raw_path, (1086, 1448), "red")

    revoked = reconcile_package_state(package)

    assert revoked["status"] == "proof_failed"
    assert revoked["next_action"] == "retry_selected_slides"
    assert not (package / ".internal/approved-final-candidates/slide-03").exists()


def test_raw_source_tamper_retracts_promoted_final_claims(tmp_path: Path) -> None:
    package = _package(tmp_path)
    prepare_codex_builtin_image_generation(package, proof_slide=3)
    ingest_synthetic_outputs(
        package,
        {"instagram_post": [_png(tmp_path / "proof.png", (1080, 1440), "linen")]},
        proof_slide=3,
    )
    (package / "proof-qa.json").write_text(
        json.dumps(_authored_qa(package, [3])), encoding="utf-8"
    )
    review_quarantined_outputs(package)
    approve_proof(package, proof_sha256=current_proof_binding_sha256(package))
    handoff = prepare_codex_builtin_image_generation(package)
    ingest_synthetic_outputs(
        package,
        {
            "instagram_post": [
                    _png(tmp_path / "batch" / f"slide-{number}.png", (1080, 1440), "linen")
                for number in handoff["selected_slides"]
            ]
        },
    )
    (package / "visual-qa.json").write_text(
        json.dumps(_authored_qa(package, [1, 2, 3, 4])), encoding="utf-8"
    )
    review_quarantined_outputs(package)
    finalize_codex_builtin_outputs(package)
    slide_one = json.loads(
        (package / ".internal/approved-final-candidates/slide-01/candidate.json").read_text()
    )
    raw_path = package / slide_one["source_evidence"]["instagram_post"]["path"]
    _png(raw_path, (1080, 1440), "red")

    revoked = reconcile_package_state(package)

    assert revoked["status"] == "final_qa_failed"
    assert not (package / "final").exists()
    assert not (package / "final-images.json").exists()
    assert not (package / "final-audit.json").exists()


def test_external_system_alias_is_allowed_but_source_file_symlink_is_rejected(
    tmp_path: Path,
) -> None:
    package = _package(tmp_path)
    source = _png(tmp_path / "external.png", (1080, 1440), "blue")
    prepare_codex_builtin_image_generation(package, proof_slide=2)
    supplied = source
    source_text = str(source)
    if source_text.startswith("/private/var/"):
        supplied = Path("/var") / source_text.removeprefix("/private/var/")
    elif source_text.startswith("/private/tmp/"):
        supplied = Path("/tmp") / source_text.removeprefix("/private/tmp/")
    ingest_synthetic_outputs(
        package,
        {"instagram_post": [supplied]},
        proof_slide=2,
    )
    assert read_generation_state(package)["slides"]["2"]["attempts"] == 1

    other_root = tmp_path / "symlink-source"
    other_root.mkdir()
    other = _package(other_root)
    prepare_codex_builtin_image_generation(other, proof_slide=2)
    link = tmp_path / "source-link.png"
    link.symlink_to(source)
    with pytest.raises(FileNotFoundError, match="unsafe generated image"):
        ingest_synthetic_outputs(
            other,
            {"instagram_post": [link]},
            proof_slide=2,
        )
    assert read_generation_state(other)["slides"]["2"]["attempts"] == 0


def test_package_system_alias_is_allowed_during_ingest(tmp_path: Path) -> None:
    package = _package(tmp_path)
    source = _png(tmp_path / "package-alias-source.png", (1080, 1440), "blue")
    prepare_codex_builtin_image_generation(package, proof_slide=2)
    supplied_package = package
    package_text = str(package)
    if package_text.startswith("/private/var/"):
        supplied_package = Path("/var") / package_text.removeprefix("/private/var/")
    elif package_text.startswith("/private/tmp/"):
        supplied_package = Path("/tmp") / package_text.removeprefix("/private/tmp/")

    state = ingest_synthetic_outputs(
        supplied_package,
        {"instagram_post": [source]},
        proof_slide=2,
    )

    assert state["status"] == "proof_qa_required"
    assert state["slides"]["2"]["attempts"] == 1


def test_package_internal_image_cannot_be_recycled_as_fresh_imagegen_output(
    tmp_path: Path,
) -> None:
    package = _package(tmp_path)
    prepare_codex_builtin_image_generation(package, proof_slide=2)
    recycled = _png(package / ".internal/recycled.png", (1080, 1440), "blue")

    with pytest.raises(ValueError, match="cannot be recycled"):
        ingest_synthetic_outputs(
            package,
            {"instagram_post": [recycled]},
            proof_slide=2,
        )

    assert read_generation_state(package)["status"] == "handoff_ready"
    assert read_generation_state(package)["slides"]["2"]["attempts"] == 0


def test_cleanup_refuses_symlinked_parent_without_deleting_external_target(
    tmp_path: Path,
) -> None:
    package = _package(tmp_path)
    prepare_codex_builtin_image_generation(package, proof_slide=2)
    external = tmp_path / "external-quarantine"
    external.mkdir()
    sentinel = external / "sentinel.txt"
    sentinel.write_text("must survive", encoding="utf-8")
    (package / ".internal/visual-quarantine").symlink_to(external, target_is_directory=True)

    with pytest.raises(ValueError, match="symlinked package directory"):
        ingest_synthetic_outputs(
            package,
            {"instagram_post": [_png(tmp_path / "fresh.png", (1080, 1440), "blue")]},
            proof_slide=2,
        )

    assert sentinel.read_text(encoding="utf-8") == "must survive"


def test_candidate_source_evidence_parent_symlink_revokes_approval(
    tmp_path: Path,
) -> None:
    package = _package(tmp_path)
    prepare_codex_builtin_image_generation(package, proof_slide=3)
    ingest_synthetic_outputs(
        package,
        {"instagram_post": [_png(tmp_path / "proof.png", (1080, 1440), "linen")]},
        proof_slide=3,
    )
    (package / "proof-qa.json").write_text(
        json.dumps(_authored_qa(package, [3])), encoding="utf-8"
    )
    review_quarantined_outputs(package)
    approve_proof(package, proof_sha256=current_proof_binding_sha256(package))
    current = _candidate(package, 3, 1)
    original_raw = package / current["source_evidence"]["instagram_post"]["path"]
    external = tmp_path / "external-evidence"
    external.mkdir()
    external_raw = external / "raw.png"
    external_raw.write_bytes(original_raw.read_bytes())
    link_parent = package / ".internal/evidence-link"
    link_parent.symlink_to(external, target_is_directory=True)
    current["source_evidence"]["instagram_post"]["path"] = (
        ".internal/evidence-link/raw.png"
    )
    candidate_path = (
        package / ".internal/visual-quarantine/slide-03/attempt-01/candidate.json"
    )
    candidate_path.write_text(json.dumps(current), encoding="utf-8")

    revoked = reconcile_package_state(package)

    assert revoked["status"] == "proof_failed"
    assert external_raw.is_file()
