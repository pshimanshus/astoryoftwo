from __future__ import annotations

import hashlib
import json
from pathlib import Path, PurePosixPath
from typing import Any

from evals.checkers.creative_rubric import check_creator_visible_copy
from evals.schemas import CheckResult, EvalTask


RUBRIC_FILES = {
    "creative_contract": Path("evals/rubrics/creative-contract.md"),
    "visual_variety": Path("evals/rubrics/visual-storytelling.md"),
}
RUBRIC_SPECS = {
    "creative_contract": {
        "dimensions": {
            "seed_preservation": 3,
            "scene_proof": 3,
            "format_judgment": 2,
            "creator_facing_taste": 2,
            "relationship_motion": 2,
        },
        "minimum_total": 9,
        "no_zero": {"seed_preservation", "scene_proof"},
    },
    "visual_variety": {
        "dimensions": {
            "image_first_story_legibility": 3,
            "shot_progression": 3,
            "object_and_setting_continuity": 3,
            "blocking_and_spatial_clarity": 2,
            "text_image_composition": 1,
        },
        "minimum_total": 9,
        "no_zero": {"image_first_story_legibility", "blocking_and_spatial_clarity"},
    },
}


def _pass(code: str, message: str, evidence: list[str] | None = None) -> CheckResult:
    return CheckResult(
        code=code,
        status="PASS",
        severity="info",
        message=message,
        evidence=evidence or [],
    )


def _fail(
    code: str,
    message: str,
    *,
    severity: str = "major",
    evidence: list[str] | None = None,
) -> CheckResult:
    return CheckResult(
        code=code,
        status="FAIL",
        severity=severity,
        message=message,
        evidence=evidence or [],
    )


def _pending(code: str, message: str, evidence: list[str] | None = None) -> CheckResult:
    return CheckResult(
        code=code,
        status="PENDING",
        severity="info",
        message=message,
        evidence=evidence or [],
    )


