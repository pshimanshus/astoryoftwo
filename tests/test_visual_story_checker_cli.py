from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path

from PIL import Image

from pipeline.stages.carousel_format_contract import write_format_contract
from pipeline.stages.carousel_pixel_qa import (
    PIXEL_QA_SCHEMA_VERSION,
    asset_binding_fingerprint,
)


SCRIPT = (
    Path(__file__).resolve().parents[1]
    / ".agents"
    / "skills"
    / "a-story-direct-visual-story"
    / "scripts"
    / "check_visual_story.py"
)


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def write_png(path: Path, size: tuple[int, int] = (1080, 1440)) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    Image.new("RGB", size, (241, 232, 217)).save(path)


def base_package(package: Path, *, with_format: bool = True) -> Path:
    package.mkdir()
    if with_format:
        write_format_contract(package, ["instagram_post"], source="test")
    write_png(package / "refs" / "couple.png", (64, 64))
    action = "Aachu and Zuv pull the same dining table toward opposite walls while the plates slide apart."
    write_json(
        package / "slides.json",
        {"slides": [{"slide": 1, "copy": "We knew who. We were learning how.", "physical_action": action}]},
    )
    write_json(
        package / "prompt-pack.json",
        {
            "identity_reference_images": ["refs/couple.png"],
            "slides": [
                {
                    "slide": 1,
                    "text": "We knew who. We were learning how.",
                    "physical_action": action,
                }
            ],
        },
    )
    return package


def _run_checker(package: Path, phase: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [
            sys.executable,
            str(SCRIPT),
            "--carousel-dir",
            str(package),
            "--phase",
            phase,
            "--compact",
        ],
        capture_output=True,
        text=True,
        timeout=30,
    )


def test_pre_checker_passes_without_event_a_or_provenance(tmp_path: Path) -> None:
    package = base_package(tmp_path / "pre")

    result = _run_checker(package, "pre")
    payload = json.loads(result.stdout)

    assert result.returncode == 0
    assert payload["pass"] is True
    assert payload["checks"]["copy_format_action_preflight"]["pass"] is True
    assert not (package / "visual-plan-quality.json").exists()


def test_pre_checker_requires_persisted_current_format_contract(tmp_path: Path) -> None:
    package = base_package(tmp_path / "missing-format", with_format=False)

    result = _run_checker(package, "pre")
    payload = json.loads(result.stdout)

    assert result.returncode == 1
    assert payload["pass"] is False
    assert any("format-contract.json is missing" in issue for issue in payload["issues"])


def test_v3_pre_checker_requires_curated_identity_roles_and_style_attachment(
    tmp_path: Path,
) -> None:
    package = base_package(tmp_path / "v3-refs")
    write_json(
        package / "generation-state.json",
        {"schema_version": "carousel-generation-state/v3", "status": "draft"},
    )

    result = _run_checker(package, "pre")
    payload = json.loads(result.stdout)

    assert result.returncode == 1
    assert any("Aachu, Zuv, and together" in issue for issue in payload["issues"])
    assert any("no attached style references" in issue for issue in payload["issues"])


def test_v3_pre_checker_rejects_story_only_physical_action_placeholders(
    tmp_path: Path,
) -> None:
    package = base_package(tmp_path / "v3-action-placeholder")
    slides = json.loads((package / "slides.json").read_text(encoding="utf-8"))
    slides["slides"][0]["physical_action"] = (
        "Draft needed: choose one specific observable action before image generation."
    )
    slides["slides"][0]["needs_physical_action"] = True
    write_json(package / "slides.json", slides)
    write_json(
        package / "generation-state.json",
        {"schema_version": "carousel-generation-state/v3", "status": "draft"},
    )

    result = _run_checker(package, "pre")
    payload = json.loads(result.stdout)

    assert result.returncode == 1
    assert any("physical action is still a draft placeholder" in issue for issue in payload["issues"])


def test_v3_pre_checker_reads_identity_roles_from_localized_selection(
    tmp_path: Path,
) -> None:
    package = base_package(tmp_path / "v3-localized")
    refs = [
        ".internal/references/identity/a1.png",
        ".internal/references/identity/b2.png",
        ".internal/references/identity/c3.png",
    ]
    style_ref = ".internal/references/style/s1.png"
    for ref in [*refs, style_ref]:
        write_png(package / ref, (64, 64))
    prompt = json.loads((package / "prompt-pack.json").read_text(encoding="utf-8"))
    prompt["identity_reference_images"] = refs
    prompt["style_reference_images"] = [style_ref]
    write_json(package / "prompt-pack.json", prompt)
    write_json(
        package / "creative-context.json",
        {
            "identity_reference_selection": {
                "selected_references": [
                    {"path": refs[0], "role": "Aachu identity anchor"},
                    {"path": refs[1], "role": "Zuv identity anchor"},
                    {"path": refs[2], "role": "together body/posture anchor"},
                ]
            }
        },
    )
    write_json(
        package / "generation-state.json",
        {"schema_version": "carousel-generation-state/v3", "status": "draft"},
    )

    result = _run_checker(package, "pre")
    payload = json.loads(result.stdout)

    assert result.returncode == 0
    assert payload["checks"]["copy_format_action_preflight"]["pass"] is True


