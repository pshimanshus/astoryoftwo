from __future__ import annotations

import json
import re
import tempfile
from collections.abc import Callable
from pathlib import Path, PurePosixPath
from typing import Any

from evals.checkers.creative_rubric import check_creator_visible_copy
from evals.schemas import CheckResult, EvalTask
from pipeline.agentic.context_loader import RequiredSectionTruncatedError, assemble_context_pack
from pipeline.stages.carousel_quality import (
    validate_anatomy_inventory_check,
    validate_scene_entity_integrity_check,
    validate_spatial_topology_check,
)
from pipeline.stages.carousel_format_contract import (
    expected_output_relative_path,
)
from pipeline.stages.carousel_visual_storytelling import (
    validate_director_storyboard,
    validate_frame_readability,
)
from pipeline.agentic.carousel_state import derive_carousel_state
from pipeline.agentic.workflow_doctor import inspect_carousel_package
from scripts.autopublish import find_risky_paths, parse_changed_paths, scan_secret_text


Checker = Callable[[EvalTask, Path], list[CheckResult]]


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
    severity: str = "critical",
    evidence: list[str] | None = None,
) -> CheckResult:
    return CheckResult(
        code=code,
        status="FAIL",
        severity=severity,
        message=message,
        evidence=evidence or [],
    )


_EVAL_FORMATS = ("instagram_post",)


def _build_eval_visual_direction(
    slides: list[dict[str, Any]],
    *,
    formats: tuple[str, ...] = _EVAL_FORMATS,
) -> dict[str, Any]:
    """Build a small valid physical-scene baseline for semantic evals."""

    narrative_jobs = (
        "establish the lived relationship geography",
        "advance the physical action and pressure",
        "release the action into visible consequence",
    )
    shot_sizes = ("wide geography shot", "medium action shot", "close evidence shot")
    records: list[dict[str, Any]] = []
    for index, source in enumerate(slides, start=1):
        action = str(
            source.get("physical_action")
            or source.get("visual")
            or "One partner moves a shared object while the other visibly reacts to its changed state."
        )
        records.append(
            {
                "slide": index,
                "physical_action": action,
                "narrative_job": narrative_jobs[(index - 1) % len(narrative_jobs)],
                "silent_read": action,
                "shot": {
                    "size": shot_sizes[(index - 1) % len(shot_sizes)],
                    "camera_position": "Eye-level beside the active hands and changed shared object.",
                },
                "setting": {
                    "motivated_light": "Window light crosses the acting hands and changed object state."
                },
                "story_evidence": [
                    {
                        "carrier": "the shared object between both partners",
                        "observable_state": "its owner and position visibly change during the action",
                        "narrative_job": "prove the relationship turn without relying on copy",
                    }
                ],
            }
        )
    return {"requested_formats": list(formats), "slides": records}


def _build_eval_frame_review(
    slides: list[dict[str, Any]],
    *,
    formats: tuple[str, ...] = _EVAL_FORMATS,
) -> dict[str, Any]:
    frames: list[dict[str, Any]] = []
    for number, source in enumerate(slides, start=1):
        for output_format in formats:
            frames.append(
                {
                    "slide": number,
                    "format": output_format,
                    "file": expected_output_relative_path(output_format, number),
                    "status": "PASS",
                    "expected_silent_read": str(source.get("visual") or source.get("physical_action") or ""),
                    "observed_image_first_read": "The frame visibly preserves the intended action, reaction, and changed object state.",
                    "core_action_legible": True,
                    "relationship_turn_legible": True,
                    "copy_visual_contradictions": [],
                    "unexpected_story": [],
                    "evidence": "Visible hands, eye-lines, object position, and reaction prove the current story beat.",
                }
            )
    return {
        "pass": True,
        "status": "PASS",
        "image_first": True,
        "frames": frames,
        "issues": [],
    }


def _line_allows_bottom_right_as_negative_example(line: str) -> bool:
    lowered = line.lower()
    return any(
        phrase in lowered
        for phrase in (
            "forbidden",
            "wrong",
            "not bottom-right",
            "never bottom-right",
            "other than top-right",
            "including bottom-right",
        )
    )


def check_brandmark_top_right_rule(task: EvalTask, root: Path) -> list[CheckResult]:
    del task
    path = root / "config" / "rules" / "brandmark.md"
    if not path.exists():
        return [_fail("brandmark_top_right_rule", "Missing config/rules/brandmark.md.")]

    text = path.read_text(encoding="utf-8")
    top_right_mentions = [
        f"{index}: {line.strip()}"
        for index, line in enumerate(text.splitlines(), start=1)
        if "top-right" in line.lower()
    ]
    bottom_right_affirmations = [
        f"{index}: {line.strip()}"
        for index, line in enumerate(text.splitlines(), start=1)
        if "bottom-right" in line.lower()
        and ("brandmark" in line.lower() or "@a.storyof.two" in line.lower())
        and not _line_allows_bottom_right_as_negative_example(line)
    ]

    if bottom_right_affirmations:
        return [
            _fail(
                "brandmark_top_right_rule",
                "Brandmark rule still contains affirmative bottom-right placement drift.",
                evidence=bottom_right_affirmations,
            )
        ]
    if not top_right_mentions:
        return [
            _fail(
                "brandmark_top_right_rule",
                "Brandmark rule does not affirm the required top-right placement.",
            )
        ]
    return [
        _pass(
            "brandmark_top_right_rule",
            "Brandmark rule affirms top-right placement without bottom-right drift.",
            evidence=top_right_mentions[:3],
        )
    ]


