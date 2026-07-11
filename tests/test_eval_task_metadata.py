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

    assert 8 <= len(tasks) <= 12
    assert len({task.id for task in tasks}) == len(tasks)
    assert all((task.task_dir / task.prompt).exists() for task in tasks)
    assert all(task.title for task in tasks)
    assert all(task.done_when for task in tasks)
    assert all(task.starting_state for task in tasks)
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
    ):
        assert fragment in source_text

    taxonomy_text = taxonomy.read_text(encoding="utf-8")
    assert "Project Failure Taxonomy" in taxonomy_text
    assert "mechanical contract" in taxonomy_text.lower()
    assert "creative contract" in taxonomy_text.lower()


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
