"""Synthetic public orchestration test; this is not a claim of vision quality."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Any

from PIL import Image
import pytest

from pipeline.stages.carousel_generation_inputs import build_generation_inputs
from pipeline.stages.codex_builtin_image_generation import reconcile_package_state
from tests.helpers.carousel_qa import (
    cinematic_slide_fields,
    passing_cinematic_story_frame,
    passing_entity_spatial_integrity,
    synthetic_route_sequence_review,
    synthetic_route_story_plan,
)


ROOT = Path(__file__).resolve().parents[1]
CAROUSEL = ROOT / "scripts/carousel.py"
DOCTOR = ROOT / "scripts/carousel_doctor.py"


def _run(*args: str, expected: int = 0) -> dict[str, Any]:
    result = subprocess.run(
        [sys.executable, str(CAROUSEL), *args],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
        timeout=30,
    )
    assert result.returncode == expected, result.stdout + result.stderr
    payload = json.loads(result.stdout)
    assert payload["schema_version"] == "carousel-cli/v1"
    assert set(
        (
            "package_dir",
            "state",
            "next_action",
            "selected_slides",
            "selected_formats",
        )
    ).issubset(payload)
    return payload


def _write_png(path: Path, size: tuple[int, int], color: str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    Image.new("RGB", size, color).save(path, optimize=True)
    return path


def _write_brief(path: Path) -> Path:
    slides = [
        {
            "copy": "I knew your hand.",
            "physical_action": "Aachu places one brass house key in Zuv's open palm.",
            "relationship_state": "certain of each other",
        },
        {
            "copy": "Life gave us two directions.",
            "physical_action": "They stand over one moving box and point toward different doorways.",
            "relationship_state": "uncertain about direction",
        },
        {
            "copy": "Love did not choose the road.",
            "physical_action": "Aachu and Zuv pull one folded paper map gently toward opposite sides of a table.",
            "relationship_state": "connected inside disagreement",
        },
        {
            "copy": "",
            "copy_mode": "wordless",
            "physical_action": "They rotate the map and trace one route with adjacent index fingers.",
            "relationship_state": "committed and learning",
        },
    ]
    path.write_text(
        json.dumps(
            {
                "story_plan": synthetic_route_story_plan(),
                "slides": [
                    {
                        **cinematic_slide_fields(index, len(slides)),
                        "copy_mode": "text",
                        "beat_delta": (
                            "The offered key establishes their shared-home commitment.",
                            "Their pointing arms reveal two different immediate destinations.",
                            "Opposing grips make the map a physical disagreement.",
                            "Adjacent fingers trace the same route without further dialogue.",
                        )[index - 1],
                        "copy_image_relation": {
                            "kind": "wordless" if index == 4 else "completion",
                            "proof": slide["physical_action"],
                        },
                        **slide,
                    }
                    for index, slide in enumerate(slides, start=1)
                ]
            }
        ),
        encoding="utf-8",
    )
    return path


def _authored_qa(package: Path, selected: list[int]) -> dict[str, Any]:
    slides_payload = json.loads((package / "slides.json").read_text(encoding="utf-8"))
    slides = slides_payload["slides"] if isinstance(slides_payload, dict) else slides_payload
    copies = {int(record["slide"]): str(record["copy"]) for record in slides}
    prompt_pack = json.loads((package / "prompt-pack.json").read_text(encoding="utf-8"))
    refs = [str(value) for value in prompt_pack["identity_reference_images"]]
    style_refs = [str(prompt_pack["style_profile"]["reference"]["path"])]
    assert len(refs) == 4
    assert len(style_refs) == 1

    records: list[dict[str, Any]] = []
    for slide in selected:
        exact_copy = copies[slide]
        checks = {
            "physical_action": {
                "status": "PASS",
                "evidence": "The intended hand and shared-object action is plainly visible.",
            },
            "relationship_state": {
                "status": "PASS",
                "evidence": "Their gaze, distance, and object use show the intended relationship state.",
            },
            "cinematic_story_frame": passing_cinematic_story_frame(package, slide),
            "entity_spatial_integrity": passing_entity_spatial_integrity(package, slide),
            "identity_wardrobe_accessories": {
                "status": "PASS",
                "evidence": (
                    "Aachu retains long dense very dark mostly-straight hair with soft bends, "
                    "large expressive dark round-almond eyes and full mostly-straight brows with a low soft arch, "
                    "and warm medium-brown skin tone. Zuv retains thick dark curly hair with visible top and side volume, "
                    "thick dark brows, and warm brown skin tone; their referenced proportions, clothing, and accessories match."
                ),
                "references": {
                    "aachu": [refs[0]],
                    "zuv": [refs[1]],
                    "together": refs[2:],
                },
            },
            "text_brandmark_style_dimensions": {
                "status": "PASS",
                "evidence": (
                    "No story text is present; the tiny top-right brandmark remains on the native watercolor frame."
                    if not exact_copy else
                    "Exact copy and the tiny top-right brandmark are visible on the native watercolor frame."
                ),
                "expected_text": exact_copy,
                "observed_text": exact_copy,
                "unexpected_visible_text": [],
                "observed_brandmark": "@a.storyof.two",
                "style_references": style_refs,
            },
        }
        records.append(
            {
                "slide": slide,
                "reviews": {"instagram_post": {"checks": checks}},
            }
        )
    result = {
        "status": "PASS",
        "inspection": {
            "method": "codex_view_image",
            "decoded_pixels_observed": True,
        },
        "selected_slides": selected,
        "slides": records,
    }
    if selected == [1, 2, 3, 4]:
        result["sequence_review"] = synthetic_route_sequence_review(package)
    return result


def _write_qa(path: Path, qa: dict[str, Any]) -> Path:
    path.write_text(json.dumps(qa), encoding="utf-8")
    return path


@pytest.mark.parametrize("tamper", ["prompt_sha256", "returned_sources", "qa_sha256", "story_plan"])
def test_public_cli_lifecycle_promotes_only_after_bound_final_qa(tmp_path: Path, tamper: str) -> None:
    aachu = _write_png(tmp_path / "identity/aachu/a.png", (32, 32), "salmon")
    zuv = _write_png(tmp_path / "identity/zuv/z.png", (32, 32), "skyblue")
    together_face = _write_png(tmp_path / "identity/together/face.png", (32, 32), "tan")
    together_body = _write_png(tmp_path / "identity/together/body.png", (32, 32), "plum")
    brief = _write_brief(tmp_path / "brief.json")

    created = _run(
        "create",
        "--story",
        "Certain of each other, learning the shared road.",
        "--creative-brief",
        str(brief),
        "--identity-image",
        str(aachu),
        "--identity-image",
        str(zuv),
        "--identity-image",
        str(together_face),
        "--identity-image",
        str(together_body),
        "--prepare-proof",
        "--proof-slide",
        "3",
        "--output-root",
        str(tmp_path / "output/carousels"),
    )
    assert created["state"] == "handoff_ready"
    assert created["selected_slides"] == [3]
    assert created["selected_formats"] == ["instagram_post"]
    package = Path(created["package_dir"])

    non_image_files = [
        path
        for path in package.rglob("*")
        if path.is_file()
        and path.suffix.lower() not in {".png", ".jpg", ".jpeg", ".webp"}
    ]
    # The enabled concept gate adds one lock marker plus the machine- and
    # creator-readable intelligence reports to the compact v3 package.
    assert len(non_image_files) <= 9
    assert (package / ".concept-lock-required").is_file()
    assert (package / "carousel-intelligence.json").is_file()
    assert (package / "carousel-intelligence.md").is_file()
    assert len(list(package.glob(".internal/compiled-prompts/**/*.prompt.txt"))) == 1
    assert not list(package.glob(".internal/compiled-prompts/**/*.md"))

    proof_png = _write_png(tmp_path / "generated/proof.png", (1080, 1440), "linen")
    ingested = _run(
        "ingest",
        str(package),
        "--instagram-post",
        str(proof_png),
        "--proof-slide",
        "3",
    )
    assert ingested["state"] == "proof_qa_required"
    receipt = json.loads((package / "generation-state.json").read_text())["slides"]["3"]["attempt_history"][-1]
    assert receipt["generator_boundary"] == "codex_builtin_imagegen"
    assert len(receipt["references"]) == 5
    assert receipt["returned_sources"][0]["width"] == 1080
    assert receipt["returned_sources"][0]["height"] == 1440
    assert receipt["pixel_review_status"] == "pending"

    proof_observations = _write_qa(
        tmp_path / "proof-observations.json", _authored_qa(package, [3])
    )
    reviewed = _run("review", str(package), "--qa", str(proof_observations))
    assert reviewed["state"] == "awaiting_creator_proof_approval"
    assert reviewed["next_action"] == "approve_proof"
    proof_sha256 = reviewed["proof_sha256"]
    bound_proof = json.loads((package / "proof-qa.json").read_text(encoding="utf-8"))
    assert "asset_bindings" in bound_proof["slides"][0]

    approved = _run(
        "approve",
        str(package),
        "--proof-sha256",
        proof_sha256,
        "--approved-by",
        "creator",
    )
    # Proof approval is the creator lock. The command immediately compiles the
    # remaining batch so there is no extra prepare gate in the hot path.
    assert approved["state"] == "handoff_ready"
    assert approved["selected_slides"] == [1, 2, 4]
    wordless_prompt = (package / ".internal/compiled-prompts/instagram-post/slide-04.prompt.txt").read_text()
    assert "No story text" in wordless_prompt
    assert "@a.storyof.two" in wordless_prompt
    reused = package / ".internal/approved-final-candidates/slide-03/instagram_post.png"
    assert reused.read_bytes() == proof_png.read_bytes()

    generated: list[Path] = []
    for slide in approved["selected_slides"]:
        generated.append(
            _write_png(
                tmp_path / f"generated/slide-{slide:02d}.png",
                (1080, 1440),
                "cornsilk",
            )
        )
    ingest_args = ["ingest", str(package)]
    for image in generated:
        ingest_args.extend(("--instagram-post", str(image)))
    final_ingested = _run(*ingest_args)
    assert final_ingested["state"] == "final_qa_required"
    assert not (package / "final-images.json").exists()
    assert not (package / "final").exists()

    final_observations = _write_qa(
        tmp_path / "final-observations.json", _authored_qa(package, [1, 2, 3, 4])
    )
    final_reviewed = _run("review", str(package), "--qa", str(final_observations))
    # Passing final QA promotes atomically; standalone finalize remains a
    # recovery/diagnostic command rather than a seventh routine step.
    assert final_reviewed["state"] == "publish_ready"
    assert final_reviewed["next_action"] == "publish"
    bound_final = json.loads((package / "visual-qa.json").read_text(encoding="utf-8"))
    assert "manifest_sha256" in bound_final
    assert "asset_binding_hashes" in bound_final
    assert bound_final["sequence_review"]["source_sha256"] == synthetic_route_sequence_review(package)["source_sha256"]
    final_text = bound_final["slides"][-1]["reviews"]["instagram_post"]["checks"]["text_brandmark_style_dimensions"]
    assert final_text["expected_text"] == final_text["observed_text"] == ""
    assert final_text["observed_brandmark"] == "@a.storyof.two"
    assert all("native_outputs" not in slide for slide in bound_final["slides"])
    assert all("asset_bindings" not in slide for slide in bound_final["slides"])
    assert final_reviewed["final_images"]["schema_version"] == "carousel-final-images/v3"
    assert (package / "final-images.json").is_file()
    assert (package / "final-audit.json").is_file()
    assert len(list((package / "final").glob("slide-*.png"))) == 4

    doctor = subprocess.run(
        [sys.executable, str(DOCTOR), str(package), "--json"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
        timeout=30,
    )
    assert doctor.returncode == 0, doctor.stdout + doctor.stderr
    report = json.loads(doctor.stdout)
    assert report["state"]["name"] == "publish_ready"
    assert report["state"]["publishable"] is True
    state_path = package / "generation-state.json"
    state = json.loads(state_path.read_text())
    assert all(slide["attempt_history"][-1]["promotion_status"] == "promoted" for slide in state["slides"].values())
    if tamper == "story_plan":
        inputs_before = build_generation_inputs(package)
        candidate_bytes = {
            path.relative_to(package): path.read_bytes()
            for path in (package / ".internal/approved-final-candidates").rglob("*.png")
        }
        context_path = package / "creative-context.json"
        context = json.loads(context_path.read_text())
        context["story_plan"]["payoff"] = "The shared route now means a decision to stay in this home."
        context_path.write_text(json.dumps(context))
        assert build_generation_inputs(package) == inputs_before
        assert synthetic_route_sequence_review(package)["source_sha256"] != bound_final["sequence_review"]["source_sha256"]
        before_status = {path.relative_to(package): path.read_bytes() for path in package.rglob("*") if path.is_file()}
        stale = _run("status", str(package), expected=2)
        assert stale["state"] == "final_qa_failed"
        assert "sequence_review.source_sha256" in stale["reason"]
        assert {path.relative_to(package): path.read_bytes() for path in package.rglob("*") if path.is_file()} == before_status
        repaired = reconcile_package_state(package)
        assert repaired["status"] == "final_qa_required"
        assert repaired["next_action"] == "repair_final_qa"
        assert "sequence_review.source_sha256" in repaired["reason"]
        assert "stale" in repaired["reason"]
        assert not (package / "final-images.json").exists()
        assert all(record["attempts"] == state["slides"][number]["attempts"] for number, record in repaired["slides"].items())
        assert all(record["attempt_history"] == state["slides"][number]["attempt_history"] for number, record in repaired["slides"].items())
        assert all(record["input_sha256"] == state["slides"][number]["input_sha256"] for number, record in repaired["slides"].items())
        assert {path: (package / path).read_bytes() for path in candidate_bytes} == candidate_bytes
        targets = _run("status", str(package))["review_targets"]
        assert [target["slide"] for target in targets] == [1, 2, 3, 4]
        assert all(target["sequence_input_sha256"] == synthetic_route_sequence_review(package)["source_sha256"] for target in targets)
        return
    receipt = state["slides"]["1"]["attempt_history"][-1]
    if tamper == "returned_sources":
        receipt["returned_sources"][0]["sha256"] = "sha256:" + "0" * 64
    else:
        receipt[tamper] = "sha256:" + "0" * 64
    state_path.write_text(json.dumps(state))
    before_status = {
        path.relative_to(package).as_posix(): path.read_bytes()
        for path in package.rglob("*")
        if path.is_file()
    }
    revoked = _run("status", str(package), expected=2)
    assert revoked["state"] == "final_qa_failed"
    assert revoked["next_action"] == "repair_publish_evidence"
    assert (package / "final-images.json").exists()
    assert {
        path.relative_to(package).as_posix(): path.read_bytes()
        for path in package.rglob("*")
        if path.is_file()
    } == before_status
