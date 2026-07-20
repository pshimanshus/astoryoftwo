import json
import subprocess
import sys
from pathlib import Path


WORKSPACE = Path(__file__).resolve().parents[1]


def test_ai_command_center_files_exist():
    for relative in (
        "Makefile",
        "docs/ai-ops-playbook.md",
        "docs/superpowers/specs/2026-05-28-ai-command-center-design.md",
        "scripts/daily_creator_brief.py",
        "scripts/jam_today.py",
        "scripts/run_content_health.py",
    ):
        assert (WORKSPACE / relative).exists(), f"{relative} should exist"


def test_makefile_exposes_primary_targets():
    text = (WORKSPACE / "Makefile").read_text(encoding="utf-8")
    for target in (
        "brief:",
        "health wiki-health:",
        "jam:",
        "prepost:",
        "carousel:",
        "article:",
        "publish:",
        "publish-dry-run:",
        "test:",
    ):
        assert target in text


def test_make_carousel_runs_existing_preflight_before_generation():
    text = (WORKSPACE / "Makefile").read_text(encoding="utf-8")
    carousel_target = text.split("\narticle:", 1)[0].split("\ncarousel:", 1)[1]
    create_index = carousel_target.index("scripts/create_illustration_carousel.py")
    for required in (
        "tests/test_agentic_docs_contract.py",
        "tests/test_instruction_surface_contract.py",
        "tests/test_codex_project_surfaces.py",
        "tests/test_creator_workflow_contract.py",
        "tests/test_checks_prompt_constraints.py",
        "tests/test_checks_image_size.py",
        "tests/test_carousel_state_contract.py",
        "tests/test_carousel_workflow_doctor.py",
        "tests/test_carousel_doctor_cli.py",
        "scripts/agentic_os.py health",
    ):
        assert required in carousel_target
        assert carousel_target.index(required) < create_index


def test_command_center_scripts_have_help():
    for script in ("daily_creator_brief.py", "jam_today.py", "run_content_health.py"):
        result = subprocess.run(
            [sys.executable, str(WORKSPACE / "scripts" / script), "--help"],
            cwd=WORKSPACE,
            capture_output=True,
            text=True,
            check=False,
            timeout=30,
        )
        assert result.returncode == 0
        assert "usage:" in result.stdout.lower()


def test_jam_today_prints_free_creative_pass_before_gates():
    result = subprocess.run(
        [sys.executable, str(WORKSPACE / "scripts" / "jam_today.py"), "--moment", "haan haan listening trap"],
        cwd=WORKSPACE,
        capture_output=True,
        text=True,
        check=False,
        timeout=30,
    )

    assert result.returncode == 0
    assert "free creative pass first" in result.stdout.lower()
    assert "engineering guardrails" in result.stdout.lower()
    assert "before writing public copy" not in result.stdout.lower()


def test_jam_today_prints_research_partner_lens_and_learning_capture():
    result = subprocess.run(
        [sys.executable, str(WORKSPACE / "scripts" / "jam_today.py"), "--moment", "blanket border moved again"],
        cwd=WORKSPACE,
        capture_output=True,
        text=True,
        check=False,
        timeout=30,
    )

    assert result.returncode == 0
    assert "## Research Partner Lens" in result.stdout
    assert "memory/semantic/engineering-workflow-preferences.md" in result.stdout
    assert "hypothesis:" in result.stdout.lower()
    assert "challenge:" in result.stdout.lower()
    assert "durable learning:" in result.stdout.lower()
    assert "scripts/agentic_os.py capture-hypothesis" in result.stdout
    assert "scripts/agentic_os.py capture-learning" in result.stdout


def test_jam_today_challenges_weak_abstract_moments_before_packaging():
    result = subprocess.run(
        [
            sys.executable,
            str(WORKSPACE / "scripts" / "jam_today.py"),
            "--moment",
            "love is important and couples should care more",
        ],
        cwd=WORKSPACE,
        capture_output=True,
        text=True,
        check=False,
        timeout=30,
    )

    assert result.returncode == 2
    assert "## Research Challenge Gate" in result.stdout
    assert "verdict: REWORK" in result.stdout
    assert "missing concrete couple scene" in result.stdout
    assert "missing reader-recognition proof" in result.stdout
    assert "Package Command" not in result.stdout


