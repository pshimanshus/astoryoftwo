from pathlib import Path

from pipeline.agentic.memory_index import build_memory_index, search_memory
from pipeline.agentic.retrieval import search
from pipeline.agentic.retrieval_manifest import build_manifest


def _root(tmp_path: Path) -> Path:
    (tmp_path / "memory" / "semantic").mkdir(parents=True)
    (tmp_path / "memory" / "semantic" / "story.md").write_text(
        "# कहानी\n\nconfidence: 0.8\nsources:\n- test\n\nथकी हुई partner ने chores quietly संभाले.\n",
        encoding="utf-8",
    )
    (tmp_path / "config" / "rules").mkdir(parents=True)
    (tmp_path / "config" / "rules" / "voice.md").write_text("# Rule\n\nAlways preserve creator corrections.\n", encoding="utf-8")
    (tmp_path / "docs").mkdir()
    (tmp_path / "docs" / "smoke-test.md").write_text("smoke only", encoding="utf-8")
    return tmp_path


def test_manifest_indexes_canonical_rules_but_excludes_smoke(tmp_path: Path):
    records = build_manifest(_root(tmp_path))
    paths = {record.source_path for record in records}
    assert "config/rules/voice.md" in paths
    assert "docs/smoke-test.md" not in paths
    assert all(record.content_sha256 and record.source_pointer.startswith("lines:") for record in records)


def test_fts5_is_unicode_aware_and_cites_chunk(tmp_path: Path):
    index = build_memory_index(_root(tmp_path))
    hits = search_memory(index, "कहानी", limit=3)
    assert hits
    assert hits[0].source_path == "memory/semantic/story.md"
    assert hits[0].source_pointer.startswith("lines:")
    assert hits[0].backend == "fts5"


def test_unavailable_opt_in_backend_falls_back_to_fts5(tmp_path: Path, monkeypatch):
    root = _root(tmp_path)
    monkeypatch.setenv("ASOT_RETRIEVAL_QMD_ENABLED", "1")
    monkeypatch.setenv("ASOT_RETRIEVAL_BACKEND", "qmd")
    hits = search(root, "creator corrections", limit=2)
    assert hits and hits[0].backend == "fts5"


def test_rebuild_is_skipped_for_unchanged_manifest(tmp_path: Path):
    root = _root(tmp_path)
    first = build_memory_index(root)
    before = first.stat().st_mtime_ns
    second = build_memory_index(root)
    assert first == second
    assert second.stat().st_mtime_ns == before
