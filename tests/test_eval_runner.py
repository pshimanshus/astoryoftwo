import hashlib
from pathlib import Path

from evals.checkers.diff_guard import check_changed_paths
from evals.checkers.report import score_checks
from evals.checkers.rubric import run_rubric_checkers
from evals.review import review_suite_once
from evals.runner import main, prepare_task_fixture_by_id, run_task_checks, select_tasks
from evals.schemas import CheckResult, EvalTask, PassCriteria, discover_tasks


ROOT = Path(__file__).resolve().parents[1]


def _task() -> EvalTask:
    return EvalTask(
        schema_version="1.0",
        id="ASTO-999",
        title="Synthetic task",
        category="instruction_drift",
        difficulty="easy",
        suites=["smoke"],
        prompt="prompt.md",
        starting_state=["A dependent instruction surface contains drift."],
        done_when=["The drift is repaired without touching AGENTS.md."],
        allowed_paths=["config/**", "tests/**"],
        forbidden_paths=["AGENTS.md", ".env*", "identity_images/**", "output/**/final/**"],
        expected_files_changed=["config/rules/brandmark.md", "tests/test_instruction_surface_contract.py"],
        forbidden_changes=["Do not edit AGENTS.md."],
        required_commands=[],
        deterministic_checkers=["diff_guard"],
        rubric_checkers=[],
        pass_criteria=PassCriteria(),
        anti_gaming_notes=["Do not weaken tests."],
        task_dir=ROOT / "evals" / "tasks" / "ASTO-999",
    )


def test_diff_guard_blocks_forbidden_and_out_of_scope_paths() -> None:
    task = _task()

    results = check_changed_paths(
        task,
        [
            "config/rules/brandmark.md",
            "AGENTS.md",
            "scripts/unrelated.py",
            "output/carousels/demo/final/slide-01.png",
        ],
    )

    failed = {result.code: result for result in results if result.status == "FAIL"}
    assert failed["forbidden_path"].severity == "critical"
    assert failed["path_outside_allowed_scope"].severity == "major"


def test_diff_guard_always_protects_eval_harness() -> None:
    task = _task()

    results = check_changed_paths(
        task,
        ["config/rules/brandmark.md", "evals/checkers/task_specific.py"],
    )

    failed = {result.code: result for result in results if result.status == "FAIL"}
    assert failed["eval_harness_protected"].severity == "critical"
    assert failed["eval_harness_protected"].evidence == [
        "evals/checkers/task_specific.py"
    ]


def test_score_checks_requires_zero_critical_and_major_failures() -> None:
    task = _task()

    report = score_checks(
        task,
        [
            CheckResult(
                code="metadata",
                status="PASS",
                severity="info",
                message="metadata ok",
            ),
            CheckResult(
                code="path_outside_allowed_scope",
                status="FAIL",
                severity="major",
                message="outside scope",
            ),
        ],
    )

    assert report.resolved is False
    assert report.summary["major_failures"] == 1
    assert report.score < 1.0


def test_select_tasks_by_suite_and_id() -> None:
    tasks = discover_tasks(ROOT)

    smoke = select_tasks(tasks, suite="smoke")
    first = select_tasks(tasks, task_id=tasks[0].id)

    assert smoke
    assert all("smoke" in task.suites for task in smoke)
    assert first == [tasks[0]]


def test_prepare_task_fixture_by_id_materializes_overlay(tmp_path: Path) -> None:
    written = prepare_task_fixture_by_id(
        ROOT,
        "ASTO-003-textless-prompt",
        tmp_path,
    )

    written_paths = {path.relative_to(tmp_path).as_posix() for path in written}
    assert ".eval/ASTO-003-textless-prompt-prompt.md" in written_paths
    assert (
        "output/carousels/fixtures/textless-prompt/prompt-pack.json"
        in written_paths
    )


