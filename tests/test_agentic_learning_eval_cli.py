import json
import subprocess
import sys
from pathlib import Path

from pipeline.agentic.audit_log import append_audit_event, snapshot_file
from pipeline.agentic.learning_loop import capture_learning_event, create_learning_proposal
from pipeline.agentic.skill_eval import evaluate_learning_proposal


def test_audit_log_appends_jsonl_and_snapshots_file(tmp_path: Path):
    root = tmp_path
    target = root / "config" / "skill.md"
    target.parent.mkdir(parents=True)
    target.write_text("before", encoding="utf-8")

    snapshot = snapshot_file(root, "config/skill.md")
    event_path = append_audit_event(
        root,
        actor="codex",
        action="snapshot",
        target_path="config/skill.md",
        rationale="test snapshot",
        evidence_paths=[snapshot.as_posix()],
    )

    assert snapshot.exists()
    assert event_path.exists()
    assert json.loads(event_path.read_text(encoding="utf-8").splitlines()[0])["action"] == "snapshot"


def test_learning_loop_creates_draft_proposal_without_auto_apply(tmp_path: Path):
    root = tmp_path
    target = root / "config" / "skills" / "alpha.md"
    target.parent.mkdir(parents=True)
    target.write_text("# Alpha\n\nconfidence: 0.8\n", encoding="utf-8")

    event = capture_learning_event(
        root,
        source="creator_feedback",
        summary="Storyboard first, copy second.",
        evidence_paths=["memory/working.md"],
    )
    proposal_path = create_learning_proposal(
        root,
        source_event_id=event.event_id,
        target_path="config/skills/alpha.md",
        proposed_action="modify",
        rationale="Persist storyboard-first rule.",
        proposed_content="# Alpha\n\nconfidence: 0.9\n\nStoryboard first.\n",
        required_validators=["skill_eval"],
    )
    proposal = json.loads(proposal_path.read_text(encoding="utf-8"))

    assert proposal["status"] == "draft"
    assert proposal["auto_apply"] is False
    assert proposal["target_path"] == "config/skills/alpha.md"


def test_agentic_os_cli_applies_valid_learning_proposal_with_approval(tmp_path: Path):
    root = tmp_path
    target = root / "config" / "skills" / "alpha.md"
    target.parent.mkdir(parents=True)
    target.write_text("# Alpha\n\nconfidence: 0.8\n", encoding="utf-8")
    event = capture_learning_event(
        root,
        source="creator_feedback",
        summary="Storyboard first, copy second.",
        evidence_paths=["memory/working.md"],
    )
    proposal_path = create_learning_proposal(
        root,
        source_event_id=event.event_id,
        target_path="config/skills/alpha.md",
        proposed_action="modify",
        rationale="Persist storyboard-first rule.",
        proposed_content="# Alpha\n\nconfidence: 0.9\n\nStoryboard first.\n",
        required_validators=["skill_eval"],
    )

    repo_root = Path(__file__).resolve().parents[1]
    result = subprocess.run(
        [
            sys.executable,
            "scripts/agentic_os.py",
            "--workspace-root",
            str(root),
            "apply-learning",
            str(proposal_path),
            "--approved-by",
            "creator",
        ],
        cwd=repo_root,
        text=True,
        capture_output=True,
        check=False,
        timeout=30,
    )

    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    proposal = json.loads(proposal_path.read_text(encoding="utf-8"))

    assert payload["status"] == "applied"
    assert payload["target_path"] == "config/skills/alpha.md"
    assert "Storyboard first." in target.read_text(encoding="utf-8")
    assert proposal["status"] == "applied"
    assert proposal["approved_by"] == "creator"
    assert (root / payload["audit_path"]).exists()
    assert (root / payload["snapshot_path"]).exists()


