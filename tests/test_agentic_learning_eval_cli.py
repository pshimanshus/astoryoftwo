import json
import subprocess
import sys
from pathlib import Path

import pytest

from pipeline.agentic.audit_log import append_audit_event, snapshot_file
from pipeline.agentic.learning_loop import (
    CREATOR_FEEDBACK_PENDING_LINKAGE,
    apply_learning_proposal,
    capture_learning_event,
    create_learning_proposal,
    learning_debt_records,
)
from pipeline.agentic.skill_eval import evaluate_learning_proposal
from pipeline.agentic.validator_registry import run_required_validators


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
        source="code_review",
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
    run_required_validators(root, proposal_path)
    proposal = json.loads(proposal_path.read_text(encoding="utf-8"))

    assert proposal["status"] == "draft"
    assert proposal["auto_apply"] is False
    assert proposal["target_path"] == "config/skills/alpha.md"


def test_learning_event_supports_idempotent_caller_id_and_feedback_metadata(tmp_path: Path):
    values = {
        "event_id": "feedback-package-quiet-morning-v2",
        "source": "creator_feedback",
        "summary": "The visual route repeated a previously rejected caretaker beat.",
        "evidence_paths": ["output/carousels/quiet-morning/creator-correction.json"],
        "user_instruction_exact": "Do not make Zuv the handler again.",
        "diagnosis": "The scene repair restored the default caretaker pattern.",
        "scope": "package",
        "package_path": "output/carousels/quiet-morning",
        "feedback_status": "captured",
        "resolution_evidence": [],
        "eval_disposition": "background",
        "feedback_metadata": {"revision": 2, "slide_ids": [4, 5]},
    }

    first = capture_learning_event(tmp_path, **values)
    second = capture_learning_event(tmp_path, **values)
    event_files = list((tmp_path / "memory" / "agentic" / "learning-events").glob("*.json"))
    stored = json.loads(event_files[0].read_text(encoding="utf-8"))

    assert first == second
    assert len(event_files) == 1
    assert stored["event_id"] == values["event_id"]
    assert stored["user_instruction_exact"] == values["user_instruction_exact"]
    assert stored["eval_disposition"] == "background"
    assert stored["feedback_metadata"] == {"revision": 2, "slide_ids": [4, 5]}


def test_learning_event_rejects_conflicting_retry_without_overwrite(tmp_path: Path):
    event_id = "feedback-package-conflict-v1"
    original = capture_learning_event(
        tmp_path,
        event_id=event_id,
        source="creator_feedback",
        summary="Keep this exact correction.",
    )
    path = tmp_path / "memory" / "agentic" / "learning-events" / f"{event_id}.json"
    before = path.read_bytes()

    with pytest.raises(ValueError, match="different content"):
        capture_learning_event(
            tmp_path,
            event_id=event_id,
            source="creator_feedback",
            summary="A conflicting correction.",
        )

    assert path.read_bytes() == before
    assert json.loads(path.read_text(encoding="utf-8"))["summary"] == original.summary


def test_unlinked_creator_feedback_defaults_to_package_local_linkage_debt(tmp_path: Path):
    exact_words = "The carousel isn't following the story structure I want."
    event = capture_learning_event(
        tmp_path,
        source="creator_feedback",
        summary="Repair this carousel's story structure.",
        user_instruction_exact=exact_words,
    )

    stored_path = (
        tmp_path
        / "memory"
        / "agentic"
        / "learning-events"
        / f"{event.event_id}.json"
    )
    stored = json.loads(stored_path.read_text(encoding="utf-8"))
    debt = learning_debt_records(tmp_path, limit=None)

    assert stored["user_instruction_exact"] == exact_words
    assert stored["feedback_status"] == "captured"
    assert stored["eval_disposition"] == CREATOR_FEEDBACK_PENDING_LINKAGE
    assert len(debt) == 1
    assert debt[0]["kind"] == "feedback_linkage"
    assert debt[0]["path"].endswith(f"{event.event_id}.json")
    assert debt[0]["line"].startswith("link package-local creator feedback")
    assert "needs proposal" not in debt[0]["line"]


