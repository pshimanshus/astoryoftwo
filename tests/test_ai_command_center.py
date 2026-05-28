import subprocess
import sys
from pathlib import Path


WORKSPACE = Path(__file__).resolve().parents[1]


def test_ai_command_center_files_exist():
    for relative in (
        "Makefile",
        "docs/ai-ops-playbook.md",
        "docs/superpowers/specs/2026-05-28-ai-command-center-design.md",
        "scripts/daily_creator_brief.py",
        "scripts/jam_today.py",
        "scripts/run_content_health.py",
    ):
        assert (WORKSPACE / relative).exists(), f"{relative} should exist"


def test_makefile_exposes_primary_targets():
    text = (WORKSPACE / "Makefile").read_text(encoding="utf-8")
    for target in (
        "brief:",
        "health wiki-health:",
        "jam:",
        "prepost:",
        "carousel:",
        "article:",
        "publish:",
        "publish-dry-run:",
        "test:",
    ):
        assert target in text


def test_command_center_scripts_have_help():
    for script in ("daily_creator_brief.py", "jam_today.py", "run_content_health.py"):
        result = subprocess.run(
            [sys.executable, str(WORKSPACE / "scripts" / script), "--help"],
            cwd=WORKSPACE,
            capture_output=True,
            text=True,
            check=False,
        )
        assert result.returncode == 0
        assert "usage:" in result.stdout.lower()
