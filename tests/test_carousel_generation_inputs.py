from __future__ import annotations

import json
from datetime import date
from pathlib import Path

from PIL import Image
import pytest

import pipeline.stages.carousel_generation_inputs as generation_inputs
from pipeline.stages.carousel_generation_inputs import (
    build_generation_inputs,
    build_shared_reference_bindings,
    canonical_fingerprint,
)
from pipeline.stages.carousel_generation_state import read_generation_state, write_v3_state
from pipeline.stages.codex_builtin_image_generation import (
    prepare_codex_builtin_image_generation,
    reconcile_package_state,
)
from pipeline.stages.codex_native_carousel import create_codex_native_carousel


def _png(path: Path, color: str = "tan") -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    Image.new("RGB", (40, 40), color).save(path)
    return path


def _cinematic_slide(number: int, *, copy_prefix: str = "Exact copy") -> dict[str, object]:
    is_final = number == 4
    return {
        "role": "payoff" if is_final else f"story_beat_{number}",
        "copy": f"{copy_prefix} {number}",
        "physical_action": f"Aachu and Zuv move shared object {number} toward the window together.",
        "relationship_state": f"Their shared effort visibly changes into coordinated trust at beat {number}.",
        "camera": {
            "shot_size": ("close payoff detail" if is_final else f"medium-wide action frame {number}"),
            "position": f"table-height three-quarter position beside active object {number}",
            "negative_space": f"quiet upper-left wall above action beat {number}",
        },
        "focal_hierarchy": f"Their active hands read first, shared object {number} second, and upper copy stays clear.",
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
        "wardrobe": "Aachu in blue, Zuv in cream.",
    }


def _identity_bundle(tmp_path: Path) -> list[Path]:
    return [
        _png(tmp_path / "identity/aachu/aachu.png", "red"),
        _png(tmp_path / "identity/zuv/zuv.png", "blue"),
        _png(tmp_path / "identity/together/face.png", "green"),
        _png(tmp_path / "identity/together/body.png", "purple"),
    ]


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
    return create_codex_native_carousel(
        story="One difficult shared direction.",
        image_paths=[_png(tmp_path / "story.png", "skyblue")],
        identity_image_paths=_identity_bundle(tmp_path),
        creative_baseline_path=brief,
        output_root=tmp_path / "output/carousels",
        today=date(2026, 8, 24),
    )


def _package_with_actual_reference_bundle(tmp_path: Path) -> Path:
    brief = tmp_path / "bundle-brief.json"
    brief.write_text(
        json.dumps(
            {
                "slides": [
                    _cinematic_slide(number, copy_prefix="Reference-bound copy")
                    for number in range(1, 5)
                ]
            }
        ),
        encoding="utf-8",
    )
    identity_paths = _identity_bundle(tmp_path)
    return create_codex_native_carousel(
        story="One difficult shared direction.",
        image_paths=[_png(tmp_path / "bundle-story.png", "skyblue")],
        identity_image_paths=identity_paths,
        creative_baseline_path=brief,
        output_root=tmp_path / "bundle-output/carousels",
        today=date(2026, 8, 24),
    )


def _mark_work_in_progress(package: Path) -> dict[str, object]:
    state = read_generation_state(package)
    state["proof_slide"] = 1
    for number, record in state["slides"].items():
        record["status"] = "approved_candidate"
        record["attempts"] = 1
        root = package / ".internal/approved-final-candidates" / f"slide-{int(number):02d}"
        root.mkdir(parents=True, exist_ok=True)
        (root / "sentinel.txt").write_text(number, encoding="utf-8")
    return write_v3_state(package, state)


def test_json_formatting_and_key_order_do_not_change_fingerprints(tmp_path: Path) -> None:
    package = _package(tmp_path)
    before = build_generation_inputs(package)
    for filename in ("slides.json", "prompt-pack.json"):
        path = package / filename
        payload = json.loads(path.read_text(encoding="utf-8"))
        path.write_text(
            json.dumps(payload, sort_keys=True, separators=(",", ":")),
            encoding="utf-8",
        )

    assert build_generation_inputs(package) == before
    assert reconcile_package_state(package) == read_generation_state(package)