def test_run_task_checks_executes_named_task_specific_checker(tmp_path: Path) -> None:
    task = next(task for task in discover_tasks(ROOT) if task.id == "ASTO-001-brandmark-drift")
    prepare_task_fixture_by_id(ROOT, task.id, tmp_path)

    report = run_task_checks(
        task,
        tmp_path,
        skip_commands=True,
        explicit_changed_paths=["config/rules/brandmark.md"],
    )

    checks = {check.code: check for check in report.checks}
    assert report.resolved is False
    assert checks["brandmark_top_right_rule"].status == "FAIL"


def test_run_task_checks_executes_declared_rubric_checker(tmp_path: Path) -> None:
    task = next(
        task
        for task in discover_tasks(ROOT)
        if task.id == "ASTO-011-small-brief-no-framework-dump"
    )
    brief = tmp_path / "output" / "evals" / "ASTO-011" / "creator-brief.md"
    brief.parent.mkdir(parents=True)
    brief.write_text(
        "She says main kar lungi, but the scene shows him noticing the quiet ask.",
        encoding="utf-8",
    )

    report = run_task_checks(
        task,
        tmp_path,
        skip_commands=True,
        explicit_changed_paths=["output/evals/ASTO-011/creator-brief.md"],
    )

    codes = {check.code for check in report.checks}
    assert "rubric_creative_contract" in codes or "creator_visible_framework_language" in codes
    assert any(check.status == "PENDING" for check in report.checks)
    assert report.resolved is False
    assert report.summary["pending_reviews"] == 1


def test_anchored_rubric_review_completes_creative_judgment(tmp_path: Path) -> None:
    task = next(
        task
        for task in discover_tasks(ROOT)
        if task.id == "ASTO-011-small-brief-no-framework-dump"
    )
    rubric = tmp_path / "evals" / "rubrics" / "creative-contract.md"
    rubric.parent.mkdir(parents=True)
    rubric.write_text("# Creative Contract Rubric\n", encoding="utf-8")
    brief = tmp_path / "output" / "evals" / "ASTO-011" / "creator-brief.md"
    brief.parent.mkdir(parents=True)
    brief.write_text(
        "She says main kar lungi. He moves the stool; she smiles. Strongest format: carousel.",
        encoding="utf-8",
    )
    review = {
        "task_id": task.id,
        "rubric": "creative_contract",
        "author_id": "agent:test-author",
        "reviewer_id": "human:test-reviewer",
        "artifact": "output/evals/ASTO-011/creator-brief.md",
        "artifact_sha256": hashlib.sha256(brief.read_bytes()).hexdigest(),
        "scores": {
            "seed_preservation": 3,
            "scene_proof": 3,
            "format_judgment": 2,
            "creator_facing_taste": 2,
            "relationship_motion": 1,
        },
        "evidence": {
            "seed_preservation": ["Exact seed phrase is present."],
            "scene_proof": ["The stool moves and she reacts."],
            "format_judgment": ["The artifact names and motivates carousel."],
            "creator_facing_taste": ["No internal framework terms appear."],
            "relationship_motion": ["The interaction is visible."],
        },
    }

    results = run_rubric_checkers(
        task,
        tmp_path,
        ["creative_contract"],
        reviews={(task.id, "creative_contract"): review},
    )

    judgment = next(
        result for result in results if result.code == "rubric_creative_contract_judgment"
    )
    assert judgment.status == "PASS"
    assert "total=11/12" in judgment.evidence

    brief.write_text(
        brief.read_text(encoding="utf-8") + "\nChanged after review.\n",
        encoding="utf-8",
    )
    stale_results = run_rubric_checkers(
        task,
        tmp_path,
        ["creative_contract"],
        reviews={(task.id, "creative_contract"): review},
    )
    stale_judgment = next(
        result
        for result in stale_results
        if result.code == "rubric_creative_contract_judgment"
    )
    assert stale_judgment.status == "FAIL"
    assert any("review is stale" in item for item in stale_judgment.evidence)


def test_single_pass_review_covers_registry_order_once() -> None:
    tasks = discover_tasks(ROOT)

    report = review_suite_once(tasks)

    assert report["status"] == "PASS", report["issues"]
    assert report["review_protocol"] == "single_pass_registry_order"
    assert report["reviewed_task_count"] == len(tasks)
    assert [item["task_id"] for item in report["tasks"]] == [task.id for task in tasks]


