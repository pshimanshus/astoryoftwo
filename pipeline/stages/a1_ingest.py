"""A1 ingest: scrape Instagram data into corpus/raw."""

from __future__ import annotations

import argparse
import json
from datetime import date
from pathlib import Path
from typing import Any

from pipeline.stages.source_integrity import (
    atomic_write_text,
    register_raw_snapshot,
    workspace_lock,
)


def save_raw_items(items: list[dict[str, Any]], root: Path, today: date | None = None) -> Path:
    """Save an immutable A1 snapshot.

    A repeated scrape with the same date and identical payload is idempotent. A
    different payload never overwrites the earlier snapshot; it gets a numeric
    collision suffix and a distinct registry entry.
    """
    root = root.resolve()
    today = today or date.today()
    out_dir = root / "corpus" / "raw"
    out_dir.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(items, indent=2, default=str) + "\n"
    with workspace_lock(root, "raw-snapshots"):
        candidate = out_dir / f"{today}-raw.json"
        collision = 2
        while candidate.exists():
            if candidate.read_text(encoding="utf-8") == payload:
                register_raw_snapshot(
                    root,
                    candidate,
                    item_count=len(items),
                    collected_at=f"{today.isoformat()}T00:00:00Z",
                )
                return candidate
            candidate = out_dir / f"{today}-raw-{collision}.json"
            collision += 1
        atomic_write_text(candidate, payload)
        register_raw_snapshot(
            root,
            candidate,
            item_count=len(items),
            collected_at=f"{today.isoformat()}T00:00:00Z",
        )
        return candidate


def run(root: Path | None = None, limit: int = 50, today: date | None = None) -> Path:
    root = (root or Path.cwd()).resolve()
    from scripts.scrape_instagram import run_scrape

    items = run_scrape(limit=limit)
    return save_raw_items(items, root=root, today=today)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="A1 ingest Instagram posts into corpus/raw.")
    parser.add_argument("--limit", type=int, default=50)
    parser.add_argument("--workspace-root", type=Path, default=Path.cwd())
    args = parser.parse_args(argv)

    out_path = run(root=args.workspace_root, limit=args.limit)
    print(out_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
