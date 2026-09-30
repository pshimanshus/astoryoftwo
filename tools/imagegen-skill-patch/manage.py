#!/usr/bin/env python3
"""Apply the pinned ImageGen maintenance diff without installing a second skill."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import shutil
import tempfile

PACKAGE = Path(__file__).resolve().parent
ALLOWLIST = frozenset({
    "SKILL.md", "scripts/image_gen.py", "references/cli.md",
    "references/image-api.md", "references/visual-repair.md",
    "references/prompting.md", "references/sample-prompts.md", "references/codex-network.md",
})
MARKER = ".imagegen-maintenance.json"


class PatchError(RuntimeError):
    pass


def digest(data):
    return hashlib.sha256(data).hexdigest()


def no_symlinks(path):
    for node in [path, *path.parents]:
        if node.is_symlink():
            raise PatchError(f"Refusing symlink path: {node}")


def _read(path):
    no_symlinks(path)
    if not path.exists():
        return None
    if not path.is_file():
        raise PatchError(f"Expected regular file: {path}")
    return path.read_bytes()


def load_package(package=PACKAGE):
    manifest_bytes = (package / "manifest.json").read_bytes()
    manifest = json.loads(manifest_bytes)
    patch = (package / "imagegen.patch").read_bytes()
    if digest(patch) != manifest["patch_sha256"]:
        raise PatchError("Patch checksum mismatch")
    if manifest["schema_version"] != 1 or set(manifest["files"]) != ALLOWLIST:
        raise PatchError("Manifest path allowlist or schema mismatch")
    # This package deliberately uses one complete-file hunk per path. Parsing
    # bytes preserves exact newlines and avoids an external patch executable.
    lines = patch.splitlines(keepends=True)
    payloads = {}
    i = 0
    while i < len(lines):
        if not lines[i].startswith(b"--- a/") or i + 2 >= len(lines):
            raise PatchError("Invalid unified patch header")
        name = lines[i][6:].rstrip(b"\n").decode()
        if name not in ALLOWLIST or PurePosixPath(name).is_absolute() or name in payloads:
            raise PatchError("Patch path is not allowlisted or is duplicated")
        if lines[i + 1] != f"+++ b/{name}\n".encode():
            raise PatchError("Mismatched unified patch path")
        match = re.fullmatch(rb"@@ -(\d+),(\d+) \+(\d+),(\d+) @@\n", lines[i + 2])
        if not match:
            raise PatchError("Expected a complete-file patch hunk")
        old_start, old_count, new_start, new_count = map(int, match.groups())
        if old_start != (1 if old_count else 0) or new_start != (1 if new_count else 0):
            raise PatchError("Patch hunk must begin at the file start")
        i += 3
        before, after = [], []
        while i < len(lines) and not lines[i].startswith(b"--- a/"):
            line = lines[i]
            if line[:1] not in (b" ", b"+", b"-"):
                raise PatchError("Unsupported patch syntax")
            if line[:1] in (b" ", b"-"):
                before.append(line[1:])
            if line[:1] in (b" ", b"+"):
                after.append(line[1:])
            i += 1
        if len(before) != old_count or len(after) != new_count:
            raise PatchError("Patch line count mismatch")
        old, new = b"".join(before), b"".join(after)
        entry = manifest["files"][name]
        expected_before = entry["before_sha256"]
        if expected_before is None:
            if old:
                raise PatchError("New file unexpectedly contains baseline bytes")
        elif digest(old) != expected_before:
            raise PatchError(f"Source checksum mismatch in patch: {name}")
        if digest(new) != entry["after_sha256"]:
            raise PatchError(f"Target checksum mismatch in patch: {name}")
        payloads[name] = (None if expected_before is None else old, new)
    if set(payloads) != ALLOWLIST:
        raise PatchError("Patch file set does not match allowlist")
    if manifest["marker"] not in payloads["SKILL.md"][1].decode():
        raise PatchError("Skill maintenance marker missing from target")
    marker = (json.dumps({"patch_id": manifest["patch_id"],
                         "manifest_sha256": digest(manifest_bytes)}, sort_keys=True) + "\n").encode()
    return manifest, payloads, marker


def inspect_target(target, payloads, marker):
    no_symlinks(target)
    if not target.is_dir():
        raise PatchError(f"Skill target must already exist: {target}")
    states = {}
    for name, (before, after) in payloads.items():
        current = _read(target / name)
        states[name] = "before" if current == before else "after" if current == after else "drift"
    current_marker = _read(target / MARKER)
    if current_marker not in (None, marker):
        raise PatchError("Installed maintenance marker drift")
    if "drift" in states.values():
        raise PatchError("Installed file drift: " + ", ".join(k for k, v in states.items() if v == "drift"))
    if all(v == "before" for v in states.values()) and current_marker is None:
        status = "baseline"
    elif all(v == "after" for v in states.values()) and current_marker == marker:
        status = "applied"
    else:
        status = "partial"
    return status, states


def atomic_write(path, data, mode=None):
    no_symlinks(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix=".imagegen-patch-", dir=path.parent)
    temporary = Path(temporary)
    try:
        with os.fdopen(fd, "wb") as stream:
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        if mode is not None:
            temporary.chmod(mode)
        no_symlinks(path)
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


def _backup_location(backup_root, target, patch_id):
    backup_root = backup_root.expanduser().absolute()
    no_symlinks(backup_root)
    # No discoverable skill tree or plugin tree may contain backup files.
    if {"skills", "plugins", ".agents"}.intersection(backup_root.parts):
        raise PatchError("Backups must be outside skill and plugin discovery roots")
    if backup_root == target or target in backup_root.parents:
        raise PatchError("Backups must be outside the installed skill")
    return backup_root / patch_id / digest(str(target).encode())[:16]


def _receipt(path, value):
    atomic_write(path, (json.dumps(value, indent=2, sort_keys=True) + "\n").encode())


def manage(action, target, backup_root, package=PACKAGE):
    target = Path(target).expanduser().absolute()
    manifest, payloads, marker = load_package(package)
    status, states = inspect_target(target, payloads, marker)
    backup = _backup_location(Path(backup_root), target, manifest["patch_id"])
    report = {"status": status, "target": str(target), "backup": str(backup), "files": states}
    if action == "check":
        return report
    if action == "apply" and status == "applied":
        return {**report, "changed": False}
    if action == "rollback" and status == "baseline":
        return {**report, "changed": False}
    if action == "apply" and status != "baseline":
        raise PatchError("Partial installation; use guarded rollback before applying")
    no_symlinks(backup)
    receipt_path = backup / "receipt.json"
    if action == "apply":
        if backup.exists():
            # A prior rolled-back run can be reused only when every saved byte
            # and its target binding still matches this exact package.
            _validate_backup(backup, target, manifest, payloads)
        else:
            backup.parent.mkdir(parents=True, exist_ok=True)
            staged_backup = Path(tempfile.mkdtemp(prefix=".preparing-", dir=backup.parent))
            try:
                for name, (before, _) in payloads.items():
                    if before is not None:
                        atomic_write(staged_backup / (name + ".before"), before)
                _receipt(staged_backup / "receipt.json", {"patch_id": manifest["patch_id"], "target": str(target),
                                       "status": "prepared", "states": states})
                if backup.exists():
                    raise PatchError("Backup appeared during preparation; retry after inspection")
                os.rename(staged_backup, backup)
            finally:
                if staged_backup.exists():
                    shutil.rmtree(staged_backup)
        try:
            _receipt(receipt_path, {"patch_id": manifest["patch_id"], "target": str(target),
                                   "status": "applying", "states": states})
            for name, (before, after) in payloads.items():
                path = target / name
                if _read(path) != before:
                    raise PatchError(f"File changed during apply: {name}")
                mode = path.stat().st_mode & 0o777 if path.exists() else 0o644
                atomic_write(path, after, mode)
            if _read(target / MARKER) is not None:
                raise PatchError("Marker changed during apply")
            atomic_write(target / MARKER, marker, 0o644)
            status, states = inspect_target(target, payloads, marker)
        except BaseException as exc:
            # Observe bytes again; a replacement may have succeeded before a
            # failure was raised. Never claim an automatic rollback occurred.
            observed = _observed_states(target, payloads)
            try:
                _receipt(receipt_path, {"patch_id": manifest["patch_id"], "target": str(target),
                        "status": "apply_failed", "states": observed, "error": str(exc)})
            except OSError:
                pass
            raise PatchError(f"Apply interrupted; inspect target and use guarded rollback. Backup: {backup}; {exc}") from exc
    elif action == "rollback":
        _validate_backup(backup, target, manifest, payloads)
        try:
            for name, (before, after) in payloads.items():
                path = target / name
                current = _read(path)
                if current not in (before, after):
                    raise PatchError(f"File changed during rollback: {name}")
                if before is None:
                    if current is not None:
                        path.unlink()
                elif current != before:
                    atomic_write(path, before, path.stat().st_mode & 0o777)
            if _read(target / MARKER) not in (None, marker):
                raise PatchError("Marker changed during rollback")
            (target / MARKER).unlink(missing_ok=True)
            status, states = inspect_target(target, payloads, marker)
        except BaseException as exc:
            observed = _observed_states(target, payloads)
            try:
                _receipt(receipt_path, {"patch_id": manifest["patch_id"], "target": str(target),
                    "status": "rollback_failed", "states": observed, "error": str(exc)})
            except OSError:
                pass
            raise PatchError(f"Rollback interrupted; backup retained at {backup}: {exc}") from exc
    else:
        raise PatchError(f"Unknown action: {action}")
    _receipt(receipt_path, {"patch_id": manifest["patch_id"], "target": str(target),
                           "status": status, "states": states})
    return {**report, "status": status, "files": states, "changed": True}


def _observed_states(target, payloads):
    states = {}
    for name, (before, after) in payloads.items():
        try:
            current = _read(target / name)
            states[name] = "before" if current == before else "after" if current == after else "drift"
        except (OSError, PatchError):
            states[name] = "unreadable"
    return states


def _validate_backup(backup, target, manifest, payloads):
    raw = _read(backup / "receipt.json")
    if raw is None:
        raise PatchError("Rollback backup receipt missing")
    receipt = json.loads(raw)
    if receipt.get("patch_id") != manifest["patch_id"] or receipt.get("target") != str(target):
        raise PatchError("Backup receipt does not match package and installed target")
    for name, (before, _) in payloads.items():
        if _read(backup / (name + ".before")) != before:
            raise PatchError(f"Backup checksum mismatch: {name}")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=["check", "apply", "rollback"])
    parser.add_argument("--target", type=Path, default=Path.home() / ".codex/skills/.system/imagegen")
    parser.add_argument("--backup-root", type=Path, default=Path.home() / ".codex/skill-maintenance-backups/imagegen")
    args = parser.parse_args()
    try:
        print(json.dumps(manage(args.action, args.target, args.backup_root), indent=2, sort_keys=True))
    except (PatchError, OSError, ValueError, KeyError) as exc:
        parser.exit(1, f"Error: {exc}\n")


if __name__ == "__main__":
    main()
