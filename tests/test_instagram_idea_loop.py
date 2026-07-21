from __future__ import annotations

import json
import subprocess
import sys
import tomllib
from pathlib import Path

from pipeline.agentic.instagram_idea_loop import (
    IdeaLoopConfig,
    blind_candidate_fingerprint,
    candidate_fingerprint,
    prepare_run,
    resume_run,
    validate_run,
)


ROOT = Path(__file__).resolve().parents[1]


def _write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def _candidate(candidate_id: str, maker_task_id: str) -> dict[str, object]:
    return {
        "candidate_id": candidate_id,
        "iteration": 1,
        "maker_agent": "asot_idea_maker",
        "maker_task_id": maker_task_id,
        "title": "The Emergency Contact Upgrade",
        "concrete_moment": "She notices he has quietly become the name on every form.",
        "universal_truth": "Love becomes official in ordinary paperwork before ceremonies notice.",
        "audience_mirror": "Couples who became each other's default person without announcing it.",
        "scroll_stop": "When did your emergency contact become home?",
        "emotional_contradiction": "A bureaucratic field reveals a deeply private belonging.",
        "scene_proof": [
            "A form pauses under her pen at emergency contact.",
            "His number is already filled on an older folded form.",
        ],
        "relationship_motion": "Both have independently chosen the other as the first call.",
        "retention_ladder": [
            "Who will she write?",
            "Why is the answer already present?",
            "What did the tiny field quietly make official?",
        ],
        "payoff": "Some love stories become family one form at a time.",
        "dm_send_reason": "A viewer sends it with: you became my person like this too.",
        "format_recommendation": "carousel",
        "asot_turn": "Warm desi shared-adulthood proof through accumulated forms, not a proposal trope.",
        "evidence_paths": ["memory/semantic/carousel-idea-preferences.md"],
        "novelty_fingerprint": "chosen-family|paperwork|mutual-default-person",
        "risks": ["Keep the forms legible as objects without turning the deck into UI."],
    }


def _review(candidate: dict[str, object], verifier_task_id: str) -> dict[str, object]:
    return {
        "candidate_id": candidate["candidate_id"],
        "candidate_sha256": candidate_fingerprint(candidate),
        "blind_input_sha256": blind_candidate_fingerprint(candidate),
        "maker_task_id": candidate["maker_task_id"],
        "verifier_agent": "asot_idea_verifier",
        "verifier_task_id": verifier_task_id,
        "scores": {
            "story_selling": 29,
            "golden_theme": 29,
            "distribution": 28,
            "visual_generativity": 28,
            "story_director": {
                "hook": 9,
                "story": 9,
                "bridge": 9,
                "relationship_motion": 9,
                "ending": 9,
                "dm_send": 9,
            },
        },
        "stage_scene_gate": "PASS",
        "taste_gate": "PASS_NO_CAP",
        "safety_gate": "PASS",
        "exclusion_hits": [],
        "hard_failures": [],
        "verdict": "PASS",
        "reasons": ["The ordinary form acts as specific, visible chosen-family proof."],
        "repair_instructions": [],
    }


