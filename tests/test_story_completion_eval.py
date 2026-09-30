"""Final-draft reviews cannot trade missing story development for clean prose."""
import hashlib
import json
import shutil
from pathlib import Path

import pytest

from evals.checkers.rubric import run_rubric_checkers
from evals.schemas import EvalTask, PassCriteria, discover_tasks


def setup_review(tmp_path):
    artifact = "output/evals/draft/creator-brief.md"
    path = tmp_path / artifact
    path.parent.mkdir(parents=True)
    path.write_text("A complete candidate draft supplied to an independent reviewer.\n")
    rubric = tmp_path / "evals/rubrics/story-completion.md"
    rubric.parent.mkdir(parents=True)
    rubric.write_text("# Story completion\n")
    task = EvalTask(
        schema_version="1.0", id="story-test", title="Complete a locked concept",
        category="creative_contract", difficulty="hard", suites=["creative"],
        prompt="prompt.md", starting_state=[], done_when=[], allowed_paths=[],
        forbidden_paths=[], expected_files_changed=[artifact], forbidden_changes=[],
        required_commands=[], deterministic_checkers=[], rubric_checkers=["story_completion"],
        pass_criteria=PassCriteria(),
    )
    review = {
        "task_id": task.id, "rubric": "story_completion",
        "author_id": "agent:author", "reviewer_id": "agent:reviewer",
        "artifact": artifact, "artifact_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        "scores": {"lock_continuity": 2, "story_architecture": 3,
                   "causal_development": 3, "earned_payoff": 3, "human_voice": 1},
        # These are synthetic reviewer inputs for validator tests, not a claim
        # that Python has read or judged the story.
        "evidence": {
            "lock_continuity": ["The reviewer locates the protected premise in the cover."],
            "story_architecture": ["The reviewer maps each phase to a different story job."],
            "causal_development": ["The reviewer cites the choice causing the final action."],
            "earned_payoff": ["The reviewer cites both partners' changed response in the ending."],
            "human_voice": ["The reviewer quotes the scene-native dialogue."],
        },
    }
    return task, review, path


def judge(task, root, review=None):
    reviews = {(task.id, "story_completion"): review} if review is not None else None
    return run_rubric_checkers(task, root, ["story_completion"], reviews)


def judgment(results):
    matches = [r for r in results if r.code == "rubric_story_completion_judgment"]
    assert len(matches) == 1, [r.to_dict() for r in results]
    return matches[0]


def test_final_draft_without_editorial_review_remains_pending(tmp_path):
    task, _, _ = setup_review(tmp_path)
    assert judgment(judge(task, tmp_path)).status == "PENDING"


@pytest.mark.parametrize("dimension", ["story_architecture", "causal_development", "earned_payoff"])
def test_high_total_cannot_compensate_for_incomplete_story_phase(tmp_path, dimension):
    task, review, _ = setup_review(tmp_path)
    review["scores"][dimension] = 1  # Still 10/12, but the story is incomplete.
    review["evidence"][dimension] = ["The ending asks a question but no response or changed state is supplied."]
    result = judgment(judge(task, tmp_path, review))
    assert result.status == "FAIL"
    assert f"minimum_block={dimension}" in result.evidence


def test_complete_independent_review_passes_but_draft_change_invalidates_it(tmp_path):
    task, review, path = setup_review(tmp_path)
    assert judgment(judge(task, tmp_path, review)).status == "PASS"
    path.write_text(path.read_text() + "The payoff has been removed.\n")
    result = judgment(judge(task, tmp_path, review))
    assert result.status == "FAIL"
    assert any("stale" in e for e in result.evidence)


def test_review_cannot_substitute_a_different_artifact_for_the_final_draft(tmp_path):
    task, review, _ = setup_review(tmp_path)
    other = tmp_path / "source.md"
    other.write_text("An earlier approved concept, not the requested final draft.")
    review["artifact"] = "source.md"
    review["artifact_sha256"] = hashlib.sha256(other.read_bytes()).hexdigest()
    result = judgment(judge(task, tmp_path, review))
    assert result.status == "FAIL"
    assert any("requested draft" in e for e in result.evidence)


@pytest.mark.parametrize("mutation", ["self_review", "missing_evidence"])
def test_story_review_requires_independent_evidence(tmp_path, mutation):
    task, review, _ = setup_review(tmp_path)
    if mutation == "self_review":
        review["reviewer_id"] = review["author_id"]
    else:
        review["evidence"].pop("earned_payoff")
    assert judgment(judge(task, tmp_path, review)).status == "FAIL"


def test_actual_rejected_draft_needs_semantic_review_and_fails_its_anchored_payoff_review(tmp_path):
    from evals.runner import run_task_checks

    root = Path(__file__).resolve().parents[1]
    task = next(t for t in discover_tasks(root) if t.id == "ASTO-022-concept-to-final-story")
    artifact = tmp_path / task.expected_files_changed[0]
    artifact.parent.mkdir(parents=True)
    shutil.copyfile(task.task_dir / "fixtures/rejected-draft.md", artifact)
    rubric = tmp_path / "evals/rubrics/story-completion.md"
    rubric.parent.mkdir(parents=True)
    shutil.copyfile(root / "evals/rubrics/story-completion.md", rubric)

    pending = run_task_checks(task, tmp_path, skip_commands=True,
                              explicit_changed_paths=task.expected_files_changed)
    assert pending.resolved is False
    assert judgment(pending.checks).status == "PENDING"
    assert all(c.status == "PASS" for c in pending.checks if c.code == "creator_visible_framework_language")

    review = json.loads((task.task_dir / "calibration/rejected-draft-review.json").read_text())
    reviewed = run_task_checks(task, tmp_path, skip_commands=True,
                               explicit_changed_paths=task.expected_files_changed,
                               rubric_reviews={(task.id, "story_completion"): review})
    assert reviewed.resolved is False
    result = judgment(reviewed.checks)
    assert result.status == "FAIL"
    assert "minimum_block=earned_payoff" in result.evidence
    assert "total=8/12" in result.evidence