def _carousel_package_from_fixture(task: EvalTask, root: Path) -> Path | None:
    for overlay in task.fixture_overlay:
        target = PurePosixPath(overlay.target.replace("\\", "/"))
        parts = target.parts
        if len(parts) >= 4 and parts[0] == "output" and parts[1] == "carousels":
            return root.joinpath(*parts[:4])
    return None


def _fixture_dir_from_overlay(
    task: EvalTask,
    root: Path,
    *,
    prefix: tuple[str, ...],
    depth: int,
) -> Path | None:
    for overlay in task.fixture_overlay:
        target = PurePosixPath(overlay.target.replace("\\", "/"))
        parts = target.parts
        if len(parts) >= depth and parts[: len(prefix)] == prefix:
            return root.joinpath(*parts[:depth])
    return None


def _fixture_file_from_overlay(task: EvalTask, root: Path, filename: str) -> Path | None:
    for overlay in task.fixture_overlay:
        target = PurePosixPath(overlay.target.replace("\\", "/"))
        if target.name == filename:
            return root.joinpath(*target.parts)
    return None


def _read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {}
    return data if isinstance(data, dict) else {}


def _read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return ""


def _stringify(value: Any) -> str:
    if isinstance(value, str):
        return value
    return json.dumps(value, ensure_ascii=False, sort_keys=True)


def _status(value: Any) -> str:
    return str(value or "").strip().lower()


def check_carousel_doctor_fixture(task: EvalTask, root: Path) -> list[CheckResult]:
    package = _carousel_package_from_fixture(task, root)
    if package is None:
        return [
            _fail(
                "carousel_doctor_fixture",
                "Task has no output/carousels fixture package target.",
            )
        ]
    if not package.exists():
        return [
            _fail(
                "carousel_doctor_fixture",
                f"Prepared carousel fixture package is missing: {package}",
            )
        ]

    report = inspect_carousel_package(package)
    state = derive_carousel_state(package)
    issue_codes = sorted({issue.code for issue in report.issues})

    if task.id == "ASTO-003-textless-prompt":
        if report.blocked and "active_textless_prompt" in issue_codes:
            return [
                _pass(
                    "carousel_doctor_fixture",
                    "Seeded textless prompt is blocked with active_textless_prompt.",
                    evidence=issue_codes,
                )
            ]
        return [
            _fail(
                "carousel_doctor_fixture",
                "Seeded textless prompt did not produce the active_textless_prompt blocker.",
                evidence=[f"blocked={report.blocked}", *issue_codes],
            )
        ]

    if task.id == "ASTO-004-fake-publishable-package":
        if report.blocked and state.blocked and not state.publishable:
            return [
                _pass(
                    "carousel_doctor_fixture",
                    "Seeded fake-publishable package is blocked and non-publishable.",
                    evidence=[f"state={state.name}", *issue_codes],
                )
            ]
        return [
            _fail(
                "carousel_doctor_fixture",
                "Seeded fake-publishable package is not blocked as non-publishable.",
                evidence=[
                    f"report_blocked={report.blocked}",
                    f"state={state.name}",
                    f"publishable={state.publishable}",
                    *issue_codes,
                ],
            )
        ]

    return [
        _fail(
            "carousel_doctor_fixture",
            f"No carousel fixture expectation is registered for {task.id}.",
            severity="major",
        )
    ]


def check_stale_artifact_fixture(task: EvalTask, root: Path) -> list[CheckResult]:
    package = _carousel_package_from_fixture(task, root)
    if package is None or not package.exists():
        return [
            _fail(
                "stale_artifact_fixture",
                "Task has no materialized stale-artifact carousel fixture package.",
            )
        ]

    report = inspect_carousel_package(package)
    state = derive_carousel_state(package)
    issue_codes = sorted({issue.code for issue in report.issues})

    if report.blocked and state.blocked and "stale_artifact_carryover" in issue_codes:
        stale_evidence = [
            evidence
            for issue in report.issues
            if issue.code == "stale_artifact_carryover"
            for evidence in issue.evidence
        ]
        return [
            _pass(
                "stale_artifact_fixture",
                "Seeded creator correction is blocked because active generation artifacts still carry old rejected phrases.",
                evidence=stale_evidence[:8],
            )
        ]
    return [
        _fail(
            "stale_artifact_fixture",
            "Seeded stale generation artifacts did not produce the stale_artifact_carryover blocker.",
            evidence=[f"blocked={report.blocked}", f"state={state.name}", *issue_codes],
        )
    ]