def test_agentic_os_cli_refuses_to_reapply_learning_proposal(tmp_path: Path):
    root = tmp_path
    target = root / "config" / "skills" / "alpha.md"
    target.parent.mkdir(parents=True)
    target.write_text("# Alpha\n\nconfidence: 0.8\n", encoding="utf-8")
    event = capture_learning_event(
        root,
        source="creator_feedback",
        summary="Storyboard first, copy second.",
        evidence_paths=["memory/working.md"],
    )
    proposal_path = create_learning_proposal(
        root,
        source_event_id=event.event_id,
        target_path="config/skills/alpha.md",
        proposed_action="modify",
        rationale="Persist storyboard-first rule.",
        proposed_content="# Alpha\n\nconfidence: 0.9\n\nStoryboard first.\n",
        required_validators=["skill_eval"],
    )

    repo_root = Path(__file__).resolve().parents[1]
    first = subprocess.run(
        [
            sys.executable,
            "scripts/agentic_os.py",
            "--workspace-root",
            str(root),
            "apply-learning",
            str(proposal_path),
            "--approved-by",
            "creator",
        ],
        cwd=repo_root,
        text=True,
        capture_output=True,
        check=False,
        timeout=30,
    )
    second = subprocess.run(
        [
            sys.executable,
            "scripts/agentic_os.py",
            "--workspace-root",
            str(root),
            "apply-learning",
            str(proposal_path),
            "--approved-by",
            "creator",
        ],
        cwd=repo_root,
        text=True,
        capture_output=True,
        check=False,
        timeout=30,
    )

    assert first.returncode == 0, first.stderr
    assert second.returncode == 2
    assert "proposal status must be draft or approved" in second.stderr


def test_agentic_os_cli_evaluate_learning_includes_review_context(tmp_path: Path):
    root = tmp_path
    target = root / "config" / "skills" / "alpha.md"
    target.parent.mkdir(parents=True)
    target.write_text("# Alpha\n\nconfidence: 0.8\n", encoding="utf-8")
    event = capture_learning_event(
        root,
        source="creator_feedback",
        summary="Storyboard first, copy second.",
        evidence_paths=["memory/working.md"],
    )
    proposal_path = create_learning_proposal(
        root,
        source_event_id=event.event_id,
        target_path="config/skills/alpha.md",
        proposed_action="modify",
        rationale="Persist storyboard-first rule.",
        proposed_content="# Alpha\n\nconfidence: 0.9\n\nStoryboard first.\n",
        required_validators=["skill_eval"],
    )

    repo_root = Path(__file__).resolve().parents[1]
    result = subprocess.run(
        [
            sys.executable,
            "scripts/agentic_os.py",
            "--workspace-root",
            str(root),
            "evaluate-learning",
            str(proposal_path),
        ],
        cwd=repo_root,
        text=True,
        capture_output=True,
        check=False,
        timeout=30,
    )

    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)

    assert payload["status"] == "PASS"
    assert payload["proposal_status"] == "draft"
    assert payload["target_path"] == "config/skills/alpha.md"
    assert payload["proposed_content_path"].startswith("memory/agentic/learning-proposals/content/")
    assert payload["next_action"] == "review_then_apply_learning"
    assert "apply-learning" in payload["apply_command"]


def test_agentic_os_cli_refuses_invalid_learning_proposal_application(tmp_path: Path):
    root = tmp_path
    proposal_path = root / "proposal.json"
    proposal_path.write_text(
        json.dumps(
            {
                "proposal_id": "proposal-invalid",
                "source_event_id": "event-1",
                "target_path": "config/skills/missing.md",
                "proposed_action": "modify",
                "rationale": "Broken proposal.",
                "before_hash": "a",
                "after_hash": "b",
                "required_validators": ["skill_eval"],
                "status": "draft",
                "auto_apply": False,
            }
        ),
        encoding="utf-8",
    )

    repo_root = Path(__file__).resolve().parents[1]
    result = subprocess.run(
        [
            sys.executable,
            "scripts/agentic_os.py",
            "--workspace-root",
            str(root),
            "apply-learning",
            str(proposal_path),
            "--approved-by",
            "creator",
        ],
        cwd=repo_root,
        text=True,
        capture_output=True,
        check=False,
        timeout=30,
    )

    assert result.returncode == 2
    assert "skill_eval failed" in result.stderr
    assert json.loads(proposal_path.read_text(encoding="utf-8"))["status"] == "draft"


