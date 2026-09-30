"""A2 parser: normalize raw Apify Instagram JSON into post records."""

from __future__ import annotations

import argparse
import json
import math
import re
from datetime import date
from pathlib import Path
from typing import Any

from pipeline.stages.source_integrity import (
    atomic_write_text,
    build_source_receipt,
    provenance_for_raw,
    source_receipt_path,
)


HASHTAG_RE = re.compile(r"(?<!\w)#([\w]+)")
MENTION_RE = re.compile(r"(?<!\w)@([\w.]+)")
NORMALIZATION_SCHEMA_VERSION = "2.0"
METRIC_ALIASES = {
    "likes": ("likesCount", "likes"),
    "comments": ("commentsCount", "comments"),
    "views": ("videoViewCount", "viewCount", "views", "Views"),
    "viewers": ("viewers", "Viewers"),
    "follows": ("follows", "Follows"),
    "profile_visits": ("profile_visits", "profileVisits", "Profile visits"),
    "plays": ("videoPlayCount", "playCount", "plays"),
    "reach": ("reach", "reachCount"),
    "saves": ("saves", "saved", "savesCount", "Saves"),
    "shares": ("shares", "sharesCount", "Shares"),
    "sends": ("sends", "sendsCount"),
    "retention_rate": ("retention_rate",),
}
FORMAT_ALIASES = {
    "video": "video",
    "clips": "video",
    "clip": "video",
    "reel": "video",
    "reels": "video",
    "igtv": "video",
    "graphvideo": "video",
    "sidecar": "sidecar",
    "carousel": "sidecar",
    "carousel_album": "sidecar",
    "graphsidecar": "sidecar",
    "image": "image",
    "photo": "image",
    "graphimage": "image",
}


def latest_file(directory: Path, pattern: str) -> Path:
    matches = sorted(directory.glob(pattern))
    if not matches:
        raise FileNotFoundError(f"No files match {directory / pattern}")
    return matches[-1]


def raw_date(raw_path: Path) -> str:
    match = re.match(r"(\d{4}-\d{2}-\d{2})-raw(?:-\d+)?\.json$", raw_path.name)
    return match.group(1) if match else str(date.today())


def _metric_value(item: dict[str, Any], metric: str) -> int | float | None:
    """Use an observed numeric value; missing data must never become zero."""
    for alias in METRIC_ALIASES[metric]:
        value = item.get(alias)
        # bool is an int subclass, and string/list metadata is not a count.
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            continue
        if value < 0 or (isinstance(value, float) and not math.isfinite(value)):
            continue
        if metric == "retention_rate" and value > 1:
            continue
        return value
    return None


def _post_type(item: dict[str, Any]) -> str:
    candidates = [str(item.get(key) or "").strip().lower() for key in ("type", "productType", "post_type", "media_type")]
    for candidate in candidates:
        if candidate in FORMAT_ALIASES:
            return FORMAT_ALIASES[candidate]
    return next((candidate for candidate in candidates if candidate), "")


def normalize_post(item: dict[str, Any], provenance: dict[str, Any] | None = None) -> dict[str, Any]:
    caption = item.get("caption")
    if not isinstance(caption, str):
        caption = item.get("text")
    if not isinstance(caption, str):
        caption = ""
    shortcode = item.get("shortCode") or item.get("shortcode")
    engagement = {metric: _metric_value(item, metric) for metric in METRIC_ALIASES}
    children = item.get("childPosts")
    images = item.get("images")
    slide_count = len(children) if isinstance(children, list) and children else len(images) if isinstance(images, list) and images else None
    explicit_count = item.get("slide_count")
    if slide_count is None and type(explicit_count) is int and explicit_count > 0:
        slide_count = explicit_count
    normalized = {
        "schema_version": NORMALIZATION_SCHEMA_VERSION,
        "id": item.get("id") or shortcode or item.get("url"),
        "shortcode": shortcode,
        "url": item.get("url"),
        "timestamp": item.get("timestamp") or item.get("takenAt") or item.get("createdAt"),
        "observed_at": item.get("observed_at"),
        "collected_on": item.get("collected_on"),
        "metric_sources": {metric: next((alias for alias in METRIC_ALIASES[metric]
                                         if _metric_value({alias: item.get(alias)}, metric) is not None), None)
                           for metric in METRIC_ALIASES},
        "post_type": _post_type(item),
        "caption": caption,
        "hashtags": [tag.lower() for tag in HASHTAG_RE.findall(caption)],
        "mentions": [mention.lower() for mention in MENTION_RE.findall(caption)],
        "engagement": engagement,
        "metric_status": {
            metric: "observed" if value is not None else "unavailable"
            for metric, value in engagement.items()
        },
        "raw_type": item.get("type"),
        "slide_count": slide_count,
        "ownerUsername": item.get("ownerUsername"),
        "coauthorProducers": item.get("coauthorProducers"),
        "inputUrl": item.get("inputUrl"),
    }
    if provenance is not None:
        normalized["source_provenance"] = provenance
    return normalized


def parse_raw_posts(raw_path: Path, output_dir: Path | None = None) -> Path:
    raw_path = raw_path.resolve()
    output_dir = output_dir or raw_path.parents[1] / "posts"
    output_dir.mkdir(parents=True, exist_ok=True)
    items = json.loads(raw_path.read_text(encoding="utf-8"))
    if not isinstance(items, list):
        raise ValueError(f"Expected a list in {raw_path}")
    root = raw_path.parents[2] if raw_path.parent.name == "raw" else raw_path.parents[1]
    provenance = provenance_for_raw(root, raw_path)
    suffix = raw_path.stem.removeprefix(f"{raw_date(raw_path)}-raw")
    out_path = output_dir / f"{raw_date(raw_path)}-posts{suffix}.json"
    provenance["normalized_posts_path"] = out_path.relative_to(root).as_posix()
    posts = [normalize_post(item, provenance) for item in items if isinstance(item, dict)]
    atomic_write_text(out_path, json.dumps(posts, indent=2, ensure_ascii=False) + "\n")
    receipt = build_source_receipt(root, raw_path, out_path, len(posts))
    atomic_write_text(
        source_receipt_path(out_path),
        json.dumps(receipt, indent=2, ensure_ascii=False, sort_keys=True) + "\n",
    )
    return out_path


def run(root: Path | None = None, raw_path: Path | None = None) -> Path:
    root = (root or Path.cwd()).resolve()
    raw_path = raw_path or latest_file(root / "corpus" / "raw", "*-raw*.json")
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
