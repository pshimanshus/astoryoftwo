"""Real local feedback lifecycle; synthetic fixtures never certify image quality."""
import hashlib
import json
import subprocess
import sys
import types
from datetime import date
from pathlib import Path

import pytest

from evals.feedback_cases import (
    ensure_feedback_case,
    evaluate_feedback_case,
    load_feedback_case,
    feedback_case_path,
)
from pipeline.agentic.learning_loop import apply_learning_proposal
from pipeline.agentic.validator_registry import run_required_validators
from pipeline.agentic.memory_index import build_memory_index, search_memory
from pipeline.stages.carousel_visual_storytelling import (
    record_creator_feedback, apply_creator_feedback_revision, creator_feedback_records,
    creator_feedback_status, update_creator_feedback_event, active_feedback_constraints,
    _replace_json_pointer,
)


def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value), encoding="utf-8")


def package(root, name="couple"):
    path = root / "output/carousels/2026-09-04" / name
    write(path / "generation-state.json", {"schema_version": "carousel-generation-state/v3", "status": "draft", "slides": {}})
    write(path / "slides.json", {"slides": [{"copy": "Locked words", "physical_action": "A posed portrait"}, {"copy": "Keep me"}]})
    return path


def capture(root, path, text="Fix the action, keep the copy.\n", **kwargs):
    return record_creator_feedback(
        path, workspace_root=root, user_instruction_exact=text,
        kind="correction", scope="slide", slide_numbers=[1],
        primary_diagnosis="scene_action", must_change=["Show the shared action"],
        must_preserve=["Locked copy and second slide"],
        repair_operations=[{"artifact": "slides.json", "json_pointer": "/slides/0/physical_action", "value": "Both pull the same table toward the window."}],
        **kwargs,
    )


def test_capture_repair_eval_recall_and_retry_end_to_end(tmp_path):
    path = package(tmp_path)
    event = capture(tmp_path, path)
    assert event["user_instruction_exact"].endswith("\n")
    assert event["status"] == "diagnosed"
    assert capture(tmp_path, path)["feedback_id"] == event["feedback_id"]
    assert len(creator_feedback_records(path)) == 1
    assert evaluate_feedback_case(tmp_path, path, event)["status"] == "failed"
    result = apply_creator_feedback_revision(path, workspace_root=tmp_path, feedback_id=event["feedback_id"])
    assert result["evaluation"]["status"] == "passed"
    assert result["evaluation"]["failure_reproduced"] is True
    assert result["evaluation"]["regression_promotable"] is True
    payload = json.loads((path / "slides.json").read_text())
    assert payload["slides"][0]["copy"] == "Locked words"
    assert payload["slides"][1] == {"copy": "Keep me"}
    before = (path / "creator-correction.json").read_bytes()
    again = apply_creator_feedback_revision(path, workspace_root=tmp_path, feedback_id=event["feedback_id"])
    assert again["evaluation"] == result["evaluation"]
    assert (path / "creator-correction.json").read_bytes() == before
    assert creator_feedback_status(path, workspace_root=tmp_path)["status"] == "ready"
    hits = search_memory(build_memory_index(tmp_path), "shared action")
    assert any(event["feedback_id"] in hit.path for hit in hits)
    assert len(list(tmp_path.glob("memory/agentic/learning-events/*.json"))) == 1


def test_regression_detects_collateral_edit_and_exact_feedback_tampering(tmp_path):
    path = package(tmp_path)
    event = capture(tmp_path, path)
    result = apply_creator_feedback_revision(path, workspace_root=tmp_path, feedback_id=event["feedback_id"])
    payload = json.loads((path / "slides.json").read_text())
    payload["slides"][1]["copy"] = "Unrequested change"
    write(path / "slides.json", payload)
    ev = result["feedback"]
    failed = evaluate_feedback_case(tmp_path, path, ev)
    assert "unaffected_json_preserved" in failed["issues"]
    assert creator_feedback_status(path, workspace_root=tmp_path)["status"] == "blocked"
    ev["user_instruction_exact"] += "altered"
    with pytest.raises(ValueError, match="exact creator wording|exact feedback|SHA|hash"):
        evaluate_feedback_case(tmp_path, path, ev)


