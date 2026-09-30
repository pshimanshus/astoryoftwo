"""Small, deterministic writer for carousel work-in-progress packages.

The package is intentionally boring. Creative context, exact slide copy, the
format lock, and compact prompts are the only inputs needed before pixels
exist. Generation state and QA artifacts are written later by the image
handoff. Historical review rooms, scorecards, ledgers, and agent transcripts
do not belong in the default package.
"""

from __future__ import annotations

from copy import deepcopy
import hashlib
import json
import shutil
from datetime import date
from pathlib import Path
from typing import Any

from pipeline.stages.carousel_format_contract import (
    build_format_contract,
    write_format_contract,
)
from pipeline.stages.carousel_sequence import (
    SEQUENCE_CONTRACT,
    sequence_plan_issues,
    slide_sequence_issues,
    story_plan_issues,
)


HOT_PATH_ARTIFACTS = (
    "creative-context.json",
    "format-contract.json",
    "slides.json",
    "prompt-pack.json",
)

SUCCESSOR_FEEDBACK_SCHEMA_VERSION = "creator-correction/v3"


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


def _paths(items: list[Path], role: str) -> list[dict[str, str]]:
    return [{"path": str(path), "role": role} for path in items]


def _materialize_reference(
    out_dir: Path,
    raw_path: str | Path,
    *,
    category: str,
    cache: dict[tuple[str, str], str],
) -> str:
    """Copy a selected reference into the package and return its relative path."""

    source = Path(raw_path).expanduser()
    if not source.is_absolute():
        source = source.resolve()
    if not source.is_file():
        raise FileNotFoundError(f"Missing selected {category} reference: {source}")
    key = (str(source), category)
    if key in cache:
        return cache[key]
    digest = hashlib.sha256(source.read_bytes()).hexdigest()[:20]
    suffix = source.suffix.lower() or ".bin"
    relative = Path(".internal") / "references" / category / f"{digest}{suffix}"
    destination = out_dir / relative
    destination.parent.mkdir(parents=True, exist_ok=True)
    if not destination.exists():
        shutil.copy2(source, destination)
    value = relative.as_posix()
    cache[key] = value
    return value


def _localize_path_list(
    out_dir: Path,
    values: Any,
    *,
    category: str,
    cache: dict[tuple[str, str], str],
) -> list[str]:
    if not isinstance(values, list):
        return []
    return [
        _materialize_reference(out_dir, value, category=category, cache=cache)
        for value in values
        if str(value).strip()
    ]


def _localize_path_records(
    out_dir: Path,
    records: Any,
    *,
    category: str,
    cache: dict[tuple[str, str], str],
) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    for record in records if isinstance(records, list) else []:
        if not isinstance(record, dict) or not str(record.get("path") or "").strip():
            continue
        current = dict(record)
        current["path"] = _materialize_reference(
            out_dir,
            current["path"],
            category=category,
            cache=cache,
        )
        result.append(current)
    return result


