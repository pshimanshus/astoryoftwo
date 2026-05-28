import json
from pathlib import Path

from pipeline.agentic.skill_registry import (
    discover_skill_records,
    load_skill_systems,
    resolve_skill_system,
)


def test_discover_skill_records_reads_markdown_skills(tmp_path: Path):
    root = tmp_path
    (root / "config" / "skills").mkdir(parents=True)
    (root / "agents").mkdir()
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