def test_skill_eval_blocks_auto_apply_and_missing_target(tmp_path: Path):
    root = tmp_path
    proposal = {
        "proposal_id": "p1",
        "source_event_id": "e1",
        "target_path": "config/skills/missing.md",
        "proposed_action": "modify",
        "rationale": "test",
        "before_hash": "a",
        "after_hash": "b",
        "required_validators": ["skill_eval"],
        "status": "draft",
        "auto_apply": True,
    }
    proposal_path = root / "proposal.json"
    proposal_path.write_text(json.dumps(proposal), encoding="utf-8")

    result = evaluate_learning_proposal(root, proposal_path)

    assert result.status == "FAIL"
    assert "auto_apply" in " ".join(result.issues)
    assert "missing" in " ".join(result.issues).lower()


def test_agentic_os_cli_context_and_search(tmp_path: Path):
    root = tmp_path
    (root / "config").mkdir()
    (root / "memory" / "semantic").mkdir(parents=True)
    (root / "memory").mkdir(exist_ok=True)
    (root / "config" / "voice.md").write_text("Warm voice.", encoding="utf-8")
    (root / "memory" / "working.md").write_text("Working memory.", encoding="utf-8")
    (root / "memory" / "semantic" / "prefs.md").write_text(
        "# Prefs\n\nconfidence: 0.9\nsources:\n- test\n\nfact: visual-first comedy.\n",
        encoding="utf-8",
    )
    (root / "config" / "agentic_context_manifest.json").write_text(
        """{
          "schema_version": "1.0",
          "default_profile": "a-story-of-two",
          "profiles": {
            "a-story-of-two": {
              "budget_tokens": 400,
              "sections": [
                {"id": "voice", "path": "config/voice.md", "kind": "brand_voice", "required": true},
                {"id": "working", "path": "memory/working.md", "kind": "working_memory", "required": true}
              ]
            }
          }
        }""",
        encoding="utf-8",
    )

    repo_root = Path(__file__).resolve().parents[1]
    context = subprocess.run(
        [sys.executable, "scripts/agentic_os.py", "--workspace-root", str(root), "context"],
        cwd=repo_root,
        text=True,
        capture_output=True,
        check=False,
        timeout=30,
    )
    search = subprocess.run(
        [sys.executable, "scripts/agentic_os.py", "--workspace-root", str(root), "search", "visual comedy"],
        cwd=repo_root,
        text=True,
        capture_output=True,
        check=False,
        timeout=30,
    )

    assert context.returncode == 0, context.stderr
    assert '"profile": "a-story-of-two"' in context.stdout
    assert search.returncode == 0, search.stderr
    assert "memory/semantic/prefs.md" in search.stdout


def test_agentic_os_cli_reports_learning_debt(tmp_path: Path):
    root = tmp_path
    event_dir = root / "memory" / "agentic" / "learning-events"
    proposal_dir = root / "memory" / "agentic" / "learning-proposals"
    event_dir.mkdir(parents=True)
    proposal_dir.mkdir(parents=True)
    (event_dir / "event-unproposed.json").write_text(
        json.dumps(
            {
                "event_id": "event-unproposed",
                "source": "jam: unproposed lesson",
                "summary": "Object-first hook failed and needs a durable anti-pattern.",
                "created_at": "2026-07-04T11:00:00+00:00",
            }
        ),
        encoding="utf-8",
    )
    (event_dir / "event-draft.json").write_text(
        json.dumps(
            {
                "event_id": "event-draft",
                "source": "jam: draft lesson",
                "summary": "A draft proposal exists for this lesson.",
                "created_at": "2026-07-04T11:05:00+00:00",
            }
        ),
        encoding="utf-8",
    )
    (proposal_dir / "proposal-draft.json").write_text(
        json.dumps(
            {
                "proposal_id": "proposal-draft",
                "source_event_id": "event-draft",
                "target_path": "memory/semantic/carousel-idea-preferences.md",
                "rationale": "Persist the draft lesson.",
                "status": "draft",
                "created_at": "2026-07-04T11:10:00+00:00",
            }
        ),
        encoding="utf-8",
    )

    repo_root = Path(__file__).resolve().parents[1]
    result = subprocess.run(
        [sys.executable, "scripts/agentic_os.py", "--workspace-root", str(root), "learning-debt"],
        cwd=repo_root,
        text=True,
        capture_output=True,
        check=False,
        timeout=30,
    )

    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    lines = "\n".join(record["line"] for record in payload["records"])

    assert payload["debt_count"] == 2
    assert "needs proposal event-unproposed" in lines
    assert "review draft proposal proposal-draft" in lines
    assert "skill_eval: FAIL" in lines