def build_manifest(
    *,
    title: str,
    slug: str,
    story: str,
    image_paths: list[Path],
    identity_image_paths: list[Path],
    identity_reference_selection: dict[str, Any],
    identity_dossier: dict[str, Any],
    slide_count: int,
    today: date,
    requested_formats: list[str] | tuple[str, ...] | None = None,
    creative_baseline: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Build the creative-context payload (legacy function name retained)."""

    format_contract = build_format_contract(
        requested_formats,
        source=("creator_request" if requested_formats is not None else "instagram_post_default"),
    )
    context = {
        "schema_version": "carousel-creative-context/v2",
        "date": str(today),
        "slug": slug,
        "title": title,
        "channel": "@a.storyof.two",
        "source_story": story,
        "slide_count": slide_count,
        "status": "copy_and_format_locked",
        "requested_formats": list(format_contract["requested_formats"]),
        "format_contract": format_contract,
        "reference_images": _paths(image_paths, "current story reference"),
        "identity_references": _paths(
            identity_image_paths,
            "Aachu/Zuv identity and wardrobe reference",
        ),
        "identity_reference_selection": identity_reference_selection,
        "identity_dossier": {
            "path": identity_dossier.get("path"),
            "preflight_path": identity_dossier.get("preflight_path"),
            "contact_sheet_path": identity_dossier.get("contact_sheet_path"),
            "status": identity_dossier.get("status"),
        },
        "artifacts": list(HOT_PATH_ARTIFACTS),
    }
    if creative_baseline is not None:
        if "architecture" in creative_baseline:
            context["architecture"] = deepcopy(creative_baseline["architecture"])
        if "story_plan" in creative_baseline:
            issues = story_plan_issues(creative_baseline["story_plan"])
            if issues:
                raise ValueError("; ".join(issues))
            context["story_plan"] = deepcopy(creative_baseline["story_plan"])
            context["sequence_contract"] = SEQUENCE_CONTRACT
        if "research_refs" in creative_baseline:
            if not isinstance(creative_baseline["research_refs"], list):
                raise ValueError("research_refs must be a list")
            context["research_refs"] = deepcopy(creative_baseline["research_refs"])
    return context


def _minimal_slide(slide: dict[str, Any]) -> dict[str, Any]:
    """Write only canonical slide semantics; read legacy aliases without emitting them."""

    issues = slide_sequence_issues(slide)
    if issues:
        raise ValueError(f"Slide {slide.get('slide')}: " + "; ".join(issues))
    keep = (
        "slide",
        "role",
        "copy",
        "copy_mode",
        "beat_delta",
        "copy_image_relation",
        "emotion",
        "physical_action",
        "relationship_state",
        "send_reason",
        "camera",
        "focal_hierarchy",
        "setting",
        "wardrobe",
        "props",
        "source_images",
        "continuity_lock",
        "negative_prompt",
        "needs_physical_action",
        "hand_map",
        "spatial_topology",
        "visual_richness",
    )
    result = {key: slide[key] for key in keep if key in slide and slide[key] not in (None, "", [])}
    if not isinstance(result.get("slide"), int):
        result["slide"] = int(slide.get("slide", 0) or 0)
    result["copy"] = str(slide.get("copy") or "")
    result["physical_action"] = str(
        slide.get("physical_action") or slide.get("visual") or slide.get("scene") or ""
    )
    from pipeline.stages.carousel_generation_inputs import canonical_image_operation

    operation = canonical_image_operation(slide.get("image_operation"))
    if operation is not None:
        result["image_operation"] = operation
    return result


def _minimal_prompt_pack(prompt_pack: dict[str, Any]) -> dict[str, Any]:
    """Keep shared immutable generation inputs; slide prose belongs in slides.json."""

    profile = prompt_pack.get("style_profile")
    if not isinstance(profile, dict):
        raise ValueError("prompt pack requires one style_profile object")
    reference = profile.get("reference")
    if not isinstance(reference, dict):
        raise ValueError("prompt pack style_profile requires one reference object")
    return {
        "schema_version": "carousel-prompt-pack/v3",
        "brandmark": "@a.storyof.two",
        "style_profile": {
            "id": str(profile.get("id") or ""),
            "version": str(profile.get("version") or ""),
            "contract_sha256": str(profile.get("contract_sha256") or ""),
            "generation_prompt": str(profile.get("generation_prompt") or ""),
            "negative_prompt": str(profile.get("negative_prompt") or ""),
            "reference": {
                "path": str(reference.get("path") or ""),
                "sha256": str(reference.get("sha256") or ""),
                "attachment_count": int(reference.get("attachment_count") or 0),
            },
        },
        "identity_reference_images": list(prompt_pack.get("identity_reference_images") or []),
    }


def write_package(out_dir: Path, manifest: dict[str, Any], package: dict[str, Any]) -> None:
    """Write only the pre-proof hot-path contract."""

    slides = [_minimal_slide(slide) for slide in package.get("slides", [])]
    if not slides or any(not slide.get("physical_action") for slide in slides):
        raise ValueError("Every carousel slide needs one visible physical scene.")
    issues = sequence_plan_issues(manifest, slides)
    if issues:
        raise ValueError("Carousel sequence: " + "; ".join(issues))
    if "research_refs" in manifest and not isinstance(manifest["research_refs"], list):
        raise ValueError("research_refs must be a list")
    out_dir.mkdir(parents=True, exist_ok=True)
    contract = manifest.get("format_contract") if isinstance(manifest, dict) else None
    requested = contract.get("requested_formats") if isinstance(contract, dict) else None
    source = str(contract.get("source") or "package") if isinstance(contract, dict) else "package"
    write_format_contract(out_dir, requested, source=source, replace=True)

    cache: dict[tuple[str, str], str] = {}
    creative_context = deepcopy(manifest)
    if "story_plan" in creative_context:
        creative_context["sequence_contract"] = SEQUENCE_CONTRACT
    creative_context["reference_images"] = _localize_path_records(
        out_dir,
        creative_context.get("reference_images"),
        category="story",
        cache=cache,
    )
    creative_context["identity_references"] = _localize_path_records(
        out_dir,
        creative_context.get("identity_references"),
        category="identity",
        cache=cache,
    )
    selection = creative_context.get("identity_reference_selection")
    if isinstance(selection, dict):
        selection["selected_references"] = _localize_path_records(
            out_dir,
            selection.get("selected_references"),
            category="identity",
            cache=cache,
        )
    creative_context.pop("format_contract", None)
    write_json(out_dir / "creative-context.json", creative_context)

    for slide in slides:
        slide["source_images"] = _localize_path_list(
            out_dir,
            slide.get("source_images"),
            category="story",
            cache=cache,
        )
        if not slide["source_images"]:
            slide.pop("source_images", None)
    write_json(out_dir / "slides.json", slides)
    prompt_pack = deepcopy(package.get("prompt_pack", {}))
    profile = prompt_pack.get("style_profile")
    if not isinstance(profile, dict) or not isinstance(profile.get("reference"), dict):
        raise ValueError("prompt pack requires one style_profile reference")
    reference = profile["reference"]
    reference["path"] = _materialize_reference(
        out_dir,
        reference.get("path"),
        category="style",
        cache=cache,
    )
    localized_style = out_dir / reference["path"]
    actual_style_sha256 = "sha256:" + hashlib.sha256(localized_style.read_bytes()).hexdigest()
    if actual_style_sha256 != str(reference.get("sha256") or ""):
        raise ValueError("Localized style reference bytes do not match the active style profile.")
    prompt_pack["identity_reference_images"] = _localize_path_list(
        out_dir,
        prompt_pack.get("identity_reference_images"),
        category="identity",
        cache=cache,
    )
    write_json(
        out_dir / "prompt-pack.json",
        _minimal_prompt_pack(prompt_pack),
    )

    # Import at the write boundary so the package writer remains independent of
    # the image lifecycle module during module import. Every new package starts
    # with the canonical compact v3 state; legacy v2 is read-only.
    from pipeline.stages.codex_builtin_image_generation import initialize_generation_state

    initialize_generation_state(out_dir)


def write_successor_feedback(
    out_dir: Path,
    document: dict[str, Any],
) -> None:
    """Attach unresolved inherited feedback to a newly created v3 package.

    This runs only after ``write_package`` has initialized fresh generation
    state. It deliberately accepts no media, receipts, QA, or state from the
    archived source package.
    """

    if document.get("schema_version") != SUCCESSOR_FEEDBACK_SCHEMA_VERSION:
        raise ValueError("successor feedback must use creator-correction/v3")
    events = document.get("events")
    if not isinstance(events, list) or any(not isinstance(item, dict) for item in events):
        raise ValueError("successor feedback requires an events array")
    feedback_ids = [str(item.get("feedback_id") or "") for item in events]
    if any(not value for value in feedback_ids) or len(feedback_ids) != len(set(feedback_ids)):
        raise ValueError("successor feedback identities must be present and unique")
    adoption = document.get("successor_adoption")
    if not isinstance(adoption, dict):
        raise ValueError("successor feedback requires adoption metadata")
    if list(adoption.get("carried_feedback_ids") or []) != feedback_ids:
        raise ValueError("successor adoption carried IDs must match its event identities")
    source_feedback_ids: list[str] = []
    for event in events:
        exact = str(event.get("user_instruction_exact") or "")
        exact_sha256 = "sha256:" + hashlib.sha256(exact.encode("utf-8")).hexdigest()
        provenance = event.get("adoption_provenance")
        if not exact or str(event.get("user_instruction_sha256") or "") != exact_sha256:
            raise ValueError("successor feedback must preserve exact creator wording and hash")
        if not isinstance(provenance, dict):
            raise ValueError("successor feedback requires source adoption provenance")
        source_feedback_id = str(provenance.get("source_feedback_id") or "")
        source_feedback_ids.append(source_feedback_id)
        if not source_feedback_id or source_feedback_id == event["feedback_id"]:
            raise ValueError("successor feedback must use a fresh destination identity")
        if str(provenance.get("source_user_instruction_sha256") or "") != exact_sha256:
            raise ValueError("successor feedback provenance must bind the source wording hash")
        if not str(provenance.get("source_package_path") or ""):
            raise ValueError("successor feedback provenance requires source_package_path")
        if event.get("learning_event_id") != f"event-feedback-{event['feedback_id']}":
            raise ValueError("successor feedback requires a fresh linked LearningEvent identity")
        eval_task_ids = event.get("eval_task_ids")
        if not isinstance(eval_task_ids, list) or len(eval_task_ids) != 1:
            raise ValueError("successor feedback requires one fresh eval identity")
    if list(adoption.get("source_feedback_ids") or []) != source_feedback_ids:
        raise ValueError("successor adoption source IDs must match event provenance")
    target = Path(out_dir) / "creator-correction.json"
    if target.exists() or target.is_symlink():
        raise ValueError("successor feedback target already exists")
    temporary = target.with_name(target.name + ".tmp")
    write_json(temporary, document)
    temporary.replace(target)
