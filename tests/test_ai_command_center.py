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
        "scripts/instagram_idea_loop.py",
        "scripts/jam_today.py",
        "scripts/run_content_health.py",
    ):
        assert (WORKSPACE / relative).exists(), f"{relative} should exist"


def test_makefile_exposes_primary_targets():
    text = (WORKSPACE / "Makefile").read_text(encoding="utf-8")
    for target in (
        "brief:",
        "health wiki-health:",
        "idea-loop:",
        "jam:",
        "prepost:",
        "carousel:",
        "article:",
        "publish:",
        "publish-dry-run:",
        "test:",
    ):
        assert target in text


def test_make_carousel_runs_only_the_production_command():
    text = (WORKSPACE / "Makefile").read_text(encoding="utf-8")
    carousel_target = text.split("\narticle:", 1)[0].split("\ncarousel:", 1)[1]

    assert carousel_target.count("scripts/carousel.py create") == 1
    assert "pytest" not in carousel_target
    assert "scripts/agentic_os.py health" not in carousel_target
    assert "wiki" not in carousel_target.lower()


def test_command_center_scripts_have_help():
    for script in (
        "daily_creator_brief.py",
        "instagram_idea_loop.py",
        "jam_today.py",
        "run_content_health.py",
    ):
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
    assert "free creative pass" in result.stdout.lower()
    assert "story-only input creates a truthful draft" in result.stdout.lower()
    assert "scripts/carousel.py create" in result.stdout
    assert "before writing public copy" not in result.stdout.lower()


def test_jam_today_omits_default_research_and_learning_ceremony():
    result = subprocess.run(
        [sys.executable, str(WORKSPACE / "scripts" / "jam_today.py"), "--moment", "blanket border moved again"],
        cwd=WORKSPACE,
        capture_output=True,
        text=True,
        check=False,
        timeout=30,
    )

    assert result.returncode == 0
    assert "Research Partner Lens" not in result.stdout
    assert "Research Challenge Gate" not in result.stdout
    assert "capture-hypothesis" not in result.stdout
    assert "capture-learning" not in result.stdout


def test_jam_today_keeps_abstract_seed_as_truthful_draft_command():
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

    assert result.returncode == 0
    assert "## Creative Pass" in result.stdout
    assert "scripts/carousel.py create" in result.stdout
    assert "--prepare-proof" not in result.stdout
    assert "Research Challenge Gate" not in result.stdout


def test_jam_today_routes_concrete_couple_moment_without_gate_ceremony():
    result = subprocess.run(
        [sys.executable, str(WORKSPACE / "scripts" / "jam_today.py"), "--moment", "blanket border moved again"],
        cwd=WORKSPACE,
        capture_output=True,
        text=True,
        check=False,
        timeout=30,
    )

    assert result.returncode == 0
    assert "## Carousel Command" in result.stdout
    assert "scripts/carousel.py create" in result.stdout
    assert "Research Challenge Gate" not in result.stdout


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
