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
