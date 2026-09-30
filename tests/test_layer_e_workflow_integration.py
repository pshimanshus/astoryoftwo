import json
from datetime import date
from pathlib import Path

from PIL import Image

from pipeline.stages.codex_builtin_image_generation import prepare_codex_builtin_image_generation
from pipeline.stages.codex_native_carousel import create_codex_native_carousel


def _cinematic(number: int, *, is_final: bool = False) -> dict[str, object]:
    return {
        "role": "payoff" if is_final else f"story_beat_{number}",
        "relationship_state": f"Their duvet effort visibly softens into shared rhythm at beat {number}.",
        "camera": {
            "shot_size": "close payoff detail" if is_final else f"medium-wide action frame {number}",
            "position": f"bed-height three-quarter view beside the active corner {number}",
            "negative_space": f"quiet upper-left wall above duvet beat {number}",
        },
        "focal_hierarchy": f"Their active hands read first, duvet corner {number} second, and upper copy stays clear.",
        "setting": {
            "place": "their lived-in bedroom beside the rain-streaked window",
            "time": "late rainy afternoon",
            "motivated_light": f"cool window light crosses frame-left over duvet corner {number}",
            "depth_layers": {
                "foreground": f"rumpled sheet edge leads toward duvet beat {number}",
                "midground": f"both partners work the same duvet corner {number}",
                "background": "the unmade bedside table proves the ongoing shared routine",
            },
        },
        "visual_richness": {
            "point_of_view": f"Their shared frustration organizes duvet beat {number}.",
            "before_frame": f"The insert had slipped away from its corner before beat {number}.",
            "after_frame": f"The duvet will lie flatter because of action beat {number}.",
            "continuation_pull": "" if is_final else f"Will the next corner finally align after beat {number}?",
            "story_evidence": [
                {
                    "carrier": f"the twisted duvet seam {number}",
                    "observable_state": "its fabric tension changes beneath both active grips",
                    "narrative_job": "proves their cooperation through a visible consequence",
                },
                {
                    "carrier": f"their synchronized knees at beat {number}",
                    "observable_state": "both bodies brace toward the same corner",
                    "narrative_job": "proves the relationship turn without relying on copy",
                },
            ],
            "posed_portrait_allowed": False,
            "decorative_clutter_allowed": False,
        },
    }


def test_default_carousel_does_not_write_layer_e_or_room_artifacts(tmp_path: Path) -> None:
    identities = []
    for relative, color in (
        ("identity/aachu/a.png", "salmon"),
        ("identity/zuv/z.png", "skyblue"),
        ("identity/together/face.png", "tan"),
        ("identity/together/body.png", "plum"),
    ):
        identity = tmp_path / relative
        identity.parent.mkdir(parents=True, exist_ok=True)
        Image.new("RGB", (300, 300), color).save(identity)
        identities.append(identity)
    brief = tmp_path / "brief.json"
    brief.write_text(
        json.dumps(
            {
                "slides": [
                    {
                        **_cinematic(1),
                        "copy": "Some days, love did not tell us what to do.",
                        "physical_action": (
                            "They reopen one duvet cover together and align the same missing corner."
                        ),
                    },
                    {
                        **_cinematic(2),
                        "copy": "We are still learning how.",
                        "physical_action": (
                            "One holds the empty corner pocket open while the other seats the insert."
                        ),
                    },
                    {
                        **_cinematic(3),
                        "copy": "Commitment answered who.",
                        "physical_action": "They shake the now-filled duvet flat from the same side.",
                    },
                    {
                        **_cinematic(4, is_final=True),
                        "copy": "We kept choosing the same bed.",
                        "physical_action": "They fall backward laughing onto the finished duvet.",
                    },
                ]
            }
        ),
        encoding="utf-8",
    )

    package = create_codex_native_carousel(
        title="Duvet Test",
        story="One shared task became a visible lesson in staying.",
        image_paths=[],
        identity_image_paths=identities,
        creative_baseline_path=brief,
        output_root=tmp_path / "output" / "carousels",
        today=date(2026, 8, 24),
    )

    assert not (package / "layer-e-story-selling.json").exists()
    assert not (package / "post-copy-visual-room.json").exists()
    assert not (package / "visual-debate.json").exists()
    assert not (package / "run-ledger.json").exists()
    result = prepare_codex_builtin_image_generation(package, proof_slide=1)
    assert result["status"] == "handoff_ready"
    assert result["proof_slide"] == 1
    assert result["selected_slides"] == [1]
    assert set(result) <= {
        "schema_version",
        "status",
        "next_action",
        "proof_slide",
        "selected_slides",
        "selected_formats",
        "format_sha256",
        "slides",
        "reason",
    }
