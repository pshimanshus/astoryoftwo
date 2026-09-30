"""Immutable raw-source registry and small safe-write primitives for A1-A4."""

from __future__ import annotations

import hashlib
import json
import os
import tempfile
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterator

try:  # POSIX is the supported production environment; keep imports test-friendly.
    import fcntl
except ImportError:  # pragma: no cover
    fcntl = None  # type: ignore[assignment]


REGISTRY_RELATIVE_PATH = Path("corpus/integrity/raw-snapshots.json")
REGISTRY_SCHEMA_VERSION = 2
SNAPSHOT_SCHEMA_VERSION = "raw-snapshot/v2"
SOURCE_RECEIPT_SCHEMA_VERSION = "source-receipt/v1"


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def raw_snapshot_id(raw_path: str, content_sha256: str) -> str:
    """Name one immutable capture without conflating it with repeated content."""
    return sha256_bytes(f"{raw_path}\0{content_sha256}".encode("utf-8"))


def relative_to_root(path: Path, root: Path) -> str:
    try:
        return path.resolve().relative_to(root.resolve()).as_posix()
    except ValueError as exc:
        raise ValueError(f"Path escapes workspace root: {path}") from exc


def registry_path(root: Path) -> Path:
    return root.resolve() / REGISTRY_RELATIVE_PATH


def empty_registry() -> dict[str, Any]:
    return {"schema_version": REGISTRY_SCHEMA_VERSION, "snapshots": []}


def load_raw_snapshot_registry(root: Path) -> dict[str, Any]:
    path = registry_path(root)
    if not path.exists():
        return empty_registry()
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("raw snapshot registry must be a JSON object")
    return data


