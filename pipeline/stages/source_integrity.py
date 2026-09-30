"""Immutable raw-source registry and small safe-write primitives for A1-A4."""

from __future__ import annotations

import hashlib
import json
import os
import tempfile
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Iterator

try:  # POSIX is the supported production environment; keep imports test-friendly.
    import fcntl
except ImportError:  # pragma: no cover
    fcntl = None  # type: ignore[assignment]


REGISTRY_RELATIVE_PATH = Path("corpus/integrity/raw-snapshots.json")
REGISTRY_SCHEMA_VERSION = 1


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


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
        if not isinstance(raw_path, str) or not raw_path.startswith("corpus/raw/"):
            errors.append(f"{label} raw_path must stay under corpus/raw")
            continue
        if raw_path in seen_paths:
            errors.append(f"{label} duplicates raw_path {raw_path}")
        seen_paths.add(raw_path)
        if not isinstance(digest, str) or len(digest) != 64:
            errors.append(f"{label} sha256 is invalid")
            continue
        if snapshot_id != digest:
            errors.append(f"{label} snapshot_id must equal sha256")
        if snapshot_id in seen_ids:
            errors.append(f"{label} duplicates snapshot_id {snapshot_id}")
        seen_ids.add(str(snapshot_id))
        target = root / raw_path
        if not target.is_file():
            errors.append(f"{label} raw snapshot is missing: {raw_path}")
            continue
        actual = sha256_bytes(target.read_bytes())
        if actual != digest:
            errors.append(f"{label} raw snapshot hash mismatch: {raw_path}")
    return errors


def snapshot_for_raw(root: Path, raw_path: Path) -> dict[str, Any] | None:
    relative = relative_to_root(raw_path, root)
    for snapshot in load_raw_snapshot_registry(root).get("snapshots", []):
        if isinstance(snapshot, dict) and snapshot.get("raw_path") == relative:
            return dict(snapshot)
    return None


def register_raw_snapshot(root: Path, raw_path: Path, item_count: int) -> dict[str, Any]:
    """Append one immutable record, rejecting a changed file at an existing path."""
    root = root.resolve()
    raw_path = raw_path.resolve()
    relative = relative_to_root(raw_path, root)
    if not relative.startswith("corpus/raw/"):
        raise ValueError("Only corpus/raw files can be registered as immutable snapshots")
    raw_bytes = raw_path.read_bytes()
    digest = sha256_bytes(raw_bytes)
    snapshot = {
        "snapshot_id": digest,
        "raw_path": relative,
        "sha256": digest,
        "bytes": len(raw_bytes),
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
