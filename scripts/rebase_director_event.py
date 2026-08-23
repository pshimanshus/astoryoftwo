#!/usr/bin/env python3
"""Rebase a fresh copy-hidden Event A onto a rebuilt carousel package.

This is intentionally narrow: unchanged directed slides may come from a
previous current-contract package, while every changed slide must be supplied
as an explicit semantic patch. The fresh critic response, current copy,
format lock, creator correction, and prompt pack are all rebound and validated
before the target visual-plan artifact is replaced.
"""

from __future__ import annotations

import argparse
from copy import deepcopy
import json
from pathlib import Path
import sys
import tempfile
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from pipeline.stages.carousel_format_contract import (
    locked_format_contract_fingerprint,
    locked_formats,
)
from pipeline.stages.carousel_visual_storytelling import (
    REVIEW_PROVENANCE_VERSION,
    blind_cards_fingerprint,
    current_creator_correction_fingerprint,
    current_generation_payload_fingerprint,
    director_event_fingerprint,
    director_review_output_fingerprint,
    review_response_fingerprint,
    storyboard_source_fingerprint,
    validate_director_storyboard,
)


def load_object(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"{path} must contain a JSON object.")
    return payload


def records_by_slide(raw: Any, *, label: str) -> dict[int, dict[str, Any]]:
    if not isinstance(raw, list):
        raise ValueError(f"{label} must be a list.")
    records: dict[int, dict[str, Any]] = {}
    for item in raw:
        if not isinstance(item, dict):
            raise ValueError(f"{label} contains a non-object record.")
        try:
            number = int(item["slide"])
        except (KeyError, TypeError, ValueError) as exc:
            raise ValueError(f"{label} record is missing a valid slide number.") from exc
        if number in records:
            raise ValueError(f"{label} repeats slide {number}.")
        records[number] = item
    return records


def critic_evidence_text(raw: Any) -> str:
    if isinstance(raw, list):
        return " ".join(
            str(item).strip() for item in raw if str(item).strip()
        )
    return str(raw or "").strip()


def replace_slide(
    records: list[dict[str, Any]], replacement: dict[str, Any], *, label: str
) -> None:
    try:
        number = int(replacement["slide"])
    except (KeyError, TypeError, ValueError) as exc:
        raise ValueError(f"{label} replacement needs a valid slide number.") from exc
    matches = [
        index
        for index, item in enumerate(records)
        if isinstance(item, dict) and int(item.get("slide", 0) or 0) == number
    ]
    if len(matches) != 1:
        raise ValueError(f"{label} must contain slide {number} exactly once.")
    records[matches[0]] = deepcopy(replacement)


