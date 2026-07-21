#!/usr/bin/env python3
"""Check the two visual-story events inside an existing carousel package."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


WORKSPACE_ROOT = Path(__file__).resolve().parents[4]
if str(WORKSPACE_ROOT) not in sys.path:
    sys.path.insert(0, str(WORKSPACE_ROOT))

from pipeline.stages.carousel_visual_storytelling import (  # noqa: E402
    VISUAL_STORY_READABILITY_KEY,
    current_creator_correction_fingerprint,
    current_generation_payload_fingerprint,
    director_author_id,
    director_creator_correction_fingerprint,
    director_event_fingerprint,
    director_generation_payload_fingerprint,
    director_review_provenance,
    director_reviewer_id,
    storyboard_source_fingerprint,
    validate_director_storyboard,
    validate_frame_readability,
)
from pipeline.stages.carousel_format_contract import (  # noqa: E402
    FORMAT_CONTRACT_FILENAME,
    expected_frame_bindings,
    locked_format_contract_fingerprint,
    locked_formats,
)


def _read_json_value(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        raise ValueError(f"Missing required artifact: {path}") from None
    except json.JSONDecodeError as exc:
        raise ValueError(f"Invalid JSON in {path}: {exc}") from exc


def _slide_records(slides: Any) -> list[dict[str, Any]]:
    if isinstance(slides, list):
        return [record for record in slides if isinstance(record, dict)]
    if isinstance(slides, dict) and isinstance(slides.get("slides"), list):
        return [record for record in slides["slides"] if isinstance(record, dict)]
    return []


def check_package(carousel_dir: Path, phase: str) -> dict[str, Any]:
    slides = _read_json_value(carousel_dir / "slides.json")
    records = _slide_records(slides)
    if not records:
        raise ValueError("slides.json has no slide records.")

    format_contract_path = carousel_dir / FORMAT_CONTRACT_FILENAME
    if not format_contract_path.is_file():
        raise ValueError(
            f"Missing required current-request format contract: {format_contract_path}"
        )

    plan = _read_json_value(carousel_dir / "visual-plan-quality.json")
    if not isinstance(plan, dict):
        raise ValueError("visual-plan-quality.json must contain an object.")
    current_formats = locked_formats(carousel_dir)
    correction_fingerprint = current_creator_correction_fingerprint(carousel_dir)
    generation_fingerprint = current_generation_payload_fingerprint(carousel_dir)

    result: dict[str, Any] = {
        "carousel_dir": str(carousel_dir),
        "phase": phase,
        "source_fingerprint": storyboard_source_fingerprint(slides),
        "locked_native_formats": list(current_formats),
        "checks": {},
    }
    failures: list[str] = []

    # Event B is only meaningful when the exact current Event A still passes.
    # Therefore post-only checks establish Event A currentness too.
    if phase in {"pre", "post", "all"}:
        pre_issues = validate_director_storyboard(
            plan,
            slide_count=len(records),
            expected_slides=slides,
            expected_formats=current_formats,
            expected_format_contract_fingerprint=(
                locked_format_contract_fingerprint(carousel_dir)
            ),
            expected_creator_correction_fingerprint=correction_fingerprint,
            expected_generation_payload_fingerprint=generation_fingerprint,
            provenance_package_dir=carousel_dir,
        )
        result["checks"]["pre_generation_director_storyboard"] = {
            "pass": not pre_issues,
            "issues": pre_issues,
        }
        failures.extend(f"pre: {issue}" for issue in pre_issues)

    if phase in {"post", "all"}:
        qa = _read_json_value(carousel_dir / "visual-qa.json")
        checks = qa.get("checks") if isinstance(qa, dict) else None
        readability = (
            checks.get(VISUAL_STORY_READABILITY_KEY)
            if isinstance(checks, dict)
            else None
        )
        post_issues = validate_frame_readability(
            readability,
            slide_count=len(records),
            required_formats=current_formats,
            expected_director_event_fingerprint=director_event_fingerprint(plan),
            event_a_review_provenance=director_review_provenance(plan),
            event_a_creator_correction_fingerprint=(
                director_creator_correction_fingerprint(plan)
            ),
            expected_creator_correction_fingerprint=correction_fingerprint,
            event_a_generation_payload_fingerprint=(
                director_generation_payload_fingerprint(plan)
            ),
            expected_generation_payload_fingerprint=generation_fingerprint,
            director_author_id=director_author_id(plan),
            director_reviewer_id=director_reviewer_id(plan),
            expected_frame_bindings=expected_frame_bindings(
                carousel_dir,
                len(records),
                current_formats,
            ),
            package_dir=carousel_dir,
            provenance_package_dir=carousel_dir,
            require_files=True,
        )
        result["checks"]["post_generation_visual_story_readability"] = {
            "pass": not post_issues,
            "issues": post_issues,
        }
        failures.extend(f"post: {issue}" for issue in post_issues)

    result["pass"] = not failures
    result["issues"] = failures
    return result


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Validate copy-hidden director and rendered-frame story checks."
    )
    parser.add_argument(
        "--carousel-dir",
        required=True,
        type=Path,
        help="Existing output/carousels/YYYY-MM-DD/slug package directory.",
    )
    parser.add_argument(
        "--phase",
        choices=("pre", "post", "all"),
        default="all",
        help="Lifecycle phase to validate.",
    )
    parser.add_argument(
        "--compact",
        action="store_true",
        help="Print compact JSON instead of indented JSON.",
    )
    return parser


def main() -> int:
    args = build_parser().parse_args()
    carousel_dir = args.carousel_dir.expanduser().resolve()
    try:
        result = check_package(carousel_dir, args.phase)
    except ValueError as exc:
        result = {
            "carousel_dir": str(carousel_dir),
            "phase": args.phase,
            "pass": False,
            "issues": [str(exc)],
        }
    print(
        json.dumps(
            result,
            ensure_ascii=False,
            separators=(",", ":") if args.compact else None,
            indent=None if args.compact else 2,
        )
    )
    return 0 if result.get("pass") else 1


if __name__ == "__main__":
    raise SystemExit(main())