def test_nonproof_slide_change_invalidates_only_that_slide(tmp_path: Path) -> None:
    package = _package(tmp_path)
    before = _mark_work_in_progress(package)
    slides = json.loads((package / "slides.json").read_text(encoding="utf-8"))
    slides[1]["copy"] = "A corrected exact copy for slide two."
    (package / "slides.json").write_text(json.dumps(slides), encoding="utf-8")

    after = reconcile_package_state(package)

    assert after["slides"]["1"]["attempts"] == 1
    assert after["slides"]["1"]["input_sha256"] == before["slides"]["1"]["input_sha256"]
    assert after["slides"]["2"]["attempts"] == 1
    assert after["slides"]["2"]["status"] == "draft"
    assert after["slides"]["3"]["attempts"] == 1
    assert (package / ".internal/approved-final-candidates/slide-01/sentinel.txt").is_file()
    assert not (package / ".internal/approved-final-candidates/slide-02").exists()
    assert (package / ".internal/approved-final-candidates/slide-03/sentinel.txt").is_file()


def test_one_slide_cinematic_change_invalidates_only_that_slide(tmp_path: Path) -> None:
    package = _package(tmp_path)
    before = build_generation_inputs(package)
    slides_path = package / "slides.json"
    slides = json.loads(slides_path.read_text(encoding="utf-8"))
    slides[1]["visual_richness"]["after_frame"] = (
        "They set the shared object down and finally release their shoulders together."
    )
    slides_path.write_text(json.dumps(slides), encoding="utf-8")

    after = build_generation_inputs(package)

    assert after["slides"]["2"]["source_sha256"] != before["slides"]["2"]["source_sha256"]
    assert after["slides"]["2"]["prompt_sha256"] != before["slides"]["2"]["prompt_sha256"]
    assert after["slides"]["1"] == before["slides"]["1"]
    assert after["slides"]["3"] == before["slides"]["3"]
    assert after["slides"]["4"] == before["slides"]["4"]


def test_slide_visual_corrections_change_compiled_prompt_not_stale_prompt_pack(
    tmp_path: Path,
) -> None:
    package = _package_with_actual_reference_bundle(tmp_path)
    before = build_generation_inputs(package)
    slides_path = package / "slides.json"
    slides = json.loads(slides_path.read_text(encoding="utf-8"))
    slides[0].update(
        {
            "physical_action": "Aachu places one brass key in Zuv's open left palm.",
            "camera": {
                "shot_size": "tight doorway action frame",
                "position": "threshold-height view with the key centered between their hands",
                "negative_space": "quiet upper-left wall above their joined hands",
            },
            "focal_hierarchy": "The brass key reads first, their eye contact second, and upper-left copy stays clear.",
            "wardrobe": "Aachu black overshirt; Zuv white zip jacket",
            "relationship_state": "Their careful handoff makes trust visible after changing direction together.",
            "negative_prompt": "no spare key, label, or printed logo",
        }
    )
    slides_path.write_text(json.dumps(slides), encoding="utf-8")

    after = build_generation_inputs(package)

    assert after["slides"]["1"]["source_sha256"] != before["slides"]["1"]["source_sha256"]
    assert after["slides"]["1"]["prompt_sha256"] != before["slides"]["1"]["prompt_sha256"]
    assert after["slides"]["2"] == before["slides"]["2"]

    prepare_codex_builtin_image_generation(package, proof_slide=1)
    compiled = (
        package / ".internal/compiled-prompts/instagram-post/slide-01.prompt.txt"
    ).read_text(encoding="utf-8")
    for fragment in (
        "places one brass key in Zuv's open left palm",
        "key centered between their hands",
        "Aachu black overshirt",
        "makes trust visible after changing direction together",
        "no spare key, label, or printed logo",
    ):
        assert fragment in compiled


