from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent.parent))

from pipeline.stages.codex_builtin_image_generation import package_codex_builtin_outputs


def package_generated_images(
    carousel_dir: Path,
    *,
    instagram_post_paths: list[Path],
    reels_stories_paths: list[Path],
    refresh_quality: bool = False,
) -> dict[str, Any]:
    """Package paired native outputs; never derive one social format from another."""

    return package_codex_builtin_outputs(
        carousel_dir,
        generated_paths_by_format={
            "instagram_post": instagram_post_paths,
            "reels_stories": reels_stories_paths,
        },
        refresh_quality=refresh_quality,
    )


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Package native generated carousel images into final/ and final-reels-stories/. "
            "Provide one Instagram post image and one Reels/Stories image per slide."
        )
    )
    parser.add_argument("carousel_dir", type=Path)
    parser.add_argument("--instagram-post", dest="instagram_post_paths", action="append", required=True, type=Path)
    parser.add_argument("--reels-stories", dest="reels_stories_paths", action="append", required=True, type=Path)
    parser.add_argument(
        "--no-quality-refresh",
        action="store_true",
        help="Skip refreshing visual-qa/run-ledger/stage-reviews/final-audit after packaging.",
    )
    args = parser.parse_args()
    manifest = package_generated_images(
        args.carousel_dir,
        instagram_post_paths=args.instagram_post_paths,
        reels_stories_paths=args.reels_stories_paths,
        refresh_quality=not args.no_quality_refresh,
    )
    print(json.dumps(manifest, indent=2))


if __name__ == "__main__":
    main()
