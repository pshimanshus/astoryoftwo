"""A1 ingest: scrape Instagram data into corpus/raw."""

from __future__ import annotations

import argparse
import json
from datetime import date
from pathlib import Path
from typing import Any


def save_raw_items(items: list[dict[str, Any]], root: Path, today: date | None = None) -> Path:
    today = today or date.today()
    out_dir = root / "corpus" / "raw"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"{today}-raw.json"
    out_path.write_text(json.dumps(items, indent=2, default=str), encoding="utf-8")
    return out_path


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
