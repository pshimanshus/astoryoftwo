from __future__ import annotations

import json
import subprocess
import sys
import tomllib
from pathlib import Path

import pytest

import pipeline.agentic.instagram_idea_loop as idea_loop
from pipeline.agentic.instagram_idea_loop import (
    IdeaLoopConfig,
    blind_candidate_card,
    blind_candidate_fingerprint,
    build_codex_command,
    candidate_fingerprint,
    execute_loop,
    failure_signature,
    prepare_run,
    resume_run,
    validate_run,
)


ROOT = Path(__file__).resolve().parents[1]
TEST_CORE_EVIDENCE_PATHS = (
    "config/skills/creator-skill-stack.md",
    "config/skills/carousel-jam-runtime-context.md",
    "memory/semantic/carousel-idea-preferences.md",
    "wiki/insights/successful-carousel-standard.md",
)


def _write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def _candidate(
    candidate_id: str,
    maker_task_id: str,
    *,
    iteration: int = 1,
    parent_candidate_id: str | None = None,
    repair_task_id: str | None = None,
) -> dict[str, object]:
    candidate: dict[str, object] = {
        "candidate_id": candidate_id,
        "iteration": iteration,
        "maker_agent": "asot_idea_maker",
        "maker_task_id": maker_task_id,
        "alive_premise": (
            "A tiny bureaucratic field reveals that two people quietly became family."
        ),
        "moment_origin": "generic_relationship_hypothesis",
        "moment_origin_detail": (
            "A generic relationship pattern; no lived Aachu/Zuv incident is claimed."
        ),
        "lived_fact_status": "NOT_CLAIMED",
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
        "asot_turn": (
            "Warm desi shared-adulthood proof through accumulated forms, "
            "not a proposal trope."
        ),
        "evidence_paths": ["memory/semantic/carousel-idea-preferences.md"],
        "novelty_fingerprint": "chosen-family|paperwork|mutual-default-person",
        "risks": ["Keep the forms legible as objects without turning the deck into UI."],
    }
    if parent_candidate_id is not None:
        candidate["parent_candidate_id"] = parent_candidate_id
    if repair_task_id is not None:
        candidate["repair_task_id"] = repair_task_id
    return candidate


