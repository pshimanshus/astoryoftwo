"""Regression evidence for feedback repair, targeting, and health truth."""
import hashlib
import json
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from datetime import date
from pathlib import Path
from threading import Barrier

from pipeline.agentic.learning_loop import learning_debt_records
from pipeline.stages.carousel_visual_storytelling import (
    active_feedback_constraints, apply_creator_feedback_revision,
    creator_feedback_records, creator_feedback_status, record_creator_feedback,
    retire_successor_feedback, revise_creator_feedback_assertions,
    successor_feedback_retirement_status, update_creator_feedback_event,
)
from pipeline.stages.wiki_health import feedback_health_evidence
from evals.feedback_cases import revise_feedback_case_assertions


def write(path, payload):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload))


def package(root, name="couple"):
    path = root / "output/carousels/2026-09-04" / name
    write(path / "generation-state.json", {"schema_version": "carousel-generation-state/v3", "slides": {}, "status": "draft"})
    write(path / "slides.json", {"slides": [{"physical_action": "Zuv opens the letter", "copy": "Keep exactly"}]})
    return path


def capture(root, path, **extra):
    exact = extra.pop(
        "user_instruction_exact",
        "Approved; use the umbrella after the argument.",
    )
    return record_creator_feedback(path, workspace_root=root,
        user_instruction_exact=exact,
        kind="approval", scope="package", must_change=["Slide 1 uses the umbrella."],
        primary_diagnosis="scene_action", affected_artifacts=["slides.json"], **extra)


def adopt(root, successor, source, source_event):
    event = capture(root, successor)
    provenance = {
        "source_feedback_id": source_event["feedback_id"],
        "source_package_path": source.relative_to(root).as_posix(),
        "source_learning_event_id": source_event["learning_event_id"],
        "source_user_instruction_sha256": source_event["user_instruction_sha256"],
    }
    update_creator_feedback_event(
        successor,
        event["feedback_id"],
        updates={"adoption_provenance": provenance},
    )
    document = json.loads((successor / "creator-correction.json").read_text())
    document["successor_adoption"] = {
        "source_package_path": source.relative_to(root).as_posix(),
        "carried_feedback_ids": [event["feedback_id"]],
        "source_feedback_ids": [source_event["feedback_id"]],
    }
    write(successor / "creator-correction.json", document)
    return creator_feedback_records(successor)[0]


def test_approval_with_work_remains_unresolved_and_targeted(tmp_path):
    path = package(tmp_path)
    event = capture(tmp_path, path)
    assert active_feedback_constraints(path, 1)[0]["must_change"] == event["must_change"]
    assert active_feedback_constraints(path, 2) == []
    assert creator_feedback_status(path, workspace_root=tmp_path)["unresolved_feedback_ids"] == [event["feedback_id"]]
    assert feedback_health_evidence(tmp_path, date(2026, 9, 5))["invalid_events"]


def test_slide_clauses_do_not_cross_contaminate_and_exact_text_is_unchanged(tmp_path):
    path = package(tmp_path)
    event = capture(tmp_path, path)
    update_creator_feedback_event(path, event["feedback_id"], updates={
        "must_change": ["Slide 5 removes the extra hand.", "Slide 6 uses one umbrella grip."],
        "must_preserve": ["Keep the locked copy.", "Slide 6 preserves the rain."],
    })
    assert active_feedback_constraints(path, 5)[0]["must_change"] == ["Slide 5 removes the extra hand."]
    assert active_feedback_constraints(path, 5)[0]["must_preserve"] == ["Keep the locked copy."]
    assert active_feedback_constraints(path, 6)[0]["must_change"] == ["Slide 6 uses one umbrella grip."]
    assert active_feedback_constraints(path, 10)[0]["must_change"] == []
    assert active_feedback_constraints(path, 10)[0]["must_preserve"] == ["Keep the locked copy."]
    assert creator_feedback_records(path)[0]["user_instruction_exact"] == event["user_instruction_exact"]