def test_jam_today_allows_concrete_couple_moments_through_challenge_gate():
    result = subprocess.run(
        [sys.executable, str(WORKSPACE / "scripts" / "jam_today.py"), "--moment", "blanket border moved again"],
        cwd=WORKSPACE,
        capture_output=True,
        text=True,
        check=False,
        timeout=30,
    )

    assert result.returncode == 0
    assert "## Research Challenge Gate" in result.stdout
    assert "verdict: PASS" in result.stdout
    assert "## Package Command" in result.stdout


def test_daily_creator_brief_surfaces_research_partner_lens():
    result = subprocess.run(
        [sys.executable, str(WORKSPACE / "scripts" / "daily_creator_brief.py")],
        cwd=WORKSPACE,
        capture_output=True,
        text=True,
        check=False,
        timeout=30,
    )

    assert result.returncode == 0
    assert "## Research Partner Lens" in result.stdout
    assert "memory/semantic/engineering-workflow-preferences.md" in result.stdout
    assert "hypothesis:" in result.stdout.lower()
    assert "challenge:" in result.stdout.lower()
    assert "durable learning:" in result.stdout.lower()


def test_daily_creator_brief_collects_recent_learning_loop_records(tmp_path: Path):
    from scripts.daily_creator_brief import recent_learning_records

    event_dir = tmp_path / "memory" / "agentic" / "learning-events"
    proposal_dir = tmp_path / "memory" / "agentic" / "learning-proposals"
    event_dir.mkdir(parents=True)
    proposal_dir.mkdir(parents=True)
    (event_dir / "event-1.json").write_text(
        json.dumps(
            {
                "event_id": "event-1",
                "source": "jam: blanket border moved again",
                "summary": "Blanket border worked because it turned a tiny fight into a shared ritual.",
                "evidence_paths": ["output/carousels/blanket-border/review.json"],
                "created_at": "2026-07-04T10:00:00+00:00",
            }
        ),
        encoding="utf-8",
    )
    (proposal_dir / "proposal-1.json").write_text(
        json.dumps(
            {
                "proposal_id": "proposal-1",
                "source_event_id": "event-1",
                "target_path": "memory/semantic/carousel-idea-preferences.md",
                "proposed_action": "modify",
                "rationale": "Persist blanket-border ritual as a repeatable proof pattern.",
                "required_validators": ["skill_eval"],
                "status": "draft",
                "auto_apply": False,
                "created_at": "2026-07-04T10:05:00+00:00",
            }
        ),
        encoding="utf-8",
    )

    records = recent_learning_records(tmp_path, limit=4)
    rendered = "\n".join(record["line"] for record in records)

    assert records[0]["kind"] == "proposal"
    assert "proposal-only draft" in rendered
    assert "blanket border worked" in rendered.lower()
    assert "memory/semantic/carousel-idea-preferences.md" in rendered


def test_daily_creator_brief_surfaces_recent_learning_loop():
    result = subprocess.run(
        [sys.executable, str(WORKSPACE / "scripts" / "daily_creator_brief.py")],
        cwd=WORKSPACE,
        capture_output=True,
        text=True,
        check=False,
        timeout=30,
    )

    assert result.returncode == 0
    assert "## Recent Learning Loop" in result.stdout
    assert "proposal-only" in result.stdout.lower()


