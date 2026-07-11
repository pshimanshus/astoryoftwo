#!/usr/bin/env python3
"""
Interactive CLI for the C-layer illustrated carousel automation.

Default runtime is codex-native/local: it requires no Anthropic key and writes
the full carousel artifact contract plus best-effort stylized exports.

Examples:
  venv/bin/python scripts/create_illustration_carousel.py
  venv/bin/python scripts/create_illustration_carousel.py \
    --story "I proposed to Anchal under the stars" \
    --image /path/to/photo1.jpg \
    --image /path/to/photo2.jpg
  venv/bin/python scripts/create_illustration_carousel.py --mode anthropic \
    --story "I proposed to Anchal under the stars" \
    --image /path/to/photo1.jpg
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from pipeline.stages.c1_illustration_carousel import (  # noqa: E402
    DEFAULT_SLIDE_COUNT,
    create_illustration_carousel,
    interactive_mode,
)
from pipeline.agentic.carousel_state import derive_carousel_state  # noqa: E402
from pipeline.agentic.generation_capability import write_generation_capability  # noqa: E402
from pipeline.stages.codex_builtin_image_generation import prepare_codex_builtin_image_generation  # noqa: E402
from pipeline.stages.codex_native_carousel import create_codex_native_carousel  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Create an illustrated carousel package for @a.storyof.two",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  venv/bin/python scripts/create_illustration_carousel.py
  venv/bin/python scripts/create_illustration_carousel.py --story "Anchal tries wazwan for the first time" --image photo.jpg
  venv/bin/python scripts/create_illustration_carousel.py --story-file story.txt --image one.jpg --image two.jpg --slide-count 6
  venv/bin/python scripts/create_illustration_carousel.py --mode anthropic --story "..." --image photo.jpg
        """,
    )
    parser.add_argument("--story", help="Story or memory behind the pictures")
    parser.add_argument("--story-file", help="Read story from a text file")
    parser.add_argument("--title", help="Optional working title")
    parser.add_argument(
        "--image",
        dest="images",
        action="append",
        default=[],
        help="Reference image path. Repeat for multiple images.",
    )
    parser.add_argument(
        "--identity-image",
        dest="identity_images",
        action="append",
        default=None,
        help="Aachu/Zuv identity or clothing reference image. Repeat for multiple references.",
    )
    parser.add_argument(
        "--slide-count",
        type=int,
        default=DEFAULT_SLIDE_COUNT,
        help="Slide count, usually 4-10",
    )
    parser.add_argument("--style-brief", help="Optional illustration/style direction")
    parser.add_argument(
        "--creative-brief-file",
        help=(
            "JSON file from the free creative pass. When supplied in codex-native mode, "
            "its concept, slide copy, visual setup, and caption are preserved before QA gates."
        ),
    )
    parser.add_argument(
        "--mode",
        choices=["codex-native", "anthropic"],
        default="codex-native",
        help="Runtime to use. Default is codex-native and requires no API key.",
    )
    parser.add_argument(
        "--output-root",
        type=Path,
        default=Path("output") / "carousels",
        help="Directory where dated carousel packages are written.",
    )
    parser.add_argument(
        "--no-render",
        action="store_true",
        help="Deprecated compatibility flag. Local preview rendering is disabled by default.",
    )
    parser.add_argument(
        "--render-assets",
        action="store_true",
        help="Opt in to legacy local preview assets. Do not use for final @a.storyof.two carousel art.",
    )
    parser.add_argument(
        "--generate-images",
        action="store_true",
        help=(
            "Deprecated alias for --prepare-image-handoff. Prepares Codex built-in "
            "handoff files; does not generate final PNGs."
        ),
    )
    parser.add_argument(
        "--prepare-image-handoff",
        action="store_true",
        help="Prepare Codex built-in image-generation handoff files. Does not generate final PNGs.",
    )
    parser.add_argument(
        "--proof-slide",
        type=int,
        help="Prepare handoff prompts only for this slide number.",
    )
    parser.add_argument(
        "--proof-format",
        choices=["instagram_post", "reels_stories"],
        action="append",
        help="Limit handoff prompts to one native format. Repeat to include both formats.",
    )
    parser.add_argument(
        "--image-backend",
        choices=["codex-built-in", "local-dry-run"],
        default="codex-built-in",
        help=(
            "Image generation backend. codex-built-in prepares final image-generation handoff; "
            "local-dry-run writes deterministic non-publishable PNGs for tests/previews."
        ),
    )
    args = parser.parse_args()

    if args.image_backend == "local-dry-run" and (
        args.prepare_image_handoff or args.generate_images or args.proof_slide is not None or args.proof_format
    ):
        parser.error(
            "local-dry-run cannot be combined with --prepare-image-handoff, "
            "--generate-images, --proof-slide, or --proof-format."
        )

    story = Path(args.story_file).expanduser().read_text(encoding="utf-8") if args.story_file else args.story
    if story and (args.images or args.identity_images):
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

    if args.mode == "anthropic":
        if args.creative_brief_file:
            parser.error("--creative-brief-file is supported only in codex-native mode.")
        out_dir = create_illustration_carousel(
            **options,
            output_root=args.output_root,
        )
    else:
        out_dir = create_codex_native_carousel(
            **options,
            output_root=args.output_root,
            render_assets=args.render_assets and not args.no_render,
            creative_baseline_path=args.creative_brief_file,
        )
        if args.generate_images:
            print(
                "Warning: --generate-images is deprecated; use --prepare-image-handoff. "
                "This command does not generate final PNGs."
            )
        if args.image_backend == "local-dry-run":
            from pipeline.stages.local_dry_run_image_backend import generate_local_dry_run_images

            result = generate_local_dry_run_images(out_dir)
            print(f"Local dry-run image backend -> {result['status']}")
            print("Dry-run PNGs are for tests/previews only and are not publish-ready final art.")
        handoff_requested = (
            args.generate_images
            or args.prepare_image_handoff
            or args.proof_slide is not None
            or bool(args.proof_format)
        )
        if handoff_requested and args.image_backend == "codex-built-in":
            capability = write_generation_capability(out_dir)
            result = prepare_codex_builtin_image_generation(
                out_dir,
                proof_slide=args.proof_slide,
                formats=args.proof_format,
            )
            print(f"Codex built-in image handoff only -> {result['status']}")
            print("No final PNGs were generated by this command.")
            print(f"Generation capability -> {capability['package_terminal_state']}")
            print(f"Image-generation blocker -> {out_dir / 'image-generation-blocker.md'}")
        state = derive_carousel_state(out_dir)
        print(f"Package state -> {state.name}; next action -> {state.next_action}")
        print(f"\nCodex-native carousel package saved -> {out_dir}")


if __name__ == "__main__":
    main()
