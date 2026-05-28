#!/usr/bin/env python3
"""Safe git closeout gate for verified session publishing."""

from __future__ import annotations

import argparse
import dataclasses
import datetime as dt
import re
import subprocess
import sys
from pathlib import Path
from typing import Sequence


ROOT = Path(__file__).resolve().parents[1]


@dataclasses.dataclass(frozen=True)
class PathBlock:
    path: str
    reason: str


@dataclasses.dataclass(frozen=True)
class SecretFinding:
    path: str
    line: int
    kind: str


@dataclasses.dataclass(frozen=True)
class CommandResult:
    args: list[str]
    returncode: int
    stdout: str
    stderr: str


RISKY_PREFIXES = (
    "identity_images/",
    "draft_videos/",
    "corpus/media/",
    "corpus/raw/",
    "venv/",
    ".venv/",
    "env/",
    ".pytest_cache/",
    ".mypy_cache/",
    ".ruff_cache/",
    "logs/",
)

RISKY_PARTS = (
    "/__pycache__/",
    "/final/",
    "/final-reels-stories/",
    "/final-with-text/",
)

RISKY_OUTPUT_EXTENSIONS = (
    ".png",
    ".jpg",
    ".jpeg",
    ".webp",
    ".gif",
    ".mp4",
)

SECRET_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("openai_key", re.compile(r"sk-[A-Za-z0-9_-]{20,}")),
    ("apify_key", re.compile(r"apify_api_[A-Za-z0-9]{20,}")),
    ("github_token", re.compile(r"(?:ghp|github_pat)_[A-Za-z0-9_]{20,}")),
    ("anthropic_key", re.compile(r"sk-ant-[A-Za-z0-9_-]{20,}")),
    ("slack_token", re.compile(r"xox[baprs]-[A-Za-z0-9-]{20,}")),
)

SECRET_ASSIGNMENT_RE = re.compile(
    r"""(?ix)
    \b
    (?:api[_-]?key|access[_-]?token|secret|password|private[_-]?key)
    \b
    \s*[:=]\s*
    ['"]?
    (?P<value>[A-Za-z0-9_./+=:@-]{12,})
    ['"]?
    """
)

PLACEHOLDER_VALUES = {
    "...",
    "changeme",
    "change_me",
    "placeholder",
    "your_api_key_here",
    "your_apify_key_here",
    "your_openai_key_here",
    "your_anthropic_key_here",
    "your_github_token_here",
}


def normalize_path(path: str) -> str:
    return path.strip().strip('"').replace("\\", "/")


def parse_changed_paths(status_text: str) -> list[str]:
    """Extract current paths from `git status --porcelain` output."""

    paths: list[str] = []
    for raw_line in status_text.splitlines():
        if not raw_line:
            continue
        payload = raw_line[3:] if len(raw_line) > 3 else ""
        if " -> " in payload:
            payload = payload.split(" -> ", 1)[1]
        path = normalize_path(payload)
        if path:
            paths.append(path)
    return paths


def risky_reason(path: str) -> str | None:
    normalized = normalize_path(path)
    if normalized == ".env" or normalized.startswith(".env."):
        return "local environment file"
    if normalized.startswith(RISKY_PREFIXES):
        return "sensitive or generated path"
    if normalized.startswith("__pycache__/") or "/__pycache__/" in normalized:
        return "python cache file"
    if any(part in f"/{normalized}" for part in RISKY_PARTS):
        return "generated carousel output directory"
    if normalized.startswith("output/carousels/") and normalized.lower().endswith(
        RISKY_OUTPUT_EXTENSIONS
    ):
        return "generated carousel media"
    return None


def find_risky_paths(paths: Sequence[str]) -> list[PathBlock]:
    blocks: list[PathBlock] = []
    for path in paths:
        reason = risky_reason(path)
        if reason:
            blocks.append(PathBlock(path=normalize_path(path), reason=reason))
    return blocks


def filter_included_paths(paths: Sequence[str], includes: Sequence[str]) -> list[str]:
    if not includes:
        return [normalize_path(path) for path in paths]

    normalized_includes = [normalize_path(item).rstrip("/") for item in includes]
    selected: list[str] = []
    for path in paths:
        normalized_path = normalize_path(path)
        for include in normalized_includes:
            if normalized_path == include or normalized_path.startswith(f"{include}/"):
                selected.append(normalized_path)
                break
    return selected