def check_identity_stop_gate_fixture(task: EvalTask, root: Path) -> list[CheckResult]:
    package = _carousel_package_from_fixture(task, root)
    if package is None or not package.exists():
        return [
            _fail(
                "identity_stop_gate_fixture",
                "Task has no materialized identity stop-gate carousel fixture package.",
            )
        ]

    report = inspect_carousel_package(package)
    state = derive_carousel_state(package)
    issue_codes = sorted({issue.code for issue in report.issues})
    expected_codes = {
        "identity_references_missing",
        "identity_eval_missing_stop_gate",
        "identity_eval_unverified_stop_gate",
        "identity_eval_not_passed_stop_gate",
        "identity_eval_incomplete_stop_gate",
    }

    if report.blocked and state.blocked and expected_codes.intersection(issue_codes):
        return [
            _pass(
                "identity_stop_gate_fixture",
                "Seeded proof/batch continuation is blocked until structured identity evidence exists.",
                evidence=issue_codes,
            )
        ]
    return [
        _fail(
            "identity_stop_gate_fixture",
            "Seeded proof/batch continuation did not trigger an identity stop-gate blocker.",
            evidence=[f"blocked={report.blocked}", f"state={state.name}", *issue_codes],
        )
    ]


def check_score_rejection_fixture(task: EvalTask, root: Path) -> list[CheckResult]:
    concept_dir = _fixture_dir_from_overlay(
        task,
        root,
        prefix=("output", "concepts"),
        depth=4,
    )
    if concept_dir is None or not concept_dir.exists():
        return [
            _fail(
                "score_rejection_fixture",
                "Task has no materialized rejected-concept scoring fixture.",
            )
        ]

    selection = _read_json(concept_dir / "concept-selection.json")
    records = selection.get("concepts") or selection.get("routes") or selection.get("options") or []
    if not isinstance(records, list):
        records = []

    active_inflated: list[str] = []
    for record in records:
        if not isinstance(record, dict):
            continue
        text = _stringify(record).lower()
        rejected = "reject" in text or "unsendable" in text
        scores = [
            float(value)
            for key, value in record.items()
            if "score" in str(key).lower() and isinstance(value, int | float)
        ]
        max_score = max(scores) if scores else 0.0
        stop_marked = any(
            token in text
            for token in (
                "stop",
                "do_not_polish",
                "do not polish",
                "rebuild",
                "score_invalidated",
                "invalid calibration",
                "cap_applied",
            )
        )
        if rejected and max_score >= 28 and not stop_marked:
            active_inflated.append(f"{record.get('title') or record.get('name') or 'unnamed'}: {max_score:g}")

    if active_inflated:
        return [
            _fail(
                "score_rejection_fixture",
                "Creator-rejected concepts still carry active 28+ scores without STOP/cap/invalidation routing.",
                evidence=active_inflated,
            )
        ]
    if records:
        return [
            _pass(
                "score_rejection_fixture",
                "Creator-rejected concept records are capped, stopped, invalidated, or no longer active 28+ calibration.",
                evidence=[str(concept_dir / "concept-selection.json")],
            )
        ]
    return [
        _fail(
            "score_rejection_fixture",
            "Rejected high-score concept fixture was not recognized as score inflation.",
            evidence=[str(concept_dir / "concept-selection.json")],
        )
    ]


def check_home_cinematic_fixture(task: EvalTask, root: Path) -> list[CheckResult]:
    plan_path = _fixture_file_from_overlay(task, root, "home-visual-plan.json")
    if plan_path is None or not plan_path.exists():
        return [
            _fail(
                "home_cinematic_fixture",
                "Task has no materialized home visual plan fixture.",
            )
        ]

    fixture = _read_json(plan_path)
    slides = fixture.get("slides") if isinstance(fixture.get("slides"), list) else []
    if not slides:
        return [
            _fail(
                "home_cinematic_fixture",
                "Home-cinematic fixture has no source slides.",
                evidence=[str(plan_path)],
            )
        ]

    plan = _build_eval_visual_direction(slides)
    baseline_issues = validate_director_storyboard(
        plan,
        slide_count=len(slides),
        expected_slides=slides,
        expected_formats=_EVAL_FORMATS,
    )
    if baseline_issues:
        return [
            _fail(
                "home_cinematic_fixture",
                "Home-cinematic eval harness is not a valid physical-scene baseline.",
                evidence=baseline_issues,
            )
        ]

    defect = fixture.get("defect")
    if isinstance(defect, dict) and defect:
        try:
            target = plan["slides"][int(defect.get("slide") or 1) - 1]
        except (IndexError, TypeError, ValueError):
            return [
                _fail(
                    "home_cinematic_fixture",
                    "Home-cinematic defect targets an invalid slide.",
                    evidence=[str(defect)],
                )
            ]
        target["silent_read"] = str(defect.get("silent_read") or "cozy home")
        target["shot"]["camera_position"] = str(
            defect.get("camera_position") or "appropriate composition"
        )
        target["setting"]["motivated_light"] = str(
            defect.get("motivated_light") or "nice lighting"
        )
        target["story_evidence"] = defect.get("story_evidence") or [
            {
                "carrier": "some props",
                "observable_state": "warm scene",
                "narrative_job": "couple moment",
            }
        ]

    issues = validate_director_storyboard(
        plan,
        slide_count=len(slides),
        expected_slides=slides,
        expected_formats=_EVAL_FORMATS,
    )

    required_target_markers = (
        ".silent_read",
        ".shot.camera_position",
        ".setting.motivated_light",
        ".story_evidence",
    )
    target_issues = [
        issue for issue in issues if any(marker in issue for marker in required_target_markers)
    ]
    if all(any(marker in issue for issue in target_issues) for marker in required_target_markers):
        return [
            _pass(
                "home_cinematic_fixture",
                "The physical-scene preflight blocks generic home-story evidence.",
                evidence=target_issues,
            )
        ]
    return [
        _fail(
            "home_cinematic_fixture",
            "Home visual fixture was not isolated to concrete cinematic story-evidence failures.",
            evidence=[*issues, str(plan_path)],
        )
    ]


