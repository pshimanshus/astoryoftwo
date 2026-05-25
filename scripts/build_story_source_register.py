import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

try:
    from scripts.story_canon_policy import (
        ALLOWED_USES,
        has_full_text_violation,
        unknown_allowed_uses,
    )
except ModuleNotFoundError:  # pragma: no cover - direct script execution fallback
    from story_canon_policy import ALLOWED_USES, has_full_text_violation, unknown_allowed_uses


DEFAULT_REGISTER = Path("config/references/story-selling-canon/source-register.json")

REQUIRED_FIELDS = {
    "id": str,
    "type": str,
    "title": str,
    "creator": str,
    "source_url": str,
    "license_status": str,
    "allowed_use": list,
    "ingestion_mode": str,
    "priority": int,
    "confidence": (int, float),
    "scraped_at": str,
}


def slugify(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", value.lower())
    return slug.strip("-")


def load_register(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def validate_source(source: dict[str, Any], index: int) -> list[str]:
    errors: list[str] = []
    source_label = source.get("id", f"source[{index}]")

    for field, expected_type in REQUIRED_FIELDS.items():
        if field not in source:
            errors.append(f"{source_label}: missing required field {field}")
            continue
        if not isinstance(source[field], expected_type):
            errors.append(f"{source_label}: field {field} has invalid type")

    confidence = source.get("confidence")
    if isinstance(confidence, (int, float)) and not 0 <= confidence <= 1:
        errors.append(f"{source_label}: confidence must be between 0 and 1")

    allowed_use = source.get("allowed_use")
    if isinstance(allowed_use, list):
        if not allowed_use:
            errors.append(f"{source_label}: allowed_use must be a non-empty list")
        for item in allowed_use:
            if not isinstance(item, str) or not item:
                errors.append(f"{source_label}: allowed_use entries must be non-empty strings")
        for item in unknown_allowed_uses(source):
            errors.append(
                f"{source_label}: allowed_use {item} is not in allowed policy values "
                f"{sorted(ALLOWED_USES)}"
            )
        if has_full_text_violation(source):
            errors.append(
                f"{source_label}: full_text_analysis is not allowed for "
                f"license_status={source.get('license_status')}"
            )

    source_url = source.get("source_url")
    if isinstance(source_url, str) and not source_url.startswith(("https://", "http://")):
        errors.append(f"{source_label}: source_url must be an http or https URL")

    scraped_at = source.get("scraped_at")
    if isinstance(scraped_at, str) and not re.fullmatch(r"\d{4}-\d{2}-\d{2}", scraped_at):
        errors.append(f"{source_label}: scraped_at must be YYYY-MM-DD")

    return errors


def normalize_register(register: dict[str, Any]) -> dict[str, Any]:
    normalized = {"sources": []}
    for source in register["sources"]:
        normalized_source = dict(source)
        normalized_source["id"] = slugify(normalized_source["id"])
        normalized["sources"].append(normalized_source)
    normalized["sources"].sort(key=lambda item: (item["priority"], item["id"]))
    return normalized


def validate_register(register: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if not isinstance(register, dict):
        return ["register root must be an object"]
    if "sources" not in register:
        return ["register must contain sources"]
    if not isinstance(register["sources"], list):
        return ["sources must be a list"]
    if not register["sources"]:
        return ["sources must not be empty"]

    ids: set[str] = set()
    for index, source in enumerate(register["sources"]):
        if not isinstance(source, dict):
            errors.append(f"source[{index}]: must be an object")
            continue
        errors.extend(validate_source(source, index))
        source_id = source.get("id")
        if isinstance(source_id, str):
            normalized_id = slugify(source_id)
            if not normalized_id:
                errors.append(f"source[{index}]: id must contain slug characters")
            if normalized_id in ids:
                errors.append(f"{source_id}: duplicate normalized id {normalized_id}")
            ids.add(normalized_id)
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate and normalize the story-selling source register.")
    parser.add_argument("--source-register", type=Path, default=DEFAULT_REGISTER)
    parser.add_argument("--write", action="store_true", help="Write normalized JSON back to the register.")
    args = parser.parse_args()

    register = load_register(args.source_register)
    errors = validate_register(register)
    if errors:
        for error in errors:
            print(error, file=sys.stderr)
        return 1

    normalized = normalize_register(register)
    if args.write:
        args.source_register.write_text(
            json.dumps(normalized, indent=2, ensure_ascii=True) + "\n",
            encoding="utf-8",
        )

    print(f"validated {len(normalized['sources'])} sources")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
