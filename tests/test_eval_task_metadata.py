import json
import re
from fnmatch import fnmatch
from pathlib import Path

from evals.schemas import discover_tasks, load_registry, validate_task_suite


ROOT = Path(__file__).resolve().parents[1]


def test_eval_registry_declares_starter_suites() -> None:
    registry = load_registry(ROOT)

    assert registry.schema_version == "1.0"
    assert "smoke" in registry.suites
    assert "contract" in registry.suites
    assert "creative" in registry.suites
    assert len(registry.tasks) >= 8


def test_starter_tasks_are_issue_like_and_cover_project_contract() -> None:
    tasks = discover_tasks(ROOT)

    assert 12 <= len(tasks) <= 24
    assert len({task.id for task in tasks}) == len(tasks)
    assert all((task.task_dir / task.prompt).exists() for task in tasks)
    assert all(task.title for task in tasks)
    assert all(task.done_when for task in tasks)
    assert all(task.starting_state for task in tasks)
    assert all(task.fail_to_pass for task in tasks)
    assert all(task.pass_to_pass for task in tasks)
    assert all(task.pass_criteria.critical_failures_allowed == 0 for task in tasks)

    categories = {task.category for task in tasks}
    assert {
        "instruction_drift",
        "carousel_package",
        "closeout_safety",
        "memory_wiki",
        "agentic_os",
        "creative_contract",
    }.issubset(categories)

    task_ids = {task.id for task in tasks}
    expected_new_tasks = (
        "ASTO-013-stale-artifact-after-correction",
        "ASTO-014-identity-eval-stop-gate",
        "ASTO-015-score-inflation-after-rejection",
        "ASTO-016-home-cinematic-visual-evidence",
        "ASTO-017-public-name-leakage",
        "ASTO-018-copy-visual-logic-contradiction",
    )
    for expected in (
        *expected_new_tasks,
        "ASTO-019-duplicate-background-characters",
        "ASTO-020-hand-object-integrity",
        "ASTO-021-whole-person-spatial-integrity",
        "ASTO-022-hil-stage-checkpoints",
    ):
        assert expected in task_ids

    task_by_id = {task.id: task for task in tasks}
    for expected in expected_new_tasks:
        task = task_by_id[expected]
        assert task.fixture_overlay, f"{expected} must remain fixture-backed"
        assert any(checker != "diff_guard" for checker in task.deterministic_checkers), (
            f"{expected} needs a task-specific deterministic checker"
        )

    for task in tasks:
        assert task.fixture_overlay, f"{task.id} must remain fixture-backed"
        assert any(checker != "diff_guard" for checker in task.deterministic_checkers), (
            f"{task.id} needs a task-specific deterministic checker"
        )
        assert task.fixture_contract.mode in {"solution", "regression"}
        if task.fixture_contract.mode == "solution":
            assert task.fixture_contract.expected_outcome == "unresolved"
            assert task.fixture_contract.benchmark_setup == "fixture_overlay"
            assert any(
                any(fnmatch(overlay.target, pattern) for pattern in task.allowed_paths)
                for overlay in task.fixture_overlay
            ), f"{task.id}: solution fixture has no solver-editable repair target"
        else:
            assert task.fixture_contract.expected_outcome == "guarded"
            assert (
                task.fixture_contract.benchmark_setup
                == "hidden_code_mutation_required"
            )
        assert not any(path.startswith("evals/") for path in task.allowed_paths)
        assert not any(
            path.startswith("evals/") for path in task.expected_files_changed
        )


def test_task_metadata_protects_root_contract_and_sensitive_outputs() -> None:
    tasks = discover_tasks(ROOT)

    for task in tasks:
        forbidden = set(task.forbidden_paths)
        assert "AGENTS.md" in forbidden or task.category == "instruction_surface"
        assert any(pattern.startswith(".env") for pattern in forbidden)
        assert any("identity" in pattern for pattern in forbidden)
        assert any("output/**/final" in pattern for pattern in forbidden)


def test_task_suite_validation_reports_no_issues() -> None:
    report = validate_task_suite(ROOT)

    assert report["status"] == "PASS", report
    assert report["task_count"] >= 8
    assert not report["issues"]


def test_each_task_has_deep_evaluator_spec_not_one_line_prompt() -> None:
    tasks = discover_tasks(ROOT)
    required_headings = [
        "## Why This Task Exists",
        "## Starting Fixture",
        "## Failure Modes",
        "## Checker Design",
        "## Anti-Gaming",
        "## Severity Model",
    ]

    for task in tasks:
        spec_path = task.task_dir / "deep-spec.md"
        assert spec_path.exists(), f"{task.id} is missing deep-spec.md"
        text = spec_path.read_text(encoding="utf-8")
        words = text.split()
        assert len(words) >= 220, f"{task.id} deep spec is too thin"
        for heading in required_headings:
            assert heading in text, f"{task.id} missing {heading}"
        assert "hidden variant" in text.lower(), f"{task.id} must define hidden variants"
        assert "pass-to-pass" in text.lower(), f"{task.id} must define pass-to-pass coverage"
        assert "fail-to-pass" in text.lower(), f"{task.id} must define fail-to-pass coverage"


