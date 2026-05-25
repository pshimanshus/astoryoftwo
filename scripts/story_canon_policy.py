"""Shared safety policy for Layer E story-canon source handling."""

from __future__ import annotations

from typing import Any


ALLOWED_USES = {
    "citation",
    "derived_patterns",
    "discovery_reference_only",
    "full_text_analysis",
    "ingestion_rules",
    "internal_research",
    "metadata_analysis",
    "short_quotes",
    "short_summary",
    "source_discovery",
    "visual_reference_review",
}

RESTRICTED_FULL_TEXT_LICENSE_TOKENS = {
    "api",
    "copyright",
    "dataset",
    "metadata",
    "paid",
    "platform",
    "policy",
    "review",
    "site_reference",
    "terms",
    "unclear",
    "unknown",
    "video_reference",
}

FULL_TEXT_ALLOWED_LICENSES = {
    "public_domain",
    "public_domain_us",
    "public_domain_world",
    "licensed_full_text",
    "user_provided_rights_confirmed",
}

PATTERN_EXCLUSION_ALLOWED_USES = {
    "discovery_reference_only",
    "ingestion_rules",
    "internal_research",
    "source_discovery",
}

PATTERN_EXCLUSION_INGESTION_MODES = {
    "api_metadata_only",
    "dataset_metadata_only",
    "discovery_reference_only",
    "policy_reference",
    "sparql_metadata_only",
}

PATTERN_EXCLUSION_LICENSE_TOKENS = {
    "api",
    "dataset",
    "metadata_terms",
    "policy",
}


def normalized_license_status(source: dict[str, Any] | str) -> str:
    if isinstance(source, dict):
        value = source.get("license_status", "")
    else:
        value = source
    return str(value).strip().lower()


def normalize_allowed_use(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(item).strip() for item in value if str(item).strip()]


def unknown_allowed_uses(source: dict[str, Any]) -> list[str]:
    return sorted(
        item for item in normalize_allowed_use(source.get("allowed_use")) if item not in ALLOWED_USES
    )


def license_allows_full_text(source: dict[str, Any] | str) -> bool:
    license_status = normalized_license_status(source)
    if not license_status:
        return False
    if any(token in license_status for token in RESTRICTED_FULL_TEXT_LICENSE_TOKENS):
        return False
    return license_status in FULL_TEXT_ALLOWED_LICENSES or license_status.startswith("public_domain")


def has_full_text_violation(source: dict[str, Any]) -> bool:
    return "full_text_analysis" in normalize_allowed_use(source.get("allowed_use")) and not license_allows_full_text(source)


def source_is_discovery_only(source: dict[str, Any]) -> bool:
    allowed_use = set(normalize_allowed_use(source.get("allowed_use")))
    if "discovery_reference_only" in allowed_use:
        return True
    if allowed_use and allowed_use <= {"citation", "discovery_reference_only", "source_discovery"}:
        return True
    return str(source.get("ingestion_mode", "")).strip().lower() == "discovery_reference_only"


def source_should_generate_patterns(source: dict[str, Any]) -> bool:
    allowed_use = set(normalize_allowed_use(source.get("allowed_use")))
    ingestion_mode = str(source.get("ingestion_mode", "")).strip().lower()
    license_status = normalized_license_status(source)
    source_id = str(source.get("id", "")).strip().lower()
    title = str(source.get("title", "")).strip().lower()

    if source_is_discovery_only(source):
        return False
    if allowed_use & PATTERN_EXCLUSION_ALLOWED_USES and "derived_patterns" not in allowed_use:
        return False
    if ingestion_mode in PATTERN_EXCLUSION_INGESTION_MODES:
        return False
    if any(token in license_status for token in PATTERN_EXCLUSION_LICENSE_TOKENS):
        return False
    if any(token in source_id for token in ("api", "dataset", "policy")):
        return False
    if any(token in title for token in ("api", "dataset", "policy", "metadata query")):
        return False
    return "derived_patterns" in allowed_use
