"""
Quality spine for Codex-native illustrated carousel packages.

The creative pipeline builds the package. This module records what was expected,
what was produced, what reviewers checked, and what the wiki should remember.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Any

from PIL import Image

from pipeline.stages.carousel_format_contract import (
    expected_frame_bindings,
    expected_output_path,
    expected_output_relative_path,
    format_spec,
    locked_format_contract_fingerprint,
    locked_formats,
)
from pipeline.stages.carousel_style_consistency import prompt_style_drift_issues
from pipeline.stages.successful_carousel_standard import (
    SUCCESSFUL_CAROUSEL_STANDARD_PATH,
    evaluate_successful_carousel_standard,
)
from pipeline.stages.carousel_visual_storytelling import (
    VISUAL_STORY_READABILITY_KEY,
    current_creator_correction_fingerprint,
    current_generation_payload_fingerprint,
    director_author_id,
    director_creator_correction_fingerprint,
    director_event_fingerprint,
    director_generation_payload_fingerprint,
    director_review_provenance,
    director_reviewer_id,
    validate_director_storyboard,
    validate_frame_readability,
)


QUALITY_ARTIFACTS = {
    "run_ledger": "run-ledger.json",
    "stage_reviews": "stage-reviews.json",
    "final_audit": "final-audit.json",
    "wiki_update": "wiki-update.md",
    "visual_qa": "visual-qa.md",
}


def _current_generation_fingerprint_or_none(package_dir: Path) -> str | None:
    try:
        return current_generation_payload_fingerprint(package_dir)
    except ValueError:
        return None

BASE_ARTIFACTS = {
    "manifest": "manifest.json",
    "format_contract": "format-contract.json",
    "concept": "concept.json",
    "post_copy_visual_room": "post-copy-visual-room.json",
    "visual_debate": "visual-debate.json",
    "visual_plan_quality": "visual-plan-quality.json",
    "slides": "slides.json",
    "prompt_pack": "prompt-pack.json",
    "identity_dossier": "identity-dossier.json",
    "identity_generation_preflight": "identity-generation-preflight.md",
    "identity_face_contact_sheet": "identity-face-contact-sheet.jpg",
    "identity_consistency_review": "identity-consistency-review.json",
    "copy": "copy.json",
    "review": "review.json",
    "approval": "final-approval.md",
    "storyboard": "storyboard.md",
    "agent_reports": "agent-reports.md",
    "image_generation": "image-generation.json",
    "final_images": "final-images.json",
}

MIN_STORY_SLIDES = 4
MAX_STORY_SLIDES = 11

FORBIDDEN_FINAL_SOURCE_PARTS = {
    "source-generated-local",
    "hd-clean",
    "hd-story",
    "instagram-clean",
    "instagram-story",
    "legacy-preview-clean",
    "legacy-preview-text",
}

REQUIRED_VISUAL_QA_CHECKS = {
    "storyboard",
    "aachu_face",
    "zuv_face",
    "dress_continuity",
    "style",
    "scene_logic",
    "scene_entity_integrity",
    VISUAL_STORY_READABILITY_KEY,
    "anatomy_inventory",
    "spatial_topology",
    "visual_richness",
    "integrated_final_text",
    "final_files",
}

VISUAL_QA_SCHEMA_MINIMUM = (2, 1)
REQUIRED_POST_GENERATION_REVIEWERS = {
    "anatomy_entity_spatial_identity",
    "storytelling_richness_text_style",
}
QA_PASSED_PROOF_STATES = {
    "QA_PASS_CANDIDATE",
    "CREATOR_APPROVED_PROOF",
    "BATCH_ALLOWED",
}

FACE_VISUAL_QA_CHECKS = {
    "aachu_face": "Aachu/Anchal",
    "zuv_face": "Himanshu/Zuv",
}


def _schema_version_tuple(value: Any) -> tuple[int, int] | None:
    parts = str(value or "").strip().split(".")
    if len(parts) < 2:
        return None
    try:
        return int(parts[0]), int(parts[1])
    except ValueError:
        return None


def _per_slide_records(
    check: Any,
    *,
    check_id: str,
    slide_count: int,
) -> tuple[list[dict[str, Any]], list[str]]:
    if not isinstance(check, dict):
        return [], [f"{check_id} must be a structured object, not a boolean."]
    slides = check.get("slides")
    if not isinstance(slides, list):
        return [], [f"{check_id} must include a per-slide slides list."]

    issues: list[str] = []
    records = [record for record in slides if isinstance(record, dict)]
    if len(records) != len(slides):
        issues.append(f"{check_id} slide records must all be objects.")
    if len(slides) != slide_count:
        issues.append(f"{check_id} has {len(slides)} slide records, expected {slide_count}.")
    seen = {record.get("slide") for record in records if isinstance(record.get("slide"), int)}
    missing = sorted(set(range(1, slide_count + 1)) - seen)
    if missing:
        issues.append(f"{check_id} is missing slide records: " + ", ".join(map(str, missing)))
    if len(seen) != len(records):
        issues.append(f"{check_id} has invalid or duplicate slide numbers.")
    return records, issues


def validate_anatomy_inventory_check(check: Any, *, slide_count: int) -> list[str]:
    """Require an attributable, attached inventory for every visible limb."""

    records, issues = _per_slide_records(
        check,
        check_id="anatomy_inventory",
        slide_count=slide_count,
    )
    for index, record in enumerate(records, start=1):
        number = record.get("slide", index)
        for limb in ("arms", "hands"):
            expected = record.get(f"expected_{limb}")
            observed = record.get(f"observed_{limb}")
            if not isinstance(expected, int) or expected < 0:
                issues.append(f"anatomy_inventory slide {number} has invalid expected_{limb}.")
            if not isinstance(observed, int) or observed < 0:
                issues.append(f"anatomy_inventory slide {number} has invalid observed_{limb}.")
            if isinstance(expected, int) and isinstance(observed, int) and expected != observed:
                issues.append(
                    f"anatomy_inventory slide {number} expected {expected} {limb} but observed {observed}."
                )

        visible_hands = record.get("visible_hands")
        if not isinstance(visible_hands, list):
            issues.append(f"anatomy_inventory slide {number} must list every visible hand.")
            visible_hands = []
        observed_hands = record.get("observed_hands")
        if isinstance(observed_hands, int) and observed_hands != len(visible_hands):
            issues.append(
                f"anatomy_inventory slide {number} records {observed_hands} observed hands "
                f"but inventories {len(visible_hands)}."
            )
        for hand_index, hand in enumerate(visible_hands, start=1):
            label = f"anatomy_inventory slide {number} hand {hand_index}"
            if not isinstance(hand, dict):
                issues.append(f"{label} must be an object with owner, side, action, and attachment evidence.")
                continue
            if not str(hand.get("owner") or "").strip():
                issues.append(f"{label} has no owner.")
            if hand.get("side") not in {"left", "right"}:
                issues.append(f"{label} must identify left or right side.")
            if not str(hand.get("action") or "").strip():
                issues.append(f"{label} has no action.")
            if hand.get("story_required") is not True:
                issues.append(f"{label} is not required by the locked scene.")
            if hand.get("attachment_visible") is not True:
                issues.append(f"{label} is not visibly attached through a wrist/forearm.")
            if len(str(hand.get("attachment_evidence") or "").strip()) < 12:
                issues.append(f"{label} needs concrete wrist/forearm attachment evidence.")
            if "contact_object" not in hand:
                issues.append(f"{label} must record contact_object, including null.")
            if hand.get("contact_geometry_pass") is not True:
                issues.append(f"{label} fails hand-object contact geometry.")
            if len(str(hand.get("occlusion_evidence") or "").strip()) < 12:
                issues.append(f"{label} needs concrete contact/occlusion evidence.")
            if hand.get("solid_object_intersection") is not False:
                issues.append(f"{label} intersects or may intersect a solid object.")
            if hand.get("edge_entry_unexplained") is not False:
                issues.append(
                    f"{label} has an unexplained edge entry from a frame or object without a visible owner."
                )

        for field in ("unexpected_limbs", "duplicated_limbs"):
            value = record.get(field)
            if not isinstance(value, list):
                issues.append(f"anatomy_inventory slide {number} must include {field} as a list.")
            elif value:
                issues.append(
                    f"anatomy_inventory slide {number} contains {field.replace('_', ' ')}: "
                    + ", ".join(str(item) for item in value)
                )
        malformed = record.get("malformed_fingers")
        if malformed not in (False, []):
            issues.append(f"anatomy_inventory slide {number} has malformed fingers: {malformed!r}.")
    return issues


SPATIAL_RELATIONS = {
    "in_front_of",
    "behind",
    "touching",
    "separate_from",
    "occluded_by",
    "not_near_solid_object",
}


def validate_spatial_topology_check(check: Any, *, slide_count: int) -> list[str]:
    """Fail closed when a person does not occupy a coherent environmental volume."""

    records, issues = _per_slide_records(
        check,
        check_id="spatial_topology",
        slide_count=slide_count,
    )
    for index, record in enumerate(records, start=1):
        number = record.get("slide", index)
        evidence_views = record.get("evidence_views")
        if not isinstance(evidence_views, dict):
            issues.append(f"spatial_topology slide {number} must include evidence_views.")
        else:
            for view in ("full_frame", "person_object_crop", "focal_detail"):
                if len(str(evidence_views.get(view) or "").strip()) < 12:
                    issues.append(f"spatial_topology slide {number} needs concrete {view} evidence.")

        environment_planes = record.get("environment_planes")
        if not isinstance(environment_planes, list):
            issues.append(f"spatial_topology slide {number} must inventory environment_planes.")
            environment_planes = []
        for plane_index, plane in enumerate(environment_planes, start=1):
            label = f"spatial_topology slide {number} environment plane {plane_index}"
            if not isinstance(plane, dict):
                issues.append(f"{label} must be structured.")
                continue
            if not str(plane.get("object") or "").strip():
                issues.append(f"{label} has no object.")
            if len(str(plane.get("depth_order") or "").strip()) < 8:
                issues.append(f"{label} needs concrete depth_order evidence.")
            if plane.get("boundary_continuous") is not True:
                issues.append(f"{label} boundary is not continuous.")

        people = record.get("people")
        if not isinstance(people, list):
            issues.append(f"spatial_topology slide {number} must include a people list.")
            people = []
        observed_people = record.get("observed_people")
        if not isinstance(observed_people, int) or observed_people < 0:
            issues.append(f"spatial_topology slide {number} has invalid observed_people.")
        elif observed_people != len(people):
            issues.append(
                f"spatial_topology slide {number} records {observed_people} people but inventories {len(people)}."
            )

        for person_index, person in enumerate(people, start=1):
            label = f"spatial_topology slide {number} person {person_index}"
            if not isinstance(person, dict):
                issues.append(f"{label} must be structured.")
                continue
            if not str(person.get("person") or "").strip():
                issues.append(f"{label} has no identity.")
            if person.get("silhouette_traceable") is not True:
                issues.append(f"{label} silhouette is not fully traceable.")
            ambiguous_regions = person.get("ambiguous_regions")
            if not isinstance(ambiguous_regions, list):
                issues.append(f"{label} must include ambiguous_regions as a list.")
            elif ambiguous_regions:
                issues.append(f"{label} has ambiguous regions: " + ", ".join(map(str, ambiguous_regions)))
            body_regions = person.get("body_regions")
            if not isinstance(body_regions, list) or not body_regions:
                issues.append(f"{label} must inventory visible body_regions.")
                body_regions = []
            for region_index, region in enumerate(body_regions, start=1):
                region_label = f"{label} body region {region_index}"
                if not isinstance(region, dict):
                    issues.append(f"{region_label} must be structured.")
                    continue
                for field in ("region", "near_object"):
                    if not str(region.get(field) or "").strip():
                        issues.append(f"{region_label} has no {field}.")
                expected = region.get("expected_relation")
                observed = region.get("observed_relation")
                if expected not in SPATIAL_RELATIONS:
                    issues.append(f"{region_label} has invalid expected_relation {expected!r}.")
                if observed not in SPATIAL_RELATIONS:
                    issues.append(f"{region_label} has invalid observed_relation {observed!r}.")
                if expected in SPATIAL_RELATIONS and observed in SPATIAL_RELATIONS and expected != observed:
                    issues.append(
                        f"{region_label} expected {expected} but observed {observed}."
                    )
                if region.get("boundary_continuous") is not True:
                    issues.append(f"{region_label} boundary is not continuous.")
                if region.get("occlusion_order_clear") is not True:
                    issues.append(f"{region_label} has ambiguous occlusion order.")
                if region.get("solid_object_intersection") is not False:
                    issues.append(f"{region_label} intersects or may intersect a solid object.")
                if region.get("morph_or_merge") is not False:
                    issues.append(f"{region_label} morphs or merges into the environment.")
                if len(str(region.get("evidence") or "").strip()) < 20:
                    issues.append(f"{region_label} needs concrete boundary/depth evidence.")

        for field in ("ambiguous_regions", "unresolved_intersections"):
            value = record.get(field)
            if not isinstance(value, list):
                issues.append(f"spatial_topology slide {number} must include {field} as a list.")
            elif value:
                issues.append(
                    f"spatial_topology slide {number} contains {field.replace('_', ' ')}: "
                    + ", ".join(str(item) for item in value)
                )
    return issues


def validate_visual_richness_check(check: Any, *, slide_count: int) -> list[str]:
    records, issues = _per_slide_records(
        check,
        check_id="visual_richness",
        slide_count=slide_count,
    )
    for index, record in enumerate(records, start=1):
        number = record.get("slide", index)
        for field in ("foreground", "midground", "background", "focal_action", "cause_effect"):
            if len(str(record.get(field) or "").strip()) < 8:
                issues.append(f"visual_richness slide {number} needs concrete {field} evidence.")
        details = record.get("story_details")
        if not isinstance(details, list) or not 2 <= len(details) <= 4:
            issues.append(f"visual_richness slide {number} must include 2-4 story_details.")
        elif any(len(str(detail).strip()) < 3 for detail in details):
            issues.append(f"visual_richness slide {number} has an empty or non-specific story detail.")
        if record.get("posed_portrait") is not False:
            issues.append(f"visual_richness slide {number} must set posed_portrait to false.")
        if record.get("decorative_clutter") is not False:
            issues.append(f"visual_richness slide {number} must set decorative_clutter to false.")
    return issues


def validate_source_assets(
    anatomy_inventory: Any,
    *,
    package_dir: Path,
    slide_count: int,
) -> list[str]:
    """Bind QA claims to the current bytes and dimensions of every source image."""

    if not isinstance(anatomy_inventory, dict):
        return ["anatomy_inventory must carry a source_asset for every slide."]
    source_records = anatomy_inventory.get("slides")
    if not isinstance(source_records, list):
        return ["anatomy_inventory must carry a source_asset for every slide."]
    issues: list[str] = []
    if len(source_records) != slide_count:
        issues.append(
            f"anatomy_inventory source assets have {len(source_records)} records, expected {slide_count}."
        )
    seen: set[int] = set()
    for index, slide_record in enumerate(source_records, start=1):
        record = slide_record.get("source_asset") if isinstance(slide_record, dict) else None
        if not isinstance(record, dict):
            issues.append(f"anatomy_inventory slide {index} source_asset must be an object.")
            continue
        number = slide_record.get("slide")
        if not isinstance(number, int) or number < 1 or number in seen:
            issues.append(f"source_asset record {index} has an invalid or duplicate slide number.")
        else:
            seen.add(number)
        raw_path = str(record.get("path") or "").strip()
        if not raw_path:
            issues.append(f"source_asset slide {number or index} has no file path.")
            continue
        path = Path(raw_path)
        if not path.is_absolute():
            path = package_dir / path
        if not path.is_file():
            issues.append(f"source_asset slide {number or index} file does not exist: {path}.")
            continue
        actual_sha256 = hashlib.sha256(path.read_bytes()).hexdigest()
        if record.get("sha256") != actual_sha256:
            issues.append(f"source_asset slide {number or index} SHA-256 is missing or stale.")
        try:
            with Image.open(path) as image:
                actual_width, actual_height = image.size
        except (OSError, ValueError):
            issues.append(f"source_asset slide {number or index} is not a readable image: {path}.")
            continue
        if record.get("width") != actual_width or record.get("height") != actual_height:
            issues.append(
                f"source_asset slide {number or index} dimensions are missing or stale; "
                f"actual is {actual_width}x{actual_height}."
            )
    missing = sorted(set(range(1, slide_count + 1)) - seen)
    if missing:
        issues.append("source_asset bindings are missing slide records: " + ", ".join(map(str, missing)))
    return issues


def validate_independent_reviewers(reviews: Any) -> list[str]:
    if not isinstance(reviews, dict):
        return ["reviews must contain two independent post-generation reviewer records."]
    issues: list[str] = []
    reviewer_ids: list[str] = []
    for review_type in sorted(REQUIRED_POST_GENERATION_REVIEWERS):
        record = reviews.get(review_type)
        if not isinstance(record, dict):
            issues.append(f"reviews.{review_type} is missing or not structured.")
            continue
        reviewer_id = str(record.get("reviewer_id") or "").strip()
        if not reviewer_id:
            issues.append(f"reviews.{review_type} has no reviewer_id.")
        else:
            reviewer_ids.append(reviewer_id)
        if record.get("pass") is not True:
            issues.append(f"reviews.{review_type} must pass.")
        if len(str(record.get("evidence") or "").strip()) < 24:
            issues.append(f"reviews.{review_type} needs concrete review evidence.")
    if len(reviewer_ids) == 2 and len(set(reviewer_ids)) != 2:
        issues.append("Post-generation reviewers must be independent and use different reviewer_id values.")
    return issues


def validate_scene_entity_integrity_check(
    check: Any,
    *,
    slide_count: int,
) -> list[str]:
    """Return blocking issues for per-slide people/entity inventory evidence."""

    if not isinstance(check, dict):
        return ["scene_entity_integrity must be a structured object."]

    issues: list[str] = []
    slides = check.get("slides")
    if not isinstance(slides, list):
        return ["scene_entity_integrity must include a per-slide slides list."]
    if len(slides) != slide_count:
        issues.append(
            f"scene_entity_integrity has {len(slides)} slide records, expected {slide_count}."
        )

    seen_slides: set[int] = set()
    for index, record in enumerate(slides, start=1):
        if not isinstance(record, dict):
            issues.append(f"scene_entity_integrity slide record {index} must be an object.")
            continue
        number = record.get("slide")
        if not isinstance(number, int) or number < 1:
            issues.append(f"scene_entity_integrity slide record {index} has no valid slide number.")
        elif number in seen_slides:
            issues.append(f"scene_entity_integrity repeats slide {number}.")
        else:
            seen_slides.add(number)

        expected_people = record.get("expected_people")
        observed_people = record.get("observed_people")
        if not isinstance(expected_people, int) or expected_people < 0:
            issues.append(f"scene_entity_integrity slide {number or index} has invalid expected_people.")
        if not isinstance(observed_people, int) or observed_people < 0:
            issues.append(f"scene_entity_integrity slide {number or index} has invalid observed_people.")
        if (
            isinstance(expected_people, int)
            and isinstance(observed_people, int)
            and expected_people != observed_people
        ):
            issues.append(
                f"scene_entity_integrity slide {number or index} expected {expected_people} people "
                f"but observed {observed_people}."
            )

        for limb in ("arms", "hands"):
            expected = record.get(f"expected_{limb}")
            observed = record.get(f"observed_{limb}")
            if not isinstance(expected, int) or expected < 0:
                issues.append(
                    f"scene_entity_integrity slide {number or index} has invalid expected_{limb}."
                )
            if not isinstance(observed, int) or observed < 0:
                issues.append(
                    f"scene_entity_integrity slide {number or index} has invalid observed_{limb}."
                )
            if isinstance(expected, int) and isinstance(observed, int) and expected != observed:
                issues.append(
                    f"scene_entity_integrity slide {number or index} expected {expected} {limb} "
                    f"but observed {observed}."
                )

        for field in ("unexpected_limbs", "duplicated_limbs"):
            value = record.get(field)
            if not isinstance(value, list):
                issues.append(
                    f"scene_entity_integrity slide {number or index} must include {field} as a list."
                )
            elif value:
                issues.append(
                    f"scene_entity_integrity slide {number or index} contains {field.replace('_', ' ')}: "
                    + ", ".join(str(item) for item in value)
                )

        unexpected = record.get("unexpected_entities")
        if not isinstance(unexpected, list):
            issues.append(
                f"scene_entity_integrity slide {number or index} must include unexpected_entities as a list."
            )
        elif unexpected:
            issues.append(
                f"scene_entity_integrity slide {number or index} contains unexpected entities: "
                + ", ".join(str(item) for item in unexpected)
            )

        evidence = str(record.get("evidence") or "").strip()
        if len(evidence) < 20:
            issues.append(
                f"scene_entity_integrity slide {number or index} needs concrete visual evidence."
            )

    if set(range(1, slide_count + 1)) - seen_slides:
        missing = sorted(set(range(1, slide_count + 1)) - seen_slides)
        issues.append("scene_entity_integrity is missing slide records: " + ", ".join(map(str, missing)))
    return issues

PUBLISHABLE_FINAL_GENERATION_MODES = {
    "model_native_publishable",
    "model_art_local_text_publishable",
}


@dataclass(frozen=True)
class QualityContext:
    story: str
    title: str
    slug: str
    today: date
    out_dir: Path
    image_paths: list[Path]
    slide_count: int
    package: dict[str, Any]
    manifest: dict[str, Any]
    render_result: dict[str, Any]
    workspace_root: Path
    asset_root: Path | None = None
    visual_qa_path: Path | None = None


def quality_asset_root(context: QualityContext) -> Path:
    """Physical root for audited images; may be an internal promotion stage."""

    return context.asset_root or context.out_dir


def quality_asset_path(context: QualityContext, folder: str, filename: str) -> Path:
    return quality_asset_root(context) / folder / filename


def quality_visual_qa_path(context: QualityContext) -> tuple[Path, str | None]:
    """Resolve one explicit QA artifact without escaping or symlinking the package."""

    raw_path = context.visual_qa_path or Path("visual-qa.json")
    raw_path = Path(raw_path)
    if not raw_path.is_absolute() and ".." in raw_path.parts:
        return (
            context.out_dir / raw_path,
            "visual QA path must not traverse outside the carousel package.",
        )

    package_dir = context.out_dir.expanduser().absolute()
    package_root = package_dir.resolve()
    candidate = raw_path.expanduser() if raw_path.is_absolute() else package_dir / raw_path
    try:
        lexical_relative = candidate.absolute().relative_to(package_dir)
    except ValueError:
        return candidate, "visual QA path must stay inside the carousel package."

    cursor = package_dir
    for part in lexical_relative.parts:
        cursor = cursor / part
        if cursor.is_symlink():
            return candidate, "visual QA path must not contain symlinks."
    try:
        candidate.expanduser().resolve().relative_to(package_root)
    except (OSError, ValueError):
        return candidate, "visual QA path must stay inside the carousel package."
    return candidate, None


def required_final_files(context: QualityContext) -> list[Path]:
    return [
        quality_asset_root(context) / expected_output_relative_path(output_format, number)
        for number in range(1, context.slide_count + 1)
        for output_format in locked_formats(context.out_dir)
    ]


def write_json(path: Path, data: Any) -> None:
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


def status_from_issues(issues: list[str], notes: list[str] | None = None) -> str:
    if issues:
        return "NEEDS_FIXES"
    if notes:
        return "PASS_WITH_NOTES"
    return "PASS"


def required_artifacts() -> dict[str, str]:
    artifacts = dict(BASE_ARTIFACTS)
    artifacts.update(QUALITY_ARTIFACTS)
    return artifacts


def build_requirements(context: QualityContext) -> list[dict[str, Any]]:
    return [
        {
            "id": "REQ-STYLE-001",
            "label": "Use romantic watercolor-and-ink / identity-rooted illustration style",
            "source": "creator master-prompt style requirement",
            "evidence": ["prompt_pack.shared_style_prompt", "concept.visual_style"],
            "critical": True,
        },
        {
            "id": "REQ-HOUSE-STYLE-SCENE-001",
            "label": "Final prompts stay scene-first in the @a.storyof.two house style",
            "source": "creator style-consistency correction on 2026-05-24",
            "evidence": ["prompt_pack.slides[].prompt"],
            "critical": True,
        },
        {
            "id": "REQ-PHOTO-001",
            "label": "Preserve supplied photo cues, outfits, settings, poses, and relationship energy",
            "source": "C-layer framework",
            "evidence": ["slides[].source_images", "prompt_pack.slides[].prompt"],
            "critical": True,
        },
        {
            "id": "REQ-IDENTITY-001",
            "label": "Aachu/Zuv identity reference is present in manifest and prompt pack",
            "source": "user face-consistency requirement",
            "critical": True,
        },
        {
            "id": "REQ-IDENTITY-DOSSIER-001",
            "label": "Identity dossier, preflight checklist, and face contact sheet are present before image generation",
            "source": "user face-consistency requirement",
            "critical": True,
        },
        {
            "id": "REQ-IDENTITY-CONSISTENCY-001",
            "label": "Face structure, expressions, clothing, and cross-slide identity continuity are reviewed before image generation",
            "source": "user identity-consistency gate requirement",
            "critical": True,
        },
        {
            "id": "REQ-POST-COPY-VISUAL-ROOM-001",
            "label": "Run the post-copy visual creative room after approved copy and before prompt/image handoff",
            "source": "creator mandatory visual-room workflow",
            "critical": True,
        },
        {
            "id": "REQ-VISUAL-PLAN-QUALITY-001",
            "label": "Per-slide visual screen passes before image generation",
            "source": "user pre-generation storyboard QA requirement",
            "critical": True,
        },
        {
            "id": "REQ-SLIDES-001",
            "label": "Create an approved 4-10 slide carousel arc, matching prompt count",
            "source": "/story contract",
            "expected": context.slide_count,
            "critical": True,
        },
        {
            "id": "REQ-SUCCESS-STANDARD-001",
            "label": "Successful carousel standard is carried as open agent alignment and passes before final approval",
            "source": SUCCESSFUL_CAROUSEL_STANDARD_PATH,
            "evidence": [
                "concept.successful_carousel_standard",
                "prompt_pack.successful_carousel_standard",
                "review.successful_carousel_standard_gate",
            ],
            "critical": True,
        },
        {
            "id": "REQ-FINAL-IMAGES-001",
            "label": "Final generated carousel images are packaged independently for every request-locked native format, not local placeholders",
            "source": "user final-output requirement",
            "expected": context.slide_count,
            "critical": True,
        },
        {
            "id": "REQ-INTEGRATED-FINAL-TEXT-001",
            "label": "Final slides include exact integrated copy and brandmark in every current-request format locked by format-contract.json",
            "source": "user publishable composition requirement",
            "expected": context.slide_count,
            "critical": True,
        },
        {
            "id": "REQ-VISUAL-QA-001",
            "label": "Structured face and storyboard visual QA gate passes with evidence",
            "source": "user face/storyboard QA requirement",
            "critical": True,
        },
        {
            "id": "REQ-BRAND-001",
            "label": "Keep @a.storyof.two as a tiny, low-contrast top-right brandmark",
            "source": "brandmark rule",
            "critical": True,
        },
        {
            "id": "REQ-NEGATIVE-001",
            "label": "Block photorealism, 3D rendering, generic stock couple art, and quote-card layout",
            "source": "negative prompt contract",
            "critical": True,
        },
        {
            "id": "REQ-OUTPUT-001",
            "label": "Write complete C-layer artifact contract",
            "source": "AGENTS.md C-layer output",
            "expected": sorted(required_artifacts().values()),
            "critical": True,
        },
        {
            "id": "REQ-WIKI-001",
            "label": "Enrich wiki, index, working memory, and graph memory after the run",
            "source": "Rohit v2 wiki memory lifecycle",
            "critical": True,
        },
    ]


def build_run_ledger(context: QualityContext) -> dict[str, Any]:
    return {
        "schema_version": "1.0",
        "observer": {
            "agent": "C0.5-Jarvis",
            "role": "Track requirements, stage completion, reviewer findings, and final gate status.",
        },
        "run": {
            "date": str(context.today),
            "title": context.title,
            "slug": context.slug,
            "channel": "@a.storyof.two",
            "pipeline": "C-layer illustrated carousel",
            "runtime": context.manifest.get("runtime", "codex_native_local"),
            "output_dir": str(context.out_dir),
        },
        "source_inputs": {
            "story": context.story,
            "slide_count": context.slide_count,
            "reference_images": [str(path) for path in context.image_paths],
        },
        "requirements": build_requirements(context),
        "expected_artifacts": required_artifacts(),
        "stage_statuses": {
            "intake": "PENDING",
            "story": "PENDING",
            "arc": "PENDING",
            "visual": "PENDING",
            "identity_consistency": "PENDING",
            "prompt": "PENDING",
            "copy": "PENDING",
            "success_standard": "PENDING",
            "assets": "PENDING",
            "wiki_learning": "PENDING",
            "final_contract": "PENDING",
        },
        "final_gate": {
            "status": "PENDING",
            "pass": False,
            "notes": [],
        },
    }


def prompt_pack(context: QualityContext) -> dict[str, Any]:
    return context.package.get("prompt_pack", {})


def identity_consistency_review(context: QualityContext) -> dict[str, Any]:
    value = context.package.get("identity_consistency_review")
    if isinstance(value, dict):
        return value
    path = context.out_dir / BASE_ARTIFACTS["identity_consistency_review"]
    if path.exists():
        return json.loads(path.read_text(encoding="utf-8"))
    return {}


def visual_plan_quality(context: QualityContext) -> dict[str, Any]:
    value = context.package.get("visual_plan_quality")
    if isinstance(value, dict):
        return value
    path = context.out_dir / BASE_ARTIFACTS["visual_plan_quality"]
    if path.exists():
        return json.loads(path.read_text(encoding="utf-8"))
    return {}


def post_copy_visual_room(context: QualityContext) -> dict[str, Any]:
    value = context.package.get("post_copy_visual_room")
    if isinstance(value, dict):
        return value
    path = context.out_dir / BASE_ARTIFACTS["post_copy_visual_room"]
    if path.exists():
        return json.loads(path.read_text(encoding="utf-8"))
    return {}


def is_identity_only_context(context: QualityContext) -> bool:
    prompt_refs = prompt_pack(context).get("identity_reference_images", [])
    manifest_refs = context.manifest.get("identity_references", [])
    return not context.image_paths and bool(prompt_refs) and bool(manifest_refs)


def slides(context: QualityContext) -> list[dict[str, Any]]:
    value = context.package.get("slides", [])
    return value if isinstance(value, list) else []


def review_item(stage: str, expected: list[str], done: list[str], issues: list[str], notes: list[str] | None = None) -> dict[str, Any]:
    notes = notes or []
    return {
        "stage": stage,
        "status": status_from_issues(issues, notes),
        "expected": expected,
        "done": done,
        "issues": issues,
        "notes": notes,
    }


def final_image_gate(context: QualityContext, final_files: list[Path]) -> dict[str, Any]:
    final_manifest_path = context.out_dir / BASE_ARTIFACTS["final_images"]
    issues: list[str] = []
    manifest: dict[str, Any] = {}
    required_formats = list(locked_formats(context.out_dir))
    if final_manifest_path.exists():
        manifest = json.loads(final_manifest_path.read_text(encoding="utf-8"))
    else:
        issues.append("final-images.json is missing.")

    if not all(path.exists() for path in final_files):
        missing = [str(path) for path in final_files if not path.exists()]
        issues.append("Missing final images: " + ", ".join(missing))

    if manifest:
        if manifest.get("status") not in {"packaged", "generated", "BATCH_ALLOWED"}:
            issues.append(
                f"final-images.json status is {manifest.get('status')!r}, expected "
                "'packaged', 'generated', or internal pre-promotion 'BATCH_ALLOWED'."
            )
        contract_formats = manifest.get("native_output_contract", {}).get("formats", [])
        if contract_formats != required_formats:
            issues.append(
                "final-images.json native output contract must match the current-request lock exactly: "
                + ", ".join(required_formats)
            )
        records = manifest.get("slides", [])
        if len(records) != context.slide_count:
            issues.append(f"final-images.json has {len(records)} slide records, expected {context.slide_count}.")
        for record in records:
            number = int(record.get("slide", 0) or 0)
            native_outputs = record.get("native_outputs", {})
            if not isinstance(native_outputs, dict):
                native_outputs = {}
            missing_formats = [name for name in required_formats if name not in native_outputs]
            if missing_formats:
                issues.append(
                    f"Slide {number} native_outputs missing required format(s): "
                    + ", ".join(missing_formats)
                )
                continue
            unexpected_formats = sorted(set(native_outputs) - set(required_formats))
            if unexpected_formats:
                issues.append(
                    f"Slide {number} native_outputs contains unrequested format(s): "
                    + ", ".join(unexpected_formats)
                )
            source_values: list[str] = []
            for format_name in required_formats:
                output = native_outputs[format_name]
                source_text = str(output.get("source", ""))
                if not source_text:
                    issues.append(
                        f"Slide {number} {format_name} native source provenance is missing."
                    )
                else:
                    source_values.append(source_text)
                source_parts = set(Path(source_text).parts)
                forbidden = sorted(source_parts & FORBIDDEN_FINAL_SOURCE_PARTS)
                if forbidden:
                    issues.append(
                        f"Slide {number} {format_name} source uses forbidden local placeholder/preview path part(s): "
                        + ", ".join(forbidden)
                    )
                expected_file = expected_output_path(context.out_dir, format_name, number)
                if Path(output.get("file", "")) != expected_file:
                    issues.append(
                        f"Slide {number} {format_name} native output file must be {expected_file}."
                    )
                relative_path = expected_output_relative_path(format_name, number)
                physical_file = quality_asset_root(context) / relative_path
                if not physical_file.exists():
                    issues.append(f"Missing {format_name} final image: {expected_file}.")
            if len(source_values) != len(set(source_values)):
                issues.append(
                    f"Slide {number} requested native outputs must use distinct source images."
                )

    return {
        "pass": not issues,
        "evidence": {
            "files": [
                str(path)
                for path in final_files
                if path.exists()
            ],
            "manifest": str(final_manifest_path) if final_manifest_path.exists() else None,
            "status": manifest.get("status") if manifest else None,
            "issues": issues,
        },
    }


def structured_visual_qa_gate(context: QualityContext) -> dict[str, Any]:
    qa_path, qa_path_issue = quality_visual_qa_path(context)
    if qa_path_issue:
        return {
            "pass": False,
            "path": str(qa_path),
            "failed": [qa_path_issue],
        }
    failed: list[str] = []
    checks: dict[str, Any] = {}
    if not qa_path.exists():
        failed.append("visual-qa.json is missing; visual-qa.md is only a review worksheet.")
    else:
        try:
            qa = json.loads(qa_path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError) as exc:
            return {
                "pass": False,
                "path": str(qa_path),
                "failed": [f"visual-qa.json could not be read as JSON: {exc}"],
            }
        schema_version = _schema_version_tuple(qa.get("schema_version"))
        if schema_version is None or schema_version < VISUAL_QA_SCHEMA_MINIMUM:
            failed.append("visual-qa.json schema_version must be at least 2.1.")
        if qa.get("proof_state") not in QA_PASSED_PROOF_STATES:
            failed.append(
                "visual-qa.json proof_state must be QA_PASS_CANDIDATE or a later approved state."
            )
        if qa.get("status") != "PASS":
            failed.append("visual-qa.json status must be PASS.")
        raw_checks = qa.get("checks", {})
        if isinstance(raw_checks, list):
            checks = {str(item.get("id", "")): item for item in raw_checks if isinstance(item, dict)}
        elif isinstance(raw_checks, dict):
            checks = raw_checks
        else:
            failed.append("visual-qa.json checks must be an object or list.")

        if "integrated_final_text" not in checks and "model_native_text" in checks:
            checks["integrated_final_text"] = checks["model_native_text"]

        missing = sorted(REQUIRED_VISUAL_QA_CHECKS - set(checks))
        if missing:
            failed.append("visual-qa.json missing required checks: " + ", ".join(missing))
        for check_id, check in checks.items():
            passed = check.get("pass") if isinstance(check, dict) else check is True
            if passed is not True:
                failed.append(f"visual-qa.json check failed: {check_id}")
        if isinstance(checks.get("pose_anatomy"), bool) and "anatomy_inventory" not in checks:
            failed.append(
                "visual-qa.json boolean-only pose_anatomy is invalid; per-slide anatomy_inventory is required."
            )
        anatomy_issues = validate_anatomy_inventory_check(
            checks.get("anatomy_inventory"),
            slide_count=context.slide_count,
        )
        failed.extend(f"visual-qa.json {issue}" for issue in anatomy_issues)
        topology_issues = validate_spatial_topology_check(
            checks.get("spatial_topology"),
            slide_count=context.slide_count,
        )
        failed.extend(f"visual-qa.json {issue}" for issue in topology_issues)
        richness_issues = validate_visual_richness_check(
            checks.get("visual_richness"),
            slide_count=context.slide_count,
        )
        failed.extend(f"visual-qa.json {issue}" for issue in richness_issues)
        asset_issues = validate_source_assets(
            checks.get("anatomy_inventory"),
            package_dir=context.out_dir,
            slide_count=context.slide_count,
        )
        failed.extend(f"visual-qa.json {issue}" for issue in asset_issues)
        reviewer_issues = validate_independent_reviewers(qa.get("reviews"))
        failed.extend(f"visual-qa.json {issue}" for issue in reviewer_issues)
        scene_entity_issues = validate_scene_entity_integrity_check(
            checks.get("scene_entity_integrity"),
            slide_count=context.slide_count,
        )
        failed.extend(
            f"visual-qa.json {issue}"
            for issue in scene_entity_issues
        )
        visual_plan_path = context.out_dir / "visual-plan-quality.json"
        visual_plan = {}
        if visual_plan_path.exists():
            try:
                loaded_visual_plan = json.loads(visual_plan_path.read_text(encoding="utf-8"))
                if isinstance(loaded_visual_plan, dict):
                    visual_plan = loaded_visual_plan
            except (json.JSONDecodeError, OSError):
                visual_plan = {}
        readability_issues = validate_frame_readability(
            checks.get(VISUAL_STORY_READABILITY_KEY),
            slide_count=context.slide_count,
            required_formats=locked_formats(context.out_dir),
            expected_director_event_fingerprint=director_event_fingerprint(visual_plan),
            event_a_review_provenance=director_review_provenance(visual_plan),
            event_a_creator_correction_fingerprint=(
                director_creator_correction_fingerprint(visual_plan)
            ),
            expected_creator_correction_fingerprint=(
                current_creator_correction_fingerprint(context.out_dir)
            ),
            event_a_generation_payload_fingerprint=(
                director_generation_payload_fingerprint(visual_plan)
            ),
            expected_generation_payload_fingerprint=(
                _current_generation_fingerprint_or_none(context.out_dir)
            ),
            director_author_id=director_author_id(visual_plan),
            director_reviewer_id=director_reviewer_id(visual_plan),
            expected_frame_bindings=expected_frame_bindings(
                context.out_dir,
                context.slide_count,
                locked_formats(context.out_dir),
            ),
            package_dir=quality_asset_root(context),
            provenance_package_dir=context.out_dir,
            require_files=True,
        )
        failed.extend(
            f"visual-qa.json {issue}"
            for issue in readability_issues
        )
        for check_id, person in FACE_VISUAL_QA_CHECKS.items():
            check = checks.get(check_id)
            if not isinstance(check, dict):
                failed.append(f"visual-qa.json {check_id} must include reference_option_ids and likeness_notes for {person}.")
                continue
            option_ids = check.get("reference_option_ids")
            notes = str(check.get("likeness_notes") or "").strip()
            if not isinstance(option_ids, list) or not option_ids or not all(str(item).startswith("ID") for item in option_ids):
                failed.append(f"visual-qa.json {check_id} must name contact-sheet reference_option_ids for {person}.")
            if len(notes) < 24:
                failed.append(f"visual-qa.json {check_id} must include specific likeness_notes for {person}.")

    return {
        "pass": not failed,
        "path": str(qa_path),
        "failed": failed,
    }


def build_stage_reviews(context: QualityContext, ledger: dict[str, Any]) -> dict[str, Any]:
    package_slides = slides(context)
    prompts = prompt_pack(context).get("slides", [])
    identity_review = identity_consistency_review(context)
    post_copy_room = post_copy_visual_room(context)
    visual_quality = visual_plan_quality(context)
    shared_style = prompt_pack(context).get("shared_style_prompt", "")
    negative = prompt_pack(context).get("shared_negative_prompt", "")
    success_gate = evaluate_successful_carousel_standard(
        context.package,
        slide_count=context.slide_count,
    )
    render_status = context.render_result.get("status", "unknown")
    final_files = required_final_files(context)

    intake_issues = []
    if not context.story.strip():
        intake_issues.append("Story text is empty.")
    identity_only = is_identity_only_context(context)
    if not context.image_paths and not identity_only:
        intake_issues.append("No reference images were supplied.")
    missing_paths = [str(path) for path in context.image_paths if not path.exists()]
    if missing_paths:
        intake_issues.append("Missing reference image paths: " + ", ".join(missing_paths))

    slide_issues = []
    if context.slide_count < MIN_STORY_SLIDES or context.slide_count > MAX_STORY_SLIDES:
        slide_issues.append(f"Slide count must be between {MIN_STORY_SLIDES} and {MAX_STORY_SLIDES}.")
    if len(package_slides) != context.slide_count:
        slide_issues.append(f"slides.json has {len(package_slides)} slides, expected {context.slide_count}.")
    if len(prompts) != context.slide_count:
        slide_issues.append(f"prompt-pack.json has {len(prompts)} slide prompts, expected {context.slide_count}.")

    visual_issues = []
    if not post_copy_room:
        visual_issues.append("post-copy-visual-room.json is missing.")
    elif post_copy_room.get("status") != "GO":
        visual_issues.append(
            f"post-copy-visual-room.json status is {post_copy_room.get('status')}."
        )
    for slide in package_slides:
        required_visual_fields = ["copy", "role", "visual", "emotion", "cta_intent"]
        if not identity_only:
            required_visual_fields.append("source_images")
        missing = [
            field
            for field in required_visual_fields
            if not slide.get(field)
        ]
        if missing:
            visual_issues.append(f"Slide {slide.get('slide', '?')} missing: {', '.join(missing)}.")
    if not visual_quality:
        visual_issues.append("visual-plan-quality.json is missing.")
    else:
        if visual_quality.get("status") != "PASS" or not visual_quality.get("can_generate"):
            visual_issues.extend(
                visual_quality.get("issues")
                or ["visual-plan-quality.json did not pass the pre-generation screen."]
            )
        if len(visual_quality.get("slide_reviews", [])) != context.slide_count:
            visual_issues.append(
                f"visual-plan-quality.json has {len(visual_quality.get('slide_reviews', []))} slide records, expected {context.slide_count}."
            )
        visual_issues.extend(
            validate_director_storyboard(
                visual_quality,
                slide_count=context.slide_count,
                expected_slides=package_slides,
                expected_formats=locked_formats(context.out_dir),
                expected_format_contract_fingerprint=locked_format_contract_fingerprint(
                    context.out_dir
                ),
                expected_creator_correction_fingerprint=(
                    current_creator_correction_fingerprint(context.out_dir)
                ),
                expected_generation_payload_fingerprint=(
                    _current_generation_fingerprint_or_none(context.out_dir)
                ),
                provenance_package_dir=context.out_dir,
            )
        )

    identity_issues = []
    dossier_path = context.out_dir / "identity-dossier.json"
    preflight_path = context.out_dir / "identity-generation-preflight.md"
    contact_sheet_path = context.out_dir / "identity-face-contact-sheet.jpg"
    if not dossier_path.exists():
        identity_issues.append("identity-dossier.json is missing.")
    if not preflight_path.exists():
        identity_issues.append("identity-generation-preflight.md is missing.")
    if not contact_sheet_path.exists():
        identity_issues.append("identity-face-contact-sheet.jpg is missing.")
    if not prompt_pack(context).get("identity_dossier_reference_images"):
        identity_issues.append("prompt-pack.json missing identity_dossier_reference_images.")
    if not identity_review:
        identity_issues.append("identity-consistency-review.json is missing.")
    else:
        if identity_review.get("status") != "PASS":
            identity_issues.extend(identity_review.get("issues") or ["Identity consistency review did not pass."])
        if len(identity_review.get("slides", [])) != context.slide_count:
            identity_issues.append(
                f"identity-consistency-review.json has {len(identity_review.get('slides', []))} slide records, expected {context.slide_count}."
            )
    for slide in package_slides:
        continuity = slide.get("identity_continuity", {})
        missing = [
            field
            for field in ["face_structure", "facial_expression", "clothing", "cross_slide_consistency"]
            if not continuity.get(field)
        ]
        if missing:
            identity_issues.append(
                f"Slide {slide.get('slide', '?')} missing identity continuity fields: {', '.join(missing)}."
            )

    prompt_issues = []
    style_lower = shared_style.lower()
    if "watercolor" not in style_lower or "ink" not in style_lower:
        prompt_issues.append("Shared style prompt does not specify watercolor-and-ink illustration.")
    if "hand-drawn" not in style_lower and "hand drawn" not in style_lower:
        prompt_issues.append("Shared style prompt does not specify hand-drawn illustration.")
    if "photo" not in style_lower and "reference" not in style_lower:
        prompt_issues.append("Shared style prompt does not explicitly preserve photo/reference details.")
    prompt_issues.extend(prompt_style_drift_issues(prompt_pack(context)))
    negative_lower = negative.lower()
    for required_negative in ["photorealism", "3d", "stock", "quote-card"]:
        if required_negative not in negative_lower:
            prompt_issues.append(f"Negative prompt missing '{required_negative}'.")
    for prompt in prompts:
        if "identity continuity lock" not in prompt.get("prompt", "").lower():
            prompt_issues.append(f"Slide {prompt.get('slide', '?')} prompt missing Identity continuity lock.")

    copy_pack = context.package.get("copy", {})
    copy_issues = []
    if not copy_pack.get("caption_recommended"):
        copy_issues.append("Recommended caption is missing.")
    if not copy_pack.get("alt_text"):
        copy_issues.append("Alt text list is missing.")

    asset_notes = []
    asset_issues = []
    if render_status == "skipped":
        asset_notes.append(context.render_result.get("reason", "Asset rendering skipped."))
    elif render_status in {"dry_run_generated", "legacy_preview_generated"}:
        asset_notes.append(
            context.render_result.get(
                "reason",
                "Preview/dry-run images were generated, but they are not publishable final art.",
            )
        )
    elif render_status not in {"rendered", "partial", "generated"}:
        asset_issues.append(f"Unexpected render status: {render_status}.")
    if not all(path.exists() for path in final_files):
        missing = [str(path) for path in final_files if not path.exists()]
        asset_issues.append("Missing final generated images: " + ", ".join(missing))

    wiki_notes = [
        "Wiki and memory files are updated after final audit generation.",
    ]

    reviews = {
        "intake_reviewer": review_item(
            "intake",
            ["story captured", "reference images exist", "slide count accepted"],
            [
                "identity-only concept-led run" if identity_only else f"{len(context.image_paths)} reference image(s)",
                f"{context.slide_count} requested slide(s)",
            ],
            intake_issues,
            ["No story photos supplied; identity references and the creative brief are the source of truth."]
            if identity_only
            else [],
        ),
        "story_reviewer": review_item(
            "story",
            ["human truth present", "source story preserved"],
            [context.package.get("concept", {}).get("human_truth", "")],
            [] if context.package.get("concept", {}).get("human_truth") else ["Human truth is missing."],
        ),
        "arc_reviewer": review_item(
            "arc",
            ["slide plan count matches request", "prompt count matches slide plan"],
            [f"{len(package_slides)} planned slide(s)", f"{len(prompts)} prompt slide(s)"],
            slide_issues,
        ),
        "visual_reviewer": review_item(
            "visual",
            [
                "every slide has copy, role, visual, emotion, CTA intent, and source images",
                "post-copy visual room runs after copy lock",
                "pre-generation visual screen passes before image handoff",
            ],
            [
                f"checked {len(package_slides)} slide(s)",
                f"post-copy visual room: {post_copy_room.get('status', 'missing')}",
                f"visual screen: {visual_quality.get('status', 'missing')}",
            ],
            visual_issues,
        ),
        "identity_consistency_reviewer": review_item(
            "identity_consistency",
            [
                "selected identity bundle is present",
                "each slide locks face structure",
                "each slide locks facial expression",
                "each slide locks clothing/body-language cues",
                "each prompt includes Identity continuity lock before generation",
            ],
            [
                f"{len(identity_review.get('identity_references', [])) if identity_review else 0} identity reference(s)",
                f"{len(identity_review.get('slides', [])) if identity_review else 0} reviewed slide(s)",
            ],
            identity_issues,
        ),
        "prompt_reviewer": review_item(
            "prompt",
            ["shared style prompt", "shared negative prompt", "self-contained slide prompts"],
            ["style prompt present" if shared_style else "style prompt missing", "negative prompt present" if negative else "negative prompt missing"],
            prompt_issues,
        ),
        "copy_reviewer": review_item(
            "copy",
            ["caption", "alt text", "posting notes"],
            [key for key in ["caption_recommended", "alt_text", "posting_notes"] if copy_pack.get(key)],
            copy_issues,
        ),
        "success_standard_reviewer": review_item(
            "success_standard",
            [
                "open agent alignment to the success goals",
                "relationship-first premise",
                "Story-Selling / golden-theme / story-director support",
                "visual-room and visual-plan support",
                "prompt-level success-goal handoff",
            ],
            [
                f"standard source: {success_gate['source']}",
                f"gate: {success_gate['status']}",
            ],
            success_gate["issues"],
        ),
        "asset_reviewer": review_item(
            "assets",
            ["local preview status recorded", "final generated images packaged"],
            [f"render status: {render_status}", f"final images present: {sum(path.exists() for path in final_files)} / {context.slide_count}"],
            asset_issues,
            asset_notes,
        ),
        "wiki_learning_reviewer": review_item(
            "wiki_learning",
            ["wiki page", "wiki index link", "working memory entry", "graph entity"],
            ["scheduled wiki and memory updates"],
            [],
            wiki_notes,
        ),
    }

    stage_statuses = {
        "intake": reviews["intake_reviewer"]["status"],
        "story": reviews["story_reviewer"]["status"],
        "arc": reviews["arc_reviewer"]["status"],
        "visual": reviews["visual_reviewer"]["status"],
        "identity_consistency": reviews["identity_consistency_reviewer"]["status"],
        "prompt": reviews["prompt_reviewer"]["status"],
        "copy": reviews["copy_reviewer"]["status"],
        "success_standard": reviews["success_standard_reviewer"]["status"],
        "assets": reviews["asset_reviewer"]["status"],
        "wiki_learning": reviews["wiki_learning_reviewer"]["status"],
        "final_contract": "PENDING",
    }
    ledger["stage_statuses"].update(stage_statuses)

    return {
        "schema_version": "1.0",
        "observer": ledger["observer"],
        "reviews": reviews,
    }


def evaluate_requirements(context: QualityContext) -> dict[str, dict[str, Any]]:
    package_slides = slides(context)
    prompts = prompt_pack(context).get("slides", [])
    identity_review = identity_consistency_review(context)
    post_copy_room = post_copy_visual_room(context)
    visual_quality = visual_plan_quality(context)
    shared_style = prompt_pack(context).get("shared_style_prompt", "")
    negative = prompt_pack(context).get("shared_negative_prompt", "")
    identity_refs = context.manifest.get("identity_references", [])
    identity_prompt_refs = prompt_pack(context).get("identity_reference_images", [])
    style_lower = shared_style.lower()
    negative_lower = negative.lower()

    results: dict[str, dict[str, Any]] = {}
    results["REQ-STYLE-001"] = {
        "pass": ("watercolor" in style_lower and "ink" in style_lower)
        and ("hand-drawn" in style_lower or "hand drawn" in style_lower)
        and ("photo" in style_lower or "reference" in style_lower),
        "evidence": shared_style,
    }
    style_drift_issues = prompt_style_drift_issues(prompt_pack(context))
    results["REQ-HOUSE-STYLE-SCENE-001"] = {
        "pass": not style_drift_issues,
        "evidence": style_drift_issues or "No artifact/poster prompt drift detected.",
    }
    results["REQ-PHOTO-001"] = {
        "pass": (
            all(slide.get("source_images") for slide in package_slides)
            or is_identity_only_context(context)
        )
        and all("reference" in prompt.get("prompt", "").lower() or "photo" in prompt.get("prompt", "").lower() for prompt in prompts),
        "evidence": (
            "identity-only concept-led run using identity references and creative brief"
            if is_identity_only_context(context)
            else f"{len(package_slides)} slide(s), {len(prompts)} prompt(s)"
        ),
    }
    results["REQ-IDENTITY-001"] = {
        "pass": bool(identity_refs) and bool(identity_prompt_refs),
        "evidence": {"manifest": identity_refs, "prompt_pack": identity_prompt_refs},
    }
    dossier_path = context.out_dir / "identity-dossier.json"
    preflight_path = context.out_dir / "identity-generation-preflight.md"
    contact_sheet_path = context.out_dir / "identity-face-contact-sheet.jpg"
    dossier_prompt_refs = prompt_pack(context).get("identity_dossier_reference_images", [])
    results["REQ-IDENTITY-DOSSIER-001"] = {
        "pass": dossier_path.exists()
        and preflight_path.exists()
        and contact_sheet_path.exists()
        and bool(dossier_prompt_refs)
        and str(contact_sheet_path) in [str(path) for path in dossier_prompt_refs],
        "evidence": {
            "dossier": str(dossier_path) if dossier_path.exists() else None,
            "preflight": str(preflight_path) if preflight_path.exists() else None,
            "contact_sheet": str(contact_sheet_path) if contact_sheet_path.exists() else None,
            "prompt_refs": dossier_prompt_refs,
        },
    }
    identity_issues: list[str] = []
    if not identity_review:
        identity_issues.append("identity-consistency-review.json is missing.")
    elif identity_review.get("status") != "PASS":
        identity_issues.extend(identity_review.get("issues") or ["Identity consistency review did not pass."])
    if identity_review and len(identity_review.get("slides", [])) != context.slide_count:
        identity_issues.append(
            f"identity-consistency-review.json has {len(identity_review.get('slides', []))} slide records, expected {context.slide_count}."
        )
    for slide in package_slides:
        continuity = slide.get("identity_continuity", {})
        missing = [
            field
            for field in ["face_structure", "facial_expression", "clothing", "cross_slide_consistency"]
            if not continuity.get(field)
        ]
        if missing:
            identity_issues.append(
                f"Slide {slide.get('slide', '?')} missing identity continuity fields: {', '.join(missing)}."
            )
    for prompt in prompts:
        if "identity continuity lock" not in prompt.get("prompt", "").lower():
            identity_issues.append(f"Slide {prompt.get('slide', '?')} prompt missing Identity continuity lock.")
    results["REQ-IDENTITY-CONSISTENCY-001"] = {
        "pass": bool(identity_refs) and bool(identity_prompt_refs) and not identity_issues,
        "evidence": {
            "identity_review": str(context.out_dir / BASE_ARTIFACTS["identity_consistency_review"])
            if (context.out_dir / BASE_ARTIFACTS["identity_consistency_review"]).exists()
            else None,
            "status": identity_review.get("status") if identity_review else None,
            "issues": identity_issues,
        },
    }
    post_copy_issues: list[str] = []
    if not post_copy_room:
        post_copy_issues.append("post-copy-visual-room.json is missing.")
    else:
        if post_copy_room.get("status") != "GO":
            post_copy_issues.append(f"post-copy-visual-room.json status is {post_copy_room.get('status')}.")
        if len(post_copy_room.get("visual_system_candidates", [])) < 3:
            post_copy_issues.append("post-copy visual room must compare at least three visual systems.")
        if not post_copy_room.get("slide_visual_blueprint"):
            post_copy_issues.append("post-copy visual room must include slide_visual_blueprint.")
    results["REQ-POST-COPY-VISUAL-ROOM-001"] = {
        "pass": not post_copy_issues,
        "evidence": {
            "path": str(context.out_dir / BASE_ARTIFACTS["post_copy_visual_room"]),
            "status": post_copy_room.get("status") if post_copy_room else None,
            "decision": post_copy_room.get("decision") if post_copy_room else None,
            "selected_visual_system": post_copy_room.get("selected_visual_system") if post_copy_room else None,
            "issues": post_copy_issues,
        },
    }
    visual_quality_issues: list[str] = []
    if not visual_quality:
        visual_quality_issues.append("visual-plan-quality.json is missing.")
    else:
        if visual_quality.get("status") != "PASS":
            visual_quality_issues.append(
                f"visual-plan-quality.json status is {visual_quality.get('status')}."
            )
        if not visual_quality.get("can_generate"):
            visual_quality_issues.append("visual-plan-quality.json blocks image generation.")
        visual_quality_issues.extend(visual_quality.get("issues", []))
        if len(visual_quality.get("slide_reviews", [])) != context.slide_count:
            visual_quality_issues.append(
                f"visual-plan-quality.json has {len(visual_quality.get('slide_reviews', []))} slide records, expected {context.slide_count}."
            )
    results["REQ-VISUAL-PLAN-QUALITY-001"] = {
        "pass": not visual_quality_issues,
        "evidence": {
            "path": str(context.out_dir / BASE_ARTIFACTS["visual_plan_quality"]),
            "status": visual_quality.get("status") if visual_quality else None,
            "decision": visual_quality.get("decision") if visual_quality else None,
            "issues": visual_quality_issues,
        },
    }
    results["REQ-SLIDES-001"] = {
        "pass": MIN_STORY_SLIDES <= context.slide_count <= MAX_STORY_SLIDES
        and len(package_slides) == context.slide_count
        and len(prompts) == context.slide_count,
        "evidence": f"requested={context.slide_count}, slides={len(package_slides)}, prompts={len(prompts)}",
    }
    success_gate = evaluate_successful_carousel_standard(
        context.package,
        slide_count=context.slide_count,
    )
    results["REQ-SUCCESS-STANDARD-001"] = {
        "pass": success_gate["pass"],
        "evidence": success_gate,
    }
    final_files = required_final_files(context)
    results["REQ-FINAL-IMAGES-001"] = final_image_gate(context, final_files)
    model_native_manifest_path = context.out_dir / BASE_ARTIFACTS["final_images"]
    model_native_issues: list[str] = []
    model_native_manifest: dict[str, Any] = {}
    if model_native_manifest_path.exists():
        model_native_manifest = json.loads(model_native_manifest_path.read_text(encoding="utf-8"))
    else:
        model_native_issues.append("final-images.json is missing.")
    if not all(path.exists() for path in final_files):
        missing = [str(path) for path in final_files if not path.exists()]
        model_native_issues.append("Missing publishable final slides: " + ", ".join(missing))
    if model_native_manifest:
        if model_native_manifest.get("backend") not in {"codex_builtin", "model_art_local_text"}:
            model_native_issues.append(
                "final-images.json backend must be codex_builtin or model_art_local_text for Instagram-grade final art."
            )
        if model_native_manifest.get("generation_mode") not in PUBLISHABLE_FINAL_GENERATION_MODES:
            model_native_issues.append(
                "final-images.json generation_mode must be one of: "
                + ", ".join(sorted(PUBLISHABLE_FINAL_GENERATION_MODES))
            )
        records = model_native_manifest.get("slides", [])
        if len(records) != context.slide_count:
            model_native_issues.append(f"final-images.json has {len(records)} slide records, expected {context.slide_count}.")
        for record in records:
            if record.get("backend") not in {"codex_builtin", "model_art_local_text"}:
                model_native_issues.append(f"Slide {record.get('slide')} backend is not an approved final-art backend.")
            if record.get("generation_mode") not in PUBLISHABLE_FINAL_GENERATION_MODES:
                model_native_issues.append(f"Slide {record.get('slide')} is not marked as a publishable final generation mode.")
            if record.get("local_generated_source"):
                model_native_issues.append(f"Slide {record.get('slide')} uses local_generated_source as final art provenance.")
            native_outputs = record.get("native_outputs", {})
            if isinstance(native_outputs, dict):
                for format_name, native_output in native_outputs.items():
                    if isinstance(native_output, dict) and native_output.get("local_generated_source"):
                        model_native_issues.append(
                            f"Slide {record.get('slide')} {format_name} uses local_generated_source as final art provenance."
                        )
            file_text = str(record.get("file", ""))
            if "final-with-text" in file_text:
                model_native_issues.append(f"Slide {record.get('slide')} uses final-with-text as publishable output.")
            if not record.get("prompt"):
                model_native_issues.append(f"Slide {record.get('slide')} is missing source prompt provenance.")
    if (context.out_dir / "final-with-text").exists():
        compatibility_outputs = sorted((context.out_dir / "final-with-text").glob("slide-*.png"))
        if compatibility_outputs and not all(path.exists() for path in final_files):
            model_native_issues.append(
                "final-with-text exists without complete publishable final/slide-XX.png outputs; "
                "text placement must be integrated into final/, not left only in a compatibility folder."
            )
    results["REQ-INTEGRATED-FINAL-TEXT-001"] = {
        "pass": not model_native_issues,
        "evidence": {
            "files": [str(path) for path in final_files if path.exists()],
            "manifest": str(model_native_manifest_path) if model_native_manifest_path.exists() else None,
            "generation_mode": model_native_manifest.get("generation_mode"),
            "issues": model_native_issues,
        },
    }
    visual_qa_path = context.out_dir / QUALITY_ARTIFACTS["visual_qa"]
    structured_qa = structured_visual_qa_gate(context)
    if visual_qa_path.exists():
        visual_qa_text = visual_qa_path.read_text(encoding="utf-8")
        failed_checks = [
            line.strip()
            for line in visual_qa_text.splitlines()
            if line.strip().startswith("- [x] FAIL")
        ]
        unchecked_face_or_storyboard_items = [
            line.strip()
            for line in visual_qa_text.splitlines()
            if line.strip().startswith("- [ ]")
            and ("face" in line.lower() or "storyboard" in line.lower())
        ]
    else:
        failed_checks = ["visual-qa.md is missing"]
        unchecked_face_or_storyboard_items = []
    results["REQ-VISUAL-QA-001"] = {
        "pass": visual_qa_path.exists()
        and structured_qa["pass"]
        and not failed_checks
        and not unchecked_face_or_storyboard_items,
        "evidence": {
            "visual_qa": str(visual_qa_path),
            "structured_visual_qa": structured_qa["path"],
            "failed": [*structured_qa["failed"], *failed_checks],
            "unchecked_face_or_storyboard_items": unchecked_face_or_storyboard_items,
        },
    }
    integrated_text_plan = prompt_pack(context).get("integrated_text_plan") or prompt_pack(context).get("text_overlay_plan", {})
    results["REQ-BRAND-001"] = {
        "pass": integrated_text_plan.get("brandmark") == "@a.storyof.two"
        and "top-right" in integrated_text_plan.get("brandmark_placement", ""),
        "evidence": integrated_text_plan,
    }
    results["REQ-NEGATIVE-001"] = {
        "pass": all(token in negative_lower for token in ["photorealism", "3d", "stock", "quote-card"]),
        "evidence": negative,
    }
    results["REQ-OUTPUT-001"] = {
        "pass": all((context.out_dir / path).exists() for path in BASE_ARTIFACTS.values()),
        "evidence": [path for path in BASE_ARTIFACTS.values() if (context.out_dir / path).exists()],
    }
    wiki_evidence = {
        name: path.exists()
        for name, path in expected_wiki_paths(context).items()
    }
    results["REQ-WIKI-001"] = {
        "pass": all(wiki_evidence.values()),
        "evidence": wiki_evidence,
    }
    return results


def build_final_audit(
    context: QualityContext,
    ledger: dict[str, Any],
    stage_reviews: dict[str, Any],
) -> dict[str, Any]:
    requirement_results = evaluate_requirements(context)
    issues: list[str] = []
    notes: list[str] = []

    for requirement in ledger["requirements"]:
        result = requirement_results.get(requirement["id"], {"pass": False, "evidence": "No evaluator."})
        if requirement.get("critical") and not result["pass"]:
            issues.append(f"{requirement['id']}: {requirement['label']}")

    for name, review in stage_reviews["reviews"].items():
        if review["status"] == "NEEDS_FIXES":
            issues.append(f"{name}: " + "; ".join(review["issues"]))
        elif review["status"] == "PASS_WITH_NOTES":
            notes.extend(review["notes"])

    missing_base_artifacts = [
        path for path in BASE_ARTIFACTS.values() if not (context.out_dir / path).exists()
    ]
    if missing_base_artifacts:
        issues.append("Missing base artifacts: " + ", ".join(missing_base_artifacts))

    render_status = context.render_result.get("status")
    if render_status == "skipped":
        reason = context.render_result.get("reason", "render skipped")
        if reason not in notes:
            notes.append(reason)

    visual_qa_path = context.out_dir / QUALITY_ARTIFACTS["visual_qa"]
    final_images_exist = all(
        quality_asset_path(context, "final", f"slide-{number:02d}.png").exists()
        for number in range(1, context.slide_count + 1)
    )
    if visual_qa_path.exists():
        visual_qa_text = visual_qa_path.read_text(encoding="utf-8")
        failed_checks = [
            line.strip()
            for line in visual_qa_text.splitlines()
            if line.strip().startswith("- [x] FAIL")
        ]
        if failed_checks:
            issues.append("Visual QA failed: " + "; ".join(failed_checks))
    elif final_images_exist:
        issues.append("Final images exist but visual-qa.md is missing.")

    blocked = False
    for artifact_name in ["image-generation.json", "final-images.json"]:
        artifact_path = context.out_dir / artifact_name
        if artifact_path.exists():
            try:
                artifact_status = json.loads(artifact_path.read_text(encoding="utf-8")).get("status")
                blocked = artifact_status in {"BLOCKED", "blocked"} or blocked
            except json.JSONDecodeError:
                pass
    status = "BLOCKED" if blocked else status_from_issues(issues, notes)
    return {
        "schema_version": "1.0",
        "auditor": "C7-Final Contract Auditor",
        "status": status,
        "pass": status in {"PASS", "PASS_WITH_NOTES"},
        "requirements": requirement_results,
        "checked_artifacts": {
            path: (context.out_dir / path).exists()
            for path in BASE_ARTIFACTS.values()
        },
        "quality_artifacts": QUALITY_ARTIFACTS,
        "issues": issues,
        "notes": notes,
    }


def markdown_link(title: str, target: str) -> str:
    return f"[{title}]({target})"


def build_wiki_update(context: QualityContext, audit: dict[str, Any]) -> str:
    concept = context.package.get("concept", {})
    copy_pack = context.package.get("copy", {})
    lines = [
        f"# {context.title} - Carousel Quality Update",
        "",
        f"last_updated: {context.today}",
        "confidence: 0.7",
        "sources:",
        f"- {context.out_dir / 'manifest.json'}",
        f"- {context.out_dir / 'prompt-pack.json'}",
        f"- {context.out_dir / 'final-audit.json'}",
        "",
        "## Status",
        "",
        f"Final audit: {audit['status']}",
        "",
    ]
    if audit.get("issues"):
        lines.extend(["## Issues", ""])
        lines.extend(f"- {issue}" for issue in audit["issues"])
        lines.append("")
    if audit.get("notes"):
        lines.extend(["## Notes", ""])
        lines.extend(f"- {note}" for note in audit["notes"])
        lines.append("")
    lines.extend(
        [
            "## Human Truth",
            "",
            concept.get("human_truth", ""),
            "",
            "## Learning",
            "",
            "- Keep the romantic watercolor-and-ink / identity-rooted style as the default for memory-led carousels.",
            "- Preserve source-photo objects before adding decorative story elements.",
            "- Preserve Aachu/Zuv identity references across every generated slide.",
            "- Carry the successful-carousel standard as open agent alignment, not a keyword checklist.",
            "- Generate model-native publishable slides when typography, face quality, outfit continuity, and composition must match the reference examples.",
            "",
            "## Caption",
            "",
            copy_pack.get("caption_recommended", ""),
            "",
        ]
    )
    return "\n".join(lines)


def build_carousel_wiki_page(context: QualityContext, audit: dict[str, Any]) -> str:
    concept = context.package.get("concept", {})
    lines = [
        f"# {context.title}",
        "",
        f"last_updated: {context.today}",
        "confidence: 0.7",
        "sources:",
        f"- {context.out_dir / 'manifest.json'}",
        f"- {context.out_dir / 'slides.json'}",
        f"- {context.out_dir / 'prompt-pack.json'}",
        f"- {context.out_dir / 'final-audit.json'}",
        "",
        "## Summary",
        "",
        concept.get("human_truth", ""),
        "",
        "## Style Memory",
        "",
        "- Romantic watercolor-and-ink / identity-rooted illustration.",
        "- Fine ink and pencil linework, transparent watercolor blooms, muted vintage colors, warm ivory paper with visible paper grain.",
        "- Preserve real outfits, poses, settings, and relationship cues.",
        "- Use Aachu/Zuv identity references for recurring character likeness.",
        "- Keep the successful-carousel standard active as open agent alignment: public identity mirror, private receipts, active Zuv response, emotional turn, and send/save thesis.",
        "",
        "## Slide Flow",
        "",
    ]
    for slide in slides(context):
        lines.append(f"- Slide {slide.get('slide')}: {slide.get('copy')} - {slide.get('visual')}")
    lines.extend(
        [
            "",
            "## Final Audit",
            "",
            f"Status: {audit['status']}",
            "",
        ]
    )
    if audit.get("issues"):
        lines.extend(["## Issues", ""])
        lines.extend(f"- {issue}" for issue in audit["issues"])
        lines.append("")
    if audit.get("notes"):
        lines.extend(["## Notes", ""])
        lines.extend(f"- {note}" for note in audit["notes"])
        lines.append("")
    lines.extend(
        [
            "## Artifact Links",
            "",
            f"- {markdown_link('Run ledger', str(context.out_dir / 'run-ledger.json'))}",
            f"- {markdown_link('Stage reviews', str(context.out_dir / 'stage-reviews.json'))}",
            f"- {markdown_link('Final audit', str(context.out_dir / 'final-audit.json'))}",
            "",
        ]
    )
    return "\n".join(lines)


def update_index(index_path: Path, context: QualityContext) -> None:
    link = f"| [{context.title}](carousels/{context.slug}.md) | {context.today} | {context.slide_count} | C-layer | 0.7 |"
    if index_path.exists():
        text = index_path.read_text(encoding="utf-8")
    else:
        text = (
            "# Wiki Index - @a.storyof.two Knowledge Base\n\n"
            "last_updated: 0\n"
            "total_pages: 0\n"
            "confidence_floor: 0.4\n\n"
            "---\n"
        )

    text = text.replace("last_updated: 0", f"last_updated: {context.today}")
    if "## Carousels" not in text:
        insertion = (
            "\n## Carousels\n"
            "Illustrated carousel packages and their learning records.\n\n"
            "| Carousel | Date | Slides | Pipeline | Confidence |\n"
            "|----------|------|--------|----------|------------|\n"
            f"{link}\n"
        )
        if "## Insights" in text:
            text = text.replace("## Insights", insertion + "\n## Insights", 1)
        else:
            text = text.rstrip() + "\n" + insertion
    elif link not in text:
        marker = "|----------|------|--------|----------|------------|"
        if marker in text:
            text = text.replace(marker, marker + "\n" + link, 1)
        else:
            text = text.rstrip() + "\n" + link + "\n"

    text = replace_metadata_value(text, "last_updated", str(context.today))
    index_path.parent.mkdir(parents=True, exist_ok=True)
    index_path.write_text(text, encoding="utf-8")


def expected_wiki_paths(context: QualityContext) -> dict[str, Path]:
    return {
        "carousel_page": context.workspace_root / "wiki" / "carousels" / f"{context.slug}.md",
        "wiki_index": context.workspace_root / "wiki" / "index.md",
        "working_memory": context.workspace_root / "memory" / "working.md",
        "graph_memory": context.workspace_root / "memory" / "graph.json",
    }


def replace_metadata_value(text: str, key: str, value: str) -> str:
    lines = text.splitlines()
    for index, line in enumerate(lines):
        if line.startswith(f"{key}:"):
            lines[index] = f"{key}: {value}"
            return "\n".join(lines) + "\n"
    return f"{key}: {value}\n" + text


def append_working_memory(memory_path: Path, context: QualityContext, audit: dict[str, Any]) -> None:
    if memory_path.exists():
        text = memory_path.read_text(encoding="utf-8").rstrip()
    else:
        text = "# Working Memory - Current Analysis Session\n"

    header = f"## C-layer carousel run: {context.title}"
    header_index = text.find(header)
    if header_index != -1:
        next_header_index = text.find("\n## ", header_index + len(header))
        if next_header_index == -1:
            text = text[:header_index].rstrip()
        else:
            text = (text[:header_index].rstrip() + "\n" + text[next_header_index:].lstrip()).rstrip()

    entry = "\n".join(
        [
            "",
            header,
            f"- date: {context.today}",
            f"- slug: {context.slug}",
            f"- final_audit: {audit['status']}",
            "- learning: romantic watercolor-and-ink / identity-rooted style remains the default for story carousels.",
            f"- package: {context.out_dir}",
        ]
    )
    memory_path.parent.mkdir(parents=True, exist_ok=True)
    memory_path.write_text(text + "\n" + entry + "\n", encoding="utf-8")


def update_graph(graph_path: Path, context: QualityContext, audit: dict[str, Any]) -> None:
    if graph_path.exists():
        graph = json.loads(graph_path.read_text(encoding="utf-8"))
    else:
        graph = {"entities": {}, "relationships": [], "themes": {}}

    graph.setdefault("entities", {})
    graph.setdefault("relationships", [])
    graph.setdefault("themes", {})

    entity_id = f"carousel:{context.slug}"
    graph["entities"][entity_id] = {
        "id": entity_id,
        "type": "illustrated_carousel",
        "title": context.title,
        "date": str(context.today),
        "status": audit["status"],
        "slide_count": context.slide_count,
        "package": str(context.out_dir),
        "content_lane": context.package.get("concept", {}).get("content_lane"),
    }
    graph["themes"].setdefault(
        "watercolor_ink_identity_rooted",
        {
            "id": "watercolor_ink_identity_rooted",
            "type": "creative_style",
            "confidence": 0.7,
            "description": "Premium romantic watercolor-and-ink illustration rooted in identity references and story photos.",
        },
    )
    relationship = {
        "from": entity_id,
        "to": "watercolor_ink_identity_rooted",
        "type": "uses_creative_style",
        "confidence": 0.7,
    }
    if relationship not in graph["relationships"]:
        graph["relationships"].append(relationship)
    graph["last_updated"] = str(context.today)

    graph_path.parent.mkdir(parents=True, exist_ok=True)
    write_json(graph_path, graph)


def update_wiki_memory(context: QualityContext, audit: dict[str, Any]) -> None:
    wiki_dir = context.workspace_root / "wiki"
    carousel_dir = wiki_dir / "carousels"
    memory_dir = context.workspace_root / "memory"

    carousel_dir.mkdir(parents=True, exist_ok=True)
    (carousel_dir / f"{context.slug}.md").write_text(
        build_carousel_wiki_page(context, audit),
        encoding="utf-8",
    )
    update_index(wiki_dir / "index.md", context)
    append_working_memory(memory_dir / "working.md", context, audit)
    update_graph(memory_dir / "graph.json", context, audit)


def build_visual_qa(context: QualityContext) -> str:
    structured_qa_passed = structured_visual_qa_gate(context)["pass"]
    mark = "x" if structured_qa_passed else " "
    status_note = (
        "Structured visual QA has passed; these checklist items mirror `visual-qa.json`."
        if structured_qa_passed
        else "Mark any failed item as `- [x] FAIL: ...`; the final audit treats that as a blocker."
    )
    lines = [
        "# Visual QA",
        "",
        status_note,
        "",
    ]
    for slide in slides(context):
        lines.append(
            f"- [{mark}] Slide {slide.get('slide')} final image matches slide "
            f"{slide.get('slide')} storyboard: {slide.get('copy')}"
        )
    lines.extend(
        [
            f"- [{mark}] Aachu face is recognizably based on the identity reference.",
            f"- [{mark}] Zuv face is recognizably based on the identity reference.",
            f"- [{mark}] Clothing and dress details follow the identity/style references.",
            f"- [{mark}] Illustration style matches the selected carousel style direction.",
            f"- [{mark}] Scene logic matches the copy: clothing, props, hands, and action prove the written line without contradiction.",
            f"- [{mark}] Pose/anatomy is natural and flattering for both Aachu and Zuv; no crouched, cramped, broken, or awkward body language.",
            f"- [{mark}] Successful carousel standard is visible: scene-first behavior proves the relationship truth before mood or decoration.",
            f"- [{mark}] Rendered text and brandmark are visible, accurate, and part of the artwork.",
            f"- [{mark}] Final publishable files exist for every canvas locked in `format-contract.json`.",
            "",
        ]
    )
    return "\n".join(lines)


def write_quality_artifacts(context: QualityContext) -> dict[str, Any]:
    ledger = build_run_ledger(context)
    stage_reviews = build_stage_reviews(context, ledger)
    update_wiki_memory(context, {"status": "PENDING"})
    context.out_dir.mkdir(parents=True, exist_ok=True)
    visual_qa_path = context.out_dir / QUALITY_ARTIFACTS["visual_qa"]
    if not visual_qa_path.exists():
        visual_qa_path.write_text(
            build_visual_qa(context),
            encoding="utf-8",
        )
    final_audit = build_final_audit(context, ledger, stage_reviews)
    ledger["stage_statuses"]["final_contract"] = final_audit["status"]
    ledger["final_gate"] = {
        "status": final_audit["status"],
        "pass": final_audit["pass"],
        "notes": final_audit["notes"],
    }

    write_json(context.out_dir / QUALITY_ARTIFACTS["run_ledger"], ledger)
    write_json(context.out_dir / QUALITY_ARTIFACTS["stage_reviews"], stage_reviews)
    write_json(context.out_dir / QUALITY_ARTIFACTS["final_audit"], final_audit)
    (context.out_dir / QUALITY_ARTIFACTS["wiki_update"]).write_text(
        build_wiki_update(context, final_audit),
        encoding="utf-8",
    )
    update_wiki_memory(context, final_audit)
    return final_audit
