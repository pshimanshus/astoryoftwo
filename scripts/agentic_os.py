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
    capture_hypothesis,
    capture_learning_event,
    create_learning_proposal,
    learning_debt_records,
    list_hypotheses,
    resolve_hypothesis,
)
from pipeline.agentic.memory_index import build_memory_index, search_memory  # noqa: E402
from pipeline.agentic.recall import build_recall_bundle, render_recall_bundle  # noqa: E402
from pipeline.agentic.skill_eval import evaluate_learning_proposal  # noqa: E402
from pipeline.agentic.skill_registry import discover_skill_records, load_skill_systems, resolve_skill_system  # noqa: E402
from pipeline.agentic.skill_usage import record_skill_run, summarize_skill_usage  # noqa: E402
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
    index_memory = sub.add_parser("index-memory")
    index_memory.add_argument("--index-path", type=Path)

    search = sub.add_parser("search")
    search.add_argument("query")
    search.add_argument("--limit", type=int, default=8)

    recall = sub.add_parser("recall")
    recall.add_argument("query")
    recall.add_argument("--profile")
    recall.add_argument("--json", action="store_true")

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
    learning_debt = sub.add_parser("learning-debt")
    learning_debt.add_argument("--limit", type=int, default=8)

    doctor = sub.add_parser("carousel-doctor")
    doctor.add_argument("package_dir", type=Path)

    sub.add_parser("health")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    root = args.workspace_root.resolve()

    if args.command == "context":
        pack = assemble_context_pack(root, profile=args.profile)
        print(render_context_pack(pack) if args.render else json.dumps(pack.model_dump(), indent=2, ensure_ascii=False))
    elif args.command == "registry":
        print_json([record.model_dump() for record in discover_skill_records(root)])
    elif args.command in {"index", "index-memory"}:
        path = build_memory_index(root, index_path=args.index_path)
        print_json({"index_path": str(path)})
    elif args.command == "search":
        index_path = build_memory_index(root)
        print_json([hit.model_dump() for hit in search_memory(index_path, args.query, limit=args.limit)])
    elif args.command == "recall":
        bundle = build_recall_bundle(root, args.query, profile=args.profile)
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
        print_json(evaluate_learning_proposal(root, args.proposal_path))
    elif args.command == "learning-debt":
        records = learning_debt_records(root, limit=args.limit)
        print_json(
            {
                "debt_count": len(records),
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
        print_json(
            {
                "context_sections": len(pack.sections),
                "skill_systems": sorted(systems.get("systems", {}).keys()),
                "skill_records": len(records),
            }
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