def _review(
    candidate: dict[str, object],
    verifier_task_id: str,
    verifier_lens: str | None = None,
) -> dict[str, object]:
    verifier_lens = verifier_lens or (
        "audience_distribution"
        if "-a" in verifier_task_id
        else "stage_scene_taste_safety"
    )
    return {
        "candidate_id": candidate["candidate_id"],
        "candidate_sha256": candidate_fingerprint(candidate),
        "blind_input_sha256": blind_candidate_fingerprint(candidate),
        "maker_task_id": candidate["maker_task_id"],
        "verifier_agent": "asot_idea_verifier",
        "verifier_task_id": verifier_task_id,
        "verifier_lens": verifier_lens,
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


def _failing_review(
    candidate: dict[str, object], verifier_task_id: str
) -> dict[str, object]:
    review = _review(candidate, verifier_task_id)
    review["scores"]["story_selling"] = 22
    review["verdict"] = "REPAIR"
    review["reasons"] = ["The route remains recognizable but too generic to promote."]
    review["repair_instructions"] = ["Find a more ownable visible incident."]
    return review


def _stopping_review(
    candidate: dict[str, object], verifier_task_id: str
) -> dict[str, object]:
    review = _failing_review(candidate, verifier_task_id)
    review["taste_gate"] = "STOP"
    review["verdict"] = "STOP"
    review["hard_failures"] = ["nonrepairable_genericity"]
    review["repair_instructions"] = []
    return review


def _source_brief(run_id: str) -> dict[str, object]:
    return {
        "schema_version": "1.0",
        "run_id": run_id,
        "scout_agent": "asot_idea_scout",
        "scout_task_id": "scout-task-a",
        "evidence_paths": ["memory/semantic/carousel-idea-preferences.md"],
        "excluded_lanes": ["recent generic chai route"],
        "opportunity_signals": ["chosen family revealed through ordinary paperwork"],
        "uncertainties": ["Performance remains unproven until posting."],
    }


def _no_go_artifacts(
    run_id: str,
    *,
    iteration: int = 1,
    repairable: bool = False,
) -> tuple[dict[str, object], dict[str, object]]:
    suffix = f"-round-{iteration}"
    parent_a = f"idea-a-round-{iteration - 1}" if iteration > 1 else None
    parent_b = f"idea-b-round-{iteration - 1}" if iteration > 1 else None
    route_a = _candidate(
        f"idea-a-round-{iteration}",
        f"maker-task-a{suffix}",
        iteration=iteration,
        parent_candidate_id=parent_a,
        repair_task_id=f"repair-task-a{suffix}" if iteration > 1 else None,
    )
    route_b = _candidate(
        f"idea-b-round-{iteration}",
        f"maker-task-b{suffix}",
        iteration=iteration,
        parent_candidate_id=parent_b,
        repair_task_id=f"repair-task-b{suffix}" if iteration > 1 else None,
    )
    route_b["title"] = "A second independently made route"
    critic_a = f"critic-task-a{suffix}"
    critic_b = f"critic-task-b{suffix}"
    review_factory = _failing_review if repairable else _stopping_review
    pool = {
        "schema_version": "1.0",
        "run_id": run_id,
        "candidates": [route_a, route_b],
    }
    verification = {
        "schema_version": "1.0",
        "run_id": run_id,
        "reviews": [
            review_factory(route_a, critic_a),
            review_factory(route_a, critic_b),
            review_factory(route_b, critic_a),
            review_factory(route_b, critic_b),
        ],
        "selector": {
            "selector_agent": "asot_idea_verifier",
            "selector_task_id": f"selector-task-c{suffix}",
            "candidate_id": None,
            "candidate_sha256": None,
            "critic_task_ids": [critic_a, critic_b],
            "verdict": "NO_GO",
            "reasons": ["Neither independently reviewed route clears the fixed bar."],
        },
    }
    return pool, verification


def _write_iteration_snapshot(
    run_dir: Path,
    *,
    iteration: int,
    pool: dict[str, object],
    verification: dict[str, object],
) -> None:
    run_id = str(pool["run_id"])
    candidates = {
        str(candidate["candidate_id"]): candidate
        for candidate in pool["candidates"]
    }
    for review in verification["reviews"]:
        candidate = candidates[str(review["candidate_id"])]
        _write_json(
            run_dir
            / ".internal"
            / "critic-inputs"
            / str(review["verifier_task_id"])
            / f"{review['candidate_id']}.json",
            {
                "schema_version": "1.0",
                "run_id": run_id,
                "iteration": candidate["iteration"],
                "verifier_task_id": review["verifier_task_id"],
                "verifier_lens": review["verifier_lens"],
                "candidate_id": review["candidate_id"],
                "blind_input_sha256": blind_candidate_fingerprint(candidate),
                "card": blind_candidate_card(candidate),
            },
        )
    iteration_dir = run_dir / ".internal" / "iterations" / f"{iteration:02d}"
    _write_json(iteration_dir / "concept-routes.json", pool)
    _write_json(iteration_dir / "verification.json", verification)


def _collab_spawn_event(task_id: str, role: str) -> dict[str, object]:
    return {
        "type": "item.completed",
        "item": {
            "id": f"spawn-{task_id}",
            "type": "collab_tool_call",
            "tool": "spawn_agent",
            "sender_thread_id": "root-thread",
            "receiver_thread_ids": [task_id],
            "prompt": f"ASOT_IDEA_LOOP_ROLE={role}\nDo the assigned bounded task.",
            "agents_states": {
                task_id: {
                    "status": "running",
                    "message": None,
                }
            },
            "status": "completed",
        },
    }


def _collab_completion_event(task_id: str) -> dict[str, object]:
    return {
        "type": "item.completed",
        "item": {
            "id": f"wait-{task_id}",
            "type": "collab_tool_call",
            "tool": "wait",
            "sender_thread_id": "root-thread",
            "receiver_thread_ids": [task_id],
            "prompt": None,
            "agents_states": {
                task_id: {
                    "status": "completed",
                    "message": f"Completed independent result for {task_id}.",
                }
            },
            "status": "completed",
        },
    }


def _write_codex_event_log(
    run_dir: Path,
    execution_name: str,
    role_by_task: dict[str, str],
    *,
    omit_completion: set[str] | None = None,
) -> None:
    omit_completion = omit_completion or set()
    events: list[dict[str, object]] = []
    for task_id, role in role_by_task.items():
        events.append(_collab_spawn_event(task_id, role))
        if task_id not in omit_completion:
            events.append(_collab_completion_event(task_id))
    path = run_dir / ".internal" / "executions" / execution_name / "codex-events.jsonl"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "".join(json.dumps(event, sort_keys=True) + "\n" for event in events),
        encoding="utf-8",
    )