def test_legacy_declined_feedback_can_revise_assertions_without_faking_artifact_edit(tmp_path):
    path = package(tmp_path)
    event = capture(tmp_path, path)
    document = json.loads((path / "creator-correction.json").read_text())
    document["events"][0]["status"] = "learning_declined"
    write(path / "creator-correction.json", document)
    original = (path / "slides.json").read_bytes()
    revised = revise_creator_feedback_assertions(path, workspace_root=tmp_path,
        feedback_id=event["feedback_id"], revised_by="codex", reason="Verify actual narrator ownership",
        verification_assertions=[{"artifact": "slides.json", "json_pointer": "/slides/0/physical_action", "operator": "contains", "value": "Zuv"}])
    assert revised["status"] == "pending"
    result = apply_creator_feedback_revision(path, workspace_root=tmp_path, feedback_id=event["feedback_id"])
    assert result["evaluation"]["status"] == "passed"
    assert result["evaluation"]["regression_promotable"] is False
    assert result["feedback"]["learning_disposition"] == "declined"
    assert result["feedback"]["action_taken"]["type"] == "verification_of_current_state"
    assert (path / "slides.json").read_bytes() == original


def test_assertion_revision_retry_repairs_partial_case_first_commit(tmp_path):
    path = package(tmp_path)
    event = capture(tmp_path, path)
    assertions = [{
        "artifact": "slides.json",
        "json_pointer": "/slides/0/physical_action",
        "operator": "contains",
        "value": "Zuv",
    }]
    committed_case = revise_feedback_case_assertions(
        tmp_path,
        path,
        event,
        assertions,
        revised_by="codex",
        reason="Simulate the eval case committing before the event write.",
    )

    recovered = revise_creator_feedback_assertions(
        path,
        workspace_root=tmp_path,
        feedback_id=event["feedback_id"],
        verification_assertions=assertions,
        revised_by="codex",
        reason="Retry the same revision after the partial commit.",
    )

    assert recovered["verification_contract_revision"] == 2
    assert len(recovered["verification_contract_history"]) == 1
    assert recovered["verification_contract_sha256"] == committed_case[
        "verification_contract_sha256"
    ]
    saved = creator_feedback_records(path)[0]
    assert saved["verification_assertions"] == assertions
    assert saved["eval_task_ids"] == [recovered["task_id"]]
    try:
        revise_feedback_case_assertions(
            tmp_path,
            path,
            saved,
            assertions,
            revised_by="codex",
            reason="A synchronized no-op must still be rejected.",
        )
    except ValueError as exc:
        assert "does not change" in str(exc)
    else:
        raise AssertionError("a synchronized no-op revision was accepted")


def test_health_and_debt_report_same_live_readonly_feedback(tmp_path):
    path = package(tmp_path)
    write(path / "generation-state.json", {"schema_version": "carousel-generation-state/v2"})
    event = capture(tmp_path, path)
    health = feedback_health_evidence(tmp_path, date.today())
    assert len(health["unresolved_records"]) == 1
    debt = learning_debt_records(tmp_path, limit=100)
    assert len(debt) == 1 and debt[0]["kind"] == "feedback_repair"
    assert event["feedback_id"] in debt[0]["line"]


def test_source_debt_is_carried_only_by_matching_successor(tmp_path):
    source = package(tmp_path, "old")
    write(source / "generation-state.json", {"schema_version": "carousel-generation-state/v2"})
    event = capture(tmp_path, source)
    successor = package(tmp_path, "new")
    adopted = capture(tmp_path, successor)
    update_creator_feedback_event(successor, adopted["feedback_id"], updates={"adoption_provenance": {
        "source_feedback_id": event["feedback_id"], "source_package_path": source.relative_to(tmp_path).as_posix(),
        "source_learning_event_id": event["learning_event_id"],
    }})
    health = feedback_health_evidence(tmp_path, date.today())
    assert len(health["unresolved_records"]) == 1
    assert health["unresolved_records"][0]["feedback_id"] == adopted["feedback_id"]
    assert health["carried_forward"][0]["feedback_id"] == event["feedback_id"]
    document = json.loads((successor / "creator-correction.json").read_text())
    document["events"][0]["user_instruction_sha256"] = "sha256:" + hashlib.sha256(b"other words").hexdigest()
    write(successor / "creator-correction.json", document)
    assert len(feedback_health_evidence(tmp_path, date.today())["unresolved_records"]) == 2