def test_package_linked_creator_feedback_defaults_to_background_disposition(tmp_path: Path):
    event = capture_learning_event(
        tmp_path,
        source="creator_feedback",
        summary="Repair the current package before considering durable learning.",
        package_path="output/carousels/quiet-morning",
        feedback_metadata={"feedback_id": "fb-package-quiet-morning"},
    )

    assert event.feedback_status == "captured"
    assert event.eval_disposition == "background"
    assert event.package_path == "output/carousels/quiet-morning"
    assert event.feedback_metadata == {"feedback_id": "fb-package-quiet-morning"}


def test_capture_learning_cli_routes_creator_feedback_to_linkage_not_proposal(tmp_path: Path):
    repo_root = Path(__file__).resolve().parents[1]
    capture = subprocess.run(
        [
            sys.executable,
            "scripts/agentic_os.py",
            "--workspace-root",
            str(tmp_path),
            "capture-learning",
            "--source",
            "creator_feedback",
            "--summary",
            "Repair the selected carousel structure without changing its concept.",
        ],
        cwd=repo_root,
        text=True,
        capture_output=True,
        check=False,
        timeout=30,
    )
    debt = subprocess.run(
        [
            sys.executable,
            "scripts/agentic_os.py",
            "--workspace-root",
            str(tmp_path),
            "learning-debt",
        ],
        cwd=repo_root,
        text=True,
        capture_output=True,
        check=False,
        timeout=30,
    )

    assert capture.returncode == 0, capture.stderr
    captured = json.loads(capture.stdout)
    assert captured["feedback_status"] == "captured"
    assert captured["eval_disposition"] == CREATOR_FEEDBACK_PENDING_LINKAGE
    assert debt.returncode == 0, debt.stderr
    debt_payload = json.loads(debt.stdout)
    assert debt_payload["debt_count"] == 1
    assert debt_payload["records"][0]["kind"] == "feedback_linkage"
    assert "needs proposal" not in debt_payload["records"][0]["line"]


