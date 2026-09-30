"""Single local builder for the @a.storyof.two carousel hot path.

This module creates the copy/format/prompt contract. It does not pretend that
planning artifacts are visual proof and it does not run an agent room. Real
image generation, pixel QA, creator proof approval, and final promotion happen
in :mod:`codex_builtin_image_generation`.
"""

from __future__ import annotations

import hashlib
import json
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any

from pipeline.stages.c1_illustration_carousel import (
    normalize_image_paths,
    slugify_title,
    validate_slide_count,
)
from pipeline.stages.carousel_contract import (
    load_active_illustration_style_profile,
    resolve_style_profile_reference_path,
    style_profile_contract_sha256,
)
from pipeline.stages.carousel_lanes import (
    IDENTITY_DOSSIER_PATH,
    build_identity_reference_selection,
    build_slides,
    discover_identity_images,
    infer_title,
    select_identity_reference_bundle,
)
from pipeline.stages.carousel_package_writer import (
    build_manifest,
    write_package,
    write_successor_feedback,
)
from pipeline.stages.carousel_sequence import (
    sequence_plan_issues,
    slide_sequence_issues,
    story_plan_issues,
)
from pipeline.stages.carousel_visual_storytelling import physical_action_issue
from pipeline.stages.carousel_visual_integrity import (
    build_hand_ownership_map,
    build_spatial_topology_contract,
    build_visual_richness_contract,
)


MAX_IMAGEGEN_REFERENCE_ATTACHMENTS = 5
WORKSPACE_ROOT = Path(__file__).resolve().parents[2]
# Declining a durable cross-package learning proposal does not resolve the
# package correction that produced it.  Only terminal correction decisions are
# omitted from successor adoption.
TERMINAL_FEEDBACK_STATUSES = frozenset({"promoted", "rejected"})


def _json_object(path: Path, *, label: str) -> dict[str, Any]:
    if path.is_symlink() or not path.is_file():
        raise ValueError(f"{label} must be a regular JSON file: {path}")
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValueError(f"{label} must contain valid UTF-8 JSON: {path}") from exc
    if not isinstance(payload, dict):
        raise ValueError(f"{label} must contain one JSON object: {path}")
    return payload


def _workspace_for_package(package_dir: Path) -> Path:
    for ancestor in package_dir.parents:
        relative = package_dir.relative_to(ancestor)
        if relative.parts[:2] == ("output", "carousels"):
            return ancestor
    return WORKSPACE_ROOT


def _workspace_path(path: Path, workspace: Path) -> str:
    try:
        return path.relative_to(workspace).as_posix()
    except ValueError:
        return str(path)


def _feedback_text_sha256(value: str) -> str:
    return "sha256:" + hashlib.sha256(value.encode("utf-8")).hexdigest()


