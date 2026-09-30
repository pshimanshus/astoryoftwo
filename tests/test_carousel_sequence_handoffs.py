from __future__ import annotations

from datetime import date
import json
from pathlib import Path

import pytest

from pipeline.stages.carousel_generation_inputs import build_generation_inputs
from pipeline.stages.carousel_generation_state import read_generation_state, write_v3_state
from pipeline.stages.carousel_sequence import sequence_input_fingerprint
import pipeline.stages.codex_builtin_image_generation as generation
from pipeline.stages.codex_builtin_image_generation import (
    prepare_codex_builtin_image_generation,
    reconcile_package_state,
    visual_plan_quality_gate_reason,
)
from pipeline.stages.codex_native_carousel import (
    create_codex_native_carousel,
    slides_from_creative_baseline,
)
from tests.test_carousel_generation_inputs import (
    _cinematic_slide,
    _identity_bundle,
    _mark_work_in_progress,
    _package,
)
from tests.test_carousel_prompt_compiler import _compile


def _brief() -> dict:
    slides = [_cinematic_slide(number) for number in range(1, 5)]
    beats = [
        "The object starts between two different destinations.",
        "Aachu loosens her grip and lets Zuv try his direction.",
        "Zuv pauses at the narrow doorway and looks back for her hand.",
        "Their paired grips bring the object to the window together.",
    ]
    for slide, beat in zip(slides, beats):
        slide.update(
            copy_mode="text",
            beat_delta=beat,
            copy_image_relation={
                "kind": "completion",
                "proof": "Both grips and the object's destination make the shared choice visible.",
            },
        )
    slides[-1].update(
        copy="",
        copy_mode="wordless",
        copy_image_relation={
            "kind": "wordless",
            "proof": "Both partners release the object at the same window.",
        },
    )
    return {
        "architecture": "Two directions -> a pause -> one shared destination",
        "story_plan": {
            "theme": "Learning to choose a direction together.",
            "recognition": "Couples who begin a small job with two separate plans.",
            "sequence_mode": "relationship_change",
            "opening_promise": "How will they find one destination?",
            "mismatch": "Each partner is pulling toward a different place.",
            "turn_or_accumulation": "They pause and rejoin their grips.",
            "payoff": "They set the object down together.",
            "send_reason": "We keep learning how to do ordinary things together.",
            "architecture": ["Separate directions", "Try", "Return", "Together"],
        },
        "research_refs": [{"source": "local-observation", "why": "Paired grips reveal coordination."}],
        "slides": slides,
    }


def _sequence_package(tmp_path: Path, brief: dict | None = None) -> Path:
    baseline = tmp_path / "sequence-brief.json"
    baseline.write_text(json.dumps(brief or _brief()), encoding="utf-8")
    return create_codex_native_carousel(
        story="One difficult shared direction.",
        image_paths=[],
        identity_image_paths=_identity_bundle(tmp_path),
        creative_baseline_path=baseline,
        output_root=tmp_path / "output/carousels",
        today=date(2026, 9, 20),
    )


def test_approved_sequence_roundtrips_and_wordless_handoff_remains_explicit(tmp_path: Path) -> None:
    brief = _brief()
    package = _sequence_package(tmp_path, brief)
    context = json.loads((package / "creative-context.json").read_text())
    slides = json.loads((package / "slides.json").read_text())

    assert context["story_plan"] == brief["story_plan"]
    assert context["research_refs"] == brief["research_refs"]
    assert context["architecture"] == brief["architecture"]
    assert context["sequence_contract"] == "carousel-sequence/v1"
    for actual, approved in zip(slides, brief["slides"]):
        for key in ("copy", "copy_mode", "beat_delta", "copy_image_relation", "role", "physical_action", "visual_richness"):
            assert actual[key] == approved[key]
    assert visual_plan_quality_gate_reason(package) is None
    state = prepare_codex_builtin_image_generation(package, proof_slide=4)
    assert state["status"] == "handoff_ready", state.get("reason")
    prompt = (package / ".internal/compiled-prompts/instagram-post/slide-04.prompt.txt").read_text()
    assert "No story text" in prompt
    assert "@a.storyof.two" in prompt
    assert brief["slides"][-1]["beat_delta"] in prompt
    assert brief["slides"][-1]["copy_image_relation"]["proof"] in prompt
    assert "local-observation" not in prompt
    assert "research_refs" not in prompt


