import json
from datetime import date
from pathlib import Path

from pipeline.stages.wiki_health import (
    collect_wiki_health,
    feedback_health_evidence,
    generation_receipt_health_evidence,
    heal_proposal_markdown,
    repair_wiki_index_metadata,
    write_health_artifacts,
)
from pipeline.stages.carousel_generation_inputs import canonical_fingerprint, sha256_binding


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


def test_generation_health_accepts_hash_verified_superseded_draft_attempt(tmp_path):
    package = tmp_path / "output" / "carousels" / "2026-09-05" / "archived-attempt"
    source_relative = ".internal/visual-quarantine/slide-06/attempt-01/source/instagram_post.png"
    candidate_relative = ".internal/visual-quarantine/slide-06/attempt-01/candidate.json"
    receipt = {
        "generator_boundary": "codex_builtin_imagegen",
        "tool_reported_model": "codex-imagegen",
        "prompt_sha256": "sha256:prompt",
        "reference_manifest_sha256": "sha256:references",
        "references": [{"path": ".internal/references/person.png", "sha256": "sha256:ref"}],
        "slide": 6,
        "attempt": 1,
        "returned_sources": [{"path": source_relative, "sha256": "", "width": 1080, "height": 1440}],
        "feedback_id": None,
        "pixel_review_status": "passed",
        "promotion_status": "pending",
    }
    archive = package / ".internal" / "visual-quarantine" / "superseded" / "archive-one"
    source = archive / source_relative
    source.parent.mkdir(parents=True, exist_ok=True)
    source.write_bytes(b"historical-pixels")
    receipt["returned_sources"][0]["sha256"] = sha256_binding(source.read_bytes())
    candidate = archive / candidate_relative
    write_text(candidate, json.dumps({"slide": 6, "generation_receipt": receipt}))
    qa = {"schema_version": "carousel-pixel-qa/v3", "status": "PASS"}
    write_text(archive / "proof-qa.json", json.dumps(qa))
    receipt["qa_sha256"] = canonical_fingerprint(qa)
    write_text(candidate, json.dumps({"slide": 6, "generation_receipt": receipt}))
    entries = []
    for relative in (candidate_relative, source_relative, "proof-qa.json"):
        target = archive / relative
        entries.append({"original_path": relative, "sha256": sha256_binding(target.read_bytes())})
    write_text(archive / "archive.json", json.dumps({
        "schema_version": "carousel-superseded-evidence/v1",
        "archive_id": "archive-one",
        "files": entries,
    }))
    write_text(package / "prompt-pack.json", json.dumps({"schema_version": "carousel-prompt-pack/v3"}))
    write_text(package / "generation-state.json", json.dumps({
        "schema_version": "carousel-generation-state/v3",
        "status": "proof_qa_required",
        "selected_slides": [8],
        "slides": {
            "6": {"status": "draft", "attempts": 1, "attempt_history": [receipt]},
            "8": {"status": "draft", "attempts": 0, "attempt_history": []},
        },
    }))

    assert generation_receipt_health_evidence(tmp_path, date(2026, 9, 30)) == {}
    source.write_bytes(b"tampered")
    failures = generation_receipt_health_evidence(tmp_path, date(2026, 9, 30))
    assert "slide 6: receipt has no candidate" in next(iter(failures.values()))


def checks_by_id(health: dict) -> dict[str, dict]:
    return {check["id"]: check for check in health["checks"]}


def test_healthy_run_does_not_invent_a_missing_closeout_gate():
    proposal = heal_proposal_markdown(
        {
            "date": "2026-09-30",
            "checks": [
                {
                    "id": "instruction_surface_sync",
                    "status": "PASS",
                    "message": "Closeout commands present.",
                },
            ],
        }
    )

    assert "No repair is proposed" in proposal
    assert "no repo-wide session-close gate" not in proposal
    assert "`instruction_surface_sync`" not in proposal


def test_heal_proposal_limits_repairs_to_observed_failures_and_warnings():
    proposal = heal_proposal_markdown(
        {
            "date": "2026-09-30",
            "checks": [
                {
                    "id": "instruction_surface_sync",
                    "status": "PASS",
                    "message": "Closeout commands present.",
                },
                {
                    "id": "wiki_index_total_pages",
                    "status": "FAIL",
                    "message": "Page count is stale.",
                },
                {
                    "id": "episodic_records",
                    "status": "WARN",
                    "message": "No episodic records found.",
                },
            ],
        }
    )

    assert "wiki_index_total_pages: FAIL - Page count is stale." in proposal
    assert "episodic_records: WARN - No episodic records found." in proposal
    assert "Investigate `wiki_index_total_pages`" in proposal
    assert "Investigate `episodic_records`" in proposal
    assert "instruction_surface_sync" not in proposal
    assert "No repair is proposed" not in proposal
    assert "no repo-wide session-close gate" not in proposal
    assert "does not establish their root causes" in proposal


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


