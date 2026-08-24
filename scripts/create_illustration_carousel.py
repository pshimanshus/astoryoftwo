#!/usr/bin/env python3
"""Create the small copy/format/prompt package for an illustrated carousel."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from pipeline.stages.c1_illustration_carousel import DEFAULT_SLIDE_COUNT, interactive_mode  # noqa: E402
from pipeline.stages.codex_builtin_image_generation import prepare_codex_builtin_image_generation  # noqa: E402
from pipeline.stages.codex_native_carousel import create_codex_native_carousel  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Create an @a.storyof.two carousel package and optional proof handoff."
    )
    parser.add_argument("--story")
    parser.add_argument("--story-file")
    parser.add_argument("--title")
    parser.add_argument("--image", dest="images", action="append", default=[])
    parser.add_argument(
        "--identity-image",
        dest="identity_images",
        action="append",
        default=None,
        help="Aachu/Zuv identity or wardrobe reference. Repeat up to four times.",
    )
    parser.add_argument("--slide-count", type=int, default=DEFAULT_SLIDE_COUNT)
    parser.add_argument("--style-brief")
    parser.add_argument("--creative-brief-file")
    parser.add_argument(
        "--output-root",
        type=Path,
        default=Path("output") / "carousels",
    )
    parser.add_argument(
        "--prepare-proof",
        action="store_true",
        help="Compile only the riskiest real-image proof handoff.",
    )
    parser.add_argument(
        "--proof-slide",
        type=int,
        help="Use this slide as the real-image proof instead of automatic risk selection.",
    )
    parser.add_argument(
        "--format",
        dest="formats",
        choices=["instagram_post", "reels_stories", "square"],
        action="append",
        help="Lock an explicitly requested output. Default is only 1080x1440 Instagram post.",
    )
    args = parser.parse_args()

    story = (
        Path(args.story_file).expanduser().read_text(encoding="utf-8")
        if args.story_file
        else args.story
    )
    if story:
        options = {
            "story": story,
            "image_paths": args.images,
            "identity_image_paths": args.identity_images,
            "title": args.title,
            "slide_count": args.slide_count,
            "style_brief": args.style_brief,
        }
    else:
        options = interactive_mode()

    out_dir = create_codex_native_carousel(
        **options,
        output_root=args.output_root,
        creative_baseline_path=args.creative_brief_file,
        requested_formats=args.formats,
    )
    if args.prepare_proof or args.proof_slide is not None:
        result = prepare_codex_builtin_image_generation(
            out_dir,
            proof_slide=args.proof_slide,
        )
        print(f"Proof handoff -> {result['status']}")
    print(f"Carousel package -> {out_dir}")


if __name__ == "__main__":
    main()
