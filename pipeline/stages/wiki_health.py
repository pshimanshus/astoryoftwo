"""
Repo-wide wiki and memory health checks.

Carousel runs already have a quality spine. This module provides the missing
session/repo spine: deterministic linting, diagnostics, HEAL proposals, and an
episodic record that future sessions can read.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from datetime import date, datetime
from pathlib import Path
from typing import Any


ADVERTISED_PIPELINE_FILES = [
    "pipeline/runner.py",
    "pipeline/stages/a1_ingest.py",
    "pipeline/stages/a2_parser.py",
    "pipeline/stages/a3_analyzer.py",
    "pipeline/stages/a4_wiki.py",
    "pipeline/stages/a5_report.py",
]

INSTRUCTION_SURFACE_FILES = [
    "AGENTS.md",
]

REQUIRED_CLOSEOUT_PHRASES = [
    "scripts/autopublish.py",
    "scripts/wiki_health.py --write --fix-index",
]

REQUIRED_AGENTIC_OS_FILES = [
    "pipeline/agentic/__init__.py",
    "pipeline/agentic/contracts.py",
    "pipeline/agentic/context_loader.py",
    "pipeline/agentic/skill_registry.py",
    "pipeline/agentic/memory_index.py",
    "pipeline/agentic/recall.py",
    "pipeline/agentic/audit_log.py",
    "pipeline/agentic/learning_loop.py",
    "pipeline/agentic/skill_eval.py",
    "pipeline/agentic/workflow_metadata.py",
    "pipeline/agentic/workflow_state.py",
    "scripts/agentic_os.py",
    "config/agentic_context_manifest.json",
    "config/skill-systems.json",
    "docs/superpowers/specs/agentic-os-control-plane.md",
]

REQUIRED_MEMORY_SURFACE = {
    "wiki_index": "wiki/index.md",
    "wiki_themes": "wiki/themes",
    "wiki_insights": "wiki/insights",
    "wiki_posts": "wiki/posts",
    "wiki_people": "wiki/people",
    "working_memory": "memory/working.md",
    "semantic_memory": "memory/semantic",
    "episodic_memory": "memory/episodic",
    "graph_memory": "memory/graph.json",
    "logs": "logs",
}

WIKI_REQUIRED_METADATA = ["last_updated", "confidence", "sources"]
ACTIVE_CAROUSEL_GUIDANCE = [
    ".agents/skills/a-story-carousel-jam/SKILL.md",
    ".agents/skills/a-story-direct-visual-story/SKILL.md",
    ".agents/skills/astory/references/imagegen-contract.md",
    ".agents/skills/astory/references/house-style-contract.md",
    ".agents/skills/astory/references/master-prompt.md",
    ".agents/skills/astory/references/failure-taxonomy.md",
    "config/skills/carousel-jam-autopilot.md",
    "config/skills/illustration-carousel-framework.md",
    "docs/ai-ops-playbook.md",
    "config/skill-systems.json",
]
STALE_GUIDANCE_PATTERNS = {
    "1080x1350": re.compile(r"1080\s*[x×]\s*1350", re.IGNORECASE),
    "eleven_reference_generation": re.compile(r"\b(?:11|eleven)[ -]references?\b", re.IGNORECASE),
    "review_room": re.compile(r"\breview[ -]rooms?\b", re.IGNORECASE),
    "agent_assignment_flow": re.compile(r"\bagent[ -]assignment\b", re.IGNORECASE),
}


def _package_date(path: Path, root: Path) -> date | None:
    try:
        relative = path.relative_to(root / "output" / "carousels")
        return date.fromisoformat(relative.parts[0])
    except (ValueError, IndexError):
        return None


def _iso_date(value: object) -> date | None:
    try:
        return date.fromisoformat(str(value)[:10])
    except (TypeError, ValueError):
        return None


def _feedback_event_issues(
    root: Path,
    package_dir: Path | None,
    event: dict[str, Any],
    *,
    require_action_taken: bool,
    include_approval_work: bool = False,
) -> list[str]:
    """Return lifecycle failures without turning feedback checks into generation gates."""
    issues: list[str] = []
    if not event.get("primary_diagnosis"):
        issues.append("missing diagnosis")
    if not event.get("root_cause"):
        issues.append("missing root_cause")
    elif event.get("root_cause") == event.get("primary_diagnosis"):
        issues.append("root_cause is only a diagnosis label")
    if not event.get("desired_behavior"):
        issues.append("missing desired_behavior")

    kind = str(event.get("kind") or "correction")
    tracks_repair = kind in {"correction", "rejection"} or (
        include_approval_work and bool(event.get("must_change"))
    )
    if not tracks_repair:
        return issues

    status = str(event.get("status") or "captured")
    resolved = status in {
        "evaluated",
        "learning_proposed",
        "learning_declined",
        "approved",
        "promoted",
        "rejected",
    }
    if not resolved:
        issues.append("unresolved feedback debt")
        return issues

    if (require_action_taken and not event.get("action_taken")) or not event.get("resolution_evidence"):
        issues.append("resolved without repair evidence")
    task_ids = event.get("eval_task_ids") or []
    waiver = event.get("eval_waiver_reason")
    if not task_ids and not waiver:
        issues.append("resolved without eval or waiver")
    if waiver and not task_ids:
        return issues

    from evals.feedback_cases import feedback_case_is_current, load_feedback_case

    for task_id in task_ids:
        try:
            case = load_feedback_case(root, str(task_id))
            if case.get("status") not in {"passed", "waived"}:
                issues.append(f"linked eval {task_id} has not passed")
            elif package_dir is None or not feedback_case_is_current(package_dir, case, event):
                issues.append(f"linked eval {task_id} is stale after artifact or contract changes")
        except (OSError, ValueError):
            issues.append(f"linked eval {task_id} is missing or invalid")
    return issues


def feedback_health_evidence(root: Path, today: date) -> dict[str, Any]:
    cutoff = date(2026, 8, 7)
    unsupported: list[str] = []
    invalid: dict[str, list[str]] = {}
    blocking: dict[str, list[str]] = {}
    seen_feedback_ids: set[str] = set()
    historical_feedback: list[dict[str, str]] = []
    live_feedback_on_read_only_packages: list[dict[str, str]] = []
    unresolved_records: list[dict[str, Any]] = []
    carried_forward: list[dict[str, str]] = []
    retired_successors: list[dict[str, Any]] = []
    retired_feedback_ids_by_package: dict[str, set[str]] = {}
    retired_learning_ids_by_package: dict[str, set[str]] = {}
    correction_paths = sorted(root.glob("output/carousels/**/creator-correction.json"))
    from pipeline.stages.carousel_visual_storytelling import (
        successor_feedback_retirement_status,
    )

    for path in correction_paths:
        package_date = _package_date(path, root)
        if package_date is None or not cutoff <= package_date <= today:
            continue
        try:
            document = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        if not isinstance(document, dict) or "successor_retirement" not in document:
            continue
        retirement = successor_feedback_retirement_status(
            path.parent, workspace_root=root
        )
        if retirement.get("retired"):
            package_path = relative_path(path.parent, root)
            retired_feedback_ids_by_package[package_path] = set(
                retirement.get("retired_feedback_ids") or []
            )
            retired_learning_ids_by_package[package_path] = set(
                retirement.get("retired_learning_event_ids") or []
            )
            retired_successors.append(retirement)
        else:
            retirement_issues = [
                f"invalid successor retirement: {issue}"
                for issue in retirement.get("issues") or ["unknown validation failure"]
            ]
            invalid.setdefault(relative_path(path, root), []).extend(retirement_issues)
            blocking.setdefault(relative_path(path, root), []).extend(retirement_issues)
    # Only an existing successor with matching immutable wording can carry debt.
    adopted: dict[tuple[str, str, str], list[str]] = {}
    adoption_edges: dict[tuple[str, str, str], list[tuple[str, str, str]]] = {}
    for path in correction_paths:
        package_date = _package_date(path, root)
        if package_date is None or not cutoff <= package_date <= today:
            continue
        try:
            document = json.loads(path.read_text(encoding="utf-8"))
            if document.get("schema_version") != "creator-correction/v3":
                continue
            package_path = relative_path(path.parent, root)
            retired_feedback_ids = retired_feedback_ids_by_package.get(
                package_path, set()
            )
            for event in document.get("events") or []:
                if event.get("feedback_id") in retired_feedback_ids:
                    continue
                provenance = event.get("adoption_provenance") or {}
                exact_hash = "sha256:" + hashlib.sha256(str(event.get("user_instruction_exact") or "").encode("utf-8")).hexdigest()
                if (event.get("historical_only") or event.get("status") == "rejected"
                        or not provenance.get("source_feedback_id")
                        or event.get("user_instruction_sha256") != exact_hash
                        or provenance.get("source_package_path") == relative_path(path.parent, root)):
                    continue
                key = (str(provenance.get("source_package_path") or ""),
                       str(provenance["source_feedback_id"]),
                       str(event.get("user_instruction_sha256") or ""))
                adopted.setdefault(key, []).append(relative_path(path, root))
                adoption_edges.setdefault(key, []).append((relative_path(path.parent, root),
                    str(event.get("feedback_id") or ""), exact_hash))
        except (OSError, ValueError, TypeError, AttributeError):
            continue

    def is_carried(package: str, feedback_id: str, instruction_hash: str, source: str) -> bool:
        key = (package, feedback_id, instruction_hash)
        successors = adopted.get(key, [])
        if not successors:
            return False
        def reaches_leaf(node: tuple[str, str, str], visited: set[tuple[str, str, str]]) -> bool:
            if node in visited:
                return False
            children = adoption_edges.get(node, [])
            return not children or all(reaches_leaf(child, visited | {node}) for child in children)
        if not reaches_leaf(key, set()):
            return False
        carried_forward.append({"feedback_id": feedback_id, "source": source,
                                "successor": ", ".join(successors)})
        return True
    for path in correction_paths:
        package_date = _package_date(path, root)
        if package_date is None or not cutoff <= package_date <= today:
            continue
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            unsupported.append(relative_path(path, root))
            continue
        if payload.get("schema_version") != "creator-correction/v3" or not isinstance(payload.get("events"), list):
            unsupported.append(relative_path(path, root))
            continue
        package_path = relative_path(path.parent, root)
        retired_feedback_ids = retired_feedback_ids_by_package.get(package_path, set())
        for event in payload["events"]:
            if not isinstance(event, dict):
                invalid.setdefault(relative_path(path, root), []).append("non-object event")
                blocking.setdefault(relative_path(path, root), []).append("non-object event")
                continue
            feedback_id = str(event.get("feedback_id") or "unknown")
            if feedback_id in retired_feedback_ids:
                continue
            seen_feedback_ids.add(feedback_id)
            if event.get("historical_only"):
                historical_feedback.append(
                    {
                        "feedback_id": feedback_id,
                        "source": relative_path(path, root),
                        "classification": "historical_feedback",
                    }
                )
                continue
            if is_carried(relative_path(path.parent, root), feedback_id,
                          str(event.get("user_instruction_sha256") or ""), relative_path(path, root)):
                continue
            issues = _feedback_event_issues(
                root,
                path.parent,
                event,
                require_action_taken=True,
                include_approval_work=True,
            )
            if issues:
                invalid.setdefault(relative_path(path, root), []).extend(
                    f"{feedback_id}: {issue}" for issue in issues
                )
                hard_issues = [
                    issue for issue in issues
                    if issue != "unresolved feedback debt"
                    and not (issue.startswith("linked eval ") and (
                        "has not passed" in issue or "is stale" in issue
                    ))
                ]
                if hard_issues:
                    blocking.setdefault(relative_path(path, root), []).extend(
                        f"{feedback_id}: {issue}" for issue in hard_issues
                    )
                unresolved_records.append({"feedback_id": feedback_id,
                    "source": relative_path(path, root), "package_path": relative_path(path.parent, root),
                    "event_id": event.get("learning_event_id") or feedback_id,
                    "summary": "; ".join(issues), "created_at": event.get("captured_at") or ""})

    # Some legacy prompt-packages are intentionally immutable. Current creator
    # feedback about those packages is stored as a LearningEvent until a v3
    # successor package can carry the repair. That is live repair debt; it is
    # not made historical merely because the rejected package is read-only.
    for path in sorted(root.glob("memory/agentic/learning-events/*.json")):
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        metadata = payload.get("feedback_metadata")
        if payload.get("source") != "creator_feedback" or not isinstance(metadata, dict):
            continue
        feedback_id = str(metadata.get("feedback_id") or "")
        if not feedback_id or feedback_id in seen_feedback_ids:
            continue
        captured_on = _iso_date(payload.get("created_at"))
        if captured_on is None or not cutoff <= captured_on <= today:
            continue
        source = relative_path(path, root)
        if metadata.get("historical_only"):
            historical_feedback.append(
                {
                    "feedback_id": feedback_id,
                    "source": source,
                    "classification": "historical_feedback",
                }
            )
            continue
        package_value = str(payload.get("package_path") or "")
        retired_feedback_ids = retired_feedback_ids_by_package.get(package_value, set())
        retired_learning_ids = retired_learning_ids_by_package.get(package_value, set())
        if (
            feedback_id in retired_feedback_ids
            or str(payload.get("event_id") or "") in retired_learning_ids
        ):
            continue
        exact_hash = "sha256:" + hashlib.sha256(str(payload.get("user_instruction_exact") or "").encode("utf-8")).hexdigest()
        if is_carried(package_value, feedback_id, exact_hash, source):
            continue
        live_feedback_on_read_only_packages.append(
            {
                "feedback_id": feedback_id,
                "source": source,
                "package_path": package_value,
                "classification": "live_feedback_on_read_only_historical_package",
            }
        )
        event = {
            "feedback_id": feedback_id,
            "user_instruction_exact": payload.get("user_instruction_exact"),
            "user_instruction_sha256": exact_hash,
            "primary_diagnosis": payload.get("diagnosis") or metadata.get("primary_diagnosis"),
            "root_cause": metadata.get("root_cause"),
            "desired_behavior": metadata.get("desired_behavior"),
            "kind": metadata.get("kind") or "correction",
            "status": payload.get("feedback_status") or "captured",
            "must_change": metadata.get("must_change") or [],
            "must_preserve": metadata.get("must_preserve") or [],
            "repair_operations": metadata.get("repair_operations") or [],
            "verification_assertions": metadata.get("verification_assertions") or [],
            "affected_artifacts": metadata.get("affected_artifacts") or [],
            "resolution_evidence": payload.get("resolution_evidence") or [],
            "eval_task_ids": metadata.get("eval_task_ids") or [],
            "eval_waiver_reason": metadata.get("eval_waiver_reason"),
        }
        package_dir = root / package_value if package_value else None
        issues = _feedback_event_issues(
            root,
            package_dir,
            event,
            require_action_taken=False,
            include_approval_work=True,
        )
        if package_dir is None or not package_dir.is_dir():
            issues.append("read-only historical package is missing")
        if issues:
            invalid.setdefault(source, []).extend(f"{feedback_id}: {issue}" for issue in issues)
            hard_issues = [
                issue for issue in issues
                if issue != "unresolved feedback debt"
                and not (issue.startswith("linked eval ") and (
                    "has not passed" in issue or "is stale" in issue
                ))
            ]
            if hard_issues:
                blocking.setdefault(source, []).extend(
                    f"{feedback_id}: {issue}" for issue in hard_issues
                )
            unresolved_records.append({"feedback_id": feedback_id, "source": source,
                "package_path": package_value, "event_id": payload.get("event_id") or feedback_id,
                "summary": "; ".join(issues), "created_at": payload.get("created_at") or ""})

    return {
        "window_start": str(cutoff),
        "unsupported": unsupported,
        "invalid_events": invalid,
        "blocking_events": blocking,
        "historical_feedback": historical_feedback,
        "live_feedback_on_read_only_packages": live_feedback_on_read_only_packages,
        "retired_successors": retired_successors,
        "carried_forward": carried_forward,
        "unresolved_records": unresolved_records,
    }


def _verified_superseded_attempt(package_dir: Path, number: int, receipt: dict[str, Any]) -> bool:
    """Verify an invalidated attempt in quarantine without restoring it as current."""
    from pipeline.stages.carousel_generation_inputs import canonical_fingerprint, sha256_binding

    attempt = int(receipt.get("attempt") or 0)
    if attempt <= 0:
        return False
    candidate_relative = f".internal/visual-quarantine/slide-{number:02d}/attempt-{attempt:02d}/candidate.json"
    expected_paths = {candidate_relative}
    for returned in receipt.get("returned_sources") or []:
        if not isinstance(returned, dict) or not isinstance(returned.get("path"), str):
            return False
        expected_paths.add(returned["path"])

    archive_base = package_dir / ".internal" / "visual-quarantine" / "superseded"
    for manifest_path in sorted(archive_base.glob("*/archive.json")):
        archive_root = manifest_path.parent.resolve()
        try:
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            entries = manifest.get("files") if isinstance(manifest, dict) else None
            if manifest.get("schema_version") != "carousel-superseded-evidence/v1" or not isinstance(entries, list):
                continue
            by_original: dict[str, str] = {}
            valid = True
            for entry in entries:
                if not isinstance(entry, dict) or not isinstance(entry.get("original_path"), str):
                    valid = False
                    break
                archived = (archive_root / entry["original_path"]).resolve()
                if archive_root not in archived.parents or archived.is_symlink() or not archived.is_file():
                    valid = False
                    break
                if sha256_binding(archived.read_bytes()) != entry.get("sha256"):
                    valid = False
                    break
                by_original[entry["original_path"]] = str(entry.get("sha256"))
            if not valid or not expected_paths.issubset(by_original):
                continue
            if any(
                by_original.get(returned["path"]) != returned.get("sha256")
                for returned in receipt.get("returned_sources") or []
            ):
                continue
            candidate = json.loads((archive_root / candidate_relative).read_text(encoding="utf-8"))
            original_receipt = candidate.get("generation_receipt") if isinstance(candidate, dict) else None
            immutable = (
                "generator_boundary", "tool_reported_model", "prompt_sha256",
                "reference_manifest_sha256", "references", "slide", "attempt",
                "returned_sources", "feedback_id", "feedback_ids",
            )
            if not isinstance(original_receipt, dict) or any(
                receipt.get(key) != original_receipt.get(key) for key in immutable
            ):
                continue
            qa_hash = receipt.get("qa_sha256")
            if qa_hash:
                qa_path = archive_root / "proof-qa.json"
                if not qa_path.is_file():
                    continue
                qa = json.loads(qa_path.read_text(encoding="utf-8"))
                if not isinstance(qa, dict):
                    continue
                qa_without_approval = {key: value for key, value in qa.items() if key != "creator_approval"}
                if canonical_fingerprint(qa_without_approval) != qa_hash:
                    continue
            return True
        except (OSError, ValueError, json.JSONDecodeError, TypeError):
            continue
    return False


def generation_receipt_health_evidence(root: Path, today: date) -> dict[str, list[str]]:
    cutoff = date(2026, 8, 7)
    failures: dict[str, list[str]] = {}
    advanced = {
        "proof_qa_required", "proof_failed", "awaiting_creator_proof_approval",
        "batch_ready", "final_qa_required", "final_qa_failed", "publish_ready",
    }
    for path in sorted(root.glob("output/carousels/**/generation-state.json")):
        package_date = _package_date(path, root)
        if package_date is None or not cutoff <= package_date <= today:
            continue
        try:
            state = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        if state.get("schema_version") != "carousel-generation-state/v3" or state.get("status") not in advanced:
            continue
        # This rollout is prospective for ImageGen receipts. Archived prompt-v2
        # packages cannot generate through the active pipeline and their original
        # tool provenance must not be invented during correction-only backfill.
        try:
            prompt_pack = json.loads((path.parent / "prompt-pack.json").read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            prompt_pack = {}
        if prompt_pack.get("schema_version") == "carousel-prompt-pack/v2":
            continue
        if not state.get("slides"):
            failures.setdefault(relative_path(path, root), []).append("advanced state has no slide receipts")
        for number, slide in (state.get("slides") or {}).items():
            if not isinstance(slide, dict):
                failures.setdefault(relative_path(path, root), []).append(f"slide {number}: malformed state")
                continue
            if int(slide.get("attempts") or 0) == 0 and slide.get("status") not in {"qa_required", "qa_passed", "failed", "approved_candidate", "publish_ready"}:
                continue
            history = slide.get("attempt_history") or []
            if not history:
                failures.setdefault(relative_path(path, root), []).append(f"slide {number}: missing attempt receipt")
                continue
            receipt = history[-1]
            required = ("generator_boundary", "prompt_sha256", "reference_manifest_sha256", "references", "returned_sources")
            missing = [key for key in required if not receipt.get(key)]
            if missing:
                failures.setdefault(relative_path(path, root), []).append(
                    f"slide {number}: missing {', '.join(missing)}"
                )
            if slide.get("status") in {"qa_passed", "approved_candidate", "publish_ready"} and (
                receipt.get("pixel_review_status") != "passed" or not receipt.get("qa_sha256")
            ):
                failures.setdefault(relative_path(path, root), []).append(f"slide {number}: QA is not pixel-hash-bound")
            if slide.get("status") == "publish_ready" and receipt.get("promotion_status") != "promoted":
                failures.setdefault(relative_path(path, root), []).append(f"slide {number}: promotion receipt missing")
            is_historical_draft = (
                slide.get("status") == "draft"
                and int(number) not in {int(value) for value in state.get("selected_slides") or []}
            )
            if is_historical_draft and _verified_superseded_attempt(path.parent, int(number), receipt):
                continue
            try:
                from pipeline.stages.codex_builtin_image_generation import _current_candidate, _approved_candidate, _assert_current_receipt
                candidate = _current_candidate(path.parent, state, int(number)) or _approved_candidate(path.parent, int(number))
                if candidate is None:
                    raise ValueError("receipt has no candidate")
                _assert_current_receipt(path.parent, state, candidate, require_review=slide.get("status") in {"qa_passed", "approved_candidate", "publish_ready"})
            except (OSError, ValueError, KeyError) as exc:
                failures.setdefault(relative_path(path, root), []).append(f"slide {number}: {exc}")
    return failures


def learning_approval_health_evidence(root: Path) -> list[str]:
    failures: list[str] = []
    for path in sorted(root.glob("memory/agentic/learning-proposals/*.json")):
        try:
            proposal = json.loads(path.read_text(encoding="utf-8"))
            event_path = root / "memory/agentic/learning-events" / f"{proposal.get('source_event_id')}.json"
            event = json.loads(event_path.read_text(encoding="utf-8")) if event_path.is_file() else {}
        except (OSError, json.JSONDecodeError):
            continue
        if (
            proposal.get("status") == "applied"
            and event.get("source") == "creator_feedback"
            and not proposal.get("creator_approved_by")
        ):
            failures.append(relative_path(path, root))
    return failures


def normalize_instruction_text(text: str) -> str:
    return re.sub(r"\s+", " ", text)


def instruction_has_phrase(text: str, phrase: str) -> bool:
    normalized_text = normalize_instruction_text(text)
    normalized_phrase = normalize_instruction_text(phrase)
    return normalized_phrase in normalized_text


def instruction_surface_evidence(root: Path) -> dict[str, Any]:
    missing_files: list[str] = []
    missing_phrases: dict[str, list[str]] = {}
    for relative in INSTRUCTION_SURFACE_FILES:
        path = root / relative
        if not path.exists():
            missing_files.append(relative)
            missing_phrases[relative] = list(REQUIRED_CLOSEOUT_PHRASES)
            continue
        text = path.read_text(encoding="utf-8")
        absent = [
            phrase
            for phrase in REQUIRED_CLOSEOUT_PHRASES
            if not instruction_has_phrase(text, phrase)
        ]
        if absent:
            missing_phrases[relative] = absent
    return {
        "required_files": INSTRUCTION_SURFACE_FILES,
        "required_phrases": REQUIRED_CLOSEOUT_PHRASES,
        "missing_files": missing_files,
        "missing_phrases": missing_phrases,
    }


def instruction_surface_contract_evidence(root: Path) -> dict[str, Any]:
    path = root / "config" / "instruction_surface_contract.json"
    if not path.exists():
        return {
            "contract_path": "config/instruction_surface_contract.json",
            "missing_contract": True,
            "missing_phrases": {},
            "banned_hits": {},
            "line_count_violations": {},
        }

    contract = json.loads(path.read_text(encoding="utf-8"))
    required = contract.get("required_phrases", [])
    banned_by_surface = contract.get("banned_phrases", {})
    retired_paths = contract.get("retired_paths", [])
    surfaces = contract.get("surfaces", INSTRUCTION_SURFACE_FILES)
    max_agents_lines = int(contract.get("max_agents_md_lines", 10_000))

    missing_phrases: dict[str, list[str]] = {}
    banned_hits: dict[str, list[str]] = {}
    line_count_violations: dict[str, int] = {}
    retired_hits = [
        relative
        for relative in retired_paths
        if (root / relative).exists()
    ]

    for relative in surfaces:
        surface_path = root / relative
        text = surface_path.read_text(encoding="utf-8") if surface_path.exists() else ""
        absent = [phrase for phrase in required if not instruction_has_phrase(text, phrase)]
        if absent:
            missing_phrases[relative] = absent

        hits = [
            phrase
            for phrase in banned_by_surface.get(relative, [])
            if instruction_has_phrase(text, phrase)
        ]
        if hits:
            banned_hits[relative] = hits

        if relative == "AGENTS.md":
            line_count = len(text.splitlines())
            if line_count > max_agents_lines:
                line_count_violations[relative] = line_count

    return {
        "contract_path": "config/instruction_surface_contract.json",
        "missing_contract": False,
        "missing_phrases": missing_phrases,
        "banned_hits": banned_hits,
        "line_count_violations": line_count_violations,
        "retired_hits": retired_hits,
    }


def relative_path(path: Path, root: Path) -> str:
    try:
        return path.relative_to(root).as_posix()
    except ValueError:
        return path.as_posix()


def wiki_pages(root: Path) -> list[Path]:
    wiki_root = root / "wiki"
    if not wiki_root.exists():
        return []
    return sorted(
        path
        for path in wiki_root.rglob("*.md")
        if path.name != "index.md"
    )


def md_files(root: Path, directory: str) -> list[Path]:
    base = root / directory
    if not base.exists():
        return []
    return sorted(path for path in base.rglob("*.md") if path.is_file())


def metadata_missing(path: Path) -> list[str]:
    text = path.read_text(encoding="utf-8")
    missing = []
    for key in WIKI_REQUIRED_METADATA:
        if key == "sources":
            if "sources:" not in text or not re.search(r"(?m)^sources:\s*\n(?:-\s+.+\n?)+", text):
                missing.append(key)
        elif not re.search(rf"(?m)^{re.escape(key)}:\s*.+$", text):
            missing.append(key)
    return missing


def declared_total_pages(index_text: str) -> int | None:
    match = re.search(r"(?m)^total_pages:\s*(\d+)\s*$", index_text)
    if not match:
        return None
    return int(match.group(1))


def make_check(
    check_id: str,
    status: str,
    severity: str,
    message: str,
    evidence: Any,
) -> dict[str, Any]:
    return {
        "id": check_id,
        "status": status,
        "severity": severity,
        "message": message,
        "evidence": evidence,
    }


def compiler_receipt_evidence(root: Path) -> dict[str, Any]:
    """Verify the last-write boundary for A4's multi-file compile transaction."""
    import hashlib
    from pipeline.stages.source_integrity import verify_provenance, verify_source_receipt

    receipt_dir = root / "output" / "receipts" / "a4-wiki"
    latest_page = root / "wiki" / "insights" / "latest-analysis.md"
    receipts = sorted(receipt_dir.glob("*.json")) if receipt_dir.exists() else []
    interrupted = (receipt_dir / ".pending.json").exists()
    errors: dict[str, list[str]] = {}
    loaded: list[tuple[Path, dict[str, Any]]] = []
    for path in receipts:
        current: list[str] = []
        try:
            receipt = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            errors[relative_path(path, root)] = [f"unreadable receipt: {exc}"]
            continue
        if not isinstance(receipt, dict):
            errors[relative_path(path, root)] = ["receipt must be an object"]
            continue
        loaded.append((path, receipt))
    def application_order(item: tuple[Path, dict[str, Any]]) -> tuple[float, int, str]:
        path, receipt = item
        raw = receipt.get("applied_at")
        try:
            applied = datetime.fromisoformat(str(raw).replace("Z", "+00:00")).timestamp()
        except (TypeError, ValueError):
            applied = 0.0
        try:
            modified = path.stat().st_mtime_ns
        except OSError:
            modified = 0
        return applied, modified, path.name

    active_path = max(loaded, key=application_order, default=(None, {}))[0]
    for path, receipt in loaded:
        current = []
        analysis = receipt.get("analysis_path")
        if not isinstance(analysis, str) or not (root / analysis).is_file():
            current.append("analysis_path is missing")
        elif receipt.get("analysis_sha256") and hashlib.sha256((root / analysis).read_bytes()).hexdigest() != receipt["analysis_sha256"]:
            current.append("analysis hash mismatch")
        provenance = receipt.get("source_provenance")
        if not isinstance(provenance, dict):
            current.append("source_provenance is missing")
        else:
            current.extend(verify_provenance(root, provenance))
        if receipt.get("status") != "applied":
            current.append("receipt status is not applied")
        output_hashes = receipt.get("output_hashes")
        if not isinstance(output_hashes, dict):
            current.append("output_hashes are missing")
        else:
            for target, expected in output_hashes.items():
                if not isinstance(target, str) or not isinstance(expected, str) or len(expected) != 64:
                    current.append("output_hashes contain an invalid target or digest")
                    continue
                if path == active_path:
                    target_path = root / target
                    if not target_path.is_file():
                        current.append(f"compiled target is missing: {target}")
                    elif hashlib.sha256(target_path.read_bytes()).hexdigest() != expected:
                        current.append(f"compiled target hash mismatch: {target}")
        analysis_json = receipt.get("analysis_json_path")
        if not isinstance(analysis_json, str) or not (root / analysis_json).is_file():
            current.append("analysis_json_path is missing")
        elif hashlib.sha256((root / analysis_json).read_bytes()).hexdigest() != receipt.get("analysis_json_sha256"):
            current.append("analysis JSON hash mismatch")
        source_receipt = receipt.get("source_receipt_path")
        normalized_sha256 = receipt.get("normalized_sha256")
        if source_receipt is not None or normalized_sha256 is not None:
            if not isinstance(source_receipt, str) or not (root / source_receipt).is_file():
                current.append("source_receipt_path is missing")
            else:
                try:
                    source_receipt_path = root / source_receipt
                    if hashlib.sha256(source_receipt_path.read_bytes()).hexdigest() != receipt.get("source_receipt_sha256"):
                        current.append("source receipt hash mismatch")
                    source_receipt_payload = json.loads(source_receipt_path.read_text(encoding="utf-8"))
                    normalized = source_receipt_payload.get("normalized_path")
                    if not isinstance(normalized, str):
                        current.append("source receipt does not name a normalized artifact")
                    else:
                        _verified, source_errors = verify_source_receipt(root, root / normalized)
                        current.extend(source_errors)
                        if source_receipt_payload.get("normalized_sha256") != normalized_sha256:
                            current.append("normalized source binding mismatch")
                except (OSError, json.JSONDecodeError):
                    current.append("source receipt is unreadable")
        if current:
            errors[relative_path(path, root)] = current
    return {"receipts": [relative_path(path, root) for path in receipts], "errors": errors,
            "active_receipt": relative_path(active_path, root) if active_path else None,
            "historical_receipts": [relative_path(path, root) for path, _ in loaded if path != active_path],
            "interrupted_compile": interrupted,
            "missing_receipt_for_compiled_page": latest_page.exists() and not receipts}