def atomic_write_bytes(path: Path, content: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    try:
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    except BaseException:
        try:
            os.unlink(temporary)
        except FileNotFoundError:
            pass
        raise


def atomic_write_text(path: Path, content: str) -> None:
    atomic_write_bytes(path, content.encode("utf-8"))


@contextmanager
def workspace_lock(root: Path, name: str) -> Iterator[None]:
    """Serialize a shared registry/compiler mutation without leaving lock artifacts."""
    lock_path = root.resolve() / ".locks" / f"{name}.lock"
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    with lock_path.open("a+", encoding="utf-8") as handle:
        if fcntl is not None:
            fcntl.flock(handle.fileno(), fcntl.LOCK_EX)
        try:
            yield
        finally:
            if fcntl is not None:
                fcntl.flock(handle.fileno(), fcntl.LOCK_UN)


def validate_raw_snapshot_registry(root: Path) -> list[str]:
    """Verify that registry records still name and hash immutable raw snapshots."""
    root = root.resolve()
    try:
        registry = load_raw_snapshot_registry(root)
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        return [f"registry unreadable: {exc}"]

    errors: list[str] = []
    if registry.get("schema_version") != REGISTRY_SCHEMA_VERSION:
        errors.append("registry schema_version is unsupported")
    snapshots = registry.get("snapshots")
    if not isinstance(snapshots, list):
        return [*errors, "registry snapshots must be a list"]

    seen_paths: set[str] = set()
    seen_ids: set[str] = set()
    for index, snapshot in enumerate(snapshots):
        label = f"snapshots[{index}]"
        if not isinstance(snapshot, dict):
            errors.append(f"{label} must be an object")
            continue
        raw_path = snapshot.get("raw_path")
        digest = snapshot.get("sha256")
        snapshot_id = snapshot.get("snapshot_id")
        required = {
            "schema_version": SNAPSHOT_SCHEMA_VERSION,
            "source_id": str,
            "source_relative_path": str,
            "collected_at": str,
            "record_count": int,
            "prior_version": (str, type(None)),
        }
        for key, expected in required.items():
            value = snapshot.get(key)
            if key == "schema_version":
                if value != expected:
                    errors.append(f"{label} schema_version is unsupported")
            elif not isinstance(value, expected):
                errors.append(f"{label} {key} is invalid")
        if not isinstance(raw_path, str) or not raw_path.startswith("corpus/raw/"):
            errors.append(f"{label} raw_path must stay under corpus/raw")
            continue
        if snapshot.get("source_relative_path") != raw_path:
            errors.append(f"{label} source_relative_path must match raw_path")
        if raw_path in seen_paths:
            errors.append(f"{label} duplicates raw_path {raw_path}")
        seen_paths.add(raw_path)
        if not isinstance(digest, str) or len(digest) != 64:
            errors.append(f"{label} sha256 is invalid")
            continue
        if snapshot_id != raw_snapshot_id(raw_path, digest):
            errors.append(f"{label} snapshot_id does not bind raw_path and sha256")
        prior_ids = set(seen_ids)
        if snapshot_id in seen_ids:
            errors.append(f"{label} duplicates snapshot_id {snapshot_id}")
        seen_ids.add(str(snapshot_id))
        try:
            datetime.fromisoformat(str(snapshot.get("collected_at", "")).replace("Z", "+00:00"))
        except ValueError:
            errors.append(f"{label} collected_at is not ISO-8601")
        prior = snapshot.get("prior_version")
        if prior is not None and (prior == snapshot_id or prior not in prior_ids):
            errors.append(f"{label} prior_version does not name an earlier snapshot")
        target = root / raw_path
        if not target.is_file():
            errors.append(f"{label} raw snapshot is missing: {raw_path}")
            continue
        actual = sha256_bytes(target.read_bytes())
        if actual != digest:
            errors.append(f"{label} raw snapshot hash mismatch: {raw_path}")
        if snapshot.get("bytes") != target.stat().st_size:
            errors.append(f"{label} byte count mismatch: {raw_path}")
    return errors


def snapshot_for_raw(root: Path, raw_path: Path) -> dict[str, Any] | None:
    relative = relative_to_root(raw_path, root)
    for snapshot in load_raw_snapshot_registry(root).get("snapshots", []):
        if isinstance(snapshot, dict) and snapshot.get("raw_path") == relative:
            return dict(snapshot)
    return None


def register_raw_snapshot(
    root: Path,
    raw_path: Path,
    item_count: int,
    *,
    collected_at: str | None = None,
    prior_version: str | None = None,
) -> dict[str, Any]:
    """Append one immutable record, rejecting a changed file at an existing path."""
    root = root.resolve()
    raw_path = raw_path.resolve()
    relative = relative_to_root(raw_path, root)
    if not relative.startswith("corpus/raw/"):
        raise ValueError("Only corpus/raw files can be registered as immutable snapshots")
    raw_bytes = raw_path.read_bytes()
    digest = sha256_bytes(raw_bytes)
    collected_at = collected_at or datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    if prior_version is None:
        previous = [
            item for item in load_raw_snapshot_registry(root).get("snapshots", [])
            if isinstance(item, dict)
        ]
        prior_version = str(previous[-1]["snapshot_id"]) if previous else None
    snapshot_id = raw_snapshot_id(relative, digest)
    snapshot = {
        "schema_version": SNAPSHOT_SCHEMA_VERSION,
        "snapshot_id": snapshot_id,
        "source_id": f"a1-instagram:{collected_at[:10]}:{snapshot_id[:16]}",
        "source_relative_path": relative,
        "raw_path": relative,
        "sha256": digest,
        "bytes": len(raw_bytes),
        "collected_at": collected_at,
        "record_count": item_count,
        "prior_version": prior_version,
        # Kept for readers written before registry v2.
        "item_count": item_count,
    }
    registry = load_raw_snapshot_registry(root)
    snapshots = registry.setdefault("snapshots", [])
    if not isinstance(snapshots, list):
        raise ValueError("raw snapshot registry snapshots must be a list")
    for existing in snapshots:
        if not isinstance(existing, dict):
            continue
        if existing.get("raw_path") == relative:
            if existing.get("sha256") != digest:
                raise ValueError(f"Immutable raw snapshot collision at {relative}")
            return dict(existing)
    snapshots.append(snapshot)
    registry["schema_version"] = REGISTRY_SCHEMA_VERSION
    atomic_write_text(registry_path(root), json.dumps(registry, indent=2, sort_keys=True) + "\n")
    return snapshot


def source_receipt_path(normalized_path: Path) -> Path:
    return normalized_path.with_suffix(normalized_path.suffix + ".source-receipt.json")


def build_source_receipt(root: Path, raw_path: Path, normalized_path: Path, record_count: int) -> dict[str, Any]:
    provenance = provenance_for_raw(root, raw_path)
    provenance["normalized_posts_path"] = relative_to_root(normalized_path, root)
    return {
        "schema_version": SOURCE_RECEIPT_SCHEMA_VERSION,
        "status": "verified" if provenance.get("status") == "verified" else "unverified_legacy",
        "source_provenance": provenance,
        "raw_path": relative_to_root(raw_path, root),
        "raw_sha256": sha256_bytes(raw_path.read_bytes()),
        "normalized_path": relative_to_root(normalized_path, root),
        "normalized_sha256": sha256_bytes(normalized_path.read_bytes()),
        "record_count": record_count,
    }


def verify_source_receipt(root: Path, normalized_path: Path) -> tuple[dict[str, Any], list[str]]:
    """Verify the A2 output and its complete A1 receipt chain."""
    path = source_receipt_path(normalized_path)
    if not path.is_file():
        return {"status": "unverified_legacy"}, ["A2 source receipt is missing"]
    try:
        receipt = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return {"status": "unverified_legacy"}, [f"A2 source receipt is unreadable: {exc}"]
    errors: list[str] = []
    if not isinstance(receipt, dict) or receipt.get("schema_version") != SOURCE_RECEIPT_SCHEMA_VERSION:
        return {"status": "unverified_legacy"}, ["A2 source receipt schema is unsupported"]
    try:
        relative = relative_to_root(normalized_path, root)
    except ValueError as exc:
        return receipt, [str(exc)]
    if receipt.get("normalized_path") != relative:
        errors.append("A2 source receipt names a different normalized artifact")
    if receipt.get("normalized_sha256") != sha256_bytes(normalized_path.read_bytes()):
        errors.append("A2 normalized artifact hash mismatch")
    provenance = receipt.get("source_provenance")
    if not isinstance(provenance, dict):
        errors.append("A2 source provenance is missing")
    else:
        errors.extend(verify_provenance(root, provenance))
    if receipt.get("status") != "verified":
        errors.append("A2 source receipt is not verified")
    return receipt, errors


def provenance_for_raw(root: Path, raw_path: Path) -> dict[str, Any]:
    """Return explicit provenance even for a legacy manual parse, never guessing trust."""
    snapshot = snapshot_for_raw(root, raw_path)
    actual = sha256_bytes(raw_path.read_bytes())
    relative = relative_to_root(raw_path, root)
    if snapshot and snapshot.get("sha256") == actual:
        return {
            "status": "verified",
            "registry_path": REGISTRY_RELATIVE_PATH.as_posix(),
            "raw_path": relative,
            "raw_sha256": actual,
            "snapshot_id": snapshot["snapshot_id"],
        }
    return {
        "status": "unregistered",
        "registry_path": REGISTRY_RELATIVE_PATH.as_posix(),
        "raw_path": relative,
        "raw_sha256": actual,
        "snapshot_id": None,
    }


def verify_provenance(root: Path, provenance: dict[str, Any]) -> list[str]:
    if provenance.get("status") != "verified":
        return ["provenance status is not verified"]
    raw_path = provenance.get("raw_path")
    snapshot_id = provenance.get("snapshot_id")
    digest = provenance.get("raw_sha256")
    if not isinstance(raw_path, str) or not isinstance(snapshot_id, str) or not isinstance(digest, str):
        return ["provenance is missing raw_path, snapshot_id, or raw_sha256"]
    errors = validate_raw_snapshot_registry(root)
    if errors:
        return errors
    try:
        snapshot = snapshot_for_raw(root, root / raw_path)
    except ValueError as exc:
        return [f"provenance raw_path escapes workspace: {exc}"]
    if snapshot is None:
        return [f"provenance raw snapshot is not registered: {raw_path}"]
    if snapshot.get("snapshot_id") != snapshot_id or snapshot.get("sha256") != digest:
        return ["provenance does not match immutable raw snapshot registry"]
    return []
