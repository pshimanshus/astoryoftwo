import json
from pathlib import Path


def write_minimal_agentic_workspace(root: Path) -> None:
    (root / "config" / "rules").mkdir(parents=True, exist_ok=True)
    (root / "memory" / "semantic").mkdir(parents=True, exist_ok=True)
    (root / "memory").mkdir(exist_ok=True)
    (root / "config" / "rules" / "voice.md").write_text(
        "Warm A Story of Two voice.",
        encoding="utf-8",
    )
    (root / "memory" / "working.md").write_text(
        "Current visual-first carousel work.",
        encoding="utf-8",
    )
    (root / "memory" / "semantic" / "prefs.md").write_text(
        "# Preferences\n\nconfidence: 0.9\n\nfact: Use visual-first proof for couple stories.\n",
        encoding="utf-8",
    )
    (root / "config" / "agentic_context_manifest.json").write_text(
        json.dumps(
            {
                "schema_version": "1.0",
                "default_profile": "a-story-of-two",
                "profiles": {
                    "a-story-of-two": {
                        "budget_tokens": 500,
                        "sections": [
                            {
                                "id": "voice",
                                "path": "config/rules/voice.md",
                                "kind": "brand_voice",
                                "required": True,
                            },
                            {
                                "id": "working",
                                "path": "memory/working.md",
                                "kind": "working_memory",
                                "required": True,
                            },
                        ],
                    },
                    "article": {
                        "budget_tokens": 500,
                        "sections": [
                            {
                                "id": "voice",
                                "path": "config/rules/voice.md",
                                "kind": "brand_voice",
                                "required": True,
                            },
                            {
                                "id": "working",
                                "path": "memory/working.md",
                                "kind": "working_memory",
                                "required": True,
                            },
                        ],
                    },
                },
            }
        ),
        encoding="utf-8",
    )
    (root / "config" / "skill-systems.json").write_text(
        json.dumps(
            {
                "schema_version": "1.0",
                "systems": {
                    "carousel_jam": {
                        "components": ["config/skills/carousel-jam-autopilot.md"],
                        "agents": [],
                        "gates": ["visual_debate_go"],
                    },
                    "story_article": {
                        "components": ["config/skills/couple-substack-article-framework.md"],
                        "agents": [],
                        "gates": ["final_approval"],
                    },
                    "prepost_reel": {
                        "components": ["config/skills/hook-and-edit-framework.md"],
                        "agents": [],
                        "gates": ["verdict"],
                    },
                },
            }
        ),
        encoding="utf-8",
    )
