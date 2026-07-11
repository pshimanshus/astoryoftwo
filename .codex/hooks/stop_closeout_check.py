#!/usr/bin/env python3
"""Print a safe closeout reminder at Codex Stop.

This hook is intentionally non-blocking and never publishes. It only inspects
the current git status, runs a lightweight Agentic OS health check, highlights
risky scope, and reminds the operator which closeout gate to run manually or
through the a-story-closeout skill.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


RISKY_PREFIXES = (
    ".env",
    "identity_images/",
    "draft_videos/",
    "corpus/raw/",
    "venv/",
    ".venv/",
    "logs/",
)

RISKY_CONTAINS = (
    "/final/",
    "/final-reels-stories/",
    "/final-with-text/",
)


def parse_status_paths(status: str) -> list[str]:
    paths: list[str] = []
    for raw_line in status.splitlines():
        if not raw_line.strip():
            continue
        line = raw_line.rstrip()
        path = line[3:] if len(line) > 3 else line
        if " -> " in path:
            path = path.split(" -> ", 1)[1]
        paths.append(path)
    return paths


def is_risky(path: str) -> bool:
    return path.startswith(RISKY_PREFIXES) or any(part in path for part in RISKY_CONTAINS)


def run_agentic_health() -> None:
    """Run read-only Agentic OS health and print a compact non-blocking summary."""

    result = subprocess.run(
        [sys.executable, "scripts/agentic_os.py", "health"],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if result.returncode != 0:
        print("[codex-stop] Agentic OS health check could not run.")
        if result.stderr.strip():
            print(result.stderr.strip())
        return

    try:
        payload = json.loads(result.stdout)
    except json.JSONDecodeError:
        print("[codex-stop] Agentic OS health output was not JSON.")
        if result.stdout.strip():
            print(result.stdout.strip())
        return

    print(
        "[codex-stop] Agentic OS health: "
        f"{payload.get('context_sections', '?')} context section(s), "
        f"{len(payload.get('skill_systems', []))} skill system(s), "
        f"{payload.get('skill_records', '?')} skill record(s)."
    )


def main() -> int:
    if not (Path.cwd() / ".git").exists():
        print("[codex-stop] No .git directory found; closeout check skipped.")
        return 0

    run_agentic_health()

    result = subprocess.run(
        ["git", "status", "--short"],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if result.returncode != 0:
        print("[codex-stop] Could not inspect git status; closeout check skipped.")
        if result.stderr.strip():
            print(result.stderr.strip())
        return 0

    paths = parse_status_paths(result.stdout)
    if not paths:
        print("[codex-stop] Worktree is clean; no closeout action needed.")
        return 0

    risky_paths = [path for path in paths if is_risky(path)]
    print(f"[codex-stop] Worktree has {len(paths)} changed path(s).")
    if risky_paths:
        print("[codex-stop] Risky paths present; autopublish will require repair or exclusion:")
        for path in risky_paths[:10]:
            print(f"  - {path}")
        if len(risky_paths) > 10:
            print(f"  - ... and {len(risky_paths) - 10} more")

    print(
        "[codex-stop] Close substantial sessions with: "
        'venv/bin/python scripts/autopublish.py --session-note "short summary"'
    )
    print("[codex-stop] For mixed scope, add repeated --include PATH flags.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