def test_feedback_is_slide_local_and_no_feedback_prompt_bytes_stay_stable(
    tmp_path: Path,
) -> None:
    package = _package_with_actual_reference_bundle(tmp_path)
    before = build_generation_inputs(package)
    assert build_generation_inputs(package) == before
    (package / "creator-correction.json").write_text(
        json.dumps(
            {
                "schema_version": "creator-correction/v2",
                "feedback": [
                    {
                        "feedback_id": "fb-slide-one",
                        "user_instruction_exact": "Raw creator words stay in memory only.",
                        "kind": "correction",
                        "scope": "slide",
                        "slides": [1],
                        "must_change": ["move the shared object with both hands visible"],
                        "must_preserve": ["the exact slide copy"],
                        "generation_effect": "slide_local",
                        "historical_only": False,
                    }
                ],
            }
        ),
        encoding="utf-8",
    )

    after = build_generation_inputs(package)

    assert after["slides"]["1"]["prompt_sha256"] != before["slides"]["1"]["prompt_sha256"]
    assert after["slides"]["2"] == before["slides"]["2"]
    prepare_codex_builtin_image_generation(package, proof_slide=1)
    prompt = (
        package / ".internal/compiled-prompts/instagram-post/slide-01.prompt.txt"
    ).read_text(encoding="utf-8")
    assert "ACTIVE CREATOR FEEDBACK — THIS SLIDE:" in prompt
    assert "move the shared object with both hands visible" in prompt
    assert "the exact slide copy" in prompt
    assert "Raw creator words stay in memory only." not in prompt


def test_proof_slide_change_revokes_embedded_approval_only_for_proof(tmp_path: Path) -> None:
    package = _package(tmp_path)
    _mark_work_in_progress(package)
    (package / "proof-qa.json").write_text(
        json.dumps({"creator_approval": {"approved": True}}), encoding="utf-8"
    )
    slides = json.loads((package / "slides.json").read_text(encoding="utf-8"))
    changed_action = "They visibly turn one shared map around together."
    slides[0]["physical_action"] = changed_action
    slides[0]["hand_map"]["scene_action_binding"] = changed_action
    slides[0]["spatial_topology"]["scene_action_binding"] = changed_action
    (package / "slides.json").write_text(json.dumps(slides), encoding="utf-8")

    after = reconcile_package_state(package)

    assert after["slides"]["1"]["attempts"] == 0
    assert after["slides"]["2"]["attempts"] == 1
    assert not (package / "proof-qa.json").exists()


def test_shared_identity_byte_change_invalidates_complete_deck(tmp_path: Path) -> None:
    package = _package(tmp_path)
    _mark_work_in_progress(package)
    prompt_pack = json.loads((package / "prompt-pack.json").read_text(encoding="utf-8"))
    identity = package / prompt_pack["identity_reference_images"][0]
    _png(identity, "black")

    after = reconcile_package_state(package)

    assert all(record["attempts"] == 1 for record in after["slides"].values())
    assert not (package / ".internal/approved-final-candidates").exists()
    assert "all slide candidates" in after["reason"]


def test_brand_contract_change_invalidates_complete_deck(tmp_path: Path) -> None:
    package = _package_with_actual_reference_bundle(tmp_path)
    _mark_work_in_progress(package)
    prompt_path = package / "prompt-pack.json"
    prompt_pack = json.loads(prompt_path.read_text(encoding="utf-8"))
    prompt_pack["brandmark"] = "@a.storyof.two.changed"
    prompt_path.write_text(json.dumps(prompt_pack), encoding="utf-8")

    after = reconcile_package_state(package)

    assert all(record["attempts"] == 1 for record in after["slides"].values())
    assert "all slide candidates" in after["reason"]


