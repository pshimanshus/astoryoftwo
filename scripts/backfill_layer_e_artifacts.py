#!/usr/bin/env python3
"""Backfill Layer E artifacts for an existing carousel package."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from pipeline.layer_e.artifacts import JSON_ARTIFACT, write_layer_e_artifacts  # noqa: E402
from pipeline.layer_e.engine import run_layer_e  # noqa: E402


def read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def infer_workspace_root(carousel_dir: Path) -> Path:
    for candidate in [carousel_dir, *carousel_dir.parents]:
        if (candidate / "config" / "agentic_context_manifest.json").exists():
            return candidate
    return ROOT


def infer_layer_e_root(workspace_root: Path) -> Path:
    if (workspace_root / "output" / "story-canon").exists():
        return workspace_root
    return ROOT


def build_story_source(carousel_dir: Path) -> tuple[str, str]:
    manifest = read_json(carousel_dir / "manifest.json")
    concept = read_json(carousel_dir / "concept.json")
    storyboard = (
        (carousel_dir / "storyboard.md").read_text(encoding="utf-8", errors="ignore")
        if (carousel_dir / "storyboard.md").exists()
        else ""
    )
    slides = read_json(carousel_dir / "slides.json")
    title = str(manifest.get("title") or concept.get("title") or carousel_dir.name)
    story = "\n\n".join(
        part
        for part in [
            f"Title: {title}",
            str(manifest.get("source_story") or ""),
            str(concept.get("human_truth") or ""),
            str(concept.get("emotional_arc") or ""),
            storyboard[:2400],
            json.dumps(slides, ensure_ascii=False)[:1800] if slides else "",
        ]
        if part.strip()
    )
    return title, story


def backfill_layer_e_artifacts(carousel_dir: Path, *, force: bool = False) -> dict[str, Any]:
    carousel_dir = carousel_dir.expanduser().resolve()
    artifact = carousel_dir / JSON_ARTIFACT
    if artifact.exists() and not force:
        return {"status": "exists", "artifact": str(artifact)}

    workspace_root = infer_workspace_root(carousel_dir)
    title, story = build_story_source(carousel_dir)
    decision = run_layer_e(
        infer_layer_e_root(workspace_root),
        {
            "task_type": "carousel_idea",
            "story_or_moment": story,
            "constraints": [
                "backfill existing carousel package",
                "do not overwrite final images or package creative files",
            ],
            "requested_tone": title,
            "reference_images": [],
        },
    )
    write_layer_e_artifacts(carousel_dir, decision)
    return {
        "status": decision.status,
        "artifact": str(artifact),
        "selected_story_lens": decision.selected_story_lens,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("carousel_dir", type=Path)
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args(argv)
    print(json.dumps(backfill_layer_e_artifacts(args.carousel_dir, force=args.force), indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
