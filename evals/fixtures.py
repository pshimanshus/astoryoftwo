from __future__ import annotations

import shutil
from pathlib import Path, PurePosixPath

from evals.schemas import EvalTask, FixtureOverlay


class UnsafeFixturePathError(ValueError):
    """Raised when a fixture overlay attempts to escape its sandbox."""


def _is_relative_to(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root)
    except ValueError:
        return False
    return True


def _normalized_overlay_path(raw_path: str, *, label: str) -> Path:
    normalized = raw_path.replace("\\", "/")
    pure = PurePosixPath(normalized)
    if normalized in {"", "."}:
        raise UnsafeFixturePathError(f"{label} fixture path is empty")
    if pure.is_absolute():
        raise UnsafeFixturePathError(f"{label} fixture path must be relative: {raw_path}")
    if any(part == ".." for part in pure.parts):
        raise UnsafeFixturePathError(f"{label} fixture path may not contain '..': {raw_path}")
    return Path(*pure.parts)


def _safe_join(root: Path, raw_path: str, *, label: str) -> Path:
    resolved_root = root.resolve()
    candidate = (resolved_root / _normalized_overlay_path(raw_path, label=label)).resolve(strict=False)
    if not _is_relative_to(candidate, resolved_root):
        raise UnsafeFixturePathError(f"{label} fixture path escapes root: {raw_path}")
    return candidate


def _assert_write_target_is_safe(target: Path, destination_root: Path, raw_path: str) -> None:
    resolved_root = destination_root.resolve()
    resolved_parent = target.parent.resolve(strict=False)
    if not _is_relative_to(resolved_parent, resolved_root):
        raise UnsafeFixturePathError(f"target fixture parent escapes root: {raw_path}")
    if target.exists() or target.is_symlink():
        resolved_target = target.resolve(strict=False)
        if not _is_relative_to(resolved_target, resolved_root):
            raise UnsafeFixturePathError(f"target fixture path escapes root: {raw_path}")


def _copy_fixture_file(task: EvalTask, overlay: FixtureOverlay, destination_root: Path) -> Path:
    source = _safe_join(task.task_dir, overlay.source, label="source")
    target = _safe_join(destination_root, overlay.target, label="target")
    target.parent.mkdir(parents=True, exist_ok=True)
    _assert_write_target_is_safe(target, destination_root, overlay.target)
    if overlay.mode == "binary":
        shutil.copyfile(source, target)
    else:
        target.write_text(source.read_text(encoding="utf-8"), encoding="utf-8")
    return target


def materialize_task_fixture(task: EvalTask, destination_root: Path) -> list[Path]:
    """Write a task's fixture overlay into a destination directory.

    This is intentionally an overlay materializer, not a full repository clone.
    In a full eval run, callers should apply the overlay to an isolated repo
    checkout. Unit tests can materialize only the fixture files needed by the
    checker.
    """

    destination_root = destination_root.resolve()
    destination_root.mkdir(parents=True, exist_ok=True)
    written = [_copy_fixture_file(task, overlay, destination_root) for overlay in task.fixture_overlay]

    prompt_target = destination_root / ".eval" / f"{task.id}-prompt.md"
    prompt_target.parent.mkdir(parents=True, exist_ok=True)
    prompt_target.write_text((task.task_dir / task.prompt).read_text(encoding="utf-8"), encoding="utf-8")
    written.append(prompt_target)
    return written