def test_explicit_successor_retirement_removes_duplicate_debt_and_keeps_lineage(tmp_path):
    from pipeline.agentic.memory_index import build_memory_index, search_memory

    source = package(tmp_path, "archived-source")
    source_event = capture(tmp_path, source)
    write(source / "generation-state.json", {"schema_version": "carousel-generation-state/v2"})
    retired = package(tmp_path, "duplicate-successor")
    active = package(tmp_path, "named-successor")
    retired_event = adopt(tmp_path, retired, source, source_event)
    active_event = adopt(tmp_path, active, source, source_event)
    media = retired / "final" / "slide-01.png"
    media.parent.mkdir(parents=True)
    media.write_bytes(b"preserved-media")
    events_before = json.loads((retired / "creator-correction.json").read_text())["events"]
    state_before = (retired / "generation-state.json").read_bytes()

    result = retire_successor_feedback(
        retired,
        workspace_root=tmp_path,
        superseded_by=active,
        retired_by="creator",
        reason_exact="This duplicate route is superseded by the named successor.",
    )
    retry = retire_successor_feedback(
        retired,
        workspace_root=tmp_path,
        superseded_by=active,
        retired_by="creator",
        reason_exact="This duplicate route is superseded by the named successor.",
    )

    saved = json.loads((retired / "creator-correction.json").read_text())
    assert result["retired"] is True and result["carried_feedback_count"] == 1
    assert retry["idempotent"] is True
    assert saved["events"] == events_before
    assert saved["events"][0]["status"] == retired_event["status"] == "diagnosed"
    assert creator_feedback_records(active)[0]["status"] == active_event["status"] == "diagnosed"
    assert (retired / "generation-state.json").read_bytes() == state_before
    assert media.read_bytes() == b"preserved-media"
    assert saved["successor_retirement"]["production_state_effect"] == "none"

    health = feedback_health_evidence(tmp_path, date.today())
    assert [item["feedback_id"] for item in health["unresolved_records"]] == [
        active_event["feedback_id"]
    ]
    assert health["retired_successors"][0]["package_path"] == retired.relative_to(tmp_path).as_posix()
    assert health["retired_successors"][0]["superseded_by_package_path"] == active.relative_to(tmp_path).as_posix()
    debt = learning_debt_records(tmp_path, limit=100)
    assert len(debt) == 1
    assert active_event["learning_event_id"] in debt[0]["line"]

    hits = search_memory(build_memory_index(tmp_path), "umbrella argument", limit=20)
    retired_path = retired.relative_to(tmp_path).as_posix()
    assert hits
    assert all(retired_path not in hit.path for hit in hits)


def test_successor_retirement_fails_closed_when_target_does_not_carry_lineage(tmp_path):
    source = package(tmp_path, "archived-source")
    source_event = capture(tmp_path, source)
    retired = package(tmp_path, "duplicate-successor")
    target = package(tmp_path, "unrelated-successor")
    adopt(tmp_path, retired, source, source_event)
    unrelated_source = package(tmp_path, "other-source")
    unrelated_event = capture(tmp_path, unrelated_source)
    adopt(tmp_path, target, unrelated_source, unrelated_event)

    try:
        retire_successor_feedback(
            retired,
            workspace_root=tmp_path,
            superseded_by=target,
            retired_by="creator",
            reason_exact="Retire this duplicate.",
        )
    except ValueError as exc:
        assert "does not carry every live feedback origin" in str(exc)
    else:
        raise AssertionError("unrelated successor was allowed to hide feedback debt")
    assert "successor_retirement" not in json.loads(
        (retired / "creator-correction.json").read_text()
    )


def test_tampered_retirement_is_invalid_and_reactivates_debt(tmp_path):
    source = package(tmp_path, "archived-source")
    source_event = capture(tmp_path, source)
    retired = package(tmp_path, "duplicate-successor")
    active = package(tmp_path, "named-successor")
    retired_event = adopt(tmp_path, retired, source, source_event)
    adopt(tmp_path, active, source, source_event)
    retire_successor_feedback(
        retired,
        workspace_root=tmp_path,
        superseded_by=active,
        retired_by="creator",
        reason_exact="Retire this duplicate.",
    )
    document = json.loads((retired / "creator-correction.json").read_text())
    document["successor_retirement"]["carried_feedback_lineage"] = []
    write(retired / "creator-correction.json", document)

    status = successor_feedback_retirement_status(retired, workspace_root=tmp_path)
    health = feedback_health_evidence(tmp_path, date.today())

    assert status["retired"] is False
    assert any("lineage no longer matches" in issue for issue in status["issues"])
    assert retired_event["feedback_id"] in {
        item["feedback_id"] for item in health["unresolved_records"]
    }
    assert any(
        "invalid successor retirement" in issue
        for issues in health["invalid_events"].values()
        for issue in issues
    )


