#!/usr/bin/env python3
"""Run, inspect, or validate the bounded Instagram idea-agent loop."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from pipeline.agentic.instagram_idea_loop import (  # noqa: E402
    IdeaLoopConfig,
    artifact_schema,
    candidate_fingerprint,
    execute_loop,
    find_candidate,
    load_state,
    prepare_run,
    resume_run,
    validate_run,
)


def _config_from_args(args: argparse.Namespace) -> IdeaLoopConfig:
    return IdeaLoopConfig(
        max_iterations=args.max_iterations,
        candidate_budget=args.candidate_budget,
        command_timeout_seconds=args.command_timeout,
        live_search=args.live_search,
    )


def _run(args: argparse.Namespace) -> int:
    config = _config_from_args(args)
    run_dir = prepare_run(
        ROOT,
        config=config,
        seed=args.seed,
        run_dir=args.run_dir,
    )
    if args.dry_run:
        state_path = run_dir / ".internal" / "loop-state.json"
        state = json.loads(state_path.read_text(encoding="utf-8"))
        state.update(
            {
                "status": "DRY_RUN",
                "stage": "PREPARED",
                "stop_reason": "Dry run prepared the evidence and orchestration prompt without invoking Codex.",
            }
        )
        state_path.write_text(
            json.dumps(state, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
        print(
            json.dumps(
                {
                    "status": "DRY_RUN",
                    "run_dir": str(run_dir),
                    "prompt": str(run_dir / ".internal" / "orchestration-prompt.md"),
                },
                indent=2,
            )
        )
        return 0

    returncode, report = execute_loop(ROOT, run_dir, config=config)
    print(json.dumps(report.to_dict(), indent=2, ensure_ascii=False))
    return returncode


def _validate(args: argparse.Namespace) -> int:
    report = validate_run(args.run_dir)
    validation_path = args.run_dir.expanduser().resolve() / ".internal" / "validation.json"
    validation_path.parent.mkdir(parents=True, exist_ok=True)
    validation_path.write_text(
        json.dumps(report.to_dict(), indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(report.to_dict(), indent=2, ensure_ascii=False))
    return 0 if report.valid else 2


def _resume(args: argparse.Namespace) -> int:
    state = resume_run(args.run_dir)
    config = IdeaLoopConfig(
        max_iterations=state.max_iterations,
        candidate_budget=state.candidate_budget,
        command_timeout_seconds=args.command_timeout,
        live_search=args.live_search,
    )
    returncode, report = execute_loop(ROOT, args.run_dir, config=config)
    print(json.dumps(report.to_dict(), indent=2, ensure_ascii=False))
    return returncode


def _status(args: argparse.Namespace) -> int:
    state = load_state(args.run_dir)
    print(json.dumps(state.model_dump(mode="json"), indent=2, ensure_ascii=False))
    return 0


def _fingerprint(args: argparse.Namespace) -> int:
    candidate = find_candidate(args.candidate_file, args.candidate_id)
    print(candidate_fingerprint(candidate))
    return 0


def _schema(_args: argparse.Namespace) -> int:
    print(json.dumps(artifact_schema(), indent=2, ensure_ascii=False))
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    run = subparsers.add_parser("run", help="Prepare the durable state and execute the Codex loop.")
    run.add_argument("--seed", help="Optional real couple moment or constraint; discovery works without one.")
    run.add_argument("--max-iterations", type=int, default=3)
    run.add_argument("--candidate-budget", type=int, default=6)
    run.add_argument("--command-timeout", type=int, default=1800, help="Codex timeout in seconds.")
    run.add_argument("--run-dir", type=Path, help="Optional exact output directory.")
    run.add_argument("--live-search", action="store_true", help="Allow current web search in the controller run.")
    run.add_argument("--dry-run", action="store_true", help="Prepare evidence and prompt without invoking Codex.")
    run.set_defaults(handler=_run)

    resume = subparsers.add_parser("resume", help="Resume a non-terminal durable loop run.")
    resume.add_argument("run_dir", type=Path)
    resume.add_argument("--command-timeout", type=int, default=1800, help="Codex timeout in seconds.")
    resume.add_argument("--live-search", action="store_true")
    resume.set_defaults(handler=_resume)

    validate = subparsers.add_parser("validate", help="Validate one completed loop against the stop contract.")
    validate.add_argument("run_dir", type=Path)
    validate.set_defaults(handler=_validate)

    status = subparsers.add_parser("status", help="Print durable loop state.")
    status.add_argument("run_dir", type=Path)
    status.set_defaults(handler=_status)

    fingerprint = subparsers.add_parser(
        "fingerprint",
        help="Fingerprint one exact candidate card for verifier binding.",
    )
    fingerprint.add_argument("candidate_file", type=Path)
    fingerprint.add_argument("--candidate-id", required=True)
    fingerprint.set_defaults(handler=_fingerprint)

    schema = subparsers.add_parser("schema", help="Print exact agent-written JSON schemas.")
    schema.set_defaults(handler=_schema)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        return args.handler(args)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(json.dumps({"status": "ERROR", "error": str(exc)}, indent=2), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
