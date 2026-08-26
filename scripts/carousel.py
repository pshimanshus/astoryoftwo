#!/usr/bin/env python3
"""Canonical Codex-first carousel lifecycle command.

Repository code prepares and binds work. Codex performs image generation and
pixel inspection outside this process, then passes the exact files and authored
QA back through this command. No renderer, API key, OCR, or backend integration
lives here.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Sequence


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from pipeline.stages.carousel_format_contract import locked_formats  # noqa: E402
from pipeline.stages.carousel_generation_state import (  # noqa: E402
    PUBLIC_STATUSES,
    canonical_state_and_next_action,
)
from pipeline.stages.codex_native_carousel import create_codex_native_carousel  # noqa: E402


CLI_SCHEMA_VERSION = "carousel-cli/v1"
CANONICAL_STATES = frozenset(PUBLIC_STATUSES)
FAILED_EXIT_STATES = {"blocked", "proof_failed", "final_qa_failed"}


class CliInputError(ValueError):
    """Input error rendered through the versioned JSON response."""


class JsonArgumentParser(argparse.ArgumentParser):
    def error(self, message: str) -> None:
        raise CliInputError(message)


def _core_read(package_dir: Path) -> dict[str, Any]:
    from pipeline.stages.codex_builtin_image_generation import reconcile_package_state

    return reconcile_package_state(package_dir)


def _core_prepare(
    package_dir: Path,
    *,
    proof_slide: int | None,
    formats: list[str] | None,
) -> dict[str, Any]:
    from pipeline.stages.codex_builtin_image_generation import (
        prepare_codex_builtin_image_generation,
    )

    return prepare_codex_builtin_image_generation(
        package_dir,
        proof_slide=proof_slide,
        formats=formats,
    )


def _core_ingest(
    package_dir: Path,
    generated_paths_by_format: dict[str, list[Path]],
    *,
    proof_slide: int | None,
) -> dict[str, Any]:
    from pipeline.stages.codex_builtin_image_generation import ingest_generated_outputs

    return ingest_generated_outputs(
        package_dir,
        generated_paths_by_format,
        proof_slide=proof_slide,
    )


def _core_review(package_dir: Path, qa_path: Path) -> dict[str, Any]:
    from pipeline.stages.codex_builtin_image_generation import review_quarantined_outputs

    state = _core_read(package_dir)
    if state.get("schema_version") != "carousel-generation-state/v3":
        raise CliInputError(
            "Archived v2 carousel packages are read-only; create a new v3 package."
        )
    status = _canonical_state(state)
    if status == "proof_qa_required":
        target = package_dir / "proof-qa.json"
    elif status == "final_qa_required":
        target = package_dir / "visual-qa.json"
    else:
        raise CliInputError("No current proof or final candidate is awaiting pixel QA")
    authored = json.loads(qa_path.read_text(encoding="utf-8"))
    if not isinstance(authored, dict):
        raise CliInputError("QA input must contain one JSON object")
    temporary = target.with_name(target.name + ".tmp")
    temporary.write_text(
        json.dumps(authored, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    temporary.replace(target)
    return review_quarantined_outputs(package_dir)


def _core_approve(
    package_dir: Path,
    approved_by: str,
    proof_sha256: str,
) -> dict[str, Any]:
    from pipeline.stages.codex_builtin_image_generation import approve_proof

    return approve_proof(
        package_dir,
        approved_by=approved_by,
        proof_sha256=proof_sha256,
    )


def _core_finalize(package_dir: Path) -> dict[str, Any]:
    from pipeline.stages.codex_builtin_image_generation import finalize_codex_builtin_outputs

    return finalize_codex_builtin_outputs(package_dir)


def _canonical_state(state: dict[str, Any]) -> str:
    value, _ = canonical_state_and_next_action(state)
    return value if value in CANONICAL_STATES else "blocked"


def _response(package_dir: Path | None, state: dict[str, Any]) -> dict[str, Any]:
    package = package_dir.expanduser().resolve() if package_dir is not None else None
    status, canonical_next_action = canonical_state_and_next_action(state)
    if status not in CANONICAL_STATES:
        status = "blocked"
    selected_formats = state.get("selected_formats")
    if not isinstance(selected_formats, list) and package is not None and package.is_dir():
        try:
            selected_formats = list(locked_formats(package))
        except (OSError, ValueError):
            selected_formats = []
    reason = str(state.get("reason") or "").strip()
    payload: dict[str, Any] = {
        "schema_version": CLI_SCHEMA_VERSION,
        "package_dir": str(package) if package is not None else "",
        "state": status,
        "next_action": canonical_next_action,
        "selected_slides": [int(value) for value in state.get("selected_slides") or []],
        "selected_formats": [str(value) for value in selected_formats or []],
    }
    if reason:
        payload["reason"] = reason
    if status == "awaiting_creator_proof_approval" and package is not None:
        from pipeline.stages.codex_builtin_image_generation import (
            current_proof_binding_sha256,
        )

        payload["proof_sha256"] = current_proof_binding_sha256(package)
    return payload


def _emit(package_dir: Path | None, state: dict[str, Any]) -> int:
    payload = _response(package_dir, state)
    print(json.dumps(payload, ensure_ascii=False, sort_keys=True))
    return 2 if payload["state"] in FAILED_EXIT_STATES else 0


def _read_story(args: argparse.Namespace) -> str:
    if args.story_file:
        path = Path(args.story_file).expanduser()
        if not path.is_file():
            raise CliInputError(f"Story file not found: {path}")
        return path.read_text(encoding="utf-8")
    return str(args.story or "")


def _generated_paths(args: argparse.Namespace) -> dict[str, list[Path]]:
    supplied = {
        "instagram_post": args.instagram_post,
        "reels_stories": args.reels_stories,
        "square": args.square,
    }
    return {
        output_format: [Path(value).expanduser() for value in values]
        for output_format, values in supplied.items()
        if values
    }


def _run_create(args: argparse.Namespace) -> tuple[Path, dict[str, Any]]:
    story = _read_story(args)
    if not story.strip():
        raise CliInputError("create requires --story or --story-file with non-empty text")
    should_prepare = args.prepare_proof or args.proof_slide is not None
    if should_prepare and not args.creative_brief:
        raise CliInputError("--prepare-proof requires a locked --creative-brief")
    package_dir = create_codex_native_carousel(
        story=story,
        image_paths=args.story_images,
        identity_image_paths=args.identity_images,
        style_reference_paths=args.style_references,
        title=args.title,
        slide_count=args.slide_count,
        style_brief=args.style_brief,
        output_root=args.output_root,
        creative_baseline_path=args.creative_brief,
        requested_formats=args.formats,
    )
    if should_prepare:
        return package_dir, _core_prepare(
            package_dir,
            proof_slide=args.proof_slide,
            formats=args.formats,
        )
    return package_dir, _core_read(package_dir)


def _run(args: argparse.Namespace) -> tuple[Path, dict[str, Any]]:
    if args.command == "create":
        return _run_create(args)
    package_dir = Path(args.package_dir).expanduser()
    if not package_dir.is_dir():
        raise CliInputError(f"Carousel package not found: {package_dir}")
    if args.command == "prepare":
        return package_dir, _core_prepare(
            package_dir,
            proof_slide=args.proof_slide,
            formats=args.formats,
        )
    if args.command == "ingest":
        paths = _generated_paths(args)
        if not paths:
            raise CliInputError("ingest requires at least one generated image path")
        return package_dir, _core_ingest(
            package_dir,
            paths,
            proof_slide=args.proof_slide,
        )
    if args.command == "review":
        qa_path = Path(args.qa).expanduser()
        if not qa_path.is_file():
            raise CliInputError(f"QA file not found: {qa_path}")
        return package_dir, _core_review(package_dir, qa_path)
    if args.command == "approve":
        approved_by = str(args.approved_by or "").strip()
        if not approved_by:
            raise CliInputError("approve requires a non-empty --approved-by")
        return package_dir, _core_approve(
            package_dir,
            approved_by,
            str(args.proof_sha256),
        )
    if args.command == "status":
        return package_dir, _core_read(package_dir)
    if args.command == "finalize":
        return package_dir, _core_finalize(package_dir)
    raise CliInputError(f"Unsupported command: {args.command}")


def build_parser() -> argparse.ArgumentParser:
    parser = JsonArgumentParser(description="Run the Codex-first carousel lifecycle.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    create = subparsers.add_parser("create", help="Create the minimal package.")
    story_source = create.add_mutually_exclusive_group(required=True)
    story_source.add_argument("--story")
    story_source.add_argument("--story-file")
    create.add_argument("--title")
    create.add_argument(
        "--slide-count",
        type=int,
        default=None,
        help="Optional explicit cap; omitted preserves every supplied story beat.",
    )
    create.add_argument("--story-image", "--image", dest="story_images", action="append", default=[])
    create.add_argument("--identity-image", dest="identity_images", action="append", default=None)
    create.add_argument("--style-reference", dest="style_references", action="append", default=None)
    create.add_argument("--style-brief")
    create.add_argument("--creative-brief", "--creative-brief-file", dest="creative_brief")
    create.add_argument("--output-root", type=Path, default=Path("output") / "carousels")
    create.add_argument("--prepare-proof", action="store_true")
    create.add_argument("--proof-slide", type=int)
    create.add_argument(
        "--format",
        dest="formats",
        choices=("instagram_post", "reels_stories", "square"),
        action="append",
        default=None,
    )

    prepare = subparsers.add_parser("prepare", help="Compile proof or remaining-slide prompts.")
    prepare.add_argument("package_dir")
    prepare.add_argument("--proof-slide", type=int)
    prepare.add_argument(
        "--format",
        dest="formats",
        choices=("instagram_post", "reels_stories", "square"),
        action="append",
        default=None,
    )

    ingest = subparsers.add_parser("ingest", help="Quarantine exact Codex imagegen outputs.")
    ingest.add_argument("package_dir")
    ingest.add_argument("--instagram-post", action="append", default=[])
    ingest.add_argument("--reels-stories", action="append", default=[])
    ingest.add_argument("--square", action="append", default=[])
    ingest.add_argument("--proof-slide", type=int)

    review = subparsers.add_parser("review", help="Validate and bind externally authored pixel QA.")
    review.add_argument("package_dir")
    review.add_argument("--qa", required=True)

    approve = subparsers.add_parser("approve", help="Embed hash-bound creator proof approval.")
    approve.add_argument("package_dir")
    approve.add_argument("--approved-by", default="creator")
    approve.add_argument(
        "--proof-sha256",
        required=True,
        help="Exact proof binding returned by review/status; stale values are rejected.",
    )

    status = subparsers.add_parser("status", help="Return canonical state and next action.")
    status.add_argument("package_dir")

    finalize = subparsers.add_parser("finalize", help="Audit hidden candidates and promote atomically.")
    finalize.add_argument("package_dir")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    package_hint: Path | None = None
    try:
        args = build_parser().parse_args(argv)
        raw_package = getattr(args, "package_dir", None)
        package_hint = Path(raw_package).expanduser() if raw_package else None
        package_dir, state = _run(args)
        return _emit(package_dir, state)
    except (CliInputError, ImportError, OSError, json.JSONDecodeError, ValueError) as exc:
        return _emit(
            package_hint,
            {
                "status": "blocked",
                "next_action": "repair_inputs",
                "selected_slides": [],
                "selected_formats": [],
                "reason": str(exc),
            },
        )


if __name__ == "__main__":
    raise SystemExit(main())
