from pathlib import Path
import json

import pytest

from evals.checkers.task_specific import run_named_checkers
from evals.fixtures import UnsafeFixturePathError, materialize_task_fixture
from evals.schemas import EvalTask, FixtureOverlay, PassCriteria, discover_tasks
from pipeline.agentic.carousel_state import derive_carousel_state
from pipeline.agentic.workflow_doctor import inspect_carousel_package
from scripts.autopublish import SECRET_PATTERNS, find_risky_paths, parse_changed_paths, scan_secret_text


ROOT = Path(__file__).resolve().parents[1]


def _task(task_id: str):
    return next(task for task in discover_tasks(ROOT) if task.id == task_id)


def _synthetic_overlay_task(overlay: FixtureOverlay, task_dir: Path) -> EvalTask:
    return EvalTask(
        schema_version="1.0",
        id="ASTO-999",
        title="Synthetic fixture overlay task",
        category="fixture_security",
        difficulty="easy",
        suites=["smoke"],
        prompt="prompt.md",
        starting_state=["Fixture overlay is unsafe."],
        done_when=["Unsafe overlay is rejected."],
        allowed_paths=["fixtures/**"],
        forbidden_paths=["AGENTS.md", ".env*", "identity_images/**", "output/**/final/**"],
        expected_files_changed=[],
        forbidden_changes=[],
        required_commands=[],
        deterministic_checkers=[],
        rubric_checkers=[],
        pass_criteria=PassCriteria(),
        fixture_overlay=[overlay],
        task_dir=task_dir,
    )


def test_smoke_tasks_have_materialized_fixture_overlays() -> None:
    smoke_tasks = [task for task in discover_tasks(ROOT) if "smoke" in task.suites]

    assert smoke_tasks
    for task in smoke_tasks:
        assert task.fixture_overlay, f"{task.id} needs at least one fixture overlay"
        for fixture in task.fixture_overlay:
            assert (task.task_dir / fixture.source).exists(), (
                f"{task.id} fixture source missing: {fixture.source}"
            )


def test_tracked_eval_fixtures_do_not_contain_live_looking_secrets() -> None:
    fixture_files = [
        path
        for path in (ROOT / "evals" / "tasks").rglob("*")
        if path.is_file() and "/fixtures/" in path.as_posix()
    ]

    assert fixture_files
    for path in fixture_files:
        text = path.read_text(encoding="utf-8", errors="ignore")
        for kind, pattern in SECRET_PATTERNS:
            assert not pattern.search(text), f"{kind} found in {path.relative_to(ROOT)}"


def test_fixture_overlay_rejects_parent_directory_target(tmp_path: Path) -> None:
    task_dir = tmp_path / "task"
    task_dir.mkdir()
    (task_dir / "prompt.md").write_text("Prompt", encoding="utf-8")
    (task_dir / "fixture.txt").write_text("unsafe", encoding="utf-8")
    task = _synthetic_overlay_task(
        FixtureOverlay(source="fixture.txt", target="../escape.txt"),
        task_dir,
    )

    with pytest.raises(UnsafeFixturePathError):
        materialize_task_fixture(task, tmp_path / "workspace")

    assert not (tmp_path / "escape.txt").exists()


def test_fixture_overlay_rejects_absolute_source(tmp_path: Path) -> None:
    task_dir = tmp_path / "task"
    task_dir.mkdir()
    (task_dir / "prompt.md").write_text("Prompt", encoding="utf-8")
    source = tmp_path / "outside.txt"
    source.write_text("unsafe", encoding="utf-8")
    task = _synthetic_overlay_task(
        FixtureOverlay(source=str(source), target="safe.txt"),
        task_dir,
    )

    with pytest.raises(UnsafeFixturePathError):
        materialize_task_fixture(task, tmp_path / "workspace")


def test_brandmark_fixture_triggers_named_checker(tmp_path: Path) -> None:
    task = _task("ASTO-001-brandmark-drift")
    materialize_task_fixture(task, tmp_path)

    results = run_named_checkers(task, tmp_path, ["brandmark_top_right_rule"])

    assert [result.status for result in results] == ["FAIL"]
    assert results[0].code == "brandmark_top_right_rule"
    assert "bottom-right" in "\n".join(results[0].evidence)


