import json
from datetime import date
from pathlib import Path

from pipeline.stages.wiki_health import (
    collect_wiki_health,
    repair_wiki_index_metadata,
    write_health_artifacts,
)


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def minimal_workspace(root: Path) -> None:
    write_text(
        root / "AGENTS.md",
        "# AGENTS\n\nPipeline promises `pipeline.runner` and A1-A5 stage files.\n",
    )
    write_text(
        root / "wiki" / "index.md",
        "\n".join(
            [
                "# Wiki Index",
                "last_updated: 2026-05-09",
                "total_pages: 0",
                "confidence_floor: 0.4",
                "",
                "## Themes",
                "",
            ]
        ),
    )
    write_text(
        root / "wiki" / "themes" / "calm-enough-for-chaos.md",
        "\n".join(
            [
                "# Calm Enough For Chaos",
                "last_updated: 2026-05-17",
                "confidence: 0.86",
                "sources:",
                "- output/reports/gold.md",
                "",
                "## Summary",
                "A real wiki page.",
            ]
        ),
    )
    write_text(
        root / "memory" / "working.md",
        "# Working Memory\n\ncurrent notes\n",
    )
    write_text(root / "memory" / "graph.json", json.dumps({"entities": {}}))
    (root / "memory" / "semantic").mkdir(parents=True)
    (root / "memory" / "episodic").mkdir(parents=True)
    (root / "logs").mkdir()
    (root / "pipeline" / "stages").mkdir(parents=True)


def checks_by_id(health: dict) -> dict[str, dict]:
    return {check["id"]: check for check in health["checks"]}


def test_health_flags_missing_advertised_stage_files_and_stale_index(tmp_path):
    minimal_workspace(tmp_path)

    health = collect_wiki_health(tmp_path, today=date(2026, 5, 19))
    checks = checks_by_id(health)

    assert health["status"] == "NEEDS_HEAL"
    assert checks["advertised_pipeline_files"]["status"] == "FAIL"
    assert "pipeline/runner.py" in checks["advertised_pipeline_files"]["evidence"]["missing"]
    assert "pipeline/stages/a4_wiki.py" in checks["advertised_pipeline_files"]["evidence"]["missing"]
    assert checks["wiki_index_total_pages"]["status"] == "FAIL"
    assert checks["wiki_index_total_pages"]["evidence"]["declared"] == 0
    assert checks["wiki_index_total_pages"]["evidence"]["actual"] == 1
    assert checks["episodic_records"]["status"] == "WARN"


def test_write_health_artifacts_creates_diagnostics_heal_episode_and_log(tmp_path):
    minimal_workspace(tmp_path)
    health = collect_wiki_health(tmp_path, today=date(2026, 5, 19))

    artifacts = write_health_artifacts(
        tmp_path,
        health,
        today=date(2026, 5, 19),
        session_note="Creator flagged repeated setup failures and stale memory.",
    )

    diagnostics = artifacts["diagnostics"]
    proposal = artifacts["heal_proposal"]
    episode = artifacts["episode"]
    log = artifacts["log"]

    assert diagnostics == tmp_path / "output" / "diagnostics" / "wiki-health-2026-05-19.md"
    assert proposal == tmp_path / "memory" / "heal" / "proposals" / "2026-05-19-wiki-health.md"
    assert episode == tmp_path / "memory" / "episodic" / "2026-05-19-session-health.md"
    assert log == tmp_path / "logs" / "2026-05-19-wiki-health.log"

    diagnostics_text = diagnostics.read_text(encoding="utf-8")
    assert "Wiki Health Diagnostics" in diagnostics_text
    assert "Warnings: 0" in diagnostics_text
    assert "HEAL Proposal" in proposal.read_text(encoding="utf-8")
    assert "advertised_pipeline_files" in proposal.read_text(encoding="utf-8")
    assert "Creator flagged repeated setup failures" in episode.read_text(encoding="utf-8")
    assert "NEEDS_HEAL" in log.read_text(encoding="utf-8")


def test_write_health_artifacts_never_overwrites_episodic_records_or_logs(tmp_path):
    minimal_workspace(tmp_path)
    health = collect_wiki_health(tmp_path, today=date(2026, 5, 19))

    first = write_health_artifacts(
        tmp_path,
        health,
        today=date(2026, 5, 19),
        session_note="First health run.",
    )
    second = write_health_artifacts(
        tmp_path,
        health,
        today=date(2026, 5, 19),
        session_note="Second health run.",
    )

    assert first["episode"].exists()
    assert second["episode"].exists()
    assert first["episode"] != second["episode"]
    assert first["log"] != second["log"]
    assert "First health run" in first["episode"].read_text(encoding="utf-8")
    assert "Second health run" in second["episode"].read_text(encoding="utf-8")


def test_repair_wiki_index_metadata_updates_page_count_and_date(tmp_path):
    minimal_workspace(tmp_path)

    repair_wiki_index_metadata(tmp_path, today=date(2026, 5, 19))

    index = (tmp_path / "wiki" / "index.md").read_text(encoding="utf-8")
    assert "last_updated: 2026-05-19" in index
    assert "total_pages: 1" in index
