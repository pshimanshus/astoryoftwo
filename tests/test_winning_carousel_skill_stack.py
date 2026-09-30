from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

NEW_SKILLS = [
    "a-story-audience-analyst",
    "a-story-carousel-researcher",
    "a-story-hook-generator",
    "a-story-swipe-architect",
    "a-story-brand-guidance",
    "a-story-visual-storyteller",
    "a-story-caption-cta-engine",
    "a-story-content-repurposer",
]


def _read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_winning_carousel_skills_are_codex_native_and_discoverable():
    for skill_name in NEW_SKILLS:
        skill = _read(f".agents/skills/{skill_name}/SKILL.md")
        metadata = _read(f".agents/skills/{skill_name}/agents/openai.yaml")

        assert skill.startswith("---\n")
        assert f"name: {skill_name}\n" in skill
        assert "description: Use when" in skill
        assert "Claude" not in skill
        assert "Claude" not in metadata
        assert "policy:" in metadata
        assert "allow_implicit_invocation: true" in metadata
        assert f'default_prompt: "Use ${skill_name}' in metadata


def test_shared_winning_carousel_context_captures_reference_learnings():
    runtime = _read("config/skills/winning-carousel-research-runtime-context.md")
    profile = _read("memory/semantic/a-story-audience-profile.md")

    for fragment in (
        "slide 2 confirms the hook",
        "Every slide should work as a screenshot",
        "one slide worth saving",
        "caption is the second post",
        "feed brand DNA before asking for a carousel",
        "current official sources",
    ):
        assert fragment in runtime

    for fragment in (
        "this is us",
        "send/save",
        "partner",
        "Hinglish",
        "beautiful",
        "prompt please",
    ):
        assert fragment in profile


def test_carousel_jam_references_research_stack_without_preloading_all_skills():
    skill = _read(".agents/skills/a-story-carousel-jam/SKILL.md")

    assert "winning_carousel_research" in skill
    assert "Use the winning-carousel research stack" in skill
    load_first = skill.split("## Load First", 1)[1].split("## Operating Contract", 1)[0]
    for skill_name in NEW_SKILLS:
        assert skill_name not in load_first
