#!/usr/bin/env python3
"""Safe metadata-only ingestion for the story-canon source register."""

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

try:
    from scripts.story_canon_policy import ALLOWED_USES, has_full_text_violation, unknown_allowed_uses
except ModuleNotFoundError:  # pragma: no cover - direct script execution fallback
    from story_canon_policy import ALLOWED_USES, has_full_text_violation, unknown_allowed_uses


DEFAULT_SOURCE_REGISTER = Path("config/references/story-selling-canon/source-register.json")
DEFAULT_OUTPUT_DIR = Path("corpus/story-canon")
SOURCE_TYPES = {"book", "film", "article", "craft_article", "story_selling_framework"}
ARTICLE_SOURCE_TYPES = {"article", "craft_article", "story_selling_framework"}
PARSED_DIRS = {
    "book": "books",
    "film": "films",
    "article": "articles",
    "craft_article": "articles",
    "story_selling_framework": "articles",
}
REQUIRED_FIELDS = {
    "id",
    "type",
    "title",
    "source_url",
    "license_status",
    "allowed_use",
    "confidence",
}


def read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise ValueError(f"Source register not found: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def validate_source(source: dict[str, Any]) -> None:
    missing = sorted(field for field in REQUIRED_FIELDS if field not in source)
    source_id = source.get("id", "<missing id>")
    if missing:
        raise ValueError(f"Source {source_id} missing required fields: {', '.join(missing)}")

    source_type = source["type"]
    if source_type not in SOURCE_TYPES:
        raise ValueError(f"Source {source_id} has unsupported type: {source_type}")

    allowed_use = source["allowed_use"]
    if not isinstance(allowed_use, list):
        raise ValueError(f"Source {source_id} allowed_use must be a list")
    unknown_uses = unknown_allowed_uses(source)
    if unknown_uses:
        raise ValueError(
            f"Source {source_id} has unsupported allowed_use values: "
            f"{', '.join(unknown_uses)}. Allowed values: {', '.join(sorted(ALLOWED_USES))}"
        )
    if has_full_text_violation(source):
        raise ValueError(
            f"Source {source_id} has license_status={source['license_status']} but "
            "allowed_use contains full_text_analysis"
        )


def load_source_register(source_register: Path) -> list[dict[str, Any]]:
    data = read_json(source_register)
    sources = data.get("sources")
    if not isinstance(sources, list):
        raise ValueError("Source register must be shaped like {'sources': [...]}")
    for source in sources:
        if not isinstance(source, dict):
            raise ValueError("Every source register entry must be an object")
        validate_source(source)
    return sources


def select_sources(
    sources: list[dict[str, Any]],
    source_type: str,
    max_sources: int | None,
) -> list[dict[str, Any]]:
    if source_type != "all" and source_type not in {"book", "film", "article"}:
        raise ValueError("--type must be one of book, film, article, all")
    selected = [
        source for source in sources
        if source_type == "all"
        or source["type"] == source_type
        or (source_type == "article" and source["type"] in ARTICLE_SOURCE_TYPES)
    ]
    selected.sort(key=lambda source: (source.get("priority", 9999), source["id"]))
    if max_sources is not None:
        if max_sources < 0:
            raise ValueError("--max-sources must be zero or greater")
        selected = selected[:max_sources]
    return selected


def plan_ingestion(source: dict[str, Any]) -> dict[str, Any]:
    source_url = source.get("source_url", "")
    ingestion_mode = source.get("ingestion_mode", "metadata_only")
    notes = "Metadata-only ingestion. Network fetching is disabled by default."
    fetch_status = "metadata_only"

    if "gutenberg.org" in source_url or ingestion_mode == "robot_harvest_or_manual_seed":
        fetch_status = "planned_not_fetched"
        notes = (
            "Project Gutenberg source is planned for robot-approved harvest or manual seed; "
            "human pages are not scraped."
        )
    elif source.get("type") in ARTICLE_SOURCE_TYPES:
        notes = "Article source stores source metadata, short summary, tags, and extraction notes only."
    elif "openlibrary.org" in source_url:
        notes = "Open Library source stores metadata only; bulk work should use approved dumps."

    return {
        "id": source["id"],
        "type": source["type"],
        "title": source["title"],
        "source_url": source_url,
        "ingestion_mode": ingestion_mode,
        "fetch_status": fetch_status,
        "network_fetch": False,
        "notes": notes,
    }


def build_source_card(source: dict[str, Any], scraped_at: str) -> dict[str, Any]:
    return {
        "id": source["id"],
        "type": source["type"],
        "title": source["title"],
        "creator": source.get("creator"),
        "source_url": source["source_url"],
        "license_status": source["license_status"],
        "allowed_use": source["allowed_use"],
        "ingestion_mode": source.get("ingestion_mode", "metadata_only"),
        "priority": source.get("priority"),
        "confidence": source["confidence"],
        "scraped_at": scraped_at,
        "content_policy": "metadata_only_no_full_text_fetch",
    }


def build_parsed_metadata(source: dict[str, Any], scraped_at: str) -> dict[str, Any]:
    planned = plan_ingestion(source)
    return {
        "id": source["id"],
        "type": source["type"],
        "title": source["title"],
        "creator": source.get("creator"),
        "source_url": source["source_url"],
        "license_status": source["license_status"],
        "allowed_use": source["allowed_use"],
        "confidence": source["confidence"],
        "scraped_at": scraped_at,
        "content_policy": "metadata_only_no_full_text_fetch",
        "fetch_status": planned["fetch_status"],
        "network_fetch": False,
        "body_text": None,
        "summary": source.get("summary"),
        "process_tags": source.get("process_tags", []),
        "extraction_notes": source.get("extraction_notes", []),
        "metadata": {
            key: value
            for key, value in source.items()
            if key not in {"summary", "process_tags", "extraction_notes"}
        },
    }


def ingest_story_canon(
    source_register: Path = DEFAULT_SOURCE_REGISTER,
    source_type: str = "all",
    dry_run: bool = False,
    max_sources: int | None = None,
    output_dir: Path = DEFAULT_OUTPUT_DIR,
) -> dict[str, Any]:
    sources = load_source_register(source_register)
    selected = select_sources(sources, source_type, max_sources)
    plans = [plan_ingestion(source) for source in selected]

    if dry_run:
        return {
            "mode": "dry_run",
            "source_register": str(source_register),
            "output_dir": str(output_dir),
            "selected_count": len(selected),
            "sources": plans,
        }

    scraped_at = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    written_files: list[str] = []
    for source in selected:
        source_card_path = output_dir / "source-cards" / f"{source['id']}.json"
        parsed_path = output_dir / "parsed" / PARSED_DIRS[source["type"]] / f"{source['id']}.json"
        write_json(source_card_path, build_source_card(source, scraped_at))
        write_json(parsed_path, build_parsed_metadata(source, scraped_at))
        written_files.extend([str(source_card_path), str(parsed_path)])

    return {
        "mode": "ingest",
        "source_register": str(source_register),
        "output_dir": str(output_dir),
        "selected_count": len(selected),
        "written_count": len(written_files),
        "written_files": written_files,
        "sources": plans,
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Safely ingest story-canon source metadata without full-text scraping.",
    )
    parser.add_argument(
        "--source-register",
        type=Path,
        default=DEFAULT_SOURCE_REGISTER,
        help="Path to source-register.json shaped like {'sources': [...]}",
    )
    parser.add_argument(
        "--type",
        choices=["book", "film", "article", "all"],
        default="all",
        help="Source type to ingest.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print the ingestion plan and write no source-card or parsed files.",
    )
    parser.add_argument(
        "--max-sources",
        type=int,
        default=None,
        help="Maximum number of selected sources to plan or ingest.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=DEFAULT_OUTPUT_DIR,
        help="Output directory for story-canon artifacts.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        result = ingest_story_canon(
            source_register=args.source_register,
            source_type=args.type,
            dry_run=args.dry_run,
            max_sources=args.max_sources,
            output_dir=args.output_dir,
        )
    except ValueError as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 1

    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