def test_hash_only_feedback_repair_is_unverified_not_a_regression_pass(tmp_path):
    path = package(tmp_path)
    event = record_creator_feedback(
        path,
        workspace_root=tmp_path,
        user_instruction_exact="Tell this from his POV.",
        kind="correction",
        scope="slide",
        slide_numbers=[1],
        primary_diagnosis="scene_action",
        must_change=["Zuv owns the scene."],
        must_preserve=["Keep the exact copy."],
        affected_artifacts=["slides.json"],
    )
    payload = json.loads((path / "slides.json").read_text())
    payload["slides"][0]["physical_action"] = "Zuv opens the old letter."
    write(path / "slides.json", payload)
    event["action_taken"] = {
        "type": "existing_package_repair",
        "artifacts_changed": ["slides.json"],
    }
    event["resolution_evidence"] = ["slides.json"]

    result = evaluate_feedback_case(tmp_path, path, event)

    assert result["status"] == "unverified"
    assert result["regression_promotable"] is False
    assert "machine_verifiable_repair_contract" in result["issues"]
    contract = next(
        check
        for check in result["checks"]
        if check["code"] == "machine_verifiable_repair_contract"
    )
    assert contract["status"] == "UNVERIFIED"
    assert "hashes alone cannot prove" in contract["reason"]


def test_explicit_waiver_can_close_feedback_without_claiming_regression_proof(tmp_path):
    path = package(tmp_path)
    event = record_creator_feedback(
        path,
        workspace_root=tmp_path,
        user_instruction_exact="Keep this as a documented exception.",
        kind="approval",
        scope="package",
        primary_diagnosis="instruction_drift",
        must_preserve=["Keep the approved route."],
        affected_artifacts=["slides.json"],
        eval_waiver_reason="Creator approved this package-specific exception.",
    )
    event["action_taken"] = {"type": "documented_eval_waiver"}
    event["resolution_evidence"] = ["creator-correction.json"]

    result = evaluate_feedback_case(tmp_path, path, event)

    assert result["status"] == "waived"
    assert result["regression_promotable"] is False
    contract = next(
        check
        for check in result["checks"]
        if check["code"] == "machine_verifiable_repair_contract"
    )
    assert contract["status"] == "WAIVED"


def test_verification_assertions_prove_current_state_without_regression_promotion(tmp_path):
    path = package(tmp_path)
    event = record_creator_feedback(
        path,
        workspace_root=tmp_path,
        user_instruction_exact="Tell this from his POV and keep the exact copy.",
        kind="correction",
        scope="slide",
        slide_numbers=[1],
        primary_diagnosis="scene_action",
        must_change=["Zuv owns the scene."],
        must_preserve=["Keep the exact copy."],
        affected_artifacts=["slides.json"],
    )
    feedback_case_path(tmp_path, event["eval_task_ids"][0]).unlink()
    event["verification_assertions"] = [
        {
            "artifact": "slides.json",
            "json_pointer": "/slides/0/physical_action",
            "operator": "contains",
            "value": "Zuv",
        },
        {
            "artifact": "slides.json",
            "json_pointer": "/slides/0/copy",
            "operator": "equals",
            "value": "Locked words",
        },
    ]
    ensure_feedback_case(tmp_path, path, event)
    payload = json.loads((path / "slides.json").read_text())
    payload["slides"][0]["physical_action"] = "Zuv opens the old letter."
    write(path / "slides.json", payload)
    event["action_taken"] = {
        "type": "existing_package_repair",
        "artifacts_changed": ["slides.json"],
    }
    event["resolution_evidence"] = ["slides.json"]

    result = evaluate_feedback_case(tmp_path, path, event)

    assert result["status"] == "passed"
    assert result["failure_reproduced"] is False
    assert result["regression_promotable"] is False
    assertion_check = next(
        check for check in result["checks"] if check["code"] == "verification_assertions"
    )
    assert assertion_check["status"] == "PASS"