def test_legacy_unlinked_creator_feedback_is_reported_without_mutation(tmp_path: Path):
    event_dir = tmp_path / "memory" / "agentic" / "learning-events"
    event_dir.mkdir(parents=True)
    event_path = event_dir / "event-legacy-package-feedback.json"
    event_path.write_text(
        json.dumps(
            {
                "schema_version": "learning-event/v1",
                "event_id": "event-legacy-package-feedback",
                "source": "creator_feedback",
                "summary": "Creator selected the sofa route for this carousel.",
                "evidence_paths": ["Exact creator selection: We needed a bigger sofa."],
                "created_at": "2026-09-12T06:11:46+00:00",
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    original_bytes = event_path.read_bytes()

    debt = learning_debt_records(tmp_path, limit=None)

    assert event_path.read_bytes() == original_bytes
    assert len(debt) == 1
    assert debt[0]["kind"] == "feedback_linkage"
    assert "needs proposal" not in debt[0]["line"]


def test_explicit_proposal_replaces_unlinked_feedback_linkage_debt(tmp_path: Path):
    target = tmp_path / "config" / "skills" / "alpha.md"
    target.parent.mkdir(parents=True)
    target.write_text("# Alpha\n", encoding="utf-8")
    event = capture_learning_event(
        tmp_path,
        source="creator_feedback",
        summary="A reviewed correction should become durable.",
    )
    proposal_path = create_learning_proposal(
        tmp_path,
        source_event_id=event.event_id,
        target_path="config/skills/alpha.md",
        proposed_action="modify",
        rationale="The creator explicitly requested a durable workflow change.",
        proposed_content="# Alpha\n\nRead the current pixels.\n",
        required_validators=["skill_eval"],
    )

    debt = learning_debt_records(tmp_path, limit=None)

    assert not any(item["kind"] == "feedback_linkage" for item in debt)
    assert any(
        item["kind"] == "draft_proposal"
        and item["path"] == proposal_path.relative_to(tmp_path).as_posix()
        for item in debt
    )


def test_agentic_os_cli_applies_valid_learning_proposal_with_approval(tmp_path: Path):
    root = tmp_path
    target = root / "config" / "skills" / "alpha.md"
    target.parent.mkdir(parents=True)
    target.write_text("# Alpha\n\nconfidence: 0.8\n", encoding="utf-8")
    event = capture_learning_event(
        root,
        source="code_review",
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
    run_required_validators(root, proposal_path)

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


def test_apply_learning_refuses_stale_target_before_hash(tmp_path: Path):
    target = tmp_path / "config" / "skills" / "alpha.md"
    target.parent.mkdir(parents=True)
    target.write_text("# Alpha\n\nBefore.\n", encoding="utf-8")
    proposal_path = create_learning_proposal(
        tmp_path,
        source_event_id="event-1",
        target_path="config/skills/alpha.md",
        proposed_action="modify",
        rationale="Update the guidance.",
        proposed_content="# Alpha\n\nAfter.\n",
        required_validators=["skill_eval"],
    )
    target.write_text("# Alpha\n\nConcurrent creator edit.\n", encoding="utf-8")

    with pytest.raises(ValueError, match="before_hash mismatch"):
        apply_learning_proposal(tmp_path, proposal_path, approved_by="creator")

    assert "Concurrent creator edit" in target.read_text(encoding="utf-8")
    assert json.loads(proposal_path.read_text(encoding="utf-8"))["status"] == "draft"


def test_apply_learning_refuses_changed_proposed_content(tmp_path: Path):
    target = tmp_path / "config" / "skills" / "alpha.md"
    target.parent.mkdir(parents=True)
    target.write_text("# Alpha\n\nBefore.\n", encoding="utf-8")
    proposal_path = create_learning_proposal(
        tmp_path,
        source_event_id="event-1",
        target_path="config/skills/alpha.md",
        proposed_action="modify",
        rationale="Update the guidance.",
        proposed_content="# Alpha\n\nAfter.\n",
        required_validators=["skill_eval"],
    )
    proposal = json.loads(proposal_path.read_text(encoding="utf-8"))
    content_path = tmp_path / proposal["proposed_content_path"]
    content_path.write_text("# Alpha\n\nTampered.\n", encoding="utf-8")

    with pytest.raises(ValueError, match="after_hash mismatch"):
        apply_learning_proposal(tmp_path, proposal_path, approved_by="creator")

    assert target.read_text(encoding="utf-8") == "# Alpha\n\nBefore.\n"
    assert json.loads(proposal_path.read_text(encoding="utf-8"))["status"] == "draft"


def test_apply_learning_refuses_target_traversal(tmp_path: Path):
    target = tmp_path / "config" / "skills" / "alpha.md"
    target.parent.mkdir(parents=True)
    target.write_text("# Alpha\n\nBefore.\n", encoding="utf-8")
    proposal_path = create_learning_proposal(
        tmp_path,
        source_event_id="event-1",
        target_path="config/skills/alpha.md",
        proposed_action="modify",
        rationale="Update the guidance.",
        proposed_content="# Alpha\n\nAfter.\n",
        required_validators=["skill_eval"],
    )
    proposal = json.loads(proposal_path.read_text(encoding="utf-8"))
    proposal["target_path"] = "../outside.md"
    proposal_path.write_text(json.dumps(proposal), encoding="utf-8")

    with pytest.raises(ValueError, match="parent traversal"):
        apply_learning_proposal(tmp_path, proposal_path, approved_by="creator")

    assert target.read_text(encoding="utf-8") == "# Alpha\n\nBefore.\n"


def test_apply_learning_refuses_symlink_target(tmp_path: Path):
    outside = tmp_path.parent / f"{tmp_path.name}-outside.md"
    outside.write_text("outside content", encoding="utf-8")
    target = tmp_path / "config" / "skills" / "alpha.md"
    target.parent.mkdir(parents=True)
    target.write_text("# Alpha\n\nBefore.\n", encoding="utf-8")
    proposal_path = create_learning_proposal(
        tmp_path,
        source_event_id="event-1",
        target_path="config/skills/alpha.md",
        proposed_action="modify",
        rationale="Update the guidance.",
        proposed_content="# Alpha\n\nAfter.\n",
        required_validators=["skill_eval"],
    )
    target.unlink()
    target.symlink_to(outside)

    with pytest.raises(ValueError, match="symlink"):
        apply_learning_proposal(tmp_path, proposal_path, approved_by="creator")

    assert outside.read_text(encoding="utf-8") == "outside content"


def test_agentic_os_cli_refuses_to_reapply_learning_proposal(tmp_path: Path):
    root = tmp_path
    target = root / "config" / "skills" / "alpha.md"
    target.parent.mkdir(parents=True)
    target.write_text("# Alpha\n\nconfidence: 0.8\n", encoding="utf-8")
    event = capture_learning_event(
        root,
        source="code_review",
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
    run_required_validators(root, proposal_path)

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
        source="code_review",
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
    assert payload["next_action"] == "validate_then_review_then_apply_learning"
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
