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
    )
    search = subprocess.run(
        [sys.executable, "scripts/agentic_os.py", "--workspace-root", str(root), "search", "visual comedy"],
        cwd=repo_root,
        text=True,
        capture_output=True,
        check=False,
    )

    assert context.returncode == 0, context.stderr
    assert '"profile": "a-story-of-two"' in context.stdout
    assert search.returncode == 0, search.stderr
    assert "memory/semantic/prefs.md" in search.stdout