def test_prepare_unknown_task_is_cli_friendly(tmp_path: Path, capsys) -> None:
    status = main(["prepare", "ASTO-DOES-NOT-EXIST", "--output", str(tmp_path)])
    captured = capsys.readouterr()

    assert status == 2
    assert "Unknown eval task" in captured.err
    assert "Traceback" not in captured.err


def test_duplicate_background_character_fixture_is_blocked(tmp_path: Path) -> None:
    task = next(
        task
        for task in discover_tasks(ROOT)
        if task.id == "ASTO-019-duplicate-background-characters"
    )
    prepare_task_fixture_by_id(ROOT, task.id, tmp_path)

    report = run_task_checks(
        task,
        tmp_path,
        skip_commands=True,
        explicit_changed_paths=["pipeline/stages/carousel_quality.py"],
    )

    checks = {check.code: check for check in report.checks}
    assert report.resolved is True
    assert checks["scene_entity_integrity_fixture"].status == "PASS"
    evidence = " ".join(checks["scene_entity_integrity_fixture"].evidence).lower()
    assert "expected 2 people but observed 4" in evidence
    assert "background couple" in evidence


def test_hand_object_ai_slop_fixture_is_blocked(tmp_path: Path) -> None:
    task = next(
        task
        for task in discover_tasks(ROOT)
        if task.id == "ASTO-020-hand-object-integrity"
    )
    prepare_task_fixture_by_id(ROOT, task.id, tmp_path)

    report = run_task_checks(
        task,
        tmp_path,
        skip_commands=True,
        explicit_changed_paths=["pipeline/stages/carousel_quality.py"],
    )

    checks = {check.code: check for check in report.checks}
    assert report.resolved is True
    assert checks["hand_object_integrity_fixture"].status == "PASS"
    evidence = " ".join(checks["hand_object_integrity_fixture"].evidence).lower()
    assert "not required by the locked scene" in evidence
    assert "unexplained edge entry" in evidence
    assert "fails hand-object contact geometry" in evidence
    assert "intersects or may intersect a solid object" in evidence


def test_whole_person_spatial_integrity_fixture_is_blocked(tmp_path: Path) -> None:
    task = next(
        task
        for task in discover_tasks(ROOT)
        if task.id == "ASTO-021-whole-person-spatial-integrity"
    )
    prepare_task_fixture_by_id(ROOT, task.id, tmp_path)

    report = run_task_checks(
        task,
        tmp_path,
        skip_commands=True,
        explicit_changed_paths=["pipeline/stages/carousel_quality.py"],
    )

    checks = {check.code: check for check in report.checks}
    assert report.resolved is True
    assert checks["whole_person_spatial_integrity_fixture"].status == "PASS"
    evidence = " ".join(checks["whole_person_spatial_integrity_fixture"].evidence).lower()
    assert "silhouette is not fully traceable" in evidence
    assert "morphs or merges into the environment" in evidence
    assert "door edge enters zuv's torso" in evidence


def test_hil_stage_checkpoint_fixture_rejects_stale_approval(tmp_path: Path) -> None:
    task = next(
        task
        for task in discover_tasks(ROOT)
        if task.id == "ASTO-022-hil-stage-checkpoints"
    )
    prepare_task_fixture_by_id(ROOT, task.id, tmp_path)

    report = run_task_checks(
        task,
        tmp_path,
        skip_commands=True,
        explicit_changed_paths=["pipeline/agentic/carousel_hil_checkpoints.py"],
    )

    checks = {check.code: check for check in report.checks}
    assert report.resolved is True
    assert checks["hil_stage_checkpoint_fixture"].status == "PASS"
    evidence = " ".join(checks["hil_stage_checkpoint_fixture"].evidence).lower()
    assert "approval_valid(concept)=false" in evidence
    assert "next_unapproved_stage=concept" in evidence
    assert "creator_concept_approval_required" in evidence
