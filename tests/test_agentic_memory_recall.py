from pathlib import Path

from pipeline.agentic.memory_index import build_memory_index, search_memory
from pipeline.agentic.recall import build_recall_bundle, render_recall_bundle


def test_memory_index_finds_semantic_memory_by_meaningful_terms(tmp_path: Path):
    root = tmp_path
    (root / "memory" / "semantic").mkdir(parents=True)
    (root / "memory" / "semantic" / "prefs.md").write_text(
        "# Preferences\n\nconfidence: 0.9\nsources:\n- test\n\nfact: Use visual-first kitchen comedy and tiny thought bubbles.\n",
        encoding="utf-8",
    )

    index_path = build_memory_index(root)
    hits = search_memory(index_path, "kitchen thought bubble", limit=3)

    assert hits
    assert hits[0].path == "memory/semantic/prefs.md"
    assert "kitchen" in hits[0].snippet.lower()


def test_recall_bundle_combines_context_and_ranked_hits(tmp_path: Path):
    root = tmp_path
    (root / "config").mkdir()
    (root / "memory" / "semantic").mkdir(parents=True)
    (root / "memory").mkdir(exist_ok=True)
    (root / "config" / "voice.md").write_text("Warm couple voice.", encoding="utf-8")
    (root / "memory" / "working.md").write_text("Current kitchen carousel draft.", encoding="utf-8")
    (root / "memory" / "semantic" / "prefs.md").write_text(
        "# Preferences\n\nconfidence: 0.9\nsources:\n- test\n\nfact: Build visual-first carousels.\n",
        encoding="utf-8",
    )
    (root / "config" / "agentic_context_manifest.json").write_text(
        """{
          "schema_version": "1.0",
          "default_profile": "a-story-of-two",
          "profiles": {
            "a-story-of-two": {
              "budget_tokens": 400,
              "sections": [
                {"id": "voice", "path": "config/voice.md", "kind": "brand_voice", "required": true},
                {"id": "working", "path": "memory/working.md", "kind": "working_memory", "required": true}
              ]
            }
          }
        }""",
        encoding="utf-8",
    )

    bundle = build_recall_bundle(root, query="visual carousel", profile="a-story-of-two")

    assert bundle.query == "visual carousel"
    assert bundle.context.profile == "a-story-of-two"
    assert bundle.hits


def test_render_recall_bundle_includes_context_and_ranked_citations(tmp_path: Path):
    root = tmp_path
    (root / "config").mkdir()
    (root / "memory" / "semantic").mkdir(parents=True)
    (root / "memory").mkdir(exist_ok=True)
    (root / "config" / "voice.md").write_text("Warm couple voice.", encoding="utf-8")
    (root / "memory" / "working.md").write_text("Current kitchen carousel draft.", encoding="utf-8")
    (root / "memory" / "semantic" / "prefs.md").write_text(
        "# Preferences\n\nconfidence: 0.9\nsources:\n- test\n\nfact: Build visual-first carousels.\n",
        encoding="utf-8",
    )
    (root / "config" / "agentic_context_manifest.json").write_text(
        """{
          "schema_version": "1.0",
          "default_profile": "a-story-of-two",
          "profiles": {
            "a-story-of-two": {
              "budget_tokens": 400,
              "sections": [
                {"id": "voice", "path": "config/voice.md", "kind": "brand_voice", "required": true},
                {"id": "working", "path": "memory/working.md", "kind": "working_memory", "required": true}
              ]
            }
          }
        }""",
        encoding="utf-8",
    )

    rendered = render_recall_bundle(
        build_recall_bundle(root, query="visual carousel", profile="a-story-of-two")
    )

    assert "# Recall Bundle" in rendered
    assert "# Agentic Context Pack" in rendered
    assert "memory/semantic/prefs.md" in rendered
    assert "Build visual-first carousels" in rendered