def _successful_run(tmp_path: Path) -> tuple[Path, dict[str, object], dict[str, object]]:
    run_dir = prepare_run(
        ROOT,
        config=IdeaLoopConfig(max_iterations=3, candidate_budget=6),
        run_dir=tmp_path / "idea-run",
    )
    state_path = run_dir / ".internal" / "loop-state.json"
    state = json.loads(state_path.read_text(encoding="utf-8"))
    state.update(
        {
            "status": "READY_FOR_CONCEPT_LOCK",
            "stage": "CONCEPT_LOCK",
            "iteration": 2,
            "final_candidate_id": "idea-01",
        }
    )
    _write_json(state_path, state)

    selected = _candidate("idea-01", "maker-task-a")
    rejected = _candidate("idea-02", "maker-task-b")
    rejected["title"] = "Internal rejected route"
    _write_json(
        run_dir / "concept-routes.json",
        {"schema_version": "1.0", "run_id": state["run_id"], "candidates": [selected, rejected]},
    )
    _write_json(
        run_dir / "verification.json",
        {
            "schema_version": "1.0",
            "run_id": state["run_id"],
            "reviews": [
                _review(selected, "critic-task-a"),
                _review(selected, "critic-task-b"),
            ],
            "selector": {
                "selector_agent": "asot_idea_verifier",
                "selector_task_id": "selector-task-c",
                "candidate_id": "idea-01",
                "candidate_sha256": candidate_fingerprint(selected),
                "critic_task_ids": ["critic-task-a", "critic-task-b"],
                "verdict": "PASS",
                "reasons": ["Both independent reviews pass and the route remains the strongest."],
            },
        },
    )
    _write_json(
        run_dir / "concept-selection.json",
        {
            "schema_version": "1.0",
            "run_id": state["run_id"],
            "status": "READY_FOR_CONCEPT_LOCK",
            "selected_candidate_id": "idea-01",
            "selector_task_id": "selector-task-c",
            "creator_approval": "PENDING",
            "reason": "The route cleared both blind reviews without a taste cap.",
            "next_action": "Ask the creator to approve, reject, or repair the concept.",
            "uncertainties": ["Performance remains a hypothesis until published."],
        },
    )
    for name in (
        "source-memory-brief.json",
        "concept-debate.json",
        "concept-repairs.json",
        "taste-gate.json",
    ):
        _write_json(run_dir / name, {"schema_version": "1.0", "run_id": state["run_id"]})
    (run_dir / "creator-brief.md").write_text(
        "# The Emergency Contact Upgrade\n\nselected candidate: idea-01\n\n"
        "A current best bet for concept approval, not a performance guarantee.\n",
        encoding="utf-8",
    )
    return run_dir, selected, rejected


def test_prepare_run_discovers_evidence_without_requiring_a_seed(tmp_path: Path) -> None:
    run_dir = prepare_run(
        ROOT,
        config=IdeaLoopConfig(),
        run_dir=tmp_path / "no-seed",
    )

    state = json.loads((run_dir / ".internal/loop-state.json").read_text(encoding="utf-8"))
    evidence = json.loads(
        (run_dir / ".internal/evidence-manifest.json").read_text(encoding="utf-8")
    )
    prompt = (run_dir / ".internal/orchestration-prompt.md").read_text(encoding="utf-8")

    assert state["seed"] is None
    assert state["status"] == "RUNNING"
    assert "memory/semantic/carousel-idea-preferences.md" in {
        record["path"] for record in evidence["core"]
    }
    assert "asot_idea_scout" in prompt
    assert "two blind verifier tasks" in prompt


def test_success_requires_two_fresh_verifiers_and_a_distinct_selector(tmp_path: Path) -> None:
    run_dir, _, _ = _successful_run(tmp_path)

    report = validate_run(run_dir)

    assert report.valid is True
    assert report.status == "READY_FOR_CONCEPT_LOCK"


def test_taste_cap_cannot_be_hidden_by_high_numeric_scores(tmp_path: Path) -> None:
    run_dir, _, _ = _successful_run(tmp_path)
    verification_path = run_dir / "verification.json"
    verification = json.loads(verification_path.read_text(encoding="utf-8"))
    verification["reviews"][0]["taste_gate"] = "REPAIR"
    _write_json(verification_path, verification)

    report = validate_run(run_dir)

    assert report.valid is False
    assert any("cannot bypass" in error or "did not earn PASS" in error for error in report.errors)


def test_maker_cannot_verify_its_own_route(tmp_path: Path) -> None:
    run_dir, _, _ = _successful_run(tmp_path)
    verification_path = run_dir / "verification.json"
    verification = json.loads(verification_path.read_text(encoding="utf-8"))
    verification["reviews"][0]["verifier_task_id"] = "maker-task-a"
    _write_json(verification_path, verification)

    report = validate_run(run_dir)

    assert report.valid is False
    assert any("maker and verifier" in error for error in report.errors)


def test_creator_brief_never_exposes_internal_losing_routes(tmp_path: Path) -> None:
    run_dir, _, rejected = _successful_run(tmp_path)
    brief = run_dir / "creator-brief.md"
    brief.write_text(brief.read_text(encoding="utf-8") + f"\n{rejected['candidate_id']}\n")

    report = validate_run(run_dir)

    assert report.valid is False
    assert "creator-brief.md exposes a non-selected route" in report.errors


def test_stale_verifier_fingerprint_cannot_pass_after_candidate_repair(tmp_path: Path) -> None:
    run_dir, _, _ = _successful_run(tmp_path)
    routes_path = run_dir / "concept-routes.json"
    routes = json.loads(routes_path.read_text(encoding="utf-8"))
    routes["candidates"][0]["payoff"] = "A repaired payoff that changes the reviewed card."
    _write_json(routes_path, routes)

    report = validate_run(run_dir)

    assert report.valid is False
    assert any("fingerprint is stale" in error for error in report.errors)


