from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_instruction_surface_contract_declares_required_and_banned_phrases() -> None:
    path = ROOT / "config" / "instruction_surface_contract.json"
    data = json.loads(path.read_text(encoding="utf-8"))

    assert data["schema_version"] == "1.0"
    assert data["max_agents_md_lines"] <= 420
    assert "AGENTS.md" in data["surfaces"]
    assert "CLAUDE.md" in data["surfaces"]
    assert ".claude/commands/story.md" in data["retired_paths"]

    required = set(data["required_phrases"])
    assert "config/rules/" in required
    assert "config/skill-systems.json" in required
    assert "scripts/agentic_os.py carousel-doctor" in required
    assert "memory/semantic/" in required
    assert "memory/working.md is pointer-only" in required
    assert "Learning proposals are draft-only" in required
    assert "scripts/wiki_health.py --write --fix-index" in required
    assert "scripts/autopublish.py" in required

    banned = set(data["banned_phrases"]["AGENTS.md"])
    assert "Entry: scripts/create_illustration_carousel.py" in banned
    assert "and can be called directly from Claude Code sessions" in banned


def test_retired_instruction_paths_are_absent() -> None:
    path = ROOT / "config" / "instruction_surface_contract.json"
    data = json.loads(path.read_text(encoding="utf-8"))

    for retired_path in data["retired_paths"]:
        assert not (ROOT / retired_path).exists(), f"{retired_path} is retired"