def check_public_name_boundary_fixture(task: EvalTask, root: Path) -> list[CheckResult]:
    copy_path = _fixture_file_from_overlay(task, root, "public-copy.json")
    if copy_path is None or not copy_path.exists():
        return [
            _fail(
                "public_name_boundary_fixture",
                "Task has no materialized public-copy name-boundary fixture.",
            )
        ]

    payload = _read_json(copy_path)
    public_text = _stringify(payload.get("public_slide_copy") or payload.get("public") or payload)
    creator_artifact = _creator_visible_artifact(task, root)
    if creator_artifact.exists():
        public_text = "\n".join([public_text, _read_text(creator_artifact)])
    internal_text = _stringify(payload.get("internal_identity_prompt") or payload.get("internal") or "")
    leaked_names = sorted(set(re.findall(r"\b(?:Aachu|Zuv)\b", public_text)))
    internal_names = sorted(set(re.findall(r"\b(?:Aachu|Zuv)\b", internal_text)))

    if leaked_names:
        return [
            _fail(
                "public_name_boundary_fixture",
                "Public-facing copy leaks internal Aachu/Zuv names without an explicit public-name request.",
                evidence=[f"public={', '.join(leaked_names)}", str(copy_path)],
            )
        ]
    if internal_names:
        return [
            _pass(
                "public_name_boundary_fixture",
                "Public copy keeps names out while internal identity prompt still preserves Aachu/Zuv anchors.",
                evidence=[f"internal={', '.join(internal_names)}"],
            )
        ]
    return [
        _fail(
            "public_name_boundary_fixture",
            "Name-boundary artifact removed public names but also lost internal Aachu/Zuv identity anchors.",
            severity="major",
            evidence=[str(copy_path)],
        )
    ]


def check_copy_visual_logic_fixture(task: EvalTask, root: Path) -> list[CheckResult]:
    qa_path = _fixture_file_from_overlay(task, root, "visual-qa.json")
    if qa_path is None or not qa_path.exists():
        return [
            _fail(
                "copy_visual_logic_fixture",
                "Task has no materialized copy-visual logic fixture.",
            )
        ]

    fixture = _read_json(qa_path)
    slides = fixture.get("slides") if isinstance(fixture.get("slides"), list) else []
    if not slides:
        return [
            _fail(
                "copy_visual_logic_fixture",
                "Copy-visual fixture has no locked source slides.",
                evidence=[str(qa_path)],
            )
        ]

    plan = _build_eval_visual_direction(slides)
    pre_issues = validate_director_storyboard(
        plan,
        slide_count=len(slides),
        expected_slides=slides,
        expected_formats=_EVAL_FORMATS,
    )
    if pre_issues:
        return [
            _fail(
                "copy_visual_logic_fixture",
                "Copy-visual eval harness is not a valid physical-scene baseline.",
                evidence=pre_issues,
            )
        ]

    readability = _build_eval_frame_review(slides)
    baseline_issues = validate_frame_readability(
        readability,
        slide_count=len(slides),
        required_formats=_EVAL_FORMATS,
    )
    if baseline_issues:
        return [
            _fail(
                "copy_visual_logic_fixture",
                "Copy-visual eval harness is not a valid rendered-frame baseline.",
                evidence=baseline_issues,
            )
        ]

    defect = fixture.get("defect")
    if isinstance(defect, dict) and defect:
        try:
            target_slide = int(defect.get("slide") or 1)
            target = next(
                frame
                for frame in readability["frames"]
                if frame["slide"] == target_slide
                and frame["format"] == str(defect.get("format") or "instagram_post")
            )
        except (StopIteration, TypeError, ValueError):
            return [
                _fail(
                    "copy_visual_logic_fixture",
                    "Copy-visual defect targets an invalid frame.",
                    evidence=[str(defect)],
                )
            ]
        target["expected_silent_read"] = str(
            defect.get("expected_silent_read")
            or "The visible clothing action follows the locked order."
        )
        target["observed_image_first_read"] = str(
            defect.get("observed_image_first_read")
            or "The current clothing state visibly reverses the locked action order."
        )
        contradictions = defect.get("copy_visual_contradictions")
        target["copy_visual_contradictions"] = (
            contradictions
            if isinstance(contradictions, list)
            else ["The visible action contradicts the locked copy order."]
        )

    issues = validate_frame_readability(
        readability,
        slide_count=len(slides),
        required_formats=_EVAL_FORMATS,
    )
    contradiction_issues = [
        issue for issue in issues if "copy_visual_contradictions" in issue
    ]
    if contradiction_issues and len(issues) == len(contradiction_issues):
        return [
            _pass(
                "copy_visual_logic_fixture",
                "Rendered-frame QA is blocked only by the seeded copy-visual contradiction.",
                evidence=contradiction_issues,
            )
        ]
    return [
        _fail(
            "copy_visual_logic_fixture",
            "Copy-visual fixture was not isolated to its concrete visible contradiction.",
            evidence=[*issues, str(qa_path)],
        )
    ]