def test_compiler_version_change_invalidates_complete_deck(
    tmp_path: Path,
    monkeypatch,
) -> None:
    package = _package_with_actual_reference_bundle(tmp_path)
    _mark_work_in_progress(package)
    monkeypatch.setattr(
        generation_inputs,
        "PROMPT_COMPILER_VERSION",
        "carousel-prompt-compiler/v-next",
    )

    after = reconcile_package_state(package)

    assert all(record["attempts"] == 1 for record in after["slides"].values())
    assert "all slide candidates" in after["reason"]


def test_actual_prompt_pack_references_are_hashed_and_byte_drift_is_global(
    tmp_path: Path,
) -> None:
    package = _package_with_actual_reference_bundle(tmp_path)
    prompt_pack = json.loads((package / "prompt-pack.json").read_text(encoding="utf-8"))
    assert len(prompt_pack["identity_reference_images"]) == 4
    assert prompt_pack["schema_version"] == "carousel-prompt-pack/v3"
    assert "slides" not in prompt_pack
    assert prompt_pack["style_profile"]["reference"]["attachment_count"] == 1
    slides = json.loads((package / "slides.json").read_text(encoding="utf-8"))
    assert all(
        not ({"visual", "scene", "composition", "pose", "background"} & set(slide))
        for slide in slides
    )
    assert all("scene_action_binding" not in slide["visual_richness"] for slide in slides)

    before_inputs = build_generation_inputs(package)
    empty_list_sha256 = canonical_fingerprint([])
    assert all(
        record["references_sha256"] != empty_list_sha256
        for record in before_inputs["slides"].values()
    )

    _mark_work_in_progress(package)
    (package / "proof-qa.json").write_text(
        json.dumps({"creator_approval": {"approved": True}}),
        encoding="utf-8",
    )
    (package / "final").mkdir()
    _png(package / "final/slide-01.png")
    for filename in ("final-images.json", "visual-qa.json", "final-audit.json"):
        (package / filename).write_text("{}", encoding="utf-8")

    identity = package / prompt_pack["identity_reference_images"][0]
    _png(identity, "black")
    after = reconcile_package_state(package)

    assert all(record["attempts"] == 1 for record in after["slides"].values())
    assert all(
        after["slides"][number]["references_sha256"]
        != before_inputs["slides"][number]["references_sha256"]
        for number in after["slides"]
    )
    assert "all slide candidates" in after["reason"]
    assert not (package / "proof-qa.json").exists()
    assert not (package / ".internal/approved-final-candidates").exists()
    assert not (package / "final").exists()
    assert not (package / "final-images.json").exists()
    assert not (package / "visual-qa.json").exists()
    assert not (package / "final-audit.json").exists()


def test_shared_identity_path_and_role_are_semantic_but_order_is_not(
    tmp_path: Path,
) -> None:
    package = _package_with_actual_reference_bundle(tmp_path)
    prompt_path = package / "prompt-pack.json"
    prompt_pack = json.loads(prompt_path.read_text(encoding="utf-8"))
    before = build_generation_inputs(package)

    prompt_pack["identity_reference_images"].reverse()
    prompt_path.write_text(json.dumps(prompt_pack), encoding="utf-8")
    assert build_generation_inputs(package) == before

    context_path = package / "creative-context.json"
    context = json.loads(context_path.read_text(encoding="utf-8"))
    context["identity_reference_selection"]["selected_references"][0]["role"] = (
        "changed identity role"
    )
    context_path.write_text(json.dumps(context), encoding="utf-8")
    role_changed = build_generation_inputs(package)
    assert all(
        role_changed["slides"][number]["references_sha256"]
        != before["slides"][number]["references_sha256"]
        for number in before["slides"]
    )

    replacement = package / ".internal/references/identity/replacement.png"
    _png(replacement, "white")
    prompt_pack["identity_reference_images"][0] = replacement.relative_to(package).as_posix()
    prompt_path.write_text(json.dumps(prompt_pack), encoding="utf-8")
    path_changed = build_generation_inputs(package)
    assert all(
        path_changed["slides"][number]["references_sha256"]
        != role_changed["slides"][number]["references_sha256"]
        for number in before["slides"]
    )