def test_verification_assertion_failure_and_identity_drift_are_rejected(tmp_path):
    path = package(tmp_path)
    event = record_creator_feedback(
        path,
        workspace_root=tmp_path,
        user_instruction_exact="Make Zuv own this scene.",
        kind="correction",
        scope="slide",
        slide_numbers=[1],
        primary_diagnosis="scene_action",
        must_change=["Zuv owns the scene."],
        affected_artifacts=["slides.json"],
    )
    feedback_case_path(tmp_path, event["eval_task_ids"][0]).unlink()
    event["verification_assertions"] = [
        {
            "artifact": "slides.json",
            "json_pointer": "/slides/0/physical_action",
            "operator": "contains",
            "value": "Zuv",
        }
    ]
    ensure_feedback_case(tmp_path, path, event)
    event["action_taken"] = {"type": "existing_package_repair"}
    event["resolution_evidence"] = ["slides.json"]
    result = evaluate_feedback_case(tmp_path, path, event)
    assert result["status"] == "failed"
    assert "verification_assertions" in result["issues"]

    drifted = dict(event)
    drifted["verification_assertions"] = [
        {**event["verification_assertions"][0], "value": "Aachu"}
    ]
    with pytest.raises(ValueError, match="different identity"):
        evaluate_feedback_case(tmp_path, path, drifted)


def test_explicit_rule_is_proposed_not_auto_applied_then_creator_can_promote(tmp_path):
    path = package(tmp_path)
    target = tmp_path / "config/rules/visual-variety.md"
    target.parent.mkdir(parents=True)
    target.write_text("# Visual variety\n\nconfidence: 0.9\n")
    event = capture(tmp_path, path, text="Always show a shared physical action.")
    result = apply_creator_feedback_revision(path, workspace_root=tmp_path, feedback_id=event["feedback_id"])
    assert result["feedback"]["status"] == "learning_proposed"
    assert "Required behavior" not in target.read_text()
    proposal = next(tmp_path.glob("memory/agentic/learning-proposals/*.json"))
    with pytest.raises(ValueError, match="creator approval"):
        apply_learning_proposal(tmp_path, proposal, approved_by="agent")
    with pytest.raises(ValueError, match="creator approval"):
        apply_learning_proposal(tmp_path, proposal, approved_by="not creator")
    run_required_validators(tmp_path, proposal)
    apply_learning_proposal(tmp_path, proposal, approved_by="creator")
    assert creator_feedback_records(path)[0]["status"] == "promoted"
    assert "Required behavior: Show the shared action" in target.read_text()


def test_same_package_does_not_count_as_independent_repeated_failure(tmp_path):
    path = package(tmp_path)
    first = capture(tmp_path, path)
    apply_creator_feedback_revision(path, workspace_root=tmp_path, feedback_id=first["feedback_id"])
    # Restore the bad action to reproduce a distinct correction in this package.
    write(path / "slides.json", {"slides": [{"copy": "Locked words", "physical_action": "A posed portrait"}, {"copy": "Keep me"}]})
    second = capture(tmp_path, path, text="This action still feels posed.")
    result = apply_creator_feedback_revision(path, workspace_root=tmp_path, feedback_id=second["feedback_id"])
    assert result["feedback"]["status"] == "evaluated"
    assert not list(tmp_path.glob("memory/agentic/learning-proposals/*.json"))


def repeated_capture(root, path, text, behavior, repaired_action):
    event = record_creator_feedback(
        path,
        workspace_root=root,
        user_instruction_exact=text,
        kind="correction",
        scope="slide",
        slide_numbers=[1],
        primary_diagnosis="scene_action",
        must_change=[behavior],
        must_preserve=["Locked copy and second slide"],
        repair_operations=[{
            "artifact": "slides.json",
            "json_pointer": "/slides/0/physical_action",
            "value": repaired_action,
        }],
    )
    return apply_creator_feedback_revision(
        path,
        workspace_root=root,
        feedback_id=event["feedback_id"],
    )