def _unresolved_feedback_record(
    record: dict[str, Any],
    *,
    source_package_path: str,
    origin: str,
    source_learning_event_id: str | None,
) -> dict[str, Any]:
    """Reset inherited evidence while preserving exact source provenance.

    The source feedback ID is retained temporarily so adoption can deduplicate
    and remap supersession relationships.  A successor-scoped ID is minted
    after the destination package path is known.
    """

    exact = str(record.get("user_instruction_exact") or "")
    feedback_id = str(record.get("feedback_id") or "")
    if not exact or not feedback_id:
        raise ValueError("Live successor feedback requires exact wording and a feedback_id")
    kind = str(record.get("kind") or "correction")
    scope = str(record.get("scope") or "package")
    slides = sorted({int(value) for value in record.get("slides") or []})
    effect = str(record.get("generation_effect") or "")
    if effect not in {"none", "slide_local", "shared"} or (
        effect == "none" and kind in {"correction", "rejection"}
    ):
        effect = (
            "slide_local"
            if slides and scope in {"slide", "copy", "asset"}
            else "shared" if kind in {"correction", "rejection"} else "none"
        )
    primary_diagnosis = str(record.get("primary_diagnosis") or "provenance_qa")
    must_change = list(record.get("must_change") or [])
    root_cause = str(record.get("root_cause") or "").strip()
    if not root_cause or root_cause == primary_diagnosis:
        repair_summary = "; ".join(str(value) for value in must_change if str(value).strip())
        root_cause = (
            f"Creator-reported {primary_diagnosis} failure in the archived package remains unresolved. "
            + (f"Required repair: {repair_summary}" if repair_summary else "Specific cause requires review of the source evidence.")
        )
    desired_behavior = str(record.get("desired_behavior") or "").strip() or (
        "; ".join(str(value) for value in must_change if str(value).strip()) or None
    )
    source_instruction_sha256 = str(record.get("user_instruction_sha256") or "")
    computed_instruction_sha256 = _feedback_text_sha256(exact)
    if source_instruction_sha256 and source_instruction_sha256 != computed_instruction_sha256:
        raise ValueError("Source feedback exact wording hash does not match its text")
    source_instruction_sha256 = source_instruction_sha256 or computed_instruction_sha256
    return {
        "feedback_id": feedback_id,
        "captured_at": str(record.get("captured_at") or ""),
        "user_instruction_exact": exact,
        "user_instruction_sha256": _feedback_text_sha256(exact),
        "kind": kind,
        "scope": scope,
        "slide_number": slides[0] if len(slides) == 1 else None,
        "slides": slides,
        "asset_sha256": record.get("asset_sha256"),
        "primary_diagnosis": primary_diagnosis,
        "secondary_diagnoses": list(record.get("secondary_diagnoses") or []),
        "root_cause": root_cause,
        "desired_behavior": desired_behavior,
        "must_change": must_change,
        "must_preserve": list(record.get("must_preserve") or []),
        "affected_artifacts": list(record.get("affected_artifacts") or []),
        "repair_operations": list(record.get("repair_operations") or []),
        "verification_assertions": list(record.get("verification_assertions") or []),
        "action_taken": None,
        "resolution_evidence": [],
        "learning_event_id": source_learning_event_id or record.get("learning_event_id"),
        "learning_proposal_id": None,
        "eval_task_ids": [],
        "eval_waiver_reason": None,
        "status": "diagnosed",
        "generation_effect": effect,
        "learning_disposition": (
            record.get("learning_disposition")
            or ("declined" if record.get("status") == "learning_declined" else None)
        ),
        "supersedes_feedback_id": record.get("supersedes_feedback_id"),
        "historical_only": False,
        "adoption_provenance": {
            "origin": origin,
            "source_package_path": source_package_path,
            "source_feedback_id": feedback_id,
            "source_learning_event_id": source_learning_event_id,
            "source_eval_task_ids": list(record.get("eval_task_ids") or []),
            "source_status": str(record.get("status") or "captured"),
            "source_captured_at": str(record.get("captured_at") or ""),
            "source_user_instruction_sha256": source_instruction_sha256,
            "source_supersedes_feedback_id": record.get("supersedes_feedback_id"),
            "old_resolution_evidence_discarded": True,
        },
    }