def test_daily_creator_brief_collects_learning_debt(tmp_path: Path):
    from scripts.daily_creator_brief import learning_debt_records

    event_dir = tmp_path / "memory" / "agentic" / "learning-events"
    proposal_dir = tmp_path / "memory" / "agentic" / "learning-proposals"
    event_dir.mkdir(parents=True)
    proposal_dir.mkdir(parents=True)
    (event_dir / "event-without-proposal.json").write_text(
        json.dumps(
            {
                "event_id": "event-without-proposal",
                "source": "jam: unproposed lesson",
                "summary": "A direct object-first hook failed and needs a durable anti-pattern.",
                "created_at": "2026-07-04T11:00:00+00:00",
            }
        ),
        encoding="utf-8",
    )
    (event_dir / "event-with-draft-proposal.json").write_text(
        json.dumps(
            {
                "event_id": "event-with-draft-proposal",
                "source": "jam: draft lesson",
                "summary": "A draft proposal already exists for this event.",
                "created_at": "2026-07-04T11:05:00+00:00",
            }
        ),
        encoding="utf-8",
    )
    (proposal_dir / "draft-proposal.json").write_text(
        json.dumps(
            {
                "proposal_id": "draft-proposal",
                "source_event_id": "event-with-draft-proposal",
                "target_path": "memory/semantic/carousel-idea-preferences.md",
                "rationale": "Persist the draft lesson.",
                "status": "draft",
                "created_at": "2026-07-04T11:10:00+00:00",
            }
        ),
        encoding="utf-8",
    )

    debt = learning_debt_records(tmp_path, limit=5)
    rendered = "\n".join(record["line"] for record in debt)

    assert "needs proposal event-without-proposal" in rendered
    assert "review draft proposal draft-proposal" in rendered
    assert "event-with-draft-proposal" not in rendered


def test_daily_creator_brief_surfaces_learning_debt_section():
    result = subprocess.run(
        [sys.executable, str(WORKSPACE / "scripts" / "daily_creator_brief.py")],
        cwd=WORKSPACE,
        capture_output=True,
        text=True,
        check=False,
        timeout=30,
    )

    assert result.returncode == 0
    assert "## Learning Debt" in result.stdout
    debt_text = result.stdout.lower()
    assert (
        "no unresolved learning debt" in debt_text
        or "needs proposal" in debt_text
        or "review draft proposal" in debt_text
        or "apply approved proposal" in debt_text
    )


def test_daily_creator_brief_collects_hypothesis_tracker_records(tmp_path: Path):
    from scripts.daily_creator_brief import hypothesis_brief_records

    hypothesis_dir = tmp_path / "memory" / "agentic" / "hypotheses"
    hypothesis_dir.mkdir(parents=True)
    (hypothesis_dir / "hypothesis-open.json").write_text(
        json.dumps(
            {
                "hypothesis_id": "hypothesis-open",
                "source": "jam: blanket border",
                "hypothesis": "Blanket border can become a sendable ritual.",
                "success_signal": "Creator chooses it over generic care concepts.",
                "falsifier": "It reads as private trivia.",
                "status": "open",
                "created_at": "2026-07-04T12:00:00+00:00",
            }
        ),
        encoding="utf-8",
    )
    (hypothesis_dir / "hypothesis-resolved.json").write_text(
        json.dumps(
            {
                "hypothesis_id": "hypothesis-resolved",
                "source": "jam: plate stack",
                "hypothesis": "Plate stack works as a daily care proof.",
                "success_signal": "Creator approves the scene.",
                "falsifier": "It feels like chore advice.",
                "status": "resolved",
                "outcome": "supported",
                "result_summary": "Creator approved the scene because it felt lived.",
                "created_at": "2026-07-04T11:00:00+00:00",
                "resolved_at": "2026-07-04T12:05:00+00:00",
            }
        ),
        encoding="utf-8",
    )

    records = hypothesis_brief_records(tmp_path, limit=5)
    rendered = "\n".join(record["line"] for record in records)

    assert "open hypothesis-open from jam: blanket border" in rendered
    assert "resolved supported hypothesis-resolved" in rendered
    assert "Creator approved the scene" in rendered


def test_daily_creator_brief_surfaces_hypothesis_tracker():
    result = subprocess.run(
        [sys.executable, str(WORKSPACE / "scripts" / "daily_creator_brief.py")],
        cwd=WORKSPACE,
        capture_output=True,
        text=True,
        check=False,
        timeout=30,
    )

    assert result.returncode == 0
    assert "## Hypothesis Tracker" in result.stdout
    assert "no hypotheses captured yet" in result.stdout.lower() or "hypothesis" in result.stdout.lower()