def test_same_diagnosis_with_different_package_facts_does_not_propose_global_rule(tmp_path):
    target = tmp_path / "config/rules/visual-variety.md"
    target.parent.mkdir(parents=True)
    target.write_text("# Visual variety\n\nconfidence: 0.9\n")
    first = package(tmp_path, "train-story")
    second = package(tmp_path, "flight-story")

    repeated_capture(
        tmp_path,
        first,
        "Tell this train scene from Zuv's point of view.",
        "Use Zuv's point of view on the train",
        "Zuv watches the train platform recede.",
    )
    repeated_capture(
        tmp_path,
        second,
        "This needs to be a commercial flight.",
        "Use a commercial flight",
        "They fasten their seatbelts inside a commercial flight.",
    )

    assert not list(tmp_path.glob("memory/agentic/learning-proposals/*.json"))
    assert "commercial flight" not in target.read_text()
    assert "Zuv's point of view" not in target.read_text()


def test_semantically_matching_behavior_needs_independent_packages_and_dedupes(tmp_path):
    target = tmp_path / "config/rules/visual-variety.md"
    target.parent.mkdir(parents=True)
    target.write_text("# Visual variety\n\nconfidence: 0.9\n")
    first = package(tmp_path, "shared-table")
    second = package(tmp_path, "shared-box")
    third = package(tmp_path, "shared-curtain")

    first_result = repeated_capture(
        tmp_path,
        first,
        "The pose needs a real shared action.",
        "Show the shared action",
        "Both pull the table toward the window.",
    )
    second_result = repeated_capture(
        tmp_path,
        second,
        "Let both of them act together.",
        "Both partners act together",
        "They lift the same box together.",
    )
    third_result = repeated_capture(
        tmp_path,
        third,
        "Again, let both partners act together.",
        "Both partners act together",
        "They draw the same curtain together.",
    )

    proposals = list(tmp_path.glob("memory/agentic/learning-proposals/*.json"))
    proposal = json.loads(proposals[0].read_text())
    assert first_result["feedback"]["status"] == "evaluated"
    assert second_result["feedback"]["status"] == "learning_proposed"
    assert third_result["feedback"]["status"] == "evaluated"
    assert len(proposals) == 1
    assert len(proposal["supporting_package_paths"]) == 3
    assert len(proposal["supporting_event_ids"]) == 3


def test_decline_learning_cli_keeps_evaluated_correction_active(tmp_path):
    path = package(tmp_path)
    target = tmp_path / "config/rules/visual-variety.md"
    target.parent.mkdir(parents=True)
    target.write_text("# Visual variety\n\nconfidence: 0.9\n")
    event = capture(tmp_path, path, text="Always show a shared physical action.")
    result = apply_creator_feedback_revision(
        path,
        workspace_root=tmp_path,
        feedback_id=event["feedback_id"],
    )
    proposal = next(tmp_path.glob("memory/agentic/learning-proposals/*.json"))
    before = target.read_bytes()
    repo_root = Path(__file__).resolve().parents[1]

    declined = subprocess.run(
        [
            sys.executable,
            "scripts/agentic_os.py",
            "--workspace-root",
            str(tmp_path),
            "decline-learning",
            str(proposal),
            "--declined-by",
            "codex-review",
            "--reason",
            "Package-specific evidence does not justify a global rule.",
        ],
        cwd=repo_root,
        text=True,
        capture_output=True,
        check=False,
        timeout=30,
    )

    assert result["feedback"]["status"] == "learning_proposed"
    assert declined.returncode == 0, declined.stderr
    decision = json.loads(declined.stdout)
    feedback = creator_feedback_records(path)[0]
    learning_event = json.loads(next(tmp_path.glob("memory/agentic/learning-events/*.json")).read_text())
    assert decision["status"] == "rejected" and decision["decision"] == "declined"
    assert decision["declined_reason"].startswith("Package-specific evidence")
    assert feedback["status"] == "evaluated"
    assert feedback["learning_disposition"] == "declined"
    assert learning_event["feedback_status"] == "evaluated"
    assert creator_feedback_status(path, workspace_root=tmp_path)["status"] == "ready"
    assert active_feedback_constraints(path, 1)[0]["feedback_id"] == event["feedback_id"]
    assert target.read_bytes() == before


