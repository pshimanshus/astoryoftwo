from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from pipeline.agentic.knowledge_workflow import run_knowledge_workflow, select_roles


ROOT = Path(__file__).resolve().parents[1]


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _role_records(root: Path) -> None:
    target = root / ".codex" / "agents"
    target.mkdir(parents=True)
    for name in (
        "asot_evidence_reviewer.toml",
        "asot_contradiction_reviewer.toml",
        "asot_wiki_compiler_verifier.toml",
    ):
        (target / name).write_bytes((ROOT / ".codex" / "agents" / name).read_bytes())


def _successful_event(root: Path, *, conflicts: bool = False) -> Path:
    _role_records(root)
    source = root / "corpus" / "normalized" / "source.json"
    source.parent.mkdir(parents=True)
    source.write_text('{"fact": "one"}\n', encoding="utf-8")
    analysis = root / "output" / "reports" / "analysis.md"
    analysis.parent.mkdir(parents=True)
    analysis.write_text("# Analysis\n", encoding="utf-8")
    output = root / "wiki" / "concepts" / "fact.md"
    output.parent.mkdir(parents=True)
    output.write_text("# Fact\n", encoding="utf-8")
    receipt = root / "output" / "receipts" / "compile.json"
    receipt.parent.mkdir(parents=True)
    receipt.write_text(
        json.dumps(
            {
                "status": "applied",
                "analysis_path": analysis.relative_to(root).as_posix(),
                "analysis_sha256": _sha(analysis),
                "targets": [output.relative_to(root).as_posix()],
                "output_hashes": {output.relative_to(root).as_posix(): _sha(output)},
            }
        ),
        encoding="utf-8",
    )
    event = {
        "event_id": "evt-1",
        "evidence": [
            {"path": source.relative_to(root).as_posix(), "sha256": _sha(source)}
        ],
        "analysis_path": analysis.relative_to(root).as_posix(),
        "compile_receipt_path": receipt.relative_to(root).as_posix(),
    }
    if conflicts:
        second_source = root / "corpus" / "normalized" / "source-two.json"
        second_source.write_text('{"fact": "two"}\n', encoding="utf-8")
        event["evidence"].append(
            {"path": second_source.relative_to(root).as_posix(), "sha256": _sha(second_source)}
        )
        event["conflicts"] = [
            {
                "claim": "The observed wording differs across captures.",
                "source_paths": [
                    source.relative_to(root).as_posix(),
                    second_source.relative_to(root).as_posix(),
                ],
                "resolution": "unresolved",
            }
        ]
    event_path = root / "event.json"
    event_path.write_text(json.dumps(event), encoding="utf-8")
    return event_path


def test_router_selects_only_needed_roles() -> None:
    assert select_roles({"compile": False}) == ["evidence_reviewer"]
    assert select_roles({"compile": False, "conflicts": [{"claim": "x"}]}) == [
        "evidence_reviewer",
        "contradiction_reviewer",
    ]


def test_contradictory_claim_values_are_preserved_without_prefilled_conflicts(tmp_path: Path) -> None:
    event_path = _successful_event(tmp_path)
    event = json.loads(event_path.read_text())
    first_source = event["evidence"][0]["path"]
    second_source_path = tmp_path / "corpus" / "normalized" / "source-two.json"
    second_source_path.write_text('{"fact": "two"}\n', encoding="utf-8")
    second_source = second_source_path.relative_to(tmp_path).as_posix()
    event["evidence"].append({"path": second_source, "sha256": _sha(second_source_path)})
    event["claims"] = [
        {"claim": "Questions correlate with the higher observed tail.", "direction": "higher", "source_path": first_source},
        {"claim": "Questions correlate with the higher observed tail.", "direction": "lower", "source_path": second_source},
    ]
    event_path.write_text(json.dumps(event), encoding="utf-8")

    receipt = run_knowledge_workflow(tmp_path, event_path)

    delta = json.loads((tmp_path / receipt["knowledge_delta_path"]).read_text())
    assert delta["preserved_conflicts"] == [{
        "claim": "Questions correlate with the higher observed tail.",
        "source_paths": sorted([first_source, second_source]),
        "observed_values": ["higher", "lower"],
        "resolution": "unresolved",
    }]