def test_textless_prompt_fixture_triggers_carousel_doctor(tmp_path: Path) -> None:
    task = _task("ASTO-003-textless-prompt")
    materialize_task_fixture(task, tmp_path)

    package = tmp_path / "output" / "carousels" / "fixtures" / "textless-prompt"
    report = inspect_carousel_package(package)
    codes = {issue.code for issue in report.issues}

    assert report.blocked is True
    assert "active_textless_prompt" in codes

    results = run_named_checkers(task, tmp_path, ["carousel_doctor_fixture"])
    assert [result.status for result in results] == ["PASS"]


def test_fake_publishable_fixture_derives_blocked_state(tmp_path: Path) -> None:
    task = _task("ASTO-004-fake-publishable-package")
    materialize_task_fixture(task, tmp_path)

    package = tmp_path / "output" / "carousels" / "fixtures" / "fake-publishable"
    report = inspect_carousel_package(package)
    state = derive_carousel_state(package)

    assert report.blocked is True
    assert state.blocked is True
    assert state.publishable is False

    results = run_named_checkers(task, tmp_path, ["carousel_doctor_fixture"])
    assert [result.status for result in results] == ["PASS"]


def test_autopublish_fixture_contains_blocked_risky_paths_and_secret(tmp_path: Path) -> None:
    task = _task("ASTO-008-autopublish-risky-paths")
    materialize_task_fixture(task, tmp_path)
    (tmp_path / ".env.local").write_text(
        "OPENAI_API_KEY=" + "sk-" + ("a" * 24) + "\n",
        encoding="utf-8",
    )

    status_text = (tmp_path / "fixtures" / "git-status.txt").read_text(encoding="utf-8")
    paths = parse_changed_paths(status_text)
    risky = {block.path for block in find_risky_paths(paths)}
    secrets = scan_secret_text(tmp_path, paths)

    assert ".env.local" in risky
    assert "identity_images/aachu-reference.png" in risky
    assert "output/carousels/fixtures/demo/final/slide-01.png" in risky
    assert any(finding.kind == "openai_key" for finding in secrets)


def test_autopublish_fixture_named_checker_blocks_risky_paths_without_tracked_secret(tmp_path: Path) -> None:
    task = _task("ASTO-008-autopublish-risky-paths")
    materialize_task_fixture(task, tmp_path)

    results = run_named_checkers(task, tmp_path, ["autopublish_safety_fixture"])

    assert [result.status for result in results] == ["PASS", "PASS"]


def test_stale_artifact_fixture_triggers_named_checker(tmp_path: Path) -> None:
    task = _task("ASTO-013-stale-artifact-after-correction")
    materialize_task_fixture(task, tmp_path)

    results = run_named_checkers(task, tmp_path, ["stale_artifact_fixture"])

    assert [result.status for result in results] == ["PASS"]
    assert "seeti count" in "\n".join(results[0].evidence)


def test_identity_stop_gate_fixture_triggers_named_checker(tmp_path: Path) -> None:
    task = _task("ASTO-014-identity-eval-stop-gate")
    materialize_task_fixture(task, tmp_path)

    results = run_named_checkers(task, tmp_path, ["identity_stop_gate_fixture"])

    assert [result.status for result in results] == ["PASS"]
    assert "identity_references_missing" in results[0].evidence


def test_score_rejection_fixture_fails_until_rejected_scores_are_stopped(tmp_path: Path) -> None:
    task = _task("ASTO-015-score-inflation-after-rejection")
    materialize_task_fixture(task, tmp_path)

    results = run_named_checkers(task, tmp_path, ["score_rejection_fixture"])

    assert [result.status for result in results] == ["FAIL"]
    assert "Seeti Count Marriage" in "\n".join(results[0].evidence)


