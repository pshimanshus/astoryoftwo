#!/usr/bin/env python3
"""Prepare a carousel jam without bypassing the repo's creative gates."""

from __future__ import annotations

import argparse
import shlex
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


REQUIRED_CONTEXT = [
    "config/skills/carousel-jam-runtime-context.md",
    "config/skills/carousel-jam-autopilot.md",
    "config/skills/carousel-story-director-persona.md",
]

DEEP_SOURCE_CONTEXT = [
    "wiki/insights/successful-carousel-standard.md",
    "memory/semantic/carousel-idea-preferences.md",
    "wiki/themes/calm-enough-for-chaos.md",
    "output/reports/2026-05-17-he-didnt-marry-peace-viral-theme-analysis.md",
    "config/skills/romance-story-selling-engine.md",
    "config/skills/golden-viral-carousel-theme.md",
]


def rel(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


def context_status() -> list[tuple[str, bool]]:
    return [(path, (ROOT / path).exists()) for path in REQUIRED_CONTEXT]


def recent_carousels(limit: int = 5) -> list[Path]:
    root = ROOT / "output" / "carousels"
    if not root.exists():
        return []
    packages: list[Path] = []
    for day in root.iterdir():
        if day.is_dir():
            packages.extend(item for item in day.iterdir() if item.is_dir())
    return sorted(packages, key=lambda item: (item.stat().st_mtime, str(item)), reverse=True)[:limit]


def build_carousel_command(args: argparse.Namespace) -> list[str]:
    command = [
        sys.executable,
        "scripts/create_illustration_carousel.py",
        "--story",
        args.moment,
        "--slide-count",
        str(args.slides),
    ]
    if args.title:
        command.extend(["--title", args.title])
    for image in args.image:
        command.extend(["--image", image])
    for identity_image in args.identity_image:
        command.extend(["--identity-image", identity_image])
    if args.prepare_image_handoff:
        command.append("--prepare-image-handoff")
    return command


def print_shell_command(command: list[str]) -> None:
    print(" ".join(shlex.quote(part) for part in command))


def main() -> int:
    parser = argparse.ArgumentParser(description="Prepare or run today's carousel jam route.")
    parser.add_argument("--moment", help="Specific couple moment or story seed.")
    parser.add_argument("--title", help="Optional working title.")
    parser.add_argument("--slides", type=int, default=5, help="Slide count to pass to the carousel packager.")
    parser.add_argument("--image", action="append", default=[], help="Reference image path. Repeatable.")
    parser.add_argument("--identity-image", action="append", default=[], help="Identity reference path. Repeatable.")
    parser.add_argument("--prepare-image-handoff", action="store_true", help="Ask the packager to prepare image handoff files.")
    parser.add_argument("--package", action="store_true", help="Run the existing carousel packager after printing context.")
    args = parser.parse_args()

    print("# Carousel Jam Prep")
    print("\n## Required Runtime Context")
    missing: list[str] = []
    for path, exists in context_status():
        marker = "OK" if exists else "MISSING"
        print(f"- {marker}: {path}")
        if not exists:
            missing.append(path)

    print("\n## Deep Source References")
    for path in DEEP_SOURCE_CONTEXT:
        marker = "OK" if (ROOT / path).exists() else "MISSING"
        print(f"- {marker}: {path}")

    print("\n## Recent Carousel Packages")
    for package in recent_carousels():
        print(f"- {rel(package)}")
    if not recent_carousels():
        print("- none found")

    if not args.moment:
        print("\n## Next Question")
        print("What is the one concrete couple moment, conflict, or private joke for today's carousel?")
        print("\nExample:")
        print("make jam MOMENT=\"she moved the blanket border again\"")
        return 2 if missing else 0

    print("\n## Jam Instruction For Codex")
    print(
        "Free creative pass first: let the model generate concept, copy, and visual setup. "
        "Then apply engineering guardrails for repetition, identity, visual quality, exact text, "
        "brandmark, dimensions, stale artifacts, and house guidance."
    )
    print("If the creative pass is approved, save it as creative-baseline.json and package with --creative-brief-file.")
    print(f"moment: {args.moment}")

    command = build_carousel_command(args)
    print("\n## Package Command")
    print_shell_command(command)

    if missing:
        print("\nBlocked: required context is missing. Repair those files before packaging.")
        return 2

    if args.package:
        print("\n## Running Package Command")
        return subprocess.run(command, cwd=ROOT, check=False).returncode

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