def collect_wiki_health(root: Path, today: date | None = None) -> dict[str, Any]:
    root = root.resolve()
    today = today or date.today()
    checks: list[dict[str, Any]] = []
    from pipeline.stages.source_integrity import validate_raw_snapshot_registry

    raw_registry_errors = validate_raw_snapshot_registry(root)
    checks.append(
        make_check(
            "raw_snapshot_registry",
            "FAIL" if raw_registry_errors else "PASS",
            "critical" if raw_registry_errors else "info",
            "Registered raw snapshots exist and retain their recorded hashes.",
            {"errors": raw_registry_errors},
        )
    )
    receipt_evidence = compiler_receipt_evidence(root)
    receipt_failed = bool(
        receipt_evidence["errors"]
        or receipt_evidence["missing_receipt_for_compiled_page"]
        or receipt_evidence["interrupted_compile"]
    )
    checks.append(
        make_check(
            "a4_compile_receipts",
            "FAIL" if receipt_failed else "PASS",
            "critical" if receipt_failed else "info",
            "Compiled A4 pages have hash-bound receipts whose provenance still verifies.",
            receipt_evidence,
        )
    )

    missing_surface = [
        path
        for path in REQUIRED_MEMORY_SURFACE.values()
        if not (root / path).exists()
    ]
    checks.append(
        make_check(
            "memory_surface",
            "FAIL" if missing_surface else "PASS",
            "critical" if missing_surface else "info",
            "Required wiki, memory, graph, and log surfaces exist.",
            {"missing": missing_surface},
        )
    )

    missing_pipeline = [
        path
        for path in ADVERTISED_PIPELINE_FILES
        if not (root / path).exists()
    ]
    checks.append(
        make_check(
            "advertised_pipeline_files",
            "FAIL" if missing_pipeline else "PASS",
            "critical" if missing_pipeline else "info",
            "AGENTS.md advertised pipeline entry points exist.",
            {"missing": missing_pipeline},
        )
    )

    instruction_evidence = instruction_surface_evidence(root)
    instruction_drift = bool(
        instruction_evidence["missing_files"]
        or instruction_evidence["missing_phrases"]
    )
    checks.append(
        make_check(
            "instruction_surface_sync",
            "FAIL" if instruction_drift else "PASS",
            "critical" if instruction_drift else "info",
            "AGENTS.md carries the required health and autopublish closeout commands.",
            instruction_evidence,
        )
    )

    contract_evidence = instruction_surface_contract_evidence(root)
    contract_drift = bool(
        contract_evidence["missing_contract"]
        or contract_evidence["missing_phrases"]
        or contract_evidence["banned_hits"]
        or contract_evidence["line_count_violations"]
        or contract_evidence["retired_hits"]
    )
    checks.append(
        make_check(
            "instruction_surface_contract",
            "FAIL" if contract_drift else "PASS",
            "critical" if contract_drift else "info",
            "Instruction surfaces match the current source hierarchy and avoid stale workflow claims.",
            contract_evidence,
        )
    )

    stale_hits: dict[str, list[str]] = {}
    boundary_missing: list[str] = []
    for relative in ACTIVE_CAROUSEL_GUIDANCE:
        path = root / relative
        text = path.read_text(encoding="utf-8") if path.is_file() else ""
        hits = [name for name, pattern in STALE_GUIDANCE_PATTERNS.items() if pattern.search(text)]
        if hits:
            stale_hits[relative] = hits
        if relative in {
            ".agents/skills/a-story-carousel-jam/SKILL.md",
            ".agents/skills/a-story-direct-visual-story/SKILL.md",
            "config/skills/carousel-jam-autopilot.md",
            "config/skills/illustration-carousel-framework.md",
            "docs/ai-ops-playbook.md",
        } and not (
            re.search(r"Codex.{0,80}(?:calls?|invokes?).{0,40}ImageGen", text, re.IGNORECASE | re.DOTALL)
            or re.search(r"Codex-owned.{0,40}ImageGen", text, re.IGNORECASE | re.DOTALL)
        ):
            boundary_missing.append(relative)
    checks.append(
        make_check(
            "active_carousel_guidance",
            "FAIL" if stale_hits else "PASS",
            "critical" if stale_hits else "info",
            "Active carousel guidance uses the native canvas, five-reference bundle, and current workflow.",
            {"stale_hits": stale_hits},
        )
    )
    checks.append(
        make_check(
            "codex_imagegen_boundary",
            "FAIL" if boundary_missing else "PASS",
            "critical" if boundary_missing else "info",
            "The active skill, workflow, and playbook agree that Codex invokes ImageGen.",
            {"missing_boundary_statement": boundary_missing},
        )
    )

    feedback_evidence = feedback_health_evidence(root, today)
    feedback_failed = bool(feedback_evidence["unsupported"] or feedback_evidence["blocking_events"])
    feedback_pending = bool(feedback_evidence["unresolved_records"])
    checks.append(
        make_check(
            "creator_feedback_lifecycle",
            "FAIL" if feedback_failed else "WARN" if feedback_pending else "PASS",
            "critical" if feedback_failed else "warning" if feedback_pending else "info",
            "Creator-feedback records are structurally valid; unresolved repair work remains visible until evaluated.",
            feedback_evidence,
        )
    )

    receipt_failures = generation_receipt_health_evidence(root, today)
    checks.append(
        make_check(
            "imagegen_attempt_receipts",
            "FAIL" if receipt_failures else "PASS",
            "critical" if receipt_failures else "info",
            "Advanced generation state has returned-source and pixel-QA provenance.",
            receipt_failures,
        )
    )

    approval_failures = learning_approval_health_evidence(root)
    checks.append(
        make_check(
            "creator_learning_approval",
            "FAIL" if approval_failures else "PASS",
            "critical" if approval_failures else "info",
            "Feedback-derived durable learning is never applied without creator approval.",
            {"unapproved_applied_proposals": approval_failures},
        )
    )

    working_path = root / "memory/working.md"
    working_text = working_path.read_text(encoding="utf-8") if working_path.is_file() else ""
    durable_lines = [
        line
        for line in working_text.splitlines()
        if line.strip()
        and not line.startswith(("#", "session_date:", "status:", "updated_at:"))
        and not (line.startswith("- ") and re.search(r"`[^`]+/[^`]*`", line))
    ]
    checks.append(
        make_check(
            "working_memory_pointer_only",
            "FAIL" if durable_lines else "PASS",
            "critical" if durable_lines else "info",
            "memory/working.md contains pointers only, not durable prose.",
            {"non_pointer_lines": durable_lines[:20]},
        )
    )

    missing_agentic = [
        path
        for path in REQUIRED_AGENTIC_OS_FILES
        if not (root / path).exists()
    ]
    checks.append(
        make_check(
            "agentic_os_surface",
            "FAIL" if missing_agentic else "PASS",
            "critical" if missing_agentic else "info",
            "Agentic OS control-plane files exist and are available to future sessions.",
            {"required": REQUIRED_AGENTIC_OS_FILES, "missing": missing_agentic},
        )
    )

    index_path = root / "wiki" / "index.md"
    pages = wiki_pages(root)
    if index_path.exists():
        index_text = index_path.read_text(encoding="utf-8")
        declared = declared_total_pages(index_text)
        checks.append(
            make_check(
                "wiki_index_total_pages",
                "FAIL" if declared != len(pages) else "PASS",
                "major" if declared != len(pages) else "info",
                "wiki/index.md total_pages matches actual wiki page count.",
                {"declared": declared, "actual": len(pages)},
            )
        )
        link_targets = [target.split("#", 1)[0] for target in re.findall(r"\[[^\]]+\]\(([^)]+)\)", index_text)]
        missing_links = [target for target in link_targets if target and "://" not in target and not (index_path.parent / target).exists()]
        checks.append(
            make_check(
                "wiki_index_links",
                "FAIL" if missing_links else "PASS",
                "major" if missing_links else "info",
                "wiki/index.md links resolve to existing wiki pages.",
                {"missing": missing_links, "checked": len(link_targets)},
            )
        )
        local_targets = [target for target in link_targets if target and "://" not in target]
        normalized_targets = [
            relative_path((index_path.parent / target).resolve(), root / "wiki")
            for target in local_targets
            if (index_path.parent / target).exists() and (index_path.parent / target).resolve() != index_path.resolve()
        ]
        duplicates = sorted({target for target in normalized_targets if normalized_targets.count(target) > 1})
        page_targets = {relative_path(path, root / "wiki") for path in pages}
        unlisted = sorted(page_targets - set(normalized_targets))
        checks.append(
            make_check(
                "wiki_index_membership",
                "FAIL" if duplicates or unlisted else "PASS",
                "major" if duplicates or unlisted else "info",
                "wiki/index.md lists each wiki page exactly once.",
                {"duplicates": duplicates, "unlisted": unlisted},
            )
        )
    else:
        checks.append(
            make_check(
                "wiki_index_total_pages",
                "FAIL",
                "critical",
                "wiki/index.md exists and declares total_pages.",
                {"declared": None, "actual": len(pages)},
            )
        )

    missing_metadata = {
        relative_path(path, root): missing
        for path in pages
        if (missing := metadata_missing(path))
    }
    checks.append(
        make_check(
            "wiki_markdown_metadata",
            "FAIL" if missing_metadata else "PASS",
            "major" if missing_metadata else "info",
            "Every wiki page has last_updated, confidence, and sources metadata.",
            missing_metadata,
        )
    )

    semantic_missing_confidence = {
        relative_path(path, root): ["confidence"]
        for path in md_files(root, "memory/semantic")
        if not re.search(r"(?m)^confidence:\s*(0(?:\.\d+)?|1(?:\.0+)?)\s*$", path.read_text(encoding="utf-8"))
    }
    checks.append(
        make_check(
            "semantic_memory_confidence",
            "FAIL" if semantic_missing_confidence else "PASS",
            "major" if semantic_missing_confidence else "info",
            "Semantic memory markdown files carry confidence scores.",
            semantic_missing_confidence,
        )
    )

    episodic_records = md_files(root, "memory/episodic")
    checks.append(
        make_check(
            "episodic_records",
            "WARN" if not episodic_records else "PASS",
            "major" if not episodic_records else "info",
            "Episodic memory has at least one permanent session record.",
            {"count": len(episodic_records)},
        )
    )

    logs = sorted((root / "logs").glob("*")) if (root / "logs").exists() else []
    checks.append(
        make_check(
            "session_logs",
            "WARN" if not logs else "PASS",
            "minor" if not logs else "info",
            "Session/log directory has written diagnostics.",
            {"count": len(logs)},
        )
    )

    status = "PASS"
    if any(check["status"] == "FAIL" for check in checks):
        status = "NEEDS_HEAL"
    elif any(check["status"] == "WARN" for check in checks):
        status = "PASS_WITH_WARNINGS"

    return {
        "schema_version": "1.0",
        "date": str(today),
        "workspace": str(root),
        "status": status,
        "summary": {
            "checks": len(checks),
            "failures": sum(check["status"] == "FAIL" for check in checks),
            "warnings": sum(check["status"] == "WARN" for check in checks),
            "wiki_pages": len(pages),
        },
        "checks": checks,
    }