def test_supersession_excludes_old_wording_even_when_new_event_does_not_match(tmp_path):
    path = package(tmp_path)
    first = capture(tmp_path, path, text="Use a vermilion umbrella.")
    second = capture(tmp_path, path, text="Use a blue coat.", supersedes_feedback_id=first["feedback_id"])
    hits = search_memory(build_memory_index(tmp_path), "vermilion")
    assert not any(hit.path.endswith("#" + first["feedback_id"]) for hit in hits)
    assert not any(first["learning_event_id"] in hit.path for hit in hits)
    assert second["supersedes_feedback_id"] == first["feedback_id"]
    with pytest.raises(ValueError, match="existing correction"):
        capture(tmp_path, path, text="Another", supersedes_feedback_id="fb-no-such-event")


@pytest.mark.parametrize("pointer", ["/slides/-1/copy", "/slides/90/copy", "/missing", ""])
def test_repairs_cannot_replace_document_or_use_missing_or_negative_slots(pointer):
    with pytest.raises(ValueError):
        _replace_json_pointer({"slides": [{"copy": "stay"}]}, pointer, "bad")


def test_illegal_lifecycle_and_path_traversal_are_rejected(tmp_path):
    path = package(tmp_path)
    event = capture(tmp_path, path)
    with pytest.raises(ValueError, match="transition"):
        update_creator_feedback_event(path, event["feedback_id"], updates={"status": "promoted"})
    with pytest.raises(ValueError):
        feedback_case_path(tmp_path, "../../outside")


def test_backfill_preserves_exact_raw_legacy_and_media_without_waiving_live_debt(tmp_path):
    from scripts.backfill_creator_feedback import migrate
    legacy = tmp_path / "output/carousels/2026-08-14/legacy"
    original = {"creator_feedback": "keep EXACT\nwords", "extra_original_field": [1, 2]}
    write(legacy / "creator-correction.json", original)
    raw = (legacy / "creator-correction.json").read_bytes()
    (legacy / "slide.png").write_bytes(b"unchanged media")
    live = package(tmp_path)
    capture(tmp_path, live)
    live_before = (live / "creator-correction.json").read_bytes()
    report = migrate(tmp_path, date(2026, 8, 7), date(2026, 9, 4), apply=True)
    assert report["media_unchanged"] and report["media_file_count"] == 1
    normalized = json.loads((legacy / "creator-correction.json").read_text())
    assert normalized["legacy_sources"][0]["raw_utf8"].encode() == raw
    assert normalized["events"][0]["user_instruction_exact"] == original["creator_feedback"]
    assert normalized["events"][0]["historical_only"] is True
    assert (live / "creator-correction.json").read_bytes() == live_before
    before = (legacy / "creator-correction.json").read_bytes()
    migrate(tmp_path, date(2026, 8, 7), date(2026, 9, 4), apply=True)
    assert (legacy / "creator-correction.json").read_bytes() == before


