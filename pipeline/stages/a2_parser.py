"""A2 parser: normalize raw Apify Instagram JSON into post records."""

from __future__ import annotations

import argparse
import json
import re
from datetime import date
from pathlib import Path
from typing import Any


HASHTAG_RE = re.compile(r"(?<!\w)#([\w]+)")
MENTION_RE = re.compile(r"(?<!\w)@([\w.]+)")


def latest_file(directory: Path, pattern: str) -> Path:
    matches = sorted(directory.glob(pattern))
    if not matches:
        raise FileNotFoundError(f"No files match {directory / pattern}")
    return matches[-1]


def raw_date(raw_path: Path) -> str:
    match = re.match(r"(\d{4}-\d{2}-\d{2})-raw\.json$", raw_path.name)
    return match.group(1) if match else str(date.today())


def normalize_post(item: dict[str, Any]) -> dict[str, Any]:
    caption = item.get("caption") or item.get("text") or ""
    shortcode = item.get("shortCode") or item.get("shortcode")
    post_type = str(item.get("type") or item.get("productType") or "").lower()
    return {
        "id": item.get("id") or shortcode or item.get("url"),
        "shortcode": shortcode,
        "url": item.get("url"),
        "timestamp": item.get("timestamp") or item.get("takenAt") or item.get("createdAt"),
        "post_type": post_type,
        "caption": caption,
        "hashtags": [tag.lower() for tag in HASHTAG_RE.findall(caption)],
        "mentions": [mention.lower() for mention in MENTION_RE.findall(caption)],
        "engagement": {
            "likes": item.get("likesCount") or item.get("likes") or 0,
            "comments": item.get("commentsCount") or item.get("comments") or 0,
            "views": item.get("videoViewCount") or item.get("viewCount") or 0,
            "plays": item.get("videoPlayCount") or item.get("playCount") or 0,
        },
        "raw_type": item.get("type"),
    }


def parse_raw_posts(raw_path: Path, output_dir: Path | None = None) -> Path:
    raw_path = raw_path.resolve()
    output_dir = output_dir or raw_path.parents[1] / "posts"
    output_dir.mkdir(parents=True, exist_ok=True)
    items = json.loads(raw_path.read_text(encoding="utf-8"))
    if not isinstance(items, list):
        raise ValueError(f"Expected a list in {raw_path}")
    posts = [normalize_post(item) for item in items if isinstance(item, dict)]
    out_path = output_dir / f"{raw_date(raw_path)}-posts.json"
    out_path.write_text(json.dumps(posts, indent=2, ensure_ascii=False), encoding="utf-8")
    return out_path


def run(root: Path | None = None, raw_path: Path | None = None) -> Path:
    root = (root or Path.cwd()).resolve()
    raw_path = raw_path or latest_file(root / "corpus" / "raw", "*-raw.json")
    return parse_raw_posts(raw_path, output_dir=root / "corpus" / "posts")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="A2 parse raw Apify JSON into normalized posts.")
    parser.add_argument("--raw-path", type=Path)
    parser.add_argument("--workspace-root", type=Path, default=Path.cwd())
    args = parser.parse_args(argv)

    out_path = run(root=args.workspace_root, raw_path=args.raw_path)
    print(out_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