def replace_or_insert_metadata(text: str, key: str, value: str) -> str:
    pattern = rf"(?m)^{re.escape(key)}:\s*.*$"
    replacement = f"{key}: {value}"
    if re.search(pattern, text):
        return re.sub(pattern, replacement, text, count=1)
    lines = text.splitlines()
    insert_at = 1 if lines and lines[0].startswith("#") else 0
    lines.insert(insert_at, replacement)
    return "\n".join(lines) + "\n"


def repair_wiki_index_metadata(root: Path, today: date | None = None) -> None:
    root = root.resolve()
    today = today or date.today()
    index_path = root / "wiki" / "index.md"
    index_path.parent.mkdir(parents=True, exist_ok=True)
    receipt_evidence = compiler_receipt_evidence(root)
    if (root / "wiki" / "insights" / "latest-analysis.md").exists() and (
        receipt_evidence["errors"]
        or receipt_evidence["missing_receipt_for_compiled_page"]
        or receipt_evidence["interrupted_compile"]
    ):
        raise ValueError("Refusing --fix-index until the A4 compile receipt chain passes")
    if index_path.exists():
        text = index_path.read_text(encoding="utf-8")
    else:
        text = "# Wiki Index\n\n"
    text = replace_or_insert_metadata(text, "last_updated", str(today))
    text = replace_or_insert_metadata(text, "total_pages", str(len(wiki_pages(root))))
    from pipeline.stages.source_integrity import atomic_write_text
    atomic_write_text(index_path, text)


