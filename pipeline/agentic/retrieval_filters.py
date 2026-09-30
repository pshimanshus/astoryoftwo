"""Shared query controls for every retrieval backend."""
from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Collection

SCOPE_FILTER_RE = re.compile(r"\bscope:(workflow|package|slide|asset|copy|global|research)\b")
PACKAGE_FILTER_RE = re.compile(
    r"(?<![A-Za-z0-9_])package:(?:\"([^\"]+)\"|'([^']+)'|([A-Za-z0-9_./-]+))"
)
ROLE_FILTER_RE = re.compile(r"\brole:([A-Za-z0-9_.-]+)\b")


@dataclass(frozen=True)
class RetrievalFilters:
    lexical_query: str
    scope: str = ""
    package: str = ""
    role: str = ""


def parse_retrieval_filters(query: str) -> RetrievalFilters:
    scope_match = SCOPE_FILTER_RE.search(query)
    package_match = PACKAGE_FILTER_RE.search(query)
    role_match = ROLE_FILTER_RE.search(query)
    package = ""
    if package_match:
        package = next((value for value in package_match.groups() if value), "").strip("/")
    lexical = SCOPE_FILTER_RE.sub(" ", query)
    lexical = PACKAGE_FILTER_RE.sub(" ", lexical)
    lexical = ROLE_FILTER_RE.sub(" ", lexical)
    return RetrievalFilters(
        lexical_query=" ".join(lexical.split()),
        scope=scope_match.group(1) if scope_match else "",
        package=package,
        role=role_match.group(1) if role_match else "",
    )


def package_matches(candidate: str, requested: str) -> bool:
    normalized = str(candidate or "").strip("/")
    return not requested or normalized == requested or normalized.endswith("/" + requested)


def record_is_eligible(
    *, package: str, eligible_roles: Collection[str], filters: RetrievalFilters,
) -> bool:
    if not package_matches(package, filters.package):
        return False
    roles = set(eligible_roles)
    return not filters.role or "*" in roles or filters.role in roles


def scope_priority(candidate: str, requested: str) -> int:
    """Scope is a ranking preference, preserving established broad recall."""
    return 1 if requested and candidate == requested else 0