def check_scene_entity_integrity_fixture(task: EvalTask, root: Path) -> list[CheckResult]:
    qa_path = _fixture_file_from_overlay(task, root, "visual-qa.json")
    if qa_path is None or not qa_path.exists():
        return [
            _fail(
                "scene_entity_integrity_fixture",
                "Task has no materialized scene-entity visual QA fixture.",
            )
        ]

    payload = _read_json(qa_path)
    checks = payload.get("checks") if isinstance(payload.get("checks"), dict) else {}
    scene_check = checks.get("scene_entity_integrity")
    slide_count = payload.get("slide_count")
    if not isinstance(slide_count, int) or slide_count < 1:
        slide_count = 1
    issues = validate_scene_entity_integrity_check(scene_check, slide_count=slide_count)
    text = " ".join(issues).lower()
    detects_extra_people = (
        "expected 2 people but observed 4" in text
        and "background couple" in text
    )

    if detects_extra_people:
        return [
            _pass(
                "scene_entity_integrity_fixture",
                "The seeded duplicate-background-couple fixture is blocked by instance-level entity QA.",
                evidence=issues,
            )
        ]
    return [
        _fail(
            "scene_entity_integrity_fixture",
            "Scene-entity QA did not block the seeded extra background couple.",
            evidence=issues or [str(qa_path)],
        )
    ]


def check_hand_object_integrity_fixture(task: EvalTask, root: Path) -> list[CheckResult]:
    qa_path = _fixture_file_from_overlay(task, root, "visual-qa.json")
    if qa_path is None or not qa_path.exists():
        return [_fail("hand_object_integrity_fixture", "Task has no hand-object visual QA fixture.")]

    payload = _read_json(qa_path)
    checks = payload.get("checks") if isinstance(payload.get("checks"), dict) else {}
    anatomy = checks.get("anatomy_inventory")
    slide_count = payload.get("slide_count")
    if not isinstance(slide_count, int) or slide_count < 1:
        slide_count = 1
    issues = validate_anatomy_inventory_check(anatomy, slide_count=slide_count)
    text = " ".join(issues).lower()
    detects_both_failures = (
        "not required by the locked scene" in text
        and "unexplained edge entry" in text
        and "fails hand-object contact geometry" in text
        and "intersects or may intersect a solid object" in text
    )
    if detects_both_failures:
        return [
            _pass(
                "hand_object_integrity_fixture",
                "The seeded anonymous-door-hand and forearm-through-box failures are both blocked.",
                evidence=issues,
            )
        ]
    return [
        _fail(
            "hand_object_integrity_fixture",
            "Hand-object QA did not block both seeded AI-slop failures.",
            evidence=issues or [str(qa_path)],
        )
    ]


def check_whole_person_spatial_integrity_fixture(task: EvalTask, root: Path) -> list[CheckResult]:
    qa_path = _fixture_file_from_overlay(task, root, "visual-qa.json")
    if qa_path is None or not qa_path.exists():
        return [
            _fail(
                "whole_person_spatial_integrity_fixture",
                "Task has no whole-person spatial-topology fixture.",
            )
        ]

    payload = _read_json(qa_path)
    checks = payload.get("checks") if isinstance(payload.get("checks"), dict) else {}
    topology = checks.get("spatial_topology")
    slide_count = payload.get("slide_count")
    if not isinstance(slide_count, int) or slide_count < 1:
        slide_count = 1
    issues = validate_spatial_topology_check(topology, slide_count=slide_count)
    text = " ".join(issues).lower()
    detects_door_morph = (
        "silhouette is not fully traceable" in text
        and "expected in_front_of but observed touching" in text
        and "intersects or may intersect a solid object" in text
        and "morphs or merges into the environment" in text
        and "door edge enters zuv's torso" in text
    )
    if detects_door_morph:
        return [
            _pass(
                "whole_person_spatial_integrity_fixture",
                "The seeded Zuv-inside-door body/environment morph is blocked by production spatial QA.",
                evidence=issues,
            )
        ]
    return [
        _fail(
            "whole_person_spatial_integrity_fixture",
            "Spatial QA did not block the seeded body/door morph.",
            evidence=issues or [str(qa_path)],
        )
    ]