def markdown_table_row(values: list[str]) -> str:
    return "| " + " | ".join(value.replace("\n", " ") for value in values) + " |"


def health_markdown(health: dict[str, Any]) -> str:
    lines = [
        "# Wiki Health Diagnostics",
        "",
        f"last_updated: {health['date']}",
        "confidence: 0.82",
        "sources:",
        "- AGENTS.md",
        "- wiki/index.md",
        "- memory/working.md",
        "- memory/graph.json",
        "",
        "## Status",
        "",
        f"Status: {health['status']}",
        f"Failures: {health['summary']['failures']}",
        f"Warnings: {health['summary']['warnings']}",
        f"Wiki pages: {health['summary']['wiki_pages']}",
        "",
        "## Checks",
        "",
        markdown_table_row(["Check", "Status", "Severity", "Message"]),
        markdown_table_row(["---", "---", "---", "---"]),
    ]
    for check in health["checks"]:
        lines.append(
            markdown_table_row(
                [
                    check["id"],
                    check["status"],
                    check["severity"],
                    check["message"],
                ]
            )
        )
    lines.extend(["", "## Evidence", ""])
    for check in health["checks"]:
        lines.extend(
            [
                f"### {check['id']}",
                "",
                "```json",
                json.dumps(check["evidence"], indent=2, ensure_ascii=False),
                "```",
                "",
            ]
        )
    return "\n".join(lines)