def test_learning_debt_includes_supported_hypotheses_without_learning_event(tmp_path: Path):
    root = tmp_path
    hypothesis_dir = root / "memory" / "agentic" / "hypotheses"
    event_dir = root / "memory" / "agentic" / "learning-events"
    hypothesis_dir.mkdir(parents=True)
    event_dir.mkdir(parents=True)
    hypothesis_path = hypothesis_dir / "hypothesis-supported.json"
    hypothesis_path.write_text(
        json.dumps(
            {
                "hypothesis_id": "hypothesis-supported",
                "source": "jam gate verification",
                "hypothesis": "The jam gate blocks abstract seeds.",
                "status": "resolved",
                "outcome": "supported",
                "result_summary": "Weak seeds are blocked before packaging.",
                "created_at": "2026-07-11T10:00:00+00:00",
                "resolved_at": "2026-07-11T10:05:00+00:00",
            }
        ),
        encoding="utf-8",
    )

    repo_root = Path(__file__).resolve().parents[1]
    first = subprocess.run(
        [sys.executable, "scripts/agentic_os.py", "--workspace-root", str(root), "learning-debt"],
        cwd=repo_root,
        text=True,
        capture_output=True,
        check=False,
        timeout=30,
    )

    assert first.returncode == 0, first.stderr
    first_payload = json.loads(first.stdout)
    first_lines = "\n".join(record["line"] for record in first_payload["records"])

    assert first_payload["debt_count"] == 1
    assert "capture learning from supported hypothesis hypothesis-supported" in first_lines

    (event_dir / "event-from-hypothesis.json").write_text(
        json.dumps(
            {
                "event_id": "event-from-hypothesis",
                "source": "jam gate verification",
                "summary": "Jam gate should keep blocking abstract seeds before packaging.",
                "evidence_paths": ["memory/agentic/hypotheses/hypothesis-supported.json"],
                "created_at": "2026-07-11T10:10:00+00:00",
            }
        ),
        encoding="utf-8",
    )
    second = subprocess.run(
        [sys.executable, "scripts/agentic_os.py", "--workspace-root", str(root), "learning-debt"],
        cwd=repo_root,
        text=True,
        capture_output=True,
        check=False,
        timeout=30,
    )

    assert second.returncode == 0, second.stderr
    second_payload = json.loads(second.stdout)
    second_lines = "\n".join(record["line"] for record in second_payload["records"])

    assert second_payload["debt_count"] == 1
    assert "capture learning from supported hypothesis hypothesis-supported" not in second_lines
    assert "needs proposal event-from-hypothesis" in second_lines


def test_agentic_os_health_reports_research_loop_counts(tmp_path: Path):
    from tests.helpers.agentic_workspace import write_minimal_agentic_workspace

    root = tmp_path
    write_minimal_agentic_workspace(root)
    hypothesis_dir = root / "memory" / "agentic" / "hypotheses"
    event_dir = root / "memory" / "agentic" / "learning-events"
    hypothesis_dir.mkdir(parents=True)
    event_dir.mkdir(parents=True)
    (hypothesis_dir / "hypothesis-open.json").write_text(
        json.dumps(
            {
                "hypothesis_id": "hypothesis-open",
                "source": "jam: blanket border",
                "hypothesis": "Blanket border can become a sendable ritual.",
                "success_signal": "Creator chooses it over generic care concepts.",
                "falsifier": "It reads as private trivia.",
                "status": "open",
                "created_at": "2026-07-11T10:00:00+00:00",
            }
        ),
        encoding="utf-8",
    )
    (event_dir / "event-unproposed.json").write_text(
        json.dumps(
            {
                "event_id": "event-unproposed",
                "source": "jam: blanket border",
                "summary": "Blanket border worked and needs a durable proposal.",
                "created_at": "2026-07-11T10:05:00+00:00",
            }
        ),
        encoding="utf-8",
    )

    repo_root = Path(__file__).resolve().parents[1]
    result = subprocess.run(
        [sys.executable, "scripts/agentic_os.py", "--workspace-root", str(root), "health"],
        cwd=repo_root,
        text=True,
        capture_output=True,
        check=False,
        timeout=30,
    )

    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)

    assert payload["open_hypotheses"] == 1
    assert payload["learning_debt_count"] == 1
    assert payload["learning_debt_by_kind"] == {"event": 1}