def check_autopublish_safety_fixture(task: EvalTask, root: Path) -> list[CheckResult]:
    del task
    status_path = root / "fixtures" / "git-status.txt"
    if not status_path.exists():
        return [_fail("autopublish_risky_paths", "Missing prepared fixtures/git-status.txt.")]

    paths = parse_changed_paths(status_path.read_text(encoding="utf-8"))
    risky = {block.path for block in find_risky_paths(paths)}
    expected_risky = {
        ".env.local",
        "identity_images/aachu-reference.png",
        "output/carousels/fixtures/demo/final/slide-01.png",
    }
    missing_risky = sorted(expected_risky - risky)
    results: list[CheckResult] = []
    if missing_risky:
        results.append(
            _fail(
                "autopublish_risky_paths",
                "Autopublish did not block every seeded risky path.",
                evidence=missing_risky,
            )
        )
    else:
        results.append(
            _pass(
                "autopublish_risky_paths",
                "Autopublish blocks the seeded env, identity, and generated-final paths.",
                evidence=sorted(risky),
            )
        )

    placeholder_findings = scan_secret_text(root, [".env.local"])
    with tempfile.TemporaryDirectory() as tmp:
        synthetic_root = Path(tmp)
        token = "sk-" + ("a" * 24)
        (synthetic_root / ".env.local").write_text(
            f"OPENAI_API_KEY={token}\n",
            encoding="utf-8",
        )
        synthetic_findings = scan_secret_text(synthetic_root, [".env.local"])

    if placeholder_findings:
        results.append(
            _fail(
                "autopublish_secret_scan",
                "Secret scanner flagged the safe placeholder fixture.",
                evidence=[
                    f"{finding.path}:{finding.line}:{finding.kind}"
                    for finding in placeholder_findings
                ],
            )
        )
    elif any(finding.kind == "openai_key" for finding in synthetic_findings):
        results.append(
            _pass(
                "autopublish_secret_scan",
                "Secret scanner ignores placeholders and catches a synthetic live-looking OpenAI key.",
                evidence=[
                    f"{finding.path}:{finding.line}:{finding.kind}"
                    for finding in synthetic_findings
                ],
            )
        )
    else:
        results.append(
            _fail(
                "autopublish_secret_scan",
                "Secret scanner did not catch a synthetic live-looking OpenAI key.",
            )
        )
    return results


def check_format_snapback_fixture(task: EvalTask, root: Path) -> list[CheckResult]:
    path = _fixture_file_from_overlay(task, root, "request-state.json")
    if path is None or not path.exists():
        return [_fail("format_snapback_fixture", "Task has no format snapback request-state fixture.")]
    payload = _read_json(path)
    latest = payload.get("latest_creator_request") if isinstance(payload.get("latest_creator_request"), dict) else {}
    requested = str(latest.get("requested_output") or latest.get("canvas") or "").strip()
    generated = payload.get("generated_outputs")
    generated_outputs = [item for item in generated if isinstance(item, dict)] if isinstance(generated, list) else []
    unrequested = [
        str(item.get("format") or item.get("canvas") or item.get("path") or "unknown")
        for item in generated_outputs
        if item.get("requested_by_latest_creator_message") is not True
    ]
    if requested and unrequested:
        return [
            _fail(
                "format_snapback_fixture",
                "Latest creator format correction was ignored by unrequested generated outputs.",
                evidence=[f"latest={requested}", *unrequested],
            )
        ]
    return [
        _pass(
            "format_snapback_fixture",
            "Generated outputs respect the latest creator format correction.",
            evidence=[f"latest={requested or 'unspecified'}"],
        )
    ]


def check_working_memory_pointer_fixture(task: EvalTask, root: Path) -> list[CheckResult]:
    working_path = root / "memory" / "working.md"
    semantic_path = root / "memory" / "semantic" / "engineering-workflow-preferences.md"
    working = _read_text(working_path).lower()
    semantic = _read_text(semantic_path).lower()
    seeded_phrase = "durable learning: after creator corrections"
    if seeded_phrase in working or "confidence:" in working:
        return [
            _fail(
                "working_memory_pointer_fixture",
                "memory/working.md contains durable learning instead of pointer-only session state.",
                evidence=[str(working_path)],
            )
        ]
    if "after creator corrections" not in semantic and "stale downstream artifacts" not in semantic:
        return [
            _fail(
                "working_memory_pointer_fixture",
                "Durable learning was removed from working memory but not preserved in semantic memory.",
                evidence=[str(semantic_path)],
            )
        ]
    return [
        _pass(
            "working_memory_pointer_fixture",
            "Working memory is pointer-only and durable correction learning is preserved semantically.",
            evidence=[str(working_path), str(semantic_path)],
        )
    ]


def check_creator_skill_routing_fixture(task: EvalTask, root: Path) -> list[CheckResult]:
    del task
    required = "config/skills/creator-skill-stack.md"
    surfaces = [
        root / "config" / "skill-systems.json",
        root / "config" / "agentic_context_manifest.json",
        root / "config" / "skills" / "carousel-jam-runtime-context.md",
        root / "config" / "skills" / "carousel-jam-autopilot.md",
        root / ".agents" / "skills" / "a-story-carousel-jam" / "SKILL.md",
    ]
    missing = [
        path.relative_to(root).as_posix()
        for path in surfaces
        if required not in _read_text(path)
    ]
    if missing:
        return [
            _fail(
                "creator_skill_routing_fixture",
                "Carousel jam routing surfaces do not all load creator-skill-stack.md.",
                evidence=missing,
            )
        ]
    return [
        _pass(
            "creator_skill_routing_fixture",
            "Carousel jam routing surfaces consistently load creator-skill-stack.md.",
            evidence=[path.relative_to(root).as_posix() for path in surfaces],
        )
    ]


