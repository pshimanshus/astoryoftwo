from __future__ import annotations

import json
import hashlib
from pathlib import Path
from unittest.mock import patch

import pytest
from PIL import Image

from pipeline.stages.codex_builtin_image_generation import (
    build_compiled_prompt_handoff,
    image_set_sha256,
    load_attempt_ledger,
    package_codex_builtin_outputs,
    promote_quarantined_codex_builtin_outputs,
    run_fail_closed_visual_worker,
    validate_exact_image_visual_qa,
    validate_quarantine_integrity,
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