def test_retire_successor_feedback_cli_requires_named_target(tmp_path):
    source = package(tmp_path, "archived-source")
    source_event = capture(tmp_path, source)
    retired = package(tmp_path, "duplicate-successor")
    active = package(tmp_path, "named-successor")
    adopt(tmp_path, retired, source, source_event)
    adopt(tmp_path, active, source, source_event)
    repo = Path(__file__).resolve().parents[1]
    command = [
        sys.executable,
        "scripts/agentic_os.py",
        "--workspace-root",
        str(tmp_path),
        "retire-successor-feedback",
        retired.relative_to(tmp_path).as_posix(),
        "--superseded-by",
        active.relative_to(tmp_path).as_posix(),
        "--retired-by",
        "creator",
        "--reason",
        "This duplicate is replaced by the explicitly named successor.",
    ]

    result = subprocess.run(
        command,
        cwd=repo,
        capture_output=True,
        text=True,
        check=False,
        timeout=30,
    )

    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    assert payload["retired"] is True
    assert payload["superseded_by_package_path"] == active.relative_to(tmp_path).as_posix()
    assert payload["carried_feedback_count"] == 1


def test_annotation_cli_import_is_idempotent_candidate_only(tmp_path):
    input_path = tmp_path / "annotations.json"
    write(input_path, {"data": [{"id": "annotation-1", "source": "ANNOTATION", "comment": " Exact words\n"}]})
    command = [sys.executable, "scripts/agentic_os.py", "--workspace-root", str(tmp_path),
               "import-feedback-annotations", str(input_path)]
    repo = Path(__file__).resolve().parents[1]
    first = subprocess.run(command, cwd=repo, capture_output=True, text=True, check=True)
    second = subprocess.run(command, cwd=repo, capture_output=True, text=True, check=True)
    assert json.loads(first.stdout)["candidate_count"] == 1
    assert json.loads(second.stdout)["duplicate_count"] == 1
    events = list(tmp_path.glob("memory/agentic/learning-events/*.json"))
    assert len(events) == 1
    saved = json.loads(events[0].read_text())
    assert saved["source"] == "langfuse_annotation_candidate"
    assert saved["user_instruction_exact"] == " Exact words\n"
    assert saved["eval_disposition"] == "candidate_only"
    assert not list(tmp_path.glob("output/**/creator-correction.json"))
    assert not list(tmp_path.glob("memory/agentic/learning-proposals/*.json"))


def test_annotation_cli_dry_run_does_not_persist(tmp_path):
    input_path = tmp_path / "annotations.json"
    write(input_path, [{"id": "annotation-1", "source": "ANNOTATION", "comment": "Review this"}])
    result = subprocess.run([sys.executable, "scripts/agentic_os.py", "--workspace-root", str(tmp_path),
        "import-feedback-annotations", str(input_path), "--dry-run"],
        cwd=Path(__file__).resolve().parents[1], capture_output=True, text=True, check=True)
    assert json.loads(result.stdout)["persistence"] == "dry_run"
    assert not (tmp_path / "memory").exists()


def test_event_repair_contract_drift_revokes_status_and_health(tmp_path):
    path = package(tmp_path)
    event = record_creator_feedback(path, workspace_root=tmp_path,
        user_instruction_exact="Fix his action.", kind="correction", scope="slide", slide_numbers=[1],
        must_change=["Zuv waits"], primary_diagnosis="scene_action",
        repair_operations=[{"artifact": "slides.json", "json_pointer": "/slides/0/physical_action", "value": "Zuv waits"}])
    apply_creator_feedback_revision(path, workspace_root=tmp_path, feedback_id=event["feedback_id"])
    assert creator_feedback_status(path, workspace_root=tmp_path)["status"] == "ready"
    update_creator_feedback_event(path, event["feedback_id"], updates={
        "repair_operations": [{"artifact": "slides.json", "json_pointer": "/slides/0/physical_action", "value": "Aachu returns"}]})
    assert creator_feedback_status(path, workspace_root=tmp_path)["status"] == "blocked"
    assert feedback_health_evidence(tmp_path, date(2026, 9, 5))["invalid_events"]


