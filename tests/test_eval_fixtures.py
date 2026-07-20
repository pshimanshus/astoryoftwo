from pathlib import Path

import pytest

from evals.checkers.task_specific import run_named_checkers
from evals.fixtures import UnsafeFixturePathError, materialize_task_fixture
from evals.schemas import EvalTask, FixtureOverlay, PassCriteria, discover_tasks
from pipeline.agentic.carousel_state import derive_carousel_state
from pipeline.agentic.workflow_doctor import inspect_carousel_package
from scripts.autopublish import SECRET_PATTERNS, find_risky_paths, parse_changed_paths, scan_secret_text


ROOT = Path(__file__).resolve().parents[1]


def _task(task_id: str):
    return next(task for task in discover_tasks(ROOT) if task.id == task_id)


def _synthetic_overlay_task(overlay: FixtureOverlay, task_dir: Path) -> EvalTask:
    return EvalTask(
        schema_version="1.0",
        id="ASTO-999",
        title="Synthetic fixture overlay task",
        category="fixture_security",
        difficulty="easy",
        suites=["smoke"],
        prompt="prompt.md",
        starting_state=["Fixture overlay is unsafe."],
        done_when=["Unsafe overlay is rejected."],
        allowed_paths=["fixtures/**"],
        forbidden_paths=["AGENTS.md", ".env*", "identity_images/**", "output/**/final/**"],
        expected_files_changed=[],
        forbidden_changes=[],
        required_commands=[],
        deterministic_checkers=[],
        rubric_checkers=[],
        pass_criteria=PassCriteria(),
        fixture_overlay=[overlay],
        task_dir=task_dir,
    )


def test_smoke_tasks_have_materialized_fixture_overlays() -> None:
    smoke_tasks = [task for task in discover_tasks(ROOT) if "smoke" in task.suites]

    assert smoke_tasks
    for task in smoke_tasks:
        assert task.fixture_overlay, f"{task.id} needs at least one fixture overlay"
        for fixture in task.fixture_overlay:
            assert (task.task_dir / fixture.source).exists(), (
                f"{task.id} fixture source missing: {fixture.source}"
            )


def test_tracked_eval_fixtures_do_not_contain_live_looking_secrets() -> None:
    fixture_files = [
        path
        for path in (ROOT / "evals" / "tasks").rglob("*")
        if path.is_file() and "/fixtures/" in path.as_posix()
    ]

    assert fixture_files
    for path in fixture_files:
        text = path.read_text(encoding="utf-8", errors="ignore")
        for kind, pattern in SECRET_PATTERNS:
            assert not pattern.search(text), f"{kind} found in {path.relative_to(ROOT)}"


def test_fixture_overlay_rejects_parent_directory_target(tmp_path: Path) -> None:
    task_dir = tmp_path / "task"
    task_dir.mkdir()
    (task_dir / "prompt.md").write_text("Prompt", encoding="utf-8")
    (task_dir / "fixture.txt").write_text("unsafe", encoding="utf-8")
    task = _synthetic_overlay_task(
        FixtureOverlay(source="fixture.txt", target="../escape.txt"),
        task_dir,
    )

    with pytest.raises(UnsafeFixturePathError):
        materialize_task_fixture(task, tmp_path / "workspace")

    assert not (tmp_path / "escape.txt").exists()


def test_fixture_overlay_rejects_absolute_source(tmp_path: Path) -> None:
    task_dir = tmp_path / "task"
    task_dir.mkdir()
    (task_dir / "prompt.md").write_text("Prompt", encoding="utf-8")
    source = tmp_path / "outside.txt"
    source.write_text("unsafe", encoding="utf-8")
    task = _synthetic_overlay_task(
        FixtureOverlay(source=str(source), target="safe.txt"),
        task_dir,
    )

    with pytest.raises(UnsafeFixturePathError):
        materialize_task_fixture(task, tmp_path / "workspace")


def test_brandmark_fixture_triggers_named_checker(tmp_path: Path) -> None:
    task = _task("ASTO-001-brandmark-drift")
    materialize_task_fixture(task, tmp_path)

    results = run_named_checkers(task, tmp_path, ["brandmark_top_right_rule"])

    assert [result.status for result in results] == ["FAIL"]
    assert results[0].code == "brandmark_top_right_rule"
    assert "bottom-right" in "\n".join(results[0].evidence)


def test_textless_prompt_fixture_triggers_carousel_doctor(tmp_path: Path) -> None:
    task = _task("ASTO-003-textless-prompt")
    materialize_task_fixture(task, tmp_path)

    package = tmp_path / "output" / "carousels" / "fixtures" / "textless-prompt"
    report = inspect_carousel_package(package)
    codes = {issue.code for issue in report.issues}

    assert report.blocked is True
    assert "active_textless_prompt" in codes

    results = run_named_checkers(task, tmp_path, ["carousel_doctor_fixture"])
    assert [result.status for result in results] == ["PASS"]


def test_fake_publishable_fixture_derives_blocked_state(tmp_path: Path) -> None:
    task = _task("ASTO-004-fake-publishable-package")
    materialize_task_fixture(task, tmp_path)

    package = tmp_path / "output" / "carousels" / "fixtures" / "fake-publishable"
    report = inspect_carousel_package(package)
    state = derive_carousel_state(package)

    assert report.blocked is True
    assert state.blocked is True
    assert state.publishable is False

    results = run_named_checkers(task, tmp_path, ["carousel_doctor_fixture"])
    assert [result.status for result in results] == ["PASS"]


def test_autopublish_fixture_contains_blocked_risky_paths_and_secret(tmp_path: Path) -> None:
    task = _task("ASTO-008-autopublish-risky-paths")
    materialize_task_fixture(task, tmp_path)
    (tmp_path / ".env.local").write_text(
        "OPENAI_API_KEY=" + "sk-" + ("a" * 24) + "\n",
        encoding="utf-8",
    )

    status_text = (tmp_path / "fixtures" / "git-status.txt").read_text(encoding="utf-8")
    paths = parse_changed_paths(status_text)
    risky = {block.path for block in find_risky_paths(paths)}
    secrets = scan_secret_text(tmp_path, paths)

    assert ".env.local" in risky
    assert "identity_images/aachu-reference.png" in risky
    assert "output/carousels/fixtures/demo/final/slide-01.png" in risky
    assert any(finding.kind == "openai_key" for finding in secrets)


def test_autopublish_fixture_named_checker_blocks_risky_paths_without_tracked_secret(tmp_path: Path) -> None:
    task = _task("ASTO-008-autopublish-risky-paths")
    materialize_task_fixture(task, tmp_path)

    results = run_named_checkers(task, tmp_path, ["autopublish_safety_fixture"])

    assert [result.status for result in results] == ["PASS", "PASS"]
