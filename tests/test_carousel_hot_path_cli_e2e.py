"""Synthetic public orchestration test; this is not a claim of vision quality."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Any

from PIL import Image


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
            "copy": "We turned the map together.",
            "physical_action": "They rotate the map and trace one route with adjacent index fingers.",
            "relationship_state": "committed and learning",
        },
    ]
    path.write_text(json.dumps({"slides": slides}), encoding="utf-8")
    return path


def _authored_qa(package: Path, selected: list[int]) -> dict[str, Any]:
    slides_payload = json.loads((package / "slides.json").read_text(encoding="utf-8"))
    slides = slides_payload["slides"] if isinstance(slides_payload, dict) else slides_payload
    copies = {int(record["slide"]): str(record["copy"]) for record in slides}
    prompt_pack = json.loads((package / "prompt-pack.json").read_text(encoding="utf-8"))
    refs = [str(value) for value in prompt_pack["identity_reference_images"]]
    style_refs = [str(value) for value in prompt_pack["style_reference_images"]]
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
            "entity_spatial_integrity": {
                "status": "PASS",
                "evidence": "Two continuous people, four owned hands, and one coherent object are visible.",
            },
            "identity_wardrobe_accessories": {
                "status": "PASS",
                "evidence": "Aachu and Zuv retain the referenced faces, hair, proportions, clothing, and accessories.",
                "references": {
                    "aachu": [refs[0]],
                    "zuv": [refs[1]],
                    "together": refs[2:],
                },
            },
            "text_brandmark_style_dimensions": {
                "status": "PASS",
                "evidence": "Exact copy and the tiny top-right brandmark are visible on the native watercolor frame.",
                "expected_text": exact_copy,
                "observed_text": exact_copy,
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
    return {
        "status": "PASS",
        "inspection": {
            "method": "codex_view_image",
            "decoded_pixels_observed": True,
        },
        "selected_slides": selected,
        "slides": records,
    }


def _write_qa(path: Path, qa: dict[str, Any]) -> Path:
    path.write_text(json.dumps(qa), encoding="utf-8")
    return path


def test_public_cli_lifecycle_promotes_only_after_bound_final_qa(tmp_path: Path) -> None:
    aachu = _write_png(tmp_path / "identity/aachu/a.png", (32, 32), "salmon")
    zuv = _write_png(tmp_path / "identity/zuv/z.png", (32, 32), "skyblue")
    together_face = _write_png(tmp_path / "identity/together/face.png", (32, 32), "tan")
    together_body = _write_png(tmp_path / "identity/together/body.png", (32, 32), "plum")
    style = _write_png(tmp_path / "style/watercolor.png", (32, 32), "ivory")
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
        "--style-reference",
        str(style),
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
    assert len(non_image_files) <= 8
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
    assert approved["state"] == "batch_ready"
    reused = package / ".internal/approved-final-candidates/slide-03/instagram_post.png"
    assert reused.read_bytes() == proof_png.read_bytes()

    prepared = _run("prepare", str(package))
    assert prepared["state"] == "handoff_ready"
    assert prepared["selected_slides"] == [1, 2, 4]
    generated: list[Path] = []
    for slide in prepared["selected_slides"]:
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
    assert final_reviewed["state"] == "final_qa_required"
    assert final_reviewed["next_action"] == "finalize_deck"
    bound_final = json.loads((package / "visual-qa.json").read_text(encoding="utf-8"))
    assert "manifest_sha256" in bound_final
    assert "asset_binding_hashes" in bound_final
    assert all("native_outputs" not in slide for slide in bound_final["slides"])
    assert all("asset_bindings" not in slide for slide in bound_final["slides"])
    assert not (package / "final-images.json").exists()

    finalized = _run("finalize", str(package))
    assert finalized["state"] == "publish_ready"
    assert finalized["next_action"] == "publish"
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
