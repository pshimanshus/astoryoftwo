from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Sequence

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from evals.checkers.deterministic import check_prompt_exists, run_required_commands  # noqa: E402
from evals.checkers.diff_guard import changed_paths, check_changed_paths  # noqa: E402
from evals.checkers.report import EvalReport, score_checks  # noqa: E402
from evals.checkers.task_specific import run_named_checkers  # noqa: E402
from evals.fixtures import UnsafeFixturePathError, materialize_task_fixture  # noqa: E402
from evals.schemas import EvalTask, discover_tasks, validate_task_suite  # noqa: E402


def select_tasks(
    tasks: list[EvalTask],
    *,
    suite: str | None = None,
    task_id: str | None = None,
) -> list[EvalTask]:
    if task_id:
        return [task for task in tasks if task.id == task_id]
    if suite:
        return [task for task in tasks if suite in task.suites]
    return tasks


def run_task_checks(
    task: EvalTask,
    root: Path,
    *,
    skip_commands: bool = False,
    explicit_changed_paths: list[str] | None = None,
) -> EvalReport:
    checks = [check_prompt_exists(task)]
    paths = explicit_changed_paths if explicit_changed_paths is not None else changed_paths(root)
    if "diff_guard" in task.deterministic_checkers:
        checks.extend(check_changed_paths(task, paths))
    checks.extend(run_named_checkers(task, root, task.deterministic_checkers))
    if not skip_commands:
        checks.extend(run_required_commands(task, root))
    return score_checks(task, checks)


def prepare_task_fixture_by_id(root: Path, task_id: str, output_dir: Path) -> list[Path]:
    tasks = discover_tasks(root)
    selected = select_tasks(tasks, task_id=task_id)
    if not selected:
        raise ValueError(f"Unknown eval task: {task_id}")
    return materialize_task_fixture(selected[0], output_dir)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run repo-local SWE-bench-style eval checks.")
    parser.add_argument("--workspace-root", type=Path, default=ROOT)
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("validate")

    list_parser = sub.add_parser("list")
    list_parser.add_argument("--suite")

    check = sub.add_parser("check")
    check.add_argument("task_id", nargs="?")
    check.add_argument("--suite")
    check.add_argument("--skip-commands", action="store_true")
    check.add_argument("--changed-path", action="append", default=[])

    prepare = sub.add_parser("prepare")
    prepare.add_argument("task_id")
    prepare.add_argument("--output", type=Path, required=True)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    root = args.workspace_root.resolve()

    if args.command == "validate":
        report = validate_task_suite(root)
        print(json.dumps(report, indent=2))
        return 0 if report["status"] == "PASS" else 1

    tasks = discover_tasks(root)
    if args.command == "list":
        selected = select_tasks(tasks, suite=args.suite)
        print(json.dumps([{"id": task.id, "title": task.title, "suites": task.suites} for task in selected], indent=2))
        return 0

    if args.command == "check":
        selected = select_tasks(tasks, suite=args.suite, task_id=args.task_id)
        if not selected:
            print("No eval tasks matched.", file=sys.stderr)
            return 2
        reports = [
            run_task_checks(
                task,
                root,
                skip_commands=args.skip_commands,
                explicit_changed_paths=args.changed_path or None,
            ).to_dict()
            for task in selected
        ]
        print(json.dumps(reports, indent=2))
        return 0 if all(report["resolved"] for report in reports) else 1

    if args.command == "prepare":
        try:
            written = prepare_task_fixture_by_id(root, args.task_id, args.output)
        except (ValueError, UnsafeFixturePathError) as exc:
            print(str(exc), file=sys.stderr)
            return 2
        print(
            json.dumps(
                {
                    "task_id": args.task_id,
                    "output": str(args.output.resolve()),
                    "written": [str(path) for path in written],
                },
                indent=2,
            )
        )
        return 0

    return 2


if __name__ == "__main__":
    raise SystemExit(main())
