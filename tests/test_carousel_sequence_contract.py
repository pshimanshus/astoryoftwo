"""Sequence intent is review input, never a synthetic visual observation."""
import copy
import json

import pytest


def story_context(mode="unfolding_question"):
    return {"sequence_contract": "carousel-sequence/v1", "story_plan": {
        "theme": "A summons becomes a request for affection.",
        "recognition": "The partner who calls across the house for no practical reason.",
        "sequence_mode": mode,
        "opening_promise": "Find out why she is calling him across the room.",
        "mismatch": "He expects a task; she wants him nearby.",
        "turn_or_accumulation": "His arrival reveals the affectionate motive.",
        "payoff": "He returns her embrace, closing the distance together.",
        "send_reason": "Tell your partner that sometimes you only want them close.",
    }}


def story_slides():
    return [
        {"slide": 1, "role": "call", "copy": "Zuv!", "copy_mode": "text",
         "beat_delta": "Her call interrupts his reading across the room.",
         "copy_image_relation": {"kind": "completion", "proof": "Her mouth faces him while he keeps his book open."},
         "physical_action": "Aachu calls across the room while Zuv lifts his eyes from a book.",
         "visual_richness": {"continuation_pull": "What does she need from him?"}},
        {"slide": 2, "role": "response", "copy": "", "copy_mode": "wordless",
         "beat_delta": "He embraces her instead of waiting for a practical request.",
         "copy_image_relation": {"kind": "wordless", "proof": "Both sets of arms close the distance in a reciprocal hug."},
         "physical_action": "Zuv wraps both arms around Aachu as she rests her cheek on his shoulder.",
         "visual_richness": {"after_frame": "They stay in the embrace without a task to complete."}},
    ]


def sequence_review(context, slides, formats=("instagram_post",)):
    from pipeline.stages.carousel_sequence import sequence_input_fingerprint
    return {"schema_version": "carousel-sequence-review/v1",
            "source_sha256": sequence_input_fingerprint(context, slides),
            "formats": {fmt: {
                "status": "PASS", "hook_observed": "Her turned head and his interrupted book establish a summons.",
                "transitions": [{"from_slide": 1, "to_slide": 2, "development_observed": "His distant attention becomes a reciprocal embrace."}],
                "copy_image": [{"slide": s["slide"], "kind": s["copy_image_relation"]["kind"], "observed": s["copy_image_relation"]["proof"]} for s in slides],
                "coherence_observed": "His book is left behind before both arms enter the embrace.",
                "redundancy_observed": "The call and physical answer each contribute a different state.",
                "closure": {"setup_slides": [1], "ending_slide": 2, "observed": "The final reciprocal hug answers why she called him over."},
                "issues": [],
            } for fmt in formats}}


@pytest.mark.parametrize("mode", ["unfolding_question", "recognition_rewards", "accumulating_evidence", "relationship_change", "hybrid", "creator_defined"])
def test_sequence_modes_do_not_force_a_single_plot(mode):
    from pipeline.stages.carousel_sequence import sequence_plan_issues
    assert sequence_plan_issues(story_context(mode), story_slides()) == []


def test_wordlessness_requires_explicit_intent():
    from pipeline.stages.carousel_sequence import copy_issue
    assert copy_issue({"copy": "", "copy_mode": "wordless"}) is None
    assert copy_issue({"copy": ""})
    assert copy_issue({"copy": "invented words", "copy_mode": "wordless"})
    assert copy_issue({"copy": "a line", "copy_mode": "typo"})


@pytest.mark.parametrize("kind", [[], {}, 7, None])
def test_malformed_relation_returns_a_validation_issue(kind):
    from pipeline.stages.carousel_sequence import slide_sequence_issues
    row = story_slides()[0]
    row["copy_image_relation"]["kind"] = kind
    assert slide_sequence_issues(row)


def test_review_fingerprint_covers_story_order_and_semantics_but_not_research():
    from pipeline.stages.carousel_sequence import sequence_input_fingerprint
    ctx, slides = story_context(), story_slides()
    original = sequence_input_fingerprint(ctx, slides)
    ctx["research_refs"] = ["a new source annotation"]
    assert sequence_input_fingerprint(ctx, slides) == original
    assert sequence_input_fingerprint(ctx, list(reversed(slides))) != original
    ctx["story_plan"]["payoff"] = "A different final meaning."
    assert sequence_input_fingerprint(ctx, slides) != original