@pytest.mark.parametrize(
    ("legacy_payload", "expected_exact_text"),
    [
        (
            {
                "schema_version": "1.0",
                "status": "LOCKED",
                "recorded_on": "2026-08-14",
                "corrections": [
                    {
                        "instruction": "Keep this first line exactly.\nIncluding its line break.",
                        "resolution": "Recorded without rewriting the instruction.",
                    },
                    {
                        "instruction": "Do not turn the lived moment into a generic quote card.",
                        "resolution": "The scene remains observable.",
                    },
                ],
            },
            (
                "Keep this first line exactly.\nIncluding its line break.\n"
                "Do not turn the lived moment into a generic quote card."
            ),
        ),
        (
            {
                "status": "CORRECTED_BY_CREATOR",
                "revision": 2,
                "corrections": [
                    "They travelled by car, not scooter.",
                    "Both partners participate in the same lock check.",
                ],
                "rejected_route_phrases": ["parked scooter", "two helmets"],
                "active_artifact_paths": ["slides.json", "prompt-pack.json"],
            },
            (
                "They travelled by car, not scooter.\n"
                "Both partners participate in the same lock check."
            ),
        ),
        (
            {
                "schema_version": "creator-correction/v1",
                "recorded_date": "2026-08-14",
                "status": "LOCKED",
                "correction": (
                    "Keep the creator's exact copy and replace only the rejected visual route."
                ),
                "exact_copy": [
                    {"slide": 1, "text": "We’re not married yet.\nBut try telling that to our habits."}
                ],
                "visual_story_correction": {
                    "creator_diagnosis": "The prior route made the copy serve a prop story."
                },
            },
            "Keep the creator's exact copy and replace only the rejected visual route.",
        ),
    ],
    ids=("schema-1.0-object-corrections", "unversioned-string-corrections", "creator-correction-v1"),
)
def test_backfill_normalizes_each_real_legacy_family_exactly_and_idempotently(
    tmp_path, legacy_payload, expected_exact_text
):
    from scripts.backfill_creator_feedback import migrate

    package_path = tmp_path / "output/carousels/2026-08-14/legacy-family"
    correction_path = package_path / "creator-correction.json"
    write(correction_path, legacy_payload)
    original_raw = correction_path.read_bytes()

    migrate(tmp_path, date(2026, 8, 7), date(2026, 9, 4), apply=True)

    normalized = json.loads(correction_path.read_text(encoding="utf-8"))
    assert normalized["schema_version"] == "creator-correction/v3"
    assert len(normalized["events"]) == 1
    assert normalized["events"][0]["user_instruction_exact"] == expected_exact_text
    assert normalized["legacy_sources"][0]["payload"] == legacy_payload
    assert normalized["legacy_sources"][0]["raw_utf8"].encode("utf-8") == original_raw

    normalized_raw = correction_path.read_bytes()
    migrate(tmp_path, date(2026, 8, 7), date(2026, 9, 4), apply=True)
    assert correction_path.read_bytes() == normalized_raw


def test_optional_mirror_redacts_and_fails_nonblocking(tmp_path, monkeypatch):
    from pipeline.agentic.langfuse_mirror import redacted_feedback_payload, mirror_feedback_event, candidate_event_from_annotation
    event = {"user_instruction_exact": "PRIVATE TEXT", "primary_diagnosis": "scene_action", "scope": "slide", "secondary_diagnoses": [{"bad": "PRIVATE"}], "reference_path": "/private/photo.png"}
    assert "PRIVATE" not in json.dumps(redacted_feedback_payload(event))
    monkeypatch.delenv("ASOT_LANGFUSE_ENABLED", raising=False)
    assert mirror_feedback_event(event)["status"] == "disabled"
    monkeypatch.setenv("ASOT_LANGFUSE_ENABLED", "1")
    monkeypatch.setenv("LANGFUSE_PUBLIC_KEY", "test-only")
    monkeypatch.setenv("LANGFUSE_SECRET_KEY", "test-only")
    def fail(_):
        raise RuntimeError("PRIVATE PROVIDER ERROR")
    assert mirror_feedback_event(event, exporter=fail)["status"] == "failed_nonblocking"
    exported = []
    assert mirror_feedback_event(event, exporter=exported.append)["status"] == "mirrored"
    assert len(exported) == 1
    assert candidate_event_from_annotation({"id": "test-annotation", "source": "ANNOTATION", "comment": "Exact words"})["candidate_status"] == "pending_local_review"


def test_shadow_reports_not_run_without_credentials_and_never_gates(tmp_path, monkeypatch):
    from evals.deepeval_adapter import run_deepeval_shadow
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    result = run_deepeval_shadow(tmp_path, prompt="x", actual_output="y")
    assert result["status"] == "not_run" and result["can_gate"] is False
    assert len(result["metrics"]) == 8