def test_score_rejection_fixture_passes_when_rejected_scores_are_invalidated(tmp_path: Path) -> None:
    task = _task("ASTO-015-score-inflation-after-rejection")
    materialize_task_fixture(task, tmp_path)
    selection_path = (
        tmp_path
        / "output"
        / "concepts"
        / "fixtures"
        / "score-inflation-after-rejection"
        / "concept-selection.json"
    )
    payload = json.loads(selection_path.read_text(encoding="utf-8"))
    rejected = payload["concepts"][0]
    rejected["recommendation"] = "STOP"
    rejected["calibration_use"] = "score_invalidated_do_not_represent"
    rejected["repair_route"] = "rebuild from fresh creator-specific incident"
    selection_path.write_text(json.dumps(payload), encoding="utf-8")

    results = run_named_checkers(task, tmp_path, ["score_rejection_fixture"])

    assert [result.status for result in results] == ["PASS"]


def test_home_cinematic_fixture_triggers_named_checker(tmp_path: Path) -> None:
    task = _task("ASTO-016-home-cinematic-visual-evidence")
    materialize_task_fixture(task, tmp_path)

    results = run_named_checkers(task, tmp_path, ["home_cinematic_fixture"])

    assert [result.status for result in results] == ["PASS"]
    evidence = " ".join(results[0].evidence)
    assert "camera_position" in evidence
    assert "motivated_light" in evidence
    assert "story_evidence" in evidence
    assert "fingerprint" not in evidence
    assert "review_provenance" not in evidence


def test_public_name_boundary_fixture_fails_until_public_names_are_removed(tmp_path: Path) -> None:
    task = _task("ASTO-017-public-name-leakage")
    materialize_task_fixture(task, tmp_path)

    results = run_named_checkers(task, tmp_path, ["public_name_boundary_fixture"])

    assert [result.status for result in results] == ["FAIL"]
    assert any("Aachu" in item for item in results[0].evidence)


def test_public_name_boundary_fixture_passes_when_public_names_are_removed(tmp_path: Path) -> None:
    task = _task("ASTO-017-public-name-leakage")
    materialize_task_fixture(task, tmp_path)
    copy_path = tmp_path / "output" / "evals" / "ASTO-017" / "public-copy.json"
    payload = json.loads(copy_path.read_text(encoding="utf-8"))
    payload["public_slide_copy"] = [
        "She kept saying the charger was hers.",
        "He kept pretending he had never seen it.",
        "Somehow they both knew where it belonged.",
    ]
    copy_path.write_text(json.dumps(payload), encoding="utf-8")
    brief_path = tmp_path / "output" / "evals" / "ASTO-017" / "creator-brief.md"
    brief_path.write_text(
        "Public copy uses she/he/they language while internal prompts keep identity anchors.",
        encoding="utf-8",
    )

    results = run_named_checkers(task, tmp_path, ["public_name_boundary_fixture"])

    assert [result.status for result in results] == ["PASS"]


def test_small_brief_seed_fixture_fails_until_creator_brief_is_alive(tmp_path: Path) -> None:
    task = _task("ASTO-011-small-brief-no-framework-dump")
    materialize_task_fixture(task, tmp_path)

    results = run_named_checkers(
        task,
        tmp_path,
        ["creator_visible_copy", "small_brief_seed_fixture"],
    )

    assert [result.status for result in results] == ["FAIL", "FAIL"]
    assert "Story-Selling" in "\n".join(results[0].evidence)
    assert "exact seed phrase" in "\n".join(results[1].evidence)


