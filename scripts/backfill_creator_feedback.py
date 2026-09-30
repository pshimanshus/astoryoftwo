#!/usr/bin/env python3
"""Metadata-only correction migration with before/after media-hash proof."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from pipeline.agentic.learning_loop import atomic_write_text
from pipeline.stages.carousel_visual_storytelling import backfill_creator_correction, creator_feedback_records

MEDIA_SUFFIXES = {".png", ".jpg", ".jpeg", ".webp", ".gif", ".mp4", ".mov", ".pdf"}


def window_packages(root: Path, start: date, end: date) -> list[Path]:
    packages: list[Path] = []
    for dated in sorted((root / "output/carousels").glob("*")):
        try:
            stamp = date.fromisoformat(dated.name)
        except ValueError:
            continue
        if start <= stamp <= end and dated.is_dir() and not dated.is_symlink():
            packages.extend(path for path in sorted(dated.iterdir()) if path.is_dir() and not path.is_symlink())
    return packages


def media_hashes(root: Path, packages: list[Path]) -> dict[str, str]:
    result: dict[str, str] = {}
    for package in packages:
        for path in sorted(package.rglob("*")):
            if path.is_file() and not path.is_symlink() and path.suffix.lower() in MEDIA_SUFFIXES:
                with path.open("rb") as handle:
                    result[path.relative_to(root).as_posix()] = hashlib.file_digest(handle, "sha256").hexdigest()
    return result


def migrate(root: Path, start: date, end: date, *, apply: bool) -> dict:
    root = root.resolve()
    packages = window_packages(root, start, end)
    before = media_hashes(root, packages)
    inventory: list[dict] = []
    for package in packages:
        if not any((package / name).is_file() for name in ("creator-correction.json", "correction.json")):
            continue
        original = creator_feedback_records(package)
        exact = {item["feedback_id"]: item["user_instruction_exact"] for item in original}
        document = backfill_creator_correction(package, workspace_root=root) if apply else {"events": original}
        after_exact = {item["feedback_id"]: item["user_instruction_exact"] for item in document["events"]}
        if exact != after_exact:
            raise RuntimeError(f"Exact creator text changed during migration: {package}")
        inventory.append({"package": package.relative_to(root).as_posix(), "events": len(original), "exact_text_preserved": True})
    after = media_hashes(root, packages)
    if before != after:
        raise RuntimeError("Media inventory or hashes changed during metadata-only migration")
    return {
        "schema_version": "creator-feedback-migration/v1", "mode": "apply" if apply else "dry_run",
        "window_start": str(start), "window_end": str(end), "packages": inventory,
        "feedback_event_count": sum(item["events"] for item in inventory),
        "media_file_count": len(before), "media_unchanged": True,
        "media_hashes_before": before, "media_hashes_after": after,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workspace-root", type=Path, default=ROOT)
    parser.add_argument("--start", type=date.fromisoformat, default=date(2026, 8, 7))
    parser.add_argument("--end", type=date.fromisoformat, default=date(2026, 9, 4))
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--report", type=Path)
    args = parser.parse_args()
    report = migrate(args.workspace_root, args.start, args.end, apply=args.apply)
    if args.report:
        atomic_write_text(args.report, json.dumps(report, indent=2, ensure_ascii=False) + "\n")
    print(json.dumps({key: value for key, value in report.items() if not key.startswith("media_hashes_")}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
