import json
import hashlib
import subprocess
import sys
from pathlib import Path

from pipeline.stages.carousel_intelligence import (
    DEFAULT_HEURISTIC_FLOOR,
    NATIVE_METRIC_LABELS,
    REQUIRED_DIMENSION_MINIMUMS,
    analyze_package,
    calibrate_seed,
    carousel_gate_policy,
    dry_run_seed,
    write_intelligence_artifacts,
    write_dry_run_report,
)


ROOT = Path(__file__).resolve().parents[1]


def test_calibration_thresholds_remain_unchanged():
    assert DEFAULT_HEURISTIC_FLOOR == 70
    assert REQUIRED_DIMENSION_MINIMUMS == {
        "scene_proof": 3,
        "relationship_motion": 3,
        "send_save_reason": 3,
    }


def test_creator_approved_gate_policy_is_enabled_and_hash_bound():
    policy = carousel_gate_policy(ROOT)
    assert policy["enabled"] is True
    assert policy["mode"] == "fail_closed"
    assert policy["reason"] == "creator_approved_workflow"
    assert policy["approved_by"] == "creator"
    assert policy["evaluation"] == "structural_with_advisory_heuristics"


def test_gate_policy_fails_closed_when_approved_evidence_drifts(tmp_path):
    report_dir = tmp_path / "output/reports/2026-09-19-full-carousel-audit"
    report_dir.mkdir(parents=True)
    config_dir = tmp_path / "config"
    config_dir.mkdir()
    visual = report_dir / "visual-verification-decisions.json"
    paths = report_dir / "local-slide-path-map.json"
    visual.write_text("approved visual decisions\n", encoding="utf-8")
    paths.write_text("approved path map\n", encoding="utf-8")
    policy = {
        "schema_version": "carousel-intelligence-gate/v1",
        "enabled": True,
        "mode": "fail_closed",
        "thresholds": {
            "heuristic_floor": 70,
            "required_dimension_minimums": REQUIRED_DIMENSION_MINIMUMS,
        },
        "bindings": {
            "visual_decisions": {
                "path": str(visual.relative_to(tmp_path)),
                "sha256": hashlib.sha256(visual.read_bytes()).hexdigest(),
            },
            "local_path_map": {
                "path": str(paths.relative_to(tmp_path)),
                "sha256": hashlib.sha256(paths.read_bytes()).hexdigest(),
            },
        },
    }
    (config_dir / "carousel-intelligence-gate.json").write_text(json.dumps(policy), encoding="utf-8")
    assert carousel_gate_policy(tmp_path)["enabled"] is True
    visual.write_text("drifted\n", encoding="utf-8")
    result = carousel_gate_policy(tmp_path)
    assert result["enabled"] is False
    assert result["reason"] == "policy_validation_failed"
    assert "visual_decisions_drift" in result["errors"]


def _package(tmp_path: Path, slides: list[dict]) -> Path:
    package = tmp_path / "carousel"
    package.mkdir(parents=True)
    (package / "slides.json").write_text(json.dumps({"slides": slides}), encoding="utf-8")
    (package / "concept.json").write_text(json.dumps({"title": "A couple moment"}), encoding="utf-8")
    return package


def _passing_slides() -> list[dict]:
    return [
        {"slide": 1, "copy": "The specific couple problem", "visual": "doorway with bags", "story_job": "cover", "send_reason": "send to your partner"},
        {"slide": 2, "copy": "One responds", "visual": "one holds the bag while the other opens the door", "story_job": "escalation", "relationship_motion": "chooses to help"},
        {"slide": 3, "copy": "Maybe this is love", "visual": "they sit together after the problem", "story_job": "payoff", "payoff": "reframe", "send_reason": "save this"},
    ]


def test_verified_seed_covers_all_current_carousels_and_slides():
    payload = json.loads((ROOT / "output/reports/2026-09-19-full-carousel-audit/current-carousel-sequences.json").read_text())
    assert payload["schema_version"] == "carousel-seed-evidence/v1"
    assert payload["coverage"]["carousel_count"] == 27
    assert payload["coverage"]["slide_count"] == 158
    assert sum(len(sequence["slides"]) for sequence in payload["sequences"]) == 158
    assert all(slide["observed_scene"] and slide["story_job"] for sequence in payload["sequences"] for slide in sequence["slides"])


def test_native_metric_labels_are_preserved_and_reels_are_excluded(tmp_path):
    corpus = tmp_path / "corpus"
    corpus.mkdir()
    (corpus / "rows.json").write_text(json.dumps({"posts": [
        {"shortcode": "carousel1", "post_type": "carousel", "Views": 10, "Viewers": 8, "Shares": 2, "Saves": 3, "Profile visits": 1, "Follows": 1},
        {"shortcode": "reel1", "post_type": "reel", "Views": 100, "Shares": 100},
    ]}), encoding="utf-8")
    report = analyze_package(_package(tmp_path, _passing_slides()), root=tmp_path)
    assert report["metrics"]["native_labels"] == list(NATIVE_METRIC_LABELS)
    assert [row["shortcode"] for row in report["metrics"]["eligible_carousel_rows"]] == ["carousel1"]
    assert report["metrics"]["coverage"]["causal_claims_allowed"] is False