def _read_json(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        return {}
    return payload if isinstance(payload, dict) else {}


def _task_artifact(task: EvalTask, root: Path, suffix: str) -> Path | None:
    for path in task.expected_files_changed:
        if path.endswith(suffix):
            return root / path
    for overlay in task.fixture_overlay:
        if overlay.target.endswith(suffix):
            return root / overlay.target
    return None


def _creator_visible_artifact(task: EvalTask, root: Path) -> Path | None:
    return _task_artifact(task, root, "creator-brief.md")


def _concept_selection_artifact(task: EvalTask, root: Path) -> Path | None:
    return _task_artifact(task, root, "concept-selection.json")


def _visual_plan_artifact(task: EvalTask, root: Path) -> Path | None:
    for suffix in ("home-visual-plan.json", "visual-plan-quality.json", "visual-qa.json"):
        path = _task_artifact(task, root, suffix)
        if path is not None:
            return path
    return None


def _active_rejected_high_scores(path: Path) -> list[str]:
    payload = _read_json(path)
    records = payload.get("concepts") or payload.get("routes") or payload.get("options") or []
    if not isinstance(records, list):
        return []
    active: list[str] = []
    for record in records:
        if not isinstance(record, dict):
            continue
        text = json.dumps(record, ensure_ascii=False).lower()
        rejected = any(token in text for token in ("reject", "unsendable", "hard_no", "creator_no"))
        scores = [
            float(value)
            for key, value in record.items()
            if "score" in str(key).lower() and isinstance(value, int | float)
        ]
        max_score = max(scores) if scores else 0.0
        stopped = any(
            token in text
            for token in (
                "stop",
                "do_not_polish",
                "do not polish",
                "score_invalidated",
                "invalid calibration",
                "rebuild",
                "cap_applied",
            )
        )
        if rejected and max_score >= 28 and not stopped:
            active.append(f"{record.get('title') or record.get('name') or 'unnamed'}: {max_score:g}")
    return active


def check_creative_contract_rubric(task: EvalTask, root: Path) -> list[CheckResult]:
    rubric_path = root / RUBRIC_FILES["creative_contract"]
    if not rubric_path.exists():
        return [_fail("rubric_creative_contract", "Missing creative contract rubric file.")]

    results: list[CheckResult] = []
    creator_artifact = _creator_visible_artifact(task, root)
    if creator_artifact is not None and creator_artifact.exists():
        results.extend(check_creator_visible_copy(creator_artifact))

    concept_selection = _concept_selection_artifact(task, root)
    if concept_selection is not None and concept_selection.exists():
        active = _active_rejected_high_scores(concept_selection)
        if active:
            results.append(
                _fail(
                    "rubric_creative_contract_score_calibration",
                    "Creative contract rubric blocks active 28+ scores on creator-rejected concepts.",
                    evidence=active,
                )
            )
        else:
            results.append(
                _pass(
                    "rubric_creative_contract_score_calibration",
                    "No active 28+ creator-rejected concept remains in the rubric artifact.",
                    evidence=[str(concept_selection)],
                )
            )

    if results:
        return results
    return [
        _pass(
            "rubric_creative_contract",
            "Creative contract rubric precheck executed; subjective review remains separate from mechanical gates.",
            evidence=[str(rubric_path)],
        )
    ]


def check_visual_variety_rubric(task: EvalTask, root: Path) -> list[CheckResult]:
    rubric_path = root / RUBRIC_FILES["visual_variety"]
    if not rubric_path.exists():
        return [_fail("rubric_visual_variety", "Missing visual-storytelling rubric file.")]

    artifact = _visual_plan_artifact(task, root)
    if artifact is not None and artifact.exists():
        text = artifact.read_text(encoding="utf-8", errors="ignore").lower()
        repeated_terms = sum(
            token in text
            for token in ("same shot", "same room", "same plants", "cozy home", "generic couple")
        )
        if repeated_terms and '"status": "pass"' in text and "director_storyboard" not in text:
            return [
                _fail(
                    "rubric_visual_variety_repetition",
                    "Visual-variety rubric blocks PASS artifacts that rely on repeated/generic visual grammar.",
                    evidence=[str(artifact)],
                )
            ]
        return [
            _pass(
                "rubric_visual_variety_artifact",
                "Visual-variety rubric hook inspected a concrete visual artifact.",
                evidence=[str(artifact)],
            )
        ]

    return [
        _pass(
            "rubric_visual_variety",
            "Visual-variety rubric precheck executed; subjective shot-quality review remains separate from mechanical gates.",
            evidence=[str(rubric_path)],
        )
    ]


RUBRIC_CHECKERS = {
    "creative_contract": check_creative_contract_rubric,
    "visual_variety": check_visual_variety_rubric,
}


def load_rubric_reviews(path: Path) -> dict[tuple[str, str], dict[str, Any]]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if payload.get("schema_version") != "1.0":
        raise ValueError("rubric results must use schema_version 1.0")
    raw_reviews = payload.get("reviews")
    if not isinstance(raw_reviews, list):
        raise ValueError("rubric results must contain a reviews list")

    reviews: dict[tuple[str, str], dict[str, Any]] = {}
    for index, review in enumerate(raw_reviews, start=1):
        if not isinstance(review, dict):
            raise ValueError(f"rubric review {index} must be an object")
        task_id = str(review.get("task_id") or "").strip()
        rubric = str(review.get("rubric") or "").strip()
        if not task_id or rubric not in RUBRIC_SPECS:
            raise ValueError(f"rubric review {index} has invalid task_id or rubric")
        key = (task_id, rubric)
        if key in reviews:
            raise ValueError(f"duplicate rubric review for {task_id}/{rubric}")
        reviews[key] = review
    return reviews


def _rubric_judgment(
    task: EvalTask,
    root: Path,
    rubric_name: str,
    review: dict[str, Any] | None,
) -> CheckResult:
    code = f"rubric_{rubric_name}_judgment"
    rubric_path = root / RUBRIC_FILES[rubric_name]
    if review is None:
        return _pending(
            code,
            "Subjective rubric review has not been supplied; mechanical prechecks cannot award creative-quality credit.",
            evidence=[str(rubric_path)],
        )

    author_id = str(review.get("author_id") or "").strip()
    reviewer_id = str(review.get("reviewer_id") or "").strip()
    artifact = str(review.get("artifact") or "").strip().replace("\\", "/")
    expected_sha256 = str(review.get("artifact_sha256") or "").strip().lower()
    scores = review.get("scores")
    evidence = review.get("evidence")
    issues: list[str] = []
    if not author_id:
        issues.append("author_id is required")
    if not reviewer_id:
        issues.append("reviewer_id is required")
    if author_id and reviewer_id and author_id == reviewer_id:
        issues.append("reviewer_id must differ from author_id")
    artifact_path = PurePosixPath(artifact)
    resolved_artifact: Path | None = None
    if not artifact or artifact_path.is_absolute() or ".." in artifact_path.parts:
        issues.append("artifact must be a safe repo-relative path")
    else:
        resolved_root = root.resolve()
        resolved_artifact = root.joinpath(*artifact_path.parts).resolve(strict=False)
        try:
            resolved_artifact.relative_to(resolved_root)
        except ValueError:
            issues.append("artifact resolves outside the workspace root")
            resolved_artifact = None
        if resolved_artifact is not None and not resolved_artifact.is_file():
            issues.append(f"reviewed artifact does not exist: {artifact}")
            resolved_artifact = None
    if not expected_sha256 or len(expected_sha256) != 64 or any(
        character not in "0123456789abcdef" for character in expected_sha256
    ):
        issues.append("artifact_sha256 must be a lowercase 64-character SHA-256 digest")
    elif resolved_artifact is not None:
        observed_sha256 = hashlib.sha256(resolved_artifact.read_bytes()).hexdigest()
        if observed_sha256 != expected_sha256:
            issues.append(
                "artifact_sha256 does not match the reviewed artifact; the review is stale"
            )
    if not isinstance(scores, dict):
        issues.append("scores must be an object")
        scores = {}
    if not isinstance(evidence, dict):
        issues.append("evidence must be an object")
        evidence = {}

    spec = RUBRIC_SPECS[rubric_name]
    dimensions: dict[str, int] = spec["dimensions"]
    normalized_scores: dict[str, int] = {}
    for dimension, maximum in dimensions.items():
        value = scores.get(dimension)
        if not isinstance(value, int) or isinstance(value, bool) or not 0 <= value <= maximum:
            issues.append(f"{dimension} score must be an integer from 0 to {maximum}")
            continue
        normalized_scores[dimension] = value
        anchors = evidence.get(dimension)
        if not isinstance(anchors, list) or not any(str(item).strip() for item in anchors):
            issues.append(f"{dimension} requires at least one concrete evidence anchor")

    unexpected_scores = sorted(set(scores) - set(dimensions))
    if unexpected_scores:
        issues.append(f"unexpected score dimensions: {unexpected_scores}")
    if issues:
        return _fail(
            code,
            "Rubric review is incomplete or invalid.",
            evidence=issues,
        )

    total = sum(normalized_scores.values())
    zero_blocks = sorted(
        dimension
        for dimension in spec["no_zero"]
        if normalized_scores[dimension] == 0
    )
    score_evidence = [
        f"author={author_id}",
        f"reviewer={reviewer_id}",
        f"artifact={artifact}",
        f"artifact_sha256={expected_sha256}",
        f"total={total}/12",
        *[f"{name}={value}" for name, value in normalized_scores.items()],
    ]
    if total < spec["minimum_total"] or zero_blocks:
        return _fail(
            code,
            "Anchored rubric review does not meet the creative-quality threshold.",
            evidence=[*score_evidence, *[f"zero_block={name}" for name in zero_blocks]],
        )
    return _pass(
        code,
        "Anchored rubric review meets the creative-quality threshold.",
        evidence=score_evidence,
    )


def run_rubric_checkers(
    task: EvalTask,
    root: Path,
    checker_names: list[str],
    reviews: dict[tuple[str, str], dict[str, Any]] | None = None,
) -> list[CheckResult]:
    results: list[CheckResult] = []
    reviews = reviews or {}
    for name in checker_names:
        checker = RUBRIC_CHECKERS.get(name)
        if checker is None:
            results.append(
                _fail(
                    "unknown_rubric_checker",
                    f"No rubric checker is registered for {name}.",
                )
            )
            continue
        results.extend(checker(task, root))
        results.append(_rubric_judgment(task, root, name, reviews.get((task.id, name))))
    return results