def heal_proposal_markdown(health: dict[str, Any]) -> str:
    actionable = [
        check for check in health["checks"] if check["status"] in {"FAIL", "WARN"}
    ]
    hypothesis = (
        "The listed failing or warning checks need investigation. This scan "
        "identifies symptoms; it does not establish their root causes."
        if actionable
        else "No repair is proposed: the latest run has no failing or warning checks."
    )
    lines = [
        "# HEAL Proposal - Wiki Health",
        "",
        f"last_updated: {health['date']}",
        "confidence: 0.78",
        "sources:",
        "- output/diagnostics/wiki-health report",
        "- AGENTS.md architecture contract",
        "- repository filesystem scan",
        "",
        "## Hypothesis",
        "",
        hypothesis,
        "",
        "## Evidence",
        "",
    ]
    if actionable:
        for check in actionable:
            lines.append(f"- {check['id']}: {check['status']} - {check['message']}")
    else:
        lines.append("- No failing or warning checks in the latest run.")
    lines.extend(["", "## Action", ""])
    if actionable:
        for check in actionable:
            lines.append(f"- Investigate `{check['id']}`, repair confirmed issues, and rerun `venv/bin/python scripts/wiki_health.py --write --fix-index`.")
    else:
        lines.append("- Keep running the health check at session close.")
    lines.extend(
        [
            "",
            "## Learning",
            "",
            "A session should not be considered closed until diagnostics, a HEAL proposal when needed, an episodic record, and a log entry exist.",
            "",
        ]
    )
    return "\n".join(lines)