def test_each_agent_prompt_is_a_real_issue_not_a_label() -> None:
    tasks = discover_tasks(ROOT)
    required_headings = [
        "## Context",
        "## Task",
        "## Acceptance Criteria",
        "## Constraints",
    ]

    for task in tasks:
        prompt_path = task.task_dir / task.prompt
        text = prompt_path.read_text(encoding="utf-8")
        assert len(text.split()) >= 90, f"{task.id} prompt is too thin"
        for heading in required_headings:
            assert heading in text, f"{task.id} prompt missing {heading}"
        assert "Do not edit `AGENTS.md`" in text or "Do not edit AGENTS.md" in text


def test_eval_research_assets_are_present_and_source_grounded() -> None:
    sources = ROOT / "evals" / "research" / "sources.json"
    taxonomy = ROOT / "evals" / "research" / "failure-taxonomy.md"
    rubric = ROOT / "evals" / "rubrics" / "creative-contract.md"

    assert sources.exists()
    assert taxonomy.exists()
    assert rubric.exists()

    source_text = sources.read_text(encoding="utf-8")
    for fragment in (
        "SWE-bench",
        "SWE-bench Verified",
        "SWE-bench-Live",
        "OpenAI evaluation best practices",
        "OpenAI coding-eval data quality audit",
    ):
        assert fragment in source_text

    taxonomy_text = taxonomy.read_text(encoding="utf-8")
    assert "Project Failure Taxonomy" in taxonomy_text
    assert "Evidence Ledger" in taxonomy_text
    assert "mechanical contract" in taxonomy_text.lower()
    assert "creative contract" in taxonomy_text.lower()
    assert "Score inflation after rejection" in taxonomy_text
    assert "Home-cinematic" in taxonomy_text
    assert "duplicate background" in taxonomy_text.lower()
    assert "hand ownership" in taxonomy_text.lower()
    assert "ASTO-020" in taxonomy_text
    assert "whole-person spatial" in taxonomy_text.lower()
    assert "ASTO-021" in taxonomy_text
    for fragment in (
        "Seeti Count Marriage",
        "The Almosts Were Practicing",
        "stale artifact carryover",
        "home-like visuals",
        "copy-visual logic",
    ):
        assert fragment in taxonomy_text


def test_eval_source_links_are_unique_https_urls_with_design_impact() -> None:
    payload = json.loads(
        (ROOT / "evals" / "research" / "sources.json").read_text(encoding="utf-8")
    )
    records = payload["sources"]
    urls = [record["url"] for record in records]

    assert len(urls) == len(set(urls))
    for record in records:
        assert record["url"].startswith("https://")
        assert record["claim"].strip()
        assert record["use_in_this_repo"].strip()
        assert 0 <= record["confidence"] <= 1


def test_required_test_command_paths_exist() -> None:
    for task in discover_tasks(ROOT):
        for command in task.required_commands:
            for argument in command:
                if argument.startswith("tests/") and argument.endswith(".py"):
                    assert (ROOT / argument).exists(), f"{task.id}: missing {argument}"


def test_eval_review_local_markdown_links_resolve() -> None:
    review = ROOT / "docs" / "evals" / "2026-07-21-eval-suite-alignment-review.md"
    text = review.read_text(encoding="utf-8")
    targets = re.findall(r"\[[^]]+\]\(([^)]+)\)", text)

    assert targets
    for target in targets:
        assert not target.startswith(("http://", "https://"))
        resolved = (review.parent / target).resolve()
        assert resolved.exists(), f"broken local link: {target}"


def test_validate_task_suite_fails_when_deep_spec_is_missing(tmp_path: Path) -> None:
    task_dir = tmp_path / "evals" / "tasks" / "ASTO-X"
    task_dir.mkdir(parents=True)
    (tmp_path / "evals").mkdir(exist_ok=True)
    (tmp_path / "evals" / "registry.json").write_text(
        """
        {
          "schema_version": "1.0",
          "suites": {"smoke": {"description": "Smoke"}},
          "tasks": ["ASTO-X"]
        }
        """,
        encoding="utf-8",
    )
    (task_dir / "prompt.md").write_text("# Prompt\n", encoding="utf-8")
    (task_dir / "task.json").write_text(
        """
        {
          "schema_version": "1.0",
          "id": "ASTO-X",
          "title": "Thin task",
          "category": "instruction_drift",
          "difficulty": "easy",
          "suites": ["smoke"],
          "prompt": "prompt.md",
          "starting_state": ["drift"],
          "done_when": ["fixed"],
          "allowed_paths": ["config/**"],
          "forbidden_paths": ["AGENTS.md", ".env*", "identity_images/**", "output/**/final/**"],
          "expected_files_changed": [],
          "forbidden_changes": [],
          "required_commands": [],
          "deterministic_checkers": ["diff_guard"],
          "rubric_checkers": [],
          "pass_criteria": {"critical_failures_allowed": 0, "major_failures_allowed": 0}
        }
        """,
        encoding="utf-8",
    )

    report = validate_task_suite(tmp_path)

    assert report["status"] == "FAIL"
    assert any("deep-spec.md" in issue for issue in report["issues"])