def test_shadow_uses_real_metric_interfaces_with_images_and_trajectory(tmp_path, monkeypatch):
    from evals.deepeval_adapter import run_deepeval_shadow
    measured = []
    class Metric:
        def __init__(self, **kwargs):
            assert kwargs["threshold"] is None
            self.score, self.reason = 0.8, "synthetic SDK contract test"
        def measure(self, case):
            measured.append(case)
    class Case:
        def __init__(self, **kwargs):
            self.__dict__.update(kwargs)
    class InputImage:
        def __init__(self, *, url, local):
            assert local
            self.url = url
        def __str__(self):
            return "<image:" + self.url + ">"
    monkeypatch.setenv("OPENAI_API_KEY", "test-only")
    monkeypatch.setenv("ASOT_DEEPEVAL_ENABLED", "1")
    monkeypatch.setenv("ASOT_DEEPEVAL_ALLOW_MEDIA", "1")
    monkeypatch.setitem(sys.modules, "deepeval.metrics", types.SimpleNamespace(GEval=Metric, ImageCoherenceMetric=Metric, TextToImageMetric=Metric))
    monkeypatch.setitem(sys.modules, "deepeval.test_case", types.SimpleNamespace(LLMTestCase=Case, LLMTestCaseParams=types.SimpleNamespace(INPUT="input", ACTUAL_OUTPUT="output"), MLLMImage=InputImage))
    (tmp_path / "image.png").write_bytes(b"fixture")
    result = run_deepeval_shadow(tmp_path, prompt="Draw", actual_output="Generated", image_paths=[str(tmp_path / "image.png")], reference_paths=[str(tmp_path / "image.png")], trajectory=[{"tool": "imagegen"}])
    assert len(measured) == 8
    assert all(item["status"] == "scored" for item in result["metrics"])
    assert "Ordered tool trajectory" in measured[0].actual_output
    assert result["can_gate"] is False


def test_calibration_requires_distinct_creator_reviewed_outputs_and_packages(tmp_path):
    from evals.deepeval_adapter import calibration_status
    for i in range(20):
        package_id = f"output/carousels/2026-09-04/package-{i % 5}"
        output_path = f"{package_id}/output-{i}.png"
        output = tmp_path / output_path
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_bytes(str(i).encode())
        write(tmp_path / f"evals/calibration/{i}.json", {"creator_reviewed": True, "output_sha256": hashlib.sha256(output.read_bytes()).hexdigest(), "package_id": package_id, "output_path": output_path, "creator_hard_fail": False, "judge_hard_fail": i < 2})
    assert calibration_status(tmp_path)["calibrated"] is False
    write(tmp_path / "evals/calibration/1.json", {"creator_reviewed": True, "output_sha256": hashlib.sha256(b"1").hexdigest(), "package_id": "output/carousels/2026-09-04/package-1", "output_path": "output/carousels/2026-09-04/package-1/output-1.png", "creator_hard_fail": False, "judge_hard_fail": False})
    assert calibration_status(tmp_path)["calibrated"] is True
    write(tmp_path / "evals/calibration/20.json", {"creator_reviewed": False, "output_sha256": "unreviewed", "package_id": "fake", "creator_hard_fail": False, "judge_hard_fail": True})
    assert calibration_status(tmp_path)["reviewed_outputs"] == 20


def test_health_rejects_advanced_empty_state_and_unresolved_corrections(tmp_path):
    from pipeline.stages.wiki_health import generation_receipt_health_evidence, feedback_health_evidence
    path = package(tmp_path)
    capture(tmp_path, path)
    assert feedback_health_evidence(tmp_path, date(2026, 9, 4))["invalid_events"]
    write(path / "generation-state.json", {"schema_version": "carousel-generation-state/v3", "status": "publish_ready", "slides": {}})
    assert generation_receipt_health_evidence(tmp_path, date(2026, 9, 4))
