from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


ACTIVE_TEXT_RULE_SURFACES = [
    "config/rules/on-image-text.md",
    "config/carousel_style_contract.json",
    "config/references/a-story-illustration-master-prompt.md",
    "config/references/a-story-premium-illustration-style-lock.md",
    "config/skills/illustration-carousel-framework.md",
    "agents/carousel-post-copy-visual-room-orchestrator.md",
    "memory/semantic/carousel-idea-preferences.md",
    "memory/semantic/premium-illustration-style-lock.md",
]


def test_instruction_surface_contract_declares_required_and_banned_phrases() -> None:
    path = ROOT / "config" / "instruction_surface_contract.json"
    data = json.loads(path.read_text(encoding="utf-8"))

    assert data["schema_version"] == "1.0"
    assert data["max_agents_md_lines"] <= 420
    assert "AGENTS.md" in data["surfaces"]
    assert data["agents_md_edit_policy"].startswith("Do not edit AGENTS.md")
    assert "CLAUDE.md" not in data["surfaces"]
    assert "CLAUDE.md" in data["retired_paths"]
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
    assert "CLAUDE.md" not in data["banned_phrases"]


def test_retired_instruction_paths_are_absent() -> None:
    path = ROOT / "config" / "instruction_surface_contract.json"
    data = json.loads(path.read_text(encoding="utf-8"))

    for retired_path in data["retired_paths"]:
        assert not (ROOT / retired_path).exists(), f"{retired_path} is retired"


def test_dependent_brandmark_surfaces_follow_agents_md_source_text() -> None:
    agents = (ROOT / "AGENTS.md").read_text(encoding="utf-8")
    if "tiny `@a.storyof.two` top-right signature" in agents:
        placement = "top-right"
        opposite = "bottom-right"
    elif "tiny `@a.storyof.two` bottom-right signature" in agents:
        placement = "bottom-right"
        opposite = "top-right"
    else:
        raise AssertionError("AGENTS.md must declare the brandmark placement source text")

    dependent_paths = [
        "config/rules/brandmark.md",
        "config/rules/on-image-text.md",
        "config/carousel_style_contract.json",
        "config/skills/carousel-jam-autopilot.md",
        "config/skills/illustration-carousel-framework.md",
        "config/references/a-story-illustration-master-prompt.md",
        "config/references/a-story-premium-illustration-style-lock.md",
        "agents/carousel-post-copy-visual-room-orchestrator.md",
        "memory/semantic/carousel-idea-preferences.md",
        "memory/semantic/premium-illustration-style-lock.md",
        "pipeline/agentic/checks/prompt_constraints.py",
        "pipeline/stages/carousel_quality.py",
        "pipeline/stages/carousel_visual_rooms.py",
        "pipeline/stages/codex_native_carousel.py",
        "tests/test_checks_prompt_constraints.py",
        "tests/test_illustration_carousel.py",
    ]
    for relative in dependent_paths:
        text = (ROOT / relative).read_text(encoding="utf-8")
        assert placement in text, f"{relative} must follow AGENTS.md brandmark placement"
        opposite_brandmark_lines = [
            line.strip()
            for line in text.splitlines()
            if opposite in line
            and ("brandmark" in line or "@a.storyof.two" in line or "signature" in line)
            and not any(token in line.lower() for token in ("not", "never", "do not", "don't", "no "))
        ]
        assert not opposite_brandmark_lines, (
            f"{relative} must not override AGENTS.md brandmark placement: "
            f"{opposite_brandmark_lines}"
        )


def test_active_text_rule_surfaces_do_not_allow_source_art_text_later_workflow() -> None:
    banned_fragments = [
        "source art first",
        "source-scene generation",
        "source scene",
        "source art may be generated",
        "clean reserved paper space",
        "reserved blank",
        "leave blank",
        "blank upper",
        "add text later",
        "text later",
        "text-placement pass",
        "text placement afterward",
        "text placement later",
        "text to be added",
        "place the approved text into the same final raster",
    ]

    offenders: list[str] = []
    for relative in ACTIVE_TEXT_RULE_SURFACES:
        text = (ROOT / relative).read_text(encoding="utf-8").lower()
        for fragment in banned_fragments:
            if fragment in text:
                offenders.append(f"{relative}: {fragment}")

    assert not offenders, (
        "Active @a.storyof.two instruction surfaces must block/retry when exact "
        f"text cannot be rendered, not permit source-art/text-later workflows: {offenders}"
    )
