import json

import pytest

from pipeline.stages.carousel_generation_state import GenerationStatus, write_generation_state


def read_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def test_write_handoff_ready_state_writes_both_manifests(tmp_path):
    slide_records = [
        {
            "slide": 1,
            "expected_files": {
                "instagram_post": "final/slide-01.png",
                "reels_stories": "final-reels-stories/slide-01.png",
            },
            "source_prompt_slide": 1,
        }
    ]

    state = write_generation_state(
        tmp_path,
        status=GenerationStatus.HANDOFF_READY,
        backend="codex_builtin",
        generation_mode="model_native_publishable",
        slide_count=1,
        reason="Ready for human generation.",
        slides=slide_records,
    )

    image_generation = read_json(tmp_path / "image-generation.json")
    final_images = read_json(tmp_path / "final-images.json")
    assert image_generation == final_images == state
    assert final_images["status"] == "handoff_ready"
    assert final_images["done"] is False
    assert final_images["publishable"] is False
    assert final_images["requires_human_generation"] is True
    assert final_images["slides"] == slide_records


def test_generated_state_requires_slide_records(tmp_path):
    with pytest.raises(ValueError, match="slides"):
        write_generation_state(
            tmp_path,
            status=GenerationStatus.GENERATED,
            backend="codex_builtin",
            generation_mode="model_native_publishable",
            slide_count=1,
        )

    state = write_generation_state(
        tmp_path,
        status=GenerationStatus.GENERATED,
        backend="codex_builtin",
        generation_mode="model_native_publishable",
        slide_count=1,
        slides=[
            {
                "slide": 1,
                "file": "final/slide-01.png",
            }
        ],
    )

    final_images = read_json(tmp_path / "final-images.json")
    assert final_images == state
    assert final_images["status"] == "generated"
    assert final_images["done"] is True
    assert final_images["publishable"] is True
    assert final_images["slides"][0]["file"] == "final/slide-01.png"


def test_extra_cannot_overwrite_schema_fields(tmp_path):
    with pytest.raises(ValueError, match="reserved"):
        write_generation_state(
            tmp_path,
            status=GenerationStatus.HANDOFF_READY,
            backend="codex_builtin",
            generation_mode="model_native_publishable",
            slide_count=1,
            extra={"status": "oops"},
        )


def test_only_generated_state_is_done(tmp_path):
    state = write_generation_state(
        tmp_path,
        status=GenerationStatus.QA_PASSED,
        backend="codex_builtin",
        generation_mode="model_native_publishable",
        slide_count=1,
        slides=[{"slide": 1, "file": "final/slide-01.png"}],
    )

    assert state["done"] is False
    assert state["publishable"] is False


def test_audit_failed_state_is_non_publishable(tmp_path):
    state = write_generation_state(
        tmp_path,
        status=GenerationStatus.GENERATED_AUDIT_FAILED,
        backend="codex_builtin",
        generation_mode="model_native_publishable",
        slide_count=1,
        reason="Generated files were packaged, but final-audit.json did not pass.",
        slides=[{"slide": 1, "file": "final/slide-01.png"}],
    )

    assert state["status"] == "generated_audit_failed"
    assert state["done"] is False
    assert state["publishable"] is False