def test_candidate_budget_is_enforced_per_iteration(tmp_path: Path) -> None:
    run_dir, _, _ = _successful_run(tmp_path)
    routes_path = run_dir / "concept-routes.json"
    routes = json.loads(routes_path.read_text(encoding="utf-8"))
    for number in range(3, 9):
        routes["candidates"].append(_candidate(f"idea-{number:02d}", f"maker-task-{number}"))
    _write_json(routes_path, routes)

    report = validate_run(run_dir)

    assert report.valid is False
    assert any("candidate budget exceeded" in error for error in report.errors)


def test_nonterminal_run_can_resume_without_losing_history(tmp_path: Path) -> None:
    run_dir = prepare_run(
        ROOT,
        config=IdeaLoopConfig(),
        run_dir=tmp_path / "resumable",
    )

    state = resume_run(run_dir)

    assert state.status == "RUNNING"
    assert state.history[-1]["event"] == "run_resumed"


def test_honest_no_go_is_valid_but_never_promotes_a_candidate(tmp_path: Path) -> None:
    run_dir = prepare_run(
        ROOT,
        config=IdeaLoopConfig(),
        run_dir=tmp_path / "no-go",
    )
    state_path = run_dir / ".internal/loop-state.json"
    state = json.loads(state_path.read_text(encoding="utf-8"))
    state.update(
        {
            "status": "NO_GO",
            "stage": "SELECT",
            "iteration": 3,
            "stop_reason": "No fresh route cleared the taste gate within budget.",
            "final_candidate_id": None,
        }
    )
    _write_json(state_path, state)
    for name in ("source-memory-brief.json", "concept-routes.json", "verification.json"):
        _write_json(run_dir / name, {"schema_version": "1.0", "run_id": state["run_id"]})
    (run_dir / "creator-brief.md").write_text(
        "No route cleared every gate; no candidate is being promoted.\n",
        encoding="utf-8",
    )

    report = validate_run(run_dir)

    assert report.valid is True
    assert report.status == "NO_GO"


def test_cli_dry_run_prepares_durable_prompt_without_invoking_codex(tmp_path: Path) -> None:
    run_dir = tmp_path / "dry-run"
    completed = subprocess.run(
        [
            sys.executable,
            "scripts/instagram_idea_loop.py",
            "run",
            "--dry-run",
            "--run-dir",
            str(run_dir),
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
        timeout=30,
    )

    assert completed.returncode == 0
    assert json.loads(completed.stdout)["status"] == "DRY_RUN"
    state = json.loads((run_dir / ".internal/loop-state.json").read_text(encoding="utf-8"))
    assert state["status"] == "DRY_RUN"


def test_loop_agents_are_project_scoped_read_only_and_bounded() -> None:
    expected = {"asot_idea_scout", "asot_idea_maker", "asot_idea_verifier"}
    found: set[str] = set()
    for path in (ROOT / ".codex" / "agents").glob("asot_idea_*.toml"):
        payload = tomllib.loads(path.read_text(encoding="utf-8"))
        found.add(payload["name"])
        assert payload["sandbox_mode"] == "read-only"
        assert payload["developer_instructions"].strip()

    config = tomllib.loads((ROOT / ".codex/config.toml").read_text(encoding="utf-8"))
    assert found == expected
    assert config["agents"] == {"max_threads": 4, "max_depth": 1}


def test_make_and_skill_registry_expose_one_command_loop() -> None:
    makefile = (ROOT / "Makefile").read_text(encoding="utf-8")
    systems = json.loads((ROOT / "config/skill-systems.json").read_text(encoding="utf-8"))
    loop = systems["systems"]["instagram_idea_loop"]

    assert "idea-loop:" in makefile
    assert "scripts/instagram_idea_loop.py run" in makefile
    assert ".agents/skills/a-story-instagram-idea-loop/SKILL.md" in loop["components"]
    assert set(loop["agents"]) == {
        ".codex/agents/asot_idea_scout.toml",
        ".codex/agents/asot_idea_maker.toml",
        ".codex/agents/asot_idea_verifier.toml",
    }
    assert "creator_concept_lock_required" in loop["gates"]
