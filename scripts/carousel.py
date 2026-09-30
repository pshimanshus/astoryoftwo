#!/usr/bin/env python3
"""Canonical Codex-first carousel lifecycle command.

Repository code prepares and binds work. Codex performs image generation and
pixel inspection outside this process, then passes the exact files and authored
QA back through this command. No renderer, API key, OCR, or backend integration
lives here.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Sequence


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from pipeline.stages.carousel_format_contract import locked_formats  # noqa: E402
from pipeline.stages.carousel_generation_state import (  # noqa: E402
    PUBLIC_STATUSES,
    archived_package_read_only_reason,
    canonical_state_and_next_action,
    require_writable_package,
)
from pipeline.stages.codex_native_carousel import create_codex_native_carousel  # noqa: E402


CLI_SCHEMA_VERSION = "carousel-cli/v1"
CANONICAL_STATES = frozenset(PUBLIC_STATUSES)
FAILED_EXIT_STATES = {"blocked", "proof_failed", "final_qa_failed"}


class CliInputError(ValueError):
    """Input error rendered through the versioned JSON response."""


class JsonArgumentParser(argparse.ArgumentParser):
    def error(self, message: str) -> None:
        raise CliInputError(message)


def _core_read(package_dir: Path) -> dict[str, Any]:
    """Return a read-only lifecycle view, including current input drift."""

    from pipeline.stages.carousel_generation_state import (
        STATE_SCHEMA_VERSION,
        read_generation_state,
    )

    state = read_generation_state(package_dir)
    archived_reason = archived_package_read_only_reason(package_dir)
    if archived_reason and state.get("schema_version") == STATE_SCHEMA_VERSION:
        return {
            **state,
            "status": "blocked",
            "next_action": "rebuild_with_active_style_profile",
            "reason": archived_reason,
        }
    from pipeline.agentic.carousel_state import derive_carousel_state
    from pipeline.agentic.workflow_doctor import inspect_carousel_package

    report = inspect_carousel_package(package_dir)
    if state.get("schema_version") == STATE_SCHEMA_VERSION:
        issue = next(
            (
                item
                for item in report.issues
                if item.severity == "blocker"
            ),
            None,
        )
        if issue is None:
            return state
        derived = derive_carousel_state(package_dir, report=report)
        failed_status = (
            derived.name
            if derived.name in FAILED_EXIT_STATES
            else "blocked"
        )
        return {
            **state,
            "status": failed_status,
            "next_action": issue.next_action or "repair_current_failure",
            "reason": issue.message,
        }
    derived = derive_carousel_state(package_dir, report=report)
    result = {
        **state,
        "status": derived.name,
        "next_action": derived.next_action,
    }
    if derived.blocked and report.issues:
        result["reason"] = report.issues[0].message
    return result


def _core_reconcile(package_dir: Path) -> dict[str, Any]:
    """Apply lifecycle invalidation for commands that explicitly mutate work."""

    from pipeline.stages.codex_builtin_image_generation import reconcile_package_state

    return reconcile_package_state(package_dir)


def _core_prepare(
    package_dir: Path,
    *,
    proof_slide: int | None,
    formats: list[str] | None,
) -> dict[str, Any]:
    # New v3 packages must pass concept lock before any proof prompts are
    # prepared. Archived/legacy packages remain readable and are not silently
    # migrated into the new gate.
    from pipeline.stages.carousel_generation_state import read_generation_state
    from pipeline.stages.carousel_intelligence import require_concept_gate

    generation_state = read_generation_state(package_dir)
    if generation_state.get("schema_version") == "carousel-generation-state/v3" and (
        (package_dir / ".concept-lock-required").is_file()
        or (package_dir / "carousel-intelligence.json").is_file()
    ):
        require_concept_gate(package_dir)
    from pipeline.stages.codex_builtin_image_generation import (
        prepare_codex_builtin_image_generation,
    )

    return prepare_codex_builtin_image_generation(
        package_dir,
        proof_slide=proof_slide,
        formats=formats,
    )


def _core_ingest(
    package_dir: Path,
    generated_paths_by_format: dict[str, list[Path]],
    *,
    proof_slide: int | None,
    tool_reported_model: str | None,
    feedback_id: str | None,
) -> dict[str, Any]:
    from pipeline.stages.codex_builtin_image_generation import ingest_generated_outputs

    return ingest_generated_outputs(
        package_dir,
        generated_paths_by_format,
        proof_slide=proof_slide,
        tool_reported_model=tool_reported_model,
        feedback_id=feedback_id,
    )


def _core_review(package_dir: Path, qa_path: Path) -> dict[str, Any]:
    from pipeline.stages.codex_builtin_image_generation import (
        finalize_codex_builtin_outputs,
        review_quarantined_outputs,
    )

    require_writable_package(package_dir)
    state = _core_reconcile(package_dir)
    if state.get("schema_version") != "carousel-generation-state/v3":
        raise CliInputError(
            "Archived v2 carousel packages are read-only; create a new v3 package."
        )
    status = _canonical_state(state)
    if status == "proof_qa_required":
        target = package_dir / "proof-qa.json"
    elif status == "final_qa_required":
        target = package_dir / "visual-qa.json"
    else:
        raise CliInputError("No current proof or final candidate is awaiting pixel QA")
    authored = json.loads(qa_path.read_text(encoding="utf-8"))
    if not isinstance(authored, dict):
        raise CliInputError("QA input must contain one JSON object")
    temporary = target.with_name(target.name + ".tmp")
    temporary.write_text(
        json.dumps(authored, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    temporary.replace(target)
    reviewed = review_quarantined_outputs(package_dir)
    if (
        reviewed.get("status") == "final_qa_required"
        and reviewed.get("next_action") == "finalize_deck"
    ):
        return finalize_codex_builtin_outputs(package_dir)
    return reviewed


def _core_approve(
    package_dir: Path,
    approved_by: str,
    proof_sha256: str,
) -> dict[str, Any]:
    from pipeline.stages.codex_builtin_image_generation import (
        approve_proof,
        prepare_codex_builtin_image_generation,
    )

    approved = approve_proof(
        package_dir,
        approved_by=approved_by,
        proof_sha256=proof_sha256,
    )
    if approved.get("status") == "batch_ready":
        return prepare_codex_builtin_image_generation(package_dir)
    return approved


def _core_finalize(package_dir: Path) -> dict[str, Any]:
    from pipeline.stages.codex_builtin_image_generation import finalize_codex_builtin_outputs

    return finalize_codex_builtin_outputs(package_dir)


def _core_concept_check(package_dir: Path) -> dict[str, Any]:
    from pipeline.stages.carousel_intelligence import analyze_and_write

    report = analyze_and_write(package_dir, root=ROOT)
    gate = report.get("concept_gate", {})
    status = "handoff_ready" if gate.get("status") == "passed" else "blocked"
    return {
        "status": status,
        "next_action": "prepare_proof" if status == "handoff_ready" else "repair_carousel_intelligence",
        "selected_slides": [],
        "selected_formats": [],
        "concept_check_only": True,
        "reason": "; ".join(gate.get("repairs", [])) if status == "blocked" else "Concept gate passed.",
        "intelligence": report,
    }


def _core_dry_run(output_dir: Path | None = None) -> dict[str, Any]:
    from pipeline.stages.carousel_intelligence import write_dry_run_report

    report = write_dry_run_report(ROOT, output_dir=output_dir)
    return {
        "status": "draft",
        "next_action": "inspect_carousel_intelligence_dry_run",
        "selected_slides": [],
        "selected_formats": [],
        "dry_run": report,
    }


def _core_calibrate(output_dir: Path | None = None) -> dict[str, Any]:
    from pipeline.stages.carousel_intelligence import write_calibration_report

    report = write_calibration_report(ROOT, output_dir=output_dir)
    return {
        "status": "draft",
        "next_action": "inspect_carousel_intelligence_calibration",
        "selected_slides": [],
        "selected_formats": [],
        "calibration": report,
    }


def _canonical_state(state: dict[str, Any]) -> str:
    value, _ = canonical_state_and_next_action(state)
    return value if value in CANONICAL_STATES else "blocked"


def _response(package_dir: Path | None, state: dict[str, Any]) -> dict[str, Any]:
    package = package_dir.expanduser().resolve() if package_dir is not None else None
    status, canonical_next_action = canonical_state_and_next_action(state)
    if status not in CANONICAL_STATES:
        status = "blocked"
    selected_formats = state.get("selected_formats")
    if not isinstance(selected_formats, list) and package is not None and package.is_dir():
        try:
            selected_formats = list(locked_formats(package))
        except (OSError, ValueError):
            selected_formats = []
    reason = str(state.get("reason") or "").strip()
    payload: dict[str, Any] = {
        "schema_version": CLI_SCHEMA_VERSION,
        "package_dir": str(package) if package is not None else "",
        "state": status,
        "next_action": canonical_next_action,
        "selected_slides": [int(value) for value in state.get("selected_slides") or []],
        "selected_formats": [str(value) for value in selected_formats or []],
    }
    if reason:
        payload["reason"] = reason
    feedback_id = str(state.get("feedback_id") or "").strip()
    if feedback_id:
        payload["feedback_id"] = feedback_id
    if isinstance(state.get("feedback"), dict):
        payload["feedback"] = state["feedback"]
    if isinstance(state.get("feedback_evaluation"), dict):
        payload["feedback_evaluation"] = state["feedback_evaluation"]
    if isinstance(state.get("feedback_status_report"), dict):
        payload["feedback_status"] = state["feedback_status_report"]
    if isinstance(state.get("intelligence"), dict):
        payload["intelligence"] = state["intelligence"]
    if isinstance(state.get("dry_run"), dict):
        payload["dry_run"] = state["dry_run"]
    if isinstance(state.get("calibration"), dict):
        payload["calibration"] = state["calibration"]
    for key in ("patterns", "sequence", "publication", "snapshot", "results"):
        if key in state:
            payload[key] = state[key]
    if package is not None and status == "handoff_ready" and not state.get("concept_check_only"):
        from pipeline.stages.codex_builtin_image_generation import (
            build_compiled_prompt_handoff,
        )

        payload["handoff"] = build_compiled_prompt_handoff(
            package,
            slide_numbers=payload["selected_slides"],
            output_formats=payload["selected_formats"],
        )
    if package is not None and status in {"proof_qa_required", "final_qa_required"}:
        from pipeline.stages.codex_builtin_image_generation import (
            build_generation_review_targets,
        )

        payload["review_targets"] = build_generation_review_targets(package, state=state)
    if package is not None and status == "publish_ready":
        from pipeline.stages.codex_builtin_image_generation import build_final_inventory

        final_images = build_final_inventory(package, state=state)
        if final_images is not None:
            payload["final_images"] = final_images
    if status == "awaiting_creator_proof_approval" and package is not None:
        from pipeline.stages.codex_builtin_image_generation import (
            current_proof_binding_sha256,
        )

        payload["proof_sha256"] = current_proof_binding_sha256(package, state=state)
    return payload


def _emit(package_dir: Path | None, state: dict[str, Any]) -> int:
    payload = _response(package_dir, state)
    print(json.dumps(payload, ensure_ascii=False, sort_keys=True))
    feedback_failed = (payload.get("feedback_evaluation") or {}).get("status") == "failed"
    feedback_blocked = (payload.get("feedback_status") or {}).get("status") == "blocked"
    return 2 if payload["state"] in FAILED_EXIT_STATES or feedback_failed or feedback_blocked else 0


def _read_story(args: argparse.Namespace) -> str:
    if args.story_file:
        path = Path(args.story_file).expanduser()
        if not path.is_file():
            raise CliInputError(f"Story file not found: {path}")
        return path.read_text(encoding="utf-8")
    return str(args.story or "")


def _read_feedback(args: argparse.Namespace) -> str:
    if args.text_file:
        path = Path(args.text_file).expanduser()
        if not path.is_file() or path.is_symlink():
            raise CliInputError(f"Feedback file not found or unsafe: {path}")
        try:
            return path.read_bytes().decode("utf-8")
        except UnicodeDecodeError as exc:
            raise CliInputError("Feedback file must be UTF-8 text") from exc
    return str(args.text or "")


def _read_repair_operations(values: list[str]) -> list[dict[str, Any]]:
    operations: list[dict[str, Any]] = []
    for value in values:
        source = str(value)
        candidate = Path(source).expanduser()
        if source.startswith("@"):
            candidate = Path(source[1:]).expanduser()
            if not candidate.is_file() or candidate.is_symlink():
                raise CliInputError(f"Repair operation file not found or unsafe: {candidate}")
            source = candidate.read_text(encoding="utf-8")
        try:
            payload = json.loads(source)
        except json.JSONDecodeError as exc:
            raise CliInputError("--repair-json must be a JSON object or @UTF-8-file") from exc
        if not isinstance(payload, dict):
            raise CliInputError("--repair-json must contain one JSON object")
        operations.append(payload)
    return operations


def _feedback_workspace_root(package_dir: Path) -> Path:
    package = package_dir.resolve(strict=True)
    try:
        package.relative_to(ROOT.resolve(strict=True))
        return ROOT
    except ValueError:
        pass
    for ancestor in package.parents:
        try:
            relative = package.relative_to(ancestor)
        except ValueError:
            continue
        if relative.parts[:2] == ("output", "carousels"):
            return ancestor
    return package.parent


def _core_feedback(package_dir: Path, args: argparse.Namespace) -> dict[str, Any]:
    from pipeline.stages.carousel_generation_state import (
        STATE_SCHEMA_VERSION,
        read_generation_state,
    )
    from pipeline.stages.carousel_visual_storytelling import record_creator_feedback

    record = record_creator_feedback(
        package_dir,
        workspace_root=_feedback_workspace_root(package_dir),
        user_instruction_exact=_read_feedback(args),
        kind=args.kind,
        scope=args.scope,
        slide_numbers=args.slides,
        diagnosis=args.diagnosis,
        primary_diagnosis=args.primary_diagnosis,
        secondary_diagnoses=args.secondary_diagnosis,
        root_cause=args.root_cause,
        desired_behavior=args.desired_behavior,
        must_change=args.must_change,
        must_preserve=args.must_preserve,
        affected_artifacts=args.affected_artifact,
        repair_operations=_read_repair_operations(args.repair_json),
        verification_assertions=_read_repair_operations(args.assertion_json),
        asset_sha256=args.asset_sha,
        eval_waiver_reason=args.eval_waiver,
        generation_effect=args.generation_effect,
        supersedes_feedback_id=args.supersedes_feedback_id,
    )
    state_path = package_dir / "generation-state.json"
    state_payload: dict[str, Any] = {}
    if state_path.is_file() and not state_path.is_symlink():
        loaded = json.loads(state_path.read_text(encoding="utf-8"))
        if isinstance(loaded, dict):
            state_payload = loaded
    if state_payload.get("schema_version") == STATE_SCHEMA_VERSION:
        state = _core_reconcile(package_dir)
    else:
        # Legacy packages may save feedback metadata, but feedback capture must
        # never initialize or migrate their archived generation lifecycle.
        state = read_generation_state(package_dir)
        if not state:
            state = {
                "status": "draft",
                "next_action": "inspect_archived_package",
                "selected_slides": [],
                "selected_formats": [],
            }
    return {**state, "feedback_id": record["feedback_id"], "feedback": record}


def _core_revise(package_dir: Path, args: argparse.Namespace) -> dict[str, Any]:
    from pipeline.stages.carousel_visual_storytelling import apply_creator_feedback_revision

    if (args.assertion_json or args.must_change is not None or args.must_preserve is not None
            or args.primary_diagnosis or args.repair_json is not None
            or args.affected_artifact is not None or args.eval_waiver is not None):
        from pipeline.stages.carousel_visual_storytelling import revise_creator_feedback_assertions

        revise_creator_feedback_assertions(
            package_dir, workspace_root=_feedback_workspace_root(package_dir),
            feedback_id=str(args.feedback_id),
            verification_assertions=_read_repair_operations(args.assertion_json) if args.assertion_json else None,
            diagnosis=args.primary_diagnosis, must_change=args.must_change, must_preserve=args.must_preserve,
            repair_operations=_read_repair_operations(args.repair_json) if args.repair_json is not None else None,
            affected_artifacts=args.affected_artifact, eval_waiver_reason=args.eval_waiver,
            revised_by=args.revised_by, reason=args.reason or "",
        )

    result = apply_creator_feedback_revision(
        package_dir,
        workspace_root=_feedback_workspace_root(package_dir),
        feedback_id=str(args.feedback_id),
    )
    state = result.get("generation_state") or _core_reconcile(package_dir)
    return {
        **state,
        "feedback_id": str(args.feedback_id),
        "feedback": result["feedback"],
        "feedback_evaluation": result["evaluation"],
    }


def _core_feedback_status(package_dir: Path, args: argparse.Namespace) -> dict[str, Any]:
    from pipeline.stages.carousel_visual_storytelling import creator_feedback_status

    report = creator_feedback_status(
        package_dir,
        workspace_root=_feedback_workspace_root(package_dir),
        feedback_id=args.feedback_id,
    )
    state = _core_read(package_dir) or {
        "status": "draft", "next_action": "inspect_feedback", "selected_slides": [], "selected_formats": []
    }
    return {**state, "feedback_status_report": report}


def _generated_paths(args: argparse.Namespace) -> dict[str, list[Path]]:
    supplied = {
        "instagram_post": args.instagram_post,
        "reels_stories": args.reels_stories,
        "square": args.square,
    }
    return {
        output_format: [Path(value).expanduser() for value in values]
        for output_format, values in supplied.items()
        if values
    }


def _run_create(args: argparse.Namespace) -> tuple[Path, dict[str, Any]]:
    story = _read_story(args)
    if not story.strip():
        raise CliInputError("create requires --story or --story-file with non-empty text")
    should_prepare = args.prepare_proof or args.proof_slide is not None
    if should_prepare and not args.creative_brief:
        raise CliInputError("--prepare-proof requires a locked --creative-brief")
    if args.successor_of and not args.creative_brief:
        raise CliInputError(
            "create --successor-of requires a real --creative-brief with non-empty slides"
        )
    package_dir = create_codex_native_carousel(
        story=story,
        image_paths=args.story_images,
        identity_image_paths=args.identity_images,
        title=args.title,
        slide_count=args.slide_count,
        output_root=args.output_root,
        creative_baseline_path=args.creative_brief,
        requested_formats=args.formats,
        successor_of=args.successor_of,
    )
    if args.creative_brief:
        from pipeline.stages.carousel_sequence import package_sequence_inputs, SEQUENCE_CONTRACT
        context, _ = package_sequence_inputs(package_dir)
        context["sequence_contract"] = SEQUENCE_CONTRACT
        (package_dir / "creative-context.json").write_text(json.dumps(context, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        if "story_plan" not in context:
            return package_dir, {
                "status": "blocked", "next_action": "define_story_plan",
                "reason": "A new locked brief needs story_plan and per-slide beat_delta/copy_image_relation before proof preparation.",
                "selected_slides": [], "selected_formats": [],
            }
    intelligence_state = None
    if args.creative_brief:
        from pipeline.stages.carousel_intelligence import carousel_gate_policy

        gate_policy = carousel_gate_policy(ROOT)
        if not gate_policy.get("enabled") and gate_policy.get("reason") != "policy_disabled":
            return package_dir, {
                "status": "blocked",
                "next_action": "repair_carousel_intelligence_gate_policy",
                "selected_slides": [],
                "selected_formats": [],
                "reason": f"Carousel intelligence gate policy failed closed: {gate_policy.get('reason')}.",
                "gate_policy": gate_policy,
            }
        if gate_policy.get("enabled"):
            (package_dir / ".concept-lock-required").write_text("carousel-intelligence/v1\n", encoding="utf-8")
            intelligence_state = _core_concept_check(package_dir)
            if intelligence_state.get("status") == "blocked":
                intelligence_state["gate_policy"] = gate_policy
                return package_dir, intelligence_state
    if should_prepare:
        prepared = _core_prepare(
            package_dir,
            proof_slide=args.proof_slide,
            formats=args.formats,
        )
        if intelligence_state and isinstance(intelligence_state.get("intelligence"), dict):
            prepared["intelligence"] = intelligence_state["intelligence"]
        return package_dir, prepared
    reconciled = _core_reconcile(package_dir)
    if intelligence_state and isinstance(intelligence_state.get("intelligence"), dict):
        reconciled["intelligence"] = intelligence_state["intelligence"]
    return package_dir, reconciled


def _run(args: argparse.Namespace) -> tuple[Path | None, dict[str, Any]]:
    if args.command == "create":
        return _run_create(args)
    if args.command == "dry-run":
        return None, _core_dry_run(args.output_dir)
    if args.command == "calibrate":
        return None, _core_calibrate(args.output_dir)
    if args.command == "patterns":
        from pipeline.stages.carousel_patterns import find_patterns
        return None, {"status": "draft", "next_action": "apply_relevant_evidence_after_first_draft",
                      "patterns": find_patterns(ROOT, args.query, limit=args.limit)}
    if args.command in {"insights", "results"}:
        from pipeline.stages.carousel_results import record_snapshot, review_results
        if args.command == "insights":
            record = json.loads(Path(args.record).read_text(encoding="utf-8"))
            return None, {"status": "draft", "next_action": "review_dated_results",
                          "snapshot": record_snapshot(ROOT, args.shortcode, record)}
        result = review_results(ROOT, args.shortcode)
        from pipeline.agentic.memory_index import build_memory_index
        build_memory_index(ROOT)
        return None, {"status": "draft", "next_action": "choose_next_hypothesis", "results": result}
    package_dir = Path(args.package_dir).expanduser()
    if not package_dir.is_dir():
        raise CliInputError(f"Carousel package not found: {package_dir}")
    if args.command == "publication":
        from pipeline.stages.carousel_results import record_publication
        record = json.loads(Path(args.record).read_text(encoding="utf-8"))
        return None, {"status": "draft", "next_action": "collect_dated_insights",
                      "publication": record_publication(ROOT, package_dir, record)}
    if args.command == "sequence-check":
        from pipeline.stages.carousel_sequence import package_sequence_inputs, sequence_input_fingerprint, sequence_plan_issues
        context, slides = package_sequence_inputs(package_dir)
        issues = sequence_plan_issues(context, slides)
        return package_dir, {"status": "blocked" if issues else "draft",
                             "next_action": "repair_sequence_inputs" if issues else "review_sequence_pixels",
                             "reason": "; ".join(issues),
                             "sequence": {"source_sha256": sequence_input_fingerprint(context, slides),
                                          "story_plan": context.get("story_plan"), "slides": slides,
                                          "pixel_review_status": "not_run"}}
    if args.command == "feedback":
        return package_dir, _core_feedback(package_dir, args)
    if args.command == "revise":
        return package_dir, _core_revise(package_dir, args)
    if args.command == "feedback-status":
        return package_dir, _core_feedback_status(package_dir, args)
    if args.command == "prepare":
        return package_dir, _core_prepare(
            package_dir,
            proof_slide=args.proof_slide,
            formats=args.formats,
        )
    if args.command == "concept-check":
        return package_dir, _core_concept_check(package_dir)
    if args.command == "ingest":
        paths = _generated_paths(args)
        if not paths:
            raise CliInputError("ingest requires at least one generated image path")
        return package_dir, _core_ingest(
            package_dir,
            paths,
            proof_slide=args.proof_slide,
            tool_reported_model=args.model,
            feedback_id=args.feedback_id,
        )
    if args.command == "review":
        qa_path = Path(args.qa).expanduser()
        if not qa_path.is_file():
            raise CliInputError(f"QA file not found: {qa_path}")
        return package_dir, _core_review(package_dir, qa_path)
    if args.command == "approve":
        approved_by = str(args.approved_by or "").strip()
        if not approved_by:
            raise CliInputError("approve requires a non-empty --approved-by")
        return package_dir, _core_approve(
            package_dir,
            approved_by,
            str(args.proof_sha256),
        )
    if args.command == "status":
        return package_dir, _core_read(package_dir)
    if args.command == "finalize":
        return package_dir, _core_finalize(package_dir)
    raise CliInputError(f"Unsupported command: {args.command}")


def build_parser() -> argparse.ArgumentParser:
    parser = JsonArgumentParser(description="Run the Codex-first carousel lifecycle.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    create = subparsers.add_parser("create", help="Create the minimal package.")
    story_source = create.add_mutually_exclusive_group(required=True)
    story_source.add_argument("--story")
    story_source.add_argument("--story-file")
    create.add_argument("--title")
    create.add_argument(
        "--slide-count",
        type=int,
        default=None,
        help="Optional explicit cap; omitted preserves every supplied story beat.",
    )
    create.add_argument("--story-image", "--image", dest="story_images", action="append", default=[])
    create.add_argument("--identity-image", dest="identity_images", action="append", default=None)
    create.add_argument("--creative-brief", "--creative-brief-file", dest="creative_brief")
    create.add_argument(
        "--successor-of",
        type=Path,
        help="Adopt unresolved feedback from one archived/read-only v2 package.",
    )
    create.add_argument("--output-root", type=Path, default=Path("output") / "carousels")
    create.add_argument("--prepare-proof", action="store_true")
    create.add_argument("--proof-slide", type=int)
    create.add_argument(
        "--format",
        dest="formats",
        choices=("instagram_post", "reels_stories", "square"),
        action="append",
        default=None,
    )

    feedback = subparsers.add_parser(
        "feedback",
        help="Record creator feedback and link it to the existing learning loop.",
    )
    feedback.add_argument("package_dir")
    feedback_text = feedback.add_mutually_exclusive_group(required=True)
    feedback_text.add_argument("--text")
    feedback_text.add_argument("--text-file")
    feedback.add_argument(
        "--kind",
        default="correction",
        choices=("correction", "rejection", "approval", "preference", "lock", "observation"),
    )
    feedback.add_argument(
        "--scope",
        required=True,
        choices=("workflow", "package", "slide", "asset", "copy", "global"),
    )
    feedback.add_argument("--slide", dest="slides", type=int, action="append", default=[])
    feedback.add_argument("--diagnosis")
    feedback.add_argument("--primary-diagnosis")
    feedback.add_argument("--secondary-diagnosis", action="append", default=[])
    feedback.add_argument("--root-cause")
    feedback.add_argument("--desired-behavior")
    feedback.add_argument("--must-change", action="append", default=[])
    feedback.add_argument("--must-preserve", action="append", default=[])
    feedback.add_argument("--affected-artifact", action="append", default=[])
    feedback.add_argument(
        "--repair-json",
        action="append",
        default=[],
        help='JSON object (or @file) with artifact, json_pointer, and value.',
    )
    feedback.add_argument("--asset-sha")
    feedback.add_argument("--assertion-json", action="append", default=[],
                          help="Verification object or @file: artifact, json_pointer, operator, value.")
    feedback.add_argument("--eval-waiver")
    feedback.add_argument(
        "--generation-effect",
        choices=("none", "slide_local", "shared"),
    )
    feedback.add_argument("--supersedes-feedback-id")

    revise = subparsers.add_parser(
        "revise",
        help="Apply a captured correction to the same package and run its regression eval.",
    )
    revise.add_argument("package_dir")
    revise.add_argument("--feedback-id", required=True)
    revise.add_argument("--assertion-json", action="append", default=[])
    revise.add_argument("--revised-by", default="codex")
    revise.add_argument("--reason", help="Required when revising the verification contract.")
    revise.add_argument("--must-change", action="append")
    revise.add_argument("--must-preserve", action="append")
    revise.add_argument("--primary-diagnosis")
    revise.add_argument("--repair-json", action="append")
    revise.add_argument("--affected-artifact", action="append")
    revise.add_argument("--eval-waiver")

    feedback_status = subparsers.add_parser(
        "feedback-status",
        help="Report correction lifecycle and linked eval evidence.",
    )
    feedback_status.add_argument("package_dir")
    feedback_status.add_argument("--feedback-id")

    prepare = subparsers.add_parser("prepare", help="Compile proof or remaining-slide prompts.")
    prepare.add_argument("package_dir")
    prepare.add_argument("--proof-slide", type=int)
    prepare.add_argument(
        "--format",
        dest="formats",
        choices=("instagram_post", "reels_stories", "square"),
        action="append",
        default=None,
    )

    ingest = subparsers.add_parser("ingest", help="Quarantine exact Codex imagegen outputs.")
    ingest.add_argument("package_dir")
    ingest.add_argument("--instagram-post", action="append", default=[])
    ingest.add_argument("--reels-stories", action="append", default=[])
    ingest.add_argument("--square", action="append", default=[])
    ingest.add_argument("--proof-slide", type=int)
    ingest.add_argument(
        "--model",
        help="Tool-reported ImageGen model, when the built-in tool exposes it.",
    )
    ingest.add_argument(
        "--feedback-id",
        help="Correction event that triggered this edit attempt.",
    )

    review = subparsers.add_parser("review", help="Validate and bind externally authored pixel QA.")
    review.add_argument("package_dir")
    review.add_argument("--qa", required=True)

    approve = subparsers.add_parser("approve", help="Embed hash-bound creator proof approval.")
    approve.add_argument("package_dir")
    approve.add_argument("--approved-by", default="creator")
    approve.add_argument(
        "--proof-sha256",
        required=True,
        help="Exact proof binding returned by review/status; stale values are rejected.",
    )

    status = subparsers.add_parser("status", help="Return canonical state and next action.")
    status.add_argument("package_dir")

    finalize = subparsers.add_parser("finalize", help="Audit hidden candidates and promote atomically.")
    finalize.add_argument("package_dir")
    concept_check = subparsers.add_parser(
        "concept-check",
        help="Run carousel intelligence and the concept-lock gate.",
    )
    concept_check.add_argument("package_dir")
    dry_run = subparsers.add_parser(
        "dry-run",
        help="Calibrate the concept gate against the verified 27-carousel seed.",
    )
    dry_run.add_argument("--output-dir", type=Path)
    calibrate = subparsers.add_parser(
        "calibrate",
        help="Write the per-carousel evidence-mapping calibration table.",
    )
    calibrate.add_argument("--output-dir", type=Path)
    patterns = subparsers.add_parser("patterns", help="Recall reviewed mechanisms and counterexamples after the first draft.")
    patterns.add_argument("--query", required=True)
    patterns.add_argument("--limit", type=int, default=2)
    sequence = subparsers.add_parser("sequence-check", help="Read current story/beat inputs and their review fingerprint; never certifies pixels.")
    sequence.add_argument("package_dir")
    publication = subparsers.add_parser("publication", help="Link a finalized package to an already confirmed published post; does not publish.")
    publication.add_argument("package_dir")
    publication.add_argument("--record", required=True, help="JSON publication record.")
    insights = subparsers.add_parser("insights", help="Record one dated native-metric observation without overwriting history.")
    insights.add_argument("shortcode")
    insights.add_argument("--record", required=True, help="JSON Insights observation.")
    results = subparsers.add_parser("results", help="Review observed results and index research without changing policy.")
    results.add_argument("shortcode")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    package_hint: Path | None = None
    try:
        args = build_parser().parse_args(argv)
        raw_package = getattr(args, "package_dir", None)
        package_hint = Path(raw_package).expanduser() if raw_package else None
        package_dir, state = _run(args)
        return _emit(package_dir, state)
    except (CliInputError, ImportError, OSError, json.JSONDecodeError, ValueError) as exc:
        return _emit(
            package_hint,
            {
                "status": "blocked",
                "next_action": "repair_inputs",
                "selected_slides": [],
                "selected_formats": [],
                "reason": str(exc),
            },
        )


if __name__ == "__main__":
    raise SystemExit(main())