def _executable_run(
    tmp_path: Path,
    *,
    name: str,
) -> tuple[Path, Path, IdeaLoopConfig]:
    repo_root = tmp_path / "repo"
    for relative in TEST_CORE_EVIDENCE_PATHS:
        path = repo_root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(f"test evidence for {relative}\n", encoding="utf-8")
    config = IdeaLoopConfig(max_iterations=3, candidate_budget=6)
    run_dir = prepare_run(
        repo_root,
        config=config,
        run_dir=repo_root / "output" / "idea-loops" / "2026-07-25" / name,
    )
    return repo_root, run_dir, config


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
            "iteration": 1,
            "final_candidate_id": "idea-01",
        }
    )
    _write_json(state_path, state)

    selected = _candidate("idea-01", "maker-task-a")
    rejected = _candidate("idea-02", "maker-task-b")
    rejected["title"] = "Internal rejected route"
    pool = {
        "schema_version": "1.0",
        "run_id": state["run_id"],
        "candidates": [selected, rejected],
    }
    verification = {
        "schema_version": "1.0",
        "run_id": state["run_id"],
        "reviews": [
            _review(selected, "critic-task-a"),
            _review(selected, "critic-task-b"),
            _review(rejected, "critic-task-a"),
            _review(rejected, "critic-task-b"),
        ],
        "selector": {
            "selector_agent": "asot_idea_verifier",
            "selector_task_id": "selector-task-c",
            "candidate_id": "idea-01",
            "candidate_sha256": candidate_fingerprint(selected),
            "critic_task_ids": ["critic-task-a", "critic-task-b"],
            "verdict": "PASS",
            "reasons": [
                "Both independent reviews pass and the route remains the strongest."
            ],
        },
    }
    _write_json(run_dir / "concept-routes.json", pool)
    _write_json(run_dir / "verification.json", verification)
    _write_iteration_snapshot(
        run_dir,
        iteration=1,
        pool=pool,
        verification=verification,
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
    _write_json(
        run_dir / "source-memory-brief.json",
        _source_brief(state["run_id"]),
    )
    _write_json(
        run_dir / "concept-debate.json",
        {
            "schema_version": "1.0",
            "run_id": state["run_id"],
            "blind_reviews": [
                {
                    "candidate_id": "idea-01",
                    "blind_input_sha256": blind_candidate_fingerprint(selected),
                    "critic_task_ids": ["critic-task-a", "critic-task-b"],
                    "objections": [],
                }
            ],
        },
    )
    _write_json(
        run_dir / "concept-repairs.json",
        {"schema_version": "1.0", "run_id": state["run_id"], "repairs": []},
    )
    _write_json(
        run_dir / "taste-gate.json",
        {
            "schema_version": "1.0",
            "run_id": state["run_id"],
            "records": [
                {
                    "candidate_id": "idea-01",
                    "verifier_task_ids": ["critic-task-a", "critic-task-b"],
                    "verdict": "PASS_NO_CAP",
                    "reasons": ["The paperwork turn is specific, stageable, and ownable."],
                }
            ],
            "selected_candidate_id": "idea-01",
        },
    )
    (run_dir / "creator-brief.md").write_text(
        "# The Emergency Contact Upgrade\n\n"
        "selected candidate: idea-01\n\n"
        "This is a generic relationship hypothesis, not a claimed lived fact.\n\n"
        "## Concrete moment\n\n"
        "A form pauses at the emergency-contact field.\n\n"
        "## Why a cold viewer recognizes it\n\n"
        "Many couples become each other's default person before a ceremony.\n\n"
        "## Format and visible proof\n\n"
        "Carousel: the same name quietly accumulates across ordinary forms.\n\n"
        "## One-person send reason\n\n"
        "You became my person like this too.\n\n"
        "## Evidence and uncertainties\n\n"
        "Grounded in the preference ledger; performance remains unproven.\n\n"
        "## Decision needed\n\n"
        "Approve, reject, or repair this concept. It is a current best bet, "
        "not a performance guarantee.\n",
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
    assert any(
        "does not inspect Codex execution provenance" in warning
        and "does not cryptographically attest agent execution" in warning
        for warning in report.warnings
    )


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


def test_rejected_route_maker_cannot_reappear_as_selected_route_critic(
    tmp_path: Path,
) -> None:
    run_dir, _, _ = _successful_run(tmp_path)
    routes_path = run_dir / "concept-routes.json"
    routes = json.loads(routes_path.read_text(encoding="utf-8"))
    routes["candidates"][1]["maker_task_id"] = "critic-task-a"
    _write_json(routes_path, routes)

    report = validate_run(run_dir)

    assert report.valid is False
    assert any("overlaps a maker task" in error for error in report.errors)


def test_success_requires_two_distinct_maker_tasks(tmp_path: Path) -> None:
    run_dir, _, _ = _successful_run(tmp_path)
    routes_path = run_dir / "concept-routes.json"
    routes = json.loads(routes_path.read_text(encoding="utf-8"))
    routes["candidates"][1]["maker_task_id"] = "maker-task-a"
    _write_json(routes_path, routes)

    report = validate_run(run_dir)

    assert report.valid is False
    assert any("requires two distinct maker task IDs" in error for error in report.errors)


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


def test_candidate_cannot_cite_evidence_outside_the_manifest(tmp_path: Path) -> None:
    run_dir, _, _ = _successful_run(tmp_path)
    routes_path = run_dir / "concept-routes.json"
    routes = json.loads(routes_path.read_text(encoding="utf-8"))
    routes["candidates"][0]["evidence_paths"] = ["memory/semantic/not-captured.md"]
    _write_json(routes_path, routes)

    report = validate_run(run_dir)

    assert report.valid is False
    assert any("evidence path is absent from manifest" in error for error in report.errors)


def test_nonterminal_run_can_resume_without_losing_history(tmp_path: Path) -> None:
    run_dir = prepare_run(
        ROOT,
        config=IdeaLoopConfig(),
        run_dir=tmp_path / "resumable",
    )

    state = resume_run(run_dir)

    assert state.status == "RUNNING"
    assert state.history[-1]["event"] == "run_resumed"


def test_active_execution_lease_blocks_resume(tmp_path: Path) -> None:
    run_dir = prepare_run(
        ROOT,
        config=IdeaLoopConfig(),
        run_dir=tmp_path / "leased",
    )
    _write_json(
        run_dir / ".internal" / "execution-lease.json",
        {"lease_id": "already-running"},
    )

    with pytest.raises(ValueError, match="active execution lease"):
        resume_run(run_dir)


def test_live_execution_rejects_arbitrary_repo_or_external_directories(
    tmp_path: Path,
) -> None:
    run_dir = prepare_run(
        ROOT,
        config=IdeaLoopConfig(),
        run_dir=tmp_path / "unsafe-live-run",
    )
    called = False

    def fake_run(*_args: object, **_kwargs: object) -> subprocess.CompletedProcess[str]:
        nonlocal called
        called = True
        return subprocess.CompletedProcess([], 0, "", "")

    returncode, report = execute_loop(
        ROOT,
        run_dir,
        config=IdeaLoopConfig(),
        run_command=fake_run,
    )

    assert returncode == 2
    assert report.status == "EXECUTION_FAILED"
    assert called is False
    assert "output/idea-loops" in report.errors[0]


def test_live_execution_rejects_symlinked_output_root(tmp_path: Path) -> None:
    fake_root = tmp_path / "repo"
    external = tmp_path / "external"
    (fake_root / "output").mkdir(parents=True)
    external.mkdir()
    (fake_root / "output/idea-loops").symlink_to(external, target_is_directory=True)

    error = idea_loop.execution_location_error(
        fake_root,
        fake_root / "output/idea-loops/2026-07-25/run",
    )

    assert error is not None
    assert "symlink" in error


@pytest.mark.parametrize("mutation", ["repo_root", "evidence_hash"])
def test_execute_loop_rejects_evidence_manifest_mutation_after_controller_capture(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    mutation: str,
) -> None:
    repo_root, run_dir, config = _executable_run(
        tmp_path,
        name=f"manifest-{mutation}",
    )
    manifest_path = run_dir / ".internal" / "evidence-manifest.json"

    def fake_run(*_args: object, **_kwargs: object) -> subprocess.CompletedProcess[str]:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        if mutation == "repo_root":
            manifest["repo_root"] = str(repo_root / "redirected")
        else:
            manifest["core"][0]["sha256"] = "0" * 64
        _write_json(manifest_path, manifest)
        return subprocess.CompletedProcess([], 0, "", "")

    monkeypatch.setattr(
        "pipeline.agentic.instagram_idea_loop.shutil.which",
        lambda _command: "/usr/bin/codex",
    )
    returncode, report = execute_loop(
        repo_root,
        run_dir,
        config=config,
        run_command=fake_run,
    )

    assert returncode == 2
    assert report.status == "INVALID_OUTPUT"
    assert report.valid is False
    assert any("pre-execution snapshot" in error for error in report.errors)
    if mutation == "repo_root":
        assert any("repo_root changed" in error for error in report.errors)


def test_execute_loop_rejects_and_restores_mutated_run_identity_and_budgets(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    repo_root, run_dir, config = _executable_run(tmp_path, name="state-integrity")
    state_path = run_dir / ".internal" / "loop-state.json"
    initial = json.loads(state_path.read_text(encoding="utf-8"))

    def fake_run(*_args: object, **_kwargs: object) -> subprocess.CompletedProcess[str]:
        state = json.loads(state_path.read_text(encoding="utf-8"))
        state.update(
            {
                "run_id": "forged-run",
                "max_iterations": 4,
                "candidate_budget": 8,
            }
        )
        _write_json(state_path, state)
        return subprocess.CompletedProcess([], 0, "", "")

    monkeypatch.setattr(
        "pipeline.agentic.instagram_idea_loop.shutil.which",
        lambda _command: "/usr/bin/codex",
    )
    returncode, report = execute_loop(
        repo_root,
        run_dir,
        config=config,
        run_command=fake_run,
    )

    assert returncode == 2
    assert report.status == "INVALID_OUTPUT"
    assert report.valid is False
    for field in ("run_id", "max_iterations", "candidate_budget"):
        assert any(field in error for error in report.errors)

    persisted = json.loads(state_path.read_text(encoding="utf-8"))
    assert persisted["status"] == "INVALID_OUTPUT"
    assert persisted["run_id"] == initial["run_id"]
    assert persisted["max_iterations"] == initial["max_iterations"]
    assert persisted["candidate_budget"] == initial["candidate_budget"]


def test_codex_child_is_confined_to_the_run_directory(tmp_path: Path) -> None:
    run_dir = tmp_path / "run"
    command = build_codex_command(
        codex_path="codex",
        working_dir=run_dir,
        live_search=False,
    )

    assert command[command.index("-C") + 1] == str(run_dir)
    assert "-s" not in command
    assert "-o" not in command
    assert 'web_search="disabled"' in command
    assert "allow_login_shell=false" in command
    assert 'shell_environment_policy.inherit="none"' in command
    config = tomllib.loads((ROOT / ".codex/config.toml").read_text(encoding="utf-8"))
    assert config["sandbox_mode"] == "workspace-write"
    assert config["sandbox_workspace_write"] == {
        "writable_roots": [],
        "network_access": False,
        "exclude_tmpdir_env_var": True,
        "exclude_slash_tmp": True,
    }


@pytest.mark.parametrize(
    ("validated_status", "validated_ok", "expected_returncode"),
    [
        ("READY_FOR_CONCEPT_LOCK", True, 0),
        ("NO_GO", True, 3),
        ("INVALID_OUTPUT", False, 2),
    ],
)
def test_live_controller_maps_outcomes_and_cleans_lease(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    validated_status: str,
    validated_ok: bool,
    expected_returncode: int,
) -> None:
    fake_root = tmp_path / "repo"
    run_dir = fake_root / "output" / "idea-loops" / "2026-07-25" / "controller"
    prepared = prepare_run(
        fake_root,
        config=IdeaLoopConfig(),
        run_dir=run_dir,
    )
    monkeypatch.setattr(idea_loop.shutil, "which", lambda _name: "/usr/bin/codex")
    monkeypatch.setattr(
        idea_loop,
        "validate_run",
        lambda _run_dir, **_kwargs: idea_loop.ValidationReport(
            run_dir=str(prepared),
            status=validated_status,
            valid=validated_ok,
            errors=() if validated_ok else ("contract failed",),
        ),
    )
    observed: dict[str, object] = {}

    def fake_run(
        command: list[str], **kwargs: object
    ) -> subprocess.CompletedProcess[str]:
        observed["command"] = command
        observed["cwd"] = kwargs["cwd"]
        state_path = prepared / ".internal" / "loop-state.json"
        state = json.loads(state_path.read_text(encoding="utf-8"))
        state["status"] = validated_status
        state["stage"] = "CONCEPT_LOCK" if validated_ok else "VALIDATE"
        _write_json(state_path, state)
        return subprocess.CompletedProcess(
            command,
            0,
            '{"type":"turn.completed"}\n',
            "",
        )

    returncode, report = execute_loop(
        fake_root,
        prepared,
        config=IdeaLoopConfig(),
        run_command=fake_run,
    )

    assert returncode == expected_returncode
    assert report.status == validated_status
    assert observed["cwd"] == prepared
    assert (prepared / ".internal/executions/run-01/codex-events.jsonl").is_file()
    assert not list((fake_root / "output/idea-loops/.leases").glob("*.json"))
    assert idea_loop.controller_finalization_valid(prepared) is validated_ok


def test_nonzero_codex_exit_is_normalized_and_logged(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fake_root = tmp_path / "repo"
    run_dir = fake_root / "output" / "idea-loops" / "2026-07-25" / "nonzero"
    prepared = prepare_run(
        fake_root,
        config=IdeaLoopConfig(),
        run_dir=run_dir,
    )
    monkeypatch.setattr(idea_loop.shutil, "which", lambda _name: "/usr/bin/codex")

    def fake_run(
        command: list[str], **_kwargs: object
    ) -> subprocess.CompletedProcess[str]:
        return subprocess.CompletedProcess(command, 17, "", "child failed")

    returncode, report = execute_loop(
        fake_root,
        prepared,
        config=IdeaLoopConfig(),
        run_command=fake_run,
    )

    assert returncode == 2
    assert report.status == "EXECUTION_FAILED"
    assert "status 17" in report.errors[0]
    assert (
        prepared / ".internal/executions/run-01/codex-stderr.log"
    ).read_text(encoding="utf-8") == "child failed"


def test_parent_rejects_child_symlink_before_post_child_writes(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fake_root = tmp_path / "repo"
    run_dir = fake_root / "output" / "idea-loops" / "2026-07-25" / "symlink"
    prepared = prepare_run(
        fake_root,
        config=IdeaLoopConfig(),
        run_dir=run_dir,
    )
    sensitive = tmp_path / "sensitive.txt"
    sensitive.write_text("keep me\n", encoding="utf-8")
    monkeypatch.setattr(idea_loop.shutil, "which", lambda _name: "/usr/bin/codex")

    def fake_run(
        command: list[str], **_kwargs: object
    ) -> subprocess.CompletedProcess[str]:
        (prepared / "concept-routes.json").symlink_to(sensitive)
        return subprocess.CompletedProcess(command, 0, "events", "")

    returncode, report = execute_loop(
        fake_root,
        prepared,
        config=IdeaLoopConfig(),
        run_command=fake_run,
    )

    assert returncode == 2
    assert any("forbidden symlink" in error for error in report.errors)
    assert sensitive.read_text(encoding="utf-8") == "keep me\n"
    assert not (prepared / ".internal/executions/run-01/codex-events.jsonl").exists()


def test_failure_signature_ignores_task_churn_but_tracks_gate_changes() -> None:
    candidate = _candidate("idea-a", "maker-a")
    review_a = _review(candidate, "critic-a")
    review_a["scores"]["story_selling"] = 20
    review_a["verdict"] = "REPAIR"
    review_b = json.loads(json.dumps(review_a))
    review_b["candidate_id"] = "idea-b"
    review_b["verifier_task_id"] = "critic-b"
    review_b["candidate_sha256"] = "f" * 64

    assert failure_signature({"reviews": [review_a]}) == failure_signature(
        {"reviews": [review_b]}
    )

    review_b["taste_gate"] = "STOP"
    assert failure_signature({"reviews": [review_a]}) != failure_signature(
        {"reviews": [review_b]}
    )


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
            "iteration": 1,
            "stop_reason": "No fresh route cleared the taste gate within budget.",
            "final_candidate_id": None,
        }
    )
    pool, verification = _no_go_artifacts(state["run_id"])
    state["history"].append(
        {
            "event": "verification_failed",
            "failure_signature": failure_signature(verification),
        }
    )
    _write_json(state_path, state)
    _write_json(run_dir / "source-memory-brief.json", _source_brief(state["run_id"]))
    _write_json(run_dir / "concept-routes.json", pool)
    _write_json(run_dir / "verification.json", verification)
    _write_iteration_snapshot(
        run_dir,
        iteration=1,
        pool=pool,
        verification=verification,
    )
    (run_dir / "creator-brief.md").write_text(
        "No route cleared every gate; no candidate is being promoted.\n",
        encoding="utf-8",
    )

    report = validate_run(run_dir)

    assert report.valid is True
    assert report.status == "NO_GO"


def test_empty_honest_stop_artifacts_are_rejected(tmp_path: Path) -> None:
    run_dir = prepare_run(
        ROOT,
        config=IdeaLoopConfig(),
        run_dir=tmp_path / "empty-no-go",
    )
    state_path = run_dir / ".internal/loop-state.json"
    state = json.loads(state_path.read_text(encoding="utf-8"))
    state.update(
        {
            "status": "NO_GO",
            "stage": "SELECT",
            "iteration": 1,
            "stop_reason": "Claimed failure without saved proof.",
            "final_candidate_id": None,
        }
    )
    _write_json(state_path, state)
    for name in ("source-memory-brief.json", "concept-routes.json", "verification.json"):
        _write_json(run_dir / name, {"schema_version": "1.0", "run_id": state["run_id"]})
    (run_dir / "creator-brief.md").write_text("No route promoted.\n", encoding="utf-8")

    report = validate_run(run_dir)

    assert report.valid is False
    assert any("Field required" in error for error in report.errors)


def test_human_required_early_stop_has_structured_evidence(tmp_path: Path) -> None:
    run_dir = prepare_run(
        ROOT,
        config=IdeaLoopConfig(),
        run_dir=tmp_path / "human-required",
    )
    state_path = run_dir / ".internal/loop-state.json"
    state = json.loads(state_path.read_text(encoding="utf-8"))
    reason = "The seed depends on a lived detail that cannot be inferred safely."
    state.update(
        {
            "status": "HUMAN_REQUIRED",
            "stage": "DISCOVER",
            "iteration": 0,
            "stop_reason": reason,
            "final_candidate_id": None,
        }
    )
    _write_json(state_path, state)
    _write_json(run_dir / "source-memory-brief.json", _source_brief(state["run_id"]))
    _write_json(
        run_dir / "stop-evidence.json",
        {
            "schema_version": "1.0",
            "run_id": state["run_id"],
            "status": "HUMAN_REQUIRED",
            "reason": reason,
            "evidence_paths": ["memory/semantic/carousel-idea-preferences.md"],
            "missing_or_ambiguous_inputs": ["Which real couple incident is safe to use?"],
        },
    )
    (run_dir / "creator-brief.md").write_text(
        "One lived detail is needed before responsible ideation can continue.\n",
        encoding="utf-8",
    )

    report = validate_run(run_dir)

    assert report.valid is True
    assert report.status == "HUMAN_REQUIRED"


def test_stagnated_stop_requires_two_identical_normalized_signatures(tmp_path: Path) -> None:
    run_dir = prepare_run(
        ROOT,
        config=IdeaLoopConfig(),
        run_dir=tmp_path / "stagnated",
    )
    state_path = run_dir / ".internal" / "loop-state.json"
    state = json.loads(state_path.read_text(encoding="utf-8"))
    state.update(
        {
            "status": "STAGNATED",
            "stage": "VERIFY",
            "iteration": 2,
            "stop_reason": "The same verifier failure categories repeated twice.",
            "final_candidate_id": None,
        }
    )
    pool_one, verification_one = _no_go_artifacts(
        state["run_id"],
        iteration=1,
        repairable=True,
    )
    pool_two, verification_two = _no_go_artifacts(
        state["run_id"],
        iteration=2,
        repairable=True,
    )
    signature_one = failure_signature(verification_one)
    signature_two = failure_signature(verification_two)
    assert signature_one == signature_two
    state["history"].extend(
        [
            {"event": "verification_failed", "failure_signature": signature_one},
            {"event": "verification_failed", "failure_signature": signature_two},
        ]
    )
    _write_json(state_path, state)
    _write_json(run_dir / "source-memory-brief.json", _source_brief(state["run_id"]))
    _write_json(run_dir / "concept-routes.json", pool_two)
    _write_json(run_dir / "verification.json", verification_two)
    _write_iteration_snapshot(
        run_dir,
        iteration=1,
        pool=pool_one,
        verification=verification_one,
    )
    _write_iteration_snapshot(
        run_dir,
        iteration=2,
        pool=pool_two,
        verification=verification_two,
    )
    (run_dir / "creator-brief.md").write_text("The loop stagnated without a winner.\n")

    assert validate_run(run_dir).valid is True

    state["history"][-1]["failure_signature"] = "b" * 64
    _write_json(state_path, state)
    report = validate_run(run_dir)
    assert report.valid is False
    assert any(
        "history must contain the computed failure signature" in error
        for error in report.errors
    )


def test_cli_dry_run_prepares_durable_prompt_without_invoking_codex(tmp_path: Path) -> None:
    fake_root = tmp_path / "repo"
    run_dir = fake_root / "output" / "idea-loops" / "2026-07-25" / "dry-run"
    driver = """
import sys
from pathlib import Path
import scripts.instagram_idea_loop as cli

cli.ROOT = Path(sys.argv[1])
raise SystemExit(cli.main([
    "run",
    "--dry-run",
    "--run-dir",
    sys.argv[2],
]))
"""
    completed = subprocess.run(
        [
            sys.executable,
            "-c",
            driver,
            str(fake_root),
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

    rejected = subprocess.run(
        [
            sys.executable,
            "scripts/instagram_idea_loop.py",
            "run",
            "--dry-run",
            "--run-dir",
            str(tmp_path / "outside-boundary"),
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
        timeout=30,
    )
    assert rejected.returncode == 2
    assert "output/idea-loops" in rejected.stderr


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