def test_unverified_contradiction_sources_block_compilation(tmp_path: Path) -> None:
    event_path = _successful_event(tmp_path)
    event = json.loads(event_path.read_text())
    event["claims"] = [
        {"claim": "A claim", "direction": "higher", "source_path": "missing-a.json"},
        {"claim": "A claim", "direction": "lower", "source_path": "missing-b.json"},
    ]
    event_path.write_text(json.dumps(event), encoding="utf-8")

    receipt = run_knowledge_workflow(tmp_path, event_path)

    assert receipt["status"] == "REPAIR"
    contradiction = json.loads(
        next(
            (tmp_path / path).read_text()
            for path in receipt["review_paths"]
            if path.endswith("contradiction_reviewer.json")
        )
    )
    assert contradiction["status"] == "DATA_GAP"
    assert all("cites unverified evidence" in issue for issue in contradiction["issues"])


def test_verified_compile_persists_reviews_delta_and_invalidation(tmp_path: Path) -> None:
    event_path = _successful_event(tmp_path, conflicts=True)
    source = tmp_path / "corpus" / "normalized" / "source.json"
    before = source.read_bytes()

    receipt = run_knowledge_workflow(tmp_path, event_path)

    assert receipt["status"] == "PASS"
    assert receipt["selected_roles"] == [
        "evidence_reviewer",
        "contradiction_reviewer",
        "wiki_compiler",
        "wiki_compiler_verifier",
    ]
    assert source.read_bytes() == before
    assert (tmp_path / receipt["route_path"]).is_file()
    assert (tmp_path / receipt["knowledge_delta_path"]).is_file()
    invalidation = tmp_path / receipt["retrieval_invalidation_path"]
    assert invalidation.is_file()
    delta = json.loads((tmp_path / receipt["knowledge_delta_path"]).read_text())
    assert delta["preserved_conflicts"][0]["resolution"] == "unresolved"


def test_failed_compile_never_invalidates_retrieval(tmp_path: Path) -> None:
    event_path = _successful_event(tmp_path)
    event = json.loads(event_path.read_text())
    receipt_path = tmp_path / event["compile_receipt_path"]
    compile_receipt = json.loads(receipt_path.read_text())
    compile_receipt["output_hashes"][compile_receipt["targets"][0]] = "0" * 64
    receipt_path.write_text(json.dumps(compile_receipt), encoding="utf-8")

    receipt = run_knowledge_workflow(tmp_path, event_path)

    assert receipt["status"] == "REPAIR"
    assert receipt["retrieval_invalidation_path"] is None
    assert not (tmp_path / "memory" / "agentic" / "retrieval-invalidations").exists()


def test_missing_evidence_blocks_compiler_stage(tmp_path: Path) -> None:
    _role_records(tmp_path)
    event_path = tmp_path / "event.json"
    event_path.write_text(
        json.dumps({"event_id": "no-evidence", "evidence": [], "compile": True}),
        encoding="utf-8",
    )

    receipt = run_knowledge_workflow(tmp_path, event_path)

    assert receipt["status"] == "REPAIR"
    assert receipt["retrieval_invalidation_path"] is None
    assert all("wiki_compiler_verifier" not in path for path in receipt["review_paths"])


def test_router_refuses_reviewer_record_with_write_capability(tmp_path: Path) -> None:
    event_path = _successful_event(tmp_path)
    record = tmp_path / ".codex" / "agents" / "asot_evidence_reviewer.toml"
    record.write_text(
        record.read_text(encoding="utf-8").replace(
            'sandbox_mode = "read-only"', 'sandbox_mode = "workspace-write"'
        ),
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="reviewer role must be read-only"):
        run_knowledge_workflow(tmp_path, event_path)
