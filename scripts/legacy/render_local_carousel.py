#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from pipeline.stages.local_carousel_renderer import render_local_carousel  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Render preview-only @a.storyof.two carousel images locally. "
            "Creates separate 4:5 and 9:16 PNGs for flow checks without satisfying final publishable gates."
        )
    )
    parser.add_argument("carousel_dir", type=Path)
    parser.add_argument(
        "--no-quality-refresh",
        action="store_true",
        help="Only render image files and manifests; do not rerun final-audit quality artifacts.",
    )
    args = parser.parse_args()
    result = render_local_carousel(args.carousel_dir, refresh_quality=not args.no_quality_refresh)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
