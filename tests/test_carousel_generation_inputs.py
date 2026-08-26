from __future__ import annotations

import json
from datetime import date
from pathlib import Path

from PIL import Image

import pipeline.stages.carousel_generation_inputs as generation_inputs
from pipeline.stages.carousel_generation_inputs import (
    build_generation_inputs,
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


def _package(tmp_path: Path) -> Path:
    brief = tmp_path / "brief.json"
    brief.write_text(
        json.dumps(
            {
                "slides": [
                    {
                        "copy": f"Exact copy {number}",
                        "physical_action": f"They move shared object {number} together.",
                        "wardrobe": "Aachu in blue, Zuv in cream.",
                    }
                    for number in range(1, 5)
                ]
            }
        ),
        encoding="utf-8",
    )
    return create_codex_native_carousel(
        story="One difficult shared direction.",
        image_paths=[_png(tmp_path / "story.png", "skyblue")],
        identity_image_paths=[_png(tmp_path / "identity.png")],
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
                    {
                        "copy": f"Reference-bound copy {number}",
                        "physical_action": f"They move shared object {number} together.",
                    }
                    for number in range(1, 5)
                ]
            }
        ),
        encoding="utf-8",
    )
    identity_paths = [
        _png(tmp_path / "identity/aachu/aachu.png", "red"),
        _png(tmp_path / "identity/zuv/zuv.png", "blue"),
        _png(tmp_path / "identity/together/face.png", "green"),
        _png(tmp_path / "identity/together/body.png", "purple"),
    ]
    return create_codex_native_carousel(
        story="One difficult shared direction.",
        image_paths=[_png(tmp_path / "bundle-story.png", "skyblue")],
        identity_image_paths=identity_paths,
        style_reference_paths=[_png(tmp_path / "style-board.png", "orange")],
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
    assert after["slides"]["2"]["attempts"] == 0
    assert after["slides"]["2"]["status"] == "draft"
    assert after["slides"]["3"]["attempts"] == 1
    assert (package / ".internal/approved-final-candidates/slide-01/sentinel.txt").is_file()
    assert not (package / ".internal/approved-final-candidates/slide-02").exists()
    assert (package / ".internal/approved-final-candidates/slide-03/sentinel.txt").is_file()


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
            "visual": "Aachu places one brass key in Zuv's open left palm.",
            "composition": "tight doorway frame with the key centered between their hands",
            "wardrobe": "Aachu black overshirt; Zuv white zip jacket",
            "relationship_state": "trust after changing direction together",
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
        "trust after changing direction together",
        "no spare key, label, or printed logo",
    ):
        assert fragment in compiled


def test_proof_slide_change_revokes_embedded_approval_only_for_proof(tmp_path: Path) -> None:
    package = _package(tmp_path)
    _mark_work_in_progress(package)
    (package / "proof-qa.json").write_text(
        json.dumps({"creator_approval": {"approved": True}}), encoding="utf-8"
    )
    slides = json.loads((package / "slides.json").read_text(encoding="utf-8"))
    slides[0]["physical_action"] = "They visibly turn one shared map around together."
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
    _png(identity, "red")

    after = reconcile_package_state(package)

    assert all(record["attempts"] == 0 for record in after["slides"].values())
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

    assert all(record["attempts"] == 0 for record in after["slides"].values())
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

    assert all(record["attempts"] == 0 for record in after["slides"].values())
    assert "all slide candidates" in after["reason"]


def test_actual_prompt_pack_references_are_hashed_and_byte_drift_is_global(
    tmp_path: Path,
) -> None:
    package = _package_with_actual_reference_bundle(tmp_path)
    prompt_pack = json.loads((package / "prompt-pack.json").read_text(encoding="utf-8"))
    assert len(prompt_pack["identity_reference_images"]) == 4
    assert len(prompt_pack["style_reference_images"]) == 1

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

    assert all(record["attempts"] == 0 for record in after["slides"].values())
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


def test_shared_reference_path_and_role_are_semantic_but_order_is_not(
    tmp_path: Path,
) -> None:
    package = _package_with_actual_reference_bundle(tmp_path)
    prompt_path = package / "prompt-pack.json"
    prompt_pack = json.loads(prompt_path.read_text(encoding="utf-8"))
    before = build_generation_inputs(package)

    prompt_pack["identity_reference_images"].reverse()
    prompt_path.write_text(json.dumps(prompt_pack), encoding="utf-8")
    assert build_generation_inputs(package) == before

    identity = prompt_pack["identity_reference_images"].pop()
    prompt_pack["style_reference_images"].append(identity)
    prompt_path.write_text(json.dumps(prompt_pack), encoding="utf-8")
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
    prompt_pack["style_reference_images"] = [str(outside)]
    prompt_path.write_text(json.dumps(prompt_pack), encoding="utf-8")

    try:
        build_generation_inputs(package)
    except ValueError as exc:
        assert "outside the carousel package" in str(exc)
    else:
        raise AssertionError("outside reference path was accepted")


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
    assert after["slides"]["2"]["attempts"] == 0
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
    slides[2]["camera"] = "Overhead, with their joined hands centered."
    (package / "slides.json").write_text(json.dumps(slides), encoding="utf-8")

    reconcile_package_state(package)

    assert not (package / "final").exists()
    assert not (package / "final-images.json").exists()
    assert not (package / "visual-qa.json").exists()
    assert not (package / "final-audit.json").exists()
