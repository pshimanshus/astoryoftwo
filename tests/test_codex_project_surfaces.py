import json
import tomllib
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


EXPECTED_SKILLS = {
    "a-story-carousel-jam": [
        "config/skill-systems.json",
        "carousel_jam",
        "config/skills/carousel-jam-autopilot.md",
    ],
    "a-story-article": [
        "config/skill-systems.json",
        "story_article",
        "config/skills/couple-substack-article-framework.md",
    ],
    "a-story-prepost": [
        "config/skill-systems.json",
        "prepost_reel",
        "scripts/analyze_prepost.py",
    ],
    "a-story-wiki-health": [
        "config/skill-systems.json",
        "wiki_health",
        "scripts/agentic_os.py health",
    ],
    "a-story-closeout": [
        "scripts/autopublish.py",
        "make publish",
        "--include",
    ],
}


def test_agents_md_is_a_lean_codex_router_with_core_links():
    agents_path = ROOT / "AGENTS.md"
    agents = agents_path.read_text(encoding="utf-8")

    assert agents_path.stat().st_size < 32 * 1024
    assert "config/rules/" in agents
    assert "config/skill-systems.json" in agents
    assert "docs/ai-ops-playbook.md" in agents
    assert "docs/agentic-os-operating-manual.md" in agents
    assert "## Review guidelines" in agents
    assert "Codex Worktrees" in agents
    assert "Browser" in agents
    assert "/review" in agents
    assert "@codex review" in agents
    assert "Automations" in agents


def test_original_operating_contract_is_preserved_outside_agents_router():
    manual = (ROOT / "docs" / "agentic-os-operating-manual.md").read_text(encoding="utf-8")

    assert "Illustrated Carousel Pipeline" in manual
    assert "Creator Jam Response Contract" in manual
    assert "Visual Debate Gate" in manual
    assert "Autopublish Closeout Gate" in manual


def test_repo_codex_skills_wrap_existing_agentic_os_workflows():
    for skill_name, required_fragments in EXPECTED_SKILLS.items():
        skill_file = ROOT / ".agents" / "skills" / skill_name / "SKILL.md"
        text = skill_file.read_text(encoding="utf-8")

        assert text.startswith("---\n")
        assert f"name: {skill_name}" in text
        assert "description:" in text
        for fragment in required_fragments:
            assert fragment in text


def test_project_codex_config_hooks_and_rules_are_present_and_safe():
    config = tomllib.loads((ROOT / ".codex" / "config.toml").read_text(encoding="utf-8"))
    hooks = json.loads((ROOT / ".codex" / "hooks.json").read_text(encoding="utf-8"))
    rules = (ROOT / ".codex" / "rules" / "default.rules").read_text(encoding="utf-8")
    hook_script = (ROOT / ".codex" / "hooks" / "stop_closeout_check.py").read_text(
        encoding="utf-8"
    )

    assert config["project_doc_max_bytes"] == 65536
    assert config["features"]["goals"] is True
    assert config["features"]["hooks"] is True

    stop_hooks = hooks["hooks"]["Stop"][0]["hooks"]
    assert stop_hooks[0]["type"] == "command"
    assert "stop_closeout_check.py" in stop_hooks[0]["command"]
    assert "git push" not in hooks["hooks"]["Stop"][0]["hooks"][0]["command"]
    assert "autopublish.py" not in hooks["hooks"]["Stop"][0]["hooks"][0]["command"]

    assert "git push" not in hook_script
    assert "subprocess.run" in hook_script
    assert "scripts/autopublish.py" in hook_script

    assert 'pattern = ["venv/bin/python", "-m", "pytest"]' in rules
    assert 'pattern = ["venv/bin/python", "scripts/wiki_health.py"]' in rules
    assert 'pattern = ["venv/bin/python", "scripts/autopublish.py"]' in rules
    assert 'pattern = ["make", "publish"]' in rules
    assert 'decision = "prompt"' in rules


def test_project_local_worktree_directory_is_ignored_for_git_fallback():
    gitignore = (ROOT / ".gitignore").read_text(encoding="utf-8")

    assert ".worktrees/" in gitignore
