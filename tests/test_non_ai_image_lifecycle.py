"""Synthetic planning/prepare coverage; no generated pixels or visual QA evidence."""

from __future__ import annotations

import json
from datetime import date
from pathlib import Path

from PIL import Image

from pipeline.stages.carousel_generation_inputs import build_generation_inputs
from pipeline.stages.carousel_visual_integrity import (
    build_hand_ownership_map,
    build_pre_generation_scene_contract,
)
from pipeline.stages.codex_builtin_image_generation import prepare_codex_builtin_image_generation
from pipeline.stages.codex_native_carousel import create_codex_native_carousel
from tests.helpers.carousel_qa import cinematic_slide_fields


def _png(path: Path, color: str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    Image.new("RGB", (40, 40), color).save(path)
    return path


def _scene_contract(visual_richness: dict[str, object]) -> dict[str, object]:
    scene = (
        "Aachu and Zuv stand upright at the apartment doorframe while Aachu holds "
        "a phone with the route map facing Zuv."
    )
    return build_pre_generation_scene_contract(
        scene,
        "We checked the route together.",
        hand_map=build_hand_ownership_map(
            scene,
            explicit_hands=[
                {
                    "owner": "Aachu",
                    "side": "right",
                    "visibility": "focal_action",
                    "action": "hold the phone steady for Zuv",
                    "target": "the phone's right edge",
                    "contact_target": {"object": "phone", "region": "right edge"},
                    "attachment": "continuous right shoulder-to-elbow-to-wrist-to-hand",
                    "contact": "fingers wrap the phone's right edge without hiding the screen",
                },
                *[
                    {
                        "owner": owner,
                        "side": side,
                        "visibility": "visible_relaxed",
                        "action": "hang relaxed beside the owner's hip",
                        "attachment": f"continuous {side} shoulder-to-elbow-to-wrist-to-hand",
                        "contact": "none",
                    }
                    for owner, side in (("Aachu", "left"), ("Zuv", "left"), ("Zuv", "right"))
                ],
            ],
        ),
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
        visual_richness=visual_richness,
    )


def _slide(number: int) -> dict[str, object]:
    fields = cinematic_slide_fields(number, 4)
    fields["focal_hierarchy"] = "Phone screen and Aachu's right grip first, their shared gaze second."
    fields["setting"].update(
        {
            "place": "their apartment threshold beside the doorframe",
            "depth_layers": {
                "foreground": "a soft shoe edge anchors the floor",
                "midground": "the couple pause with one phone between them",
                "background": "the doorframe establishes adult scale",
            },
        }
    )
    fields["visual_richness"].update(
        {
            "point_of_view": "Zuv studies the route Aachu offers him.",
            "before_frame": "Aachu had been studying the screen alone.",
            "after_frame": "They will take their first step along the shared route.",
            "continuation_pull": "Which route will they choose?" if number < 4 else "",
            "story_evidence": [
                {
                    "carrier": "phone route map",
                    "observable_state": "screen angled toward Zuv",
                    "narrative_job": "makes her private route a shared decision",
                },
                {
                    "carrier": "their feet at the threshold",
                    "observable_state": "both remain planted by the doorway",
                    "narrative_job": "shows they pause to decide together",
                },
            ],
        }
    )
    fields["visual_richness"].pop("scene_action_binding", None)
    contract = _scene_contract(fields["visual_richness"])
    return {
        **fields,
        "copy": "We checked the route together.",
        "physical_action": contract["scene_action_binding"],
        "relationship_state": "shared practical care",
        "scene_contract": contract,
        "hand_map": contract["hand_map"],
        "spatial_topology": contract["spatial_topology"],
    }


def test_scene_contract_survives_package_and_controls_compiled_prompt(tmp_path: Path) -> None:
    planned_slides = [_slide(number) for number in range(1, 5)]
    contract = planned_slides[0]["scene_contract"]
    brief = tmp_path / "brief.json"
    brief.write_text(
        json.dumps(
            {
                "slides": planned_slides,
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
        creative_baseline_path=brief,
        output_root=tmp_path / "output/carousels",
        today=date(2026, 9, 30),
    )

    slides = json.loads((package / "slides.json").read_text(encoding="utf-8"))
    slide = slides[0]
    prompt_pack = json.loads((package / "prompt-pack.json").read_text(encoding="utf-8"))
    assert slide["scene_contract"] == contract
    assert slide["hand_map"] == contract["hand_map"]
    assert slide["spatial_topology"] == contract["spatial_topology"]
    assert prompt_pack["schema_version"] == "carousel-prompt-pack/v3"
    assert "slides" not in prompt_pack
    assert "scene_contract" not in prompt_pack
    before = build_generation_inputs(package)

    handoff = prepare_codex_builtin_image_generation(package, proof_slide=1)
    assert handoff["status"] == "handoff_ready", handoff
    compiled = (package / ".internal/compiled-prompts/instagram-post/slide-01.prompt.txt").read_text(
        encoding="utf-8"
    )
    assert json.loads((package / "slides.json").read_text(encoding="utf-8"))[0]["scene_contract"] == contract
    assert "LOCKED SCENE CONTRACT:" in compiled
    assert "visible face=front_screen" in compiled
    assert "Aachu right: focal_action; hold the phone steady for Zuv" in compiled
    assert "Contact region=phone:right edge" in compiled

    slide["scene_contract"]["device_contract"]["devices"][0]["orientation"] = "portrait screen angled toward Zuv"
    (package / "slides.json").write_text(json.dumps(slides), encoding="utf-8")
    after = build_generation_inputs(package)
    assert after["slides"]["1"]["source_sha256"] != before["slides"]["1"]["source_sha256"]
    assert after["slides"]["1"]["prompt_sha256"] != before["slides"]["1"]["prompt_sha256"]
    assert after["shared_sha256"] == before["shared_sha256"]
    for number in ("2", "3", "4"):
        assert after["slides"][number] == before["slides"][number]

    updated_handoff = prepare_codex_builtin_image_generation(package, proof_slide=1)
    assert updated_handoff["status"] == "handoff_ready", updated_handoff
    updated_compiled = (package / ".internal/compiled-prompts/instagram-post/slide-01.prompt.txt").read_text(
        encoding="utf-8"
    )
    assert updated_compiled != compiled
    assert "portrait screen angled toward Zuv" in updated_compiled