def is_closeout_artifact(path: str) -> bool:
    normalized = normalize_path(path)
    if normalized == "wiki/index.md":
        return True
    if re.fullmatch(r"memory/episodic/\d{4}-\d{2}-\d{2}-session-health(?:-\d+)?\.md", normalized):
        return True
    if re.fullmatch(r"memory/heal/proposals/\d{4}-\d{2}-\d{2}-wiki-health\.md", normalized):
        return True
    if re.fullmatch(r"output/diagnostics/wiki-health-\d{4}-\d{2}-\d{2}\.md", normalized):
        return True
    return False


def filter_publish_paths(paths: Sequence[str], includes: Sequence[str]) -> list[str]:
    selected = filter_included_paths(paths, includes)
    if not includes:
        return selected

    seen = set(selected)
    for path in paths:
        normalized = normalize_path(path)
        if normalized not in seen and is_closeout_artifact(normalized):
            selected.append(normalized)
            seen.add(normalized)
    return selected


def is_placeholder_secret(value: str) -> bool:
    cleaned = value.strip().strip("'\"").lower()
    if not cleaned:
        return True
    if cleaned in PLACEHOLDER_VALUES:
        return True
    if cleaned.startswith("your_") and cleaned.endswith("_here"):
        return True
    return False


def is_probably_text(path: Path) -> bool:
    try:
        sample = path.read_bytes()[:4096]
    except OSError:
        return False
    return b"\x00" not in sample


def scan_secret_text(root: Path, paths: Sequence[str]) -> list[SecretFinding]:
    findings: list[SecretFinding] = []
    for relative in paths:
        normalized = normalize_path(relative)
        path = root / normalized
        if not path.exists() or not path.is_file() or not is_probably_text(path):
            continue
        try:
            lines = path.read_text(encoding="utf-8", errors="ignore").splitlines()
        except OSError:
            continue
        for line_number, line in enumerate(lines, start=1):
            for kind, pattern in SECRET_PATTERNS:
                if pattern.search(line):
                    findings.append(
                        SecretFinding(path=normalized, line=line_number, kind=kind)
                    )
            assignment = SECRET_ASSIGNMENT_RE.search(line)
            if assignment and not is_placeholder_secret(assignment.group("value")):
                findings.append(
                    SecretFinding(
                        path=normalized,
                        line=line_number,
                        kind="secret_assignment",
                    )
                )
    return findings


def build_validation_commands(session_note: str) -> list[list[str]]:
    return [
        ["venv/bin/python", "-m", "pytest", "-q"],
        [
            "venv/bin/python",
            "scripts/wiki_health.py",
            "--write",
            "--fix-index",
            "--session-note",
            session_note,
        ],
    ]


def generate_commit_message(paths: Sequence[str]) -> str:
    path_set = set(paths)
    if "scripts/autopublish.py" in path_set or "tests/test_autopublish.py" in path_set:
        return "chore: add safe autopublish closeout"
    if paths and all(path.startswith("docs/") for path in paths):
        return "docs: update project docs"
    if any(path.startswith("memory/") for path in paths):
        return "chore: update project memory"
    return "chore: autopublish session closeout"


def run_command(args: Sequence[str], root: Path = ROOT) -> CommandResult:
    result = subprocess.run(
        list(args),
        cwd=root,
        text=True,
        capture_output=True,
        check=False,
    )
    return CommandResult(
        args=list(args),
        returncode=result.returncode,
        stdout=result.stdout,
        stderr=result.stderr,
    )


def require_success(result: CommandResult) -> None:
    if result.returncode == 0:
        return
    command = " ".join(result.args)
    sys.stderr.write(f"\nBLOCKED: command failed: {command}\n")
    if result.stdout:
        sys.stderr.write(result.stdout)
    if result.stderr:
        sys.stderr.write(result.stderr)
    raise SystemExit(result.returncode)


def git_status(root: Path) -> str:
    result = run_command(["git", "status", "--porcelain"], root)
    require_success(result)
    return result.stdout


