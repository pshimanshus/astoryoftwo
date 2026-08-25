#!/usr/bin/env python3
"""Prepare or run the small Codex-first carousel command.

The jam remains a creative conversation. This script only prints the compact
runtime context and the exact executable command; it does not insert a default
research gate, agent room, hypothesis ledger, or unsupported generation flag.
"""

from __future__ import annotations

import argparse
import shlex
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

REQUIRED_CONTEXT = (
    "config/skills/creator-skill-stack.md",
    ".agents/skills/a-story-storytelling-hook/SKILL.md",
    "config/skills/carousel-jam-runtime-context.md",
    "config/skills/carousel-jam-autopilot.md",
    "config/skills/carousel-story-director-persona.md",
)


def context_status() -> list[tuple[str, bool]]:
    return [(path, (ROOT / path).is_file()) for path in REQUIRED_CONTEXT]


def build_carousel_command(args: argparse.Namespace) -> list[str]:
    command = [
        sys.executable,
        "scripts/carousel.py",
        "create",
        "--story",
        args.moment,
    ]
    if args.slides is not None:
        command.extend(["--slide-count", str(args.slides)])
    if args.title:
        command.extend(["--title", args.title])
    if args.creative_brief:
        command.extend(["--creative-brief", args.creative_brief, "--prepare-proof"])
    if args.output_root:
        command.extend(["--output-root", args.output_root])
    if args.proof_slide is not None:
        command.extend(["--proof-slide", str(args.proof_slide)])
    for output_format in args.format:
        command.extend(["--format", output_format])
    for image in args.image:
        command.extend(["--story-image", image])
    for identity_image in args.identity_image:
        command.extend(["--identity-image", identity_image])
    for style_reference in args.style_reference:
        command.extend(["--style-reference", style_reference])
    return command


def print_shell_command(command: list[str]) -> None:
    print(" ".join(shlex.quote(part) for part in command))


def main() -> int:
    parser = argparse.ArgumentParser(description="Prepare or run today's carousel jam route.")
    parser.add_argument("--moment", help="Specific couple moment or story seed.")
    parser.add_argument("--title", help="Optional working title.")
    parser.add_argument(
        "--slides",
        type=int,
        default=None,
        help="Optional explicit beat cap; omitted preserves the supplied architecture.",
    )
    parser.add_argument("--image", "--story-image", dest="image", action="append", default=[])
    parser.add_argument("--identity-image", action="append", default=[])
    parser.add_argument("--style-reference", action="append", default=[])
    parser.add_argument("--creative-brief")
    parser.add_argument("--output-root")
    parser.add_argument("--proof-slide", type=int)
    parser.add_argument(
        "--format",
        action="append",
        choices=("instagram_post", "reels_stories", "square"),
        default=[],
    )
    parser.add_argument("--package", action="store_true")
    args = parser.parse_args()

    missing = [path for path, exists in context_status() if not exists]
    print("# Carousel Jam")
    print("\n## Runtime Context")
    for path, exists in context_status():
        print(f"- {'OK' if exists else 'MISSING'}: {path}")
    if missing:
        print("\nBlocked: required carousel runtime context is missing.")
        return 2
    if not args.moment:
        print("\nWhat is the one concrete couple moment, conflict, or private recognition?")
        return 0

    print("\n## Creative Pass")
    print(
        "Use the storytelling hook and free creative pass to lock the concept, exact copy, "
        "and visible actions before creating pixels. Story-only input creates a truthful "
        "draft; a locked creative brief may prepare one proof."
    )
    command = build_carousel_command(args)
    print("\n## Carousel Command")
    print_shell_command(command)
    if not args.package:
        return 0
    return subprocess.run(command, cwd=ROOT, check=False).returncode


if __name__ == "__main__":
    raise SystemExit(main())
