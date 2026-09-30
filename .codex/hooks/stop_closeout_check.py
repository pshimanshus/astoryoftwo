#!/usr/bin/env python3
"""Warn about risky closeout scope without running recurring health work."""

from __future__ import annotations

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


def main() -> int:
    if not (Path.cwd() / ".git").exists():
        print("[codex-stop] No .git directory found; closeout check skipped.")
        return 0

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
        return 0

    risky_paths = [path for path in paths if is_risky(path)]
    if not risky_paths:
        return 0
    print("[codex-stop] Risky paths present; repair or exclude them before publishing:")
    for path in risky_paths[:10]:
        print(f"  - {path}")
    if len(risky_paths) > 10:
        print(f"  - ... and {len(risky_paths) - 10} more")
    return 0


if __name__ == "__main__":
    sys.exit(main())