def test_removed_resolution_evidence_revokes_ready_status(tmp_path):
    path = package(tmp_path)
    event = record_creator_feedback(
        path,
        workspace_root=tmp_path,
        user_instruction_exact="Keep Zuv as the visible actor.",
        kind="correction",
        scope="slide",
        slide_numbers=[1],
        must_change=["Zuv remains the actor."],
        primary_diagnosis="scene_action",
        verification_assertions=[{
            "artifact": "slides.json",
            "json_pointer": "/slides/0/physical_action",
            "operator": "contains",
            "value": "Zuv",
        }],
    )
    apply_creator_feedback_revision(
        path,
        workspace_root=tmp_path,
        feedback_id=event["feedback_id"],
    )
    assert creator_feedback_status(path, workspace_root=tmp_path)["status"] == "ready"

    update_creator_feedback_event(
        path,
        event["feedback_id"],
        updates={"resolution_evidence": []},
    )

    assert creator_feedback_status(path, workspace_root=tmp_path)["status"] == "blocked"


def test_future_successor_cannot_hide_current_source_debt(tmp_path):
    source = package(tmp_path, "old")
    event = capture(tmp_path, source)
    successor = package(tmp_path, "future")
    adopted = capture(tmp_path, successor)
    update_creator_feedback_event(successor, adopted["feedback_id"], updates={"adoption_provenance": {
        "source_feedback_id": event["feedback_id"], "source_package_path": source.relative_to(tmp_path).as_posix()}})
    destination = tmp_path / "output/carousels/2099-01-01/future"
    destination.parent.mkdir(parents=True)
    successor.rename(destination)
    health = feedback_health_evidence(tmp_path, date(2026, 9, 5))
    assert not health["carried_forward"]
    assert health["unresolved_records"][0]["feedback_id"] == event["feedback_id"]


def test_adoption_cycle_cannot_retire_both_repairs(tmp_path):
    first, second = package(tmp_path, "one"), package(tmp_path, "two")
    a, b = capture(tmp_path, first), capture(tmp_path, second)
    for path, event, source, source_event in [(first, a, second, b), (second, b, first, a)]:
        update_creator_feedback_event(path, event["feedback_id"], updates={"adoption_provenance": {
            "source_feedback_id": source_event["feedback_id"], "source_package_path": source.relative_to(tmp_path).as_posix()}})
    health = feedback_health_evidence(tmp_path, date(2026, 9, 5))
    assert not health["carried_forward"]
    assert len(health["unresolved_records"]) == 2


def test_adoption_does_not_mistake_taxonomy_for_cause(tmp_path):
    from pipeline.stages.codex_native_carousel import _unresolved_feedback_record

    path = package(tmp_path)
    event = capture(tmp_path, path)
    event["root_cause"] = "scene_action"
    adopted = _unresolved_feedback_record(event, source_package_path="output/carousels/2026-09-04/old",
        origin="creator_correction", source_learning_event_id=event["learning_event_id"])
    assert adopted["root_cause"] != "scene_action"
    assert "Required repair: Slide 1 uses the umbrella." in adopted["root_cause"]


def test_successor_retirement_chain_requires_one_valid_active_leaf(tmp_path):
    source = package(tmp_path, "chain-source")
    source_event = capture(tmp_path, source)
    first = package(tmp_path, "chain-a")
    second = package(tmp_path, "chain-b")
    leaf = package(tmp_path, "chain-c")
    first_event = adopt(tmp_path, first, source, source_event)
    second_event = adopt(tmp_path, second, source, source_event)
    leaf_event = adopt(tmp_path, leaf, source, source_event)

    retire_successor_feedback(
        first, workspace_root=tmp_path, superseded_by=second,
        retired_by="creator", reason_exact="A is replaced by B.",
    )
    retire_successor_feedback(
        second, workspace_root=tmp_path, superseded_by=leaf,
        retired_by="creator", reason_exact="B is replaced by C.",
    )

    first_status = successor_feedback_retirement_status(first, workspace_root=tmp_path)
    assert first_status["retired"] is True
    assert first_status["active_leaf_package_path"] == leaf.relative_to(tmp_path).as_posix()
    health = feedback_health_evidence(tmp_path, date.today())
    assert {item["package_path"] for item in health["retired_successors"]} == {
        first.relative_to(tmp_path).as_posix(),
        second.relative_to(tmp_path).as_posix(),
    }
    assert [item["feedback_id"] for item in health["unresolved_records"]] == [
        leaf_event["feedback_id"]
    ]

    (leaf / "creator-correction.json").unlink()
    assert successor_feedback_retirement_status(first, workspace_root=tmp_path)["retired"] is False
    assert successor_feedback_retirement_status(second, workspace_root=tmp_path)["retired"] is False
    broken_health = feedback_health_evidence(tmp_path, date.today())
    unresolved = {item["feedback_id"] for item in broken_health["unresolved_records"]}
    assert {first_event["feedback_id"], second_event["feedback_id"]}.issubset(unresolved)