def check_context_rule_truncation_fixture(task: EvalTask, root: Path) -> list[CheckResult]:
    del task
    try:
        pack = assemble_context_pack(root, profile="eval_tiny")
    except RequiredSectionTruncatedError as exc:
        return [
            _pass(
                "context_rule_truncation_fixture",
                "Required rule include fails loudly instead of truncating mid-rule.",
                evidence=[str(exc)],
            )
        ]
    except Exception as exc:  # noqa: BLE001 - eval report should expose fixture/setup issues.
        return [
            _fail(
                "context_rule_truncation_fixture",
                "Context truncation fixture could not be evaluated.",
                evidence=[str(exc)],
            )
        ]
    truncated_required = [
        section.id
        for section in pack.sections
        if section.required and section.truncated
    ]
    if truncated_required:
        return [
            _fail(
                "context_rule_truncation_fixture",
                "Required context sections were silently truncated.",
                evidence=truncated_required,
            )
        ]
    return [
        _fail(
            "context_rule_truncation_fixture",
            "Tiny truncation fixture rendered without proving a fail-loud rule include.",
            severity="major",
        )
    ]


def check_article_story_selling_fixture(task: EvalTask, root: Path) -> list[CheckResult]:
    article_dir = _fixture_dir_from_overlay(
        task,
        root,
        prefix=("output", "articles"),
        depth=4,
    )
    if article_dir is None or not article_dir.exists():
        return [_fail("article_story_selling_fixture", "Task has no article package fixture.")]
    manifest = _read_json(article_dir / "source-manifest.json")
    gates = _read_text(article_dir / "editorial-gates.md").lower()
    manifest_text = _stringify(manifest).lower()
    missing: list[str] = []
    if "layer_e_story_selling" not in manifest_text:
        missing.append("layer_e_story_selling")
    if "story_selling_contract" not in manifest_text:
        missing.append("story_selling_contract")
    if "story selling fit" not in gates and "story-selling fit" not in gates:
        missing.append("editorial-gates: story selling fit")
    if missing:
        return [
            _fail(
                "article_story_selling_fixture",
                "Article package omits Layer E / Story-Selling gate evidence.",
                evidence=missing,
            )
        ]
    return [
        _pass(
            "article_story_selling_fixture",
            "Article package carries Layer E story-selling contract and editorial gate evidence.",
            evidence=[str(article_dir)],
        )
    ]


def check_prepost_layer_e_fixture(task: EvalTask, root: Path) -> list[CheckResult]:
    path = _fixture_file_from_overlay(task, root, "prepost-config.json")
    if path is None or not path.exists():
        return [_fail("prepost_layer_e_fixture", "Task has no prepost config fixture.")]
    payload = _read_json(path)
    agents = payload.get("agents")
    agent_records = agents if isinstance(agents, list) else []
    missing = []
    for index, record in enumerate(agent_records, start=1):
        text = _stringify(record).lower()
        if "layer e" not in text and "layer_e" not in text and "romance-story-selling-engine" not in text:
            missing.append(str(record.get("name") or record.get("id") or f"agent-{index}"))
    if not agent_records:
        missing.append("agents")
    if missing:
        return [
            _fail(
                "prepost_layer_e_fixture",
                "Prepost agent config omits Layer E grounding for one or more agents.",
                evidence=missing,
            )
        ]
    return [
        _pass(
            "prepost_layer_e_fixture",
            "Prepost agent config is grounded in Layer E / story-selling behavior.",
            evidence=[str(path)],
        )
    ]


def check_visual_variety_shot_ladder_fixture(task: EvalTask, root: Path) -> list[CheckResult]:
    path = _fixture_file_from_overlay(task, root, "visual-plan-quality.json")
    if path is None or not path.exists():
        return [_fail("visual_variety_shot_ladder_fixture", "Task has no visual-plan-quality fixture.")]
    fixture = _read_json(path)
    slides = fixture.get("slides") if isinstance(fixture.get("slides"), list) else []
    if not slides:
        return [
            _fail(
                "visual_variety_shot_ladder_fixture",
                "Shot-ladder fixture has no source slides.",
                evidence=[str(path)],
            )
        ]

    plan = _build_eval_visual_direction(slides)
    baseline_issues = validate_director_storyboard(
        plan,
        slide_count=len(slides),
        expected_slides=slides,
        expected_formats=_EVAL_FORMATS,
    )
    if baseline_issues:
        return [
            _fail(
                "visual_variety_shot_ladder_fixture",
                "Shot-ladder eval harness is not a valid physical-scene baseline.",
                evidence=baseline_issues,
            )
        ]

    defect = fixture.get("defect")
    if isinstance(defect, dict) and defect:
        repeated_job = str(
            defect.get("narrative_job") or "repeat the same table interaction"
        )
        repeated_size = str(defect.get("shot_size") or "medium two-shot")
        for slide in plan["slides"]:
            slide["narrative_job"] = repeated_job
            slide["shot"]["size"] = repeated_size
        plan.pop("deliberate_shot_repetition_reason", None)

    issues = validate_director_storyboard(
        plan,
        slide_count=len(slides),
        expected_slides=slides,
        expected_formats=_EVAL_FORMATS,
    )
    target_issues = [
        issue
        for issue in issues
        if "repeats one narrative job" in issue
        or "repeats one shot size" in issue
    ]
    if (
        any("repeats one narrative job" in issue for issue in target_issues)
        and any("repeats one shot size" in issue for issue in target_issues)
        and len(issues) == len(target_issues)
    ):
        return [
            _pass(
                "visual_variety_shot_ladder_fixture",
                "The physical-scene preflight blocks repeated narrative job and shot size.",
                evidence=target_issues,
            )
        ]
    return [
        _fail(
            "visual_variety_shot_ladder_fixture",
            "Visual-variety fixture was not isolated to the repeated shot-ladder defect.",
            evidence=[*issues, str(path)],
        )
    ]


