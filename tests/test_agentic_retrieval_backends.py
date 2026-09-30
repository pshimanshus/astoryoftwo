from pathlib import Path

from pipeline.agentic.memory_index import build_memory_index, search_memory
import json

from pipeline.agentic.retrieval import search, search_with_status
from pipeline.agentic.retrieval_manifest import build_manifest, load_manifest
from pipeline.agentic.retrieval_qmd import QmdHybridBackend
from pipeline.agentic.retrieval_sentence_transformers import SentenceTransformersHybridBackend


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
    assert hits[0].requested_backend == "qmd"
    assert "unavailable" in hits[0].fallback_reason


def test_rebuild_is_skipped_for_unchanged_manifest(tmp_path: Path):
    root = _root(tmp_path)
    first = build_memory_index(root)
    before = first.stat().st_mtime_ns
    second = build_memory_index(root)
    assert first == second
    assert second.stat().st_mtime_ns == before


def test_incremental_fts_removes_deleted_manifest_records(tmp_path: Path):
    root = _root(tmp_path)
    index = build_memory_index(root)
    assert search_memory(index, "कहानी")
    (root / "memory" / "semantic" / "story.md").unlink()
    build_memory_index(root)
    assert search_memory(index, "कहानी") == []


def test_qmd_collection_is_manifest_bound_and_rejects_foreign_ids(tmp_path: Path, monkeypatch):
    root = _root(tmp_path)
    monkeypatch.setenv("ASOT_RETRIEVAL_QMD_ENABLED", "1")
    _path, records, _digest = load_manifest(root)
    wanted = next(record for record in records if record.source_path.endswith("story.md"))

    def runner(command, _cwd, env):
        assert env["QMD_NO_UPDATE"] == "1"
        if "query" in command:
            return json.dumps([{"record_id": "foreign", "score": 99},
                               {"record_id": wanted.record_id, "score": .8}])
        return ""

    backend = QmdHybridBackend(runner=runner, executable="fake-qmd")
    directory = backend.build(root)
    hits = backend.search(root, "कहानी", 5)
    assert directory.name == "qmd"
    assert [hit.record_id for hit in hits] == [wanted.record_id]
    assert hits[0].source_pointer.startswith("lines:")


def test_qmd_applies_shared_package_scope_and_role_controls(tmp_path: Path, monkeypatch):
    root = _root(tmp_path)
    alpha = root / "output" / "carousels" / "2026-09-30" / "alpha"
    beta = root / "output" / "carousels" / "2026-09-30" / "beta"
    events = root / "memory" / "agentic" / "learning-events"
    alpha.mkdir(parents=True)
    beta.mkdir(parents=True)
    events.mkdir(parents=True)
    (alpha / "creator-correction.json").write_text(json.dumps({
        "package_id": "output/carousels/2026-09-30/alpha",
        "events": [{"feedback_id": "alpha", "scope": "package", "status": "captured",
                    "user_instruction_exact": "current cerulean latch"}],
    }), encoding="utf-8")
    (beta / "creator-correction.json").write_text(json.dumps({
        "package_id": "output/carousels/2026-09-30/beta",
        "events": [{"feedback_id": "beta", "scope": "package", "status": "captured",
                    "user_instruction_exact": "current crimson latch"}],
    }), encoding="utf-8")
    (events / "private.json").write_text(json.dumps({
        "event_id": "private", "source": "creator_feedback", "summary": "private current latch",
        "eval_disposition": "passed", "scope": "package",
    }), encoding="utf-8")
    monkeypatch.setenv("ASOT_RETRIEVAL_QMD_ENABLED", "1")
    _path, records, _digest = load_manifest(root)
    by_path = {record.legacy_path: record for record in records}
    alpha_record = by_path["output/carousels/2026-09-30/alpha/creator-correction.json#alpha"]
    beta_record = by_path["output/carousels/2026-09-30/beta/creator-correction.json#beta"]
    private_record = next(record for record in records if record.source_path.endswith("private.json"))
    story_record = next(record for record in records if record.source_path.endswith("story.md"))
    query_commands = []

    def runner(command, _cwd, _env):
        if "query" in command:
            query_commands.append(command)
            return json.dumps([{"record_id": story_record.record_id},
                               {"record_id": private_record.record_id},
                               {"record_id": beta_record.record_id},
                               {"record_id": alpha_record.record_id}])
        return ""

    backend = QmdHybridBackend(runner=runner, executable="fake-qmd")
    backend.build(root)
    package_hits = backend.search(
        root,
        "package:output/carousels/2026-09-30/alpha scope:package role:maker current latch",
        5,
    )
    assert [hit.record_id for hit in package_hits] == [alpha_record.record_id]
    assert query_commands[-1][2] == "current latch"
    assert query_commands[-1][-1] == "64"

    role_hits = backend.search(root, "scope:package role:maker current latch", 5)
    assert private_record.record_id not in {hit.record_id for hit in role_hits}
    assert role_hits[0].record_id == beta_record.record_id


def test_local_dense_persists_vectors_and_rrf_uses_exact_manifest_citations(tmp_path: Path, monkeypatch):
    np = __import__("numpy")
    root = _root(tmp_path)
    monkeypatch.setenv("ASOT_RETRIEVAL_LOCAL_DENSE_ENABLED", "1")

    class Encoder:
        calls = 0
        def encode(self, texts, **_kwargs):
            self.calls += 1
            return np.asarray([[1.0, 0.0] if "कहानी" in text else [0.0, 1.0] for text in texts])

    encoder = Encoder()
    backend = SentenceTransformersHybridBackend(encoder=encoder)
    directory = backend.build(root)
    first_calls = encoder.calls
    backend.build(root)
    assert encoder.calls == first_calls
    hits = backend.search(root, "कहानी", 2)
    assert (directory / "vectors.npz").is_file()
    assert hits[0].backend == "sentence_transformers_hybrid"
    assert hits[0].source_path == "memory/semantic/story.md"
    assert hits[0].content_sha256


def test_candidate_status_never_labels_fts_fallback_as_evaluated_qmd(tmp_path: Path, monkeypatch):
    root = _root(tmp_path)
    monkeypatch.delenv("ASOT_RETRIEVAL_QMD_ENABLED", raising=False)
    result = search_with_status(root, "creator corrections", backend="qmd")
    assert result.actual_backend == "fts5"
    assert result.evaluated is False
    assert result.fallback_reason