def test_missing_visual_evidence_blocks(tmp_path):
    slides = _passing_slides()
    slides[1]["visual"] = ""
    report = analyze_package(_package(tmp_path, slides), root=tmp_path)
    assert report["concept_gate"]["status"] == "blocked"
    assert "concrete action" in " ".join(report["concept_gate"]["repairs"])


def test_repeated_static_scene_blocks_unless_continuous(tmp_path):
    slides = _passing_slides()
    for slide in slides:
        slide["visual"] = "the same static room"
    report = analyze_package(_package(tmp_path, slides), root=tmp_path)
    assert report["concept_gate"]["gates"]["repeated_static_scene_rejected"] is False
    assert report["concept_gate"]["status"] == "blocked"


def test_missing_payoff_and_send_reason_blocks(tmp_path):
    slides = _passing_slides()
    slides[-1].pop("payoff")
    slides[-1]["story_job"] = "beat"
    for slide in slides:
        slide.pop("send_reason", None)
    report = analyze_package(_package(tmp_path, slides), root=tmp_path)
    assert report["concept_gate"]["status"] == "blocked"
    repairs = " ".join(report["concept_gate"]["repairs"])
    assert "ending deepen" in repairs
    assert "send or save" in repairs


def test_low_heuristic_score_blocks_and_passing_writes_both_artifacts(tmp_path):
    blocked = analyze_package(_package(tmp_path, [{"slide": 1, "copy": "A line"}]), root=tmp_path)
    assert blocked["heuristic"]["total"] < 70
    assert blocked["concept_gate"]["status"] == "blocked"
    package = _package(tmp_path / "pass", _passing_slides())
    report = write_intelligence_artifacts(package, analyze_package(package, root=tmp_path))
    assert report["concept_gate"]["status"] == "passed"
    assert (package / "carousel-intelligence.json").is_file()
    markdown = (package / "carousel-intelligence.md").read_text()
    assert "not a prediction" in markdown
    assert "causal" in markdown