def test_post_checker_fails_fast_on_semantic_pixels(tmp_path: Path) -> None:
    package = base_package(tmp_path / "semantic")
    proof = package / ".internal" / "visual-quarantine" / "proof.png"
    write_png(proof)
    digest = hashlib.sha256(proof.read_bytes()).hexdigest()
    write_json(
        package / "generation-state.json",
        {"status": "GENERATED_QUARANTINED", "requested_formats": ["instagram_post"]},
    )
    write_json(
        package / "proof-qa.json",
        {
            "status": "FAIL",
            "pass": False,
            "checks": {
                "semantic_action": {"pass": False},
                "relationship_state": {"pass": False},
            },
            "slides": [
                {
                    "slide": 1,
                    "native_outputs": {
                        "instagram_post": {
                            "path": str(proof.relative_to(package)),
                            "sha256": digest,
                        }
                    },
                }
            ],
        },
    )

    result = _run_checker(package, "post")
    payload = json.loads(result.stdout)

    assert result.returncode == 1
    assert payload["checks"]["bound_pixel_observation_qa"]["pass"] is False
    assert payload["issues"] == [
        "post: semantic_action failed on the rendered pixels (semantic_action)."
    ]


def test_post_checker_rejects_stale_asset_hash(tmp_path: Path) -> None:
    package = base_package(tmp_path / "stale")
    proof = package / ".internal" / "visual-quarantine" / "proof.png"
    write_png(proof)
    write_json(
        package / "generation-state.json",
        {"status": "QA_PASS_CANDIDATE", "requested_formats": ["instagram_post"]},
    )
    write_json(
        package / "proof-qa.json",
        {
            "status": "PASS",
            "pass": True,
            "checks": {
                "semantic_action": {"pass": True},
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
                            "path": str(proof.relative_to(package)),
                            "sha256": "0" * 64,
                        }
                    },
                }
            ],
        },
    )

    result = _run_checker(package, "post")
    payload = json.loads(result.stdout)

    assert result.returncode == 1
    assert any("SHA-256 is missing or stale" in issue for issue in payload["issues"])


def test_strict_post_checker_validates_authored_view_image_evidence_without_claiming_vision(
    tmp_path: Path,
) -> None:
    package = base_package(tmp_path / "strict")
    # Strict identity evidence names the exact four selected role anchors.
    refs = [
        "refs/aachu.png",
        "refs/zuv.png",
        "refs/together-face.png",
        "refs/together-body.png",
    ]
    style_ref = "refs/style.png"
    for ref in [*refs, style_ref]:
        write_png(package / ref, (64, 64))
    prompt = json.loads((package / "prompt-pack.json").read_text(encoding="utf-8"))
    prompt["identity_reference_images"] = refs
    prompt["style_reference_images"] = [style_ref]
    write_json(package / "prompt-pack.json", prompt)
    write_json(
        package / "creative-context.json",
        {
            "identity_reference_selection": {
                "selected_references": [
                    {"path": refs[0], "role": "Aachu identity anchor"},
                    {"path": refs[1], "role": "Zuv identity anchor"},
                    {"path": refs[2], "role": "together face/scale anchor"},
                    {"path": refs[3], "role": "together body/posture anchor"},
                ]
            }
        },
    )

    proof = package / ".internal" / "visual-quarantine" / "slide-01" / "attempt-01" / "instagram_post.png"
    write_png(proof)
    binding = {
        "path": str(proof.relative_to(package)),
        "sha256": "sha256:" + hashlib.sha256(proof.read_bytes()).hexdigest(),
        "width": 1080,
        "height": 1440,
    }
    binding["binding_sha256"] = asset_binding_fingerprint(1, "instagram_post", binding)
    copy_text = "We knew who. We were learning how."
    checks = {
        "physical_action": {
            "status": "PASS",
            "evidence": "Both people visibly pull the dining table toward opposite walls.",
        },
        "relationship_state": {
            "status": "PASS",
            "evidence": "Their conflict is visible while the shared table keeps them connected.",
        },
        "entity_spatial_integrity": {
            "status": "PASS",
            "evidence": "Two silhouettes, four hands, and the shared table have coherent contact and ownership.",
        },
        "identity_wardrobe_accessories": {
            "status": "PASS",
            "evidence": "Aachu and Zuv match the named face, body, wardrobe, and shared-scale references.",
            "references": {
                "aachu": [refs[0]],
                "zuv": [refs[1]],
                "together": refs[2:],
            },
        },
        "text_brandmark_style_dimensions": {
            "status": "PASS",
            "evidence": "The exact text and tiny top-right brandmark are visible on the native post canvas.",
            "expected_text": copy_text,
            "observed_text": copy_text,
            "observed_brandmark": "@a.storyof.two",
            "style_references": [style_ref],
        },
    }
    write_json(
        package / "proof-qa.json",
        {
            "schema_version": PIXEL_QA_SCHEMA_VERSION,
            "scope": "proof",
            "status": "PASS",
            "inspection": {
                "method": "codex_view_image",
                "decoded_pixels_observed": True,
            },
            "selected_slides": [1],
            "slides": [
                {
                    "slide": 1,
                    "asset_bindings": {"instagram_post": binding},
                    "reviews": {"instagram_post": {"checks": checks}},
                }
            ],
        },
    )

    result = _run_checker(package, "post")
    payload = json.loads(result.stdout)

    # The checker validates an external pixel observation. It does not invoke
    # image generation, OCR, or a vision backend itself.
    assert result.returncode == 0
    assert payload["checks"]["bound_pixel_observation_qa"]["pass"] is True


def test_strict_post_checker_rejects_fabricated_unobserved_qa(tmp_path: Path) -> None:
    package = base_package(tmp_path / "fabricated")
    write_json(
        package / "proof-qa.json",
        {
            "schema_version": PIXEL_QA_SCHEMA_VERSION,
            "scope": "proof",
            "status": "PASS",
            "selected_slides": [1],
            "slides": [],
        },
    )

    result = _run_checker(package, "post")
    payload = json.loads(result.stdout)

    assert result.returncode == 1
    assert any("inspection metadata is missing" in issue for issue in payload["issues"])
