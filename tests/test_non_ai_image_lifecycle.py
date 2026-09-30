from __future__ import annotations

import json
from datetime import date
from pathlib import Path

from PIL import Image

from pipeline.stages.carousel_generation_inputs import build_generation_inputs
from pipeline.stages.carousel_visual_integrity import build_pre_generation_scene_contract
from pipeline.stages.codex_builtin_image_generation import prepare_codex_builtin_image_generation
from pipeline.stages.codex_native_carousel import create_codex_native_carousel


def _png(path: Path, color: str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    Image.new("RGB", (40, 40), color).save(path)
    return path


def _scene_contract() -> dict[str, object]:
    scene = (
        "Aachu and Zuv stand upright at the apartment doorframe while Aachu holds "
        "a phone with the route map facing Zuv."
    )
    return build_pre_generation_scene_contract(
        scene,
        "We checked the route together.",
        hand_map={
            "people": ["Aachu", "Zuv"],
            "hands": [
                {
                    "owner": "Aachu",
                    "side": "right",
                    "visibility": "focal_action",
                    "action": "hold the phone steady for Zuv",
                    "target": "the phone's right edge",
                    "contact_target": {"object": "phone", "region": "right edge"},
                    "attachment": "continuous right shoulder-to-elbow-to-wrist-to-hand",
                }
            ],
        },
        devices=[
            {
                "object": "phone",
                "owner": "Aachu",
                "visible_face": "front_screen",
                "orientation": "portrait screen facing Zuv",
                "use": "show the route together",
                "ui_visible": True,
                "screen_content": "a route map",
            }
        ],
        scale={
            "aachu_height": "5 ft 6 in",
            "zuv_height": "5 ft 8 in",
            "relative_height": "Zuv is only slightly taller than Aachu",
            "pose": "upright standing",
            "evidence": ["both pairs of feet meet the floor", "the doorframe establishes adult scale"],
        },
        accessories=[
            {
                "owner": "Aachu",
                "item": "evil-eye bracelet",
                "worn": True,
                "visibility": "visible",
                "placement": "right wrist",
            },
            {
                "owner": "Zuv",
                "item": "small round evil-eye locket on a slim silver chain",
                "worn": True,
                "visibility": "occluded",
                "occlusion_reason": "his closed collar covers the chain",
            },
        ],
    )


def test_scene_contract_survives_package_and_controls_compiled_prompt(tmp_path: Path) -> None:
    contract = _scene_contract()
    brief = tmp_path / "brief.json"
    brief.write_text(
        json.dumps(
            {
                "slides": [
                    {
                        "copy": "We checked the route together.",
                        "physical_action": contract["scene_action_binding"],
                        "relationship_state": "shared practical care",
                        "scene_contract": contract,
                    }
                    for _ in range(4)
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
    package = create_codex_native_carousel(
        story="A practical pause before leaving.",
        image_paths=[_png(tmp_path / "story.png", "ivory")],
        identity_image_paths=identity_paths,
        style_reference_paths=[_png(tmp_path / "style.png", "orange")],
        creative_baseline_path=brief,
        output_root=tmp_path / "output/carousels",
        today=date(2026, 9, 30),
    )

    slides = json.loads((package / "slides.json").read_text(encoding="utf-8"))
    slide = slides[0]
    prompt = json.loads((package / "prompt-pack.json").read_text(encoding="utf-8"))["slides"][0]
    assert slide["scene_contract"] == contract
    assert prompt["scene_contract"] == contract
    before = build_generation_inputs(package)

    handoff = prepare_codex_builtin_image_generation(package, proof_slide=1)
    compiled = (package / ".internal/compiled-prompts/instagram-post/slide-01.prompt.txt").read_text(
        encoding="utf-8"
    )
    assert handoff["status"] == "handoff_ready"
    assert "LOCKED SCENE CONTRACT:" in compiled
    assert "visible face=front_screen" in compiled
    assert "contact=phone:right edge" in compiled

    slide["scene_contract"]["device_contract"]["devices"][0]["orientation"] = "portrait screen angled toward Zuv"
    (package / "slides.json").write_text(json.dumps(slides), encoding="utf-8")
    after = build_generation_inputs(package)
    assert after["slides"]["1"]["source_sha256"] != before["slides"]["1"]["source_sha256"]
    assert after["slides"]["1"]["prompt_sha256"] != before["slides"]["1"]["prompt_sha256"]