def current_branch(root: Path) -> str:
    result = run_command(["git", "branch", "--show-current"], root)
    require_success(result)
    branch = result.stdout.strip()
    if not branch:
        raise SystemExit("BLOCKED: detached HEAD; autopublish needs a branch.")
    return branch


def block_if_unsafe(root: Path, paths: Sequence[str]) -> None:
    risky = find_risky_paths(paths)
    if risky:
        sys.stderr.write("\nBLOCKED: risky paths are present in git status:\n")
        for item in risky:
            sys.stderr.write(f"- {item.path}: {item.reason}\n")
        raise SystemExit(2)

    findings = scan_secret_text(root, paths)
    if findings:
        sys.stderr.write("\nBLOCKED: possible secrets found in changed files:\n")
        for finding in findings:
            sys.stderr.write(f"- {finding.path}:{finding.line}: {finding.kind}\n")
        raise SystemExit(2)


def write_log(root: Path, message: str) -> Path:
    timestamp = dt.datetime.now().strftime("%Y-%m-%d-%H%M%S")
    path = root / "logs" / f"{timestamp}-autopublish.log"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(message, encoding="utf-8")
    return path


def autopublish(
    root: Path,
    session_note: str,
    dry_run: bool,
    no_push: bool,
    includes: Sequence[str] = (),
) -> int:
    all_initial_paths = parse_changed_paths(git_status(root))
    initial_paths = filter_publish_paths(all_initial_paths, includes)
    if not initial_paths:
        print("No matching git changes to autopublish.")
        return 0

    block_if_unsafe(root, initial_paths)

    validation_commands = build_validation_commands(session_note)
    if dry_run:
        print("Autopublish dry run.")
        print("Changed paths:")
        for path in initial_paths:
            print(f"- {path}")
        print("Validation commands:")
        for command in validation_commands:
            print(f"- {' '.join(command)}")
        print("Publish commands:")
        if includes:
            print(f"- git add -A -- {' '.join(initial_paths)}")
        else:
            print("- git add -A")
        print(f"- git commit -m \"{generate_commit_message(initial_paths)}\"")
        if not no_push:
            print("- git push")
        return 0

    for command in validation_commands:
        print(f"Running: {' '.join(command)}")
        require_success(run_command(command, root))

    final_paths = filter_publish_paths(parse_changed_paths(git_status(root)), includes)
    if not final_paths:
        print("No git changes remain after validation.")
        return 0

    block_if_unsafe(root, final_paths)

    add_command = ["git", "add", "-A"]
    if includes:
        add_command.extend(["--", *final_paths])
    require_success(run_command(add_command, root))
    diff_result = run_command(["git", "diff", "--cached", "--quiet"], root)
    if diff_result.returncode == 0:
        print("No staged changes to commit.")
        return 0
    if diff_result.returncode not in (0, 1):
        require_success(diff_result)

    message = generate_commit_message(final_paths)
    require_success(run_command(["git", "commit", "-m", message], root))

    branch = current_branch(root)
    pushed = False
    if not no_push:
        require_success(run_command(["git", "push", "origin", branch], root))
        pushed = True

    log = write_log(
        root,
        "\n".join(
            [
                f"session_note: {session_note}",
                f"commit_message: {message}",
                f"branch: {branch}",
                f"pushed: {pushed}",
                "paths:",
                *[f"- {path}" for path in final_paths],
                "",
            ]
        ),
    )
    print(f"Autopublish log written to {log.relative_to(root)}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--session-note",
        required=True,
        help="Short human-readable summary for wiki health and local logs.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print the planned closeout without committing or pushing.",
    )
    parser.add_argument(
        "--no-push",
        action="store_true",
        help="Commit locally but skip git push.",
    )
    parser.add_argument(
        "--include",
        action="append",
        default=[],
        metavar="PATH",
        help=(
            "Restrict publishing to a file or directory path. Repeat this flag "
            "when the worktree contains unrelated changes."
        ),
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    return autopublish(
        root=ROOT,
        session_note=args.session_note,
        dry_run=args.dry_run,
        no_push=args.no_push,
        includes=args.include,
    )


if __name__ == "__main__":
    raise SystemExit(main())
