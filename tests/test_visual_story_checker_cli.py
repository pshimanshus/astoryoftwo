from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path

from PIL import Image

from pipeline.stages.carousel_format_contract import write_format_contract


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
    assert payload["checks"]["actual_pixel_story_qa"]["pass"] is False
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
