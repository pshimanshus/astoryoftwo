#!/usr/bin/env python3
"""Run the required wiki/memory health gate with safe defaults."""

from __future__ import annotations

import argparse
import subprocess
import sys
from datetime import date
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    parser = argparse.ArgumentParser(description="Run wiki health with write + index repair defaults.")
    parser.add_argument(
        "--session-note",
        default=f"AI command-center health run on {date.today().isoformat()}.",
        help="Short human-readable note written into memory/episodic.",
    )
    parser.add_argument(
        "--no-fix-index",
        action="store_true",
        help="Do not repair wiki/index.md metadata before checking.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Run checks without writing diagnostics, logs, or episodic memory.",
    )
    args = parser.parse_args()

    command = [sys.executable, "scripts/wiki_health.py"]
    if not args.dry_run:
        command.append("--write")
    if not args.no_fix_index:
        command.append("--fix-index")
    if args.session_note:
        command.extend(["--session-note", args.session_note])

    print("running:", " ".join(command))
    return subprocess.run(command, cwd=ROOT, check=False).returncode


if __name__ == "__main__":
    raise SystemExit(main())
