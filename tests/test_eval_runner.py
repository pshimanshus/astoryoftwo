from pathlib import Path

from evals.checkers.diff_guard import check_changed_paths
from evals.checkers.report import score_checks
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


def test_prepare_unknown_task_is_cli_friendly(tmp_path: Path, capsys) -> None:
    status = main(["prepare", "ASTO-DOES-NOT-EXIST", "--output", str(tmp_path)])
    captured = capsys.readouterr()

    assert status == 2
    assert "Unknown eval task" in captured.err
    assert "Traceback" not in captured.err
