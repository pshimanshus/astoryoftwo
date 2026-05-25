from pathlib import Path


WORKSPACE = Path(__file__).resolve().parents[1]


def test_creator_jam_contract_overrides_generic_visual_companion():
    agents = (WORKSPACE / "AGENTS.md").read_text(encoding="utf-8")
    golden_skill = (WORKSPACE / "config/skills/golden-viral-carousel-theme.md").read_text(
        encoding="utf-8"
    )

    for text in (agents, golden_skill):
        assert "Creator Jam Response Contract" in text
        assert "Do not offer the generic visual companion" in text
    assert "golden-theme variant tournament" in agents
    assert "Think like an author before thinking like a packager" in agents
    assert "concept-process card" in agents


def test_visual_debate_gate_is_persistent_for_carousel_work():
    agents = (WORKSPACE / "AGENTS.md").read_text(encoding="utf-8")
    framework = (WORKSPACE / "config/skills/illustration-carousel-framework.md").read_text(
        encoding="utf-8"
    )
    contract = (WORKSPACE / "config/carousel_style_contract.json").read_text(encoding="utf-8")

    for text in (agents, framework):
        assert "Visual Debate Gate" in text
        assert "three visual agents" in text
        assert "visual-debate.json" in text
        assert "before image generation" in text

    for agent_file in (
        "agents/carousel-visual-evidence-planner.md",
        "agents/carousel-romance-scene-planner.md",
        "agents/carousel-visual-continuity-judge.md",
    ):
        path = WORKSPACE / agent_file
        assert path.exists(), f"{agent_file} must exist for the visual debate gate"

    assert '"visual_debate_policy"' in contract
    assert '"required": true' in contract