def test_clean_checkout_without_generated_logs_is_warning_only(tmp_path):
    minimal_workspace(tmp_path)
    (tmp_path / "logs").rmdir()

    health = collect_wiki_health(tmp_path, today=date(2026, 5, 19))
    checks = checks_by_id(health)

    assert "logs" not in checks["memory_surface"]["evidence"]["missing"]
    assert checks["session_logs"]["status"] == "WARN"


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


def test_health_flags_instruction_surface_drift_for_missing_autopublish(tmp_path):
    minimal_workspace(tmp_path)
    write_text(
        tmp_path / "AGENTS.md",
        "\n".join(
                [
                    "# AGENTS",
                    "",
                    "Run `venv/bin/python scripts/wiki_health.py --write --fix-index`.",
                ]
            ),
        )

    health = collect_wiki_health(tmp_path, today=date(2026, 5, 28))
    checks = checks_by_id(health)

    assert health["status"] == "NEEDS_HEAL"
    assert checks["instruction_surface_sync"]["status"] == "FAIL"
    assert "AGENTS.md" in checks["instruction_surface_sync"]["evidence"]["missing_phrases"]
    assert (
        "scripts/autopublish.py"
        in checks["instruction_surface_sync"]["evidence"]["missing_phrases"]["AGENTS.md"]
    )


def test_health_passes_when_agents_md_carries_closeout_commands(tmp_path):
    minimal_workspace(tmp_path)
    closeout = "\n".join(
        [
            "Run `venv/bin/python scripts/autopublish.py --session-note \"summary\"`.",
            "Run `venv/bin/python scripts/wiki_health.py --write --fix-index`.",
        ]
    )
    write_text(tmp_path / "AGENTS.md", "# AGENTS\n\n" + closeout)

    health = collect_wiki_health(tmp_path, today=date(2026, 5, 28))
    checks = checks_by_id(health)

    assert checks["instruction_surface_sync"]["status"] == "PASS"


def test_wiki_health_checks_agentic_os_surface(tmp_path):
    minimal_workspace(tmp_path)
    closeout = "\n".join(
        [
            "Run `venv/bin/python scripts/autopublish.py --session-note \"summary\"`.",
            "Run `venv/bin/python scripts/wiki_health.py --write --fix-index`.",
        ]
    )
    write_text(tmp_path / "AGENTS.md", "# AGENTS\n\n" + closeout)

    health = collect_wiki_health(tmp_path, today=date(2026, 5, 28))
    checks = checks_by_id(health)

    assert checks["agentic_os_surface"]["status"] == "FAIL"
    assert "pipeline/agentic/contracts.py" in checks["agentic_os_surface"]["evidence"]["missing"]
    assert "scripts/agentic_os.py" in checks["agentic_os_surface"]["evidence"]["missing"]


def test_health_flags_stale_agents_instruction_surface(tmp_path):
    minimal_workspace(tmp_path)
    write_text(
        tmp_path / "config" / "instruction_surface_contract.json",
        json.dumps(
            {
                "schema_version": "1.0",
                "max_agents_md_lines": 20,
                "surfaces": ["AGENTS.md"],
                "retired_paths": ["CLAUDE.md"],
                "required_phrases": [
                    "config/rules/",
                    "scripts/agentic_os.py carousel-doctor",
                    "scripts/autopublish.py",
                ],
                "banned_phrases": {
                    "AGENTS.md": ["Entry: scripts/create_illustration_carousel.py"],
                },
            }
        ),
    )
    write_text(
        tmp_path / "AGENTS.md",
        "\n".join(
            [
                "# AGENTS",
                "config/rules/",
                "scripts/agentic_os.py carousel-doctor",
                "scripts/autopublish.py",
                "Entry: scripts/create_illustration_carousel.py",
            ]
        ),
    )

    health = collect_wiki_health(tmp_path, today=date(2026, 6, 6))
    checks = checks_by_id(health)

    assert checks["instruction_surface_contract"]["status"] == "FAIL"
    assert (
        "Entry: scripts/create_illustration_carousel.py"
        in checks["instruction_surface_contract"]["evidence"]["banned_hits"]["AGENTS.md"]
    )


def test_health_flags_retired_claude_instruction_surface(tmp_path):
    minimal_workspace(tmp_path)
    write_text(
        tmp_path / "config" / "instruction_surface_contract.json",
        json.dumps(
            {
                "schema_version": "1.0",
                "max_agents_md_lines": 20,
                "surfaces": ["AGENTS.md"],
                "retired_paths": ["CLAUDE.md"],
                "required_phrases": ["scripts/autopublish.py"],
                "banned_phrases": {"AGENTS.md": []},
            }
        ),
    )
    write_text(tmp_path / "AGENTS.md", "# AGENTS\n\nscripts/autopublish.py\n")
    write_text(tmp_path / "CLAUDE.md", "# Retired compatibility surface\n")

    health = collect_wiki_health(tmp_path, today=date(2026, 6, 28))
    checks = checks_by_id(health)

    assert checks["instruction_surface_contract"]["status"] == "FAIL"
    assert "CLAUDE.md" in checks["instruction_surface_contract"]["evidence"]["retired_hits"]


