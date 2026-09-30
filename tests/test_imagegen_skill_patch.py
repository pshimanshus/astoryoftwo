"""The maintenance package is tested against scratch skills, never installed state."""
import importlib.util
import json
from pathlib import Path
import shutil

import pytest


PACKAGE = Path(__file__).resolve().parents[1] / "tools/imagegen-skill-patch"


@pytest.fixture
def manager():
    spec = importlib.util.spec_from_file_location("imagegen_patch_manager", PACKAGE / "manage.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture
def installation(manager, tmp_path):
    target = tmp_path / "installed" / "imagegen"
    target.mkdir(parents=True)
    _, payloads, _ = manager.load_package()
    for name, (before, _) in payloads.items():
        if before is not None:
            path = target / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(before)
    (target / "scripts/image_gen.py").chmod(0o755)
    (target / "unrelated.txt").write_text("untouched")
    return target, tmp_path / "backups"


def test_package_is_non_discoverable_and_fixture_is_pinned(manager):
    manifest, payloads, _ = manager.load_package()
    assert not list(PACKAGE.rglob("SKILL.md"))
    fixture = (PACKAGE / "fixtures/image_gen.py.before").read_bytes()
    assert manager.digest(fixture) == manifest["files"]["scripts/image_gen.py"]["before_sha256"]
    assert fixture == payloads["scripts/image_gen.py"][0]


def test_check_has_no_writes_and_apply_rollback_are_idempotent(manager, installation):
    target, backups = installation
    before = {p.relative_to(target): p.read_bytes() for p in target.rglob("*") if p.is_file()}
    assert manager.manage("check", target, backups)["status"] == "baseline"
    assert not backups.exists()
    applied = manager.manage("apply", target, backups)
    assert applied["status"] == "applied"
    assert manager.manage("apply", target, backups)["changed"] is False
    assert (target / "scripts/image_gen.py").stat().st_mode & 0o777 == 0o755
    assert manager.manage("rollback", target, backups)["status"] == "baseline"
    assert manager.manage("rollback", target, backups)["changed"] is False
    assert {p.relative_to(target): p.read_bytes() for p in target.rglob("*") if p.is_file()} == before
    assert manager.manage("apply", target, backups)["status"] == "applied"


@pytest.mark.parametrize("action", ["check", "apply", "rollback"])
def test_drift_is_never_overwritten(manager, installation, action):
    target, backups = installation
    if action == "rollback":
        manager.manage("apply", target, backups)
    path = target / "scripts/image_gen.py"
    path.write_bytes(path.read_bytes() + b"# user change\n")
    before = path.read_bytes()
    with pytest.raises(manager.PatchError, match="drift"):
        manager.manage(action, target, backups)
    assert path.read_bytes() == before


@pytest.mark.parametrize("which", ["target", "file", "directory", "marker", "backup"])
def test_symlinks_are_refused(manager, installation, tmp_path, which):
    target, backups = installation
    if which == "target":
        alias = tmp_path / "alias"
        alias.symlink_to(target, target_is_directory=True)
        target = alias
    elif which in ("file", "marker"):
        name = "scripts/image_gen.py" if which == "file" else manager.MARKER
        path = target / name
        other = tmp_path / "other"
        other.write_bytes(path.read_bytes() if path.exists() else b"marker")
        path.unlink(missing_ok=True)
        path.symlink_to(other)
    elif which == "directory":
        other = tmp_path / "script-dir"
        (target / "scripts").rename(other)
        (target / "scripts").symlink_to(other, target_is_directory=True)
    else:
        other = tmp_path / "backup-real"
        other.mkdir()
        backups.symlink_to(other, target_is_directory=True)
    with pytest.raises(manager.PatchError, match="symlink"):
        manager.manage("apply", target, backups)


def test_marker_drift_and_missing_marker_refuse_reapply(manager, installation):
    target, backups = installation
    manager.manage("apply", target, backups)
    marker = target / manager.MARKER
    marker.write_text("unrelated maintenance")
    with pytest.raises(manager.PatchError, match="marker drift"):
        manager.manage("rollback", target, backups)
    marker.unlink()
    assert manager.manage("check", target, backups)["status"] == "partial"
    with pytest.raises(manager.PatchError, match="Partial"):
        manager.manage("apply", target, backups)
    assert manager.manage("rollback", target, backups)["status"] == "baseline"


def test_failed_replacement_reports_actual_states_and_guarded_rollback(manager, installation, monkeypatch):
    target, backups = installation
    original = manager.atomic_write

    def fail_after_replacement(path, data, mode=None):
        original(path, data, mode)
        if path == target / "scripts/image_gen.py":
            raise OSError("injected after replace")

    monkeypatch.setattr(manager, "atomic_write", fail_after_replacement)
    with pytest.raises(manager.PatchError, match="interrupted"):
        manager.manage("apply", target, backups)
    receipt = json.loads(next(backups.rglob("receipt.json")).read_text())
    assert receipt["status"] == "apply_failed"
    assert receipt["states"]["scripts/image_gen.py"] == "after"
    assert receipt["states"]["references/cli.md"] == "before"
    monkeypatch.setattr(manager, "atomic_write", original)
    assert manager.manage("check", target, backups)["status"] == "partial"
    assert manager.manage("rollback", target, backups)["status"] == "baseline"
    assert (target / "unrelated.txt").read_text() == "untouched"


def test_failed_backup_preparation_leaves_retriable_baseline(manager, installation, monkeypatch):
    target, backups = installation
    original = manager.atomic_write

    def fail_backup(path, data, mode=None):
        if path.name.endswith(".before"):
            raise OSError("disk failure")
        original(path, data, mode)

    monkeypatch.setattr(manager, "atomic_write", fail_backup)
    with pytest.raises(OSError, match="disk failure"):
        manager.manage("apply", target, backups)
    assert manager.manage("check", target, backups)["status"] == "baseline"
    monkeypatch.setattr(manager, "atomic_write", original)
    assert manager.manage("apply", target, backups)["status"] == "applied"


def test_corrupt_backup_refuses_rollback(manager, installation):
    target, backups = installation
    manager.manage("apply", target, backups)
    next(backups.rglob("image_gen.py.before")).write_bytes(b"corrupt")
    with pytest.raises(manager.PatchError, match="Backup checksum"):
        manager.manage("rollback", target, backups)
    assert manager.manage("check", target, backups)["status"] == "applied"


def test_backup_must_be_outside_discovery(manager, installation, tmp_path):
    target, _ = installation
    with pytest.raises(manager.PatchError, match="discovery"):
        manager.manage("apply", target, tmp_path / "skills" / "backups")


def test_patch_and_manifest_tamper_fail_closed(manager, tmp_path):
    package = tmp_path / "package"
    shutil.copytree(PACKAGE, package)
    patch = package / "imagegen.patch"
    patch.write_bytes(patch.read_bytes() + b"tamper")
    with pytest.raises(manager.PatchError, match="checksum"):
        manager.load_package(package)
    shutil.copyfile(PACKAGE / "imagegen.patch", patch)
    manifest_path = package / "manifest.json"
    manifest = json.loads(manifest_path.read_text())
    manifest["files"]["../../escape"] = manifest["files"].pop("SKILL.md")
    manifest_path.write_text(json.dumps(manifest))
    with pytest.raises(manager.PatchError, match="allowlist"):
        manager.load_package(package)
