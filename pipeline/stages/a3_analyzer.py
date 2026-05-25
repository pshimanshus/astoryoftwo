"""A3 analyzer: deterministic post-corpus summary report."""

from __future__ import annotations

import argparse
import json
from collections import Counter
from datetime import date
from pathlib import Path
from typing import Any

from pipeline.stages.a2_parser import latest_file


def load_posts(posts_path: Path) -> list[dict[str, Any]]:
    posts = json.loads(posts_path.read_text(encoding="utf-8"))
    if not isinstance(posts, list):
        raise ValueError(f"Expected a list in {posts_path}")
    return [post for post in posts if isinstance(post, dict)]


def analyze_posts(posts: list[dict[str, Any]]) -> dict[str, Any]:
    likes = [post.get("engagement", {}).get("likes", 0) for post in posts]
    comments = [post.get("engagement", {}).get("comments", 0) for post in posts]
    hashtags = Counter(
        tag
        for post in posts
        for tag in post.get("hashtags", [])
    )
    post_types = Counter(post.get("post_type") or "unknown" for post in posts)
    top_posts = sorted(
        posts,
        key=lambda post: post.get("engagement", {}).get("likes", 0),
        reverse=True,
    )[:5]
    return {
        "post_count": len(posts),
        "total_likes": sum(likes),
        "total_comments": sum(comments),
        "average_likes": round(sum(likes) / len(likes), 2) if likes else 0,
        "post_types": dict(post_types),
        "top_hashtags": hashtags.most_common(12),
        "top_posts": top_posts,
    }


def report_markdown(summary: dict[str, Any], source: Path, today: date) -> str:
    lines = [
        "# @a.storyof.two - Corpus Analysis",
        "",
        f"last_updated: {today}",
        "confidence: 0.72",
        "sources:",
        f"- {source}",
        "",
        "## Summary",
        "",
        f"- posts: {summary['post_count']}",
        f"- total likes: {summary['total_likes']}",
        f"- total comments: {summary['total_comments']}",
        f"- average likes: {summary['average_likes']}",
        f"- post types: {summary['post_types']}",
        "",
        "## Top Hashtags",
        "",
    ]
    lines.extend(f"- #{tag}: {count}" for tag, count in summary["top_hashtags"])
    lines.extend(["", "## Top Posts", ""])
    for post in summary["top_posts"]:
        engagement = post.get("engagement", {})
        caption = (post.get("caption") or "").replace("\n", " ")[:100]
        lines.append(f"- {engagement.get('likes', 0)} likes - {caption}")
    lines.append("")
    return "\n".join(lines)


def run(root: Path | None = None, posts_path: Path | None = None, today: date | None = None) -> Path:
    root = (root or Path.cwd()).resolve()
    today = today or date.today()
    posts_path = posts_path or latest_file(root / "corpus" / "posts", "*-posts.json")
    summary = analyze_posts(load_posts(posts_path))
    out_dir = root / "output" / "reports"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"{today}-analysis.md"
    out_path.write_text(report_markdown(summary, posts_path, today), encoding="utf-8")
    return out_path


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="A3 analyze normalized posts.")
    parser.add_argument("--posts-path", type=Path)
    parser.add_argument("--workspace-root", type=Path, default=Path.cwd())
    args = parser.parse_args(argv)

    out_path = run(root=args.workspace_root, posts_path=args.posts_path)
    print(out_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