def test_health_passes_clean_instruction_surface_contract(tmp_path):
    minimal_workspace(tmp_path)
    write_text(
        tmp_path / "config" / "instruction_surface_contract.json",
        json.dumps(
            {
                "schema_version": "1.0",
                "max_agents_md_lines": 20,
                "surfaces": ["AGENTS.md"],
                "retired_paths": ["CLAUDE.md"],
                "required_phrases": [
                    "config/rules/",
                    "scripts/agentic_os.py carousel-doctor",
                    "scripts/autopublish.py",
                ],
                "banned_phrases": {
                    "AGENTS.md": ["Entry: scripts/create_illustration_carousel.py"],
                },
            }
        ),
    )
    clean = "# SURFACE\n\nconfig/rules/\nscripts/agentic_os.py carousel-doctor\nscripts/autopublish.py\n"
    write_text(tmp_path / "AGENTS.md", clean)

    health = collect_wiki_health(tmp_path, today=date(2026, 6, 6))
    checks = checks_by_id(health)

    assert checks["instruction_surface_contract"]["status"] == "PASS"


def test_feedback_health_rejects_a_stored_pass_after_its_artifact_changes(tmp_path):
    package = tmp_path / "output" / "carousels" / "2026-09-04" / "flight-story"
    write_text(package / "slides.json", json.dumps({"route": "flight"}))
    write_text(
        package / "creator-correction.json",
        json.dumps(
            {
                "schema_version": "creator-correction/v3",
                "events": [
                    {
                        "feedback_id": "fb-stale-eval",
                        "kind": "correction",
                        "primary_diagnosis": "scene_action",
                        "status": "evaluated",
                        "action_taken": {"type": "existing_package_repair"},
                        "resolution_evidence": ["slides.json"],
                        "eval_task_ids": ["FEEDBACK-STALE-EVAL"],
                    }
                ],
            }
        ),
    )
    write_text(
        tmp_path / "evals" / "feedback-cases" / "FEEDBACK-STALE-EVAL.json",
        json.dumps(
            {
                "schema_version": "creator-feedback-eval/v1",
                "task_id": "FEEDBACK-STALE-EVAL",
                "status": "passed",
                "affected_artifacts": ["slides.json"],
                "checks": [
                    {
                        "code": "declared_artifacts_repaired",
                        "status": "PASS",
                        "current_hashes": {"slides.json": "sha256:" + "0" * 64},
                    }
                ],
            }
        ),
    )

    evidence = feedback_health_evidence(tmp_path, date(2026, 9, 5))

    issues = evidence["invalid_events"][
        "output/carousels/2026-09-04/flight-story/creator-correction.json"
    ]
    assert any("linked eval FEEDBACK-STALE-EVAL is stale" in issue for issue in issues)


def test_feedback_health_separates_live_feedback_on_read_only_package_from_history(tmp_path):
    package = tmp_path / "output" / "carousels" / "2026-07-01" / "legacy-story"
    package.mkdir(parents=True)
    event_dir = tmp_path / "memory" / "agentic" / "learning-events"
    write_text(
        event_dir / "event-feedback-live.json",
        json.dumps(
            {
                "schema_version": "learning-event/v1",
                "event_id": "event-feedback-live",
                "source": "creator_feedback",
                "created_at": "2026-09-05T06:00:00+00:00",
                "diagnosis": "provenance_qa",
                "package_path": "output/carousels/2026-07-01/legacy-story",
                "feedback_status": "captured",
                "resolution_evidence": [],
                "feedback_metadata": {
                    "feedback_id": "fb-live-on-legacy",
                    "kind": "rejection",
                    "primary_diagnosis": "provenance_qa",
                    "must_change": ["Reject the visibly broken hand."],
                    "eval_task_ids": [],
                    "historical_package_read_only": True,
                },
            }
        ),
    )
    write_text(
        event_dir / "event-feedback-history.json",
        json.dumps(
            {
                "schema_version": "learning-event/v1",
                "event_id": "event-feedback-history",
                "source": "creator_feedback",
                "created_at": "2026-09-05T06:00:00+00:00",
                "feedback_status": "evaluated",
                "feedback_metadata": {
                    "feedback_id": "fb-backfilled-history",
                    "historical_only": True,
                },
            }
        ),
    )

    evidence = feedback_health_evidence(tmp_path, date(2026, 9, 5))

    assert [item["feedback_id"] for item in evidence["live_feedback_on_read_only_packages"]] == [
        "fb-live-on-legacy"
    ]
    assert [item["feedback_id"] for item in evidence["historical_feedback"]] == [
        "fb-backfilled-history"
    ]
    live_path = "memory/agentic/learning-events/event-feedback-live.json"
    assert any("unresolved feedback debt" in issue for issue in evidence["invalid_events"][live_path])
    assert not any("fb-backfilled-history" in issue for issues in evidence["invalid_events"].values() for issue in issues)
