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


def test_make_carousel_runs_existing_preflight_before_generation():
    text = (WORKSPACE / "Makefile").read_text(encoding="utf-8")
    carousel_target = text.split("\narticle:", 1)[0].split("\ncarousel:", 1)[1]
    create_index = carousel_target.index("scripts/create_illustration_carousel.py")
    for required in (
        "tests/test_agentic_docs_contract.py",
        "tests/test_instruction_surface_contract.py",
        "tests/test_codex_project_surfaces.py",
        "tests/test_creator_workflow_contract.py",
        "tests/test_checks_prompt_constraints.py",
        "tests/test_checks_image_size.py",
        "tests/test_carousel_state_contract.py",
        "tests/test_carousel_workflow_doctor.py",
        "tests/test_carousel_doctor_cli.py",
        "scripts/agentic_os.py health",
    ):
        assert required in carousel_target
        assert carousel_target.index(required) < create_index


def test_command_center_scripts_have_help():
    for script in ("daily_creator_brief.py", "jam_today.py", "run_content_health.py"):
        result = subprocess.run(
            [sys.executable, str(WORKSPACE / "scripts" / script), "--help"],
            cwd=WORKSPACE,
            capture_output=True,
            text=True,
            check=False,
            timeout=30,
        )
        assert result.returncode == 0
        assert "usage:" in result.stdout.lower()


def test_jam_today_prints_free_creative_pass_before_gates():
    result = subprocess.run(
        [sys.executable, str(WORKSPACE / "scripts" / "jam_today.py"), "--moment", "haan haan listening trap"],
        cwd=WORKSPACE,
        capture_output=True,
        text=True,
        check=False,
        timeout=30,
    )

    assert result.returncode == 0
    assert "free creative pass first" in result.stdout.lower()
    assert "engineering guardrails" in result.stdout.lower()
    assert "before writing public copy" not in result.stdout.lower()