def test_agentic_os_cli_captures_and_lists_hypotheses(tmp_path: Path):
    root = tmp_path
    repo_root = Path(__file__).resolve().parents[1]
    capture = subprocess.run(
        [
            sys.executable,
            "scripts/agentic_os.py",
            "--workspace-root",
            str(root),
            "capture-hypothesis",
            "--source",
            "jam: blanket border moved again",
            "--hypothesis",
            "Blanket border can become a sendable ritual if it proves shared negotiation.",
            "--success-signal",
            "Creator chooses it over generic care concepts.",
            "--falsifier",
            "It reads as cute private trivia without a reader mirror.",
        ],
        cwd=repo_root,
        text=True,
        capture_output=True,
        check=False,
        timeout=30,
    )

    assert capture.returncode == 0, capture.stderr
    captured = json.loads(capture.stdout)
    assert captured["status"] == "open"
    assert captured["source"] == "jam: blanket border moved again"
    assert captured["hypothesis_path"].startswith("memory/agentic/hypotheses/")

    listed = subprocess.run(
        [sys.executable, "scripts/agentic_os.py", "--workspace-root", str(root), "hypotheses"],
        cwd=repo_root,
        text=True,
        capture_output=True,
        check=False,
        timeout=30,
    )

    assert listed.returncode == 0, listed.stderr
    payload = json.loads(listed.stdout)
    assert payload["open_count"] == 1
    assert payload["records"][0]["hypothesis_id"] == captured["hypothesis_id"]
    assert "sendable ritual" in payload["records"][0]["hypothesis"]


def test_agentic_os_cli_resolves_hypotheses_with_outcomes(tmp_path: Path):
    root = tmp_path
    repo_root = Path(__file__).resolve().parents[1]
    capture = subprocess.run(
        [
            sys.executable,
            "scripts/agentic_os.py",
            "--workspace-root",
            str(root),
            "capture-hypothesis",
            "--source",
            "jam: blanket border moved again",
            "--hypothesis",
            "Blanket border can become a sendable ritual if it proves shared negotiation.",
            "--success-signal",
            "Creator chooses it over generic care concepts.",
            "--falsifier",
            "It reads as cute private trivia without a reader mirror.",
        ],
        cwd=repo_root,
        text=True,
        capture_output=True,
        check=False,
        timeout=30,
    )
    captured = json.loads(capture.stdout)

    resolve = subprocess.run(
        [
            sys.executable,
            "scripts/agentic_os.py",
            "--workspace-root",
            str(root),
            "resolve-hypothesis",
            captured["hypothesis_id"],
            "--outcome",
            "supported",
            "--result-summary",
            "Creator picked the route because it felt like a shared ritual, not private trivia.",
            "--evidence",
            "output/carousels/blanket-border/review.json",
        ],
        cwd=repo_root,
        text=True,
        capture_output=True,
        check=False,
        timeout=30,
    )

    assert resolve.returncode == 0, resolve.stderr
    resolved = json.loads(resolve.stdout)
    assert resolved["status"] == "resolved"
    assert resolved["outcome"] == "supported"
    assert "shared ritual" in resolved["result_summary"]
    assert "output/carousels/blanket-border/review.json" in resolved["evidence_paths"]

    open_list = subprocess.run(
        [sys.executable, "scripts/agentic_os.py", "--workspace-root", str(root), "hypotheses"],
        cwd=repo_root,
        text=True,
        capture_output=True,
        check=False,
        timeout=30,
    )
    resolved_list = subprocess.run(
        [
            sys.executable,
            "scripts/agentic_os.py",
            "--workspace-root",
            str(root),
            "hypotheses",
            "--status",
            "resolved",
        ],
        cwd=repo_root,
        text=True,
        capture_output=True,
        check=False,
        timeout=30,
    )

    assert json.loads(open_list.stdout)["open_count"] == 0
    resolved_payload = json.loads(resolved_list.stdout)
    assert resolved_payload["records"][0]["hypothesis_id"] == captured["hypothesis_id"]
    assert resolved_payload["records"][0]["outcome"] == "supported"