def test_reference_paths_must_resolve_inside_package(tmp_path: Path) -> None:
    package = _package_with_actual_reference_bundle(tmp_path)
    outside = _png(tmp_path / "outside.png", "black")
    prompt_path = package / "prompt-pack.json"
    prompt_pack = json.loads(prompt_path.read_text(encoding="utf-8"))
    prompt_pack["style_profile"]["reference"]["path"] = str(outside)
    prompt_path.write_text(json.dumps(prompt_pack), encoding="utf-8")

    try:
        build_generation_inputs(package)
    except ValueError as exc:
        assert "outside the carousel package" in str(exc)
    else:
        raise AssertionError("outside reference path was accepted")


def test_style_profile_metadata_drift_fails_closed_for_the_whole_package(
    tmp_path: Path,
) -> None:
    package = _package_with_actual_reference_bundle(tmp_path)
    prompt_path = package / "prompt-pack.json"
    prompt_pack = json.loads(prompt_path.read_text(encoding="utf-8"))
    prompt_pack["style_profile"]["generation_prompt"] += " stale mutation"
    prompt_path.write_text(json.dumps(prompt_pack), encoding="utf-8")

    with pytest.raises(ValueError, match="style_profile_stale: generation_prompt"):
        build_generation_inputs(package)


def test_style_profile_reference_byte_drift_fails_closed(tmp_path: Path) -> None:
    package = _package_with_actual_reference_bundle(tmp_path)
    prompt_pack = json.loads((package / "prompt-pack.json").read_text(encoding="utf-8"))
    style_path = package / prompt_pack["style_profile"]["reference"]["path"]
    _png(style_path, "black")

    with pytest.raises(ValueError, match="style_profile_stale: reference bytes"):
        build_generation_inputs(package)


def test_style_profile_reference_path_drift_fails_closed_even_for_same_bytes(
    tmp_path: Path,
) -> None:
    package = _package_with_actual_reference_bundle(tmp_path)
    prompt_path = package / "prompt-pack.json"
    prompt_pack = json.loads(prompt_path.read_text(encoding="utf-8"))
    canonical = package / prompt_pack["style_profile"]["reference"]["path"]
    alternate = canonical.with_name("same-style-bytes.png")
    alternate.write_bytes(canonical.read_bytes())
    prompt_pack["style_profile"]["reference"]["path"] = alternate.relative_to(
        package
    ).as_posix()
    prompt_path.write_text(json.dumps(prompt_pack), encoding="utf-8")

    with pytest.raises(ValueError, match="style_profile_stale: reference_path"):
        build_generation_inputs(package)


def test_prompt_pack_requires_exactly_four_distinct_identity_photographs(
    tmp_path: Path,
) -> None:
    package = _package_with_actual_reference_bundle(tmp_path)
    prompt_path = package / "prompt-pack.json"
    prompt_pack = json.loads(prompt_path.read_text(encoding="utf-8"))
    prompt_pack["identity_reference_images"] = prompt_pack["identity_reference_images"][:3]
    prompt_path.write_text(json.dumps(prompt_pack), encoding="utf-8")

    with pytest.raises(ValueError, match="exactly four identity photographs"):
        build_shared_reference_bindings(package)

    prompt_pack = json.loads(prompt_path.read_text(encoding="utf-8"))
    prompt_pack["identity_reference_images"] = [
        prompt_pack["identity_reference_images"][0],
        prompt_pack["identity_reference_images"][0],
        *prompt_pack["identity_reference_images"][1:],
    ]
    prompt_path.write_text(json.dumps(prompt_pack), encoding="utf-8")

    with pytest.raises(ValueError, match="four distinct files"):
        build_shared_reference_bindings(package)


