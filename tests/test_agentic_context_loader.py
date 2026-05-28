import json
from pathlib import Path

import pytest

from pipeline.agentic.context_loader import assemble_context_pack, estimate_tokens, render_context_pack


def test_estimate_tokens_is_deterministic():
    assert estimate_tokens("one two three four") == 1
    assert estimate_tokens("x" * 400) == 100


def test_assemble_context_pack_loads_profile_with_provenance(tmp_path: Path):
    root = tmp_path
    (root / "config").mkdir()
    (root / "memory").mkdir()
    (root / "config" / "voice.md").write_text("Warm voice " * 20, encoding="utf-8")
    (root / "memory" / "working.md").write_text("Working memory " * 20, encoding="utf-8")
    manifest = {
        "schema_version": "1.0",
        "default_profile": "a-story-of-two",
        "profiles": {
            "a-story-of-two": {
                "budget_tokens": 80,
                "sections": [
                    {"id": "voice", "path": "config/voice.md", "kind": "brand_voice", "required": True},
                    {"id": "working", "path": "memory/working.md", "kind": "working_memory", "required": True},
                ],
            }
        },
    }
    (root / "config" / "agentic_context_manifest.json").write_text(
        json.dumps(manifest),
        encoding="utf-8",
    )

    pack = assemble_context_pack(root, profile="a-story-of-two")

    assert pack.profile == "a-story-of-two"
    assert [section.id for section in pack.sections] == ["voice", "working"]
    assert pack.estimated_tokens <= pack.budget_tokens
    assert pack.sections[0].path == "config/voice.md"


def test_assemble_context_pack_rejects_missing_required_file(tmp_path: Path):
    root = tmp_path
    (root / "config").mkdir()
    manifest = {
        "schema_version": "1.0",
        "default_profile": "a-story-of-two",
        "profiles": {
            "a-story-of-two": {
                "budget_tokens": 80,
                "sections": [
                    {"id": "voice", "path": "config/voice.md", "kind": "brand_voice", "required": True}
                ],
            }
        },
    }
    (root / "config" / "agentic_context_manifest.json").write_text(
        json.dumps(manifest),
        encoding="utf-8",
    )

    with pytest.raises(FileNotFoundError) as exc:
        assemble_context_pack(root, profile="a-story-of-two")
    assert "config/voice.md" in str(exc.value)


def test_render_context_pack_includes_budget_and_provenance(tmp_path: Path):
    root = tmp_path
    (root / "config").mkdir()
    (root / "memory").mkdir()
    (root / "config" / "voice.md").write_text("Warm voice.", encoding="utf-8")
    (root / "memory" / "working.md").write_text("Current memory.", encoding="utf-8")
    (root / "config" / "agentic_context_manifest.json").write_text(
        json.dumps(
            {
                "schema_version": "1.0",
                "default_profile": "a-story-of-two",
                "profiles": {
                    "a-story-of-two": {
                        "budget_tokens": 80,
                        "sections": [
                            {
                                "id": "voice",
                                "path": "config/voice.md",
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
                    }
                },
            }
        ),
        encoding="utf-8",
    )

    rendered = render_context_pack(assemble_context_pack(root, profile="a-story-of-two"))

    assert "# Agentic Context Pack" in rendered
    assert "Profile: a-story-of-two" in rendered
    assert "Budget:" in rendered
    assert "Source: `config/voice.md`" in rendered
    assert "Warm voice." in rendered
