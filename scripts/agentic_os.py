#!/usr/bin/env python3
"""Agentic OS control-plane CLI."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from pipeline.agentic.context_loader import assemble_context_pack, render_context_pack  # noqa: E402
from pipeline.agentic.carousel_state import derive_carousel_state  # noqa: E402
from pipeline.agentic.learning_loop import (  # noqa: E402
    apply_learning_proposal,
    approve_learning_proposal,
    capture_hypothesis,
    capture_learning_event,
    create_learning_proposal,
    decline_learning_proposal,
    evaluate_learning_proposal_review,
    learning_debt_records,
    list_hypotheses,
    resolve_hypothesis,
)
from pipeline.agentic.knowledge_workflow import run_knowledge_workflow  # noqa: E402
from pipeline.agentic.memory_index import build_memory_index, search_memory  # noqa: E402
from pipeline.agentic.recall import build_recall_bundle, render_recall_bundle  # noqa: E402
from pipeline.agentic.skill_eval import evaluate_learning_proposal  # noqa: E402
from pipeline.agentic.skill_registry import discover_skill_records, load_skill_systems, resolve_skill_system  # noqa: E402
from pipeline.agentic.skill_usage import record_skill_run, summarize_skill_usage  # noqa: E402
from pipeline.agentic.validator_registry import run_required_validators  # noqa: E402
from pipeline.agentic.workflow_doctor import inspect_carousel_package  # noqa: E402


def print_json(data: object) -> None:
    if hasattr(data, "model_dump"):
        data = data.model_dump()
    print(json.dumps(data, indent=2, ensure_ascii=False))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workspace-root", type=Path, default=ROOT)
    sub = parser.add_subparsers(dest="command", required=True)

    context = sub.add_parser("context")
    context.add_argument("--profile")
    context.add_argument("--render", action="store_true")

    sub.add_parser("registry")
    index = sub.add_parser("index")
    index.add_argument("--index-path", type=Path)
    index.add_argument("--backend", choices=["fts5", "qmd", "sentence_transformers"], default="fts5")
    index_memory = sub.add_parser("index-memory")
    index_memory.add_argument("--index-path", type=Path)
    index_memory.add_argument("--backend", choices=["fts5", "qmd", "sentence_transformers"], default="fts5")

    search = sub.add_parser("search")
    search.add_argument("query")
    search.add_argument("--limit", type=int, default=8)
    search.add_argument("--backend", choices=["fts5", "qmd", "sentence_transformers", "auto"], default="fts5")

    recall = sub.add_parser("recall")
    recall.add_argument("query")
    recall.add_argument("--profile")
    recall.add_argument("--json", action="store_true")
    recall.add_argument("--backend", choices=["fts5", "qmd", "sentence_transformers", "auto"], default="fts5")

    system = sub.add_parser("system")
    system.add_argument("name")
    skill_system = sub.add_parser("skill-system")
    skill_system.add_argument("name")
    sub.add_parser("skill-usage")
    record_skill = sub.add_parser("record-skill-run")
    record_skill.add_argument("skill_name")
    record_skill.add_argument("--outcome", required=True, choices=["pass", "fail", "blocked"])
    record_skill.add_argument("--note", default="")

    hypothesis = sub.add_parser("capture-hypothesis")
    hypothesis.add_argument("--source", required=True)
    hypothesis.add_argument("--hypothesis", required=True)
    hypothesis.add_argument("--success-signal", required=True)
    hypothesis.add_argument("--falsifier", required=True)
    hypothesis.add_argument("--evidence", action="append", default=[])

    hypotheses = sub.add_parser("hypotheses")
    hypotheses.add_argument("--status", default="open")
    hypotheses.add_argument("--limit", type=int, default=20)

    resolve_hypothesis_parser = sub.add_parser("resolve-hypothesis")
    resolve_hypothesis_parser.add_argument("hypothesis_id")
    resolve_hypothesis_parser.add_argument(
        "--outcome",
        required=True,
        choices=["supported", "refuted", "inconclusive"],
    )
    resolve_hypothesis_parser.add_argument("--result-summary", required=True)
    resolve_hypothesis_parser.add_argument("--evidence", action="append", default=[])

    event = sub.add_parser("capture-learning")
    event.add_argument("--source", required=True)
    event.add_argument("--summary", required=True)
    event.add_argument("--evidence", action="append", default=[])

    proposal = sub.add_parser("propose-learning")
    proposal.add_argument("--source-event-id", required=True)
    proposal.add_argument("--target-path", required=True)
    proposal.add_argument("--action", default="modify")
    proposal.add_argument("--rationale", required=True)
    proposal.add_argument("--content-file", type=Path, required=True)
    proposal.add_argument("--validator", action="append", default=["skill_eval"])

    evaluate = sub.add_parser("evaluate-learning")
    evaluate.add_argument("proposal_path", type=Path)
    validate = sub.add_parser("validate-learning")
    validate.add_argument("proposal_path", type=Path)
    apply_learning = sub.add_parser("apply-learning")
    apply_learning.add_argument("proposal_path", type=Path)
    apply_learning.add_argument("--approved-by", required=True)
    approve_learning = sub.add_parser("approve-learning")
    approve_learning.add_argument("proposal_path", type=Path)
    approve_learning.add_argument("--approved-by", required=True)
    decline_learning = sub.add_parser("decline-learning")
    decline_learning.add_argument("proposal_path", type=Path)
    decline_learning.add_argument("--declined-by", required=True)
    decline_learning.add_argument("--reason", required=True)
    learning_debt = sub.add_parser("learning-debt")
    learning_debt.add_argument("--limit", type=int, default=8)
    knowledge_workflow = sub.add_parser(
        "knowledge-workflow",
        help="Dynamically review and compile one bounded knowledge event.",
    )
    knowledge_workflow.add_argument("event_path", type=Path)
    knowledge_workflow.add_argument(
        "--execute-compile",
        action="store_true",
        help="Invoke the A4 build/apply compiler boundary after read-only reviews pass.",
    )
    sub.add_parser("feedback-integrations", help="Report optional SDK and calibration availability.")
    annotations = sub.add_parser("import-feedback-annotations", help="Import exported Langfuse annotations as local review candidates.")
    annotations.add_argument("input", type=Path)
    annotations.add_argument("--dry-run", action="store_true")
    retire_successor = sub.add_parser(
        "retire-successor-feedback",
        help="Explicitly retire duplicate successor feedback into a named successor.",
    )
    retire_successor.add_argument("package_dir", type=Path)
    retire_successor.add_argument("--superseded-by", type=Path, required=True)
    retire_successor.add_argument("--retired-by", required=True)
    retire_successor.add_argument("--reason", required=True)

    doctor = sub.add_parser("carousel-doctor")
    doctor.add_argument("package_dir", type=Path)

    sub.add_parser("health")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    root = args.workspace_root.resolve()

    if args.command == "knowledge-workflow":
        try:
            result = run_knowledge_workflow(
                root,
                args.event_path,
                execute_compile=args.execute_compile,
            )
        except (OSError, ValueError) as exc:
            print(str(exc), file=sys.stderr)
            return 2
        print_json(result)
        return 0 if result["status"] == "PASS" else 2
    if args.command == "feedback-integrations":
        from evals.deepeval_adapter import calibration_status, deepeval_environment_status
        from pipeline.agentic.langfuse_mirror import langfuse_environment_status

        print_json({"deepeval": deepeval_environment_status(),
                    "calibration": calibration_status(root),
                    "langfuse": langfuse_environment_status(), "can_gate_generation": False})
    elif args.command == "import-feedback-annotations":
        from pipeline.agentic.langfuse_mirror import import_annotation_candidates

        if args.input.is_symlink() or not args.input.is_file():
            raise ValueError("Annotation input must be a regular JSON file")
        payload = json.loads(args.input.read_text(encoding="utf-8"))
        annotations = payload if isinstance(payload, list) else payload.get("data")
        if not isinstance(annotations, list):
            raise ValueError("Annotation export must be an array or an object with data array")
        existing = []
        for path in root.glob("memory/agentic/learning-events/event-langfuse-*.json"):
            saved = json.loads(path.read_text(encoding="utf-8"))
            identity = (saved.get("feedback_metadata") or {}).get("external_annotation_id_sha256")
            if identity:
                existing.append(identity)
        report = import_annotation_candidates(annotations, existing_annotation_ids=existing)
        event_ids = []
        if not args.dry_run:
            for candidate in report["candidates"]:
                identity = candidate["external_annotation_id_sha256"]
                event = capture_learning_event(root, source="langfuse_annotation_candidate",
                    summary="Imported annotation awaiting local review",
                    event_id="event-langfuse-" + identity.removeprefix("sha256:"),
                    user_instruction_exact=candidate["user_instruction_exact"],
                    scope=candidate["scope"], feedback_status="captured",
                    eval_disposition="candidate_only",
                    feedback_metadata={"external_annotation_id_sha256": identity,
                                       "candidate_status": "pending_local_review"})
                event_ids.append(event.event_id)
        report["event_ids"] = event_ids
        report["persistence"] = "dry_run" if args.dry_run else (
            "learning_events_candidate_only" if event_ids else "none"
        )
        print_json(report)
    elif args.command == "retire-successor-feedback":
        from pipeline.stages.carousel_visual_storytelling import (
            retire_successor_feedback,
        )

        try:
            print_json(
                retire_successor_feedback(
                    args.package_dir,
                    workspace_root=root,
                    superseded_by=args.superseded_by,
                    retired_by=args.retired_by,
                    reason_exact=args.reason,
                )
            )
        except (OSError, ValueError) as exc:
            print(str(exc), file=sys.stderr)
            return 2
    elif args.command == "context":
        pack = assemble_context_pack(root, profile=args.profile)
        print(render_context_pack(pack) if args.render else json.dumps(pack.model_dump(), indent=2, ensure_ascii=False))
    elif args.command == "registry":
        print_json([record.model_dump() for record in discover_skill_records(root)])
    elif args.command in {"index", "index-memory"}:
        if args.backend == "fts5":
            path = build_memory_index(root, index_path=args.index_path)
        else:
            if args.index_path is not None:
                print("--index-path is supported only by the fts5 backend", file=sys.stderr)
                return 2
            from pipeline.agentic.retrieval import get_backend
            path = get_backend(args.backend).build(root)
        print_json({"backend": args.backend, "index_path": str(path)})
    elif args.command == "search":
        from pipeline.agentic.retrieval import search as search_retrieval
        print_json([hit.model_dump() for hit in search_retrieval(root, args.query, limit=args.limit, backend=args.backend)])
    elif args.command == "recall":
        bundle = build_recall_bundle(root, args.query, profile=args.profile, backend=args.backend)
        print_json(bundle) if args.json else print(render_recall_bundle(bundle))
    elif args.command in {"system", "skill-system"}:
        print_json(resolve_skill_system(load_skill_systems(root), args.name))
    elif args.command == "skill-usage":
        print_json(summarize_skill_usage(root))
    elif args.command == "record-skill-run":
        print_json(
            record_skill_run(
                root,
                skill_name=args.skill_name,
                outcome=args.outcome,
                note=args.note,
            )
        )
    elif args.command == "capture-hypothesis":
        print_json(
            capture_hypothesis(
                root,
                source=args.source,
                hypothesis=args.hypothesis,
                success_signal=args.success_signal,
                falsifier=args.falsifier,
                evidence_paths=args.evidence,
            )
        )
    elif args.command == "hypotheses":
        records = list_hypotheses(root, status=args.status, limit=args.limit)
        print_json(
            {
                "open_count": len([record for record in records if record.get("status") == "open"]),
                "records": records,
            }
        )
    elif args.command == "resolve-hypothesis":
        print_json(
            resolve_hypothesis(
                root,
                hypothesis_id=args.hypothesis_id,
                outcome=args.outcome,
                result_summary=args.result_summary,
                evidence_paths=args.evidence,
            )
        )
    elif args.command == "capture-learning":
        print_json(
            capture_learning_event(
                root,
                source=args.source,
                summary=args.summary,
                evidence_paths=args.evidence,
            )
        )
    elif args.command == "propose-learning":
        content = args.content_file.read_text(encoding="utf-8")
        print_json(
            {
                "proposal_path": str(
                    create_learning_proposal(
                        root,
                        source_event_id=args.source_event_id,
                        target_path=args.target_path,
                        proposed_action=args.action,
                        rationale=args.rationale,
                        proposed_content=content,
                        required_validators=args.validator,
                    )
                )
            }
        )
    elif args.command == "evaluate-learning":
        print_json(evaluate_learning_proposal_review(root, args.proposal_path))
    elif args.command == "validate-learning":
        receipts = run_required_validators(root, args.proposal_path)
        print_json({"receipts": receipts, "status": "PASS" if all(item["status"] == "PASS" for item in receipts) else "FAIL"})
    elif args.command == "apply-learning":
        try:
            print_json(
                apply_learning_proposal(
                    root,
                    args.proposal_path,
                    approved_by=args.approved_by,
                )
            )
        except ValueError as exc:
            print(str(exc), file=sys.stderr)
            return 2
    elif args.command == "approve-learning":
        try:
            print_json(
                approve_learning_proposal(
                    root,
                    args.proposal_path,
                    approved_by=args.approved_by,
                )
            )
        except ValueError as exc:
            print(str(exc), file=sys.stderr)
            return 2
    elif args.command == "decline-learning":
        try:
            print_json(
                decline_learning_proposal(
                    root,
                    args.proposal_path,
                    declined_by=args.declined_by,
                    reason=args.reason,
                )
            )
        except (StopIteration, ValueError) as exc:
            print(str(exc), file=sys.stderr)
            return 2
    elif args.command == "learning-debt":
        all_records = learning_debt_records(root, limit=None)
        records = all_records[:max(0, args.limit)]
        print_json(
            {
                "debt_count": len(all_records),
                "returned_count": len(records),
                "records": records,
            }
        )
    elif args.command == "carousel-doctor":
        package_dir = args.package_dir
        if not package_dir.is_absolute():
            package_dir = root / package_dir
        report = inspect_carousel_package(package_dir)
        state = derive_carousel_state(package_dir)
        payload = report.to_dict()
        payload["state"] = state.to_dict()
        print_json(payload)
    elif args.command == "health":
        pack = assemble_context_pack(root)
        systems = load_skill_systems(root)
        records = discover_skill_records(root)
        open_hypotheses = list_hypotheses(root, status="open", limit=1000)
        learning_debt = learning_debt_records(root, limit=1000)
        learning_debt_by_kind: dict[str, int] = {}
        for record in learning_debt:
            kind = str(record.get("kind", "unknown"))
            learning_debt_by_kind[kind] = learning_debt_by_kind.get(kind, 0) + 1
        from datetime import date
        from pipeline.stages.wiki_health import (
            feedback_health_evidence, generation_receipt_health_evidence,
            learning_approval_health_evidence,
        )
        feedback_health = feedback_health_evidence(root, date.today())
        receipt_failures = generation_receipt_health_evidence(root, date.today())
        approval_failures = learning_approval_health_evidence(root)
        failed = bool(feedback_health["unsupported"] or feedback_health["invalid_events"] or receipt_failures or approval_failures)
        print_json(
            {
                "context_sections": len(pack.sections),
                "skill_systems": sorted(systems.get("systems", {}).keys()),
                "skill_records": len(records),
                "open_hypotheses": len(open_hypotheses),
                "learning_debt_count": len(learning_debt),
                "learning_debt_by_kind": learning_debt_by_kind,
                "status": "FAIL" if failed else "PASS",
                "creator_feedback": feedback_health,
                "generation_receipt_failures": receipt_failures,
                "learning_approval_failures": approval_failures,
            }
        )
        return 2 if failed else 0
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