def test_cli_concept_check_returns_block_and_repairs(tmp_path):
    package = _package(tmp_path, [{"slide": 1, "copy": "A line"}])
    result = subprocess.run(
        [sys.executable, str(ROOT / "scripts/carousel.py"), "concept-check", str(package)],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 2
    payload = json.loads(result.stdout)
    assert payload["state"] == "blocked"
    assert "intelligence" in payload
    assert (package / "carousel-intelligence.json").is_file()
    assert "repair" in payload["next_action"]


def test_verified_seed_dry_run_reports_every_sequence(tmp_path):
    report = dry_run_seed(ROOT)
    assert report["sequence_count"] == 27
    assert report["slide_count"] == 158
    assert report["causal_claims_allowed"] is False
    assert len(report["sequences"]) == 27
    write_dry_run_report(ROOT, output_dir=tmp_path)
    assert (tmp_path / "carousel-intelligence-dry-run.json").is_file()
    assert (tmp_path / "carousel-intelligence-dry-run.md").is_file()


def test_calibration_reports_all_sequences_with_complete_visual_coverage():
    report = calibrate_seed(ROOT)
    assert report["schema_version"] == "carousel-intelligence-calibration/v1"
    assert len(report["sequences"]) == 27
    assert sum(item["slide_count"] for item in report["sequences"]) == 158
    inventory = report["coverage"]["workspace_visual_inventory"]
    assert inventory["expected_slide_count"] == 158
    assert inventory["available_slide_count"] == 158
    assert inventory["missing_slide_count"] == 0
    assert report["after"]["causal_claims_allowed"] is False
    assert report["effective"] == {
        "passed_count": 27,
        "blocked_count": 0,
        "basis": "complete local pixels plus the recorded visual-verification decision plus analyzer pass",
    }
    assert report["gate_enablement"]["enabled"] is True
    assert report["gate_enablement"]["mode"] == "fail_closed"
    assert report["gate_enablement"]["reason"] == "creator_approved_workflow"
    assert all("decision" in item and "visual_verification" in item for item in report["sequences"])

    rows = {item["shortcode"]: item for item in report["sequences"]}
    assert rows["DcT42EoCb1d"]["after"]["status"] == "passed"
    assert rows["DcT42EoCb1d"]["visual_verification"]["classification"] == "analyzer_false_negative"
    assert rows["DcT42EoCb1d"]["decision"] == "allow_pass"
    assert rows["DaiMWVMiQ7v"]["after"]["status"] == "passed"
    assert rows["DaiMWVMiQ7v"]["decision"] == "allow_pass"
    assert rows["DbvlHgXCdIS"]["decision"] == "allow_pass"
    assert all(item["decision"] == "allow_pass" for item in report["sequences"])


def test_terminal_audit_language_maps_to_payoff_and_send_save(tmp_path):
    package = _package(tmp_path, [
        {"slide": 1, "copy": "A couple problem", "visual": "doorway", "story_job": "cover"},
        {"slide": 2, "copy": "They choose each other", "visual": "one holds the bag", "story_job": "relationship turn"},
        {"slide": 3, "copy": "Maybe love is finding home", "visual": "they sit together", "story_job": "terminal reframe"},
    ])
    report = analyze_package(package, root=tmp_path)
    assert report["concept_gate"]["gates"]["ending_payoff_or_reframe"] is True
    assert report["concept_gate"]["gates"]["send_or_save_reason"] is True


def test_confirmed_bodily_metaphor_language_maps_to_terminal_payoff(tmp_path):
    package = _package(tmp_path, [
        {"slide": 1, "copy": "Some people change the weather inside you", "visual": "couple at a table", "story_job": "opens a metaphor"},
        {"slide": 2, "copy": "The pressure gets loud", "visual": "crowded cafe", "story_job": "shows the pre-state"},
        {"slide": 3, "copy": "Your chest stops arguing with the world", "visual": "partner sits beside him", "story_job": "makes the metaphor bodily and affectionate"},
    ])
    report = analyze_package(package, root=tmp_path)
    assert report["concept_gate"]["gates"]["ending_payoff_or_reframe"] is True


def test_cli_calibrate_writes_machine_and_creator_reports(tmp_path):
    result = subprocess.run(
        [sys.executable, str(ROOT / "scripts/carousel.py"), "calibrate", "--output-dir", str(tmp_path)],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
    payload = json.loads(result.stdout)
    assert payload["next_action"] == "inspect_carousel_intelligence_calibration"
    assert payload["calibration"]["schema_version"] == "carousel-intelligence-calibration/v1"
    assert (tmp_path / "carousel-intelligence-calibration.json").is_file()
    assert (tmp_path / "carousel-intelligence-calibration.md").is_file()


def test_proof_prepare_requires_gate_for_marked_v3_package(tmp_path):
    package = _package(tmp_path, _passing_slides())
    (package / "generation-state.json").write_text(json.dumps({"schema_version": "carousel-generation-state/v3"}), encoding="utf-8")
    (package / ".concept-lock-required").write_text("carousel-intelligence/v1\n", encoding="utf-8")
    import scripts.carousel as carousel_cli

    try:
        carousel_cli._core_prepare(package, proof_slide=1, formats=None)
    except ValueError as exc:
        assert "Concept gate required" in str(exc)
    else:
        raise AssertionError("proof preparation bypassed the concept gate")


def test_legacy_v2_package_can_still_be_read_without_gate(tmp_path, monkeypatch):
    package = _package(tmp_path, _passing_slides())
    (package / "generation-state.json").write_text(json.dumps({"schema_version": "carousel-generation-state/v2"}), encoding="utf-8")
    import pipeline.stages.codex_builtin_image_generation as generation
    import scripts.carousel as carousel_cli

    monkeypatch.setattr(generation, "prepare_codex_builtin_image_generation", lambda *args, **kwargs: {"status": "draft", "next_action": "legacy"})
    assert carousel_cli._core_prepare(package, proof_slide=1, formats=None)["status"] == "draft"


def test_analyzer_merges_copy_concept_and_visual_plan_artifacts(tmp_path):
    package = _package(tmp_path, [
        {"slide": 1, "copy": "A specific couple situation", "role": "cover"},
        {"slide": 2, "copy": "They choose each other", "role": "turn"},
        {"slide": 3, "copy": "This is love", "role": "payoff", "payoff": "reframe"},
    ])
    (package / "concept.json").write_text(json.dumps({"title": "Merged concept", "send_reason": "send this to your partner"}), encoding="utf-8")
    (package / "visual-plan.json").write_text(json.dumps({"slides": [
        {"slide": 1, "physical_action": "couple exchanges a key"},
        {"slide": 2, "physical_action": "one opens the door for the other", "relationship_motion": "chooses to help"},
        {"slide": 3, "physical_action": "they sit together at home"},
    ]}), encoding="utf-8")
    report = analyze_package(package, root=tmp_path)
    assert report["sequence"]["title"] == "Merged concept"
    assert all(slide["scene"] for slide in report["slides"])
    assert report["concept_gate"]["gates"]["copy_visual_alignment"] is True


def test_metric_age_bands_are_recorded_without_enabling_causal_claims(tmp_path):
    corpus = tmp_path / "corpus"
    corpus.mkdir()
    rows = []
    for age, code in ((10, "c1"), (20, "c2"), (40, "c3")):
        rows.append({"shortcode": code, "post_type": "carousel", "age_days": age, "Views": age})
    rows.append({"shortcode": "r1", "post_type": "reel", "age_days": 10, "Views": 999})
    (corpus / "metrics.json").write_text(json.dumps({"posts": rows}), encoding="utf-8")
    report = analyze_package(_package(tmp_path, _passing_slides()), root=tmp_path)
    assert report["metrics"]["coverage"]["age_bands_complete"] is False
    assert all(row["age_days"] is None for row in report["metrics"]["eligible_carousel_rows"])
    assert len(report["metrics"]["eligible_carousel_rows"]) == 3
    assert report["metrics"]["coverage"]["causal_claims_allowed"] is False