def test_inverse_retirement_race_serializes_and_cannot_commit_cycle(tmp_path):
    source = package(tmp_path, "race-source")
    source_event = capture(tmp_path, source)
    first = package(tmp_path, "race-a")
    second = package(tmp_path, "race-b")
    adopt(tmp_path, first, source, source_event)
    adopt(tmp_path, second, source, source_event)
    barrier = Barrier(2)

    def attempt(source_package, target_package, reason):
        barrier.wait(timeout=5)
        try:
            return retire_successor_feedback(
                source_package,
                workspace_root=tmp_path,
                superseded_by=target_package,
                retired_by="creator",
                reason_exact=reason,
            )
        except ValueError as exc:
            return exc

    with ThreadPoolExecutor(max_workers=2) as executor:
        outcomes = [
            executor.submit(attempt, first, second, "A is replaced by B."),
            executor.submit(attempt, second, first, "B is replaced by A."),
        ]
        results = [outcome.result(timeout=10) for outcome in outcomes]

    assert sum(isinstance(result, dict) for result in results) == 1
    assert sum(isinstance(result, ValueError) for result in results) == 1
    statuses = [
        successor_feedback_retirement_status(path, workspace_root=tmp_path)
        for path in (first, second)
    ]
    assert sum(status["retired"] for status in statuses) == 1
    assert all(
        not any("cycle" in issue for issue in status.get("issues", []))
        for status in statuses
    )


def test_retirement_binds_historical_exact_history_and_canonical_origin(tmp_path):
    source = package(tmp_path, "origin-source")
    source_event = capture(tmp_path, source)
    retired = package(tmp_path, "history-a")
    active = package(tmp_path, "history-b")
    adopt(tmp_path, retired, source, source_event)
    adopt(tmp_path, active, source, source_event)
    historical = capture(
        tmp_path,
        retired,
        user_instruction_exact="Historical note must remain exact.",
    )
    document = json.loads((retired / "creator-correction.json").read_text())
    history_event = next(
        item for item in document["events"] if item["feedback_id"] == historical["feedback_id"]
    )
    history_event["historical_only"] = True
    history_event["status"] = "evaluated"
    write(retired / "creator-correction.json", document)
    retire_successor_feedback(
        retired, workspace_root=tmp_path, superseded_by=active,
        retired_by="creator", reason_exact="The live correction moved to B.",
    )

    document = json.loads((retired / "creator-correction.json").read_text())
    history_event = next(
        item for item in document["events"] if item["feedback_id"] == historical["feedback_id"]
    )
    history_event["user_instruction_exact"] = "Changed historical words."
    history_event["user_instruction_sha256"] = "sha256:" + hashlib.sha256(
        history_event["user_instruction_exact"].encode()
    ).hexdigest()
    write(retired / "creator-correction.json", document)
    status = successor_feedback_retirement_status(retired, workspace_root=tmp_path)
    assert status["retired"] is False
    assert any("document changed" in issue for issue in status["issues"])

    # Restore the retired package, then prove that changing the claimed origin
    # also invalidates retirement even though the retired bytes are untouched.
    history_event["user_instruction_exact"] = "Historical note must remain exact."
    history_event["user_instruction_sha256"] = "sha256:" + hashlib.sha256(
        history_event["user_instruction_exact"].encode()
    ).hexdigest()
    write(retired / "creator-correction.json", document)
    origin = json.loads((source / "creator-correction.json").read_text())
    origin["events"][0]["user_instruction_exact"] = "Tampered origin words."
    origin["events"][0]["user_instruction_sha256"] = "sha256:" + hashlib.sha256(
        origin["events"][0]["user_instruction_exact"].encode()
    ).hexdigest()
    write(source / "creator-correction.json", origin)
    status = successor_feedback_retirement_status(retired, workspace_root=tmp_path)
    assert status["retired"] is False
    assert any("origin exact text" in issue for issue in status["issues"])
