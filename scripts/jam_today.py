#!/usr/bin/env python3
"""Prepare a carousel jam without bypassing the repo's creative gates."""

from __future__ import annotations

import argparse
import shlex
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.start_agentic_session import load_research_partner_lens  # noqa: E402


REQUIRED_CONTEXT = [
    "config/skills/creator-skill-stack.md",
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

ABSTRACT_IDEA_WORDS = set(
    "love relationship relationships couple couples important should need needs care caring "
    "communicate communication trust respect support understand understanding".split()
)
CONCRETE_SCENE_WORDS = set(
    "blanket border moved plate kitchen cup tea coffee phone sofa bed door car bag shirt hair "
    "listening haan trap fight argument".split()
)
RECOGNITION_WORDS = set(
    "again always still secretly pretend pretending trap listening moved forgot remembered waited".split()
)


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


def words(text: str) -> set[str]:
    return {"".join(char for char in token.lower() if char.isalnum()) for token in text.split()} - {""}


def research_challenge(moment: str) -> dict[str, object]:
    tokens = words(moment)
    abstract_hits = tokens & ABSTRACT_IDEA_WORDS
    concrete_hits = tokens & CONCRETE_SCENE_WORDS
    recognition_hits = tokens & RECOGNITION_WORDS
    reasons: list[str] = []
    repairs: list[str] = []

    if abstract_hits and not concrete_hits:
        reasons.append("missing concrete couple scene")
        repairs.append("replace the theme with one visible action, object, room, or line of dialogue")
    if abstract_hits and not recognition_hits:
        reasons.append("missing reader-recognition proof")
        repairs.append("name the private pattern that makes someone think this is us")
    if len(tokens) < 4 and not (concrete_hits or recognition_hits):
        reasons.append("too thin to test")
        repairs.append("add the tiny conflict, gesture, or repeated habit before packaging")
    if abstract_hits and len(abstract_hits) >= max(2, len(tokens) // 3) and not concrete_hits:
        reasons.append("too abstract for a sendable moment")

    return {
        "verdict": "REWORK" if reasons else "PASS",
        "reasons": reasons,
        "repairs": repairs,
    }


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


def print_research_challenge_gate(moment: str) -> dict[str, object]:
    challenge = research_challenge(moment)
    print("\n## Research Challenge Gate")
    print(f"verdict: {challenge['verdict']}")
    if challenge["reasons"]:
        print("why:")
        for reason in challenge["reasons"]:
            print(f"- {reason}")
        print("repair before packaging:")
        for repair in challenge["repairs"]:
            print(f"- {repair}")
    else:
        print("- seed has a concrete scene or private pattern to test")
    return challenge


def print_research_partner_lens(moment: str) -> None:
    lens = load_research_partner_lens(ROOT)
    rules = " ".join(lens["operating_rules"]).lower()
    source = f"jam: {moment}"
    hypothesis_command = [
        sys.executable,
        "scripts/agentic_os.py",
        "capture-hypothesis",
        "--source",
        source,
        "--hypothesis",
        "this moment can become a sendable relationship mirror if the first route proves a real shared pattern, not just a cute incident",
        "--success-signal",
        "creator selects the route or it beats generic alternatives on recognition and scene proof",
        "--falsifier",
        "the idea reads as private trivia, stale template, or cute incident without a reader mirror",
    ]
    capture_command = [
        sys.executable,
        "scripts/agentic_os.py",
        "capture-learning",
        "--source",
        source,
        "--summary",
        "what worked, failed, or should become durable",
    ]

    print("\n## Research Partner Lens")
    print(f"memory: {lens['path']} ({lens['status']})")
    print(f"- hypothesis: this moment can become a sendable relationship mirror if the first route proves a real shared pattern, not just a cute incident")
    if "challenge" in rules:
        print("- challenge: reject stale, generic, or template-shaped routes with repo evidence before packaging")
    else:
        print("- challenge: ask what weak idea or stale default should be challenged before packaging")
    if "durable" in rules:
        print("- durable learning: after creator approval/rejection, capture what worked or failed for memory/rules/skills/wiki/tests")
    else:
        print("- durable learning: after the jam, identify what should become memory if this route works")
    print("hypothesis capture:")
    print_shell_command(hypothesis_command)
    print("learning capture:")
    print_shell_command(capture_command)


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
        "Creator Skill Stack hook first: define scroll stop, recognition, emotional "
        "contradiction, scene proof, retention ladder, payoff, format remix, audience "
        "mirror, volume path, taste gate, and DM Send Test before showing concepts."
    )
    print(
        "Free creative pass first: let the model generate concept, copy, and visual setup. "
        "Then apply engineering guardrails for repetition, identity, visual quality, exact text, "
        "brandmark, dimensions, stale artifacts, and house guidance."
    )
    print("If the creative pass is approved, save it as creative-baseline.json and package with --creative-brief-file.")
    print(f"moment: {args.moment}")
    challenge = print_research_challenge_gate(args.moment)
    print_research_partner_lens(args.moment)

    if challenge["verdict"] == "REWORK":
        print("\nBlocked: sharpen the seed before packaging so the jam starts from a couple moment, not a generic theme.")
        return 2

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
