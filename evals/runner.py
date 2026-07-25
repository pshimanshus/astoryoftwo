from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Sequence

TRUSTED_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(TRUSTED_ROOT))

# Bind the eval package to the trusted runner location before adding a solver
# workspace to sys.path. Trusted checker code can then import production modules
# from the isolated solver checkout without loading solver-edited eval modules.
import evals as _trusted_evals  # noqa: E402,F401


def _cli_workspace_root(argv: Sequence[str]) -> Path | None:
    for index, argument in enumerate(argv):
        if argument == "--workspace-root" and index + 1 < len(argv):
            return Path(argv[index + 1]).resolve()
        if argument.startswith("--workspace-root="):
            return Path(argument.split("=", 1)[1]).resolve()
    return None


CLI_WORKSPACE_ROOT = _cli_workspace_root(sys.argv[1:])
if CLI_WORKSPACE_ROOT is not None and CLI_WORKSPACE_ROOT != TRUSTED_ROOT:
    sys.path.insert(0, str(CLI_WORKSPACE_ROOT))

ROOT = TRUSTED_ROOT

from evals.attempts import (  # noqa: E402
    AttemptContractError,
    attempt_transition_checks,
    capture_workspace,
    changed_since_baseline,
    create_baseline_record,
    load_baseline_record,
    write_baseline_record,
)
from evals.checkers.deterministic import check_prompt_exists, run_required_commands  # noqa: E402
from evals.checkers.diff_guard import changed_paths, check_changed_paths  # noqa: E402
from evals.checkers.report import EvalReport, score_checks  # noqa: E402
from evals.checkers.rubric import load_rubric_reviews, run_rubric_checkers  # noqa: E402
from evals.checkers.task_specific import run_named_checkers  # noqa: E402
from evals.fixtures import UnsafeFixturePathError, materialize_task_fixture  # noqa: E402
from evals.review import review_suite_once  # noqa: E402
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
    rubric_reviews: dict[tuple[str, str], dict] | None = None,
) -> EvalReport:
    checks = [check_prompt_exists(task)]
    paths = explicit_changed_paths if explicit_changed_paths is not None else changed_paths(root)
    if "diff_guard" in task.deterministic_checkers:
        checks.extend(check_changed_paths(task, paths))
    checks.extend(run_named_checkers(task, root, task.deterministic_checkers))
    checks.extend(
        run_rubric_checkers(
            task,
            root,
            task.rubric_checkers,
            reviews=rubric_reviews,
        )
    )
    if not skip_commands:
        checks.extend(run_required_commands(task, root))
    return score_checks(task, checks)


def prepare_task_fixture_by_id(root: Path, task_id: str, output_dir: Path) -> list[Path]:
    tasks = discover_tasks(root)
    selected = select_tasks(tasks, task_id=task_id)
    if not selected:
        raise ValueError(f"Unknown eval task: {task_id}")
    return materialize_task_fixture(selected[0], output_dir)


def create_task_baseline(
    task: EvalTask,
    root: Path,
    *,
    mutation_manifest_path: Path | None = None,
) -> dict:
    checker_names = [
        name for name in task.deterministic_checkers if name != "diff_guard"
    ]
    checks = run_named_checkers(task, root, checker_names)
    return create_baseline_record(
        task,
        root,
        checks,
        mutation_manifest_path=mutation_manifest_path,
    )


