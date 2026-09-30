from __future__ import annotations

import copy
import hashlib
import json
import re
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[2]
CONTRACT_PATH = PROJECT_ROOT / "config" / "carousel_style_contract.json"
ACTIVE_STYLE_PROFILE_ID = "cinematic-observational-watercolor"
ACTIVE_STYLE_PROFILE_VERSION = "1.0.0"
_SHA256_PATTERN = re.compile(r"^sha256:[0-9a-f]{64}$")
_LEGACY_STYLE_KEYS = {
    "shared_style_prompt",
    "compact_style_prompt",
    "shared_negative_prompt",
    "style_references",
    "style_reference_attachment_limit",
}


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return f"sha256:{digest.hexdigest()}"


def style_profile_contract_sha256(profile: dict[str, Any]) -> str:
    """Return the stable hash of the exact machine-readable profile fields."""

    payload = json.dumps(
        profile,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    return f"sha256:{hashlib.sha256(payload).hexdigest()}"


def resolve_style_profile_reference_path(
    profile: dict[str, Any],
    *,
    project_root: Path = PROJECT_ROOT,
) -> Path:
    """Resolve the declared repo-relative board without permitting path escape."""

    reference = profile.get("reference")
    if not isinstance(reference, dict):
        raise ValueError("Active illustration style profile reference must be an object.")
    raw_path = reference.get("path")
    if not isinstance(raw_path, str) or not raw_path.strip():
        raise ValueError("Active illustration style profile reference.path is required.")
    relative_path = Path(raw_path)
    if relative_path.is_absolute():
        raise ValueError("Active illustration style profile reference.path must be repo-relative.")

    root = project_root.resolve()
    resolved = (root / relative_path).resolve()
    try:
        resolved.relative_to(root)
    except ValueError as exc:
        raise ValueError(
            "Active illustration style profile reference.path escapes the project root."
        ) from exc
    return resolved


def _validate_active_style_profile(
    profile: Any,
    *,
    project_root: Path,
) -> dict[str, Any]:
    if not isinstance(profile, dict):
        raise ValueError("Style contract style_profile must be an object.")

    required = (
        "id",
        "version",
        "status",
        "generation_prompt",
        "negative_prompt",
        "reference",
    )
    missing = [key for key in required if not profile.get(key)]
    if missing:
        raise ValueError(
            "Active illustration style profile missing required keys: "
            + ", ".join(missing)
        )
    if profile["id"] != ACTIVE_STYLE_PROFILE_ID:
        raise ValueError(
            "Unsupported active illustration style profile id: "
            f"{profile['id']!r}; expected {ACTIVE_STYLE_PROFILE_ID!r}."
        )
    if profile["version"] != ACTIVE_STYLE_PROFILE_VERSION:
        raise ValueError(
            "Unsupported active illustration style profile version: "
            f"{profile['version']!r}; expected {ACTIVE_STYLE_PROFILE_VERSION!r}."
        )
    if profile["status"] != "active":
        raise ValueError("The illustration style profile must have status 'active'.")
    for key in ("generation_prompt", "negative_prompt"):
        if not isinstance(profile[key], str) or not profile[key].strip():
            raise ValueError(f"Active illustration style profile {key} must be text.")

    reference = profile["reference"]
    if not isinstance(reference, dict):
        raise ValueError("Active illustration style profile reference must be an object.")
    reference_missing = [
        key for key in ("path", "sha256", "attachment_count") if reference.get(key) in (None, "")
    ]
    if reference_missing:
        raise ValueError(
            "Active illustration style profile reference missing required keys: "
            + ", ".join(reference_missing)
        )
    if reference["attachment_count"] != 1 or isinstance(
        reference["attachment_count"], bool
    ):
        raise ValueError(
            "Active illustration style profile must declare exactly one style attachment."
        )
    declared_hash = reference["sha256"]
    if not isinstance(declared_hash, str) or not _SHA256_PATTERN.fullmatch(declared_hash):
        raise ValueError(
            "Active illustration style profile reference.sha256 must be "
            "'sha256:' followed by 64 lowercase hexadecimal characters."
        )

    resolved = resolve_style_profile_reference_path(profile, project_root=project_root)
    if not resolved.is_file():
        raise ValueError(f"Active illustration style reference is missing: {resolved}")
    actual_hash = _sha256(resolved)
    if actual_hash != declared_hash:
        raise ValueError(
            "Active illustration style reference hash mismatch: "
            f"expected {declared_hash}, got {actual_hash}."
        )
    return profile


def load_style_contract(
    path: Path = CONTRACT_PATH,
    *,
    project_root: Path | None = None,
) -> dict[str, Any]:
    contract_path = Path(path).resolve()
    root = project_root.resolve() if project_root is not None else contract_path.parent.parent
    contract = json.loads(contract_path.read_text(encoding="utf-8"))
    if not isinstance(contract, dict):
        raise ValueError("Style contract root must be an object.")
    required = [
        "schema_version",
        "north_star",
        "brandmark",
        "canonical_illustration_master_prompt",
        "style_profile",
        "typography",
        "characters",
        "identity_reference_policy",
        "visual_story_policy",
        "content_lanes",
        "production_gate",
    ]
    missing = [key for key in required if not contract.get(key)]
    if missing:
        raise ValueError("Style contract missing required keys: " + ", ".join(missing))
    if contract["schema_version"] != "3.0":
        raise ValueError("Style contract schema_version must be '3.0'.")
    retired = sorted(_LEGACY_STYLE_KEYS.intersection(contract))
    if retired:
        raise ValueError(
            "Style contract contains retired duplicate style keys: " + ", ".join(retired)
        )
    _validate_active_style_profile(contract["style_profile"], project_root=root)
    return contract


def load_active_illustration_style_profile(
    path: Path = CONTRACT_PATH,
    *,
    project_root: Path | None = None,
) -> dict[str, Any]:
    """Load the only active style profile, or fail before package generation."""

    contract = load_style_contract(path, project_root=project_root)
    return copy.deepcopy(contract["style_profile"])


def build_character_bible(contract: dict[str, Any] | None = None) -> str:
    contract = contract or load_style_contract()
    aachu = contract["characters"]["aachu"]
    zuv = contract["characters"]["zuv"]
    aachu_cues = ", ".join(aachu["visual_cues"])
    zuv_cues = ", ".join(zuv["visual_cues"])
    return (
        f"Aachu/Anchal: {aachu_cues}; she is the {aachu['relationship_role']}. "
        f"Zuv/Himanshu: {zuv_cues}; he is the {zuv['relationship_role']}. "
        "Together: she is the spark, he is the steady flame; the humor must feel tender underneath."
    )