def episode_markdown(health: dict[str, Any], session_note: str) -> str:
    note = session_note or "Wiki health check run."
    lines = [
        "# Session Health Episode",
        "",
        f"last_updated: {health['date']}",
        "confidence: 0.8",
        "sources:",
        "- scripts/wiki_health.py",
        "- output/diagnostics/wiki-health report",
        "",
        "## Session Note",
        "",
        note,
        "",
        "## Outcome",
        "",
        f"- status: {health['status']}",
        f"- failures: {health['summary']['failures']}",
        f"- warnings: {health['summary']['warnings']}",
        "",
    ]
    return "\n".join(lines)


def log_text(health: dict[str, Any]) -> str:
    return "\n".join(
        [
            f"date={health['date']}",
            f"status={health['status']}",
            f"failures={health['summary']['failures']}",
            f"warnings={health['summary']['warnings']}",
            f"wiki_pages={health['summary']['wiki_pages']}",
            "",
        ]
    )


def write_health_artifacts(
    root: Path,
    health: dict[str, Any],
    today: date | None = None,
    session_note: str = "",
) -> dict[str, Path]:
    root = root.resolve()
    today = today or date.fromisoformat(health["date"])
    stamp = str(today)
    paths = {
        "diagnostics": root / "output" / "diagnostics" / f"wiki-health-{stamp}.md",
        "heal_proposal": root / "memory" / "heal" / "proposals" / f"{stamp}-wiki-health.md",
        "episode": unique_path(root / "memory" / "episodic" / f"{stamp}-session-health.md"),
        "log": unique_path(root / "logs" / f"{stamp}-wiki-health.log"),
    }
    for path in paths.values():
        path.parent.mkdir(parents=True, exist_ok=True)

    paths["diagnostics"].write_text(health_markdown(health), encoding="utf-8")
    paths["heal_proposal"].write_text(heal_proposal_markdown(health), encoding="utf-8")
    paths["episode"].write_text(episode_markdown(health, session_note), encoding="utf-8")
    paths["log"].write_text(log_text(health), encoding="utf-8")

    refreshed_health = collect_wiki_health(root, today=today)
    paths["diagnostics"].write_text(health_markdown(refreshed_health), encoding="utf-8")
    paths["heal_proposal"].write_text(heal_proposal_markdown(refreshed_health), encoding="utf-8")
    paths["episode"].write_text(episode_markdown(refreshed_health, session_note), encoding="utf-8")
    paths["log"].write_text(log_text(refreshed_health), encoding="utf-8")
    return paths