def grade_task_attempt(
    task: EvalTask,
    root: Path,
    baseline_record: dict,
    *,
    rubric_reviews: dict[tuple[str, str], dict] | None = None,
    skip_commands: bool = False,
) -> tuple[EvalReport, list[str]]:
    current_files = capture_workspace(root)
    baseline_files = baseline_record["workspace"]["files"]
    paths = changed_since_baseline(baseline_files, current_files)
    final_report = run_task_checks(
        task,
        root,
        skip_commands=skip_commands,
        explicit_changed_paths=paths,
        rubric_reviews=rubric_reviews,
    )
    _, transition_checks = attempt_transition_checks(
        task,
        root,
        baseline_record,
        final_report.checks,
        current_files=current_files,
    )
    return score_checks(task, [*transition_checks, *final_report.checks]), paths


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run repo-local SWE-bench-style eval checks.")
    parser.add_argument("--workspace-root", type=Path, default=ROOT)
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("validate")

    list_parser = sub.add_parser("list")
    list_parser.add_argument("--suite")

    review = sub.add_parser(
        "review",
        help="Review each selected task fixture once in registry order.",
    )
    review.add_argument("--suite")

    check = sub.add_parser("check")
    check.add_argument("task_id", nargs="?")
    check.add_argument("--suite")
    check.add_argument("--skip-commands", action="store_true")
    check.add_argument("--changed-path", action="append", default=[])
    check.add_argument(
        "--rubric-results",
        type=Path,
        help="JSON file containing anchored human/judge rubric reviews.",
    )

    baseline = sub.add_parser(
        "baseline",
        help="Freeze an evaluator-owned failing baseline before the agent runs.",
    )
    baseline.add_argument("task_id")
    baseline.add_argument("--record", type=Path, required=True)
    baseline.add_argument(
        "--mutation-manifest",
        type=Path,
        help="Evaluator-owned hidden mutation proof required by regression tasks.",
    )

    grade = sub.add_parser(
        "grade",
        help="Certify a real fail-to-pass repair against a frozen baseline.",
    )
    grade.add_argument("task_id")
    grade.add_argument("--baseline", type=Path, required=True)
    grade.add_argument(
        "--rubric-results",
        type=Path,
        help="JSON file containing anchored human/judge rubric reviews.",
    )

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
        print(
            json.dumps(
                [
                    {
                        "id": task.id,
                        "title": task.title,
                        "suites": task.suites,
                        "fixture_mode": task.fixture_contract.mode,
                        "fixture_expected_outcome": task.fixture_contract.expected_outcome,
                        "benchmark_setup": task.fixture_contract.benchmark_setup,
                        "certification_contract": {
                            "baseline_must_fail": True,
                            "patch_required": True,
                            "expected_solution_file_changes_minimum": 1,
                            "baseline_failures_must_flip_to_pass": True,
                            "final_regressions_must_pass": True,
                        },
                    }
                    for task in selected
                ],
                indent=2,
            )
        )
        return 0

    if args.command == "review":
        selected = select_tasks(tasks, suite=args.suite)
        if not selected:
            print("No eval tasks matched.", file=sys.stderr)
            return 2
        report = review_suite_once(selected)
        print(json.dumps(report, indent=2))
        return 0 if report["status"] == "PASS" else 1

    if args.command == "check":
        selected = select_tasks(tasks, suite=args.suite, task_id=args.task_id)
        if not selected:
            print("No eval tasks matched.", file=sys.stderr)
            return 2
        try:
            rubric_reviews = (
                load_rubric_reviews(args.rubric_results)
                if args.rubric_results is not None
                else {}
            )
        except (FileNotFoundError, json.JSONDecodeError, OSError, ValueError) as exc:
            print(f"Invalid rubric results: {exc}", file=sys.stderr)
            return 2
        reports = [
            run_task_checks(
                task,
                root,
                skip_commands=args.skip_commands,
                explicit_changed_paths=args.changed_path or None,
                rubric_reviews=rubric_reviews,
            ).to_dict()
            for task in selected
        ]
        print(json.dumps(reports, indent=2))
        return 0 if all(report["resolved"] for report in reports) else 1

    if args.command == "baseline":
        selected = select_tasks(tasks, task_id=args.task_id)
        if not selected:
            print(f"Unknown eval task: {args.task_id}", file=sys.stderr)
            return 2
        try:
            record = create_task_baseline(
                selected[0],
                root,
                mutation_manifest_path=args.mutation_manifest,
            )
            if record["status"] == "READY":
                write_baseline_record(
                    record,
                    args.record,
                    workspace_root=root,
                )
        except (
            AttemptContractError,
            FileNotFoundError,
            json.JSONDecodeError,
            OSError,
        ) as exc:
            print(f"Invalid eval baseline: {exc}", file=sys.stderr)
            return 2
        summary = {
            "status": record["status"],
            "task_id": record["task_id"],
            "record": str(args.record.resolve())
            if record["status"] == "READY"
            else None,
            "baseline": record["baseline"],
            "mutation": record["mutation"],
            "issues": record["issues"],
        }
        print(json.dumps(summary, indent=2))
        return 0 if record["status"] == "READY" else 1

    if args.command == "grade":
        selected = select_tasks(tasks, task_id=args.task_id)
        if not selected:
            print(f"Unknown eval task: {args.task_id}", file=sys.stderr)
            return 2
        try:
            baseline_record = load_baseline_record(
                args.baseline,
                workspace_root=root,
            )
            rubric_reviews = (
                load_rubric_reviews(args.rubric_results)
                if args.rubric_results is not None
                else {}
            )
            report, paths = grade_task_attempt(
                selected[0],
                root,
                baseline_record,
                rubric_reviews=rubric_reviews,
            )
        except (
            AttemptContractError,
            FileNotFoundError,
            json.JSONDecodeError,
            OSError,
            ValueError,
        ) as exc:
            print(f"Invalid eval attempt: {exc}", file=sys.stderr)
            return 2
        certified = report.resolved
        print(
            json.dumps(
                {
                    "status": "PASS" if certified else "FAIL",
                    "certified_repair": certified,
                    "task_id": selected[0].id,
                    "changed_paths": paths,
                    "baseline_failing_check_codes": baseline_record["baseline"][
                        "failing_check_codes"
                    ],
                    "report": report.to_dict(),
                },
                indent=2,
            )
        )
        return 0 if certified else 1

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
