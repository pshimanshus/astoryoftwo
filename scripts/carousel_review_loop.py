#!/usr/bin/env python3
"""Run a fail-closed carousel review/repair loop until clean or honestly blocked."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from pipeline.agentic.carousel_review_loop import (  # noqa: E402
    ReviewLoopConfig,
    parse_command,
    run_review_loop,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("package_dir", type=Path, help="Carousel package to review and repair.")
    parser.add_argument("--max-iterations", type=int, default=12)
    parser.add_argument("--stagnation-limit", type=int, default=3)
    parser.add_argument("--command-timeout", type=int, default=1800, help="Per-command timeout in seconds.")
    parser.add_argument(
        "--repair-command",
        help=(
            "Optional non-shell repair command. Supports {package} and {feedback} placeholders. "
            "Defaults to a constrained ephemeral `codex exec` repair pass."
        ),
    )
    parser.add_argument(
        "--verify-command",
        action="append",
        default=[],
        help="Optional deterministic verifier; repeat for more. Supports {package} and {feedback}.",
    )
    parser.add_argument("--review-only", action="store_true", help="Inspect once without invoking repairs.")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    config = ReviewLoopConfig(
        max_iterations=args.max_iterations,
        stagnation_limit=args.stagnation_limit,
        repair_command=parse_command(args.repair_command) if args.repair_command else None,
        verify_commands=tuple(parse_command(value) for value in args.verify_command),
        review_only=args.review_only,
        command_timeout_seconds=args.command_timeout,
    )
    result = run_review_loop(args.package_dir, repo_root=ROOT, config=config)
    print(json.dumps(result.to_dict(), indent=2, ensure_ascii=False))
    if result.status == "COMPLETE":
        return 0
    if result.status == "HUMAN_REQUIRED":
        return 3
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
