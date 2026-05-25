"""A0-A5 runner for the @a.storyof.two analysis pipeline."""

from __future__ import annotations

import argparse
import importlib
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class Stage:
    name: str
    module: str
    description: str


STAGE_ORDER = [
    Stage("a1", "pipeline.stages.a1_ingest", "Scrape Instagram into corpus/raw"),
    Stage("a2", "pipeline.stages.a2_parser", "Parse raw Apify JSON into normalized posts"),
    Stage("a3", "pipeline.stages.a3_analyzer", "Analyze normalized post corpus"),
    Stage("a4", "pipeline.stages.a4_wiki", "Compile wiki and memory updates"),
    Stage("a5", "pipeline.stages.a5_report", "Write human-readable strategy report"),
]


def resolve_stages(stage: str | None = None, from_stage: str | None = None) -> list[Stage]:
    if stage and from_stage:
        raise ValueError("Use either --stage or --from, not both.")
    names = [item.name for item in STAGE_ORDER]
    if stage:
        if stage not in names:
            raise ValueError(f"Unknown stage: {stage}")
        return [item for item in STAGE_ORDER if item.name == stage]
    if from_stage:
        if from_stage not in names:
            raise ValueError(f"Unknown stage: {from_stage}")
        start = names.index(from_stage)
        return STAGE_ORDER[start:]
    return list(STAGE_ORDER)


def run_stages(stages: list[Stage], root: Path, dry_run: bool = False, limit: int = 50) -> list[Any]:
    results: list[Any] = []
    for stage in stages:
        print(f"{stage.name} {stage.module} - {stage.description}")
        if dry_run:
            continue
        module = importlib.import_module(stage.module)
        if stage.name == "a1":
            results.append(module.run(root=root, limit=limit))
        else:
            results.append(module.run(root=root))
    return results


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run the @a.storyof.two A0-A5 analysis pipeline.")
    parser.add_argument("--stage", choices=[stage.name for stage in STAGE_ORDER])
    parser.add_argument("--from", dest="from_stage", choices=[stage.name for stage in STAGE_ORDER])
    parser.add_argument("--dry-run", action="store_true", help="List selected stages without executing them.")
    parser.add_argument("--limit", type=int, default=50, help="A1 scrape result limit.")
    parser.add_argument("--workspace-root", type=Path, default=Path.cwd())
    args = parser.parse_args(argv)

    stages = resolve_stages(stage=args.stage, from_stage=args.from_stage)
    run_stages(stages, root=args.workspace_root.resolve(), dry_run=args.dry_run, limit=args.limit)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