def check_small_brief_seed_fixture(task: EvalTask, root: Path) -> list[CheckResult]:
    path = _creator_visible_artifact(task, root)
    if not path.exists():
        return [
            _fail(
                "small_brief_seed_fixture",
                f"Missing creator-visible brief artifact: {path}",
                severity="critical",
            )
        ]

    text = path.read_text(encoding="utf-8", errors="ignore")
    lower = text.lower()
    missing: list[str] = []
    if "main kar lungi" not in lower:
        missing.append("exact seed phrase main kar lungi")
    if not any(token in lower for token in ("format:", "strongest format", "carousel", "reel", "post")):
        missing.append("explicit format choice")
    if not ("she" in lower and "he" in lower):
        missing.append("couple-specific she/he scene")
    if not any(
        token in lower
        for token in (
            "bag",
            "bottle",
            "charger",
            "cup",
            "door",
            "jar",
            "key",
            "phone",
            "stool",
            "switch",
            "tiffin",
        )
    ):
        missing.append("visible object or prop")
    if not any(token in lower for token in ("reaction", "knows", "not believe", "doesn't believe", "already")):
        missing.append("observable reaction")
    if not any(token in lower for token in ("payoff", "ends", "final", "turn", "reveals")):
        missing.append("relationship payoff")
    if any(token in lower for token in ("what concept do you want", "send me the concept", "bring a finished concept")):
        missing.append("agent must not ask creator to solve the concept")

    if missing:
        return [
            _fail(
                "small_brief_seed_fixture",
                "Creator brief does not yet satisfy the small-brief contract.",
                evidence=missing,
            )
        ]

    return [
        _pass(
            "small_brief_seed_fixture",
            "Creator brief preserves the seed, chooses a format, and grounds the route in scene proof.",
            evidence=[str(path)],
        )
    ]


def _creator_visible_artifact(task: EvalTask, root: Path) -> Path:
    for path in task.expected_files_changed:
        if path.endswith("creator-brief.md"):
            return root / path
    task_prefix = "-".join(task.id.split("-")[:2])
    return root / "output" / "evals" / task_prefix / "creator-brief.md"


def check_creator_visible_copy_artifact(task: EvalTask, root: Path) -> list[CheckResult]:
    return check_creator_visible_copy(_creator_visible_artifact(task, root))


TASK_SPECIFIC_CHECKERS: dict[str, Checker] = {
    "brandmark_top_right_rule": check_brandmark_top_right_rule,
    "carousel_doctor_fixture": check_carousel_doctor_fixture,
    "autopublish_safety_fixture": check_autopublish_safety_fixture,
    "creator_visible_copy": check_creator_visible_copy_artifact,
    "stale_artifact_fixture": check_stale_artifact_fixture,
    "identity_stop_gate_fixture": check_identity_stop_gate_fixture,
    "score_rejection_fixture": check_score_rejection_fixture,
    "home_cinematic_fixture": check_home_cinematic_fixture,
    "public_name_boundary_fixture": check_public_name_boundary_fixture,
    "copy_visual_logic_fixture": check_copy_visual_logic_fixture,
    "scene_entity_integrity_fixture": check_scene_entity_integrity_fixture,
    "hand_object_integrity_fixture": check_hand_object_integrity_fixture,
    "whole_person_spatial_integrity_fixture": check_whole_person_spatial_integrity_fixture,
    "format_snapback_fixture": check_format_snapback_fixture,
    "working_memory_pointer_fixture": check_working_memory_pointer_fixture,
    "creator_skill_routing_fixture": check_creator_skill_routing_fixture,
    "context_rule_truncation_fixture": check_context_rule_truncation_fixture,
    "article_story_selling_fixture": check_article_story_selling_fixture,
    "prepost_layer_e_fixture": check_prepost_layer_e_fixture,
    "visual_variety_shot_ladder_fixture": check_visual_variety_shot_ladder_fixture,
    "small_brief_seed_fixture": check_small_brief_seed_fixture,
}


def run_named_checkers(task: EvalTask, root: Path, checker_names: list[str]) -> list[CheckResult]:
    results: list[CheckResult] = []
    for name in checker_names:
        if name == "diff_guard":
            continue
        checker = TASK_SPECIFIC_CHECKERS.get(name)
        if checker is None:
            results.append(
                _fail(
                    "unknown_deterministic_checker",
                    f"No deterministic checker is registered for {name}.",
                    severity="major",
                )
            )
            continue
        results.extend(checker(task, root))
    return results
