import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_agentic_os_control_plane_is_documented_for_future_sessions():
    agents = (ROOT / "AGENTS.md").read_text(encoding="utf-8")

    assert "Agentic OS Control Plane" in agents
    assert "scripts/agentic_os.py" in agents
    assert "config/agentic_context_manifest.json" in agents
    assert "config/skill-systems.json" in agents
    assert "pipeline/agentic/" in agents

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


def test_instruction_precedence_is_documented_on_agent_surfaces():
    agents = (ROOT / "AGENTS.md").read_text(encoding="utf-8")

    assert "Instruction Precedence" in agents
    assert "Explicit user prompts" in agents
    assert "config/rules/" in agents

    assert "closest `AGENTS.md`" in agents
    assert "override an explicit user request" in agents


def test_claude_md_is_retired_not_required_instruction_surface():
    assert not (ROOT / "CLAUDE.md").exists()


def test_active_illustration_docs_point_to_one_style_authority():
    contract = json.loads(
        (ROOT / "config" / "carousel_style_contract.json").read_text(encoding="utf-8")
    )
    profile = contract["style_profile"]
    active_surfaces = (
        ".agents/skills/a-story-carousel-jam/SKILL.md",
        ".agents/skills/a-story-direct-visual-story/SKILL.md",
        ".agents/skills/astory/references/master-prompt.md",
        "config/skills/carousel-jam-runtime-context.md",
        "config/skills/carousel-jam-autopilot.md",
        "config/skills/illustration-carousel-framework.md",
        "config/references/a-story-premium-illustration-style-lock.md",
        "wiki/insights/carousel-quality-spine.md",
        "wiki/insights/successful-carousel-standard.md",
        "docs/ai-ops-playbook.md",
    )
    combined = "\n".join((ROOT / path).read_text(encoding="utf-8") for path in active_surfaces)

    assert "config/carousel_style_contract.json" in combined
    assert "config/rules/palette.md" in combined
    assert "config/rules/visual-variety.md" in combined
    assert profile["generation_prompt"] not in combined
    assert "config/references/style-lock/observational-intimacy-premium/contact-sheet.png" not in combined