def test_v2_prompt_pack_is_read_only_for_generation(tmp_path: Path) -> None:
    package = _package_with_actual_reference_bundle(tmp_path)
    prompt_path = package / "prompt-pack.json"
    payload = json.loads(prompt_path.read_text(encoding="utf-8"))
    payload["schema_version"] = "carousel-prompt-pack/v2"
    prompt_path.write_text(json.dumps(payload), encoding="utf-8")

    with pytest.raises(ValueError, match="historical and read-only"):
        build_generation_inputs(package)


def test_v3_prompt_pack_rejects_retired_slide_prompt_aliases(tmp_path: Path) -> None:
    package = _package_with_actual_reference_bundle(tmp_path)
    prompt_path = package / "prompt-pack.json"
    payload = json.loads(prompt_path.read_text(encoding="utf-8"))
    payload["slides"] = [{"slide": 1, "prompt": "stale duplicate prose"}]
    prompt_path.write_text(json.dumps(payload), encoding="utf-8")

    with pytest.raises(ValueError, match="retired duplicate fields: slides"):
        build_generation_inputs(package)


def test_story_reference_drift_remains_slide_local(tmp_path: Path) -> None:
    package = _package_with_actual_reference_bundle(tmp_path)
    slides_path = package / "slides.json"
    slides = json.loads(slides_path.read_text(encoding="utf-8"))
    local_story_paths: list[Path] = []
    for slide in slides:
        number = int(slide["slide"])
        local = _png(
            package / f".internal/references/story/slide-{number:02d}.png",
            ("red", "blue", "green", "orange")[number - 1],
        )
        local_story_paths.append(local)
        slide["source_images"] = [local.relative_to(package).as_posix()]
    slides_path.write_text(json.dumps(slides), encoding="utf-8")
    reconcile_package_state(package)
    before = _mark_work_in_progress(package)

    _png(local_story_paths[1], "black")
    after = reconcile_package_state(package)

    assert after["slides"]["1"]["attempts"] == 1
    assert after["slides"]["2"]["attempts"] == 1
    assert after["slides"]["3"]["attempts"] == 1
    assert after["slides"]["4"]["attempts"] == 1
    assert (
        after["slides"]["1"]["references_sha256"]
        == before["slides"]["1"]["references_sha256"]
    )
    assert (
        after["slides"]["2"]["references_sha256"]
        != before["slides"]["2"]["references_sha256"]
    )
    assert "only slides: 2" in after["reason"]


def test_any_semantic_drift_retracts_public_final_claims(tmp_path: Path) -> None:
    package = _package(tmp_path)
    _mark_work_in_progress(package)
    (package / "final").mkdir()
    _png(package / "final/slide-01.png")
    for filename in ("final-images.json", "visual-qa.json", "final-audit.json"):
        (package / filename).write_text("{}", encoding="utf-8")
    slides = json.loads((package / "slides.json").read_text(encoding="utf-8"))
    slides[2]["camera"]["position"] = "Overhead, with their joined hands centered."
    (package / "slides.json").write_text(json.dumps(slides), encoding="utf-8")

    reconcile_package_state(package)

    assert not (package / "final").exists()
    assert not (package / "final-images.json").exists()
    assert not (package / "visual-qa.json").exists()
    archives = list(
        (package / ".internal/visual-quarantine/superseded").glob("*/archive.json")
    )
    assert len(archives) == 1
    archive = json.loads(archives[0].read_text(encoding="utf-8"))
    originals = {item["original_path"] for item in archive["files"]}
    assert "final/slide-01.png" in originals
    assert ".internal/approved-final-candidates/slide-03/sentinel.txt" in originals
    archive_root = archives[0].parent
    assert (archive_root / "final/slide-01.png").is_file()
    assert not (package / "final-audit.json").exists()