@pytest.mark.parametrize("changes", [
    {"copy": ""},
    {"copy_mode": "silent"},
    {"copy_mode": "wordless", "copy": "Do not erase me."},
    {"copy_mode": None},
    {"beat_delta": []},
    {"copy_image_relation": {"kind": "contradiction", "proof": ""}},
    {"copy_image_relation": {"kind": "caption", "proof": "Visible tears."}},
])
def test_malformed_sequence_fields_are_rejected_before_normalization(changes: dict) -> None:
    brief = _brief()
    brief["slides"][0].update(changes)
    field = next(iter(changes))
    with pytest.raises(ValueError, match="copy|wordless" if field in {"copy", "copy_mode"} else field):
        slides_from_creative_baseline({"slides": [brief["slides"][0]]}, [])


def test_explicit_wordless_copy_does_not_resurrect_legacy_text_alias() -> None:
    brief = _brief()
    brief["slides"][-1]["text"] = "A retired line must not return."
    slides = slides_from_creative_baseline(brief, [])
    assert slides[-1]["copy"] == ""
    assert slides[-1]["copy_mode"] == "wordless"


def test_invalid_story_plan_is_rejected_instead_of_dropped(tmp_path: Path) -> None:
    brief = _brief()
    brief["story_plan"]["payoff"] = []
    with pytest.raises(ValueError, match="payoff"):
        _sequence_package(tmp_path, brief)


def test_wordless_compiler_forbids_invented_story_copy_but_keeps_brandmark() -> None:
    prompt = _compile(slide_copy="", copy_mode="wordless")
    assert "No story text" in prompt
    assert "tiny" in prompt and "@a.storyof.two" in prompt
    assert "Render the ON-IMAGE TEXT exactly" not in prompt
    with pytest.raises(ValueError):
        _compile(slide_copy="")
    with pytest.raises(ValueError):
        _compile(slide_copy="Still locked.", copy_mode="wordless")


def test_compiler_keeps_contradiction_proof_within_existing_prompt_budget() -> None:
    prompt = _compile(
        beat_delta="Her denial becomes visibly unconvincing.",
        copy_image_relation={"kind": "contradiction", "proof": "Her spoken denial contrasts with tears on both cheeks."},
    )
    assert "Her denial becomes visibly unconvincing." in prompt
    assert "Her spoken denial contrasts with tears on both cheeks." in prompt


@pytest.mark.parametrize("field,value", [
    ("beat_delta", "He stops pulling and waits for her to choose."),
    ("copy_image_relation", {"kind": "reinterpretation", "proof": "His open grip reveals an invitation to choose."}),
    ("copy_mode", "text"),
])
def test_slide_sequence_semantics_invalidate_only_affected_art(tmp_path: Path, field: str, value: object) -> None:
    package = _package(tmp_path)
    before = _mark_work_in_progress(package)
    path = package / "slides.json"
    slides = json.loads(path.read_text())
    slides[1][field] = value
    path.write_text(json.dumps(slides))
    after = reconcile_package_state(package)
    assert after["slides"]["2"]["status"] == "draft"
    assert after["slides"]["2"]["source_sha256"] != before["slides"]["2"]["source_sha256"]
    for number in ("1", "3", "4"):
        assert after["slides"][number] == before["slides"][number]


def test_research_annotation_changes_preserve_generation_inputs_and_candidates(tmp_path: Path) -> None:
    package = _sequence_package(tmp_path)
    before = _mark_work_in_progress(package)
    # Candidate inventory can exist without claiming a proof approval; the
    # fixture deliberately has no pixel QA or creator approval evidence.
    before["proof_slide"] = None
    before = write_v3_state(package, before)
    inputs = build_generation_inputs(package)
    path = package / "creative-context.json"
    context = json.loads(path.read_text())
    context["research_refs"] = [{"source": "new observation", "why": "Different editorial comparison."}]
    path.write_text(json.dumps(context))
    assert build_generation_inputs(package) == inputs
    assert reconcile_package_state(package) == before
    assert (package / ".internal/approved-final-candidates/slide-02/sentinel.txt").exists()


def test_review_targets_expose_sequence_inputs_without_authoring_qa(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    package = _sequence_package(tmp_path)
    state = read_generation_state(package)
    state.update(status="final_qa_required", selected_slides=[4])
    monkeypatch.setattr(generation, "_current_candidate", lambda *_: {
        "input_sha256": state["slides"]["4"]["input_sha256"],
        "native_outputs": {"instagram_post": {"path": "candidate.png"}},
    })
    targets = generation.build_generation_review_targets(package, state=state)
    context = json.loads((package / "creative-context.json").read_text())
    slides = json.loads((package / "slides.json").read_text())
    assert targets[0]["sequence_input_sha256"] == sequence_input_fingerprint(context, slides)
    assert targets[0]["story_plan"] == context["story_plan"]
    assert "sequence_review" not in targets[0]
    assert not (package / "visual-qa.json").exists()
