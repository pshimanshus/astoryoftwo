import json
from datetime import date
from pathlib import Path

from PIL import Image

from pipeline.stages.codex_builtin_image_generation import prepare_codex_builtin_image_generation
from pipeline.stages.codex_native_carousel import create_codex_native_carousel


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
    style = tmp_path / "style.png"
    Image.new("RGB", (300, 300), "ivory").save(style)
    brief = tmp_path / "brief.json"
    brief.write_text(
        json.dumps(
            {
                "slides": [
                    {
                        "copy": "Some days, love did not tell us what to do.",
                        "physical_action": (
                            "They reopen one duvet cover together and align the same missing corner."
                        ),
                    },
                    {
                        "copy": "We are still learning how.",
                        "physical_action": (
                            "One holds the empty corner pocket open while the other seats the insert."
                        ),
                    },
                    {
                        "copy": "Commitment answered who.",
                        "physical_action": "They shake the now-filled duvet flat from the same side.",
                    },
                    {
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
        style_reference_paths=[style],
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
