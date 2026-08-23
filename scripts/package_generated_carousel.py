from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent.parent))

from pipeline.agentic.workflow_doctor import inspect_carousel_package
from pipeline.stages.carousel_format_contract import (
    INSTAGRAM_POST_FORMAT,
    REELS_STORIES_FORMAT,
    SQUARE_FORMAT,
    locked_formats,
)
from pipeline.stages.codex_builtin_image_generation import (
    accept_failed_proof_by_creator,
    package_codex_builtin_outputs,
    promote_quarantined_codex_builtin_outputs,
    recompile_failed_proof_handoff,
)


RETRYABLE_LIFECYCLE_BLOCKERS = {
    "generated_proof_without_structured_qa_v2",
    "quarantined_proof_claims_continuation",
    "qa_pass_without_creator_approval",
    "batch_allowed_without_correct_state",
}


def package_generated_images(
    carousel_dir: Path,
    *,
    instagram_post_paths: list[Path] | None = None,
    reels_stories_paths: list[Path] | None = None,
    square_paths: list[Path] | None = None,
    refresh_quality: bool = False,
    visual_qa_path: Path | None = None,
    creator_approval_path: Path | None = None,
    proof_slide: int | None = None,
) -> dict[str, Any]:
    """Package exactly the native outputs locked by the current request."""

    doctor_report = inspect_carousel_package(carousel_dir)
    hard_blockers = [
        issue
        for issue in doctor_report.issues
        if issue.severity == "blocker"
        and issue.code not in RETRYABLE_LIFECYCLE_BLOCKERS
    ]
    if hard_blockers:
        issue_codes = ", ".join(issue.code for issue in hard_blockers)
        raise ValueError(f"Cannot package generated images for blocked carousel package: {issue_codes}")

    supplied = {
        key: paths
        for key, paths in {
            INSTAGRAM_POST_FORMAT: instagram_post_paths,
            REELS_STORIES_FORMAT: reels_stories_paths,
            SQUARE_FORMAT: square_paths,
        }.items()
        if paths
    }
    return package_codex_builtin_outputs(
        carousel_dir,
        generated_paths_by_format=supplied,
        refresh_quality=refresh_quality,
        visual_qa_path=visual_qa_path,
        creator_approval_path=creator_approval_path,
        proof_slide=proof_slide,
    )


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Package native generated carousel images for exactly the package's locked "
            "current-request formats."
        )
    )
    parser.add_argument("carousel_dir", type=Path)
    parser.add_argument("--instagram-post", dest="instagram_post_paths", action="append", type=Path)
    parser.add_argument("--reels-stories", dest="reels_stories_paths", action="append", type=Path)
    parser.add_argument("--square", dest="square_paths", action="append", type=Path)
    parser.add_argument(
        "--promote-quarantine",
        action="store_true",
        help="Revalidate and promote the existing quarantined image set after QA and creator approval.",
    )
    parser.add_argument(
        "--recompile-failed-proof-handoff",
        action="store_true",
        help=(
            "Atomically recompile the proof-only prompt handoff after persisted failed QA, "
            "without changing the proof lifecycle state or evidence."
        ),
    )
    parser.add_argument(
        "--accept-failed-proof-by-creator",
        action="store_true",
        help=(
            "Allow batch generation from one exact QA-failed proof only after a "
            "hash-bound creator approval explicitly accepts every known QA exception. "
            "This does not mark QA passed or make the proof publishable."
        ),
    )
    parser.add_argument("--visual-qa", dest="visual_qa_path", type=Path)
    parser.add_argument("--creator-approval", dest="creator_approval_path", type=Path)
    parser.add_argument(
        "--proof-slide",
        type=int,
        help=(
            "Quarantine exactly this generated proof slide from a matching proof-only "
            "compiled handoff. No final folders are populated."
        ),
    )
    parser.add_argument(
        "--no-quality-refresh",
        action="store_true",
        help=(
            "Do not run final audit. Creator-approved pixels remain internal and are not "
            "written to publishable final folders."
        ),
    )
    args = parser.parse_args()
    if args.accept_failed_proof_by_creator:
        incompatible = (
            args.instagram_post_paths
            or args.reels_stories_paths
            or args.square_paths
            or args.promote_quarantine
            or args.recompile_failed_proof_handoff
            or args.proof_slide is not None
            or args.visual_qa_path is not None
            or args.no_quality_refresh
        )
        if incompatible:
            parser.error(
                "--accept-failed-proof-by-creator cannot be combined with image paths, "
                "--promote-quarantine, --recompile-failed-proof-handoff, --proof-slide, "
                "--visual-qa, or --no-quality-refresh."
            )
        if args.creator_approval_path is None:
            parser.error(
                "--accept-failed-proof-by-creator requires --creator-approval PATH."
            )
        manifest = accept_failed_proof_by_creator(
            args.carousel_dir,
            args.creator_approval_path,
        )
    elif args.recompile_failed_proof_handoff:
        incompatible = (
            args.instagram_post_paths
            or args.reels_stories_paths
            or args.square_paths
            or args.promote_quarantine
            or args.accept_failed_proof_by_creator
            or args.proof_slide is not None
            or args.visual_qa_path is not None
            or args.creator_approval_path is not None
            or args.no_quality_refresh
        )
        if incompatible:
            parser.error(
                "--recompile-failed-proof-handoff cannot be combined with image paths, "
                "--promote-quarantine, --proof-slide, --visual-qa, --creator-approval, "
                "or --no-quality-refresh."
            )
        manifest = recompile_failed_proof_handoff(args.carousel_dir)
    elif args.promote_quarantine:
        if args.instagram_post_paths or args.reels_stories_paths or args.square_paths:
            parser.error("--promote-quarantine cannot be combined with new generated image paths.")
        if args.proof_slide is not None:
            parser.error(
                "--proof-slide is only for a new proof candidate; quarantine promotion "
                "uses the recorded proof scope."
            )
        manifest = promote_quarantined_codex_builtin_outputs(
            args.carousel_dir,
            refresh_quality=not args.no_quality_refresh,
            visual_qa_path=args.visual_qa_path,
            creator_approval_path=args.creator_approval_path,
        )
    else:
        supplied_formats = {
            key
            for key, paths in {
                INSTAGRAM_POST_FORMAT: args.instagram_post_paths,
                REELS_STORIES_FORMAT: args.reels_stories_paths,
                SQUARE_FORMAT: args.square_paths,
            }.items()
            if paths
        }
        required_formats = set(locked_formats(args.carousel_dir))
        if supplied_formats != required_formats:
            parser.error(
                "new generated images must match the locked format contract exactly; required: "
                + ", ".join(sorted(required_formats))
            )
        manifest = package_generated_images(
            args.carousel_dir,
            instagram_post_paths=args.instagram_post_paths,
            reels_stories_paths=args.reels_stories_paths,
            square_paths=args.square_paths,
            refresh_quality=not args.no_quality_refresh,
            visual_qa_path=args.visual_qa_path,
            creator_approval_path=args.creator_approval_path,
            proof_slide=args.proof_slide,
        )
    print(json.dumps(manifest, indent=2))


if __name__ == "__main__":
    main()
