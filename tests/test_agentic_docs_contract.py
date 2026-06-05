from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_agentic_os_control_plane_is_documented_for_future_sessions():
    agents = (ROOT / "AGENTS.md").read_text(encoding="utf-8")
    claude = (ROOT / "CLAUDE.md").read_text(encoding="utf-8")

    for text in (agents, claude):
        assert "Agentic OS Control Plane" in text
        assert "scripts/agentic_os.py" in text
        assert "config/agentic_context_manifest.json" in text
        assert "config/skill-systems.json" in text
        assert "pipeline/agentic/" in text

    spec = (ROOT / "docs" / "superpowers" / "specs" / "agentic-os-control-plane.md").read_text(
        encoding="utf-8"
    )
    assert "Learning is proposal-only" in spec
    assert "source-memory-brief.md" in spec


def test_agents_md_is_codex_instruction_index_not_stale_workflow_dump():
    agents = (ROOT / "AGENTS.md").read_text(encoding="utf-8")

    assert len(agents.splitlines()) <= 420
    assert "docs/superpowers/plans/creative-os-master-plan.md" in agents
    assert "docs/superpowers/plans/THE-PLAN.md" in agents
    assert "config/skill-systems.json" in agents
    assert "scripts/agentic_os.py carousel-doctor" in agents
    assert "memory/working.md is pointer-only" in agents
    assert "Learning proposals are draft-only" in agents
    assert "memory/semantic/" in agents

    assert "Entry: scripts/create_illustration_carousel.py" not in agents
    assert "and can be called directly from Claude Code sessions" not in agents
    assert "Each package contains:" not in agents