def unique_path(path: Path) -> Path:
    if not path.exists():
        return path
    for index in range(2, 1000):
        candidate = path.with_name(f"{path.stem}-{index}{path.suffix}")
        if not candidate.exists():
            return candidate
    raise RuntimeError(f"Could not find a unique path for {path}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Lint wiki/memory health and write session diagnostics.")
    parser.add_argument("--workspace-root", type=Path, default=Path.cwd())
    parser.add_argument("--write", action="store_true", help="Write diagnostics, HEAL proposal, episode, and log files.")
    parser.add_argument("--fix-index", action="store_true", help="Repair wiki/index.md last_updated and total_pages metadata before checking.")
    parser.add_argument("--session-note", default="", help="Short note to include in memory/episodic.")
    args = parser.parse_args(argv)

    today = date.today()
    if args.fix_index:
        repair_wiki_index_metadata(args.workspace_root, today=today)
    health = collect_wiki_health(args.workspace_root, today=today)
    if args.write:
        paths = write_health_artifacts(
            args.workspace_root,
            health,
            today=today,
            session_note=args.session_note,
        )
        for name, path in paths.items():
            print(f"{name}: {path}")
    print(f"wiki health: {health['status']} ({health['summary']['failures']} failures, {health['summary']['warnings']} warnings)")
    return 1 if health["status"] == "NEEDS_HEAL" else 0


if __name__ == "__main__":
    raise SystemExit(main())
