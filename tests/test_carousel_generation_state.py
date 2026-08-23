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
    assert final_images["publishable"] is False
    assert final_images["slides"][0]["file"] == "final/slide-01.png"


def test_publish_ready_state_is_the_publishable_manifest_state(tmp_path):
    state = write_generation_state(
        tmp_path,
        status=GenerationStatus.PUBLISH_READY,
        backend="codex_builtin",
        generation_mode="model_native_publishable",
        slide_count=1,
        slides=[
            {
                "slide": 1,
                "file": "final/slide-01.png",
                "reels_stories_file": "final-reels-stories/slide-01.png",
            }
        ],
        extra={"final_audit_pass": True},
    )

    final_images = read_json(tmp_path / "final-images.json")
    assert final_images == state
    assert final_images["status"] == "publish_ready"
    assert final_images["done"] is True
    assert final_images["publishable"] is True


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


def test_only_generated_and_publish_ready_states_are_done(tmp_path):
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


def test_proof_state_machine_rejects_skipping_qa_and_creator_approval(tmp_path):
    slides = [{"slide": 1, "file": ".internal/visual-quarantine/attempt-01/slide-01.png"}]
    write_generation_state(
        tmp_path,
        status=GenerationStatus.GENERATED_QUARANTINED,
        backend="codex_builtin",
        generation_mode="model_native_publishable",
        slide_count=1,
        slides=slides,
    )

    with pytest.raises(ValueError, match="Invalid proof-state transition"):
        write_generation_state(
            tmp_path,
            status=GenerationStatus.BATCH_ALLOWED,
            backend="codex_builtin",
            generation_mode="model_native_publishable",
            slide_count=1,
            slides=slides,
        )


@pytest.mark.parametrize(
    "initial_status",
    [None, GenerationStatus.DRAFT, GenerationStatus.HANDOFF_READY],
)
@pytest.mark.parametrize(
    "skipped_status",
    [
        GenerationStatus.QA_PASS_CANDIDATE,
        GenerationStatus.CREATOR_APPROVED_PROOF,
        GenerationStatus.BATCH_ALLOWED,
    ],
)
def test_proof_state_machine_rejects_entering_after_quarantine(
    tmp_path, initial_status, skipped_status
):
    if initial_status is not None:
        write_generation_state(
            tmp_path,
            status=initial_status,
            backend="test",
            generation_mode="test",
            slide_count=1,
        )

    with pytest.raises(ValueError, match="first state must be GENERATED_QUARANTINED"):
        write_generation_state(
            tmp_path,
            status=skipped_status,
            backend="test",
            generation_mode="test",
            slide_count=1,
            slides=[{"slide": 1}],
        )


def test_batch_allowed_to_handoff_requires_validated_creator_override(tmp_path):
    batch_state = {
        "status": GenerationStatus.BATCH_ALLOWED.value,
        "slides": [{"slide": 1}],
    }
    for filename in ("image-generation.json", "final-images.json"):
        (tmp_path / filename).write_text(
            json.dumps(batch_state),
            encoding="utf-8",
        )

    with pytest.raises(
        ValueError,
        match="Invalid exit from fail-closed proof state",
    ):
        write_generation_state(
            tmp_path,
            status=GenerationStatus.HANDOFF_READY,
            backend="codex_builtin",
            generation_mode="model_native_publishable",
            slide_count=2,
            slides=[{"slide": 1}, {"slide": 2}],
        )

    handoff = write_generation_state(
        tmp_path,
        status=GenerationStatus.HANDOFF_READY,
        backend="codex_builtin",
        generation_mode="model_native_publishable",
        slide_count=2,
        slides=[{"slide": 1}, {"slide": 2}],
        creator_override_handoff_validated=True,
    )

    assert handoff["status"] == GenerationStatus.HANDOFF_READY.value
    assert handoff["publishable"] is False


@pytest.mark.parametrize(
    "failed_status",
    [
        GenerationStatus.GENERATED_QUARANTINED,
        GenerationStatus.REJECTED_SPATIAL_INTEGRITY,
    ],
)
def test_qa_failed_full_deck_retry_to_handoff_requires_validation(
    tmp_path, failed_status
):
    failed_state = {
        "status": failed_status.value,
        "slides": [{"slide": 1}, {"slide": 2}],
    }
    for filename in ("image-generation.json", "final-images.json"):
        (tmp_path / filename).write_text(
            json.dumps(failed_state),
            encoding="utf-8",
        )

    with pytest.raises(
        ValueError,
        match="Invalid exit from fail-closed proof state",
    ):
        write_generation_state(
            tmp_path,
            status=GenerationStatus.HANDOFF_READY,
            backend="codex_builtin",
            generation_mode="model_native_publishable",
            slide_count=2,
            slides=[{"slide": 1}, {"slide": 2}],
        )

    handoff = write_generation_state(
        tmp_path,
        status=GenerationStatus.HANDOFF_READY,
        backend="codex_builtin",
        generation_mode="model_native_publishable",
        slide_count=2,
        slides=[{"slide": 1}, {"slide": 2}],
        qa_failed_full_deck_retry_handoff_validated=True,
    )

    assert handoff["status"] == GenerationStatus.HANDOFF_READY.value
    assert handoff["publishable"] is False
