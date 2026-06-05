#!/usr/bin/env python3
"""Inspect an illustrated carousel package and derive its honest state."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from pipeline.agentic.carousel_state import derive_carousel_state  # noqa: E402
from pipeline.agentic.workflow_doctor import inspect_carousel_package  # noqa: E402


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("package_dir", type=Path, help="Carousel package directory to inspect.")
    parser.add_argument("--json", action="store_true", help="Print machine-readable JSON.")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    report = inspect_carousel_package(args.package_dir)
    state = derive_carousel_state(args.package_dir)
    payload = report.to_dict()
    payload["state"] = state.to_dict()

    if args.json:
        print(json.dumps(payload, indent=2, ensure_ascii=False))
    else:
        print(f"package: {payload['package_dir']}")
        print(f"state: {state.name}")
        print(f"highest severity: {report.highest_severity}")
        if report.issues:
            print("issues:")
            for issue in report.issues:
                print(f"- [{issue.severity}] {issue.code}: {issue.message}")
        else:
            print("issues: none")
        print(f"next action: {state.next_action}")

    return 2 if report.blocked else 0


if __name__ == "__main__":
    raise SystemExit(main())
