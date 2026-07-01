from pathlib import Path


WORKSPACE = Path(__file__).resolve().parents[1]


def _read(path: str) -> str:
    return (WORKSPACE / path).read_text(encoding="utf-8")


def _flat(path: str) -> str:
    return " ".join(_read(path).split())


def test_agents_md_is_human_first_router_not_creative_os_dump():
    agents = _read("AGENTS.md")

    assert "This is the project contract for agents working in this repo." in agents
    assert "What Matters Most" in agents
    assert "Small Brief First" in agents
    assert "Human Draft First" in agents
    assert "Context As Seasoning" in agents
    assert "Do not answer a small creative brief with a framework report" in agents
    assert "Use agents surgically" in agents

    assert "## Hard Creative Rules" not in agents
    assert "golden-theme variant tournament" not in agents
    assert "Visual Debate Gate" not in agents
    assert "Stage-Scene Gate" not in agents
    assert "28/30" not in agents


def test_agents_md_protects_shareable_instagram_love_ideas():
    agents = _flat("AGENTS.md")

    for fragment in (
        "Fresh ideas must feel shareable on Instagram",
        "couple moment",
        "love learning",
        "this is me",
        "this is her",
        "this is us",
        "send it to their partner",
    ):
        assert fragment in agents


def test_carousel_hot_path_allows_creator_seed_or_agent_jam():
    agents = _read("AGENTS.md")
    skill = _read(".agents/skills/a-story-carousel-jam/SKILL.md")

    assert "There are two valid starts" in agents
    assert "The creator may bring a seed" in agents
    assert "jam and propose fresh concept ideas" in agents
    assert "concept already formed" in agents
    assert "creator asks to jam from scratch" in skill
    assert "fresh concept seeds" in skill


def test_agents_md_requires_format_choice_and_transformability():
    agents = _flat("AGENTS.md")
    skill = _flat(".agents/skills/a-story-carousel-jam/SKILL.md")

    assert "post, Reel, carousel, or multi-format package" in agents
    assert "Idea -> Format -> Proof -> Package" in agents
    assert "Format First" in agents
    assert "post, Reel, carousel" in skill


def test_agents_md_protects_identity_wardrobe_dimensions_and_brandmark():
    agents = _flat("AGENTS.md")
    skill = _flat(".agents/skills/a-story-carousel-jam/SKILL.md")

    for fragment in (
        "Aachu and Zuv must both stay recognizable",
        "whole illustrated person, not just a face patch",
        "face, hair, body proportions, height, expression, posture, and clothing",
        "clothing and couple styling come from those images first",
        "1080x1350",
        "1080x1920",
        "square only when requested",
        "tiny `@a.storyof.two`",
    ):
        assert fragment in agents

    assert "whole illustrated person, not just a face patch" in skill
    assert "Wardrobe and couple styling" in skill
    assert "tiny `@a.storyof.two`" in skill


def test_agents_md_requires_one_command_currentness_and_learning_updates():
    agents = _flat("AGENTS.md")
    skill = _flat(".agents/skills/a-story-carousel-jam/SKILL.md")

    for fragment in (
        "Prefer one-command workflows",
        "name the missing automation link and plan it",
        "check current official docs",
        "Agentic OS health, skill registry, wiki health, and focused tests",
        "Important learnings must update the durable layer",
        "no generic AI process fluff",
    ):
        assert fragment in agents

    assert "Prefer one-command automation" in skill
    assert "missing automation link" in skill


def test_agents_md_preserves_project_specific_sources_and_commands():
    agents = _read("AGENTS.md")

    for fragment in (
        "config/rules/",
        "config/agentic_context_manifest.json",
        "config/skill-systems.json",
        "config/skills/carousel-jam-runtime-context.md",
        "docs/superpowers/plans/2026-06-28-analysis-hot-path-repair.md",
        "docs/ai-ops-playbook.md",
        "scripts/agentic_os.py carousel-doctor",
        "memory/working.md` is pointer-only",
        "Learning proposals are draft-only",
        "make carousel STORY=",
        "scripts/autopublish.py",
    ):
        assert fragment in agents


def test_agents_md_uses_native_output_dimensions_not_square_default():
    agents = _read("AGENTS.md")

    assert "native 1080x1350 post" in agents
    assert "1080x1920 story/reel" in agents
    assert "square only for explicit experiments" in agents
    assert "1080x1080 proof/concept/single-slide generation gate" not in agents


def test_carousel_jam_skill_matches_hot_path_contract():
    skill = _read(".agents/skills/a-story-carousel-jam/SKILL.md")

    for fragment in (
        "Small Brief First",
        "Free Creative Pass First",
        "Human Draft First",
        "Context As Seasoning",
        "engineering is the guardrail layer",
        "No Visible Framework Language",
        "concept lock, copy lock, imagegen proof lock, and final package lock",
        "Use subagents only for bounded reviews",
    ):
        assert fragment in skill

    assert "Run Layer E before concept selection" not in skill
    assert "golden-theme variant tournament" not in skill
    assert "Run a nested debate room" not in skill
    assert "Stage-Scene Gate" not in skill
    assert "Visual Debate" not in skill


def test_hot_path_makes_model_first_creative_authority_durable():
    agents = _flat("AGENTS.md")
    runtime = _flat("config/skills/carousel-jam-runtime-context.md")
    prefs = _flat("memory/semantic/engineering-workflow-preferences.md")

    for text in (agents, runtime, prefs):
        assert "model owns concept, copy, and visual invention" in text
        assert "engineering is the guardrail layer" in text

    assert "free creative pass before private scoring" in agents
    assert "free creative pass before scoring" in runtime


def test_instruction_contract_protects_actual_project_failures():
    agents = _flat("AGENTS.md")

    for fragment in (
        "too much framework before the first human draft",
        "root docs and tool-specific docs drifting apart",
        "image outputs passing taste but failing exact text, identity, or dimensions",
        "Never revert changes you did not make",
        "Do not stage a mixed worktree silently",
        "Do not recreate `CLAUDE.md` or let skills/memory become a second competing root contract",
        "Do not edit `AGENTS.md` to resolve downstream mismatches",
        "update dependent rules, prompts, skills, and tests to match it",
    ):
        assert fragment in agents