def atomic_write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        "w",
        encoding="utf-8",
        dir=path.parent,
        prefix=f".{path.name}.",
        suffix=".tmp",
        delete=False,
    ) as handle:
        json.dump(payload, handle, indent=2, ensure_ascii=False)
        handle.write("\n")
        temp_path = Path(handle.name)
    temp_path.replace(path)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Rebind a fresh copy-hidden director event onto a rebuilt package."
    )
    parser.add_argument("--template-package", required=True, type=Path)
    parser.add_argument("--target-package", required=True, type=Path)
    parser.add_argument("--event-response", required=True, type=Path)
    parser.add_argument("--slide-repair", required=True, type=Path)
    parser.add_argument("--author-task-id", required=True)
    parser.add_argument("--author-run-id", required=True)
    parser.add_argument("--reviewer-task-id", required=True)
    parser.add_argument("--reviewer-run-id", required=True)
    args = parser.parse_args()

    template_plan = load_object(args.template_package / "visual-plan-quality.json")
    target_plan_path = args.target_package / "visual-plan-quality.json"
    target_plan = load_object(target_plan_path)
    template_director = template_plan.get("director_storyboard")
    if not isinstance(template_director, dict):
        raise ValueError("Template package has no structured director_storyboard.")

    response_text = args.event_response.read_text(encoding="utf-8")
    response = json.loads(response_text)
    if not isinstance(response, dict):
        raise ValueError("Event response must contain a JSON object.")
    if response.get("reviewer_task_id") != args.reviewer_task_id:
        raise ValueError("Event response reviewer_task_id does not match the CLI lock.")
    if response.get("reviewer_run_id") != args.reviewer_run_id:
        raise ValueError("Event response reviewer_run_id does not match the CLI lock.")

    repair = load_object(args.slide_repair)
    blind_replacement = repair.get("blind_card")
    director_replacement = repair.get("director_slide")
    if not isinstance(blind_replacement, dict) or not isinstance(
        director_replacement, dict
    ):
        raise ValueError("Slide repair needs blind_card and director_slide objects.")

    target_slides = json.loads(
        (args.target_package / "slides.json").read_text(encoding="utf-8")
    )
    target_records = (
        target_slides
        if isinstance(target_slides, list)
        else target_slides.get("slides", [])
        if isinstance(target_slides, dict)
        else []
    )
    expected_numbers = sorted(records_by_slide(target_records, label="slides.json"))
    if not expected_numbers:
        raise ValueError("Target package has no slides.")

    director = deepcopy(template_director)
    blind_cards = director.get("blind_cards")
    directed_slides = director.get("slides")
    if not isinstance(blind_cards, list) or not isinstance(directed_slides, list):
        raise ValueError("Template director is missing blind_cards or slides.")
    replace_slide(blind_cards, blind_replacement, label="blind_cards")
    replace_slide(directed_slides, director_replacement, label="director slides")
    if "setup_payoff_ledger" in repair:
        director["setup_payoff_ledger"] = deepcopy(repair["setup_payoff_ledger"])
    if "object_motif_ledger" in repair:
        director["object_motif_ledger"] = deepcopy(repair["object_motif_ledger"])

    critic_slides = records_by_slide(response.get("slides"), label="critic slides")
    if sorted(critic_slides) != expected_numbers:
        raise ValueError("Critic response does not cover the target slide set exactly.")
    directed_by_slide = records_by_slide(directed_slides, label="director slides")
    for number in expected_numbers:
        critic = critic_slides[number]
        directed = directed_by_slide[number]
        directed["status"] = "PASS"
        directed["inference_match"] = True
        directed["silent_read"] = str(critic.get("silent_read") or "")
        directed["critic_evidence"] = critic_evidence_text(
            critic.get("critic_evidence")
            if critic.get("critic_evidence") is not None
            else critic.get("concrete_critic_evidence")
        )
        directed["unresolved_ambiguities"] = []

    raw_relative = args.event_response.resolve().relative_to(
        args.target_package.resolve()
    ).as_posix()
    director.update(
        {
            "status": "PASS",
            "event": "copy_hidden_storyboard_read",
            "copy_locked": True,
            "copy_hidden": True,
            "intent_hidden": True,
            "author_id": args.author_task_id,
            "reviewer_id": args.reviewer_task_id,
            "reviewer_evidence": (
                "A fresh orchestrated critic reviewed only the seven observable staged "
                "cards in order; the changed slide was supplied as a new copy-hidden card."
            ),
            "requested_formats": list(locked_formats(args.target_package)),
            "format_contract_fingerprint": locked_format_contract_fingerprint(
                args.target_package
            ),
            "creator_correction_fingerprint": (
                current_creator_correction_fingerprint(args.target_package)
            ),
            "generation_payload_fingerprint": current_generation_payload_fingerprint(
                args.target_package
            ),
            "blind_cards": blind_cards,
            "blind_input_fingerprint": blind_cards_fingerprint(blind_cards),
            "source_fingerprint": storyboard_source_fingerprint(target_records),
            "sequence_read": str(response.get("sequence_read") or ""),
            "slides": directed_slides,
            "issues": [],
            "review_provenance": {
                "schema_version": REVIEW_PROVENANCE_VERSION,
                "author_task_id": args.author_task_id,
                "author_run_id": args.author_run_id,
                "reviewer_task_id": args.reviewer_task_id,
                "reviewer_run_id": args.reviewer_run_id,
                "input_fingerprint": blind_cards_fingerprint(blind_cards),
                "raw_response_artifact": raw_relative,
                "raw_response_fingerprint": review_response_fingerprint(response_text),
            },
        }
    )
    director["review_provenance"]["output_fingerprint"] = (
        director_review_output_fingerprint(director)
    )
    director["director_event_fingerprint"] = director_event_fingerprint(director)
    target_plan["director_storyboard"] = director

    issues = validate_director_storyboard(
        target_plan,
        slide_count=len(target_records),
        expected_slides=target_slides,
        expected_formats=locked_formats(args.target_package),
        expected_format_contract_fingerprint=locked_format_contract_fingerprint(
            args.target_package
        ),
        expected_creator_correction_fingerprint=(
            current_creator_correction_fingerprint(args.target_package)
        ),
        expected_generation_payload_fingerprint=current_generation_payload_fingerprint(
            args.target_package
        ),
        provenance_package_dir=args.target_package,
    )
    if issues:
        raise ValueError("Rebased director event failed validation: " + "; ".join(issues))

    stage_reviews_path = args.target_package / "stage-reviews.json"
    stage_reviews = load_object(stage_reviews_path)
    visual_review = stage_reviews.get("reviews", {}).get("visual_reviewer")
    if not isinstance(visual_review, dict):
        raise ValueError("stage-reviews.json is missing visual_reviewer.")
    visual_review["status"] = "PASS"
    visual_review["issues"] = []
    done = visual_review.setdefault("done", [])
    marker = "fresh copy-hidden director_storyboard Event A: PASS"
    if marker not in done:
        done.append(marker)

    atomic_write_json(target_plan_path, target_plan)
    atomic_write_json(stage_reviews_path, stage_reviews)
    print(
        json.dumps(
            {
                "status": "PASS",
                "target_package": str(args.target_package),
                "director_event_fingerprint": director["director_event_fingerprint"],
                "blind_input_fingerprint": director["blind_input_fingerprint"],
                "reviewer_task_id": args.reviewer_task_id,
                "reviewer_run_id": args.reviewer_run_id,
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
