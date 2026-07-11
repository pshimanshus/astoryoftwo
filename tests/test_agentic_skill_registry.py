import json
from pathlib import Path

from pipeline.agentic.skill_registry import (
    discover_skill_records,
    load_skill_systems,
    resolve_skill_system,
)
from pipeline.agentic.skill_usage import record_skill_run, summarize_skill_usage


def test_discover_skill_records_reads_markdown_skills(tmp_path: Path):
    root = tmp_path
    (root / "config" / "skills").mkdir(parents=True)
    (root / "agents").mkdir()
    repo_skill_dir = root / ".agents" / "skills" / "gamma-skill"
    repo_skill_dir.mkdir(parents=True)
    (repo_skill_dir / "SKILL.md").write_text(
        "---\n"
        "name: gamma-skill\n"
        "description: Gamma repo skill for workflow routing.\n"
        "---\n"
        "\n"
        "# Gamma Skill\n\n"
        "Load `config/skills/alpha-skill.md` before running.\n",
        encoding="utf-8",
    )
    (repo_skill_dir / "agents").mkdir()
    (repo_skill_dir / "agents" / "openai.yaml").write_text(
        "interface:\n"
        '  display_name: "Gamma Skill"\n'
        '  short_description: "Gamma workflow routing helper"\n'
        "policy:\n"
        "  allow_implicit_invocation: false\n",
        encoding="utf-8",
    )
    (root / "config" / "skills" / "alpha-skill.md").write_text(
        "# Alpha Skill\n\nconfidence: 0.8\n\n## Purpose\n\nDoes alpha work.\n",
        encoding="utf-8",
    )
    (root / "agents" / "beta-agent.md").write_text(
        "# beta-agent\n# skill_refs:\n#   - config/skills/alpha-skill.md\n",
        encoding="utf-8",
    )

    records = discover_skill_records(root)

    ids = {record.skill_id for record in records}
    assert "skill.alpha-skill" in ids
    assert "agent.beta-agent" in ids
    assert "repo_skill.gamma-skill" in ids

    repo_skill = next(record for record in records if record.skill_id == "repo_skill.gamma-skill")
    assert repo_skill.kind == "repo_skill"
    assert repo_skill.description == "Gamma repo skill for workflow routing."
    assert repo_skill.implicit_invocation is False
    assert repo_skill.dependencies == ["alpha-skill"]


def test_resolve_skill_system_expands_ordered_components(tmp_path: Path):
    root = tmp_path
    (root / "config").mkdir()
    (root / "config" / "skill-systems.json").write_text(
        json.dumps(
            {
                "schema_version": "1.0",
                "systems": {
                    "carousel_jam": {
                        "description": "Carousel jam workflow.",
                        "components": [
                            "config/skills/romance-story-selling-engine.md",
                            "config/skills/golden-viral-carousel-theme.md",
                        ],
                        "source_references": [
                            "wiki/insights/successful-carousel-standard.md",
                        ],
                    }
                },
            }
        ),
        encoding="utf-8",
    )

    systems = load_skill_systems(root)
    resolved = resolve_skill_system(systems, "carousel_jam")

    assert resolved["name"] == "carousel_jam"
    assert resolved["components"][0] == "config/skills/romance-story-selling-engine.md"
    assert resolved["source_references"] == [
        "wiki/insights/successful-carousel-standard.md"
    ]


def test_story_article_uses_canonical_voice_rule():
    systems = load_skill_systems(Path(__file__).resolve().parents[1])
    resolved = resolve_skill_system(systems, "story_article")

    assert "config/rules/voice.md" in resolved["components"]
    assert "config/voice.md" not in resolved["components"]


def test_repo_skill_usage_tracks_frequency_and_failures(tmp_path: Path):
    root = tmp_path
    repo_skill_dir = root / ".agents" / "skills" / "gamma-skill"
    repo_skill_dir.mkdir(parents=True)
    (repo_skill_dir / "SKILL.md").write_text(
        "---\n"
        "name: gamma-skill\n"
        "description: Gamma repo skill for workflow routing.\n"
        "---\n"
        "\n"
        "# Gamma Skill\n",
        encoding="utf-8",
    )

    record_skill_run(root, skill_name="gamma-skill", outcome="fail", note="missing proof")
    record_skill_run(root, skill_name="gamma-skill", outcome="pass", note="proof added")

    summary = summarize_skill_usage(root)
    gamma = next(item for item in summary if item["skill"] == "gamma-skill")

    assert gamma["invocations"] == 2
    assert gamma["failures"] == 1
    assert gamma["passes"] == 1
    assert gamma["last_outcome"] == "pass"