def _successor_feedback_id(
    *,
    successor_package_id: str,
    source_package_path: str,
    source_feedback_id: str,
) -> str:
    identity = {
        "schema": "successor-feedback-adoption/v1",
        "successor_package_id": successor_package_id,
        "source_package_path": source_package_path,
        "source_feedback_id": source_feedback_id,
    }
    digest = hashlib.sha256(
        json.dumps(identity, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()
    return "fb-" + digest[:16]


def _scope_successor_feedback_records(
    records: list[dict[str, Any]],
    *,
    successor_package_id: str,
) -> list[dict[str, Any]]:
    """Mint destination-local feedback, LearningEvent, and eval identities."""

    source_to_successor: dict[str, str] = {}
    for record in records:
        provenance = record.get("adoption_provenance")
        if not isinstance(provenance, dict):
            raise ValueError("successor feedback requires adoption provenance")
        source_feedback_id = str(provenance.get("source_feedback_id") or "")
        source_package_path = str(provenance.get("source_package_path") or "")
        if not source_feedback_id or not source_package_path:
            raise ValueError("successor feedback provenance is incomplete")
        source_to_successor[source_feedback_id] = _successor_feedback_id(
            successor_package_id=successor_package_id,
            source_package_path=source_package_path,
            source_feedback_id=source_feedback_id,
        )

    from evals.feedback_cases import feedback_eval_task_id

    captured_at = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    adopted: list[dict[str, Any]] = []
    for record in records:
        current = dict(record)
        provenance = dict(current["adoption_provenance"])
        source_feedback_id = str(provenance["source_feedback_id"])
        feedback_id = source_to_successor[source_feedback_id]
        source_supersedes = provenance.get("source_supersedes_feedback_id")
        current.update(
            {
                "feedback_id": feedback_id,
                "captured_at": captured_at,
                "learning_event_id": f"event-feedback-{feedback_id}",
                "eval_task_ids": [feedback_eval_task_id(feedback_id)],
                "supersedes_feedback_id": source_to_successor.get(
                    str(source_supersedes or "")
                ),
                "adoption_provenance": provenance,
            }
        )
        adopted.append(current)
    return adopted


def _initialize_successor_feedback_lifecycle(
    package_dir: Path,
    *,
    workspace: Path,
    package_id: str,
    records: list[dict[str, Any]],
) -> None:
    """Create destination-local eval cases and LearningEvents for adoption."""

    from evals.feedback_cases import ensure_feedback_case
    from pipeline.agentic.learning_loop import capture_learning_event

    for record in records:
        case = ensure_feedback_case(workspace, package_dir, record)
        expected_task_ids = list(record.get("eval_task_ids") or [])
        if expected_task_ids != [case["task_id"]]:
            raise ValueError("successor feedback eval identity does not match its case")
        provenance = dict(record.get("adoption_provenance") or {})
        capture_learning_event(
            workspace,
            source="creator_feedback",
            summary=str(
                record.get("root_cause")
                or record.get("primary_diagnosis")
                or record["user_instruction_exact"]
            ),
            evidence_paths=[f"{package_id}/creator-correction.json"],
            event_id=str(record["learning_event_id"]),
            user_instruction_exact=str(record["user_instruction_exact"]),
            diagnosis=str(record.get("primary_diagnosis") or "provenance_qa"),
            scope=str(record.get("scope") or "package"),
            package_path=package_id,
            feedback_status="diagnosed",
            resolution_evidence=[],
            eval_disposition="background",
            supersedes_event_id=(
                f"event-feedback-{record['supersedes_feedback_id']}"
                if record.get("supersedes_feedback_id")
                else None
            ),
            feedback_metadata={
                "feedback_id": record["feedback_id"],
                "kind": record.get("kind"),
                "slides": list(record.get("slides") or []),
                "asset_sha256": record.get("asset_sha256"),
                "primary_diagnosis": record.get("primary_diagnosis"),
                "root_cause": record.get("root_cause"),
                "desired_behavior": record.get("desired_behavior"),
                "must_change": list(record.get("must_change") or []),
                "must_preserve": list(record.get("must_preserve") or []),
                "verification_assertions": list(
                    record.get("verification_assertions") or []
                ),
                "generation_effect": record.get("generation_effect"),
                "learning_disposition": record.get("learning_disposition"),
                "eval_task_ids": expected_task_ids,
                "adoption_provenance": provenance,
            },
        )


def _learning_event_feedback_record(payload: dict[str, Any]) -> dict[str, Any]:
    metadata = payload.get("feedback_metadata")
    if not isinstance(metadata, dict):
        metadata = {}
    return {
        "feedback_id": metadata.get("feedback_id"),
        "captured_at": payload.get("created_at"),
        "user_instruction_exact": payload.get("user_instruction_exact"),
        "user_instruction_sha256": metadata.get("user_instruction_sha256"),
        "kind": metadata.get("kind") or "correction",
        "scope": payload.get("scope") or "package",
        "slides": metadata.get("slides") or [],
        "asset_sha256": metadata.get("asset_sha256"),
        "primary_diagnosis": metadata.get("primary_diagnosis") or payload.get("diagnosis"),
        "root_cause": metadata.get("root_cause"),
        "desired_behavior": metadata.get("desired_behavior"),
        "must_change": metadata.get("must_change") or [],
        "must_preserve": metadata.get("must_preserve") or [],
        "verification_assertions": metadata.get("verification_assertions") or [],
        "generation_effect": metadata.get("generation_effect"),
        "supersedes_feedback_id": metadata.get("supersedes_feedback_id"),
        "eval_task_ids": metadata.get("eval_task_ids") or [],
        "status": payload.get("feedback_status") or "captured",
    }


def load_successor_adoption(
    source_package: str | Path,
) -> tuple[Path, Path, dict[str, Any], list[dict[str, Any]]]:
    """Validate one archived source and collect its still-live feedback."""

    from pipeline.stages.carousel_generation_state import archived_package_read_only_reason
    from pipeline.stages.carousel_visual_storytelling import creator_feedback_records

    supplied = Path(source_package).expanduser()
    if supplied.is_symlink():
        raise ValueError("--successor-of cannot reference a symlink")
    try:
        source = supplied.resolve(strict=True)
    except FileNotFoundError as exc:
        raise ValueError(f"Archived successor source not found: {supplied}") from exc
    if not source.is_dir():
        raise ValueError("--successor-of must reference an archived package directory")
    if not archived_package_read_only_reason(source):
        raise ValueError("--successor-of must reference an archived/read-only v2 package")
    source_context = _json_object(
        source / "creative-context.json",
        label="Archived creative-context.json",
    )
    workspace = _workspace_for_package(source)
    source_package_path = _workspace_path(source, workspace)
    carried: list[dict[str, Any]] = []
    seen: set[str] = set()
    for record in creator_feedback_records(source):
        feedback_id = str(record.get("feedback_id") or "")
        if (
            not feedback_id
            or bool(record.get("historical_only"))
            or str(record.get("status") or "") in TERMINAL_FEEDBACK_STATUSES
        ):
            continue
        carried.append(
            _unresolved_feedback_record(
                record,
                source_package_path=source_package_path,
                origin="package_creator_correction",
                source_learning_event_id=(
                    str(record.get("learning_event_id"))
                    if record.get("learning_event_id")
                    else None
                ),
            )
        )
        seen.add(feedback_id)

    event_root = workspace / "memory" / "agentic" / "learning-events"
    for path in sorted(event_root.glob("*.json")) if event_root.is_dir() else []:
        if path.is_symlink() or not path.is_file():
            continue
        payload = _json_object(path, label="Creator feedback LearningEvent")
        if payload.get("source") != "creator_feedback":
            continue
        package_value = str(payload.get("package_path") or "")
        candidate = Path(package_value).expanduser()
        candidate = candidate if candidate.is_absolute() else workspace / candidate
        if candidate.resolve(strict=False) != source:
            continue
        feedback = _learning_event_feedback_record(payload)
        feedback_id = str(feedback.get("feedback_id") or "")
        if not feedback_id or feedback_id in seen:
            continue
        if str(payload.get("feedback_status") or "") in TERMINAL_FEEDBACK_STATUSES:
            continue
        carried.append(
            _unresolved_feedback_record(
                feedback,
                source_package_path=source_package_path,
                origin="workspace_learning_event",
                source_learning_event_id=str(payload.get("event_id") or path.stem),
            )
        )
        seen.add(feedback_id)
    return source, workspace, source_context, carried


def load_creative_baseline(path: str | Path | None) -> dict[str, Any] | None:
    if not path:
        return None
    baseline_path = Path(path).expanduser()
    if not baseline_path.is_file():
        raise FileNotFoundError(f"Creative brief not found: {baseline_path}")
    payload = json.loads(baseline_path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("Creative brief must be a JSON object.")
    raw_slides = payload.get("slides")
    if isinstance(raw_slides, list):
        for index, slide in enumerate(raw_slides, start=1):
            if not isinstance(slide, dict) or "source_images" not in slide:
                continue
            values = slide.get("source_images")
            if not isinstance(values, list):
                raise ValueError(f"Creative brief slide {index} source_images must be a list.")
            resolved: list[str] = []
            for value in values:
                source = Path(str(value)).expanduser()
                if not source.is_absolute():
                    source = baseline_path.parent / source
                resolved.append(str(source))
            slide["source_images"] = resolved
    return payload


def slides_from_creative_baseline(
    baseline: dict[str, Any] | None,
    image_paths: list[Path],
) -> list[dict[str, Any]] | None:
    if not baseline:
        return None
    if "story_plan" in baseline:
        issues = story_plan_issues(baseline["story_plan"])
        if issues:
            raise ValueError("Creative brief " + "; ".join(issues))
    raw_slides = baseline.get("slides")
    if not isinstance(raw_slides, list) or not raw_slides:
        return None
    slides: list[dict[str, Any]] = []
    for index, item in enumerate(raw_slides, start=1):
        if not isinstance(item, dict):
            raise ValueError(f"Creative brief slide {index} must be an object.")
        # An explicit empty copy is authoritative; never resurrect a legacy
        # text alias over an approved wordless beat.
        copy = item.get("copy", item.get("text", ""))
        issues = slide_sequence_issues({**item, "copy": copy})
        if issues:
            raise ValueError(f"Creative brief slide {index}: " + "; ".join(issues))
        physical_action = str(
            item.get("physical_action") or item.get("visual") or item.get("scene") or ""
        )
        if not physical_action:
            raise ValueError(
                f"Creative brief slide {index} needs a visible physical action."
            )
        action_issue = physical_action_issue(
            physical_action,
            copy=copy,
        )
        if action_issue:
            raise ValueError(f"Creative brief slide {index} {action_issue}.")
        local_sources = item.get("source_images")
        if local_sources is not None and not isinstance(local_sources, list):
            raise ValueError(f"Creative brief slide {index} source_images must be a list.")
        source_images = [
            str(value)
            for value in (image_paths if local_sources is None else local_sources)
        ]
        raw_camera = item.get("camera")
        if isinstance(raw_camera, dict):
            camera: dict[str, Any] = dict(raw_camera)
        else:
            camera = {}
            camera_position = str(
                raw_camera or item.get("composition") or item.get("pose") or ""
            ).strip()
            if camera_position:
                camera["position"] = camera_position
        raw_setting = item.get("setting")
        if isinstance(raw_setting, dict):
            setting: dict[str, Any] = dict(raw_setting)
        else:
            setting = {}
            place = str(raw_setting or item.get("background") or "").strip()
            if place:
                setting["place"] = place
        raw_richness = item.get("visual_richness")
        if raw_richness is not None and not isinstance(raw_richness, dict):
            raise ValueError(f"Creative brief slide {index} visual_richness must be an object.")
        if isinstance(raw_richness, dict):
            visual_richness = dict(raw_richness)
            visual_richness.pop("scene_action_binding", None)
            visual_richness.setdefault("posed_portrait_allowed", False)
            visual_richness.setdefault("decorative_clutter_allowed", False)
        else:
            visual_richness = build_visual_richness_contract(physical_action)

        slide = {
            "slide": index,
            "role": str(item.get("role") or "story_beat"),
            "copy": copy,
            "physical_action": physical_action,
            "relationship_state": str(
                item.get("relationship_state") or item.get("emotion") or ""
            ),
            "emotion": str(item.get("emotion") or ""),
            "camera": camera,
            "focal_hierarchy": str(item.get("focal_hierarchy") or ""),
            "setting": setting,
            "visual_richness": visual_richness,
            "source_images": source_images,
        }
        for key in ("copy_mode", "beat_delta", "copy_image_relation"):
            if key in item:
                slide[key] = item[key]
        send_reason = str(
            item.get("send_reason")
            or item.get("save_reason")
            or item.get("cta_intent")
            or item.get("cta")
            or ""
        ).strip()
        if send_reason:
            slide["send_reason"] = send_reason
        for key in (
            "wardrobe",
            "props",
            "continuity_lock",
            "negative_prompt",
            "hand_map",
            "spatial_topology",
            "scene_contract",
        ):
            value = item.get(key)
            if value not in (None, "", []):
                if key in {"hand_map", "spatial_topology"} and not isinstance(value, dict):
                    raise ValueError(f"Creative brief slide {index} {key} must be an object.")
                slide[key] = value
        slides.append(slide)
    issues = sequence_plan_issues(baseline, slides)
    if issues:
        raise ValueError("Creative brief sequence: " + "; ".join(issues))
    return slides


def build_package(
    *,
    story: str,
    image_paths: list[Path],
    identity_image_paths: list[Path],
    identity_reference_selection: dict[str, Any],
    identity_dossier: dict[str, Any],
    slide_count: int | None,
    creative_baseline: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Create one human-readable slide plan and its compact prompt pack."""

    profile = load_active_illustration_style_profile(project_root=WORKSPACE_ROOT)
    style_reference = resolve_style_profile_reference_path(
        profile,
        project_root=WORKSPACE_ROOT,
    )
    slides = slides_from_creative_baseline(creative_baseline, image_paths)
    if slides is None:
        slides = build_slides(story, image_paths, slide_count)
    for slide in slides:
        slide.setdefault(
            "physical_action",
            str(slide.get("visual") or slide.get("scene") or ""),
        )
        slide.setdefault("relationship_state", str(slide.get("emotion") or ""))
        scene = str(slide.get("physical_action") or slide.get("visual") or "")
        slide.setdefault("hand_map", build_hand_ownership_map(scene))
        slide.setdefault("spatial_topology", build_spatial_topology_contract(scene))
        slide.setdefault("visual_richness", build_visual_richness_contract(scene))
        for retired in ("visual", "scene", "composition", "pose", "background"):
            slide.pop(retired, None)
    attachment_count = len(identity_image_paths) + int(profile["reference"]["attachment_count"])
    if attachment_count > MAX_IMAGEGEN_REFERENCE_ATTACHMENTS:
        raise ValueError(
            "Image generation supports at most five identity and style attachments; "
            f"selected {len(identity_image_paths)} identity and "
            f"{profile['reference']['attachment_count']} style."
        )
    return {
        "slides": slides,
        "prompt_pack": {
            "schema_version": "carousel-prompt-pack/v3",
            # Placement remains top-right under config/rules/brandmark.md;
            # the compiler owns that direction, so the package stores no alias.
            "brandmark": "@a.storyof.two",
            "style_profile": {
                "id": profile["id"],
                "version": profile["version"],
                "contract_sha256": style_profile_contract_sha256(profile),
                "generation_prompt": profile["generation_prompt"],
                "negative_prompt": profile["negative_prompt"],
                "reference": {
                    "path": str(style_reference),
                    "sha256": profile["reference"]["sha256"],
                    "attachment_count": profile["reference"]["attachment_count"],
                },
            },
            "identity_reference_images": [str(path) for path in identity_image_paths],
        },
        "identity_reference_selection": identity_reference_selection,
        "identity_dossier": identity_dossier,
    }


def create_codex_native_carousel(
    *,
    story: str,
    image_paths: list[str | Path],
    identity_image_paths: list[str | Path] | None = None,
    title: str | None = None,
    slide_count: int | None = None,
    output_root: Path = Path("output") / "carousels",
    today: date | None = None,
    creative_baseline_path: str | Path | None = None,
    requested_formats: list[str] | None = None,
    successor_of: str | Path | None = None,
) -> Path:
    if not story.strip():
        raise ValueError("Story is required.")
    creative_baseline = load_creative_baseline(creative_baseline_path)
    successor_source: Path | None = None
    successor_workspace: Path | None = None
    source_context: dict[str, Any] | None = None
    carried_feedback: list[dict[str, Any]] = []
    if successor_of is not None:
        if (
            not creative_baseline
            or not isinstance(creative_baseline.get("slides"), list)
            or not creative_baseline["slides"]
        ):
            raise ValueError(
                "create --successor-of requires a real --creative-brief with non-empty slides"
            )
        (
            successor_source,
            successor_workspace,
            source_context,
            carried_feedback,
        ) = load_successor_adoption(successor_of)
    if creative_baseline and isinstance(creative_baseline.get("slides"), list):
        brief_slide_count = len(creative_baseline["slides"])
        if slide_count is not None and slide_count != brief_slide_count:
            raise ValueError(
                f"Creative brief contains {brief_slide_count} slides but --slide-count is "
                f"{slide_count}; refusing to discard or invent creator beats."
            )
        slide_count = brief_slide_count
        validate_slide_count(slide_count)
    elif slide_count is not None:
        validate_slide_count(slide_count)
    today = today or date.today()
    output_root = Path(output_root)
    story_paths = normalize_image_paths(image_paths)
    explicit_identity = identity_image_paths is not None
    identity_candidates = (
        normalize_image_paths(identity_image_paths or [])
        if explicit_identity
        else discover_identity_images(WORKSPACE_ROOT)
    )
    identity_paths = select_identity_reference_bundle(
        identity_candidates,
        explicit=explicit_identity,
    )
    selection = build_identity_reference_selection(
        candidate_paths=identity_candidates,
        selected_paths=identity_paths,
        explicit=explicit_identity,
    )
    identity_dossier = (
        {
            "status": "selected_generation_bundle",
            "path": str(IDENTITY_DOSSIER_PATH),
        }
        if not explicit_identity and identity_paths
        else {
            "status": "creator_selected" if identity_paths else "unavailable",
            "path": None,
        }
    )

    final_title = infer_title(story, title)
    dated_root = output_root / str(today)
    out_dir = dated_root / slugify_title(final_title)
    suffix = 2
    while out_dir.exists():
        out_dir = dated_root / f"{slugify_title(final_title)}-{suffix}"
        suffix += 1

    successor_target_workspace: Path | None = None
    successor_package_id: str | None = None
    source_feedback_ids: list[str] = []
    if successor_source is not None and successor_workspace is not None:
        resolved_output_root = output_root.expanduser().resolve()
        resolved_out_dir = out_dir.expanduser().resolve()
        try:
            resolved_out_dir.relative_to(successor_workspace)
            successor_target_workspace = successor_workspace
        except ValueError:
            discovered = _workspace_for_package(resolved_out_dir)
            successor_target_workspace = (
                resolved_output_root.parent
                if discovered == WORKSPACE_ROOT
                and WORKSPACE_ROOT not in resolved_out_dir.parents
                else discovered
            )
        successor_package_id = _workspace_path(
            resolved_out_dir, successor_target_workspace
        )
        source_feedback_ids = [
            str((item.get("adoption_provenance") or {}).get("source_feedback_id") or "")
            for item in carried_feedback
        ]
        carried_feedback = _scope_successor_feedback_records(
            carried_feedback,
            successor_package_id=successor_package_id,
        )

    package = build_package(
        story=story,
        image_paths=story_paths,
        identity_image_paths=identity_paths,
        identity_reference_selection=selection,
        identity_dossier=identity_dossier,
        slide_count=slide_count,
        creative_baseline=creative_baseline,
    )
    context = build_manifest(
        title=final_title,
        slug=out_dir.name,
        story=story,
        image_paths=story_paths,
        identity_image_paths=identity_paths,
        identity_reference_selection=selection,
        identity_dossier=identity_dossier,
        slide_count=len(package["slides"]),
        today=today,
        requested_formats=requested_formats,
        creative_baseline=creative_baseline,
    )
    context["identity_reference_status"] = (
        "attached" if identity_paths else "explicitly_unavailable"
    )
    if (
        successor_source is not None
        and successor_workspace is not None
        and source_context is not None
    ):
        source_context_bytes = (successor_source / "creative-context.json").read_bytes()
        context["lineage"] = {
            "relationship": "successor_of",
            "source_package_path": _workspace_path(
                successor_source, successor_workspace
            ),
            "source_package_slug": str(
                source_context.get("slug") or successor_source.name
            ),
            "source_creative_context_sha256": "sha256:"
            + hashlib.sha256(source_context_bytes).hexdigest(),
            "carried_feedback_ids": [
                item["feedback_id"] for item in carried_feedback
            ],
            "source_feedback_ids": source_feedback_ids,
        }
    write_package(out_dir, context, package)
    if successor_source is not None and successor_workspace is not None:
        if successor_target_workspace is None or successor_package_id is None:
            raise ValueError("successor lifecycle workspace was not resolved")
        write_successor_feedback(
            out_dir,
            {
                "schema_version": "creator-correction/v3",
                "package_id": successor_package_id,
                "successor_adoption": {
                    "source_package_path": _workspace_path(
                        successor_source, successor_workspace
                    ),
                    "carried_feedback_ids": [
                        item["feedback_id"] for item in carried_feedback
                    ],
                    "source_feedback_ids": source_feedback_ids,
                    "evidence_policy": (
                        "Archived receipts, QA, finals, resolution evidence, and eval claims "
                        "are not inherited."
                    ),
                },
                "events": carried_feedback,
            },
        )
        _initialize_successor_feedback_lifecycle(
            out_dir.resolve(),
            workspace=successor_target_workspace,
            package_id=successor_package_id,
            records=carried_feedback,
        )

    return out_dir


__all__ = [
    "build_manifest",
    "build_package",
    "create_codex_native_carousel",
    "load_creative_baseline",
    "load_successor_adoption",
    "slides_from_creative_baseline",
]