def test_complete_review_passes_and_missing_or_stale_review_fails():
    from pipeline.stages.carousel_sequence import sequence_review_issues
    ctx, slides = story_context(), story_slides()
    qa = sequence_review(ctx, slides)
    assert sequence_review_issues(ctx, slides, qa, ["instagram_post"]) == []
    assert sequence_review_issues(ctx, slides, None, ["instagram_post"])
    ctx["story_plan"]["opening_promise"] = "A new promise about a different request."
    assert any("stale" in s for s in sequence_review_issues(ctx, slides, qa, ["instagram_post"]))


@pytest.mark.parametrize("mutation", ["transition", "duplicate", "relation", "closure", "failure", "format"])
def test_sequence_review_cannot_hide_gaps(mutation):
    from pipeline.stages.carousel_sequence import sequence_review_issues
    ctx, slides = story_context(), story_slides()
    qa = sequence_review(ctx, slides)
    review = qa["formats"]["instagram_post"]
    if mutation == "transition": review["transitions"] = []
    if mutation == "duplicate": review["copy_image"][1] = copy.deepcopy(review["copy_image"][0])
    if mutation == "relation": review["copy_image"][1]["kind"] = "completion"
    if mutation == "closure": review["closure"]["ending_slide"] = 1
    if mutation == "failure": review["issues"] = ["The embrace does not answer the summons."]
    if mutation == "format": qa["formats"]["square"] = copy.deepcopy(review)
    assert sequence_review_issues(ctx, slides, qa, ["instagram_post"])


def test_new_contract_cannot_downgrade_itself_by_removing_story_plan():
    from pipeline.stages.carousel_sequence import sequence_plan_issues
    assert sequence_plan_issues({"sequence_contract": "carousel-sequence/v1"}, story_slides())


def test_final_pixel_gate_requires_sequence_review_for_current_story_contract(tmp_path):
    from tests.test_carousel_pixel_qa import _package, _manifest, _binding, _final_qa
    from pipeline.stages.carousel_pixel_qa import bind_final_qa, validate_final_qa
    package = _package(tmp_path)
    ctx = json.loads((package / "creative-context.json").read_text())
    ctx.update(story_context())
    (package / "creative-context.json").write_text(json.dumps(ctx))
    # Existing frame fixture remains valid. The new story-level evidence is absent.
    manifest = _manifest(package, _binding(package))
    qa = _final_qa(package, manifest)
    assert any("sequence" in issue for issue in validate_final_qa(package, qa, manifest))


def test_current_analyzer_uses_story_contract_and_advisory_scores(tmp_path):
    from pipeline.stages.carousel_intelligence import analyze_package
    package = tmp_path / "package"
    package.mkdir()
    (package / "creative-context.json").write_text(json.dumps(story_context("recognition_rewards")))
    (package / "slides.json").write_text(json.dumps(story_slides()))
    report = analyze_package(package, root=tmp_path)
    assert report["concept_gate"]["status"] == "passed"
    assert report["heuristic"]["blocking"] is False
    assert report["concept_gate"]["pixel_review_status"] == "not_run"
    assert report["sequence"]["mode"] == "recognition_rewards"
    assert "copy_visual_alignment" not in report["concept_gate"]["gates"]


def test_concept_pass_expires_when_story_intention_changes(tmp_path):
    from pipeline.stages.carousel_intelligence import analyze_and_write, require_concept_gate
    package = tmp_path / "package"
    package.mkdir()
    context = story_context()
    (package / "creative-context.json").write_text(json.dumps(context))
    (package / "slides.json").write_text(json.dumps(story_slides()))
    analyze_and_write(package, root=tmp_path)
    assert require_concept_gate(package)["concept_gate"]["status"] == "passed"
    context["story_plan"]["payoff"] = "He returns to the book rather than the embrace."
    (package / "creative-context.json").write_text(json.dumps(context))
    with pytest.raises(ValueError, match="stale"):
        require_concept_gate(package)


def test_new_cli_brief_cannot_skip_story_plan(tmp_path):
    from tests.test_carousel_cli import _write_brief, _run
    brief = _write_brief(tmp_path / "brief.json")
    payload = json.loads(brief.read_text())
    payload.pop("story_plan", None)
    for row in payload["slides"]:
        row.pop("beat_delta", None)
        row.pop("copy_image_relation", None)
    brief.write_text(json.dumps(payload))
    result = _run("create", "--story", "Learning a shared route.", "--creative-brief", str(brief), "--output-root", str(tmp_path / "output"))
    body = json.loads(result.stdout)
    assert body["state"] == "blocked"
    assert body["next_action"] == "define_story_plan"
