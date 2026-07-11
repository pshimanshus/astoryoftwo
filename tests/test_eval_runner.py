from pathlib import Path

from evals.checkers.diff_guard import check_changed_paths
from evals.checkers.report import score_checks
from evals.runner import select_tasks
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