def test_small_brief_seed_fixture_passes_after_seed_and_scene_repair(tmp_path: Path) -> None:
    task = _task("ASTO-011-small-brief-no-framework-dump")
    materialize_task_fixture(task, tmp_path)
    brief_path = tmp_path / "output" / "evals" / "ASTO-011" / "creator-brief.md"
    brief_path.write_text(
        "\n".join(
            [
                "# Creator Brief",
                "",
                "Seed to preserve: she says \"main kar lungi,\" but the love is that he knows when not to believe her.",
                "",
                "Strongest format: carousel, because the joke needs repeated small refusals before the final turn.",
                "",
                "Scene: she reaches for the high kitchen jar and says she can do it; he stays quiet, slides the stool near her, and keeps holding the cup she forgot.",
                "",
                "Reaction: he does not announce help, he just already knows the moment when her independence is mostly theatre.",
                "",
                "Payoff: the final slide reveals she was smiling before she asked, because both of them knew the ritual.",
            ]
        ),
        encoding="utf-8",
    )

    results = run_named_checkers(
        task,
        tmp_path,
        ["creator_visible_copy", "small_brief_seed_fixture"],
    )

    assert [result.status for result in results] == ["PASS", "PASS"]


def test_copy_visual_logic_fixture_triggers_named_checker(tmp_path: Path) -> None:
    task = _task("ASTO-018-copy-visual-logic-contradiction")
    materialize_task_fixture(task, tmp_path)

    results = run_named_checkers(task, tmp_path, ["copy_visual_logic_fixture"])

    assert [result.status for result in results] == ["PASS"]
    evidence = " ".join(results[0].evidence)
    assert "copy_visual_contradictions" in evidence
    assert "fingerprint" not in evidence
    assert "review_provenance" not in evidence


@pytest.mark.parametrize(
    ("task_id", "checker", "fixture_path"),
    [
        (
            "ASTO-012-visual-variety-shot-ladder",
            "visual_variety_shot_ladder_fixture",
            "output/evals/ASTO-012/visual-plan-quality.json",
        ),
        (
            "ASTO-016-home-cinematic-visual-evidence",
            "home_cinematic_fixture",
            "output/evals/ASTO-016/home-visual-plan.json",
        ),
        (
            "ASTO-018-copy-visual-logic-contradiction",
            "copy_visual_logic_fixture",
            "output/evals/ASTO-018/visual-qa.json",
        ),
    ],
)
def test_visual_story_eval_does_not_pass_on_valid_lifecycle_envelope_alone(
    tmp_path: Path,
    task_id: str,
    checker: str,
    fixture_path: str,
) -> None:
    task = _task(task_id)
    materialize_task_fixture(task, tmp_path)
    path = tmp_path / fixture_path
    payload = json.loads(path.read_text(encoding="utf-8"))
    payload.pop("defect")
    path.write_text(json.dumps(payload), encoding="utf-8")

    results = run_named_checkers(task, tmp_path, [checker])

    assert [result.status for result in results] == ["FAIL"]


def test_older_eval_fixtures_have_named_checker_coverage(tmp_path: Path) -> None:
    expectations = {
        "ASTO-002-format-snapback": ("format_snapback_fixture", "FAIL"),
        "ASTO-005-working-memory-pointer": ("working_memory_pointer_fixture", "FAIL"),
        "ASTO-006-creator-skill-routing": ("creator_skill_routing_fixture", "FAIL"),
        "ASTO-007-context-rule-truncation": ("context_rule_truncation_fixture", "PASS"),
        "ASTO-009-article-story-selling-gate": ("article_story_selling_fixture", "FAIL"),
        "ASTO-010-prepost-layer-e": ("prepost_layer_e_fixture", "FAIL"),
        "ASTO-011-small-brief-no-framework-dump": ("small_brief_seed_fixture", "FAIL"),
        "ASTO-012-visual-variety-shot-ladder": ("visual_variety_shot_ladder_fixture", "PASS"),
    }

    for index, (task_id, (checker, status)) in enumerate(expectations.items(), start=1):
        workspace = tmp_path / str(index)
        task = _task(task_id)
        materialize_task_fixture(task, workspace)

        results = run_named_checkers(task, workspace, [checker])

        assert [result.status for result in results] == [status], task_id
        if task_id == "ASTO-012-visual-variety-shot-ladder":
            evidence = " ".join(results[0].evidence)
            assert "repeats one narrative job" in evidence
            assert "repeats one shot size" in evidence
            assert "fingerprint" not in evidence
            assert "review_provenance" not in evidence
