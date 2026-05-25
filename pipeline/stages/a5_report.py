"""A5 report: write a concise strategy report from current wiki/memory."""

from __future__ import annotations

import argparse
from datetime import date
from pathlib import Path


def run(root: Path | None = None, today: date | None = None) -> Path:
    root = (root or Path.cwd()).resolve()
    today = today or date.today()
    out_dir = root / "output" / "reports"
    out_dir.mkdir(parents=True, exist_ok=True)
    index_path = root / "wiki" / "index.md"
    memory_path = root / "memory" / "working.md"
    index_source = index_path.read_text(encoding="utf-8") if index_path.exists() else ""
    memory_source = memory_path.read_text(encoding="utf-8") if memory_path.exists() else ""
    out_path = out_dir / f"strategy-{today}.md"
    out_path.write_text(
        "\n".join(
            [
                "# @a.storyof.two - Strategy Report",
                "",
                f"last_updated: {today}",
                "confidence: 0.7",
                "sources:",
                f"- {index_path}",
                f"- {memory_path}",
                "",
                "## Current Wiki State",
                "",
                index_source[:1200].rstrip(),
                "",
                "## Current Working Memory",
                "",
                memory_source[:1200].rstrip(),
                "",
            ]
        ),
        encoding="utf-8",
    )
    return out_path


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="A5 write strategy report from wiki/memory.")
    parser.add_argument("--workspace-root", type=Path, default=Path.cwd())
    args = parser.parse_args(argv)

    out_path = run(root=args.workspace_root)
    print(out_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
